# BioStudio

Computational drug discovery research platform implemented in Python using RDKit, scikit-learn, XGBoost, Streamlit, and FastAPI.

BioStudio demonstrates modular pharmaceutical data science workflows for small molecules and biologics, including molecular descriptor computation, drug-likeness assessment, ADME/PK heuristics, toxicity modeling, target class prediction, and knowledge graph exploration.

🌐 **Live Demo:** https://biostudio.arditmishra.com

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![RDKit](https://img.shields.io/badge/RDKit-2022.9-green.svg)](https://www.rdkit.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.51-red.svg)](https://streamlit.io/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.121-teal.svg)](https://fastapi.tiangolo.com/)

---

## Important Note

This platform is intended for educational and research purposes.

Current ADME/PK, toxicity, and target class predictors primarily use heuristic scoring functions derived from established molecular descriptors. For production or regulatory use, these components should be replaced with validated QSAR models trained on curated pharmaceutical datasets.

Scientific foundations and methodological references are documented in `METHODOLOGY.md` and `REFERENCES.md`.

---

## Features

### Small Molecule Analysis

- SMILES validation and canonicalization  
- RDKit molecular descriptor computation (200+ properties)  
- Morgan fingerprint generation (ECFP4, radius=2, 2048 bits)  
- Drug-likeness scoring (Lipinski Rule of 5, Veber rules, QED, Synthetic Accessibility)  
- ADME/PK heuristic scoring (LogP, permeability, BBB, CYP450, clearance)  
- Toxicity prediction  
  - Heuristic structural alerts  
  - Neural network toxicity model (DeepTox-inspired architecture)  
- Target class likelihood estimation (kinase, GPCR, ion channel, enzyme)  
- Ensemble ML predictions (Random Forest, XGBoost, Neural Network)  
- SHAP-based feature importance visualization  

### Biologic & Protein Analysis

- FASTA validation and parsing  
- Amino acid composition profiling  
- GRAVY hydrophobicity scoring (Kyte-Doolittle scale)  
- Instability index calculation  
- Aliphatic index estimation  
- Developability heuristics (solubility, aggregation risk, stability)  

### Knowledge Graph & Network Analysis

- Drug–target–disease relationship modeling  
- Mechanism-of-action exploration  
- Interactive network visualization (NetworkX / PyVis)  

### REST API

FastAPI endpoints provide programmatic access:

- `/predict/druglikeness`
- `/predict/adme`
- `/predict/toxicity`
- `/predict/target`
- `/predict/comprehensive`
- `/batch/predict`

---

## Installation

### Prerequisites

- Python 3.11
- pip or uv package manager
- NumPy < 2.0 (required for RDKit compatibility)

### Clone the Repository

```bash
git clone https://github.com/Ardit-Mishra/biostudio.git
cd biostudio
```

### Create Virtual Environment (Recommended)

```bash
python -m venv .venv
source .venv/bin/activate
```

### Install Dependencies

Using requirements:

```bash
pip install -r requirements.txt
```

Or using pyproject:

```bash
pip install -e .
```

### Run Streamlit Application

```bash
streamlit run app.py --server.port 5000
```

Application will be available at:

```
http://localhost:5000
```

### Optional: Run FastAPI Backend

```bash
uvicorn api.prediction_api:app --host 0.0.0.0 --port 8000
```

---

## Usage

### Small Molecule Workflow

1. Input SMILES string
2. Automatic descriptor calculation
3. Drug-likeness scoring
4. ADME/PK and toxicity evaluation
5. Target class prediction
6. Model explanation via SHAP

### Biologic Workflow

1. Input FASTA sequence
2. Sequence validation
3. Amino acid composition analysis
4. Developability assessment
5. Stability and aggregation risk scoring

### Programmatic Example

```python
from utils.molecular_utils import process_smiles
from models.adme_predictors import predict_adme

smiles = "CC(=O)OC1=CC=CC=C1C(=O)O"
mol_data = process_smiles(smiles)
adme_profile = predict_adme(mol_data)

print(adme_profile)
```

---

## Project Structure

```text
biostudio/
├── app.py
├── features/
│   ├── protein_utils.py
│   └── input_detector.py
├── models/
│   ├── adme_predictors.py
│   ├── toxicity_predictors.py
│   ├── neural_toxicity.py
│   ├── target_predictors.py
│   └── ml_models.py
├── utils/
│   ├── molecular_utils.py
│   ├── drug_likeness.py
│   ├── knowledge_graph.py
│   └── visualization_utils.py
├── api/
│   └── prediction_api.py
├── data/
├── tests/
├── documentation/
│   ├── SETUP.md
│   ├── TUTORIAL.md
│   ├── METHODOLOGY.md
│   ├── VALIDATION.md
│   └── REFERENCES.md
├── pyproject.toml
├── uv.lock
└── LICENSE
```

---

## API Reference

Example request:

```bash
curl -X POST "http://localhost:8000/predict/comprehensive" \
     -H "Content-Type: application/json" \
     -d '{"smiles": "CCO"}'
```

Returns structured JSON including drug-likeness, ADME/PK, toxicity, and target predictions.

---

## Testing

Run all tests:

```bash
pytest tests/ -v
```

Run with coverage:

```bash
pytest tests/ --cov=biostudio --cov-report=html
```

Reproducibility notes:

- Random seeds are fixed where applicable.
- Descriptor generation uses deterministic RDKit functions.
- Neural network model weights are documented and reproducible.

---

## Core Dependencies

| Package        | Purpose |
|---------------|---------|
| RDKit         | Molecular descriptors and cheminformatics |
| scikit-learn  | Machine learning models |
| XGBoost       | Gradient boosted trees |
| Streamlit     | Interactive web application |
| FastAPI       | REST API backend |
| SHAP          | Model interpretability |
| NetworkX      | Knowledge graph modeling |
| PyVis         | Network visualization |
| Biopython     | Protein sequence analysis |

---

## Scientific Basis

Methods implemented are grounded in established literature:

- Lipinski Rule of 5  
- Veber molecular property filters  
- QED scoring methodology  
- Morgan fingerprints  
- Random Forest and Gradient Boosting for QSAR  
- SHAP interpretability framework  
- DeepTox-inspired neural network toxicity modeling  

See `REFERENCES.md` for full citations.

---

## Reproducibility

All outputs are reproducible from source using documented installation steps.

- Deterministic descriptor computation
- Explicit dependency versions in `pyproject.toml`
- Locked environment via `uv.lock`
- Documented methodological assumptions
- Validation benchmarks described in `VALIDATION.md`

---

## Citation

If you use BioStudio in academic work, please cite:

```bibtex
@software{mishra2025biostudio,
  author = {Mishra, Ardit},
  title = {BioStudio: Modular Computational Drug Discovery Platform},
  year = {2025},
  url = {https://github.com/Ardit-Mishra/biostudio},
  version = {1.0.0}
}
```
---

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

This project is licensed under the MIT License.

---

## Author

**Ardit Mishra**

- GitHub: [@Ardit-Mishra](https://github.com/Ardit-Mishra)
- Website: https://arditmishra.com
- LinkedIn: https://linkedin.com/in/ardit-mishra

## Acknowledgments

- RDKit community for cheminformatics infrastructure
- scikit-learn and XGBoost contributors
- SHAP framework authors
- Open-source scientific computing ecosystem
