import React from 'react'
import './AlertPanel.css'

function AlertPanel({ alerts }) {
  return (
    <div className="alert-panel">
      <div className="alert-header">
        <h2>Active Alerts</h2>
        <span className={`alert-count ${alerts.length > 0 ? 'has-alerts' : ''}`}>
          {alerts.length}
        </span>
      </div>
      <div className="alert-list">
        {alerts.length === 0 ? (
          <div className="no-alerts">
            <span className="check-icon">✓</span>
            <p>No active alerts</p>
            <p className="subtext">All routes operating normally</p>
          </div>
        ) : (
          alerts.map((alert, index) => (
            <div key={alert.route_id} className="alert-item">
              <div className="alert-indicator" />
              <div className="alert-content">
                <div className="alert-title">{alert.name}</div>
                <div className="alert-details">
                  <span className="alert-route">
                    {alert.origin.name} → {alert.destination.name}
                  </span>
                  <span className="alert-risk">
                    Risk: {(alert.risk_score * 100).toFixed(1)}%
                  </span>
                </div>
                {alert.predicted_delay_hours && (
                  <div className="alert-delay">
                    Predicted Delay: {alert.predicted_delay_hours.toFixed(1)}h
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default AlertPanel

