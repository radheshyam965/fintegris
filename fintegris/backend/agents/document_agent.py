"""
Fintegris - Document Intelligence Agent.

Responsible for turning an uploaded file into raw transaction rows
in the database. This is Step 1 of the pipeline.
"""

from datetime import datetime
from services.file_parser import parse_file
import db


def process_document(document_row):
    """
    document_row: sqlite3.Row from the documents table.
    Returns the number of transactions extracted.
    """
    filepath = document_row["filepath"]
    doc_type = document_row["doc_type"]

    raw_transactions = parse_file(filepath)

    conn = db.get_conn()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for tx in raw_transactions:
        conn.execute(
            """INSERT INTO transactions
               (tx_id, date, vendor_raw, vendor, amount, description, source_document,
                doc_type, normalized, duplicate_flag, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?)""",
            (
                tx["tx_id"], tx["date"], tx["vendor"], tx["vendor"], tx["amount"],
                tx["description"], tx["source_document"], doc_type, now,
            ),
        )
    conn.execute(
        "UPDATE documents SET status = 'processed', processed_at = ? WHERE id = ?",
        (now, document_row["id"]),
    )
    conn.commit()
    conn.close()

    db.log_audit(
        "Transactions extracted",
        "Document Intelligence Agent",
        f"{len(raw_transactions)} records from {document_row['filename']}",
    )
    return len(raw_transactions)
