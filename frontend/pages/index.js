import React from 'react'

const dashboardUrl =
  process.env.NEXT_PUBLIC_GRAFANA_DASHBOARD_URL ||
  'http://localhost:3000/d/motor1-energy-dashboard/motor-1-energy-calculation-dashboard?orgId=1&refresh=5s&from=now-15m&to=now'

export default function Home() {
  return (
    <div style={{height: '100vh', margin: 0}}>
      <header style={{padding: 16, background: '#071019', color: '#eaf2f3'}}>
        <h1 style={{margin: 0}}>Calculation Engine</h1>
      </header>

      <iframe
        title="Calculation Engine - Grafana"
        src={dashboardUrl}
        style={{width: '100%', height: 'calc(100vh - 64px)', border: 0}}
      />
    </div>
  )
}
