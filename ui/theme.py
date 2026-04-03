"""
theme.py — Dark trading-terminal QSS stylesheet and helper factories for PySide6.
"""

from core.constants import COLORS

# ── Master Stylesheet ─────────────────────────────────────────────

STYLESHEET = f"""
/* ─── Base ────────────────────────────────────────────────── */
QMainWindow, QDialog, QWidget#central {{
    background-color: {COLORS['bg_darkest']};
    color: {COLORS['text_primary']};
    font-family: 'Segoe UI', 'Inter', sans-serif;
    font-size: 13px;
}}

/* ─── Labels ──────────────────────────────────────────────── */
QLabel {{
    color: {COLORS['text_primary']};
    background: transparent;
}}
QLabel#heading {{
    font-size: 22px;
    font-weight: bold;
}}
QLabel#subheading {{
    font-size: 14px;
    color: {COLORS['text_secondary']};
}}
QLabel#muted {{
    color: {COLORS['text_muted']};
    font-size: 12px;
}}
QLabel#kpi_value {{
    font-size: 26px;
    font-weight: bold;
}}
QLabel#error {{
    color: {COLORS['red']};
    font-size: 12px;
}}

/* ─── Inputs ──────────────────────────────────────────────── */
QLineEdit, QTextEdit, QDateEdit {{
    background-color: {COLORS['bg_surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 8px 12px;
    color: {COLORS['text_primary']};
    font-size: 13px;
    selection-background-color: {COLORS['accent']};
}}
QLineEdit:focus, QTextEdit:focus, QDateEdit:focus {{
    border-color: {COLORS['accent']};
}}
QLineEdit:disabled {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text_muted']};
}}

/* ─── Buttons ─────────────────────────────────────────────── */
QPushButton {{
    background-color: {COLORS['accent']};
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: bold;
}}
QPushButton:hover {{
    background-color: {COLORS['accent_hover']};
}}
QPushButton:pressed {{
    background-color: #4a42b5;
}}
QPushButton#secondary {{
    background-color: {COLORS['bg_surface']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
}}
QPushButton#secondary:hover {{
    background-color: {COLORS['bg_hover']};
}}
QPushButton#danger {{
    background-color: {COLORS['red']};
}}
QPushButton#danger:hover {{
    background-color: {COLORS['red_dim']};
}}
QPushButton#success {{
    background-color: {COLORS['green']};
}}
QPushButton#success:hover {{
    background-color: {COLORS['green_dim']};
}}
QPushButton#nav {{
    background-color: transparent;
    color: {COLORS['text_secondary']};
    text-align: left;
    padding: 12px 18px;
    border-radius: 10px;
    font-weight: normal;
    font-size: 14px;
}}
QPushButton#nav:hover {{
    background-color: {COLORS['bg_surface']};
    color: {COLORS['text_primary']};
}}
QPushButton#nav:checked {{
    background-color: {COLORS['accent']};
    color: white;
    font-weight: bold;
}}

/* ─── ComboBox ────────────────────────────────────────────── */
QComboBox {{
    background-color: {COLORS['bg_surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 8px 12px;
    color: {COLORS['text_primary']};
    font-size: 13px;
}}
QComboBox::drop-down {{
    border: none;
    width: 30px;
}}
QComboBox QAbstractItemView {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    color: {COLORS['text_primary']};
    selection-background-color: {COLORS['accent']};
    padding: 4px;
}}

/* ─── Tables ──────────────────────────────────────────────── */
QTableWidget {{
    background-color: {COLORS['bg_card']};
    alternate-background-color: {COLORS['bg_surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    gridline-color: {COLORS['border']};
    color: {COLORS['text_primary']};
    font-size: 12px;
}}
QTableWidget::item {{
    padding: 6px 10px;
}}
QTableWidget::item:selected {{
    background-color: {COLORS['accent']};
    color: white;
}}
QHeaderView::section {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text_secondary']};
    border: none;
    border-bottom: 1px solid {COLORS['border']};
    padding: 8px 10px;
    font-weight: bold;
    font-size: 11px;
    text-transform: uppercase;
}}

/* ─── ScrollBar ───────────────────────────────────────────── */
QScrollBar:vertical {{
    background: {COLORS['bg_darkest']};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {COLORS['border']};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {COLORS['text_muted']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

/* ─── Cards ───────────────────────────────────────────────── */
QFrame#card {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
}}
QFrame#card_accent {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['accent']};
    border-radius: 12px;
}}

/* ─── Sidebar ─────────────────────────────────────────────── */
QFrame#sidebar {{
    background-color: {COLORS['bg_dark']};
    border-right: 1px solid {COLORS['border']};
}}

/* ─── ProgressBar ─────────────────────────────────────────── */
QProgressBar {{
    background-color: {COLORS['bg_surface']};
    border: none;
    border-radius: 6px;
    height: 12px;
    text-align: center;
    font-size: 10px;
    color: {COLORS['text_primary']};
}}
QProgressBar::chunk {{
    background-color: {COLORS['accent']};
    border-radius: 6px;
}}

/* ─── Tab Widget ──────────────────────────────────────────── */
QTabWidget::pane {{
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    background-color: {COLORS['bg_card']};
}}
QTabBar::tab {{
    background-color: {COLORS['bg_surface']};
    color: {COLORS['text_secondary']};
    padding: 10px 20px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-weight: bold;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background-color: {COLORS['bg_card']};
    color: {COLORS['accent']};
}}

/* ─── MessageBox ──────────────────────────────────────────── */
QMessageBox {{
    background-color: {COLORS['bg_card']};
}}
QMessageBox QLabel {{
    color: {COLORS['text_primary']};
}}
"""
