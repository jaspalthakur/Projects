"""
database.py — SQLite database handler for Wallet Hub v3.
Schema: users (TOTP), expenses (merchant/recurring), assets, budgets, envelopes.
"""

import sqlite3
import os
from datetime import datetime
from core.constants import DB_NAME


class Database:
    """Manages all SQLite operations."""

    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), DB_NAME)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._create_tables()

    # ================================================================ #
    #  Schema
    # ================================================================ #
    def _create_tables(self):
        c = self.conn.cursor()
        c.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT    UNIQUE NOT NULL,
                password_hash TEXT    NOT NULL,
                totp_secret   TEXT,
                created_at    TEXT    DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS expenses (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id       INTEGER NOT NULL,
                date          TEXT    NOT NULL,
                amount        REAL    NOT NULL,
                category      TEXT    NOT NULL,
                description   TEXT    DEFAULT '',
                merchant      TEXT    DEFAULT '',
                is_recurring  INTEGER DEFAULT 0,
                created_at    TEXT    DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS assets (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id       INTEGER NOT NULL,
                name          TEXT    NOT NULL,
                asset_type    TEXT    NOT NULL,
                quantity      REAL    NOT NULL DEFAULT 0,
                cost_basis    REAL    NOT NULL DEFAULT 0,
                current_price REAL    NOT NULL DEFAULT 0,
                updated_at    TEXT    DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS budgets (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id       INTEGER UNIQUE NOT NULL,
                monthly_limit REAL   NOT NULL DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS envelopes (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id       INTEGER NOT NULL,
                category      TEXT    NOT NULL,
                monthly_limit REAL    NOT NULL DEFAULT 0,
                UNIQUE(user_id, category),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_expenses_user   ON expenses(user_id);
            CREATE INDEX IF NOT EXISTS idx_expenses_date   ON expenses(user_id, date);
            CREATE INDEX IF NOT EXISTS idx_assets_user     ON assets(user_id);
            CREATE INDEX IF NOT EXISTS idx_envelopes_user  ON envelopes(user_id);
        """)
        self.conn.commit()

    # ================================================================ #
    #  Users
    # ================================================================ #
    def add_user(self, username: str, password_hash: str, totp_secret: str) -> bool:
        try:
            self.conn.execute(
                "INSERT INTO users (username, password_hash, totp_secret) VALUES (?, ?, ?)",
                (username, password_hash, totp_secret),
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def get_user_by_username(self, username: str) -> dict | None:
        row = self.conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        return dict(row) if row else None

    # ================================================================ #
    #  Expenses
    # ================================================================ #
    def add_expense(self, user_id: int, date: str, amount: float,
                    category: str, description: str = "",
                    merchant: str = "", is_recurring: int = 0) -> int:
        cur = self.conn.execute(
            "INSERT INTO expenses (user_id, date, amount, category, description, merchant, is_recurring) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, date, amount, category, description, merchant, is_recurring),
        )
        return int(cur.lastrowid) if cur.lastrowid else 0

    def bulk_add_expenses(self, rows: list[tuple]) -> int:
        """Insert many expenses at once. Each tuple: (user_id, date, amount, category, desc, merchant, is_recurring)."""
        self.conn.executemany(
            "INSERT INTO expenses (user_id, date, amount, category, description, merchant, is_recurring) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)", rows,
        )
        self.conn.commit()
        return len(rows)

    def get_expenses(self, user_id: int, limit: int | None = None) -> list[dict]:
        q = "SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC, id DESC"
        if limit:
            q += f" LIMIT {int(limit)}"
        return [dict(r) for r in self.conn.execute(q, (user_id,)).fetchall()]

    def search_expenses(self, user_id: int, *, keyword: str = "",
                        category: str = "", date_from: str = "",
                        date_to: str = "") -> list[dict]:
        q = "SELECT * FROM expenses WHERE user_id = ?"
        p: list = [user_id]
        if keyword:
            q += " AND (description LIKE ? OR category LIKE ? OR merchant LIKE ?)"
            p += [f"%{keyword}%"] * 3
        if category:
            q += " AND category = ?"
            p.append(category)
        if date_from:
            q += " AND date >= ?"
            p.append(date_from)
        if date_to:
            q += " AND date <= ?"
            p.append(date_to)
        q += " ORDER BY date DESC, id DESC"
        return [dict(r) for r in self.conn.execute(q, p).fetchall()]

    def delete_expense(self, expense_id: int, user_id: int) -> bool:
        cur = self.conn.execute(
            "DELETE FROM expenses WHERE id = ? AND user_id = ?", (expense_id, user_id)
        )
        self.conn.commit()
        return cur.rowcount > 0

    def get_all_expenses_raw(self, user_id: int) -> list[dict]:
        """All expenses, no limit, for analytics."""
        return [dict(r) for r in self.conn.execute(
            "SELECT * FROM expenses WHERE user_id = ? ORDER BY date ASC", (user_id,)
        ).fetchall()]

    # ================================================================ #
    #  Assets
    # ================================================================ #
    def add_asset(self, user_id: int, name: str, asset_type: str,
                  quantity: float, cost_basis: float, current_price: float) -> int:
        cur = self.conn.execute(
            "INSERT INTO assets (user_id, name, asset_type, quantity, cost_basis, current_price) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, name, asset_type, quantity, cost_basis, current_price),
        )
        return int(cur.lastrowid) if cur.lastrowid else 0

    def get_assets(self, user_id: int) -> list[dict]:
        return [dict(r) for r in self.conn.execute(
            "SELECT * FROM assets WHERE user_id = ? ORDER BY asset_type, name", (user_id,)
        ).fetchall()]

    def update_asset(self, asset_id: int, user_id: int, **kwargs):
        allowed = {"name", "asset_type", "quantity", "cost_basis", "current_price"}
        sets = []
        vals = []
        for k, v in kwargs.items():
            if k in allowed:
                sets.append(f"{k} = ?")
                vals.append(v)
        if not sets:
            return
        sets.append("updated_at = ?")
        vals.append(datetime.now().isoformat())
        vals.append(asset_id)
        vals.append(user_id)
        self.conn.execute(
            f"UPDATE assets SET {', '.join(sets)} WHERE id = ? AND user_id = ?", vals
        )
        self.conn.commit()

    def delete_asset(self, asset_id: int, user_id: int) -> bool:
        cur = self.conn.execute(
            "DELETE FROM assets WHERE id = ? AND user_id = ?", (asset_id, user_id)
        )
        self.conn.commit()
        return cur.rowcount > 0

    def get_total_asset_value(self, user_id: int) -> float:
        row = self.conn.execute(
            "SELECT COALESCE(SUM(quantity * current_price), 0) AS total "
            "FROM assets WHERE user_id = ?", (user_id,)
        ).fetchone()
        return row["total"]

    # ================================================================ #
    #  Budgets
    # ================================================================ #
    def get_budget(self, user_id: int) -> float:
        row = self.conn.execute(
            "SELECT monthly_limit FROM budgets WHERE user_id = ?", (user_id,)
        ).fetchone()
        return row["monthly_limit"] if row else 0.0

    def set_budget(self, user_id: int, monthly_limit: float):
        self.conn.execute(
            "INSERT INTO budgets (user_id, monthly_limit) VALUES (?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET monthly_limit = excluded.monthly_limit",
            (user_id, monthly_limit),
        )
        self.conn.commit()

    # ================================================================ #
    #  Aggregate queries
    # ================================================================ #
    def get_total_spent(self, user_id: int) -> float:
        row = self.conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS t FROM expenses "
            "WHERE user_id = ? AND category != 'Income'", (user_id,)
        ).fetchone()
        return row["t"]

    def get_total_income(self, user_id: int) -> float:
        row = self.conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS t FROM expenses "
            "WHERE user_id = ? AND category = 'Income'", (user_id,)
        ).fetchone()
        return row["t"]

    def get_monthly_spent(self, user_id: int) -> float:
        month = datetime.now().strftime("%Y-%m")
        row = self.conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS t FROM expenses "
            "WHERE user_id = ? AND category != 'Income' AND strftime('%%Y-%%m', date) = ?",
            (user_id, month),
        ).fetchone()
        return row["t"]

    # ================================================================ #
    #  Envelopes (Dynamic Budget)
    # ================================================================ #
    def get_envelopes(self, user_id: int) -> list[dict]:
        return [dict(r) for r in self.conn.execute(
            "SELECT * FROM envelopes WHERE user_id = ? ORDER BY category", (user_id,)
        ).fetchall()]

    def set_envelope(self, user_id: int, category: str, monthly_limit: float):
        self.conn.execute(
            "INSERT INTO envelopes (user_id, category, monthly_limit) VALUES (?, ?, ?) "
            "ON CONFLICT(user_id, category) DO UPDATE SET monthly_limit = excluded.monthly_limit",
            (user_id, category, monthly_limit),
        )
        self.conn.commit()

    def delete_envelope(self, user_id: int, category: str):
        self.conn.execute(
            "DELETE FROM envelopes WHERE user_id = ? AND category = ?",
            (user_id, category),
        )
        self.conn.commit()

    # ================================================================ #
    #  Cleanup
    # ================================================================ #
    def close(self):
        self.conn.close()
