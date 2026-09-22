# What was tried, what won, what is still unknown

Most of the work on this project is not visible in the code that shipped. Models
were trained and then not used; a benchmark was run, superseded, and partly lost;
an earlier version claimed things it had not measured. This file is the record.

Every number here comes from a file in the training repository. Where a number
cannot be sourced, it says so rather than being rounded into existence.

---

## The problem this project started with

The first version of BioStudio presented a **random-weight "neural network"** and
a **synthetic-data ensemble** as toxicity predictions, and advertised "200+
molecular descriptors" that were about **30 real descriptors padded with roughly
170 literal zeros**.

The rebuild was authored on 2026-08-24 with one governing rule:

> Real data, correct splits, true numbers … never a fabricated table (this is
> exactly what the old code did).

Everything below follows from that.

## Property prediction — what shipped

Seven ADMET endpoints on Therapeutics Data Commons benchmarks under a
Bemis-Murcko scaffold split. Features are **217 real RDKit descriptors plus ECFP4
fingerprints**, 2,265 in total. Three model families are trained on *identical*
splits and reported together:

| Endpoint | Metric | XGBoost | Random Forest | MLP | n train / test |
|---|---|---:|---:|---:|---:|
| Hepatotoxicity (DILI) | AUROC | 0.920 | **0.940** | 0.804 | 379 / 96 |
| Cardiotoxicity (hERG) | AUROC | 0.824 | **0.867** | 0.849 | 523 / 132 |
| Mutagenicity (Ames) | AUROC | **0.866** | 0.850 | 0.818 | 5,821 / 1,457 |
| Blood-brain barrier | AUROC | 0.900 | **0.914** | 0.879 | 1,624 / 406 |
| P-glycoprotein inhibition | AUROC | **0.927** | 0.919 | 0.909 | 973 / 245 |
| CYP3A4 inhibition | AUPRC | **0.880** | 0.853 | 0.855 | 9,861 / 2,467 |
| Caco-2 permeability | MAE (lower better) | **0.272** | 0.292 | 1.152 | 728 / 182 |
| Carcinogenicity | — | unavailable | unavailable | unavailable | — |

**Random Forest wins three of the seven and XGBoost is still the model served.**
That is a real inconsistency and there is no recorded rationale for it in the
training repository. It is written down here rather than hidden by reporting only
the served model's column.

**Carcinogenicity is shown as unavailable, not estimated.** The endpoint errors
out — `('carcinogens_lagunin', 'does not match to available values')` — and an
eighth number invented to fill the row would be precisely the failure this
rebuild exists to remove.

**"Ensemble" would be the wrong word.** Three estimators are trained and saved
separately. Nothing combines their outputs.

## What was trained and did not ship

Two deep-learning families were trained on the same endpoints, with the official
test set, three seeds each:

| Endpoint | ChemBERTa-LoRA | Chemprop D-MPNN | Served XGBoost |
|---|---:|---:|---:|
| Blood-brain barrier | 0.8818 ± 0.0067 | 0.8465 ± 0.0247 | 0.900 |
| Cardiotoxicity (hERG) | 0.7829 ± 0.0080 | 0.6988 ± 0.0025 | 0.824 |
| Mutagenicity (Ames) | 0.8163 ± 0.0049 | 0.8180 ± 0.0133 | 0.866 |
| Hepatotoxicity (DILI) | 0.8733 ± 0.0215 | 0.8604 ± 0.0357 | 0.920 |

Neither beat the gradient-boosted baseline on any of the four. They were built as
a check on the assumption that a bigger model would obviously be better, and the
answer was no. The scripts write metrics but persist no deployable weights, so
nothing was ever a candidate for serving.

The honest caveat: the XGBoost column is fit on merged train+validation data
while these are not, so this is not a strictly matched comparison. It is enough
to say the deep models did not clear the bar; it is not enough to quantify by
how much.

## Problems hit, and what was done

**Training succeeded and scoring crashed.** `AttributeError: 'ValueError' object
has no attribute 'values'` — the benchmark helper requires exactly five seeds.
Metrics are now computed directly per seed.

**RDKit crashed on import.** `_ARRAY_API not found` — the wheel is compiled
against NumPy 1.x while the data library pulled 2.x. Pinned `numpy<2`.

**SHAP could not read the saved models.** `could not convert string to float:
'[5E-1]'` — a serialization incompatibility between the XGBoost sklearn wrapper
and SHAP. Models are saved through the native booster instead; predictions load
byte-identically under the serving version.

**MLflow would not start.** A protobuf import failure and a filesystem-store
write restriction. Replaced with `mlflow-skinny` over SQLite.

**A descriptor returning NaN or inf was silently coerced to 0.0.** Caught in
review and fixed: the substitution is now recorded with the molecule, the
descriptor and the reason. Note the limit — *the fix logs the substitution, it
does not eliminate it.*

## What is still unknown

- The original twelve-endpoint, five-seed benchmark cannot be reconstructed. Five
  numbers survive in a planning document as claims, not as a reproducible table.
- No calibration or applicability-domain study was completed, though both were
  planned.
- Operating thresholds are computed from training predictions; there is no
  independent evidence for them.
- DILI's test set is 96 molecules. Single-split differences of a few points on a
  set that size should not be read as a ranking, and no confidence intervals
  accompany the table.
- The deep-learning result JSONs omit device, epochs and library versions.

## Scope

This is research-use software for exploring published benchmark data. It is not
a substitute for laboratory assays, and no output here is a clinical or
regulatory claim.
