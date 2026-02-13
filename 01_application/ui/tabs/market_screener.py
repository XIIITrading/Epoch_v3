"""
Market Screener Tab
Epoch Trading System v2.0 - XIII Trading LLC

Tab for ticker input, anchor date selection, and running analysis.

Supports per-ticker anchor dates in format:
  INTC,2025-12-24
  AMD,2025-09-18
  TSLA

Analysis Date + Market Mode determines the cutoff timestamp for data.
"""

from datetime import datetime, date, timedelta, time, timezone
from zoneinfo import ZoneInfo
from typing import Dict, Any, List, Optional, Tuple

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QDateEdit,
    QFrame, QProgressBar, QTextEdit, QGroupBox, QSpinBox,
    QMessageBox, QPlainTextEdit
)
from PyQt6.QtCore import Qt, QDate, QThread, pyqtSignal
from PyQt6.QtGui import QFont

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ui.tabs.base_tab import BaseTab
from ui.styles import COLORS
from config import INDEX_TICKERS, MAX_TICKERS, ANCHOR_PRESETS


# Market time cutoffs (Eastern Time)
# These cutoffs ensure the last COMPLETE H1 bar is:
# - Pre-Market: 08:00-09:00 ET (cutoff at 09:00 excludes the 09:00-10:00 bar)
# - Post-Market: 14:00-15:00 ET (cutoff at 15:00 excludes the 15:00-16:00 bar)
# - Live: Uses current time rounded to previous minute (handled dynamically)
MARKET_CUTOFFS = {
    "Live": None,  # Dynamic - uses current time rounded to previous minute
    "Pre-Market": time(9, 0),    # Last complete H1 bar: 08:00-09:00 ET
    "Post-Market": time(15, 0),  # Last complete H1 bar: 14:00-15:00 ET
}


class AnalysisWorker(QThread):
    """Worker thread for running analysis."""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, ticker_inputs: List[Dict], analysis_date: date,
                 market_mode: str, end_timestamp: Optional[datetime] = None):
        super().__init__()
        self.ticker_inputs = ticker_inputs
        self.analysis_date = analysis_date
        self.market_mode = market_mode
        self.end_timestamp = end_timestamp
        self._is_cancelled = False

    def run(self):
        """Run the analysis pipeline."""
        try:
            from core.pipeline_runner import PipelineRunner

            def progress_callback(percent: int, message: str):
                if not self._is_cancelled:
                    self.progress.emit(percent, message)

            runner = PipelineRunner(progress_callback=progress_callback)
            results = runner.run(
                self.ticker_inputs,
                self.analysis_date,
                end_timestamp=self.end_timestamp
            )

            if not self._is_cancelled:
                self.finished.emit(results)

        except Exception as e:
            if not self._is_cancelled:
                self.error.emit(str(e))

    def cancel(self):
        """Cancel the analysis."""
        self._is_cancelled = True


class MarketScreenerTab(BaseTab):
    """
    Market Screener Tab

    Features:
    - Ticker input with optional per-ticker anchor dates (TICKER,YYYY-MM-DD)
    - Default anchor date preset for tickers without custom dates
    - Analysis date selection (historical or current)
    - Market mode (Live, Pre-Market, Post-Market)
    - Run/Stop controls
    - Progress tracking
    - Console output
    """

    def __init__(self, analysis_results):
        self._worker: Optional[AnalysisWorker] = None
        super().__init__(analysis_results)

    def _setup_ui(self):
        """Set up the tab UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Title
        title = QLabel("MARKET SCREENER")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # Input section
        input_section = self._create_input_section()
        layout.addWidget(input_section)

        # Control section
        control_section = self._create_control_section()
        layout.addWidget(control_section)

        # Progress section
        progress_section = self._create_progress_section()
        layout.addWidget(progress_section)

        # Console output
        console_section = self._create_console_section()
        layout.addWidget(console_section)

        layout.addStretch()

    def _create_input_section(self) -> QFrame:
        """Create the ticker and date input section."""
        frame = QFrame()
        frame.setObjectName("sectionFrame")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Section title
        title = QLabel("ANALYSIS INPUTS")
        title.setObjectName("sectionLabel")
        title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        layout.addWidget(title)

        # Ticker input - multi-line for per-ticker dates
        ticker_label = QLabel("Tickers (one per line, optional anchor date: TICKER,YYYY-MM-DD):")
        layout.addWidget(ticker_label)

        self.ticker_input = QPlainTextEdit()
        self.ticker_input.setPlaceholderText(
            "INTC,2025-12-24\n"
            "AMD,2025-09-18\n"
            "TSLA\n"
            "AMZN,2025-10-17\n"
            "(Tickers without dates use Default Anchor below)"
        )
        self.ticker_input.setMinimumHeight(120)
        self.ticker_input.setMaximumHeight(180)
        layout.addWidget(self.ticker_input)

        # Grid layout for date inputs
        grid = QGridLayout()
        grid.setSpacing(12)

        # Row 0: Default anchor preset (for tickers without custom dates)
        grid.addWidget(QLabel("Default Anchor:"), 0, 0)
        self.anchor_preset = QComboBox()
        for key, value in ANCHOR_PRESETS.items():
            self.anchor_preset.addItem(value, key)
        self.anchor_preset.setCurrentIndex(3)  # Prior Month default
        self.anchor_preset.currentIndexChanged.connect(self._on_anchor_preset_changed)
        grid.addWidget(self.anchor_preset, 0, 1)

        # Row 0: Custom default anchor date
        grid.addWidget(QLabel("Custom Default:"), 0, 2)
        self.anchor_date = QDateEdit()
        self.anchor_date.setCalendarPopup(True)
        self.anchor_date.setDate(QDate.currentDate().addMonths(-1))
        self.anchor_date.setEnabled(False)  # Disabled unless custom preset
        grid.addWidget(self.anchor_date, 0, 3)

        # Row 1: Analysis date
        grid.addWidget(QLabel("Analysis Date:"), 1, 0)
        self.analysis_date = QDateEdit()
        self.analysis_date.setCalendarPopup(True)
        self.analysis_date.setDate(QDate.currentDate())
        self.analysis_date.dateChanged.connect(self._on_analysis_date_changed)
        grid.addWidget(self.analysis_date, 1, 1)

        # Row 1: Market mode
        grid.addWidget(QLabel("Market Mode:"), 1, 2)
        self.market_mode = QComboBox()
        self.market_mode.addItems(["Live", "Pre-Market", "Post-Market"])
        self.market_mode.setCurrentIndex(0)
        self.market_mode.currentIndexChanged.connect(self._on_market_mode_changed)
        grid.addWidget(self.market_mode, 1, 3)

        layout.addLayout(grid)

        # Info labels
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        self.cutoff_label = QLabel("Data cutoff: Using all available data")
        self.cutoff_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10pt;")
        info_layout.addWidget(self.cutoff_label)

        index_label = QLabel(f"Index tickers (auto-added with default anchor): {', '.join(INDEX_TICKERS)}")
        index_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10pt;")
        info_layout.addWidget(index_label)

        layout.addLayout(info_layout)

        return frame

    def _create_control_section(self) -> QFrame:
        """Create the run/stop control section."""
        frame = QFrame()
        frame.setObjectName("sectionFrame")

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(16)

        # Run button
        self.run_button = QPushButton("RUN ANALYSIS")
        self.run_button.setObjectName("runButton")
        self.run_button.clicked.connect(self._on_run_clicked)
        layout.addWidget(self.run_button)

        # Stop button
        self.stop_button = QPushButton("STOP")
        self.stop_button.setObjectName("stopButton")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self._on_stop_clicked)
        layout.addWidget(self.stop_button)

        # Clear button
        self.clear_button = QPushButton("CLEAR")
        self.clear_button.setObjectName("clearButton")
        self.clear_button.clicked.connect(self._on_clear_clicked)
        layout.addWidget(self.clear_button)

        layout.addStretch()

        # Status indicator
        self.status_indicator = QLabel("Ready")
        self.status_indicator.setStyleSheet(f"color: {COLORS['status_ready']}; font-weight: bold;")
        layout.addWidget(self.status_indicator)

        return frame

    def _create_progress_section(self) -> QFrame:
        """Create the progress tracking section."""
        frame = QFrame()
        frame.setObjectName("sectionFrame")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p% - %v/%m")
        layout.addWidget(self.progress_bar)

        # Progress message
        self.progress_label = QLabel("Waiting to start...")
        self.progress_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(self.progress_label)

        return frame

    def _create_console_section(self) -> QFrame:
        """Create the console output section."""
        frame = QFrame()
        frame.setObjectName("terminalFrame")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QHBoxLayout()
        header.setContentsMargins(12, 8, 12, 8)

        header_label = QLabel("CONSOLE OUTPUT")
        header_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-weight: bold;")
        header.addWidget(header_label)

        header.addStretch()

        clear_console_btn = QPushButton("Clear")
        clear_console_btn.setFixedSize(60, 24)
        clear_console_btn.clicked.connect(self._clear_console)
        header.addWidget(clear_console_btn)

        layout.addLayout(header)

        # Console text
        self.console = QTextEdit()
        self.console.setObjectName("terminalOutput")
        self.console.setReadOnly(True)
        self.console.setMinimumHeight(200)
        self.console.setMaximumHeight(300)
        layout.addWidget(self.console)

        # Welcome message
        self._log("EPOCH Zone Analysis v2.0")
        self._log("=" * 50)
        self._log("Enter tickers (with optional per-ticker anchor dates)")
        self._log("Format: TICKER,YYYY-MM-DD or just TICKER")
        self._log("Click RUN ANALYSIS to begin.")
        self._log("")

        return frame

    def _on_anchor_preset_changed(self, index: int):
        """Handle anchor preset change."""
        preset_key = self.anchor_preset.currentData()
        self.anchor_date.setEnabled(preset_key == "custom")

        if preset_key != "custom":
            # Calculate date based on preset relative to analysis date
            ref_date = self.analysis_date.date().toPyDate()
            anchor = self._calculate_anchor_from_preset(preset_key, ref_date)
            self.anchor_date.setDate(QDate(anchor.year, anchor.month, anchor.day))

    def _on_analysis_date_changed(self, new_date: QDate):
        """Handle analysis date change - update cutoff label."""
        self._update_cutoff_label()

    def _on_market_mode_changed(self, index: int):
        """Handle market mode change - update cutoff label."""
        self._update_cutoff_label()

    def _update_cutoff_label(self):
        """Update the cutoff label based on current analysis date and market mode."""
        mode = self.market_mode.currentText()
        analysis_dt = self.analysis_date.date().toPyDate()
        today = date.today()

        if mode == "Live":
            if analysis_dt == today:
                self.cutoff_label.setText("Data cutoff: Current time (rounded to previous minute)")
            else:
                self.cutoff_label.setText("Data cutoff: Using all available data for date")
        elif mode == "Pre-Market":
            self.cutoff_label.setText(f"Data cutoff: {analysis_dt} 09:00 ET (last H1: 08:00-09:00)")
        elif mode == "Post-Market":
            self.cutoff_label.setText(f"Data cutoff: {analysis_dt} 15:00 ET (last H1: 14:00-15:00)")

    def _calculate_anchor_from_preset(self, preset_key: str, ref_date: date) -> date:
        """Calculate anchor date from preset relative to a reference date."""
        if preset_key == "prior_day":
            # Previous trading day (skip weekends)
            anchor = ref_date - timedelta(days=1)
            while anchor.weekday() >= 5:  # Saturday=5, Sunday=6
                anchor -= timedelta(days=1)
        elif preset_key == "prior_week":
            # Previous Friday
            days_since_friday = (ref_date.weekday() - 4) % 7
            if days_since_friday == 0:
                days_since_friday = 7
            anchor = ref_date - timedelta(days=days_since_friday)
        elif preset_key == "prior_month":
            # First of previous month
            first_of_month = ref_date.replace(day=1)
            anchor = first_of_month - timedelta(days=1)
            anchor = anchor.replace(day=1)
        elif preset_key == "ytd":
            anchor = date(ref_date.year, 1, 1)
        else:
            anchor = ref_date
        return anchor

    def _parse_ticker_input(self) -> Tuple[List[Dict], List[str]]:
        """
        Parse ticker input with optional per-ticker anchor dates.

        Returns:
            Tuple of (ticker_inputs list, error messages list)
        """
        ticker_inputs = []
        errors = []

        text = self.ticker_input.toPlainText().strip()
        if not text:
            return [], ["No tickers entered"]

        # Get default anchor date
        default_anchor = self.anchor_date.date().toPyDate()

        # Parse each line
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if line has a date (TICKER,YYYY-MM-DD)
            if ',' in line:
                parts = line.split(',', 1)
                ticker = parts[0].strip().upper()
                date_str = parts[1].strip()

                # Try to parse the date
                try:
                    anchor = datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    errors.append(f"Invalid date format for {ticker}: {date_str} (use YYYY-MM-DD)")
                    continue
            else:
                # No date specified - use default anchor
                ticker = line.upper()
                anchor = default_anchor

            # Validate ticker
            if not ticker.isalnum():
                errors.append(f"Invalid ticker symbol: {ticker}")
                continue

            ticker_inputs.append({
                "ticker": ticker,
                "anchor_date": anchor
            })

        return ticker_inputs, errors

    def _get_end_timestamp(self, analysis_dt: date, market_mode: str) -> Optional[datetime]:
        """
        Get the end timestamp for data fetching based on analysis date and market mode.

        Logic:
        - Live + Current Date: Current time rounded down to previous minute
        - Live + Past Date: None (use all available data for that date)
        - Pre-Market: analysis_date at 09:00 ET
        - Post-Market: analysis_date at 16:00 ET

        Returns:
            timezone-aware datetime in Eastern Time if cutoff should be applied, None otherwise
        """
        eastern = ZoneInfo("America/New_York")
        today = date.today()

        if market_mode == "Live":
            # Live mode: only apply timestamp cutoff for current date
            if analysis_dt == today:
                # Get current time in Eastern Time, rounded down to previous minute
                now_et = datetime.now(eastern)
                # Round down to the previous minute (clear seconds and microseconds)
                rounded_et = now_et.replace(second=0, microsecond=0)
                return rounded_et
            else:
                # Past date in Live mode: use all available data
                return None
        else:
            # Pre-Market or Post-Market: use the fixed cutoff time
            cutoff_time = MARKET_CUTOFFS.get(market_mode)
            if cutoff_time is None:
                return None

            # Combine analysis date with cutoff time in Eastern Time
            et_datetime = datetime.combine(analysis_dt, cutoff_time, tzinfo=eastern)
            return et_datetime

    def _on_run_clicked(self):
        """Handle run button click."""
        # Parse tickers with per-ticker dates
        ticker_inputs, errors = self._parse_ticker_input()

        if errors:
            error_msg = "Ticker parsing errors:\n" + "\n".join(errors)
            QMessageBox.warning(self, "Input Errors", error_msg)
            return

        if not ticker_inputs:
            QMessageBox.warning(self, "No Tickers", "Please enter at least one ticker symbol.")
            return

        if len(ticker_inputs) > MAX_TICKERS:
            QMessageBox.warning(
                self, "Too Many Tickers",
                f"Maximum {MAX_TICKERS} tickers allowed. You entered {len(ticker_inputs)}."
            )
            return

        # Get analysis date and market mode
        analysis_dt = self.analysis_date.date().toPyDate()
        market_mode = self.market_mode.currentText()
        end_timestamp = self._get_end_timestamp(analysis_dt, market_mode)

        # Log configuration
        self._log("")
        self._log("=" * 50)
        self._log(f"Starting analysis: {len(ticker_inputs)} tickers")
        self._log(f"Analysis Date: {analysis_dt} | Market Mode: {market_mode}")
        if end_timestamp:
            # Format timestamp in Eastern Time for display
            eastern = ZoneInfo("America/New_York")
            et_display = end_timestamp.astimezone(eastern)
            self._log(f"Data Cutoff: {et_display.strftime('%Y-%m-%d %H:%M')} ET")
        else:
            self._log("Data Cutoff: None (using all available data)")
        self._log("-" * 50)

        # Log each ticker with its anchor
        for ti in ticker_inputs:
            self._log(f"  {ti['ticker']}: anchor={ti['anchor_date']}")
        self._log("=" * 50)

        # Update UI state
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status_indicator.setText("Running...")
        self.status_indicator.setStyleSheet(f"color: {COLORS['status_running']}; font-weight: bold;")
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(100)

        # Clear previous results
        self.analysis_results.clear_results()

        # Start worker thread
        self._worker = AnalysisWorker(
            ticker_inputs,
            analysis_dt,
            market_mode,
            end_timestamp
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_stop_clicked(self):
        """Handle stop button click."""
        if self._worker:
            self._worker.cancel()
            self._worker.quit()
            self._worker.wait()
            self._worker = None

        self._log("\n[!] Analysis cancelled by user.")
        self._reset_ui()

    def _on_clear_clicked(self):
        """Handle clear button click."""
        self.ticker_input.clear()
        self._clear_console()
        self.analysis_results.clear_results()
        self.progress_bar.setValue(0)
        self.progress_label.setText("Waiting to start...")
        self._log("Results cleared.")

    def _on_progress(self, percent: int, message: str):
        """Handle progress update from worker."""
        self.progress_bar.setValue(percent)
        self.progress_label.setText(message)
        self._log(f"[{percent}%] {message}")

    def _on_finished(self, results: Dict[str, Any]):
        """Handle analysis completion."""
        self._worker = None

        # Count results
        index_count = len(results.get("index", []))
        custom_count = len(results.get("custom", []))
        total_zones = sum(
            len(r.get("filtered_zones", []))
            for r in results.get("index", []) + results.get("custom", [])
        )

        self._log("")
        self._log("=" * 50)
        self._log("ANALYSIS COMPLETE")
        self._log(f"Index tickers: {index_count}")
        self._log(f"Custom tickers: {custom_count}")
        self._log(f"Total zones found: {total_zones}")
        self._log("=" * 50)

        # Update shared results
        results["run_complete"] = True
        results["analysis_date"] = self.analysis_date.date().toPyDate()
        results["market_mode"] = self.market_mode.currentText()
        # Store end_timestamp so other tabs (like pre-market report) can use the same cutoff
        results["end_timestamp"] = self._get_end_timestamp(
            self.analysis_date.date().toPyDate(),
            self.market_mode.currentText()
        )
        self.analysis_results.update_results(results)

        self._reset_ui()
        self.status_indicator.setText("Complete")
        self.status_indicator.setStyleSheet(f"color: {COLORS['status_complete']}; font-weight: bold;")

    def _on_error(self, error_msg: str):
        """Handle analysis error."""
        self._worker = None
        self._log(f"\n[ERROR] {error_msg}")
        self._reset_ui()
        self.status_indicator.setText("Error")
        self.status_indicator.setStyleSheet(f"color: {COLORS['status_error']}; font-weight: bold;")

        QMessageBox.critical(self, "Analysis Error", f"An error occurred:\n\n{error_msg}")

    def _reset_ui(self):
        """Reset UI to ready state."""
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_indicator.setText("Ready")
        self.status_indicator.setStyleSheet(f"color: {COLORS['status_ready']}; font-weight: bold;")

    def _log(self, message: str):
        """Log message to console."""
        self.console.append(message)

    def _clear_console(self):
        """Clear the console."""
        self.console.clear()
        self._log("Console cleared.")

    def on_results_updated(self, results: Dict[str, Any]):
        """Handle results update (not used in this tab)."""
        pass
