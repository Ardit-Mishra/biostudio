# =============================================================================
# DRUG-LIKENESS CALCULATOR MODULE
# =============================================================================
# This module evaluates whether a molecule has properties typical of successful drugs.
# It implements industry-standard rules and scores used in pharmaceutical research:
# - Lipinski's Rule of 5: Predicts oral bioavailability
# - Veber Descriptors: Assesses molecular flexibility and polarity
# - QED Score: Quantitative measure of drug-likeness
# - Synthetic Accessibility: How easy the molecule is to synthesize
# =============================================================================

# Import RDKit library for molecular property calculations
from rdkit import Chem
# Import descriptor calculators from RDKit
# Descriptors: General molecular properties (MW, TPSA, bond counts, etc.)
# Crippen: LogP calculation using Wildman-Crippen method
# QED: Quantitative Estimate of Drug-likeness scoring
from rdkit.Chem import Descriptors, Crippen, QED
# Import type hints for better code documentation
from typing import Dict, Optional
# Import numpy for numerical operations
import numpy as np


# Main class for calculating drug-likeness properties
# Contains static methods so no instance needed (can call directly on class)
class DrugLikenessCalculator:
    
    # Lipinski's Rule of 5 evaluation
    # This rule predicts if a drug can be taken orally (by mouth)
    # Named "Rule of 5" because all cutoff values are multiples of 5
    @staticmethod
    def lipinski_rule_of_5(mol) -> Dict:
        # Check if molecule object is valid before proceeding
        if mol is None:
            # Return error dictionary if molecule is invalid
            return {'error': 'Invalid molecule'}
        
        # Calculate molecular weight in Daltons (atomic mass units)
        # Drugs typically need MW < 500 to be absorbed in the gut
        mw = Descriptors.MolWt(mol)
        
        # Calculate LogP (partition coefficient) using Wildman-Crippen method
        # LogP measures how "fatty" vs "water-loving" a molecule is
        # Range of -2 to 5 is typically good for oral drugs
        logp = Crippen.MolLogP(mol)
        
        # Count hydrogen bond donors (NH and OH groups)
        # Too many donors (>5) reduces membrane permeability
        hbd = Descriptors.NumHDonors(mol)
        
        # Count hydrogen bond acceptors (N and O atoms)
        # Too many acceptors (>10) reduces membrane permeability
        hba = Descriptors.NumHAcceptors(mol)
        
        # Track which rules are violated
        violations = []
        
        # Check Rule 1: Molecular weight should be ≤500 Daltons
        # Larger molecules have trouble crossing cell membranes
        if mw > 500:
            violations.append("MW > 500")
        
        # Check Rule 2: LogP should be ≤5
        # Too lipophilic (fatty) molecules have poor solubility
        if logp > 5:
            violations.append("LogP > 5")
        
        # Check Rule 3: H-bond donors should be ≤5
        # Too many donors means poor passive diffusion
        if hbd > 5:
            violations.append("HBD > 5")
        
        # Check Rule 4: H-bond acceptors should be ≤10
        # Too many acceptors means poor membrane crossing
        if hba > 10:
            violations.append("HBA > 10")
        
        # Return results as a dictionary
        return {
            # Rounded molecular weight for display
            'Molecular Weight': round(mw, 2),
            # Rounded LogP value
            'LogP': round(logp, 2),
            # Number of hydrogen bond donors
            'H-Bond Donors': hbd,
            # Number of hydrogen bond acceptors
            'H-Bond Acceptors': hba,
            # Count of violated rules (0-4)
            'Violations': len(violations),
            # List of which specific rules were violated
            'Details': violations if violations else ['All criteria met'],
            # Passes if 0 or 1 violation (most drugs have ≤1 violation)
            'Passes': len(violations) <= 1
        }
    
    # Veber descriptors for oral bioavailability prediction
    # Complements Lipinski by focusing on molecular flexibility and polarity
    @staticmethod
    def veber_descriptors(mol) -> Dict:
        # Validate molecule input
        if mol is None:
            return {'error': 'Invalid molecule'}
        
        # Count rotatable bonds (single bonds that can rotate freely)
        # More rotatable bonds = more flexible molecule
        # Flexible molecules have trouble binding to targets
        rotatable_bonds = Descriptors.NumRotatableBonds(mol)
        
        # Calculate topological polar surface area (TPSA)
        # TPSA is the surface area of polar atoms (N, O, their hydrogens)
        # High TPSA = poor membrane permeability
        tpsa = Descriptors.TPSA(mol)
        
        # Track violations of Veber rules
        violations = []
        
        # Check Rule 1: Rotatable bonds should be ≤10
        # Too flexible molecules lose binding affinity
        if rotatable_bonds > 10:
            violations.append("Rotatable bonds > 10")
        
        # Check Rule 2: TPSA should be ≤140 Å² (square angstroms)
        # High polarity prevents membrane crossing
        if tpsa > 140:
            violations.append("TPSA > 140 Ų")
        
        # Return Veber analysis results
        return {
            # Number of rotatable bonds
            'Rotatable Bonds': rotatable_bonds,
            # Topological polar surface area in Å²
            'TPSA': round(tpsa, 2),
            # Details of any violations
            'Details': violations if violations else ['All criteria met'],
            # Passes only if BOTH criteria are met (stricter than Lipinski)
            'Passes': len(violations) == 0
        }
    
    # QED (Quantitative Estimate of Drug-likeness) score
    # Provides a continuous 0-1 score instead of pass/fail
    # Based on properties of known successful drugs
    @staticmethod
    def qed_score(mol) -> Dict:
        # Validate molecule input
        if mol is None:
            return {'error': 'Invalid molecule'}
        
        # Try to calculate QED score (may fail for unusual molecules)
        try:
            # RDKit's QED function calculates the score
            # Considers 8 properties weighted by their importance
            score = QED.qed(mol)
            
            # Categorize the score into human-readable labels
            # These thresholds are based on the distribution of approved drugs
            if score >= 0.7:
                # Top-tier drug candidates
                category = "Excellent"
            elif score >= 0.5:
                # Good candidates worth pursuing
                category = "Good"
            elif score >= 0.3:
                # May need optimization but still viable
                category = "Moderate"
            else:
                # Likely needs significant redesign
                category = "Poor"
            
            # Return QED results
            return {
                # Numeric score rounded to 3 decimal places
                'QED Score': round(score, 3),
                # Human-readable category
                'Category': category,
                # Description for UI display
                'Description': f"Drug-likeness: {category}"
            }
        # Handle any calculation errors gracefully
        except Exception as e:
            return {'error': str(e)}
    
    # Synthetic Accessibility (SA) score calculation
    # Estimates how difficult the molecule is to synthesize in a lab
    # Lower score = easier to make
    @staticmethod
    def synthetic_accessibility(mol) -> Dict:
        # Validate molecule input
        if mol is None:
            return {'error': 'Invalid molecule'}
        
        try:
            # Import Morgan fingerprint calculator for complexity estimation
            from rdkit.Chem import rdMolDescriptors
            
            # Generate Morgan fingerprint with radius 2 (ECFP4 equivalent)
            # This captures the local chemical environment around each atom
            fp = rdMolDescriptors.GetMorganFingerprint(mol, 2)
            
            # Count unique molecular fragments
            # More unique fragments = more complex molecule
            complexity = len(fp.GetNonzeroElements())
            
            # Map complexity to 1-10 scale
            # Divide by 50 as a normalization factor based on typical drug complexity
            # Clamp to range 1-10 using max/min
            sa_score = max(1, min(10, complexity / 50))
            
            # Categorize synthesis difficulty
            if sa_score <= 3:
                # Simple molecules with common building blocks
                category = "Easy to synthesize"
            elif sa_score <= 6:
                # Standard medicinal chemistry complexity
                category = "Moderate difficulty"
            else:
                # Complex natural product-like structures
                category = "Difficult to synthesize"
            
            # Return SA score results
            return {
                # Numeric score (1=easy, 10=very difficult)
                'SA Score': round(sa_score, 2),
                # Human-readable category
                'Category': category,
                # Description explaining the scale
                'Description': f"Score: {round(sa_score, 2)}/10 (lower is easier)"
            }
        # Handle any calculation errors
        except Exception as e:
            return {'error': str(e)}
    
    # Comprehensive drug-likeness analysis
    # Combines all four assessments into a single report
    # Used by the Drug-Likeness Deck page in the app
    @staticmethod
    def comprehensive_analysis(mol) -> Dict:
        # Validate molecule before running all analyses
        if mol is None:
            return {'error': 'Invalid molecule'}
        
        # Run all four individual assessments
        # Each returns a dictionary with detailed results
        lipinski = DrugLikenessCalculator.lipinski_rule_of_5(mol)
        veber = DrugLikenessCalculator.veber_descriptors(mol)
        qed = DrugLikenessCalculator.qed_score(mol)
        sa = DrugLikenessCalculator.synthetic_accessibility(mol)
        
        # Calculate overall score (0-4 points possible)
        overall_score = 0
        max_score = 4
        
        # Award 1 point for passing Lipinski (≤1 violation)
        if lipinski.get('Passes', False):
            overall_score += 1
        
        # Award 1 point for passing Veber (both criteria met)
        if veber.get('Passes', False):
            overall_score += 1
        
        # Award 1 point for good QED score (≥0.5)
        if qed.get('QED Score', 0) >= 0.5:
            overall_score += 1
        
        # Award 1 point for reasonable SA score (≤6)
        if sa.get('SA Score', 10) <= 6:
            overall_score += 1
        
        # Generate recommendation based on overall score
        # Using conditional expression for concise assignment
        recommendation = "Excellent drug candidate" if overall_score >= 3 else \
                        "Good drug candidate" if overall_score == 2 else \
                        "Needs optimization"
        
        # Return comprehensive results dictionary
        return {
            # Individual assessment results
            'Lipinski': lipinski,
            'Veber': veber,
            'QED': qed,
            'Synthetic Accessibility': sa,
            # Overall score as fraction string
            'Overall Score': f"{overall_score}/{max_score}",
            # Final recommendation for the molecule
            'Recommendation': recommendation
        }
