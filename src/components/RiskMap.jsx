import React, { useEffect, useRef } from 'react'
import { MapContainer, TileLayer, Marker, Popup, Polyline, CircleMarker } from 'react-leaflet'
import L from 'leaflet'
import './RiskMap.css'

// Fix for default marker icons in React-Leaflet
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
})

function RiskMap({ routes, ports, alerts, onRouteClick }) {
  const mapRef = useRef(null)

  const getRiskColor = (riskScore) => {
    if (riskScore >= 0.7) return '#ef4444' // red
    if (riskScore >= 0.4) return '#f59e0b' // orange
    return '#10b981' // green
  }

  const getRiskWidth = (riskScore) => {
    return Math.max(2, riskScore * 6)
  }

  const alertRouteIds = new Set(alerts.map(a => a.route_id))

  return (
    <div className="risk-map-container">
      <MapContainer
        center={[30, 0]}
        zoom={2}
        style={{ height: '100%', width: '100%' }}
        ref={mapRef}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* Render ports */}
        {ports.map(port => (
          <CircleMarker
            key={port.port_id}
            center={[port.latitude, port.longitude]}
            radius={8}
            fillColor={port.congestion_index > 0.7 ? '#ef4444' : port.congestion_index > 0.4 ? '#f59e0b' : '#10b981'}
            fillOpacity={0.8}
            color="#fff"
            weight={2}
          >
            <Popup>
              <div className="port-popup">
                <h4>{port.name}</h4>
                <p>Vessels: {port.vessel_count}</p>
                <p>Wait Time: {port.wait_time_hours.toFixed(1)}h</p>
                <p>Congestion: {(port.congestion_index * 100).toFixed(1)}%</p>
              </div>
            </Popup>
          </CircleMarker>
        ))}

        {/* Render routes */}
        {routes.map(route => {
          const isAlert = alertRouteIds.has(route.route_id)
          const color = getRiskColor(route.risk_score)
          const width = getRiskWidth(route.risk_score)

          return (
            <Polyline
              key={route.route_id}
              positions={[
                [route.origin.latitude, route.origin.longitude],
                [route.destination.latitude, route.destination.longitude]
              ]}
              color={color}
              weight={width}
              opacity={0.7}
              dashArray={isAlert ? '10, 5' : undefined}
              eventHandlers={{
                click: () => onRouteClick(route.route_id)
              }}
            >
              <Popup>
                <div className="route-popup">
                  <h4>{route.name}</h4>
                  <div className={`risk-badge risk-${route.risk_level}`}>
                    {route.risk_level.toUpperCase()}
                  </div>
                  <p>Risk Score: {(route.risk_score * 100).toFixed(1)}%</p>
                  {route.predicted_delay_hours && (
                    <p>Predicted Delay: {route.predicted_delay_hours.toFixed(1)}h</p>
                  )}
                  {isAlert && <p className="alert-indicator">⚠️ ALERT</p>}
                </div>
              </Popup>
            </Polyline>
          )
        })}
      </MapContainer>
    </div>
  )
}

export default RiskMap

