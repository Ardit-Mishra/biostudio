# 🧬 AbbVie-Aligned AI Drug Discovery Platform

**Demonstration Platform for Pharmaceutical Data Science & ML Capabilities**

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![RDKit](https://img.shields.io/badge/RDKit-2022.9-green.svg)](https://www.rdkit.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.51-red.svg)](https://streamlit.io/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.121-teal.svg)](https://fastapi.tiangolo.com/)

---

## ⚠️ Important Note

**This is a demonstration/educational platform** showcasing pharmaceutical data science workflows and ML techniques. Current ADME/PK, toxicity, and target class predictors use **heuristic scoring functions** based on RDKit molecular descriptors for demonstration purposes. For production use, these should be replaced with validated, data-driven QSAR models trained on real pharmaceutical datasets.

---

## 📋 Project Overview

This is an interactive demonstration platform that showcases practical data science and machine learning skills aligned with pharmaceutical R&D workflows at **AbbVie** and other leading biopharma companies. The application uses real molecular data (SMILES notation) and implements industry-standard pharmaceutical ML techniques to demonstrate drug discovery workflows, visualize chemical structures, and showcase model explainability.

### Purpose

Developed as part of an application for the **Associate Data Scientist role at AbbVie**, this project demonstrates:

- Deep understanding of pharmaceutical data science workflows and methodologies
- Proficiency with industry-standard cheminformatics tools (RDKit)
- Implementation of ML models used in drug discovery (Random Forest, XGBoost, Neural Networks)
- Knowledge of ADME/PK, toxicity prediction, and target class identification concepts
- Ability to build interactive applications showcasing pharmaceutical AI/ML capabilities

---

## 🎯 Key Features

### Core Capabilities

- **🔬 Molecular Processing**: SMILES validation, descriptor calculation, fingerprint generation
- **💊 ADME/PK Prediction**: LogP, Caco-2 permeability, BBB penetration, CYP450 metabolism, clearance
- **⚠️ Toxicity Profiling**: Hepatotoxicity, hERG inhibition, mutagenicity (Ames), carcinogenicity
- **🎯 Target Class Prediction**: Kinase, GPCR, ion channel, enzyme inhibitor likelihood
- **📊 Drug-Likeness Scoring**: Lipinski Rule of 5, Veber descriptors, QED, Synthetic Accessibility
- **🤖 Multi-Model ML**: Random Forest, XGBoost, Neural Network ensemble predictions
- **📈 Model Explainability**: SHAP values, feature importance visualization
- **🧠 Knowledge Graph**: Drug-target-disease relationships with interactive exploration
- **📁 Batch Screening**: CSV upload for high-throughput lead prioritization
- **🔌 FastAPI Backend**: REST API endpoints demonstrating pharmaceutical prediction services
- **📚 Case Study**: "Ranking Potential Kinase Inhibitor Leads" demonstration

### AbbVie-Specific Alignment

This platform mirrors workflows and methodologies used at AbbVie:

1. **ADME/PK Focus**: Critical for small-molecule development (similar to Humira, Imbruvica pipeline)
2. **Kinase Inhibitor Analysis**: Central to AbbVie's oncology portfolio
3. **Toxicity Risk Assessment**: hERG, hepatotoxicity, mutagenicity - standard pharma safety screens
4. **Multi-Model Approach**: Ensemble predictions improve robustness for regulatory submissions
5. **Knowledge Graphs**: Drug-target-disease mapping for precision medicine initiatives

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
- **Uvicorn**: ASGI server for production deployment
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
git clone <repository-url>
cd abbvie-drug-discovery

# Install dependencies
pip install -r requirements.txt

# Run the Streamlit app
streamlit run app.py --server.port 5000

# (Optional) Run the FastAPI backend
uvicorn api.prediction_api:app --host 0.0.0.0 --port 8000
```

### Dependencies

Core packages:
- streamlit>=1.51.0
- rdkit-pypi>=2022.9.5
- scikit-learn>=1.7.2
- xgboost>=3.1.1
- fastapi>=0.121.2
- pandas, numpy, matplotlib, seaborn, plotly
- networkx, pyvis, umap-learn
- uvicorn, pydantic, biopython

---

## 📖 Usage Guide

### 1. Molecule Input & Analysis

```python
# Enter SMILES string
smiles = "CC(C)Cc1ccc(cc1)C(C)C(=O)O"  # Ibuprofen

# Platform validates, canonicalizes, and displays:
# - 2D structure visualization
# - Basic molecular properties
# - Drug-likeness quick check
```

### 2. ADME/PK Prediction

Comprehensive absorption, distribution, metabolism, and excretion analysis:

- **LogP**: Lipophilicity and membrane permeability indicator
- **Caco-2**: Intestinal absorption prediction
- **BBB Penetration**: Blood-brain barrier permeability
- **CYP450 Metabolism**: Drug-drug interaction assessment
- **Clearance**: Elimination half-life estimation

### 3. Toxicity Risk Assessment

Multi-endpoint toxicity profiling:

- **Hepatotoxicity**: Liver toxicity risk
- **hERG Inhibition**: Cardiotoxicity and QT prolongation
- **Mutagenicity**: Ames test prediction
- **Carcinogenicity**: Long-term safety assessment

### 4. Target Class Prediction

Identify probable protein target classes:

- Kinase inhibitor likelihood
- GPCR ligand probability
- Ion channel modulator potential
- General enzyme inhibitor characteristics

### 5. ML Models & Explainability

Ensemble predictions with transparency:

- Random Forest, XGBoost, Neural Network predictions
- SHAP values for feature attribution
- Top 15 most important molecular descriptors
- Cross-validated performance metrics

### 6. Knowledge Graph Explorer

Interactive drug-target-disease network:

- Query drug mechanisms of action
- Find drugs targeting specific proteins
- Explore disease-target associations
- Visualize biological pathways

### 7. Batch Screening

High-throughput lead prioritization:

- Upload CSV with SMILES strings
- Rank compounds by drug-likeness
- Export results for further analysis
- Compare multiple candidates simultaneously

---

## 🧪 Case Study: Ranking Kinase Inhibitor Leads

The platform includes a built-in pharmaceutical workflow demonstration:

**Scenario**: Evaluate 5 potential kinase inhibitor candidates

**Evaluation Criteria**:
1. ADME/PK properties (permeability, BBB penetration, metabolism)
2. Toxicity profile (hepatotoxicity, hERG, mutagenicity)
3. Drug-likeness (Lipinski, Veber, QED, SA score)
4. Kinase inhibitor likelihood
5. Overall lead-like score

**Output**: Ranked list with detailed property breakdown

This mirrors real-world lead optimization workflows at AbbVie.

---

## 🔌 API Endpoints (FastAPI)

### Available Endpoints

```python
GET  /                          # API information
POST /predict/druglikeness      # Lipinski, Veber, QED, SA score
POST /predict/adme              # ADME/PK profile
POST /predict/toxicity          # Toxicity risk assessment
POST /predict/target            # Target class prediction
POST /predict/comprehensive     # All predictions combined
POST /batch/predict             # Batch processing
```

### Example Request

```python
import requests

response = requests.post(
    "http://localhost:8000/predict/comprehensive",
    json={
        "smiles": "CC(C)Cc1ccc(cc1)C(C)C(=O)O",
        "name": "Ibuprofen"
    }
)

print(response.json())
```

---

## 📊 Model Training & Validation

### Cross-Validation Strategy

- **5-fold cross-validation** for model robustness
- **Train/test split**: 80/20
- **Performance metrics**: Accuracy, precision, recall, AUC-ROC

### Hyperparameter Tuning

- Random Forest: 100 estimators, max_depth=10
- XGBoost: 100 estimators, learning_rate=0.1, max_depth=6
- Neural Network: Single hidden layer, sigmoid activation

### Feature Engineering

- 200+ molecular descriptors
- Morgan fingerprints (radius=2, 2048 bits)
- Standard scaling for neural networks

---

## 🏢 Alignment with AbbVie's ML Workflows

### Research & Publications Alignment

This platform echoes AbbVie's published approaches to AI/ML in drug discovery:

1. **Random Forest & XGBoost**: Standard models for QSAR in pharmaceutical industry
2. **ADME/PK Prediction**: Core to small-molecule optimization (e.g., Rinvoq, Venclexta development)
3. **Kinase Inhibitor Focus**: Reflects AbbVie's oncology pipeline (BCR-ABL, JAK inhibitors)
4. **Multi-parameter Optimization**: Balancing efficacy, safety, and PK properties
5. **Explainable AI**: SHAP values support regulatory documentation requirements

### Regulatory Considerations

- **Model transparency**: Feature importance and decision pathways
- **Validation protocols**: Cross-validation and hold-out test sets
- **Documentation**: Clear methodology and limitations
- **SDTM compatibility**: Output format considerations for clinical data

---

## 📚 References & Industry Standards

### Drug-Likeness Rules
- Lipinski, C. A. (2004). Lead- and drug-like compounds. *Drug Discovery Today*
- Veber, D. F. et al. (2002). Molecular properties that influence oral bioavailability. *JMED*

### ADME/PK Prediction
- Hou, T. & Wang, J. (2008). Structure-ADME relationship. *Expert Opinion Drug Metab Toxicol*
- Lombardo, F. et al. (2004). In silico ADME prediction. *Drug Discovery Today*

### Toxicity Prediction
- Cheng, A. & Dixon, S. L. (2003). In silico models for hERG inhibition. *JCIM*
- Kazius, J. et al. (2005). Derivation and validation of Ames mutagenicity. *JMED*

### ML in Drug Discovery
- Chen, H. et al. (2018). The rise of deep learning in drug discovery. *Drug Discovery Today*
- Vamathevan, J. et al. (2019). Applications of machine learning in drug discovery. *Nature Reviews Drug Discovery*

---

## 🎓 Skills Demonstrated

### Data Science
- Feature engineering from molecular structures
- Multi-model ensemble predictions
- Cross-validation and model evaluation
- Dimensionality reduction (UMAP)
- Clustering and similarity analysis

### Cheminformatics
- SMILES processing and validation
- Molecular descriptor calculation
- Fingerprint generation and comparison
- Structure-activity relationship modeling
- Drug-likeness assessment

### Software Engineering
- Modular, maintainable codebase
- REST API development (FastAPI)
- Interactive web applications (Streamlit)
- Version control and documentation
- Production-ready deployment

### Domain Knowledge
- Pharmaceutical R&D workflows
- ADME/PK principles
- Toxicology and safety assessment
- Target class identification
- Regulatory compliance considerations

---

## 🔮 Future Enhancements

### Phase 2 Additions (Planned)

1. **Protein Language Models**: ESM-2/ProtBERT integration for antibody analysis
2. **Molecule Optimization**: AI-powered analog generation using BRICS decomposition
3. **Expanded Knowledge Graph**: Integration with ChEMBL, PubChem, DrugBank
4. **Cloud Deployment**: AWS/GCP deployment with scalable infrastructure
5. **Advanced Visualizations**: 3D molecular structures, interactive pathway maps
6. **Regulatory Module**: SDTM format export, FDA guideline alignment
7. **Multi-task Learning**: Joint prediction of multiple endpoints
8. **Active Learning**: Iterative model improvement with user feedback

---

## 📄 License

This project is developed for educational and demonstration purposes as part of a job application.

---

## 👤 Author

**[Your Name]**

- **Position Applied**: Associate Data Scientist at AbbVie
- **LinkedIn**: [Your LinkedIn]
- **GitHub**: [Your GitHub]
- **Email**: [Your Email]

---

## 🙏 Acknowledgments

- **RDKit community** for the excellent cheminformatics toolkit
- **AbbVie** for inspiration from their groundbreaking work in pharmaceutical AI
- **Hugging Face** for transformer model infrastructure
- **scikit-learn team** for robust ML implementations

---

## 📞 Contact

For questions about this project or to discuss pharmaceutical AI/ML applications:

- **Email**: [Your email]
- **LinkedIn**: [Your LinkedIn URL]
- **Portfolio**: [Your website]

---

<div align="center">

**Built with** ❤️ **for pharmaceutical data science**

🧬 RDKit • 🤖 scikit-learn • ⚡ XGBoost • 🎨 Streamlit • 🚀 FastAPI

*Demonstrating pharmaceutical AI/ML workflows and data science capabilities*

</div>
