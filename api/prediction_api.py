from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.molecular_utils import MolecularProcessor
from utils.drug_likeness import DrugLikenessCalculator
from models.adme_predictors import ADMEPredictor
from models.toxicity_predictors import ToxicityPredictor
from models.target_predictors import TargetClassPredictor

app = FastAPI(
    title="AbbVie-Aligned Drug Discovery API",
    description="REST API for molecular property prediction and drug-likeness assessment",
    version="1.0.0"
)

mol_processor = MolecularProcessor()
drug_likeness = DrugLikenessCalculator()
adme_predictor = ADMEPredictor()
toxicity_predictor = ToxicityPredictor()
target_predictor = TargetClassPredictor()


class MoleculeInput(BaseModel):
    smiles: str
    name: Optional[str] = None


class BatchMoleculeInput(BaseModel):
    molecules: List[MoleculeInput]


@app.get("/")
def read_root():
    return {
        "message": "AbbVie-Aligned Drug Discovery API",
        "version": "1.0.0",
        "endpoints": [
            "/predict/druglikeness",
            "/predict/adme",
            "/predict/toxicity",
            "/predict/target",
            "/predict/comprehensive",
            "/batch/predict"
        ]
    }


@app.post("/predict/druglikeness")
def predict_druglikeness(molecule: MoleculeInput) -> Dict:
    is_valid, canonical_smiles = mol_processor.validate_smiles(molecule.smiles)
    
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid SMILES string")
    
    mol = mol_processor.smiles_to_mol(canonical_smiles)
    result = drug_likeness.comprehensive_analysis(mol)
    
    return {
        "molecule_name": molecule.name or "Unknown",
        "smiles": canonical_smiles,
        "analysis": result
    }


@app.post("/predict/adme")
def predict_adme(molecule: MoleculeInput) -> Dict:
    is_valid, canonical_smiles = mol_processor.validate_smiles(molecule.smiles)
    
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid SMILES string")
    
    mol = mol_processor.smiles_to_mol(canonical_smiles)
    result = adme_predictor.comprehensive_adme_profile(mol)
    
    return {
        "molecule_name": molecule.name or "Unknown",
        "smiles": canonical_smiles,
        "adme_profile": result
    }


@app.post("/predict/toxicity")
def predict_toxicity(molecule: MoleculeInput) -> Dict:
    is_valid, canonical_smiles = mol_processor.validate_smiles(molecule.smiles)
    
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid SMILES string")
    
    mol = mol_processor.smiles_to_mol(canonical_smiles)
    result = toxicity_predictor.comprehensive_toxicity_profile(mol)
    
    return {
        "molecule_name": molecule.name or "Unknown",
        "smiles": canonical_smiles,
        "toxicity_profile": result
    }


@app.post("/predict/target")
def predict_target(molecule: MoleculeInput) -> Dict:
    is_valid, canonical_smiles = mol_processor.validate_smiles(molecule.smiles)
    
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid SMILES string")
    
    mol = mol_processor.smiles_to_mol(canonical_smiles)
    result = target_predictor.comprehensive_target_prediction(mol)
    
    return {
        "molecule_name": molecule.name or "Unknown",
        "smiles": canonical_smiles,
        "target_prediction": result
    }


@app.post("/predict/comprehensive")
def predict_comprehensive(molecule: MoleculeInput) -> Dict:
    is_valid, canonical_smiles = mol_processor.validate_smiles(molecule.smiles)
    
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid SMILES string")
    
    mol = mol_processor.smiles_to_mol(canonical_smiles)
    
    return {
        "molecule_name": molecule.name or "Unknown",
        "smiles": canonical_smiles,
        "basic_properties": mol_processor.calculate_basic_properties(mol),
        "drug_likeness": drug_likeness.comprehensive_analysis(mol),
        "adme_profile": adme_predictor.comprehensive_adme_profile(mol),
        "toxicity_profile": toxicity_predictor.comprehensive_toxicity_profile(mol),
        "target_prediction": target_predictor.comprehensive_target_prediction(mol)
    }


@app.post("/batch/predict")
def batch_predict(batch: BatchMoleculeInput) -> List[Dict]:
    results = []
    
    for molecule in batch.molecules:
        try:
            is_valid, canonical_smiles = mol_processor.validate_smiles(molecule.smiles)
            
            if not is_valid:
                results.append({
                    "molecule_name": molecule.name or "Unknown",
                    "error": "Invalid SMILES string"
                })
                continue
            
            mol = mol_processor.smiles_to_mol(canonical_smiles)
            
            results.append({
                "molecule_name": molecule.name or "Unknown",
                "smiles": canonical_smiles,
                "drug_likeness": drug_likeness.comprehensive_analysis(mol),
                "adme_profile": adme_predictor.comprehensive_adme_profile(mol),
                "toxicity_profile": toxicity_predictor.comprehensive_toxicity_profile(mol)
            })
        
        except Exception as e:
            results.append({
                "molecule_name": molecule.name or "Unknown",
                "error": str(e)
            })
    
    return results


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
