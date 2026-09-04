const DEFAULT_AGENTS = [
  'Document Intelligence Agent',
  'Transaction Intelligence Agent',
  'GL Mapping Agent',
  'Reconciliation Agent',
  'Anomaly Detection Agent',
  'Human Review',
  'Reporting Agent',
]

/**
 * steps: optional array of { agent, status } from POST /process.
 * If omitted, renders the static pipeline in a neutral state.
 */
export default function AgentPipeline({ steps }) {
  const byAgent = {}
  ;(steps || []).forEach((s) => { byAgent[s.agent] = s.status })

  return (
    <div className="pipeline">
      {DEFAULT_AGENTS.map((agent, i) => {
        const status = byAgent[agent]
        const cls = status === 'done' ? 'done' : status === 'attention' ? 'attention' : ''
        const icon = status === 'done' ? '✓' : status === 'attention' ? '⚠' : agent === 'Human Review' ? '☺' : '·'
        return (
          <span key={agent} style={{ display: 'flex', alignItems: 'center' }}>
            <span className={`pipeline-step ${cls}`}>
              <span>{icon}</span>
              <span>{agent}</span>
            </span>
            {i < DEFAULT_AGENTS.length - 1 && <span className="pipeline-arrow">→</span>}
          </span>
        )
      })}
    </div>
  )
}
