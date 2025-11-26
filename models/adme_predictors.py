# =============================================================================
# ADME/PK PREDICTION MODULE
# =============================================================================
# This module predicts ADME (Absorption, Distribution, Metabolism, Excretion)
# and Pharmacokinetic (PK) properties of drug candidates.
#
# ADME describes what happens to a drug in the body:
# - Absorption: Getting into the bloodstream (from gut, skin, etc.)
# - Distribution: Where the drug goes (brain, fat, organs)
# - Metabolism: How the body breaks down the drug (mainly liver)
# - Excretion: How the drug leaves the body (kidney, bile, etc.)
#
# NOTE: These are heuristic predictions for educational purposes.
# Production use requires validated QSAR models trained on experimental data.
# =============================================================================

# Import numpy for numerical operations
import numpy as np
# Import scikit-learn for machine learning models (future use)
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
# Import type hints for better code documentation
from typing import Dict, Optional
# Import RDKit core chemistry module
from rdkit import Chem
# Import RDKit descriptor calculators
# Descriptors: General molecular properties (MW, TPSA, etc.)
# Crippen: LogP calculation (Wildman-Crippen method)
# Lipinski: Drug-likeness descriptors
from rdkit.Chem import Descriptors, Crippen, Lipinski


# Main class for ADME/PK predictions
# Uses molecular descriptors to estimate pharmacokinetic properties
class ADMEPredictor:
    
    # Constructor initializes models dictionary and loads models
    def __init__(self):
        # Dictionary to store trained ML models (for future use)
        self.models = {}
        # Initialize any pre-trained models
        self._initialize_models()
    
    # Model initialization method
    # Currently empty - placeholder for loading trained models
    def _initialize_models(self):
        # Future: Load pre-trained QSAR models from disk
        pass
    
    # Predict LogP (partition coefficient)
    # LogP = log of octanol/water partition ratio
    # Measures how "fatty" (lipophilic) vs "water-loving" (hydrophilic) a molecule is
    def predict_logp(self, mol) -> Dict:
        # Validate molecule input
        if mol is None:
            return {'error': 'Invalid molecule'}
        
        # Calculate LogP using Wildman-Crippen method from RDKit
        # This is an atom-type based calculation
        logp = Crippen.MolLogP(mol)
        
        # Initialize interpretation based on LogP value
        interpretation = ""
        
        # Interpret LogP value for drug development context
        if logp < 0:
            # Negative LogP = highly water-soluble
            # May have trouble crossing cell membranes
            interpretation = "Highly hydrophilic - may have poor membrane permeability"
        elif logp <= 3:
            # Sweet spot for oral drugs
            # Good balance between solubility and permeability
            interpretation = "Good balance - optimal for oral bioavailability"
        elif logp <= 5:
            # Lipophilic - crosses membranes easily
            # But may have solubility or metabolic issues
            interpretation = "Lipophilic - good membrane permeability but potential issues"
        else:
            # Very lipophilic (LogP > 5)
            # Poor solubility, may accumulate in fat tissue
            interpretation = "Highly lipophilic - may have poor solubility and ADME issues"
        
        # Return LogP prediction results
        return {
            # LogP value rounded to 2 decimal places
            'LogP': round(logp, 2),
            # Simple category: Optimal (0-3) or Suboptimal
            'Category': 'Optimal' if 0 <= logp <= 3 else 'Suboptimal',
            # Detailed interpretation for the user
            'Interpretation': interpretation
        }
    
    # Predict Caco-2 permeability
    # Caco-2 cells are human intestinal cells used to model drug absorption
    # High permeability = drug can cross from gut into bloodstream
    def predict_caco2_permeability(self, mol) -> Dict:
        # Validate molecule input
        if mol is None:
            return {'error': 'Invalid molecule'}
        
        # Get key molecular properties that affect permeability
        # LogP: More lipophilic = better membrane crossing
        logp = Crippen.MolLogP(mol)
        
        # TPSA: Polar surface area - higher = worse permeability
        tpsa = Descriptors.TPSA(mol)
        
        # Molecular weight - not directly used but collected for reference
        mw = Descriptors.MolWt(mol)
        
        # Hydrogen bond donors - more donors = worse permeability
        hbd = Descriptors.NumHDonors(mol)
        
        # Calculate permeability score using heuristic formula
        # Positive contributions: LogP (x10)
        # Negative contributions: TPSA (x0.1), H-bond donors (x5)
        # Base of 50 centers the scale
        permeability_score = (logp * 10) - (tpsa * 0.1) - (hbd * 5) + 50
        
        # Clamp score to 0-100 range
        permeability_score = max(0, min(100, permeability_score))
        
        # Categorize permeability and interpret results
        if permeability_score >= 70:
            # High permeability: Excellent absorption expected
            category = "High permeability"
            interpretation = "Excellent intestinal absorption expected (>70%)"
        elif permeability_score >= 40:
            # Moderate permeability: Acceptable absorption
            category = "Moderate permeability"
            interpretation = "Good absorption expected (40-70%)"
        else:
            # Low permeability: Poor absorption
            # May need formulation strategies or alternative delivery
            category = "Low permeability"
            interpretation = "Poor absorption expected (<40%)"
        
        # Return Caco-2 permeability prediction results
        return {
            # Permeability score (0-100)
            'Caco-2 Score': round(permeability_score, 1),
            # Category label
            'Category': category,
            # Detailed interpretation
            'Interpretation': interpretation,
            # Include TPSA and HBD as contributing factors
            'TPSA': round(tpsa, 2),
            'HBD': hbd
        }
    
    # Predict Blood-Brain Barrier (BBB) penetration
    # BBB is a selective barrier protecting the brain
    # Important for CNS drugs (need penetration) vs peripheral drugs (avoid penetration)
    def predict_bbb_penetration(self, mol) -> Dict:
        # Validate molecule input
        if mol is None:
            return {'error': 'Invalid molecule'}
        
        # Get molecular properties affecting BBB penetration
        # LogP: Lipophilic molecules cross BBB better
        logp = Crippen.MolLogP(mol)
        
        # TPSA: Critical for BBB - must be <90Å² for good penetration
        tpsa = Descriptors.TPSA(mol)
        
        # Molecular weight - smaller molecules cross easier
        mw = Descriptors.MolWt(mol)
        
        # Hydrogen bond donors and acceptors
        hbd = Descriptors.NumHDonors(mol)
        hba = Descriptors.NumHAcceptors(mol)
        
        # Calculate BBB penetration score using heuristic formula
        # Higher LogP helps, high TPSA hurts, many H-bond donors hurt
        bbb_score = (logp - (tpsa / 20) - (hbd * 0.5))
        
        # Categorize BBB penetration based on score and TPSA
        if bbb_score > 0.3 and tpsa < 90:
            # High penetration: Will reach brain effectively
            category = "High BBB penetration"
            probability = "High (>80%)"
        elif bbb_score > -0.5 and tpsa < 120:
            # Moderate penetration: Some brain exposure
            category = "Moderate BBB penetration"
            probability = "Moderate (40-80%)"
        else:
            # Low penetration: Stays in periphery
            category = "Low BBB penetration"
            probability = "Low (<40%)"
        
        # Return BBB penetration prediction results
        return {
            # BBB score (higher = better penetration)
            'BBB Score': round(bbb_score, 2),
            # Category label
            'Category': category,
            # Probability of brain penetration
            'Probability': probability,
            # TPSA is key factor
            'TPSA': round(tpsa, 2),
            # Recommendation based on results
            'Recommendation': 'Suitable for CNS drugs' if bbb_score > 0.3 else 'Peripheral action likely'
        }
    
    # Predict CYP450 metabolism
    # CYP450 enzymes in liver are responsible for drug metabolism
    # Understanding which enzyme metabolizes a drug helps predict:
    # - Drug-drug interactions
    # - Dosing requirements
    # - Genetic variation effects
    def predict_cyp450_metabolism(self, mol) -> Dict:
        # Validate molecule input
        if mol is None:
            return {'error': 'Invalid molecule'}
        
        # Get molecular properties affecting CYP metabolism
        # LogP: Lipophilic drugs are more likely CYP substrates
        logp = Crippen.MolLogP(mol)
        
        # Molecular weight
        mw = Descriptors.MolWt(mol)
        
        # Aromatic rings are common sites of CYP metabolism
        aromatic_rings = Descriptors.NumAromaticRings(mol)
        
        # Calculate probability of being substrate for each major CYP enzyme
        # These are heuristic formulas based on known substrate properties
        
        # CYP3A4: Metabolizes ~50% of all drugs
        # Prefers large, lipophilic molecules
        cyp3a4_prob = min(100, max(0, (logp * 15) + (aromatic_rings * 20) + 30))
        
        # CYP2D6: Metabolizes ~25% of drugs
        # Important for many psychiatric and cardiovascular drugs
        cyp2d6_prob = min(100, max(0, (logp * 12) + (aromatic_rings * 15) + 25))
        
        # CYP2C9: Important for anti-inflammatory and anticoagulant drugs
        cyp2c9_prob = min(100, max(0, (logp * 10) + (aromatic_rings * 18) + 20))
        
        # Return CYP450 metabolism prediction results
        return {
            # Probability of being CYP3A4 substrate
            'CYP3A4 Substrate Probability': f"{round(cyp3a4_prob, 1)}%",
            # Probability of being CYP2D6 substrate
            'CYP2D6 Substrate Probability': f"{round(cyp2d6_prob, 1)}%",
            # Probability of being CYP2C9 substrate
            'CYP2C9 Substrate Probability': f"{round(cyp2c9_prob, 1)}%",
            # Identify the most likely primary metabolizer
            'Primary Metabolizer': 'CYP3A4' if cyp3a4_prob == max(cyp3a4_prob, cyp2d6_prob, cyp2c9_prob) else
                                   'CYP2D6' if cyp2d6_prob == max(cyp3a4_prob, cyp2d6_prob, cyp2c9_prob) else 'CYP2C9',
            # General recommendation about drug interactions
            'Interpretation': 'Monitor for drug-drug interactions with CYP inhibitors/inducers'
        }
    
    # Predict clearance (elimination rate)
    # Clearance determines how fast a drug is removed from the body
    # Affects dosing frequency and potential for accumulation
    def predict_clearance(self, mol) -> Dict:
        # Validate molecule input
        if mol is None:
            return {'error': 'Invalid molecule'}
        
        # Get molecular properties affecting clearance
        # LogP: Lipophilic drugs often have slower clearance
        logp = Crippen.MolLogP(mol)
        
        # Molecular weight: Larger molecules may have different clearance
        mw = Descriptors.MolWt(mol)
        
        # TPSA: Affects renal vs hepatic clearance route
        tpsa = Descriptors.TPSA(mol)
        
        # Calculate clearance score using heuristic formula
        # Higher LogP contributes to score (metabolic clearance)
        # Larger MW slightly increases score
        # Higher TPSA reduces score (polar compounds have different clearance)
        clearance_score = (logp * 5) + (mw * 0.01) - (tpsa * 0.1)
        
        # Clamp to 10-100 range
        clearance_score = max(10, min(100, clearance_score))
        
        # Categorize clearance and provide interpretation
        if clearance_score >= 60:
            # High clearance: Drug eliminated quickly
            # May need frequent dosing
            category = "High clearance"
            interpretation = "Rapid elimination - may require frequent dosing"
        elif clearance_score >= 30:
            # Moderate clearance: Balanced elimination
            # Good for once or twice daily dosing
            category = "Moderate clearance"
            interpretation = "Balanced elimination profile"
        else:
            # Low clearance: Drug stays in body longer
            # Risk of accumulation with repeated dosing
            category = "Low clearance"
            interpretation = "Slow elimination - potential for accumulation"
        
        # Return clearance prediction results
        return {
            # Clearance score
            'Clearance Score': round(clearance_score, 1),
            # Category label
            'Category': category,
            # Detailed interpretation
            'Interpretation': interpretation,
            # Estimated half-life based on clearance
            'Half-life Estimate': 'Short (<4h)' if clearance_score >= 60 else 'Medium (4-12h)' if clearance_score >= 30 else 'Long (>12h)'
        }
    
    # Generate comprehensive ADME profile
    # Combines all five ADME predictions into single report
    # Called by ADME Navigator page in the app
    def comprehensive_adme_profile(self, mol) -> Dict:
        # Run all ADME predictions and return as dictionary
        return {
            # Lipophilicity assessment
            'LogP': self.predict_logp(mol),
            # Intestinal absorption prediction
            'Caco-2 Permeability': self.predict_caco2_permeability(mol),
            # Brain penetration prediction
            'BBB Penetration': self.predict_bbb_penetration(mol),
            # Liver metabolism prediction
            'CYP450 Metabolism': self.predict_cyp450_metabolism(mol),
            # Elimination rate prediction
            'Clearance': self.predict_clearance(mol)
        }
