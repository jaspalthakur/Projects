# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for Wallet Hub.
Builds a one-folder distribution with all PySide6, cryptography,
pdfplumber, and yfinance dependencies bundled.
"""

from PyInstaller.utils.hooks import collect_all, collect_submodules

# ── Collect PySide6 fully (plugins, binaries, data) ──
pyside6_datas, pyside6_binaries, pyside6_hiddenimports = collect_all('PySide6')

# ── Collect other packages that have data files ──
pdfplumber_datas, pdfplumber_binaries, pdfplumber_hidden = collect_all('pdfplumber')
cryptography_datas, cryptography_binaries, cryptography_hidden = collect_all('cryptography')

# ── All hidden imports ──
hidden_imports = [
    # Application modules
    'ui', 'ui.theme', 'ui.login_window', 'ui.signup_window',
    'ui.main_window', 'ui.dashboard_page', 'ui.expenses_page',
    'ui.analytics_page', 'ui.assets_page', 'ui.import_page',
    'ui.settings_page',
    'core', 'core.database', 'core.security', 'core.encryption',
    'core.constants', 'core.categorizer', 'core.data_engine',
    'core.anomaly', 'core.forecaster', 'core.dynamic_budget',
    'core.api_client', 'core.pdf_parser',
    'utils_helpers',
    # yfinance and its dependencies
    'yfinance', 'yfinance.data',
    'appdirs', 'frozendict', 'peewee',
    'html5lib',
    'lxml', 'lxml.etree',
    # pdfplumber internals
    'pdfminer', 'pdfminer.high_level',
]
hidden_imports += pyside6_hiddenimports
hidden_imports += pdfplumber_hidden
hidden_imports += cryptography_hidden
hidden_imports += collect_submodules('yfinance')

# ── Merge data files ──
all_datas = pyside6_datas + pdfplumber_datas + cryptography_datas
all_datas += [('assets/logo.png', 'assets')]
all_binaries = pyside6_binaries + pdfplumber_binaries + cryptography_binaries

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=all_binaries,
    datas=all_datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy', 'numpy.tests'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='WalletHub',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    icon='assets/logo.png',
    console=False,              # No console window for the GUI app
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='WalletHub',
)
