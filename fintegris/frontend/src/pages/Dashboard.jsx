import { useEffect, useState } from 'react'
import { api } from '../api/client.js'
import StatusBadge from '../components/StatusBadge.jsx'
import AgentPipeline from '../components/AgentPipeline.jsx'

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  const load = () => {
    api.getDashboard().then(setData).catch((e) => setError(e.message))
  }

  useEffect(() => { load() }, [])

  const cards = data && [
    { label: 'TOTAL TRANSACTIONS', value: data.total_transactions, tone: 'accent' },
    { label: 'MATCHED', value: data.matched, tone: 'ok' },
    { label: 'MISMATCHED', value: data.mismatched, tone: data.mismatched > 0 ? 'danger' : '' },
    { label: 'ANOMALIES', value: data.anomalies, tone: data.anomalies > 0 ? 'warn' : '' },
    { label: 'HUMAN REVIEW', value: data.human_review, tone: data.human_review > 0 ? 'warn' : '' },
  ]

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Financial Intelligence Dashboard</h1>
          <p className="page-subtitle">Live status across the reconciliation pipeline.</p>
        </div>
        <button className="btn ghost" onClick={load}>Refresh</button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {cards && (
        <div className="card-grid">
          {cards.map((c) => (
            <div key={c.label} className={`stat-card ${c.tone}`}>
              <div className="stat-label">{c.label}</div>
              <div className="stat-value">{c.value}</div>
            </div>
          ))}
        </div>
      )}

      <div className="panel">
        <h3 className="panel-title">Agent Pipeline Status</h3>
        <AgentPipeline />
      </div>

      <div className="panel">
        <h3 className="panel-title">Recent Transactions</h3>
        {!data || data.recent_transactions.length === 0 ? (
          <div className="empty-state">No transactions yet. Upload a document to get started.</div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Transaction</th>
                <th>Vendor</th>
                <th>Amount</th>
                <th>Reconciliation</th>
              </tr>
            </thead>
            <tbody>
              {data.recent_transactions.map((t) => (
                <tr key={t.tx_id}>
                  <td className="mono">{t.tx_id}</td>
                  <td>{t.vendor}</td>
                  <td className="mono">₹{t.amount.toLocaleString('en-IN')}</td>
                  <td><StatusBadge status={t.recon_status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
