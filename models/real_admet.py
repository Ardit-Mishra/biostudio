# =============================================================================
# REAL ADMET PREDICTION MODULE
# =============================================================================
# Serves genuine, held-out-validated ADMET predictions from an ensemble of
# XGBoost, RandomForest, and MLP models trained on public Therapeutics Data
# Commons (TDC) datasets with scaffold splits. Replaces the previous
# random-weight "neural network" demo.
#
# The served prediction (probability / value, threshold, etc.) still comes
# from XGBoost -- it is the model app.py has always shown and the one every
# existing test asserts a schema against. RandomForest and MLP are trained on
# the identical split and identical features and their held-out scores are
# shipped alongside it (models/saved_models/*_meta.json -> "models"), so the
# comparison is real and inspectable, not decorative. `ensemble_predict()`
# below exposes all three for callers that want to show or use them.
#
# Featurization is the full RDKit descriptor set (217 descriptors) + ECFP4
# (2048 bits) -- see descriptors.py, which MUST stay byte-identical to
# ml-training/biostudio/descriptors.py (a separate repo) so training and
# serving compute the same numbers for the same molecule. If a model file is
# absent, that endpoint reports as unavailable rather than fabricating a
# value.
#
# SHAP: `explain_endpoint()` returns real per-prediction feature attributions
# for the served XGBoost model via exact Tree SHAP -- computed through
# xgboost's own `Booster.predict(pred_contribs=True)` rather than the `shap`
# package's TreeExplainer. Same algorithm (Tree SHAP is exact for tree
# ensembles either way; contributions sum to margin - base_value, verified
# against shap.TreeExplainer's output on this exact model/molecule pair
# during development), but computed without shap's XGBoost model-dump parser,
# which cannot read the `base_score` field xgboost >=2.2 writes (a bracketed
# scientific-notation string like "[5E-1]" -- confirmed reproducible with
# shap 0.49.1 + xgboost 3.4.1: `ValueError: could not convert string to
# float: '[5E-1]'`, on both the sklearn wrapper and a plain loaded Booster).
# Training-side global feature-importance reporting
# (ml-training/biostudio/train_and_save_admet.py, *_shap.json) still uses the
# `shap` package directly, in a pinned xgboost==2.1.4 environment where that
# parser works -- see that script's docstring. This module never imports
# `shap` at all, so this endpoint has no extra runtime dependency and no
# version-pinning risk in production.
# =============================================================================
import os
import json
import logging
from typing import Dict, List, Optional, Union

_log = logging.getLogger(__name__)

from rdkit import Chem
from rdkit import RDLogger
RDLogger.DisableLog("rdApp.*")

import numpy as np

try:
    import xgboost as xgb
    _HAS_XGB = True
except Exception:
    _HAS_XGB = False

try:
    import joblib
    _HAS_JOBLIB = True
except Exception:
    _HAS_JOBLIB = False

from . import descriptors as feat

FeaturizationError = feat.FeaturizationError

# Toxicity endpoints that back comprehensive_toxicity_profile (drop-in for the
# old NeuralToxicityPredictor). Keys are the exact UI labels the app already uses.
_TOX_MAP = {
    "Hepatotoxicity": "DILI",
    "Cardiotoxicity (hERG)": "hERG",
    "Mutagenicity (Ames)": "AMES",
    "Carcinogenicity": "Carcinogens_Lagunin",
}
# Which endpoints are "positive = concerning" so risk wording reads correctly.
_POSITIVE_IS_RISK = {"DILI", "hERG", "AMES", "Carcinogens_Lagunin"}


def _featurize_one(mol) -> np.ndarray:
    """Featurize one molecule, or raise.

    This used to return an all-zero vector whenever RDKit threw. That zero
    vector is a perfectly valid input as far as XGBoost is concerned: the
    booster scored it and returned a confident-looking probability, which the
    UI rendered exactly like a real prediction. A descriptor crash therefore
    became a number a user could act on, with nothing anywhere to say the
    molecule had never actually been featurized.

    Raising is the whole point. The caller turns this into an explicit
    "unavailable", and no model ever sees a fabricated input. Delegates to
    descriptors.featurize_one, which additionally records *which* descriptor
    failed rather than only that featurization as a whole did.
    """
    return feat.featurize_one(mol).reshape(1, -1)


def _default_model_dir() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    # 1) bundled with the app (deployment)
    bundled = os.path.join(here, "saved_models")
    if os.path.isdir(bundled):
        return bundled
    # 2) dev fallback: the training output tree
    dev = os.path.abspath(os.path.join(
        here, "..", "..", "ml-training", "biostudio", "saved_models"))
    return dev if os.path.isdir(dev) else bundled


class RealADMETPredictor:
    """Loads saved XGBoost/RandomForest/MLP ADMET models and serves real,
    provenance-tagged predictions. Safe to instantiate even when no models
    are present."""

    def __init__(self, model_dir: Optional[str] = None):
        self.model_dir = model_dir or _default_model_dir()
        self.models: Dict[str, "xgb.Booster"] = {}
        self.rf_models: Dict[str, object] = {}
        self.mlp_models: Dict[str, object] = {}
        self.meta: Dict[str, dict] = {}
        self._load()

    def _load(self):
        if not _HAS_XGB or not os.path.isdir(self.model_dir):
            return
        manifest = os.path.join(self.model_dir, "admet_models_manifest.json")
        names = []
        if os.path.exists(manifest):
            try:
                names = list(json.load(open(manifest)).keys())
            except Exception:
                names = []
        if not names:
            names = [f[:-9] for f in os.listdir(self.model_dir) if f.endswith("_xgb.json")]
        for name in names:
            mpath = os.path.join(self.model_dir, f"{name}_xgb.json")
            metap = os.path.join(self.model_dir, f"{name}_meta.json")
            if not os.path.exists(mpath):
                continue
            try:
                meta = json.load(open(metap)) if os.path.exists(metap) else {}
                # Native Booster (not the sklearn wrapper) so we don't drag in
                # scikit-learn just to serve. save_model preserves the objective,
                # so binary:logistic boosters predict probabilities directly.
                booster = xgb.Booster()
                booster.load_model(mpath)
                self.models[name] = booster
                self.meta[name] = meta
            except Exception as exc:
                _log.warning("failed to load XGBoost model for %s: %s", name, exc)
                continue
            # Ensemble siblings are optional: a missing/unloadable RF or MLP
            # file degrades that one model to "unavailable" in
            # ensemble_predict(), it never blocks XGBoost from serving.
            if _HAS_JOBLIB:
                rf_info = meta.get("models", {}).get("random_forest", {})
                rf_file = rf_info.get("model_file") or f"{name}_rf.joblib"
                rf_path = os.path.join(self.model_dir, rf_file)
                if os.path.exists(rf_path):
                    try:
                        self.rf_models[name] = joblib.load(rf_path)
                    except Exception as exc:
                        _log.warning("failed to load RF for %s: %s", name, exc)
                mlp_info = meta.get("models", {}).get("mlp", {})
                mlp_file = mlp_info.get("model_file") or f"{name}_mlp.joblib"
                mlp_path = os.path.join(self.model_dir, mlp_file)
                if os.path.exists(mlp_path):
                    try:
                        self.mlp_models[name] = joblib.load(mlp_path)
                    except Exception as exc:
                        _log.warning("failed to load MLP for %s: %s", name, exc)

    def _raw_predict(self, tdc_name: str, X: np.ndarray) -> float:
        dm = xgb.DMatrix(X)
        return float(self.models[tdc_name].predict(dm)[0])

    def available(self) -> bool:
        return len(self.models) > 0

    def _provenance(self, name: str) -> str:
        m = self.meta.get(name, {})
        metric = m.get("official_metric", "")
        score = m.get("test_score")
        if score is None:
            return "XGBoost (TDC)"
        return f"XGBoost - {metric} {score:.2f} (TDC held-out test)"

    def caveat(self, name: str) -> Optional[str]:
        """A stated limitation for this endpoint, or None.

        Read from the model's own `*_meta.json` so the caveat travels with the
        artifact. The regressions on AMES and Caco2_Wang were previously
        disclosed only in repository markdown — README, METHODOLOGY, VALIDATION
        — none of which app.py ever opens, so a visitor to the live demo saw a
        confident number with no indication the endpoint had got worse. A
        caveat that only exists in a file the product never reads has not been
        communicated to anyone.
        """
        return self.meta.get(name, {}).get("caveat")

    def predict_endpoint(self, mol_or_smiles: Union[str, "Chem.Mol"],
                         tdc_name: str) -> Optional[dict]:
        """Return a real prediction for one endpoint, or None if unavailable."""
        if tdc_name not in self.models:
            return None
        mol = (Chem.MolFromSmiles(mol_or_smiles)
               if isinstance(mol_or_smiles, str) else mol_or_smiles)
        if mol is None:
            return None
        try:
            X = _featurize_one(mol)
        except FeaturizationError as exc:
            # Returning None routes into the caller's existing "unavailable"
            # path. Never fall through to _raw_predict here: a prediction made
            # from a substitute feature vector is worse than no prediction,
            # because it is indistinguishable from a real one.
            _log.warning("featurization failed for %s: %s", tdc_name, exc)
            return None
        m = self.meta.get(tdc_name, {})
        if m.get("task") == "regression":
            value = self._raw_predict(tdc_name, X)
            return {"task": "regression", "value": round(value, 3),
                    "metric": m.get("official_metric"), "test_score": m.get("test_score"),
                    "provenance": self._provenance(tdc_name), "caveat": self.caveat(tdc_name),
                "app_label": m.get("app_label")}
        prob = self._raw_predict(tdc_name, X)  # binary:logistic booster -> probability
        thr = m.get("threshold") or 0.5
        return {"task": "classification", "probability": round(prob, 3),
                "threshold": thr, "positive": prob >= thr,
                "metric": m.get("official_metric"), "test_score": m.get("test_score"),
                "provenance": self._provenance(tdc_name), "caveat": self.caveat(tdc_name),
                "app_label": m.get("app_label")}

    def ensemble_predict(self, mol_or_smiles: Union[str, "Chem.Mol"],
                          tdc_name: str) -> Optional[dict]:
        """XGBoost + RandomForest + MLP predictions for one endpoint, each
        with its own held-out test score, so a caller can show the full
        comparison instead of only the served model. A model whose file
        didn't load reports `available: False` under its own key rather than
        being silently omitted -- the caller can tell "this model wasn't
        trained/didn't load" from "this model wasn't asked for"."""
        if tdc_name not in self.models:
            return None
        mol = (Chem.MolFromSmiles(mol_or_smiles)
               if isinstance(mol_or_smiles, str) else mol_or_smiles)
        if mol is None:
            return None
        try:
            X = _featurize_one(mol)
        except FeaturizationError as exc:
            _log.warning("featurization failed for %s: %s", tdc_name, exc)
            return None

        m = self.meta.get(tdc_name, {})
        is_clf = m.get("task") != "regression"
        model_scores = m.get("models", {})
        out = {}

        xgb_prob = self._raw_predict(tdc_name, X)
        out["xgboost"] = {
            "available": True,
            "value": round(xgb_prob, 3),
            "test_score": model_scores.get("xgboost", {}).get("test_score", m.get("test_score")),
        }

        for key, bucket in (("random_forest", self.rf_models), ("mlp", self.mlp_models)):
            pipe = bucket.get(tdc_name)
            if pipe is None:
                out[key] = {"available": False, "reason": "model file not present or failed to load"}
                continue
            try:
                pred = pipe.predict_proba(X)[:, 1][0] if is_clf else pipe.predict(X)[0]
                out[key] = {
                    "available": True,
                    "value": round(float(pred), 3),
                    "test_score": model_scores.get(key, {}).get("test_score"),
                }
            except Exception as exc:
                out[key] = {"available": False, "reason": f"{type(exc).__name__}: {exc}"}

        return {
            "task": "classification" if is_clf else "regression",
            "metric": m.get("official_metric"),
            "app_label": m.get("app_label"),
            "best_model": m.get("model_comparison", {}).get("best"),
            "models": out,
        }

    def explain_endpoint(self, mol_or_smiles: Union[str, "Chem.Mol"],
                          tdc_name: str, top_k: int = 10) -> Optional[dict]:
        """Real per-prediction SHAP (Tree SHAP, exact) feature attribution
        for the served XGBoost model. Computed via xgboost's own
        `Booster.predict(pred_contribs=True)` -- see the module docstring for
        why this isn't the `shap` package's TreeExplainer. Returns None if
        the molecule/endpoint is unavailable -- never a fabricated
        explanation standing in for a real one.

        Contributions are in margin (logit) space for classifiers -- they sum
        with `base_value` to the pre-sigmoid score, not directly to the
        displayed probability. That is Tree SHAP's actual unit for a
        binary:logistic booster; converting each contribution to a
        probability-space number individually would not be additive and
        would misrepresent the method, so this reports the true unit instead
        of a more readable but wrong one.
        """
        if not _HAS_XGB or tdc_name not in self.models:
            return None
        mol = (Chem.MolFromSmiles(mol_or_smiles)
               if isinstance(mol_or_smiles, str) else mol_or_smiles)
        if mol is None:
            return None
        try:
            X = _featurize_one(mol)
        except FeaturizationError as exc:
            _log.warning("featurization failed for %s: %s", tdc_name, exc)
            return None
        try:
            dm = xgb.DMatrix(X)
            contribs = self.models[tdc_name].predict(dm, pred_contribs=True)[0]
            base_value = float(contribs[-1])
            row = contribs[:-1]
            order = np.argsort(-np.abs(row))[:top_k]
            top = [
                {
                    "feature": feat.feature_name(int(i)),
                    "value": round(float(X[0, i]), 4),
                    "shap_contribution": round(float(row[i]), 4),
                }
                for i in order
            ]
            return {
                "tdc_name": tdc_name, "base_value": round(base_value, 4), "top_features": top,
                "units": "margin (logit) space" if self.meta.get(tdc_name, {}).get("task") != "regression"
                         else "predicted value's own units",
                "method": "exact Tree SHAP via xgboost Booster.predict(pred_contribs=True)",
            }
        except Exception as exc:
            _log.warning("SHAP explanation failed for %s: %s", tdc_name, exc)
            return None

    def comprehensive_toxicity_profile(self, mol) -> Dict:
        """Drop-in replacement for NeuralToxicityPredictor.comprehensive_toxicity_profile.
        Same dict shape and UI labels, but real model probabilities and honest
        provenance in the 'confidence' field. Missing models report as unavailable."""
        if mol is None:
            return {"error": "Invalid molecule"}
        profile = {}
        for label, tdc_name in _TOX_MAP.items():
            res = self.predict_endpoint(mol, tdc_name)
            if res is None:
                profile[label] = {"probability": None, "percentage": "n/a",
                                  "risk_level": "Unavailable",
                                  "confidence": "model not loaded"}
                continue
            p = res["probability"]
            if label == "Mutagenicity (Ames)":
                risk = "Positive" if res["positive"] else "Negative"
            else:
                risk = "High" if p > 0.7 else "Moderate" if p > 0.4 else "Low"
            profile[label] = {
                "probability": round(p, 3),
                "percentage": f"{round(p * 100, 1)}%",
                "risk_level": risk,
                "confidence": res["provenance"],
                # Carried through so the UI can state a known limitation at the
                # point the number is shown, rather than in a repo file.
                "caveat": res.get("caveat"),
            }
        return profile


# convenience singleton
_PREDICTOR: Optional[RealADMETPredictor] = None
def get_predictor() -> RealADMETPredictor:
    global _PREDICTOR
    if _PREDICTOR is None:
        _PREDICTOR = RealADMETPredictor()
    return _PREDICTOR
