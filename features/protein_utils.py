"""
Protein and Biologic Analysis Utilities

This module provides tools for analyzing protein sequences, peptides, and biologics.
Includes FASTA validation, amino acid composition analysis, and physicochemical property calculations.

Author: Ardit Mishra
"""

import re
from typing import Dict, Tuple, Optional, List
import numpy as np


class ProteinAnalyzer:
    """
    Comprehensive protein sequence analyzer for biologic drug developability assessment.
    
    Calculates amino acid composition, hydrophobicity, instability, aliphatic index,
    and other properties relevant to therapeutic protein development.
    """
    
    AMINO_ACIDS = set('ACDEFGHIKLMNPQRSTVWY')
    
    HYDROPHOBICITY_SCALE = {
        'A': 1.8, 'R': -4.5, 'N': -3.5, 'D': -3.5, 'C': 2.5,
        'Q': -3.5, 'E': -3.5, 'G': -0.4, 'H': -3.2, 'I': 4.5,
        'L': 3.8, 'K': -3.9, 'M': 1.9, 'F': 2.8, 'P': -1.6,
        'S': -0.8, 'T': -0.7, 'W': -0.9, 'Y': -1.3, 'V': 4.2
    }
    
    INSTABILITY_VALUES = {
        'WW': 1.0, 'WC': 24.68, 'WF': 1.0, 'WY': 1.0, 'WH': 24.68,
        'WQ': 1.0, 'WN': 13.34, 'WK': 1.0, 'WD': 1.0, 'WE': 1.0,
        'CC': 1.0, 'CF': 1.0, 'CY': 1.0, 'CH': 33.60, 'CQ': -6.54,
        'CN': 1.0, 'CK': 1.0, 'CD': 20.26, 'CE': 1.0, 'FF': 1.0,
        'FY': 1.0, 'FH': 1.0, 'FQ': 1.0, 'FN': 1.0, 'FK': 1.0,
        'FD': 13.34, 'FE': 1.0, 'YY': 1.0, 'YH': 1.0, 'YQ': 1.0,
        'YN': 1.0, 'YK': 1.0, 'YD': 1.0, 'YE': 1.0, 'HH': 1.0,
        'HQ': 1.0, 'HN': 24.68, 'HK': 1.0, 'HD': 1.0, 'HE': -6.54,
        'QQ': 20.26, 'QN': 1.0, 'QK': 1.0, 'QD': 1.0, 'QE': 20.26,
        'NN': 1.0, 'NK': 24.68, 'ND': 1.0, 'NE': 1.0, 'KK': -7.49,
        'KD': 1.0, 'KE': 1.0, 'DD': 1.0, 'DE': 1.0, 'EE': 33.60
    }
    
    MOLECULAR_WEIGHT_AA = {
        'A': 89.09, 'R': 174.20, 'N': 132.12, 'D': 133.10, 'C': 121.15,
        'Q': 146.15, 'E': 147.13, 'G': 75.07, 'H': 155.16, 'I': 131.17,
        'L': 131.17, 'K': 146.19, 'M': 149.21, 'F': 165.19, 'P': 115.13,
        'S': 105.09, 'T': 119.12, 'W': 204.23, 'Y': 181.19, 'V': 117.15
    }
    
    def __init__(self):
        """Initialize protein analyzer."""
        pass
    
    def validate_fasta(self, sequence: str) -> Tuple[bool, str, str]:
        """
        Validate a protein sequence (FASTA format or plain sequence).
        
        Args:
            sequence: Protein sequence string (may include FASTA header)
        
        Returns:
            Tuple of (is_valid, cleaned_sequence, error_message)
        """
        if not sequence or len(sequence.strip()) == 0:
            return False, "", "Empty sequence"
        
        lines = sequence.strip().split('\n')
        
        if lines[0].startswith('>'):
            seq = ''.join(lines[1:]).replace(' ', '').replace('\n', '').upper()
        else:
            seq = sequence.replace(' ', '').replace('\n', '').upper()
        
        if len(seq) == 0:
            return False, "", "No sequence data found"
        
        invalid_chars = set(seq) - self.AMINO_ACIDS
        if invalid_chars:
            return False, seq, f"Invalid amino acids: {', '.join(invalid_chars)}"
        
        if len(seq) < 5:
            return False, seq, "Sequence too short (minimum 5 amino acids)"
        
        return True, seq, ""
    
    def calculate_amino_acid_composition(self, sequence: str) -> Dict[str, float]:
        """
        Calculate amino acid composition percentages.
        
        Args:
            sequence: Cleaned protein sequence
        
        Returns:
            Dictionary with AA percentages and category summaries
        """
        length = len(sequence)
        composition = {aa: (sequence.count(aa) / length) * 100 for aa in self.AMINO_ACIDS}
        
        hydrophobic = sum(sequence.count(aa) for aa in 'AILMFVPGW') / length * 100
        polar = sum(sequence.count(aa) for aa in 'STQNCY') / length * 100
        charged = sum(sequence.count(aa) for aa in 'DEKR') / length * 100
        positive = sum(sequence.count(aa) for aa in 'KR') / length * 100
        negative = sum(sequence.count(aa) for aa in 'DE') / length * 100
        
        return {
            'composition': composition,
            'hydrophobic_percent': round(hydrophobic, 2),
            'polar_percent': round(polar, 2),
            'charged_percent': round(charged, 2),
            'positive_percent': round(positive, 2),
            'negative_percent': round(negative, 2)
        }
    
    def calculate_hydrophobicity_index(self, sequence: str) -> float:
        """
        Calculate GRAVY (Grand Average of Hydropathy) index.
        Uses Kyte-Doolittle scale.
        
        Args:
            sequence: Cleaned protein sequence
        
        Returns:
            GRAVY score (more positive = more hydrophobic)
        """
        if len(sequence) == 0:
            return 0.0
        
        total = sum(self.HYDROPHOBICITY_SCALE.get(aa, 0) for aa in sequence)
        return round(total / len(sequence), 3)
    
    def calculate_instability_index(self, sequence: str) -> float:
        """
        Calculate instability index based on dipeptide instability values.
        
        Values > 40 indicate unstable protein.
        Values < 40 indicate stable protein.
        
        Args:
            sequence: Cleaned protein sequence
        
        Returns:
            Instability index
        """
        if len(sequence) < 2:
            return 0.0
        
        dipeptide_sum = 0.0
        for i in range(len(sequence) - 1):
            dipeptide = sequence[i:i+2]
            if dipeptide in self.INSTABILITY_VALUES:
                dipeptide_sum += self.INSTABILITY_VALUES[dipeptide]
            elif dipeptide[::-1] in self.INSTABILITY_VALUES:
                dipeptide_sum += self.INSTABILITY_VALUES[dipeptide[::-1]]
        
        instability = (10.0 / len(sequence)) * dipeptide_sum
        return round(instability, 2)
    
    def calculate_aliphatic_index(self, sequence: str) -> float:
        """
        Calculate aliphatic index - relative volume of aliphatic side chains.
        Higher values indicate greater thermostability.
        
        Args:
            sequence: Cleaned protein sequence
        
        Returns:
            Aliphatic index
        """
        if len(sequence) == 0:
            return 0.0
        
        ala = sequence.count('A')
        val = sequence.count('V')
        ile = sequence.count('I')
        leu = sequence.count('L')
        
        aliphatic = (ala / len(sequence)) * 100 + \
                    2.9 * (val / len(sequence)) * 100 + \
                    3.9 * ((ile + leu) / len(sequence)) * 100
        
        return round(aliphatic, 2)
    
    def calculate_molecular_weight(self, sequence: str) -> float:
        """
        Calculate molecular weight of protein.
        
        Args:
            sequence: Cleaned protein sequence
        
        Returns:
            Molecular weight in Daltons
        """
        if len(sequence) == 0:
            return 0.0
        
        weight = sum(self.MOLECULAR_WEIGHT_AA.get(aa, 0) for aa in sequence)
        weight -= (len(sequence) - 1) * 18.015
        
        return round(weight, 2)
    
    def predict_aggregation_risk(self, sequence: str) -> Dict[str, any]:
        """
        Predict aggregation propensity based on sequence properties.
        
        High hydrophobicity + low net charge = high aggregation risk
        
        Args:
            sequence: Cleaned protein sequence
        
        Returns:
            Dictionary with aggregation risk assessment
        """
        composition = self.calculate_amino_acid_composition(sequence)
        hydrophobicity = self.calculate_hydrophobicity_index(sequence)
        
        net_charge = abs(composition['positive_percent'] - composition['negative_percent'])
        
        risk_score = 0
        if hydrophobicity > 0.5:
            risk_score += 30
        elif hydrophobicity > 0:
            risk_score += 15
        
        if net_charge < 5:
            risk_score += 30
        elif net_charge < 10:
            risk_score += 15
        
        if composition['hydrophobic_percent'] > 50:
            risk_score += 25
        elif composition['hydrophobic_percent'] > 40:
            risk_score += 10
        
        aromatic = sum(sequence.count(aa) for aa in 'FWY') / len(sequence) * 100
        if aromatic > 10:
            risk_score += 15
        
        if risk_score >= 60:
            category = "High Risk"
            recommendation = "High aggregation propensity. Consider formulation optimization or sequence engineering."
        elif risk_score >= 30:
            category = "Moderate Risk"
            recommendation = "Moderate aggregation risk. Monitor during development and formulation."
        else:
            category = "Low Risk"
            recommendation = "Low aggregation propensity. Favorable for biologic development."
        
        return {
            'aggregation_score': risk_score,
            'category': category,
            'recommendation': recommendation,
            'hydrophobicity': hydrophobicity,
            'net_charge': round(net_charge, 2)
        }
    
    def predict_solubility(self, sequence: str) -> Dict[str, any]:
        """
        Predict solubility based on charge and hydrophobicity.
        
        Args:
            sequence: Cleaned protein sequence
        
        Returns:
            Dictionary with solubility assessment
        """
        composition = self.calculate_amino_acid_composition(sequence)
        hydrophobicity = self.calculate_hydrophobicity_index(sequence)
        
        charged_percent = composition['charged_percent']
        
        solubility_score = 50
        
        if hydrophobicity < -0.5:
            solubility_score += 25
        elif hydrophobicity < 0:
            solubility_score += 10
        elif hydrophobicity > 0.5:
            solubility_score -= 25
        elif hydrophobicity > 0:
            solubility_score -= 10
        
        if charged_percent > 20:
            solubility_score += 20
        elif charged_percent > 15:
            solubility_score += 10
        elif charged_percent < 10:
            solubility_score -= 15
        
        solubility_score = max(0, min(100, solubility_score))
        
        if solubility_score >= 70:
            category = "High Solubility"
            recommendation = "Favorable solubility profile for biologic development."
        elif solubility_score >= 40:
            category = "Moderate Solubility"
            recommendation = "Acceptable solubility. May require formulation optimization."
        else:
            category = "Low Solubility"
            recommendation = "Poor solubility predicted. Consider sequence modification or advanced formulation."
        
        return {
            'solubility_score': solubility_score,
            'category': category,
            'recommendation': recommendation
        }
    
    def comprehensive_biologic_profile(self, sequence: str) -> Dict[str, any]:
        """
        Generate complete biologic developability assessment.
        
        Args:
            sequence: Protein sequence (FASTA or plain)
        
        Returns:
            Comprehensive profile dictionary
        """
        is_valid, clean_seq, error = self.validate_fasta(sequence)
        
        if not is_valid:
            return {'error': error, 'sequence': sequence}
        
        composition = self.calculate_amino_acid_composition(clean_seq)
        hydrophobicity = self.calculate_hydrophobicity_index(clean_seq)
        instability = self.calculate_instability_index(clean_seq)
        aliphatic = self.calculate_aliphatic_index(clean_seq)
        mw = self.calculate_molecular_weight(clean_seq)
        aggregation = self.predict_aggregation_risk(clean_seq)
        solubility = self.predict_solubility(clean_seq)
        
        stability_category = "Stable" if instability < 40 else "Unstable"
        
        return {
            'sequence': clean_seq,
            'length': len(clean_seq),
            'molecular_weight': mw,
            'amino_acid_composition': composition,
            'hydrophobicity_index': hydrophobicity,
            'instability_index': instability,
            'stability_category': stability_category,
            'aliphatic_index': aliphatic,
            'aggregation_risk': aggregation,
            'solubility': solubility
        }
    
    def detect_sequence_type(self, sequence: str) -> str:
        """
        Detect if sequence is small peptide, medium peptide, or protein.
        
        Args:
            sequence: Cleaned sequence
        
        Returns:
            'peptide_small' (<20 AA), 'peptide_medium' (20-60 AA), 'protein' (>60 AA)
        """
        length = len(sequence)
        
        if length < 20:
            return "peptide_small"
        elif length <= 60:
            return "peptide_medium"
        else:
            return "protein"
