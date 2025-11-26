# =============================================================================
# TOXICITY PREDICTION MODULE
# =============================================================================
# This module predicts potential safety concerns for drug candidates.
# It uses molecular properties to estimate risk of various toxicity types:
# - Hepatotoxicity: Liver damage potential
# - Cardiotoxicity (hERG): Heart rhythm issues
# - Mutagenicity (Ames): DNA damage potential
# - Carcinogenicity: Cancer-causing potential
#
# NOTE: These are heuristic predictions for educational purposes.
# Real drug development requires laboratory testing and clinical trials.
# =============================================================================

# Import numpy for numerical calculations
import numpy as np
# Import type hints for better code documentation
from typing import Dict
# Import RDKit core chemistry module
from rdkit import Chem
# Import RDKit descriptor calculators
# Descriptors: General molecular properties
# Crippen: LogP calculations
# Fragments: Counts specific chemical groups (functional groups)
# Lipinski: Drug-likeness related properties
from rdkit.Chem import Descriptors, Crippen, Fragments, Lipinski


# Main class for toxicity risk predictions
# Uses rule-based scoring derived from known toxic structure patterns
class ToxicityPredictor:
    
    # Constructor initializes empty models dictionary
    # In production, this would load trained ML models
    def __init__(self):
        # Placeholder for future ML model storage
        self.models = {}
    
    # Predict hepatotoxicity (liver toxicity) risk
    # Liver processes most drugs, so damage here is common and serious
    def predict_hepatotoxicity(self, mol) -> Dict:
        # Validate molecule input
        if mol is None:
            return {'error': 'Invalid molecule'}
        
        # Calculate molecular weight
        # Larger molecules are harder for liver to process
        mw = Descriptors.MolWt(mol)
        
        # Calculate LogP (lipophilicity)
        # Highly lipophilic drugs accumulate in liver
        logp = Crippen.MolLogP(mol)
        
        # Count aromatic rings
        # Many aromatic rings can form reactive metabolites
        aromatic_rings = Descriptors.NumAromaticRings(mol)
        
        # Count reactive functional groups known to cause liver damage
        # Halogens (F, Cl, Br, I) can form toxic metabolites
        # Nitro groups (-NO2) are often toxic
        reactive_groups = Fragments.fr_halogen(mol) + Fragments.fr_nitro(mol)
        
        # Calculate risk score (0-100 scale)
        risk_score = 0
        
        # Add 25 points if highly lipophilic (LogP > 3)
        # Lipophilic compounds concentrate in liver
        if logp > 3:
            risk_score += 25
        
        # Add 20 points if large molecule (MW > 500)
        # Large molecules stress liver metabolism
        if mw > 500:
            risk_score += 20
        
        # Add 20 points if many aromatic rings (>3)
        # Aromatic compounds can form epoxide metabolites
        if aromatic_rings > 3:
            risk_score += 20
        
        # Add 35 points for reactive groups
        # These are strong predictors of liver toxicity
        if reactive_groups > 0:
            risk_score += 35
        
        # Cap score at 100%
        risk_score = min(100, risk_score)
        
        # Categorize risk level and provide recommendations
        if risk_score >= 60:
            # High risk: Extensive testing needed before human use
            category = "High Risk"
            recommendation = "Requires extensive hepatotoxicity testing"
        elif risk_score >= 30:
            # Moderate risk: Standard monitoring should suffice
            category = "Moderate Risk"
            recommendation = "Standard liver function monitoring recommended"
        else:
            # Low risk: Minimal concern
            category = "Low Risk"
            recommendation = "Minimal hepatotoxicity concerns"
        
        # Return hepatotoxicity prediction results
        return {
            # Risk score as percentage
            'Hepatotoxicity Risk': f"{risk_score}%",
            # Risk category label
            'Category': category,
            # Action recommendation
            'Recommendation': recommendation,
            # Detailed risk factors for transparency
            'Risk Factors': f"LogP: {round(logp, 2)}, MW: {round(mw, 1)}, Aromatic Rings: {aromatic_rings}"
        }
    
    # Predict cardiotoxicity risk via hERG channel inhibition
    # hERG channel controls heart rhythm; blocking it causes arrhythmias
    # Many drugs have been withdrawn from market due to hERG issues
    def predict_cardiotoxicity_herg(self, mol) -> Dict:
        # Validate molecule input
        if mol is None:
            return {'error': 'Invalid molecule'}
        
        # Calculate LogP - moderately lipophilic compounds bind hERG
        logp = Crippen.MolLogP(mol)
        
        # Calculate molecular weight
        mw = Descriptors.MolWt(mol)
        
        # Count nitrogen-containing groups (basic nitrogens)
        # Basic amines are common hERG blockers
        basic_nitrogens = Lipinski.NumHAcceptors(mol)
        
        # Count aromatic rings - flat structures fit hERG channel
        aromatic_rings = Descriptors.NumAromaticRings(mol)
        
        # Calculate hERG inhibition risk score
        herg_risk = 0
        
        # Moderate LogP (2-5) correlates with hERG binding
        # This "sweet spot" allows membrane penetration to reach the channel
        if logp > 2 and logp < 5:
            herg_risk += 30
        
        # Medium-sized molecules (300-500 Da) fit hERG channel
        if 300 < mw < 500:
            herg_risk += 25
        
        # Multiple basic nitrogens increase hERG affinity
        if basic_nitrogens >= 2:
            herg_risk += 25
        
        # Aromatic rings create hydrophobic interactions with channel
        if aromatic_rings >= 2:
            herg_risk += 20
        
        # Cap score at 100%
        herg_risk = min(100, herg_risk)
        
        # Categorize and recommend based on risk level
        if herg_risk >= 60:
            # High risk: QT prolongation is life-threatening
            category = "High Risk"
            recommendation = "hERG inhibition testing required - QT prolongation concern"
        elif herg_risk >= 30:
            # Moderate risk: Should screen before clinical trials
            category = "Moderate Risk"
            recommendation = "hERG screening recommended"
        else:
            # Low risk: Unlikely to cause cardiac issues
            category = "Low Risk"
            recommendation = "Low probability of hERG inhibition"
        
        # Return cardiotoxicity prediction results
        return {
            # Risk score as percentage
            'hERG Inhibition Risk': f"{herg_risk}%",
            # Risk category
            'Category': category,
            # Recommended action
            'Recommendation': recommendation,
            # Estimated IC50 (concentration causing 50% inhibition)
            # Lower IC50 = more potent inhibitor = more dangerous
            'IC50 Estimate': '>10 μM' if herg_risk < 30 else '1-10 μM' if herg_risk < 60 else '<1 μM (concerning)'
        }
    
    # Predict mutagenicity using Ames test indicators
    # Ames test detects if a chemical causes DNA mutations
    # Mutagens can cause cancer and birth defects
    def predict_mutagenicity_ames(self, mol) -> Dict:
        # Validate molecule input
        if mol is None:
            return {'error': 'Invalid molecule'}
        
        # Count aromatic amines (Ar-NH2)
        # Known to cause DNA damage after metabolic activation
        aromatic_amines = Fragments.fr_Ar_N(mol)
        
        # Count nitro groups (-NO2)
        # Can be reduced to reactive nitroso compounds
        nitro_groups = Fragments.fr_nitro(mol)
        
        # Count halogens (F, Cl, Br, I)
        # Some halogenated compounds are mutagenic
        halogens = Fragments.fr_halogen(mol)
        
        # Count epoxide groups
        # Highly reactive with DNA
        epoxides = Fragments.fr_epoxide(mol)
        
        # Calculate structural alerts score
        # More weight given to known strong mutagens
        # Epoxides are weighted x2 due to direct DNA reactivity
        structural_alerts = aromatic_amines + nitro_groups + (halogens if halogens > 2 else 0) + epoxides * 2
        
        # Categorize based on number of structural alerts
        if structural_alerts >= 3:
            # Multiple alerts = high concern
            risk = "High"
            probability = ">70%"
            recommendation = "Ames test required - structural alerts present"
        elif structural_alerts >= 1:
            # Some alerts present = moderate concern
            risk = "Moderate"
            probability = "30-70%"
            recommendation = "Ames testing recommended"
        else:
            # No alerts = low concern
            risk = "Low"
            probability = "<30%"
            recommendation = "Low mutagenicity concern"
        
        # Return mutagenicity prediction results
        return {
            # Overall risk level
            'Mutagenicity Risk': risk,
            # Probability of positive Ames test
            'Ames Positive Probability': probability,
            # Count of structural alerts found
            'Structural Alerts': structural_alerts,
            # Breakdown of specific alerts
            'Alert Details': f"Aromatic amines: {aromatic_amines}, Nitro: {nitro_groups}, Halogens: {halogens}",
            # Recommended next steps
            'Recommendation': recommendation
        }
    
    # Predict carcinogenicity (cancer-causing potential)
    # Long-term safety concern requiring extensive testing
    def predict_carcinogenicity(self, mol) -> Dict:
        # Validate molecule input
        if mol is None:
            return {'error': 'Invalid molecule'}
        
        # Count aromatic rings
        # Polycyclic aromatic hydrocarbons (PAHs) are carcinogenic
        aromatic_rings = Descriptors.NumAromaticRings(mol)
        
        # Count reactive functional groups
        # Combination of halogens, nitro groups, and aromatic amines
        reactive_groups = Fragments.fr_halogen(mol) + Fragments.fr_nitro(mol) + Fragments.fr_Ar_N(mol)
        
        # Calculate molecular weight
        mw = Descriptors.MolWt(mol)
        
        # Calculate carcinogenicity risk score
        risk_score = 0
        
        # Polycyclic aromatic compounds (≥4 rings) are concerning
        # These can intercalate into DNA
        if aromatic_rings >= 4:
            risk_score += 30
        
        # Multiple reactive groups increase cancer risk
        if reactive_groups >= 2:
            risk_score += 35
        
        # Large molecules may accumulate in tissues
        if mw > 400:
            risk_score += 20
        
        # Cap at 100%
        risk_score = min(100, risk_score)
        
        # Categorize and provide recommendations
        if risk_score >= 60:
            # High risk: Full 2-year carcinogenicity studies needed
            category = "High Risk"
            recommendation = "Comprehensive carcinogenicity studies required"
        elif risk_score >= 30:
            # Moderate risk: Standard screening needed
            category = "Moderate Risk"
            recommendation = "Standard carcinogenicity screening recommended"
        else:
            # Low risk: Minimal concern
            category = "Low Risk"
            recommendation = "Low carcinogenicity concern"
        
        # Return carcinogenicity prediction results
        return {
            # Risk score as percentage
            'Carcinogenicity Risk': f"{risk_score}%",
            # Risk category
            'Category': category,
            # Recommended action
            'Recommendation': recommendation
        }
    
    # Generate comprehensive toxicity profile
    # Combines all four toxicity predictions into single report
    # Called by Toxicity Radar page in the app
    def comprehensive_toxicity_profile(self, mol) -> Dict:
        # Run all four toxicity predictions and return as dictionary
        return {
            # Liver toxicity assessment
            'Hepatotoxicity': self.predict_hepatotoxicity(mol),
            # Heart toxicity (hERG) assessment
            'Cardiotoxicity (hERG)': self.predict_cardiotoxicity_herg(mol),
            # DNA damage (Ames test) assessment
            'Mutagenicity (Ames)': self.predict_mutagenicity_ames(mol),
            # Cancer risk assessment
            'Carcinogenicity': self.predict_carcinogenicity(mol)
        }
