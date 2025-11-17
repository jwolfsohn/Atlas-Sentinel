"""
Weather Data Ingestion Pipeline
Simulates NOAA weather alert ingestion
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
import random

from backend.data.data_simulator import DataSimulator


class WeatherPipeline:
    """
    Ingests and stores weather alert data
    Simulates NOAA API ingestion
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize pipeline
        
        Args:
            data_dir: Directory to store data files (defaults to .data/weather)
        """
        if data_dir is None:
            data_dir = os.getenv('DATA_DIR', '.data')
        
        self.data_dir = Path(data_dir) / 'weather'
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.simulator = DataSimulator()
        self.cache_duration = timedelta(minutes=10)  # Cache for 10 minutes
    
    def ingest_weather_alerts(self, region: Optional[str] = None, force_refresh: bool = False) -> List[Dict]:
        """
        Ingest weather alerts for a region or all regions
        
        Args:
            region: Specific region to query (None for all)
            force_refresh: Force refresh even if cached
            
        Returns:
            List of weather alerts
        """
        if region:
            cache_file = self.data_dir / f"{region}_alerts.json"
            regions = [region]
        else:
            cache_file = self.data_dir / "all_alerts.json"
            regions = list(self.simulator.weather_zones.keys())
        
        # Check cache
        if not force_refresh and cache_file.exists():
            cache_data = self._load_cache(cache_file)
            if cache_data and self._is_cache_valid(cache_data):
                return cache_data['data']
        
        # Generate alerts for each region
        alerts = []
        for reg in regions:
            alert = self.simulator.generate_weather_alert(reg)
            alerts.append(alert)
        
        # Store in cache
        self._save_cache(cache_file, alerts)
        
        # Store individual alerts
        for alert in alerts:
            self._store_alert(alert)
        
        return alerts
    
    def get_active_alerts(self, severity_threshold: str = 'moderate') -> List[Dict]:
        """
        Get currently active weather alerts
        
        Args:
            severity_threshold: Minimum severity level
            
        Returns:
            List of active alerts
        """
        severity_levels = {'light': 1, 'moderate': 2, 'severe': 3, 'extreme': 4}
        threshold_level = severity_levels.get(severity_threshold, 2)
        
        all_alerts = self.ingest_weather_alerts()
        active = []
        
        for alert in all_alerts:
            alert_level = severity_levels.get(alert['severity'], 0)
            if alert_level >= threshold_level:
                # Check if alert is still active (within duration)
                alert_time = datetime.fromisoformat(alert['timestamp'])
                duration = timedelta(hours=alert.get('duration_hours', 24))
                
                if datetime.now() - alert_time < duration:
                    active.append(alert)
        
        return active
    
    def get_weather_for_port(self, port_id: str) -> Optional[Dict]:
        """Get weather alert for a specific port"""
        port = next((p for p in self.simulator.ports if p['id'] == port_id), None)
        if not port:
            return None
        
        region = port['region']
        alerts = self.ingest_weather_alerts(region)
        
        # Return most severe alert
        if alerts:
            severity_levels = {'light': 1, 'moderate': 2, 'severe': 3, 'extreme': 4}
            return max(alerts, key=lambda a: severity_levels.get(a['severity'], 0))
        
        return None
    
    def _store_alert(self, alert: Dict):
        """Store individual alert to history"""
        alert_id = f"{alert['weather_zone']}_{alert['timestamp']}"
        alert_file = self.data_dir / f"alerts/{alert_id}.json"
        alert_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(alert_file, 'w') as f:
            json.dump(alert, f, indent=2)
    
    def _save_cache(self, cache_file: Path, data: List[Dict]):
        """Save data to cache file"""
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, indent=2)
    
    def _load_cache(self, cache_file: Path) -> Optional[Dict]:
        """Load data from cache file"""
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None
    
    def _is_cache_valid(self, cache_data: Dict) -> bool:
        """Check if cache is still valid"""
        if 'timestamp' not in cache_data:
            return False
        
        cache_time = datetime.fromisoformat(cache_data['timestamp'])
        return datetime.now() - cache_time < self.cache_duration

