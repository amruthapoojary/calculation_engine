/**
 * API endpoint to fetch latest metrics from InfluxDB.
 * Returns the most recent metric values for the dashboard cards.
 */

export default async function handler(req, res) {
  try {
    const influxUrl = process.env.INFLUX_URL || 'http://influxdb:8086'
    const influxToken = process.env.INFLUX_TOKEN || ''
    const influxOrg = process.env.INFLUX_ORG || 'ukshati'
    const influxBucket = process.env.INFLUX_BUCKET || 'energy'

    if (!influxToken) {
      return res.status(500).json({ error: 'InfluxDB token not configured' })
    }

    // Build Flux query to get the latest values for each metric
    const query = `
from(bucket:"${influxBucket}")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "calculated_metrics" and r.asset_id == "motor1")
  |> last()
`

    const response = await fetch(`${influxUrl}/api/v1/query`, {
      method: 'POST',
      headers: {
        'Authorization': `Token ${influxToken}`,
        'Content-Type': 'application/vnd.flux',
        'Accept': 'application/json',
      },
      body: query,
    })

    if (!response.ok) {
      console.error(`[API] InfluxDB query failed: ${response.status}`)
      return res.status(500).json({ error: 'InfluxDB query failed' })
    }

    const data = await response.json()
      if (!response.ok) {
        const text = await response.text()
        console.error(`[API] InfluxDB query failed: ${response.status} - ${text.substring(0, 200)}`)
        return res.status(500).json({ error: 'InfluxDB query failed', details: text.substring(0, 500) })
      }

      let data
      try {
        data = await response.json()
      } catch (e) {
        const text = await response.text()
        console.error(`[API] Failed to parse JSON: ${text.substring(0, 200)}`)
        return res.status(500).json({ error: 'Invalid JSON from InfluxDB', details: text.substring(0, 500) })
      }

    // Parse the response into metric values
    const metrics = {
      imbalance: 0,
      power: 0,
      avg_current: 0,
      load_percentage: 0,
    }

    let status = 'NORMAL'

    // Extract values from the response
    if (data.results && data.results[0] && data.results[0].series) {
      const series = data.results[0].series[0]
      if (series.values && series.values.length > 0) {
        const row = series.values[0]
        const columns = series.columns

        for (let i = 0; i < columns.length; i++) {
          const col = columns[i]
          const val = row[i]

          if (col === 'metric' || col === '_field') {
            // This is the metric type, like "imbalance", "power", etc.
            const metricType = row[i]
            // The value should be in the next column or marked as "_value"
            const valueIndex = columns.indexOf('_value') !== -1 ? columns.indexOf('_value') : i + 1
            if (valueIndex < columns.length) {
              const metricValue = row[valueIndex]
              if (metricType === 'imbalance') metrics.imbalance = metricValue
              else if (metricType === 'power') metrics.power = metricValue
              else if (metricType === 'avg_current') metrics.avg_current = metricValue
              else if (metricType === 'load_percentage') metrics.load_percentage = metricValue
            }
          }
        }
      }
    }

    // Query the latest overall status
    const statusQuery = `
from(bucket:"${influxBucket}")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "overall_status" and r.asset_id == "motor1")
  |> last()
`

    const statusResponse = await fetch(`${influxUrl}/api/v1/query`, {
      method: 'POST',
      headers: {
        'Authorization': `Token ${influxToken}`,
        'Content-Type': 'application/vnd.flux',
        'Accept': 'application/json',
      },
      body: statusQuery,
    })

    if (statusResponse.ok) {
      const statusData = await statusResponse.json()
      if (
        statusData.results &&
        statusData.results[0] &&
        statusData.results[0].series &&
        statusData.results[0].series[0] &&
        statusData.results[0].series[0].values &&
        statusData.results[0].series[0].values.length > 0
      ) {
        const statusRow = statusData.results[0].series[0].values[0]
        const statusCols = statusData.results[0].series[0].columns
        const statusIdx = statusCols.indexOf('status')
        if (statusIdx !== -1) {
          status = statusRow[statusIdx] || 'NORMAL'
        }
      }
    }

    res.status(200).json({
      metrics,
      status,
      timestamp: new Date().toISOString(),
    })
  } catch (error) {
    console.error('[API] Error:', error)
    res.status(500).json({ error: error.message })
  }
}
