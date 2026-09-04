import { NavLink } from 'react-router-dom'

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: '◆' },
  { to: '/documents', label: 'Documents', icon: '▤' },
  { to: '/transactions', label: 'Transactions', icon: '≡' },
  { to: '/gl-mapping', label: 'GL Mapping', icon: '#' },
  { to: '/reconciliation', label: 'Reconciliation', icon: '⇄' },
  { to: '/anomalies', label: 'Anomalies', icon: '!' },
  { to: '/human-review', label: 'Human Review', icon: '☺' },
  { to: '/audit-trail', label: 'Audit Trail', icon: '⌘' },
]

export default function Sidebar({ counts }) {
  return (
    <nav className="sidebar">
      <div className="sidebar-brand">
        <span className="mark" />
        <span className="sidebar-brand-name">Fintegris</span>
      </div>
      <div style={{ padding: '0 10px 14px 10px', marginTop: -10 }}>
        <span className="sidebar-brand-tag">Multi-Agent Financial Integrity</span>
      </div>
      <ul className="nav-list">
        {NAV_ITEMS.map((item) => (
          <li key={item.to}>
            <NavLink
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) => 'nav-item' + (isActive ? ' active' : '')}
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
              {counts && counts[item.to] ? <span className="count">{counts[item.to]}</span> : null}
            </NavLink>
          </li>
        ))}
      </ul>
      <div className="sidebar-footer">
        Fintegris augments finance teams — humans stay in control of uncertain decisions.
      </div>
    </nav>
  )
}
