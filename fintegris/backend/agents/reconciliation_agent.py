"""
Fintegris - Reconciliation Agent.

Compares transactions tagged as doc_type='bank_statement' against
doc_type='company_books' and produces a per-transaction status:
MATCHED, AMOUNT_MISMATCH, MISSING_IN_BOOKS, MISSING_IN_BANK.

This is the centerpiece demo feature.
"""

from datetime import datetime
import db
from services.llm_service import explain_reconciliation


def run_reconciliation():
    conn = db.get_conn()

    # Clear previous reconciliation results so re-running /process is idempotent
    conn.execute("DELETE FROM reconciliations")

    bank_rows = conn.execute(
        "SELECT * FROM transactions WHERE doc_type = 'bank_statement'"
    ).fetchall()
    books_rows = conn.execute(
        "SELECT * FROM transactions WHERE doc_type = 'company_books'"
    ).fetchall()

    bank_by_id = {r["tx_id"]: r for r in bank_rows}
    books_by_id = {r["tx_id"]: r for r in books_rows}

    all_ids = sorted(set(bank_by_id.keys()) | set(books_by_id.keys()))
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    matched, mismatched = 0, 0

    for tx_id in all_ids:
        bank = bank_by_id.get(tx_id)
        books = books_by_id.get(tx_id)

        bank_amount = bank["amount"] if bank else None
        books_amount = books["amount"] if books else None
        vendor = (bank or books)["vendor"]

        if bank and not books:
            status, reason = "MISSING_IN_BOOKS", f"Transaction {tx_id} appears in the bank statement but not in company books."
        elif books and not bank:
            status, reason = "MISSING_IN_BANK", f"Transaction {tx_id} appears in company books but not in the bank statement."
        elif round(bank_amount, 2) == round(books_amount, 2):
            status, reason = "MATCHED", "Bank and books amounts agree."
            matched += 1
        else:
            difference = round(bank_amount - books_amount, 2)
            status = "AMOUNT_MISMATCH"
            reason = explain_reconciliation(tx_id, vendor, bank_amount, books_amount, difference)
            mismatched += 1

        difference = round((bank_amount or 0) - (books_amount or 0), 2)

        conn.execute(
            """INSERT INTO reconciliations
               (tx_id, vendor, bank_amount, books_amount, difference, status, reason, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (tx_id, vendor, bank_amount, books_amount, difference, status, reason, now),
        )

    conn.commit()
    conn.close()

    db.log_audit(
        "Reconciliation completed",
        "Reconciliation Agent",
        f"{matched} matched, {mismatched} mismatched, {len(all_ids) - matched - mismatched} missing",
    )
    return {"matched": matched, "mismatched": mismatched, "total": len(all_ids)}
