import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'

export default function CreateSite() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    domain: '',
    name: '',
    environment: 'prod',
    blueprint: 'saas',
    consent_preset: 'none',
    enable_bigquery: false,
    bigquery_project: '',
    bigquery_dataset: '',
    linked_domains: '',
  })
  const [progress, setProgress] = useState('')
  const [error, setError] = useState('')
  const [result, setResult] = useState<Record<string, unknown> | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    setError('')
    setResult(null)
    setProgress('Creating GA4 property...')
    try {
      setProgress('Creating GA4 property & web data stream...')
      await new Promise((r) => setTimeout(r, 300))
      setProgress('Creating GTM container & GA4 config tag...')
      await new Promise((r) => setTimeout(r, 300))
      setProgress('Applying tracking blueprint...')
      const body = {
        ...form,
        linked_domains: form.linked_domains ? form.linked_domains.split(',').map((d) => d.trim()) : [],
      }
      const data = await api<Record<string, unknown>>('/sites', {
        method: 'POST',
        body: JSON.stringify(body),
      })
      setProgress('Done!')
      setResult(data)
      setTimeout(() => navigate(`/sites/${form.domain}`), 2000)
    } catch (err) {
      setError(String(err))
      setProgress('')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div>
      <h2 style={{ marginBottom: '1.5rem' }}>Create Analytics Setup</h2>
      <div className="card">
        <form onSubmit={handleSubmit}>
          <label>Domain</label>
          <input required value={form.domain} onChange={(e) => setForm({ ...form, domain: e.target.value })} placeholder="example.com" />

          <label>Site Name</label>
          <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Example Site" />

          <label>Environment</label>
          <select value={form.environment} onChange={(e) => setForm({ ...form, environment: e.target.value })}>
            <option value="dev">dev</option>
            <option value="stage">stage</option>
            <option value="prod">prod</option>
          </select>

          <label>Blueprint</label>
          <select value={form.blueprint} onChange={(e) => setForm({ ...form, blueprint: e.target.value })}>
            <option value="saas">SaaS</option>
            <option value="ecommerce">Ecommerce</option>
            <option value="content">Content</option>
          </select>

          <label>Consent Preset</label>
          <select value={form.consent_preset} onChange={(e) => setForm({ ...form, consent_preset: e.target.value })}>
            <option value="none">none</option>
            <option value="basic">basic</option>
            <option value="advanced">advanced</option>
          </select>

          <label>Linked Domains (comma-separated)</label>
          <input value={form.linked_domains} onChange={(e) => setForm({ ...form, linked_domains: e.target.value })} placeholder="shop.example.com, app.example.com" />

          <label>
            <input type="checkbox" checked={form.enable_bigquery} onChange={(e) => setForm({ ...form, enable_bigquery: e.target.checked })} />
            {' '}Enable BigQuery Export
          </label>

          {form.enable_bigquery && (
            <>
              <label>BigQuery Project</label>
              <input value={form.bigquery_project} onChange={(e) => setForm({ ...form, bigquery_project: e.target.value })} />
              <label>BigQuery Dataset</label>
              <input value={form.bigquery_dataset} onChange={(e) => setForm({ ...form, bigquery_dataset: e.target.value })} />
            </>
          )}

          <button type="submit" disabled={submitting}>{submitting ? 'Creating...' : 'Create Setup'}</button>
        </form>
        {progress && <p className="progress">{progress}</p>}
        {error && <p className="error">{error}</p>}
        {result && (
          <div className="success">
            <p>Setup complete! Redirecting...</p>
            <pre>{JSON.stringify(result, null, 2)}</pre>
          </div>
        )}
      </div>
    </div>
  )
}
