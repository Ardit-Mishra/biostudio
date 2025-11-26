# =============================================================================
# KINASE INHIBITORS CASE STUDY DATA
# =============================================================================
# This file contains sample data for demonstrating drug discovery workflows.
# It includes candidate molecules for evaluation and FDA-approved benchmark drugs.
# Used by the Case Study page to show how to rank potential drug candidates.
# =============================================================================

# Dictionary containing the complete case study for kinase inhibitor lead ranking
# This simulates a real pharmaceutical research scenario where multiple candidates are evaluated
kinase_inhibitor_case_study = {
    # Title of the case study displayed in the UI
    'title': 'Ranking Potential Kinase Inhibitor Leads',
    
    # Detailed description explaining the purpose and methodology of the case study
    # Uses triple quotes for multi-line string formatting
    'description': '''
    This case study demonstrates a typical early-stage drug discovery workflow in pharmaceutical research.
    We evaluate 5 potential kinase inhibitor candidates using ML-based predictions of ADME/PK properties, toxicity profiles,
    and drug-likeness scores to prioritize leads for further development. This workflow mirrors industry-standard 
    lead optimization processes used in oncology drug discovery.
    ''',
    
    # List of candidate molecules to be evaluated in the case study
    # Each candidate has a name, SMILES structure, and description
    'molecules': [
        {
            # First candidate: Based on Imatinib structure (FDA-approved for CML)
            'name': 'Candidate A (Imatinib-like)',
            # SMILES notation: Text representation of the molecular structure
            # This encodes the atoms, bonds, and connectivity of the molecule
            'smiles': 'Cc1ccc(cc1Nc2nccc(n2)c3cccnc3)NC(=O)c4ccc(cc4)CN5CCN(CC5)C',
            # Description of the molecule's therapeutic target and mechanism
            'description': 'BCR-ABL inhibitor scaffold, known kinase inhibitor profile'
        },
        {
            # Second candidate: Based on Gefitinib structure (FDA-approved for NSCLC)
            'name': 'Candidate B (Gefitinib-like)',
            # SMILES contains methoxy groups (COc), fluorine (F), and chlorine (Cl)
            'smiles': 'COc1cc2ncnc(c2cc1OCCCN3CCOCC3)Nc4ccc(c(c4)Cl)F',
            # EGFR (Epidermal Growth Factor Receptor) is a common cancer target
            'description': 'EGFR inhibitor scaffold, tyrosine kinase targeting'
        },
        {
            # Third candidate: A newly designed molecule not based on existing drugs
            'name': 'Candidate C (Novel scaffold)',
            # Novel structure with piperazine ring and cyano group (C#N)
            'smiles': 'CN1CCN(CC1)c2ccc(cc2)Nc3ncc(c(n3)Nc4ccc(cc4)C#N)Cl',
            # Selectivity means it targets specific kinases with fewer off-target effects
            'description': 'Novel kinase inhibitor with improved selectivity'
        },
        {
            # Fourth candidate: Modified version optimized for better properties
            'name': 'Candidate D (Optimized)',
            # Contains morpholine ring (CCOCC) which often improves solubility
            'smiles': 'Cc1cc(c(cc1NC(=O)c2ccc(cc2)CN3CCOCC3)C)Nc4nccc(n4)c5cccnc5',
            # PK = Pharmacokinetics (how the drug moves through the body)
            'description': 'Optimized for better PK properties'
        },
        {
            # Fifth candidate: Simpler structure as a backup option
            'name': 'Candidate E (Backup)',
            # Smaller molecule with fewer rotatable bonds (easier to make)
            'smiles': 'COc1cc2c(cc1OC)c(ncn2)Nc3ccc(c(c3)Cl)F',
            # Simplified structures are often easier and cheaper to synthesize
            'description': 'Backup candidate with simplified structure'
        }
    ],
    
    # List of criteria used to evaluate and rank the candidate molecules
    # These are industry-standard parameters for drug development decisions
    'evaluation_criteria': [
        # ADME/PK: Absorption, Distribution, Metabolism, Excretion / Pharmacokinetics
        'ADME/PK properties (permeability, BBB penetration, metabolism)',
        # Safety profile: Potential for liver damage, heart issues, DNA damage
        'Toxicity profile (hepatotoxicity, hERG inhibition, mutagenicity)',
        # Drug-likeness: Does the molecule have properties typical of successful drugs
        'Drug-likeness (Lipinski, Veber, QED, SA score)',
        # Target prediction: Likelihood of binding to kinase proteins
        'Target class prediction (kinase inhibitor likelihood)',
        # Combined score for overall candidate quality
        'Overall lead-like score'
    ]
}


# List of FDA-approved kinase inhibitor drugs used as benchmarks
# These serve as reference points for comparing novel candidates
# If a candidate has similar properties to approved drugs, it's a good sign
approved_kinase_drugs_benchmark = [
    {
        # Venetoclax: First-in-class BCL-2 inhibitor approved in 2016
        'name': 'Venetoclax',
        # Complex SMILES structure - large molecule with many functional groups
        'smiles': 'CC1(CCC(=C(C1)CN2CCN(CC2)C3=CC=C(C=C3)C(=O)NS(=O)(=O)C4=CC(=C(C=C4)NCC5CCOCC5)[N+](=O)[O-])C6=CC=C(C=C6)Cl)C',
        # BCL-2: Anti-apoptotic protein that prevents cancer cell death
        'target': 'BCL-2',
        # CLL: A type of blood cancer affecting white blood cells
        'indication': 'Chronic Lymphocytic Leukemia',
        # Category for classification purposes
        'category': 'Oncology',
        # Additional context about the drug's significance
        'notes': 'First-in-class BCL-2 inhibitor for CLL'
    },
    {
        # Upadacitinib: JAK inhibitor approved for autoimmune diseases
        'name': 'Upadacitinib',
        # Contains fluorine atoms (F) which improve metabolic stability
        'smiles': 'CN1CCN(CC1)C(=O)C2=C(C=CC(=C2F)N3C=C(C=N3)C4CC4)F',
        # JAK1: Janus Kinase 1, involved in immune signaling
        'target': 'JAK1',
        # RA: Autoimmune disease causing joint inflammation
        'indication': 'Rheumatoid Arthritis',
        # Immunology drugs modulate the immune system
        'category': 'Immunology',
        # Selective means it primarily targets JAK1 over other JAK family members
        'notes': 'Selective JAK1 inhibitor for autoimmune diseases'
    },
    {
        # Ibrutinib: BTK inhibitor for B-cell cancers
        'name': 'Ibrutinib',
        # Contains acrylamide group for irreversible binding
        'smiles': 'C1CN(CCN1C2=CC=CC=C2)C(=O)C=CC3=CC=C(C=C3)C#N.C1CN(CCN1C2=CC=CC=C2)C(=O)C=CC3=CC=C(C=C3)C#N',
        # BTK: Bruton's Tyrosine Kinase, essential for B-cell development
        'target': 'BTK',
        # MCL: An aggressive form of non-Hodgkin lymphoma
        'indication': 'Mantle Cell Lymphoma',
        # Oncology drugs are used to treat cancer
        'category': 'Oncology',
        # Irreversible inhibitors form permanent bonds with their targets
        'notes': 'Irreversible BTK inhibitor for B-cell malignancies'
    }
]


# Function to retrieve the case study data
# Called by the Streamlit app when loading the Case Study page
def get_case_study_data():
    """
    Returns case study data for kinase inhibitor lead ranking demonstration.
    
    This function provides the molecules, criteria, and descriptions needed
    to run the case study workflow in the Streamlit application.
    
    Returns:
        dict: Dictionary containing:
            - title: Name of the case study
            - description: Detailed explanation of the workflow
            - molecules: List of candidate molecules with SMILES and descriptions
            - evaluation_criteria: List of criteria for ranking candidates
    """
    # Return the pre-defined case study dictionary
    return kinase_inhibitor_case_study


# Function to retrieve benchmark drug data
# Used to compare novel candidates against known successful drugs
def get_approved_kinase_drugs():
    """
    Returns benchmark data of FDA-approved kinase inhibitor drugs.
    These serve as reference compounds for comparison with novel candidates.
    
    Benchmark comparison helps validate predictions:
    - If predictions match known properties of approved drugs, model is working
    - Novel candidates with similar profiles may have higher success probability
    
    Returns:
        list: List of dictionaries containing approved drug information:
            - name: Drug name
            - smiles: Chemical structure in SMILES format
            - target: Primary protein target
            - indication: Disease the drug treats
            - category: Therapeutic area
            - notes: Additional context
    """
    # Return the pre-defined list of approved drugs
    return approved_kinase_drugs_benchmark
