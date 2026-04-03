"""
data_engine.py — Polars-based analytics engine for lightning-fast data processing.
Converts raw SQLite rows into Polars DataFrames and provides aggregation helpers.
"""

from __future__ import annotations
import polars as pl
from datetime import datetime, timedelta


class DataEngine:
    """Processes expense data via Polars for dashboards and analytics."""

    def __init__(self, expenses: list[dict]):
        if expenses:
            self.df = pl.DataFrame(expenses).with_columns(
                pl.col("date").str.to_date("%Y-%m-%d").alias("date_parsed"),
                pl.col("amount").cast(pl.Float64),
            )
        else:
            self.df = pl.DataFrame(
                schema={
                    "id": pl.Int64, "user_id": pl.Int64, "date": pl.Utf8,
                    "amount": pl.Float64, "category": pl.Utf8,
                    "description": pl.Utf8, "merchant": pl.Utf8,
                    "is_recurring": pl.Int64, "created_at": pl.Utf8,
                }
            ).with_columns(
                pl.lit(None).cast(pl.Date).alias("date_parsed"),
            )

    @property
    def is_empty(self) -> bool:
        return self.df.height == 0

    # ── Category Breakdown ────────────────────────────────────────
    def category_breakdown(self) -> dict[str, float]:
        """Returns {category: total_amount} excluding Income."""
        if self.is_empty:
            return {}
        result = (
            self.df
            .filter(pl.col("category") != "Income")
            .group_by("category")
            .agg(pl.col("amount").sum().alias("total"))
            .sort("total", descending=True)
        )
        return dict(zip(result["category"].to_list(), result["total"].to_list()))

    # ── Monthly Totals ────────────────────────────────────────────
    def monthly_totals(self, months: int = 6) -> dict[str, dict[str, float]]:
        """Returns {month: {spending, income}} for the last N months."""
        if self.is_empty:
            return {}
        now = datetime.now()
        cutoff = (now - timedelta(days=months * 31)).strftime("%Y-%m")

        df = self.df.with_columns(
            pl.col("date_parsed").dt.strftime("%Y-%m").alias("month")
        ).filter(pl.col("month") >= cutoff)

        spending = (
            df.filter(pl.col("category") != "Income")
            .group_by("month").agg(pl.col("amount").sum().alias("spending"))
        )
        income = (
            df.filter(pl.col("category") == "Income")
            .group_by("month").agg(pl.col("amount").sum().alias("income"))
        )
        merged = spending.join(income, on="month", how="full", coalesce=True).sort("month")

        result = {}
        for row in merged.iter_rows(named=True):
            result[row["month"]] = {
                "spending": row.get("spending") or 0.0,
                "income": row.get("income") or 0.0,
            }
        return result

    # ── Daily Spending Series ─────────────────────────────────────
    def daily_spending(self, days: int = 90) -> list[dict]:
        """Returns [{date, amount}] of daily spending totals."""
        if self.is_empty:
            return []
        cutoff = (datetime.now() - timedelta(days=days)).date()
        result = (
            self.df
            .filter((pl.col("category") != "Income") & (pl.col("date_parsed") >= cutoff))
            .group_by("date_parsed")
            .agg(pl.col("amount").sum().alias("amount"))
            .sort("date_parsed")
        )
        return [
            {"date": row["date_parsed"].isoformat(), "amount": row["amount"]}
            for row in result.iter_rows(named=True)
        ]

    # ── Spending Velocity ─────────────────────────────────────────
    def spending_velocity(self) -> float:
        """Average daily spend over the last 30 days."""
        if self.is_empty:
            return 0.0
        cutoff = (datetime.now() - timedelta(days=30)).date()
        total = (
            self.df
            .filter((pl.col("category") != "Income") & (pl.col("date_parsed") >= cutoff))
            .select(pl.col("amount").sum())
            .item()
        )
        return (total or 0.0) / 30.0

    # ── Recurring Transaction Detection ───────────────────────────
    def recurring_candidates(self) -> list[dict]:
        """Finds transactions from the same merchant appearing 3+ times."""
        if self.is_empty:
            return []
        result = (
            self.df
            .filter(pl.col("merchant") != "")
            .group_by("merchant", "category")
            .agg(
                pl.col("amount").mean().alias("avg_amount"),
                pl.col("amount").count().alias("count"),
                pl.col("date_parsed").max().alias("last_seen"),
            )
            .filter(pl.col("count") >= 3)
            .sort("count", descending=True)
        )
        return result.to_dicts()

    # ── Total Spending / Income ───────────────────────────────────
    def total_spending(self) -> float:
        if self.is_empty:
            return 0.0
        return self.df.filter(pl.col("category") != "Income")["amount"].sum() or 0.0

    def total_income(self) -> float:
        if self.is_empty:
            return 0.0
        return self.df.filter(pl.col("category") == "Income")["amount"].sum() or 0.0
