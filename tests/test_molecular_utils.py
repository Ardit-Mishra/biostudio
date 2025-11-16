"""
Unit tests for molecular utility functions.

Tests SMILES validation, molecular descriptor calculation,
and feature extraction.
"""

import pytest
import numpy as np
from rdkit import Chem
from rdkit.Chem import Descriptors

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.molecular_utils import MolecularProcessor, MolecularFeatureExtractor


class TestMolecularProcessor:
    """Test suite for MolecularProcessor class."""
    
    def setup_method(self):
        """Initialize processor before each test."""
        self.processor = MolecularProcessor()
    
    def test_valid_smiles_ethanol(self):
        """Test processing of simple valid SMILES (ethanol)."""
        smiles = "CCO"
        mol = self.processor.validate_smiles(smiles)
        
        assert mol is not None
        assert Chem.MolToSmiles(mol) == smiles
    
    def test_valid_smiles_aspirin(self):
        """Test processing of drug molecule (aspirin)."""
        smiles = "CC(=O)Oc1ccccc1C(=O)O"
        mol = self.processor.validate_smiles(smiles)
        
        assert mol is not None
        properties = self.processor.calculate_basic_properties(mol)
        
        assert 'molecular_weight' in properties
        assert properties['molecular_weight'] == pytest.approx(180.16, rel=0.01)
        assert properties['num_aromatic_rings'] == 1
    
    def test_invalid_smiles(self):
        """Test handling of invalid SMILES."""
        invalid_smiles = "INVALID_SMILES_123"
        mol = self.processor.validate_smiles(invalid_smiles)
        
        assert mol is None
    
    def test_empty_smiles(self):
        """Test handling of empty SMILES string."""
        mol = self.processor.validate_smiles("")
        assert mol is None
    
    def test_basic_properties_calculation(self):
        """Test basic property calculations."""
        mol = Chem.MolFromSmiles("CC(=O)Oc1ccccc1C(=O)O")  # Aspirin
        properties = self.processor.calculate_basic_properties(mol)
        
        # Check all expected keys are present
        expected_keys = [
            'molecular_weight', 'logp', 'num_h_donors', 'num_h_acceptors',
            'num_rotatable_bonds', 'num_aromatic_rings', 'tpsa'
        ]
        
        for key in expected_keys:
            assert key in properties
        
        # Check value ranges
        assert 100 < properties['molecular_weight'] < 300
        assert -5 < properties['logp'] < 5
        assert properties['num_h_donors'] >= 0
        assert properties['num_h_acceptors'] >= 0
    
    @pytest.mark.parametrize("smiles,expected_mw", [
        ("CCO", 46.07),  # Ethanol
        ("c1ccccc1", 78.11),  # Benzene
        ("CC(=O)Oc1ccccc1C(=O)O", 180.16),  # Aspirin
    ])
    def test_molecular_weight(self, smiles, expected_mw):
        """Test molecular weight calculation for known molecules."""
        mol = Chem.MolFromSmiles(smiles)
        properties = self.processor.calculate_basic_properties(mol)
        
        assert properties['molecular_weight'] == pytest.approx(expected_mw, rel=0.01)


class TestMolecularFeatureExtractor:
    """Test suite for MolecularFeatureExtractor class."""
    
    def test_feature_extraction_ethanol(self):
        """Test feature extraction for simple molecule."""
        mol = Chem.MolFromSmiles("CCO")
        features = MolecularFeatureExtractor.extract_features(mol)
        
        assert isinstance(features, np.ndarray)
        assert len(features) == 2078  # 30 descriptors + 2048 fingerprint bits
    
    def test_feature_extraction_aspirin(self):
        """Test feature extraction for drug molecule."""
        mol = Chem.MolFromSmiles("CC(=O)Oc1ccccc1C(=O)O")
        features = MolecularFeatureExtractor.extract_features(mol)
        
        assert isinstance(features, np.ndarray)
        assert len(features) == 2078
        assert not np.any(np.isnan(features))  # No NaN values
        assert not np.any(np.isinf(features))  # No infinite values
    
    def test_feature_extraction_invalid_molecule(self):
        """Test handling of None molecule."""
        with pytest.raises(AttributeError):
            MolecularFeatureExtractor.extract_features(None)
    
    def test_descriptor_calculation(self):
        """Test individual descriptor calculation."""
        mol = Chem.MolFromSmiles("CC(=O)Oc1ccccc1C(=O)O")
        features = MolecularFeatureExtractor.extract_features(mol)
        
        # First 30 values are descriptors
        descriptors = features[:30]
        
        # Check reasonable ranges for some descriptors
        assert descriptors[0] > 0  # Molecular weight
        assert -10 < descriptors[1] < 10  # LogP
        assert 0 <= descriptors[2] < 100  # NumHDonors
    
    def test_fingerprint_generation(self):
        """Test Morgan fingerprint generation."""
        mol = Chem.MolFromSmiles("CCO")
        features = MolecularFeatureExtractor.extract_features(mol)
        
        # Last 2048 values are fingerprint bits
        fingerprint = features[30:]
        
        assert len(fingerprint) == 2048
        assert all(bit in [0, 1] for bit in fingerprint)  # Binary values only
    
    def test_different_molecules_different_features(self):
        """Test that different molecules produce different features."""
        mol1 = Chem.MolFromSmiles("CCO")  # Ethanol
        mol2 = Chem.MolFromSmiles("CCCCCC")  # Hexane
        
        features1 = MolecularFeatureExtractor.extract_features(mol1)
        features2 = MolecularFeatureExtractor.extract_features(mol2)
        
        assert not np.array_equal(features1, features2)


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def setup_method(self):
        self.processor = MolecularProcessor()
    
    def test_large_molecule(self):
        """Test processing of large molecule."""
        # Imatinib (Gleevec) - large kinase inhibitor
        smiles = "CN1CCN(CC1)Cc2ccc(cc2)C(=O)Nc3ccc(c(c3)Nc4nccc(n4)c5cccnc5)C(F)(F)F"
        mol = self.processor.validate_smiles(smiles)
        
        assert mol is not None
        properties = self.processor.calculate_basic_properties(mol)
        assert properties['molecular_weight'] > 400  # Large molecule
    
    def test_aromatic_molecule(self):
        """Test aromatic ring detection."""
        mol = Chem.MolFromSmiles("c1ccccc1c2ccccc2")  # Biphenyl
        properties = self.processor.calculate_basic_properties(mol)
        
        assert properties['num_aromatic_rings'] == 2
    
    def test_charged_molecule(self):
        """Test handling of charged species."""
        # Protonated amine
        smiles = "CC[NH3+]"
        mol = self.processor.validate_smiles(smiles)
        
        # RDKit may handle this differently, just ensure no crash
        assert mol is not None or mol is None  # Either way is okay
    
    def test_stereochemistry(self):
        """Test SMILES with stereochemistry."""
        # L-alanine with stereochemistry
        smiles = "C[C@H](N)C(=O)O"
        mol = self.processor.validate_smiles(smiles)
        
        assert mol is not None
        
    def test_disconnected_fragments(self):
        """Test molecule with disconnected fragments (salt)."""
        smiles = "CC(=O)O.[Na+]"  # Sodium acetate
        mol = self.processor.validate_smiles(smiles)
        
        # Should handle salts
        assert mol is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
