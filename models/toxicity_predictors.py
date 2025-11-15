import numpy as np
from typing import Dict
from rdkit import Chem
from rdkit.Chem import Descriptors, Crippen, Fragments, Lipinski


class ToxicityPredictor:
    
    def __init__(self):
        self.models = {}
    
    def predict_hepatotoxicity(self, mol) -> Dict:
        if mol is None:
            return {'error': 'Invalid molecule'}
        
        mw = Descriptors.MolWt(mol)
        logp = Crippen.MolLogP(mol)
        aromatic_rings = Descriptors.NumAromaticRings(mol)
        reactive_groups = Fragments.fr_halogen(mol) + Fragments.fr_nitro(mol)
        
        risk_score = 0
        if logp > 3:
            risk_score += 25
        if mw > 500:
            risk_score += 20
        if aromatic_rings > 3:
            risk_score += 20
        if reactive_groups > 0:
            risk_score += 35
        
        risk_score = min(100, risk_score)
        
        if risk_score >= 60:
            category = "High Risk"
            recommendation = "Requires extensive hepatotoxicity testing"
        elif risk_score >= 30:
            category = "Moderate Risk"
            recommendation = "Standard liver function monitoring recommended"
        else:
            category = "Low Risk"
            recommendation = "Minimal hepatotoxicity concerns"
        
        return {
            'Hepatotoxicity Risk': f"{risk_score}%",
            'Category': category,
            'Recommendation': recommendation,
            'Risk Factors': f"LogP: {round(logp, 2)}, MW: {round(mw, 1)}, Aromatic Rings: {aromatic_rings}"
        }
    
    def predict_cardiotoxicity_herg(self, mol) -> Dict:
        if mol is None:
            return {'error': 'Invalid molecule'}
        
        logp = Crippen.MolLogP(mol)
        mw = Descriptors.MolWt(mol)
        basic_nitrogens = Lipinski.NumHAcceptors(mol)
        aromatic_rings = Descriptors.NumAromaticRings(mol)
        
        herg_risk = 0
        if logp > 2 and logp < 5:
            herg_risk += 30
        if 300 < mw < 500:
            herg_risk += 25
        if basic_nitrogens >= 2:
            herg_risk += 25
        if aromatic_rings >= 2:
            herg_risk += 20
        
        herg_risk = min(100, herg_risk)
        
        if herg_risk >= 60:
            category = "High Risk"
            recommendation = "hERG inhibition testing required - QT prolongation concern"
        elif herg_risk >= 30:
            category = "Moderate Risk"
            recommendation = "hERG screening recommended"
        else:
            category = "Low Risk"
            recommendation = "Low probability of hERG inhibition"
        
        return {
            'hERG Inhibition Risk': f"{herg_risk}%",
            'Category': category,
            'Recommendation': recommendation,
            'IC50 Estimate': '>10 μM' if herg_risk < 30 else '1-10 μM' if herg_risk < 60 else '<1 μM (concerning)'
        }
    
    def predict_mutagenicity_ames(self, mol) -> Dict:
        if mol is None:
            return {'error': 'Invalid molecule'}
        
        aromatic_amines = Fragments.fr_Ar_N(mol)
        nitro_groups = Fragments.fr_nitro(mol)
        halogens = Fragments.fr_halogen(mol)
        epoxides = Fragments.fr_epoxide(mol)
        
        structural_alerts = aromatic_amines + nitro_groups + (halogens if halogens > 2 else 0) + epoxides * 2
        
        if structural_alerts >= 3:
            risk = "High"
            probability = ">70%"
            recommendation = "Ames test required - structural alerts present"
        elif structural_alerts >= 1:
            risk = "Moderate"
            probability = "30-70%"
            recommendation = "Ames testing recommended"
        else:
            risk = "Low"
            probability = "<30%"
            recommendation = "Low mutagenicity concern"
        
        return {
            'Mutagenicity Risk': risk,
            'Ames Positive Probability': probability,
            'Structural Alerts': structural_alerts,
            'Alert Details': f"Aromatic amines: {aromatic_amines}, Nitro: {nitro_groups}, Halogens: {halogens}",
            'Recommendation': recommendation
        }
    
    def predict_carcinogenicity(self, mol) -> Dict:
        if mol is None:
            return {'error': 'Invalid molecule'}
        
        aromatic_rings = Descriptors.NumAromaticRings(mol)
        reactive_groups = Fragments.fr_halogen(mol) + Fragments.fr_nitro(mol) + Fragments.fr_Ar_N(mol)
        mw = Descriptors.MolWt(mol)
        
        risk_score = 0
        if aromatic_rings >= 4:
            risk_score += 30
        if reactive_groups >= 2:
            risk_score += 35
        if mw > 400:
            risk_score += 20
        
        risk_score = min(100, risk_score)
        
        if risk_score >= 60:
            category = "High Risk"
            recommendation = "Comprehensive carcinogenicity studies required"
        elif risk_score >= 30:
            category = "Moderate Risk"
            recommendation = "Standard carcinogenicity screening recommended"
        else:
            category = "Low Risk"
            recommendation = "Low carcinogenicity concern"
        
        return {
            'Carcinogenicity Risk': f"{risk_score}%",
            'Category': category,
            'Recommendation': recommendation
        }
    
    def comprehensive_toxicity_profile(self, mol) -> Dict:
        return {
            'Hepatotoxicity': self.predict_hepatotoxicity(mol),
            'Cardiotoxicity (hERG)': self.predict_cardiotoxicity_herg(mol),
            'Mutagenicity (Ames)': self.predict_mutagenicity_ames(mol),
            'Carcinogenicity': self.predict_carcinogenicity(mol)
        }
