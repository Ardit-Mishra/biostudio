# =============================================================================
# MOLECULAR PROCESSING UTILITIES MODULE
# =============================================================================
# This module provides core cheminformatics functionality for drug discovery:
# - SMILES validation and canonicalization
# - Molecular property calculation (MW, LogP, TPSA, etc.)
# - Drug-likeness assessment (Lipinski, Veber, QED, SA)
# - Molecular fingerprint generation for similarity analysis
# - Comprehensive descriptor calculation for ML models
#
# All calculations use RDKit, the industry-standard open-source cheminformatics toolkit.
# For scientific references, see REFERENCES.md in the project root.
# =============================================================================

"""
Molecular Processing Utilities

This module provides core cheminformatics functionality for molecular property calculation,
SMILES validation, fingerprint generation, and drug-likeness assessment using RDKit.

The implementation is based on established computational chemistry methods:
- Wildman-Crippen LogP calculation [REFERENCES.md: 6]
- Lipinski Rule of 5 for oral bioavailability [REFERENCES.md: 1,2]
- Veber rules for molecular property filters [REFERENCES.md: 3]
- QED (Quantitative Estimate of Drug-likeness) scoring [REFERENCES.md: 4]
- Synthetic Accessibility estimation [REFERENCES.md: 5]
- Morgan (circular) fingerprints for similarity calculations [REFERENCES.md: 37]

All methods use RDKit (https://www.rdkit.org/) as the underlying cheminformatics toolkit.

Classes:
    MolecularProcessor: Static methods for molecular property calculations

References:
    See REFERENCES.md for complete citations of all scientific methods.
"""

# Import numpy for numerical array operations
# NumPy arrays are used for fingerprints and descriptor vectors
import numpy as np

# Import pandas for data manipulation
# Used for tabular data in batch processing
import pandas as pd

# Import RDKit core chemistry module
# Chem provides basic molecule handling: parsing, writing, manipulation
from rdkit import Chem

# Import various RDKit submodules for specific calculations
# AllChem: Advanced chemistry operations (fingerprints, 3D coordinates)
# Descriptors: Molecular property calculators (MW, TPSA, etc.)
# Crippen: LogP and molar refractivity calculations (Wildman-Crippen method)
# Lipinski: Drug-likeness related properties
# QED: Quantitative Estimate of Drug-likeness scoring
# Fragments: Count specific functional groups in molecules
from rdkit.Chem import AllChem, Descriptors, Crippen, Lipinski, QED, Fragments

# Import additional RDKit descriptor and manipulation modules
# rdMolDescriptors: Additional molecular descriptors (formula, fingerprints)
# rdmolops: Molecular operations (kekulization, aromaticity)
from rdkit.Chem import rdMolDescriptors, rdmolops

# Import type hints for better code documentation
# Optional: Value can be of specified type or None
# Dict: Dictionary type hint
# List: List type hint
# Tuple: Tuple type hint (multiple return values)
from typing import Optional, Dict, List, Tuple

# Import warnings module to suppress non-critical warnings
import warnings
# Ignore RDKit deprecation and stereochemistry warnings
# These are informational and don't affect calculation accuracy
warnings.filterwarnings('ignore')


# Main class for molecular processing and property calculation
# Uses static methods so no instance creation needed
class MolecularProcessor:
    """
    Core molecular processing and property calculation class.
    
    This class provides static methods for:
    - SMILES validation and canonicalization
    - Basic molecular property calculation
    - Drug-likeness assessment (Lipinski, Veber, QED, SA)
    - Molecular fingerprint generation
    - Comprehensive molecular descriptor calculation
    
    All methods are based on RDKit implementations of established cheminformatics algorithms.
    """
    
    # Validate and canonicalize a SMILES string
    # SMILES = Simplified Molecular Input Line Entry System
    # A text notation for representing chemical structures
    @staticmethod
    def validate_smiles(smiles: str) -> Tuple[bool, Optional[str]]:
        """
        Validate and canonicalize a SMILES string.
        
        Uses RDKit's SMILES parser to verify molecular structure validity and 
        returns the canonical SMILES representation. Canonical SMILES ensures
        unique representation of molecules (Weininger, 1988 [REFERENCES.md: 39]).
        
        Args:
            smiles (str): Input SMILES string to validate
            
        Returns:
            Tuple[bool, Optional[str]]: 
                - (True, canonical_smiles) if valid
                - (False, error_message) if invalid
                
        Example:
            >>> is_valid, canonical = MolecularProcessor.validate_smiles("CC(C)Cc1ccc(cc1)C(C)C(=O)O")
            >>> print(is_valid, canonical)
            True CC(C)Cc1ccc(C(C)C(=O)O)cc1
            
        References:
            - SMILES notation: Weininger (1988) [REFERENCES.md: 39]
            - RDKit canonicalization algorithm
        """
        # Wrap in try-except to catch any parsing errors
        try:
            # Parse SMILES string into RDKit molecule object
            # MolFromSmiles returns None if SMILES is invalid
            mol = Chem.MolFromSmiles(smiles)
            
            # Check if parsing was successful
            if mol is None:
                # Return False with error message if parsing failed
                return False, "Invalid SMILES string"
            
            # Convert molecule back to canonical SMILES
            # Canonical SMILES provides a unique string for each molecule
            # Different input SMILES for same molecule give same canonical output
            return True, Chem.MolToSmiles(mol)
        except:
            # Return False with error message if any exception occurred
            return False, "Error parsing SMILES"
    
    # Convert SMILES string to RDKit molecule object
    # This is the starting point for all property calculations
    @staticmethod
    def smiles_to_mol(smiles: str):
        """
        Convert SMILES string to RDKit molecule object.
        
        Creates an RDKit Mol object from SMILES notation, which enables all
        subsequent molecular property calculations and transformations.
        
        Args:
            smiles (str): Valid SMILES string
            
        Returns:
            rdkit.Chem.Mol: RDKit molecule object, or None if parsing fails
            
        Note:
            For critical applications, use validate_smiles() first to ensure
            SMILES validity before calling this method.
        """
        # Wrap in try-except for safety
        try:
            # Parse SMILES and return molecule object
            return Chem.MolFromSmiles(smiles)
        except:
            # Return None if parsing fails
            return None
    
    # Calculate basic physicochemical properties of a molecule
    # These are the fundamental properties used in drug discovery
    @staticmethod
    def calculate_basic_properties(mol) -> Dict:
        """
        Calculate fundamental physicochemical properties of a molecule.
        
        Computes core molecular descriptors used in drug discovery:
        - Molecular weight (MW): Size indicator
        - LogP: Lipophilicity (Wildman-Crippen method [REFERENCES.md: 6])
        - TPSA: Topological polar surface area (permeability indicator)
        - Hydrogen bond donors/acceptors: Solubility and binding indicators
        - Rotatable bonds: Molecular flexibility
        - Aromatic rings: Structural features
        - Fraction Csp3: Saturation level (escape from flatland metric)
        - Molar refractivity: Molecular volume and polarizability
        
        Args:
            mol (rdkit.Chem.Mol): RDKit molecule object
            
        Returns:
            Dict: Dictionary of molecular properties with the following keys:
                - 'Molecular Weight': float (Da)
                - 'LogP': float (partition coefficient)
                - 'TPSA': float (Ų, topological polar surface area)
                - 'H-Bond Donors': int (NH and OH groups)
                - 'H-Bond Acceptors': int (N and O atoms)
                - 'Rotatable Bonds': int (non-ring single bonds)
                - 'Aromatic Rings': int (count of aromatic ring systems)
                - 'Molecular Formula': str (elemental composition)
                - 'Fraction Csp3': float (0-1, ratio of sp³ carbons)
                - 'Molar Refractivity': float (molar refractivity)
                
        Returns:
            Empty dict if mol is None, or dict with 'error' key if calculation fails
            
        Example:
            >>> mol = MolecularProcessor.smiles_to_mol("CC(C)Cc1ccc(cc1)C(C)C(=O)O")
            >>> props = MolecularProcessor.calculate_basic_properties(mol)
            >>> print(f"MW: {props['Molecular Weight']}, LogP: {props['LogP']}")
            MW: 206.28, LogP: 3.50
            
        References:
            - LogP calculation: Wildman & Crippen (1999) [REFERENCES.md: 6]
            - TPSA: Ertl et al. (2000) - standard implementation in RDKit
            - Fraction Csp3: Lovering et al. (2009) - escape from flatland
        """
        # Return empty dictionary if molecule is None
        if mol is None:
            return {}
        
        # Wrap calculations in try-except for error handling
        try:
            # Return dictionary with all calculated properties
            return {
                # Molecular Weight in Daltons (atomic mass units)
                # Larger molecules (>500 Da) often have poor absorption
                'Molecular Weight': round(Descriptors.MolWt(mol), 2),
                
                # LogP: Partition coefficient (octanol/water)
                # Measures lipophilicity (how "fatty" the molecule is)
                # Uses Wildman-Crippen atom-type based method
                'LogP': round(Crippen.MolLogP(mol), 2),
                
                # TPSA: Topological Polar Surface Area in square Angstroms
                # Sum of surface areas of polar atoms (N, O, their H)
                # Correlates with intestinal absorption and BBB penetration
                'TPSA': round(Descriptors.TPSA(mol), 2),
                
                # H-Bond Donors: Count of NH and OH groups
                # Important for binding to biological targets
                'H-Bond Donors': Descriptors.NumHDonors(mol),
                
                # H-Bond Acceptors: Count of N and O atoms
                # Important for solubility and target binding
                'H-Bond Acceptors': Descriptors.NumHAcceptors(mol),
                
                # Rotatable Bonds: Single bonds that can rotate freely
                # More rotatable bonds = more flexible molecule
                # Too flexible molecules may have entropic penalty for binding
                'Rotatable Bonds': Descriptors.NumRotatableBonds(mol),
                
                # Aromatic Rings: Count of aromatic ring systems
                # Many drugs contain aromatic rings for π-π interactions
                'Aromatic Rings': Descriptors.NumAromaticRings(mol),
                
                # Molecular Formula: Elemental composition (e.g., C9H8O4)
                # Useful for identification and mass spectrometry
                'Molecular Formula': rdMolDescriptors.CalcMolFormula(mol),
                
                # Fraction Csp3: Ratio of sp³ carbons to total carbons
                # Higher values (more 3D character) often have better properties
                # "Escape from flatland" concept
                'Fraction Csp3': round(Lipinski.FractionCSP3(mol), 2),
                
                # Molar Refractivity: Related to molecular volume and polarizability
                # Used in QSAR models for binding affinity
                'Molar Refractivity': round(Crippen.MolMR(mol), 2)
            }
        # Handle any calculation errors
        except Exception as e:
            # Return error message in dictionary
            return {'error': str(e)}
    
    # Calculate Lipinski Rule of 5 descriptors
    # The most famous drug-likeness filter
    @staticmethod
    def calculate_lipinski_descriptors(mol) -> Dict:
        """
        Calculate Lipinski Rule of 5 descriptors for oral bioavailability prediction.
        
        The Rule of 5 (Lipinski et al., 2001 [REFERENCES.md: 1]) predicts oral 
        bioavailability based on four molecular properties. Compounds violating more
        than one rule are likely to have poor absorption or permeation.
        
        Rule of 5 criteria:
        1. Molecular weight ≤ 500 Da
        2. LogP ≤ 5 (lipophilicity)
        3. Hydrogen bond donors ≤ 5
        4. Hydrogen bond acceptors ≤ 10
        
        Compounds with ≤1 violation are generally considered drug-like.
        
        Args:
            mol (rdkit.Chem.Mol): RDKit molecule object
            
        Returns:
            Dict: Dictionary containing:
                - 'MW': float - Molecular weight (Da)
                - 'LogP': float - Partition coefficient (Wildman-Crippen)
                - 'HBD': int - Hydrogen bond donors (NH, OH)
                - 'HBA': int - Hydrogen bond acceptors (N, O)
                - 'Violations': int - Number of Lipinski violations (0-4)
                - 'Passes': bool - True if ≤1 violation (drug-like)
                
        Example:
            >>> mol = MolecularProcessor.smiles_to_mol("CC(=O)Oc1ccccc1C(=O)O")  # Aspirin
            >>> lipinski = MolecularProcessor.calculate_lipinski_descriptors(mol)
            >>> print(f"Violations: {lipinski['Violations']}, Passes: {lipinski['Passes']}")
            Violations: 0, Passes: True
            
        References:
            - Lipinski et al. (2001) Adv. Drug Deliv. Rev. [REFERENCES.md: 1]
            - Lipinski (2004) Drug Discov. Today Technol. [REFERENCES.md: 2]
            
        Note:
            This is a filter, not a predictor. Compounds passing Ro5 may still have
            poor bioavailability. Beyond-Rule-of-5 (bRo5) drugs exist but require
            special consideration (e.g., macrocycles, natural products).
        """
        # Return empty dictionary if molecule is None
        if mol is None:
            return {}
        
        # Calculate molecular weight in Daltons
        mw = Descriptors.MolWt(mol)
        
        # Calculate LogP using Wildman-Crippen method
        logp = Crippen.MolLogP(mol)
        
        # Count hydrogen bond donors (NH and OH groups)
        hbd = Descriptors.NumHDonors(mol)
        
        # Count hydrogen bond acceptors (N and O atoms)
        hba = Descriptors.NumHAcceptors(mol)
        
        # Count violations of each rule
        violations = 0
        
        # Check Rule 1: MW ≤ 500
        if mw > 500:
            violations += 1
        
        # Check Rule 2: LogP ≤ 5
        if logp > 5:
            violations += 1
        
        # Check Rule 3: HBD ≤ 5
        if hbd > 5:
            violations += 1
        
        # Check Rule 4: HBA ≤ 10
        if hba > 10:
            violations += 1
        
        # Return Lipinski analysis results
        return {
            # Molecular weight rounded to 2 decimals
            'MW': round(mw, 2),
            # LogP rounded to 2 decimals
            'LogP': round(logp, 2),
            # Hydrogen bond donor count
            'HBD': hbd,
            # Hydrogen bond acceptor count
            'HBA': hba,
            # Number of violated rules
            'Violations': violations,
            # Passes if 0 or 1 violation (most drugs have ≤1)
            'Passes': violations <= 1
        }
    
    # Calculate Veber descriptors for oral bioavailability
    # Complements Lipinski with flexibility and polarity criteria
    @staticmethod
    def calculate_veber_descriptors(mol) -> Dict:
        """
        Calculate Veber descriptors for oral bioavailability prediction.
        
        Veber et al. (2002) [REFERENCES.md: 3] found that rotatable bonds and
        polar surface area are better predictors of oral bioavailability than
        Lipinski's Rule of 5 alone. These rules complement Lipinski by focusing
        on molecular flexibility and polarity.
        
        Veber criteria:
        1. Rotatable bonds ≤ 10 (molecular flexibility)
        2. TPSA ≤ 140 Ų (polar surface area)
        
        Both criteria must be met for good oral bioavailability.
        
        Args:
            mol (rdkit.Chem.Mol): RDKit molecule object
            
        Returns:
            Dict: Dictionary containing:
                - 'Rotatable Bonds': int - Number of non-ring single bonds
                - 'TPSA': float - Topological polar surface area (Ų)
                - 'Passes': bool - True if both criteria met
                
        Example:
            >>> mol = MolecularProcessor.smiles_to_mol("CC(C)Cc1ccc(cc1)C(C)C(=O)O")
            >>> veber = MolecularProcessor.calculate_veber_descriptors(mol)
            >>> print(f"RotBonds: {veber['Rotatable Bonds']}, Passes: {veber['Passes']}")
            RotBonds: 4, Passes: True
            
        References:
            - Veber et al. (2002) J. Med. Chem. [REFERENCES.md: 3]
            - TPSA correlation with bioavailability
            
        Note:
            TPSA correlates with:
            - Intestinal absorption (Caco-2 permeability)
            - Blood-brain barrier penetration
            - Pgp efflux substrate likelihood
        """
        # Return empty dictionary if molecule is None
        if mol is None:
            return {}
        
        # Count rotatable bonds (non-ring single bonds that can rotate)
        rotatable_bonds = Descriptors.NumRotatableBonds(mol)
        
        # Calculate topological polar surface area
        tpsa = Descriptors.TPSA(mol)
        
        # Both criteria must be met for Veber to pass
        passes = (rotatable_bonds <= 10) and (tpsa <= 140)
        
        # Return Veber analysis results
        return {
            # Rotatable bond count
            'Rotatable Bonds': rotatable_bonds,
            # TPSA rounded to 2 decimals
            'TPSA': round(tpsa, 2),
            # Pass/fail based on both criteria
            'Passes': passes
        }
    
    # Calculate QED (Quantitative Estimate of Drug-likeness) score
    # Continuous score (0-1) instead of binary pass/fail
    @staticmethod
    def calculate_qed(mol) -> float:
        """
        Calculate Quantitative Estimate of Drug-likeness (QED) score.
        
        QED (Bickerton et al., 2012 [REFERENCES.md: 4]) provides a continuous
        measure of drug-likeness (0 to 1) based on the distribution of molecular
        properties in marketed drugs. Unlike Lipinski and Veber rules (binary pass/fail),
        QED provides a nuanced assessment of overall drug-likeness.
        
        QED considers 8 molecular properties:
        1. Molecular weight
        2. LogP
        3. H-bond donors
        4. H-bond acceptors  
        5. Polar surface area
        6. Rotatable bonds
        7. Aromatic rings
        8. Structural alerts
        
        Score interpretation:
        - QED ≥ 0.67: High drug-likeness (top third of approved drugs)
        - QED 0.49-0.67: Moderate drug-likeness (middle third)
        - QED < 0.49: Low drug-likeness (bottom third)
        
        Args:
            mol (rdkit.Chem.Mol): RDKit molecule object
            
        Returns:
            float: QED score (0.0 to 1.0)
                   Returns 0.0 if mol is None or calculation fails
                   
        Example:
            >>> mol = MolecularProcessor.smiles_to_mol("CC(=O)Oc1ccccc1C(=O)O")  # Aspirin
            >>> qed = MolecularProcessor.calculate_qed(mol)
            >>> print(f"QED: {qed:.3f}")
            QED: 0.541
            
        References:
            - Bickerton et al. (2012) Nature Chemistry [REFERENCES.md: 4]
            - RDKit QED implementation based on original publication
            
        Note:
            QED is optimized for small molecule oral drugs. For biologics,
            peptides, or CNS drugs, consider alternative drug-likeness metrics.
        """
        # Return 0 if molecule is None
        if mol is None:
            return 0.0
        
        # Try to calculate QED score
        try:
            # Use RDKit's QED implementation (Bickerton method)
            return round(QED.qed(mol), 3)
        except:
            # Return 0 if calculation fails
            return 0.0
    
    # Calculate Synthetic Accessibility (SA) score
    # Estimates how easy the molecule is to synthesize
    @staticmethod
    def calculate_sa_score(mol) -> float:
        """
        Calculate Synthetic Accessibility (SA) score.
        
        The SA score (Ertl & Schuffenhauer, 2009 [REFERENCES.md: 5]) estimates
        the ease of chemical synthesis based on:
        1. Fragment contributions (common vs rare substructures)
        2. Molecular complexity (ring systems, stereocenters, bridging)
        
        Score range: 1 (easy to synthesize) to 10 (very difficult)
        
        Score interpretation:
        - SA 1-3: Easy to synthesize (few synthetic steps)
        - SA 4-6: Moderate difficulty (standard medicinal chemistry)
        - SA 7-10: Very difficult (complex natural product-like)
        
        Args:
            mol (rdkit.Chem.Mol): RDKit molecule object
            
        Returns:
            float: SA score (1.0 to 10.0)
                   Returns 0.0 if mol is None
                   Falls back to fingerprint-based estimate if RDKit SA contrib unavailable
                   
        Example:
            >>> mol = MolecularProcessor.smiles_to_mol("CC(C)Cc1ccc(cc1)C(C)C(=O)O")
            >>> sa = MolecularProcessor.calculate_sa_score(mol)
            >>> print(f"SA Score: {sa:.2f}")
            SA Score: 2.31
            
        References:
            - Ertl & Schuffenhauer (2009) J. Cheminform. [REFERENCES.md: 5]
            - Fragment-based complexity assessment
            
        Note:
            SA score is an estimate. Actual synthetic feasibility depends on:
            - Available starting materials
            - Chemist expertise
            - Budget and timeline constraints
            
            This implementation attempts to use RDKit's contributed SA scorer.
            If unavailable, falls back to a simplified fingerprint complexity measure.
        """
        # Return 0 if molecule is None
        if mol is None:
            return 0.0
        
        # Try to use RDKit's contributed SA scorer (more accurate)
        try:
            # Import RDKit configuration to find contrib directory
            from rdkit.Chem import RDConfig
            import sys
            import os
            
            # Add SA_Score contrib module to Python path
            sys.path.append(os.path.join(RDConfig.RDContribDir, 'SA_Score'))
            
            # Import the SA scorer module
            import sascorer
            
            # Calculate and return SA score
            return round(sascorer.calculateScore(mol), 2)
        except:
            # Fallback: Estimate based on fingerprint complexity
            # Generate Morgan fingerprint (captures molecular features)
            fp = rdMolDescriptors.GetMorganFingerprint(mol, 2)
            
            # Count unique molecular fragments
            complexity = len(fp.GetNonzeroElements())
            
            # Map complexity to 1-10 scale
            # Division by 50 is empirical normalization
            return round(max(1, min(10, complexity / 50)), 2)
    
    # Generate Morgan (ECFP) fingerprint for similarity calculations
    # Fingerprints are bit vectors representing molecular features
    @staticmethod
    def generate_morgan_fingerprint(mol, radius=2, n_bits=2048) -> np.ndarray:
        """
        Generate Morgan (circular) fingerprint for molecular similarity calculations.
        
        Morgan fingerprints (Rogers & Hahn, 2010 [REFERENCES.md: 37]), also known as
        ECFP (Extended Connectivity Fingerprints), are widely used for:
        - Molecular similarity calculations
        - Virtual screening
        - QSAR model input features
        - Clustering and diversity analysis
        
        The algorithm iteratively expands around each atom, capturing local
        molecular environments at increasing radii. Equivalent to:
        - ECFP4: radius=2
        - ECFP6: radius=3
        
        Args:
            mol (rdkit.Chem.Mol): RDKit molecule object
            radius (int, optional): Fingerprint radius. Defaults to 2 (ECFP4).
                                   Common values: 2 (ECFP4), 3 (ECFP6)
            n_bits (int, optional): Fingerprint length. Defaults to 2048.
                                   Longer fingerprints reduce collision probability.
                                   
        Returns:
            np.ndarray: Binary fingerprint vector of length n_bits
                       Returns zero vector if mol is None
                       
        Example:
            >>> mol = MolecularProcessor.smiles_to_mol("CC(C)Cc1ccc(cc1)C(C)C(=O)O")
            >>> fp = MolecularProcessor.generate_morgan_fingerprint(mol, radius=2)
            >>> print(f"Fingerprint shape: {fp.shape}, Set bits: {fp.sum()}")
            Fingerprint shape: (2048,), Set bits: 124
            
        References:
            - Rogers & Hahn (2010) J. Chem. Inf. Model. [REFERENCES.md: 37]
            - ECFP fingerprints for similarity searching
            
        Note:
            - Radius=2 (ECFP4) is standard for drug-like molecules
            - For very large or small molecules, adjust radius accordingly
            - Longer fingerprints (4096 bits) reduce hash collisions
            - Tanimoto similarity commonly used with Morgan fingerprints
        """
        # Return zero vector if molecule is None
        if mol is None:
            return np.zeros(n_bits)
        
        # Generate Morgan fingerprint as bit vector
        # radius=2 captures atoms up to 2 bonds away (ECFP4)
        # nBits specifies the length of the bit vector
        fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
        
        # Convert RDKit fingerprint to numpy array
        return np.array(fp)
    
    # Calculate comprehensive set of molecular descriptors
    # Used as features for machine learning models
    @staticmethod
    def calculate_molecular_descriptors(mol) -> np.ndarray:
        """
        Calculate comprehensive set of molecular descriptors for QSAR modeling.
        
        Computes 200 molecular descriptors spanning:
        - Constitutional (MW, formula)
        - Topological (connectivity indices)
        - Geometric (3D shape, if applicable)
        - Electronic (partial charges, VSA)
        - Physicochemical (LogP, TPSA, refractivity)
        
        These descriptors form feature vectors for machine learning models:
        - Random Forest QSAR [REFERENCES.md: 28]
        - XGBoost predictions [REFERENCES.md: 30]
        - Neural networks
        
        Descriptor categories included:
        - Basic properties: MW, LogP, TPSA, HBD, HBA
        - Topological indices: Kappa indices, Chi indices
        - VSA descriptors: PEOE_VSA, SMR_VSA, SlogP_VSA, EState_VSA
        - Complexity: Bertz CT, Hall-Kier Alpha
        - Ring counts: Saturated, aromatic, aliphatic rings
        - Fragment counts: Heterocycles
        
        Args:
            mol (rdkit.Chem.Mol): RDKit molecule object
            
        Returns:
            np.ndarray: Array of 200 molecular descriptors
                       Returns zero array if mol is None
                       Pads with zeros if fewer descriptors calculated
                       
        Example:
            >>> mol = MolecularProcessor.smiles_to_mol("CC(C)Cc1ccc(cc1)C(C)C(=O)O")
            >>> descriptors = MolecularProcessor.calculate_molecular_descriptors(mol)
            >>> print(f"Descriptor vector shape: {descriptors.shape}")
            Descriptor vector shape: (200,)
            
        References:
            - Descriptor usage in QSAR: Tropsha (2010) [REFERENCES.md: 44]
            - Random Forest with molecular descriptors [REFERENCES.md: 28]
            - Best practices for descriptor selection [REFERENCES.md: 44,45,46]
            
        Note:
            Current implementation includes ~30 key descriptors, padded to 200.
            For production QSAR models:
            - Expand to full RDKit descriptor set (>200 available)
            - Apply feature selection (remove low-variance, correlated)
            - Normalize/standardize before ML model training
            - Consider descriptor importance for model interpretability
            
            Descriptor selection should be task-specific (ADME vs toxicity vs activity).
        """
        # Return zero vector if molecule is None
        if mol is None:
            return np.zeros(200)
        
        # Initialize list to store descriptor values
        descriptors = []
        
        # Basic physicochemical properties
        # These are the most commonly used descriptors
        descriptors.append(Descriptors.MolWt(mol))             # Molecular weight
        descriptors.append(Crippen.MolLogP(mol))               # LogP (Wildman-Crippen)
        descriptors.append(Descriptors.TPSA(mol))              # Polar surface area
        descriptors.append(Descriptors.NumHDonors(mol))        # H-bond donors
        descriptors.append(Descriptors.NumHAcceptors(mol))     # H-bond acceptors
        descriptors.append(Descriptors.NumRotatableBonds(mol)) # Rotatable bonds
        descriptors.append(Descriptors.NumAromaticRings(mol))  # Aromatic rings
        descriptors.append(Lipinski.FractionCSP3(mol))         # sp3 carbon fraction
        descriptors.append(Crippen.MolMR(mol))                 # Molar refractivity
        
        # Complexity and topological indices
        # Measure molecular complexity and shape
        descriptors.append(Descriptors.BertzCT(mol))           # Bertz complexity index
        descriptors.append(Descriptors.HallKierAlpha(mol))     # Hall-Kier alpha
        descriptors.append(Descriptors.Kappa1(mol))            # Kappa shape index 1
        descriptors.append(Descriptors.Kappa2(mol))            # Kappa shape index 2
        descriptors.append(Descriptors.Kappa3(mol))            # Kappa shape index 3
        
        # Chi connectivity indices
        # Measure molecular branching and connectivity
        descriptors.append(Descriptors.Chi0v(mol))             # Chi0v
        descriptors.append(Descriptors.Chi1v(mol))             # Chi1v
        descriptors.append(Descriptors.Chi2v(mol))             # Chi2v
        descriptors.append(Descriptors.Chi3v(mol))             # Chi3v
        descriptors.append(Descriptors.Chi4v(mol))             # Chi4v
        
        # VSA (van der Waals surface area) descriptors
        # Partition surface area by atomic properties
        descriptors.append(Descriptors.LabuteASA(mol))         # Labute ASA
        descriptors.append(Descriptors.PEOE_VSA1(mol))         # Partial charge VSA
        descriptors.append(Descriptors.PEOE_VSA2(mol))         # Partial charge VSA 2
        descriptors.append(Descriptors.SMR_VSA1(mol))          # Molar refractivity VSA
        descriptors.append(Descriptors.SlogP_VSA1(mol))        # LogP VSA
        descriptors.append(Descriptors.EState_VSA1(mol))       # E-state VSA
        descriptors.append(Descriptors.VSA_EState1(mol))       # VSA E-state
        
        # Ring and structural features
        descriptors.append(Descriptors.NumSaturatedRings(mol))      # Saturated rings
        descriptors.append(Descriptors.NumAliphaticRings(mol))      # Aliphatic rings
        descriptors.append(rdMolDescriptors.CalcNumRings(mol))      # Total rings
        descriptors.append(rdMolDescriptors.CalcNumHeterocycles(mol))  # Heterocycles
        
        # Pad to 200 dimensions with zeros
        # In production, expand with additional RDKit descriptors
        for i in range(170):
            descriptors.append(0)
        
        # Convert to numpy array and return first 200 elements
        return np.array(descriptors[:200])


# Shared molecular feature extractor for neural network models
# Combines descriptors and fingerprints into single feature vector
class MolecularFeatureExtractor:
    """
    Shared molecular feature extractor for neural network models.
    
    Extracts standardized feature vectors combining:
    - 30 RDKit molecular descriptors
    - 2048 Morgan fingerprint bits (ECFP4, radius=2)
    
    Total: 2078 features
    
    Used by:
    - NeuralToxicityPredictor (models/neural_toxicity.py)
    - ProteinLigandCompatibilityScorer (models/protein_ligand_compatibility.py)
    """
    
    # Extract comprehensive molecular feature vector
    @staticmethod
    def extract_features(mol) -> np.ndarray:
        """
        Extract comprehensive molecular feature vector.
        
        Combines:
        - RDKit molecular descriptors (30 features)
        - Morgan fingerprints (2048 bits, radius=2)
        
        Args:
            mol: RDKit molecule object
        
        Returns:
            Feature vector (2078 dimensions)
        """
        # Return zero vector if molecule is None
        if mol is None:
            return np.zeros(2078)
        
        # Extract 30 key molecular descriptors
        # These capture physicochemical properties
        descriptors = np.array([
            # Basic properties
            Descriptors.MolWt(mol),              # Molecular weight
            Descriptors.MolLogP(mol),            # LogP
            Descriptors.TPSA(mol),               # Polar surface area
            Descriptors.NumHDonors(mol),         # H-bond donors
            Descriptors.NumHAcceptors(mol),      # H-bond acceptors
            Descriptors.NumRotatableBonds(mol),  # Rotatable bonds
            # Ring counts
            Descriptors.NumAromaticRings(mol),   # Aromatic rings
            Descriptors.NumAliphaticRings(mol),  # Aliphatic rings
            Descriptors.NumSaturatedRings(mol),  # Saturated rings
            Descriptors.NumHeteroatoms(mol),     # Heteroatoms (N, O, S, etc.)
            Descriptors.RingCount(mol),          # Total ring count
            Descriptors.FractionCSP3(mol),       # Fraction sp3 carbons
            # Aromatic/saturated ring breakdown
            Descriptors.NumAromaticCarbocycles(mol),    # Aromatic carbocycles
            Descriptors.NumAromaticHeterocycles(mol),   # Aromatic heterocycles
            Descriptors.NumSaturatedCarbocycles(mol),   # Saturated carbocycles
            Descriptors.NumSaturatedHeterocycles(mol),  # Saturated heterocycles
            Descriptors.NumAliphaticCarbocycles(mol),   # Aliphatic carbocycles
            Descriptors.NumAliphaticHeterocycles(mol),  # Aliphatic heterocycles
            # Topological indices
            Descriptors.BalabanJ(mol),           # Balaban J index
            Descriptors.BertzCT(mol),            # Bertz complexity
            Descriptors.Chi0(mol),               # Chi0 connectivity
            Descriptors.Chi1(mol),               # Chi1 connectivity
            Descriptors.HallKierAlpha(mol),      # Hall-Kier alpha
            Descriptors.Kappa1(mol),             # Kappa 1
            Descriptors.Kappa2(mol),             # Kappa 2
            Descriptors.Kappa3(mol),             # Kappa 3
            # Surface area descriptors
            Descriptors.LabuteASA(mol),          # Labute ASA
            Descriptors.PEOE_VSA1(mol),          # Partial charge VSA 1
            Descriptors.SMR_VSA1(mol),           # Molar refractivity VSA 1
            Descriptors.SlogP_VSA1(mol)          # LogP VSA 1
        ])
        
        # Generate Morgan fingerprints (ECFP4, radius=2, 2048 bits)
        # Import DataStructs for fingerprint conversion
        from rdkit.Chem import DataStructs
        
        # Generate Morgan fingerprint as bit vector
        morgan_fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius=2, nBits=2048)
        
        # Initialize numpy array for fingerprint
        fp_array = np.zeros(2048)
        
        # Convert RDKit fingerprint to numpy array
        DataStructs.ConvertToNumpyArray(morgan_fp, fp_array)
        
        # Concatenate descriptors and fingerprints
        features = np.concatenate([descriptors, fp_array])
        
        # Normalize descriptors (simple min-max scaling)
        # Add small epsilon (1e-8) to prevent division by zero
        features[:30] = features[:30] / (np.max(features[:30]) + 1e-8)
        
        # Return combined feature vector
        return features
