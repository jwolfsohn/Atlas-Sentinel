"""
Port Congestion Analysis
Computes rolling congestion indices from port traffic data
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta


class CongestionAnalyzer:
    """
    Analyzes port congestion from traffic data
    Computes rolling indices and predicts congestion trends
    """
    
    def __init__(self, window_hours: int = 24):
        """
        Initialize congestion analyzer
        
        Args:
            window_hours: Time window for rolling calculations
        """
        self.window_hours = window_hours
    
    def compute_congestion_index(self, 
                                 current_vessels: int,
                                 capacity: int,
                                 wait_time_hours: float,
                                 historical_avg: Optional[float] = None) -> float:
        """
        Compute congestion index (0-1 scale)
        
        Args:
            current_vessels: Number of vessels currently at port
            capacity: Port capacity (max vessels)
            wait_time_hours: Average wait time in hours
            historical_avg: Historical average wait time
            
        Returns:
            Congestion index between 0 and 1
        """
        # Capacity utilization (0-1)
        capacity_util = min(1.0, current_vessels / capacity) if capacity > 0 else 0.0
        
        # Wait time factor
        # Normal wait time: 12 hours, severe: 72+ hours
        wait_factor = min(1.0, wait_time_hours / 72.0)
        
        # Historical comparison
        if historical_avg:
            deviation = (wait_time_hours - historical_avg) / max(historical_avg, 1.0)
            historical_factor = min(1.0, max(0.0, 0.5 + deviation * 0.5))
        else:
            historical_factor = 0.5
        
        # Weighted combination
        congestion_index = (
            capacity_util * 0.4 +
            wait_factor * 0.4 +
            historical_factor * 0.2
        )
        
        return min(1.0, max(0.0, congestion_index))
    
    def compute_rolling_index(self, 
                              port_id: str,
                              traffic_data: List[Dict]) -> Dict:
        """
        Compute rolling congestion index from time series data
        
        Args:
            port_id: Port identifier
            traffic_data: List of traffic snapshots with timestamps
            
        Returns:
            Current congestion metrics
        """
        if not traffic_data:
            return {
                'port_id': port_id,
                'congestion_index': 0.0,
                'vessel_count': 0,
                'wait_time_hours': 0.0,
                'trend': 'stable'
            }
        
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(traffic_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Get most recent data
        now = datetime.now()
        window_start = now - timedelta(hours=self.window_hours)
        recent_data = df[df['timestamp'] >= window_start]
        
        if recent_data.empty:
            recent_data = df.tail(1)
        
        latest = recent_data.iloc[-1]
        
        # Compute metrics
        avg_vessels = recent_data['vessel_count'].mean()
        avg_wait = recent_data['wait_time_hours'].mean()
        capacity = latest.get('capacity', 100)  # Default capacity
        
        # Historical average (from older data)
        historical_avg = None
        if len(df) > len(recent_data):
            historical_data = df[df['timestamp'] < window_start]
            if not historical_data.empty:
                historical_avg = historical_data['wait_time_hours'].mean()
        
        congestion_index = self.compute_congestion_index(
            avg_vessels, capacity, avg_wait, historical_avg
        )
        
        # Compute trend
        if len(recent_data) >= 2:
            recent_trend = recent_data['wait_time_hours'].iloc[-1] - recent_data['wait_time_hours'].iloc[0]
            if recent_trend > 2:
                trend = 'increasing'
            elif recent_trend < -2:
                trend = 'decreasing'
            else:
                trend = 'stable'
        else:
            trend = 'stable'
        
        return {
            'port_id': port_id,
            'congestion_index': float(congestion_index),
            'vessel_count': int(avg_vessels),
            'wait_time_hours': float(avg_wait),
            'capacity_utilization': float(avg_vessels / capacity) if capacity > 0 else 0.0,
            'trend': trend,
            'timestamp': now.isoformat()
        }
    
    def predict_congestion(self, 
                          current_metrics: Dict,
                          incoming_vessels: int,
                          processing_rate: float) -> Dict:
        """
        Predict future congestion based on incoming traffic
        
        Args:
            current_metrics: Current congestion metrics
            incoming_vessels: Expected vessels in next 24 hours
            processing_rate: Vessels processed per hour
            
        Returns:
            Predicted congestion metrics
        """
        current_vessels = current_metrics['vessel_count']
        current_wait = current_metrics['wait_time_hours']
        
        # Project forward 24 hours
        hours_ahead = 24
        total_incoming = current_vessels + incoming_vessels
        total_processed = processing_rate * hours_ahead
        
        projected_vessels = max(0, total_incoming - total_processed)
        
        # Estimate wait time
        if processing_rate > 0:
            projected_wait = projected_vessels / processing_rate
        else:
            projected_wait = current_wait + hours_ahead
        
        # Compute projected congestion
        capacity = current_metrics.get('capacity', 100)
        projected_index = self.compute_congestion_index(
            projected_vessels, capacity, projected_wait, current_wait
        )
        
        return {
            'projected_congestion_index': float(projected_index),
            'projected_vessel_count': int(projected_vessels),
            'projected_wait_hours': float(projected_wait),
            'hours_ahead': hours_ahead,
            'timestamp': datetime.now().isoformat()
        }

