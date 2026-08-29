"""
Unit tests for drug-likeness calculations.

Tests Lipinski Rule of 5, Veber rules, QED, and SA score.

WHY THIS FILE WAS REWRITTEN
---------------------------
Every test here previously failed with AttributeError. The suite called
``DrugLikenessCalculator.calculate_lipinski`` / ``calculate_veber`` /
``calculate_qed`` / ``calculate_sa_score`` / ``assess_drug_likeness`` — five
methods that have never existed on that class. Those names belong (roughly) to
``MolecularProcessor``; the author appears to have conflated the two classes.
The result keys were wrong in the same way: the tests read ``result['violations']``
where the implementation returns ``result['Violations']``.

So the suite was not "failing" in the usual sense — it was exercising an API
that does not exist, which means these modules had NO real coverage while
appearing to be tested. That is worse than having no tests, because a green-ish
looking suite invites trust it never earned.

The scientific assertions were sound and are all preserved verbatim: aspirin
passes Lipinski with zero violations, a C50 alkane does not, QED lies in [0, 1],
aspirin scores higher than a bare alkane chain, SA lies in [1, 10], and ethanol
is easier to synthesise than imatinib. Only the method names and dict keys
changed — the tests now target the real API.

``TestPublicApiSurface`` at the bottom exists so this class of drift fails
immediately and legibly next time, rather than as thirteen confusing
AttributeErrors.
"""

import pytest
from rdkit import Chem

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.drug_likeness import DrugLikenessCalculator

ASPIRIN = "CC(=O)Oc1ccccc1C(=O)O"
IMATINIB = "CN1CCN(CC1)Cc2ccc(cc2)C(=O)Nc3ccc(c(c3)Nc4nccc(n4)c5cccnc5)C(F)(F)F"


class TestDrugLikenessCalculator:
    """Test suite for DrugLikenessCalculator."""

    def setup_method(self):
        """Initialize calculator before each test."""
        self.calculator = DrugLikenessCalculator()

    def test_lipinski_aspirin(self):
        """Test Lipinski Rule of 5 on aspirin (should pass)."""
        mol = Chem.MolFromSmiles(ASPIRIN)
        result = self.calculator.lipinski_rule_of_5(mol)

        assert 'Violations' in result
        assert result['Violations'] == 0  # Aspirin passes all rules
        assert result['Passes'] is True

    def test_lipinski_violations(self):
        """Test Lipinski violations on large molecule."""
        # Long alkane chain: far too lipophilic and too heavy.
        large_mol = Chem.MolFromSmiles("C" * 50)
        result = self.calculator.lipinski_rule_of_5(large_mol)

        assert result['Violations'] > 0
        assert result['Passes'] is False

    def test_veber_rules_aspirin(self):
        """Test Veber rules on aspirin."""
        mol = Chem.MolFromSmiles(ASPIRIN)
        result = self.calculator.veber_descriptors(mol)

        assert 'Rotatable Bonds' in result
        assert 'TPSA' in result
        assert result['Passes'] is True

    def test_qed_range(self):
        """Test QED score is in valid range [0, 1]."""
        mol = Chem.MolFromSmiles("CCO")  # Ethanol
        qed = self.calculator.qed_score(mol)['QED Score']

        assert 0 <= qed <= 1

    def test_qed_drug_vs_non_drug(self):
        """Test QED distinguishes drugs from non-drugs."""
        aspirin = Chem.MolFromSmiles(ASPIRIN)
        long_chain = Chem.MolFromSmiles("C" * 30)

        qed_aspirin = self.calculator.qed_score(aspirin)['QED Score']
        qed_chain = self.calculator.qed_score(long_chain)['QED Score']

        # Aspirin should have higher QED than simple alkane chain
        assert qed_aspirin > qed_chain

    def test_sa_score_range(self):
        """Test SA score is in expected range [1, 10]."""
        mol = Chem.MolFromSmiles("CCO")
        sa = self.calculator.synthetic_accessibility(mol)['SA Score']

        assert 1 <= sa <= 10

    def test_sa_score_simple_vs_complex(self):
        """Test SA score distinguishes simple from complex molecules."""
        simple = Chem.MolFromSmiles("CCO")  # Ethanol
        complex_mol = Chem.MolFromSmiles(IMATINIB)

        sa_simple = self.calculator.synthetic_accessibility(simple)['SA Score']
        sa_complex = self.calculator.synthetic_accessibility(complex_mol)['SA Score']

        # Simple molecule should have lower SA score (easier to synthesize)
        assert sa_simple < sa_complex

    @pytest.mark.parametrize("smiles,expected_pass", [
        ("CCO", True),          # Ethanol - passes
        (ASPIRIN, True),        # Aspirin - passes
        ("C" * 50, False),      # Long chain - fails
    ])
    def test_lipinski_multiple_molecules(self, smiles, expected_pass):
        """Test Lipinski on multiple molecules."""
        mol = Chem.MolFromSmiles(smiles)
        result = self.calculator.lipinski_rule_of_5(mol)

        assert result['Passes'] == expected_pass

    def test_comprehensive_assessment(self):
        """Test comprehensive drug-likeness assessment."""
        mol = Chem.MolFromSmiles(ASPIRIN)
        result = self.calculator.comprehensive_analysis(mol)

        # Check all components are present
        assert 'Lipinski' in result
        assert 'Veber' in result
        assert 'QED' in result
        assert 'Synthetic Accessibility' in result

        # Overall Score is a "criteria passed / criteria checked" fraction
        # string such as "4/4", NOT a 0-100 percentage. The original test
        # asserted 0 <= score <= 100, which is what this assertion looked like
        # before anyone checked what the function returns.
        assert 'Overall Score' in result
        passed, total = (int(x) for x in result['Overall Score'].split('/'))
        assert 0 <= passed <= total
        assert total == 4  # Lipinski, Veber, QED, synthetic accessibility
        assert result['Recommendation']  # non-empty verdict string

    def test_overall_score_reflects_a_failing_molecule(self):
        """A molecule that fails criteria must not score as a clean pass."""
        bad = Chem.MolFromSmiles("C" * 50)
        result = self.calculator.comprehensive_analysis(bad)
        passed, total = (int(x) for x in result['Overall Score'].split('/'))
        assert passed < total


class TestEdgeCases:
    """Test edge cases for drug-likeness calculations."""

    def setup_method(self):
        self.calculator = DrugLikenessCalculator()

    def test_invalid_molecule(self):
        """A None molecule reports an error rather than a plausible score."""
        result = self.calculator.lipinski_rule_of_5(None)

        assert result is not None
        # The distinction matters: an error dict cannot be mistaken for a
        # molecule that legitimately has zero violations.
        assert 'error' in result
        assert 'Violations' not in result

    @pytest.mark.parametrize("method", [
        "lipinski_rule_of_5", "veber_descriptors", "qed_score", "synthetic_accessibility",
    ])
    def test_every_calculation_reports_none_as_an_error(self, method):
        """No calculation may turn an absent molecule into a number."""
        result = getattr(self.calculator, method)(None)
        assert 'error' in result

    def test_very_small_molecule(self):
        """Test very small molecule (methane)."""
        mol = Chem.MolFromSmiles("C")

        lipinski = self.calculator.lipinski_rule_of_5(mol)
        qed = self.calculator.qed_score(mol)['QED Score']

        assert lipinski['Passes'] is True
        assert 0 <= qed <= 1

    def test_aromatic_systems(self):
        """Test molecules with aromatic systems."""
        benzene = Chem.MolFromSmiles("c1ccccc1")
        naphthalene = Chem.MolFromSmiles("c1ccc2ccccc2c1")

        qed_benzene = self.calculator.qed_score(benzene)['QED Score']
        qed_naphthalene = self.calculator.qed_score(naphthalene)['QED Score']

        # Both should have valid QED scores
        assert 0 <= qed_benzene <= 1
        assert 0 <= qed_naphthalene <= 1


class TestPublicApiSurface:
    """Pin the API these tests target.

    Thirteen tests in this file used to fail with AttributeError against method
    names that never existed. A single explicit contract check turns that into
    one legible failure naming the missing method, instead of a scattered pile
    of errors that read like the implementation is broken.
    """

    EXPECTED_METHODS = {
        "lipinski_rule_of_5",
        "veber_descriptors",
        "qed_score",
        "synthetic_accessibility",
        "comprehensive_analysis",
    }

    def test_calculator_exposes_the_methods_these_tests_call(self):
        missing = {m for m in self.EXPECTED_METHODS
                   if not callable(getattr(DrugLikenessCalculator, m, None))}
        assert not missing, (
            f"DrugLikenessCalculator is missing {sorted(missing)}. Either the "
            f"implementation was renamed and these tests were not updated, or "
            f"the tests are aimed at the wrong class — which is exactly how "
            f"this suite came to test an API that did not exist."
        )

    @pytest.mark.parametrize("method,expected_keys", [
        ("lipinski_rule_of_5", {"Violations", "Passes"}),
        ("veber_descriptors", {"Rotatable Bonds", "TPSA", "Passes"}),
        ("qed_score", {"QED Score"}),
        ("synthetic_accessibility", {"SA Score"}),
    ])
    def test_result_keys_are_the_ones_the_ui_reads(self, method, expected_keys):
        """app.py indexes these keys directly, so a rename breaks the app."""
        mol = Chem.MolFromSmiles(ASPIRIN)
        result = getattr(DrugLikenessCalculator, method)(mol)
        assert expected_keys <= set(result), (
            f"{method} is missing {sorted(expected_keys - set(result))}; "
            f"it returned {sorted(result)}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
