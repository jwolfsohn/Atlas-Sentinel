"""
Data Pipeline Orchestrator
Coordinates all data ingestion pipelines
"""

import os
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

from backend.data.pipelines.port_traffic_pipeline import PortTrafficPipeline
from backend.data.pipelines.weather_pipeline import WeatherPipeline
from backend.data.pipelines.news_pipeline import NewsPipeline


class PipelineOrchestrator:
    """
    Orchestrates all data ingestion pipelines
    Manages data flow and coordination
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize orchestrator
        
        Args:
            data_dir: Base directory for data storage
        """
        if data_dir is None:
            data_dir = os.getenv('DATA_DIR', '.data')
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize pipelines
        self.port_traffic = PortTrafficPipeline(data_dir)
        self.weather = WeatherPipeline(data_dir)
        self.news = NewsPipeline(data_dir)
    
    def ingest_all_data(self, force_refresh: bool = False) -> Dict:
        """
        Ingest data from all sources
        
        Args:
            force_refresh: Force refresh all caches
            
        Returns:
            Dict with all ingested data
        """
        result = {
            'timestamp': datetime.now().isoformat(),
            'ports': [],
            'weather': [],
            'news': {}
        }
        
        # Ingest port traffic
        result['ports'] = self.port_traffic.ingest_all_ports()
        
        # Ingest weather alerts
        result['weather'] = self.weather.ingest_weather_alerts(force_refresh=force_refresh)
        
        # Ingest news articles (by region)
        regions = ['North America', 'Asia', 'Europe', 'Middle East']
        result['news'] = {}
        for region in regions:
            result['news'][region] = self.news.ingest_news_articles(
                region=region,
                limit=10,
                force_refresh=force_refresh
            )
        
        return result
    
    def ingest_route_data(self, route_id: str, force_refresh: bool = False) -> Dict:
        """
        Ingest all data for a specific route
        
        Args:
            route_id: Route identifier (e.g., 'LAX-SHG')
            force_refresh: Force refresh caches
            
        Returns:
            Complete route data with all sources
        """
        from backend.data.data_simulator import DataSimulator
        
        simulator = DataSimulator()
        route = next((r for r in simulator.routes if r['route_id'] == route_id), None)
        
        if not route:
            return {}
        
        origin_id = route['origin']
        dest_id = route['destination']
        
        # Get port data
        origin_port = next(p for p in simulator.ports if p['id'] == origin_id)
        dest_port = next(p for p in simulator.ports if p['id'] == dest_id)
        
        # Ingest all data sources
        origin_traffic = self.port_traffic.ingest_port_traffic(origin_id, force_refresh)
        dest_traffic = self.port_traffic.ingest_port_traffic(dest_id, force_refresh)
        
        origin_weather = self.weather.get_weather_for_port(origin_id)
        dest_weather = self.weather.get_weather_for_port(dest_id)
        
        origin_news = self.news.ingest_news_articles(port_id=origin_id, limit=5, force_refresh=force_refresh)
        dest_news = self.news.ingest_news_articles(port_id=dest_id, limit=5, force_refresh=force_refresh)
        
        return {
            'route_id': route_id,
            'route_name': route['name'],
            'origin_port': {
                'id': origin_id,
                'traffic': origin_traffic,
                'weather': origin_weather or {},
                'news': origin_news
            },
            'destination_port': {
                'id': dest_id,
                'traffic': dest_traffic,
                'weather': dest_weather or {},
                'news': dest_news
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def get_data_summary(self) -> Dict:
        """Get summary of all stored data"""
        summary = {
            'data_directory': str(self.data_dir),
            'ports': {
                'count': len(list((self.data_dir / 'ports').glob('*_traffic.json'))) if (self.data_dir / 'ports').exists() else 0,
                'history_files': len(list((self.data_dir / 'ports').glob('*_history.json'))) if (self.data_dir / 'ports').exists() else 0
            },
            'weather': {
                'alert_files': len(list((self.data_dir / 'weather' / 'alerts').glob('*.json'))) if (self.data_dir / 'weather' / 'alerts').exists() else 0,
                'cache_files': len(list((self.data_dir / 'weather').glob('*_alerts.json'))) if (self.data_dir / 'weather').exists() else 0
            },
            'news': {
                'article_files': len(list((self.data_dir / 'news' / 'articles').glob('*.json'))) if (self.data_dir / 'news' / 'articles').exists() else 0,
                'cache_files': len(list((self.data_dir / 'news').glob('*_articles.json'))) if (self.data_dir / 'news').exists() else 0
            }
        }
        
        return summary
    
    async def continuous_ingestion(self, interval_seconds: int = 300):
        """
        Run continuous data ingestion in background
        
        Args:
            interval_seconds: Interval between ingestion cycles (default 5 minutes)
        """
        while True:
            try:
                self.ingest_all_data(force_refresh=True)
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                print(f"Error in continuous ingestion: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error

