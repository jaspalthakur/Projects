"""
main.py — Entry point for Wallet Hub.
Bootstraps PySide6, applies theme, and manages auth → main window lifecycle
with a smooth splash transition.
"""

import sys
import os
from typing import Optional, cast

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QPixmap, QIcon
from core.database import Database
from ui.theme import STYLESHEET
from ui.login_window import LoginWindow
from ui.signup_window import SignupWindow
from ui.main_window import MainWindow
from core.constants import COLORS

LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "logo.png")


class SplashOverlay(QWidget):
    """Branded loading screen shown during the login → main window transition."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Wallet Hub")
        self.setFixedSize(420, 340)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setStyleSheet(
            f"background-color: {COLORS['bg_darkest']};"
            f"color: {COLORS['text_primary']};"
            "border-radius: 16px;"
        )

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(16)

        # Logo
        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignCenter)
        if os.path.exists(LOGO_PATH):
            pix = QPixmap(LOGO_PATH).scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(pix)
        else:
            logo_label.setText("💰")
            logo_label.setFont(QFont("Segoe UI Emoji", 48))
        layout.addWidget(logo_label)

        # Title
        title = QLabel("Wallet Hub")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            f"font-size: 28px; font-weight: bold; color: {COLORS['accent']};"
            "background: transparent;"
        )
        layout.addWidget(title)

        # Status
        self.status_label = QLabel("Loading your financial dashboard...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet(
            f"font-size: 13px; color: {COLORS['text_secondary']};"
            "background: transparent;"
        )
        layout.addWidget(self.status_label)

        # Dots animation
        self._dot_count = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate_dots)
        self._timer.start(400)

        # Center on screen
        self._center()

    def _center(self):
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = (geo.width() - self.width()) // 2
            y = (geo.height() - self.height()) // 2
            self.move(x, y)

    def _animate_dots(self):
        self._dot_count = (self._dot_count + 1) % 4
        dots = "." * self._dot_count
        self.status_label.setText(f"Loading your financial dashboard{dots}")


class App:
    """Application lifecycle manager."""

    def __init__(self):
        self.qapp = QApplication(sys.argv)
        self.qapp.setApplicationName("Wallet Hub")
        self.qapp.setStyleSheet(STYLESHEET)

        # Set app icon
        if os.path.exists(LOGO_PATH):
            self.qapp.setWindowIcon(QIcon(LOGO_PATH))

        self.db = Database()
        self._current_window: Optional[QWidget] = None
        self._splash: Optional[SplashOverlay] = None
        self._pending_user: Optional[dict] = None
        self._show_login()

    def _show_login(self):
        self._close_current()
        login = LoginWindow(self.db)
        login.setWindowTitle("Wallet Hub — Vault Login")
        login.resize(500, 620)
        if os.path.exists(LOGO_PATH):
            login.setWindowIcon(QIcon(LOGO_PATH))
        login.login_success.connect(self._on_auth_success)
        login.show_signup.connect(self._show_signup)
        login.show()
        self._current_window = login

    def _show_signup(self):
        self._close_current()
        signup = SignupWindow(self.db)
        signup.setWindowTitle("Wallet Hub — Create Account")
        signup.resize(500, 720)
        if os.path.exists(LOGO_PATH):
            signup.setWindowIcon(QIcon(LOGO_PATH))
        signup.signup_success.connect(self._on_auth_success)
        signup.show_login.connect(self._show_login)
        signup.show()
        self._current_window = signup

    def _on_auth_success(self, user: dict):
        """Show splash overlay, then build MainWindow in a deferred call."""
        # Hide the login/signup window (don't close yet to avoid blank gap)
        if self._current_window is not None:
            cast(QWidget, self._current_window).hide()

        # Show branded splash
        self._splash = SplashOverlay()
        if self._splash is not None:
            cast(SplashOverlay, self._splash).show()
        QApplication.processEvents()

        # Defer the heavy MainWindow construction so splash renders first
        self._pending_user = user
        QTimer.singleShot(80, self._build_main_window)

    def _build_main_window(self):
        """Construct the main window (heavy) and swap out the splash."""
        user = self._pending_user

        # Close old auth window now
        if self._current_window is not None:
            cast(QWidget, self._current_window).close()
            self._current_window = None

        # Build main window
        main = MainWindow(self.db, user)
        main.logout_signal.connect(self._show_login)
        if os.path.exists(LOGO_PATH):
            main.setWindowIcon(QIcon(LOGO_PATH))

        # Show it, then dismiss splash
        main.show()
        QApplication.processEvents()

        if self._splash is not None:
            cast(SplashOverlay, self._splash).close()
            self._splash = None

        self._current_window = main

    def _close_current(self):
        if self._current_window is not None:
            cast(QWidget, self._current_window).close()
            self._current_window = None

    def run(self) -> int:
        code = self.qapp.exec()
        self.db.close()
        return code


def main():
    app = App()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
