"""
settings_page.py — Budget, dynamic envelope config, CSV/PDF export, and logout.
"""

import csv
import os
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton,
    QLineEdit, QMessageBox, QFileDialog, QComboBox, QScrollArea,
    QGridLayout,
)
from PySide6.QtCore import Qt
from core.constants import COLORS, CATEGORIES, DEFAULT_ENVELOPES
from utils_helpers import validate_amount, format_currency


class SettingsPage(QWidget):
    """Budget config, dynamic envelopes, CSV/PDF export, logout."""

    def __init__(self, db, user, navigate, logout_cb, parent=None):
        super().__init__(parent)
        self.db = db
        self.user = user
        self.navigate = navigate
        self.logout_cb = logout_cb
        self._build_ui()

    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(28, 24, 28, 24)
        main.setSpacing(0)

        title = QLabel("Settings")
        title.setObjectName("heading")
        main.addWidget(title)
        main.addSpacing(16)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setSpacing(16)
        scroll.setWidget(container)
        main.addWidget(scroll)

        # ── Budget Card ──
        budget_card = QFrame()
        budget_card.setObjectName("card")
        bl = QVBoxLayout(budget_card)
        bl.setContentsMargins(24, 20, 24, 20)
        bl.addWidget(self._bold("🎯  Monthly Budget"))

        current = self.db.get_budget(self.user["id"])
        bl.addWidget(self._muted(
            f"Current: {format_currency(current) if current else 'Not set'}"
        ))

        row = QHBoxLayout()
        self.budget_input = QLineEdit()
        self.budget_input.setPlaceholderText("Enter monthly limit (₹)")
        self.budget_input.setMinimumHeight(40)
        if current:
            self.budget_input.setText(str(int(current)))
        row.addWidget(self.budget_input)

        save_btn = QPushButton("Save")
        save_btn.setMinimumHeight(40)
        save_btn.setFixedWidth(100)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self._save_budget)
        row.addWidget(save_btn)
        bl.addLayout(row)

        self.budget_err = QLabel("")
        self.budget_err.setObjectName("error")
        bl.addWidget(self.budget_err)
        layout.addWidget(budget_card)

        # ── Dynamic Envelopes Card ──
        env_card = QFrame()
        env_card.setObjectName("card")
        el = QVBoxLayout(env_card)
        el.setContentsMargins(24, 20, 24, 20)
        el.addWidget(self._bold("📊  Dynamic Envelope Budgets"))
        el.addWidget(self._muted(
            "Per-category spending limits that auto-adjust based on income fluctuations."
        ))
        el.addSpacing(10)

        # Envelope inputs grid
        self._env_inputs: dict[str, QLineEdit] = {}
        env_grid = QGridLayout()
        env_grid.setSpacing(8)

        expense_cats = [c for c in CATEGORIES if c != "Income" and c != "Other"]
        for i, cat in enumerate(expense_cats):
            lbl = QLabel(cat)
            lbl.setStyleSheet(f"font-size: 12px; color: {COLORS['text_secondary']};")
            env_grid.addWidget(lbl, i, 0)

            inp = QLineEdit()
            inp.setPlaceholderText("Limit (₹)")
            inp.setMinimumHeight(32)
            inp.setFixedWidth(120)

            # Pre-fill from DB or defaults
            envelopes = self.db.get_envelopes(self.user["id"])
            existing = {e["category"]: e["monthly_limit"] for e in envelopes}
            val = existing.get(cat) or DEFAULT_ENVELOPES.get(cat, 0)
            if val:
                inp.setText(str(int(val)))

            env_grid.addWidget(inp, i, 1)
            self._env_inputs[cat] = inp

        el.addLayout(env_grid)

        save_env_btn = QPushButton("Save Envelopes")
        save_env_btn.setMinimumHeight(40)
        save_env_btn.setFixedWidth(160)
        save_env_btn.setCursor(Qt.PointingHandCursor)
        save_env_btn.clicked.connect(self._save_envelopes)
        el.addSpacing(10)
        el.addWidget(save_env_btn)

        self.env_err = QLabel("")
        self.env_err.setObjectName("error")
        el.addWidget(self.env_err)
        layout.addWidget(env_card)

        # ── Export Card ──
        export_card = QFrame()
        export_card.setObjectName("card")
        xl = QVBoxLayout(export_card)
        xl.setContentsMargins(24, 20, 24, 20)
        xl.addWidget(self._bold("📁  Export Data"))
        xl.addWidget(self._muted("Download your financial data in CSV or PDF format."))

        btn_row = QHBoxLayout()
        csv_btn = QPushButton("Export CSV")
        csv_btn.setObjectName("secondary")
        csv_btn.setMinimumHeight(40)
        csv_btn.setCursor(Qt.PointingHandCursor)
        csv_btn.clicked.connect(self._export_csv)
        btn_row.addWidget(csv_btn)

        pdf_btn = QPushButton("Export PDF Report")
        pdf_btn.setObjectName("secondary")
        pdf_btn.setMinimumHeight(40)
        pdf_btn.setCursor(Qt.PointingHandCursor)
        pdf_btn.clicked.connect(self._export_pdf)
        btn_row.addWidget(pdf_btn)
        btn_row.addStretch()
        xl.addLayout(btn_row)
        layout.addWidget(export_card)

        # ── Account Card ──
        account_card = QFrame()
        account_card.setObjectName("card")
        al = QVBoxLayout(account_card)
        al.setContentsMargins(24, 20, 24, 20)
        al.addWidget(self._bold("👤  Account"))
        al.addWidget(self._muted(
            f"Logged in as: {self.user['username']}\n"
            f"2FA: {'Enabled ✅' if self.user.get('totp_secret') else 'Disabled ❌'}"
        ))

        logout_btn = QPushButton("🚪  Logout")
        logout_btn.setObjectName("danger")
        logout_btn.setMinimumHeight(42)
        logout_btn.setFixedWidth(160)
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.clicked.connect(self._logout)
        al.addWidget(logout_btn)
        layout.addWidget(account_card)

        layout.addStretch()

    def refresh(self):
        pass

    def _bold(self, t):
        lbl = QLabel(t)
        lbl.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {COLORS['text_primary']};")
        return lbl

    def _muted(self, t):
        lbl = QLabel(t)
        lbl.setStyleSheet(f"font-size: 13px; color: {COLORS['text_secondary']};")
        return lbl

    def _save_budget(self):
        val = self.budget_input.text().strip()
        ok, err = validate_amount(val)
        if not ok:
            self.budget_err.setText(err); return
        self.db.set_budget(self.user["id"], float(val))
        self.budget_err.setText("")
        QMessageBox.information(self, "Success", "Monthly budget updated!")

    def _save_envelopes(self):
        errors = []
        for cat, inp in self._env_inputs.items():
            val = inp.text().strip()
            if not val:
                continue
            try:
                limit = float(val)
                if limit > 0:
                    self.db.set_envelope(self.user["id"], cat, limit)
            except ValueError:
                errors.append(cat)

        if errors:
            self.env_err.setText(f"Invalid values for: {', '.join(errors)}")
        else:
            self.env_err.setText("")
            QMessageBox.information(self, "Success", "Envelope budgets saved!")

    def _export_csv(self):
        expenses = self.db.get_expenses(self.user["id"])
        if not expenses:
            QMessageBox.warning(self, "No Data", "No expenses to export."); return

        path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "expenses_export.csv",
                                              "CSV Files (*.csv)")
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["Date", "Amount", "Category", "Description", "Merchant"])
            for e in expenses:
                w.writerow([e["date"], e["amount"], e["category"],
                            e.get("description", ""), e.get("merchant", "")])
        QMessageBox.information(self, "Exported", f"CSV saved to:\n{path}")

    def _export_pdf(self):
        expenses = self.db.get_expenses(self.user["id"])
        if not expenses:
            QMessageBox.warning(self, "No Data", "No expenses to export."); return

        path, _ = QFileDialog.getSaveFileName(self, "Save PDF",
                                              "financial_report.pdf", "PDF Files (*.pdf)")
        if not path:
            return

        try:
            from fpdf import FPDF

            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()

            pdf.set_font("Helvetica", "B", 18)
            pdf.cell(0, 12, "Wallet Hub Report", new_x="LMARGIN", new_y="NEXT", align="C")
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(0, 8, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}  |  User: {self.user['username']}",
                     new_x="LMARGIN", new_y="NEXT", align="C")
            pdf.ln(8)

            total = sum(e["amount"] for e in expenses if e["category"] != "Income")
            income = sum(e["amount"] for e in expenses if e["category"] == "Income")
            budget = self.db.get_budget(self.user["id"])

            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 8, "Summary", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(0, 6, f"Total Spending: Rs {total:,.2f}", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 6, f"Total Income: Rs {income:,.2f}", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 6, f"Net: Rs {income - total:,.2f}", new_x="LMARGIN", new_y="NEXT")
            if budget:
                pdf.cell(0, 6, f"Monthly Budget: Rs {budget:,.2f}", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(6)

            pdf.set_font("Helvetica", "B", 9)
            col_widths = [28, 28, 40, 45, 49]
            headers = ["Date", "Amount", "Category", "Description", "Merchant"]
            for w, h in zip(col_widths, headers):
                pdf.cell(w, 8, h, border=1)
            pdf.ln()

            pdf.set_font("Helvetica", "", 8)
            for e in expenses:
                pdf.cell(col_widths[0], 7, e["date"][:10], border=1)
                pdf.cell(col_widths[1], 7, f"Rs {e['amount']:,.2f}", border=1)
                pdf.cell(col_widths[2], 7, e["category"][:18], border=1)
                pdf.cell(col_widths[3], 7, (e.get("description") or "")[:22], border=1)
                pdf.cell(col_widths[4], 7, (e.get("merchant") or "")[:24], border=1)
                pdf.ln()

            pdf.output(path)
            QMessageBox.information(self, "Exported", f"PDF saved to:\n{path}")
        except Exception as ex:
            QMessageBox.critical(self, "Error", f"PDF generation failed:\n{ex}")

    def _logout(self):
        if QMessageBox.question(self, "Logout", "Are you sure?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.logout_cb()
