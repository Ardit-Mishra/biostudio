# =============================================================================
# FASTAPI PREDICTION API MODULE
# =============================================================================
# This module provides REST API endpoints for pharmaceutical predictions.
# Enables programmatic access to all platform capabilities:
# - Drug-likeness analysis
# - ADME/PK profiling
# - Toxicity screening
# - Target class prediction
# - Comprehensive analysis
# - Batch processing
#
# Run with: uvicorn api.prediction_api:app --host 0.0.0.0 --port 8000
# =============================================================================

# Import FastAPI framework for building REST APIs
from fastapi import FastAPI, HTTPException
# Import Pydantic for request/response data validation
from pydantic import BaseModel
# Import type hints for documentation
from typing import List, Dict, Optional
# Import sys for modifying Python path
import sys
# Import os for path manipulation
import os

# Add parent directory to Python path
# This allows importing from sibling directories (utils, models)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import core molecular processing utilities
from utils.molecular_utils import MolecularProcessor
# Import drug-likeness calculator
from utils.drug_likeness import DrugLikenessCalculator
# Import ADME prediction module
from models.adme_predictors import ADMEPredictor
# Import toxicity prediction module
from models.toxicity_predictors import ToxicityPredictor
# Import target class prediction module
from models.target_predictors import TargetClassPredictor

# Create FastAPI application instance
# title: Display name in API documentation
# description: Explains API purpose
# version: API version number
app = FastAPI(
    title="AI-Powered Drug Discovery API",
    description="REST API for molecular property prediction, ADME/PK analysis, toxicity screening, and drug-likeness assessment",
    version="1.0.0"
)

# Initialize model instances (created once, reused for all requests)
# MolecularProcessor: SMILES validation and property calculation
mol_processor = MolecularProcessor()
# DrugLikenessCalculator: Lipinski, Veber, QED, SA scores
drug_likeness = DrugLikenessCalculator()
# ADMEPredictor: Absorption, distribution, metabolism, excretion
adme_predictor = ADMEPredictor()
# ToxicityPredictor: Hepatotox, cardiotox, mutagenicity, carcinogenicity
toxicity_predictor = ToxicityPredictor()
# TargetClassPredictor: Kinase, GPCR, ion channel, enzyme
target_predictor = TargetClassPredictor()


# Pydantic model for single molecule input
# Defines expected request body structure
class MoleculeInput(BaseModel):
    # SMILES string is required
    smiles: str
    # Molecule name is optional (defaults to None)
    name: Optional[str] = None


# Pydantic model for batch molecule input
# Allows processing multiple molecules in one request
class BatchMoleculeInput(BaseModel):
    # List of MoleculeInput objects
    molecules: List[MoleculeInput]


# Root endpoint - API documentation/welcome page
# GET / returns API information
@app.get("/")
def read_root():
    # Return JSON with API info and available endpoints
    return {
        # Welcome message
        "message": "AI-Powered Drug Discovery API",
        # API description
        "description": "Computational chemistry and machine learning platform for pharmaceutical research",
        # Current version
        "version": "1.0.0",
        # List of available endpoints
        "endpoints": [
            "/predict/druglikeness",
            "/predict/adme",
            "/predict/toxicity",
            "/predict/target",
            "/predict/comprehensive",
            "/batch/predict"
        ]
    }


# Drug-likeness prediction endpoint
# POST /predict/druglikeness
# Analyzes molecule for Lipinski, Veber, QED, SA scores
@app.post("/predict/druglikeness")
def predict_druglikeness(molecule: MoleculeInput) -> Dict:
    # Validate and canonicalize SMILES input
    is_valid, canonical_smiles = mol_processor.validate_smiles(molecule.smiles)
    
    # Return HTTP 400 error if SMILES is invalid
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid SMILES string")
    
    # Convert SMILES to RDKit molecule object
    mol = mol_processor.smiles_to_mol(canonical_smiles)
    
    # Run comprehensive drug-likeness analysis
    result = drug_likeness.comprehensive_analysis(mol)
    
    # Return results with molecule info
    return {
        # Molecule name (from input or "Unknown")
        "molecule_name": molecule.name or "Unknown",
        # Canonical SMILES representation
        "smiles": canonical_smiles,
        # Drug-likeness analysis results
        "analysis": result
    }


# ADME/PK prediction endpoint
# POST /predict/adme
# Predicts absorption, distribution, metabolism, excretion properties
@app.post("/predict/adme")
def predict_adme(molecule: MoleculeInput) -> Dict:
    # Validate SMILES input
    is_valid, canonical_smiles = mol_processor.validate_smiles(molecule.smiles)
    
    # Return error for invalid SMILES
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid SMILES string")
    
    # Convert to RDKit molecule
    mol = mol_processor.smiles_to_mol(canonical_smiles)
    
    # Run comprehensive ADME profiling
    result = adme_predictor.comprehensive_adme_profile(mol)
    
    # Return ADME profile with molecule info
    return {
        "molecule_name": molecule.name or "Unknown",
        "smiles": canonical_smiles,
        "adme_profile": result
    }


# Toxicity prediction endpoint
# POST /predict/toxicity
# Assesses hepatotoxicity, cardiotoxicity, mutagenicity, carcinogenicity
@app.post("/predict/toxicity")
def predict_toxicity(molecule: MoleculeInput) -> Dict:
    # Validate SMILES input
    is_valid, canonical_smiles = mol_processor.validate_smiles(molecule.smiles)
    
    # Return error for invalid SMILES
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid SMILES string")
    
    # Convert to RDKit molecule
    mol = mol_processor.smiles_to_mol(canonical_smiles)
    
    # Run comprehensive toxicity profiling
    result = toxicity_predictor.comprehensive_toxicity_profile(mol)
    
    # Return toxicity profile with molecule info
    return {
        "molecule_name": molecule.name or "Unknown",
        "smiles": canonical_smiles,
        "toxicity_profile": result
    }


# Target class prediction endpoint
# POST /predict/target
# Predicts likely drug target class (kinase, GPCR, ion channel, enzyme)
@app.post("/predict/target")
def predict_target(molecule: MoleculeInput) -> Dict:
    # Validate SMILES input
    is_valid, canonical_smiles = mol_processor.validate_smiles(molecule.smiles)
    
    # Return error for invalid SMILES
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid SMILES string")
    
    # Convert to RDKit molecule
    mol = mol_processor.smiles_to_mol(canonical_smiles)
    
    # Run comprehensive target prediction
    result = target_predictor.comprehensive_target_prediction(mol)
    
    # Return target predictions with molecule info
    return {
        "molecule_name": molecule.name or "Unknown",
        "smiles": canonical_smiles,
        "target_prediction": result
    }


# Comprehensive prediction endpoint
# POST /predict/comprehensive
# Runs all analyses in one request
@app.post("/predict/comprehensive")
def predict_comprehensive(molecule: MoleculeInput) -> Dict:
    # Validate SMILES input
    is_valid, canonical_smiles = mol_processor.validate_smiles(molecule.smiles)
    
    # Return error for invalid SMILES
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid SMILES string")
    
    # Convert to RDKit molecule
    mol = mol_processor.smiles_to_mol(canonical_smiles)
    
    # Return all analyses combined
    return {
        # Molecule identification
        "molecule_name": molecule.name or "Unknown",
        "smiles": canonical_smiles,
        # Basic molecular properties
        "basic_properties": mol_processor.calculate_basic_properties(mol),
        # Drug-likeness scores
        "drug_likeness": drug_likeness.comprehensive_analysis(mol),
        # ADME/PK profile
        "adme_profile": adme_predictor.comprehensive_adme_profile(mol),
        # Toxicity assessment
        "toxicity_profile": toxicity_predictor.comprehensive_toxicity_profile(mol),
        # Target class prediction
        "target_prediction": target_predictor.comprehensive_target_prediction(mol)
    }


# Batch prediction endpoint
# POST /batch/predict
# Process multiple molecules in one request
# Useful for high-throughput screening workflows
@app.post("/batch/predict")
def batch_predict(batch: BatchMoleculeInput) -> List[Dict]:
    # Initialize results list
    results = []
    
    # Process each molecule in the batch
    for molecule in batch.molecules:
        # Wrap in try-except for error handling
        try:
            # Validate SMILES
            is_valid, canonical_smiles = mol_processor.validate_smiles(molecule.smiles)
            
            # Handle invalid SMILES gracefully (don't fail entire batch)
            if not is_valid:
                # Add error result and continue to next molecule
                results.append({
                    "molecule_name": molecule.name or "Unknown",
                    "error": "Invalid SMILES string"
                })
                # Skip to next molecule
                continue
            
            # Convert to RDKit molecule
            mol = mol_processor.smiles_to_mol(canonical_smiles)
            
            # Run analyses and add to results
            results.append({
                "molecule_name": molecule.name or "Unknown",
                "smiles": canonical_smiles,
                # Include key analyses
                "drug_likeness": drug_likeness.comprehensive_analysis(mol),
                "adme_profile": adme_predictor.comprehensive_adme_profile(mol),
                "toxicity_profile": toxicity_predictor.comprehensive_toxicity_profile(mol)
            })
        
        # Handle any unexpected errors
        except Exception as e:
            # Add error to results and continue
            results.append({
                "molecule_name": molecule.name or "Unknown",
                "error": str(e)
            })
    
    # Return all results
    return results


# Entry point for running server directly
# Execute with: python api/prediction_api.py
if __name__ == "__main__":
    # Import uvicorn ASGI server
    import uvicorn
    # Run server on all interfaces (0.0.0.0) port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
