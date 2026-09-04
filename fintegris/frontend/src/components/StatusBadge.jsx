const STATUS_MAP = {
  MATCHED: { tone: 'ok', label: 'MATCHED' },
  AMOUNT_MISMATCH: { tone: 'danger', label: 'MISMATCH' },
  MISSING_IN_BOOKS: { tone: 'danger', label: 'MISSING IN BOOKS' },
  MISSING_IN_BANK: { tone: 'danger', label: 'MISSING IN BANK' },
  PENDING: { tone: 'neutral', label: 'PENDING' },
  Pending: { tone: 'warn', label: 'PENDING' },
  Approved: { tone: 'ok', label: 'APPROVED' },
  Rejected: { tone: 'danger', label: 'REJECTED' },
  Investigating: { tone: 'warn', label: 'INVESTIGATING' },
  Open: { tone: 'warn', label: 'OPEN' },
  Resolved: { tone: 'ok', label: 'RESOLVED' },
  High: { tone: 'danger', label: 'HIGH' },
  Medium: { tone: 'warn', label: 'MEDIUM' },
  Low: { tone: 'neutral', label: 'LOW' },
  uploaded: { tone: 'warn', label: 'UPLOADED' },
  processed: { tone: 'ok', label: 'PROCESSED' },
  error: { tone: 'danger', label: 'ERROR' },
}

export default function StatusBadge({ status }) {
  const info = STATUS_MAP[status] || { tone: 'neutral', label: status }
  return <span className={`badge ${info.tone}`}>{info.label}</span>
}
