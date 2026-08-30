# ADMET Models — provenance & reproduction

These are the **real, held-out-validated** models the app serves (via
[`models/real_admet.py`](../real_admet.py)). They are not placeholders: each was trained on public
data with a leakage-resistant split and evaluated once on a held-out test set.

Three models are trained and scored per endpoint — **XGBoost, RandomForest, and an
MLPClassifier/Regressor** — on the identical split and identical features. XGBoost is what the app
serves (consistency across all seven endpoints, and it is the fastest at inference); the other two
are not decorative benchmarks run once and forgotten — they are shipped, loadable, and evaluated
every retrain, so "XGBoost wins" is a checked claim. It does not always win: RandomForest scores
higher on 3 of 7 endpoints below.

## What's here

| File | Contents |
|---|---|
| `{endpoint}_xgb.json` | The served XGBoost model (native `Booster` format, loadable with `xgboost`). |
| `{endpoint}_rf.joblib` | A scikit-learn `Pipeline` (median imputer + `RandomForestClassifier`/`Regressor`). |
| `{endpoint}_mlp.joblib` | A scikit-learn `Pipeline` (median imputer + standard scaler + `MLPClassifier`/`Regressor`). |
| `{endpoint}_shap.json` | Global SHAP feature importance for the XGBoost model (mean \|SHAP\| over the held-out test set, top 20 features), computed with the `shap` package during training. |
| `{endpoint}_meta.json` | Task type, official metric + held-out score for all three models, operating threshold, feature spec, train/test sizes, data source, SHAP top features. |
| `admet_models_manifest.json` | All endpoints aggregated (the file the app reads to enumerate models). |
| `descriptor_failures.json` | Every RDKit descriptor that raised for any molecule during training, if any (see "Featurization" below). Empty for this run. |

## How they were made

- **Data:** [Therapeutics Data Commons (TDC)](https://tdcommons.ai/) ADMET Benchmark Group — public,
  standardized datasets and splits.
- **Split:** Bemis–Murcko **scaffold split** (train+valid vs. held-out test), so structurally similar
  molecules don't leak across the split. This is the standard that prevents the inflated "random-split"
  numbers common in cheminformatics.
- **Features:** ECFP4/Morgan fingerprint (2048 bits, radius 2) + **217 RDKit descriptors** — the
  full `rdkit.Chem.Descriptors._descList` set (name-sorted for a stable column order), not a curated
  subset. Computed by [`models/descriptors.py`](../descriptors.py), kept byte-identical to
  `ml-training/biostudio/descriptors.py` (a separate repo) so training and serving compute the same
  numbers for the same molecule.
- **Featurization failures:** a descriptor that raises for a specific molecule (rare — e.g. the
  `BCUT2D_*` descriptors need Gasteiger partial charges that don't converge on some structures) gets
  `NaN` in its slot and is logged to `descriptor_failures.json`, never silently replaced with `0.0`.
  XGBoost treats `NaN` as its native "missing" value; RandomForest/MLP require it be imputed
  (median, fit on train only) since scikit-learn doesn't accept `NaN` natively — see
  `train_and_save_admet.py` for exactly where that happens.
- **Models:** XGBoost, RandomForest, and MLPClassifier/Regressor, each trained on the same
  train+valid split and the same features. Classifier vs. regressor per task.
- **Reporting:** each score is a **single held-out test evaluation** with the dataset's official
  metric. No synthetic data, no fabricated numbers.

## Held-out test performance — evaluated, not assumed

| Endpoint | ADMET class | Metric | XGBoost (served) | Random Forest | MLP | Best of 3 | n_test |
|---|---|---|---|---|---|---|---|
| Hepatotoxicity (DILI) | Toxicity | AUROC | 0.920 | 0.940 | 0.804 | Random Forest | 96 (small → higher variance) |
| Cardiotoxicity (hERG) | Toxicity | AUROC | 0.824 | 0.867 | 0.849 | Random Forest | 132 |
| Mutagenicity (Ames) | Toxicity | AUROC | 0.866 | 0.850 | 0.818 | XGBoost | 1457 |
| Blood-Brain Barrier | Distribution | AUROC | 0.900 | 0.914 | 0.879 | Random Forest | 406 |
| P-glycoprotein Inhibition | Absorption | AUROC | 0.927 | 0.919 | 0.909 | XGBoost | 245 |
| CYP3A4 Inhibition | Metabolism | AUPRC | 0.880 | 0.853 | 0.855 | XGBoost | 2467 |
| Caco-2 Permeability | Absorption | MAE ↓ | 0.272 | 0.292 | 1.152 | XGBoost | 182 |

"Best of 3" is the highest-scoring model on that endpoint's held-out test set (lowest for Caco-2's
MAE, where lower is better). RandomForest wins 3 of 7 (DILI, hERG, BBB); XGBoost wins the other 4.
MLP does not win any endpoint here, and on Caco-2 it is badly overfit relative to the other two
(MAE 1.152 vs. XGBoost's 0.272 on a 728-molecule training set with 2265 features) — reported as-is
rather than dropped, because "evaluated, not assumed" includes reporting the loss, not just the
win. XGBoost remains the served model on every endpoint for consistency, not because it always wins.

These sit near published TDC leaderboard baselines. They are an honest classical-ML baseline, not a
claim of state-of-the-art; small datasets (e.g. DILI) carry real variance.

**Retrained 2026-08-30** with the full 217-descriptor feature set (previously 10) — see
"Featurization" above. XGBoost's held-out scores shifted versus the previous 10-descriptor batch:
DILI 0.925→0.920 (−0.005), hERG 0.809→0.824 (+0.015), Ames 0.845→0.866 (+0.021),
BBB 0.905→0.900 (−0.005), P-gp 0.926→0.927 (+0.001), CYP3A4 0.869→0.880 (+0.011),
Caco-2 0.339→0.272 MAE (**improvement** — MAE is lower-is-better, so this is a real reduction in
mean absolute error). Two endpoints (DILI, BBB) regressed very slightly with more features; disclosed
rather than hidden, consistent with this repo's practice.

## SHAP: real per-prediction feature attribution

`models/real_admet.py`'s `explain_endpoint()` returns exact Tree SHAP feature attributions for the
served XGBoost model, computed via `Booster.predict(pred_contribs=True)` — XGBoost's own C++
implementation of the same Tree SHAP algorithm the `shap` package's `TreeExplainer` implements, run
directly rather than through `shap`'s Python model-dump parser. That parser cannot read the
`base_score` field xgboost ≥2.2 writes to the model dump (a bracketed scientific-notation string
like `"[5E-1]"`) — confirmed reproducible with `shap==0.49.1` + `xgboost==3.4.1`:
`ValueError: could not convert string to float: '[5E-1]'`, on both the sklearn wrapper and a plain
loaded `Booster`. Using xgboost's native `pred_contribs` sidesteps the incompatibility entirely and
adds no runtime dependency on `shap` in the serving app.

The `shap` package genuinely is used at training time (pinned to `xgboost==2.1.4`, where the same
parser works) to compute each `{endpoint}_shap.json` — the *global* feature-importance ranking
(mean \|SHAP\| over the held-out test set), which is a different, complementary view from the
*per-prediction* explanation `explain_endpoint()` serves live. Surfaced in the app's
**Explainability Canvas → ML Model Explainability (SHAP)** tab.

## Reproduce

The canonical training script lives in the separate `ml-training` repo, not here — this app repo
only ships the trained artifacts.

From `ml-training/biostudio/`, with [`uv`](https://docs.astral.sh/uv/):

```bash
uv run --python 3.12 --with "numpy<2" --with "rdkit>=2025.9.1" --with "xgboost==2.1.4" \
       --with scikit-learn --with pandas --with PyTDC --with shap --with joblib \
       --with mlflow-skinny --with sqlalchemy --with alembic \
       python train_and_save_admet.py
```

`xgboost==2.1.4` is pinned for **this training run only** (not for serving — this app's
`requirements.txt` still targets `xgboost>=3.1.1`): `shap` 0.49.1's model-dump parser cannot read
the `base_score` format xgboost ≥2.2 writes (see "SHAP" above). The saved artifact is unaffected —
models are saved via the native `Booster.save_model()`, and that JSON format is forward-compatible
(verified: a model trained and saved with xgboost 2.1.4 loads and predicts byte-identical output
under xgboost 3.4.1, what this app actually serves with).

This re-downloads the TDC data, retrains every endpoint (XGBoost + RandomForest + MLP), rewrites
`*_xgb.json` / `*_rf.joblib` / `*_mlp.joblib` / `*_shap.json` / `*_meta.json` plus
`admet_models_manifest.json`, and logs a full MLflow run per endpoint (git SHA, dataset fingerprint,
split, seed, params, train time, every model's metric, every relevant library's version) to a local
sqlite store — see `ml-training/biostudio/mlflow.db` / `ml-training/_shared/mlflow_utils.py`.
Featurizing all 7 endpoints' ~25k molecules against 217 descriptors plus training all three model
types took several minutes on a laptop CPU (not "well under a minute" like the smaller 10-descriptor
batch this replaces — the RF/MLP tier and the larger feature set both add real time).
`{endpoint}_rf.joblib` files are saved with `compress=3` (CYP3A4_Veith's RandomForest was 54MB
uncompressed, 12MB compressed — `compress=9` was tested and barely improved on that for ~60x the
write time). Copy the refreshed files into this directory to ship an update.
