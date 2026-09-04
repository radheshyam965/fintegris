import { useEffect, useState } from 'react'
import { api } from '../api/client.js'
import StatusBadge from '../components/StatusBadge.jsx'

export default function HumanReview() {
  const [rows, setRows] = useState([])
  const [error, setError] = useState(null)
  const [busyId, setBusyId] = useState(null)

  const load = () => {
    api.getReviews().then(setRows).catch((e) => setError(e.message))
  }

  useEffect(() => { load() }, [])

  const decide = async (id, decision) => {
    setBusyId(id)
    setError(null)
    try {
      await api.decideReview(id, decision, 'Finance Reviewer')
      load()
    } catch (e) {
      setError(e.message)
    } finally {
      setBusyId(null)
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Human Review</h1>
          <p className="page-subtitle">Uncertain decisions stop here. A reviewer decides — the system never overrides.</p>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {rows.length === 0 ? (
        <div className="panel"><div className="empty-state">Nothing awaiting review right now.</div></div>
      ) : (
        rows.map((r) => (
          <div key={r.id} className={'review-card' + (r.status !== 'Pending' ? ' resolved' : '')}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <div style={{ fontWeight: 700, fontSize: 15 }}>TRANSACTION REQUIRING REVIEW</div>
                <div className="mono" style={{ fontSize: 18, marginTop: 2 }}>{r.tx_id}</div>
                <div style={{ color: 'var(--ink-soft)', fontSize: 13 }}>Vendor: {r.vendor}</div>
              </div>
              <StatusBadge status={r.status} />
            </div>

            {(r.bank_amount != null || r.books_amount != null) && (
              <div className="review-grid">
                <div className="review-amount-block">
                  <div className="review-amount-label">BANK</div>
                  <div className="review-amount-value">₹{(r.bank_amount ?? 0).toLocaleString('en-IN')}</div>
                </div>
                <div className="review-amount-block">
                  <div className="review-amount-label">BOOKS</div>
                  <div className="review-amount-value">₹{(r.books_amount ?? 0).toLocaleString('en-IN')}</div>
                </div>
                <div className="review-amount-block">
                  <div className="review-amount-label">DIFFERENCE</div>
                  <div className="review-amount-value danger">₹{Math.abs(r.difference ?? 0).toLocaleString('en-IN')}</div>
                </div>
              </div>
            )}

            <div className="explain-box">
              <span className="explain-label">Reason</span>
              {r.reason}
            </div>
            <div className="explain-box" style={{ background: 'var(--ok-soft)', borderColor: '#bfe3d9' }}>
              <span className="explain-label" style={{ color: 'var(--ok)' }}>AI Recommendation</span>
              {r.ai_recommendation}
            </div>

            {r.status === 'Pending' ? (
              <div className="btn-row">
                <button className="btn success" disabled={busyId === r.id} onClick={() => decide(r.id, 'Approved')}>Approve</button>
                <button className="btn danger" disabled={busyId === r.id} onClick={() => decide(r.id, 'Rejected')}>Reject</button>
                <button className="btn ghost" disabled={busyId === r.id} onClick={() => decide(r.id, 'Investigating')}>Request Investigation</button>
              </div>
            ) : (
              <div style={{ marginTop: 14, fontSize: 12, color: 'var(--ink-faint)' }}>
                Decided by {r.decision_by} at {r.decision_at}
              </div>
            )}
          </div>
        ))
      )}
    </div>
  )
}
