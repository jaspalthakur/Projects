"""
signup_window.py — Account registration with TOTP QR code setup.
"""

import io
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap, QImage
from core.constants import COLORS
from core.security import hash_password, generate_totp_secret, get_totp_uri, generate_qr_pixmap


class SignupWindow(QWidget):
    """Registration form → generates TOTP secret → shows QR code."""

    signup_success = Signal(dict)  # emits user dict
    show_login = Signal()

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self._totp_secret = None
        self._build_ui()

    def _build_ui(self):
        self.setObjectName("central")
        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignCenter)

        card = QFrame()
        card.setObjectName("card")
        card.setFixedWidth(460)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(40, 36, 40, 36)
        cl.setSpacing(6)

        icon = QLabel("✨")
        icon.setFont(QFont("Segoe UI Emoji", 36))
        icon.setAlignment(Qt.AlignCenter)
        cl.addWidget(icon)

        title = QLabel("Create Account")
        title.setObjectName("heading")
        title.setAlignment(Qt.AlignCenter)
        cl.addWidget(title)

        sub = QLabel("Secure your finances with Argon2 + 2FA")
        sub.setObjectName("subheading")
        sub.setAlignment(Qt.AlignCenter)
        cl.addWidget(sub)
        cl.addSpacing(16)

        # Username
        cl.addWidget(self._label("Username"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Choose a username")
        self.username_input.setMinimumHeight(40)
        cl.addWidget(self.username_input)
        cl.addSpacing(8)

        # Password
        cl.addWidget(self._label("Password"))
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Create a strong password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(40)
        cl.addWidget(self.password_input)
        cl.addSpacing(8)

        # Confirm
        cl.addWidget(self._label("Confirm Password"))
        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText("Repeat your password")
        self.confirm_input.setEchoMode(QLineEdit.Password)
        self.confirm_input.setMinimumHeight(40)
        cl.addWidget(self.confirm_input)
        cl.addSpacing(8)

        # QR placeholder
        self.qr_label = QLabel("")
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.qr_label.setVisible(False)
        cl.addWidget(self.qr_label)

        self.qr_info = QLabel("")
        self.qr_info.setObjectName("subheading")
        self.qr_info.setAlignment(Qt.AlignCenter)
        self.qr_info.setWordWrap(True)
        self.qr_info.setVisible(False)
        cl.addWidget(self.qr_info)

        # Error
        self.error_label = QLabel("")
        self.error_label.setObjectName("error")
        self.error_label.setAlignment(Qt.AlignCenter)
        cl.addWidget(self.error_label)
        cl.addSpacing(6)

        # Buttons
        self.create_btn = QPushButton("Create Account")
        self.create_btn.setMinimumHeight(44)
        self.create_btn.setCursor(Qt.PointingHandCursor)
        self.create_btn.clicked.connect(self._signup)
        cl.addWidget(self.create_btn)
        cl.addSpacing(10)

        link_row = QHBoxLayout()
        link_row.setAlignment(Qt.AlignCenter)
        lbl = QLabel("Already have an account?")
        lbl.setObjectName("muted")
        link_row.addWidget(lbl)
        login_btn = QPushButton("Login")
        login_btn.setObjectName("secondary")
        login_btn.setCursor(Qt.PointingHandCursor)
        login_btn.setFixedWidth(80)
        login_btn.clicked.connect(self.show_login.emit)
        link_row.addWidget(login_btn)
        cl.addLayout(link_row)

        outer.addWidget(card)

    def _label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(f"font-weight: bold; font-size: 12px; color: {COLORS['text_secondary']};")
        return lbl

    def _signup(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        confirm = self.confirm_input.text().strip()

        if not username or not password or not confirm:
            self.error_label.setText("Please fill in all fields.")
            return
        if len(password) < 6:
            self.error_label.setText("Password must be at least 6 characters.")
            return
        if password != confirm:
            self.error_label.setText("Passwords do not match.")
            return

        # Generate TOTP secret
        self._totp_secret = generate_totp_secret()
        pw_hash = hash_password(password)

        if not self.db.add_user(username, pw_hash, self._totp_secret):
            self.error_label.setText("Username already taken.")
            return

        # Show QR code
        uri = get_totp_uri(self._totp_secret, username)
        pil_img = generate_qr_pixmap(uri)

        # Convert PIL → QPixmap
        buf = io.BytesIO()
        pil_img.save(buf, format="PNG")
        buf.seek(0)
        qimage = QImage()
        qimage.loadFromData(buf.read())
        pixmap = QPixmap.fromImage(qimage)
        self.qr_label.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.qr_label.setVisible(True)
        self.qr_info.setText(
            "Scan this QR code with Google Authenticator or any TOTP app.\n"
            "You'll need the 6-digit code to log in."
        )
        self.qr_info.setVisible(True)

        self.error_label.setStyleSheet(f"color: {COLORS['green']}; font-size: 12px;")
        self.error_label.setText("Account created! Scan the QR code, then go to Login.")

        self.create_btn.setEnabled(False)
        self.create_btn.setText("Account Created ✓")
