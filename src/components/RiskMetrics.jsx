import React from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import './RiskMetrics.css'

function RiskMetrics({ routes, alerts }) {
  // Calculate statistics
  const totalRoutes = routes.length
  const highRiskCount = routes.filter(r => r.risk_level === 'high').length
  const mediumRiskCount = routes.filter(r => r.risk_level === 'medium').length
  const lowRiskCount = routes.filter(r => r.risk_level === 'low').length
  const alertCount = alerts.length

  const avgRiskScore = routes.length > 0
    ? routes.reduce((sum, r) => sum + r.risk_score, 0) / routes.length
    : 0

  // Risk distribution data
  const riskDistribution = [
    { name: 'High', count: highRiskCount, color: '#ef4444' },
    { name: 'Medium', count: mediumRiskCount, color: '#f59e0b' },
    { name: 'Low', count: lowRiskCount, color: '#10b981' }
  ]

  // Component breakdown (average)
  const componentData = routes.length > 0
    ? (() => {
        const totals = routes.reduce((acc, r) => {
          if (r.risk_components) {
            acc.weather += r.risk_components.weather || 0
            acc.sentiment += r.risk_components.sentiment || 0
            acc.congestion += r.risk_components.congestion || 0
            acc.historical += r.risk_components.historical || 0
          }
          return acc
        }, { weather: 0, sentiment: 0, congestion: 0, historical: 0 })

        const count = routes.length
        return [
          { name: 'Weather', value: (totals.weather / count) * 100 },
          { name: 'Sentiment', value: (totals.sentiment / count) * 100 },
          { name: 'Congestion', value: (totals.congestion / count) * 100 },
          { name: 'Historical', value: (totals.historical / count) * 100 }
        ]
      })()
    : []

  return (
    <div className="risk-metrics">
      <h2 className="metrics-title">Risk Analytics</h2>

      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-label">Total Routes</div>
          <div className="metric-value">{totalRoutes}</div>
        </div>
        <div className="metric-card alert">
          <div className="metric-label">Active Alerts</div>
          <div className="metric-value">{alertCount}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Avg Risk Score</div>
          <div className="metric-value">{(avgRiskScore * 100).toFixed(1)}%</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">High Risk Routes</div>
          <div className="metric-value">{highRiskCount}</div>
        </div>
      </div>

      <div className="chart-section">
        <h3 className="chart-title">Risk Distribution</h3>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={riskDistribution}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
            <XAxis dataKey="name" stroke="#888" />
            <YAxis stroke="#888" />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1a1f3a',
                border: '1px solid rgba(255,255,255,0.1)',
                color: '#fff'
              }}
            />
            <Bar dataKey="count" fill="#3b82f6" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="chart-section">
        <h3 className="chart-title">Average Risk Components</h3>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={componentData}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
            <XAxis dataKey="name" stroke="#888" />
            <YAxis stroke="#888" />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1a1f3a',
                border: '1px solid rgba(255,255,255,0.1)',
                color: '#fff'
              }}
              formatter={(value) => `${value.toFixed(1)}%`}
            />
            <Bar dataKey="value" fill="#60a5fa" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

export default RiskMetrics

