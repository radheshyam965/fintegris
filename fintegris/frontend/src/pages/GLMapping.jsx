import { useEffect, useState, Fragment } from 'react'
import { api } from '../api/client.js'

export default function GLMapping() {
  const [rows, setRows] = useState([])
  const [error, setError] = useState(null)
  const [expanded, setExpanded] = useState(null)

  useEffect(() => {
    api.getGlMap().then(setRows).catch((e) => setError(e.message))
  }, [])

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">GL Mapping</h1>
          <p className="page-subtitle">Each transaction is classified with a confidence score. Low confidence is routed to review.</p>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="panel">
        {rows.length === 0 ? (
          <div className="empty-state">No GL classifications yet. Process a document first.</div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Tx ID</th>
                <th>Vendor</th>
                <th>GL Code</th>
                <th>GL Category</th>
                <th>Confidence</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <Fragment key={r.id}>
                  <tr style={{ cursor: 'pointer' }} onClick={() => setExpanded(expanded === r.id ? null : r.id)}>
                    <td className="mono">{r.tx_id}</td>
                    <td>{r.vendor}</td>
                    <td className="mono">{r.gl_code}</td>
                    <td>{r.gl_category}</td>
                    <td>
                      <span className={`badge ${r.confidence >= 80 ? 'ok' : 'warn'}`}>
                        {r.confidence.toFixed(0)}%
                      </span>
                      {r.needs_review ? <span className="badge warn" style={{ marginLeft: 6 }}>REVIEW</span> : null}
                    </td>
                    <td style={{ color: 'var(--ink-faint)', fontSize: 12 }}>{expanded === r.id ? '▲ hide' : '▼ why'}</td>
                  </tr>
                  {expanded === r.id && (
                    <tr>
                      <td colSpan={6} style={{ background: 'var(--bg)' }}>
                        <div className="explain-box">
                          <span className="explain-label">Why this classification</span>
                          {r.reason}
                        </div>
                      </td>
                    </tr>
                  )}
                </Fragment>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
