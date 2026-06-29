const API = '/api'

export async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })
  if (!res.ok) {
    const errorText = await res.text()
    // Sanitize error text to prevent XSS
    const sanitized = errorText.replace(/[<>]/g, '')
    throw new Error(`API Error (${res.status}): ${sanitized.slice(0, 200)}`)
  }
  return res.json()
}

export interface Site {
  id: number
  domain: string
  name: string
  environment: string
  status: string
  blueprint: string | null
  consent_preset: string
  ga4_measurement_id: string | null
  gtm_container_public_id: string | null
  gtm_latest_version_id: string | null
  bigquery_enabled: boolean
}

export interface HealthResult {
  status: string
  event_count_24h: number
  conversion_count_24h: number
  traffic_sessions_24h: number
  anomaly_flags: string[]
}

export interface AuditLog {
  id: number
  operation: string
  actor: string
  status: string
  details: Record<string, unknown> | null
  created_at: string
}

export interface Blueprint {
  name: string
  description: string
  version: string
}
