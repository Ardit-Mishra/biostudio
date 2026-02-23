# Contributing to BioStudio

Thank you for your interest in contributing to **BioStudio** - AI-Powered Molecular Intelligence Platform!

This document provides guidelines for contributing to ensure high-quality, scientifically rigorous additions to the project.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [How Can I Contribute?](#how-can-i-contribute)
3. [Development Setup](#development-setup)
4. [Scientific Standards](#scientific-standards)
5. [Code Style Guidelines](#code-style-guidelines)
6. [Adding New Models](#adding-new-models)
7. [Testing Requirements](#testing-requirements)
8. [Pull Request Process](#pull-request-process)
9. [Documentation Standards](#documentation-standards)
10. [Citation Requirements](#citation-requirements)

---

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to amishra7599@gmail.com.

---

## How Can I Contribute?

### Reporting Bugs

Before submitting a bug report:

1. Check [existing issues](https://github.com/Ardit-Mishra/biostudio/issues)
2. Verify you're using the correct NumPy version (<2.0)
3. Test with a fresh virtual environment

**Good Bug Reports Include:**

- Python version and operating system
- Complete error traceback
- Minimal code to reproduce the issue
- Expected vs. actual behavior
- Relevant SMILES/FASTA sequences (if applicable)

Use the [bug report template](.github/ISSUE_TEMPLATE/bug_report.md).

### Suggesting Features

Feature requests are welcome! Use the [feature request template](.github/ISSUE_TEMPLATE/feature_request.md).

**Great Feature Requests Include:**

- Clear scientific rationale
- References to published methods
- Use cases and benefits
- Proposed implementation approach

### Contributing Code

Areas where contributions are particularly welcome:

1. **Validated QSAR Models**
   - Replace heuristic functions with data-driven models
   - Integrate models trained on ChEMBL, Tox21, BindingDB
   - Add performance benchmarking

2. **Molecular Descriptors**
   - Additional RDKit descriptors
   - Custom pharmaceutical property calculations
   - 3D conformer-based features

3. **Knowledge Graph Expansion**
   - Integration with ChEMBL, PubChem APIs
   - Additional drug-target relationships
   - Pathway mapping

4. **Documentation**
   - Tutorial improvements
   - Scientific method clarifications
   - Additional example notebooks

5. **Performance Optimizations**
   - Batch processing improvements
   - Caching strategies
   - Parallel processing

---

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
git clone https://github.com/YOUR_USERNAME/biostudio.git
cd biostudio
```

### 2. Create Development Environment

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development tools
pip install pytest black flake8 mypy jupyter
```

### 3. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
# OR
git checkout -b fix/bug-description
```

### 4. Make Changes

Follow the coding standards outlined below.

### 5. Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_molecular_utils.py

# Check code coverage
pytest --cov=models --cov=utils --cov=features tests/
```

### 6. Commit Changes

```bash
git add .
git commit -m "feat: Add validated QSAR model for hepatotoxicity

- Implemented Random Forest classifier
- Trained on Tox21 dataset (n=8000 compounds)
- Cross-validated AUC: 0.82
- References: Smith et al. (2020) DOI:10.1234/example"
```

Use conventional commit format:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Adding/updating tests
- `refactor:` Code refactoring
- `perf:` Performance improvements

---

## Scientific Standards

### Core Principles

All contributions must maintain scientific rigor:

1. **Evidence-Based**: Methods must be grounded in peer-reviewed literature
2. **Transparent**: Clear distinction between heuristics and validated models
3. **Reproducible**: Complete documentation for replication
4. **Cited**: Proper attribution to original research

### Adding Scientific Methods

When implementing a new predictive method:

```python
def predict_new_property(mol):
    """
    Predict [property name] using [method name].
    
    Implementation of the method from [Authors (Year)]:
    
    Reference:
        [Full citation]
        DOI: [DOI link]
    
    Args:
        mol: RDKit molecule object
    
    Returns:
        Prediction value with appropriate units
    
    Notes:
        - Current implementation: [heuristic/validated model]
        - Training data: [dataset name, size]
        - Performance: [accuracy metrics]
        - Limitations: [known issues]
    """
    # Implementation here
    pass
```

### Required Documentation for Models

1. **Scientific Reference**: Link to original paper
2. **Validation Status**: Heuristic vs. validated QSAR
3. **Training Data**: Dataset used (if applicable)
4. **Performance Metrics**: Accuracy, AUC, R², etc.
5. **Applicability Domain**: Chemical space limitations
6. **Known Limitations**: Edge cases, failure modes

---

## Code Style Guidelines

### Python Style

We follow **PEP 8** with these specifics:

```python
# Good: Clear, descriptive names
def calculate_lipinski_violations(mol: Chem.Mol) -> int:
    """Calculate number of Lipinski Rule of 5 violations."""
    violations = 0
    mw = Descriptors.MolWt(mol)
    if mw > 500:
        violations += 1
    return violations

# Bad: Unclear names, no types
def calc(m):
    v = 0
    if Descriptors.MolWt(m) > 500:
        v += 1
    return v
```

### Type Hints

Use type hints for all function signatures:

```python
from typing import Dict, List, Tuple, Optional
from rdkit import Chem
import numpy as np

def extract_features(mol: Chem.Mol) -> np.ndarray:
    """Extract molecular features."""
    pass

def batch_predict(smiles_list: List[str]) -> Dict[str, float]:
    """Predict properties for multiple molecules."""
    pass
```

### Docstrings

Use Google-style docstrings:

```python
def predict_solubility(mol: Chem.Mol, ph: float = 7.4) -> float:
    """
    Predict aqueous solubility using ESOL method.
    
    Reference:
        Delaney, J. S. (2004). ESOL: Estimating aqueous solubility directly
        from molecular structure. J. Chem. Inf. Comput. Sci., 44(3), 1000-1005.
        DOI: 10.1021/ci034243x
    
    Args:
        mol: RDKit molecule object
        ph: pH value for ionization correction (default: 7.4)
    
    Returns:
        Predicted log solubility in mol/L
    
    Raises:
        ValueError: If molecule is None or pH is out of range
    
    Example:
        >>> from rdkit import Chem
        >>> mol = Chem.MolFromSmiles('CCO')
        >>> solubility = predict_solubility(mol)
        >>> print(f"LogS: {solubility:.2f}")
    """
    if mol is None:
        raise ValueError("Molecule cannot be None")
    if not 0 <= ph <= 14:
        raise ValueError("pH must be between 0 and 14")
    
    # Implementation
    return predicted_value
```

### Code Formatting

```bash
# Auto-format with Black
black .

# Check style
flake8 models/ utils/ features/

# Type checking
mypy models/ utils/ features/ --ignore-missing-imports
```

### Import Organization

```python
# Standard library
import os
import sys
from typing import Dict, List

# Third-party
import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import Descriptors

# Local
from utils.molecular_utils import MolecularFeatureExtractor
from models.base_predictor import BasePredictor
```

---

## Adding New Models

### File Structure

```
models/
├── your_new_model.py          # Implementation
tests/
├── test_your_new_model.py     # Unit tests
examples/
├── your_model_demo.ipynb      # Demo notebook
```

### Model Template

```python
"""
[Model Name] Prediction Module

Implementation of [method] from [Authors, Year].

Reference:
    [Full citation]
    DOI: [link]

Author: Your Name
"""

import numpy as np
from typing import Dict, Optional
from rdkit import Chem
from rdkit.Chem import Descriptors


class YourNewPredictor:
    """
    [Model Name] predictor.
    
    Attributes:
        model_type: 'heuristic' or 'qsar'
        references: List of scientific papers
    """
    
    def __init__(self):
        """Initialize predictor with model parameters."""
        self.model_type = "heuristic"  # or "qsar"
        self.references = [
            "Authors et al. (Year). Title. Journal. DOI: xxx"
        ]
    
    def predict(self, mol: Chem.Mol) -> Dict[str, float]:
        """
        Predict [property] for given molecule.
        
        Args:
            mol: RDKit molecule object
        
        Returns:
            Dictionary with prediction results
        """
        if mol is None:
            return {'error': 'Invalid molecule'}
        
        # Your prediction logic here
        prediction = self._calculate_score(mol)
        
        return {
            'score': prediction,
            'category': self._categorize(prediction),
            'model_type': self.model_type
        }
    
    def _calculate_score(self, mol: Chem.Mol) -> float:
        """Internal scoring logic."""
        # Implementation
        pass
    
    def _categorize(self, score: float) -> str:
        """Convert score to category."""
        # Implementation
        pass
```

### Testing New Models

Create comprehensive tests:

```python
# tests/test_your_new_model.py
import pytest
from rdkit import Chem
from models.your_new_model import YourNewPredictor


class TestYourNewPredictor:
    """Test suite for YourNewPredictor."""
    
    def setup_method(self):
        """Initialize predictor before each test."""
        self.predictor = YourNewPredictor()
    
    def test_valid_molecule(self):
        """Test prediction on valid molecule."""
        mol = Chem.MolFromSmiles('CCO')  # Ethanol
        result = self.predictor.predict(mol)
        
        assert 'score' in result
        assert isinstance(result['score'], float)
        assert 'category' in result
    
    def test_invalid_molecule(self):
        """Test handling of invalid molecule."""
        result = self.predictor.predict(None)
        assert 'error' in result
    
    def test_known_compounds(self):
        """Test on compounds with known properties."""
        # Aspirin
        aspirin = Chem.MolFromSmiles('CC(=O)Oc1ccccc1C(=O)O')
        result = self.predictor.predict(aspirin)
        # Add assertions based on expected values
    
    @pytest.mark.parametrize("smiles,expected_category", [
        ('CCO', 'low_risk'),
        ('c1ccccc1', 'moderate_risk'),
        # Add more test cases
    ])
    def test_categorization(self, smiles, expected_category):
        """Test score categorization."""
        mol = Chem.MolFromSmiles(smiles)
        result = self.predictor.predict(mol)
        assert result['category'] == expected_category
```

---

## Testing Requirements

### Minimum Test Coverage

- **New Models**: >80% code coverage
- **Critical Functions**: 100% coverage
- **Edge Cases**: Test None, invalid inputs, boundary values

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific module
pytest tests/test_your_new_model.py

# With coverage
pytest --cov=models/your_new_model tests/test_your_new_model.py

# Coverage report
pytest --cov=models --cov-report=html tests/
```

### Test Categories

Use pytest markers:

```python
@pytest.mark.unit
def test_feature_extraction():
    """Unit test for feature extraction."""
    pass

@pytest.mark.integration
def test_end_to_end_prediction():
    """Integration test for complete prediction workflow."""
    pass

@pytest.mark.slow
def test_large_batch_processing():
    """Test on large dataset (may take several minutes)."""
    pass
```

---

## Pull Request Process

### Before Submitting

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New tests added for new functionality
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Scientific references added to REFERENCES.md
- [ ] No merge conflicts with main branch

### PR Template Checklist

See [Pull Request Template](.github/PULL_REQUEST_TEMPLATE.md)

### Review Process

1. **Automated Checks**: CI/CD runs tests and style checks
2. **Scientific Review**: Validation of methods and references
3. **Code Review**: Maintainer reviews implementation
4. **Approval**: Requires 1 maintainer approval
5. **Merge**: Squash and merge into main branch

### After Merge

- Your contribution will be acknowledged in CHANGELOG.md
- Feature will be included in next release
- You'll be added to contributors list

---

## Documentation Standards

### README Updates

When adding features, update relevant sections:

```markdown
## Key Features

### Your New Feature

- **Feature Name**: Brief description
- **Method**: Reference to scientific paper
- **Status**: Heuristic/Validated QSAR
```

### METHODOLOGY.md Updates

Add scientific details:

```markdown
## [Your Method Name]

### Scientific Basis

[Detailed explanation of the method]

### Implementation

- **Algorithm**: [Description]
- **Parameters**: [List and explanation]
- **Validation**: [Dataset and metrics]

### References

[1] Authors et al. (Year). Title. Journal. DOI: xxx
```

### REFERENCES.md Updates

Add full citations:

```markdown
### [Category]

**[Reference Number]** Authors, A. B., & Authors, C. D. (Year). Article title.
*Journal Name*, Volume(Issue), pages.  
DOI: [10.xxxx/xxxxx](https://doi.org/10.xxxx/xxxxx)

- Key contribution to the field
- Relevance to this project
```

---

## Citation Requirements

### When to Cite

You **must** cite when:

1. Implementing a published algorithm
2. Using a publicly available dataset
3. Adapting code from another project
4. Building upon previous work

### How to Cite in Code

```python
"""
Implementation of [Method Name] from:

Reference:
    Authors, A. B., et al. (2020). "Title of Paper."
    Journal Name, 15(3), 123-145.
    DOI: 10.1234/example
    
Notes:
    - Original implementation: [link if available]
    - Modifications: [describe any changes]
    - License: [if applicable]
"""
```

### Updating Reference Documents

1. Add citation to `REFERENCES.md`
2. Link from `METHODOLOGY.md`
3. Reference in docstrings
4. Mention in module header

---

## Questions?

- **Technical Issues**: Open a [GitHub Issue](https://github.com/Ardit-Mishra/biostudio/issues)
- **Scientific Questions**: Email amishra7599@gmail.com
- **General Discussion**: Start a [Discussion](https://github.com/Ardit-Mishra/biostudio/discussions)

---

## Recognition

Contributors will be acknowledged in:

- README.md contributors section
- CHANGELOG.md for specific contributions
- Academic citations (if applicable)

Thank you for helping make BioStudio better! 🧬

---

**Last Updated**: November 2025  
**Maintained by**: Ardit Mishra  
**Contact**: amishra7599@gmail.com | [GitHub](https://github.com/ardit-mishra)
