# =============================================================================
# REAL ADMET PREDICTION MODULE
# =============================================================================
# Serves genuine, held-out-validated ADMET predictions from XGBoost models
# trained on public Therapeutics Data Commons (TDC) datasets with scaffold
# splits. Replaces the previous random-weight "neural network" demo.
#
# Each prediction carries its model's honest held-out test metric (AUROC/AUPRC/
# MAE on the TDC test set), so the UI can show provenance instead of a bare
# number. Featurization here is bit-for-bit identical to training
# (ml-training/biostudio/train_and_save_admet.py): ECFP4(2048) + 10 RDKit
# descriptors. If a model file is absent, that endpoint reports as unavailable
# rather than fabricating a value.
# =============================================================================
import os
import json
import numpy as np
from typing import Dict, Optional, Union

from rdkit import Chem
from rdkit.Chem import Descriptors
from rdkit import RDLogger
RDLogger.DisableLog("rdApp.*")

try:
    import xgboost as xgb
    _HAS_XGB = True
except Exception:
    _HAS_XGB = False

# ---- feature spec: MUST match train_and_save_admet.py exactly ----------------
try:
    from rdkit.Chem import rdFingerprintGenerator
    _MG = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    def _fp(m):
        return np.asarray(_MG.GetFingerprintAsNumPy(m), dtype=np.float32)
except Exception:
    from rdkit.Chem import AllChem, DataStructs
    def _fp(m):
        bv = AllChem.GetMorganFingerprintAsBitVect(m, 2, nBits=2048)
        a = np.zeros((2048,), np.float32)
        DataStructs.ConvertToNumpyArray(bv, a)
        return a

_DESCS = [Descriptors.MolWt, Descriptors.MolLogP, Descriptors.TPSA, Descriptors.NumHDonors,
          Descriptors.NumHAcceptors, Descriptors.NumRotatableBonds, Descriptors.NumAromaticRings,
          Descriptors.FractionCSP3, Descriptors.HeavyAtomCount, Descriptors.NumHeteroatoms]
_NFEAT = 2048 + len(_DESCS)

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
    if mol is None:
        return np.zeros(_NFEAT, np.float32)
    try:
        d = np.array([f(mol) for f in _DESCS], np.float32)
        v = np.concatenate([_fp(mol), d])
    except Exception:
        v = np.zeros(_NFEAT, np.float32)
    return np.nan_to_num(v, nan=0.0, posinf=0.0, neginf=0.0).reshape(1, -1)


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
    """Loads saved XGBoost ADMET models and serves real, provenance-tagged
    predictions. Safe to instantiate even when no models are present."""

    def __init__(self, model_dir: Optional[str] = None):
        self.model_dir = model_dir or _default_model_dir()
        self.models: Dict[str, "xgb.XGBModel"] = {}
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
            except Exception:
                continue

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

    def predict_endpoint(self, mol_or_smiles: Union[str, "Chem.Mol"],
                         tdc_name: str) -> Optional[dict]:
        """Return a real prediction for one endpoint, or None if unavailable."""
        if tdc_name not in self.models:
            return None
        mol = (Chem.MolFromSmiles(mol_or_smiles)
               if isinstance(mol_or_smiles, str) else mol_or_smiles)
        if mol is None:
            return None
        X = _featurize_one(mol)
        m = self.meta.get(tdc_name, {})
        if m.get("task") == "regression":
            value = self._raw_predict(tdc_name, X)
            return {"task": "regression", "value": round(value, 3),
                    "metric": m.get("official_metric"), "test_score": m.get("test_score"),
                    "provenance": self._provenance(tdc_name), "app_label": m.get("app_label")}
        prob = self._raw_predict(tdc_name, X)  # binary:logistic booster -> probability
        thr = m.get("threshold") or 0.5
        return {"task": "classification", "probability": round(prob, 3),
                "threshold": thr, "positive": prob >= thr,
                "metric": m.get("official_metric"), "test_score": m.get("test_score"),
                "provenance": self._provenance(tdc_name), "app_label": m.get("app_label")}

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
            }
        return profile


# convenience singleton
_PREDICTOR: Optional[RealADMETPredictor] = None
def get_predictor() -> RealADMETPredictor:
    global _PREDICTOR
    if _PREDICTOR is None:
        _PREDICTOR = RealADMETPredictor()
    return _PREDICTOR
