"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 05: SYSTEM ANALYSIS v2.0
Main Window - PyQt6 dashboard with filter sidebar and 4 tabs
XIII Trading LLC
================================================================================
"""
import sys
from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTabWidget, QComboBox, QFrame, QScrollArea, QPushButton,
    QDateEdit, QApplication, QSplitter, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QDate
from PyQt6.QtGui import QFont
import pandas as pd

from ui.styles import COLORS, DARK_STYLESHEET

from ui.tabs.performance_tab import PerformanceTab
from ui.tabs.entry_quality_tab import EntryQualityTab
from ui.tabs.trade_management_tab import TradeManagementTab
from ui.tabs.edge_monitor_tab import EdgeMonitorTab

from data.provider import DataProvider
from config import ENTRY_MODELS, DIRECTIONS


# =============================================================================
# Background data loader
# =============================================================================
class DataLoadThread(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, provider: DataProvider, filters: dict):
        super().__init__()
        self._provider = provider
        self._filters = filters

    def run(self):
        try:
            f = self._filters
            model = f.get("model")
            direction = f.get("direction")
            ticker = f.get("ticker")
            date_from = f.get("date_from")
            date_to = f.get("date_to")

            trades = self._provider.get_trades(
                model=model, direction=direction, ticker=ticker,
                date_from=date_from, date_to=date_to
            )
            entry_indicators = self._provider.get_entry_indicators(
                model=model, direction=direction,
                date_from=date_from, date_to=date_to
            )
            m5_stops = self._provider.get_m5_atr_stops(
                model=model, direction=direction,
                date_from=date_from, date_to=date_to
            )
            m1_stops = self._provider.get_m1_atr_stops(
                model=model, direction=direction,
                date_from=date_from, date_to=date_to
            )

            # ML state (file reads, no filtering needed)
            ml_state = self._provider.get_ml_system_state()
            ml_hypotheses = self._provider.get_ml_hypothesis_tracker()
            ml_pending = self._provider.get_ml_pending_edges()

            self.finished.emit({
                "trades": trades,
                "entry_indicators": entry_indicators,
                "m5_stops": m5_stops,
                "m1_stops": m1_stops,
                "ml_state": ml_state,
                "ml_hypotheses": ml_hypotheses,
                "ml_pending": ml_pending,
            })
        except Exception as e:
            self.error.emit(str(e))


# =============================================================================
# Main Window
# =============================================================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EPOCH System Analysis v2.0 - XIII Trading LLC")
        self.setMinimumSize(1400, 900)
        self.setStyleSheet(DARK_STYLESHEET)

        self._provider = DataProvider()
        self._load_thread = None

        self._setup_ui()
        self._connect_and_load()

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------
    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        main_layout.addWidget(self._create_header())

        # Body = filters + tabs
        body = QSplitter(Qt.Orientation.Horizontal)

        # Left: filter panel
        filter_panel = self._create_filter_panel()
        body.addWidget(filter_panel)

        # Right: tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)

        self.perf_tab = PerformanceTab()
        self.entry_tab = EntryQualityTab()
        self.mgmt_tab = TradeManagementTab()
        self.edge_tab = EdgeMonitorTab()

        self.tab_widget.addTab(self._wrap_scroll(self.perf_tab), "Performance")
        self.tab_widget.addTab(self._wrap_scroll(self.entry_tab), "Entry Quality")
        self.tab_widget.addTab(self._wrap_scroll(self.mgmt_tab), "Trade Management")
        self.tab_widget.addTab(self._wrap_scroll(self.edge_tab), "Edge Monitor")

        body.addWidget(self.tab_widget)
        body.setSizes([220, 1180])

        main_layout.addWidget(body, stretch=1)

        # Status bar
        main_layout.addWidget(self._create_status_bar())

    def _create_header(self) -> QFrame:
        header = QFrame()
        header.setStyleSheet(
            f"background-color: {COLORS['bg_header']}; padding: 10px;"
        )
        header.setFixedHeight(55)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 0, 20, 0)

        title = QLabel("EPOCH SYSTEM ANALYSIS")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(title)

        layout.addStretch()

        ver = QLabel("v2.0")
        ver.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        layout.addWidget(ver)

        return header

    def _create_filter_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("sectionFrame")
        panel.setFixedWidth(220)
        panel.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        lbl = QLabel("Filters")
        lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(lbl)

        # Model filter
        layout.addWidget(QLabel("Model"))
        self.model_combo = QComboBox()
        self.model_combo.addItem("All Models", None)
        for key, desc in ENTRY_MODELS.items():
            self.model_combo.addItem(f"{key} - {desc}", key)
        layout.addWidget(self.model_combo)

        # Direction filter
        layout.addWidget(QLabel("Direction"))
        self.direction_combo = QComboBox()
        self.direction_combo.addItem("All Directions", None)
        for d in DIRECTIONS:
            self.direction_combo.addItem(d, d)
        layout.addWidget(self.direction_combo)

        # Ticker filter
        layout.addWidget(QLabel("Ticker"))
        self.ticker_combo = QComboBox()
        self.ticker_combo.addItem("All Tickers", None)
        layout.addWidget(self.ticker_combo)

        # Date from
        layout.addWidget(QLabel("Date From"))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate(2026, 1, 1))
        self.date_from.setDisplayFormat("yyyy-MM-dd")
        layout.addWidget(self.date_from)

        # Date to
        layout.addWidget(QLabel("Date To"))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setDisplayFormat("yyyy-MM-dd")
        layout.addWidget(self.date_to)

        # Refresh button
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setObjectName("primaryButton")
        self.refresh_btn.clicked.connect(self._on_refresh)
        layout.addWidget(self.refresh_btn)

        layout.addStretch()

        # Trade count label
        self.trade_count_label = QLabel("Trades: -")
        self.trade_count_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        layout.addWidget(self.trade_count_label)

        return panel

    def _create_status_bar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("statusBar")
        bar.setFixedHeight(28)

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 0, 20, 0)

        self.status_label = QLabel("Connecting...")
        self.status_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        layout.addWidget(self.status_label)

        layout.addStretch()

        self.time_label = QLabel(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.time_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        layout.addWidget(self.time_label)

        return bar

    def _wrap_scroll(self, widget: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        return scroll

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------
    def _connect_and_load(self):
        self.status_label.setText("Connecting to database...")
        if not self._provider.connect():
            self.status_label.setText("Database connection failed")
            return

        # Load tickers for filter
        try:
            tickers = self._provider.get_tickers()
            for t in tickers:
                self.ticker_combo.addItem(t, t)
        except Exception:
            pass

        # Set date range
        try:
            dr = self._provider.get_date_range()
            if dr["min_date"]:
                self.date_from.setDate(QDate(
                    dr["min_date"].year, dr["min_date"].month, dr["min_date"].day
                ))
            if dr["max_date"]:
                self.date_to.setDate(QDate(
                    dr["max_date"].year, dr["max_date"].month, dr["max_date"].day
                ))
        except Exception:
            pass

        self._on_refresh()

    def _get_filters(self) -> dict:
        model = self.model_combo.currentData()
        direction = self.direction_combo.currentData()
        ticker = self.ticker_combo.currentData()

        qd_from = self.date_from.date()
        qd_to = self.date_to.date()

        from datetime import date
        return {
            "model": model,
            "direction": direction,
            "ticker": ticker,
            "date_from": date(qd_from.year(), qd_from.month(), qd_from.day()),
            "date_to": date(qd_to.year(), qd_to.month(), qd_to.day()),
        }

    def _on_refresh(self):
        self.refresh_btn.setEnabled(False)
        self.status_label.setText("Loading data...")

        self._load_thread = DataLoadThread(self._provider, self._get_filters())
        self._load_thread.finished.connect(self._on_data_loaded)
        self._load_thread.error.connect(self._on_load_error)
        self._load_thread.start()

    def _on_data_loaded(self, data: dict):
        self.refresh_btn.setEnabled(True)

        trades = data["trades"]
        count = len(trades)
        self.trade_count_label.setText(f"Trades: {count:,}")
        self.status_label.setText(f"Loaded {count:,} trades")
        self.time_label.setText(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        # Refresh all tabs
        self.perf_tab.refresh(trades)
        self.entry_tab.refresh(data["entry_indicators"])
        self.mgmt_tab.refresh(trades, data["m5_stops"], data["m1_stops"])
        self.edge_tab.refresh(data["ml_state"], data["ml_hypotheses"], data["ml_pending"])

    def _on_load_error(self, error_msg: str):
        self.refresh_btn.setEnabled(True)
        self.status_label.setText(f"Error: {error_msg}")

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------
    def closeEvent(self, event):
        self._provider.close()
        super().closeEvent(event)
