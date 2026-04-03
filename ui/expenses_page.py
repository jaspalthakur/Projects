"""
expenses_page.py — Full expense management: table view, add form, search, delete.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QDialog, QFormLayout,
)
from PySide6.QtCore import Qt
from core.constants import COLORS, CATEGORIES
from utils_helpers import validate_amount, validate_date, format_currency, today_str


class ExpensesPage(QWidget):
    """Expense list with search, add, and delete."""

    def __init__(self, db, user, navigate, parent=None):
        super().__init__(parent)
        self.db = db
        self.user = user
        self.navigate = navigate
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        # ── Header ──
        header = QHBoxLayout()
        title = QLabel("Expenses")
        title.setObjectName("heading")
        header.addWidget(title)
        header.addStretch()

        add_btn = QPushButton("➕  Add Expense")
        add_btn.setMinimumHeight(40)
        add_btn.setFixedWidth(160)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.clicked.connect(self._show_add_dialog)
        header.addWidget(add_btn)
        layout.addLayout(header)

        # ── Search / Filter Bar ──
        filter_frame = QFrame()
        filter_frame.setObjectName("card")
        fl = QHBoxLayout(filter_frame)
        fl.setContentsMargins(16, 12, 16, 12)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍  Search by description or merchant...")
        self.search_input.setMinimumHeight(38)
        self.search_input.textChanged.connect(self._load_data)
        fl.addWidget(self.search_input, stretch=2)

        self.cat_filter = QComboBox()
        self.cat_filter.addItem("All Categories")
        self.cat_filter.addItems(CATEGORIES)
        self.cat_filter.setMinimumHeight(38)
        self.cat_filter.setMinimumWidth(180)
        self.cat_filter.currentTextChanged.connect(self._load_data)
        fl.addWidget(self.cat_filter)

        self.date_from = QLineEdit()
        self.date_from.setPlaceholderText("From (YYYY-MM-DD)")
        self.date_from.setMinimumHeight(38)
        self.date_from.setFixedWidth(150)
        self.date_from.textChanged.connect(self._load_data)
        fl.addWidget(self.date_from)

        self.date_to = QLineEdit()
        self.date_to.setPlaceholderText("To (YYYY-MM-DD)")
        self.date_to.setMinimumHeight(38)
        self.date_to.setFixedWidth(150)
        self.date_to.textChanged.connect(self._load_data)
        fl.addWidget(self.date_to)

        layout.addWidget(filter_frame)

        # ── Table ──
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Date", "Amount", "Category", "Description", "Merchant", "Action"]
        )
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnHidden(0, True)  # hide ID

        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.Stretch)
        hh.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(6, QHeaderView.Fixed)
        self.table.setColumnWidth(6, 80)

        layout.addWidget(self.table)

    def refresh(self):
        self._load_data()

    def _load_data(self):
        keyword = self.search_input.text().strip()
        cat = self.cat_filter.currentText()
        date_from = self.date_from.text().strip()
        date_to = self.date_to.text().strip()

        rows = self.db.search_expenses(
            self.user["id"],
            keyword=keyword,
            category="" if cat == "All Categories" else cat,
            date_from=date_from,
            date_to=date_to,
        )

        self.table.setRowCount(len(rows))
        for i, exp in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(str(exp["id"])))
            self.table.setItem(i, 1, QTableWidgetItem(exp["date"]))

            amt_item = QTableWidgetItem(format_currency(exp["amount"]))
            color = COLORS["green"] if exp["category"] == "Income" else COLORS["red"]
            amt_item.setForeground(Qt.GlobalColor.red if exp["category"] != "Income" else Qt.GlobalColor.green)
            self.table.setItem(i, 2, amt_item)

            self.table.setItem(i, 3, QTableWidgetItem(exp["category"]))
            self.table.setItem(i, 4, QTableWidgetItem(exp.get("description") or ""))
            self.table.setItem(i, 5, QTableWidgetItem(exp.get("merchant") or ""))

            del_btn = QPushButton("🗑")
            del_btn.setObjectName("danger")
            del_btn.setFixedSize(36, 28)
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.clicked.connect(lambda _, eid=exp["id"]: self._delete(eid))
            self.table.setCellWidget(i, 6, del_btn)

    def _delete(self, eid):
        reply = QMessageBox.question(self, "Delete", "Delete this expense?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db.delete_expense(eid, self.user["id"])
            self._load_data()

    def _show_add_dialog(self):
        dlg = _AddDialog(self.db, self.user, self)
        if dlg.exec() == QDialog.Accepted:
            self._load_data()


class _AddDialog(QDialog):
    """Modal dialog to add a new expense."""

    def __init__(self, db, user, parent=None):
        super().__init__(parent)
        self.db = db
        self.user = user
        self.setWindowTitle("Add Expense")
        self.setFixedSize(400, 400)
        self._build()

    def _build(self):
        form = QFormLayout(self)
        form.setSpacing(12)
        form.setContentsMargins(24, 24, 24, 24)

        self.date_input = QLineEdit(today_str())
        self.date_input.setMinimumHeight(36)
        form.addRow("Date:", self.date_input)

        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("e.g. 500")
        self.amount_input.setMinimumHeight(36)
        form.addRow("Amount (₹):", self.amount_input)

        self.cat_input = QComboBox()
        self.cat_input.addItems(CATEGORIES)
        self.cat_input.setMinimumHeight(36)
        form.addRow("Category:", self.cat_input)

        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Optional description")
        self.desc_input.setMinimumHeight(36)
        form.addRow("Description:", self.desc_input)

        self.merchant_input = QLineEdit()
        self.merchant_input.setPlaceholderText("Optional merchant name")
        self.merchant_input.setMinimumHeight(36)
        form.addRow("Merchant:", self.merchant_input)

        self.error_label = QLabel("")
        self.error_label.setObjectName("error")
        form.addRow(self.error_label)

        btn = QPushButton("Save Expense")
        btn.setMinimumHeight(42)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(self._save)
        form.addRow(btn)

    def _save(self):
        date = self.date_input.text().strip()
        amount = self.amount_input.text().strip()

        ok, err = validate_date(date)
        if not ok:
            self.error_label.setText(err); return
        ok, err = validate_amount(amount)
        if not ok:
            self.error_label.setText(err); return

        self.db.add_expense(
            self.user["id"], date, float(amount),
            self.cat_input.currentText(),
            self.desc_input.text().strip(),
            self.merchant_input.text().strip(),
        )
        self.accept()
