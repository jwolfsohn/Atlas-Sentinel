"""
Machine Learning Risk Prediction Model
Uses ensemble models (Random Forest + Gradient Boosting) for risk classification
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, VotingRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
import joblib
import os
from pathlib import Path
import pickle


class MLRiskModel:
    """
    Machine learning model for supply chain risk prediction
    Uses ensemble of Random Forest and Gradient Boosting
    """
    
    def __init__(self, model_dir: Optional[str] = None):
        """
        Initialize ML risk model
        
        Args:
            model_dir: Directory to save/load models
        """
        if model_dir is None:
            model_dir = os.getenv('DATA_DIR', '.data')
        
        self.model_dir = Path(model_dir) / 'models'
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.is_trained = False
        
        # Try to load existing model
        self._load_model()
        
        # If no model exists, train on synthetic data
        if not self.is_trained:
            self._train_on_synthetic_data()
    
    def _extract_features(self, 
                         weather_data: Dict,
                         sentiment_data: Dict,
                         congestion_data: Dict,
                         historical_data: Optional[Dict] = None) -> np.ndarray:
        """
        Extract features from raw data for ML model
        
        Args:
            weather_data: Weather information
            sentiment_data: News sentiment information
            congestion_data: Port congestion information
            historical_data: Optional historical data
            
        Returns:
            Feature vector as numpy array
        """
        features = []
        
        # Weather features (5 features)
        severity_map = {'none': 0, 'light': 1, 'moderate': 2, 'severe': 3, 'extreme': 4}
        features.append(severity_map.get(weather_data.get('severity', 'none'), 0))
        
        weather_type_map = {
            'hurricane': 4, 'typhoon': 4, 'storm': 3, 'wind': 2, 
            'fog': 1, 'ice': 2, 'none': 0
        }
        features.append(weather_type_map.get(weather_data.get('type', 'none'), 0))
        features.append(weather_data.get('duration_hours', 0) / 72.0)  # Normalized
        
        # Weather location features
        features.append(weather_data.get('latitude', 0) / 90.0)  # Normalized
        features.append(weather_data.get('longitude', 0) / 180.0)  # Normalized
        
        # Sentiment features (4 features)
        features.append(sentiment_data.get('sentiment_score', 0))  # Already -1 to 1
        features.append(min(1.0, sentiment_data.get('article_count', 0) / 10.0))  # Normalized
        features.append(min(1.0, sentiment_data.get('urgency_keywords', 0) / 5.0))  # Normalized
        features.append(len(sentiment_data.get('individual_scores', [])) / 10.0)  # Normalized
        
        # Congestion features (5 features)
        features.append(congestion_data.get('congestion_index', 0))
        features.append(min(1.0, congestion_data.get('wait_time_hours', 0) / 72.0))
        features.append(min(1.0, congestion_data.get('vessel_count', 0) / 50.0))
        features.append(congestion_data.get('capacity_utilization', 0))
        features.append(1.0 if congestion_data.get('trend') == 'increasing' else 0.0)
        
        # Historical features (3 features)
        if historical_data:
            features.append(historical_data.get('disruption_rate', 0))
            features.append(min(1.0, historical_data.get('recent_disruptions', 0) / 3.0))
            features.append(historical_data.get('avg_delay_hours', 0) / 72.0)
        else:
            features.extend([0.0, 0.0, 0.0])
        
        # Route features (2 features) - would need route_id mapping
        # For now, use hash-based features
        route_hash = hash(str(weather_data.get('affected_port_id', ''))) % 100
        features.append(route_hash / 100.0)
        features.append((route_hash % 10) / 10.0)
        
        return np.array(features).reshape(1, -1)
    
    def _generate_synthetic_training_data(self, n_samples: int = 1000) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate synthetic training data for model training
        
        Args:
            n_samples: Number of training samples
            
        Returns:
            X (features), y (target risk scores)
        """
        np.random.seed(42)
        X = []
        y = []
        
        for _ in range(n_samples):
            # Generate synthetic features
            weather_severity = np.random.choice([0, 1, 2, 3, 4], p=[0.2, 0.3, 0.3, 0.15, 0.05])
            weather_type = np.random.choice([0, 1, 2, 3, 4], p=[0.1, 0.2, 0.3, 0.3, 0.1])
            weather_duration = np.random.uniform(0, 1)
            lat = np.random.uniform(-1, 1)
            lon = np.random.uniform(-1, 1)
            
            sentiment = np.random.uniform(-1, 1)
            article_count = np.random.uniform(0, 1)
            urgency = np.random.uniform(0, 1)
            score_count = np.random.uniform(0, 1)
            
            congestion_idx = np.random.uniform(0, 1)
            wait_time = np.random.uniform(0, 1)
            vessel_count = np.random.uniform(0, 1)
            capacity_util = np.random.uniform(0, 1)
            trend = np.random.choice([0, 1])
            
            disruption_rate = np.random.uniform(0, 1)
            recent_disruptions = np.random.uniform(0, 1)
            avg_delay = np.random.uniform(0, 1)
            
            route_hash1 = np.random.uniform(0, 1)
            route_hash2 = np.random.uniform(0, 1)
            
            features = np.array([
                weather_severity, weather_type, weather_duration, lat, lon,
                sentiment, article_count, urgency, score_count,
                congestion_idx, wait_time, vessel_count, capacity_util, trend,
                disruption_rate, recent_disruptions, avg_delay,
                route_hash1, route_hash2
            ])
            
            # Generate target (risk score) based on features with some noise
            risk = (
                weather_severity * 0.15 +
                (1 - sentiment) / 2 * 0.25 +  # Negative sentiment = risk
                congestion_idx * 0.20 +
                wait_time * 0.15 +
                disruption_rate * 0.10 +
                urgency * 0.10 +
                np.random.normal(0, 0.1)  # Noise
            )
            risk = np.clip(risk, 0, 1)
            
            X.append(features)
            y.append(risk)
        
        return np.array(X), np.array(y)
    
    def _train_on_synthetic_data(self):
        """Train model on synthetic data"""
        print("Training ML risk model on synthetic data...")
        
        X, y = self._generate_synthetic_training_data(n_samples=2000)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Create ensemble model
        rf = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            random_state=42,
            n_jobs=-1
        )
        
        gb = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42
        )
        
        self.model = VotingRegressor([
            ('rf', rf),
            ('gb', gb)
        ])
        
        # Train
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate
        train_score = self.model.score(X_train_scaled, y_train)
        test_score = self.model.score(X_test_scaled, y_test)
        
        print(f"Model trained - Train R²: {train_score:.3f}, Test R²: {test_score:.3f}")
        
        self.is_trained = True
        self._save_model()
    
    def predict_risk(self,
                    weather_data: Dict,
                    sentiment_data: Dict,
                    congestion_data: Dict,
                    historical_data: Optional[Dict] = None) -> float:
        """
        Predict risk score using ML model
        
        Args:
            weather_data: Weather information
            sentiment_data: News sentiment information
            congestion_data: Port congestion information
            historical_data: Optional historical data
            
        Returns:
            Predicted risk score (0-1)
        """
        if not self.is_trained:
            self._train_on_synthetic_data()
        
        # Extract features
        features = self._extract_features(
            weather_data, sentiment_data, congestion_data, historical_data
        )
        
        # Scale features
        features_scaled = self.scaler.transform(features)
        
        # Predict
        risk_score = self.model.predict(features_scaled)[0]
        
        # Clip to [0, 1]
        return float(np.clip(risk_score, 0.0, 1.0))
    
    def predict_risk_level(self, risk_score: float) -> str:
        """
        Classify risk level from score
        
        Args:
            risk_score: Risk score (0-1)
            
        Returns:
            Risk level: 'low', 'medium', or 'high'
        """
        if risk_score >= 0.7:
            return 'high'
        elif risk_score >= 0.4:
            return 'medium'
        else:
            return 'low'
    
    def get_feature_importance(self) -> Dict[str, float]:
        """
        Get feature importance from model
        
        Returns:
            Dict mapping feature names to importance scores
        """
        if not self.is_trained or self.model is None:
            return {}
        
        feature_names = [
            'weather_severity', 'weather_type', 'weather_duration', 'weather_lat', 'weather_lon',
            'sentiment_score', 'article_count', 'urgency_keywords', 'score_count',
            'congestion_index', 'wait_time', 'vessel_count', 'capacity_util', 'trend',
            'disruption_rate', 'recent_disruptions', 'avg_delay',
            'route_hash1', 'route_hash2'
        ]
        
        # Get average importance from both models
        rf_importance = self.model.named_estimators_['rf'].feature_importances_
        gb_importance = self.model.named_estimators_['gb'].feature_importances_
        avg_importance = (rf_importance + gb_importance) / 2
        
        return dict(zip(feature_names, avg_importance))
    
    def _save_model(self):
        """Save trained model to disk"""
        model_path = self.model_dir / 'risk_model.pkl'
        scaler_path = self.model_dir / 'scaler.pkl'
        
        with open(model_path, 'wb') as f:
            pickle.dump(self.model, f)
        
        with open(scaler_path, 'wb') as f:
            pickle.dump(self.scaler, f)
    
    def _load_model(self):
        """Load trained model from disk"""
        model_path = self.model_dir / 'risk_model.pkl'
        scaler_path = self.model_dir / 'scaler.pkl'
        
        if model_path.exists() and scaler_path.exists():
            try:
                with open(model_path, 'rb') as f:
                    self.model = pickle.load(f)
                
                with open(scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
                
                self.is_trained = True
                print("Loaded existing ML risk model")
            except Exception as e:
                print(f"Error loading model: {e}")
                self.is_trained = False

