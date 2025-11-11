"""
Data Simulator for Real-time Supply Chain Data
Generates realistic simulated data for ports, routes, weather, and news
"""

import random
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List
import json


class DataSimulator:
    """
    Simulates real-time data from various sources:
    - Port traffic (MarineTraffic/AIS)
    - Weather alerts (NOAA)
    - News articles (NewsAPI)
    """
    
    def __init__(self, seed: int = 42):
        """Initialize simulator with random seed"""
        random.seed(seed)
        np.random.seed(seed)
        
        # Major global ports
        self.ports = [
            {'id': 'LAX', 'name': 'Los Angeles', 'country': 'USA', 'lat': 33.75, 'lon': -118.25, 'region': 'North America'},
            {'id': 'NYC', 'name': 'New York', 'country': 'USA', 'lat': 40.68, 'lon': -74.04, 'region': 'North America'},
            {'id': 'SHG', 'name': 'Shanghai', 'country': 'China', 'lat': 31.23, 'lon': 121.47, 'region': 'Asia'},
            {'id': 'SGP', 'name': 'Singapore', 'country': 'Singapore', 'lat': 1.29, 'lon': 103.85, 'region': 'Asia'},
            {'id': 'RTM', 'name': 'Rotterdam', 'country': 'Netherlands', 'lat': 51.92, 'lon': 4.48, 'region': 'Europe'},
            {'id': 'HAM', 'name': 'Hamburg', 'country': 'Germany', 'lat': 53.55, 'lon': 9.99, 'region': 'Europe'},
            {'id': 'DXB', 'name': 'Dubai', 'country': 'UAE', 'lat': 25.27, 'lon': 55.30, 'region': 'Middle East'},
            {'id': 'HKG', 'name': 'Hong Kong', 'country': 'China', 'lat': 22.32, 'lon': 114.17, 'region': 'Asia'},
            {'id': 'LON', 'name': 'London', 'country': 'UK', 'lat': 51.51, 'lon': -0.13, 'region': 'Europe'},
            {'id': 'TOK', 'name': 'Tokyo', 'country': 'Japan', 'lat': 35.68, 'lon': 139.77, 'region': 'Asia'},
        ]
        
        # Generate routes between ports
        self.routes = []
        for i, origin in enumerate(self.ports):
            for dest in self.ports[i+1:]:
                route_id = f"{origin['id']}-{dest['id']}"
                distance = self._calculate_distance(
                    origin['lat'], origin['lon'],
                    dest['lat'], dest['lon']
                )
                self.routes.append({
                    'route_id': route_id,
                    'origin': origin['id'],
                    'destination': dest['id'],
                    'name': f"{origin['name']} → {dest['name']}",
                    'distance_km': distance,
                    'typical_duration_hours': distance / 25.0  # ~25 km/h average
                })
        
        # Weather zones
        self.weather_zones = {
            'North America': ['storm', 'hurricane', 'fog'],
            'Asia': ['typhoon', 'storm', 'fog'],
            'Europe': ['storm', 'wind', 'ice'],
            'Middle East': ['wind', 'storm']
        }
        
        # News templates
        self.news_templates = [
            "Port {port} experiencing delays due to {issue}",
            "Weather alert: {severity} {type} affecting {region} shipping lanes",
            "Congestion at {port} port reaches critical levels",
            "Supply chain disruption reported in {region}",
            "Vessel backlog at {port} causing extended wait times",
            "Storm system impacting {region} maritime operations",
            "Port {port} operations running smoothly",
            "Improved efficiency at {port} reduces wait times"
        ]
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points (Haversine formula)"""
        from math import radians, sin, cos, sqrt, atan2
        R = 6371  # Earth radius in km
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        return R * c
    
    def generate_port_traffic(self, port_id: str) -> Dict:
        """Generate port traffic data"""
        port = next((p for p in self.ports if p['id'] == port_id), None)
        if not port:
            return {}
        
        # Simulate congestion (some ports more congested)
        base_congestion = random.uniform(0.2, 0.8) if port_id in ['LAX', 'SHG', 'SGP'] else random.uniform(0.1, 0.5)
        
        vessel_count = int(30 + base_congestion * 40)
        wait_time = base_congestion * 48 + random.uniform(-10, 10)
        wait_time = max(0, wait_time)
        
        return {
            'port_id': port_id,
            'port_name': port['name'],
            'vessel_count': vessel_count,
            'capacity': 100,
            'wait_time_hours': round(wait_time, 2),
            'congestion_index': round(base_congestion, 3),
            'timestamp': datetime.now().isoformat(),
            'latitude': port['lat'],
            'longitude': port['lon']
        }
    
    def generate_weather_alert(self, region: str = None) -> Dict:
        """Generate weather alert data"""
        if not region:
            region = random.choice(list(self.weather_zones.keys()))
        
        weather_types = self.weather_zones.get(region, ['storm'])
        weather_type = random.choice(weather_types)
        
        # Severity distribution (more moderate/severe than extreme)
        severity_weights = ['light', 'moderate', 'severe', 'extreme']
        severity = np.random.choice(severity_weights, p=[0.3, 0.4, 0.25, 0.05])
        
        duration = random.uniform(6, 72) if severity in ['severe', 'extreme'] else random.uniform(2, 24)
        
        # Get a port in this region
        region_ports = [p for p in self.ports if p['region'] == region]
        affected_port = random.choice(region_ports) if region_ports else self.ports[0]
        
        return {
            'weather_zone': region,
            'type': weather_type,
            'severity': severity,
            'duration_hours': round(duration, 1),
            'affected_port_id': affected_port['id'],
            'affected_port_name': affected_port['name'],
            'latitude': affected_port['lat'],
            'longitude': affected_port['lon'],
            'timestamp': datetime.now().isoformat()
        }
    
    def generate_news_article(self, port_id: str = None, region: str = None) -> Dict:
        """Generate news article with sentiment"""
        if not port_id:
            port = random.choice(self.ports)
            port_id = port['id']
            port_name = port['name']
            region = port['region']
        else:
            port = next((p for p in self.ports if p['id'] == port_id), self.ports[0])
            port_name = port['name']
            region = port['region']
        
        # Determine if article is negative (disruption) or positive
        is_negative = random.random() < 0.6  # 60% chance of negative news
        
        if is_negative:
            issues = ['congestion', 'weather delays', 'equipment failure', 'labor strike', 'backlog']
            issue = random.choice(issues)
            template = random.choice(self.news_templates[:6])  # Negative templates
            content = template.format(port=port_name, issue=issue, region=region, 
                                    severity='severe', type='storm')
            sentiment_score = random.uniform(-0.8, -0.2)
        else:
            template = random.choice(self.news_templates[6:])  # Positive templates
            content = template.format(port=port_name, region=region)
            sentiment_score = random.uniform(0.2, 0.8)
        
        return {
            'article_id': f"news_{random.randint(1000, 9999)}",
            'title': content[:80] + '...',
            'content': content,
            'source': random.choice(['Maritime News', 'Shipping Times', 'Port Authority', 'Trade Journal']),
            'port_id': port_id,
            'port_name': port_name,
            'region': region,
            'sentiment_score': round(sentiment_score, 3),
            'timestamp': datetime.now().isoformat()
        }
    
    def generate_route_data(self, route_id: str = None) -> Dict:
        """Generate complete route data with all risk factors"""
        if not route_id:
            route = random.choice(self.routes)
        else:
            route = next((r for r in self.routes if r['route_id'] == route_id), self.routes[0])
        
        # Get port data
        origin_port = next(p for p in self.ports if p['id'] == route['origin'])
        dest_port = next(p for p in self.ports if p['id'] == route['destination'])
        
        # Generate data for both ports
        origin_traffic = self.generate_port_traffic(route['origin'])
        dest_traffic = self.generate_port_traffic(route['destination'])
        
        # Generate weather for regions
        origin_weather = self.generate_weather_alert(origin_port['region'])
        dest_weather = self.generate_weather_alert(dest_port['region'])
        
        # Generate news articles
        origin_news = [self.generate_news_article(route['origin']) for _ in range(random.randint(1, 5))]
        dest_news = [self.generate_news_article(route['destination']) for _ in range(random.randint(1, 5))]
        
        return {
            'route_id': route['route_id'],
            'route_name': route['name'],
            'origin_port': {
                'id': route['origin'],
                'traffic': origin_traffic,
                'weather': origin_weather,
                'news': origin_news
            },
            'destination_port': {
                'id': route['destination'],
                'traffic': dest_traffic,
                'weather': dest_weather,
                'news': dest_news
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def generate_all_routes_data(self) -> List[Dict]:
        """Generate data for all routes"""
        return [self.generate_route_data(route['route_id']) for route in self.routes]

