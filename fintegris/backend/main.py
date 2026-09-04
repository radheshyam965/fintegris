"""
Fintegris - Autonomous Multi-Agent AI for Financial Integrity
Backend entrypoint (FastAPI).

Run with:  uvicorn main:app --reload --port 8000
"""

import os
import shutil
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import db
from models.schemas import ReviewDecision
from agents import document_agent, transaction_agent, gl_agent, reconciliation_agent, anomaly_agent, reporting_agent

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "data", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="Fintegris API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    db.init_db()


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------

@app.post("/upload")
async def upload_documents(
    files: list[UploadFile] = File(...),
    doc_type: str = Form("general"),
):
    """
    doc_type: 'general' | 'bank_statement' | 'company_books'
    Multiple files can be uploaded at once.
    """
    if doc_type not in ("general", "bank_statement", "company_books"):
        raise HTTPException(400, "doc_type must be general, bank_statement, or company_books")

    saved = []
    conn = db.get_conn()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for f in files:
        ext = os.path.splitext(f.filename)[1].lower()
        if ext not in (".csv", ".xlsx", ".xls", ".pdf"):
            raise HTTPException(400, f"Unsupported file type: {f.filename}")

        dest_path = os.path.join(UPLOAD_DIR, f"{int(datetime.now().timestamp()*1000)}_{f.filename}")
        with open(dest_path, "wb") as out:
            shutil.copyfileobj(f.file, out)

        cur = conn.execute(
            "INSERT INTO documents (filename, doc_type, filepath, status, uploaded_at) VALUES (?, ?, ?, 'uploaded', ?)",
            (f.filename, doc_type, dest_path, now),
        )
        saved.append({"id": cur.lastrowid, "filename": f.filename, "doc_type": doc_type})

    conn.commit()
    conn.close()

    db.log_audit("Document uploaded", "User", f"{len(saved)} file(s): {', '.join(s['filename'] for s in saved)}")

    return {"uploaded": saved, "count": len(saved)}


@app.get("/documents")
def list_documents():
    conn = db.get_conn()
    rows = conn.execute("SELECT * FROM documents ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

@app.post("/process")
def process_documents():
    """
    Runs the full agent pipeline over every not-yet-processed document,
    then GL-maps, reconciles, and detects anomalies across the whole
    transaction set. Returns a step-by-step trace for the UI to animate.
    """
    conn = db.get_conn()
    pending_docs = conn.execute("SELECT * FROM documents WHERE status = 'uploaded'").fetchall()
    conn.close()

    if not pending_docs:
        raise HTTPException(400, "No unprocessed documents. Upload a document first.")

    steps = []

    extracted_total = 0
    for doc in pending_docs:
        n = document_agent.process_document(doc)
        extracted_total += n
    steps.append({"agent": "Document Intelligence Agent", "status": "done", "detail": f"{extracted_total} transactions extracted"})

    n_norm = transaction_agent.run_normalization()
    steps.append({"agent": "Transaction Intelligence Agent", "status": "done", "detail": f"{n_norm} transactions normalized"})

    n_gl = gl_agent.run_gl_mapping()
    steps.append({"agent": "GL Mapping Agent", "status": "done", "detail": f"{n_gl} transactions classified"})

    recon = reconciliation_agent.run_reconciliation()
    steps.append({"agent": "Reconciliation Agent", "status": "done", "detail": f"{recon['matched']} matched / {recon['mismatched']} mismatched"})

    flagged = anomaly_agent.run_anomaly_detection()
    steps.append({
        "agent": "Anomaly Detection Agent",
        "status": "attention" if flagged else "done",
        "detail": f"{len(flagged)} anomalies found" if flagged else "No anomalies found",
    })

    steps.append({
        "agent": "Human Review",
        "status": "attention" if flagged else "done",
        "detail": f"{len(flagged)} case(s) awaiting review" if flagged else "Nothing pending",
    })

    steps.append({"agent": "Reporting Agent", "status": "done", "detail": "Dashboard updated"})

    return {"steps": steps, "reconciliation_summary": recon, "anomalies_found": flagged}


@app.post("/reset")
def reset_everything():
    """Wipes all data - handy to re-run the demo from a clean slate."""
    db.reset_db()
    db.log_audit("System reset", "User", "All data cleared")
    return {"status": "reset"}


# ---------------------------------------------------------------------------
# Transactions / GL / Reconciliation / Anomalies (read endpoints)
# ---------------------------------------------------------------------------

@app.get("/transactions")
def get_transactions():
    conn = db.get_conn()
    rows = conn.execute("SELECT * FROM transactions ORDER BY id ASC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/gl-map")
def get_gl_mappings():
    conn = db.get_conn()
    rows = conn.execute("SELECT * FROM gl_mappings ORDER BY id ASC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/reconcile")
def get_reconciliations():
    conn = db.get_conn()
    rows = conn.execute("SELECT * FROM reconciliations ORDER BY id ASC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/anomalies")
def get_anomalies():
    conn = db.get_conn()
    rows = conn.execute("SELECT * FROM anomalies ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Human review
# ---------------------------------------------------------------------------

@app.get("/reviews")
def get_reviews():
    conn = db.get_conn()
    rows = conn.execute("SELECT * FROM reviews ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.post("/reviews/{review_id}/decision")
def decide_review(review_id: int, body: ReviewDecision):
    if body.decision not in ("Approved", "Rejected", "Investigating"):
        raise HTTPException(400, "decision must be Approved, Rejected, or Investigating")

    conn = db.get_conn()
    row = conn.execute("SELECT * FROM reviews WHERE id = ?", (review_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(404, "Review not found")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "UPDATE reviews SET status = ?, decision_by = ?, decision_at = ? WHERE id = ?",
        (body.decision, body.decided_by, now, review_id),
    )
    if body.decision in ("Approved", "Rejected"):
        conn.execute("UPDATE anomalies SET status = 'Resolved' WHERE tx_id = ?", (row["tx_id"],))

    conn.commit()
    conn.close()

    db.log_audit(
        f"Review decision: {body.decision}",
        body.decided_by or "Reviewer",
        f"{row['tx_id']} marked {body.decision}",
    )
    return {"status": "ok", "tx_id": row["tx_id"], "decision": body.decision}


# ---------------------------------------------------------------------------
# Audit + Dashboard
# ---------------------------------------------------------------------------

@app.get("/audit-log")
def audit_log():
    return reporting_agent.get_audit_log()


@app.get("/dashboard")
def dashboard():
    return reporting_agent.get_dashboard()


@app.get("/")
def root():
    return {"service": "Fintegris API", "status": "running"}
