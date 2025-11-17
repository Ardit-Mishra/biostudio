import networkx as nx
from typing import Dict, List, Tuple, Optional
import pandas as pd
import json
from pyvis.network import Network
import tempfile


class BiomedicalKnowledgeGraph:
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self._initialize_graph()
    
    def _initialize_graph(self):
        compounds = [
            ('Imatinib', 'BCR-ABL', 'inhibits', 'Chronic Myeloid Leukemia'),
            ('Imatinib', 'PDGFR', 'inhibits', 'GIST'),
            ('Imatinib', 'KIT', 'inhibits', 'GIST'),
            ('Gefitinib', 'EGFR', 'inhibits', 'Non-small Cell Lung Cancer'),
            ('Erlotinib', 'EGFR', 'inhibits', 'Non-small Cell Lung Cancer'),
            ('Afatinib', 'EGFR', 'inhibits', 'Non-small Cell Lung Cancer'),
            ('Osimertinib', 'EGFR', 'inhibits', 'Non-small Cell Lung Cancer'),
            ('Sorafenib', 'VEGFR', 'inhibits', 'Renal Cell Carcinoma'),
            ('Sorafenib', 'RAF', 'inhibits', 'Hepatocellular Carcinoma'),
            ('Sorafenib', 'PDGFR', 'inhibits', 'Renal Cell Carcinoma'),
            ('Sunitinib', 'VEGFR', 'inhibits', 'Renal Cell Carcinoma'),
            ('Sunitinib', 'PDGFR', 'inhibits', 'Renal Cell Carcinoma'),
            ('Pazopanib', 'VEGFR', 'inhibits', 'Renal Cell Carcinoma'),
            ('Venetoclax', 'BCL-2', 'inhibits', 'Chronic Lymphocytic Leukemia'),
            ('Venetoclax', 'BCL-2', 'inhibits', 'Acute Myeloid Leukemia'),
            ('Upadacitinib', 'JAK1', 'inhibits', 'Rheumatoid Arthritis'),
            ('Tofacitinib', 'JAK1', 'inhibits', 'Rheumatoid Arthritis'),
            ('Tofacitinib', 'JAK3', 'inhibits', 'Rheumatoid Arthritis'),
            ('Baricitinib', 'JAK1', 'inhibits', 'Rheumatoid Arthritis'),
            ('Baricitinib', 'JAK2', 'inhibits', 'Rheumatoid Arthritis'),
            ('Rinvoq', 'JAK1', 'inhibits', 'Atopic Dermatitis'),
            ('Ibrutinib', 'BTK', 'inhibits', 'Mantle Cell Lymphoma'),
            ('Ibrutinib', 'BTK', 'inhibits', 'Chronic Lymphocytic Leukemia'),
            ('Acalabrutinib', 'BTK', 'inhibits', 'Mantle Cell Lymphoma'),
            ('Zanubrutinib', 'BTK', 'inhibits', 'Mantle Cell Lymphoma'),
            ('Adalimumab', 'TNF-alpha', 'inhibits', 'Rheumatoid Arthritis'),
            ('Adalimumab', 'TNF-alpha', 'inhibits', "Crohn's Disease"),
            ('Adalimumab', 'TNF-alpha', 'inhibits', 'Psoriasis'),
            ('Infliximab', 'TNF-alpha', 'inhibits', 'Rheumatoid Arthritis'),
            ('Infliximab', 'TNF-alpha', 'inhibits', "Crohn's Disease"),
            ('Etanercept', 'TNF-alpha', 'inhibits', 'Rheumatoid Arthritis'),
            ('Etanercept', 'TNF-alpha', 'inhibits', 'Psoriasis'),
            ('Pembrolizumab', 'PD-1', 'inhibits', 'Melanoma'),
            ('Pembrolizumab', 'PD-1', 'inhibits', 'Non-small Cell Lung Cancer'),
            ('Nivolumab', 'PD-1', 'inhibits', 'Melanoma'),
            ('Nivolumab', 'PD-1', 'inhibits', 'Renal Cell Carcinoma'),
            ('Atezolizumab', 'PD-L1', 'inhibits', 'Non-small Cell Lung Cancer'),
            ('Durvalumab', 'PD-L1', 'inhibits', 'Non-small Cell Lung Cancer'),
            ('Trastuzumab', 'HER2', 'inhibits', 'Breast Cancer'),
            ('Pertuzumab', 'HER2', 'inhibits', 'Breast Cancer'),
            ('Lapatinib', 'HER2', 'inhibits', 'Breast Cancer'),
            ('Lapatinib', 'EGFR', 'inhibits', 'Breast Cancer'),
            ('Bevacizumab', 'VEGF', 'inhibits', 'Colorectal Cancer'),
            ('Bevacizumab', 'VEGF', 'inhibits', 'Non-small Cell Lung Cancer'),
            ('Ramucirumab', 'VEGFR2', 'inhibits', 'Gastric Cancer'),
            ('Cetuximab', 'EGFR', 'inhibits', 'Colorectal Cancer'),
            ('Panitumumab', 'EGFR', 'inhibits', 'Colorectal Cancer'),
            ('Rituximab', 'CD20', 'inhibits', 'Non-Hodgkin Lymphoma'),
            ('Obinutuzumab', 'CD20', 'inhibits', 'Chronic Lymphocytic Leukemia'),
            ('Bortezomib', 'Proteasome', 'inhibits', 'Multiple Myeloma'),
            ('Carfilzomib', 'Proteasome', 'inhibits', 'Multiple Myeloma'),
            ('Lenalidomide', 'Cereblon', 'modulates', 'Multiple Myeloma'),
            ('Pomalidomide', 'Cereblon', 'modulates', 'Multiple Myeloma'),
            ('Dasatinib', 'BCR-ABL', 'inhibits', 'Chronic Myeloid Leukemia'),
            ('Dasatinib', 'SRC', 'inhibits', 'Chronic Myeloid Leukemia'),
            ('Nilotinib', 'BCR-ABL', 'inhibits', 'Chronic Myeloid Leukemia'),
            ('Bosutinib', 'BCR-ABL', 'inhibits', 'Chronic Myeloid Leukemia'),
            ('Ponatinib', 'BCR-ABL', 'inhibits', 'Chronic Myeloid Leukemia'),
            ('Ruxolitinib', 'JAK1', 'inhibits', 'Myelofibrosis'),
            ('Ruxolitinib', 'JAK2', 'inhibits', 'Myelofibrosis'),
            ('Fedratinib', 'JAK2', 'inhibits', 'Myelofibrosis'),
            ('Vemurafenib', 'BRAF', 'inhibits', 'Melanoma'),
            ('Dabrafenib', 'BRAF', 'inhibits', 'Melanoma'),
            ('Encorafenib', 'BRAF', 'inhibits', 'Melanoma'),
            ('Trametinib', 'MEK', 'inhibits', 'Melanoma'),
            ('Cobimetinib', 'MEK', 'inhibits', 'Melanoma'),
            ('Binimetinib', 'MEK', 'inhibits', 'Melanoma'),
            ('Crizotinib', 'ALK', 'inhibits', 'Non-small Cell Lung Cancer'),
            ('Alectinib', 'ALK', 'inhibits', 'Non-small Cell Lung Cancer'),
            ('Ceritinib', 'ALK', 'inhibits', 'Non-small Cell Lung Cancer'),
            ('Brigatinib', 'ALK', 'inhibits', 'Non-small Cell Lung Cancer'),
            ('Lorlatinib', 'ALK', 'inhibits', 'Non-small Cell Lung Cancer'),
            ('Olaparib', 'PARP', 'inhibits', 'Ovarian Cancer'),
            ('Olaparib', 'PARP', 'inhibits', 'Breast Cancer'),
            ('Rucaparib', 'PARP', 'inhibits', 'Ovarian Cancer'),
            ('Niraparib', 'PARP', 'inhibits', 'Ovarian Cancer'),
            ('Talazoparib', 'PARP', 'inhibits', 'Breast Cancer'),
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
            ('EGFR', 'PI3K/AKT Pathway', 'activates'),
            ('BCR-ABL', 'PI3K/AKT Pathway', 'activates'),
            ('BCR-ABL', 'MAPK Pathway', 'activates'),
            ('JAK1', 'STAT Signaling', 'activates'),
            ('JAK2', 'STAT Signaling', 'activates'),
            ('JAK3', 'STAT Signaling', 'activates'),
            ('TNF-alpha', 'NF-kB Pathway', 'activates'),
            ('TNF-alpha', 'MAPK Pathway', 'activates'),
            ('PD-1', 'T-cell Inhibition', 'regulates'),
            ('PD-L1', 'T-cell Inhibition', 'regulates'),
            ('HER2', 'PI3K/AKT Pathway', 'activates'),
            ('HER2', 'MAPK Pathway', 'activates'),
            ('VEGFR', 'Angiogenesis', 'promotes'),
            ('VEGF', 'Angiogenesis', 'promotes'),
            ('BRAF', 'MAPK Pathway', 'activates'),
            ('MEK', 'MAPK Pathway', 'activates'),
            ('ALK', 'PI3K/AKT Pathway', 'activates'),
            ('ALK', 'MAPK Pathway', 'activates'),
            ('RAF', 'MAPK Pathway', 'activates'),
            ('SRC', 'Cell Proliferation', 'promotes'),
            ('BTK', 'B-cell Signaling', 'activates'),
            ('CD20', 'B-cell Survival', 'promotes'),
            ('PARP', 'DNA Repair', 'facilitates'),
            ('Proteasome', 'Protein Degradation', 'catalyzes'),
            ('Cereblon', 'Protein Degradation', 'regulates'),
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
    
    def create_interactive_visualization(self, 
                                         filter_types: Optional[List[str]] = None,
                                         height: str = "700px") -> str:
        net = Network(height=height, width="100%", bgcolor="#ffffff", font_color="black")
        
        net.barnes_hut(
            gravity=-80000,
            central_gravity=0.3,
            spring_length=250,
            spring_strength=0.001,
            damping=0.09,
            overlap=0
        )
        
        color_map = {
            'compound': '#3498db',
            'target': '#2ecc71',
            'disease': '#e74c3c',
            'pathway': '#9b59b6'
        }
        
        for node, data in self.graph.nodes(data=True):
            node_type = data.get('node_type', 'unknown')
            
            if filter_types and node_type not in filter_types:
                continue
            
            color = color_map.get(node_type, '#95a5a6')
            
            degree = self.graph.degree(node)
            size = 10 + (degree * 3)
            
            title = f"<b>{node}</b><br>Type: {data.get('category', 'Unknown')}<br>Connections: {degree}"
            
            net.add_node(
                node,
                label=node,
                color=color,
                size=size,
                title=title,
                shape='dot'
            )
        
        for source, target, data in self.graph.edges(data=True):
            source_type = self.graph.nodes[source].get('node_type', 'unknown')
            target_type = self.graph.nodes[target].get('node_type', 'unknown')
            
            if filter_types and (source_type not in filter_types or target_type not in filter_types):
                continue
            
            relationship = data.get('relationship', 'related')
            edge_type = data.get('edge_type', 'unknown')
            
            net.add_edge(
                source,
                target,
                title=f"{relationship}",
                arrows='to',
                smooth={'type': 'continuous'}
            )
        
        net.toggle_physics(True)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.html') as f:
            net.save_graph(f.name)
            return f.name
    
    def get_centrality_metrics(self) -> Dict[str, Dict]:
        degree_centrality = nx.degree_centrality(self.graph)
        betweenness_centrality = nx.betweenness_centrality(self.graph)
        
        try:
            closeness_centrality = nx.closeness_centrality(self.graph)
        except:
            closeness_centrality = {}
        
        metrics = {}
        for node in self.graph.nodes():
            metrics[node] = {
                'degree': degree_centrality.get(node, 0),
                'betweenness': betweenness_centrality.get(node, 0),
                'closeness': closeness_centrality.get(node, 0),
                'node_type': self.graph.nodes[node].get('node_type', 'unknown')
            }
        
        return metrics
    
    def get_top_central_nodes(self, metric: str = 'degree', top_n: int = 10) -> List[Tuple[str, float]]:
        metrics = self.get_centrality_metrics()
        
        if metric not in ['degree', 'betweenness', 'closeness']:
            metric = 'degree'
        
        sorted_nodes = sorted(
            metrics.items(),
            key=lambda x: x[1][metric],
            reverse=True
        )
        
        return [(node, data[metric]) for node, data in sorted_nodes[:top_n]]
    
    def find_shortest_path(self, source: str, target: str) -> Optional[List[str]]:
        if source not in self.graph or target not in self.graph:
            return None
        
        try:
            path = nx.shortest_path(self.graph.to_undirected(), source, target)
            return path
        except nx.NetworkXNoPath:
            return None
    
    def predict_drug_repurposing(self, drug_name: str, top_n: int = 5) -> List[Dict]:
        if drug_name not in self.graph:
            return []
        
        current_targets = set(self.get_drug_targets(drug_name))
        current_diseases = set(self.get_drug_indications(drug_name))
        
        candidates = []
        
        all_diseases = [n for n, d in self.graph.nodes(data=True) 
                       if d.get('node_type') == 'disease']
        
        for disease in all_diseases:
            if disease in current_diseases:
                continue
            
            disease_targets = set([n for n in self.graph.predecessors(disease) 
                                  if self.graph.nodes[n].get('node_type') == 'target'])
            
            shared_targets = current_targets.intersection(disease_targets)
            
            if not shared_targets:
                continue
            
            try:
                path = self.find_shortest_path(drug_name, disease)
                path_length = len(path) if path else float('inf')
            except:
                path_length = float('inf')
            
            score = len(shared_targets) * 10 - path_length
            
            candidates.append({
                'disease': disease,
                'shared_targets': list(shared_targets),
                'num_shared_targets': len(shared_targets),
                'path_length': path_length,
                'repurposing_score': score
            })
        
        candidates.sort(key=lambda x: x['repurposing_score'], reverse=True)
        return candidates[:top_n]
    
    def export_to_json(self) -> str:
        nodes, edges = self.export_for_visualization()
        
        data = {
            'nodes': nodes,
            'edges': edges,
            'statistics': self.get_graph_statistics(),
            'metadata': {
                'graph_type': 'Biomedical Knowledge Graph',
                'node_types': ['compound', 'target', 'disease', 'pathway'],
                'edge_types': ['drug-target', 'target-disease', 'drug-disease', 'target-pathway']
            }
        }
        
        return json.dumps(data, indent=2)
    
    def export_to_csv(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        nodes_data = []
        for node, data in self.graph.nodes(data=True):
            nodes_data.append({
                'node_id': node,
                'node_type': data.get('node_type', 'unknown'),
                'category': data.get('category', 'Unknown'),
                'degree': self.graph.degree(node)
            })
        
        edges_data = []
        for source, target, data in self.graph.edges(data=True):
            edges_data.append({
                'source': source,
                'target': target,
                'relationship': data.get('relationship', 'related'),
                'edge_type': data.get('edge_type', 'unknown')
            })
        
        nodes_df = pd.DataFrame(nodes_data)
        edges_df = pd.DataFrame(edges_data)
        
        return nodes_df, edges_df
    
    def export_to_graphml(self) -> str:
        from io import BytesIO
        
        buffer = BytesIO()
        nx.write_graphml(self.graph, buffer)
        return buffer.getvalue().decode('utf-8')
    
    def get_disease_relationships(self, disease_name: str) -> Dict:
        if disease_name not in self.graph:
            return {'error': 'Disease not found in knowledge graph'}
        
        drugs = [n for n in self.graph.predecessors(disease_name) 
                if self.graph.nodes[n].get('node_type') == 'compound']
        
        targets = [n for n in self.graph.predecessors(disease_name) 
                  if self.graph.nodes[n].get('node_type') == 'target']
        
        pathways = []
        for target in targets:
            target_pathways = [n for n in self.graph.successors(target) 
                             if self.graph.nodes[n].get('node_type') == 'pathway']
            pathways.extend(target_pathways)
        
        return {
            'Disease': disease_name,
            'Approved_Drugs': drugs,
            'Associated_Targets': targets,
            'Involved_Pathways': list(set(pathways)),
            'Total_Drugs': len(drugs),
            'Total_Targets': len(targets)
        }
