"""
main_window.py — Main application shell with sidebar navigation and stacked pages.
"""

import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame,
    QPushButton, QLabel, QStackedWidget, QSpacerItem, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap
from core.constants import COLORS
from core.database import Database


class MainWindow(QMainWindow):
    """Sidebar shell that hosts all app pages via QStackedWidget."""

    logout_signal = Signal()

    NAV_ITEMS = [
        ("📊", "Dashboard",  "dashboard"),
        ("💳", "Expenses",   "expenses"),
        ("📥", "Import",     "import"),
        ("📈", "Analytics",  "analytics"),
        ("💼", "Portfolio",  "assets"),
        ("⚙️", "Settings",   "settings"),
    ]

    def __init__(self, db: Database, user: dict, parent=None):
        super().__init__(parent)
        self.db = db
        self.user = user
        self.setWindowTitle(f"Wallet Hub  —  {user['username']}")
        self.setMinimumSize(1120, 720)
        self.resize(1280, 800)
        self._build_ui()
        self._navigate("dashboard")

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Sidebar ──
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(12, 20, 12, 20)
        sb_layout.setSpacing(4)

        # Brand
        brand_row = QHBoxLayout()
        brand_icon = QLabel()
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "logo.png")
        if os.path.exists(logo_path):
            pix = QPixmap(logo_path).scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            brand_icon.setPixmap(pix)
        else:
            brand_icon.setText("💰")
            brand_icon.setFont(QFont("Segoe UI Emoji", 20))
        brand_row.addWidget(brand_icon)
        brand_text = QLabel("Wallet Hub")
        brand_text.setStyleSheet(
            f"font-size: 18px; font-weight: bold; color: {COLORS['accent']};"
        )
        brand_row.addWidget(brand_text)
        brand_row.addStretch()
        sb_layout.addLayout(brand_row)
        sb_layout.addSpacing(30)

        # Nav buttons
        self._nav_buttons: dict[str, QPushButton] = {}
        for icon, label, key in self.NAV_ITEMS:
            btn = QPushButton(f"  {icon}   {label}")
            btn.setObjectName("nav")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setMinimumHeight(42)
            btn.clicked.connect(lambda checked, k=key: self._navigate(k))
            sb_layout.addWidget(btn)
            self._nav_buttons[key] = btn

        sb_layout.addStretch()

        # User info
        user_frame = QFrame()
        user_frame.setStyleSheet(
            f"background-color: {COLORS['bg_surface']}; border-radius: 10px;"
        )
        uf_layout = QVBoxLayout(user_frame)
        uf_layout.setContentsMargins(14, 12, 14, 12)
        user_label = QLabel(f"👤  {self.user['username']}")
        user_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 13px; font-weight: bold;")
        uf_layout.addWidget(user_label)
        vault_label = QLabel("🔒  Vault Secured")
        vault_label.setStyleSheet(f"color: {COLORS['green']}; font-size: 11px;")
        uf_layout.addWidget(vault_label)
        sb_layout.addWidget(user_frame)

        root.addWidget(sidebar)

        # ── Page Stack ──
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background-color: {COLORS['bg_darkest']};")
        root.addWidget(self.stack)

        # ── Build Pages (lazy import to avoid circular deps) ──
        from ui.dashboard_page import DashboardPage
        from ui.expenses_page import ExpensesPage
        from ui.import_page import ImportPage
        from ui.analytics_page import AnalyticsPage
        from ui.assets_page import AssetsPage
        from ui.settings_page import SettingsPage

        self._pages: dict[str, QWidget] = {}
        page_classes = {
            "dashboard": DashboardPage,
            "expenses":  ExpensesPage,
            "import":    ImportPage,
            "analytics": AnalyticsPage,
            "assets":    AssetsPage,
            "settings":  SettingsPage,
        }
        for key, cls in page_classes.items():
            if key == "settings":
                page = cls(self.db, self.user, self._navigate, self._logout)
            else:
                page = cls(self.db, self.user, self._navigate)
            self.stack.addWidget(page)
            self._pages[key] = page

    def _navigate(self, page_key: str):
        page = self._pages.get(page_key)
        if not page:
            return

        # Update sidebar highlight
        for k, btn in self._nav_buttons.items():
            btn.setChecked(k == page_key)

        # Refresh page data if it has a refresh method
        if hasattr(page, "refresh"):
            page.refresh()

        self.stack.setCurrentWidget(page)

    def _logout(self):
        self.logout_signal.emit()
        self.close()
