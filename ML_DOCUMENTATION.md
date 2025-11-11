# Atlas Sentinel - Machine Learning Documentation

## Overview

Atlas Sentinel uses a multi-modal machine learning approach to predict supply chain disruptions by combining weather data, news sentiment, port congestion metrics, and historical patterns.

## ML Architecture

### 1. Risk Scoring Engine (`backend/ml/risk_scorer.py`)

The core ML component that combines multiple data modalities into a unified risk score.

#### Components

**Weather Risk Scoring**

- Input: Weather severity, type, duration
- Algorithm: Severity mapping + type multipliers + duration factors
- Output: Risk score 0-1
- Formula: `base_risk × type_multiplier × (0.7 + 0.3 × duration_factor)`

**Sentiment Risk Scoring**

- Input: News sentiment scores, article count, urgency keywords
- Algorithm: Negative sentiment conversion + volume weighting + urgency boost
- Output: Risk score 0-1
- Formula: `(1 - sentiment_score) / 2 × (0.6 + 0.2 × volume_factor + 0.2 × urgency_factor)`

**Congestion Risk Scoring**

- Input: Vessel count, capacity, wait time, historical averages
- Algorithm: Capacity utilization + wait time normalization + historical comparison
- Output: Risk score 0-1
- Formula: `capacity_util × 0.4 + wait_factor × 0.4 + historical_factor × 0.2`

**Historical Risk Scoring**

- Input: Historical disruption rates, recent disruption counts
- Algorithm: Weighted combination of historical patterns
- Output: Risk score 0-1

#### Weighted Combination

Default weights (configurable):

- Weather: 35%
- Sentiment: 30%
- Congestion: 25%
- Historical: 10%

Final risk score: Weighted sum of all components

#### Risk Levels

- **High Risk**: ≥ 0.7 (70%)
- **Medium Risk**: 0.4 - 0.7 (40-70%)
- **Low Risk**: < 0.4 (< 40%)

#### Cascading Delay Prediction

Predicts downstream impacts:

- High risk routes: Base delay 24-124 hours
- Medium risk routes: Base delay 6-36 hours
- Cascading effects: 30% of upstream delay propagates to dependent routes

### 2. Sentiment Analyzer (`backend/ml/sentiment_analyzer.py`)

Analyzes news articles to detect supply chain disruption signals.

#### Features

- **Text Analysis**: Keyword-based sentiment scoring (production-ready for transformer models)
- **Urgency Detection**: Identifies disruption-related keywords
- **Aggregation**: Combines multiple articles into region/port-level sentiment
- **Scalability**: Ready for OpenAI API or HuggingFace transformers

#### Urgency Keywords

Monitors for: delay, disruption, closure, shutdown, strike, congestion, backlog, shortage, crisis, emergency, blockade, storm, hurricane, typhoon, flood, accident, incident, breakdown, failure, outage

#### Sentiment Score Range

- -1.0: Very negative (high disruption risk)
- 0.0: Neutral
- +1.0: Very positive (low disruption risk)

### 3. Congestion Analyzer (`backend/ml/congestion_analyzer.py`)

Computes port congestion indices from traffic data.

#### Metrics

**Congestion Index Calculation**

- Capacity utilization: Current vessels / Port capacity
- Wait time factor: Normalized to 72-hour maximum
- Historical comparison: Deviation from average wait times

**Rolling Window Analysis**

- Default window: 24 hours
- Computes trends (increasing/decreasing/stable)
- Predicts future congestion based on incoming traffic

#### Prediction Model

Projects congestion 24 hours ahead:

- Input: Current vessels, incoming vessels, processing rate
- Output: Projected congestion index, vessel count, wait time

## Data Flow

```
1. Data Ingestion (Simulated)
   ├── Port Traffic Data
   ├── Weather Alerts
   └── News Articles

2. Feature Extraction
   ├── Sentiment Analysis → Sentiment Scores
   ├── Congestion Analysis → Congestion Indices
   └── Weather Processing → Weather Risk Factors

3. Risk Scoring
   └── Multi-modal Combination → Route Risk Scores

4. Alert Generation
   └── Threshold Filtering → Active Alerts

5. Visualization
   └── Dashboard Display
```

## Ontology Layer

The knowledge graph structure enables relationship-based risk propagation:

### Entities

- **Port**: Physical locations with capacity, congestion metrics
- **Route**: Shipping lanes connecting ports
- **Shipment**: Individual cargo movements
- **RiskFactor**: Disruption events affecting entities

### Relationships

- Port → Routes (bidirectional)
- Port → Weather Zones
- Port → News Regions
- Route → Risk Factors

## Model Improvements (Production Ready)

### Current Implementation

- Keyword-based sentiment (simplified)
- Rule-based risk scoring
- Statistical congestion analysis

### Production Enhancements

1. **Sentiment Analysis**

   - Replace with transformer models (BERT, RoBERTa)
   - Fine-tune on supply chain news corpus
   - Multi-language support

2. **Risk Scoring**

   - Train ensemble models (Random Forest, XGBoost)
   - Use historical disruption data for training
   - Implement time series forecasting (LSTM, Prophet)

3. **Congestion Prediction**

   - ARIMA/Prophet for time series
   - Graph neural networks for network effects
   - Real-time AIS data integration

4. **Cascading Effects**
   - Graph-based propagation models
   - Network flow optimization
   - Dependency graph learning

## API Endpoints

### `/api/routes`

Returns all routes with risk assessments

### `/api/routes/top-risk?limit=10`

Top N at-risk routes with delay predictions

### `/api/route/{route_id}`

Detailed route analysis with component breakdown

### `/api/alerts?threshold=0.7`

Active alerts above risk threshold

### `/api/ports`

All ports with current congestion metrics

## Performance Considerations

- **Real-time Updates**: 30-second refresh cycle
- **Scalability**: Designed for 1000+ routes
- **Caching**: Route data cached with TTL
- **Batch Processing**: ML models process in batches

## Future ML Enhancements

1. **Time Series Analysis (TSA)**

   - Palantir TSA integration
   - Predictive trend analysis
   - Anomaly detection

2. **Simulation Engine**

   - "What-if" scenarios
   - Port shutdown impact modeling
   - Ripple effect simulation

3. **Reinforcement Learning**

   - Optimal route recommendations
   - Dynamic rerouting strategies
   - Resource allocation optimization

4. **Graph Neural Networks**
   - Network-wide risk propagation
   - Dependency learning
   - Community detection for risk clusters
