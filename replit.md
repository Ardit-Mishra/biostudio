# BioStudio

## Overview

BioStudio is an AI-powered molecular intelligence platform for computational drug discovery. It provides interactive tools for analyzing small molecules and proteins, including drug-likeness assessment, ADME/PK prediction, toxicity profiling, target class prediction, protein-ligand compatibility scoring, and biomedical knowledge graph exploration.

The platform is primarily educational and research-oriented. It implements a mix of validated industry-standard methods (Lipinski Rule of 5, Veber rules, QED scoring) and demonstration/heuristic models (ADME predictions, toxicity scoring, target prediction). Neural network models are trained on synthetic data as proof-of-concept. All methods are backed by peer-reviewed scientific references documented in REFERENCES.md.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend: Streamlit Web Application
- **Entry point**: `app.py` — the main Streamlit application
- **Framework**: Streamlit (v1.51) for interactive web UI with custom CSS styling
- **Pages/Modules**: Home, Molecule Studio, ADME Navigator, Toxicity Radar, Drug-Likeness Deck, Target Prediction, Protein & Biologic Studio, Explainability Canvas, Knowledge Graph, Lead Lab, Case Study, About
- **Run command**: `streamlit run app.py --server.port 5000`
- **Caching**: Uses `@st.cache_resource` for model persistence

### Backend: Python Modules
The backend is organized into four main directories:

- **`utils/`** — Core utilities
  - `molecular_utils.py`: SMILES validation, molecular property calculation, fingerprint generation, shared `MolecularFeatureExtractor` class (30 RDKit descriptors + 2048 Morgan fingerprint bits), and `MolecularProcessor` class
  - `drug_likeness.py`: Lipinski Rule of 5, Veber rules, QED scoring, synthetic accessibility
  - `knowledge_graph.py`: Biomedical knowledge graph with 70+ FDA-approved drugs, uses NetworkX and PyVis for visualization
  - `visualization_utils.py`: Molecular structure images, radar charts, feature importance plots using Matplotlib, Seaborn, Plotly, and RDKit Draw

- **`models/`** — Prediction models
  - `adme_predictors.py`: Heuristic ADME/PK predictions (absorption, distribution, metabolism, excretion)
  - `toxicity_predictors.py`: Rule-based toxicity scoring (hepatotoxicity, hERG, mutagenicity, carcinogenicity)
  - `neural_toxicity.py`: Neural network toxicity predictor (synthetic weights, 4-endpoint prediction)
  - `target_predictors.py`: Heuristic target class prediction (kinase, GPCR, ion channel, enzyme)
  - `protein_ligand_compatibility.py`: Neural network binding compatibility scorer (protein + ligand features)
  - `ml_models.py`: Multi-model ensemble (Random Forest, XGBoost) for drug-likeness prediction

- **`features/`** — Input processing
  - `input_detector.py`: Intelligent input type detection (SMILES vs peptide vs protein)
  - `protein_utils.py`: Protein sequence analysis (FASTA parsing, amino acid composition, hydrophobicity, instability index)

- **`data/`** — Reference data
  - `example_molecules.py`: Curated library of small molecules, peptides, and protein biologics
  - `kinase_inhibitors.py`: Case study data for kinase inhibitor lead ranking

### REST API: FastAPI
- **Entry point**: `api/prediction_api.py`
- **Run command**: `uvicorn api.prediction_api:app --host 0.0.0.0 --port 8000`
- **Endpoints**: Drug-likeness, ADME/PK, toxicity, target prediction, comprehensive analysis, batch processing
- **Data validation**: Pydantic models for request/response schemas

### Key Design Decisions

1. **Shared Feature Extraction**: The `MolecularFeatureExtractor` class in `utils/molecular_utils.py` provides a single source of truth for molecular feature extraction (30 RDKit descriptors + 2048 Morgan fingerprint bits), used by both `neural_toxicity.py` and `protein_ligand_compatibility.py`. This eliminates code duplication.

2. **Heuristic vs. Validated Models**: The platform clearly distinguishes between validated industry standards (Lipinski, Veber, QED, SA) and heuristic/demonstration models (ADME, toxicity, target prediction). Neural networks use synthetic weights — real training data would be needed for production use.

3. **No Database**: The application is stateless with no database. All data is computed on-the-fly or loaded from Python data files. If adding persistence, consider PostgreSQL with Drizzle ORM.

4. **Dual Interface**: Both Streamlit (interactive UI on port 5000) and FastAPI (programmatic API on port 8000) serve the same underlying prediction modules.

### Testing
- **Framework**: pytest
- **Location**: `tests/` directory
- **Test files**: `test_molecular_utils.py` (15 tests), `test_drug_likeness.py` (12 tests)
- **Run**: `pytest tests/ -v`

### Python Version
- **Required**: Python 3.11 (for RDKit compatibility)
- **Critical**: NumPy must be < 2.0 for RDKit compatibility

## External Dependencies

### Core Libraries
- **RDKit** (2022.9): Industry-standard cheminformatics toolkit for molecular operations, descriptor calculation, fingerprints, and 2D visualization
- **Streamlit** (1.51): Web application framework for the interactive frontend
- **FastAPI** (0.121): REST API framework with automatic OpenAPI documentation
- **Pydantic**: Request/response validation for the FastAPI layer

### Scientific Computing
- **NumPy** (< 2.0 required): Numerical operations, array handling for molecular descriptors and fingerprints
- **Pandas**: Data manipulation and tabular display
- **scikit-learn**: Machine learning models (RandomForest, StandardScaler, cross-validation)
- **XGBoost**: Gradient boosting models for ensemble predictions

### Visualization
- **Matplotlib**: Static plotting
- **Seaborn**: Statistical visualizations
- **Plotly**: Interactive charts and radar plots
- **PyVis**: Interactive network graph visualization for knowledge graph
- **Pillow (PIL)**: Image processing for molecular structure rendering

### Graph Analysis
- **NetworkX**: Graph data structures and algorithms for the biomedical knowledge graph

### Frontend Libraries (static assets in `lib/`)
- **vis-network** (9.1.2): Browser-based network visualization (used by PyVis-generated HTML)
- **tom-select** (2.0.0-rc.4): Enhanced select/input UI components

### No External APIs or Databases
The platform is self-contained with no external API calls, no database connections, and no authentication system. All computations run locally using RDKit and scikit-learn.