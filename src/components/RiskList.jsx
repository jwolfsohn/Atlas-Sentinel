import React from 'react'
import './RiskList.css'

function RiskList({ routes, onRouteSelect, selectedRoute }) {
  const getRiskColor = (riskLevel) => {
    switch (riskLevel) {
      case 'high': return '#ef4444'
      case 'medium': return '#f59e0b'
      default: return '#10b981'
    }
  }

  return (
    <div className="risk-list-container">
      <div className="risk-list-header">
        <h2>Top 10 At-Risk Routes</h2>
        <span className="route-count">{routes.length} routes</span>
      </div>
      <div className="risk-list">
        {routes.map((route, index) => (
          <div
            key={route.route_id}
            className={`risk-list-item ${selectedRoute?.route_id === route.route_id ? 'selected' : ''}`}
            onClick={() => onRouteSelect(route.route_id)}
          >
            <div className="item-rank">#{index + 1}</div>
            <div className="item-content">
              <div className="item-name">{route.name}</div>
              <div className="item-meta">
                <span className="item-ports">
                  {route.origin.name} → {route.destination.name}
                </span>
              </div>
            </div>
            <div className="item-risk">
              <div
                className="risk-indicator"
                style={{ backgroundColor: getRiskColor(route.risk_level) }}
              />
              <div className="risk-score">
                {(route.risk_score * 100).toFixed(1)}%
              </div>
            </div>
          </div>
        ))}
        {routes.length === 0 && (
          <div className="empty-state">No routes available</div>
        )}
      </div>
    </div>
  )
}

export default RiskList

