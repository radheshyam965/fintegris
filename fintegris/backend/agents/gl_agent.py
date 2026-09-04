"""
Fintegris - GL Mapping Agent.

Deterministic rule/keyword-based GL classification with a confidence
score. This is the "AI" layer that works with zero external API calls,
and can optionally be upgraded with an LLM explanation (see
services/llm_service.py) without changing the classification logic
itself -- classification stays deterministic so demo results never
vary between runs.
"""

from datetime import datetime
import db
from services.llm_service import explain_gl_mapping

# vendor keyword -> (gl_code, gl_category, confidence)
VENDOR_GL_TABLE = {
    "aws": ("IT-001", "Cloud / IT Expense", 98),
    "abc supplies": ("OPS-002", "Office Supplies", 96),
    "xyz services": ("SER-003", "Professional Services", 71),
}

# fallback keyword -> (gl_code, gl_category, confidence)
KEYWORD_GL_TABLE = [
    (["cloud", "hosting", "server", "saas", "software"], ("IT-010", "Cloud / IT Expense", 85)),
    (["consult", "professional", "advisory", "legal"], ("SER-020", "Professional Services", 80)),
    (["supplies", "stationery", "office"], ("OPS-030", "Office Supplies", 82)),
    (["travel", "flight", "hotel", "cab"], ("TRV-040", "Travel & Expenses", 78)),
    (["salary", "payroll", "wages"], ("HR-050", "Payroll", 90)),
    (["rent", "lease"], ("FAC-060", "Facilities / Rent", 88)),
]

DEFAULT_GL = ("UNC-000", "Uncategorized", 50)


def classify(vendor: str, description: str):
    v = (vendor or "").lower()
    d = (description or "").lower()

    for key, gl in VENDOR_GL_TABLE.items():
        if key in v:
            return gl

    for keywords, gl in KEYWORD_GL_TABLE:
        if any(k in v or k in d for k in keywords):
            return gl

    return DEFAULT_GL


def run_gl_mapping():
    conn = db.get_conn()
    rows = conn.execute(
        """SELECT t.* FROM transactions t
           LEFT JOIN gl_mappings g ON t.tx_id = g.tx_id
           WHERE g.id IS NULL AND t.normalized = 1"""
    ).fetchall()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    count = 0
    already_mapped_this_run = set()
    for row in rows:
        # A logical transaction can appear as two physical rows (one from the
        # bank statement, one from company books). GL classification is a
        # property of the transaction, not of which ledger it came from -
        # so only classify each tx_id once per run.
        if row["tx_id"] in already_mapped_this_run:
            continue
        already_mapped_this_run.add(row["tx_id"])

        gl_code, gl_category, confidence = classify(row["vendor"], row["description"])
        reason = explain_gl_mapping(row["vendor"], gl_category, row["description"])
        needs_review = 1 if confidence < 80 else 0

        conn.execute(
            """INSERT INTO gl_mappings
               (tx_id, vendor, gl_code, gl_category, confidence, reason, needs_review, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (row["tx_id"], row["vendor"], gl_code, gl_category, confidence, reason, needs_review, now),
        )
        count += 1
    conn.commit()
    conn.close()

    db.log_audit("GL mapping completed", "GL Mapping Agent", f"{count} records")
    return count
