import { useEffect, useState } from 'react'
import { api, Blueprint } from '../api'

export default function Blueprints() {
  const [blueprints, setBlueprints] = useState<Blueprint[]>([])
  const [selected, setSelected] = useState<string | null>(null)
  const [content, setContent] = useState('')
  const [applyDomain, setApplyDomain] = useState('')
  const [message, setMessage] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const [newBlueprintName, setNewBlueprintName] = useState('')
  const [showNewBlueprint, setShowNewBlueprint] = useState(false)

  useEffect(() => {
    api<Blueprint[]>('/blueprints').then(setBlueprints).catch(console.error)
  }, [])

  const loadBlueprint = async (name: string) => {
    setSelected(name)
    setShowNewBlueprint(false)
    const data = await api<Record<string, unknown>>(`/blueprints/${name}`)
    setContent(JSON.stringify(data, null, 2))
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

  const saveBlueprint = async () => {
    if (!selected) return
    setIsSaving(true)
    try {
      const parsed = JSON.parse(content)
      await api(`/blueprints/${selected}`, {
        method: 'POST',
        body: JSON.stringify({ content: parsed }),
      })
      setMessage(`Saved blueprint '${selected}' successfully`)
    } catch (err) {
      setMessage(`Error: ${err}`)
    } finally {
      setIsSaving(false)
    }
  }

  const createNewBlueprint = async () => {
    if (!newBlueprintName) return
    const template = {
      name: newBlueprintName,
      description: 'Custom blueprint',
      version: '1.0',
      events: [
        {
          name: 'custom_event',
          trigger_type: 'customEvent',
          parameters: ['category', 'action', 'label']
        }
      ],
      dataLayer: {
        helper_snippet: `function trackEvent(name, params) {\n  window.dataLayer = window.dataLayer || [];\n  window.dataLayer.push({ event: name, ...params });\n}`,
        spec: {
          custom_event: {
            description: 'Custom tracking event',
            parameters: ['category', 'action', 'label']
          }
        }
      }
    }
    setContent(JSON.stringify(template, null, 2))
    setSelected(newBlueprintName)
    setShowNewBlueprint(false)
    setNewBlueprintName('')
  }

  return (
    <div>
      <h2 style={{ marginBottom: '1.5rem' }}>Blueprint Editor</h2>
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h2 style={{ margin: 0 }}>Available Blueprints</h2>
          <button onClick={() => setShowNewBlueprint(!showNewBlueprint)} className="btn-secondary">
            + New Blueprint
          </button>
        </div>

        {showNewBlueprint && (
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
            <input
              placeholder="Blueprint name"
              value={newBlueprintName}
              onChange={(e) => setNewBlueprintName(e.target.value)}
              style={{ marginBottom: 0, flex: 1 }}
            />
            <button onClick={createNewBlueprint}>Create</button>
            <button onClick={() => setShowNewBlueprint(false)} className="btn-secondary">Cancel</button>
          </div>
        )}

        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
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
            <textarea rows={20} value={content} onChange={(e) => setContent(e.target.value)} />
            <div style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <input placeholder="domain to apply" value={applyDomain} onChange={(e) => setApplyDomain(e.target.value)} style={{ marginBottom: 0, flex: 1 }} />
              <button onClick={applyBlueprint}>Apply to Site</button>
              <button onClick={saveBlueprint} disabled={isSaving} className="btn-secondary">
                {isSaving ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
            {message && <p className={message.includes('Error') ? 'error' : 'success'}>{message}</p>}
          </>
        )}
      </div>
    </div>
  )
}
