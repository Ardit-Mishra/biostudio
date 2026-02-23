# BioStudio Tutorial

Complete user guide for **BioStudio** - AI-Powered Molecular Intelligence Platform

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Application Overview](#application-overview)
3. [Page-by-Page Guide](#page-by-page-guide)
4. [Example Workflows](#example-workflows)
5. [Sample Molecules & Proteins](#sample-molecules--proteins)
6. [Interpreting Results](#interpreting-results)
7. [Tips & Best Practices](#tips--best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Launch the Application

```bash
# Navigate to project directory
cd biostudio

# Activate virtual environment (if using)
source venv/bin/activate  # Linux/macOS
# OR
venv\Scripts\activate  # Windows

# Start Streamlit
streamlit run app.py --server.port 5000
```

The application will automatically open in your default browser at `http://localhost:5000`.

### Quick Start

1. Open the application in your browser
2. Use the **sidebar** to navigate between different tools
3. Enter a **SMILES string** (for small molecules) or **FASTA sequence** (for proteins)
4. Click **"Run Analysis"** or similar button
5. Review the results and visualizations

---

## Application Overview

### Navigation Structure

The sidebar contains 10 main pages organized by functionality:

1. **Home** - Introduction and overview
2. **Molecular Processing** - Basic molecular analysis
3. **Drug-Likeness Assessment** - Lipinski, Veber, QED, SA scores
4. **ADME/PK Prediction** - Pharmacokinetic properties
5. **Toxicity Profiling** - Safety assessment
6. **Target Class Prediction** - Potential biological targets
7. **ML Model Predictions** - Ensemble machine learning
8. **Knowledge Graph Explorer** - Drug-target-disease relationships
9. **Batch Screening** - High-throughput analysis
10. **Case Study** - Example workflow with kinase inhibitors

### Input Formats

#### SMILES (Simplified Molecular Input Line Entry System)

For **small molecules** (drugs, compounds):

```
# Example: Aspirin
CC(=O)Oc1ccccc1C(=O)O

# Example: Imatinib (Gleevec)
CN1CCN(CC1)Cc2ccc(cc2)C(=O)Nc3ccc(c(c3)Nc4nccc(n4)c5cccnc5)C(F)(F)F
```

#### FASTA

For **proteins and peptides**:

```
>Insulin A-chain
GIVEQCCTSICSLYQLENYCN

>Semaglutide (GLP-1 analog)
HAEGTFTSDVSSYLEGQAAKEFIAWLVKGR
```

---

## Page-by-Page Guide

### 1. Home Page

**Purpose**: Welcome screen with project overview

**What You'll See**:
- Project description
- Key features summary
- Navigation guidance
- Quick start tips

**Actions**: None required - informational page

---

### 2. Molecular Processing

**Purpose**: Basic molecular property analysis

**Input**: SMILES string

**Steps**:
1. Enter SMILES in text box (or select example)
2. Click "Process Molecule"
3. Review molecular properties

**Output**:
- 2D molecular structure visualization
- Basic properties:
  - Molecular weight
  - LogP (lipophilicity)
  - H-bond donors/acceptors
  - Rotatable bonds
  - Aromatic rings
- Molecular fingerprint
- Descriptor summary

**Example Molecules**:

```
# Simple molecule: Ethanol
CCO

# Common drug: Aspirin
CC(=O)Oc1ccccc1C(=O)O

# Complex drug: Imatinib
CN1CCN(CC1)Cc2ccc(cc2)C(=O)Nc3ccc(c(c3)Nc4nccc(n4)c5cccnc5)C(F)(F)F
```

**Interpretation**:
- **MW < 500**: Generally good for oral drugs
- **LogP 0-5**: Balanced lipophilicity
- **HBD ≤ 5, HBA ≤ 10**: Lipinski Rule of 5
- **Rotatable Bonds < 10**: Oral bioavailability

---

### 3. Drug-Likeness Assessment

**Purpose**: Evaluate drug-like properties

**Input**: SMILES string

**Metrics Calculated**:

#### Lipinski Rule of 5
- **Criteria**: MW ≤ 500, LogP ≤ 5, HBD ≤ 5, HBA ≤ 10
- **Interpretation**: 
  - 0 violations = Excellent drug-likeness
  - 1 violation = Acceptable
  - 2+ violations = Likely poor oral bioavailability

#### Veber Rules
- **Criteria**: Rotatable bonds ≤ 10, TPSA ≤ 140 ų
- **Interpretation**: Predicts oral bioavailability

#### QED (Quantitative Estimate of Drug-likeness)
- **Range**: 0-1
- **Interpretation**:
  - QED > 0.67 = High drug-likeness (top 25% of drugs)
  - QED 0.49-0.67 = Moderate
  - QED < 0.49 = Low

#### Synthetic Accessibility (SA) Score
- **Range**: 1 (easy) to 10 (difficult)
- **Interpretation**:
  - SA ≤ 3 = Easily synthesizable
  - SA 3-6 = Moderate difficulty
  - SA > 6 = Challenging synthesis

**Example Workflow**:

```python
# Good drug-likeness: Aspirin
Input: CC(=O)Oc1ccccc1C(=O)O
Expected:
  - Lipinski violations: 0
  - QED: 0.70-0.80 (high)
  - SA: 1-2 (easy to synthesize)

# Poor drug-likeness: Large natural product
Input: [complex molecule with MW > 600]
Expected:
  - Multiple Lipinski violations
  - QED: < 0.5
  - SA: > 7
```

---

### 4. ADME/PK Prediction

**Purpose**: Predict pharmacokinetic properties

**Input**: SMILES string

**Predictions**:

#### LogP (Lipophilicity)
- **Ideal Range**: 0-3 for most drugs
- **Interpretation**:
  - LogP < 0: Too hydrophilic, poor membrane permeability
  - LogP 0-3: Balanced, good oral absorption
  - LogP > 5: Too lipophilic, poor solubility

#### Caco-2 Permeability
- **Predicts**: Intestinal absorption
- **Categories**:
  - High: > -5.15 log units (>90% absorbed)
  - Moderate: -5.15 to -6.0 (50-90% absorbed)
  - Low: < -6.0 (<50% absorbed)

#### Blood-Brain Barrier (BBB) Penetration
- **Predicts**: CNS drug potential
- **Result**: BBB+ or BBB-
- **Interpretation**:
  - BBB+: Suitable for CNS drugs
  - BBB-: Peripheral drugs, less CNS side effects

#### CYP450 Metabolism
- **Predicts**: Metabolic liability
- **Isoforms**: 3A4, 2D6, 2C9, 2C19, 1A2
- **Interpretation**:
  - Low metabolism: Longer half-life
  - High metabolism: Shorter duration, drug-drug interactions

#### Hepatic Clearance
- **Predicts**: Liver metabolism rate
- **Categories**: Low, Moderate, High
- **Interpretation**:
  - Low clearance: Once or twice daily dosing
  - High clearance: More frequent dosing needed

**Example Analysis**:

```
# Imatinib (oral kinase inhibitor)
Input: CN1CCN(CC1)Cc2ccc(cc2)C(=O)Nc3ccc(c(c3)Nc4nccc(n4)c5cccnc5)C(F)(F)F

Expected Profile:
  - LogP: ~3.5 (good balance)
  - Caco-2: High permeability
  - BBB: Negative (peripheral action)
  - CYP3A4: Substrate (metabolized)
  - Clearance: Moderate
```

---

### 5. Toxicity Profiling

**Purpose**: Assess potential safety concerns

**Input**: SMILES string

**Endpoints**:

#### Hepatotoxicity (Liver Toxicity)
- **Risk Levels**: Low, Moderate, High, Critical
- **Structural Alerts**:
  - Reactive metabolites (quinones, epoxides)
  - Mitochondrial toxins
  - Cholestasis-inducing moieties

#### hERG Cardiotoxicity
- **Mechanism**: hERG potassium channel blockade → QT prolongation
- **Risk Assessment**: Based on structural features
- **Interpretation**:
  - Low risk: Unlikely to cause cardiac issues
  - High risk: Requires cardiac safety studies

#### Mutagenicity (Ames Test)
- **Predicts**: DNA damage potential
- **Categories**: Non-mutagenic, Mutagenic, Uncertain
- **Importance**: Regulatory requirement for all drugs

#### Carcinogenicity
- **Predicts**: Long-term cancer risk
- **Assessment**: Based on structural alerts
- **Note**: Most uncertain endpoint, requires long-term studies

**Neural Network vs. Heuristic**:

The platform provides **two approaches** side-by-side:
1. **Heuristic**: Rule-based structural alerts (fast, interpretable)
2. **Neural Network**: Deep learning model (demonstration, trained on synthetic data)

**Example Toxicity Profile**:

```
# Aspirin (known safe)
Input: CC(=O)Oc1ccccc1C(=O)O

Expected:
  - Hepatotoxicity: Low
  - hERG: Low risk
  - Mutagenicity: Negative
  - Carcinogenicity: Low risk

# Compound with toxophores
Input: [molecule with quinone or epoxide]

Expected:
  - Hepatotoxicity: High (reactive metabolite)
  - Mutagenicity: Positive (DNA alkylation)
```

---

### 6. Target Class Prediction

**Purpose**: Identify potential biological targets

**Input**: SMILES string

**Target Classes**:

#### Kinase Inhibitors
- **Features**: ATP-competitive scaffolds, hydrogen bond donors/acceptors
- **Score**: 0-100%
- **Interpretation**:
  - > 70%: Strong kinase inhibitor likelihood
  - 40-70%: Moderate probability
  - < 40%: Unlikely

#### GPCR Modulators
- **Features**: Basic nitrogen, aromatic rings, hydrophobic regions
- **Target**: G-protein coupled receptors (40% of drug targets)

#### Ion Channel Blockers
- **Features**: Aromatic systems, positive charge
- **Examples**: Antiarrhythmics, anticonvulsants

#### Enzyme Inhibitors
- **Features**: Hydrogen bonding, polar groups
- **Scope**: General enzyme inhibition potential

**Example**:

```
# Imatinib (known kinase inhibitor)
Input: CN1CCN(CC1)Cc2ccc(cc2)C(=O)Nc3ccc(c(c3)Nc4nccc(n4)c5cccnc5)C(F)(F)F

Expected:
  - Kinase Inhibitor: 85-95%
  - GPCR Modulator: 20-30%
  - Ion Channel: 10-20%
  - Enzyme Inhibitor: 40-50%
```

---

### 7. ML Model Predictions

**Purpose**: Ensemble machine learning predictions

**Input**: SMILES string

**Models Used**:
1. **Random Forest** (100 trees)
2. **XGBoost** (gradient boosting)
3. **Neural Network** (3 hidden layers)

**Output**:
- **Ensemble Prediction**: Average across models
- **Confidence**: Agreement between models
- **Individual Model Results**: Transparency
- **Feature Importance**: Which molecular properties drive predictions

**Interpretation**:
- **High Confidence** (models agree): More reliable prediction
- **Low Confidence** (models disagree): Uncertain region, experimental validation recommended
- **Feature Importance**: Understand which properties matter most

**Note**: These models are trained on **synthetic data** for demonstration purposes. For production use, retrain on real pharmaceutical datasets.

---

### 8. Knowledge Graph Explorer

**Purpose**: Explore drug-target-disease relationships

**Features**:

#### Interactive Network Visualization
- **Nodes**: Drugs, targets, diseases
- **Edges**: Relationships (treats, inhibits, associated_with)
- **Interaction**: Click nodes to see details

#### Query Mechanisms

**Mechanism of Action Query**:
```
Input: Imatinib
Output: 
  - Inhibits: BCR-ABL, c-Kit, PDGFR
  - Treats: Chronic myeloid leukemia (CML)
```

**Target Drugs Query**:
```
Input: EGFR
Output: Drugs targeting EGFR
  - Gefitinib
  - Erlotinib
  - Osimertinib
```

**Disease Treatment Query**:
```
Input: Lung cancer
Output: Approved drugs for lung cancer
```

**Use Cases**:
- Drug repurposing
- Target identification
- Off-target prediction
- Mechanism understanding

---

### 9. Batch Screening

**Purpose**: High-throughput molecular library screening

**Input**: CSV file with SMILES column

**CSV Format**:

```csv
compound_id,SMILES,name
COMP001,CCO,Ethanol
COMP002,CC(=O)Oc1ccccc1C(=O)O,Aspirin
COMP003,CN1CCN(CC1)Cc2ccc(cc2)C(=O)Nc3ccc(c(c3)Nc4nccc(n4)c5cccnc5)C(F)(F)F,Imatinib
```

**Steps**:
1. Upload CSV file
2. Select analysis types (drug-likeness, ADME, toxicity)
3. Click "Run Batch Analysis"
4. Download results as CSV

**Output**:
- All predictions for each molecule
- Ranked by drug-likeness or custom criteria
- Downloadable results for further analysis

**Use Case**: Screen virtual library (100s-1000s of molecules) to prioritize compounds for synthesis/testing

---

### 10. Case Study: Kinase Inhibitor Screening

**Purpose**: Complete workflow demonstration

**Scenario**: Rank potential kinase inhibitor leads

**Workflow**:

1. **Load Dataset**: 10 kinase inhibitor candidates
2. **Multi-Parameter Analysis**:
   - Drug-likeness (QED)
   - Kinase inhibitor score
   - Hepatotoxicity risk
   - Synthetic accessibility
3. **Ranking**: Weighted score across parameters
4. **Prioritization**: Top candidates for experimental testing

**Learning Objectives**:
- How to combine multiple predictions
- Balancing efficacy vs. safety
- Lead optimization decision-making
- Real-world drug discovery workflow

**Example Results**:

```
Rank 1: Compound A
  - QED: 0.82 (high drug-likeness)
  - Kinase Score: 88% (strong)
  - Hepatotox: Low risk
  - SA: 2.8 (easy synthesis)
  → Recommended for synthesis & testing

Rank 10: Compound J
  - QED: 0.45 (poor drug-likeness)
  - Kinase Score: 92% (strong, but...)
  - Hepatotox: High risk
  - SA: 7.2 (difficult synthesis)
  → Not recommended (safety concerns)
```

---

## Example Workflows

### Workflow 1: Single Molecule Evaluation

**Goal**: Assess a new drug candidate

1. **Molecular Processing**: Get basic properties
2. **Drug-Likeness**: Check Lipinski compliance
3. **ADME/PK**: Evaluate absorption, BBB penetration
4. **Toxicity**: Screen for safety flags
5. **Target Prediction**: Identify likely targets
6. **Decision**: Proceed to synthesis or modify structure?

**Example Molecule**: Aspirin

```
Step 1: Input SMILES → CC(=O)Oc1ccccc1C(=O)O
Step 2: Drug-Likeness → 0 violations, QED = 0.73
Step 3: ADME → Good permeability, no BBB
Step 4: Toxicity → Low risk (all endpoints)
Step 5: Target → COX enzyme inhibitor
Decision: ✅ Proceed (known safe drug)
```

---

### Workflow 2: Lead Optimization

**Goal**: Improve a lead compound

1. **Baseline Analysis**: Characterize current lead
2. **Identify Issues**: Poor solubility? Toxicity alerts?
3. **Structure Modification**: Mentally design analogs
4. **Test Analogs**: Run predictions on new structures
5. **Compare**: Which analog is better?

**Example**:

```
Lead: High lipophilicity (LogP = 6), poor solubility
Analog 1: Add polar group → LogP = 3.5
Result: Better drug-likeness, improved solubility

Lead: hERG risk due to basic amine
Analog 2: Replace with neutral group
Result: Reduced cardiotoxicity risk
```

---

### Workflow 3: Virtual Screening

**Goal**: Screen 1000 compounds to find kinase inhibitors

1. **Prepare CSV**: SMILES + IDs for 1000 compounds
2. **Batch Screening**: Upload to platform
3. **Filter**:
   - Kinase score > 70%
   - Hepatotoxicity: Low or Moderate
   - QED > 0.5
   - SA < 5
4. **Rank**: By kinase score × QED / hepatotox_risk
5. **Select Top 20**: For experimental testing

**Result**: 1000 compounds → 20 high-priority leads

---

### Workflow 4: Biologic Analysis

**Goal**: Assess therapeutic peptide developability

1. **Input**: FASTA sequence for peptide/antibody
2. **Protein Analysis**: Amino acid composition, biophysical properties
3. **Developability**: Solubility, aggregation risk, stability
4. **Protein-Ligand**: (If have target protein) compatibility scoring

**Example**: Semaglutide (GLP-1 analog for diabetes)

```
Input: HAEGTFTSDVSSYLEGQAAKEFIAWLVKGR

Analysis:
  - Type: Therapeutic peptide
  - GRAVY: -0.45 (hydrophilic)
  - Instability Index: 32 (stable)
  - Aggregation Risk: Low
  - Solubility: High
Decision: ✅ Good developability profile
```

---

## Sample Molecules & Proteins

### Small Molecules

```
# Simple molecules
Ethanol: CCO
Benzene: c1ccccc1
Acetaminophen: CC(=O)Nc1ccc(O)cc1

# FDA-approved drugs
Aspirin: CC(=O)Oc1ccccc1C(=O)O
Imatinib (Gleevec): CN1CCN(CC1)Cc2ccc(cc2)C(=O)Nc3ccc(c(c3)Nc4nccc(n4)c5cccnc5)C(F)(F)F
Warfarin: CC(=O)CC(C1=C(C2=CC=CC=C2OC1=O)O)C3=CC=CC=C3

# Kinase inhibitors
Gefitinib: COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1OCCCN4CCOCC4
Erlotinib: COCCOc1cc2ncnc(Nc3cccc(c3)C#C)c2cc1OC
```

### Peptides

```
# Insulin A-chain
>Insulin_A
GIVEQCCTSICSLYQLENYCN

# Semaglutide (GLP-1 analog)
>Semaglutide
HAEGTFTSDVSSYLEGQAAKEFIAWLVKGR

# Teriparatide (PTH 1-34)
>Teriparatide
SVSEIQLMHNLGKHLNSMERVEWLRKKLQDVHNF
```

### Target Proteins

```
# Kinase domain
>EGFR_kinase_domain
MRPSGTAGAALLALLAALCPASRALEVLA...

# GPCR
>Beta2_adrenergic_receptor
MGQPGNGSAFLLAPNRSHAPDHDVTQERDEVWVVGMGIVMSLIVLAIVFGNVLVITAIAKFERLQTVTNYFITSLACADLVMGLAVVPFGAAHILMKMWTFGNFWCEFWTSIDVLCVTASIETLCVIAVDRYFAITSPFKYQSLLTKNKARVIILMVWIVSGLTSFLPIQMHWYRATHQEAINCY...
```

---

## Interpreting Results

### Color Coding

The platform uses consistent color coding:

- 🟢 **Green / Low Risk**: Safe, favorable properties
- 🟡 **Yellow / Moderate**: Acceptable, requires monitoring
- 🔴 **Red / High Risk**: Concerning, requires attention

### Confidence Levels

**High Confidence**:
- Drug-likeness metrics (validated methods)
- Known toxic moieties (structural alerts)
- Established correlations

**Medium Confidence**:
- ADME heuristics (rule-based)
- Target class predictions (descriptor thresholds)

**Low Confidence**:
- ML models on synthetic data
- Complex toxicity endpoints (carcinogenicity)
- Novel chemical space

### When to Trust Predictions

**Trust More**:
- Drug-likeness violations (clear rules)
- Obvious structural alerts (reactive groups)
- Properties within training domain

**Trust Less**:
- Edge cases (unusual structures)
- Multiple conflicting predictions
- Novel scaffolds outside training data

### Recommendations

1. **Use as Screening Tool**: Prioritize compounds, don't make final decisions
2. **Experimental Validation Required**: All predictions must be validated
3. **Combine Multiple Predictions**: Look at overall profile, not single metric
4. **Understand Limitations**: See [VALIDATION.md](VALIDATION.md) for details

---

## Tips & Best Practices

### Input Validation

✅ **Do**:
- Use canonical SMILES when possible
- Check SMILES with online tools (e.g., PubChem, ChemSpider)
- Test with known drugs first
- Use example molecules to learn

❌ **Don't**:
- Enter invalid SMILES (will cause errors)
- Use overly long FASTA sequences (>1000 residues may be slow)
- Assume all predictions are perfect

### Efficient Workflow

1. **Start Simple**: Test aspirin or ethanol first
2. **Understand Metrics**: Read "Learn More" sections
3. **Compare**: Run both similar and different molecules
4. **Document**: Save results for later analysis
5. **Batch Process**: Use batch screening for libraries

### Performance Tips

- Close unused browser tabs (visualizations are memory-intensive)
- For large batches (>1000 molecules), use FastAPI directly
- Clear cache if issues: Settings → Clear Cache

---

## Troubleshooting

### Common Issues

#### "Invalid SMILES"

**Cause**: Malformed SMILES string

**Solution**:
- Check for typos
- Validate with: `from rdkit import Chem; Chem.MolFromSmiles('YOUR_SMILES')`
- Use example molecules to test

#### "Feature Extraction Failed"

**Cause**: RDKit cannot compute descriptors

**Solution**:
- Simplify structure
- Check for disconnected fragments
- Remove salts/counterions

#### Slow Performance

**Cause**: Large molecules or batches

**Solution**:
- Reduce batch size
- Close other applications
- Use FastAPI for production workloads

#### Unexpected Results

**Cause**: Edge case or model limitation

**Solution**:
- Review [VALIDATION.md](VALIDATION.md)
- Check if structure is in model's applicability domain
- Experimental validation recommended

---

## Getting Help

### Resources

- **Documentation**: [README.md](README.md), [METHODOLOGY.md](METHODOLOGY.md), [REFERENCES.md](REFERENCES.md)
- **Setup Issues**: [SETUP.md](SETUP.md)
- **Scientific Questions**: Read references in METHODOLOGY.md
- **GitHub Issues**: https://github.com/ardit-mishra/biostudio/issues

### Contact

- **Email**: amishra7599@gmail.com
- **GitHub**: [@ardit-mishra](https://github.com/ardit-mishra)
- **LinkedIn**: [Ardit Mishra](https://www.linkedin.com/in/ardit-mishra)

---

## Next Steps

After completing this tutorial:

1. **Explore**: Try different molecules and proteins
2. **Experiment**: Test your own compounds
3. **Learn**: Read METHODOLOGY.md for scientific details
4. **Contribute**: See [CONTRIBUTING.md](CONTRIBUTING.md) to improve the platform
5. **Validate**: Always follow up computational predictions with experiments

---

**Happy Drug Discovery!** 🧬💊

---

**Last Updated**: November 2025  
**Author**: Ardit Mishra  
**Contact**: amishra7599@gmail.com | [GitHub](https://github.com/ardit-mishra)
