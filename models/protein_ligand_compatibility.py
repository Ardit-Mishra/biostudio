"""
Protein-Ligand Compatibility Scorer

Neural network-based prediction of protein-ligand binding compatibility.
Combines protein biophysical features with small molecule descriptors to
predict binding likelihood.

Architecture:
- Protein Features: 24 features (length, AA composition, charge, hydrophobicity, etc.)
- Ligand Features: 2078 features (30 descriptors + 2048 Morgan FP bits)
- Total Input: 2102 features
- Hidden Layers: 512 → 256 → 128 → 64 neurons
- Output: Binding probability (0-1, sigmoid activation)

Author: Ardit Mishra
References:
- Ragoza et al. (2017) - Protein-ligand scoring with CNN
- Jiménez et al. (2018) - KDEEP: Protein-ligand binding affinity prediction
- Stepniewska-Dziubinska et al. (2018) - Development of 3D interaction graph
"""

import numpy as np
from typing import Dict, Tuple, Optional
from rdkit import Chem
from rdkit.Chem import Descriptors
import sys
import os
import warnings
warnings.filterwarnings('ignore')

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.molecular_utils import MolecularFeatureExtractor


class ProteinLigandCompatibilityScorer:
    """
    Neural network-based protein-ligand compatibility prediction.
    
    Predicts binding likelihood by combining:
    1. Protein biophysical features (24 features)
    2. Ligand molecular descriptors + fingerprints (2078 features)
    
    Output: Binding probability score (0-100%)
    """
    
    def __init__(self):
        """Initialize protein-ligand compatibility scorer with synthetic weights."""
        self.protein_feature_size = 24
        self.ligand_feature_size = 2078  # 30 descriptors + 2048 Morgan FP
        self.input_size = self.protein_feature_size + self.ligand_feature_size  # 2102
        
        # Initialize synthetic neural network weights
        self._initialize_synthetic_weights()
    
    def _initialize_synthetic_weights(self):
        """
        Initialize synthetic neural network weights for demonstration.
        
        In production, replace with actual trained weights from validated
        protein-ligand binding datasets (PDBbind, BindingDB, ChEMBL).
        """
        np.random.seed(42)
        
        # Layer 1: 2102 → 512
        self.W1 = np.random.randn(self.input_size, 512) * 0.01
        self.b1 = np.zeros(512)
        
        # Layer 2: 512 → 256
        self.W2 = np.random.randn(512, 256) * 0.01
        self.b2 = np.zeros(256)
        
        # Layer 3: 256 → 128
        self.W3 = np.random.randn(256, 128) * 0.01
        self.b3 = np.zeros(128)
        
        # Layer 4: 128 → 64
        self.W4 = np.random.randn(128, 64) * 0.01
        self.b4 = np.zeros(64)
        
        # Output layer: 64 → 1
        self.W5 = np.random.randn(64, 1) * 0.01
        self.b5 = np.zeros(1)
    
    def _clean_protein_sequence(self, sequence: str) -> str:
        """
        Clean protein sequence by removing FASTA headers and formatting.
        
        Args:
            sequence: Raw protein sequence (may include FASTA header)
        
        Returns:
            Cleaned amino acid sequence
        """
        if not sequence:
            return ""
        
        # Remove FASTA header if present (must do this BEFORE cleaning)
        if sequence.strip().startswith('>'):
            lines = sequence.strip().split('\n')
            # Drop first line (header), keep rest
            sequence = ''.join(lines[1:])
        
        # Clean sequence
        sequence = sequence.upper().replace('\n', '').replace(' ', '').replace('>', '')
        
        return sequence
    
    def extract_protein_features(self, sequence: str) -> np.ndarray:
        """
        Extract biophysical features from protein sequence.
        
        Features (24 total):
        - Sequence length
        - Amino acid composition (20 amino acids)
        - Charge distribution (positive, negative, neutral ratios)
        - Hydrophobicity (GRAVY score)
        
        Args:
            sequence: Protein sequence (single-letter amino acid codes)
        
        Returns:
            Feature vector (24 dimensions)
        """
        if not sequence:
            return np.zeros(self.protein_feature_size)
        
        # Clean the sequence using helper method
        sequence = self._clean_protein_sequence(sequence)
        
        # Amino acid composition
        aa_codes = 'ACDEFGHIKLMNPQRSTVWY'
        aa_counts = {aa: sequence.count(aa) for aa in aa_codes}
        total = len(sequence)
        aa_fractions = np.array([aa_counts[aa] / total if total > 0 else 0 for aa in aa_codes])
        
        # Hydrophobicity (Kyte-Doolittle scale)
        kd_scale = {
            'A': 1.8, 'C': 2.5, 'D': -3.5, 'E': -3.5, 'F': 2.8,
            'G': -0.4, 'H': -3.2, 'I': 4.5, 'K': -3.9, 'L': 3.8,
            'M': 1.9, 'N': -3.5, 'P': -1.6, 'Q': -3.5, 'R': -4.5,
            'S': -0.8, 'T': -0.7, 'V': 4.2, 'W': -0.9, 'Y': -1.3
        }
        
        gravy = sum(kd_scale.get(aa, 0) for aa in sequence) / total if total > 0 else 0
        
        # Charge distribution
        positive = sum(1 for aa in sequence if aa in 'RK') / total if total > 0 else 0
        negative = sum(1 for aa in sequence if aa in 'DE') / total if total > 0 else 0
        neutral = 1 - positive - negative
        
        # Combine features
        features = np.concatenate([
            [total / 1000.0],  # Normalized length
            aa_fractions,       # 20 AA fractions
            [gravy],            # GRAVY score
            [positive],         # Positive charge ratio
            [negative]          # Negative charge ratio
        ])
        
        return features
    
    def extract_ligand_features(self, mol) -> np.ndarray:
        """
        Extract molecular features from small molecule ligand using shared extractor.
        
        Combines:
        - 30 RDKit descriptors
        - 2048 Morgan fingerprint bits (radius=2)
        
        Args:
            mol: RDKit molecule object
        
        Returns:
            Feature vector (2078 dimensions)
        """
        return MolecularFeatureExtractor.extract_features(mol)
    
    def _relu(self, x):
        """ReLU activation function."""
        return np.maximum(0, x)
    
    def _sigmoid(self, x):
        """Sigmoid activation function."""
        return 1 / (1 + np.exp(-np.clip(x, -500, 500)))
    
    def forward(self, features: np.ndarray) -> float:
        """
        Forward pass through neural network.
        
        Args:
            features: Combined protein + ligand feature vector (2102 dimensions)
        
        Returns:
            Binding probability (0-1)
        """
        # Layer 1
        z1 = np.dot(features, self.W1) + self.b1
        a1 = self._relu(z1)
        
        # Layer 2
        z2 = np.dot(a1, self.W2) + self.b2
        a2 = self._relu(z2)
        
        # Layer 3
        z3 = np.dot(a2, self.W3) + self.b3
        a3 = self._relu(z3)
        
        # Layer 4
        z4 = np.dot(a3, self.W4) + self.b4
        a4 = self._relu(z4)
        
        # Output layer (sigmoid for probability)
        z5 = np.dot(a4, self.W5) + self.b5
        probability = self._sigmoid(z5)[0]
        
        return probability
    
    def predict_binding_compatibility(self, protein_sequence: str, mol) -> Dict:
        """
        Predict protein-ligand binding compatibility.
        
        Args:
            protein_sequence: Protein amino acid sequence
            mol: RDKit molecule object (small molecule ligand)
        
        Returns:
            Dictionary with binding predictions and confidence metrics
        """
        if not protein_sequence or mol is None:
            return {
                'error': 'Invalid protein sequence or ligand molecule',
                'binding_probability': 0.0,
                'binding_score': 0,
                'compatibility': 'Unknown'
            }
        
        # Extract features
        protein_features = self.extract_protein_features(protein_sequence)
        ligand_features = self.extract_ligand_features(mol)
        
        # Concatenate protein + ligand features
        combined_features = np.concatenate([protein_features, ligand_features])
        
        # Predict binding probability
        probability = self.forward(combined_features)
        
        # Apply heuristic adjustments based on basic compatibility checks
        adjusted_prob = self._adjust_with_heuristics(protein_sequence, mol, probability)
        
        # Convert to score (0-100)
        score = int(adjusted_prob * 100)
        
        # Determine compatibility level
        if score >= 70:
            compatibility = 'High'
            recommendation = 'Strong predicted binding. Good candidate for further study.'
        elif score >= 40:
            compatibility = 'Moderate'
            recommendation = 'Moderate predicted binding. Consider for optimization.'
        else:
            compatibility = 'Low'
            recommendation = 'Weak predicted binding. May require significant optimization.'
        
        # Get cleaned protein sequence for accurate length reporting
        clean_protein = self._clean_protein_sequence(protein_sequence)
        
        return {
            'binding_probability': round(adjusted_prob, 3),
            'binding_score': score,
            'percentage': f"{score}%",
            'compatibility': compatibility,
            'confidence': 'Neural Network',
            'recommendation': recommendation,
            'protein_length': len(clean_protein),
            'ligand_mw': round(Descriptors.MolWt(mol), 2)
        }
    
    def _adjust_with_heuristics(self, protein_sequence: str, mol, base_prob: float) -> float:
        """
        Apply heuristic adjustments based on basic compatibility checks.
        
        Temporary solution - in production, these would come from proper training.
        """
        mw = Descriptors.MolWt(mol)
        logp = Descriptors.MolLogP(mol)
        hba = Descriptors.NumHAcceptors(mol)
        hbd = Descriptors.NumHDonors(mol)
        
        adjustment = 0.0
        
        # Lipinski compliance generally favorable
        if 200 <= mw <= 500 and logp <= 5 and hba <= 10 and hbd <= 5:
            adjustment += 0.10
        
        # Very large or very small molecules less likely to bind well
        if mw < 150 or mw > 700:
            adjustment -= 0.15
        
        # Extreme LogP reduces binding likelihood
        if logp < -2 or logp > 6:
            adjustment -= 0.10
        
        return min(0.95, max(0.05, base_prob + adjustment))
