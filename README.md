# Atlas Sentinel - Global Supply Chain Early-Warning System

A real-time dashboard that flags potential global supply chain disruptions by integrating diverse data sources and ML-powered risk analysis.

## Features

- **Real-time Risk Scoring**: ML-powered risk assessment combining weather, sentiment, and congestion data
- **Interactive Map Visualization**: Leaflet-based map showing at-risk routes and ports
- **Multi-modal Data Integration**: Shipping logs, port congestion, weather alerts, and news sentiment
- **Predictive Analytics**: Cascading delay predictions and risk factor analysis

## Tech Stack

- **Frontend**: React + Vite
- **Backend**: Python FastAPI
- **ML**: scikit-learn, transformers, custom risk scoring models
- **Visualization**: Leaflet, Recharts

## Setup

### Prerequisites

- Node.js 18+ and npm
- Python 3.9+
- pip

### Installation

1. **Install Frontend Dependencies**

```bash
npm install
```

2. **Install Backend Dependencies**

```bash
pip install -r requirements.txt
```

### Running the Application

**Option 1: Use the startup scripts**

Terminal 1 - Backend:

```bash
chmod +x start_backend.sh
./start_backend.sh
```

Terminal 2 - Frontend:

```bash
chmod +x start_frontend.sh
./start_frontend.sh
```

**Option 2: Manual startup**

Terminal 1 - Backend:

```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 2 - Frontend:

```bash
npm run dev
```

The application will be available at:

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Project Structure

```
AtlasSentinel/
├── src/              # React frontend
├── backend/          # Python ML backend
│   ├── ml/          # ML models and pipelines
│   ├── data/        # Data ingestion
│   └── api/         # FastAPI endpoints
└── public/          # Static assets
```
