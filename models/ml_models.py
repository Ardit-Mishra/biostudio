# =============================================================================
# MACHINE LEARNING MODELS MODULE
# =============================================================================
# This module contains machine learning models for drug-likeness prediction.
# Demonstrates pharmaceutical ML workflows using ensemble methods:
# - Random Forest: Decision tree ensemble
# - XGBoost: Gradient boosting
# - Simple Neural Network: Logistic regression-style classifier
#
# The models are trained on synthetic data for educational purposes.
# Production systems would use validated training datasets.
# =============================================================================

# Import numpy for numerical array operations
import numpy as np
# Import pandas for data manipulation
import pandas as pd
# Import Random Forest classifiers from scikit-learn
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
# Import model evaluation utilities
from sklearn.model_selection import cross_val_score, train_test_split
# Import data preprocessing tools
from sklearn.preprocessing import StandardScaler
# Import XGBoost gradient boosting library
import xgboost as xgb
# Import type hints for documentation
from typing import Dict, List, Tuple, Optional
# Import joblib for model serialization (saving/loading)
import joblib


# Main class for multi-model ensemble predictions
# Uses Random Forest and XGBoost for robust drug-likeness assessment
class MultiModelPredictor:
    
    # Initialize the predictor with model instances
    def __init__(self):
        # Create Random Forest classifier
        # n_estimators: Number of trees (100 is standard)
        # max_depth: Maximum tree depth (10 prevents overfitting)
        # random_state: Seed for reproducibility
        # n_jobs: -1 uses all CPU cores for parallel processing
        self.rf_classifier = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        
        # Create XGBoost classifier
        # learning_rate: Step size shrinkage (0.1 is conservative)
        # max_depth: 6 is XGBoost default
        self.xgb_classifier = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42,
            n_jobs=-1
        )
        
        # Create StandardScaler for feature normalization
        # Normalizing features improves ML model performance
        self.scaler = StandardScaler()
        
        # Track whether models have been trained
        self.is_trained = False
    
    # Generate synthetic training dataset
    # Creates fake but realistic molecular descriptor data
    def create_synthetic_dataset(self, n_samples=1000) -> Tuple[np.ndarray, np.ndarray]:
        # Set random seed for reproducible data generation
        np.random.seed(42)
        
        # Create feature matrix with 30 features (molecular descriptors)
        # Initialize with random values
        X = np.random.randn(n_samples, 30)
        
        # Feature 0: Molecular Weight (realistic range 150-600 Da)
        X[:, 0] = np.random.uniform(150, 600, n_samples)
        
        # Feature 1: LogP (realistic range -2 to 6)
        X[:, 1] = np.random.uniform(-2, 6, n_samples)
        
        # Feature 2: TPSA (realistic range 20-150 Ų)
        X[:, 2] = np.random.uniform(20, 150, n_samples)
        
        # Feature 3: H-bond Donors (realistic range 0-8)
        X[:, 3] = np.random.randint(0, 8, n_samples)
        
        # Feature 4: H-bond Acceptors (realistic range 0-12)
        X[:, 4] = np.random.randint(0, 12, n_samples)
        
        # Generate labels based on Lipinski-like rules
        # Drug-like = 1 if molecule passes all these criteria
        y = ((X[:, 1] > 0) & (X[:, 1] < 5) &  # LogP between 0 and 5
             (X[:, 0] < 500) &                  # MW < 500
             (X[:, 3] < 5) &                    # HBD < 5
             (X[:, 4] < 10)).astype(int)        # HBA < 10
        
        # Add 10% label noise to make task more realistic
        # Real data always has some noise/errors
        noise = np.random.random(n_samples) < 0.1
        # Flip labels for noisy samples
        y[noise] = 1 - y[noise]
        
        # Return features and labels
        return X, y
    
    # Train both ML models on provided data
    def train_models(self, X: np.ndarray, y: np.ndarray) -> Dict:
        # Normalize features using StandardScaler
        # fit_transform: Learn mean/std and apply transformation
        X_scaled = self.scaler.fit_transform(X)
        
        # Split data into training (80%) and test (20%) sets
        # random_state ensures reproducible split
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42
        )
        
        # Train Random Forest on training data
        self.rf_classifier.fit(X_train, y_train)
        
        # Train XGBoost on training data
        self.xgb_classifier.fit(X_train, y_train)
        
        # Evaluate models on test set
        # Score returns accuracy (correct predictions / total)
        rf_score = self.rf_classifier.score(X_test, y_test)
        xgb_score = self.xgb_classifier.score(X_test, y_test)
        
        # Perform 5-fold cross-validation for more robust evaluation
        # CV splits data into 5 parts, trains on 4, tests on 1, rotates
        rf_cv_scores = cross_val_score(
            self.rf_classifier, X_scaled, y, cv=5, scoring='accuracy'
        )
        xgb_cv_scores = cross_val_score(
            self.xgb_classifier, X_scaled, y, cv=5, scoring='accuracy'
        )
        
        # Mark models as trained
        self.is_trained = True
        
        # Return training metrics
        return {
            'Random Forest': {
                # Single test set accuracy
                'Test Accuracy': round(rf_score, 3),
                # Average accuracy across 5 folds
                'CV Mean Accuracy': round(rf_cv_scores.mean(), 3),
                # Standard deviation of CV accuracy
                'CV Std': round(rf_cv_scores.std(), 3)
            },
            'XGBoost': {
                'Test Accuracy': round(xgb_score, 3),
                'CV Mean Accuracy': round(xgb_cv_scores.mean(), 3),
                'CV Std': round(xgb_cv_scores.std(), 3)
            }
        }
    
    # Make prediction using ensemble of both models
    def predict_with_ensemble(self, features: np.ndarray) -> Dict:
        # If models not trained, train on synthetic data first
        if not self.is_trained:
            # Generate synthetic training data
            X_syn, y_syn = self.create_synthetic_dataset()
            # Train models
            self.train_models(X_syn, y_syn)
        
        # Normalize input features using fitted scaler
        # reshape(1, -1) converts 1D array to 2D (1 sample, n features)
        features_scaled = self.scaler.transform(features.reshape(1, -1))
        
        # Get class probabilities from Random Forest
        # predict_proba returns [prob_class_0, prob_class_1]
        rf_pred = self.rf_classifier.predict_proba(features_scaled)[0]
        
        # Get class probabilities from XGBoost
        xgb_pred = self.xgb_classifier.predict_proba(features_scaled)[0]
        
        # Ensemble prediction: Average of both models
        # Simple averaging often works as well as complex methods
        ensemble_pred = (rf_pred + xgb_pred) / 2
        
        # Make final classification based on ensemble probability
        # Threshold of 0.5: if P(drug-like) > 0.5, classify as drug-like
        final_class = 1 if ensemble_pred[1] > 0.5 else 0
        
        # Confidence is the probability of the predicted class
        confidence = max(ensemble_pred)
        
        # Return prediction results
        return {
            # Human-readable prediction label
            'Prediction': 'Drug-like' if final_class == 1 else 'Non-drug-like',
            # Confidence as percentage
            'Confidence': round(confidence * 100, 1),
            # Individual model probabilities for transparency
            'Random Forest Probability': round(rf_pred[1] * 100, 1),
            'XGBoost Probability': round(xgb_pred[1] * 100, 1),
            # Ensemble probability
            'Ensemble Probability': round(ensemble_pred[1] * 100, 1)
        }
    
    # Get feature importance rankings
    # Helps explain which molecular properties drive predictions
    def get_feature_importance(self, feature_names: Optional[List[str]] = None) -> pd.DataFrame:
        # Return empty DataFrame if models not trained
        if not self.is_trained:
            return pd.DataFrame()
        
        # Use default feature names if not provided
        if feature_names is None:
            feature_names = [f'Feature_{i}' for i in range(30)]
        
        # Get feature importance from Random Forest
        # Based on reduction in impurity from splits on each feature
        rf_importance = self.rf_classifier.feature_importances_
        
        # Get feature importance from XGBoost
        xgb_importance = self.xgb_classifier.feature_importances_
        
        # Create DataFrame with importance scores
        df = pd.DataFrame({
            # Feature names
            'Feature': feature_names[:len(rf_importance)],
            # Random Forest importance
            'RF Importance': rf_importance,
            # XGBoost importance
            'XGBoost Importance': xgb_importance,
            # Average of both (ensemble importance)
            'Average Importance': (rf_importance + xgb_importance) / 2
        })
        
        # Sort by average importance descending
        df = df.sort_values('Average Importance', ascending=False)
        
        # Return top 15 most important features
        return df.head(15)


# Simple neural network implementation
# Single-layer perceptron (logistic regression equivalent)
# Demonstrates basic deep learning concepts
class SimpleNeuralNetwork:
    
    # Initialize network parameters
    def __init__(self):
        # Weights will be initialized during training
        self.weights = None
        # Bias term
        self.bias = None
        # Track training status
        self.is_trained = False
    
    # Sigmoid activation function
    # Converts any value to range (0, 1)
    # Used for binary classification
    def sigmoid(self, x):
        # np.clip prevents overflow in exp() for large negative values
        return 1 / (1 + np.exp(-np.clip(x, -500, 500)))
    
    # Train the neural network using gradient descent
    def train(self, X: np.ndarray, y: np.ndarray, epochs=100, learning_rate=0.01):
        # Get number of features from input
        n_features = X.shape[1]
        
        # Initialize weights with small random values
        # Small initialization prevents saturation of sigmoid
        self.weights = np.random.randn(n_features) * 0.01
        
        # Initialize bias to zero
        self.bias = 0
        
        # Training loop: iterate for specified number of epochs
        for epoch in range(epochs):
            # Forward pass: compute weighted sum
            # z = X · w + b (matrix multiplication)
            z = np.dot(X, self.weights) + self.bias
            
            # Apply sigmoid to get probabilities
            predictions = self.sigmoid(z)
            
            # Compute gradients using binary cross-entropy loss
            # Derivative of loss with respect to weights
            dw = np.dot(X.T, (predictions - y)) / len(y)
            
            # Derivative of loss with respect to bias
            db = np.sum(predictions - y) / len(y)
            
            # Update weights using gradient descent
            # Subtract because we're minimizing loss
            self.weights -= learning_rate * dw
            
            # Update bias
            self.bias -= learning_rate * db
        
        # Mark network as trained
        self.is_trained = True
    
    # Make prediction for new input
    def predict(self, X: np.ndarray) -> float:
        # Return 0.5 (uncertain) if not trained
        if not self.is_trained:
            return 0.5
        
        # Compute weighted sum
        z = np.dot(X, self.weights) + self.bias
        
        # Apply sigmoid and return probability
        return self.sigmoid(z)
