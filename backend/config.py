"""
Configuration Management
Loads settings from environment variables
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Data Configuration
DATA_DIR = os.getenv('DATA_DIR', '.data')
DATA_DIR_PATH = Path(DATA_DIR)
DATA_DIR_PATH.mkdir(parents=True, exist_ok=True)

# API Configuration
API_HOST = os.getenv('API_HOST', '0.0.0.0')
API_PORT = int(os.getenv('API_PORT', 8000))

# Cache Durations (in seconds)
PORT_TRAFFIC_CACHE_DURATION = int(os.getenv('PORT_TRAFFIC_CACHE_DURATION', 300))
WEATHER_CACHE_DURATION = int(os.getenv('WEATHER_CACHE_DURATION', 600))
NEWS_CACHE_DURATION = int(os.getenv('NEWS_CACHE_DURATION', 900))

# ML Model Weights
RISK_WEATHER_WEIGHT = float(os.getenv('RISK_WEATHER_WEIGHT', 0.35))
RISK_SENTIMENT_WEIGHT = float(os.getenv('RISK_SENTIMENT_WEIGHT', 0.30))
RISK_CONGESTION_WEIGHT = float(os.getenv('RISK_CONGESTION_WEIGHT', 0.25))
RISK_HISTORICAL_WEIGHT = float(os.getenv('RISK_HISTORICAL_WEIGHT', 0.10))

# Alert Thresholds
HIGH_RISK_THRESHOLD = float(os.getenv('HIGH_RISK_THRESHOLD', 0.7))
MEDIUM_RISK_THRESHOLD = float(os.getenv('MEDIUM_RISK_THRESHOLD', 0.4))

# External API Keys (for future integration)
MARINETRAFFIC_API_KEY = os.getenv('MARINETRAFFIC_API_KEY', '')
NOAA_API_KEY = os.getenv('NOAA_API_KEY', '')
NEWSAPI_KEY = os.getenv('NEWSAPI_KEY', '')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

