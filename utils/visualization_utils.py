# =============================================================================
# VISUALIZATION UTILITIES MODULE
# =============================================================================
# This module provides visualization functions for molecular analysis:
# - 2D molecular structure images
# - Property radar charts
# - Feature importance plots
# - Model prediction comparisons
# - ADME profile charts
# - UMAP clustering projections
# - Similarity heatmaps
#
# Uses: Matplotlib, Seaborn, Plotly, RDKit for different visualization types
# =============================================================================

# Import matplotlib for basic plotting
import matplotlib.pyplot as plt
# Import seaborn for enhanced statistical visualizations
import seaborn as sns
# Import plotly for interactive charts
import plotly.graph_objects as go
# Import plotly express for quick charts
import plotly.express as px
# Import RDKit core chemistry module
from rdkit import Chem
# Import RDKit drawing and chemistry modules
# Draw: 2D molecular structure visualization
# AllChem: Advanced chemistry operations
from rdkit.Chem import Draw, AllChem
# Import io for in-memory file operations
import io
# Import base64 for encoding images (not currently used)
import base64
# Import PIL for image processing
from PIL import Image
# Import numpy for numerical arrays
import numpy as np
# Import pandas for data manipulation
import pandas as pd


# Class for molecular visualization
# Handles 2D structure images and molecular property charts
class MolecularVisualizer:
    
    # Convert RDKit molecule to displayable image
    # Used by Molecule Studio to show 2D structures
    @staticmethod
    def mol_to_image(mol, size=(400, 400)):
        # Handle invalid molecule input
        if mol is None:
            # Create matplotlib figure for error message
            fig, ax = plt.subplots(figsize=(4, 4))
            # Display centered error text
            ax.text(0.5, 0.5, 'Invalid Molecule', 
                   ha='center', va='center', fontsize=14)
            # Hide axis for clean appearance
            ax.axis('off')
            # Return the figure (Streamlit can display this)
            return fig
        
        # Try to generate molecular image using RDKit
        try:
            # MolToImage creates PIL Image from molecule
            # size tuple controls image dimensions in pixels
            img = Draw.MolToImage(mol, size=size)
            # Return PIL Image object
            return img
        except:
            # Return None if image generation fails
            return None
    
    # Create radar chart for molecular properties
    # Visualizes multiple properties simultaneously
    @staticmethod
    def create_property_radar_chart(properties: dict):
        # Extract property names for chart categories
        categories = list(properties.keys())
        # Extract property values for chart data
        values = list(properties.values())
        
        # Create new Plotly figure
        fig = go.Figure()
        
        # Add polar scatter trace (radar chart)
        fig.add_trace(go.Scatterpolar(
            # Values determine distance from center
            r=values,
            # Categories are placed around the circle
            theta=categories,
            # Fill the area to center
            fill='toself',
            # Legend name
            name='Molecule Properties',
            # Blue line color
            line_color='#1f77b4'
        ))
        
        # Update chart layout
        fig.update_layout(
            # Configure polar axis
            polar=dict(
                radialaxis=dict(
                    # Show radial axis labels
                    visible=True,
                    # Set axis range (0 to max value plus 20% padding)
                    range=[0, max(values) * 1.2]
                )
            ),
            # Hide legend (only one trace)
            showlegend=False,
            # Chart title
            title="Molecular Property Profile"
        )
        
        # Return Plotly figure object
        return fig
    
    # Create horizontal bar chart for feature importance
    # Shows which molecular features drive ML predictions
    @staticmethod
    def create_feature_importance_plot(importance_df: pd.DataFrame):
        # Create bar chart using Plotly Express
        fig = px.bar(
            # Use top 10 most important features
            importance_df.head(10),
            # X-axis: importance score
            x='Average Importance',
            # Y-axis: feature name
            y='Feature',
            # Horizontal bars
            orientation='h',
            # Chart title
            title='Top 10 Most Important Features',
            # Axis labels
            labels={'Average Importance': 'Importance Score', 'Feature': 'Molecular Descriptor'}
        )
        
        # Update layout
        fig.update_layout(
            # Sort bars by value (ascending puts highest at top)
            yaxis={'categoryorder': 'total ascending'},
            # Chart height
            height=400
        )
        
        # Return Plotly figure
        return fig
    
    # Create bar chart comparing model predictions
    # Shows probabilities from different ML models
    @staticmethod
    def create_prediction_comparison(predictions: dict):
        # Extract model names
        models = list(predictions.keys())
        # Extract probability values
        probabilities = list(predictions.values())
        
        # Create figure with bar trace
        fig = go.Figure(data=[
            go.Bar(
                # Model names on x-axis
                x=models,
                # Probabilities on y-axis
                y=probabilities,
                # Different color for each bar
                marker_color=['#1f77b4', '#ff7f0e', '#2ca02c'],
                # Display percentage on bars
                text=[f'{p:.1f}%' for p in probabilities],
                # Position text automatically
                textposition='auto'
            )
        ])
        
        # Update layout
        fig.update_layout(
            # Chart title
            title='Model Predictions Comparison',
            # Axis labels
            xaxis_title='Model',
            yaxis_title='Drug-like Probability (%)',
            # Y-axis range 0-100%
            yaxis_range=[0, 100],
            # Chart height
            height=400
        )
        
        # Return Plotly figure
        return fig
    
    # Create horizontal bar chart for ADME profile
    # Visualizes absorption, distribution, metabolism, excretion scores
    @staticmethod
    def create_adme_profile_chart(adme_data: dict):
        # Initialize lists for properties and scores
        properties = []
        scores = []
        
        # Extract numeric scores from ADME data
        for prop, data in adme_data.items():
            # Check if data is a dict containing 'Score' key
            if isinstance(data, dict) and 'Score' in str(data):
                # Iterate through nested dict to find score values
                for key, value in data.items():
                    # Only include numeric score values
                    if 'Score' in key and isinstance(value, (int, float)):
                        properties.append(prop)
                        scores.append(value)
        
        # Return None if no scores found
        if not properties:
            return None
        
        # Create horizontal bar chart
        fig = go.Figure(data=[
            go.Bar(
                # Properties on y-axis
                y=properties,
                # Scores on x-axis
                x=scores,
                # Horizontal orientation
                orientation='h',
                # Light blue color
                marker_color='lightblue'
            )
        ])
        
        # Update layout
        fig.update_layout(
            # Chart title
            title='ADME Profile Overview',
            # Axis labels
            xaxis_title='Score',
            yaxis_title='Property',
            # Chart height
            height=400
        )
        
        # Return Plotly figure
        return fig


# Class for clustering and similarity visualizations
# Used for analyzing groups of molecules
class ClusteringVisualizer:
    
    # Create UMAP projection plot
    # UMAP reduces high-dimensional data to 2D for visualization
    @staticmethod
    def create_umap_plot(embeddings: np.ndarray, labels: np.ndarray = None, names: list = None):
        # Need at least 2 samples for UMAP
        if embeddings.shape[0] < 2:
            return None
        
        # Try to create UMAP projection
        try:
            # Import UMAP dimensionality reduction
            from umap import UMAP
            
            # Create UMAP reducer
            # n_neighbors: Number of neighbors to consider (smaller = more local structure)
            # n_components: Output dimensions (2 for 2D plot)
            # random_state: Seed for reproducibility
            reducer = UMAP(n_neighbors=min(15, embeddings.shape[0]-1), 
                          n_components=2, 
                          random_state=42)
            
            # Fit and transform embeddings to 2D
            embedding_2d = reducer.fit_transform(embeddings)
            
            # Use default labels (all zeros) if not provided
            if labels is None:
                labels = np.zeros(embeddings.shape[0])
            
            # Generate default molecule names if not provided
            if names is None:
                names = [f'Molecule {i+1}' for i in range(embeddings.shape[0])]
            
            # Create scatter plot using Plotly Express
            fig = px.scatter(
                # X coordinates from UMAP
                x=embedding_2d[:, 0],
                # Y coordinates from UMAP
                y=embedding_2d[:, 1],
                # Color points by cluster/label
                color=labels,
                # Show name on hover
                hover_name=names,
                # Chart title
                title='UMAP Projection of Molecular Fingerprints',
                # Axis labels
                labels={'x': 'UMAP 1', 'y': 'UMAP 2', 'color': 'Cluster'}
            )
            
            # Update layout
            fig.update_layout(height=500)
            
            # Return Plotly figure
            return fig
        
        except:
            # Return None if UMAP fails (missing library, etc.)
            return None
    
    # Create molecular similarity heatmap
    # Visualizes pairwise similarity between molecules
    @staticmethod
    def create_similarity_heatmap(similarity_matrix: np.ndarray, names: list):
        # Create heatmap using Plotly Express
        fig = px.imshow(
            # Similarity matrix (n x n)
            similarity_matrix,
            # X-axis labels (molecule names)
            x=names,
            # Y-axis labels (molecule names)
            y=names,
            # Color scale: Red-Yellow-Blue (reversed so red = high similarity)
            color_continuous_scale='RdYlBu_r',
            # Chart title
            title='Molecular Similarity Heatmap',
            # Colorbar label
            labels={'color': 'Tanimoto Similarity'}
        )
        
        # Update layout
        fig.update_layout(height=600)
        
        # Return Plotly figure
        return fig
