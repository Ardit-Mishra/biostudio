import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from rdkit import Chem
from rdkit.Chem import Draw, AllChem
import io
import base64
from PIL import Image
import numpy as np
import pandas as pd


class MolecularVisualizer:
    
    @staticmethod
    def mol_to_image(mol, size=(400, 400)):
        if mol is None:
            fig, ax = plt.subplots(figsize=(4, 4))
            ax.text(0.5, 0.5, 'Invalid Molecule', 
                   ha='center', va='center', fontsize=14)
            ax.axis('off')
            return fig
        
        try:
            img = Draw.MolToImage(mol, size=size)
            return img
        except:
            return None
    
    @staticmethod
    def create_property_radar_chart(properties: dict):
        categories = list(properties.keys())
        values = list(properties.values())
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='Molecule Properties',
            line_color='#1f77b4'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, max(values) * 1.2]
                )
            ),
            showlegend=False,
            title="Molecular Property Profile"
        )
        
        return fig
    
    @staticmethod
    def create_feature_importance_plot(importance_df: pd.DataFrame):
        fig = px.bar(
            importance_df.head(10),
            x='Average Importance',
            y='Feature',
            orientation='h',
            title='Top 10 Most Important Features',
            labels={'Average Importance': 'Importance Score', 'Feature': 'Molecular Descriptor'}
        )
        
        fig.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            height=400
        )
        
        return fig
    
    @staticmethod
    def create_prediction_comparison(predictions: dict):
        models = list(predictions.keys())
        probabilities = list(predictions.values())
        
        fig = go.Figure(data=[
            go.Bar(
                x=models,
                y=probabilities,
                marker_color=['#1f77b4', '#ff7f0e', '#2ca02c'],
                text=[f'{p:.1f}%' for p in probabilities],
                textposition='auto'
            )
        ])
        
        fig.update_layout(
            title='Model Predictions Comparison',
            xaxis_title='Model',
            yaxis_title='Drug-like Probability (%)',
            yaxis_range=[0, 100],
            height=400
        )
        
        return fig
    
    @staticmethod
    def create_adme_profile_chart(adme_data: dict):
        properties = []
        scores = []
        
        for prop, data in adme_data.items():
            if isinstance(data, dict) and 'Score' in str(data):
                for key, value in data.items():
                    if 'Score' in key and isinstance(value, (int, float)):
                        properties.append(prop)
                        scores.append(value)
        
        if not properties:
            return None
        
        fig = go.Figure(data=[
            go.Bar(
                y=properties,
                x=scores,
                orientation='h',
                marker_color='lightblue'
            )
        ])
        
        fig.update_layout(
            title='ADME Profile Overview',
            xaxis_title='Score',
            yaxis_title='Property',
            height=400
        )
        
        return fig


class ClusteringVisualizer:
    
    @staticmethod
    def create_umap_plot(embeddings: np.ndarray, labels: np.ndarray = None, names: list = None):
        if embeddings.shape[0] < 2:
            return None
        
        try:
            from umap import UMAP
            
            reducer = UMAP(n_neighbors=min(15, embeddings.shape[0]-1), 
                          n_components=2, 
                          random_state=42)
            embedding_2d = reducer.fit_transform(embeddings)
            
            if labels is None:
                labels = np.zeros(embeddings.shape[0])
            
            if names is None:
                names = [f'Molecule {i+1}' for i in range(embeddings.shape[0])]
            
            fig = px.scatter(
                x=embedding_2d[:, 0],
                y=embedding_2d[:, 1],
                color=labels,
                hover_name=names,
                title='UMAP Projection of Molecular Fingerprints',
                labels={'x': 'UMAP 1', 'y': 'UMAP 2', 'color': 'Cluster'}
            )
            
            fig.update_layout(height=500)
            return fig
        
        except:
            return None
    
    @staticmethod
    def create_similarity_heatmap(similarity_matrix: np.ndarray, names: list):
        fig = px.imshow(
            similarity_matrix,
            x=names,
            y=names,
            color_continuous_scale='RdYlBu_r',
            title='Molecular Similarity Heatmap',
            labels={'color': 'Tanimoto Similarity'}
        )
        
        fig.update_layout(height=600)
        return fig
