abbvie_kinase_case_study = {
    'title': 'Ranking Potential Kinase Inhibitor Leads',
    'description': '''
    This case study demonstrates a typical early-stage drug discovery workflow at pharmaceutical companies like AbbVie.
    We evaluate 5 potential kinase inhibitor candidates using ML-based predictions of ADME/PK properties, toxicity profiles,
    and drug-likeness scores to prioritize leads for further development.
    ''',
    'molecules': [
        {
            'name': 'Candidate A (Imatinib-like)',
            'smiles': 'Cc1ccc(cc1Nc2nccc(n2)c3cccnc3)NC(=O)c4ccc(cc4)CN5CCN(CC5)C',
            'description': 'BCR-ABL inhibitor scaffold, known kinase inhibitor profile'
        },
        {
            'name': 'Candidate B (Gefitinib-like)',
            'smiles': 'COc1cc2ncnc(c2cc1OCCCN3CCOCC3)Nc4ccc(c(c4)Cl)F',
            'description': 'EGFR inhibitor scaffold, tyrosine kinase targeting'
        },
        {
            'name': 'Candidate C (Novel scaffold)',
            'smiles': 'CN1CCN(CC1)c2ccc(cc2)Nc3ncc(c(n3)Nc4ccc(cc4)C#N)Cl',
            'description': 'Novel kinase inhibitor with improved selectivity'
        },
        {
            'name': 'Candidate D (Optimized)',
            'smiles': 'Cc1cc(c(cc1NC(=O)c2ccc(cc2)CN3CCOCC3)C)Nc4nccc(n4)c5cccnc5',
            'description': 'Optimized for better PK properties'
        },
        {
            'name': 'Candidate E (Backup)',
            'smiles': 'COc1cc2c(cc1OC)c(ncn2)Nc3ccc(c(c3)Cl)F',
            'description': 'Backup candidate with simplified structure'
        }
    ],
    'evaluation_criteria': [
        'ADME/PK properties (permeability, BBB penetration, metabolism)',
        'Toxicity profile (hepatotoxicity, hERG inhibition, mutagenicity)',
        'Drug-likeness (Lipinski, Veber, QED, SA score)',
        'Target class prediction (kinase inhibitor likelihood)',
        'Overall lead-like score'
    ]
}


abbvie_drugs_benchmark = [
    {
        'name': 'Venetoclax',
        'smiles': 'CC1(CCC(=C(C1)CN2CCN(CC2)C3=CC=C(C=C3)C(=O)NS(=O)(=O)C4=CC(=C(C=C4)NCC5CCOCC5)[N+](=O)[O-])C6=CC=C(C=C6)Cl)C',
        'target': 'BCL-2',
        'indication': 'Chronic Lymphocytic Leukemia',
        'category': 'Oncology'
    },
    {
        'name': 'Upadacitinib',
        'smiles': 'CN1CCN(CC1)C(=O)C2=C(C=CC(=C2F)N3C=C(C=N3)C4CC4)F',
        'target': 'JAK1',
        'indication': 'Rheumatoid Arthritis',
        'category': 'Immunology'
    },
    {
        'name': 'Ibrutinib',
        'smiles': 'C1CN(CCN1C2=CC=CC=C2)C(=O)C=CC3=CC=C(C=C3)C#N.C1CN(CCN1C2=CC=CC=C2)C(=O)C=CC3=CC=C(C=C3)C#N',
        'target': 'BTK',
        'indication': 'Mantle Cell Lymphoma',
        'category': 'Oncology'
    }
]


def get_case_study_data():
    return abbvie_kinase_case_study


def get_abbvie_benchmark_drugs():
    return abbvie_drugs_benchmark
