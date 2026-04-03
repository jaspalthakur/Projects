"""
categorizer.py — Dictionary-based smart auto-categorizer for bank transactions.
Uses fuzzy substring matching against the merchant keyword map.
"""

from core.constants import MERCHANT_CATEGORY_MAP, CATEGORIES


def auto_categorize(description: str) -> str:
    """
    Attempt to categorize a transaction description.
    Returns the best-match category, or 'Other' if no match found.
    """
    if not description:
        return "Other"

    text = description.lower().strip()

    # Exact keyword match first (fastest path)
    for keyword, category in MERCHANT_CATEGORY_MAP.items():
        if keyword in text:
            return category

    return "Other"


def categorize_batch(descriptions: list[str]) -> list[str]:
    """Categorize a batch of descriptions. Returns list of category strings."""
    return [auto_categorize(d) for d in descriptions]


def get_category_or_default(category: str) -> str:
    """Validate a category string — return it if valid, else 'Other'."""
    return category if category in CATEGORIES else "Other"
