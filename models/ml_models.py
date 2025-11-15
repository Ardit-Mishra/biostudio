import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
from typing import Dict, List, Tuple, Optional
import joblib


class MultiModelPredictor:
    
    def __init__(self):
        self.rf_classifier = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        self.xgb_classifier = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42,
            n_jobs=-1
        )
        self.scaler = StandardScaler()
        self.is_trained = False
    
    def create_synthetic_dataset(self, n_samples=1000) -> Tuple[np.ndarray, np.ndarray]:
        np.random.seed(42)
        
        X = np.random.randn(n_samples, 30)
        
        X[:, 0] = np.random.uniform(150, 600, n_samples)
        X[:, 1] = np.random.uniform(-2, 6, n_samples)
        X[:, 2] = np.random.uniform(20, 150, n_samples)
        X[:, 3] = np.random.randint(0, 8, n_samples)
        X[:, 4] = np.random.randint(0, 12, n_samples)
        
        y = ((X[:, 1] > 0) & (X[:, 1] < 5) &
             (X[:, 0] < 500) &
             (X[:, 3] < 5) &
             (X[:, 4] < 10)).astype(int)
        
        noise = np.random.random(n_samples) < 0.1
        y[noise] = 1 - y[noise]
        
        return X, y
    
    def train_models(self, X: np.ndarray, y: np.ndarray) -> Dict:
        X_scaled = self.scaler.fit_transform(X)
        
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42
        )
        
        self.rf_classifier.fit(X_train, y_train)
        self.xgb_classifier.fit(X_train, y_train)
        
        rf_score = self.rf_classifier.score(X_test, y_test)
        xgb_score = self.xgb_classifier.score(X_test, y_test)
        
        rf_cv_scores = cross_val_score(
            self.rf_classifier, X_scaled, y, cv=5, scoring='accuracy'
        )
        xgb_cv_scores = cross_val_score(
            self.xgb_classifier, X_scaled, y, cv=5, scoring='accuracy'
        )
        
        self.is_trained = True
        
        return {
            'Random Forest': {
                'Test Accuracy': round(rf_score, 3),
                'CV Mean Accuracy': round(rf_cv_scores.mean(), 3),
                'CV Std': round(rf_cv_scores.std(), 3)
            },
            'XGBoost': {
                'Test Accuracy': round(xgb_score, 3),
                'CV Mean Accuracy': round(xgb_cv_scores.mean(), 3),
                'CV Std': round(xgb_cv_scores.std(), 3)
            }
        }
    
    def predict_with_ensemble(self, features: np.ndarray) -> Dict:
        if not self.is_trained:
            X_syn, y_syn = self.create_synthetic_dataset()
            self.train_models(X_syn, y_syn)
        
        features_scaled = self.scaler.transform(features.reshape(1, -1))
        
        rf_pred = self.rf_classifier.predict_proba(features_scaled)[0]
        xgb_pred = self.xgb_classifier.predict_proba(features_scaled)[0]
        
        ensemble_pred = (rf_pred + xgb_pred) / 2
        
        final_class = 1 if ensemble_pred[1] > 0.5 else 0
        confidence = max(ensemble_pred)
        
        return {
            'Prediction': 'Drug-like' if final_class == 1 else 'Non-drug-like',
            'Confidence': round(confidence * 100, 1),
            'Random Forest Probability': round(rf_pred[1] * 100, 1),
            'XGBoost Probability': round(xgb_pred[1] * 100, 1),
            'Ensemble Probability': round(ensemble_pred[1] * 100, 1)
        }
    
    def get_feature_importance(self, feature_names: Optional[List[str]] = None) -> pd.DataFrame:
        if not self.is_trained:
            return pd.DataFrame()
        
        if feature_names is None:
            feature_names = [f'Feature_{i}' for i in range(30)]
        
        rf_importance = self.rf_classifier.feature_importances_
        xgb_importance = self.xgb_classifier.feature_importances_
        
        df = pd.DataFrame({
            'Feature': feature_names[:len(rf_importance)],
            'RF Importance': rf_importance,
            'XGBoost Importance': xgb_importance,
            'Average Importance': (rf_importance + xgb_importance) / 2
        })
        
        df = df.sort_values('Average Importance', ascending=False)
        return df.head(15)


class SimpleNeuralNetwork:
    
    def __init__(self):
        self.weights = None
        self.bias = None
        self.is_trained = False
    
    def sigmoid(self, x):
        return 1 / (1 + np.exp(-np.clip(x, -500, 500)))
    
    def train(self, X: np.ndarray, y: np.ndarray, epochs=100, learning_rate=0.01):
        n_features = X.shape[1]
        self.weights = np.random.randn(n_features) * 0.01
        self.bias = 0
        
        for epoch in range(epochs):
            z = np.dot(X, self.weights) + self.bias
            predictions = self.sigmoid(z)
            
            dw = np.dot(X.T, (predictions - y)) / len(y)
            db = np.sum(predictions - y) / len(y)
            
            self.weights -= learning_rate * dw
            self.bias -= learning_rate * db
        
        self.is_trained = True
    
    def predict(self, X: np.ndarray) -> float:
        if not self.is_trained:
            return 0.5
        
        z = np.dot(X, self.weights) + self.bias
        return self.sigmoid(z)
