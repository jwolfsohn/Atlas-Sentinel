"""
Ontology Layer for Supply Chain Entities and Relationships
Defines the knowledge graph structure
"""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class Port:
    """Port entity"""
    port_id: str
    name: str
    country: str
    latitude: float
    longitude: float
    capacity: int = 100
    current_vessels: int = 0
    wait_time_hours: float = 0.0
    congestion_index: float = 0.0
    weather_zone: Optional[str] = None
    region: Optional[str] = None


@dataclass
class Route:
    """Shipping route entity"""
    route_id: str
    origin_port_id: str
    destination_port_id: str
    name: str
    distance_km: float = 0.0
    typical_duration_hours: float = 0.0
    risk_score: float = 0.0
    risk_level: RiskLevel = RiskLevel.LOW
    active_shipments: int = 0


@dataclass
class Shipment:
    """Shipment entity"""
    shipment_id: str
    route_id: str
    origin_port_id: str
    destination_port_id: str
    status: str = "in_transit"
    current_location: Optional[Dict] = None
    estimated_arrival: Optional[datetime] = None
    delay_hours: float = 0.0


@dataclass
class RiskFactor:
    """Risk factor entity"""
    factor_id: str
    factor_type: str  # 'weather', 'sentiment', 'congestion', 'historical'
    severity: float = 0.0
    description: str = ""
    affected_entities: List[str] = field(default_factory=list)  # Port IDs, Route IDs
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class SupplyChainOntology:
    """
    Manages the supply chain knowledge graph
    """
    
    def __init__(self):
        self.ports: Dict[str, Port] = {}
        self.routes: Dict[str, Route] = {}
        self.shipments: Dict[str, Shipment] = {}
        self.risk_factors: Dict[str, RiskFactor] = {}
        
        # Relationship mappings
        self.port_to_routes: Dict[str, Set[str]] = {}  # port_id -> set of route_ids
        self.route_to_ports: Dict[str, Set[str]] = {}  # route_id -> set of port_ids
        self.port_to_weather_zones: Dict[str, str] = {}  # port_id -> weather_zone
        self.port_to_regions: Dict[str, str] = {}  # port_id -> region
        self.weather_zone_to_ports: Dict[str, Set[str]] = {}  # weather_zone -> set of port_ids
        self.region_to_ports: Dict[str, Set[str]] = {}  # region -> set of port_ids
    
    def add_port(self, port: Port):
        """Add a port to the ontology"""
        self.ports[port.port_id] = port
        
        # Update relationships
        if port.weather_zone:
            self.port_to_weather_zones[port.port_id] = port.weather_zone
            if port.weather_zone not in self.weather_zone_to_ports:
                self.weather_zone_to_ports[port.weather_zone] = set()
            self.weather_zone_to_ports[port.weather_zone].add(port.port_id)
        
        if port.region:
            self.port_to_regions[port.port_id] = port.region
            if port.region not in self.region_to_ports:
                self.region_to_ports[port.region] = set()
            self.region_to_ports[port.region].add(port.port_id)
    
    def add_route(self, route: Route):
        """Add a route to the ontology"""
        self.routes[route.route_id] = route
        
        # Update port-route relationships
        for port_id in [route.origin_port_id, route.destination_port_id]:
            if port_id not in self.port_to_routes:
                self.port_to_routes[port_id] = set()
            self.port_to_routes[port_id].add(route.route_id)
        
        self.route_to_ports[route.route_id] = {
            route.origin_port_id, route.destination_port_id
        }
    
    def add_shipment(self, shipment: Shipment):
        """Add a shipment to the ontology"""
        self.shipments[shipment.shipment_id] = shipment
    
    def add_risk_factor(self, risk_factor: RiskFactor):
        """Add a risk factor to the ontology"""
        self.risk_factors[risk_factor.factor_id] = risk_factor
    
    def get_ports_by_weather_zone(self, weather_zone: str) -> List[Port]:
        """Get all ports in a weather zone"""
        port_ids = self.weather_zone_to_ports.get(weather_zone, set())
        return [self.ports[pid] for pid in port_ids if pid in self.ports]
    
    def get_ports_by_region(self, region: str) -> List[Port]:
        """Get all ports in a region"""
        port_ids = self.region_to_ports.get(region, set())
        return [self.ports[pid] for pid in port_ids if pid in self.ports]
    
    def get_routes_by_port(self, port_id: str) -> List[Route]:
        """Get all routes connected to a port"""
        route_ids = self.port_to_routes.get(port_id, set())
        return [self.routes[rid] for rid in route_ids if rid in self.routes]
    
    def get_affected_routes(self, risk_factor: RiskFactor) -> List[Route]:
        """Get routes affected by a risk factor"""
        affected_route_ids = [
            rid for rid in risk_factor.affected_entities 
            if rid in self.routes
        ]
        return [self.routes[rid] for rid in affected_route_ids]
    
    def update_port_metrics(self, port_id: str, metrics: Dict):
        """Update port congestion and vessel metrics"""
        if port_id in self.ports:
            port = self.ports[port_id]
            port.current_vessels = metrics.get('vessel_count', port.current_vessels)
            port.wait_time_hours = metrics.get('wait_time_hours', port.wait_time_hours)
            port.congestion_index = metrics.get('congestion_index', port.congestion_index)
    
    def update_route_risk(self, route_id: str, risk_score: float, risk_level: RiskLevel):
        """Update route risk assessment"""
        if route_id in self.routes:
            route = self.routes[route_id]
            route.risk_score = risk_score
            route.risk_level = risk_level
    
    def get_top_risk_routes(self, limit: int = 10) -> List[Route]:
        """Get top N routes by risk score"""
        all_routes = list(self.routes.values())
        sorted_routes = sorted(all_routes, key=lambda r: r.risk_score, reverse=True)
        return sorted_routes[:limit]

