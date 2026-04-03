"""
pdf_parser.py — Bank statement PDF parser using pdfplumber.
Extracts tabular transaction data from common bank PDF formats.
"""

from __future__ import annotations
import re
from datetime import datetime
import pdfplumber


def parse_bank_pdf(filepath: str) -> list[dict]:
    """
    Extract transactions from a bank statement PDF.

    Returns list of dicts with keys: date, description, amount.
    Uses heuristic column detection for common bank formats.
    """
    transactions: list[dict] = []

    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            # Try table extraction first (most reliable)
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    transactions.extend(_parse_table(table))
            else:
                # Fallback: line-by-line text parsing
                text = page.extract_text() or ""
                transactions.extend(_parse_text_lines(text))

    return transactions


def _parse_table(table: list[list]) -> list[dict]:
    """Parse a pdfplumber-extracted table into transaction dicts."""
    if not table or len(table) < 2:
        return []

    results = []
    # Try to identify header row
    header = [str(c).lower().strip() if c else "" for c in table[0]]

    date_col = _find_col(header, ["date", "transaction date", "txn date", "posting date", "value date"])
    desc_col = _find_col(header, ["description", "narration", "details", "particulars", "merchant", "memo"])
    amount_col = _find_col(header, ["amount", "debit", "withdrawal", "transaction amount", "value"])
    credit_col = _find_col(header, ["credit", "deposit"])

    # If we can't find headers, try positional (Date, Desc, Amount pattern)
    if date_col is None:
        if len(header) >= 3:
            date_col, desc_col, amount_col = 0, 1, 2
        else:
            return []

    for row in table[1:]:
        if not row or len(row) <= max(c for c in [date_col, desc_col or 0, amount_col or 0] if c is not None):
            continue

        date_val = _clean_str(row[date_col]) if date_col is not None else ""
        desc_val = _clean_str(row[desc_col]) if desc_col is not None else ""

        amount = 0.0
        if amount_col is not None:
            amount = _parse_amount(row[amount_col])
        if credit_col is not None and amount == 0:
            amount = _parse_amount(row[credit_col])

        if not date_val or amount == 0:
            continue

        # Normalize date
        parsed_date = _normalize_date(date_val)
        if not parsed_date:
            continue

        results.append({
            "date": parsed_date,
            "description": desc_val,
            "amount": abs(amount),
        })

    return results


def _parse_text_lines(text: str) -> list[dict]:
    """
    Fallback parser: scan lines for date + amount patterns.
    Works for simpler statement formats.
    """
    results = []
    # Pattern: date  description  amount
    date_pattern = re.compile(
        r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})"
    )
    amount_pattern = re.compile(
        r"[\$₹€£]?\s*([\d,]+\.?\d*)"
    )

    for line in text.split("\n"):
        line = line.strip()
        if not line or len(line) < 10:
            continue

        date_match = date_pattern.search(line)
        if not date_match:
            continue

        # Find amounts (take the last number in the line as amount)
        amounts = amount_pattern.findall(line)
        if not amounts:
            continue

        date_str = _normalize_date(date_match.group(1))
        if not date_str:
            continue

        amount = _parse_amount(amounts[-1])
        if amount <= 0:
            continue

        # Description is everything between date and amount
        desc = line[date_match.end():].strip()
        desc = amount_pattern.sub("", desc).strip()
        desc = re.sub(r"\s+", " ", desc).strip(" -|")

        results.append({
            "date": date_str,
            "description": desc[:100],
            "amount": abs(amount),
        })

    return results


# ── Helpers ───────────────────────────────────────────────────────

def _find_col(header: list[str], candidates: list[str]) -> int | None:
    for i, h in enumerate(header):
        for c in candidates:
            if c in h:
                return i
    return None


def _clean_str(val) -> str:
    if val is None:
        return ""
    return str(val).strip()


def _parse_amount(val) -> float:
    if val is None:
        return 0.0
    s = str(val).strip()
    s = re.sub(r"[^\d.\-]", "", s)
    try:
        return abs(float(s))
    except ValueError:
        return 0.0


def _normalize_date(date_str: str) -> str | None:
    """Try multiple date formats and return YYYY-MM-DD or None."""
    formats = [
        "%Y-%m-%d", "%d-%m-%Y", "%m-%d-%Y",
        "%Y/%m/%d", "%d/%m/%Y", "%m/%d/%Y",
        "%d-%m-%y", "%m-%d-%y",
        "%d/%m/%y", "%m/%d/%y",
    ]
    date_str = date_str.strip()
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            # Sanity check: year should be reasonable
            if 2000 <= dt.year <= 2030:
                return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None
