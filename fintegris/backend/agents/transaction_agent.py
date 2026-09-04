"""
Fintegris - Transaction Intelligence Agent.

Normalizes vendor names / dates, and flags likely duplicate
transactions. Step 2 of the pipeline.
"""

import re
from datetime import datetime
import db

# Known vendor aliases -> canonical name. In production this would be
# learned/looked up against a vendor master; for the MVP it's a
# deterministic table, which keeps the demo 100% reproducible.
VENDOR_ALIASES = {
    "amazon web services": "AWS",
    "aws": "AWS",
    "amazon aws": "AWS",
    "abc supplies pvt ltd": "ABC Supplies",
    "abc supplies": "ABC Supplies",
    "xyz services": "XYZ Services",
    "xyz consulting services": "XYZ Services",
}

DATE_FORMATS = ["%d %b", "%d %B", "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%m/%d/%Y", "%d %b %Y"]


def normalize_vendor(raw_name: str) -> str:
    if not raw_name:
        return "Unknown Vendor"
    cleaned = re.sub(r"\b(pvt\.?|ltd\.?|inc\.?|llc|corp\.?)\b", "", raw_name, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    key = cleaned.lower()
    if key in VENDOR_ALIASES:
        return VENDOR_ALIASES[key]
    return cleaned.title() if cleaned else "Unknown Vendor"


def normalize_date(raw_date: str) -> str:
    if not raw_date or raw_date.lower() == "nan":
        return ""
    raw_date = raw_date.strip()
    for fmt in DATE_FORMATS:
        try:
            dt = datetime.strptime(raw_date, fmt)
            if dt.year == 1900:
                dt = dt.replace(year=datetime.now().year)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return raw_date  # leave as-is if unrecognized rather than losing data


def run_normalization():
    """Normalizes every un-normalized transaction and flags duplicates."""
    conn = db.get_conn()
    rows = conn.execute("SELECT * FROM transactions WHERE normalized = 0").fetchall()

    seen = {}
    for row in rows:
        vendor = normalize_vendor(row["vendor_raw"])
        date = normalize_date(row["date"])
        # Scope the duplicate check to the same doc_type + source document set.
        # The SAME transaction legitimately appears in both the bank statement
        # and company books - that's not a duplicate, that's reconciliation.
        # A real duplicate is the same vendor/date/amount appearing twice
        # WITHIN one dataset (e.g. the same CSV had a row entered twice).
        key = (row["doc_type"], vendor, date, round(row["amount"], 2))
        is_duplicate = key in seen
        seen[key] = True

        conn.execute(
            "UPDATE transactions SET vendor = ?, date = ?, normalized = 1, duplicate_flag = ? WHERE id = ?",
            (vendor, date, 1 if is_duplicate else 0, row["id"]),
        )
    conn.commit()
    conn.close()

    db.log_audit("Vendor names normalized", "Transaction Intelligence Agent", f"{len(rows)} records")
    return len(rows)
