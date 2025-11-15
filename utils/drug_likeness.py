from rdkit import Chem
from rdkit.Chem import Descriptors, Crippen, QED
from typing import Dict, Optional
import numpy as np


class DrugLikenessCalculator:
    
    @staticmethod
    def lipinski_rule_of_5(mol) -> Dict:
        if mol is None:
            return {'error': 'Invalid molecule'}
        
        mw = Descriptors.MolWt(mol)
        logp = Crippen.MolLogP(mol)
        hbd = Descriptors.NumHDonors(mol)
        hba = Descriptors.NumHAcceptors(mol)
        
        violations = []
        if mw > 500:
            violations.append("MW > 500")
        if logp > 5:
            violations.append("LogP > 5")
        if hbd > 5:
            violations.append("HBD > 5")
        if hba > 10:
            violations.append("HBA > 10")
        
        return {
            'Molecular Weight': round(mw, 2),
            'LogP': round(logp, 2),
            'H-Bond Donors': hbd,
            'H-Bond Acceptors': hba,
            'Violations': len(violations),
            'Details': violations if violations else ['All criteria met'],
            'Passes': len(violations) <= 1
        }
    
    @staticmethod
    def veber_descriptors(mol) -> Dict:
        if mol is None:
            return {'error': 'Invalid molecule'}
        
        rotatable_bonds = Descriptors.NumRotatableBonds(mol)
        tpsa = Descriptors.TPSA(mol)
        
        violations = []
        if rotatable_bonds > 10:
            violations.append("Rotatable bonds > 10")
        if tpsa > 140:
            violations.append("TPSA > 140 Ų")
        
        return {
            'Rotatable Bonds': rotatable_bonds,
            'TPSA': round(tpsa, 2),
            'Details': violations if violations else ['All criteria met'],
            'Passes': len(violations) == 0
        }
    
    @staticmethod
    def qed_score(mol) -> Dict:
        if mol is None:
            return {'error': 'Invalid molecule'}
        
        try:
            score = QED.qed(mol)
            
            if score >= 0.7:
                category = "Excellent"
            elif score >= 0.5:
                category = "Good"
            elif score >= 0.3:
                category = "Moderate"
            else:
                category = "Poor"
            
            return {
                'QED Score': round(score, 3),
                'Category': category,
                'Description': f"Drug-likeness: {category}"
            }
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def synthetic_accessibility(mol) -> Dict:
        if mol is None:
            return {'error': 'Invalid molecule'}
        
        try:
            from rdkit.Chem import rdMolDescriptors
            fp = rdMolDescriptors.GetMorganFingerprint(mol, 2)
            complexity = len(fp.GetNonzeroElements())
            sa_score = max(1, min(10, complexity / 50))
            
            if sa_score <= 3:
                category = "Easy to synthesize"
            elif sa_score <= 6:
                category = "Moderate difficulty"
            else:
                category = "Difficult to synthesize"
            
            return {
                'SA Score': round(sa_score, 2),
                'Category': category,
                'Description': f"Score: {round(sa_score, 2)}/10 (lower is easier)"
            }
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def comprehensive_analysis(mol) -> Dict:
        if mol is None:
            return {'error': 'Invalid molecule'}
        
        lipinski = DrugLikenessCalculator.lipinski_rule_of_5(mol)
        veber = DrugLikenessCalculator.veber_descriptors(mol)
        qed = DrugLikenessCalculator.qed_score(mol)
        sa = DrugLikenessCalculator.synthetic_accessibility(mol)
        
        overall_score = 0
        max_score = 4
        
        if lipinski.get('Passes', False):
            overall_score += 1
        if veber.get('Passes', False):
            overall_score += 1
        if qed.get('QED Score', 0) >= 0.5:
            overall_score += 1
        if sa.get('SA Score', 10) <= 6:
            overall_score += 1
        
        recommendation = "Excellent drug candidate" if overall_score >= 3 else \
                        "Good drug candidate" if overall_score == 2 else \
                        "Needs optimization"
        
        return {
            'Lipinski': lipinski,
            'Veber': veber,
            'QED': qed,
            'Synthetic Accessibility': sa,
            'Overall Score': f"{overall_score}/{max_score}",
            'Recommendation': recommendation
        }
