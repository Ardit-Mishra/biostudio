# Pull Request

## Description

Provide a clear and concise description of your changes.

Fixes # (issue number)

## Type of Change

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Code refactoring
- [ ] Performance improvement
- [ ] Test additions

## Scientific Contributions

If this PR adds or modifies scientific methods:

### Method Information

- **Method Name**: [e.g., QSAR model for hepatotoxicity]
- **Type**: [ ] Validated QSAR [ ] Heuristic [ ] Machine Learning [ ] Other
- **References**: 
  - Authors et al. (Year). Title. Journal. DOI: xxx

### Validation

- **Dataset**: [e.g., Tox21, n=8000 compounds]
- **Performance Metrics**: [e.g., AUC=0.85, Accuracy=0.78]
- **Cross-validation**: [ ] Yes [ ] No

## Changes Made

List the specific changes:

- Added [feature/module]
- Modified [file/function]
- Fixed [bug/issue]
- Updated [documentation]

## Testing

### Tests Performed

- [ ] All existing tests pass (`pytest tests/ -v`)
- [ ] Added new tests for new functionality
- [ ] Manual testing completed
- [ ] Tested on example molecules (Aspirin, Imatinib, etc.)

### Test Results

```bash
# Paste test output here
pytest tests/ -v
```

### Coverage

```bash
# If applicable
pytest --cov=models --cov=utils --cov=features tests/
```

## Code Quality

- [ ] Code follows project style guidelines (PEP 8)
- [ ] Code has been formatted with `black .`
- [ ] No new warnings from `flake8`
- [ ] Type hints added (checked with `mypy`)
- [ ] Docstrings added/updated (Google style)
- [ ] No hardcoded values (use constants/config)

## Documentation

- [ ] README.md updated (if needed)
- [ ] METHODOLOGY.md updated with scientific details
- [ ] REFERENCES.md updated with citations
- [ ] CHANGELOG.md updated
- [ ] Function/class docstrings added
- [ ] Example notebooks updated (if applicable)

## Dependencies

- [ ] No new dependencies added
- [ ] New dependencies added and documented:
  - Package: [name], Version: [x.x.x], Reason: [why needed]
- [ ] Dependencies are compatible with Python 3.11
- [ ] NumPy version constraint maintained (<2.0)

## Breaking Changes

Does this PR introduce breaking changes?

- [ ] No
- [ ] Yes (describe below)

**Breaking Changes Description**:

[If yes, describe what breaks and how users should adapt]

## Screenshots

If applicable, add screenshots showing:

- New UI features
- Visualization improvements
- Before/after comparisons

## Deployment Notes

Any special steps needed for deployment:

- [ ] No special steps needed
- [ ] Requires database migration
- [ ] Requires model retraining
- [ ] Requires configuration changes

## Performance Impact

- [ ] No performance impact
- [ ] Performance improved (describe)
- [ ] Performance may be affected (explain why acceptable)

## Checklist

### General

- [ ] My code follows the project's code style
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes

### Scientific Integrity

- [ ] Methods are properly cited with DOI links
- [ ] Heuristic vs. validated models clearly distinguished
- [ ] Limitations documented
- [ ] Performance metrics reported honestly
- [ ] No fabricated or manipulated data

### For New Models

- [ ] Model type clearly stated (heuristic/QSAR/ML)
- [ ] Scientific references provided
- [ ] Input/output format documented
- [ ] Edge cases handled (None, invalid molecules)
- [ ] Unit tests added
- [ ] Example usage provided

## Additional Context

Add any other context about the pull request here.

## Reviewer Notes

Any specific areas you'd like reviewers to focus on?

---

**Thank you for contributing to BioStudio!** 🧬
