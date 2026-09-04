import { useEffect, useState } from 'react'
import { api } from '../api/client.js'
import StatusBadge from '../components/StatusBadge.jsx'

export default function Reconciliation() {
  const [rows, setRows] = useState([])
  const [error, setError] = useState(null)

  useEffect(() => {
    api.getReconciliations().then(setRows).catch((e) => setError(e.message))
  }, [])

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Reconciliation</h1>
          <p className="page-subtitle">Bank statement vs. company books — every transaction compared line by line.</p>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="panel">
        {rows.length === 0 ? (
          <div className="empty-state">
            No reconciliation results yet. Upload a "Bank Statement" and a "Company Books" document, then process them.
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Tx ID</th>
                <th>Vendor</th>
                <th>Bank</th>
                <th>Books</th>
                <th>Difference</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id}>
                  <td className="mono">{r.tx_id}</td>
                  <td>{r.vendor}</td>
                  <td className="mono">{r.bank_amount != null ? `₹${r.bank_amount.toLocaleString('en-IN')}` : '—'}</td>
                  <td className="mono">{r.books_amount != null ? `₹${r.books_amount.toLocaleString('en-IN')}` : '—'}</td>
                  <td className="mono" style={{ color: r.difference !== 0 ? 'var(--danger)' : 'inherit' }}>
                    {r.difference !== 0 ? `₹${Math.abs(r.difference).toLocaleString('en-IN')}` : '—'}
                  </td>
                  <td><StatusBadge status={r.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {rows.some((r) => r.status !== 'MATCHED') && (
        <div className="panel">
          <h3 className="panel-title">⚠ Mismatch Detail</h3>
          {rows.filter((r) => r.status !== 'MATCHED').map((r) => (
            <div key={r.id} className="review-grid" style={{ marginBottom: 16 }}>
              <div className="review-amount-block">
                <div className="review-amount-label">BANK</div>
                <div className="review-amount-value">{r.bank_amount != null ? `₹${r.bank_amount.toLocaleString('en-IN')}` : '—'}</div>
              </div>
              <div className="review-amount-block">
                <div className="review-amount-label">BOOKS</div>
                <div className="review-amount-value">{r.books_amount != null ? `₹${r.books_amount.toLocaleString('en-IN')}` : '—'}</div>
              </div>
              <div className="review-amount-block">
                <div className="review-amount-label">DIFFERENCE</div>
                <div className="review-amount-value danger">₹{Math.abs(r.difference).toLocaleString('en-IN')}</div>
              </div>
              <div style={{ gridColumn: '1 / -1' }}>
                <div className="explain-box">
                  <span className="explain-label">Explanation</span>
                  {r.reason}
                </div>
                <div style={{ marginTop: 10 }}><span className="badge warn">HUMAN REVIEW REQUIRED</span></div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
