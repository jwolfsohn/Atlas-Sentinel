"""
Port Traffic Data Ingestion Pipeline
Simulates MarineTraffic/AIS data ingestion
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
import random
import numpy as np

from backend.data.data_simulator import DataSimulator


class PortTrafficPipeline:
    """
    Ingests and stores port traffic data
    Simulates real-time AIS/MarineTraffic API
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize pipeline
        
        Args:
            data_dir: Directory to store data files (defaults to .data/ports)
        """
        if data_dir is None:
            data_dir = os.getenv('DATA_DIR', '.data')
        
        self.data_dir = Path(data_dir) / 'ports'
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.simulator = DataSimulator()
        self.cache_duration = timedelta(minutes=5)  # Cache for 5 minutes
    
    def ingest_port_traffic(self, port_id: str, force_refresh: bool = False) -> Dict:
        """
        Ingest port traffic data
        
        Args:
            port_id: Port identifier
            force_refresh: Force refresh even if cached
            
        Returns:
            Port traffic data
        """
        cache_file = self.data_dir / f"{port_id}_traffic.json"
        
        # Check cache
        if not force_refresh and cache_file.exists():
            cache_data = self._load_cache(cache_file)
            if cache_data and self._is_cache_valid(cache_data):
                return cache_data['data']
        
        # Generate new data
        traffic_data = self.simulator.generate_port_traffic(port_id)
        
        # Add historical context (load previous data if exists)
        if cache_file.exists():
            previous_data = self._load_cache(cache_file)
            if previous_data:
                traffic_data['previous_vessel_count'] = previous_data['data'].get('vessel_count', 0)
                traffic_data['trend'] = 'increasing' if traffic_data['vessel_count'] > previous_data['data'].get('vessel_count', 0) else 'decreasing'
        
        # Store in cache
        self._save_cache(cache_file, traffic_data)
        
        return traffic_data
    
    def ingest_all_ports(self) -> List[Dict]:
        """Ingest traffic data for all ports"""
        all_traffic = []
        for port in self.simulator.ports:
            traffic = self.ingest_port_traffic(port['id'])
            all_traffic.append(traffic)
        return all_traffic
    
    def get_port_history(self, port_id: str, hours: int = 24) -> List[Dict]:
        """
        Get historical port traffic data
        
        Args:
            port_id: Port identifier
            hours: Number of hours of history to retrieve
            
        Returns:
            List of historical traffic snapshots
        """
        history_file = self.data_dir / f"{port_id}_history.json"
        
        if history_file.exists():
            with open(history_file, 'r') as f:
                history = json.load(f)
            
            # Filter by time window
            cutoff_time = datetime.now() - timedelta(hours=hours)
            filtered = [
                entry for entry in history
                if datetime.fromisoformat(entry['timestamp']) >= cutoff_time
            ]
            return filtered
        
        return []
    
    def _save_cache(self, cache_file: Path, data: Dict):
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
    
    def update_port_history(self, port_id: str, traffic_data: Dict):
        """Append traffic data to historical record"""
        history_file = self.data_dir / f"{port_id}_history.json"
        
        history = []
        if history_file.exists():
            with open(history_file, 'r') as f:
                history = json.load(f)
        
        # Add new entry
        history.append({
            'timestamp': traffic_data.get('timestamp', datetime.now().isoformat()),
            'vessel_count': traffic_data.get('vessel_count', 0),
            'wait_time_hours': traffic_data.get('wait_time_hours', 0),
            'congestion_index': traffic_data.get('congestion_index', 0)
        })
        
        # Keep only last 7 days
        cutoff_time = datetime.now() - timedelta(days=7)
        history = [
            entry for entry in history
            if datetime.fromisoformat(entry['timestamp']) >= cutoff_time
        ]
        
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)

