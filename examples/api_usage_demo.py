"""
Ardit BioCore API Usage Demo

This script demonstrates how to use the FastAPI backend programmatically
for batch molecular analysis.

Requirements:
    - FastAPI server running on localhost:8000
    - Run with: uvicorn api.prediction_api:app --host 0.0.0.0 --port 8000
"""

import requests
import json
import pandas as pd
from typing import List, Dict


class ArditBioCoreAPI:
    """Client for Ardit BioCore FastAPI endpoints."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize API client.
        
        Args:
            base_url: Base URL of FastAPI server
        """
        self.base_url = base_url
    
    def predict_druglikeness(self, smiles: str) -> Dict:
        """
        Predict drug-likeness properties.
        
        Args:
            smiles: SMILES string
        
        Returns:
            Dictionary with Lipinski, Veber, QED, SA scores
        """
        endpoint = f"{self.base_url}/predict/druglikeness"
        payload = {"smiles": smiles}
        
        response = requests.post(endpoint, json=payload)
        response.raise_for_status()
        
        return response.json()
    
    def predict_adme(self, smiles: str) -> Dict:
        """
        Predict ADME/PK properties.
        
        Args:
            smiles: SMILES string
        
        Returns:
            Dictionary with ADME predictions
        """
        endpoint = f"{self.base_url}/predict/adme"
        payload = {"smiles": smiles}
        
        response = requests.post(endpoint, json=payload)
        response.raise_for_status()
        
        return response.json()
    
    def predict_toxicity(self, smiles: str) -> Dict:
        """
        Predict toxicity endpoints.
        
        Args:
            smiles: SMILES string
        
        Returns:
            Dictionary with toxicity predictions
        """
        endpoint = f"{self.base_url}/predict/toxicity"
        payload = {"smiles": smiles}
        
        response = requests.post(endpoint, json=payload)
        response.raise_for_status()
        
        return response.json()
    
    def predict_target(self, smiles: str) -> Dict:
        """
        Predict target class likelihood.
        
        Args:
            smiles: SMILES string
        
        Returns:
            Dictionary with target predictions
        """
        endpoint = f"{self.base_url}/predict/target"
        payload = {"smiles": smiles}
        
        response = requests.post(endpoint, json=payload)
        response.raise_for_status()
        
        return response.json()
    
    def comprehensive_analysis(self, smiles: str) -> Dict:
        """
        Get comprehensive molecular profile.
        
        Args:
            smiles: SMILES string
        
        Returns:
            Dictionary with all predictions
        """
        endpoint = f"{self.base_url}/predict/comprehensive"
        payload = {"smiles": smiles}
        
        response = requests.post(endpoint, json=payload)
        response.raise_for_status()
        
        return response.json()
    
    def batch_predict(self, smiles_list: List[str]) -> List[Dict]:
        """
        Batch prediction for multiple molecules.
        
        Args:
            smiles_list: List of SMILES strings
        
        Returns:
            List of prediction dictionaries
        """
        endpoint = f"{self.base_url}/batch/predict"
        payload = {"smiles_list": smiles_list}
        
        response = requests.post(endpoint, json=payload)
        response.raise_for_status()
        
        return response.json()


def example_single_molecule_analysis():
    """Example: Analyze a single molecule (Aspirin)."""
    print("=" * 70)
    print("Example 1: Single Molecule Analysis - Aspirin")
    print("=" * 70)
    
    api = ArditBioCoreAPI()
    aspirin_smiles = "CC(=O)Oc1ccccc1C(=O)O"
    
    # Get comprehensive analysis
    result = api.comprehensive_analysis(aspirin_smiles)
    
    print(f"\nSMILES: {aspirin_smiles}")
    print(f"\nDrug-Likeness:")
    print(f"  - Lipinski Violations: {result['druglikeness']['lipinski']['violations']}")
    print(f"  - QED: {result['druglikeness']['qed']:.3f}")
    print(f"  - SA Score: {result['druglikeness']['sa_score']:.2f}")
    
    print(f"\nADME Properties:")
    print(f"  - LogP: {result['adme']['logp']:.2f}")
    print(f"  - Caco-2: {result['adme']['caco2']['category']}")
    print(f"  - BBB: {result['adme']['bbb']}")
    
    print(f"\nToxicity Assessment:")
    print(f"  - Hepatotoxicity: {result['toxicity']['hepatotoxicity']['risk_level']}")
    print(f"  - hERG: {result['toxicity']['herg']['risk_level']}")
    
    print("\n" + "=" * 70)


def example_batch_screening():
    """Example: Screen multiple kinase inhibitor candidates."""
    print("\n" + "=" * 70)
    print("Example 2: Batch Screening - Kinase Inhibitors")
    print("=" * 70)
    
    api = ArditBioCoreAPI()
    
    # Small library of kinase inhibitor-like molecules
    molecules = {
        "Imatinib": "CN1CCN(CC1)Cc2ccc(cc2)C(=O)Nc3ccc(c(c3)Nc4nccc(n4)c5cccnc5)C(F)(F)F",
        "Gefitinib": "COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1OCCCN4CCOCC4",
        "Erlotinib": "COCCOc1cc2ncnc(Nc3cccc(c3)C#C)c2cc1OC",
        "Sunitinib": "CCN(CC)CCNC(=O)c1c(C)[nH]c(C=C2C(=O)Nc3ccc(F)cc32)c1C",
        "Sorafenib": "CNC(=O)C1=NC=CC(OC2=CC=C(NC(=O)NC3=CC(=C(Cl)C=C3)C(F)(F)F)C=C2)=C1",
    }
    
    smiles_list = list(molecules.values())
    
    # Batch prediction
    results = api.batch_predict(smiles_list)
    
    # Create DataFrame for analysis
    data = []
    for name, result in zip(molecules.keys(), results):
        if 'error' not in result:
            data.append({
                'Name': name,
                'QED': result.get('qed', 0),
                'Kinase_Score': result.get('kinase_inhibitor_score', 0),
                'Hepatotox_Risk': result.get('hepatotoxicity_risk', 'Unknown'),
                'SA_Score': result.get('sa_score', 0)
            })
    
    df = pd.DataFrame(data)
    
    # Rank by QED score
    df = df.sort_values('QED', ascending=False)
    
    print(f"\nScreened {len(df)} kinase inhibitor candidates")
    print(f"\nRanked by QED (Drug-Likeness):")
    print(df.to_string(index=False))
    
    print("\n" + "=" * 70)


def example_lead_optimization():
    """Example: Compare lead compound with analogs."""
    print("\n" + "=" * 70)
    print("Example 3: Lead Optimization - Aspirin Analogs")
    print("=" * 70)
    
    api = ArditBioCoreAPI()
    
    # Aspirin and related compounds
    compounds = {
        "Aspirin": "CC(=O)Oc1ccccc1C(=O)O",
        "Salicylic Acid": "O=C(O)c1ccccc1O",
        "Methyl Salicylate": "COC(=O)c1ccccc1O",
        "Acetaminophen": "CC(=O)Nc1ccc(O)cc1",
    }
    
    print("\nComparing Aspirin with related compounds:\n")
    
    results = []
    for name, smiles in compounds.items():
        try:
            result = api.predict_druglikeness(smiles)
            results.append({
                'Compound': name,
                'Lipinski_Violations': result['lipinski']['violations'],
                'QED': result['qed'],
                'SA_Score': result['sa_score'],
                'Drug_Like': '✓' if result['qed'] > 0.5 else '✗'
            })
        except Exception as e:
            print(f"Error analyzing {name}: {e}")
    
    df = pd.DataFrame(results)
    print(df.to_string(index=False))
    
    print("\n" + "=" * 70)


def example_export_results():
    """Example: Export results to CSV."""
    print("\n" + "=" * 70)
    print("Example 4: Export Results to CSV")
    print("=" * 70)
    
    api = ArditBioCoreAPI()
    
    # Small drug library
    drugs = {
        "Aspirin": "CC(=O)Oc1ccccc1C(=O)O",
        "Ibuprofen": "CC(C)Cc1ccc(cc1)C(C)C(=O)O",
        "Naproxen": "COc1ccc2cc(ccc2c1)C(C)C(=O)O",
    }
    
    results = []
    for name, smiles in drugs.items():
        try:
            result = api.comprehensive_analysis(smiles)
            results.append({
                'Name': name,
                'SMILES': smiles,
                'QED': result['druglikeness']['qed'],
                'LogP': result['adme']['logp'],
                'Hepatotox': result['toxicity']['hepatotoxicity']['risk_level'],
                'SA_Score': result['druglikeness']['sa_score']
            })
        except Exception as e:
            print(f"Error: {e}")
    
    df = pd.DataFrame(results)
    
    # Save to CSV
    output_file = "ardit_biocore_results.csv"
    df.to_csv(output_file, index=False)
    
    print(f"\n✓ Results exported to: {output_file}")
    print(f"\nPreview:")
    print(df.to_string(index=False))
    
    print("\n" + "=" * 70)


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("Ardit BioCore API Usage Demo")
    print("=" * 70)
    print("\nNOTE: This requires the FastAPI server to be running.")
    print("Start server with: uvicorn api.prediction_api:app --host 0.0.0.0 --port 8000")
    print("=" * 70)
    
    try:
        # Check if API is available
        api = ArditBioCoreAPI()
        response = requests.get(f"{api.base_url}/docs")
        if response.status_code != 200:
            raise ConnectionError("API not responding")
        
        # Run examples
        example_single_molecule_analysis()
        example_batch_screening()
        example_lead_optimization()
        example_export_results()
        
        print("\n✓ All examples completed successfully!")
        print("\nNext Steps:")
        print("  1. Explore the API documentation at http://localhost:8000/docs")
        print("  2. Modify the examples for your own molecules")
        print("  3. Integrate into your drug discovery pipeline")
        
    except requests.exceptions.ConnectionError:
        print("\n✗ ERROR: Cannot connect to FastAPI server")
        print("\nPlease start the server first:")
        print("  uvicorn api.prediction_api:app --host 0.0.0.0 --port 8000")
    except Exception as e:
        print(f"\n✗ ERROR: {e}")


if __name__ == "__main__":
    main()
