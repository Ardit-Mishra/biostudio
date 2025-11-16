# Ardit BioCore Examples

Example scripts and notebooks demonstrating platform usage.

## Contents

- **api_usage_demo.py**: Python script demonstrating FastAPI usage
- **batch_workflow_tutorial.ipynb**: (Future) Jupyter notebook with complete workflows

## Running the Examples

### API Usage Demo

This script demonstrates programmatic access to the FastAPI backend.

**Requirements**:
1. FastAPI server must be running
2. Python packages: `requests`, `pandas`

**Start the server**:
```bash
uvicorn api.prediction_api:app --host 0.0.0.0 --port 8000
```

**Run the demo**:
```bash
python examples/api_usage_demo.py
```

**What it demonstrates**:
- Single molecule analysis
- Batch screening of multiple compounds
- Lead optimization comparisons
- Exporting results to CSV

### Expected Output

```
======================================================================
Example 1: Single Molecule Analysis - Aspirin
======================================================================

SMILES: CC(=O)Oc1ccccc1C(=O)O

Drug-Likeness:
  - Lipinski Violations: 0
  - QED: 0.734
  - SA Score: 1.82

ADME Properties:
  - LogP: 1.28
  - Caco-2: High
  - BBB: Negative

Toxicity Assessment:
  - Hepatotoxicity: Low
  - hERG: Low

======================================================================
Example 2: Batch Screening - Kinase Inhibitors
======================================================================

Screened 5 kinase inhibitor candidates

Ranked by QED (Drug-Likeness):
     Name    QED  Kinase_Score Hepatotox_Risk  SA_Score
Erlotinib  0.82          85.0            Low      3.45
Gefitinib  0.79          82.3            Low      3.78
Imatinib   0.75          91.2       Moderate      4.12
Sunitinib  0.71          78.5            Low      3.92
Sorafenib  0.68          80.1           High      4.55

======================================================================
```

## Example Use Cases

### Use Case 1: Virtual Screening

Screen a virtual library to identify promising candidates:

```python
from examples.api_usage_demo import ArditBioCoreAPI

api = ArditBioCoreAPI()

# Your library of SMILES
library = [...]  # List of SMILES strings

# Batch predict
results = api.batch_predict(library)

# Filter for drug-like, non-toxic compounds
good_candidates = [
    r for r in results 
    if r.get('qed', 0) > 0.6 
    and r.get('hepatotoxicity_risk') in ['Low', 'Moderate']
]
```

### Use Case 2: Lead Optimization

Compare a lead compound with its analogs:

```python
lead_compound = "CC(=O)Oc1ccccc1C(=O)O"  # Your lead
analogs = ["...", "...", "..."]  # Designed analogs

results_lead = api.comprehensive_analysis(lead_compound)
results_analogs = [api.comprehensive_analysis(s) for s in analogs]

# Find improved analogs
for i, result in enumerate(results_analogs):
    if result['druglikeness']['qed'] > results_lead['druglikeness']['qed']:
        print(f"Analog {i+1} has better drug-likeness!")
```

### Use Case 3: Toxicity Flagging

Quickly flag compounds with toxicity concerns:

```python
def flag_toxic_compounds(smiles_list):
    """Flag compounds with high toxicity risk."""
    api = ArditBioCoreAPI()
    flagged = []
    
    for smiles in smiles_list:
        result = api.predict_toxicity(smiles)
        
        if result['hepatotoxicity']['risk_level'] in ['High', 'Critical']:
            flagged.append({
                'smiles': smiles,
                'reason': 'Hepatotoxicity',
                'risk': result['hepatotoxicity']['risk_level']
            })
        
        if result['herg']['risk_level'] == 'High':
            flagged.append({
                'smiles': smiles,
                'reason': 'hERG Cardiotoxicity',
                'risk': 'High'
            })
    
    return flagged
```

## Integration with External Tools

### Pandas Integration

```python
import pandas as pd

# Load molecules from CSV
df = pd.read_csv('molecules.csv')

# Add predictions
api = ArditBioCoreAPI()
df['qed'] = df['SMILES'].apply(
    lambda s: api.predict_druglikeness(s)['qed']
)

# Filter and export
df_filtered = df[df['qed'] > 0.6]
df_filtered.to_csv('drug_like_molecules.csv', index=False)
```

### RDKit Integration

```python
from rdkit import Chem
from rdkit.Chem import Draw

# Get predictions
api = ArditBioCoreAPI()
result = api.comprehensive_analysis(smiles)

# Visualize with RDKit
mol = Chem.MolFromSmiles(smiles)
img = Draw.MolToImage(mol, size=(300, 300))
img.save(f"molecule_qed_{result['druglikeness']['qed']:.2f}.png")
```

## Tips for Production Use

1. **Error Handling**: Always wrap API calls in try-except blocks
2. **Rate Limiting**: For large batches, implement delays between requests
3. **Validation**: Validate SMILES before sending to API
4. **Caching**: Cache results for molecules you analyze repeatedly
5. **Batch Size**: For very large libraries, process in chunks of 100-1000

## Future Examples

Coming soon:
- Jupyter notebook with interactive visualizations
- Integration with ChEMBL database
- ML model retraining workflows
- Advanced batch processing strategies

## Resources

- **API Documentation**: http://localhost:8000/docs
- **Main Documentation**: [README.md](../README.md)
- **Tutorial**: [TUTORIAL.md](../TUTORIAL.md)
- **Scientific Background**: [METHODOLOGY.md](../METHODOLOGY.md)

---

**Last Updated**: November 2025  
**Author**: Ardit Mishra  
**Contact**: amishra7599@gmail.com
