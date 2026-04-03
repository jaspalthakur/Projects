"""
dynamic_budget.py — Income-adaptive envelope budgeting engine.

Each category gets a monthly spending limit ("envelope").
If actual income > expected income, envelopes scale UP proportionally.
If actual income < expected income, envelopes scale DOWN to protect savings.
"""

from __future__ import annotations
from core.constants import CATEGORIES


class EnvelopeBudget:
    """Calculates dynamic per-category budget limits based on income fluctuations."""

    def __init__(self, db, user_id: int):
        self.db = db
        self.user_id = user_id

    def get_envelopes(self) -> list[dict]:
        """
        Return envelope status for each configured category.

        Each dict: {
            category, limit, adjusted_limit, spent, remaining, pct, status
        }
        """
        raw_envelopes = self.db.get_envelopes(self.user_id)
        if not raw_envelopes:
            return []

        # Income adjustment factor
        adjustment = self._income_adjustment_factor()

        monthly_spent = self.db.get_monthly_spent(self.user_id)
        # Per-category spending this month
        cat_spent = self._category_spending_this_month()

        results = []
        for env in raw_envelopes:
            cat = env["category"]
            base_limit = env["monthly_limit"]
            adjusted = round(base_limit * adjustment, 2)
            spent = cat_spent.get(cat, 0.0)
            remaining = max(0, adjusted - spent)
            pct = (spent / adjusted * 100) if adjusted > 0 else 0

            status = "ok"
            if pct >= 100:
                status = "over"
            elif pct >= 80:
                status = "warning"

            results.append({
                "category": cat,
                "limit": base_limit,
                "adjusted_limit": adjusted,
                "spent": spent,
                "remaining": remaining,
                "pct": round(pct, 1),
                "status": status,
            })

        return results

    def _income_adjustment_factor(self) -> float:
        """
        Compare this month's income vs 3-month average income.
        Returns a multiplier: >1 if income is above average, <1 if below.
        Clamped to [0.7, 1.5] to prevent extreme swings.
        """
        import sqlite3
        from datetime import datetime, timedelta

        now = datetime.now()
        current_month = now.strftime("%Y-%m")

        # Current month income
        row = self.db.conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM expenses "
            "WHERE user_id = ? AND category = 'Income' AND strftime('%%Y-%%m', date) = ?",
            (self.user_id, current_month),
        ).fetchone()
        current_income = row["total"]

        # 3-month average income (excluding current month)
        three_months_ago = (now - timedelta(days=90)).strftime("%Y-%m")
        row = self.db.conn.execute(
            "SELECT COALESCE(SUM(amount), 0) / 3.0 AS avg_income FROM expenses "
            "WHERE user_id = ? AND category = 'Income' "
            "AND strftime('%%Y-%%m', date) >= ? AND strftime('%%Y-%%m', date) < ?",
            (self.user_id, three_months_ago, current_month),
        ).fetchone()
        avg_income = row["avg_income"]

        if avg_income <= 0:
            return 1.0  # no history — no adjustment

        factor = current_income / avg_income
        return max(0.7, min(1.5, factor))  # clamp

    def _category_spending_this_month(self) -> dict[str, float]:
        """Returns {category: total_spent} for current month, excluding Income."""
        from datetime import datetime

        month = datetime.now().strftime("%Y-%m")
        rows = self.db.conn.execute(
            "SELECT category, SUM(amount) AS total FROM expenses "
            "WHERE user_id = ? AND category != 'Income' "
            "AND strftime('%%Y-%%m', date) = ? "
            "GROUP BY category",
            (self.user_id, month),
        ).fetchall()
        return {r["category"]: r["total"] for r in rows}
