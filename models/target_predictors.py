import numpy as np
from typing import Dict, List
from rdkit import Chem
from rdkit.Chem import Descriptors, Crippen, Fragments, AllChem


class TargetClassPredictor:
    
    def __init__(self):
        self.models = {}
    
    def predict_kinase_inhibitor(self, mol) -> Dict:
        if mol is None:
            return {'error': 'Invalid molecule'}
        
        aromatic_rings = Descriptors.NumAromaticRings(mol)
        hbd = Descriptors.NumHDonors(mol)
        hba = Descriptors.NumHAcceptors(mol)
        mw = Descriptors.MolWt(mol)
        logp = Crippen.MolLogP(mol)
        
        score = 0
        if 3 <= aromatic_rings <= 5:
            score += 25
        if 1 <= hbd <= 3:
            score += 20
        if 3 <= hba <= 6:
            score += 20
        if 300 <= mw <= 550:
            score += 20
        if 2 <= logp <= 5:
            score += 15
        
        probability = min(100, score)
        
        if probability >= 70:
            category = "Highly Likely"
            interpretation = "Strong structural similarity to known kinase inhibitors"
        elif probability >= 40:
            category = "Possible"
            interpretation = "Some kinase inhibitor characteristics present"
        else:
            category = "Unlikely"
            interpretation = "Does not match typical kinase inhibitor profile"
        
        return {
            'Kinase Inhibitor Probability': f"{probability}%",
            'Category': category,
            'Interpretation': interpretation,
            'Key Features': f"Aromatic rings: {aromatic_rings}, HBD: {hbd}, HBA: {hba}"
        }
    
    def predict_gpcr_ligand(self, mol) -> Dict:
        if mol is None:
            return {'error': 'Invalid molecule'}
        
        mw = Descriptors.MolWt(mol)
        logp = Crippen.MolLogP(mol)
        rotatable_bonds = Descriptors.NumRotatableBonds(mol)
        basic_nitrogens = Fragments.fr_NH2(mol) + Fragments.fr_NH1(mol) + Fragments.fr_Ar_NH(mol)
        aromatic_rings = Descriptors.NumAromaticRings(mol)
        
        score = 0
        if 200 <= mw <= 450:
            score += 25
        if 1 <= logp <= 4:
            score += 25
        if 2 <= rotatable_bonds <= 8:
            score += 20
        if basic_nitrogens >= 1:
            score += 20
        if 1 <= aromatic_rings <= 3:
            score += 10
        
        probability = min(100, score)
        
        if probability >= 70:
            category = "Highly Likely"
            interpretation = "Strong GPCR ligand characteristics"
        elif probability >= 40:
            category = "Possible"
            interpretation = "Some GPCR ligand features present"
        else:
            category = "Unlikely"
            interpretation = "Does not match typical GPCR ligand profile"
        
        return {
            'GPCR Ligand Probability': f"{probability}%",
            'Category': category,
            'Interpretation': interpretation,
            'Receptor Subtype Hint': 'Consider aminergic GPCR' if basic_nitrogens >= 1 else 'Consider peptidergic GPCR'
        }
    
    def predict_ion_channel_modulator(self, mol) -> Dict:
        if mol is None:
            return {'error': 'Invalid molecule'}
        
        mw = Descriptors.MolWt(mol)
        logp = Crippen.MolLogP(mol)
        aromatic_rings = Descriptors.NumAromaticRings(mol)
        rotatable_bonds = Descriptors.NumRotatableBonds(mol)
        
        score = 0
        if 250 <= mw <= 500:
            score += 25
        if 2 <= logp <= 5:
            score += 25
        if 2 <= aromatic_rings <= 4:
            score += 25
        if rotatable_bonds <= 6:
            score += 25
        
        probability = min(100, score)
        
        if probability >= 70:
            category = "Highly Likely"
            interpretation = "Strong ion channel modulator characteristics"
            channel_type = "Voltage-gated channel"
        elif probability >= 40:
            category = "Possible"
            interpretation = "Some ion channel modulator features"
            channel_type = "Ligand-gated channel"
        else:
            category = "Unlikely"
            interpretation = "Does not match typical ion channel modulator profile"
            channel_type = "Unknown"
        
        return {
            'Ion Channel Modulator Probability': f"{probability}%",
            'Category': category,
            'Interpretation': interpretation,
            'Likely Target': channel_type
        }
    
    def predict_enzyme_inhibitor(self, mol) -> Dict:
        if mol is None:
            return {'error': 'Invalid molecule'}
        
        mw = Descriptors.MolWt(mol)
        logp = Crippen.MolLogP(mol)
        hbd = Descriptors.NumHDonors(mol)
        hba = Descriptors.NumHAcceptors(mol)
        
        score = 0
        if 200 <= mw <= 600:
            score += 25
        if 0 <= logp <= 5:
            score += 25
        if hbd >= 2:
            score += 25
        if hba >= 3:
            score += 25
        
        probability = min(100, score)
        
        return {
            'Enzyme Inhibitor Probability': f"{probability}%",
            'Category': 'Likely' if probability >= 60 else 'Possible' if probability >= 30 else 'Unlikely',
            'Interpretation': 'Compatible with enzyme inhibition mechanism'
        }
    
    def comprehensive_target_prediction(self, mol) -> Dict:
        kinase = self.predict_kinase_inhibitor(mol)
        gpcr = self.predict_gpcr_ligand(mol)
        ion_channel = self.predict_ion_channel_modulator(mol)
        enzyme = self.predict_enzyme_inhibitor(mol)
        
        scores = {
            'Kinase': int(kinase['Kinase Inhibitor Probability'].rstrip('%')),
            'GPCR': int(gpcr['GPCR Ligand Probability'].rstrip('%')),
            'Ion Channel': int(ion_channel['Ion Channel Modulator Probability'].rstrip('%')),
            'Enzyme': int(enzyme['Enzyme Inhibitor Probability'].rstrip('%'))
        }
        
        primary_target = max(scores, key=scores.get)
        
        return {
            'Kinase Inhibitor': kinase,
            'GPCR Ligand': gpcr,
            'Ion Channel Modulator': ion_channel,
            'Enzyme Inhibitor': enzyme,
            'Primary Target Class': primary_target,
            'Confidence': f"{scores[primary_target]}%"
        }
