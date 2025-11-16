# Installation & Setup Guide

Complete installation instructions for **Ardit BioCore** - AI-Powered Molecular Intelligence Platform

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation Methods](#installation-methods)
3. [Virtual Environment Setup](#virtual-environment-setup)
4. [Dependency Installation](#dependency-installation)
5. [Critical: NumPy Compatibility](#critical-numpy-compatibility)
6. [Verification](#verification)
7. [Running the Application](#running-the-application)
8. [Troubleshooting](#troubleshooting)
9. [Advanced Configuration](#advanced-configuration)

---

## System Requirements

### Minimum Requirements

- **Operating System**: Linux, macOS, or Windows 10/11
- **Python**: 3.11 (required - RDKit compatibility)
- **RAM**: 4 GB minimum, 8 GB recommended
- **Disk Space**: 2 GB for dependencies and cached data
- **Internet**: Required for initial dependency installation

### Recommended Setup

- **Python**: 3.11.x (latest patch version)
- **RAM**: 16 GB for large batch screening operations
- **CPU**: Multi-core processor for ML model training
- **GPU**: Not required (CPU-only implementation)

---

## Installation Methods

### Method 1: Using pip (Recommended for most users)

```bash
# Clone the repository
git clone https://github.com/ardit-mishra/ardit-biocore.git
cd ardit-biocore

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Method 2: Using uv (Faster installation)

```bash
# Clone the repository
git clone https://github.com/ardit-mishra/ardit-biocore.git
cd ardit-biocore

# Install uv if not already installed
pip install uv

# Install dependencies
uv pip install -r requirements.txt
```

### Method 3: Using pyproject.toml directly

```bash
# Clone the repository
git clone https://github.com/ardit-mishra/ardit-biocore.git
cd ardit-biocore

# Install with pip
pip install -e .
```

---

## Virtual Environment Setup

### Why Use Virtual Environments?

Virtual environments isolate project dependencies, preventing conflicts with other Python projects. **Highly recommended** for this project due to specific version requirements (especially NumPy <2.0).

### Creating Virtual Environments

#### Linux/macOS

```bash
# Using venv (built-in)
python3.11 -m venv venv
source venv/bin/activate

# Using conda
conda create -n ardit-biocore python=3.11
conda activate ardit-biocore
```

#### Windows

```bash
# Using venv
python -m venv venv
venv\Scripts\activate

# Using conda
conda create -n ardit-biocore python=3.11
conda activate ardit-biocore
```

### Deactivating Virtual Environment

```bash
deactivate  # For venv
conda deactivate  # For conda
```

---

## Dependency Installation

### Core Dependencies

The platform requires these primary packages:

```bash
# Cheminformatics
rdkit-pypi>=2022.9.5

# Machine Learning
scikit-learn>=1.7.2
xgboost>=3.1.1

# Web Framework
streamlit>=1.51.0
fastapi>=0.121.2
uvicorn>=0.38.0

# Data Science
numpy>=1.24,<2.0  # CRITICAL: Must be <2.0 for RDKit
pandas>=2.3.3
scipy>=1.16.3

# Visualization
matplotlib>=3.10.7
seaborn>=0.13.2
plotly>=6.4.0

# Bioinformatics
biopython>=1.86
```

### Installing All Dependencies

```bash
# Standard installation
pip install -r requirements.txt

# Verify installation
pip list | grep -E "rdkit|streamlit|numpy|scikit"
```

---

## Critical: NumPy Compatibility

### ⚠️ NumPy <2.0 Requirement

**RDKit 2022.9.5 is compiled against NumPy 1.x** and is NOT compatible with NumPy 2.x.

#### The Problem

If you install NumPy 2.x, you'll encounter errors like:

```
ImportError: numpy.core.multiarray failed to import
RuntimeError: module compiled against API version 0x10 but this version of numpy is 0x12
```

#### The Solution

Our `pyproject.toml` and `requirements.txt` enforce `numpy>=1.24,<2.0`:

```toml
[project]
dependencies = [
    "numpy>=1.24,<2.0",  # Explicit version constraint
    "rdkit-pypi>=2022.9.5",
    # ... other packages
]
```

#### Verification

```bash
# Check NumPy version
python -c "import numpy; print(f'NumPy version: {numpy.__version__}')"

# Should output: NumPy version: 1.26.4 (or similar 1.x version)
```

#### Fixing NumPy Version Issues

```bash
# If you have NumPy 2.x installed, downgrade:
pip uninstall numpy
pip install "numpy>=1.24,<2.0"

# Verify RDKit works
python -c "from rdkit import Chem; print('RDKit OK')"
```

---

## Verification

### Step 1: Check Python Version

```bash
python --version
# Expected: Python 3.11.x
```

### Step 2: Check Core Package Versions

```bash
python -c "
import sys
import numpy
import rdkit
import streamlit
import sklearn
import xgboost

print(f'Python: {sys.version}')
print(f'NumPy: {numpy.__version__}')
print(f'RDKit: {rdkit.__version__}')
print(f'Streamlit: {streamlit.__version__}')
print(f'scikit-learn: {sklearn.__version__}')
print(f'XGBoost: {xgboost.__version__}')
"
```

### Step 3: Test RDKit Functionality

```bash
python -c "
from rdkit import Chem
from rdkit.Chem import Descriptors

# Test SMILES parsing
mol = Chem.MolFromSmiles('CCO')
if mol:
    print(f'✓ RDKit SMILES parsing: OK')
    print(f'✓ Molecular weight: {Descriptors.MolWt(mol):.2f}')
else:
    print('✗ RDKit SMILES parsing: FAILED')
"
```

### Step 4: Test Molecular Feature Extraction

```bash
python -c "
from utils.molecular_utils import MolecularFeatureExtractor
from rdkit import Chem

mol = Chem.MolFromSmiles('CC(=O)Oc1ccccc1C(=O)O')  # Aspirin
features = MolecularFeatureExtractor.extract_features(mol)
print(f'✓ Feature extraction: {len(features)} features')
print(f'✓ Expected: 2078 features (30 descriptors + 2048 FP bits)')
"
```

---

## Running the Application

### 1. Streamlit Web Application (Primary Interface)

```bash
# Navigate to project directory
cd ardit-biocore

# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# OR
venv\Scripts\activate  # Windows

# Run Streamlit app
streamlit run app.py --server.port 5000

# Application will open in browser at http://localhost:5000
```

### 2. FastAPI Backend (Optional - For API Access)

```bash
# In a separate terminal
cd ardit-biocore
source venv/bin/activate

# Run FastAPI server
uvicorn api.prediction_api:app --host 0.0.0.0 --port 8000

# API documentation available at http://localhost:8000/docs
```

### 3. Running Both Services

```bash
# Terminal 1: Streamlit
streamlit run app.py --server.port 5000

# Terminal 2: FastAPI
uvicorn api.prediction_api:app --host 0.0.0.0 --port 8000
```

---

## Troubleshooting

### Issue 1: RDKit Import Error

**Symptom:**
```
ImportError: No module named 'rdkit'
```

**Solution:**
```bash
pip install rdkit-pypi
# Verify
python -c "from rdkit import Chem; print('OK')"
```

### Issue 2: NumPy Version Conflict

**Symptom:**
```
RuntimeError: module compiled against API version 0x10 but this version of numpy is 0x12
```

**Solution:**
```bash
pip uninstall numpy
pip install "numpy>=1.24,<2.0"
python -c "import numpy; print(numpy.__version__)"
```

### Issue 3: Streamlit Command Not Found

**Symptom:**
```
bash: streamlit: command not found
```

**Solution:**
```bash
# Ensure virtual environment is activated
which python  # Should point to venv/bin/python

# Reinstall streamlit
pip install streamlit

# Try running again
streamlit run app.py
```

### Issue 4: Port Already in Use

**Symptom:**
```
OSError: [Errno 98] Address already in use
```

**Solution:**
```bash
# Find process using port 5000
lsof -i :5000  # Linux/macOS
netstat -ano | findstr :5000  # Windows

# Kill the process or use different port
streamlit run app.py --server.port 5001
```

### Issue 5: Missing System Dependencies (Linux)

**Symptom:**
```
error: command 'gcc' failed
```

**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3-dev build-essential

# Fedora/CentOS
sudo yum install python3-devel gcc gcc-c++

# Then reinstall packages
pip install -r requirements.txt
```

### Issue 6: Memory Error During Batch Processing

**Symptom:**
```
MemoryError: Unable to allocate array
```

**Solution:**
- Reduce batch size in batch screening
- Close other applications
- Use incremental processing for large datasets

---

## Advanced Configuration

### Streamlit Configuration

Create `.streamlit/config.toml` for custom settings:

```toml
[server]
port = 5000
address = "0.0.0.0"
headless = true
runOnSave = true

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#D4AF37"  # Gold accent
backgroundColor = "#0E1117"
secondaryBackgroundColor = "#262730"
textColor = "#FAFAFA"
```

### FastAPI Configuration

Set environment variables:

```bash
export API_HOST="0.0.0.0"
export API_PORT="8000"
export LOG_LEVEL="info"

uvicorn api.prediction_api:app --host $API_HOST --port $API_PORT --log-level $LOG_LEVEL
```

### Performance Optimization

```bash
# Enable parallel processing (for batch screening)
export NUMEXPR_MAX_THREADS=8
export OMP_NUM_THREADS=8

# For large molecular libraries
export RDKIT_QUIET=1  # Suppress RDKit warnings
```

---

## Development Setup

### Installing Development Dependencies

```bash
# Install additional dev tools
pip install pytest black flake8 mypy jupyter

# Run tests
pytest tests/

# Code formatting
black .

# Type checking
mypy models/ utils/ features/
```

### Jupyter Notebook Setup

```bash
# Install Jupyter
pip install jupyter ipykernel

# Create kernel for this project
python -m ipykernel install --user --name=ardit-biocore

# Launch Jupyter
jupyter notebook examples/
```

---

## Platform-Specific Notes

### Linux

- Recommended platform for production use
- All dependencies install cleanly
- Best performance for batch processing

### macOS

- Works well on both Intel and Apple Silicon
- May require Xcode Command Line Tools: `xcode-select --install`
- Some packages may take longer to install on M1/M2

### Windows

- Use Python from python.org (not Microsoft Store version)
- Some RDKit visualizations may require additional setup
- Consider using WSL2 for better compatibility

---

## Docker Installation (Alternative)

See `Dockerfile` for containerized setup:

```bash
# Build image
docker build -t ardit-biocore .

# Run container
docker run -p 5000:5000 ardit-biocore
```

---

## Getting Help

If you encounter issues not covered here:

1. Check existing [GitHub Issues](https://github.com/ardit-mishra/ardit-biocore/issues)
2. Review RDKit documentation: https://www.rdkit.org/docs/
3. Open a new issue with:
   - Python version (`python --version`)
   - Operating system
   - Complete error message
   - Steps to reproduce

---

## Next Steps

After successful installation:

1. Read [TUTORIAL.md](TUTORIAL.md) for usage guide
2. Review [METHODOLOGY.md](METHODOLOGY.md) for scientific background
3. Explore example molecules in the Streamlit app
4. Try the API endpoints at http://localhost:8000/docs

---

**Last Updated**: November 2025  
**Maintained by**: Ardit Mishra  
**Contact**: amishra7599@gmail.com | [GitHub](https://github.com/ardit-mishra)
