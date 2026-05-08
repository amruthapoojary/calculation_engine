/**
 * Minimal endpoint kept for compatibility.
 * The frontend now links directly to the Grafana dashboard.
 */

export default function handler(req, res) {
  const dashboardUrl =
    process.env.NEXT_PUBLIC_GRAFANA_DASHBOARD_URL ||
    'http://localhost:3000/d/motor1-energy-dashboard/motor-1-energy-calculation-dashboard?orgId=1&refresh=5s&from=now-15m&to=now'

  return res.status(200).json({ dashboardUrl })
}
