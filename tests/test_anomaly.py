"""
test_anomaly.py — Unit tests for z-score anomaly detection.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from core.anomaly import detect_anomalies


class TestDetectAnomalies:
    def test_no_anomalies_on_uniform_data(self):
        expenses = [
            {"amount": 100, "category": "Food & Dining", "date": f"2026-03-{i:02d}",
             "description": "lunch", "merchant": ""}
            for i in range(1, 11)
        ]
        anomalies = detect_anomalies(expenses)
        assert len(anomalies) == 0

    def test_detects_high_outlier(self):
        expenses = [
            {"amount": 100, "category": "Food & Dining", "date": f"2026-03-{i:02d}",
             "description": "lunch", "merchant": ""}
            for i in range(1, 20)
        ]
        # Add a massive outlier
        expenses.append({
            "amount": 5000, "category": "Food & Dining", "date": "2026-03-20",
            "description": "expensive dinner", "merchant": "FancyPlace"
        })
        anomalies = detect_anomalies(expenses)
        assert len(anomalies) >= 1
        assert anomalies[0]["amount"] == 5000

    def test_empty_expenses(self):
        assert detect_anomalies([]) == []

    def test_single_expense_no_anomaly(self):
        expenses = [{"amount": 500, "category": "Shopping", "date": "2026-03-01",
                      "description": "shoes", "merchant": ""}]
        assert detect_anomalies(expenses) == []

    def test_severity_levels(self):
        expenses = [
            {"amount": 100, "category": "Food & Dining", "date": f"2026-03-{i:02d}",
             "description": "", "merchant": ""}
            for i in range(1, 30)
        ]
        expenses.append({
            "amount": 10000, "category": "Food & Dining", "date": "2026-03-30",
            "description": "extreme", "merchant": ""
        })
        anomalies = detect_anomalies(expenses)
        if anomalies:
            assert anomalies[0]["severity"] in ("medium", "high")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
