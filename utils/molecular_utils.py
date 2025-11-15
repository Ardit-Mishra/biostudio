import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors, Crippen, Lipinski, QED, Fragments
from rdkit.Chem import rdMolDescriptors, rdmolops
from typing import Optional, Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')


class MolecularProcessor:
    
    @staticmethod
    def validate_smiles(smiles: str) -> Tuple[bool, Optional[str]]:
        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                return False, "Invalid SMILES string"
            return True, Chem.MolToSmiles(mol)
        except:
            return False, "Error parsing SMILES"
    
    @staticmethod
    def smiles_to_mol(smiles: str):
        try:
            return Chem.MolFromSmiles(smiles)
        except:
            return None
    
    @staticmethod
    def calculate_basic_properties(mol) -> Dict:
        if mol is None:
            return {}
        
        try:
            return {
                'Molecular Weight': round(Descriptors.MolWt(mol), 2),
                'LogP': round(Crippen.MolLogP(mol), 2),
                'TPSA': round(Descriptors.TPSA(mol), 2),
                'H-Bond Donors': Descriptors.NumHDonors(mol),
                'H-Bond Acceptors': Descriptors.NumHAcceptors(mol),
                'Rotatable Bonds': Descriptors.NumRotatableBonds(mol),
                'Aromatic Rings': Descriptors.NumAromaticRings(mol),
                'Molecular Formula': rdMolDescriptors.CalcMolFormula(mol),
                'Fraction Csp3': round(Descriptors.FractionCsp3(mol), 2),
                'Molar Refractivity': round(Crippen.MolMR(mol), 2)
            }
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def calculate_lipinski_descriptors(mol) -> Dict:
        if mol is None:
            return {}
        
        mw = Descriptors.MolWt(mol)
        logp = Crippen.MolLogP(mol)
        hbd = Descriptors.NumHDonors(mol)
        hba = Descriptors.NumHAcceptors(mol)
        
        violations = 0
        if mw > 500: violations += 1
        if logp > 5: violations += 1
        if hbd > 5: violations += 1
        if hba > 10: violations += 1
        
        return {
            'MW': round(mw, 2),
            'LogP': round(logp, 2),
            'HBD': hbd,
            'HBA': hba,
            'Violations': violations,
            'Passes': violations <= 1
        }
    
    @staticmethod
    def calculate_veber_descriptors(mol) -> Dict:
        if mol is None:
            return {}
        
        rotatable_bonds = Descriptors.NumRotatableBonds(mol)
        tpsa = Descriptors.TPSA(mol)
        
        passes = (rotatable_bonds <= 10) and (tpsa <= 140)
        
        return {
            'Rotatable Bonds': rotatable_bonds,
            'TPSA': round(tpsa, 2),
            'Passes': passes
        }
    
    @staticmethod
    def calculate_qed(mol) -> float:
        if mol is None:
            return 0.0
        try:
            return round(QED.qed(mol), 3)
        except:
            return 0.0
    
    @staticmethod
    def calculate_sa_score(mol) -> float:
        if mol is None:
            return 0.0
        try:
            from rdkit.Chem import RDConfig
            import sys
            import os
            sys.path.append(os.path.join(RDConfig.RDContribDir, 'SA_Score'))
            import sascorer
            return round(sascorer.calculateScore(mol), 2)
        except:
            fp = rdMolDescriptors.GetMorganFingerprint(mol, 2)
            complexity = len(fp.GetNonzeroElements())
            return round(max(1, min(10, complexity / 50)), 2)
    
    @staticmethod
    def generate_morgan_fingerprint(mol, radius=2, n_bits=2048) -> np.ndarray:
        if mol is None:
            return np.zeros(n_bits)
        fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
        return np.array(fp)
    
    @staticmethod
    def calculate_molecular_descriptors(mol) -> np.ndarray:
        if mol is None:
            return np.zeros(200)
        
        descriptors = []
        
        descriptors.append(Descriptors.MolWt(mol))
        descriptors.append(Crippen.MolLogP(mol))
        descriptors.append(Descriptors.TPSA(mol))
        descriptors.append(Descriptors.NumHDonors(mol))
        descriptors.append(Descriptors.NumHAcceptors(mol))
        descriptors.append(Descriptors.NumRotatableBonds(mol))
        descriptors.append(Descriptors.NumAromaticRings(mol))
        descriptors.append(Descriptors.FractionCsp3(mol))
        descriptors.append(Crippen.MolMR(mol))
        descriptors.append(Descriptors.BertzCT(mol))
        descriptors.append(Descriptors.HallKierAlpha(mol))
        descriptors.append(Descriptors.Kappa1(mol))
        descriptors.append(Descriptors.Kappa2(mol))
        descriptors.append(Descriptors.Kappa3(mol))
        descriptors.append(Descriptors.Chi0v(mol))
        descriptors.append(Descriptors.Chi1v(mol))
        descriptors.append(Descriptors.Chi2v(mol))
        descriptors.append(Descriptors.Chi3v(mol))
        descriptors.append(Descriptors.Chi4v(mol))
        descriptors.append(Descriptors.LabuteASA(mol))
        descriptors.append(Descriptors.PEOE_VSA1(mol))
        descriptors.append(Descriptors.PEOE_VSA2(mol))
        descriptors.append(Descriptors.SMR_VSA1(mol))
        descriptors.append(Descriptors.SlogP_VSA1(mol))
        descriptors.append(Descriptors.EState_VSA1(mol))
        descriptors.append(Descriptors.VSA_EState1(mol))
        descriptors.append(Descriptors.NumSaturatedRings(mol))
        descriptors.append(Descriptors.NumAliphaticRings(mol))
        descriptors.append(rdMolDescriptors.CalcNumRings(mol))
        descriptors.append(rdMolDescriptors.CalcNumHeterocycles(mol))
        
        for i in range(170):
            descriptors.append(0)
        
        return np.array(descriptors[:200])
