import { useEffect, useState } from 'react'
import { api, Blueprint } from '../api'

export default function Blueprints() {
  const [blueprints, setBlueprints] = useState<Blueprint[]>([])
  const [selected, setSelected] = useState<string | null>(null)
  const [yaml, setYaml] = useState('')
  const [applyDomain, setApplyDomain] = useState('')
  const [message, setMessage] = useState('')

  useEffect(() => {
    api<Blueprint[]>('/blueprints').then(setBlueprints).catch(console.error)
  }, [])

  const loadBlueprint = async (name: string) => {
    setSelected(name)
    const data = await api<Record<string, unknown>>(`/blueprints/${name}`)
    setYaml(JSON.stringify(data, null, 2))
  }

  const applyBlueprint = async () => {
    if (!selected || !applyDomain) return
    try {
      const result = await api(`/sites/${applyDomain}/blueprint`, {
        method: 'POST',
        body: JSON.stringify({ blueprint: selected }),
      })
      setMessage(`Applied ${selected} to ${applyDomain}`)
      console.log(result)
    } catch (err) {
      setMessage(String(err))
    }
  }

  return (
    <div>
      <h2 style={{ marginBottom: '1.5rem' }}>Blueprint Editor</h2>
      <div className="card">
        <h2>Available Blueprints</h2>
        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
          {blueprints.map((bp) => (
            <button key={bp.name} onClick={() => loadBlueprint(bp.name)} className={selected === bp.name ? 'btn' : ''}>
              {bp.name}
            </button>
          ))}
        </div>
        {selected && (
          <>
            <p style={{ color: '#94a3b8', marginBottom: '1rem' }}>
              {blueprints.find((b) => b.name === selected)?.description}
            </p>
            <textarea rows={20} value={yaml} onChange={(e) => setYaml(e.target.value)} />
            <div style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <input placeholder="domain to apply" value={applyDomain} onChange={(e) => setApplyDomain(e.target.value)} style={{ marginBottom: 0, flex: 1 }} />
              <button onClick={applyBlueprint}>Apply to Site</button>
            </div>
            {message && <p className="success">{message}</p>}
          </>
        )}
      </div>
    </div>
  )
}
