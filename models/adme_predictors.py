import numpy as np
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from typing import Dict, Optional
from rdkit import Chem
from rdkit.Chem import Descriptors, Crippen, Lipinski


class ADMEPredictor:
    
    def __init__(self):
        self.models = {}
        self._initialize_models()
    
    def _initialize_models(self):
        pass
    
    def predict_logp(self, mol) -> Dict:
        if mol is None:
            return {'error': 'Invalid molecule'}
        
        logp = Crippen.MolLogP(mol)
        
        interpretation = ""
        if logp < 0:
            interpretation = "Highly hydrophilic - may have poor membrane permeability"
        elif logp <= 3:
            interpretation = "Good balance - optimal for oral bioavailability"
        elif logp <= 5:
            interpretation = "Lipophilic - good membrane permeability but potential issues"
        else:
            interpretation = "Highly lipophilic - may have poor solubility and ADME issues"
        
        return {
            'LogP': round(logp, 2),
            'Category': 'Optimal' if 0 <= logp <= 3 else 'Suboptimal',
            'Interpretation': interpretation
        }
    
    def predict_caco2_permeability(self, mol) -> Dict:
        if mol is None:
            return {'error': 'Invalid molecule'}
        
        logp = Crippen.MolLogP(mol)
        tpsa = Descriptors.TPSA(mol)
        mw = Descriptors.MolWt(mol)
        hbd = Descriptors.NumHDonors(mol)
        
        permeability_score = (logp * 10) - (tpsa * 0.1) - (hbd * 5) + 50
        permeability_score = max(0, min(100, permeability_score))
        
        if permeability_score >= 70:
            category = "High permeability"
            interpretation = "Excellent intestinal absorption expected (>70%)"
        elif permeability_score >= 40:
            category = "Moderate permeability"
            interpretation = "Good absorption expected (40-70%)"
        else:
            category = "Low permeability"
            interpretation = "Poor absorption expected (<40%)"
        
        return {
            'Caco-2 Score': round(permeability_score, 1),
            'Category': category,
            'Interpretation': interpretation,
            'TPSA': round(tpsa, 2),
            'HBD': hbd
        }
    
    def predict_bbb_penetration(self, mol) -> Dict:
        if mol is None:
            return {'error': 'Invalid molecule'}
        
        logp = Crippen.MolLogP(mol)
        tpsa = Descriptors.TPSA(mol)
        mw = Descriptors.MolWt(mol)
        hbd = Descriptors.NumHDonors(mol)
        hba = Descriptors.NumHAcceptors(mol)
        
        bbb_score = (logp - (tpsa / 20) - (hbd * 0.5))
        
        if bbb_score > 0.3 and tpsa < 90:
            category = "High BBB penetration"
            probability = "High (>80%)"
        elif bbb_score > -0.5 and tpsa < 120:
            category = "Moderate BBB penetration"
            probability = "Moderate (40-80%)"
        else:
            category = "Low BBB penetration"
            probability = "Low (<40%)"
        
        return {
            'BBB Score': round(bbb_score, 2),
            'Category': category,
            'Probability': probability,
            'TPSA': round(tpsa, 2),
            'Recommendation': 'Suitable for CNS drugs' if bbb_score > 0.3 else 'Peripheral action likely'
        }
    
    def predict_cyp450_metabolism(self, mol) -> Dict:
        if mol is None:
            return {'error': 'Invalid molecule'}
        
        logp = Crippen.MolLogP(mol)
        mw = Descriptors.MolWt(mol)
        aromatic_rings = Descriptors.NumAromaticRings(mol)
        
        cyp3a4_prob = min(100, max(0, (logp * 15) + (aromatic_rings * 20) + 30))
        cyp2d6_prob = min(100, max(0, (logp * 12) + (aromatic_rings * 15) + 25))
        cyp2c9_prob = min(100, max(0, (logp * 10) + (aromatic_rings * 18) + 20))
        
        return {
            'CYP3A4 Substrate Probability': f"{round(cyp3a4_prob, 1)}%",
            'CYP2D6 Substrate Probability': f"{round(cyp2d6_prob, 1)}%",
            'CYP2C9 Substrate Probability': f"{round(cyp2c9_prob, 1)}%",
            'Primary Metabolizer': 'CYP3A4' if cyp3a4_prob == max(cyp3a4_prob, cyp2d6_prob, cyp2c9_prob) else
                                   'CYP2D6' if cyp2d6_prob == max(cyp3a4_prob, cyp2d6_prob, cyp2c9_prob) else 'CYP2C9',
            'Interpretation': 'Monitor for drug-drug interactions with CYP inhibitors/inducers'
        }
    
    def predict_clearance(self, mol) -> Dict:
        if mol is None:
            return {'error': 'Invalid molecule'}
        
        logp = Crippen.MolLogP(mol)
        mw = Descriptors.MolWt(mol)
        tpsa = Descriptors.TPSA(mol)
        
        clearance_score = (logp * 5) + (mw * 0.01) - (tpsa * 0.1)
        clearance_score = max(10, min(100, clearance_score))
        
        if clearance_score >= 60:
            category = "High clearance"
            interpretation = "Rapid elimination - may require frequent dosing"
        elif clearance_score >= 30:
            category = "Moderate clearance"
            interpretation = "Balanced elimination profile"
        else:
            category = "Low clearance"
            interpretation = "Slow elimination - potential for accumulation"
        
        return {
            'Clearance Score': round(clearance_score, 1),
            'Category': category,
            'Interpretation': interpretation,
            'Half-life Estimate': 'Short (<4h)' if clearance_score >= 60 else 'Medium (4-12h)' if clearance_score >= 30 else 'Long (>12h)'
        }
    
    def comprehensive_adme_profile(self, mol) -> Dict:
        return {
            'LogP': self.predict_logp(mol),
            'Caco-2 Permeability': self.predict_caco2_permeability(mol),
            'BBB Penetration': self.predict_bbb_penetration(mol),
            'CYP450 Metabolism': self.predict_cyp450_metabolism(mol),
            'Clearance': self.predict_clearance(mol)
        }
