import React, { useEffect, useState } from 'react'

export default function Home() {
  const [metrics, setMetrics] = useState({
    imbalance: 0,
    power: 0,
    avg_current: 0,
    load_percentage: 0
  })
  const [status, setStatus] = useState('NORMAL')

  useEffect(() => {
    // Poll InfluxDB / API endpoint every 5 seconds — replace with real API if available
    const id = setInterval(async () => {
      try {
        const res = await fetch('/api/metrics')
        if (!res.ok) return
        const json = await res.json()
        setMetrics(json.metrics || metrics)
        setStatus(json.status || 'NORMAL')
      } catch (e) {
        // fallback: keep existing
      }
    }, 5000)
    return () => clearInterval(id)
  }, [])

  function statusColor(s) {
    switch (s) {
      case 'ALARM': return '#ff3333'
      case 'WARNING': return '#ff9933'
      case 'ALERT': return '#ffcc00'
      default: return '#44aa88'
    }
  }

  return (
    <div className="container">
      <header>
        <h1>Motor 1 — Energy Dashboard</h1>
        <div className="status" style={{ background: statusColor(status) }}>{status}</div>
      </header>

      <main>
        <section className="cards">
          <div className="card">
            <h3>Phase Imbalance</h3>
            <div className="value">{metrics.imbalance.toFixed(2)}%</div>
            <div className="unit">% out of balance</div>
          </div>
          <div className="card">
            <h3>Total Power</h3>
            <div className="value">{metrics.power.toFixed(0)} W</div>
            <div className="unit">watts consumed</div>
          </div>
          <div className="card">
            <h3>Avg Current</h3>
            <div className="value">{metrics.avg_current.toFixed(2)} A</div>
            <div className="unit">amperes</div>
          </div>
          <div className="card">
            <h3>Load %</h3>
            <div className="value">{metrics.load_percentage.toFixed(1)}%</div>
            <div className="unit">of rated capacity</div>
          </div>
        </section>

        <section className="info">
          <p>📊 All metrics update every 5 seconds from the energy calculation engine.</p>
          <p>View full Grafana dashboard at <code>http://localhost:3000</code></p>
        </section>
      </main>

      <footer>
        <small>Data refresh: 5s · Status: Live</small>
      </footer>

      <style jsx>{`
        .container { font-family: Inter, system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial; background: #0f1720; color: #e6eef1; min-height: 100vh; padding: 24px; }
        header { display:flex; align-items:center; justify-content:space-between; gap:12px; margin-bottom: 24px; }
        h1 { margin:0; font-size:24px; font-weight:700 }
        .status{ color:#04160f; padding:8px 16px; border-radius:6px; font-weight:600; font-size:14px }
        main { margin-top:18px }
        .cards { display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:16px; margin-bottom:24px }
        .card { background: linear-gradient(135deg, rgba(88,168,123,0.1), rgba(88,168,123,0.05)); padding:20px; border-radius:8px; box-shadow: 0 2px 8px rgba(0,0,0,0.4); border: 1px solid rgba(88,168,123,0.2); }
        .card h3 { margin:0 0 12px 0; font-size:13px; color:#9dd1b3; text-transform: uppercase; letter-spacing: 0.5px; }
        .value { font-size:28px; font-weight:700; margin-bottom:8px; }
        .unit { font-size:11px; color:#6aa589; margin-top:6px; }
        .info { background: rgba(255,255,255,0.02); padding:16px; border-radius:8px; margin-top:24px; font-size:13px; line-height:1.6; color:#b8c4c2 }
        .info code { background: rgba(0,0,0,0.3); padding:2px 6px; border-radius:3px; font-family: 'Courier New', monospace; }
        footer { margin-top:24px; color:#6aa589; font-size:12px; }
      `}</style>
    </div>
  )
}
