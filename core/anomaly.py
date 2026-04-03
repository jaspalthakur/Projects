"""
anomaly.py — Anomalous Spend Detector using per-category z-scores.
Flags transactions whose amount is > 2 standard deviations above the category mean.
"""

from __future__ import annotations
import polars as pl


def detect_anomalies(expenses: list[dict], z_threshold: float = 2.0) -> list[dict]:
    """
    Analyse expenses and return anomalous ones.

    Each returned dict includes the original expense fields plus:
        - `category_mean`: average spend for that category
        - `category_std`:  std dev for that category
        - `z_score`:       how many std devs above the mean
        - `severity`:      'high' (>3σ) or 'medium' (>2σ)
    """
    if not expenses:
        return []

    df = pl.DataFrame(expenses).with_columns(pl.col("amount").cast(pl.Float64))

    # Filter out Income
    df = df.filter(pl.col("category") != "Income")
    if df.height < 3:
        return []  # not enough data

    # Per-category stats
    stats = (
        df.group_by("category")
        .agg(
            pl.col("amount").mean().alias("category_mean"),
            pl.col("amount").std().alias("category_std"),
            pl.col("amount").count().alias("cat_count"),
        )
        .filter(pl.col("cat_count") >= 3)  # need at least 3 to be meaningful
    )

    # Join stats back
    joined = df.join(stats, on="category", how="inner")

    # Compute z-score (guard against std == 0)
    joined = joined.with_columns(
        pl.when(pl.col("category_std") > 0)
        .then((pl.col("amount") - pl.col("category_mean")) / pl.col("category_std"))
        .otherwise(0.0)
        .alias("z_score")
    )

    # Filter anomalies
    anomalies = joined.filter(pl.col("z_score") > z_threshold).sort("z_score", descending=True)

    results = []
    for row in anomalies.iter_rows(named=True):
        row["severity"] = "high" if row["z_score"] > 3.0 else "medium"
        results.append(row)

    return results
