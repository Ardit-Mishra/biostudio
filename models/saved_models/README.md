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
| Mutagenicity (Ames) | Toxicity | AUROC | 0.845 | 1457 |
| Blood–Brain Barrier | Distribution | AUROC | 0.905 | 406 |
| P-glycoprotein Inhibition | Absorption | AUROC | 0.926 | 245 |
| CYP3A4 Inhibition | Metabolism | AUPRC | 0.869 | 2467 |
| Caco-2 Permeability | Absorption | MAE ↓ | 0.339 | 182 |

These sit near published TDC leaderboard baselines. They are an honest classical-ML baseline, not a
claim of state-of-the-art; small datasets (e.g. DILI) carry real variance.

## Reproduce

From the repo root, with [`uv`](https://docs.astral.sh/uv/):

```bash
uv run --python 3.11 --with setuptools --with "numpy<2" --with "rdkit>=2025.9.1" \
       --with xgboost --with scikit-learn --with pandas --with PyTDC \
       python models/train_admet.py
```

This re-downloads the TDC data, retrains every endpoint, and rewrites the `*_xgb.json` / `*_meta.json`
files here plus `admet_models_manifest.json`. Training is CPU-only and finishes in a few minutes.

> Note: `setuptools` is required because some dependencies import `pkg_resources`.
