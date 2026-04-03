"""
test_categorizer.py — Unit tests for auto-categorizer accuracy.
Target: 90%+ on known merchant names.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from core.categorizer import auto_categorize, get_category_or_default


class TestAutoCategorize:
    # 90%+ accuracy test set
    KNOWN_MAPPINGS = [
        ("STARBUCKS COFFEE", "Food & Dining"),
        ("McDonald's #12345", "Food & Dining"),
        ("UBER TRIP", "Transportation"),
        ("LYFT RIDE", "Transportation"),
        ("NETFLIX.COM", "Subscriptions"),
        ("Spotify Premium", "Subscriptions"),
        ("Amazon Purchase", "Shopping"),
        ("FLIPKART ORDER", "Shopping"),
        ("Walmart Supercenter", "Groceries"),
        ("COSTCO WHOLESALE", "Groceries"),
        ("Shell Gas Station", "Transportation"),
        ("AIRTEL RECHARGE", "Bills & Utilities"),
        ("Apollo Pharmacy", "Health & Medical"),
        ("Udemy Course", "Education"),
        ("Airbnb Booking", "Travel"),
        ("rent payment", "Rent & Housing"),
        ("LIC Premium", "Insurance"),
        ("salary credited", "Income"),
        ("ZOMATO ORDER", "Food & Dining"),
        ("SWIGGY DELIVERY", "Food & Dining"),
    ]

    def test_known_merchants_accuracy(self):
        correct = 0
        for description, expected in self.KNOWN_MAPPINGS:
            result = auto_categorize(description)
            if result == expected:
                correct += 1

        accuracy = correct / len(self.KNOWN_MAPPINGS) * 100
        assert accuracy >= 90, f"Accuracy {accuracy:.1f}% is below 90% target"

    def test_unknown_returns_other(self):
        assert auto_categorize("xyzrandomstring12345") == "Other"

    def test_case_insensitive(self):
        assert auto_categorize("STARBUCKS") == auto_categorize("starbucks")

    def test_empty_string(self):
        assert auto_categorize("") == "Other"


class TestValidateCategory:
    def test_valid_category(self):
        assert get_category_or_default("Food & Dining") == "Food & Dining"

    def test_invalid_category(self):
        assert get_category_or_default("NotACategory") == "Other"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
