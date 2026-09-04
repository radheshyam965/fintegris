"""
Fintegris - Reporting Agent.

Aggregates everything into the numbers the dashboard and audit
report need. Pure read/aggregation - no side effects.
"""

import db


def get_dashboard():
    conn = db.get_conn()

    # Count distinct logical transactions, not physical rows - a tx that
    # appears in both the bank statement and company books is still ONE
    # transaction, just seen from two sources.
    total_tx = conn.execute("SELECT COUNT(DISTINCT tx_id) c FROM transactions").fetchone()["c"]
    matched = conn.execute("SELECT COUNT(*) c FROM reconciliations WHERE status = 'MATCHED'").fetchone()["c"]
    mismatched = conn.execute(
        "SELECT COUNT(*) c FROM reconciliations WHERE status != 'MATCHED'"
    ).fetchone()["c"]
    anomalies = conn.execute("SELECT COUNT(*) c FROM anomalies WHERE status = 'Open'").fetchone()["c"]
    pending_review = conn.execute("SELECT COUNT(*) c FROM reviews WHERE status = 'Pending'").fetchone()["c"]

    recent = conn.execute(
        """SELECT t.tx_id, t.vendor, t.amount,
                  COALESCE(r.status, 'PENDING') as recon_status
           FROM transactions t
           LEFT JOIN reconciliations r ON t.tx_id = r.tx_id
           GROUP BY t.tx_id
           ORDER BY t.id DESC LIMIT 10"""
    ).fetchall()

    conn.close()

    return {
        "total_transactions": total_tx,
        "matched": matched,
        "mismatched": mismatched,
        "anomalies": anomalies,
        "human_review": pending_review,
        "recent_transactions": [dict(r) for r in recent],
    }


def get_audit_log():
    conn = db.get_conn()
    rows = conn.execute("SELECT * FROM audit_log ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]
