"""
test_database.py — Integration tests for SQLite CRUD operations.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from core.database import Database
from core.security import hash_password


@pytest.fixture
def db(tmp_path):
    """Create a temporary database for testing."""
    import core.constants as c
    old = c.DB_NAME
    c.DB_NAME = str(tmp_path / "test.db")
    d = Database()
    yield d
    d.close()
    c.DB_NAME = old


@pytest.fixture
def user(db):
    """Create a test user."""
    pw = hash_password("testpass123")
    db.add_user("testuser", pw, "TESTSECRET")
    return db.get_user_by_username("testuser")


class TestUserCRUD:
    def test_add_and_get_user(self, db):
        pw = hash_password("pass123")
        assert db.add_user("alice", pw, "SECRET")
        u = db.get_user_by_username("alice")
        assert u is not None
        assert u["username"] == "alice"

    def test_duplicate_username(self, db):
        pw = hash_password("pass")
        db.add_user("bob", pw, "S")
        assert db.add_user("bob", pw, "S") is False

    def test_nonexistent_user(self, db):
        assert db.get_user_by_username("ghost") is None


class TestExpenseCRUD:
    def test_add_and_get(self, db, user):
        eid = db.add_expense(user["id"], "2026-03-22", 500, "Food & Dining", "lunch")
        assert eid is not None
        exps = db.get_expenses(user["id"])
        assert len(exps) == 1
        assert exps[0]["amount"] == 500

    def test_delete(self, db, user):
        eid = db.add_expense(user["id"], "2026-03-22", 200, "Shopping")
        assert db.delete_expense(eid, user["id"])
        assert len(db.get_expenses(user["id"])) == 0

    def test_search_by_keyword(self, db, user):
        db.add_expense(user["id"], "2026-03-22", 100, "Food & Dining", "pizza")
        db.add_expense(user["id"], "2026-03-22", 200, "Shopping", "shoes")
        results = db.search_expenses(user["id"], keyword="pizza")
        assert len(results) == 1

    def test_search_by_category(self, db, user):
        db.add_expense(user["id"], "2026-03-22", 100, "Food & Dining")
        db.add_expense(user["id"], "2026-03-22", 200, "Shopping")
        results = db.search_expenses(user["id"], category="Shopping")
        assert len(results) == 1

    def test_bulk_add(self, db, user):
        rows = [
            (user["id"], f"2026-03-{i:02d}", 100 * i, "Food & Dining", "", "", 0)
            for i in range(1, 6)
        ]
        count = db.bulk_add_expenses(rows)
        assert count == 5


class TestAssetCRUD:
    def test_add_and_get_asset(self, db, user):
        aid = db.add_asset(user["id"], "Bitcoin", "Crypto", 0.5, 50000, 120000)
        assert aid is not None
        assets = db.get_assets(user["id"])
        assert len(assets) == 1
        assert assets[0]["name"] == "Bitcoin"

    def test_total_asset_value(self, db, user):
        db.add_asset(user["id"], "BTC", "Crypto", 1.0, 100000, 120000)
        db.add_asset(user["id"], "ETH", "Crypto", 10, 50000, 7000)
        total = db.get_total_asset_value(user["id"])
        assert total == 120000 + 70000

    def test_delete_asset(self, db, user):
        aid = db.add_asset(user["id"], "Gold", "Gold", 10, 50000, 6000)
        db.delete_asset(aid, user["id"])
        assert len(db.get_assets(user["id"])) == 0


class TestBudget:
    def test_set_and_get(self, db, user):
        db.set_budget(user["id"], 15000)
        assert db.get_budget(user["id"]) == 15000

    def test_update_budget(self, db, user):
        db.set_budget(user["id"], 10000)
        db.set_budget(user["id"], 20000)
        assert db.get_budget(user["id"]) == 20000


class TestEnvelopes:
    def test_set_and_get_envelopes(self, db, user):
        db.set_envelope(user["id"], "Food & Dining", 5000)
        db.set_envelope(user["id"], "Shopping", 3000)
        envs = db.get_envelopes(user["id"])
        assert len(envs) == 2

    def test_update_envelope(self, db, user):
        db.set_envelope(user["id"], "Food & Dining", 5000)
        db.set_envelope(user["id"], "Food & Dining", 7000)
        envs = db.get_envelopes(user["id"])
        assert envs[0]["monthly_limit"] == 7000

    def test_delete_envelope(self, db, user):
        db.set_envelope(user["id"], "Shopping", 3000)
        db.delete_envelope(user["id"], "Shopping")
        assert len(db.get_envelopes(user["id"])) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
