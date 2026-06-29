import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api, Site, HealthResult, AuditLog } from '../api'
import HealthCharts from './HealthCharts'
import GTMDiff from './GTMDiff'

export default function SiteDetail() {
  const { domain } = useParams<{ domain: string }>()
  const [site, setSite] = useState<Site | null>(null)
  const [health, setHealth] = useState<HealthResult | null>(null)
  const [audit, setAudit] = useState<AuditLog[]>([])
  const [describe, setDescribe] = useState<Record<string, unknown> | null>(null)

  useEffect(() => {
    if (!domain) return
    Promise.all([
      api<Site>(`/sites/${domain}`).then(setSite).catch(console.error),
      api<HealthResult>(`/sites/${domain}/health`).then(setHealth).catch(console.error),
      api<AuditLog[]>(`/sites/${domain}/audit`).then(setAudit).catch(console.error),
      api<Record<string, unknown>>(`/sites/${domain}/describe`).then(setDescribe).catch(console.error),
    ])
  }, [domain])

  if (!site) return <p>Loading...</p>

  const badgeClass = health?.status === 'healthy' ? 'badge-healthy'
    : health?.status === 'critical' ? 'badge-critical' : 'badge-warning'

  return (
    <div>
      <h2 style={{ marginBottom: '0.5rem' }}>{site.name}</h2>
      <p style={{ color: '#64748b', marginBottom: '1.5rem' }}>{site.domain} · {site.environment}</p>

      <div className="grid" style={{ marginBottom: '1.5rem' }}>
        <div className="stat">
          <div className="stat-value">{site.ga4_measurement_id || '—'}</div>
          <div className="stat-label">Measurement ID</div>
        </div>
        <div className="stat">
          <div className="stat-value">{site.gtm_container_public_id || '—'}</div>
          <div className="stat-label">GTM Container</div>
        </div>
        <div className="stat">
          <div className="stat-value">{site.blueprint || '—'}</div>
          <div className="stat-label">Blueprint</div>
        </div>
        <div className="stat">
          <div className="stat-value"><span className={`badge ${badgeClass}`}>{health?.status || 'unknown'}</span></div>
          <div className="stat-label">Health</div>
        </div>
      </div>

      {health && (
        <div className="card">
          <h2>Health Metrics (24h)</h2>
          <div className="grid">
            <div className="stat">
              <div className="stat-value">{health.event_count_24h}</div>
              <div className="stat-label">Events</div>
            </div>
            <div className="stat">
              <div className="stat-value">{health.traffic_sessions_24h}</div>
              <div className="stat-label">Sessions</div>
            </div>
            <div className="stat">
              <div className="stat-value">{health.conversion_count_24h}</div>
              <div className="stat-label">Conversions</div>
            </div>
          </div>
          {health.anomaly_flags?.length > 0 && (
            <p className="error" style={{ marginTop: '1rem' }}>Anomalies: {health.anomaly_flags.join(', ')}</p>
          )}
        </div>
      )}

      {describe && (
        <div className="card">
          <h2>Setup Description</h2>
          <p>{String(describe.summary)}</p>
          <p style={{ marginTop: '0.5rem', color: '#94a3b8' }}>{String(describe.consent_explanation)}</p>
        </div>
      )}

      {domain && <HealthCharts domain={domain} />}

      {domain && <GTMDiff domain={domain} />}

      <div className="card">
        <h2>Recent Audit Log</h2>
        <table>
          <thead>
            <tr><th>Operation</th><th>Actor</th><th>Status</th><th>Time</th></tr>
          </thead>
          <tbody>
            {audit.slice(0, 10).map((log) => (
              <tr key={log.id}>
                <td>{log.operation}</td>
                <td>{log.actor}</td>
                <td>{log.status}</td>
                <td>{new Date(log.created_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
