# =============================================================================
# TARGET CLASS PREDICTION MODULE
# =============================================================================
# This module predicts which type of biological target a molecule might bind to.
# Targets are proteins that drugs interact with to produce therapeutic effects.
#
# Main target classes:
# - Kinase Inhibitors: Block enzymes that add phosphate groups to proteins
# - GPCR Ligands: Bind to G-protein coupled receptors (cell signaling)
# - Ion Channel Modulators: Affect channels that control ion flow across membranes
# - Enzyme Inhibitors: Block various metabolic enzymes
#
# NOTE: These are heuristic predictions based on molecular properties.
# Real target identification requires experimental binding assays.
# =============================================================================

# Import numpy for numerical calculations
import numpy as np
# Import type hints for better code documentation
from typing import Dict, List
# Import RDKit core chemistry module
from rdkit import Chem
# Import RDKit descriptor calculators
# Descriptors: General molecular properties
# Crippen: LogP calculations
# Fragments: Count specific functional groups
# AllChem: Advanced chemistry operations
from rdkit.Chem import Descriptors, Crippen, Fragments, AllChem


# Main class for predicting drug target classes
# Uses molecular property patterns to estimate likely targets
class TargetClassPredictor:
    
    # Constructor initializes empty models dictionary
    def __init__(self):
        # Placeholder for future ML model storage
        self.models = {}
    
    # Predict kinase inhibitor probability
    # Kinases are enzymes that control cell growth and division
    # Many cancer drugs are kinase inhibitors (e.g., Imatinib, Gefitinib)
    def predict_kinase_inhibitor(self, mol) -> Dict:
        # Validate molecule input
        if mol is None:
            return {'error': 'Invalid molecule'}
        
        # Get molecular properties that correlate with kinase inhibition
        # Most kinase inhibitors share certain structural features
        
        # Aromatic rings: Kinase inhibitors typically have 3-5 rings
        # These form π-π stacking interactions with kinase binding site
        aromatic_rings = Descriptors.NumAromaticRings(mol)
        
        # Hydrogen bond donors: Usually 1-3 for kinase binding
        hbd = Descriptors.NumHDonors(mol)
        
        # Hydrogen bond acceptors: Usually 3-6 for ATP-competitive binding
        hba = Descriptors.NumHAcceptors(mol)
        
        # Molecular weight: Kinase inhibitors typically 300-550 Da
        mw = Descriptors.MolWt(mol)
        
        # LogP: Moderate lipophilicity (2-5) for cell penetration
        logp = Crippen.MolLogP(mol)
        
        # Calculate kinase inhibitor score based on feature matching
        score = 0
        
        # Award points for aromatic rings in optimal range (3-5)
        if 3 <= aromatic_rings <= 5:
            score += 25
        
        # Award points for H-bond donors in optimal range (1-3)
        if 1 <= hbd <= 3:
            score += 20
        
        # Award points for H-bond acceptors in optimal range (3-6)
        if 3 <= hba <= 6:
            score += 20
        
        # Award points for molecular weight in optimal range (300-550 Da)
        if 300 <= mw <= 550:
            score += 20
        
        # Award points for LogP in optimal range (2-5)
        if 2 <= logp <= 5:
            score += 15
        
        # Cap probability at 100%
        probability = min(100, score)
        
        # Categorize likelihood and provide interpretation
        if probability >= 70:
            # High score: Strong kinase inhibitor characteristics
            category = "Highly Likely"
            interpretation = "Strong structural similarity to known kinase inhibitors"
        elif probability >= 40:
            # Moderate score: Some matching features
            category = "Possible"
            interpretation = "Some kinase inhibitor characteristics present"
        else:
            # Low score: Doesn't match typical profile
            category = "Unlikely"
            interpretation = "Does not match typical kinase inhibitor profile"
        
        # Return kinase inhibitor prediction results
        return {
            # Probability as percentage
            'Kinase Inhibitor Probability': f"{probability}%",
            # Likelihood category
            'Category': category,
            # Detailed interpretation
            'Interpretation': interpretation,
            # Key features for transparency
            'Key Features': f"Aromatic rings: {aromatic_rings}, HBD: {hbd}, HBA: {hba}"
        }
    
    # Predict GPCR ligand probability
    # GPCRs (G-Protein Coupled Receptors) are the largest drug target family
    # ~34% of all FDA-approved drugs target GPCRs
    def predict_gpcr_ligand(self, mol) -> Dict:
        # Validate molecule input
        if mol is None:
            return {'error': 'Invalid molecule'}
        
        # Get molecular properties that correlate with GPCR binding
        
        # Molecular weight: GPCR ligands typically smaller (200-450 Da)
        mw = Descriptors.MolWt(mol)
        
        # LogP: Moderate lipophilicity (1-4) for membrane protein interaction
        logp = Crippen.MolLogP(mol)
        
        # Rotatable bonds: Moderate flexibility (2-8) for receptor binding
        rotatable_bonds = Descriptors.NumRotatableBonds(mol)
        
        # Basic nitrogens: Many GPCR ligands contain amines
        # Count NH2, NH, and aromatic NH groups
        basic_nitrogens = Fragments.fr_NH2(mol) + Fragments.fr_NH1(mol) + Fragments.fr_Ar_NH(mol)
        
        # Aromatic rings: Typically 1-3 for GPCR ligands
        aromatic_rings = Descriptors.NumAromaticRings(mol)
        
        # Calculate GPCR ligand score
        score = 0
        
        # Award points for molecular weight in optimal range
        if 200 <= mw <= 450:
            score += 25
        
        # Award points for LogP in optimal range
        if 1 <= logp <= 4:
            score += 25
        
        # Award points for rotatable bonds in optimal range
        if 2 <= rotatable_bonds <= 8:
            score += 20
        
        # Award points for presence of basic nitrogens
        # Important for aminergic receptors (dopamine, serotonin, etc.)
        if basic_nitrogens >= 1:
            score += 20
        
        # Award points for aromatic rings in optimal range
        if 1 <= aromatic_rings <= 3:
            score += 10
        
        # Cap probability at 100%
        probability = min(100, score)
        
        # Categorize and interpret results
        if probability >= 70:
            category = "Highly Likely"
            interpretation = "Strong GPCR ligand characteristics"
        elif probability >= 40:
            category = "Possible"
            interpretation = "Some GPCR ligand features present"
        else:
            category = "Unlikely"
            interpretation = "Does not match typical GPCR ligand profile"
        
        # Return GPCR ligand prediction results
        return {
            # Probability as percentage
            'GPCR Ligand Probability': f"{probability}%",
            # Likelihood category
            'Category': category,
            # Detailed interpretation
            'Interpretation': interpretation,
            # Suggest receptor subtype based on nitrogen content
            'Receptor Subtype Hint': 'Consider aminergic GPCR' if basic_nitrogens >= 1 else 'Consider peptidergic GPCR'
        }
    
    # Predict ion channel modulator probability
    # Ion channels control electrical signals in nerves and muscles
    # Important for pain, cardiac, and neurological drugs
    def predict_ion_channel_modulator(self, mol) -> Dict:
        # Validate molecule input
        if mol is None:
            return {'error': 'Invalid molecule'}
        
        # Get molecular properties for ion channel modulator prediction
        
        # Molecular weight: Medium size molecules (250-500 Da)
        mw = Descriptors.MolWt(mol)
        
        # LogP: Moderate to high lipophilicity (2-5) for membrane insertion
        logp = Crippen.MolLogP(mol)
        
        # Aromatic rings: Multiple rings for channel pore binding
        aromatic_rings = Descriptors.NumAromaticRings(mol)
        
        # Rotatable bonds: Limited flexibility for channel fitting
        rotatable_bonds = Descriptors.NumRotatableBonds(mol)
        
        # Calculate ion channel modulator score
        score = 0
        
        # Award points for molecular weight in optimal range
        if 250 <= mw <= 500:
            score += 25
        
        # Award points for LogP in optimal range
        if 2 <= logp <= 5:
            score += 25
        
        # Award points for aromatic rings in optimal range
        if 2 <= aromatic_rings <= 4:
            score += 25
        
        # Award points for limited rotatable bonds (rigid structure)
        if rotatable_bonds <= 6:
            score += 25
        
        # Cap probability at 100%
        probability = min(100, score)
        
        # Categorize and suggest channel type
        if probability >= 70:
            category = "Highly Likely"
            interpretation = "Strong ion channel modulator characteristics"
            # Voltage-gated channels are more common drug targets
            channel_type = "Voltage-gated channel"
        elif probability >= 40:
            category = "Possible"
            interpretation = "Some ion channel modulator features"
            channel_type = "Ligand-gated channel"
        else:
            category = "Unlikely"
            interpretation = "Does not match typical ion channel modulator profile"
            channel_type = "Unknown"
        
        # Return ion channel modulator prediction results
        return {
            # Probability as percentage
            'Ion Channel Modulator Probability': f"{probability}%",
            # Likelihood category
            'Category': category,
            # Detailed interpretation
            'Interpretation': interpretation,
            # Suggested channel type
            'Likely Target': channel_type
        }
    
    # Predict enzyme inhibitor probability
    # Enzymes are proteins that catalyze chemical reactions
    # Many drugs work by blocking specific enzymes
    def predict_enzyme_inhibitor(self, mol) -> Dict:
        # Validate molecule input
        if mol is None:
            return {'error': 'Invalid molecule'}
        
        # Get molecular properties for enzyme inhibitor prediction
        
        # Molecular weight: Wide range acceptable (200-600 Da)
        mw = Descriptors.MolWt(mol)
        
        # LogP: Moderate range (0-5)
        logp = Crippen.MolLogP(mol)
        
        # Hydrogen bond donors: Important for enzyme active site binding
        hbd = Descriptors.NumHDonors(mol)
        
        # Hydrogen bond acceptors: Form interactions with enzyme residues
        hba = Descriptors.NumHAcceptors(mol)
        
        # Calculate enzyme inhibitor score
        score = 0
        
        # Award points for molecular weight in acceptable range
        if 200 <= mw <= 600:
            score += 25
        
        # Award points for LogP in acceptable range
        if 0 <= logp <= 5:
            score += 25
        
        # Award points for sufficient H-bond donors
        if hbd >= 2:
            score += 25
        
        # Award points for sufficient H-bond acceptors
        if hba >= 3:
            score += 25
        
        # Cap probability at 100%
        probability = min(100, score)
        
        # Return enzyme inhibitor prediction results
        return {
            # Probability as percentage
            'Enzyme Inhibitor Probability': f"{probability}%",
            # Category based on probability
            'Category': 'Likely' if probability >= 60 else 'Possible' if probability >= 30 else 'Unlikely',
            # General interpretation
            'Interpretation': 'Compatible with enzyme inhibition mechanism'
        }
    
    # Generate comprehensive target prediction
    # Runs all four target class predictions and identifies most likely
    # Called by Target Prediction page in the app
    def comprehensive_target_prediction(self, mol) -> Dict:
        # Run all individual target predictions
        kinase = self.predict_kinase_inhibitor(mol)
        gpcr = self.predict_gpcr_ligand(mol)
        ion_channel = self.predict_ion_channel_modulator(mol)
        enzyme = self.predict_enzyme_inhibitor(mol)
        
        # Extract probability scores for comparison
        # Remove '%' suffix and convert to integer
        scores = {
            'Kinase': int(kinase['Kinase Inhibitor Probability'].rstrip('%')),
            'GPCR': int(gpcr['GPCR Ligand Probability'].rstrip('%')),
            'Ion Channel': int(ion_channel['Ion Channel Modulator Probability'].rstrip('%')),
            'Enzyme': int(enzyme['Enzyme Inhibitor Probability'].rstrip('%'))
        }
        
        # Find the target class with highest probability
        primary_target = max(scores, key=scores.get)
        
        # Return comprehensive target prediction results
        return {
            # Individual target class predictions
            'Kinase Inhibitor': kinase,
            'GPCR Ligand': gpcr,
            'Ion Channel Modulator': ion_channel,
            'Enzyme Inhibitor': enzyme,
            # Most likely target class
            'Primary Target Class': primary_target,
            # Confidence level (probability of primary target)
            'Confidence': f"{scores[primary_target]}%"
        }
