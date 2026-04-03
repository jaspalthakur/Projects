"""
dashboard_page.py — Trading-style dashboard with KPI cards, Plotly charts,
Financial Runway, and Dynamic Envelope progress bars.
"""

import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGridLayout, QScrollArea, QProgressBar,
)
from PySide6.QtCore import Qt
from PySide6.QtWebEngineWidgets import QWebEngineView
from core.constants import COLORS, CHART_COLORS
from core.data_engine import DataEngine
from core.anomaly import detect_anomalies
from core.forecaster import forecast_spending, financial_runway
from core.dynamic_budget import EnvelopeBudget
from utils_helpers import format_currency


class DashboardPage(QWidget):
    """Main dashboard: KPI cards + charts + runway + envelopes + recent txns."""

    def __init__(self, db, user, navigate, parent=None):
        super().__init__(parent)
        self.db = db
        self.user = user
        self.navigate = navigate
        self._build_ui()

    def _build_ui(self):
        self.layout_main = QVBoxLayout(self)
        self.layout_main.setContentsMargins(28, 24, 28, 24)
        self.layout_main.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("Dashboard")
        title.setObjectName("heading")
        header.addWidget(title)
        header.addStretch()
        self.layout_main.addLayout(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        self.content = QVBoxLayout(container)
        self.content.setSpacing(16)
        scroll.setWidget(container)
        self.layout_main.addWidget(scroll)

        self.refresh()

    def refresh(self):
        while self.content.count():
            item = self.content.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

        expenses = self.db.get_all_expenses_raw(self.user["id"])
        engine = DataEngine(expenses)
        anomalies = detect_anomalies(expenses)

        total_spent = engine.total_spending()
        total_income = engine.total_income()
        monthly_spent = self.db.get_monthly_spent(self.user["id"])
        budget = self.db.get_budget(self.user["id"])
        asset_value = self.db.get_total_asset_value(self.user["id"])
        velocity = engine.spending_velocity()
        budget_remaining = budget - monthly_spent if budget else 0

        # Financial Runway
        runway = financial_runway(total_income, total_spent, asset_value, velocity)

        # ── KPI Cards ──
        kpi_row = QWidget()
        kpi_grid = QGridLayout(kpi_row)
        kpi_grid.setSpacing(12)

        net = total_income - total_spent + asset_value
        kpis = [
            ("Net Worth", format_currency(net), COLORS["green"] if net >= 0 else COLORS["red"], "💎"),
            ("Monthly Spend", format_currency(monthly_spent), COLORS["orange"], "📅"),
            ("Runway", runway["runway_label"], COLORS["cyan"], "🛫"),
            ("Anomalies", str(len(anomalies)), COLORS["red"] if anomalies else COLORS["green"], "⚠️"),
        ]
        for i, (label, value, color, icon) in enumerate(kpis):
            card = self._kpi_card(icon, label, value, color)
            kpi_grid.addWidget(card, 0, i)

        self.content.addWidget(kpi_row)

        # ── Dynamic Envelopes ──
        envelope_engine = EnvelopeBudget(self.db, self.user["id"])
        envelopes = envelope_engine.get_envelopes()
        if envelopes:
            env_title = QLabel("📊  Dynamic Envelopes")
            env_title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {COLORS['text_primary']};")
            self.content.addWidget(env_title)

            env_widget = QWidget()
            env_grid = QGridLayout(env_widget)
            env_grid.setSpacing(10)

            for idx, env in enumerate(envelopes[:8]):
                env_card = self._envelope_card(env)
                env_grid.addWidget(env_card, idx // 4, idx % 4)

            self.content.addWidget(env_widget)

        # ── Charts Row ──
        charts_widget = QWidget()
        charts_layout = QHBoxLayout(charts_widget)
        charts_layout.setSpacing(12)

        monthly = engine.monthly_totals(months=6)
        bar_html = self._build_bar_chart(monthly)
        bar_view = QWebEngineView()
        bar_view.setMinimumHeight(360)
        bar_view.setHtml(bar_html)
        charts_layout.addWidget(self._chart_card("Monthly Spending vs Income", bar_view))

        categories = engine.category_breakdown()
        pie_html = self._build_pie_chart(categories)
        pie_view = QWebEngineView()
        pie_view.setMinimumHeight(360)
        pie_view.setHtml(pie_html)
        charts_layout.addWidget(self._chart_card("Spending Distribution", pie_view))

        self.content.addWidget(charts_widget)

        # ── Forecast Chart ──
        daily = engine.daily_spending(days=90)
        if daily:
            forecast_data = forecast_spending(daily, horizon=30)
            forecast_html = self._build_forecast_chart(forecast_data)
            forecast_view = QWebEngineView()
            forecast_view.setMinimumHeight(320)
            forecast_view.setHtml(forecast_html)
            self.content.addWidget(self._chart_card("30-Day Cash Flow Forecast", forecast_view))

        # ── Recent Transactions ──
        recent_label = QLabel("Recent Transactions")
        recent_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {COLORS['text_primary']};")
        self.content.addWidget(recent_label)

        recent = self.db.get_expenses(self.user["id"], limit=10)
        if not recent:
            empty = QLabel("No transactions yet. Add your first expense!")
            empty.setObjectName("muted")
            empty.setAlignment(Qt.AlignCenter)
            self.content.addWidget(empty)
        else:
            for exp in recent:
                self.content.addWidget(self._transaction_row(exp))

        self.content.addStretch()

    # ── KPI Card ─────────────────────────────────────────────────
    def _kpi_card(self, icon, label, value, color):
        card = QFrame()
        card.setObjectName("card")
        card.setMinimumHeight(110)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(20, 18, 20, 18)

        header = QHBoxLayout()
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 20px;")
        header.addWidget(icon_lbl)
        name_lbl = QLabel(label)
        name_lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        header.addWidget(name_lbl)
        header.addStretch()
        cl.addLayout(header)

        val_lbl = QLabel(value)
        val_lbl.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {color};")
        cl.addWidget(val_lbl)
        return card

    # ── Envelope Card ────────────────────────────────────────────
    def _envelope_card(self, env: dict) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(16, 12, 16, 12)
        cl.setSpacing(6)

        cat = QLabel(env["category"])
        cat.setStyleSheet(f"font-weight: bold; font-size: 12px; color: {COLORS['text_primary']};")
        cl.addWidget(cat)

        bar = QProgressBar()
        bar.setMaximum(100)
        pct = min(int(env["pct"]), 100)
        bar.setValue(pct)
        if env["status"] == "over":
            bar.setStyleSheet(f"QProgressBar::chunk {{ background-color: {COLORS['red']}; border-radius: 6px; }}")
        elif env["status"] == "warning":
            bar.setStyleSheet(f"QProgressBar::chunk {{ background-color: {COLORS['orange']}; border-radius: 6px; }}")
        cl.addWidget(bar)

        detail = QLabel(f"{format_currency(env['spent'])} / {format_currency(env['adjusted_limit'])}")
        detail.setStyleSheet(f"font-size: 11px; color: {COLORS['text_muted']};")
        cl.addWidget(detail)
        return card

    # ── Chart Card ───────────────────────────────────────────────
    def _chart_card(self, title, web_view):
        card = QFrame()
        card.setObjectName("card")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(16, 14, 16, 14)
        lbl = QLabel(title)
        lbl.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {COLORS['text_primary']};")
        cl.addWidget(lbl)
        cl.addWidget(web_view)
        return card

    # ── Transaction Row ──────────────────────────────────────────
    def _transaction_row(self, exp):
        row = QFrame()
        row.setStyleSheet(
            f"background-color: {COLORS['bg_card']}; border-radius: 8px; padding: 8px 14px;"
        )
        rl = QHBoxLayout(row)
        rl.setContentsMargins(14, 8, 14, 8)

        cat = QLabel(exp["category"])
        cat.setStyleSheet(
            f"background-color: {COLORS['accent']}; color: white; "
            f"border-radius: 6px; padding: 3px 10px; font-size: 11px; font-weight: bold;"
        )
        cat.setFixedHeight(24)
        rl.addWidget(cat)

        desc = QLabel(exp.get("description") or "—")
        desc.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 13px;")
        rl.addWidget(desc, stretch=1)

        date = QLabel(exp["date"])
        date.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
        rl.addWidget(date)

        amt = QLabel(format_currency(exp["amount"]))
        color = COLORS["green"] if exp["category"] == "Income" else COLORS["red"]
        amt.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: bold;")
        rl.addWidget(amt)
        return row

    # ── Plotly Chart HTML ────────────────────────────────────────
    def _build_bar_chart(self, monthly):
        months = list(monthly.keys())
        spending = [monthly[m]["spending"] for m in months]
        income = [monthly[m]["income"] for m in months]
        return self._plotly_html(f"""
        Plotly.newPlot('chart', [
            {{x:{json.dumps(months)},y:{json.dumps(spending)},name:'Spending',type:'bar',
              marker:{{color:'{COLORS["red"]}',opacity:0.85}}}},
            {{x:{json.dumps(months)},y:{json.dumps(income)},name:'Income',type:'bar',
              marker:{{color:'{COLORS["green"]}',opacity:0.85}}}}
        ],{{barmode:'group',paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(0,0,0,0)',
            font:{{color:'{COLORS["text_secondary"]}',size:11}},
            margin:{{l:50,r:20,t:10,b:40}},
            xaxis:{{gridcolor:'{COLORS["border"]}'}},yaxis:{{gridcolor:'{COLORS["border"]}'}},
            legend:{{orientation:'h',y:1.1}},showlegend:true
        }},{{responsive:true,displayModeBar:false}});""")

    def _build_pie_chart(self, categories):
        labels = list(categories.keys())
        values = list(categories.values())
        colors = CHART_COLORS[:len(labels)]
        return self._plotly_html(f"""
        Plotly.newPlot('chart',[{{
            labels:{json.dumps(labels)},values:{json.dumps(values)},
            type:'pie',hole:0.45,
            marker:{{colors:{json.dumps(colors)}}},
            textinfo:'label+percent',
            textfont:{{size:10,color:'#e6edf3'}}
        }}],{{paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(0,0,0,0)',
            font:{{color:'{COLORS["text_secondary"]}',size:11}},
            margin:{{l:10,r:10,t:10,b:10}},showlegend:false
        }},{{responsive:true,displayModeBar:false}});""")

    def _build_forecast_chart(self, data):
        hist = [d for d in data if not d["is_forecast"]]
        fore = [d for d in data if d["is_forecast"]]
        hd = [d["date"] for d in hist]; hv = [d["amount"] for d in hist]
        fd = ([hd[-1]] if hd else []) + [d["date"] for d in fore]
        fv = ([hv[-1]] if hv else []) + [d["amount"] for d in fore]
        return self._plotly_html(f"""
        Plotly.newPlot('chart',[
            {{x:{json.dumps(hd)},y:{json.dumps(hv)},name:'Actual',type:'scatter',mode:'lines',
              line:{{color:'{COLORS["accent"]}',width:2}}}},
            {{x:{json.dumps(fd)},y:{json.dumps(fv)},name:'Forecast',type:'scatter',mode:'lines',
              line:{{color:'{COLORS["cyan"]}',width:2,dash:'dot'}}}}
        ],{{paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(0,0,0,0)',
            font:{{color:'{COLORS["text_secondary"]}',size:11}},
            margin:{{l:50,r:20,t:10,b:40}},
            xaxis:{{gridcolor:'{COLORS["border"]}'}},
            yaxis:{{gridcolor:'{COLORS["border"]}',title:'Daily Spend'}},
            legend:{{orientation:'h',y:1.1}},showlegend:true
        }},{{responsive:true,displayModeBar:false}});""")

    def _plotly_html(self, js):
        return f"""<!DOCTYPE html>
<html><head>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>body{{margin:0;background:transparent;overflow:hidden}}#chart{{width:100%;height:100%}}</style>
</head><body><div id="chart"></div><script>{js}</script></body></html>"""

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())
