# ADMET Models — provenance & reproduction

These are the **real, held-out-validated** models the app serves (via
[`models/real_admet.py`](../real_admet.py)). They are not placeholders: each was trained on public
data with a leakage-resistant split and evaluated once on a held-out test set.

## What's here

| File | Contents |
|---|---|
| `{endpoint}_xgb.json` | A trained XGBoost model (native `Booster` format, loadable with `xgboost`). |
| `{endpoint}_meta.json` | Task type, official metric + held-out score, operating threshold, feature spec, train/test sizes, data source. |
| `admet_models_manifest.json` | All endpoints aggregated (the file the app reads to enumerate models). |

## How they were made

- **Data:** [Therapeutics Data Commons (TDC)](https://tdcommons.ai/) ADMET Benchmark Group — public,
  standardized datasets and splits.
- **Split:** Bemis–Murcko **scaffold split** (train+valid vs. held-out test), so structurally similar
  molecules don't leak across the split. This is the standard that prevents the inflated "random-split"
  numbers common in cheminformatics.
- **Features:** ECFP4/Morgan fingerprint (2048 bits, radius 2) + 10 RDKit physicochemical descriptors.
- **Model:** gradient-boosted trees (XGBoost), one per endpoint, classifier or regressor per task.
- **Reporting:** each score is a **single held-out test evaluation** with the dataset's official metric.
  No synthetic data, no fabricated numbers.

## Held-out test performance

| Endpoint | ADMET class | Metric | Held-out test | n_test |
|---|---|---|---|---|
| Hepatotoxicity (DILI) | Toxicity | AUROC | 0.925 | 96 (small → higher variance) |
| Cardiotoxicity (hERG) | Toxicity | AUROC | 0.809 | 132 |
| Mutagenicity (Ames) | Toxicity | AUROC | 0.845 ⚠ | 1457 |
| Blood-Brain Barrier | Distribution | AUROC | 0.905 | 406 |
| P-glycoprotein Inhibition | Absorption | AUROC | 0.926 | 245 |
| CYP3A4 Inhibition | Metabolism | AUPRC | 0.869 | 2467 |
| Caco-2 Permeability | Absorption | MAE ↓ | 0.339 ⚠ | 182 |

These sit near published TDC leaderboard baselines. They are an honest classical-ML baseline, not a
claim of state-of-the-art; small datasets (e.g. DILI) carry real variance.

**⚠ Two honest regressions, shipped anyway.** These models were retrained as one consistent batch
(same feature spec, same script) on 2026-08-29, replacing an earlier per-endpoint set. Five of seven
endpoints improved (DILI +0.077, Pgp +0.019, hERG +0.031, CYP3A4 +0.001, BBB +0.0003 AUROC/AUPRC).
Two regressed and are disclosed rather than hidden:
- **AMES**: 0.847 → 0.845 AUROC (−0.0015, within noise for a 1,457-molecule test set).
- **Caco-2 Permeability**: 0.286 → 0.339 MAE (**worse** — MAE is lower-is-better, so this is a real
  +0.053 increase in mean absolute error, not an improvement). Shipped for consistency with the rest
  of the batch and because the previous Caco-2 model's advertised 0.286 MAE was never actually what
  the app served — see the serving-bug note in `models/real_admet.py`.

## Reproduce

The canonical training script lives in the separate `ml-training` repo, not here — this app repo
only ships the trained artifacts. (An earlier, diverged copy briefly lived at
`models/train_admet.py`; it used a different, since-superseded 13-descriptor feature spec and was
removed 2026-08-29 so there is exactly one script that can produce these files, not two silently
drifting apart.)

From `ml-training/biostudio/`, with [`uv`](https://docs.astral.sh/uv/):

```bash
uv run --python 3.11 --with "numpy<2" --with "rdkit>=2025.9.1" --with xgboost \
       --with scikit-learn --with pandas --with PyTDC --with mlflow-skinny \
       python train_and_save_admet.py
```

This re-downloads the TDC data, retrains every endpoint, rewrites the `*_xgb.json` / `*_meta.json`
files there plus `admet_models_manifest.json`, and logs a full MLflow run per endpoint (git SHA,
dataset fingerprint, split, seed, params, train time, the official metric, every relevant library's
version) to a local sqlite store — see `ml-training/biostudio/mlflow.db` /
`ml-training/_shared/mlflow_utils.py`. Training is CPU-only and finishes in well under a minute.
Copy the refreshed `*_meta.json` + `admet_models_manifest.json` (and `*_xgb.json` if the numbers
actually changed) into this directory to ship an update.

Verified 2026-08-29: re-running this script reproduced every one of the 7 shipped models
**byte-for-byte identical** (`sha256sum` match on every `*_xgb.json`) and every held-out score to
full floating-point precision — the `*_meta.json` files here now carry the git SHA, library
versions, dataset fingerprint, and MLflow run ID from that verification run.
