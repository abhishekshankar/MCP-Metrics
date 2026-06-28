import { useEffect, useState } from 'react'
import { api } from '../api'

interface DiffItem {
  name?: string
  tagId?: string
  triggerId?: string
  variableId?: string
  type?: string
}

interface DiffData {
  before_version_id: string
  after_version_id: string
  tags_added: DiffItem[]
  tags_removed: DiffItem[]
  triggers_added: DiffItem[]
  triggers_removed: DiffItem[]
  variables_added: DiffItem[]
  variables_removed: DiffItem[]
}

interface GTMDiffProps {
  domain: string
}

export default function GTMDiff({ domain }: GTMDiffProps) {
  const [diff, setDiff] = useState<DiffData | null>(null)
  const [versions, setVersions] = useState<{ number: number; gtm_version_id: string; created_at: string }[]>([])
  const [beforeVersion, setBeforeVersion] = useState('')
  const [afterVersion, setAfterVersion] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    api<{ versions: { number: number; gtm_version_id: string; created_at: string }[] }>(`/sites/${domain}/versions`)
      .then((data) => {
        setVersions(data.versions || [])
        if (data.versions && data.versions.length >= 2) {
          setBeforeVersion(data.versions[1].gtm_version_id)
          setAfterVersion(data.versions[0].gtm_version_id)
        }
      })
      .catch(console.error)
  }, [domain])

  const loadDiff = () => {
    if (!beforeVersion || !afterVersion) return
    setLoading(true)
    api<DiffData>(`/sites/${domain}/diff?before=${beforeVersion}&after=${afterVersion}`)
      .then(setDiff)
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  const renderItem = (item: DiffItem, type: string) => (
    <div
      key={item.tagId || item.triggerId || item.variableId || item.name}
      style={{
        padding: '0.5rem',
        marginBottom: '0.25rem',
        background: '#1e293b',
        borderRadius: '4px',
        fontSize: '0.875rem',
      }}
    >
      <span style={{ color: '#e2e8f0', fontWeight: 500 }}>
        {item.name || item.tagId || item.triggerId || item.variableId}
      </span>
      {item.type && <span style={{ color: '#64748b', marginLeft: '0.5rem' }}>({item.type})</span>}
    </div>
  )

  const renderSection = (title: string, added: DiffItem[], removed: DiffItem[], addedColor: string, removedColor: string) => (
    <div style={{ marginBottom: '1.5rem' }}>
      <h4 style={{ marginBottom: '0.75rem', fontSize: '0.875rem', color: '#94a3b8' }}>{title}</h4>
      {added.length === 0 && removed.length === 0 ? (
        <p style={{ color: '#64748b', fontSize: '0.875rem' }}>No changes</p>
      ) : (
        <>
          {added.length > 0 && (
            <div style={{ marginBottom: '0.75rem' }}>
              <div
                style={{
                  fontSize: '0.75rem',
                  color: addedColor,
                  textTransform: 'uppercase',
                  marginBottom: '0.5rem',
                  fontWeight: 600,
                }}
              >
                + Added ({added.length})
              </div>
              {added.map((item) => renderItem(item, title))}
            </div>
          )}
          {removed.length > 0 && (
            <div>
              <div
                style={{
                  fontSize: '0.75rem',
                  color: removedColor,
                  textTransform: 'uppercase',
                  marginBottom: '0.5rem',
                  fontWeight: 600,
                }}
              >
                - Removed ({removed.length})
              </div>
              {removed.map((item) => renderItem(item, title))}
            </div>
          )}
        </>
      )}
    </div>
  )

  return (
    <div style={{ marginTop: '1.5rem' }}>
      <h3 style={{ marginBottom: '1rem' }}>GTM Configuration Diff</h3>

      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', alignItems: 'flex-end' }}>
        <div style={{ flex: 1 }}>
          <label style={{ display: 'block', fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.25rem' }}>
            Before Version
          </label>
          <select
            value={beforeVersion}
            onChange={(e) => setBeforeVersion(e.target.value)}
            style={{ width: '100%' }}
          >
            <option value="">Select version...</option>
            {versions.map((v) => (
              <option key={v.gtm_version_id} value={v.gtm_version_id}>
                Version {v.number} ({new Date(v.created_at).toLocaleDateString()})
              </option>
            ))}
          </select>
        </div>
        <div style={{ flex: 1 }}>
          <label style={{ display: 'block', fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.25rem' }}>
            After Version
          </label>
          <select
            value={afterVersion}
            onChange={(e) => setAfterVersion(e.target.value)}
            style={{ width: '100%' }}
          >
            <option value="">Select version...</option>
            {versions.map((v) => (
              <option key={v.gtm_version_id} value={v.gtm_version_id}>
                Version {v.number} ({new Date(v.created_at).toLocaleDateString()})
              </option>
            ))}
          </select>
        </div>
        <button onClick={loadDiff} disabled={!beforeVersion || !afterVersion || loading}>
          {loading ? 'Loading...' : 'Compare'}
        </button>
      </div>

      {diff && (
        <div className="card">
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '1rem',
              paddingBottom: '0.75rem',
              borderBottom: '1px solid #334155',
            }}
          >
            <span style={{ color: '#94a3b8', fontSize: '0.875rem' }}>
              Comparing version <strong style={{ color: '#e2e8f0' }}>{diff.before_version_id}</strong> to{' '}
              <strong style={{ color: '#e2e8f0' }}>{diff.after_version_id}</strong>
            </span>
          </div>

          {renderSection('Tags', diff.tags_added, diff.tags_removed, '#10b981', '#ef4444')}
          {renderSection('Triggers', diff.triggers_added, diff.triggers_removed, '#10b981', '#ef4444')}
          {renderSection('Variables', diff.variables_added, diff.variables_removed, '#10b981', '#ef4444')}
        </div>
      )}
    </div>
  )
}
