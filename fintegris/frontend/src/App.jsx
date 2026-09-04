import { Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Documents from './pages/Documents.jsx'
import Transactions from './pages/Transactions.jsx'
import GLMapping from './pages/GLMapping.jsx'
import Reconciliation from './pages/Reconciliation.jsx'
import Anomalies from './pages/Anomalies.jsx'
import HumanReview from './pages/HumanReview.jsx'
import AuditTrail from './pages/AuditTrail.jsx'

export default function App() {
  return (
    <div className="app-shell">
      <Sidebar />
      <main className="main">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/documents" element={<Documents />} />
          <Route path="/transactions" element={<Transactions />} />
          <Route path="/gl-mapping" element={<GLMapping />} />
          <Route path="/reconciliation" element={<Reconciliation />} />
          <Route path="/anomalies" element={<Anomalies />} />
          <Route path="/human-review" element={<HumanReview />} />
          <Route path="/audit-trail" element={<AuditTrail />} />
        </Routes>
      </main>
    </div>
  )
}
