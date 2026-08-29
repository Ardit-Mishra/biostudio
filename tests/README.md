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
├── test_admet_models.py       # Served ADMET model suite: artifact metadata
│                               # validity, prediction schema, a known-molecule
│                               # sanity check, models loading, model card vs
│                               # manifest. This is what .github/workflows/ci.yml
│                               # runs on every PR and push.
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

`.github/workflows/ci.yml` runs `test_admet_models.py` on every pull request and every push to the
`ui/instrument-design-system` branch. `test_drug_likeness.py` and `test_molecular_utils.py` are
**not** in that CI gate yet: they currently have 25 pre-existing failures (see Known Issues below)
unrelated to the ADMET model suite, and gating CI on them today would make it red from the first
run. Fixing those and adding them to CI is tracked as follow-up work, not silently skipped.

## Known Issues

1. `test_drug_likeness.py` and `test_molecular_utils.py` currently have 25 failing tests (as of
   2026-08-29) against `utils/drug_likeness.py` / `utils/molecular_utils.py` -- mostly `KeyError`s
   for dict keys the tests expect (e.g. `num_aromatic_rings`, `molecular_weight`) that the current
   implementation doesn't return under those names. Pre-existing, not touched by the ADMET model
   work in this repo; not yet gated in CI (see above).
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
