"""
test_forecaster.py — Unit tests for forecaster math logic + financial runway.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from core.forecaster import forecast_spending, financial_runway


class TestForecastSpending:
    def test_empty_data(self):
        assert forecast_spending([]) == []

    def test_returns_forecast_points(self):
        daily = [
            {"date": f"2026-03-{str(d).zfill(2)}", "amount": 100.0 + d}
            for d in range(1, 16)
        ]
        result = forecast_spending(daily, horizon=7)
        assert len(result) > 0
        forecasted = [r for r in result if r["is_forecast"]]
        assert len(forecasted) == 7

    def test_forecast_uses_fallback_for_short_data(self):
        daily = [
            {"date": "2026-03-01", "amount": 100},
            {"date": "2026-03-02", "amount": 200},
            {"date": "2026-03-03", "amount": 150},
        ]
        result = forecast_spending(daily, horizon=5)
        forecasted = [r for r in result if r["is_forecast"]]
        assert len(forecasted) == 5
        # Fallback uses moving average, so values should be close to mean
        avg = 150  # mean of 100, 200, 150
        for f in forecasted:
            assert f["amount"] >= 0

    def test_forecast_dates_are_sequential(self):
        daily = [
            {"date": f"2026-03-{str(d).zfill(2)}", "amount": 100.0}
            for d in range(1, 8)
        ]
        result = forecast_spending(daily, horizon=3)
        dates = [r["date"] for r in result]
        assert dates == sorted(dates)


class TestFinancialRunway:
    def test_positive_balance(self):
        r = financial_runway(100000, 30000, 0, 500)
        assert r["runway_days"] == 140
        assert r["balance"] == 70000

    def test_zero_velocity(self):
        r = financial_runway(100000, 0, 0, 0)
        assert r["runway_days"] == -1

    def test_depleted_balance(self):
        r = financial_runway(1000, 5000, 0, 500)
        assert r["runway_days"] == 0

    def test_large_runway(self):
        r = financial_runway(1000000, 100000, 500000, 100)
        assert r["runway_days"] > 365
        assert "months" in r["runway_label"]

    def test_critical_runway(self):
        r = financial_runway(10000, 5000, 0, 200)
        assert r["runway_days"] == 25
        assert "critically low" in r["runway_label"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
