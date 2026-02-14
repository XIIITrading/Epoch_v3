"""
================================================================================
EPOCH TRADING SYSTEM - System Analysis Dashboard
XIII Trading LLC
================================================================================

Main window with tabbed layout for system analysis reports.

Tabs:
    - Overview: All data (no date filter)
    - Daily: Anchor date only (single day)
    - Weekly: Anchor date - 6 days to anchor date (7-day window)
    - Monthly: Anchor date - 29 days to anchor date (30-day window)

Anchor date defaults to today (ET timezone) and can be changed
for weekend/holiday use.

Data is loaded from Supabase via DataProvider on Refresh.

================================================================================
"""

import sys
from datetime import datetime, date, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QTabWidget,
    QProgressBar, QApplication, QDateEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QDate
from PyQt6.QtGui import QFont

from styles import DARK_STYLESHEET, COLORS
from data_provider import DataProvider
from tabs.overview_tab import OverviewTab
from tabs.daily_tab import DailyTab
from tabs.weekly_tab import WeeklyTab
from tabs.monthly_tab import MonthlyTab


# ============================================================================
# Background data loading thread
# ============================================================================

class DataLoadThread(QThread):
    """Background thread for loading data from Supabase for all 4 tabs."""

    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, provider_overview, provider_daily,
                 provider_weekly, provider_monthly, anchor_date):
        super().__init__()
        self._providers = {
            'overview': provider_overview,
            'daily': provider_daily,
            'weekly': provider_weekly,
            'monthly': provider_monthly,
        }
        self._anchor = anchor_date  # Python date object

    def run(self):
        try:
            results = {}

            # Overview: no date filter (all data)
            results['overview'] = self._providers['overview'].refresh()

            # Daily: anchor date only
            results['daily'] = self._providers['daily'].refresh(
                date_from=self._anchor, date_to=self._anchor
            )

            # Weekly: anchor - 6 days to anchor (7-day window)
            week_start = self._anchor - timedelta(days=6)
            results['weekly'] = self._providers['weekly'].refresh(
                date_from=week_start, date_to=self._anchor
            )

            # Monthly: anchor - 29 days to anchor (30-day window)
            month_start = self._anchor - timedelta(days=29)
            results['monthly'] = self._providers['monthly'].refresh(
                date_from=month_start, date_to=self._anchor
            )

            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))


# ============================================================================
# Main Window
# ============================================================================

class ReportDashboardWindow(QMainWindow):
    """
    System Analysis Dashboard - Tabbed PyQt6 application.

    Features:
        - Header with title, anchor date selector, and Refresh button
        - Tabbed content area (Overview, Daily, Weekly, Monthly)
        - Status bar with trade count and last refresh time
        - Background data loading from Supabase
        - 4 independent DataProvider instances (one per tab)
        - Conditional coloring on all tables
    """

    def __init__(self):
        super().__init__()

        # One DataProvider per tab - each caches its own date-filtered data
        self._provider_overview = DataProvider()
        self._provider_daily = DataProvider()
        self._provider_weekly = DataProvider()
        self._provider_monthly = DataProvider()

        self._load_thread: Optional[DataLoadThread] = None

        self._setup_ui()

    def _setup_ui(self):
        """Build the main window layout."""
        self.setWindowTitle("EPOCH SYSTEM ANALYSIS")
        self.setMinimumSize(1300, 900)
        self.resize(1500, 1050)
        self.setStyleSheet(DARK_STYLESHEET)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(15, 15, 15, 10)
        main_layout.setSpacing(10)

        # Header
        header = self._create_header()
        main_layout.addLayout(header)

        # Tab widget
        self._tabs = self._create_tabs()
        main_layout.addWidget(self._tabs, stretch=1)

        # Status bar
        status = self._create_status_bar()
        main_layout.addWidget(status)

    def _create_header(self) -> QHBoxLayout:
        """Create header with title, anchor date, and refresh button."""
        layout = QHBoxLayout()

        # Title
        title = QLabel("EPOCH SYSTEM ANALYSIS")
        title.setObjectName("headerLabel")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        layout.addWidget(title)

        # Version
        version = QLabel("Dashboard v1.0")
        version.setStyleSheet(f"color: {COLORS['text_muted']}; padding-top: 6px;")
        version.setFont(QFont("Consolas", 11))
        layout.addWidget(version)

        layout.addStretch()

        # Anchor date selector
        anchor_label = QLabel("Anchor Date:")
        anchor_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        anchor_label.setFont(QFont("Consolas", 10))
        layout.addWidget(anchor_label)

        self._anchor_date = QDateEdit()
        self._anchor_date.setCalendarPopup(True)
        self._anchor_date.setDisplayFormat("yyyy-MM-dd")
        self._anchor_date.setFixedWidth(150)
        self._anchor_date.setFont(QFont("Consolas", 10))

        # Default to today in ET timezone
        et_today = datetime.now(ZoneInfo("America/New_York")).date()
        self._anchor_date.setDate(QDate(et_today.year, et_today.month, et_today.day))
        layout.addWidget(self._anchor_date)

        layout.addSpacing(15)

        # Progress indicator (hidden by default)
        self._progress = QProgressBar()
        self._progress.setMinimum(0)
        self._progress.setMaximum(0)  # Indeterminate
        self._progress.setFixedSize(160, 22)
        self._progress.hide()
        layout.addWidget(self._progress)

        layout.addSpacing(15)

        # Refresh button
        self._refresh_btn = QPushButton("REFRESH")
        self._refresh_btn.setObjectName("refreshButton")
        self._refresh_btn.clicked.connect(self._on_refresh)
        layout.addWidget(self._refresh_btn)

        return layout

    def _create_tabs(self) -> QTabWidget:
        """Create the tabbed content area."""
        tabs = QTabWidget()

        self._overview_tab = OverviewTab()
        self._daily_tab = DailyTab()
        self._weekly_tab = WeeklyTab()
        self._monthly_tab = MonthlyTab()

        tabs.addTab(self._overview_tab, "Overview")
        tabs.addTab(self._daily_tab, "Daily")
        tabs.addTab(self._weekly_tab, "Weekly")
        tabs.addTab(self._monthly_tab, "Monthly")

        return tabs

    def _create_status_bar(self) -> QFrame:
        """Create the status bar at the bottom."""
        frame = QFrame()
        frame.setObjectName("statusBar")
        frame.setFixedHeight(32)

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(15, 4, 15, 4)

        self._status_label = QLabel("Status: Ready - Click REFRESH to load data")
        self._status_label.setObjectName("statusLabel")
        self._status_label.setFont(QFont("Consolas", 9))

        self._time_label = QLabel("")
        self._time_label.setObjectName("statusLabel")
        self._time_label.setFont(QFont("Consolas", 9))

        layout.addWidget(self._status_label)
        layout.addStretch()
        layout.addWidget(self._time_label)

        return frame

    # ========================================================================
    # Data loading
    # ========================================================================

    def _get_anchor_date(self) -> date:
        """Read the anchor date from the QDateEdit widget."""
        qdate = self._anchor_date.date()
        return date(qdate.year(), qdate.month(), qdate.day())

    @pyqtSlot()
    def _on_refresh(self):
        """Handle Refresh button click - load data in background thread."""
        if self._load_thread and self._load_thread.isRunning():
            return

        self._refresh_btn.setEnabled(False)
        self._anchor_date.setEnabled(False)
        self._progress.show()
        self._status_label.setText("Status: Loading data from Supabase...")
        self._status_label.setStyleSheet(f"color: {COLORS['status_running']};")

        # Force UI update before thread starts
        QApplication.processEvents()

        anchor = self._get_anchor_date()

        self._load_thread = DataLoadThread(
            self._provider_overview,
            self._provider_daily,
            self._provider_weekly,
            self._provider_monthly,
            anchor
        )
        self._load_thread.finished.connect(self._on_data_loaded)
        self._load_thread.error.connect(self._on_data_error)
        self._load_thread.start()

    @pyqtSlot(dict)
    def _on_data_loaded(self, results: dict):
        """Handle successful data load - dispatch to all tabs."""
        self._refresh_btn.setEnabled(True)
        self._anchor_date.setEnabled(True)
        self._progress.hide()

        overview_result = results.get('overview', {})
        if not overview_result.get('success'):
            self._on_data_error(overview_result.get('error', 'Unknown error'))
            return

        now = datetime.now().strftime("%H:%M:%S")
        self._time_label.setText(f"Last refresh: {now}")

        # Status bar shows overview (all data) counts
        trades = overview_result.get('unique_trades', 0)
        records = overview_result.get('stop_records', 0)
        mfe_mae = overview_result.get('mfe_mae_records', 0)
        self._status_label.setText(
            f"Status: Loaded {trades:,} trades | "
            f"{records:,} stop records | "
            f"{mfe_mae:,} MFE/MAE records"
        )
        self._status_label.setStyleSheet(f"color: {COLORS['status_complete']};")

        # Read anchor date for labels
        anchor = self._get_anchor_date()

        # Update Overview (no date label)
        self._overview_tab.update_data(self._provider_overview)

        # Update Daily
        daily_label = anchor.strftime("%Y-%m-%d")
        self._daily_tab.update_data(self._provider_daily, date_label=daily_label)

        # Update Weekly
        week_start = anchor - timedelta(days=6)
        weekly_label = f"{week_start.strftime('%Y-%m-%d')} to {anchor.strftime('%Y-%m-%d')}"
        self._weekly_tab.update_data(self._provider_weekly, date_label=weekly_label)

        # Update Monthly
        month_start = anchor - timedelta(days=29)
        monthly_label = f"{month_start.strftime('%Y-%m-%d')} to {anchor.strftime('%Y-%m-%d')}"
        self._monthly_tab.update_data(self._provider_monthly, date_label=monthly_label)

    @pyqtSlot(str)
    def _on_data_error(self, error_msg: str):
        """Handle data loading error."""
        self._refresh_btn.setEnabled(True)
        self._anchor_date.setEnabled(True)
        self._progress.hide()

        self._status_label.setText(f"Status: Error - {error_msg}")
        self._status_label.setStyleSheet(f"color: {COLORS['status_error']};")

    def closeEvent(self, event):
        """Handle window close - wait for thread if running."""
        if self._load_thread and self._load_thread.isRunning():
            self._load_thread.quit()
            self._load_thread.wait(3000)
        event.accept()
