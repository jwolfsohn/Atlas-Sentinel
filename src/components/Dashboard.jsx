import React, { useState, useEffect } from 'react'
import axios from 'axios'
import RiskMap from './RiskMap'
import RiskList from './RiskList'
import RiskMetrics from './RiskMetrics'
import AlertPanel from './AlertPanel'
import './Dashboard.css'

const API_BASE = 'http://localhost:8000/api'

function Dashboard() {
  const [routes, setRoutes] = useState([])
  const [topRiskRoutes, setTopRiskRoutes] = useState([])
  const [alerts, setAlerts] = useState([])
  const [ports, setPorts] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedRoute, setSelectedRoute] = useState(null)
  const [lastUpdate, setLastUpdate] = useState(null)

  const fetchData = async () => {
    try {
      setLoading(true)
      const [routesRes, topRiskRes, alertsRes, portsRes] = await Promise.all([
        axios.get(`${API_BASE}/routes`),
        axios.get(`${API_BASE}/routes/top-risk?limit=10`),
        axios.get(`${API_BASE}/alerts?threshold=0.7`),
        axios.get(`${API_BASE}/ports`)
      ])

      setRoutes(routesRes.data.routes)
      setTopRiskRoutes(topRiskRes.data.routes)
      setAlerts(alertsRes.data.alerts)
      setPorts(portsRes.data.ports)
      setLastUpdate(new Date())
      setLoading(false)
    } catch (error) {
      console.error('Error fetching data:', error)
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 30000) // Refresh every 30 seconds
    return () => clearInterval(interval)
  }, [])

  const handleRouteSelect = async (routeId) => {
    try {
      const response = await axios.get(`${API_BASE}/route/${routeId}`)
      setSelectedRoute(response.data)
    } catch (error) {
      console.error('Error fetching route details:', error)
    }
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-content">
          <h1 className="dashboard-title">
            <span className="title-icon">🌐</span>
            Atlas Sentinel
          </h1>
          <p className="dashboard-subtitle">Global Supply Chain Early-Warning System</p>
        </div>
        <div className="header-meta">
          {lastUpdate && (
            <span className="last-update">
              Last updated: {lastUpdate.toLocaleTimeString()}
            </span>
          )}
          <button className="refresh-btn" onClick={fetchData} disabled={loading}>
            {loading ? 'Refreshing...' : '🔄 Refresh'}
          </button>
        </div>
      </header>

      {loading && routes.length === 0 ? (
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading supply chain data...</p>
        </div>
      ) : (
        <>
          <div className="dashboard-content">
            <div className="dashboard-main">
              <div className="map-section">
                <RiskMap
                  routes={routes}
                  ports={ports}
                  alerts={alerts}
                  onRouteClick={handleRouteSelect}
                />
              </div>
              
              <div className="metrics-section">
                <RiskMetrics routes={routes} alerts={alerts} />
              </div>
            </div>

            <div className="dashboard-sidebar">
              <AlertPanel alerts={alerts} />
              <RiskList
                routes={topRiskRoutes}
                onRouteSelect={handleRouteSelect}
                selectedRoute={selectedRoute}
              />
            </div>
          </div>

          {selectedRoute && (
            <div className="route-details-modal">
              <div className="modal-content">
                <button
                  className="modal-close"
                  onClick={() => setSelectedRoute(null)}
                >
                  ×
                </button>
                <RouteDetails route={selectedRoute} />
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}

function RouteDetails({ route }) {
  const risk = route.risk_assessment
  const components = risk.components

  return (
    <div className="route-details">
      <h2>{route.route_name}</h2>
      <div className="risk-summary">
        <div className="risk-score-large">
          <span className="score-label">Risk Score</span>
          <span className={`score-value risk-${risk.risk_level}`}>
            {(risk.total_risk * 100).toFixed(1)}%
          </span>
        </div>
        <div className="risk-level-badge">
          <span className={`badge badge-${risk.risk_level}`}>
            {risk.risk_level.toUpperCase()}
          </span>
        </div>
      </div>

      <div className="risk-components">
        <h3>Risk Components</h3>
        <div className="component-grid">
          <div className="component-item">
            <span className="component-label">Weather</span>
            <div className="component-bar">
              <div
                className="component-fill"
                style={{ width: `${components.weather * 100}%` }}
              />
            </div>
            <span className="component-value">
              {(components.weather * 100).toFixed(1)}%
            </span>
          </div>
          <div className="component-item">
            <span className="component-label">Sentiment</span>
            <div className="component-bar">
              <div
                className="component-fill"
                style={{ width: `${components.sentiment * 100}%` }}
              />
            </div>
            <span className="component-value">
              {(components.sentiment * 100).toFixed(1)}%
            </span>
          </div>
          <div className="component-item">
            <span className="component-label">Congestion</span>
            <div className="component-bar">
              <div
                className="component-fill"
                style={{ width: `${components.congestion * 100}%` }}
              />
            </div>
            <span className="component-value">
              {(components.congestion * 100).toFixed(1)}%
            </span>
          </div>
          <div className="component-item">
            <span className="component-label">Historical</span>
            <div className="component-bar">
              <div
                className="component-fill"
                style={{ width: `${components.historical * 100}%` }}
              />
            </div>
            <span className="component-value">
              {(components.historical * 100).toFixed(1)}%
            </span>
          </div>
        </div>
      </div>

      <div className="port-details-grid">
        <div className="port-detail">
          <h4>Origin: {route.origin_port.data.port_name}</h4>
          <p>Vessels: {route.origin_port.data.vessel_count}</p>
          <p>Wait Time: {route.origin_port.data.wait_time_hours.toFixed(1)}h</p>
          <p>Weather: {route.origin_port.weather.severity} {route.origin_port.weather.type}</p>
        </div>
        <div className="port-detail">
          <h4>Destination: {route.destination_port.data.port_name}</h4>
          <p>Vessels: {route.destination_port.data.vessel_count}</p>
          <p>Wait Time: {route.destination_port.data.wait_time_hours.toFixed(1)}h</p>
          <p>Weather: {route.destination_port.weather.severity} {route.destination_port.weather.type}</p>
        </div>
      </div>
    </div>
  )
}

export default Dashboard

