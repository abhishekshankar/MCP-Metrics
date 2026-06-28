import { useEffect, useState } from 'react'
import { api, AuditLog } from '../api'

export default function AuditLogPage() {
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [filter, setFilter] = useState({ domain: '', operation: '' })

  const load = () => {
    const params = new URLSearchParams()
    if (filter.domain) params.set('domain', filter.domain)
    if (filter.operation) params.set('operation', filter.operation)
    api<AuditLog[]>(`/audit?${params}`).then(setLogs).catch(console.error)
  }

  useEffect(() => { load() }, [])

  return (
    <div>
      <h2 style={{ marginBottom: '1.5rem' }}>Audit Log</h2>
      <div className="card">
        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
          <input placeholder="Filter by domain" value={filter.domain} onChange={(e) => setFilter({ ...filter, domain: e.target.value })} style={{ marginBottom: 0 }} />
          <input placeholder="Filter by operation" value={filter.operation} onChange={(e) => setFilter({ ...filter, operation: e.target.value })} style={{ marginBottom: 0 }} />
          <button onClick={load}>Filter</button>
        </div>
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Domain</th>
              <th>Operation</th>
              <th>Actor</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log) => (
              <tr key={log.id}>
                <td>{new Date(log.created_at).toLocaleString()}</td>
                <td>{(log as AuditLog & { domain?: string }).domain || '—'}</td>
                <td>{log.operation}</td>
                <td>{log.actor}</td>
                <td>{log.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
