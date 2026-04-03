"""
import_page.py — PDF/CSV bank statement importer with drag-and-drop
and auto-categorization preview.
"""

import os
import polars as pl
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton,
    QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QMessageBox,
)
from PySide6.QtCore import Qt
from core.constants import COLORS, CATEGORIES
from core.categorizer import auto_categorize


class DropZone(QFrame):
    """Frame that accepts drag-and-drop files."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._callback = None

    def set_callback(self, cb):
        self._callback = cb

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet(
                f"background-color: {COLORS['bg_surface']}; border: 2px dashed {COLORS['accent']}; "
                f"border-radius: 12px;"
            )

    def dragLeaveEvent(self, event):
        self.setStyleSheet(
            f"background-color: {COLORS['bg_card']}; border: 2px dashed {COLORS['border']}; "
            f"border-radius: 12px;"
        )

    def dropEvent(self, event):
        self.setStyleSheet(
            f"background-color: {COLORS['bg_card']}; border: 2px dashed {COLORS['border']}; "
            f"border-radius: 12px;"
        )
        urls = event.mimeData().urls()
        if urls and self._callback:
            path = urls[0].toLocalFile()
            self._callback(path)


class ImportPage(QWidget):
    """PDF/CSV bank statement importer with drag-and-drop + auto-categorization."""

    def __init__(self, db, user, navigate, parent=None):
        super().__init__(parent)
        self.db = db
        self.user = user
        self.navigate = navigate
        self._pending_rows: list[dict] = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        # ── Header ──
        header = QHBoxLayout()
        title = QLabel("Import Bank Statement")
        title.setObjectName("heading")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # ── Drop Zone ──
        self.drop_zone = DropZone()
        self.drop_zone.setObjectName("card")
        self.drop_zone.setMinimumHeight(140)
        self.drop_zone.setStyleSheet(
            f"background-color: {COLORS['bg_card']}; border: 2px dashed {COLORS['border']}; "
            f"border-radius: 12px;"
        )
        self.drop_zone.set_callback(self._process_file)

        dz_layout = QVBoxLayout(self.drop_zone)
        dz_layout.setAlignment(Qt.AlignCenter)
        dz_layout.setSpacing(8)

        emoji = QLabel("📥")
        emoji.setStyleSheet("font-size: 32px;")
        emoji.setAlignment(Qt.AlignCenter)
        dz_layout.addWidget(emoji)

        label = QLabel("Drag & Drop a PDF or CSV file here")
        label.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {COLORS['text_primary']};")
        label.setAlignment(Qt.AlignCenter)
        dz_layout.addWidget(label)

        sub = QLabel("Or click Browse to select a file  •  Supported: .csv, .pdf")
        sub.setObjectName("muted")
        sub.setAlignment(Qt.AlignCenter)
        dz_layout.addWidget(sub)

        browse_btn = QPushButton("📂  Browse Files")
        browse_btn.setMinimumHeight(38)
        browse_btn.setFixedWidth(160)
        browse_btn.setCursor(Qt.PointingHandCursor)
        browse_btn.clicked.connect(self._browse)
        dz_layout.addWidget(browse_btn, alignment=Qt.AlignCenter)

        layout.addWidget(self.drop_zone)

        # File info
        self.file_label = QLabel("")
        self.file_label.setObjectName("subheading")
        layout.addWidget(self.file_label)

        # ── Preview Table ──
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Date", "Description", "Amount", "Auto-Category", "Override"])
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.Fixed)
        self.table.setColumnWidth(4, 170)
        layout.addWidget(self.table)

        # ── Import button row ──
        bot = QHBoxLayout()
        bot.addStretch()
        self.count_label = QLabel("")
        self.count_label.setObjectName("subheading")
        bot.addWidget(self.count_label)

        self.import_btn = QPushButton("✅  Import All")
        self.import_btn.setObjectName("success")
        self.import_btn.setMinimumHeight(42)
        self.import_btn.setFixedWidth(160)
        self.import_btn.setCursor(Qt.PointingHandCursor)
        self.import_btn.setEnabled(False)
        self.import_btn.clicked.connect(self._import_all)
        bot.addWidget(self.import_btn)
        layout.addLayout(bot)

    def refresh(self):
        pass

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Statement", "",
            "Bank Statements (*.csv *.pdf);;CSV Files (*.csv);;PDF Files (*.pdf)"
        )
        if path:
            self._process_file(path)

    def _process_file(self, path: str):
        ext = os.path.splitext(path)[1].lower()
        self.file_label.setText(f"📄 {os.path.basename(path)}")

        if ext == ".pdf":
            self._parse_pdf(path)
        elif ext == ".csv":
            self._parse_csv(path)
        else:
            QMessageBox.warning(self, "Unsupported", f"File type '{ext}' is not supported.")

    def _parse_pdf(self, path: str):
        try:
            from core.pdf_parser import parse_bank_pdf
            rows = parse_bank_pdf(path)
            if not rows:
                QMessageBox.warning(self, "No Data",
                                    "Could not extract transactions from this PDF.\n"
                                    "The PDF may use a non-standard format.")
                return
            self._populate_table(rows)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"PDF parsing failed:\n{e}")

    def _parse_csv(self, path: str):
        try:
            df = pl.read_csv(path, infer_schema_length=0)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to read CSV:\n{e}")
            return

        cols_lower = {c.lower().strip(): c for c in df.columns}

        date_col = None
        for k in ["date", "transaction date", "txn date", "trans date", "posting date"]:
            if k in cols_lower:
                date_col = cols_lower[k]; break

        desc_col = None
        for k in ["description", "merchant", "narration", "details", "memo", "payee"]:
            if k in cols_lower:
                desc_col = cols_lower[k]; break

        amount_col = None
        for k in ["amount", "debit", "transaction amount", "value", "withdrawal"]:
            if k in cols_lower:
                amount_col = cols_lower[k]; break

        if not date_col or not amount_col:
            QMessageBox.warning(self, "Column Mismatch",
                                f"Could not find Date/Amount columns.\nFound: {list(df.columns)}")
            return

        if not desc_col:
            desc_col = date_col

        raw = df.select([date_col, desc_col, amount_col]).to_dicts()
        rows = []
        for row in raw:
            desc_val = str(row[desc_col]).strip() if desc_col != date_col else ""
            try:
                amt = abs(float(str(row[amount_col]).replace(",", "").replace("$", "").replace("₹", "")))
            except ValueError:
                amt = 0.0
            rows.append({
                "date": str(row[date_col]).strip(),
                "description": desc_val,
                "amount": amt,
            })

        self._populate_table(rows)

    def _populate_table(self, rows: list[dict]):
        self._pending_rows.clear()
        self.table.setRowCount(len(rows))

        for i, row in enumerate(rows):
            category = auto_categorize(row["description"])
            self._pending_rows.append({
                "date": row["date"], "desc": row["description"],
                "amount": row["amount"], "category": category,
            })

            self.table.setItem(i, 0, QTableWidgetItem(row["date"]))
            self.table.setItem(i, 1, QTableWidgetItem(row["description"]))
            self.table.setItem(i, 2, QTableWidgetItem(f"₹{row['amount']:,.2f}"))
            self.table.setItem(i, 3, QTableWidgetItem(category))

            combo = QComboBox()
            combo.addItems(CATEGORIES)
            combo.setCurrentText(category)
            combo.currentTextChanged.connect(lambda text, idx=i: self._override_cat(idx, text))
            self.table.setCellWidget(i, 4, combo)

        self.count_label.setText(f"{len(rows)} transactions ready")
        self.import_btn.setEnabled(True)

    def _override_cat(self, idx: int, cat: str):
        if idx < len(self._pending_rows):
            self._pending_rows[idx]["category"] = cat

    def _import_all(self):
        if not self._pending_rows:
            return

        tuples = []
        for r in self._pending_rows:
            tuples.append((
                self.user["id"], r["date"], r["amount"],
                r["category"], r["desc"], "", 0,
            ))

        count = self.db.bulk_add_expenses(tuples)
        QMessageBox.information(self, "Success", f"Imported {count} transactions!")
        self._pending_rows.clear()
        self.table.setRowCount(0)
        self.import_btn.setEnabled(False)
        self.count_label.setText("")
