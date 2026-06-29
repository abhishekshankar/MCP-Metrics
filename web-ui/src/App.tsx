import { Link, Route, Routes, useLocation } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import CreateSite from './pages/CreateSite'
import SiteDetail from './pages/SiteDetail'
import Blueprints from './pages/Blueprints'
import AuditLog from './pages/AuditLog'
import AnalyticsAudit from './pages/AnalyticsAudit'

export default function App() {
  const location = useLocation()
  const isActive = (path: string) => location.pathname === path ? 'active' : ''

  return (
    <div className="app">
      <aside className="sidebar">
        <h1>Analytics MCP</h1>
        <nav>
          <Link to="/" className={isActive('/')}>Dashboard</Link>
          <Link to="/create" className={isActive('/create')}>Create Setup</Link>
          <Link to="/blueprints" className={isActive('/blueprints')}>Blueprints</Link>
          <Link to="/audit-check" className={isActive('/audit-check')}>🔍 Audit Site</Link>
          <Link to="/audit" className={isActive('/audit')}>Audit Log</Link>
        </nav>
      </aside>
      <main className="main">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/create" element={<CreateSite />} />
          <Route path="/sites/:domain" element={<SiteDetail />} />
          <Route path="/blueprints" element={<Blueprints />} />
          <Route path="/audit-check" element={<AnalyticsAudit />} />
          <Route path="/audit" element={<AuditLog />} />
        </Routes>
      </main>
    </div>
  )
}
