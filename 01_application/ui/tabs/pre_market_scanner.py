"""
Pre-Market Scanner Tab
Epoch Trading System v2.0 - XIII Trading LLC

PyQt6 tab for two-phase pre-market scanning.
Identifies high-potential trading candidates based on:
- ATR, price, and gap filters (Phase 1)
- Overnight volume and ranking metrics (Phase 2)
"""

from datetime import datetime, date
from typing import Dict, Any, Optional
import logging

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QComboBox, QDoubleSpinBox, QDateEdit, QPushButton,
    QProgressBar, QGridLayout, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QDate
from PyQt6.QtGui import QFont

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ui.tabs.base_tab import BaseTab
from ui.styles import COLORS
from scanner import TwoPhaseScanner, FilterPhase, RankingWeights, TickerList

logger = logging.getLogger(__name__)


class ScannerWorker(QThread):
    """Worker thread for running the scanner."""
    progress = pyqtSignal(int, int, str)  # completed, total, ticker
    finished = pyqtSignal(object)  # DataFrame results
    error = pyqtSignal(str)

    def __init__(self,
                 ticker_list: TickerList,
                 filter_phase: FilterPhase,
                 ranking_weights: RankingWeights,
                 scan_date: datetime,
                 parallel_workers: int = 10):
        super().__init__()
        self.ticker_list = ticker_list
        self.filter_phase = filter_phase
        self.ranking_weights = ranking_weights
        self.scan_date = scan_date
        self.parallel_workers = parallel_workers
        self._scanner = None

    def run(self):
        try:
            self._scanner = TwoPhaseScanner(
                ticker_list=self.ticker_list,
                filter_phase=self.filter_phase,
                ranking_weights=self.ranking_weights,
                parallel_workers=self.parallel_workers
            )

            results = self._scanner.run_scan(
                scan_date=self.scan_date,
                progress_callback=self._progress_callback
            )

            self.finished.emit(results)

        except Exception as e:
            logger.error(f"Scanner error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.error.emit(str(e))

    def _progress_callback(self, completed: int, total: int, ticker: str):
        self.progress.emit(completed, total, ticker)

    def cancel(self):
        if self._scanner:
            self._scanner.cancel()


class PreMarketScannerTab(BaseTab):
    """
    Pre-Market Scanner Tab - Two-phase market scanning.

    Allows users to:
    - Select ticker list (S&P 500, NASDAQ 100, etc.)
    - Configure filter thresholds (ATR, price, gap)
    - Run scan and view ranked results
    """

    def _setup_ui(self):
        """Set up the scanner tab UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Title
        title = QLabel("PRE-MARKET SCANNER")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(title)

        # Control Panel Section
        control_section, control_layout = self.create_section_frame("Scan Configuration")
        layout.addWidget(control_section)

        # Create control grid
        control_grid = QGridLayout()
        control_grid.setSpacing(12)
        control_layout.addLayout(control_grid)

        # Row 0: Ticker List
        control_grid.addWidget(QLabel("Ticker List:"), 0, 0)
        self.ticker_list_combo = QComboBox()
        self.ticker_list_combo.addItems([
            "S&P 500",
            "NASDAQ 100",
            "DOW 30",
            "Russell 2000",
            "All US Equities"
        ])
        self.ticker_list_combo.setCurrentIndex(0)
        self.ticker_list_combo.setMinimumWidth(200)
        control_grid.addWidget(self.ticker_list_combo, 0, 1)

        # Row 0: Scan Date
        control_grid.addWidget(QLabel("Scan Date:"), 0, 2)
        self.scan_date_edit = QDateEdit()
        self.scan_date_edit.setCalendarPopup(True)
        self.scan_date_edit.setDate(QDate.currentDate())
        self.scan_date_edit.setMinimumWidth(150)
        control_grid.addWidget(self.scan_date_edit, 0, 3)

        # Row 1: Min ATR
        control_grid.addWidget(QLabel("Min ATR ($):"), 1, 0)
        self.min_atr_spin = QDoubleSpinBox()
        self.min_atr_spin.setRange(0.0, 50.0)
        self.min_atr_spin.setValue(2.00)
        self.min_atr_spin.setDecimals(2)
        self.min_atr_spin.setSingleStep(0.25)
        self.min_atr_spin.setMinimumWidth(100)
        control_grid.addWidget(self.min_atr_spin, 1, 1)

        # Row 1: Min Price
        control_grid.addWidget(QLabel("Min Price ($):"), 1, 2)
        self.min_price_spin = QDoubleSpinBox()
        self.min_price_spin.setRange(0.0, 1000.0)
        self.min_price_spin.setValue(10.00)
        self.min_price_spin.setDecimals(2)
        self.min_price_spin.setSingleStep(5.0)
        self.min_price_spin.setMinimumWidth(100)
        control_grid.addWidget(self.min_price_spin, 1, 3)

        # Row 2: Min Gap
        control_grid.addWidget(QLabel("Min Gap (%):"), 2, 0)
        self.min_gap_spin = QDoubleSpinBox()
        self.min_gap_spin.setRange(0.0, 50.0)
        self.min_gap_spin.setValue(2.0)
        self.min_gap_spin.setDecimals(1)
        self.min_gap_spin.setSingleStep(0.5)
        self.min_gap_spin.setMinimumWidth(100)
        control_grid.addWidget(self.min_gap_spin, 2, 1)

        # Row 2: Parallel Workers
        control_grid.addWidget(QLabel("Workers:"), 2, 2)
        self.workers_spin = QDoubleSpinBox()
        self.workers_spin.setRange(1, 20)
        self.workers_spin.setValue(10)
        self.workers_spin.setDecimals(0)
        self.workers_spin.setSingleStep(1)
        self.workers_spin.setMinimumWidth(100)
        control_grid.addWidget(self.workers_spin, 2, 3)

        # Add stretch column
        control_grid.setColumnStretch(4, 1)

        # Button row
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        control_layout.addLayout(button_layout)

        self.run_button = QPushButton("Run Scan")
        self.run_button.setObjectName("primaryButton")
        self.run_button.setMinimumWidth(120)
        self.run_button.clicked.connect(self._on_run_scan)
        button_layout.addWidget(self.run_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.setObjectName("dangerButton")
        self.stop_button.setMinimumWidth(80)
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self._on_stop_scan)
        button_layout.addWidget(self.stop_button)

        self.clear_button = QPushButton("Clear Results")
        self.clear_button.setMinimumWidth(100)
        self.clear_button.clicked.connect(self._on_clear_results)
        button_layout.addWidget(self.clear_button)

        button_layout.addStretch()

        # Progress section
        progress_layout = QHBoxLayout()
        progress_layout.setSpacing(12)
        control_layout.addLayout(progress_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumWidth(300)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        progress_layout.addWidget(self.status_label)

        progress_layout.addStretch()

        # Results Section
        results_section, results_layout = self.create_section_frame("Scan Results")
        layout.addWidget(results_section)

        # Results summary
        self.results_summary = QLabel("No scan results yet")
        self.results_summary.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        results_layout.addWidget(self.results_summary)

        # Results table
        self.results_table = self.create_table(
            headers=[
                "Rank", "Ticker", "Price", "Gap %", "ATR",
                "O/N Volume", "Rel O/N Vol", "Rel Vol",
                "Short %", "DTC", "Score"
            ],
            column_widths=[60, 80, 80, 80, 80, 120, 100, 100, 80, 60, 80]
        )
        results_layout.addWidget(self.results_table)

        # Add stretch at bottom
        layout.addStretch()

        # Worker reference
        self._worker: Optional[ScannerWorker] = None

    def _get_ticker_list(self) -> TickerList:
        """Convert combo selection to TickerList enum."""
        mapping = {
            0: TickerList.SP500,
            1: TickerList.NASDAQ100,
            2: TickerList.DOW30,
            3: TickerList.RUSSELL2000,
            4: TickerList.ALL_US_EQUITIES
        }
        return mapping.get(self.ticker_list_combo.currentIndex(), TickerList.SP500)

    def _on_run_scan(self):
        """Handle run scan button click."""
        if self._worker and self._worker.isRunning():
            QMessageBox.warning(self, "Scan Running", "A scan is already in progress.")
            return

        # Get configuration
        ticker_list = self._get_ticker_list()
        filter_phase = FilterPhase(
            min_atr=self.min_atr_spin.value(),
            min_price=self.min_price_spin.value(),
            min_gap_percent=self.min_gap_spin.value()
        )
        ranking_weights = RankingWeights()

        # Get scan date
        qdate = self.scan_date_edit.date()
        scan_date = datetime(qdate.year(), qdate.month(), qdate.day())

        # Update UI state
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Starting scan...")
        self.results_summary.setText("Scanning...")

        # Clear previous results
        self.results_table.setRowCount(0)

        # Create and start worker
        self._worker = ScannerWorker(
            ticker_list=ticker_list,
            filter_phase=filter_phase,
            ranking_weights=ranking_weights,
            scan_date=scan_date,
            parallel_workers=int(self.workers_spin.value())
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_scan_finished)
        self._worker.error.connect(self._on_scan_error)
        self._worker.start()

    def _on_stop_scan(self):
        """Handle stop button click."""
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self.status_label.setText("Cancelling...")
            self.stop_button.setEnabled(False)

    def _on_clear_results(self):
        """Clear scan results."""
        self.results_table.setRowCount(0)
        self.results_summary.setText("No scan results")
        self.progress_bar.setValue(0)
        self.status_label.setText("Ready")

    def _on_progress(self, completed: int, total: int, ticker: str):
        """Handle progress updates."""
        percent = int((completed / total) * 100) if total > 0 else 0
        self.progress_bar.setValue(percent)
        self.status_label.setText(f"Processing {ticker} ({completed}/{total})")

    def _on_scan_finished(self, results):
        """Handle scan completion."""
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setValue(100)

        if results is None or (hasattr(results, 'empty') and results.empty):
            self.status_label.setText("No tickers passed filters")
            self.results_summary.setText("0 tickers passed filters")
            return

        # Populate results table
        self._populate_results(results)

        # Update status
        self.status_label.setText(f"Scan complete - {len(results)} results")
        self.results_summary.setText(
            f"Found {len(results)} tickers passing filters | "
            f"Scan date: {results['scan_date'].iloc[0].strftime('%Y-%m-%d') if 'scan_date' in results.columns else 'N/A'}"
        )

        # Store results in analysis_results for other tabs
        self._store_scanner_results(results)

    def _on_scan_error(self, error_msg: str):
        """Handle scan error."""
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.status_label.setText(f"Error: {error_msg}")

        QMessageBox.critical(self, "Scan Error", f"Scanner encountered an error:\n{error_msg}")

    def _populate_results(self, df):
        """Populate the results table with scan data."""
        # Define columns to display
        display_columns = [
            ('rank', 'Rank', lambda x: f"{x:.0f}"),
            ('ticker', 'Ticker', str),
            ('current_price', 'Price', lambda x: f"${x:.2f}"),
            ('gap_percent', 'Gap %', lambda x: f"{x:+.2f}%"),
            ('atr', 'ATR', lambda x: f"${x:.2f}"),
            ('current_overnight_volume', 'O/N Volume', lambda x: f"{x:,.0f}"),
            ('relative_overnight_volume', 'Rel O/N Vol', lambda x: f"{x:.2f}x"),
            ('relative_volume', 'Rel Vol', lambda x: f"{x:.2f}x"),
            ('short_interest', 'Short %', lambda x: f"{x:.1f}%"),
            ('days_to_cover', 'DTC', lambda x: f"{x:.1f}"),
            ('ranking_score', 'Score', lambda x: f"{x:.1f}")
        ]

        # Build table data
        table_data = []
        colors = []

        for _, row in df.iterrows():
            row_data = []
            for col_name, _, formatter in display_columns:
                if col_name in row:
                    try:
                        row_data.append(formatter(row[col_name]))
                    except:
                        row_data.append(str(row[col_name]))
                else:
                    row_data.append("")
            table_data.append(row_data)

            # Color based on gap direction
            if 'gap_percent' in row:
                if row['gap_percent'] > 0:
                    colors.append(COLORS['bull'])  # Green for gap up
                elif row['gap_percent'] < 0:
                    colors.append(COLORS['bear'])  # Red for gap down
                else:
                    colors.append(None)
            else:
                colors.append(None)

        self.populate_table(self.results_table, table_data, colors)

    def _store_scanner_results(self, df):
        """Store scanner results in analysis_results for other tabs."""
        results = self.analysis_results.results.copy()
        results['scanner_results'] = df.to_dict('records')
        results['scanner_date'] = datetime.now()
        self.analysis_results.update_results(results)

    def on_results_updated(self, results: Dict[str, Any]):
        """Handle updates from other tabs (if needed)."""
        # Scanner tab doesn't need to react to other tab updates
        pass
