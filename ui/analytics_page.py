"""
analytics_page.py — Forecast visualization + anomaly alert cards.
"""

import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea,
)
from PySide6.QtCore import Qt
from PySide6.QtWebEngineWidgets import QWebEngineView
from core.constants import COLORS
from core.data_engine import DataEngine
from core.anomaly import detect_anomalies
from core.forecaster import forecast_spending
from utils_helpers import format_currency


class AnalyticsPage(QWidget):
    """Forecast chart + anomaly detection alerts."""

    def __init__(self, db, user, navigate, parent=None):
        super().__init__(parent)
        self.db = db
        self.user = user
        self.navigate = navigate
        self._build_ui()

    def _build_ui(self):
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(28, 24, 28, 24)
        self._layout.setSpacing(16)

        title = QLabel("Analytics & Insights")
        title.setObjectName("heading")
        self._layout.addWidget(title)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.content = QVBoxLayout(self.container)
        self.content.setSpacing(14)
        self.scroll.setWidget(self.container)
        self._layout.addWidget(self.scroll)

    def refresh(self):
        while self.content.count():
            item = self.content.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        expenses = self.db.get_all_expenses_raw(self.user["id"])
        engine = DataEngine(expenses)

        # ── Spending Velocity Card ──
        velocity = engine.spending_velocity()
        vel_card = QFrame()
        vel_card.setObjectName("card")
        vl = QHBoxLayout(vel_card)
        vl.setContentsMargins(24, 18, 24, 18)
        vl.addWidget(self._icon_label("⚡"))
        info_v = QVBoxLayout()
        info_v.addWidget(self._bold_label("Daily Spending Velocity"))
        info_v.addWidget(self._colored_label(
            f"{format_currency(velocity)} / day (30-day avg)", COLORS["orange"]
        ))
        vl.addLayout(info_v)
        vl.addStretch()
        projected = velocity * 30
        info_v.addWidget(self._muted_label(
            f"Projected monthly: {format_currency(projected)}"
        ))
        self.content.addWidget(vel_card)

        # ── Forecast Chart ──
        daily = engine.daily_spending(days=90)
        if daily and len(daily) >= 5:
            forecast_data = forecast_spending(daily, horizon=30)

            hist = [d for d in forecast_data if not d["is_forecast"]]
            fore = [d for d in forecast_data if d["is_forecast"]]

            forecast_view = QWebEngineView()
            forecast_view.setMinimumHeight(380)
            forecast_view.setHtml(self._forecast_html(hist, fore))

            card = QFrame()
            card.setObjectName("card")
            cl = QVBoxLayout(card)
            cl.setContentsMargins(16, 14, 16, 14)
            cl.addWidget(self._bold_label("30-Day Cash Flow Forecast"))
            cl.addWidget(forecast_view)
            self.content.addWidget(card)
        else:
            self.content.addWidget(self._info_card(
                "📈", "Forecast Unavailable",
                "Add at least 5 days of expenses to enable forecasting."
            ))

        # ── Anomaly Detection ──
        anomalies = detect_anomalies(expenses)
        anomaly_title = QLabel(f"⚠️  Anomaly Alerts ({len(anomalies)})")
        anomaly_title.setStyleSheet(
            f"font-size: 16px; font-weight: bold; color: {COLORS['text_primary']};"
        )
        self.content.addWidget(anomaly_title)

        if not anomalies:
            self.content.addWidget(self._info_card(
                "✅", "No Anomalies Detected",
                "All your transactions are within normal spending patterns."
            ))
        else:
            for a in anomalies[:20]:
                self.content.addWidget(self._anomaly_card(a))

        # ── Recurring Subscriptions ──
        recurring = engine.recurring_candidates()
        rec_title = QLabel(f"🔄  Recurring Transactions ({len(recurring)})")
        rec_title.setStyleSheet(
            f"font-size: 16px; font-weight: bold; color: {COLORS['text_primary']};"
        )
        self.content.addWidget(rec_title)

        if not recurring:
            self.content.addWidget(self._info_card(
                "📋", "No Recurring Transactions Found",
                "Recurring patterns will appear once you have enough data."
            ))
        else:
            for r in recurring[:10]:
                self.content.addWidget(self._recurring_card(r))

        self.content.addStretch()

    # ── Card Builders ────────────────────────────────────────────
    def _anomaly_card(self, a: dict) -> QFrame:
        severity = a.get("severity", "medium")
        border_color = COLORS["red"] if severity == "high" else COLORS["orange"]

        card = QFrame()
        card.setStyleSheet(
            f"background-color: {COLORS['bg_card']}; border: 1px solid {border_color}; "
            f"border-radius: 10px; padding: 12px;"
        )
        cl = QHBoxLayout(card)
        cl.setContentsMargins(16, 12, 16, 12)

        badge = "🔴" if severity == "high" else "🟡"
        cl.addWidget(self._icon_label(badge))

        info = QVBoxLayout()
        info.addWidget(self._bold_label(
            f"{a.get('category', '')} — {format_currency(a.get('amount', 0))}"
        ))
        info.addWidget(self._muted_label(
            f"Avg for category: {format_currency(a.get('category_mean', 0))} · "
            f"Z-score: {a.get('z_score', 0):.1f}σ · {a.get('date', '')}"
        ))
        desc = a.get("description") or a.get("merchant") or ""
        if desc:
            info.addWidget(self._muted_label(f'"{desc}"'))
        cl.addLayout(info)
        cl.addStretch()

        return card

    def _recurring_card(self, r: dict) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        cl = QHBoxLayout(card)
        cl.setContentsMargins(16, 12, 16, 12)

        cl.addWidget(self._icon_label("🔁"))
        info = QVBoxLayout()
        info.addWidget(self._bold_label(r.get("merchant", "Unknown")))
        info.addWidget(self._muted_label(
            f"{r.get('category', '')} · Avg {format_currency(r.get('avg_amount', 0))} · "
            f"{r.get('count', 0)} occurrences"
        ))
        cl.addLayout(info)
        cl.addStretch()

        return card

    def _info_card(self, icon: str, title: str, desc: str) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        cl = QHBoxLayout(card)
        cl.setContentsMargins(20, 16, 20, 16)
        cl.addWidget(self._icon_label(icon))
        info = QVBoxLayout()
        info.addWidget(self._bold_label(title))
        info.addWidget(self._muted_label(desc))
        cl.addLayout(info)
        cl.addStretch()
        return card

    def _icon_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("font-size: 22px;")
        lbl.setFixedWidth(36)
        return lbl

    def _bold_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(f"font-weight: bold; font-size: 13px; color: {COLORS['text_primary']};")
        return lbl

    def _muted_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(f"font-size: 12px; color: {COLORS['text_secondary']};")
        return lbl

    def _colored_label(self, text: str, color: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {color};")
        return lbl

    def _forecast_html(self, hist, fore) -> str:
        h_dates = [d["date"] for d in hist]
        h_vals = [d["amount"] for d in hist]
        f_dates = ([h_dates[-1]] if h_dates else []) + [d["date"] for d in fore]
        f_vals = ([h_vals[-1]] if h_vals else []) + [d["amount"] for d in fore]

        return f"""<!DOCTYPE html>
<html><head>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>body{{margin:0;background:transparent;overflow:hidden}}#chart{{width:100%;height:100%}}</style>
</head><body><div id="chart"></div><script>
Plotly.newPlot('chart', [
    {{x:{json.dumps(h_dates)},y:{json.dumps(h_vals)},name:'Actual',type:'scatter',mode:'lines',
      line:{{color:'{COLORS["accent"]}',width:2}}}},
    {{x:{json.dumps(f_dates)},y:{json.dumps(f_vals)},name:'Forecast',type:'scatter',mode:'lines',
      line:{{color:'{COLORS["cyan"]}',width:2,dash:'dot'}},
      fill:'tozeroy',fillcolor:'rgba(57,210,192,0.08)'}},
],{{
    paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(0,0,0,0)',
    font:{{color:'{COLORS["text_secondary"]}',size:11}},
    margin:{{l:50,r:20,t:10,b:40}},
    xaxis:{{gridcolor:'{COLORS["border"]}'}},
    yaxis:{{gridcolor:'{COLORS["border"]}',title:'Daily Spend (₹)'}},
    legend:{{orientation:'h',y:1.1}},showlegend:true
}},{{responsive:true,displayModeBar:false}});
</script></body></html>"""
