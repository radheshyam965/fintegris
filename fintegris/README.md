# Fintegris
**Autonomous Multi-Agent AI for Financial Integrity**

Built for NIOHACK2026 — Theme 9: AI Agent for Finance.

Fintegris turns fragmented financial documents (bank statements, company
books, general transaction exports) into extracted transactions, GL
classifications, reconciliation results, anomaly flags, and an audit-ready
trail — with a human always in the loop on anything uncertain.

> Fintegris augments finance teams by automating repetitive financial
> operations while keeping humans in control of uncertain decisions.

---

## 1. Architecture

```
React Frontend  →  FastAPI Backend  →  Agent Orchestrator  →  Specialized Agents  →  SQLite
```

Pipeline (each stage is a separate Python module under `backend/agents/`):

```
Financial Documents
   → Document Intelligence Agent   (parses PDF/CSV/Excel into raw transactions)
   → Transaction Intelligence Agent (normalizes vendors/dates, flags duplicates)
   → GL Mapping Agent               (rule-based classification + confidence score)
   → Reconciliation Agent           (bank statement vs. company books)
   → Anomaly Detection Agent        (mismatches, duplicates, statistical outliers)
   → Human Review                   (approve / reject / investigate — nothing auto-fixes)
   → Reporting Agent                (dashboard + audit trail)
```

**Why it works without an API key:** GL classification and reconciliation
logic are 100% deterministic (rule/keyword-based), so the demo never depends
on network access or an LLM being available. If `ANTHROPIC_API_KEY` is set
in the environment, `backend/services/llm_service.py` will use it to generate
more natural-language explanations — but every function has a deterministic
fallback, so the app is fully functional either way.

---

## 2. Project structure

```
fintegris/
├── backend/
│   ├── main.py                  ← FastAPI app, all endpoints
│   ├── db.py                    ← SQLite schema + helpers
│   ├── requirements.txt
│   ├── agents/
│   │   ├── document_agent.py
│   │   ├── transaction_agent.py
│   │   ├── gl_agent.py
│   │   ├── reconciliation_agent.py
│   │   ├── anomaly_agent.py
│   │   └── reporting_agent.py
│   ├── services/
│   │   ├── file_parser.py       ← CSV / Excel / PDF extraction
│   │   └── llm_service.py       ← optional LLM calls, deterministic fallback
│   ├── models/
│   │   └── schemas.py
│   └── data/                    ← SQLite DB + uploaded files land here at runtime
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.jsx / App.jsx
│       ├── api/client.js
│       ├── components/          ← Sidebar, StatusBadge, AgentPipeline
│       └── pages/                ← Dashboard, Documents, Transactions,
│                                    GLMapping, Reconciliation, Anomalies,
│                                    HumanReview, AuditTrail
│
├── sample_data/
│   ├── bank_statement.csv        ← TX001–TX003
│   ├── company_books.csv         ← same 3, TX003 amount deliberately differs
│   └── messy_transactions.csv    ← messy headers/vendors, for the extraction demo
│
└── README.md
```

---

## 3. Install & run locally

You need **Python 3.10+** and **Node.js 18+** installed.

### Backend

```bash
cd fintegris/backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Backend is now running at `http://localhost:8000`.
(Optional) to enable real LLM-generated explanations instead of the
deterministic fallback text, set an environment variable before starting:

```bash
export ANTHROPIC_API_KEY=sk-ant-...     # optional, app works without this
```

### Frontend

In a second terminal:

```bash
cd fintegris/frontend
npm install
npm run dev
```

Frontend is now running at `http://localhost:5173` and talks to the backend
at `http://localhost:8000` (configurable via `VITE_API_URL` if needed).

Open **http://localhost:5173** in your browser.

---

## 4. Test procedure (do this before you demo!)

1. Start backend, then frontend, as above.
2. Open the app → go to **Documents**.
3. Select doc type **"Bank Statement"**, upload `sample_data/bank_statement.csv`.
4. Select doc type **"Company Books"**, upload `sample_data/company_books.csv`.
5. Click **Process Documents**. You should see all 7 pipeline steps turn green
   (Anomaly Detection / Human Review will show a "⚠ attention" state — that's
   correct, it means TX003 was caught).
6. Go to **Transactions** — 6 rows (3 from each source).
7. Go to **GL Mapping** — TX001 98%, TX002 96%, TX003 71% (flagged for review).
8. Go to **Reconciliation** — TX001/TX002 MATCHED, TX003 AMOUNT_MISMATCH with
   a ₹10,000 difference and a plain-English explanation.
9. Go to **Anomalies** — one High-severity anomaly on TX003.
10. Go to **Human Review** — click **Approve**, **Reject**, or **Request
    Investigation** and confirm the card updates.
11. Go to **Audit Trail** — confirm every step above has a timestamped entry,
    including your review decision.
12. Go to **Dashboard** — confirm TOTAL 3 / MATCHED 2 / MISMATCHED 1 /
    ANOMALIES 1 / HUMAN REVIEW 0 or 1 (depending whether you already decided it).

If you want to re-run the demo from a clean slate at any point:
`curl -X POST http://localhost:8000/reset`

**Bonus extraction demo:** upload `sample_data/messy_transactions.csv` as
doc type "General Transactions" before processing, to show the Document
Intelligence Agent handling inconsistent headers, vendor aliases, a real
duplicate row, and an unknown vendor — all in one file.

---

## 5. API reference

| Method | Endpoint                       | Purpose                                   |
|--------|---------------------------------|--------------------------------------------|
| POST   | `/upload`                       | Upload one or more files with a `doc_type` |
| GET    | `/documents`                    | List uploaded documents                    |
| POST   | `/process`                      | Run the full agent pipeline                |
| POST   | `/reset`                        | Wipe all data (fresh demo run)             |
| GET    | `/transactions`                 | Extracted + normalized transactions        |
| GET    | `/gl-map`                       | GL classifications + confidence            |
| GET    | `/reconcile`                    | Bank vs. books comparison results          |
| GET    | `/anomalies`                    | Flagged anomalies                          |
| GET    | `/reviews`                      | Human review queue                         |
| POST   | `/reviews/{id}/decision`        | Approve / Reject / Investigate             |
| GET    | `/audit-log`                    | Full audit trail                           |
| GET    | `/dashboard`                    | Aggregated dashboard numbers                |

---

## 6. Known limitations (see also the pitch doc for judge Q&A)

- GL classification is keyword/rule-based, not a trained ML model — deliberate,
  for demo reliability and explainability.
- Reconciliation matches strictly by `tx_id` — real-world statements often
  need fuzzy matching on amount+date+vendor when IDs don't align.
- PDF extraction is best-effort (table detection + regex fallback) and works
  best on text-based PDFs, not scanned images (no OCR included in the MVP).
- SQLite is single-writer; fine for a demo, would move to Postgres for
  multi-user production use.
