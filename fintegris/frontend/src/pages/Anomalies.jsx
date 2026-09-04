import { useEffect, useState } from 'react'
import { api } from '../api/client.js'
import StatusBadge from '../components/StatusBadge.jsx'

export default function Anomalies() {
  const [rows, setRows] = useState([])
  const [error, setError] = useState(null)

  useEffect(() => {
    api.getAnomalies().then(setRows).catch((e) => setError(e.message))
  }, [])

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Anomaly Detection</h1>
          <p className="page-subtitle">Nothing is auto-corrected. Every anomaly is routed to human review.</p>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {rows.length === 0 ? (
        <div className="panel"><div className="empty-state">No anomalies detected yet.</div></div>
      ) : (
        rows.map((a) => (
          <div key={a.id} className="panel">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <div style={{ fontWeight: 700, marginBottom: 4 }}>⚠ ANOMALY DETECTED — <span className="mono">{a.tx_id}</span></div>
                <div style={{ color: 'var(--ink-soft)', fontSize: 13 }}>{a.reason}</div>
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <StatusBadge status={a.severity} />
                <StatusBadge status={a.status} />
              </div>
            </div>
            {a.difference !== 0 && (
              <div style={{ marginTop: 10 }}>
                <span className="badge danger">Difference: ₹{Math.abs(a.difference).toLocaleString('en-IN')}</span>
              </div>
            )}
            <div className="explain-box" style={{ marginTop: 12 }}>
              <span className="explain-label">Routing decision</span>
              This was not auto-corrected. It has been sent to Human Review for a supporting-evidence check.
            </div>
          </div>
        ))
      )}
    </div>
  )
}
