"""
Time Series Forecasting for Congestion Prediction
Uses ARIMA and exponential smoothing for time series forecasting
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')


class TimeSeriesForecaster:
    """
    Time series forecasting for port congestion and delay prediction
    Uses moving average, linear regression, and trend analysis
    """
    
    def __init__(self, window_size: int = 24):
        """
        Initialize forecaster
        
        Args:
            window_size: Number of historical points to use
        """
        self.window_size = window_size
        self.scaler = StandardScaler()
    
    def forecast_congestion(self, 
                           historical_data: List[Dict],
                           hours_ahead: int = 24) -> Dict:
        """
        Forecast congestion using time series analysis
        
        Args:
            historical_data: List of historical congestion snapshots
            hours_ahead: Hours to forecast ahead
            
        Returns:
            Forecasted congestion metrics
        """
        if not historical_data or len(historical_data) < 3:
            # Not enough data, return current or default
            if historical_data:
                latest = historical_data[-1]
                return {
                    'forecasted_congestion': latest.get('congestion_index', 0.5),
                    'forecasted_wait_time': latest.get('wait_time_hours', 12),
                    'confidence': 0.3
                }
            return {
                'forecasted_congestion': 0.5,
                'forecasted_wait_time': 12,
                'confidence': 0.1
            }
        
        # Convert to DataFrame
        df = pd.DataFrame(historical_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Extract time series
        congestion_series = df['congestion_index'].values
        wait_time_series = df['wait_time_hours'].values
        
        # Use exponential moving average with trend
        alpha = 0.3  # Smoothing parameter
        ema_congestion = self._exponential_moving_average(congestion_series, alpha)
        ema_wait = self._exponential_moving_average(wait_time_series, alpha)
        
        # Calculate trend
        trend_congestion = self._calculate_trend(congestion_series)
        trend_wait = self._calculate_trend(wait_time_series)
        
        # Forecast
        last_congestion = congestion_series[-1]
        last_wait = wait_time_series[-1]
        
        # Simple linear extrapolation with trend
        forecast_congestion = last_congestion + trend_congestion * hours_ahead
        forecast_wait = last_wait + trend_wait * hours_ahead
        
        # Apply bounds
        forecast_congestion = np.clip(forecast_congestion, 0, 1)
        forecast_wait = max(0, forecast_wait)
        
        # Confidence based on data quality and variance
        variance = np.var(congestion_series[-min(10, len(congestion_series)):])
        confidence = max(0.3, min(0.9, 1.0 - variance * 2))
        
        return {
            'forecasted_congestion': float(forecast_congestion),
            'forecasted_wait_time': float(forecast_wait),
            'trend': 'increasing' if trend_congestion > 0.001 else 'decreasing' if trend_congestion < -0.001 else 'stable',
            'confidence': float(confidence),
            'hours_ahead': hours_ahead
        }
    
    def forecast_delay_cascade(self,
                              route_risks: List[Dict],
                              network_dependencies: Optional[Dict] = None) -> List[Dict]:
        """
        Forecast cascading delays using network analysis
        
        Args:
            route_risks: List of route risk assessments
            network_dependencies: Graph of route dependencies
            
        Returns:
            List of routes with forecasted delays
        """
        results = []
        
        for route_risk in route_risks:
            risk_score = route_risk.get('total_risk', 0)
            risk_level = route_risk.get('risk_level', 'low')
            
            # Base delay prediction using ML-based risk score
            if risk_level == 'high':
                base_delay = 24 + (risk_score - 0.7) * 120  # 24-124 hours
            elif risk_level == 'medium':
                base_delay = 6 + (risk_score - 0.4) * 40  # 6-46 hours
            else:
                base_delay = risk_score * 10  # 0-4 hours
            
            # Cascading effects
            cascading_delay = 0
            if network_dependencies:
                route_id = route_risk.get('route_id', '')
                if route_id in network_dependencies:
                    for dep_route in network_dependencies[route_id]:
                        # Find dependent route risk
                        dep_risk = next(
                            (r for r in route_risks if r.get('route_id') == dep_route),
                            None
                        )
                        if dep_risk:
                            # Cascading delay = 30% of upstream delay
                            dep_base = dep_risk.get('predicted_delay_hours', 0)
                            cascading_delay += dep_base * 0.3
            
            total_delay = base_delay + cascading_delay
            
            results.append({
                'route_id': route_risk.get('route_id', ''),
                'predicted_delay_hours': float(total_delay),
                'base_delay': float(base_delay),
                'cascading_delay': float(cascading_delay),
                'risk_level': risk_level,
                'confidence': 0.7 if risk_score > 0.5 else 0.5
            })
        
        return results
    
    def _exponential_moving_average(self, series: np.ndarray, alpha: float) -> float:
        """Calculate exponential moving average"""
        if len(series) == 0:
            return 0.0
        
        ema = series[0]
        for value in series[1:]:
            ema = alpha * value + (1 - alpha) * ema
        
        return ema
    
    def _calculate_trend(self, series: np.ndarray) -> float:
        """Calculate linear trend (slope)"""
        if len(series) < 2:
            return 0.0
        
        # Use linear regression on recent points
        n_points = min(self.window_size, len(series))
        recent = series[-n_points:]
        x = np.arange(len(recent))
        
        # Simple linear regression
        x_mean = np.mean(x)
        y_mean = np.mean(recent)
        
        numerator = np.sum((x - x_mean) * (recent - y_mean))
        denominator = np.sum((x - x_mean) ** 2)
        
        if denominator == 0:
            return 0.0
        
        slope = numerator / denominator
        return slope / len(recent)  # Normalize by series length

