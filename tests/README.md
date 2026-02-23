# Test Suite for BioStudio

Unit tests for molecular processing, drug-likeness calculations, and prediction models.

## Running Tests

### Run All Tests

```bash
# From project root
pytest tests/ -v
```

### Run Specific Test File

```bash
pytest tests/test_molecular_utils.py -v
pytest tests/test_drug_likeness.py -v
```

### Run with Coverage

```bash
pytest --cov=utils --cov=models --cov=features tests/
```

### Run Specific Test Class or Method

```bash
# Run specific class
pytest tests/test_molecular_utils.py::TestMolecularProcessor -v

# Run specific test
pytest tests/test_molecular_utils.py::TestMolecularProcessor::test_valid_smiles_aspirin -v
```

## Test Organization

```
tests/
├── __init__.py                # Package initialization
├── test_molecular_utils.py    # Molecular processing tests
├── test_drug_likeness.py      # Drug-likeness calculation tests
└── README.md                  # This file
```

## Test Coverage

Current test coverage:

- ✅ **Molecular Processing**: SMILES validation, property calculation, feature extraction
- ✅ **Drug-Likeness**: Lipinski, Veber, QED, SA score
- ⏳ **ADME Predictions**: Future work
- ⏳ **Toxicity Predictions**: Future work
- ⏳ **ML Models**: Future work

## Adding New Tests

### Test Template

```python
import pytest
from rdkit import Chem
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from module_to_test import ClassToTest


class TestClassName:
    """Test suite for ClassName."""
    
    def setup_method(self):
        """Initialize before each test."""
        self.instance = ClassToTest()
    
    def test_basic_functionality(self):
        """Test basic functionality."""
        result = self.instance.method()
        assert result is not None
    
    @pytest.mark.parametrize("input,expected", [
        ("input1", "output1"),
        ("input2", "output2"),
    ])
    def test_multiple_cases(self, input, expected):
        """Test multiple cases."""
        result = self.instance.method(input)
        assert result == expected
```

## Testing Best Practices

1. **Test Both Success and Failure Cases**: Include valid and invalid inputs
2. **Use Parametrize**: Test multiple cases efficiently
3. **Clear Test Names**: Describe what is being tested
4. **Setup/Teardown**: Use `setup_method()` and `teardown_method()`
5. **Assertions**: Use specific assertions (`pytest.approx` for floats)
6. **Edge Cases**: Test boundary conditions and edge cases

## Continuous Integration

Tests should run automatically on:
- Every pull request
- Every commit to main branch
- Before releases

## Known Issues

1. Some ML model tests require trained models (not included in tests)
2. Large molecule tests may be slow
3. Some RDKit warnings are expected and can be ignored

## Contributing Tests

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines on adding tests.

### Test Requirements for Pull Requests

- [ ] All existing tests pass
- [ ] New functionality has tests (>80% coverage)
- [ ] Edge cases are tested
- [ ] Tests are documented
- [ ] Tests run in <30 seconds (unit tests should be fast)

## Resources

- **pytest documentation**: https://docs.pytest.org/
- **RDKit testing examples**: https://www.rdkit.org/docs/
- **Testing best practices**: [CONTRIBUTING.md](../CONTRIBUTING.md)

---

**Last Updated**: November 2025  
**Maintained by**: Ardit Mishra
