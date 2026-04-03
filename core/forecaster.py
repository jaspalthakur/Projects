"""
forecaster.py — 30-day cash-flow forecast using exponential smoothing.
Falls back to simple moving average if data is insufficient.
"""

from __future__ import annotations
import numpy as np
from datetime import datetime, timedelta


def forecast_spending(daily_data: list[dict], horizon: int = 30) -> list[dict]:
    """
    Predict next `horizon` days of spending.

    Parameters
    ----------
    daily_data : list[dict]
        Each dict has 'date' (str YYYY-MM-DD) and 'amount' (float).
    horizon : int
        Number of days to forecast.

    Returns
    -------
    list[dict]
        [{date, amount, is_forecast}] covering historical + forecasted days.
    """
    if not daily_data:
        return []

    # ── Build a gap-filled daily series ───────────────────────────
    date_amounts: dict[str, float] = {d["date"]: d["amount"] for d in daily_data}
    dates_sorted = sorted(date_amounts.keys())
    start = datetime.strptime(dates_sorted[0], "%Y-%m-%d").date()
    end = datetime.strptime(dates_sorted[-1], "%Y-%m-%d").date()

    full_dates = []
    full_values = []
    current = start
    while current <= end:
        ds = current.isoformat()
        full_dates.append(ds)
        full_values.append(date_amounts.get(ds, 0.0))
        current += timedelta(days=1)

    values = np.array(full_values, dtype=np.float64)

    # ── Forecast ──────────────────────────────────────────────────
    if len(values) >= 14:
        # Exponential smoothing (Holt's method)
        forecasted = _holt_forecast(values, horizon)
    else:
        # Fallback: 7-day moving average
        window = min(7, len(values))
        avg = float(np.mean(values[-window:]))
        forecasted = [max(0, avg)] * horizon

    # ── Combine historical + forecast ─────────────────────────────
    result = [{"date": d, "amount": v, "is_forecast": False}
              for d, v in zip(full_dates, full_values)]

    last_date = end
    for i, val in enumerate(forecasted):
        next_date = last_date + timedelta(days=i + 1)
        result.append({
            "date": next_date.isoformat(),
            "amount": max(0, round(val, 2)),
            "is_forecast": True,
        })

    return result


def _holt_forecast(values: np.ndarray, horizon: int,
                   alpha: float = 0.3, beta: float = 0.1) -> list[float]:
    """Holt's linear trend method (double exponential smoothing)."""
    n = len(values)
    level = values[0]
    trend = np.mean(np.diff(values[:min(7, n)]))

    levels = [level]
    trends = [trend]

    for t in range(1, n):
        new_level = alpha * values[t] + (1 - alpha) * (levels[-1] + trends[-1])
        new_trend = beta * (new_level - levels[-1]) + (1 - beta) * trends[-1]
        levels.append(new_level)
        trends.append(new_trend)

    forecast = []
    for h in range(1, horizon + 1):
        forecast.append(levels[-1] + h * trends[-1])

    return forecast


def financial_runway(total_income: float, total_spent: float,
                     asset_value: float, daily_velocity: float) -> dict:
    """
    Calculate the Financial Runway — how many days until balance hits zero.

    Returns:
        {
            "balance": float,       # current net balance (income - spent + assets)
            "daily_burn": float,    # avg daily spending
            "runway_days": int,     # days until zero (-1 if infinite/positive trend)
            "runway_label": str,    # human-readable label
        }
    """
    balance = total_income - total_spent + asset_value

    if daily_velocity <= 0:
        return {
            "balance": balance,
            "daily_burn": 0.0,
            "runway_days": -1,
            "runway_label": "∞  (no spending detected)",
        }

    if balance <= 0:
        return {
            "balance": balance,
            "daily_burn": daily_velocity,
            "runway_days": 0,
            "runway_label": "⚠️  Balance depleted",
        }

    days = int(balance / daily_velocity)

    if days > 365:
        label = f"🟢  {days} days (~{days // 30} months)"
    elif days > 90:
        label = f"🟡  {days} days (~{days // 30} months)"
    elif days > 30:
        label = f"🟠  {days} days"
    else:
        label = f"🔴  {days} days — critically low!"

    return {
        "balance": balance,
        "daily_burn": daily_velocity,
        "runway_days": days,
        "runway_label": label,
    }
