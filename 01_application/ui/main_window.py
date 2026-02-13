"""
Main Application Window
Epoch Trading System v2.0 - XIII Trading LLC

PyQt6 main window with 8-tab layout for zone analysis.
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QFrame, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QFont

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ui.styles import DARK_STYLESHEET, COLORS
from ui.tabs.pre_market_scanner import PreMarketScannerTab
from ui.tabs.market_screener import MarketScreenerTab
from ui.tabs.dashboard import DashboardTab
from ui.tabs.bar_data import BarDataTab
from ui.tabs.raw_zones import RawZonesTab
from ui.tabs.zone_results import ZoneResultsTab
from ui.tabs.zone_analysis import ZoneAnalysisTab
from ui.tabs.database_export import DatabaseExportTab
from ui.tabs.pre_market_report import PreMarketReportTab
from ui.tabs.tradingview_export import TradingViewExportTab


class AnalysisResults(QObject):
    """Shared analysis results that tabs can access."""
    results_updated = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self._results: Dict[str, Any] = {
            "index": [],
            "custom": [],
            "analysis_date": None,
            "run_complete": False
        }

    @property
    def results(self) -> Dict[str, Any]:
        return self._results

    def update_results(self, new_results: Dict[str, Any]):
        """Update results and notify all tabs."""
        self._results = new_results
        self.results_updated.emit(new_results)

    def clear_results(self):
        """Clear all results."""
        self._results = {
            "index": [],
            "custom": [],
            "analysis_date": None,
            "run_complete": False
        }
        self.results_updated.emit(self._results)


class MainWindow(QMainWindow):
    """
    Main application window with 10 tabs for zone analysis.

    Tabs:
    1. Pre-Market Scanner - Two-phase market scanning for candidates
    2. Market Screener - Ticker input, anchor dates, run analysis
    3. Dashboard - Summary metrics
    4. Bar Data - OHLC, ATR, Camarilla, Options, HVN POCs
    5. Raw Zones - All zone candidates before filtering
    6. Zone Results - Filtered zones with tier classification
    7. Zone Analysis - Primary/Secondary setups
    8. TradingView Export - Copyable table for PineScript data
    9. Database Export - Supabase upload with terminal
    10. Pre-Market Report - Full visualization/report
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("EPOCH Trading System v2.0 - Zone Analysis")
        self.setMinimumSize(1400, 900)

        # Shared results object
        self.analysis_results = AnalysisResults()

        # Apply dark theme
        self.setStyleSheet(DARK_STYLESHEET)

        # Build UI
        self._setup_ui()

    def _setup_ui(self):
        """Set up the main UI layout."""
        # Central widget with scroll area for whole-app scrolling
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        header = self._create_header()
        main_layout.addWidget(header)

        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)

        # Create tabs
        self._create_tabs()

        main_layout.addWidget(self.tab_widget)

        # Status bar
        status_bar = self._create_status_bar()
        main_layout.addWidget(status_bar)

    def _create_header(self) -> QWidget:
        """Create the application header."""
        header = QFrame()
        header.setStyleSheet(f"background-color: {COLORS['bg_header']}; padding: 10px;")
        header.setFixedHeight(60)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 0, 20, 0)

        # Title
        title = QLabel("EPOCH ZONE ANALYSIS")
        title.setObjectName("headerLabel")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        layout.addWidget(title)

        layout.addStretch()

        # Version
        version = QLabel("v2.0 - XIII Trading LLC")
        version.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        layout.addWidget(version)

        return header

    def _create_tabs(self):
        """Create all 10 tabs."""
        # Tab 1: Pre-Market Scanner (NEW - FIRST)
        self.pre_market_scanner_tab = PreMarketScannerTab(self.analysis_results)
        self.tab_widget.addTab(
            self._wrap_in_scroll_area(self.pre_market_scanner_tab),
            "Pre-Market Scanner"
        )

        # Tab 2: Market Screener
        self.market_screener_tab = MarketScreenerTab(self.analysis_results)
        self.tab_widget.addTab(
            self._wrap_in_scroll_area(self.market_screener_tab),
            "Market Screener"
        )

        # Tab 3: Dashboard
        self.dashboard_tab = DashboardTab(self.analysis_results)
        self.tab_widget.addTab(
            self._wrap_in_scroll_area(self.dashboard_tab),
            "Dashboard"
        )

        # Tab 4: Bar Data
        self.bar_data_tab = BarDataTab(self.analysis_results)
        self.tab_widget.addTab(
            self._wrap_in_scroll_area(self.bar_data_tab),
            "Bar Data"
        )

        # Tab 5: Raw Zones
        self.raw_zones_tab = RawZonesTab(self.analysis_results)
        self.tab_widget.addTab(
            self._wrap_in_scroll_area(self.raw_zones_tab),
            "Raw Zones"
        )

        # Tab 6: Zone Results
        self.zone_results_tab = ZoneResultsTab(self.analysis_results)
        self.tab_widget.addTab(
            self._wrap_in_scroll_area(self.zone_results_tab),
            "Zone Results"
        )

        # Tab 7: Zone Analysis
        self.zone_analysis_tab = ZoneAnalysisTab(self.analysis_results)
        self.tab_widget.addTab(
            self._wrap_in_scroll_area(self.zone_analysis_tab),
            "Zone Analysis"
        )

        # Tab 8: TradingView Export
        self.tradingview_export_tab = TradingViewExportTab(self.analysis_results)
        self.tab_widget.addTab(
            self._wrap_in_scroll_area(self.tradingview_export_tab),
            "TradingView Export"
        )

        # Tab 9: Database Export
        self.database_export_tab = DatabaseExportTab(self.analysis_results)
        self.tab_widget.addTab(
            self._wrap_in_scroll_area(self.database_export_tab),
            "Database Export"
        )

        # Tab 10: Pre-Market Report
        self.pre_market_report_tab = PreMarketReportTab(self.analysis_results)
        self.tab_widget.addTab(
            self._wrap_in_scroll_area(self.pre_market_report_tab),
            "Pre-Market Report"
        )

    def _wrap_in_scroll_area(self, widget: QWidget) -> QScrollArea:
        """Wrap a widget in a scroll area for whole-tab scrolling."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setWidget(widget)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        return scroll

    def _create_status_bar(self) -> QFrame:
        """Create the status bar."""
        status_bar = QFrame()
        status_bar.setObjectName("statusBar")
        status_bar.setFixedHeight(30)

        layout = QHBoxLayout(status_bar)
        layout.setContentsMargins(20, 0, 20, 0)

        self.status_label = QLabel("Status: Ready")
        self.status_label.setObjectName("statusLabel")
        layout.addWidget(self.status_label)

        layout.addStretch()

        self.time_label = QLabel(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.time_label.setObjectName("statusLabel")
        layout.addWidget(self.time_label)

        return status_bar

    def update_status(self, message: str):
        """Update status bar message."""
        self.status_label.setText(f"Status: {message}")
        self.time_label.setText(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
