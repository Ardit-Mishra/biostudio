"""
Unit tests for drug-likeness calculations.

Tests Lipinski Rule of 5, Veber rules, QED, and SA score.
"""

import pytest
from rdkit import Chem

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.drug_likeness import DrugLikenessCalculator


class TestDrugLikenessCalculator:
    """Test suite for DrugLikenessCalculator."""
    
    def setup_method(self):
        """Initialize calculator before each test."""
        self.calculator = DrugLikenessCalculator()
    
    def test_lipinski_aspirin(self):
        """Test Lipinski Rule of 5 on aspirin (should pass)."""
        mol = Chem.MolFromSmiles("CC(=O)Oc1ccccc1C(=O)O")
        result = self.calculator.calculate_lipinski(mol)
        
        assert 'violations' in result
        assert result['violations'] == 0  # Aspirin passes all rules
        assert result['passes_rule_of_5'] is True
    
    def test_lipinski_violations(self):
        """Test Lipinski violations on large molecule."""
        # Large molecule with multiple violations
        large_mol = Chem.MolFromSmiles("C" * 50)  # Long alkane chain
        result = self.calculator.calculate_lipinski(large_mol)
        
        assert result['violations'] > 0
        assert result['passes_rule_of_5'] is False
    
    def test_veber_rules_aspirin(self):
        """Test Veber rules on aspirin."""
        mol = Chem.MolFromSmiles("CC(=O)Oc1ccccc1C(=O)O")
        result = self.calculator.calculate_veber(mol)
        
        assert 'rotatable_bonds' in result
        assert 'tpsa' in result
        assert result['passes_veber'] is True
    
    def test_qed_range(self):
        """Test QED score is in valid range [0, 1]."""
        mol = Chem.MolFromSmiles("CCO")  # Ethanol
        qed = self.calculator.calculate_qed(mol)
        
        assert 0 <= qed <= 1
    
    def test_qed_drug_vs_non_drug(self):
        """Test QED distinguishes drugs from non-drugs."""
        aspirin = Chem.MolFromSmiles("CC(=O)Oc1ccccc1C(=O)O")
        long_chain = Chem.MolFromSmiles("C" * 30)
        
        qed_aspirin = self.calculator.calculate_qed(aspirin)
        qed_chain = self.calculator.calculate_qed(long_chain)
        
        # Aspirin should have higher QED than simple alkane chain
        assert qed_aspirin > qed_chain
    
    def test_sa_score_range(self):
        """Test SA score is in expected range [1, 10]."""
        mol = Chem.MolFromSmiles("CCO")
        sa = self.calculator.calculate_sa_score(mol)
        
        assert 1 <= sa <= 10
    
    def test_sa_score_simple_vs_complex(self):
        """Test SA score distinguishes simple from complex molecules."""
        simple = Chem.MolFromSmiles("CCO")  # Ethanol
        complex_mol = Chem.MolFromSmiles(
            "CN1CCN(CC1)Cc2ccc(cc2)C(=O)Nc3ccc(c(c3)Nc4nccc(n4)c5cccnc5)C(F)(F)F"
        )  # Imatinib
        
        sa_simple = self.calculator.calculate_sa_score(simple)
        sa_complex = self.calculator.calculate_sa_score(complex_mol)
        
        # Simple molecule should have lower SA score (easier to synthesize)
        assert sa_simple < sa_complex
    
    @pytest.mark.parametrize("smiles,expected_pass", [
        ("CCO", True),  # Ethanol - passes
        ("CC(=O)Oc1ccccc1C(=O)O", True),  # Aspirin - passes
        ("C" * 50, False),  # Long chain - fails
    ])
    def test_lipinski_multiple_molecules(self, smiles, expected_pass):
        """Test Lipinski on multiple molecules."""
        mol = Chem.MolFromSmiles(smiles)
        result = self.calculator.calculate_lipinski(mol)
        
        assert result['passes_rule_of_5'] == expected_pass
    
    def test_comprehensive_assessment(self):
        """Test comprehensive drug-likeness assessment."""
        mol = Chem.MolFromSmiles("CC(=O)Oc1ccccc1C(=O)O")  # Aspirin
        result = self.calculator.assess_drug_likeness(mol)
        
        # Check all components are present
        assert 'lipinski' in result
        assert 'veber' in result
        assert 'qed' in result
        assert 'sa_score' in result
        
        # Check overall assessment
        assert 'overall_score' in result
        assert 0 <= result['overall_score'] <= 100


class TestEdgeCases:
    """Test edge cases for drug-likeness calculations."""
    
    def setup_method(self):
        self.calculator = DrugLikenessCalculator()
    
    def test_invalid_molecule(self):
        """Test handling of None molecule."""
        result = self.calculator.calculate_lipinski(None)
        
        # Should handle gracefully
        assert result is not None
        assert 'error' in result or 'violations' in result
    
    def test_very_small_molecule(self):
        """Test very small molecule (methane)."""
        mol = Chem.MolFromSmiles("C")
        
        lipinski = self.calculator.calculate_lipinski(mol)
        qed = self.calculator.calculate_qed(mol)
        
        assert lipinski['passes_rule_of_5'] is True
        assert 0 <= qed <= 1
    
    def test_aromatic_systems(self):
        """Test molecules with aromatic systems."""
        benzene = Chem.MolFromSmiles("c1ccccc1")
        naphthalene = Chem.MolFromSmiles("c1ccc2ccccc2c1")
        
        qed_benzene = self.calculator.calculate_qed(benzene)
        qed_naphthalene = self.calculator.calculate_qed(naphthalene)
        
        # Both should have valid QED scores
        assert 0 <= qed_benzene <= 1
        assert 0 <= qed_naphthalene <= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
