"""
BioStudio — train AND SAVE real ADMET models for serving in the app.

Difference from train_admet_suite.py: that script only *benchmarks* (5-seed CV,
prints numbers, saves nothing servable). This one trains a single deployable
model per endpoint on the full non-test data, evaluates it once on the official
TDC held-out test set with the official metric, and SAVES:

  {endpoint}_xgb.json   - the trained XGBoost model (loadable via xgboost)
  {endpoint}_meta.json  - task type, official metric + value, feature spec,
                          operating threshold (clf), n_train / n_test, split

Plus a combined admet_models_manifest.json and a refreshed admet_table.md.

Every saved number is a real held-out evaluation. No fabrication, no synthetic
training data. Featurization matches train_admet_suite.py exactly so the
inference module (real_admet.py) reproduces training features bit-for-bit.

Run from the repo root (laptop CPU, free; see models/saved_models/README.md):
  uv run --python 3.11 --with setuptools --with "numpy<2" --with "rdkit>=2025.9.1" \
         --with xgboost --with scikit-learn --with pandas --with PyTDC python models/train_admet.py
"""
import os, sys, json, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "tdc_data")
MODELDIR = os.path.join(HERE, "saved_models")
os.makedirs(DATA, exist_ok=True)
os.makedirs(MODELDIR, exist_ok=True)

from rdkit import Chem
from rdkit.Chem import Descriptors
from rdkit import RDLogger
RDLogger.DisableLog("rdApp.*")

# ----- featurization: MUST match real_admet.py exactly (ECFP4 2048 + 10 desc) -----
try:
    from rdkit.Chem import rdFingerprintGenerator
    _MG = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    def _fp(m): return np.asarray(_MG.GetFingerprintAsNumPy(m), dtype=np.float32)
except Exception:
    from rdkit.Chem import AllChem, DataStructs
    def _fp(m):
        bv = AllChem.GetMorganFingerprintAsBitVect(m, 2, nBits=2048)
        a = np.zeros((2048,), np.float32); DataStructs.ConvertToNumpyArray(bv, a); return a

from rdkit.Chem import rdMolDescriptors as _rdMD

# ---------------------------------------------------------------------------
# DESCRIPTOR CHOICE IS DELIBERATE: every feature here is EXACTLY reproducible by
# RDKit.js (the WebAssembly build) so the browser recomputes bit-identical
# features and the served model returns bit-identical predictions.
#
# Continuous descriptors are deliberately excluded. Python RDKit and RDKit.js
# agree only to ~4e-5 on MolWt / MolLogP / FractionCSP3, and gradient-boosted
# trees are threshold-based: a 1e-5 difference can flip a split and visibly
# change the output. Rounding does not fix it (values land on rounding
# boundaries) -- measured 20/350 molecules mismatched at 3 decimal places.
#
# Integer topological counts have no such problem, and TPSA is a sum of fixed
# per-atom table constants, so quantizing it to hundredths is exact. Verified:
# 0 mismatches across 350 TDC test molecules for this exact feature set.
# ---------------------------------------------------------------------------
_DESC_NAMES = ["TPSA_x100", "LipinskiHBD", "LipinskiHBA", "NumRotatableBonds",
               "NumAromaticRings", "NumAliphaticRings", "NumRings", "HeavyAtomCount",
               "NumHeteroatoms", "NumAmideBonds", "NumAromaticHeterocycles",
               "NumSaturatedRings", "NumAtomStereoCenters"]
# TPSA is quantized with floor(x*100 + 0.5) -- NOT Python's round(), which is
# banker's rounding and would disagree with JavaScript's Math.round at .5 ties.
_DESCS = [lambda m: float(int(Descriptors.TPSA(m) * 100 + 0.5)),
          _rdMD.CalcNumLipinskiHBD, _rdMD.CalcNumLipinskiHBA, _rdMD.CalcNumRotatableBonds,
          _rdMD.CalcNumAromaticRings, _rdMD.CalcNumAliphaticRings, _rdMD.CalcNumRings,
          lambda m: m.GetNumHeavyAtoms(), _rdMD.CalcNumHeteroatoms, _rdMD.CalcNumAmideBonds,
          _rdMD.CalcNumAromaticHeterocycles, _rdMD.CalcNumSaturatedRings,
          _rdMD.CalcNumAtomStereoCenters]
NFEAT = 2048 + len(_DESCS)
FEATURE_SPEC = {"fingerprint": "ECFP4/Morgan radius=2 nBits=2048",
                "descriptors": _DESC_NAMES, "n_features": NFEAT,
                "browser_exact": True,
                "note": "All features are exactly reproducible by RDKit.js (WASM); verified 0/350 mismatches."}
_CACHE = {}
def featurize(smiles):
    out = []
    for sm in smiles:
        if sm in _CACHE:
            out.append(_CACHE[sm]); continue
        m = Chem.MolFromSmiles(sm)
        if m is None:
            v = np.zeros(NFEAT, np.float32)
        else:
            try:
                d = np.array([f(m) for f in _DESCS], np.float32)
                v = np.concatenate([_fp(m), d])
            except Exception:
                v = np.zeros(NFEAT, np.float32)
        v = np.nan_to_num(v, nan=0.0, posinf=0.0, neginf=0.0)
        _CACHE[sm] = v; out.append(v)
    return np.vstack(out)

# ----- endpoints. app-facing label = what the app should call it -----
# tox4 = the four the fake NeuralToxicityPredictor claimed (hepato/cardio/mutagen/carcino)
ENDPOINTS = [
    # (tdc_name, category, app_label, official_metric)
    ("DILI",               "Toxicity",    "Hepatotoxicity (DILI)",         "AUROC"),
    ("hERG",               "Toxicity",    "Cardiotoxicity (hERG)",         "AUROC"),
    ("AMES",               "Toxicity",    "Mutagenicity (Ames)",           "AUROC"),
    ("Carcinogens_Lagunin","Toxicity",    "Carcinogenicity",               "AUROC"),
    ("BBB_Martins",        "Distribution","Blood-Brain Barrier",           "AUROC"),
    ("Pgp_Broccatelli",    "Absorption",  "P-glycoprotein Inhibition",     "AUROC"),
    ("CYP3A4_Veith",       "Metabolism",  "CYP3A4 Inhibition",             "AUPRC"),
    ("Caco2_Wang",         "Absorption",  "Caco-2 Permeability",           "MAE"),
]
# allow narrowing via env: ADMET_ONLY="DILI,hERG,AMES"
_only = os.environ.get("ADMET_ONLY", "").strip()
if _only:
    keep = {x.strip() for x in _only.split(",")}
    ENDPOINTS = [e for e in ENDPOINTS if e[0] in keep]

import xgboost as xgb
from sklearn.metrics import roc_auc_score, average_precision_score, mean_absolute_error
from tdc.benchmark_group import admet_group
group = admet_group(path=DATA)

manifest = {}
table_lines = ["| Endpoint | ADMET class | Metric | Held-out test score | n_train | n_test |",
               "|---|---|---|---|---|---|"]

for tdc_name, cat, label, metric in ENDPOINTS:
    try:
        bench = group.get(tdc_name)
        test = bench["test"]
        # single deployable model: train on the full default train+valid (seed 1 split)
        train, valid = group.get_train_valid_split(benchmark=tdc_name, split_type="default", seed=1)
        tr = pd.concat([train, valid], ignore_index=True)
        ytr = tr["Y"].to_numpy()
        yte = test["Y"].to_numpy()
        is_clf = np.isin(np.unique(ytr), [0, 1]).all() and len(np.unique(ytr)) <= 2

        Xtr = featurize(tr["Drug"].tolist())
        Xte = featurize(test["Drug"].tolist())

        if is_clf:
            spw = (len(ytr) - ytr.sum()) / max(ytr.sum(), 1)
            mdl = xgb.XGBClassifier(n_estimators=600, max_depth=6, learning_rate=0.03,
                    subsample=0.8, colsample_bytree=0.8, min_child_weight=2,
                    scale_pos_weight=spw, eval_metric="auc", tree_method="hist",
                    n_jobs=0, random_state=1)
            mdl.fit(Xtr, ytr, verbose=False)
            p_te = mdl.predict_proba(Xte)[:, 1]
            if metric == "AUPRC":
                score = float(average_precision_score(yte, p_te))
            else:
                score = float(roc_auc_score(yte, p_te))
            # operating threshold: Youden's J on TRAIN preds (no test leakage)
            p_tr = mdl.predict_proba(Xtr)[:, 1]
            ts = np.linspace(0.05, 0.95, 19)
            j = [ (np.mean((p_tr >= t)[ytr == 1]) - np.mean((p_tr >= t)[ytr == 0])) for t in ts ]
            thr = float(ts[int(np.nanargmax(j))])
            score_str = f"{score:.3f} {metric}"
        else:
            mdl = xgb.XGBRegressor(n_estimators=600, max_depth=6, learning_rate=0.03,
                    subsample=0.8, colsample_bytree=0.8, min_child_weight=2,
                    eval_metric="mae", tree_method="hist", n_jobs=0, random_state=1)
            mdl.fit(Xtr, ytr, verbose=False)
            p_te = mdl.predict(Xte)
            score = float(mean_absolute_error(yte, p_te))
            thr = None
            score_str = f"{score:.3f} {metric} (lower=better)"

        mpath = os.path.join(MODELDIR, f"{tdc_name}_xgb.json")
        mdl.save_model(mpath)
        meta = {
            "tdc_name": tdc_name, "app_label": label, "admet_class": cat,
            "task": "classification" if is_clf else "regression",
            "official_metric": metric, "test_score": score,
            "threshold": thr, "n_train": int(len(ytr)), "n_test": int(len(yte)),
            "positives_frac": float(ytr.mean()) if is_clf else None,
            "split": "TDC scaffold (default, seed 1)", "feature_spec": FEATURE_SPEC,
            "model_file": os.path.basename(mpath), "source": "Therapeutics Data Commons (TDC)",
        }
        with open(os.path.join(MODELDIR, f"{tdc_name}_meta.json"), "w") as f:
            json.dump(meta, f, indent=2)
        manifest[tdc_name] = meta
        table_lines.append(f"| {label} | {cat} | {metric} | {score_str} | {len(ytr)} | {len(yte)} |")
        print(f"[OK] {label:32s} {score_str:22s}  saved -> {os.path.basename(mpath)}", flush=True)
    except Exception as e:
        print(f"[FAIL] {tdc_name}: {type(e).__name__}: {e}", flush=True)
        table_lines.append(f"| {label} | {cat} | {metric} | (failed) | - | - |")

with open(os.path.join(MODELDIR, "admet_models_manifest.json"), "w") as f:
    json.dump(manifest, f, indent=2)
with open(os.path.join(HERE, "admet_table.md"), "w") as f:
    f.write("\n".join(table_lines) + "\n")

print("\n===== BioStudio real ADMET models (XGBoost, ECFP4+desc, TDC scaffold split) =====")
print("\n".join(table_lines))
print(f"\n[save] models + meta -> {MODELDIR}")
print(f"[save] manifest -> {os.path.join(MODELDIR,'admet_models_manifest.json')}")
print(f"[save] table -> {os.path.join(HERE,'admet_table.md')}")
print("SCRIPT_DONE")
