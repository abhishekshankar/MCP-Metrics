import { useEffect, useState } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
} from 'recharts'
import { api } from '../api'

interface HealthDataPoint {
  timestamp: string
  event_count: number
  sessions: number
  conversions: number
  status: string
}

interface HealthChartsProps {
  domain: string
}

export default function HealthCharts({ domain }: HealthChartsProps) {
  const [history, setHistory] = useState<HealthDataPoint[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api<HealthDataPoint[]>(`/sites/${domain}/health/history?limit=30`)
      .then((data) => {
        // Format data for chart
        const formatted = data.map((d) => ({
          ...d,
          timestamp: new Date(d.timestamp).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
          }),
        }))
        setHistory(formatted.reverse())
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [domain])

  if (loading) return <p>Loading charts...</p>
  if (history.length === 0) return <p>No health history available yet.</p>

  return (
    <div style={{ marginTop: '1.5rem' }}>
      <h3 style={{ marginBottom: '1rem' }}>Health Trends (30 Days)</h3>

      <div style={{ marginBottom: '2rem' }}>
        <h4 style={{ fontSize: '0.875rem', color: '#94a3b8', marginBottom: '0.5rem' }}>
          Events & Sessions
        </h4>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={history}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="timestamp" stroke="#64748b" tick={{ fill: '#64748b' }} />
            <YAxis stroke="#64748b" tick={{ fill: '#64748b' }} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#0f172a',
                border: '1px solid #334155',
                borderRadius: '6px',
              }}
              labelStyle={{ color: '#94a3b8' }}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="event_count"
              name="Events"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="sessions"
              name="Sessions"
              stroke="#10b981"
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div>
        <h4 style={{ fontSize: '0.875rem', color: '#94a3b8', marginBottom: '0.5rem' }}>
          Conversions
        </h4>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={history}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="timestamp" stroke="#64748b" tick={{ fill: '#64748b' }} />
            <YAxis stroke="#64748b" tick={{ fill: '#64748b' }} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#0f172a',
                border: '1px solid #334155',
                borderRadius: '6px',
              }}
              labelStyle={{ color: '#94a3b8' }}
            />
            <Bar dataKey="conversions" name="Conversions" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
