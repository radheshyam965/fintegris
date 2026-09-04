"""
Fintegris - Anomaly Detection Agent.

Combines three simple, explainable signals (no black-box magic):
  1. Reconciliation mismatches / missing transactions (rule-based)
  2. Duplicate transactions (rule-based, from Transaction Agent)
  3. Statistically unusual amounts (scikit-learn IsolationForest,
     used ONLY as a secondary signal -- never the sole reason a
     transaction is flagged, and never used to auto-fix anything)

Every anomaly is routed to Human Review. Nothing is auto-corrected.
"""

from datetime import datetime
import db
from services.llm_service import recommend_review_action

SEVERITY_HIGH_PCT = 0.15   # >=15% difference relative to books amount
SEVERITY_MEDIUM_PCT = 0.05


def _severity_from_pct(pct_diff: float) -> str:
    if pct_diff >= SEVERITY_HIGH_PCT:
        return "High"
    elif pct_diff >= SEVERITY_MEDIUM_PCT:
        return "Medium"
    return "Low"


def _statistical_outliers(conn):
    """Optional secondary signal using scikit-learn. Returns a set of tx_ids
    whose amount looks unusual relative to the rest of the batch. Silently
    returns an empty set if there isn't enough data to fit a model -- this
    keeps small demo batches from erroring out."""
    try:
        from sklearn.ensemble import IsolationForest
        import numpy as np

        rows = conn.execute("SELECT tx_id, amount FROM transactions WHERE normalized = 1").fetchall()
        if len(rows) < 6:
            return set()

        amounts = np.array([[r["amount"]] for r in rows])
        model = IsolationForest(contamination=0.15, random_state=42)
        preds = model.fit_predict(amounts)
        return {rows[i]["tx_id"] for i, p in enumerate(preds) if p == -1}
    except Exception:
        return set()


def run_anomaly_detection():
    conn = db.get_conn()
    conn.execute("DELETE FROM anomalies")
    conn.execute("DELETE FROM reviews WHERE status = 'Pending'")

    flagged = {}  # tx_id -> {reasons: [...], severity, difference, vendor}

    # 1. Reconciliation-based anomalies
    for r in conn.execute("SELECT * FROM reconciliations WHERE status != 'MATCHED'").fetchall():
        books_amt = r["books_amount"] or r["bank_amount"] or 1
        pct = abs(r["difference"]) / books_amt if books_amt else 1.0
        severity = _severity_from_pct(pct) if r["status"] == "AMOUNT_MISMATCH" else "High"
        entry = flagged.setdefault(r["tx_id"], {"reasons": [], "severity": severity, "difference": r["difference"], "vendor": r["vendor"]})
        if r["status"] == "AMOUNT_MISMATCH":
            entry["reasons"].append(f"Amount mismatch (bank ₹{r['bank_amount']:,.0f} vs books ₹{r['books_amount']:,.0f})")
        elif r["status"] == "MISSING_IN_BOOKS":
            entry["reasons"].append("Present in bank statement but missing from company books")
        elif r["status"] == "MISSING_IN_BANK":
            entry["reasons"].append("Present in company books but missing from bank statement")

    # 2. Duplicate transactions
    for r in conn.execute("SELECT * FROM transactions WHERE duplicate_flag = 1").fetchall():
        entry = flagged.setdefault(r["tx_id"], {"reasons": [], "severity": "Medium", "difference": 0, "vendor": r["vendor"]})
        entry["reasons"].append(f"Possible duplicate transaction (same vendor, date and amount as another record)")

    # 3. Low-confidence GL classification
    for r in conn.execute("SELECT * FROM gl_mappings WHERE needs_review = 1").fetchall():
        entry = flagged.setdefault(r["tx_id"], {"reasons": [], "severity": "Low", "difference": 0, "vendor": r["vendor"]})
        entry["reasons"].append(f"GL classification confidence is low ({r['confidence']:.0f}%)")

    # 4. Statistical outliers (secondary signal only, never sole reason on its own line item unless nothing else fired)
    outlier_ids = _statistical_outliers(conn)
    for tx_id in outlier_ids:
        row = conn.execute("SELECT * FROM transactions WHERE tx_id = ? LIMIT 1", (tx_id,)).fetchone()
        if row:
            entry = flagged.setdefault(tx_id, {"reasons": [], "severity": "Low", "difference": 0, "vendor": row["vendor"]})
            entry["reasons"].append("Amount is statistically unusual compared to other transactions in this batch")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    severity_rank = {"Low": 0, "Medium": 1, "High": 2}

    for tx_id, data in flagged.items():
        combined_reason = "; ".join(data["reasons"])
        # escalate severity if multiple independent reasons fired
        severity = data["severity"]
        if len(data["reasons"]) >= 2 and severity_rank[severity] < severity_rank["High"]:
            severity = "Medium" if severity == "Low" else "High"

        conn.execute(
            """INSERT INTO anomalies (tx_id, reason, severity, difference, status, created_at)
               VALUES (?, ?, ?, ?, 'Open', ?)""",
            (tx_id, combined_reason, severity, data["difference"], now),
        )

        recon = conn.execute("SELECT * FROM reconciliations WHERE tx_id = ?", (tx_id,)).fetchone()
        bank_amount = recon["bank_amount"] if recon else None
        books_amount = recon["books_amount"] if recon else None

        ai_rec = recommend_review_action(tx_id, data["vendor"], data["difference"])

        conn.execute(
            """INSERT INTO reviews
               (tx_id, vendor, reason, ai_recommendation, bank_amount, books_amount, difference, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending', ?)""",
            (tx_id, data["vendor"], combined_reason, ai_rec, bank_amount, books_amount, data["difference"], now),
        )

    conn.commit()
    conn.close()

    db.log_audit("Anomaly detected" if flagged else "Anomaly scan completed",
                 "Anomaly Detection Agent",
                 ", ".join(flagged.keys()) if flagged else "No anomalies found")
    return list(flagged.keys())
