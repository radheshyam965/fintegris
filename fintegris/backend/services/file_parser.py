"""
Fintegris - File parsing service.

Turns uploaded PDF / CSV / Excel files into a normalized list of
raw transaction dicts: {tx_id, date, vendor, amount, description}

This is the concrete implementation behind the "Document Intelligence
Agent". It is deliberately tolerant of messy/real-world headers.
"""

import os
import re
import pandas as pd

COLUMN_ALIASES = {
    "tx_id": ["tx_id", "transaction id", "transaction_id", "id", "txn id", "txn_id"],
    "date": ["date", "transaction date", "txn date", "value date"],
    "vendor": ["vendor", "payee", "merchant", "party", "description1", "narration"],
    "amount": ["amount", "amt", "value", "debit", "credit", "total"],
    "description": ["description", "details", "narration", "remarks", "memo"],
}


def _match_column(columns, aliases):
    lower_map = {c.lower().strip(): c for c in columns}
    for alias in aliases:
        if alias in lower_map:
            return lower_map[alias]
    return None


def _clean_amount(val):
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val)
    s = re.sub(r"[^\d.\-]", "", s)  # strip currency symbols, commas, ₹ etc.
    try:
        return float(s) if s not in ("", "-", ".") else 0.0
    except ValueError:
        return 0.0


def _dataframe_to_transactions(df: pd.DataFrame, source_document: str):
    columns = list(df.columns)
    col_tx = _match_column(columns, COLUMN_ALIASES["tx_id"])
    col_date = _match_column(columns, COLUMN_ALIASES["date"])
    col_vendor = _match_column(columns, COLUMN_ALIASES["vendor"])
    col_amount = _match_column(columns, COLUMN_ALIASES["amount"])
    col_desc = _match_column(columns, COLUMN_ALIASES["description"])

    records = []
    for i, row in df.iterrows():
        tx_id = str(row[col_tx]).strip() if col_tx else f"TX{i+1:03d}"
        if not tx_id or tx_id.lower() == "nan":
            tx_id = f"TX{i+1:03d}"
        date = str(row[col_date]).strip() if col_date and pd.notna(row[col_date]) else ""
        vendor = str(row[col_vendor]).strip() if col_vendor and pd.notna(row[col_vendor]) else "Unknown Vendor"
        amount = _clean_amount(row[col_amount]) if col_amount else 0.0
        description = str(row[col_desc]).strip() if col_desc and pd.notna(row[col_desc]) else ""
        records.append({
            "tx_id": tx_id,
            "date": date,
            "vendor": vendor,
            "amount": amount,
            "description": description,
            "source_document": source_document,
        })
    return records


def parse_csv(filepath: str):
    df = pd.read_csv(filepath)
    return _dataframe_to_transactions(df, os.path.basename(filepath))


def parse_excel(filepath: str):
    df = pd.read_excel(filepath)
    return _dataframe_to_transactions(df, os.path.basename(filepath))


def parse_pdf(filepath: str):
    """
    Best-effort PDF table/text extraction. Falls back to regex line
    scanning if no clean table is detected (real-world bank/vendor PDFs
    vary a lot -- this keeps the demo from crashing on odd PDFs).
    """
    records = []
    try:
        import pdfplumber
        with pdfplumber.open(filepath) as pdf:
            row_i = 0
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    header = [h.lower().strip() if h else "" for h in table[0]]
                    for r in table[1:]:
                        row_i += 1
                        row_dict = dict(zip(header, r))
                        records.append({
                            "tx_id": row_dict.get("tx_id") or row_dict.get("transaction id") or f"TX{row_i:03d}",
                            "date": row_dict.get("date", ""),
                            "vendor": row_dict.get("vendor") or row_dict.get("payee") or "Unknown Vendor",
                            "amount": _clean_amount(row_dict.get("amount")),
                            "description": row_dict.get("description", ""),
                            "source_document": os.path.basename(filepath),
                        })
                else:
                    text = page.extract_text() or ""
                    for line in text.splitlines():
                        m = re.match(r"(\S+)\s+([\d/\-]+)\s+(.+?)\s+[₹$]?([\d,]+\.?\d*)", line)
                        if m:
                            row_i += 1
                            records.append({
                                "tx_id": m.group(1),
                                "date": m.group(2),
                                "vendor": m.group(3).strip(),
                                "amount": _clean_amount(m.group(4)),
                                "description": "",
                                "source_document": os.path.basename(filepath),
                            })
    except Exception:
        # If pdfplumber isn't available or parsing fails, return no rows
        # rather than crashing the whole pipeline.
        return []
    return records


def parse_file(filepath: str):
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".csv":
        return parse_csv(filepath)
    elif ext in (".xlsx", ".xls"):
        return parse_excel(filepath)
    elif ext == ".pdf":
        return parse_pdf(filepath)
    else:
        raise ValueError(f"Unsupported file type: {ext}")
