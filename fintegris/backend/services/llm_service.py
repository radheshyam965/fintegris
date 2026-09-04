"""
Fintegris - LLM service (optional).

If ANTHROPIC_API_KEY is set in the environment, this module can call
the Anthropic API to generate a nicer natural-language explanation.

If no key is present (or the call fails for any reason - offline demo,
no wifi at the venue, rate limit, etc.) every function falls back to a
deterministic, rule-based explanation so the DEMO NEVER BREAKS.

This is intentional: judges see "explainability" either way, and the
mock layer is what should be relied on for a live 7-minute demo.
"""

import os
import requests

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"


def _call_llm(prompt: str, max_tokens: int = 200):
    if not ANTHROPIC_API_KEY:
        return None
    try:
        resp = requests.post(
            ANTHROPIC_URL,
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-6",
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=6,
        )
        if resp.status_code == 200:
            data = resp.json()
            parts = [b["text"] for b in data.get("content", []) if b.get("type") == "text"]
            text = " ".join(parts).strip()
            return text or None
        return None
    except Exception:
        return None


def explain_reconciliation(tx_id, vendor, bank_amount, books_amount, difference):
    fallback = (
        f"Bank statement amount = ₹{bank_amount:,.0f}. "
        f"Company book amount = ₹{books_amount:,.0f}. "
        f"Difference = ₹{abs(difference):,.0f}. "
        f"Therefore the transaction was routed to human review."
    )
    prompt = (
        f"In under 40 words, explain plainly why transaction {tx_id} for vendor {vendor} "
        f"was flagged: bank amount ₹{bank_amount}, books amount ₹{books_amount}, "
        f"difference ₹{difference}. State only facts, no speculation."
    )
    return _call_llm(prompt) or fallback


def explain_gl_mapping(vendor, gl_category, description=""):
    fallback = (
        f"Mapped to {gl_category} because the vendor is {vendor}"
        + (f" and the transaction description indicates: {description}." if description else ".")
    )
    prompt = (
        f"In under 30 words, explain why vendor '{vendor}' (description: '{description}') "
        f"was classified under GL category '{gl_category}'."
    )
    return _call_llm(prompt) or fallback


def recommend_review_action(tx_id, vendor, difference):
    fallback = "Review supporting invoice and ledger entry before approval."
    prompt = (
        f"In under 20 words, recommend one concrete next step for a finance reviewer "
        f"looking at a ₹{abs(difference):,.0f} mismatch on transaction {tx_id} ({vendor})."
    )
    return _call_llm(prompt) or fallback
