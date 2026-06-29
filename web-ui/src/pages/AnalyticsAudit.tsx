import { useState } from 'react'
import { runAudit } from '../api'

interface AuditFinding {
  severity: 'critical' | 'warning' | 'info'
  category: string
  issue: string
  description: string
  affected_pages: string[]
  fix_recommendation: string
  fix_complexity: 'simple' | 'moderate' | 'complex'
}

interface AuditReport {
  url: string
  audit_timestamp: string
  crawl_pages: number
  score: number
  grade: string
  critical_count: number
  warning_count: number
  info_count: number
  category_scores: Record<string, number>
  findings: AuditFinding[]
  working_well: string[]
  action_plan: Array<{
    priority: number
    fix: string
    effort: string
    impact: string
  }>
}

const categoryLabels: Record<string, string> = {
  tag_presence: 'Tag Presence',
  duplication: 'Duplicate Tracking',
  consent: 'Consent & Privacy',
  data_quality: 'Data Quality',
  ecommerce: 'E-commerce',
  spa_tracking: 'SPA Tracking',
  gtm_specific: 'GTM Configuration',
  performance: 'Performance',
}

const severityConfig = {
  critical: { icon: '🔴', color: '#dc2626', bg: '#fef2f2' },
  warning: { icon: '🟡', color: '#d97706', bg: '#fffbeb' },
  info: { icon: '🔵', color: '#2563eb', bg: '#eff6ff' },
}

function getGradeColor(grade: string): string {
  if (grade.startsWith('A')) return '#16a34a'
  if (grade.startsWith('B')) return '#65a30d'
  if (grade.startsWith('C')) return '#d97706'
  if (grade.startsWith('D')) return '#ea580c'
  return '#dc2626'
}

function ScoreRing({ score, grade }: { score: number; grade: string }) {
  const color = getGradeColor(grade)
  const circumference = 2 * Math.PI * 45
  const strokeDashoffset = circumference - (score / 100) * circumference

  return (
    <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
      <div
        style={{
          position: 'relative',
          width: '120px',
          height: '120px',
          margin: '0 auto',
        }}
      >
        <svg viewBox="0 0 100 100" style={{ transform: 'rotate(-90deg)' }}>
          <circle
            cx="50"
            cy="50"
            r="45"
            fill="none"
            stroke="#e5e7eb"
            strokeWidth="8"
          />
          <circle
            cx="50"
            cy="50"
            r="45"
            fill="none"
            stroke={color}
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            style={{ transition: 'stroke-dashoffset 1s ease' }}
          />
        </svg>
        <div
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            textAlign: 'center',
          }}
        >
          <div style={{ fontSize: '2rem', fontWeight: 'bold', color }}>{score}</div>
          <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>/100</div>
        </div>
      </div>
      <div
        style={{
          fontSize: '1.5rem',
          fontWeight: 'bold',
          color,
          marginTop: '0.5rem',
        }}
      >
        Grade {grade}
      </div>
    </div>
  )
}

function CategoryScore({ name, score }: { name: string; score: number }) {
  const color = score >= 80 ? '#16a34a' : score >= 60 ? '#d97706' : '#dc2626'

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0.75rem',
        padding: '0.75rem',
        background: '#f9fafb',
        borderRadius: '0.5rem',
      }}
    >
      <div
        style={{
          width: '40px',
          height: '40px',
          borderRadius: '50%',
          background: color,
          color: 'white',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontWeight: 'bold',
          fontSize: '0.875rem',
        }}
      >
        {score}
      </div>
      <div style={{ fontSize: '0.875rem', fontWeight: 500, color: '#374151' }}>
        {categoryLabels[name] || name}
      </div>
    </div>
  )
}

function FindingCard({ finding }: { finding: AuditFinding }) {
  const config = severityConfig[finding.severity]

  return (
    <div
      style={{
        border: `1px solid ${config.color}40`,
        borderRadius: '0.5rem',
        padding: '1rem',
        background: config.bg,
        marginBottom: '0.75rem',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'flex-start',
          gap: '0.75rem',
          marginBottom: '0.5rem',
        }}
      >
        <span style={{ fontSize: '1.25rem' }}>{config.icon}</span>
        <div style={{ flex: 1 }}>
          <div
            style={{
              fontWeight: 600,
              color: config.color,
              marginBottom: '0.25rem',
            }}
          >
            {finding.issue}
          </div>
          <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>
            {categoryLabels[finding.category] || finding.category}
          </div>
        </div>
        <span
          style={{
            padding: '0.25rem 0.5rem',
            background: config.color,
            color: 'white',
            borderRadius: '0.25rem',
            fontSize: '0.75rem',
            fontWeight: 500,
            textTransform: 'uppercase',
          }}
        >
          {finding.severity}
        </span>
      </div>

      <p
        style={{
          fontSize: '0.875rem',
          color: '#374151',
          marginBottom: '0.75rem',
          lineHeight: 1.5,
        }}
      >
        {finding.description}
      </p>

      {finding.affected_pages.length > 0 && (
        <div
          style={{
            fontSize: '0.75rem',
            color: '#6b7280',
            marginBottom: '0.75rem',
          }}
        >
          Affected: {finding.affected_pages.slice(0, 3).join(', ')}
          {finding.affected_pages.length > 3 &&
            ` (+${finding.affected_pages.length - 3} more)`}
        </div>
      )}

      <div
        style={{
          background: 'white',
          padding: '0.75rem',
          borderRadius: '0.375rem',
          border: '1px solid #e5e7eb',
        }}
      >
        <div
          style={{
            fontSize: '0.75rem',
            fontWeight: 600,
            color: '#374151',
            marginBottom: '0.25rem',
          }}
        >
          💡 Fix Recommendation
        </div>
        <div style={{ fontSize: '0.875rem', color: '#374151' }}>
          {finding.fix_recommendation}
        </div>
        <div
          style={{
            fontSize: '0.75rem',
            color: '#6b7280',
            marginTop: '0.25rem',
          }}
        >
          Complexity: {finding.fix_complexity}
        </div>
      </div>
    </div>
  )
}

function ActionPlan({ plan }: { plan: AuditReport['action_plan'] }) {
  return (
    <div
      style={{
        background: '#f9fafb',
        borderRadius: '0.5rem',
        padding: '1rem',
      }}
    >
      <h3 style={{ margin: '0 0 1rem 0', fontSize: '1rem' }}>
        📋 Prioritized Action Plan
      </h3>
      {plan.map((item, index) => (
        <div
          key={index}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
            padding: '0.75rem',
            background: 'white',
            borderRadius: '0.375rem',
            marginBottom: '0.5rem',
            borderLeft: `4px solid ${
              item.impact === 'High'
                ? '#dc2626'
                : item.impact === 'Legal'
                  ? '#d97706'
                  : '#2563eb'
            }`,
          }}
        >
          <div
            style={{
              width: '24px',
              height: '24px',
              borderRadius: '50%',
              background: '#2563eb',
              color: 'white',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '0.75rem',
              fontWeight: 'bold',
              flexShrink: 0,
            }}
          >
            {item.priority}
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 500, color: '#374151' }}>{item.fix}</div>
            <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>
              ⏱ {item.effort} • Impact: {item.impact}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

export default function AnalyticsAudit() {
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [report, setReport] = useState<AuditReport | null>(null)
  const [error, setError] = useState('')
  const [filter, setFilter] = useState<'all' | 'critical' | 'warning'>('all')

  const handleAudit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!url.trim()) return

    setLoading(true)
    setError('')
    setReport(null)

    try {
      const data = await runAudit(url)
      setReport(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to run audit')
    } finally {
      setLoading(false)
    }
  }

  const filteredFindings = report?.findings.filter((f) => {
    if (filter === 'all') return true
    if (filter === 'critical') return f.severity === 'critical'
    if (filter === 'warning') return f.severity === 'critical' || f.severity === 'warning'
    return true
  })

  const findingsByCategory = filteredFindings?.reduce(
    (acc, finding) => {
      const cat = finding.category
      if (!acc[cat]) acc[cat] = []
      acc[cat].push(finding)
      return acc
    },
    {} as Record<string, AuditFinding[]>
  )

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto' }}>
      <h1 style={{ marginBottom: '0.5rem' }}>Analytics Audit</h1>
      <p style={{ color: '#6b7280', marginBottom: '2rem' }}>
        Check any website's analytics implementation for common mistakes, missing tags, and
        compliance issues.
      </p>

      <form
        onSubmit={handleAudit}
        style={{
          display: 'flex',
          gap: '0.75rem',
          marginBottom: '2rem',
        }}
      >
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://example.com"
          required
          style={{
            flex: 1,
            padding: '0.75rem 1rem',
            borderRadius: '0.375rem',
            border: '1px solid #d1d5db',
            fontSize: '1rem',
          }}
        />
        <button
          type="submit"
          disabled={loading}
          style={{
            padding: '0.75rem 1.5rem',
            background: loading ? '#9ca3af' : '#2563eb',
            color: 'white',
            border: 'none',
            borderRadius: '0.375rem',
            fontSize: '1rem',
            fontWeight: 500,
            cursor: loading ? 'not-allowed' : 'pointer',
          }}
        >
          {loading ? 'Auditing...' : 'Run Audit'}
        </button>
      </form>

      {error && (
        <div
          style={{
            padding: '1rem',
            background: '#fef2f2',
            border: '1px solid #fecaca',
            borderRadius: '0.5rem',
            color: '#dc2626',
            marginBottom: '2rem',
          }}
        >
          {error}
        </div>
      )}

      {report && (
        <div>
          {/* Summary Header */}
          <div
            style={{
              background: 'white',
              borderRadius: '0.75rem',
              padding: '1.5rem',
              boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
              marginBottom: '1.5rem',
            }}
          >
            <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
              <div style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '0.25rem' }}>
                {report.url}
              </div>
              <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>
                {report.crawl_pages} pages audited •{' '}
                {new Date(report.audit_timestamp).toLocaleString()}
              </div>
            </div>

            <ScoreRing score={report.score} grade={report.grade} />

            {/* Issue Counts */}
            <div
              style={{
                display: 'flex',
                justifyContent: 'center',
                gap: '1.5rem',
                marginBottom: '1.5rem',
              }}
            >
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#dc2626' }}>
                  {report.critical_count}
                </div>
                <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>Critical</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#d97706' }}>
                  {report.warning_count}
                </div>
                <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>Warnings</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#2563eb' }}>
                  {report.info_count}
                </div>
                <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>Info</div>
              </div>
            </div>

            {/* Category Scores */}
            <div>
              <h3 style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.75rem' }}>
                Category Breakdown
              </h3>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                  gap: '0.5rem',
                }}
              >
                {Object.entries(report.category_scores).map(([name, score]) => (
                  <CategoryScore key={name} name={name} score={score} />
                ))}
              </div>
            </div>
          </div>

          {/* Action Plan */}
          {report.action_plan.length > 0 && (
            <div style={{ marginBottom: '1.5rem' }}>
              <ActionPlan plan={report.action_plan} />
            </div>
          )}

          {/* Findings Filter */}
          <div
            style={{
              display: 'flex',
              gap: '0.5rem',
              marginBottom: '1rem',
            }}
          >
            {(['all', 'critical', 'warning'] as const).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                style={{
                  padding: '0.5rem 1rem',
                  borderRadius: '0.375rem',
                  border: 'none',
                  background: filter === f ? '#2563eb' : '#e5e7eb',
                  color: filter === f ? 'white' : '#374151',
                  fontSize: '0.875rem',
                  fontWeight: 500,
                  cursor: 'pointer',
                }}
              >
                {f === 'all'
                  ? `All Issues (${report.findings.length})`
                  : f === 'critical'
                    ? `Critical (${report.critical_count})`
                    : `Warnings+ (${report.critical_count + report.warning_count})`}
              </button>
            ))}
          </div>

          {/* Findings by Category */}
          {findingsByCategory && Object.entries(findingsByCategory).length > 0 ? (
            <div>
              {Object.entries(findingsByCategory).map(([category, findings]) => (
                <div key={category} style={{ marginBottom: '1.5rem' }}>
                  <h3
                    style={{
                      fontSize: '1rem',
                      fontWeight: 600,
                      marginBottom: '0.75rem',
                      color: '#374151',
                    }}
                  >
                    {categoryLabels[category] || category}
                    <span
                      style={{
                        marginLeft: '0.5rem',
                        padding: '0.125rem 0.5rem',
                        background: '#e5e7eb',
                        borderRadius: '0.25rem',
                        fontSize: '0.75rem',
                      }}
                    >
                      {findings.length}
                    </span>
                  </h3>
                  {findings.map((finding, index) => (
                    <FindingCard key={index} finding={finding} />
                  ))}
                </div>
              ))}
            </div>
          ) : (
            <div
              style={{
                padding: '2rem',
                textAlign: 'center',
                background: '#f0fdf4',
                borderRadius: '0.5rem',
                color: '#16a34a',
              }}
            >
              <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>✅</div>
              <div style={{ fontWeight: 600 }}>No issues found!</div>
              <div style={{ fontSize: '0.875rem' }}>
                Great job - no {filter === 'critical' ? 'critical' : 'filtered'} issues detected.
              </div>
            </div>
          )}

          {/* What's Working Well */}
          {report.working_well.length > 0 && (
            <div
              style={{
                background: '#f0fdf4',
                borderRadius: '0.5rem',
                padding: '1rem',
                marginTop: '1.5rem',
              }}
            >
              <h3 style={{ margin: '0 0 0.75rem 0', fontSize: '1rem', color: '#166534' }}>
                ✅ What's Working Well
              </h3>
              <ul style={{ margin: 0, paddingLeft: '1.25rem', color: '#166534' }}>
                {report.working_well.map((item, index) => (
                  <li key={index} style={{ marginBottom: '0.25rem' }}>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
