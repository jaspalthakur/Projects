"""
utils_helpers.py — Shared formatting and validation utilities.
"""

from datetime import datetime

from core.constants import CATEGORIES


def validate_amount(value: str) -> tuple[bool, str]:
    try:
        num = float(value)
        if num <= 0:
            return False, "Amount must be greater than zero."
        return True, ""
    except ValueError:
        return False, "Amount must be a valid number."


def validate_date(value: str) -> tuple[bool, str]:
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True, ""
    except ValueError:
        return False, "Date must be in YYYY-MM-DD format."


def format_currency(value: float) -> str:
    return f"₹{value:,.2f}"


def today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")
