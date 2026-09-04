import { useEffect, useRef, useState } from 'react'
import { api } from '../api/client.js'
import StatusBadge from '../components/StatusBadge.jsx'
import AgentPipeline from '../components/AgentPipeline.jsx'

const DOC_TYPES = [
  { value: 'general', label: 'General Transactions' },
  { value: 'bank_statement', label: 'Bank Statement' },
  { value: 'company_books', label: 'Company Books' },
]

export default function Documents() {
  const [docType, setDocType] = useState('general')
  const [documents, setDocuments] = useState([])
  const [dragActive, setDragActive] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [processing, setProcessing] = useState(false)
  const [steps, setSteps] = useState(null)
  const [error, setError] = useState(null)
  const fileInputRef = useRef()

  const loadDocuments = () => {
    api.listDocuments().then(setDocuments).catch((e) => setError(e.message))
  }

  useEffect(() => { loadDocuments() }, [])

  const doUpload = async (files) => {
    if (!files || files.length === 0) return
    setUploading(true)
    setError(null)
    try {
      await api.uploadDocuments(Array.from(files), docType)
      loadDocuments()
    } catch (e) {
      setError(e.message)
    } finally {
      setUploading(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragActive(false)
    doUpload(e.dataTransfer.files)
  }

  const handleProcess = async () => {
    setProcessing(true)
    setError(null)
    setSteps(null)
    try {
      const result = await api.process()
      setSteps(result.steps)
      loadDocuments()
    } catch (e) {
      setError(e.message)
    } finally {
      setProcessing(false)
    }
  }

  const pendingCount = documents.filter((d) => d.status === 'uploaded').length

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Upload Financial Documents</h1>
          <p className="page-subtitle">PDF, CSV, or Excel — tag each upload by source so reconciliation can compare them.</p>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="panel">
        <h3 className="panel-title">1. Choose document type</h3>
        <div className="doctype-select">
          {DOC_TYPES.map((dt) => (
            <div
              key={dt.value}
              className={'doctype-option' + (docType === dt.value ? ' selected' : '')}
              onClick={() => setDocType(dt.value)}
            >
              {dt.label}
            </div>
          ))}
        </div>

        <h3 className="panel-title">2. Drag & drop or browse</h3>
        <div
          className={'dropzone' + (dragActive ? ' active' : '')}
          onDragOver={(e) => { e.preventDefault(); setDragActive(true) }}
          onDragLeave={() => setDragActive(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current.click()}
        >
          <div style={{ fontSize: 24, marginBottom: 8 }}>⇧</div>
          <div style={{ fontWeight: 600, marginBottom: 4 }}>
            {uploading ? 'Uploading…' : 'Drag & drop files here, or click to browse'}
          </div>
          <div style={{ fontSize: 12 }}>Supported: PDF · CSV · Excel</div>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.csv,.xlsx,.xls"
            onChange={(e) => doUpload(e.target.files)}
          />
        </div>

        <div className="btn-row">
          <button className="btn primary" disabled={pendingCount === 0 || processing} onClick={handleProcess}>
            {processing ? 'Processing…' : `Process Documents (${pendingCount} pending)`}
          </button>
        </div>
      </div>

      {steps && (
        <div className="panel">
          <h3 className="panel-title">Pipeline Result</h3>
          <AgentPipeline steps={steps} />
          <ul className="checklist">
            {steps.map((s) => (
              <li key={s.agent} className={s.status === 'done' ? 'done' : ''}>
                <span className="tick">{s.status === 'done' ? '✓' : '!'}</span>
                {s.agent}: {s.detail}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="panel">
        <h3 className="panel-title">Uploaded Documents ({documents.length})</h3>
        {documents.length === 0 ? (
          <div className="empty-state">No documents uploaded yet.</div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>File name</th>
                <th>Type</th>
                <th>Status</th>
                <th>Uploaded</th>
              </tr>
            </thead>
            <tbody>
              {documents.map((d) => (
                <tr key={d.id}>
                  <td>{d.filename}</td>
                  <td>{d.doc_type}</td>
                  <td><StatusBadge status={d.status} /></td>
                  <td className="mono">{d.uploaded_at}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
