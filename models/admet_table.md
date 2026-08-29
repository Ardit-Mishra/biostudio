| Endpoint | ADMET class | Metric | Held-out test score | n_train | n_test |
|---|---|---|---|---|---|
| Hepatotoxicity (DILI) | Toxicity | AUROC | 0.925 AUROC | 379 | 96 |
| Cardiotoxicity (hERG) | Toxicity | AUROC | 0.809 AUROC | 523 | 132 |
| Mutagenicity (Ames) | Toxicity | AUROC | 0.845 AUROC ⚠ regression | 5821 | 1457 |
| Carcinogenicity | Toxicity | AUROC | (failed) | - | - |
| Blood-Brain Barrier | Distribution | AUROC | 0.905 AUROC | 1624 | 406 |
| P-glycoprotein Inhibition | Absorption | AUROC | 0.926 AUROC | 973 | 245 |
| CYP3A4 Inhibition | Metabolism | AUPRC | 0.869 AUPRC | 9861 | 2467 |
| Caco-2 Permeability | Absorption | MAE | 0.339 MAE (lower=better) ⚠ regression | 728 | 182 |

⚠ AMES and Caco-2 Permeability regressed vs. the prior per-endpoint model set (AMES: 0.847→0.845
AUROC, within noise; Caco-2: 0.286→0.339 MAE, a real +0.053 increase in error since MAE is
lower-is-better). Shipped anyway as part of one consistent, single-script-trained batch — see
`models/saved_models/README.md` for the full before/after and `models/real_admet.py` for a
feature-mismatch serving bug this retrain also fixed.
