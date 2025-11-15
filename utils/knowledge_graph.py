import networkx as nx
from typing import Dict, List, Tuple
import pandas as pd


class BiomedicalKnowledgeGraph:
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self._initialize_graph()
    
    def _initialize_graph(self):
        compounds = [
            ('Imatinib', 'BCR-ABL', 'inhibits', 'Chronic Myeloid Leukemia'),
            ('Imatinib', 'PDGFR', 'inhibits', 'GIST'),
            ('Gefitinib', 'EGFR', 'inhibits', 'Non-small Cell Lung Cancer'),
            ('Sorafenib', 'VEGFR', 'inhibits', 'Renal Cell Carcinoma'),
            ('Sorafenib', 'RAF', 'inhibits', 'Hepatocellular Carcinoma'),
            ('Venetoclax', 'BCL-2', 'inhibits', 'Chronic Lymphocytic Leukemia'),
            ('Upadacitinib', 'JAK1', 'inhibits', 'Rheumatoid Arthritis'),
            ('Rinvoq', 'JAK1', 'inhibits', 'Atopic Dermatitis'),
            ('Ibrutinib', 'BTK', 'inhibits', 'Mantle Cell Lymphoma'),
            ('Adalimumab', 'TNF-alpha', 'inhibits', 'Rheumatoid Arthritis'),
            ('Adalimumab', 'TNF-alpha', 'inhibits', "Crohn's Disease"),
        ]
        
        for compound, target, relationship, disease in compounds:
            self.graph.add_node(compound, node_type='compound', category='Drug')
            self.graph.add_node(target, node_type='target', category='Protein')
            self.graph.add_node(disease, node_type='disease', category='Disease')
            
            self.graph.add_edge(compound, target, relationship=relationship, edge_type='drug-target')
            self.graph.add_edge(target, disease, relationship='associated_with', edge_type='target-disease')
            self.graph.add_edge(compound, disease, relationship='treats', edge_type='drug-disease')
        
        pathways = [
            ('EGFR', 'MAPK Pathway', 'activates'),
            ('BCR-ABL', 'PI3K/AKT Pathway', 'activates'),
            ('JAK1', 'STAT Signaling', 'activates'),
            ('TNF-alpha', 'NF-kB Pathway', 'activates'),
        ]
        
        for target, pathway, relationship in pathways:
            self.graph.add_node(pathway, node_type='pathway', category='Biological Pathway')
            if target in self.graph.nodes:
                self.graph.add_edge(target, pathway, relationship=relationship, edge_type='target-pathway')
    
    def get_drug_targets(self, drug_name: str) -> List[str]:
        if drug_name not in self.graph:
            return []
        return [n for n in self.graph.successors(drug_name) 
                if self.graph.nodes[n].get('node_type') == 'target']
    
    def get_target_diseases(self, target_name: str) -> List[str]:
        if target_name not in self.graph:
            return []
        return [n for n in self.graph.successors(target_name) 
                if self.graph.nodes[n].get('node_type') == 'disease']
    
    def get_drug_indications(self, drug_name: str) -> List[str]:
        if drug_name not in self.graph:
            return []
        return [n for n in self.graph.successors(drug_name) 
                if self.graph.nodes[n].get('node_type') == 'disease']
    
    def find_similar_drugs(self, target_name: str) -> List[str]:
        if target_name not in self.graph:
            return []
        
        drugs = [n for n in self.graph.predecessors(target_name) 
                 if self.graph.nodes[n].get('node_type') == 'compound']
        return drugs
    
    def get_mechanism_of_action(self, drug_name: str) -> Dict:
        if drug_name not in self.graph:
            return {'error': 'Drug not found in knowledge graph'}
        
        targets = self.get_drug_targets(drug_name)
        pathways = []
        diseases = self.get_drug_indications(drug_name)
        
        for target in targets:
            target_pathways = [n for n in self.graph.successors(target) 
                             if self.graph.nodes[n].get('node_type') == 'pathway']
            pathways.extend(target_pathways)
        
        return {
            'Drug': drug_name,
            'Targets': targets,
            'Pathways': list(set(pathways)),
            'Indications': diseases
        }
    
    def get_graph_statistics(self) -> Dict:
        compounds = [n for n, d in self.graph.nodes(data=True) if d.get('node_type') == 'compound']
        targets = [n for n, d in self.graph.nodes(data=True) if d.get('node_type') == 'target']
        diseases = [n for n, d in self.graph.nodes(data=True) if d.get('node_type') == 'disease']
        pathways = [n for n, d in self.graph.nodes(data=True) if d.get('node_type') == 'pathway']
        
        return {
            'Total Nodes': self.graph.number_of_nodes(),
            'Total Edges': self.graph.number_of_edges(),
            'Compounds': len(compounds),
            'Targets': len(targets),
            'Diseases': len(diseases),
            'Pathways': len(pathways),
            'Avg Degree': round(sum(dict(self.graph.degree()).values()) / self.graph.number_of_nodes(), 2)
        }
    
    def export_for_visualization(self) -> Tuple[List[Dict], List[Dict]]:
        nodes = []
        for node, data in self.graph.nodes(data=True):
            nodes.append({
                'id': node,
                'label': node,
                'type': data.get('node_type', 'unknown'),
                'category': data.get('category', 'Unknown')
            })
        
        edges = []
        for source, target, data in self.graph.edges(data=True):
            edges.append({
                'from': source,
                'to': target,
                'relationship': data.get('relationship', 'related'),
                'type': data.get('edge_type', 'unknown')
            })
        
        return nodes, edges
    
    def add_custom_drug_target(self, drug: str, target: str, disease: str):
        self.graph.add_node(drug, node_type='compound', category='Drug')
        self.graph.add_node(target, node_type='target', category='Protein')
        self.graph.add_node(disease, node_type='disease', category='Disease')
        
        self.graph.add_edge(drug, target, relationship='inhibits', edge_type='drug-target')
        self.graph.add_edge(target, disease, relationship='associated_with', edge_type='target-disease')
        self.graph.add_edge(drug, disease, relationship='treats', edge_type='drug-disease')
