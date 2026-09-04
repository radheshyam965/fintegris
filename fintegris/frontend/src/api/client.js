const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function handle(res) {
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail || detail
    } catch (_) {
      // ignore
    }
    throw new Error(detail)
  }
  return res.json()
}

export const api = {
  uploadDocuments: (files, docType) => {
    const form = new FormData()
    for (const f of files) form.append('files', f)
    form.append('doc_type', docType)
    return fetch(`${BASE_URL}/upload`, { method: 'POST', body: form }).then(handle)
  },
  listDocuments: () => fetch(`${BASE_URL}/documents`).then(handle),
  process: () => fetch(`${BASE_URL}/process`, { method: 'POST' }).then(handle),
  reset: () => fetch(`${BASE_URL}/reset`, { method: 'POST' }).then(handle),
  getTransactions: () => fetch(`${BASE_URL}/transactions`).then(handle),
  getGlMap: () => fetch(`${BASE_URL}/gl-map`).then(handle),
  getReconciliations: () => fetch(`${BASE_URL}/reconcile`).then(handle),
  getAnomalies: () => fetch(`${BASE_URL}/anomalies`).then(handle),
  getReviews: () => fetch(`${BASE_URL}/reviews`).then(handle),
  decideReview: (id, decision, decidedBy) =>
    fetch(`${BASE_URL}/reviews/${id}/decision`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ decision, decided_by: decidedBy }),
    }).then(handle),
  getAuditLog: () => fetch(`${BASE_URL}/audit-log`).then(handle),
  getDashboard: () => fetch(`${BASE_URL}/dashboard`).then(handle),
}
