---
name: Bug Report
about: Report a bug or unexpected behavior
title: '[BUG] '
labels: bug
assignees: ''
---

## Bug Description

A clear and concise description of the bug.

## Steps to Reproduce

1. Go to '...'
2. Click on '...'
3. Enter SMILES/FASTA '...'
4. See error

## Expected Behavior

What you expected to happen.

## Actual Behavior

What actually happened.

## Error Message

```
Paste complete error message/traceback here
```

## Environment

- **Python Version**: [e.g., 3.11.5]
- **Operating System**: [e.g., Ubuntu 22.04, macOS 14.0, Windows 11]
- **NumPy Version**: [Run `python -c "import numpy; print(numpy.__version__)"`]
- **RDKit Version**: [Run `python -c "import rdkit; print(rdkit.__version__)"`]
- **Installation Method**: [pip, conda, Docker]

## SMILES/FASTA Input

If the bug is related to a specific molecule or protein, provide the input:

```
# Example: CC(=O)Oc1ccccc1C(=O)O
```

## Additional Context

Any additional information that might help diagnose the issue:

- Screenshots
- Related issues
- Workarounds you've tried

## Checklist

- [ ] I've checked [existing issues](https://github.com/ardit-mishra/biostudio/issues) for duplicates
- [ ] I'm using Python 3.11
- [ ] I'm using NumPy <2.0 (verify with `python -c "import numpy; print(numpy.__version__)"`)
- [ ] I've tested in a fresh virtual environment
- [ ] I've included complete error messages
