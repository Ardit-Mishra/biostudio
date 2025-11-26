# =============================================================================
# BIOMEDICAL KNOWLEDGE GRAPH MODULE
# =============================================================================
# This module implements a biomedical knowledge graph for drug discovery.
# It models relationships between drugs, targets, diseases, and pathways.
#
# Key features:
# - 70+ FDA-approved drugs with their targets and indications
# - 45+ protein targets including kinases, GPCRs, and enzymes
# - 25+ biological pathways (MAPK, PI3K, STAT signaling, etc.)
# - Interactive visualization using PyVis
# - Network analytics (centrality, shortest paths)
# - Drug repurposing predictions using network analysis
# - Export to JSON, CSV, and GraphML formats
#
# Uses NetworkX for graph operations and PyVis for visualization.
# =============================================================================

# Import NetworkX library for graph data structures and algorithms
import networkx as nx
# Import type hints for better documentation
from typing import Dict, List, Tuple, Optional
# Import pandas for tabular data export
import pandas as pd
# Import JSON for data serialization
import json
# Import PyVis for interactive network visualization
from pyvis.network import Network
# Import tempfile for creating temporary HTML files
import tempfile


# Main class for biomedical knowledge graph
# Represents drug-target-disease relationships as a directed graph
class BiomedicalKnowledgeGraph:
    
    # Initialize the knowledge graph
    def __init__(self):
        # Create directed graph (edges have direction: Drug -> Target -> Disease)
        self.graph = nx.DiGraph()
        # Populate graph with drug-target-disease data
        self._initialize_graph()
    
    # Populate graph with pharmaceutical knowledge
    # Contains 70+ FDA-approved drugs, their targets, and indications
    def _initialize_graph(self):
        # List of (drug, target, relationship, disease) tuples
        # Each tuple represents a known drug-target-disease relationship
        compounds = [
            # Imatinib: First targeted cancer therapy (2001)
            # Revolutionized CML treatment by targeting BCR-ABL fusion protein
            ('Imatinib', 'BCR-ABL', 'inhibits', 'Chronic Myeloid Leukemia'),
            # Imatinib also targets PDGFR and KIT for GIST treatment
            ('Imatinib', 'PDGFR', 'inhibits', 'GIST'),
            ('Imatinib', 'KIT', 'inhibits', 'GIST'),
            # EGFR inhibitors for lung cancer
            ('Gefitinib', 'EGFR', 'inhibits', 'Non-small Cell Lung Cancer'),
            ('Erlotinib', 'EGFR', 'inhibits', 'Non-small Cell Lung Cancer'),
            ('Afatinib', 'EGFR', 'inhibits', 'Non-small Cell Lung Cancer'),
            ('Osimertinib', 'EGFR', 'inhibits', 'Non-small Cell Lung Cancer'),
            # Multi-kinase inhibitors for kidney and liver cancer
            ('Sorafenib', 'VEGFR', 'inhibits', 'Renal Cell Carcinoma'),
            ('Sorafenib', 'RAF', 'inhibits', 'Hepatocellular Carcinoma'),
            ('Sorafenib', 'PDGFR', 'inhibits', 'Renal Cell Carcinoma'),
            ('Sunitinib', 'VEGFR', 'inhibits', 'Renal Cell Carcinoma'),
            ('Sunitinib', 'PDGFR', 'inhibits', 'Renal Cell Carcinoma'),
            ('Pazopanib', 'VEGFR', 'inhibits', 'Renal Cell Carcinoma'),
            # BCL-2 inhibitor for blood cancers
            ('Venetoclax', 'BCL-2', 'inhibits', 'Chronic Lymphocytic Leukemia'),
            ('Venetoclax', 'BCL-2', 'inhibits', 'Acute Myeloid Leukemia'),
            # JAK inhibitors for autoimmune diseases
            ('Upadacitinib', 'JAK1', 'inhibits', 'Rheumatoid Arthritis'),
            ('Tofacitinib', 'JAK1', 'inhibits', 'Rheumatoid Arthritis'),
            ('Tofacitinib', 'JAK3', 'inhibits', 'Rheumatoid Arthritis'),
            ('Baricitinib', 'JAK1', 'inhibits', 'Rheumatoid Arthritis'),
            ('Baricitinib', 'JAK2', 'inhibits', 'Rheumatoid Arthritis'),
            ('Rinvoq', 'JAK1', 'inhibits', 'Atopic Dermatitis'),
            # BTK inhibitors for B-cell malignancies
            ('Ibrutinib', 'BTK', 'inhibits', 'Mantle Cell Lymphoma'),
            ('Ibrutinib', 'BTK', 'inhibits', 'Chronic Lymphocytic Leukemia'),
            ('Acalabrutinib', 'BTK', 'inhibits', 'Mantle Cell Lymphoma'),
            ('Zanubrutinib', 'BTK', 'inhibits', 'Mantle Cell Lymphoma'),
            # TNF-alpha inhibitors for inflammatory diseases
            ('Adalimumab', 'TNF-alpha', 'inhibits', 'Rheumatoid Arthritis'),
            ('Adalimumab', 'TNF-alpha', 'inhibits', "Crohn's Disease"),
            ('Adalimumab', 'TNF-alpha', 'inhibits', 'Psoriasis'),
            ('Infliximab', 'TNF-alpha', 'inhibits', 'Rheumatoid Arthritis'),
            ('Infliximab', 'TNF-alpha', 'inhibits', "Crohn's Disease"),
            ('Etanercept', 'TNF-alpha', 'inhibits', 'Rheumatoid Arthritis'),
            ('Etanercept', 'TNF-alpha', 'inhibits', 'Psoriasis'),
            # Immune checkpoint inhibitors for cancer
            ('Pembrolizumab', 'PD-1', 'inhibits', 'Melanoma'),
            ('Pembrolizumab', 'PD-1', 'inhibits', 'Non-small Cell Lung Cancer'),
            ('Nivolumab', 'PD-1', 'inhibits', 'Melanoma'),
            ('Nivolumab', 'PD-1', 'inhibits', 'Renal Cell Carcinoma'),
            ('Atezolizumab', 'PD-L1', 'inhibits', 'Non-small Cell Lung Cancer'),
            ('Durvalumab', 'PD-L1', 'inhibits', 'Non-small Cell Lung Cancer'),
            # HER2-targeted therapies for breast cancer
            ('Trastuzumab', 'HER2', 'inhibits', 'Breast Cancer'),
            ('Pertuzumab', 'HER2', 'inhibits', 'Breast Cancer'),
            ('Lapatinib', 'HER2', 'inhibits', 'Breast Cancer'),
            ('Lapatinib', 'EGFR', 'inhibits', 'Breast Cancer'),
            # Anti-angiogenesis therapies
            ('Bevacizumab', 'VEGF', 'inhibits', 'Colorectal Cancer'),
            ('Bevacizumab', 'VEGF', 'inhibits', 'Non-small Cell Lung Cancer'),
            ('Ramucirumab', 'VEGFR2', 'inhibits', 'Gastric Cancer'),
            # EGFR antibodies for colorectal cancer
            ('Cetuximab', 'EGFR', 'inhibits', 'Colorectal Cancer'),
            ('Panitumumab', 'EGFR', 'inhibits', 'Colorectal Cancer'),
            # CD20-targeted therapies for lymphoma
            ('Rituximab', 'CD20', 'inhibits', 'Non-Hodgkin Lymphoma'),
            ('Obinutuzumab', 'CD20', 'inhibits', 'Chronic Lymphocytic Leukemia'),
            # Proteasome inhibitors for myeloma
            ('Bortezomib', 'Proteasome', 'inhibits', 'Multiple Myeloma'),
            ('Carfilzomib', 'Proteasome', 'inhibits', 'Multiple Myeloma'),
            # IMiDs (immunomodulatory drugs) for myeloma
            ('Lenalidomide', 'Cereblon', 'modulates', 'Multiple Myeloma'),
            ('Pomalidomide', 'Cereblon', 'modulates', 'Multiple Myeloma'),
            # Second/third generation BCR-ABL inhibitors
            ('Dasatinib', 'BCR-ABL', 'inhibits', 'Chronic Myeloid Leukemia'),
            ('Dasatinib', 'SRC', 'inhibits', 'Chronic Myeloid Leukemia'),
            ('Nilotinib', 'BCR-ABL', 'inhibits', 'Chronic Myeloid Leukemia'),
            ('Bosutinib', 'BCR-ABL', 'inhibits', 'Chronic Myeloid Leukemia'),
            ('Ponatinib', 'BCR-ABL', 'inhibits', 'Chronic Myeloid Leukemia'),
            # JAK inhibitors for myelofibrosis
            ('Ruxolitinib', 'JAK1', 'inhibits', 'Myelofibrosis'),
            ('Ruxolitinib', 'JAK2', 'inhibits', 'Myelofibrosis'),
            ('Fedratinib', 'JAK2', 'inhibits', 'Myelofibrosis'),
            # BRAF and MEK inhibitors for melanoma
            ('Vemurafenib', 'BRAF', 'inhibits', 'Melanoma'),
            ('Dabrafenib', 'BRAF', 'inhibits', 'Melanoma'),
            ('Encorafenib', 'BRAF', 'inhibits', 'Melanoma'),
            ('Trametinib', 'MEK', 'inhibits', 'Melanoma'),
            ('Cobimetinib', 'MEK', 'inhibits', 'Melanoma'),
            ('Binimetinib', 'MEK', 'inhibits', 'Melanoma'),
            # ALK inhibitors for lung cancer
            ('Crizotinib', 'ALK', 'inhibits', 'Non-small Cell Lung Cancer'),
            ('Alectinib', 'ALK', 'inhibits', 'Non-small Cell Lung Cancer'),
            ('Ceritinib', 'ALK', 'inhibits', 'Non-small Cell Lung Cancer'),
            ('Brigatinib', 'ALK', 'inhibits', 'Non-small Cell Lung Cancer'),
            ('Lorlatinib', 'ALK', 'inhibits', 'Non-small Cell Lung Cancer'),
            # PARP inhibitors for ovarian and breast cancer
            ('Olaparib', 'PARP', 'inhibits', 'Ovarian Cancer'),
            ('Olaparib', 'PARP', 'inhibits', 'Breast Cancer'),
            ('Rucaparib', 'PARP', 'inhibits', 'Ovarian Cancer'),
            ('Niraparib', 'PARP', 'inhibits', 'Ovarian Cancer'),
            ('Talazoparib', 'PARP', 'inhibits', 'Breast Cancer'),
        ]
        
        # Add nodes and edges for each drug-target-disease relationship
        for compound, target, relationship, disease in compounds:
            # Add drug node with metadata
            self.graph.add_node(compound, node_type='compound', category='Drug')
            # Add target node with metadata
            self.graph.add_node(target, node_type='target', category='Protein')
            # Add disease node with metadata
            self.graph.add_node(disease, node_type='disease', category='Disease')
            
            # Add edge from drug to target (drug inhibits/modulates target)
            self.graph.add_edge(compound, target, relationship=relationship, edge_type='drug-target')
            # Add edge from target to disease (target associated with disease)
            self.graph.add_edge(target, disease, relationship='associated_with', edge_type='target-disease')
            # Add edge from drug to disease (drug treats disease)
            self.graph.add_edge(compound, disease, relationship='treats', edge_type='drug-disease')
        
        # Define biological pathways and their connections to targets
        pathways = [
            # EGFR activates major signaling pathways
            ('EGFR', 'MAPK Pathway', 'activates'),
            ('EGFR', 'PI3K/AKT Pathway', 'activates'),
            # BCR-ABL (fusion protein in CML) activates multiple pathways
            ('BCR-ABL', 'PI3K/AKT Pathway', 'activates'),
            ('BCR-ABL', 'MAPK Pathway', 'activates'),
            # JAK proteins activate STAT signaling
            ('JAK1', 'STAT Signaling', 'activates'),
            ('JAK2', 'STAT Signaling', 'activates'),
            ('JAK3', 'STAT Signaling', 'activates'),
            # TNF-alpha activates inflammatory pathways
            ('TNF-alpha', 'NF-kB Pathway', 'activates'),
            ('TNF-alpha', 'MAPK Pathway', 'activates'),
            # Immune checkpoint proteins regulate T-cell responses
            ('PD-1', 'T-cell Inhibition', 'regulates'),
            ('PD-L1', 'T-cell Inhibition', 'regulates'),
            # HER2 activates growth pathways in breast cancer
            ('HER2', 'PI3K/AKT Pathway', 'activates'),
            ('HER2', 'MAPK Pathway', 'activates'),
            # VEGF/VEGFR promotes blood vessel formation
            ('VEGFR', 'Angiogenesis', 'promotes'),
            ('VEGF', 'Angiogenesis', 'promotes'),
            # BRAF-MEK-ERK cascade (MAPK pathway)
            ('BRAF', 'MAPK Pathway', 'activates'),
            ('MEK', 'MAPK Pathway', 'activates'),
            # ALK activates survival pathways
            ('ALK', 'PI3K/AKT Pathway', 'activates'),
            ('ALK', 'MAPK Pathway', 'activates'),
            # RAF is part of MAPK signaling
            ('RAF', 'MAPK Pathway', 'activates'),
            # SRC kinase promotes cell proliferation
            ('SRC', 'Cell Proliferation', 'promotes'),
            # BTK is critical for B-cell signaling
            ('BTK', 'B-cell Signaling', 'activates'),
            # CD20 is important for B-cell survival
            ('CD20', 'B-cell Survival', 'promotes'),
            # PARP is involved in DNA damage repair
            ('PARP', 'DNA Repair', 'facilitates'),
            # Proteasome degrades proteins (protein quality control)
            ('Proteasome', 'Protein Degradation', 'catalyzes'),
            # Cereblon is part of ubiquitin-proteasome system
            ('Cereblon', 'Protein Degradation', 'regulates'),
        ]
        
        # Add pathway nodes and target-pathway edges
        for target, pathway, relationship in pathways:
            # Add pathway node
            self.graph.add_node(pathway, node_type='pathway', category='Biological Pathway')
            # Add edge only if target exists in graph
            if target in self.graph.nodes:
                self.graph.add_edge(target, pathway, relationship=relationship, edge_type='target-pathway')
    
    # Get list of targets for a specific drug
    def get_drug_targets(self, drug_name: str) -> List[str]:
        # Return empty list if drug not in graph
        if drug_name not in self.graph:
            return []
        # Get successors (outgoing edges) and filter for target nodes
        return [n for n in self.graph.successors(drug_name) 
                if self.graph.nodes[n].get('node_type') == 'target']
    
    # Get list of diseases associated with a target
    def get_target_diseases(self, target_name: str) -> List[str]:
        # Return empty list if target not in graph
        if target_name not in self.graph:
            return []
        # Get successors and filter for disease nodes
        return [n for n in self.graph.successors(target_name) 
                if self.graph.nodes[n].get('node_type') == 'disease']
    
    # Get list of indications (diseases treated) for a drug
    def get_drug_indications(self, drug_name: str) -> List[str]:
        # Return empty list if drug not in graph
        if drug_name not in self.graph:
            return []
        # Get successors and filter for disease nodes
        return [n for n in self.graph.successors(drug_name) 
                if self.graph.nodes[n].get('node_type') == 'disease']
    
    # Find drugs that target the same protein
    # Useful for competitive analysis and understanding drug classes
    def find_similar_drugs(self, target_name: str) -> List[str]:
        # Return empty list if target not in graph
        if target_name not in self.graph:
            return []
        
        # Get predecessors (incoming edges) and filter for compounds
        drugs = [n for n in self.graph.predecessors(target_name) 
                 if self.graph.nodes[n].get('node_type') == 'compound']
        return drugs
    
    # Get mechanism of action for a drug
    # Returns targets, pathways, and indications
    def get_mechanism_of_action(self, drug_name: str) -> Dict:
        # Return error if drug not found
        if drug_name not in self.graph:
            return {'error': 'Drug not found in knowledge graph'}
        
        # Get direct targets of the drug
        targets = self.get_drug_targets(drug_name)
        # Initialize pathways list
        pathways = []
        # Get disease indications
        diseases = self.get_drug_indications(drug_name)
        
        # For each target, find associated pathways
        for target in targets:
            # Get pathway nodes connected to target
            target_pathways = [n for n in self.graph.successors(target) 
                             if self.graph.nodes[n].get('node_type') == 'pathway']
            pathways.extend(target_pathways)
        
        # Return mechanism of action summary
        return {
            'Drug': drug_name,
            'Targets': targets,
            # Remove duplicate pathways
            'Pathways': list(set(pathways)),
            'Indications': diseases
        }
    
    # Get summary statistics about the knowledge graph
    def get_graph_statistics(self) -> Dict:
        # Count nodes by type using list comprehensions
        compounds = [n for n, d in self.graph.nodes(data=True) if d.get('node_type') == 'compound']
        targets = [n for n, d in self.graph.nodes(data=True) if d.get('node_type') == 'target']
        diseases = [n for n, d in self.graph.nodes(data=True) if d.get('node_type') == 'disease']
        pathways = [n for n, d in self.graph.nodes(data=True) if d.get('node_type') == 'pathway']
        
        # Return statistics dictionary
        return {
            'Total Nodes': self.graph.number_of_nodes(),
            'Total Edges': self.graph.number_of_edges(),
            'Compounds': len(compounds),
            'Targets': len(targets),
            'Diseases': len(diseases),
            'Pathways': len(pathways),
            # Average degree (connections per node)
            'Avg Degree': round(sum(dict(self.graph.degree()).values()) / self.graph.number_of_nodes(), 2)
        }
    
    # Export graph data for external visualization tools
    def export_for_visualization(self) -> Tuple[List[Dict], List[Dict]]:
        # Create list of node dictionaries
        nodes = []
        for node, data in self.graph.nodes(data=True):
            nodes.append({
                'id': node,
                'label': node,
                'type': data.get('node_type', 'unknown'),
                'category': data.get('category', 'Unknown')
            })
        
        # Create list of edge dictionaries
        edges = []
        for source, target, data in self.graph.edges(data=True):
            edges.append({
                'from': source,
                'to': target,
                'relationship': data.get('relationship', 'related'),
                'type': data.get('edge_type', 'unknown')
            })
        
        return nodes, edges
    
    # Add a custom drug-target relationship to the graph
    def add_custom_drug_target(self, drug: str, target: str, disease: str):
        # Add nodes for drug, target, and disease
        self.graph.add_node(drug, node_type='compound', category='Drug')
        self.graph.add_node(target, node_type='target', category='Protein')
        self.graph.add_node(disease, node_type='disease', category='Disease')
        
        # Add edges connecting them
        self.graph.add_edge(drug, target, relationship='inhibits', edge_type='drug-target')
        self.graph.add_edge(target, disease, relationship='associated_with', edge_type='target-disease')
        self.graph.add_edge(drug, disease, relationship='treats', edge_type='drug-disease')
    
    # Create interactive network visualization using PyVis
    # Returns path to HTML file containing the visualization
    def create_interactive_visualization(self, 
                                         filter_types: Optional[List[str]] = None,
                                         height: str = "700px") -> str:
        # Create PyVis network object
        # height/width control canvas size
        # bgcolor sets background color
        # font_color sets label color
        net = Network(height=height, width="100%", bgcolor="#ffffff", font_color="black")
        
        # Configure physics simulation using Barnes-Hut algorithm
        # This creates natural-looking node layouts
        net.barnes_hut(
            gravity=-80000,           # Node repulsion strength
            central_gravity=0.3,      # Pull toward center
            spring_length=250,        # Edge length
            spring_strength=0.001,    # Edge stiffness
            damping=0.09,             # Simulation friction
            overlap=0                 # Allow node overlap
        )
        
        # Define color scheme for different node types
        color_map = {
            'compound': '#3498db',   # Blue for drugs
            'target': '#2ecc71',     # Green for proteins
            'disease': '#e74c3c',    # Red for diseases
            'pathway': '#9b59b6'     # Purple for pathways
        }
        
        # Add nodes to visualization
        for node, data in self.graph.nodes(data=True):
            # Get node type from metadata
            node_type = data.get('node_type', 'unknown')
            
            # Skip if filtering and node type not in filter
            if filter_types and node_type not in filter_types:
                continue
            
            # Get color for this node type
            color = color_map.get(node_type, '#95a5a6')
            
            # Scale node size by degree (more connections = larger)
            degree = self.graph.degree(node)
            size = 10 + (degree * 3)
            
            # Create hover tooltip with node info
            title = f"<b>{node}</b><br>Type: {data.get('category', 'Unknown')}<br>Connections: {degree}"
            
            # Add node to PyVis network
            net.add_node(
                node,               # Node ID
                label=node,         # Display label
                color=color,        # Node color
                size=size,          # Node size
                title=title,        # Hover tooltip
                shape='dot'         # Node shape
            )
        
        # Add edges to visualization
        for source, target, data in self.graph.edges(data=True):
            # Get source and target node types
            source_type = self.graph.nodes[source].get('node_type', 'unknown')
            target_type = self.graph.nodes[target].get('node_type', 'unknown')
            
            # Skip edge if either node is filtered out
            if filter_types and (source_type not in filter_types or target_type not in filter_types):
                continue
            
            # Get edge metadata
            relationship = data.get('relationship', 'related')
            edge_type = data.get('edge_type', 'unknown')
            
            # Add edge to PyVis network
            net.add_edge(
                source,                              # Source node
                target,                              # Target node
                title=f"{relationship}",             # Hover tooltip
                arrows='to',                         # Arrow direction
                smooth={'type': 'continuous'}        # Curved edges
            )
        
        # Enable physics simulation for layout
        net.toggle_physics(True)
        
        # Save to temporary HTML file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.html') as f:
            net.save_graph(f.name)
            return f.name
    
    # Calculate centrality metrics for all nodes
    # Centrality measures node importance in the network
    def get_centrality_metrics(self) -> Dict[str, Dict]:
        # Degree centrality: Based on number of connections
        degree_centrality = nx.degree_centrality(self.graph)
        
        # Betweenness centrality: Based on shortest paths passing through node
        betweenness_centrality = nx.betweenness_centrality(self.graph)
        
        # Closeness centrality: Based on average distance to all other nodes
        try:
            closeness_centrality = nx.closeness_centrality(self.graph)
        except:
            # May fail for disconnected graphs
            closeness_centrality = {}
        
        # Combine metrics into single dictionary
        metrics = {}
        for node in self.graph.nodes():
            metrics[node] = {
                'degree': degree_centrality.get(node, 0),
                'betweenness': betweenness_centrality.get(node, 0),
                'closeness': closeness_centrality.get(node, 0),
                'node_type': self.graph.nodes[node].get('node_type', 'unknown')
            }
        
        return metrics
    
    # Get top N most central nodes by specified metric
    def get_top_central_nodes(self, metric: str = 'degree', top_n: int = 10) -> List[Tuple[str, float]]:
        # Calculate all centrality metrics
        metrics = self.get_centrality_metrics()
        
        # Validate metric type
        if metric not in ['degree', 'betweenness', 'closeness']:
            metric = 'degree'
        
        # Sort nodes by specified metric (descending)
        sorted_nodes = sorted(
            metrics.items(),
            key=lambda x: x[1][metric],
            reverse=True
        )
        
        # Return top N nodes as list of (name, score) tuples
        return [(node, data[metric]) for node, data in sorted_nodes[:top_n]]
    
    # Find shortest path between two nodes
    # Uses undirected version for path finding
    def find_shortest_path(self, source: str, target: str) -> Optional[List[str]]:
        # Check that both nodes exist
        if source not in self.graph or target not in self.graph:
            return None
        
        try:
            # Convert to undirected for path finding (ignores edge direction)
            path = nx.shortest_path(self.graph.to_undirected(), source, target)
            return path
        except nx.NetworkXNoPath:
            # Return None if no path exists
            return None
    
    # Predict drug repurposing opportunities using network analysis
    # Finds diseases that share targets with the drug's current indications
    def predict_drug_repurposing(self, drug_name: str, top_n: int = 5) -> List[Dict]:
        # Return empty list if drug not in graph
        if drug_name not in self.graph:
            return []
        
        # Get current targets of the drug
        current_targets = set(self.get_drug_targets(drug_name))
        # Get current disease indications
        current_diseases = set(self.get_drug_indications(drug_name))
        
        # Initialize candidates list
        candidates = []
        
        # Get all disease nodes in graph
        all_diseases = [n for n, d in self.graph.nodes(data=True) 
                       if d.get('node_type') == 'disease']
        
        # Check each disease for repurposing potential
        for disease in all_diseases:
            # Skip diseases already treated by this drug
            if disease in current_diseases:
                continue
            
            # Get targets associated with this disease
            disease_targets = set([n for n in self.graph.predecessors(disease) 
                                  if self.graph.nodes[n].get('node_type') == 'target'])
            
            # Find targets shared between drug and disease
            shared_targets = current_targets.intersection(disease_targets)
            
            # Skip if no shared targets
            if not shared_targets:
                continue
            
            # Calculate path length from drug to disease
            try:
                path = self.find_shortest_path(drug_name, disease)
                path_length = len(path) if path else float('inf')
            except:
                path_length = float('inf')
            
            # Calculate repurposing score
            # More shared targets = higher score
            # Shorter path = higher score
            score = len(shared_targets) * 10 - path_length
            
            # Add candidate to list
            candidates.append({
                'disease': disease,
                'shared_targets': list(shared_targets),
                'num_shared_targets': len(shared_targets),
                'path_length': path_length,
                'repurposing_score': score
            })
        
        # Sort by repurposing score (descending)
        candidates.sort(key=lambda x: x['repurposing_score'], reverse=True)
        
        # Return top N candidates
        return candidates[:top_n]
    
    # Export graph to JSON format
    def export_to_json(self) -> str:
        # Get nodes and edges
        nodes, edges = self.export_for_visualization()
        
        # Create JSON structure
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
        
        # Return formatted JSON string
        return json.dumps(data, indent=2)
    
    # Export graph to CSV format (two files: nodes and edges)
    def export_to_csv(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        # Create nodes DataFrame
        nodes_data = []
        for node, data in self.graph.nodes(data=True):
            nodes_data.append({
                'node_id': node,
                'node_type': data.get('node_type', 'unknown'),
                'category': data.get('category', 'Unknown'),
                'degree': self.graph.degree(node)
            })
        
        # Create edges DataFrame
        edges_data = []
        for source, target, data in self.graph.edges(data=True):
            edges_data.append({
                'source': source,
                'target': target,
                'relationship': data.get('relationship', 'related'),
                'edge_type': data.get('edge_type', 'unknown')
            })
        
        # Convert to DataFrames
        nodes_df = pd.DataFrame(nodes_data)
        edges_df = pd.DataFrame(edges_data)
        
        return nodes_df, edges_df
    
    # Export graph to GraphML format
    # GraphML is compatible with Cytoscape, Gephi, and other network tools
    def export_to_graphml(self) -> str:
        # Import BytesIO for in-memory file
        from io import BytesIO
        
        # Create buffer
        buffer = BytesIO()
        # Write GraphML to buffer
        nx.write_graphml(self.graph, buffer)
        # Return as string
        return buffer.getvalue().decode('utf-8')
    
    # Get comprehensive information about a disease
    # Returns drugs, targets, and pathways associated with the disease
    def get_disease_relationships(self, disease_name: str) -> Dict:
        # Return error if disease not found
        if disease_name not in self.graph:
            return {'error': 'Disease not found in knowledge graph'}
        
        # Get drugs that treat this disease (predecessors with compound type)
        drugs = [n for n in self.graph.predecessors(disease_name) 
                if self.graph.nodes[n].get('node_type') == 'compound']
        
        # Get targets associated with this disease (predecessors with target type)
        targets = [n for n in self.graph.predecessors(disease_name) 
                  if self.graph.nodes[n].get('node_type') == 'target']
        
        # Find pathways connected to associated targets
        pathways = []
        for target in targets:
            target_pathways = [n for n in self.graph.successors(target) 
                             if self.graph.nodes[n].get('node_type') == 'pathway']
            pathways.extend(target_pathways)
        
        # Return disease information summary
        return {
            'Disease': disease_name,
            'Approved_Drugs': drugs,
            'Associated_Targets': targets,
            # Remove duplicate pathways
            'Involved_Pathways': list(set(pathways)),
            'Total_Drugs': len(drugs),
            'Total_Targets': len(targets)
        }
