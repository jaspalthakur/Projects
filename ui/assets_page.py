"""
assets_page.py — Multi-asset portfolio tracker with live price refresh.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QFormLayout, QLineEdit, QComboBox, QMessageBox,
)
from PySide6.QtCore import Qt
from core.constants import COLORS, ASSET_TYPES
from core.api_client import PriceFetcher, resolve_crypto_id, is_likely_ticker
from utils_helpers import format_currency


class AssetsPage(QWidget):
    """Track crypto, stock, and other asset holdings with live pricing."""

    def __init__(self, db, user, navigate, parent=None):
        super().__init__(parent)
        self.db = db
        self.user = user
        self.navigate = navigate
        self._fetcher = PriceFetcher()
        self._fetcher.prices_ready.connect(self._on_prices)
        self._fetcher.error.connect(self._on_price_error)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        # Header
        header = QHBoxLayout()
        title = QLabel("Portfolio")
        title.setObjectName("heading")
        header.addWidget(title)
        header.addStretch()

        self.refresh_btn = QPushButton("🔄  Refresh Prices")
        self.refresh_btn.setObjectName("secondary")
        self.refresh_btn.setMinimumHeight(40)
        self.refresh_btn.setFixedWidth(170)
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_btn.clicked.connect(self._fetch_live_prices)
        header.addWidget(self.refresh_btn)

        add_btn = QPushButton("➕  Add Asset")
        add_btn.setMinimumHeight(40)
        add_btn.setFixedWidth(150)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.clicked.connect(self._show_add_dialog)
        header.addWidget(add_btn)
        layout.addLayout(header)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setObjectName("muted")
        layout.addWidget(self.status_label)

        # Summary card
        self.summary_card = QFrame()
        self.summary_card.setObjectName("card")
        self.summary_layout = QHBoxLayout(self.summary_card)
        self.summary_layout.setContentsMargins(24, 18, 24, 18)
        layout.addWidget(self.summary_card)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID", "Name", "Type", "Quantity", "Cost Basis", "Current Price", "Value", "P&L", "Action"
        ])
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnHidden(0, True)

        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        for c in [2, 3, 4, 5, 6, 7]:
            hh.setSectionResizeMode(c, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(8, QHeaderView.Fixed)
        self.table.setColumnWidth(8, 80)
        layout.addWidget(self.table)

    def refresh(self):
        # Update summary
        while self.summary_layout.count():
            item = self.summary_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        total_value = self.db.get_total_asset_value(self.user["id"])
        assets = self.db.get_assets(self.user["id"])
        total_cost = sum(a["cost_basis"] for a in assets)
        total_pnl = total_value - total_cost

        icon = QLabel("💼")
        icon.setStyleSheet("font-size: 28px;")
        self.summary_layout.addWidget(icon)

        info = QVBoxLayout()
        info.addWidget(self._styled_label("Total Portfolio Value", COLORS["text_secondary"], 12))
        val_lbl = QLabel(format_currency(total_value))
        val_lbl.setStyleSheet(f"font-size: 26px; font-weight: bold; color: {COLORS['green']};")
        info.addWidget(val_lbl)

        pnl_color = COLORS["green"] if total_pnl >= 0 else COLORS["red"]
        pnl_sign = "+" if total_pnl >= 0 else ""
        pnl_lbl = QLabel(f"P&L: {pnl_sign}{format_currency(total_pnl)}")
        pnl_lbl.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {pnl_color};")
        info.addWidget(pnl_lbl)

        info.addWidget(self._styled_label(f"{len(assets)} assets tracked", COLORS["text_muted"], 11))
        self.summary_layout.addLayout(info)
        self.summary_layout.addStretch()

        # Update table
        self.table.setRowCount(len(assets))
        for i, a in enumerate(assets):
            self.table.setItem(i, 0, QTableWidgetItem(str(a["id"])))
            self.table.setItem(i, 1, QTableWidgetItem(a["name"]))
            self.table.setItem(i, 2, QTableWidgetItem(a["asset_type"]))
            self.table.setItem(i, 3, QTableWidgetItem(f"{a['quantity']:.4f}"))
            self.table.setItem(i, 4, QTableWidgetItem(format_currency(a["cost_basis"])))
            self.table.setItem(i, 5, QTableWidgetItem(format_currency(a["current_price"])))

            value = a["quantity"] * a["current_price"]
            self.table.setItem(i, 6, QTableWidgetItem(format_currency(value)))

            pnl = value - a["cost_basis"]
            pnl_item = QTableWidgetItem(f"{'+' if pnl >= 0 else ''}{format_currency(pnl)}")
            self.table.setItem(i, 7, pnl_item)

            del_btn = QPushButton("🗑")
            del_btn.setObjectName("danger")
            del_btn.setFixedSize(36, 28)
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.clicked.connect(lambda _, aid=a["id"]: self._delete(aid))
            self.table.setCellWidget(i, 8, del_btn)

    def _styled_label(self, text, color, size):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: {color}; font-size: {size}px;")
        return lbl

    def _delete(self, aid):
        if QMessageBox.question(self, "Delete", "Remove this asset?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.db.delete_asset(aid, self.user["id"])
            self.refresh()

    def _fetch_live_prices(self):
        """Fetch live prices for all portfolio assets in the background."""
        assets = self.db.get_assets(self.user["id"])
        if not assets:
            self.status_label.setText("No assets to refresh.")
            return

        self.refresh_btn.setEnabled(False)
        self.status_label.setText("⏳ Fetching live prices...")

        crypto_ids = []
        stock_tickers = []
        self._asset_map = {}

        for a in assets:
            name_lower = a["name"].lower().strip()
            if a["asset_type"] == "Crypto":
                cid = resolve_crypto_id(name_lower)
                if cid:
                    crypto_ids.append(cid)
                    self._asset_map[cid] = a
            elif a["asset_type"] == "Stock" and is_likely_ticker(a["name"]):
                ticker = a["name"].upper().strip()
                stock_tickers.append(ticker)
                self._asset_map[ticker] = a

        if crypto_ids:
            self._fetcher.fetch_crypto_prices(crypto_ids)
        if stock_tickers:
            self._fetcher.fetch_stock_prices(stock_tickers)
        if not crypto_ids and not stock_tickers:
            self.status_label.setText("No crypto/stock assets to fetch prices for.")
            self.refresh_btn.setEnabled(True)

    def _on_prices(self, prices: dict):
        for key, price in prices.items():
            asset = self._asset_map.get(key)
            if asset:
                self.db.update_asset(asset["id"], self.user["id"], current_price=price)

        self.status_label.setText(f"✅ Updated {len(prices)} asset prices")
        self.refresh_btn.setEnabled(True)
        self.refresh()

    def _on_price_error(self, msg: str):
        self.status_label.setText(f"❌ {msg}")
        self.refresh_btn.setEnabled(True)

    def _show_add_dialog(self):
        dlg = _AddAssetDialog(self.db, self.user, self)
        if dlg.exec() == QDialog.Accepted:
            self.refresh()


class _AddAssetDialog(QDialog):
    def __init__(self, db, user, parent=None):
        super().__init__(parent)
        self.db = db
        self.user = user
        self.setWindowTitle("Add Asset")
        self.setFixedSize(380, 380)
        self._build()

    def _build(self):
        form = QFormLayout(self)
        form.setSpacing(12)
        form.setContentsMargins(24, 24, 24, 24)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Bitcoin, AAPL, Gold")
        self.name_input.setMinimumHeight(36)
        form.addRow("Name:", self.name_input)

        self.type_input = QComboBox()
        self.type_input.addItems(ASSET_TYPES)
        self.type_input.setMinimumHeight(36)
        form.addRow("Type:", self.type_input)

        self.qty_input = QLineEdit()
        self.qty_input.setPlaceholderText("e.g. 0.5")
        self.qty_input.setMinimumHeight(36)
        form.addRow("Quantity:", self.qty_input)

        self.cost_input = QLineEdit()
        self.cost_input.setPlaceholderText("Total cost basis (₹)")
        self.cost_input.setMinimumHeight(36)
        form.addRow("Cost Basis:", self.cost_input)

        self.price_input = QLineEdit()
        self.price_input.setPlaceholderText("Current price per unit (₹)")
        self.price_input.setMinimumHeight(36)
        form.addRow("Current Price:", self.price_input)

        self.error_label = QLabel("")
        self.error_label.setObjectName("error")
        form.addRow(self.error_label)

        btn = QPushButton("Add Asset")
        btn.setMinimumHeight(42)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(self._save)
        form.addRow(btn)

    def _save(self):
        name = self.name_input.text().strip()
        if not name:
            self.error_label.setText("Name is required."); return
        try:
            qty = float(self.qty_input.text())
            cost = float(self.cost_input.text())
            price = float(self.price_input.text())
        except ValueError:
            self.error_label.setText("Numbers must be valid."); return

        self.db.add_asset(self.user["id"], name, self.type_input.currentText(),
                          qty, cost, price)
        self.accept()
