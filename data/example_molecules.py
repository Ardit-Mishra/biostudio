"""
Example Molecules and Biologics Library

Curated examples of small molecules, peptides, and proteins for demonstration
and intelligent input suggestions.

Author: Ardit Mishra
"""

SMALL_MOLECULES = {
    'Ibuprofen': {
        'smiles': 'CC(C)Cc1ccc(cc1)C(C)C(=O)O',
        'name': 'Ibuprofen',
        'category': 'NSAID',
        'description': 'Common pain reliever and anti-inflammatory'
    },
    'Aspirin': {
        'smiles': 'CC(=O)Oc1ccccc1C(=O)O',
        'name': 'Aspirin',
        'category': 'NSAID',
        'description': 'Pain reliever, fever reducer, anti-inflammatory'
    },
    'Paracetamol': {
        'smiles': 'CC(=O)Nc1ccc(cc1)O',
        'name': 'Paracetamol (Acetaminophen)',
        'category': 'Analgesic',
        'description': 'Pain reliever and fever reducer'
    },
    'Caffeine': {
        'smiles': 'CN1C=NC2=C1C(=O)N(C(=O)N2C)C',
        'name': 'Caffeine',
        'category': 'Stimulant',
        'description': 'Central nervous system stimulant'
    },
    'Montelukast': {
        'smiles': 'CC(C)(O)c1c(Cl)cc(cc1Cl)C(=O)NCCc2ccccc2CC(O)C(Cc3cc(ccc3)c4scnc4C)C(=O)O',
        'name': 'Montelukast',
        'category': 'Leukotriene inhibitor',
        'description': 'Asthma and allergy medication'
    },
    'Cetirizine': {
        'smiles': 'C1CN(CCN1CCOCC(=O)O)C(c2ccc(cc2)Cl)c3ccccc3',
        'name': 'Cetirizine',
        'category': 'Antihistamine',
        'description': 'Allergy medication'
    },
    'Imatinib': {
        'smiles': 'Cc1ccc(cc1Nc2nccc(n2)c3cccnc3)NC(=O)c4ccc(cc4)CN5CCN(CC5)C',
        'name': 'Imatinib',
        'category': 'Kinase inhibitor',
        'description': 'Cancer drug (CML, GIST)'
    },
    'Gefitinib': {
        'smiles': 'COc1cc2c(cc1OCC3CCNCC3)ncnc2Nc4cc(c(cc4F)Cl)F',
        'name': 'Gefitinib',
        'category': 'EGFR inhibitor',
        'description': 'Lung cancer treatment'
    },
    'Atorvastatin': {
        'smiles': 'CC(C)c1c(c(c(c(c1OCC(CC(CC(=O)O)O)O)c2ccc(cc2)F)C(=O)Nc3ccccc3)O)C(C)C',
        'name': 'Atorvastatin',
        'category': 'Statin',
        'description': 'Cholesterol-lowering medication'
    },
    'Metformin': {
        'smiles': 'CN(C)C(=N)NC(=N)N',
        'name': 'Metformin',
        'category': 'Biguanide',
        'description': 'Type 2 diabetes medication'
    }
}

PEPTIDE_DRUGS = {
    'Insulin B-chain (fragment)': {
        'sequence': 'FVNQHLCGSHLVEALYLVCGERGFFYTPKA',
        'name': 'Insulin B-chain (fragment)',
        'category': 'Peptide hormone',
        'description': 'Fragment of insulin B-chain for diabetes treatment',
        'length': 30
    },
    'Semaglutide (fragment)': {
        'sequence': 'HAEGTFTSDVSSYLEGQAAKEFIAWLVKGR',
        'name': 'Semaglutide (fragment)',
        'category': 'GLP-1 agonist',
        'description': 'Fragment of diabetes/weight-loss drug',
        'length': 30
    },
    'Exenatide (fragment)': {
        'sequence': 'HGEGTFTSDLSKQMEEEAVRLFIEWLKNGGPSSGAPPPS',
        'name': 'Exenatide (fragment)',
        'category': 'GLP-1 agonist',
        'description': 'Fragment of type 2 diabetes treatment',
        'length': 39
    },
    'Octreotide': {
        'sequence': 'FCFWKTCT',
        'name': 'Octreotide',
        'category': 'Somatostatin analog',
        'description': 'Treats acromegaly and certain tumors',
        'length': 8
    },
    'Leuprolide': {
        'sequence': 'HWSYGLRPG',
        'name': 'Leuprolide',
        'category': 'GnRH agonist',
        'description': 'Treats prostate cancer, endometriosis',
        'length': 9
    },
    'Glucagon': {
        'sequence': 'HSQGTFTSDYSKYLDSRRAQDFVQWLMNT',
        'name': 'Glucagon',
        'category': 'Peptide hormone',
        'description': 'Raises blood glucose levels',
        'length': 29
    }
}

PROTEIN_BIOLOGICS = {
    'Interferon beta-1a (fragment)': {
        'sequence': 'MSYNTIATLAAWGFLLWAAATPTACCDLPQTHSLGSRRTLMLLAQMRRISLFSCLKDRHDFGFPQEEFGNQFQKAETIPVLHEMIQQIFNLFSTKDSSAAWDETLLDKFYTELYQQLNDLEACVIQGVGVTETPLMKEDSILAVRKYFQRITLYLKEKKYSPCAWEVVRAEIMRSFSLSTNLQESLRSKE',
        'name': 'Interferon beta-1a (fragment)',
        'category': 'Cytokine',
        'description': 'Treats multiple sclerosis',
        'length': 166
    },
    'Erythropoietin (fragment)': {
        'sequence': 'APPRLICDSRVLERYLLEAKEAENITTGCAEHCSLNENITVPDTKVNFYAWKRMEVGQQAVEVWQGLALLSEAVLRGQALLVNSSQPWEPLQLHVDKAVSGLRSLTTLLRALGAQKEAISPPDAASAAPLRTITADTFRKLFRVYSNFLRGKLKLYTGEACRTGDR',
        'name': 'Erythropoietin (fragment)',
        'category': 'Growth factor',
        'description': 'Stimulates red blood cell production',
        'length': 166
    },
    'Human Growth Hormone (fragment)': {
        'sequence': 'FPTIPLSRLFDNAMLRAHRLHQLAFDTYQEFEEAYIPKEQKYSFLQNPQTSLCFSESIPTPSNREETQQKSNLELLRISLLLIQSWLEPVQFLRSVFANSLVYGASDSNVYDLLKDLEEGIQTLMGRLEDGSPRTGQIFKQTYSKFDTNSHNDDALLKNYGLLYCFRKDMDKVETFLRIVQCRSVEGSCGF',
        'name': 'Human Growth Hormone (fragment)',
        'category': 'Growth hormone',
        'description': 'Treats growth hormone deficiency',
        'length': 191
    },
    'BCR-ABL (fragment)': {
        'sequence': 'MQKLHGWPQENIVAVVGDGAQYSVKYKGEGATELLVQQVFDARETVSKYKGIPQKCIVVIVTKKAGDVIPAKNVLDKIYSMVLVGSEQVQQVFDEREEWKVARNNYPKVRKGSIVKRISSTIKRFKPVALTLKKLNFSEAEEAARLCREMAYMPRQAERAQRMEYAFE',
        'name': 'BCR-ABL fusion protein (fragment)',
        'category': 'Kinase target',
        'description': 'Target of Imatinib in CML',
        'length': 161
    },
    'EGFR (fragment)': {
        'sequence': 'LRVAPEEPLTQPGVTPQDNGTGRCEKCAWLEERGDCKVLGAPQCTFQENPKKYWELCDRLYQHVDPQTPLWAWPDLAQKGCNFNLIPAYNQKTWEYPNKKLQDVEKDGSYKVLEIFSSGLKDPRVTHVLGVCRGIGGTTKIFVQDVGKGDIVVNYADVAQTRVRTVAPNYSAGKPTLGKTVVMWRGETFVVTGWPTDGGKVKLKPLDKRVRIYTQDRWDGSGDKQATRFWGCLLGPGKSVFDLGSGYNGLSKDELATARQKVGNKKEPRQCVHFRCEHGHWLRVPCPKVWRPQCHREQEGDLYPLRFPFSKGKVYELDTCEPCLGLNIVGSLDYVKEGVLSGLNGDIIGYVVRMDGSASHHQIVAIWSLPGQPLVDSKGKGKTVTLGVTVRVGGSVDNRDAIFRLQCDRPYGEFSLLQQGGHISYMNSPLVDTGVEIQFTQPRPQCPQDSEIAVLPWLLPDQTPGQWLHYTDRRVASVFNLHQTDLLQEVEIIYGLKDWQETYPREVPVLMRQAEVVLQPIQPRGEYARQTRGVLVWSPPIRFPGREWNGDYVLRKQAEHWLRVPALHHGWLRTPCRPQWVWKSEQRSQCPDYHLCVDNRDPFFRTIIEHFFNRTFTQNVVAGEFNPGPHLVSDRQTVVKMTVGGVAELVVGQEKQRLVYPDDVVAYEQPFQMSLDSVELRTVEFLQPNVHDYQKDGWLSLQSHNLLAPDGTVTVYKQSDFNLWQLLWKPDRGVLQRDEDGWDVVQAAKGGDYRDILDRPEVLPGGAGAVVDAVQQIAMLQVLPKAGLRLDPEEPLKFENQQCREVPLLGLGIPDPPGLSQFQVSPKSNWFFGNLSGFQANPTQVRMFNYTGQHLDDLFGLLPLVHGSGVGYLTPNMNMKLSGPGSYYQKRRRLVYRLTHVMSVLDPQGVVDGQDFYHEELPVPGAKGALLLKVQGLKDIQDGVVLNILGGQHVDDCQVDALGTYQLFVVVVDRFTPNLLKDGQVVQNVWELKASLNYGTLNSLYYNLVPYKQEGGRTLIFEQKIDNVVTDQFIHVPEYWELACNGDSRNVLEQSEVVAAVGDTVSTPTQGDAQGAILNILGGAVRENAVGVGAWVYQYPELDRVLCAKLNFQQHLTDLPYQNKKRFIQEELAEVRRDLALQADPSLAFKELAAKLQAQRRAENVEALEQMLQQLQLGDLLDGLVHILKQKVLKPQRGDVAQRVQEGLLELAQRMGGSAGDSVRLLQALRDLVQGEPGDYAHSPLTPAAATEPGELKGLLRARLQEVLQLVAEHGHPQYVPQCRDVWTDGEEIVRALAEKPKDAAPYVQKLLVPLLESPPPPQRQMRSEKPQAREPAPRMPEAAPPVAPAAPPPAAAPAAATPSPVSGPEGGQGPAASAAAPTPAAAGSGASMAALPVPSALRVPAVAGQQGEAGAAEAPAQGAQQGRSVPFLQLLPKDPPLQQQGERGTTAPKGQKVPQAQGLRSQGGQPQADPGQAPPGPARPTRPPGTDTQPEDFDMQPMPADPRYSQPPQQPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPAAGGAAPQPPPAQQPLQQPPAQGP',
        'name': 'EGFR kinase domain (fragment)',
        'category': 'Kinase target',
        'description': 'Target of Gefitinib in lung cancer',
        'length': 1000
    }
}


def get_all_small_molecule_names() -> list:
    """Get list of all small molecule names."""
    return list(SMALL_MOLECULES.keys())


def get_all_peptide_names() -> list:
    """Get list of all peptide names."""
    return list(PEPTIDE_DRUGS.keys())


def get_all_protein_names() -> list:
    """Get list of all protein biologic names."""
    return list(PROTEIN_BIOLOGICS.keys())


def get_small_molecule(name: str) -> dict:
    """Get small molecule data by name."""
    return SMALL_MOLECULES.get(name, None)


def get_peptide(name: str) -> dict:
    """Get peptide data by name."""
    return PEPTIDE_DRUGS.get(name, None)


def get_protein(name: str) -> dict:
    """Get protein biologic data by name."""
    return PROTEIN_BIOLOGICS.get(name, None)


def search_examples(query: str) -> dict:
    """
    Search all examples for partial name match.
    
    Args:
        query: Search query string
    
    Returns:
        Dictionary with matching examples by category
    """
    query_lower = query.lower()
    
    results = {
        'small_molecules': [],
        'peptides': [],
        'proteins': []
    }
    
    for name, data in SMALL_MOLECULES.items():
        if query_lower in name.lower() or query_lower in data['category'].lower():
            results['small_molecules'].append(name)
    
    for name, data in PEPTIDE_DRUGS.items():
        if query_lower in name.lower() or query_lower in data['category'].lower():
            results['peptides'].append(name)
    
    for name, data in PROTEIN_BIOLOGICS.items():
        if query_lower in name.lower() or query_lower in data['category'].lower():
            results['proteins'].append(name)
    
    return results
