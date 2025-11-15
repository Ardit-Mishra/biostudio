# AI-Powered Drug Discovery Platform

## ⚠️ Important Note

**This is an educational/research platform** demonstrating pharmaceutical data science workflows and machine learning techniques used in modern drug discovery. Current ADME/PK, toxicity, and target class predictors use **heuristic scoring functions** based on RDKit molecular descriptors. For production applications, these should be replaced with validated, data-driven QSAR models trained on curated pharmaceutical datasets.

## Project Overview

An open-source platform demonstrating computational drug discovery workflows using cheminformatics, QSAR modeling, and machine learning. This project provides well-documented, replicable implementations of pharmaceutical AI/ML techniques for educational and research purposes.

## Key Features

- **ADME/PK Prediction**: LogP, Caco-2, BBB penetration, CYP450 metabolism, clearance *(heuristic-based)*
- **Toxicity Profiling**: Hepatotoxicity, hERG, mutagenicity (Ames), carcinogenicity *(heuristic-based)*
- **Target Class Prediction**: Kinase, GPCR, ion channel, enzyme inhibitors *(heuristic-based)*
- **Drug-Likeness**: Lipinski, Veber, QED, Synthetic Accessibility scores  
- **ML Models**: Random Forest, XGBoost, Neural Network ensemble *(trained on synthetic data)*
- **Knowledge Graph**: Drug-target-disease relationships *(demonstration dataset)*
- **FastAPI Backend**: REST API endpoints demonstrating pharmaceutical prediction services
- **Batch Screening**: High-throughput lead prioritization workflow demonstration
- **Case Study**: "Ranking Potential Kinase Inhibitor Leads" educational example

## Technology Stack

- **Cheminformatics**: RDKit (molecular descriptors, fingerprints, visualization)
- **ML/AI**: scikit-learn, XGBoost, UMAP
- **Backend**: FastAPI, Uvicorn
- **Frontend**: Streamlit
- **Data**: NetworkX (knowledge graphs), Pandas, NumPy

## Architecture

```
├── app.py                    # Main Streamlit application
├── utils/
│   ├── molecular_utils.py    # SMILES validation, descriptors, fingerprints
│   ├── drug_likeness.py      # Lipinski, Veber, QED, SA score calculators
│   ├── knowledge_graph.py    # Drug-target-disease network
│   └── visualization_utils.py # Molecular viz, plots, clustering
├── models/
│   ├── adme_predictors.py    # ADME/PK prediction models
│   ├── toxicity_predictors.py # Toxicity risk assessment
│   ├── target_predictors.py  # Target class prediction
│   └── ml_models.py          # RF, XGBoost, Neural Network
├── api/
│   └── prediction_api.py     # FastAPI REST endpoints
├── data/
│   └── kinase_inhibitors.py  # Case study data
└── README.md                 # Comprehensive documentation

```

## Running the Application

### Streamlit Web App
```bash
streamlit run app.py --server.port 5000
```

### FastAPI Backend (Optional)
```bash
uvicorn api.prediction_api:app --host 0.0.0.0 --port 8000
```

## Key Implementation Notes

### Dependency Management
- **NumPy Version**: Must use NumPy <2.0 for RDKit compatibility
- **Python Version**: 3.11 (constrained in pyproject.toml)
- **RDKit**: Version 2022.9.5 compiled against NumPy 1.x

### Model Implementation
- **ADME/Toxicity/Target Predictors**: Currently use heuristic scoring functions based on RDKit molecular descriptors
- **ML Models**: Ensemble approach with Random Forest, XGBoost, and simple Neural Network
- **Training**: Models trained on synthetic pharmaceutical dataset  
- **Future Enhancement**: Replace heuristics with data-driven trained models

### Industry-Standard Workflows
This platform demonstrates pharmaceutical industry best practices:
1. **ADME/PK Focus**: Critical for small-molecule drug development
2. **Kinase Inhibitor Analysis**: Important target class in oncology
3. **Multi-model Ensemble**: Standard practice for robust predictions
4. **Model Explainability**: Feature importance for regulatory compliance
5. **Knowledge Graphs**: Drug-target-disease relationship mapping

## Recent Changes

### 2025-11-15
- Fixed NumPy 2.x compatibility issue with RDKit
- Downgraded NumPy from 2.3.4 to 1.26.4
- Updated pyproject.toml to constrain `numpy>=1.24,<2.0`
- Application now runs successfully on port 5000

## Known Issues & Limitations

1. **Protein Language Models**: Deferred due to transformers dependency resolution issues
2. **Placeholder Image**: External placeholder.com images may not load (minor UI issue)
3. **Streamlit Deprecation Warnings**: `use_container_width` warnings (functionality unaffected)
4. **Model Training**: Currently using synthetic data; future versions should use real pharmaceutical datasets

## Future Enhancements (Phase 2)

- Integrate ESM-2/ProtBERT for antibody analysis
- AI-powered molecule optimization (BRICS decomposition)
- Expanded knowledge graph with ChEMBL/PubChem integration  
- Cloud deployment (AWS/GCP)
- 3D molecular visualization
- SDTM format export for regulatory compliance
- Multi-task learning for joint endpoint prediction

## Project Status

✅ Core cheminformatics modules implemented  
✅ ADME/PK and toxicity prediction functional  
✅ Target class prediction operational  
✅ ML models with ensemble predictions  
✅ Knowledge graph explorer  
✅ FastAPI backend with REST endpoints  
✅ Streamlit UI with 10 pages  
✅ Case study demonstration  
✅ Comprehensive README documentation  
⏳ Protein language model integration (pending dependency resolution)  

## About

Open-source pharmaceutical AI/ML research platform  
Developed by Ardit Mishra (github.com/ardit-mishra)  
Demonstrating computational drug discovery workflows with comprehensive documentation
