# Changelog

All notable changes to **Ardit BioCore** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.2.0] - 2025-11-16

### Added
- **Code Refactoring**: Created shared `MolecularFeatureExtractor` class in `utils/molecular_utils.py`
  - Eliminates ~80 lines of duplicate code between `neural_toxicity.py` and `protein_ligand_compatibility.py`
  - Centralized molecular feature extraction (30 RDKit descriptors + 2048 Morgan fingerprint bits)
  - Improved maintainability and consistency across neural network models

### Fixed
- Type annotation errors in `features/protein_utils.py` (changed `any` → `Any`)
- All LSP type checking errors resolved

### Changed
- `models/neural_toxicity.py` now uses shared `MolecularFeatureExtractor`
- `models/protein_ligand_compatibility.py` now uses shared `MolecularFeatureExtractor`
- Improved code quality with single source of truth for feature extraction

---

## [1.1.0] - 2025-11-15

### Added
- **Protein-Ligand Compatibility Scorer**: Neural network-based binding prediction
  - 5-layer architecture: 2102 → 512 → 256 → 128 → 64 → 1
  - Combines 24 protein biophysical features + 2078 ligand features
  - Outputs binding probability (0-100%) with compatibility categories
  - Referenced methods: Ragoza et al. (2017), Jiménez et al. (2018)

- **Enhanced Protein Analysis**:
  - FASTA header parsing improvements with `_clean_protein_sequence()` helper
  - Consistent sequence handling across all protein-related modules
  - Better error messages for invalid sequences

### Fixed
- Critical FASTA parsing bugs in protein sequence validation
- Improved handling of multi-line FASTA sequences
- Fixed edge cases in protein feature extraction

---

## [1.0.0] - 2025-11-15

### Added
- **Neural Network Toxicity Predictor**: Deep learning model for multi-endpoint toxicity
  - Architecture: 2078 → 1024 → 512 → 256 → 128 → 1 (5 layers)
  - Features: 30 RDKit descriptors + 2048 Morgan fingerprint bits (ECFP4)
  - Endpoints: Hepatotoxicity, Cardiotoxicity (hERG), Mutagenicity, Carcinogenicity
  - Side-by-side comparison with heuristic toxicity predictions
  - Methodology based on DeepTox architecture (Mayr et al. 2016)

- **Biologic & Protein Analysis Suite**:
  - FASTA format validation and sequence processing
  - Amino acid composition analysis (20 amino acids + category summaries)
  - Biophysical properties: GRAVY, Instability Index, Aliphatic Index
  - Developability assessment: Solubility, Aggregation Risk, Stability
  - Sequence type classification (peptide vs. protein)

- **Example Molecule Library**: 16 pre-loaded biologics
  - 10 small molecule drugs (Aspirin, Imatinib, Warfarin, etc.)
  - 6 therapeutic peptides (Insulin, Semaglutide, Teriparatide, etc.)
  - 5 target proteins (Kinases, GPCRs, Ion channels)

- **Intelligent Input Detection**:
  - Auto-detects SMILES vs. FASTA format
  - Context-aware suggestions and error messages
  - User-friendly guidance for beginners

- **Educational Content**:
  - "Learn More" expandable sections on all pages
  - Plain-language explanations of technical concepts
  - Real-world analogies and concrete examples
  - Beginner-friendly tooltips and help text

- **Documentation**:
  - `METHODOLOGY.md`: Complete scientific methodology (30+ pages)
  - `REFERENCES.md`: 50+ peer-reviewed citations with DOIs
  - Comprehensive module docstrings with references

### Changed
- NumPy version constraint: `numpy>=1.24,<2.0` (RDKit compatibility)
- Updated `pyproject.toml` with explicit version constraints
- Python version locked to `>=3.11,<3.12`

### Fixed
- RDKit/NumPy 2.x compatibility issues
- Streamlit deprecation warnings (functionality unaffected)
- Minor UI improvements across all pages

---

## [0.9.0] - 2025-11-14

### Added
- **Machine Learning Models**: Ensemble predictions
  - Random Forest classifier
  - XGBoost gradient boosting
  - Simple feedforward neural network
  - Feature importance visualization with SHAP

- **Knowledge Graph Explorer**:
  - Drug-target-disease relationships
  - Interactive network visualization with PyVis
  - Mechanism of action queries
  - Target information lookup

- **Batch Screening Module**:
  - CSV file upload for high-throughput screening
  - Multi-compound analysis
  - Lead prioritization workflow
  - Export results with rankings

- **Case Study**: "Ranking Potential Kinase Inhibitor Leads"
  - Complete workflow demonstration
  - Multi-parameter optimization example
  - Educational resource for drug discovery

---

## [0.8.0] - 2025-11-13

### Added
- **FastAPI Backend**: REST API for programmatic access
  - `/predict/druglikeness`: Lipinski, Veber, QED, SA
  - `/predict/adme`: ADME/PK predictions
  - `/predict/toxicity`: Toxicity risk assessment
  - `/predict/target`: Target class predictions
  - `/predict/comprehensive`: Complete molecular profile
  - `/batch/predict`: High-throughput batch processing
  - Interactive API documentation at `/docs`

- **API Features**:
  - Pydantic data validation
  - Async request handling
  - Error handling and logging
  - CORS middleware for web integration

---

## [0.7.0] - 2025-11-12

### Added
- **Target Class Prediction**:
  - Kinase inhibitor likelihood
  - GPCR modulator prediction
  - Ion channel blocker identification
  - General enzyme inhibitor scoring

- **Drug-Likeness Assessment**:
  - Lipinski Rule of 5 analysis
  - Veber descriptor rules
  - QED (Quantitative Estimate of Drug-likeness)
  - Synthetic Accessibility score

---

## [0.6.0] - 2025-11-11

### Added
- **Toxicity Prediction Module** (Heuristic):
  - Hepatotoxicity structural alerts
  - hERG cardiotoxicity screening
  - Ames mutagenicity prediction
  - Carcinogenicity risk assessment
  - Multi-endpoint toxicity dashboard

---

## [0.5.0] - 2025-11-10

### Added
- **ADME/PK Prediction Module**:
  - LogP (lipophilicity) calculation
  - Caco-2 permeability estimation
  - Blood-brain barrier (BBB) penetration
  - CYP450 metabolism prediction
  - Hepatic clearance estimation

- **Visualization Utilities**:
  - 2D molecular structure rendering
  - Molecular property plots
  - Fingerprint visualization
  - Chemical space clustering with UMAP

---

## [0.4.0] - 2025-11-09

### Added
- **Molecular Descriptor Module**:
  - 200+ RDKit molecular descriptors
  - Fingerprint generation (Morgan, MACCS, Topological)
  - Basic property calculations (MW, LogP, HBA, HBD)
  - SMILES validation and canonicalization

---

## [0.3.0] - 2025-11-08

### Added
- **Streamlit Web Interface**:
  - Multi-page application structure
  - Molecular processing page
  - Interactive input forms
  - Real-time predictions
  - Professional UI with custom styling

---

## [0.2.0] - 2025-11-07

### Added
- **Project Structure**:
  - Modular architecture (models/, utils/, features/, api/)
  - Scientific reference system
  - Comprehensive documentation framework
  - Testing infrastructure

---

## [0.1.0] - 2025-11-06

### Added
- Initial project setup
- Basic RDKit integration
- SMILES parsing functionality
- Project documentation (README, LICENSE)
- Git repository initialization

---

## Version Numbering

- **Major version (X.0.0)**: Significant architectural changes, breaking API changes
- **Minor version (0.X.0)**: New features, non-breaking additions
- **Patch version (0.0.X)**: Bug fixes, documentation updates

---

## Upcoming Features (Roadmap)

### v1.3.0 (Planned)
- [ ] Protein language model integration (ESM-2/ProtBERT)
- [ ] Enhanced 3D molecular visualization
- [ ] Additional QSAR models from literature
- [ ] Expanded knowledge graph with ChEMBL integration

### v2.0.0 (Future)
- [ ] Validated QSAR models replacing heuristics
- [ ] Multi-task learning for joint predictions
- [ ] Cloud deployment (Docker, AWS/GCP)
- [ ] Regulatory export (SDTM format)
- [ ] AI-powered molecular optimization

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for information on how to contribute to this project.

---

## Links

- **Repository**: https://github.com/ardit-mishra/ardit-biocore
- **Issues**: https://github.com/ardit-mishra/ardit-biocore/issues
- **Discussions**: https://github.com/ardit-mishra/ardit-biocore/discussions

---

**Maintained by**: Ardit Mishra  
**Contact**: amishra7599@gmail.com | [LinkedIn](https://www.linkedin.com/in/ardit-mishra)
