"""
Risk Scoring Engine for Supply Chain Disruption Prediction
Combines multiple data modalities to compute risk scores
"""

import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd


class RiskScorer:
    """
    Multi-modal risk scoring engine that combines:
    - Weather severity
    - News sentiment
    - Port congestion
    - Historical patterns
    """
    
    def __init__(self, 
                 weather_weight: float = 0.35,
                 sentiment_weight: float = 0.30,
                 congestion_weight: float = 0.25,
                 historical_weight: float = 0.10):
        """
        Initialize risk scorer with configurable weights
        
        Args:
            weather_weight: Weight for weather-based risk (0-1)
            sentiment_weight: Weight for news sentiment risk (0-1)
            congestion_weight: Weight for port congestion risk (0-1)
            historical_weight: Weight for historical pattern risk (0-1)
        """
        self.weather_weight = weather_weight
        self.sentiment_weight = sentiment_weight
        self.congestion_weight = congestion_weight
        self.historical_weight = historical_weight
        
        # Normalize weights
        total = weather_weight + sentiment_weight + congestion_weight + historical_weight
        self.weather_weight /= total
        self.sentiment_weight /= total
        self.congestion_weight /= total
        self.historical_weight /= total
        
        # Risk thresholds
        self.high_risk_threshold = 0.7
        self.medium_risk_threshold = 0.4
        
    def compute_weather_risk(self, weather_data: Dict) -> float:
        """
        Compute risk score from weather data
        
        Args:
            weather_data: Dict with keys like 'severity', 'type', 'duration'
            
        Returns:
            Risk score between 0 and 1
        """
        severity_map = {
            'none': 0.0,
            'light': 0.2,
            'moderate': 0.5,
            'severe': 0.8,
            'extreme': 1.0
        }
        
        base_risk = severity_map.get(weather_data.get('severity', 'none'), 0.0)
        
        # Adjust for weather type
        type_multipliers = {
            'hurricane': 1.2,
            'typhoon': 1.2,
            'storm': 1.0,
            'fog': 0.6,
            'ice': 0.8,
            'wind': 0.7
        }
        multiplier = type_multipliers.get(weather_data.get('type', 'storm'), 1.0)
        
        # Duration factor (longer = higher risk)
        duration_hours = weather_data.get('duration_hours', 0)
        duration_factor = min(1.0, duration_hours / 48.0)  # Cap at 48 hours
        
        risk = base_risk * multiplier * (0.7 + 0.3 * duration_factor)
        return min(1.0, risk)
    
    def compute_sentiment_risk(self, sentiment_data: Dict) -> float:
        """
        Compute risk score from news sentiment
        
        Args:
            sentiment_data: Dict with 'sentiment_score', 'article_count', 'urgency_keywords'
            
        Returns:
            Risk score between 0 and 1
        """
        # Sentiment score: -1 (very negative) to 1 (very positive)
        # We want negative sentiment to indicate risk
        sentiment_score = sentiment_data.get('sentiment_score', 0.0)
        
        # Convert to risk: negative sentiment = high risk
        sentiment_risk = (1.0 - sentiment_score) / 2.0  # Maps -1->1.0, 0->0.5, 1->0.0
        
        # Article volume factor (more articles = higher concern)
        article_count = sentiment_data.get('article_count', 0)
        volume_factor = min(1.0, article_count / 10.0)  # Normalize to 10 articles
        
        # Urgency keywords boost
        urgency_count = sentiment_data.get('urgency_keywords', 0)
        urgency_factor = min(1.0, urgency_count / 5.0)  # Normalize to 5 keywords
        
        risk = sentiment_risk * (0.6 + 0.2 * volume_factor + 0.2 * urgency_factor)
        return min(1.0, risk)
    
    def compute_congestion_risk(self, congestion_data: Dict) -> float:
        """
        Compute risk score from port congestion data
        
        Args:
            congestion_data: Dict with 'congestion_index', 'wait_time_hours', 'vessel_count'
            
        Returns:
            Risk score between 0 and 1
        """
        # Congestion index: 0 (no congestion) to 1 (severe congestion)
        congestion_index = congestion_data.get('congestion_index', 0.0)
        
        # Wait time factor
        wait_hours = congestion_data.get('wait_time_hours', 0)
        wait_factor = min(1.0, wait_hours / 72.0)  # Normalize to 72 hours
        
        # Vessel count factor (capacity pressure)
        vessel_count = congestion_data.get('vessel_count', 0)
        capacity_factor = min(1.0, vessel_count / 50.0)  # Normalize to 50 vessels
        
        risk = congestion_index * 0.5 + wait_factor * 0.3 + capacity_factor * 0.2
        return min(1.0, risk)
    
    def compute_historical_risk(self, route_id: str, historical_data: Optional[Dict] = None) -> float:
        """
        Compute risk based on historical patterns
        
        Args:
            route_id: Identifier for the route
            historical_data: Optional historical disruption data
            
        Returns:
            Risk score between 0 and 1
        """
        if historical_data is None:
            return 0.1  # Default low risk if no history
        
        # Historical disruption frequency
        disruption_rate = historical_data.get('disruption_rate', 0.0)
        
        # Recent disruptions (last 30 days)
        recent_disruptions = historical_data.get('recent_disruptions', 0)
        recent_factor = min(1.0, recent_disruptions / 3.0)
        
        risk = disruption_rate * 0.7 + recent_factor * 0.3
        return min(1.0, risk)
    
    def compute_route_risk(self, 
                          route_id: str,
                          weather_data: Dict,
                          sentiment_data: Dict,
                          congestion_data: Dict,
                          historical_data: Optional[Dict] = None) -> Dict:
        """
        Compute comprehensive risk score for a route
        
        Args:
            route_id: Route identifier
            weather_data: Weather information
            sentiment_data: News sentiment information
            congestion_data: Port congestion information
            historical_data: Optional historical data
            
        Returns:
            Dict with risk score and component breakdown
        """
        # Compute individual risk components
        weather_risk = self.compute_weather_risk(weather_data)
        sentiment_risk = self.compute_sentiment_risk(sentiment_data)
        congestion_risk = self.compute_congestion_risk(congestion_data)
        historical_risk = self.compute_historical_risk(route_id, historical_data)
        
        # Weighted combination
        total_risk = (
            weather_risk * self.weather_weight +
            sentiment_risk * self.sentiment_weight +
            congestion_risk * self.congestion_weight +
            historical_risk * self.historical_weight
        )
        
        # Determine risk level
        if total_risk >= self.high_risk_threshold:
            risk_level = 'high'
        elif total_risk >= self.medium_risk_threshold:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        return {
            'route_id': route_id,
            'total_risk': float(total_risk),
            'risk_level': risk_level,
            'components': {
                'weather': float(weather_risk),
                'sentiment': float(sentiment_risk),
                'congestion': float(congestion_risk),
                'historical': float(historical_risk)
            },
            'weights': {
                'weather': self.weather_weight,
                'sentiment': self.sentiment_weight,
                'congestion': self.congestion_weight,
                'historical': self.historical_weight
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def predict_cascading_delays(self, 
                                 route_risks: List[Dict],
                                 network_graph: Optional[Dict] = None) -> List[Dict]:
        """
        Predict cascading delays across the supply chain network
        
        Args:
            route_risks: List of route risk assessments
            network_graph: Optional graph of route dependencies
            
        Returns:
            List of routes with predicted delay impacts
        """
        results = []
        
        for route_risk in route_risks:
            base_delay_hours = 0
            
            # High risk routes get base delay
            if route_risk['risk_level'] == 'high':
                base_delay_hours = 24 + (route_risk['total_risk'] - 0.7) * 100
            elif route_risk['risk_level'] == 'medium':
                base_delay_hours = 6 + (route_risk['total_risk'] - 0.4) * 30
            
            # Cascading effects (simplified - would use graph traversal in production)
            cascading_delay = 0
            if network_graph:
                # Find dependent routes
                route_id = route_risk['route_id']
                if route_id in network_graph:
                    for dependent_route in network_graph[route_id]:
                        # Dependent routes get 30% of upstream delay
                        cascading_delay += base_delay_hours * 0.3
            
            total_delay = base_delay_hours + cascading_delay
            
            results.append({
                'route_id': route_risk['route_id'],
                'predicted_delay_hours': float(total_delay),
                'base_delay': float(base_delay_hours),
                'cascading_delay': float(cascading_delay),
                'risk_level': route_risk['risk_level']
            })
        
        return results

