"""
FastAPI Backend for Atlas Sentinel
Main API server that connects ML models with frontend
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Dict, Optional
import asyncio
from datetime import datetime

from backend.ml.risk_scorer import RiskScorer
from backend.ml.sentiment_analyzer import SentimentAnalyzer
from backend.ml.congestion_analyzer import CongestionAnalyzer
from backend.data.ontology import SupplyChainOntology, Port, Route, RiskLevel
from backend.data.data_simulator import DataSimulator
from backend.data.pipelines.pipeline_orchestrator import PipelineOrchestrator
from backend.config import DATA_DIR

app = FastAPI(title="Atlas Sentinel API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
risk_scorer = RiskScorer()
sentiment_analyzer = SentimentAnalyzer()
congestion_analyzer = CongestionAnalyzer()
ontology = SupplyChainOntology()
data_simulator = DataSimulator()
pipeline_orchestrator = PipelineOrchestrator(data_dir=DATA_DIR)

# Initialize ontology with sample data
def initialize_ontology():
    """Initialize ontology with sample ports and routes"""
    # Add ports
    for port_data in data_simulator.ports:
        port = Port(
            port_id=port_data['id'],
            name=port_data['name'],
            country=port_data['country'],
            latitude=port_data['lat'],
            longitude=port_data['lon'],
            region=port_data['region'],
            weather_zone=port_data['region']
        )
        ontology.add_port(port)
    
    # Add routes
    for route_data in data_simulator.routes:
        route = Route(
            route_id=route_data['route_id'],
            origin_port_id=route_data['origin'],
            destination_port_id=route_data['destination'],
            name=route_data['name'],
            distance_km=route_data['distance_km'],
            typical_duration_hours=route_data['typical_duration_hours']
        )
        ontology.add_route(route)

# Initialize on startup
initialize_ontology()

def _weather_severity_value(severity: str) -> int:
    """Convert weather severity to numeric value for comparison"""
    severity_map = {'none': 0, 'light': 1, 'moderate': 2, 'severe': 3, 'extreme': 4}
    return severity_map.get(severity, 0)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Atlas Sentinel API", 
        "status": "running",
        "data_directory": DATA_DIR,
        "data_summary": pipeline_orchestrator.get_data_summary()
    }

@app.get("/api/data/summary")
async def get_data_summary():
    """Get summary of stored data"""
    return pipeline_orchestrator.get_data_summary()

@app.post("/api/data/refresh")
async def refresh_data():
    """Force refresh all data caches"""
    pipeline_orchestrator.ingest_all_data(force_refresh=True)
    return {"message": "Data refreshed", "timestamp": datetime.now().isoformat()}

@app.get("/api/routes")
async def get_routes():
    """Get all routes with current risk assessments"""
    # Use pipeline orchestrator to ingest data (uses cached data when available)
    routes_data = []
    for route in data_simulator.routes:
        route_data = pipeline_orchestrator.ingest_route_data(route['route_id'])
        if route_data:
            routes_data.append(route_data)
    
    # Fallback to simulator if pipeline returns empty
    if not routes_data:
        routes_data = data_simulator.generate_all_routes_data()
    
    results = []
    for route_data in routes_data:
        route_id = route_data['route_id']
        
        # Analyze sentiment for both ports
        origin_news = route_data['origin_port']['news']
        dest_news = route_data['destination_port']['news']
        all_news = origin_news + dest_news
        
        origin_sentiment = sentiment_analyzer.analyze_articles(origin_news)
        dest_sentiment = sentiment_analyzer.analyze_articles(dest_news)
        combined_sentiment = sentiment_analyzer.analyze_articles(all_news)
        
        # Analyze congestion for both ports
        origin_traffic = route_data['origin_port']['traffic']
        dest_traffic = route_data['destination_port']['traffic']
        
        origin_congestion = congestion_analyzer.compute_congestion_index(
            origin_traffic['vessel_count'],
            origin_traffic['capacity'],
            origin_traffic['wait_time_hours']
        )
        dest_congestion = congestion_analyzer.compute_congestion_index(
            dest_traffic['vessel_count'],
            dest_traffic['capacity'],
            dest_traffic['wait_time_hours']
        )
        
        # Use worst congestion (bottleneck)
        max_congestion = max(origin_congestion, dest_congestion)
        avg_congestion_data = {
            'congestion_index': max_congestion,
            'vessel_count': (origin_traffic['vessel_count'] + dest_traffic['vessel_count']) // 2,
            'wait_time_hours': max(origin_traffic['wait_time_hours'], dest_traffic['wait_time_hours'])
        }
        
        # Use worst weather (bottleneck)
        origin_weather = route_data['origin_port']['weather']
        dest_weather = route_data['destination_port']['weather']
        worst_weather = origin_weather if (
            _weather_severity_value(origin_weather['severity']) >= 
            _weather_severity_value(dest_weather['severity'])
        ) else dest_weather
        
        # Compute risk
        risk_assessment = risk_scorer.compute_route_risk(
            route_id=route_id,
            weather_data=worst_weather,
            sentiment_data=combined_sentiment,
            congestion_data=avg_congestion_data
        )
        
        # Update ontology
        risk_level = RiskLevel(risk_assessment['risk_level'])
        ontology.update_route_risk(route_id, risk_assessment['total_risk'], risk_level)
        
        # Get route from ontology
        route = ontology.routes.get(route_id)
        
        results.append({
            'route_id': route_id,
            'name': route_data['route_name'],
            'origin': {
                'port_id': route_data['origin_port']['id'],
                'name': next(p['name'] for p in data_simulator.ports if p['id'] == route_data['origin_port']['id']),
                'latitude': origin_traffic['latitude'],
                'longitude': origin_traffic['longitude'],
                'congestion': origin_congestion,
                'vessel_count': origin_traffic['vessel_count']
            },
            'destination': {
                'port_id': route_data['destination_port']['id'],
                'name': next(p['name'] for p in data_simulator.ports if p['id'] == route_data['destination_port']['id']),
                'latitude': dest_traffic['latitude'],
                'longitude': dest_traffic['longitude'],
                'congestion': dest_congestion,
                'vessel_count': dest_traffic['vessel_count']
            },
            'risk_score': risk_assessment['total_risk'],
            'risk_level': risk_assessment['risk_level'],
            'risk_components': risk_assessment['components'],
            'weather': worst_weather,
            'sentiment': combined_sentiment,
            'congestion': avg_congestion_data
        })
    
    # Sort by risk score
    results.sort(key=lambda x: x['risk_score'], reverse=True)
    
    return {"routes": results, "timestamp": datetime.now().isoformat()}

@app.get("/api/routes/top-risk")
async def get_top_risk_routes(limit: int = 10):
    """Get top N at-risk routes"""
    routes_response = await get_routes()
    top_routes = routes_response['routes'][:limit]
    
    # Add predicted delays
    risk_assessments = [
        {
            'route_id': r['route_id'],
            'total_risk': r['risk_score'],
            'risk_level': r['risk_level']
        }
        for r in top_routes
    ]
    
    delay_predictions = risk_scorer.predict_cascading_delays(risk_assessments)
    
    # Merge delay predictions
    for route in top_routes:
        prediction = next((d for d in delay_predictions if d['route_id'] == route['route_id']), None)
        if prediction:
            route['predicted_delay_hours'] = prediction['predicted_delay_hours']
            route['cascading_delay'] = prediction['cascading_delay']
    
    return {
        "routes": top_routes,
        "limit": limit,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/ports")
async def get_ports():
    """Get all ports with current metrics"""
    ports_data = []
    
    for port_id in ontology.ports.keys():
        # Use pipeline to get port traffic (uses cache)
        traffic = pipeline_orchestrator.port_traffic.ingest_port_traffic(port_id)
        if not traffic:
            # Fallback to simulator
            traffic = data_simulator.generate_port_traffic(port_id)
        congestion_metrics = congestion_analyzer.compute_congestion_index(
            traffic['vessel_count'],
            traffic['capacity'],
            traffic['wait_time_hours']
        )
        
        port = ontology.ports[port_id]
        ports_data.append({
            'port_id': port_id,
            'name': port.name,
            'country': port.country,
            'latitude': port.latitude,
            'longitude': port.longitude,
            'region': port.region,
            'vessel_count': traffic['vessel_count'],
            'capacity': traffic['capacity'],
            'wait_time_hours': traffic['wait_time_hours'],
            'congestion_index': congestion_metrics
        })
    
    return {"ports": ports_data, "timestamp": datetime.now().isoformat()}

@app.get("/api/route/{route_id}")
async def get_route_details(route_id: str):
    """Get detailed information for a specific route"""
    # Use pipeline orchestrator to get route data
    route_data = pipeline_orchestrator.ingest_route_data(route_id)
    if not route_data:
        # Fallback to simulator
        route_data = data_simulator.generate_route_data(route_id)
    
    # Full analysis
    origin_sentiment = sentiment_analyzer.analyze_articles(route_data['origin_port']['news'])
    dest_sentiment = sentiment_analyzer.analyze_articles(route_data['destination_port']['news'])
    
    origin_congestion = congestion_analyzer.compute_congestion_index(
        route_data['origin_port']['traffic']['vessel_count'],
        route_data['origin_port']['traffic']['capacity'],
        route_data['origin_port']['traffic']['wait_time_hours']
    )
    dest_congestion = congestion_analyzer.compute_congestion_index(
        route_data['destination_port']['traffic']['vessel_count'],
        route_data['destination_port']['traffic']['capacity'],
        route_data['destination_port']['traffic']['wait_time_hours']
    )
    
    combined_sentiment = sentiment_analyzer.analyze_articles(
        route_data['origin_port']['news'] + route_data['destination_port']['news']
    )
    
    worst_weather = route_data['origin_port']['weather'] if (
        _weather_severity_value(route_data['origin_port']['weather']['severity']) >=
        _weather_severity_value(route_data['destination_port']['weather']['severity'])
    ) else route_data['destination_port']['weather']
    
    max_congestion_data = {
        'congestion_index': max(origin_congestion, dest_congestion),
        'vessel_count': max(
            route_data['origin_port']['traffic']['vessel_count'],
            route_data['destination_port']['traffic']['vessel_count']
        ),
        'wait_time_hours': max(
            route_data['origin_port']['traffic']['wait_time_hours'],
            route_data['destination_port']['traffic']['wait_time_hours']
        )
    }
    
    risk_assessment = risk_scorer.compute_route_risk(
        route_id=route_id,
        weather_data=worst_weather,
        sentiment_data=combined_sentiment,
        congestion_data=max_congestion_data
    )
    
    return {
        "route_id": route_id,
        "route_name": route_data['route_name'],
        "risk_assessment": risk_assessment,
        "origin_port": {
            "data": route_data['origin_port']['traffic'],
            "sentiment": origin_sentiment,
            "congestion": origin_congestion,
            "weather": route_data['origin_port']['weather'],
            "news": route_data['origin_port']['news']
        },
        "destination_port": {
            "data": route_data['destination_port']['traffic'],
            "sentiment": dest_sentiment,
            "congestion": dest_congestion,
            "weather": route_data['destination_port']['weather'],
            "news": route_data['destination_port']['news']
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/alerts")
async def get_alerts(threshold: float = 0.7):
    """Get active alerts (routes with risk above threshold)"""
    routes_response = await get_routes()
    alerts = [
        route for route in routes_response['routes']
        if route['risk_score'] >= threshold
    ]
    
    return {
        "alerts": alerts,
        "count": len(alerts),
        "threshold": threshold,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

