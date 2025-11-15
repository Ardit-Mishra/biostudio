# AI-Powered Drug Discovery Platform

**Open-Source Research Platform for Computational Drug Discovery**

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![RDKit](https://img.shields.io/badge/RDKit-2022.9-green.svg)](https://www.rdkit.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.51-red.svg)](https://streamlit.io/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.121-teal.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## ⚠️ Important Note

**This is an educational/research platform** demonstrating pharmaceutical data science workflows and machine learning techniques used in modern drug discovery. Current ADME/PK, toxicity, and target class predictors use **heuristic scoring functions** based on RDKit molecular descriptors. For production applications, these should be replaced with validated, data-driven QSAR models trained on curated pharmaceutical datasets.

**All methods are backed by peer-reviewed research.** See [`references.md`](references.md) for complete scientific citations.

---

## 📋 Project Overview

This project is an open-source platform demonstrating computational drug discovery workflows using cheminformatics, QSAR modeling, and machine learning. It provides well-documented, replicable implementations of pharmaceutical AI/ML techniques for educational and research purposes.

### Purpose

This platform demonstrates:

- Pharmaceutical data science workflows and methodologies
- Proficiency with industry-standard cheminformatics tools (RDKit)
- Implementation of ML models used in drug discovery (Random Forest, XGBoost, Neural Networks)
- ADME/PK, toxicity prediction, and target class identification methods
- Interactive applications for pharmaceutical AI/ML exploration
- **Complete documentation and scientific citations for all methods**

### Goals

1. **Education**: Provide hands-on learning resource for computational drug discovery
2. **Replicability**: Fully documented code allowing others to understand and extend
3. **Research**: Demonstrate integration of modern ML techniques in pharmaceutical workflows
4. **Transparency**: Clear distinction between heuristic methods and data-driven models

---

## 🎯 Key Features

### Core Capabilities

- **Molecular Processing**: SMILES validation, descriptor calculation, fingerprint generation
- **ADME/PK Prediction**: LogP, Caco-2 permeability, BBB penetration, CYP450 metabolism, clearance
- **Toxicity Profiling**: Hepatotoxicity, hERG inhibition, mutagenicity (Ames), carcinogenicity
- **Target Class Prediction**: Kinase, GPCR, ion channel, enzyme inhibitor likelihood
- **Drug-Likeness Scoring**: Lipinski Rule of 5, Veber descriptors, QED, Synthetic Accessibility
- **Multi-Model ML**: Random Forest, XGBoost, Neural Network ensemble predictions
- **Model Explainability**: SHAP values, feature importance visualization
- **Knowledge Graph**: Drug-target-disease relationships with interactive exploration
- **Batch Screening**: CSV upload for high-throughput lead prioritization
- **FastAPI Backend**: REST API endpoints for pharmaceutical predictions
- **Case Study**: "Ranking Potential Kinase Inhibitor Leads" demonstration

### Industry Alignment

This platform demonstrates pharmaceutical industry best practices:

1. **ADME/PK Focus**: Critical for small-molecule drug development
2. **Kinase Inhibitor Analysis**: Important target class in oncology research
3. **Toxicity Risk Assessment**: hERG, hepatotoxicity, mutagenicity screening
4. **Multi-Model Approach**: Ensemble predictions for robust predictions
5. **Knowledge Graphs**: Drug-target-disease relationship mapping

---

## 🛠️ Technology Stack

### Machine Learning & AI
- **scikit-learn**: Random Forest, preprocessing, cross-validation
- **XGBoost**: Gradient boosting for robust predictions
- **SHAP**: Model explainability and feature importance
- **UMAP**: Dimensionality reduction for molecular clustering

### Cheminformatics
- **RDKit**: Molecular descriptor calculation, fingerprints, structure visualization
- **SMILES Processing**: Molecular validation and canonicalization
- **Molecular Descriptors**: 200+ physicochemical properties

### Backend & API
- **FastAPI**: Modern, high-performance REST API
- **Uvicorn**: ASGI server
- **Pydantic**: Data validation and serialization

### Frontend
- **Streamlit**: Interactive web application framework
- **Plotly**: Interactive visualizations
- **Matplotlib/Seaborn**: Statistical plots

### Data & Knowledge
- **NetworkX**: Knowledge graph construction
- **PyVis**: Interactive network visualization
- **Pandas/NumPy**: Data manipulation and analysis

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.11
- pip or uv package manager

### Quick Start

```bash
# Clone the repository
git clone https://github.com/ardit-mishra/drug-discovery-platform.git
cd drug-discovery-platform

# Install dependencies
pip install -r requirements.txt
# OR using uv
uv pip install -r requirements.txt

# Run the Streamlit app
streamlit run app.py --server.port 5000

# (Optional) Run the FastAPI backend
uvicorn api.prediction_api:app --host 0.0.0.0 --port 8000
```

### Dependencies

Core packages (see `pyproject.toml` for complete list):
- streamlit>=1.51.0
- rdkit-pypi>=2022.9.5
- scikit-learn>=1.7.2
- xgboost>=3.1.1
- fastapi>=0.121.2
- pandas, numpy<2.0 (RDKit compatibility), matplotlib, seaborn, plotly
- networkx, pyvis, umap-learn
- uvicorn, pydantic, biopython

**Important**: NumPy must be <2.0 for RDKit compatibility. See [`SETUP.md`](SETUP.md) for detailed installation instructions.

---

## 📖 Documentation

This project is fully documented for educational and research purposes:

- **[SETUP.md](SETUP.md)**: Detailed installation instructions and troubleshooting
- **[TUTORIAL.md](TUTORIAL.md)**: Step-by-step guide to using the platform
- **[METHODOLOGY.md](METHODOLOGY.md)**: Scientific basis for all prediction methods
- **[REFERENCES.md](REFERENCES.md)**: Complete scientific citations and bibliography
- **[CONTRIBUTING.md](CONTRIBUTING.md)**: Guidelines for contributions

### Code Documentation

All code includes:
- **Detailed docstrings** for every function
- **Inline comments** explaining complex logic
- **Scientific references** linking methods to literature
- **Type hints** for clarity and maintainability

---

## 🧪 Modules & Features

### 1. Molecular Processing (`utils/molecular_utils.py`)

- SMILES validation and canonicalization
- Molecular descriptor calculation (200+ properties)
- Fingerprint generation (Morgan, MACCS, Topological)
- Basic property calculation (MW, LogP, HBA, HBD)

**Methods referenced**: RDKit documentation, Wildman-Crippen LogP¹, Lipinski descriptors²

### 2. Drug-Likeness Assessment (`utils/drug_likeness.py`)

- **Lipinski Rule of 5**: Oral bioavailability prediction²
- **Veber Rules**: Rotatable bonds and TPSA criteria³
- **QED Score**: Quantitative Estimate of Drug-likeness⁴
- **Synthetic Accessibility**: Ease of synthesis prediction⁵

### 3. ADME/PK Prediction (`models/adme_predictors.py`)

- **LogP**: Lipophilicity (Wildman-Crippen method)¹
- **Caco-2 Permeability**: Intestinal absorption model⁶
- **BBB Penetration**: Blood-brain barrier permeability⁷
- **CYP450 Metabolism**: Cytochrome P450 substrate prediction⁸
- **Clearance Estimation**: Hepatic clearance models⁹

**Note**: Current implementations use heuristic scoring. See `METHODOLOGY.md` for details and `REFERENCES.md` for literature on validated QSAR models.

### 4. Toxicity Prediction (`models/toxicity_predictors.py`)

- **Hepatotoxicity**: Liver toxicity risk assessment¹⁰
- **hERG Inhibition**: Cardiotoxicity screening¹¹,¹²
- **Ames Mutagenicity**: Genetic toxicity prediction¹³
- **Carcinogenicity**: Long-term cancer risk¹⁴

**Note**: State-of-the-art models achieve AUC 0.90-0.96 for hERG using Graph Neural Networks¹². Current heuristic implementation is for demonstration.

### 5. Target Class Prediction (`models/target_predictors.py`)

- **Kinase Inhibitors**: Protein kinase targeting likelihood
- **GPCR Modulators**: G-protein coupled receptor activity
- **Ion Channel Blockers**: Ion channel interaction prediction
- **Enzyme Inhibitors**: General enzyme inhibition potential

### 6. Machine Learning Models (`models/ml_models.py`)

- **Random Forest**: Ensemble decision trees for classification¹⁵
- **XGBoost**: Gradient boosted trees for robust predictions¹⁶
- **Neural Networks**: Simple feedforward architecture
- **Ensemble Predictions**: Combining multiple models
- **Feature Importance**: SHAP values for interpretability¹⁷

### 7. Knowledge Graph (`utils/knowledge_graph.py`)

- Drug-target-disease relationship network
- Mechanism of action queries
- Target information lookup
- Disease pathway mapping

### 8. API Endpoints (`api/prediction_api.py`)

RESTful API for programmatic access:
- `/predict/druglikeness`: Lipinski, Veber, QED, SA scores
- `/predict/adme`: ADME/PK property predictions
- `/predict/toxicity`: Toxicity risk assessment
- `/predict/target`: Target class predictions
- `/predict/comprehensive`: Complete molecular profile
- `/batch/predict`: High-throughput batch processing

---

## 💡 Use Cases

### 1. Educational Platform

- Learn computational drug discovery workflows
- Understand QSAR modeling concepts
- Explore ML applications in pharmaceutical research
- Study molecular property prediction methods

### 2. Research Tool

- Rapid screening of compound libraries
- Lead optimization prioritization
- Toxicity liability identification
- Multi-parameter optimization exploration

### 3. Method Development

- Benchmark for custom QSAR models
- Platform for integrating new predictors
- Knowledge graph expansion
- API integration testing

---

## 📚 Case Study: Kinase Inhibitor Lead Ranking

The platform includes a complete case study demonstrating:

1. **Multi-parameter optimization**: Balancing efficacy, safety, and PK properties
2. **Data-driven decision making**: ML-based candidate ranking
3. **Risk mitigation**: Early identification of potential liabilities

Example candidates evaluated:
- Imatinib-like scaffold (BCR-ABL inhibitor)
- Gefitinib-like scaffold (EGFR inhibitor)
- Novel kinase inhibitor scaffolds

Evaluation criteria:
- ADME/PK properties
- Toxicity profile
- Drug-likeness scores
- Target class probability
- Overall lead-like score

---

## 🔬 Scientific Rigor

All methods implemented in this platform are based on peer-reviewed research:

### Pharmaceutical Standards
- Lipinski Rule of 5 for oral bioavailability²
- Veber rules for drug-likeness³
- QED scoring methodology⁴
- Synthetic accessibility scoring⁵

### QSAR Methodologies
- Graph Neural Networks for toxicity (AUC 0.96)¹²
- Random Forest for ADME prediction¹⁵
- XGBoost for robust multi-task learning¹⁶
- SHAP for model interpretability¹⁷

### Literature References

Complete citations available in [`REFERENCES.md`](REFERENCES.md), including:

1. Wildman & Crippen (1999) - LogP calculation
2. Lipinski et al. (2001) - Rule of 5
3. Veber et al. (2002) - Molecular property filters
4. Bickerton et al. (2012) - QED score
5. Ertl & Schuffenhauer (2009) - Synthetic accessibility
6-17. [See REFERENCES.md for complete bibliography]

---

## 🛣️ Roadmap

### Phase 2 Enhancements

- [ ] **Validated QSAR Models**: Replace heuristics with trained models on curated datasets
- [ ] **Protein Language Models**: ESM-2/ProtBERT for antibody analysis
- [ ] **AI-Powered Optimization**: BRICS-based molecular generation
- [ ] **Expanded Knowledge Graph**: ChEMBL/PubChem integration
- [ ] **3D Molecular Visualization**: Interactive 3D structure viewer
- [ ] **Cloud Deployment**: AWS/GCP containerized deployment
- [ ] **Regulatory Export**: SDTM format for FDA submissions
- [ ] **Multi-task Learning**: Joint endpoint prediction models

---

## 🤝 Contributing

Contributions are welcome! Please see [`CONTRIBUTING.md`](CONTRIBUTING.md) for guidelines.

Areas particularly welcome:
- Integration of validated QSAR models from literature
- Addition of new molecular descriptors
- Knowledge graph expansion
- Documentation improvements
- Bug fixes and performance optimizations

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Ardit Mishra**

- GitHub: [@ardit-mishra](https://github.com/ardit-mishra)
- Email: [Your email]
- LinkedIn: [Your LinkedIn]

---

## 🙏 Acknowledgments

- **RDKit community** for the excellent cheminformatics toolkit
- **scikit-learn team** for robust ML implementations
- **Hugging Face** for transformer model infrastructure
- **Pharmaceutical research community** for published QSAR datasets and methodologies

---

## 📞 Contact

For questions about this project or to discuss pharmaceutical AI/ML applications:

- Open an issue on GitHub
- Email: [Your email]

---

<div align="center">

**Built with 🧬 for pharmaceutical research**

RDKit • scikit-learn • XGBoost • Streamlit • FastAPI

*Demonstrating computational drug discovery workflows with comprehensive documentation*

</div>
