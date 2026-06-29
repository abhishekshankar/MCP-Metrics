import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, Site } from '../api'

export default function Dashboard() {
  const [sites, setSites] = useState<Site[]>([])
  const [loading, setLoading] = useState(true)

  const [error, setError] = useState('')

  useEffect(() => {
    api<Site[]>('/sites')
      .then(setSites)
      .catch((err) => setError(String(err)))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p>Loading sites...</p>
  if (error) return <p className="error">Error loading sites: {error}</p>

  return (
    <div>
      <h2 style={{ marginBottom: '1.5rem' }}>Sites Dashboard</h2>
      <div className="card">
        {sites.length === 0 ? (
          <p>No sites yet. <Link to="/create">Create your first setup</Link></p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Domain</th>
                <th>Name</th>
                <th>Env</th>
                <th>Blueprint</th>
                <th>Measurement ID</th>
                <th>GTM</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {sites.map((s) => (
                <tr key={s.id}>
                  <td><Link to={`/sites/${s.domain}`}>{s.domain}</Link></td>
                  <td>{s.name}</td>
                  <td>{s.environment}</td>
                  <td>{s.blueprint || '—'}</td>
                  <td>{s.ga4_measurement_id || '—'}</td>
                  <td>{s.gtm_container_public_id || '—'}</td>
                  <td><span className="badge badge-active">{s.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
