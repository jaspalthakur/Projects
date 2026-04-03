"""
login_window.py — Vault-style login window with username + password + TOTP.
"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QSpacerItem, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap
from core.constants import COLORS


class LoginWindow(QWidget):
    """Vault login screen: username, password, optional TOTP."""

    login_success = Signal(dict)   # emits user dict
    show_signup = Signal()

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self._build_ui()

    def _build_ui(self):
        self.setObjectName("central")
        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignCenter)

        # ── Card ──
        card = QFrame()
        card.setObjectName("card")
        card.setFixedWidth(420)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 44, 40, 40)
        card_layout.setSpacing(6)

        # Icon + title
        icon = QLabel()
        icon.setAlignment(Qt.AlignCenter)
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "logo.png")
        if os.path.exists(logo_path):
            pix = QPixmap(logo_path).scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon.setPixmap(pix)
        else:
            icon.setText("🔐")
            icon.setFont(QFont("Segoe UI Emoji", 40))
        card_layout.addWidget(icon)

        title = QLabel("Vault Login")
        title.setObjectName("heading")
        title.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(title)

        sub = QLabel("Enter your credentials to access your financial data")
        sub.setObjectName("subheading")
        sub.setAlignment(Qt.AlignCenter)
        sub.setWordWrap(True)
        card_layout.addWidget(sub)
        card_layout.addSpacing(20)

        # Username
        card_layout.addWidget(self._label("Username"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.setMinimumHeight(40)
        card_layout.addWidget(self.username_input)
        card_layout.addSpacing(10)

        # Password
        card_layout.addWidget(self._label("Password"))
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(40)
        card_layout.addWidget(self.password_input)
        card_layout.addSpacing(10)

        # TOTP
        card_layout.addWidget(self._label("2FA Code (6 digits)"))
        self.totp_input = QLineEdit()
        self.totp_input.setPlaceholderText("Enter authenticator code")
        self.totp_input.setMaxLength(6)
        self.totp_input.setMinimumHeight(40)
        card_layout.addWidget(self.totp_input)
        card_layout.addSpacing(6)

        # Error
        self.error_label = QLabel("")
        self.error_label.setObjectName("error")
        self.error_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(self.error_label)
        card_layout.addSpacing(8)

        # Login button
        login_btn = QPushButton("Unlock Vault")
        login_btn.setMinimumHeight(44)
        login_btn.setCursor(Qt.PointingHandCursor)
        login_btn.clicked.connect(self._login)
        card_layout.addWidget(login_btn)
        card_layout.addSpacing(12)

        # Signup link
        link_row = QHBoxLayout()
        link_row.setAlignment(Qt.AlignCenter)
        link_label = QLabel("Don't have an account?")
        link_label.setObjectName("muted")
        link_row.addWidget(link_label)
        signup_btn = QPushButton("Create Account")
        signup_btn.setObjectName("secondary")
        signup_btn.setCursor(Qt.PointingHandCursor)
        signup_btn.setFixedWidth(130)
        signup_btn.clicked.connect(self.show_signup.emit)
        link_row.addWidget(signup_btn)
        card_layout.addLayout(link_row)

        outer.addWidget(card)

        # Enter key triggers login
        self.password_input.returnPressed.connect(self._login)
        self.totp_input.returnPressed.connect(self._login)

    def _label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(f"font-weight: bold; font-size: 12px; color: {COLORS['text_secondary']};")
        return lbl

    def _login(self):
        from core.security import verify_password, verify_totp

        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        totp_code = self.totp_input.text().strip()

        if not username or not password:
            self.error_label.setText("Please fill in username and password.")
            return

        user = self.db.get_user_by_username(username)
        if not user:
            self.error_label.setText("Invalid credentials.")
            return

        if not verify_password(user["password_hash"], password):
            self.error_label.setText("Invalid credentials.")
            return

        # TOTP check (if user has a secret set)
        if user.get("totp_secret"):
            if not totp_code:
                self.error_label.setText("Please enter your 2FA code.")
                return
            if not verify_totp(user["totp_secret"], totp_code):
                self.error_label.setText("Invalid 2FA code. Try again.")
                return

        self.error_label.setText("")
        self.login_success.emit(dict(user))
