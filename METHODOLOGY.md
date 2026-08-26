# Methodology & Scientific Basis

This document explains the scientific methodology and implementation details for all prediction algorithms in the AI-Powered Drug Discovery Platform. It provides transparency about which methods use validated QSAR models versus heuristic approximations.

---

## Table of Contents

1. [Overview](#overview)
2. [Drug-Likeness Assessment](#drug-likeness-assessment)
3. [ADME/PK Prediction](#admepk-prediction)
4. [Toxicity Profiling](#toxicity-profiling)
5. [Target Class Prediction](#target-class-prediction)
6. [Machine Learning Models](#machine-learning-models)
7. [Limitations & Future Directions](#limitations--future-directions)

---

## Overview

### Implementation Philosophy

This platform demonstrates **computational drug discovery workflows** using two approaches:

1. **Rule-Based Methods** (Gold Standard):
   - Lipinski Rule of 5, Veber rules, QED, SA score
   - Based on validated pharmaceutical research
   - **Status**: Fully implemented as per literature

2. **Heuristic Scoring Functions** (Educational):
   - ADME/PK predictions, toxicity assessment, target prediction
   - Based on molecular descriptors and physicochemical properties
   - **Status**: Educational demonstrations, not production-ready

3. **ADMET Machine Learning Models** (real, held-out validated):
   - Gradient-boosted trees (XGBoost) on ECFP4 fingerprints + RDKit descriptors
   - Trained on public Therapeutics Data Commons datasets with Bemis-Murcko scaffold splits
   - 7 endpoints served via `models/real_admet.py`; per-endpoint held-out test scores in
     `models/saved_models/admet_models_manifest.json`
   - **Status**: Live in the app. (A former synthetic-data ensemble in `models/ml_models.py`
     is **deprecated and no longer imported** — it was never a real model.)

### Scientific Transparency

This platform is designed for **education and research demonstration**. For production use:
- Replace heuristic functions with validated QSAR models trained on curated datasets (ChEMBL, proprietary data)
- Implement rigorous model validation (cross-validation, external test sets, applicability domain)
- Follow OECD QSAR validation principles [REFERENCES.md: 44]

---

## Drug-Likeness Assessment

### 1. Lipinski Rule of 5

**Method**: Direct implementation of Lipinski's Rule of 5 criteria [REFERENCES.md: 1]

**Implementation**:
```python
def calculate_lipinski_descriptors(mol):
    mw = Descriptors.MolWt(mol)          # ≤ 500 Da
    logp = Crippen.MolLogP(mol)          # ≤ 5
    hbd = Descriptors.NumHDonors(mol)    # ≤ 5
    hba = Descriptors.NumHAcceptors(mol) # ≤ 10
    
    violations = count_violations()
    passes = (violations <= 1)  # Allow 1 violation
```

**Scientific Basis**:
- Based on analysis of 2,245 approved drugs vs development compounds
- Predicts oral bioavailability based on physicochemical properties
- LogP calculation uses Wildman-Crippen method [REFERENCES.md: 6]

**Validation Status**: ✅ Gold standard industry method

**Production Readiness**: ✅ Ready for production use

---

### 2. Veber Rules

**Method**: Molecular flexibility and polarity criteria [REFERENCES.md: 3]

**Implementation**:
```python
def calculate_veber_descriptors(mol):
    rotatable_bonds = Descriptors.NumRotatableBonds(mol)  # ≤ 10
    tpsa = Descriptors.TPSA(mol)                          # ≤ 140 Ų
    
    passes = (rotatable_bonds <= 10) and (tpsa <= 140)
```

**Scientific Basis**:
- Analysis of >1,100 compounds with rat oral bioavailability data
- Better predictor than Lipinski for some compound classes
- TPSA correlates with Caco-2 permeability

**Validation Status**: ✅ Gold standard industry method

**Production Readiness**: ✅ Ready for production use

---

### 3. QED (Quantitative Estimate of Drug-likeness)

**Method**: RDKit implementation of Bickerton QED [REFERENCES.md: 4]

**Implementation**:
```python
def calculate_qed(mol):
    return QED.qed(mol)  # RDKit built-in function
```

**Scientific Basis**:
- Analysis of 771 marketed oral drugs
- Desirability functions for 8 molecular properties:
  - Molecular weight, LogP, HBD, HBA, TPSA, rotatable bonds, aromatic rings, structural alerts
- Weighted geometric mean of desirability functions

**Validation Status**: ✅ Published and validated method

**Production Readiness**: ✅ Ready for production use

---

### 4. Synthetic Accessibility (SA) Score

**Method**: RDKit SA Score contrib module [REFERENCES.md: 5]

**Implementation**:
```python
def calculate_sa_score(mol):
    # Primary: RDKit SA Score contrib
    import sascorer
    return sascorer.calculateScore(mol)
    
    # Fallback: Fingerprint complexity
    fp = rdMolDescriptors.GetMorganFingerprint(mol, 2)
    complexity = len(fp.GetNonzeroElements())
    return max(1, min(10, complexity / 50))
```

**Scientific Basis**:
- Fragment contribution method based on 13.5M compounds (PubChem)
- Complexity penalty for bridged rings, macrocycles, stereocenters
- Correlated with expert chemist assessments (r = 0.89)

**Validation Status**: ✅ Published method (fallback is approximation)

**Production Readiness**: ✅ Ready with RDKit contrib (⚠️ fallback is rough estimate)

---

## ADME/PK Prediction

**⚠️ IMPORTANT**: Current ADME/PK predictions use **heuristic scoring functions** based on molecular descriptors. These are educational demonstrations, **not validated QSAR models**.

### 1. LogP (Lipophilicity)

**Method**: Wildman-Crippen atomic contribution method [REFERENCES.md: 6]

**Implementation**:
```python
def predict_logp(mol):
    logp = Crippen.MolLogP(mol)  # Wildman-Crippen method
    
    category = (
        "Low" if logp < 0 else
        "Moderate" if logp <= 3 else
        "High" if logp <= 5 else
        "Very High"
    )
```

**Scientific Basis**:
- Atom-based contribution method
- Trained on 9,920 experimental LogP values
- Well-validated for drug-like molecules

**Validation Status**: ✅ Published method for LogP calculation

**Production Readiness**: ✅ LogP calculation ready; ⚠️ category thresholds are heuristic

---

### 2. Caco-2 Permeability

**Method**: Heuristic scoring based on LogP and TPSA [REFERENCES.md: 7,8]

**Implementation** (Current - Heuristic):
```python
def predict_caco2_permeability(mol):
    logp = Crippen.MolLogP(mol)
    tpsa = Descriptors.TPSA(mol)
    
    # Heuristic thresholds (not a trained model)
    if logp > 2 and tpsa < 75:
        return "High Permeability"
    elif logp > 0 and tpsa < 140:
        return "Moderate Permeability"
    else:
        return "Low Permeability"
```

**Scientific Basis**:
- Based on known correlations: LogP ↑ and TPSA ↓ → permeability ↑
- Thresholds derived from literature trends, not regression models

**Validation Status**: ⚠️ Heuristic approximation

**Production Recommendation**:
- Replace with Random Forest/XGBoost model trained on Caco-2 experimental data
- Wang et al. (2016) achieved R² = 0.83 using NSGA-II + boosting [REFERENCES.md: 8]
- ChEMBL provides ~900 Caco-2 permeability measurements

---

### 3. Blood-Brain Barrier (BBB) Penetration

**Method**: Heuristic scoring based on LogP and TPSA [REFERENCES.md: 9,10]

**Implementation** (Current - Heuristic):
```python
def predict_bbb_penetration(mol):
    logp = Crippen.MolLogP(mol)
    tpsa = Descriptors.TPSA(mol)
    mw = Descriptors.MolWt(mol)
    
    # Heuristic scoring (not a trained model)
    if logp > 1 and tpsa < 60 and mw < 450:
        return "High BBB Penetration"
    elif logp > 0 and tpsa < 90:
        return "Moderate BBB Penetration"  
    else:
        return "Low BBB Penetration"
```

**Scientific Basis**:
- BBB permeation correlates with: low TPSA (<90 Ų), moderate LogP (1-3), low MW
- Based on Adenot & Lahana (2004) and Muehlbacher et al. (2011) findings

**Validation Status**: ⚠️ Heuristic approximation

**Production Recommendation**:
- Replace with classification model (CNS+ vs CNS-)
- Muehlbacher et al. achieved 92% accuracy with SVM on 1,679 compounds

---

### 4. CYP450 Metabolism

**Method**: Heuristic scoring based on LogP and aromatic content [REFERENCES.md: 11,12]

**Implementation** (Current - Heuristic):
```python
def predict_cyp450_metabolism(mol):
    logp = Crippen.MolLogP(mol)
    aromatic_rings = Descriptors.NumAromaticRings(mol)
    
    # Heuristic (not CYP isoform-specific)
    if logp > 2 and aromatic_rings >= 2:
        return "Likely CYP Substrate"
    else:
        return "Unlikely CYP Substrate"
```

**Scientific Basis**:
- Lipophilic aromatic compounds are common CYP substrates
- Simplification of complex isoform-specific metabolism

**Validation Status**: ⚠️ Crude heuristic

**Production Recommendation**:
- Implement isoform-specific models (CYP3A4, 2D6, 2C9, 2C19, 1A2)
- Cheng et al. (2011) combined classifiers: AUC 0.84-0.93 per isoform [REFERENCES.md: 11]
- XenoSite provides site-of-metabolism prediction [REFERENCES.md: 12]

---

### 5. Hepatic Clearance

**Method**: Heuristic scoring based on LogP and molecular weight [REFERENCES.md: 13]

**Implementation** (Current - Heuristic):
```python
def predict_clearance(mol):
    logp = Crippen.MolLogP(mol)
    mw = Descriptors.MolWt(mol)
    
    # Simplified heuristic
    if logp > 3 and mw > 400:
        return "High Clearance"
    else:
        return "Low-Moderate Clearance"
```

**Scientific Basis**:
- Lipophilic large molecules tend toward hepatic metabolism
- Oversimplified—real clearance depends on many factors

**Validation Status**: ⚠️ Very crude heuristic

**Production Recommendation**:
- Replace with regression model for CLh prediction
- Requires extensive in vivo/in vitro clearance data
- Consider allometric scaling and in vitro-in vivo extrapolation (IVIVE)

---

## Toxicity Profiling

**⚠️ IMPORTANT**: Platform offers two toxicity/ADMET prediction approaches:
1. **Real ADMET Models** (Gradient-Boosted, XGBoost): Trained on curated Therapeutics Data Commons (TDC) datasets with held-out scaffold-split test sets. Implemented in `models/real_admet.py`.
2. **Heuristic Predictors** (Rule-Based): Structural alerts and descriptor thresholds for educational comparison. Implemented in `toxicity_predictors.py`, `adme_predictors.py`, and `utils/drug_likeness.py`.

An earlier prototype module (`models/neural_toxicity.py`) also exists in the codebase but is untrained and unused — see below.

---

### Real ADMET Models (Gradient-Boosted, XGBoost)

**Method**: Per-endpoint XGBoost classifiers/regressor, implemented in `models/real_admet.py` (class `RealADMETPredictor`), exposed to the app through `comprehensive_toxicity_profile(mol)`.

**Feature representation** (2,058 features per endpoint):
- ECFP4 / Morgan fingerprint, radius=2, 2048 bits
- 10 RDKit descriptors: MolWt, MolLogP, TPSA, NumHDonors, NumHAcceptors, NumRotatableBonds, NumAromaticRings, FractionCSP3, HeavyAtomCount, NumHeteroatoms

**Training data & split**: Each endpoint is trained on its corresponding Therapeutics Data Commons (TDC) benchmark dataset, using TDC's default scaffold split (seed 1), which groups structurally similar molecules together so the held-out test set contains scaffolds not seen during training.

**Endpoints and held-out test performance** (source of truth: `models/saved_models/admet_models_manifest.json` — the only legitimate metrics in this codebase):

| Endpoint | ADMET Class | App Label | Metric | Test Score | n_train | n_test |
|---|---|---|---|---|---|---|
| DILI | Toxicity | Hepatotoxicity (DILI) | AUROC | 0.925 | 379 | 96 |
| hERG | Toxicity | Cardiotoxicity (hERG) | AUROC | 0.809 | 523 | 132 |
| AMES | Toxicity | Mutagenicity (Ames) | AUROC | 0.845 | 5,821 | 1,457 |
| BBB_Martins | Distribution | Blood-Brain Barrier | AUROC | 0.905 | 1,624 | 406 |
| Pgp_Broccatelli | Absorption | P-glycoprotein Inhibition | AUROC | 0.926 | 973 | 245 |
| CYP3A4_Veith | Metabolism | CYP3A4 Inhibition | AUPRC | 0.869 | 9,861 | 2,467 |
| Caco2_Wang | Absorption | Caco-2 Permeability | MAE | 0.339 | 728 | 182 |

Each row is a separately trained, saved model (e.g. `DILI_xgb.json`) in `models/saved_models/`, evaluated on its own held-out TDC scaffold-split test set (never seen during training). Model files, split details, and full feature specs live in `admet_models_manifest.json` alongside each `*_meta.json`.

**Scope note**: These 7 endpoints span multiple ADMET classes — toxicity (DILI, hERG, AMES), distribution (BBB_Martins), absorption (Pgp_Broccatelli, Caco2_Wang), and metabolism (CYP3A4_Veith) — but are all surfaced together through `comprehensive_toxicity_profile(mol)`, which is the drop-in replacement for the earlier fabricated toxicity output described below. There is no trained or validated model for carcinogenicity anywhere in this codebase; where the app shows a carcinogenicity value, it comes from the rule-based heuristic documented under "Heuristic Toxicity Predictors" below, not from a trained model.

**Validation Status**: ✅ Real, held-out-validated models with reported test-set metrics.

---

### Untrained Placeholder Network (Not Used for Predictions)

`models/neural_toxicity.py` defines the shape of a feed-forward network (2,078-feature input, three hidden layers, 4-neuron sigmoid output) that was intended for multi-endpoint toxicity prediction.

**This module's weights are randomly initialized (`np.random.randn()*0.01`) and never trained; its outputs are not meaningful and it is not used to generate the toxicity predictions shown in the app.** There is no `.fit()` call or training loop for this network anywhere in the codebase — not even on synthetic data.

- ❌ Not trained — weights are random noise left over from initialization
- ❌ No training loop, dataset, loss function, or optimizer ever runs for this module
- ❌ No validation metrics exist for it, because nothing was trained to validate
- ⚠️ Layer shapes are defined but weights are randomly initialized and never trained — do not treat any output from this module as a prediction

This module is retained in the codebase as an unused placeholder. It should be removed or explicitly gated off before any production use.

---

### Heuristic Toxicity Predictors (Rule-Based)

The platform also includes traditional rule-based predictors for educational comparison and ensemble approaches.

### 1. hERG Cardiac Toxicity (Heuristic)

**Method**: Heuristic scoring based on LogP, TPSA, and basic count [REFERENCES.md: 14-17]

**Implementation** (Current - Heuristic):
```python
def predict_herg_inhibition(mol):
    logp = Crippen.MolLogP(mol)
    tpsa = Descriptors.TPSA(mol)
    basic_nitrogens = Descriptors.NumBasicAtoms(mol)
    
    # Heuristic risk assessment
    if logp > 3 and basic_nitrogens >= 2:
        return "High hERG Risk"
    elif logp > 2 or tpsa < 75:
        return "Moderate hERG Risk"
    else:
        return "Low hERG Risk"
```

**Scientific Basis**:
- hERG blockers tend to be lipophilic, basic, planar molecules
- Based on known SAR patterns, not a trained model

**Validation Status**: ⚠️ Heuristic structural alert

**Production Recommendation**:
- **State-of-the-art**: Graph Neural Networks achieving AUC 0.96 [REFERENCES.md: 17]
- Cai et al. (2020) IUP-GNN with uncertainty quantification
- ChEMBL contains ~5,000 hERG IC50 measurements
- Critical safety endpoint—use validated model

---

### 2. Hepatotoxicity

**Method**: Heuristic based on reactive functional groups and LogP [REFERENCES.md: 18,19]

**Implementation** (Current - Heuristic):
```python
def predict_hepatotoxicity(mol):
    logp = Crippen.MolLogP(mol)
    mw = Descriptors.MolWt(mol)
    reactive_groups = count_structural_alerts(mol)  # Simplified
    
    if logp > 4 or reactive_groups > 2:
        return "High Hepatotoxicity Risk"
    else:
        return "Low-Moderate Risk"
```

**Scientific Basis**:
- Lipophilic compounds with reactive metabolites → liver toxicity
- Structural alerts for reactive groups

**Validation Status**: ⚠️ Crude heuristic

**Production Recommendation**:
- Chen et al. (2013): Random Forest with 287 DILI-positive compounds [REFERENCES.md: 18]
- Xu et al. (2015): Deep learning AUC 0.76 [REFERENCES.md: 19]
- DILIrank dataset available for model training

---

### 3. Mutagenicity (Ames Test)

**Method**: Heuristic structural alerts [REFERENCES.md: 20,21]

**Implementation** (Current - Heuristic):
```python
def predict_mutagenicity(mol):
    # Simplified structural alert check
    alerts = check_genotoxic_alerts(mol)
    aromatic_amines = Fragments.fr_Ar_NH(mol)
    nitro_groups = Fragments.fr_nitro(mol)
    
    if alerts > 0 or aromatic_amines + nitro_groups > 2:
        return "Mutagenic (Ames Positive)"
    else:
        return "Non-Mutagenic (Ames Negative)"
```

**Scientific Basis**:
- Known mutagenic functional groups (nitro, aromatic amines, epoxides, etc.)
- Based on structural alert literature

**Validation Status**: ⚠️ Simplified structural alerts

**Production Recommendation**:
- Hansen et al. (2009) benchmark dataset: 6,512 compounds [REFERENCES.md: 21]
- Honma et al. (2019): Ensemble QSAR models, balanced accuracy >85% [REFERENCES.md: 20]
- Implement Derek/Sarah-like expert system or ML model

---

### 4. Carcinogenicity

**Method**: Heuristic based on mutagenicity + lipophilicity [REFERENCES.md: 22]

**Implementation** (Current - Heuristic):
```python
def predict_carcinogenicity(mol):
    mutagenic = predict_mutagenicity(mol)
    logp = Crippen.MolLogP(mol)
    
    if mutagenic == "Mutagenic" or logp > 5:
        return "Potential Carcinogen"
    else:
        return "Low Carcinogenicity Risk"
```

**Scientific Basis**:
- Many (not all) mutagens are carcinogens
- High LogP correlates with bioaccumulation

**Validation Status**: ⚠️ Oversimplified heuristic

**Production Recommendation**:
- Complex endpoint requiring long-term animal studies
- Fjodorova et al. (2010): Ensemble QSAR for rodent carcinogenicity [REFERENCES.md: 22]
- Consider REACH/ECHA guidance on carcinogenicity assessment

---

## Target Class Prediction

**⚠️ IMPORTANT**: Current target predictions use **heuristic descriptor thresholds**. Not ligand-based or structure-based models.

### General Methodology

All target class predictions use simplified heuristics based on known physicochemical property distributions for each target class.

**Production Recommendation**:
- Use ligand-based models trained on ChEMBL bioactivity data
- Structure-based docking for available target structures
- Multi-task learning across related targets [REFERENCES.md: 50]

---

### 1. Kinase Inhibitors

**Method**: Heuristic based on MW, HBA, aromatic rings [REFERENCES.md: 23,24]

**Implementation** (Current - Heuristic):
```python
def predict_kinase_inhibitor(mol):
    mw = Descriptors.MolWt(mol)
    hba = Descriptors.NumHAcceptors(mol)
    aromatic_rings = Descriptors.NumAromaticRings(mol)
    
    if 300 < mw < 550 and hba >= 4 and aromatic_rings >= 3:
        return "Likely Kinase Inhibitor"
    else:
        return "Unlikely Kinase Inhibitor"
```

**Scientific Basis**:
- Kinase inhibitors tend to be aromatic, moderate MW, multiple HBA
- Based on Bemis-Murcko scaffold analysis of approved kinase drugs

**Production Recommendation**:
- Profile-QSAR across kinase family [REFERENCES.md: 23]
- Structure-based docking to kinase homology models
- ChEMBL contains >300,000 kinase bioactivity measurements

---

### 2. GPCR Modulators

**Method**: Heuristic based on MW, HBA, basic nitrogen [REFERENCES.md: 25,26]

**Implementation** (Current - Heuristic):
```python
def predict_gpcr_modulator(mol):
    mw = Descriptors.MolWt(mol)
    basic_n = count_basic_nitrogens(mol)
    
    if mw < 500 and basic_n >= 1:
        return "Likely GPCR Modulator"
    else:
        return "Unlikely GPCR Modulator"
```

**Scientific Basis**:
- GPCRs often bind basic amines (aminergic receptors)
- Moderate molecular weight

**Production Recommendation**:
- GPCR-specific QSAR models per receptor family
- Consider GPCR class (A, B, C, Frizzled)
- Gloriam et al. (2009) transmembrane pocket modeling [REFERENCES.md: 25]

---

### 3. Ion Channel Blockers

**Method**: Heuristic based on LogP and basic nitrogen [REFERENCES.md: 27]

**Implementation** (Current - Heuristic):
```python
def predict_ion_channel_blocker(mol):
    logp = Crippen.MolLogP(mol)
    basic_n = count_basic_nitrogens(mol)
    
    if logp > 2 and basic_n >= 1:
        return "Likely Ion Channel Blocker"
    else:
        return "Unlikely Ion Channel Blocker"
```

**Production Recommendation**:
- Channel-specific models (hERG, Nav, Cav, Kv)
- Structure-based docking for available structures

---

### 4. Enzyme Inhibitors

**Method**: Generic heuristic (MW, HBD/HBA)

**Implementation** (Current - Heuristic):
```python
def predict_enzyme_inhibitor(mol):
    mw = Descriptors.MolWt(mol)
    hbd = Descriptors.NumHDonors(mol)
    hba = Descriptors.NumHAcceptors(mol)
    
    if mw < 600 and (hbd + hba) >= 4:
        return "Potential Enzyme Inhibitor"
    else:
        return "Unlikely Enzyme Inhibitor"
```

**Production Recommendation**:
- Enzyme-specific models (CYPs, proteases, kinases, etc.)
- Mechanism-based models (competitive, non-competitive, allosteric)

---

## Machine Learning Models (ADMET)

### 1. Model Architecture

**Per-endpoint gradient-boosted trees** (`models/real_admet.py`, served in the app):
```python
# One XGBoost model per ADMET endpoint, loaded via the native Booster API.
import xgboost as xgb
booster = xgb.Booster()
booster.load_model("models/saved_models/hERG_xgb.json")
prob = booster.predict(xgb.DMatrix(features))   # binary:logistic -> probability
```

- **Features**: ECFP4/Morgan fingerprint (2048 bits, radius 2) + 10 RDKit physicochemical
  descriptors (MolWt, MolLogP, TPSA, HBD, HBA, rotatable bonds, aromatic rings, FractionCSP3,
  heavy atoms, heteroatoms).
- **Data / split**: public Therapeutics Data Commons (TDC) datasets, Bemis-Murcko **scaffold**
  split (train+valid vs. held-out test), official TDC metric per endpoint.
- **7 endpoints**: DILI, hERG, AMES, BBB_Martins, Pgp_Broccatelli, CYP3A4_Veith, Caco2_Wang.

**Scientific Basis**:
- XGBoost: Chen & Guestrin (2016) [REFERENCES.md: 30]
- Scaffold splitting to avoid analog leakage (Bemis & Murcko, 1996)

**Reported performance**: real, single held-out evaluation per endpoint — see
`models/saved_models/admet_models_manifest.json` (e.g. DILI AUROC 0.925, hERG 0.809, AMES 0.845,
BBB 0.905, Pgp 0.926, CYP3A4 AUPRC 0.869, Caco-2 MAE 0.339). No synthetic training data.

> **Deprecated:** an earlier `MultiModelPredictor` ensemble (`models/ml_models.py`) was trained on a
> self-generated synthetic dataset and is **no longer imported by the app**. Its reported "accuracy"
> was circular and meaningless; it has been replaced by the real models above.

---

## Limitations & Future Directions

### Current Limitations

1. **Heuristic Functions**:
   - ADME/PK, toxicity, target predictions use descriptor thresholds
   - Not validated against experimental data
   - High false positive/negative rates expected

2. **Dataset size / coverage**:
   - Some ADMET endpoints have small public datasets (e.g. DILI test n=96), so held-out
     scores carry real variance
   - Trained only on the public TDC chemical space; extrapolation beyond it is unvalidated

3. **Applicability Domain**:
   - No checks for out-of-domain predictions
   - May give unreliable results for unusual scaffolds

4. **No Uncertainty Quantification**:
   - Predictions don't include confidence intervals
   - Users can't assess reliability

---

### Future Enhancements

**Phase 2 Improvements**:

1. **Replace Heuristics with Validated QSAR Models**:
   - Train on ChEMBL bioactivity data (>2M compounds)
   - Implement regression models for continuous endpoints (IC50, LogD, etc.)
   - Add applicability domain checks

2. **Implement Deep Learning**:
   - Graph Neural Networks for toxicity (AUC 0.96 for hERG) [REFERENCES.md: 17]
   - Message Passing Neural Networks (MPNN)
   - Transformer models for SMILES

3. **Add Uncertainty Quantification**:
   - Conformal prediction
   - Bayesian neural networks
   - Ensemble diversity metrics

4. **Expand Endpoint Coverage**:
   - Solubility (kinetic/thermodynamic)
   - Plasma protein binding (PPB)
   - Volume of distribution (Vd)
   - Human bioavailability (%F)

5. **Regulatory Compliance**:
   - OECD QSAR validation documentation
   - QMRF (QSAR Model Reporting Format)
   - Applicability domain definition
   - Model performance metrics on external test sets

---

## Validation Standards

For production QSAR models, follow these standards [REFERENCES.md: 44,46]:

### OECD QSAR Validation Principles

1. **Defined endpoint**: Clear, unambiguous biological/physicochemical endpoint
2. **Unambiguous algorithm**: Transparent, reproducible computational method
3. **Defined applicability domain**: Chemical space where model is reliable
4. **Appropriate goodness-of-fit**: R², RMSE, Q² for regression; AUC, accuracy for classification
5. **Robustness**: External validation on independent test set

### Model Performance Metrics

**Classification Tasks** (toxicity, activity):
- AUC-ROC ≥ 0.80 (good), ≥ 0.90 (excellent)
- Balanced accuracy (to handle class imbalance)
- Matthew's Correlation Coefficient (MCC)
- Sensitivity/specificity trade-offs

**Regression Tasks** (ADME properties):
- R² ≥ 0.70 (acceptable), ≥ 0.80 (good)
- RMSE within acceptable error for endpoint
- External Q² ≥ 0.60

### Data Quality

- Chemical structure curation [REFERENCES.md: 45]
- Standardization (tautomers, salts, stereochemistry)
- Outlier detection and removal
- Balanced datasets (avoid bias)

---

## Conclusion

This platform demonstrates **computational drug discovery workflows** with scientific rigor in documentation and methodology. However, users must understand:

- ✅ **Drug-likeness methods** (Lipinski, Veber, QED, SA) are rule-based and production-ready
- ✅ **ADMET models** (DILI, hERG, AMES, BBB, Pgp, CYP3A4, Caco-2) are real gradient-boosted
  (XGBoost) models trained on public TDC data with scaffold splits and held-out test metrics
- ⚠️ **ADME/PK panel** and **target predictions** remain rule-based heuristics (descriptor
  thresholds), not trained QSAR
- ⚠️ Some ADMET datasets are small (e.g. DILI test n=96), so held-out scores carry real variance

The rule-based heuristic panels above could be upgraded to validated QSAR models trained on larger curated experimental datasets following OECD principles.

---

**References**: See REFERENCES.md for complete citations (50+ peer-reviewed papers)

**Author**: Ardit Mishra  
**GitHub**: github.com/ardit-mishra  
**Last Updated**: November 2025
