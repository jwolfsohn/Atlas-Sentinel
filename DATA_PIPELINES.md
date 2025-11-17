# Data Ingestion Pipelines

Atlas Sentinel uses structured data ingestion pipelines to collect, cache, and store supply chain data from multiple sources.

## Architecture

The data ingestion system consists of three main pipelines:

1. **Port Traffic Pipeline** - Simulates MarineTraffic/AIS data
2. **Weather Pipeline** - Simulates NOAA weather alerts
3. **News Pipeline** - Simulates NewsAPI articles

All pipelines are orchestrated by the `PipelineOrchestrator` which coordinates data flow and caching.

## Data Storage

All data files are stored in the `.data/` directory (gitignored):

```
.data/
├── ports/
│   ├── {port_id}_traffic.json      # Cached port traffic
│   ├── {port_id}_history.json      # Historical traffic data
│   └── ...
├── weather/
│   ├── {region}_alerts.json        # Cached weather alerts
│   ├── alerts/
│   │   └── {alert_id}.json         # Individual alert records
│   └── ...
└── news/
    ├── {port_id}_articles.json     # Cached news articles
    ├── articles/
    │   └── {article_id}.json       # Individual article records
    └── ...
```

## Configuration

Data storage location and cache durations are configured via environment variables (see `.env.example`):

- `DATA_DIR` - Base directory for data storage (default: `.data`)
- `PORT_TRAFFIC_CACHE_DURATION` - Cache duration in seconds (default: 300)
- `WEATHER_CACHE_DURATION` - Cache duration in seconds (default: 600)
- `NEWS_CACHE_DURATION` - Cache duration in seconds (default: 900)

## Pipeline Components

### Port Traffic Pipeline

**File**: `backend/data/pipelines/port_traffic_pipeline.py`

- Ingests port traffic data (vessel counts, wait times, congestion)
- Caches data for 5 minutes by default
- Maintains historical records (last 7 days)
- Tracks trends (increasing/decreasing)

**Usage**:
```python
from backend.data.pipelines.port_traffic_pipeline import PortTrafficPipeline

pipeline = PortTrafficPipeline()
traffic = pipeline.ingest_port_traffic('LAX')
history = pipeline.get_port_history('LAX', hours=24)
```

### Weather Pipeline

**File**: `backend/data/pipelines/weather_pipeline.py`

- Ingests weather alerts by region
- Caches data for 10 minutes by default
- Filters active alerts by severity
- Stores individual alert records

**Usage**:
```python
from backend.data.pipelines.weather_pipeline import WeatherPipeline

pipeline = WeatherPipeline()
alerts = pipeline.ingest_weather_alerts(region='Asia')
active = pipeline.get_active_alerts(severity_threshold='moderate')
port_weather = pipeline.get_weather_for_port('SHG')
```

### News Pipeline

**File**: `backend/data/pipelines/news_pipeline.py`

- Ingests news articles by port or region
- Caches data for 15 minutes by default
- Filters by sentiment and time window
- Groups articles by sentiment (negative/positive/neutral)

**Usage**:
```python
from backend.data.pipelines.news_pipeline import NewsPipeline

pipeline = NewsPipeline()
articles = pipeline.ingest_news_articles(port_id='LAX', limit=10)
recent = pipeline.get_recent_articles(port_id='LAX', hours=24)
by_sentiment = pipeline.get_articles_by_sentiment(port_id='LAX', negative_only=True)
```

### Pipeline Orchestrator

**File**: `backend/data/pipelines/pipeline_orchestrator.py`

Coordinates all pipelines and provides high-level data access:

```python
from backend.data.pipelines.pipeline_orchestrator import PipelineOrchestrator

orchestrator = PipelineOrchestrator()

# Ingest all data
all_data = orchestrator.ingest_all_data(force_refresh=False)

# Get route-specific data
route_data = orchestrator.ingest_route_data('LAX-SHG')

# Get data summary
summary = orchestrator.get_data_summary()
```

## API Endpoints

The FastAPI backend exposes data pipeline endpoints:

- `GET /api/data/summary` - Get summary of stored data
- `POST /api/data/refresh` - Force refresh all data caches

## Caching Strategy

Each pipeline implements intelligent caching:

1. **Cache Check**: Before generating new data, check if cached data exists and is still valid
2. **Cache Storage**: Store data with timestamp in JSON files
3. **Cache Invalidation**: Cache expires after configured duration
4. **Force Refresh**: Can bypass cache when needed

## Data Privacy

All data files are:
- Stored in `.data/` directory (gitignored)
- Never committed to version control
- Can be safely deleted and regenerated
- Use simulated/fake data (no real API keys required)

## Future Enhancements

The pipeline architecture is designed to easily integrate real APIs:

1. Replace `DataSimulator` calls with actual API clients
2. Add API keys to `.env` file
3. Implement rate limiting and error handling
4. Add data validation and transformation layers

## Example: Adding Real API Integration

```python
# In port_traffic_pipeline.py
def _fetch_from_api(self, port_id: str) -> Dict:
    """Fetch real data from MarineTraffic API"""
    api_key = os.getenv('MARINETRAFFIC_API_KEY')
    response = requests.get(
        f'https://api.marinetraffic.com/v1/port/{port_id}',
        params={'api_key': api_key}
    )
    return response.json()
```

