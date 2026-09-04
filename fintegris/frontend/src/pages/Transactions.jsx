import { useEffect, useState } from 'react'
import { api } from '../api/client.js'

export default function Transactions() {
  const [rows, setRows] = useState([])
  const [error, setError] = useState(null)

  useEffect(() => {
    api.getTransactions().then(setRows).catch((e) => setError(e.message))
  }, [])

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Extracted Transactions</h1>
          <p className="page-subtitle">Structured records pulled from every uploaded document.</p>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="panel">
        {rows.length === 0 ? (
          <div className="empty-state">No transactions extracted yet. Upload and process a document first.</div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Tx ID</th>
                <th>Date</th>
                <th>Vendor</th>
                <th>Amount</th>
                <th>Description</th>
                <th>Source</th>
                <th>Doc Type</th>
                <th>Flags</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id}>
                  <td className="mono">{r.tx_id}</td>
                  <td className="mono">{r.date}</td>
                  <td>{r.vendor}</td>
                  <td className="mono">₹{r.amount?.toLocaleString('en-IN')}</td>
                  <td>{r.description}</td>
                  <td style={{ fontSize: 12, color: 'var(--ink-faint)' }}>{r.source_document}</td>
                  <td style={{ fontSize: 12 }}>{r.doc_type}</td>
                  <td>
                    {r.duplicate_flag ? <span className="badge warn">DUPLICATE</span> : null}
                    {r.normalized ? null : <span className="badge neutral">RAW</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
