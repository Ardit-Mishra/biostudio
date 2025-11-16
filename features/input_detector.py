"""
Intelligent Input Detection System

Automatically detects whether user input is a SMILES string, peptide sequence,
or protein sequence, and provides context-aware suggestions.

Author: Ardit Mishra
"""

import re
from typing import Dict, List, Tuple
from data.example_molecules import (
    SMALL_MOLECULES, PEPTIDE_DRUGS, PROTEIN_BIOLOGICS,
    search_examples
)


class InputDetector:
    """
    Intelligent system for detecting and classifying molecular input types.
    
    Distinguishes between:
    - SMILES strings (small molecules)
    - Peptide sequences (5-60 amino acids)
    - Protein sequences (>60 amino acids)
    """
    
    AMINO_ACIDS = set('ACDEFGHIKLMNPQRSTVWY')
    SMILES_CHARS = set('CNOPSFIBr()[]=#@+-0123456789clnos')
    
    def __init__(self):
        """Initialize input detector."""
        pass
    
    def detect_input_type(self, input_str: str) -> Dict[str, any]:
        """
        Detect what type of molecular input the user provided.
        
        Args:
            input_str: Raw user input
        
        Returns:
            Dictionary with detection results and suggestions
        """
        if not input_str or len(input_str.strip()) == 0:
            return {
                'type': 'empty',
                'confidence': 1.0,
                'suggestions': [],
                'message': 'No input provided'
            }
        
        cleaned = input_str.strip().replace(' ', '').replace('\n', '')
        
        if cleaned.startswith('>'):
            return self._detect_fasta(cleaned)
        
        upper_cleaned = cleaned.upper()
        
        has_amino_acids = all(c in self.AMINO_ACIDS for c in upper_cleaned if c.isalpha())
        has_smiles_chars = any(c in self.SMILES_CHARS for c in cleaned)
        
        if has_amino_acids and not has_smiles_chars:
            return self._detect_sequence(cleaned)
        elif has_smiles_chars:
            return self._detect_smiles(cleaned)
        else:
            return self._detect_name_search(cleaned)
    
    def _detect_smiles(self, input_str: str) -> Dict[str, any]:
        """Detect SMILES string and suggest examples."""
        confidence = 0.9 if any(c in '()[]=#' for c in input_str) else 0.7
        
        suggestions = [
            {'name': 'Ibuprofen', 'value': SMALL_MOLECULES['Ibuprofen']['smiles'], 'category': 'NSAID'},
            {'name': 'Aspirin', 'value': SMALL_MOLECULES['Aspirin']['smiles'], 'category': 'NSAID'},
            {'name': 'Imatinib', 'value': SMALL_MOLECULES['Imatinib']['smiles'], 'category': 'Kinase inhibitor'},
            {'name': 'Caffeine', 'value': SMALL_MOLECULES['Caffeine']['smiles'], 'category': 'Stimulant'},
            {'name': 'Montelukast', 'value': SMALL_MOLECULES['Montelukast']['smiles'], 'category': 'Leukotriene inhibitor'}
        ]
        
        return {
            'type': 'smiles',
            'confidence': confidence,
            'suggestions': suggestions,
            'message': 'SMILES string detected. Use Molecule Studio, ADME Navigator, or Drug-Likeness Deck.',
            'recommended_tools': ['Molecule Studio', 'ADME Navigator', 'Drug-Likeness Deck', 'Toxicity Radar']
        }
    
    def _detect_sequence(self, input_str: str) -> Dict[str, any]:
        """Detect protein/peptide sequence."""
        length = len(input_str)
        
        if length < 10:
            suggestions = [
                {'name': 'Octreotide', 'value': PEPTIDE_DRUGS['Octreotide']['sequence'], 'category': 'Peptide (8 AA)'},
                {'name': 'Leuprolide', 'value': PEPTIDE_DRUGS['Leuprolide']['sequence'], 'category': 'Peptide (9 AA)'}
            ]
            return {
                'type': 'peptide_small',
                'confidence': 0.8,
                'suggestions': suggestions,
                'message': f'Small peptide detected ({length} amino acids). Use Protein & Biologic Studio.',
                'recommended_tools': ['Protein & Biologic Studio']
            }
        
        elif length <= 60:
            suggestions = [
                {'name': 'Insulin B-chain', 'value': PEPTIDE_DRUGS['Insulin B-chain (fragment)']['sequence'], 'category': 'Peptide (30 AA)'},
                {'name': 'Semaglutide fragment', 'value': PEPTIDE_DRUGS['Semaglutide (fragment)']['sequence'], 'category': 'GLP-1 agonist (30 AA)'},
                {'name': 'Exenatide fragment', 'value': PEPTIDE_DRUGS['Exenatide (fragment)']['sequence'], 'category': 'GLP-1 agonist (39 AA)'},
                {'name': 'Glucagon', 'value': PEPTIDE_DRUGS['Glucagon']['sequence'], 'category': 'Peptide hormone (29 AA)'}
            ]
            return {
                'type': 'peptide_medium',
                'confidence': 0.9,
                'suggestions': suggestions,
                'message': f'Medium peptide detected ({length} amino acids). Use Protein & Biologic Studio.',
                'recommended_tools': ['Protein & Biologic Studio', 'Protein-Ligand Compatibility']
            }
        
        else:
            suggestions = [
                {'name': 'Interferon beta-1a', 'value': PROTEIN_BIOLOGICS['Interferon beta-1a (fragment)']['sequence'], 'category': 'Cytokine (166 AA)'},
                {'name': 'Erythropoietin', 'value': PROTEIN_BIOLOGICS['Erythropoietin (fragment)']['sequence'], 'category': 'Growth factor (166 AA)'},
                {'name': 'Human Growth Hormone', 'value': PROTEIN_BIOLOGICS['Human Growth Hormone (fragment)']['sequence'], 'category': 'Hormone (191 AA)'},
                {'name': 'BCR-ABL fragment', 'value': PROTEIN_BIOLOGICS['BCR-ABL (fragment)']['sequence'], 'category': 'Kinase target (161 AA)'}
            ]
            return {
                'type': 'protein',
                'confidence': 0.95,
                'suggestions': suggestions,
                'message': f'Protein sequence detected ({length} amino acids). Use Protein & Biologic Studio.',
                'recommended_tools': ['Protein & Biologic Studio', 'Protein-Ligand Compatibility']
            }
    
    def _detect_fasta(self, input_str: str) -> Dict[str, any]:
        """Detect FASTA format."""
        lines = input_str.split('\n')
        seq_lines = ''.join(lines[1:]).replace(' ', '').upper()
        length = len(seq_lines)
        
        suggestions = [
            {'name': 'Interferon beta-1a', 'value': f">Interferon beta-1a\n{PROTEIN_BIOLOGICS['Interferon beta-1a (fragment)']['sequence']}", 'category': 'Cytokine'},
            {'name': 'Erythropoietin', 'value': f">Erythropoietin\n{PROTEIN_BIOLOGICS['Erythropoietin (fragment)']['sequence']}", 'category': 'Growth factor'}
        ]
        
        return {
            'type': 'fasta',
            'confidence': 1.0,
            'suggestions': suggestions,
            'message': f'FASTA format detected ({length} amino acids). Use Protein & Biologic Studio.',
            'recommended_tools': ['Protein & Biologic Studio', 'Protein-Ligand Compatibility']
        }
    
    def _detect_name_search(self, input_str: str) -> Dict[str, any]:
        """Detect if user is typing a drug name."""
        results = search_examples(input_str)
        
        all_suggestions = []
        
        for name in results['small_molecules'][:3]:
            data = SMALL_MOLECULES[name]
            all_suggestions.append({
                'name': name,
                'value': data['smiles'],
                'category': f"Small molecule - {data['category']}"
            })
        
        for name in results['peptides'][:2]:
            data = PEPTIDE_DRUGS[name]
            all_suggestions.append({
                'name': name,
                'value': data['sequence'],
                'category': f"Peptide - {data['category']}"
            })
        
        for name in results['proteins'][:2]:
            data = PROTEIN_BIOLOGICS[name]
            all_suggestions.append({
                'name': name,
                'value': data['sequence'],
                'category': f"Protein - {data['category']}"
            })
        
        if len(all_suggestions) > 0:
            message = f"Found {len(all_suggestions)} matching examples. Select one or enter your own."
        else:
            message = "No matches found. Try entering SMILES or FASTA sequence."
        
        return {
            'type': 'name_search',
            'confidence': 0.6,
            'suggestions': all_suggestions,
            'message': message,
            'recommended_tools': []
        }
    
    def get_smart_suggestions(self, input_str: str, limit: int = 5) -> List[Dict]:
        """
        Get smart suggestions based on current input.
        
        Args:
            input_str: Current user input
            limit: Maximum number of suggestions
        
        Returns:
            List of suggestion dictionaries
        """
        detection = self.detect_input_type(input_str)
        return detection['suggestions'][:limit]
    
    def should_route_to_biologic_studio(self, input_str: str, molecular_weight: float = None) -> bool:
        """
        Determine if input should be routed to Biologic Studio.
        
        Args:
            input_str: User input
            molecular_weight: Calculated MW (if available)
        
        Returns:
            True if should use Biologic Studio
        """
        detection = self.detect_input_type(input_str)
        
        if detection['type'] in ['peptide_small', 'peptide_medium', 'protein', 'fasta']:
            return True
        
        if molecular_weight and molecular_weight > 1200:
            return True
        
        return False
