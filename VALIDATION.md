# Model Validation & Performance

Comprehensive documentation of validation approaches, benchmarks, performance metrics, and limitations for **BioStudio** predictive models.

---

## Table of Contents

1. [Validation Philosophy](#validation-philosophy)
2. [Model Categories](#model-categories)
3. [Drug-Likeness Metrics](#drug-likeness-metrics)
4. [ADME/PK Predictions](#admepk-predictions)
5. [Toxicity Predictions](#toxicity-predictions)
6. [Target Class Predictions](#target-class-predictions)
7. [Machine Learning Models](#machine-learning-models)
8. [Limitations & Disclaimers](#limitations--disclaimers)
9. [Future Validation Plans](#future-validation-plans)

---

## Validation Philosophy

### Educational vs. Production Models

This platform demonstrates computational drug discovery workflows with **varying levels of validation**:

| Model Type | Validation Status | Production Ready? |
|-----------|------------------|-------------------|
| Real ADMET Models (XGBoost, 7 endpoints) | ✅ **Validated** - Held-out TDC scaffold-split test scores | Research/educational screening only — no prospective, external or assay validation |
| Drug-Likeness (Lipinski, Veber, QED, SA) | ✅ **Validated** - Standard industry metrics | Established deterministic calculations — not clinical or regulatory decision support |
| Neural Network Toxicity Predictor | ❌ **NOT TRAINED** - frozen random weights (`np.random.randn`), no learning ever occurred | Deprecated/removed |
| Protein-Ligand Compatibility | ⛔ **Disabled** - untrained random-weight demo (never fitted to any data) | No |
| ADME/PK Heuristics | ⚠️ **Heuristic** - Rule-based scoring | No |
| Toxicity Heuristics | ⚠️ **Heuristic** - Structural alerts | No |
| Target Class Heuristics | ⚠️ **Heuristic** - Descriptor thresholds | No |

### Key Principles

1. **Transparency**: Clear distinction between validated and heuristic models
2. **Honesty**: Explicit documentation of limitations
3. **Scientific Rigor**: All methods grounded in published research
4. **Reproducibility**: Complete methodology documented for replication

---

## Model Categories

### Category 0: Real Validated ML (XGBoost) ✅

Seven ADMET endpoints, trained and held-out-tested on **Therapeutics Data Commons (TDC)** scaffold splits (seed 1). Served by `models/real_admet.py` (`RealADMETPredictor.comprehensive_toxicity_profile()`); metrics in `models/saved_models/admet_models_manifest.json`.

**What is served, and what else was trained.** The **XGBoost** model is the one served for every endpoint, and the table below reports its held-out scores. A **RandomForest** and an **MLP** were also trained for each endpoint on the identical task, split and features, and scored the same way — they are genuine trained comparators, not heuristics and not placeholders. Their artifacts ship alongside (`*_rf.joblib`, `*_mlp.joblib`) and the app surfaces the comparison. Keeping them is what makes "XGBoost was chosen" a checked claim rather than an assumed one; RandomForest in fact scores higher on some endpoints.

These trained models are distinct from the platform's rule-based heuristic modules, which were never fitted to data and carry no held-out metrics — see Categories 2 and 3 below.

<!-- ADMET-METRICS:START -->
| Endpoint | Task | Class | Metric | Better | Score | Threshold | n_train | n_test |
|---|---|---|---|---|---|---|---|---|
| `DILI` | Hepatotoxicity (DILI) | Toxicity | AUROC | higher | **0.920** | 0.20 | 379 | 96 |
| `hERG` | Cardiotoxicity (hERG) | Toxicity | AUROC | higher | **0.824** | 0.40 | 523 | 132 |
| `AMES` | Mutagenicity (Ames) | Toxicity | AUROC | higher | **0.866** | 0.45 | 5821 | 1457 |
| `BBB_Martins` | Blood-Brain Barrier | Distribution | AUROC | higher | **0.900** | 0.45 | 1624 | 406 |
| `Pgp_Broccatelli` | P-glycoprotein Inhibition | Absorption | AUROC | higher | **0.927** | 0.35 | 973 | 245 |
| `CYP3A4_Veith` | CYP3A4 Inhibition | Metabolism | AUPRC | higher | **0.880** | 0.55 | 9861 | 2467 |
| `Caco2_Wang` | Caco-2 Permeability | Absorption | MAE | lower | **0.272** | n/a | 728 | 182 |
<!-- ADMET-METRICS:END -->

**Features** — identical across all seven endpoints, generated from the manifest:

<!-- ADMET-FEATURES:START -->
| Component | Count |
|---|---|
| ECFP4/Morgan radius=2 nBits=2048 | 2,048 |
| RDKit descriptors | 217 |
| **Total features per molecule** | **2,265** |
<!-- ADMET-FEATURES:END -->

**Production Ready**: **No.** These are real held-out test metrics rather than training-set numbers, which makes them honest — not sufficient. Each figure comes from a single TDC scaffold split with no prospective, external, or assay validation, and several endpoints have small test sets (hERG n=132, DILI n=96). Suitable for research and educational screening and for ranking candidates; **not** suitable for production or regulatory decisions. This matches the scope stated in [README.md](README.md).

**Generations.** The table above is generated from
`models/saved_models/admet_models_manifest.json` and verified against it by
`tests/test_docs_metrics.py`. Two earlier generations are **historical and are not current
shipped performance**: a per-endpoint set, and a 2026-08-29 batch retrain that this document
previously presented as current. Its thresholds also differed from the shipped ones. For the
per-generation comparison see `models/saved_models/README.md`.

### Category 1: Validated Industry Standards ✅

**Drug-likeness metrics** (Lipinski, Veber, QED, SA) are well-established, peer-reviewed methods used in pharmaceutical industry.

**Validation**: Decades of pharmaceutical research  
**Status**: Established deterministic calculations — the formulas are standard and reproduce the
published definitions exactly. **Not clinical or regulatory decision support**: a correct Lipinski
or QED value is a property of the molecule, not a judgement about whether a compound should be
advanced.

**Confidence**: High in the calculation; the interpretation remains the reader's.

### Category 2: Deprecated/Never-Trained Modules ❌⚠️

**Neural toxicity** (`models/neural_toxicity.py`) was **never trained at all** — weights are set once via `np.random.randn() * 0.01` and no optimizer/`.fit()` ever runs. It is deprecated in favor of the real XGBoost models in Category 0. **Protein-ligand compatibility** is a separate educational implementation showing ML architecture (not covered by the real-model rebuild).

**Validation**: `neural_toxicity.py` — none, never trained. `protein_ligand_compatibility.py` — none; its weights are one-shot random noise (`np.random.randn()*0.01`), never fitted to any dataset. Both are deprecated/disabled.  
**Production Ready**: No  
**Confidence**: None (neural_toxicity) / Low, demonstration only (protein-ligand compatibility)

### Category 3: Heuristic Scoring Functions ⚠️

**ADME/PK**, **toxicity alerts**, and **target class** predictions use descriptor-based heuristics.

**Validation**: Based on literature correlations  
**Production Ready**: No  
**Confidence**: Medium - useful for screening, not decision-making

---

## Drug-Likeness Metrics

### Lipinski Rule of 5

**Status**: ✅ **Validated**

**Method**: Count violations of four criteria:
- Molecular weight ≤ 500 Da
- LogP ≤ 5
- H-bond donors ≤ 5
- H-bond acceptors ≤ 10

**Validation**:
- **Original Dataset**: 2,245 drugs from World Drug Index [1]
- **Success Rate**: ~90% of oral drugs comply
- **Industry Adoption**: Universal standard since 1997

**Performance**:
- Sensitivity: ~90% (correctly identifies drug-like molecules)
- Specificity: ~85% (correctly rejects non-drug-like molecules)
- False Positives: Natural products, biologics

**Limitations**:
- Does not apply to biologics, antibiotics, natural products
- Not a predictor of success, only drug-likeness

**References**:
[1] Lipinski et al. (2001). Adv Drug Deliv Rev, 46(1-3):3-26. DOI: 10.1016/S0169-409X(00)00129-0

---

### Veber Rules

**Status**: ✅ **Validated**

**Method**: Two criteria for oral bioavailability:
- Rotatable bonds ≤ 10
- TPSA ≤ 140 Ų

**Validation**:
- **Dataset**: 1,100 compounds from Abbott Laboratories
- **Correlation with Bioavailability**: R² = 0.68
- **Rat Model**: >80% accuracy predicting oral bioavailability

**Performance**:
- Precision: ~75% for bioavailability prediction
- Combined with Lipinski: ~85% accuracy

**References**:
[2] Veber et al. (2002). J Med Chem, 45(12):2615-23. DOI: 10.1021/jm020017n

---

### QED (Quantitative Estimate of Drug-likeness)

**Status**: ✅ **Validated**

**Method**: Weighted product of 8 molecular properties normalized to [0,1]

**Validation**:
- **Training Set**: 771 drugs from ChEMBL
- **Distribution Analysis**: Drugs vs. non-drugs
- **Benchmark**: AUC = 0.89 discriminating drugs from random molecules

**Performance**:
- QED > 0.67: High drug-likeness (top 25% of marketed drugs)
- QED 0.49-0.67: Moderate drug-likeness
- QED < 0.49: Low drug-likeness

**Limitations**:
- Biased toward oral drugs
- Not predictive of clinical success

**References**:
[3] Bickerton et al. (2012). Nat Chem, 4(2):90-8. DOI: 10.1038/nchem.1243

---

### Synthetic Accessibility (SA) Score

**Status**: ✅ **Validated**

**Method**: Complexity score based on fragment contributions and molecular complexity

**Validation**:
- **Training**: 1 million molecules from PubChem
- **Expert Agreement**: 71% correlation with medicinal chemist ratings
- **Range**: 1 (easy) to 10 (very difficult)

**Performance**:
- SA ≤ 3: Easily synthesizable (~80% success rate)
- SA 3-6: Moderate difficulty (~50% success rate)
- SA > 6: Challenging synthesis (<30% success rate)

**Limitations**:
- Doesn't account for retrosynthetic routes
- Heuristic, not synthesis planner

**References**:
[4] Ertl & Schuffenhauer (2009). J Cheminform, 1:8. DOI: 10.1186/1758-2946-1-8

---

## ADME/PK Predictions

### LogP (Lipophilicity)

**Status**: ⚠️ **Heuristic**

**Method**: Wildman-Crippen method (RDKit implementation)

**Current Implementation**:
```python
logp = Descriptors.MolLogP(mol)
# Expected accuracy: ±0.5 log units
```

**Performance** (Literature):
- **RMSE**: 0.5-0.7 log units
- **R²**: 0.85-0.90 on benchmark datasets

**Limitations**:
- No ionization correction for pH
- Less accurate for highly polar compounds
- No solvent effect modeling

**Production Alternative**:
- Trained QSAR models (e.g., ALogP, XLogP3)
- COSMO-RS calculations for accuracy

---

### Caco-2 Permeability

**Status**: ⚠️ **Heuristic**

**Method**: Descriptor-based heuristic using MW, LogP, HBD, TPSA

**Current Implementation**:
```python
# Scoring function based on Lipinski/Veber correlations
# NOT a validated QSAR model
```

**Expected Performance** (If Replaced with QSAR):
- **R²**: 0.70-0.80 on Caco-2 datasets
- **RMSE**: 0.4-0.5 log units

**Limitations**:
- Heuristic, not data-driven
- No active transport modeling
- No efflux consideration

**Production Alternative**:
- QSAR models trained on Caco-2 data (n≥500 compounds)
- In silico ADME platforms (e.g., ADMET Predictor, VolSurf)

---

### Blood-Brain Barrier (BBB) Penetration

**Status**: ⚠️ **Heuristic**

**Method**: Rule-based on MW (<450), TPSA (<90), and LogP (2-5)

**Current Implementation**:
```python
# Binary classification based on property cutoffs
# Inspired by published correlations
```

**Expected Performance** (Literature):
- **Accuracy**: 80-85% for BBB+ classification
- **Sensitivity**: 75-80%
- **Specificity**: 80-85%

**Limitations**:
- No P-glycoprotein efflux modeling
- No brain tissue binding consideration
- Binary only (no quantitative BBB ratio)

**Production Alternative**:
- Trained classifiers on CNS drugs dataset
- Include efflux transporter predictions

---

### CYP450 Metabolism

**Status**: ⚠️ **Heuristic**

**Method**: Structural alerts for CYP substrates/inhibitors

**Current Implementation**:
```python
# Pattern matching for common metabolic sites
# Based on literature SMARTs patterns
```

**Expected Performance** (If Replaced with QSAR):
- **Accuracy**: 75-85% for major CYP isoforms
- **AUC**: 0.80-0.90 for 3A4, 2D6, 2C9

**Limitations**:
- No quantitative Ki/Km values
- Isoform-specific alerts incomplete
- No metabolite prediction

**Production Alternative**:
- Multi-task DNN trained on CYP inhibition data
- QSAR models per CYP isoform

---

## Toxicity Predictions

### Hepatotoxicity

**Status**: ⚠️ **Heuristic (Structural Alerts)** + ✅ **Real XGBoost (DILI)** — legacy "Neural Network" module deprecated, never trained. Current DILI metric and threshold: see the generated table in Category 0.

#### Heuristic Approach

**Method**: Structural alerts based on known hepatotoxins

**Current Implementation**:
- Reactive metabolite formation (quinones, epoxides)
- Mitochondrial toxicity patterns
- Cholestasis-inducing structures

**Expected Performance** (Literature):
- **Sensitivity**: 60-70% (high false negatives)
- **Specificity**: 70-80%
- **PPV**: ~50% (many false positives)

#### Neural Network Approach — NOT TRAINED, deprecated

**Status**: ❌ **NOT TRAINED** — `models/neural_toxicity.py` sets weights via `np.random.randn() * 0.01` once at initialization and never runs an optimizer or `.fit()`. No learning ever occurred; "5-layer feedforward network" describes an untrained, frozen-random-weight architecture, not a working model.

**Real alternative**: DILI (hepatotoxicity) has a real, held-out-validated XGBoost model on a TDC scaffold split. Its current AUROC, threshold and test-set size are in the generated table in Category 0 above; see also `models/real_admet.py`.

---

### hERG Cardiotoxicity

**Status**: ⚠️ **Heuristic** + ✅ **Real XGBoost (hERG)** — legacy "Neural Network" module deprecated, never trained. Current hERG metric and threshold: see the generated table in Category 0.

#### Heuristic Approach

**Method**: Structural features associated with hERG binding

**Known Correlations** (Literature):
- Basic nitrogen (pKa > 7)
- Large hydrophobic regions
- Aromatic rings
- Molecular flexibility

**Expected Performance** (Literature):
- **Accuracy**: 70-80%
- **AUC**: 0.75-0.85 for binary classification

#### Neural Network — NOT TRAINED, deprecated

**Status**: ❌ **NOT TRAINED** — fixed random weights (`np.random.randn`), no `fit`/backprop ever run. Module deprecated.

**Real alternative**: Real, held-out-validated XGBoost model for hERG on a TDC scaffold split. Its current AUROC, threshold and test-set size are in the generated table in Category 0 above; see also `models/real_admet.py`.

---

### Mutagenicity (Ames Test)

**Status**: ⚠️ **Heuristic** + ✅ **Real XGBoost (Ames)** — legacy "Neural Network" module deprecated, never trained. Current Ames metric and threshold: see the generated table in Category 0.

#### Heuristic Approach

**Method**: Ashby-Tennant structural alerts (50+ patterns)

**Validation** (Literature):
- **Sensitivity**: 50-60% (Derek, MultiCASE systems)
- **Specificity**: 80-90%
- **False Negatives**: Common for pro-mutagens

#### Neural Network — NOT TRAINED, deprecated

**Status**: ❌ **NOT TRAINED** — fixed random weights (`np.random.randn`), no `fit`/backprop ever run. Module deprecated.

**Real alternative**: Real, held-out-validated XGBoost model for Ames mutagenicity on a TDC scaffold split. Its current AUROC, threshold and test-set size are in the generated table in Category 0 above; see also `models/real_admet.py`.

**References**:
[5] Kazius et al. (2005). J Med Chem, 48(1):312-20. DOI: 10.1021/jm040835a

---

### Carcinogenicity

**Status**: ⚠️ **Heuristic only**. A "Neural Network" carcinogenicity predictor was previously listed here, but `models/neural_toxicity.py` was **NOT TRAINED** (fixed random weights, `np.random.randn`, no `fit`/backprop ever run) and is deprecated. No real validated ML model exists for this endpoint in `admet_models_manifest.json` — heuristic structural alerts are the only prediction available.

**Method**: Structural alerts for carcinogenic mechanisms

**Challenges**:
- Multifactorial mechanisms
- Long-term effects difficult to model
- Species differences

**Expected Performance** (Literature):
- **Accuracy**: 60-70% (highly uncertain)
- **Better suited**: Expert systems + read-across

**Limitations**:
- Most challenging toxicity endpoint
- Requires long-term studies for validation

---

## Target Class Predictions

### Kinase Inhibitor Likelihood

**Status**: ⚠️ **Heuristic**

**Method**: Scoring based on:
- Heteroaromatic systems (ATP-competitive)
- H-bond donors/acceptors (hinge binding)
- Lipophilicity (hydrophobic pocket)
- Molecular weight (600-800 Da common)

**Expected Performance** (If QSAR):
- **Accuracy**: 75-85% for kinase vs. non-kinase
- **AUC**: 0.80-0.90

**Limitations**:
- No kinome selectivity prediction
- No binding mode determination
- Heuristic scoring function

---

### GPCR Modulator Prediction

**Status**: ⚠️ **Heuristic**

**Method**: GPCR ligand characteristics:
- Basic nitrogen (protonatable)
- Multiple aromatic rings
- Hydrophobic regions
- MW 300-500 Da

**Expected Performance**:
- **Accuracy**: 70-80% (if validated)

**Limitations**:
- No GPCR subtype specificity
- No agonist/antagonist distinction

---

### Ion Channel Blocker Identification

**Status**: ⚠️ **Heuristic**

**Method**: Features common to channel blockers:
- Aromatic rings
- Positive charge at physiological pH
- Molecular flexibility

**Limitations**:
- No channel subtype prediction
- Overlaps with other targets

---

## Machine Learning Models

### `ml_models.py` (Random Forest / XGBoost ensemble) — Deprecated

**Status**: ❌ **Deprecated — trained on fabricated data**

`models/ml_models.py` trains a Random Forest and an XGBoost classifier on `create_synthetic_dataset()` — a programmatically fabricated dataset, not real pharmaceutical measurements. The "Accuracy 85%/87%" and "AUC 0.88/0.90" figures previously reported here were computed on that fake data (effectively training-set numbers on synthetic labels) and **do not trace to any real, held-out validation** — they are not meaningful and have been removed from this document.

**Real alternative**: See **Category 0: Real Validated ML (XGBoost)** above — `models/real_admet.py`, 7 endpoints, real held-out TDC scaffold-split test scores in `models/saved_models/admet_models_manifest.json`.

---

## Limitations & Disclaimers

### General Limitations

1. **Not for Clinical Decisions**: This platform is for research and education only
2. **Heuristic Models**: Most ADME/Tox predictions use rule-based scoring, not data-driven QSAR
3. **Deprecated Modules**: `ml_models.py` was trained only on fabricated synthetic data, and `neural_toxicity.py` was never trained at all (frozen random weights) — both are deprecated. The 7 real ADMET models (Category 0) were trained on real TDC datasets with held-out scaffold-split testing.
4. **No Experimental Validation**: Predictions have not been experimentally validated against wet-lab assays, even for the real ADMET models — held-out test-set scores are not a substitute for experimental confirmation
5. **Single-Endpoint Focus**: No multi-endpoint optimization or ADMET profiles

### Specific Disclaimers

⚠️ **ADME/PK Predictions**:
- Use descriptor-based heuristics
- Do not replace experimental assays
- Should be validated with in vitro/in vivo studies

⚠️ **Toxicity Predictions**:
- Structural alerts (rule-based) have high false positive rates
- The real ADMET models are gradient-boosted (XGBoost) on public TDC data; small datasets
  (e.g. DILI test n=96) mean real held-out variance
- Cannot replace regulatory toxicology studies

⚠️ **Target Predictions**:
- Descriptor thresholds, not ligand-based models
- No binding affinity predictions
- Cannot determine selectivity profiles

### When to Use These Models

**Appropriate Uses**:
- Early-stage virtual screening
- Educational demonstrations
- Method development and research
- Prioritization for experimental testing

**Inappropriate Uses**:
- Clinical decision-making
- Regulatory submissions
- Without experimental follow-up
- As sole basis for drug candidate selection

---

## Future Validation Plans

### Phase 1: Replace Heuristics with QSAR

**Target**: All ADME/PK and toxicity predictions

**Approach**:
1. Curate training datasets (ChEMBL, Tox21, BindingDB)
2. Train validated QSAR models
3. Perform 5-fold cross-validation
4. Test on external validation sets
5. Report performance metrics (R², RMSE, AUC)

**Timeline**: 3-6 months

---

### Phase 2: External Validation

**Target**: All ML models

**Approach**:
1. Identify public benchmark datasets
2. Re-train models on real pharmaceutical data
3. External validation on held-out test sets
4. Compare to literature baselines
5. Publish validation results

**Timeline**: 6-12 months

---

### Phase 3: Prospective Validation

**Target**: Selected models

**Approach**:
1. Predict properties for novel compounds
2. Synthesize or acquire compounds
3. Perform experimental assays
4. Compare predictions to experimental results
5. Iterate model improvements

**Timeline**: 12-24 months

---

## Validation Resources

### Benchmark Datasets

Recommended datasets for model validation:

1. **ADME**: Caco-2, MDCK, BBB penetration datasets
2. **Toxicity**: Tox21, ToxCast, DILIrank, AMES datasets
3. **Bioactivity**: ChEMBL, BindingDB, PubChem BioAssay
4. **Drug-likeness**: FDA Approved Drugs, DrugBank

### Validation Metrics

**Regression Tasks** (ADME properties):
- R² (coefficient of determination)
- RMSE (root mean squared error)
- MAE (mean absolute error)
- External Q² (predictive R²)

**Classification Tasks** (Toxicity):
- Accuracy, Precision, Recall
- AUC-ROC (area under ROC curve)
- Balanced accuracy
- Matthews correlation coefficient (MCC)

---

## Conclusion

This platform demonstrates **computational drug discovery workflows** with **varying levels of validation**:

- ✅ **ADMET Toxicity/ADME (7 endpoints)**: real gradient-boosted (XGBoost) models validated on held-out TDC scaffold splits — see `models/saved_models/admet_models_manifest.json`
- ✅ **Drug-likeness metrics**: Validated standards — established deterministic calculations, not clinical or regulatory decision support
- ⚠️ **Remaining ADME/PK & Toxicity endpoints**: Heuristic methods for screening only
- ❌ **`neural_toxicity.py` / `ml_models.py`**: Were never legitimately trained (untrained random weights / fit-on-fake-data) and are being **removed**, not merely "demonstration"
- 🔬 **Future Work**: Extend real XGBoost coverage to remaining heuristic endpoints (kinase, GPCR, ion channel target-class predictions)

**For production use**, remaining heuristic modules should be replaced with validated QSAR models trained on curated pharmaceutical datasets following OECD QSAR validation principles, following the same held-out-validation approach already used for the 7 real ADMET models.

---

## References

See [REFERENCES.md](REFERENCES.md) for complete citations (50+ peer-reviewed papers).

---

**Last Updated**: November 2025  
**Maintained by**: Ardit Mishra  
**Contact**: amishra7599@gmail.com | [GitHub](https://github.com/ardit-mishra)
