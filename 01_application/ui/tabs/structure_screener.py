"""
Structure Screener Tab
Epoch Trading System v2.0 - XIII Trading LLC

Pre-market screener that runs D1 market structure v3 across the dynamic
ticker universe (same source as scanner.py, gap filter removed) and
classifies each ticker into one of four states:

    Bull         – Current price in top 70% of bull range
    Bear         – Current price in bottom 30% of bear range
    Out - Strong – Current price beyond the Strong level
    Out - Weak   – Current price beyond the Weak level
"""

from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
import logging

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QComboBox, QDoubleSpinBox, QDateEdit, QPushButton,
    QProgressBar, QGridLayout, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QDate
from PyQt6.QtGui import QFont, QColor

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ui.tabs.base_tab import BaseTab
from ui.styles import COLORS
from scanner import TickerManager, TickerList

logger = logging.getLogger(__name__)


# =============================================================================
# STATE CLASSIFICATION
# =============================================================================

def classify_ticker(direction: int, strong: float, weak: float,
                    current_price: float) -> str:
    """
    Classify a ticker's position relative to its D1 structure.

    Args:
        direction: 1 (BULL) or -1 (BEAR)
        strong: Strong (invalidation) level
        weak: Weak (target) level — may be None
        current_price: Latest close

    Returns:
        One of: "Bull", "Bear", "Out - Strong", "Out - Weak", "Neutral"
    """
    if direction == 0 or strong is None:
        return "Neutral"

    if direction == 1:  # BULL — strong is support, weak is resistance
        if weak is not None:
            # Price above weak → broken out above target
            if current_price > weak:
                return "Out - Weak"
            # Price below strong → broken below support
            if current_price < strong:
                return "Out - Strong"
            # Inside range — check top 70%
            rng = weak - strong
            if rng > 0:
                pct = (current_price - strong) / rng
                if pct >= 0.30:          # top 70% of range
                    return "Bull"
                else:
                    return "Bull (Low)"  # bottom 30% — weakening
            return "Bull"
        else:
            # No weak anchored yet — classify vs strong only
            if current_price < strong:
                return "Out - Strong"
            return "Bull"

    elif direction == -1:  # BEAR — strong is resistance, weak is support
        if weak is not None:
            # Price below weak → broken out below target
            if current_price < weak:
                return "Out - Weak"
            # Price above strong → broken above resistance
            if current_price > strong:
                return "Out - Strong"
            # Inside range — check bottom 30%
            rng = strong - weak
            if rng > 0:
                pct = (strong - current_price) / rng
                if pct >= 0.30:          # bottom 30% of range
                    return "Bear"
                else:
                    return "Bear (High)"  # top 70% — weakening
            return "Bear"
        else:
            if current_price > strong:
                return "Out - Strong"
            return "Bear"

    return "Neutral"


# =============================================================================
# WORKER THREAD
# =============================================================================

class StructureScreenerWorker(QThread):
    """Worker thread that runs D1 structure on every ticker."""
    progress = pyqtSignal(int, int, str)          # completed, total, ticker
    ticker_result = pyqtSignal(dict)               # single ticker result (for live table updates)
    finished = pyqtSignal(list)                    # all results
    error = pyqtSignal(str)

    def __init__(self, ticker_list: TickerList,
                 min_price: float = 10.0,
                 min_atr: float = 2.0,
                 lookback_days: int = 365,
                 parallel_workers: int = 10):
        super().__init__()
        self.ticker_list = ticker_list
        self.min_price = min_price
        self.min_atr = min_atr
        self.lookback_days = lookback_days
        self.parallel_workers = parallel_workers
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            from concurrent.futures import ThreadPoolExecutor, as_completed
            from data.polygon_client import PolygonClient
            from shared.indicators.structure import get_market_structure

            # Build ticker universe (same as scanner.py, gap filter removed)
            ticker_mgr = TickerManager()
            tickers = ticker_mgr.get_tickers(self.ticker_list)

            polygon = PolygonClient()
            end_date = date.today()
            start_date = end_date - timedelta(days=self.lookback_days)

            results: List[dict] = []
            total = len(tickers)

            def _process_one(ticker: str) -> Optional[dict]:
                if self._cancelled:
                    return None
                try:
                    # Fetch D1 bars
                    df = polygon.fetch_daily_bars(ticker, start_date, end_date)
                    if df.empty or len(df) < 20:
                        return None

                    current_price = float(df["close"].iloc[-1])

                    # Hard filters (same as scanner minus gap)
                    if current_price < self.min_price:
                        return None

                    # ATR filter
                    atr = self._quick_atr(df)
                    if atr < self.min_atr:
                        return None

                    # Prior day body check (open-to-close range, wicks OK)
                    if len(df) >= 2:
                        prior_open = float(df["open"].iloc[-2])
                        prior_close = float(df["close"].iloc[-2])
                        body_lo = min(prior_open, prior_close)
                        body_hi = max(prior_open, prior_close)
                        if current_price > body_hi:
                            prior_d1_body = "Above"
                        elif current_price < body_lo:
                            prior_d1_body = "Below"
                        else:
                            prior_d1_body = "Inside"
                    else:
                        prior_d1_body = "—"

                    # Run v3 market structure
                    result = get_market_structure(df)

                    # Classify
                    state = classify_ticker(
                        result.direction,
                        result.strong_level,
                        result.weak_level,
                        current_price,
                    )

                    return {
                        "ticker": ticker,
                        "price": current_price,
                        "direction": result.label,
                        "strong": result.strong_level,
                        "weak": result.weak_level,
                        "state": state,
                        "atr": round(atr, 2),
                        "prior_d1_body": prior_d1_body,
                    }
                except Exception as exc:
                    logger.debug(f"Structure screener skip {ticker}: {exc}")
                    return None

            # Parallel execution
            with ThreadPoolExecutor(max_workers=self.parallel_workers) as pool:
                futures = {
                    pool.submit(_process_one, t): t for t in tickers
                }
                completed = 0
                for future in as_completed(futures):
                    if self._cancelled:
                        pool.shutdown(wait=False, cancel_futures=True)
                        self.finished.emit([])
                        return

                    ticker = futures[future]
                    completed += 1
                    self.progress.emit(completed, total, ticker)

                    try:
                        row = future.result()
                        if row is not None:
                            results.append(row)
                            self.ticker_result.emit(row)
                    except Exception:
                        pass

            # Sort: state priority then ticker
            state_order = {
                "Out - Strong": 0, "Out - Weak": 1,
                "Bull": 2, "Bear": 3,
                "Bull (Low)": 4, "Bear (High)": 5,
                "Neutral": 6,
            }
            results.sort(key=lambda r: (state_order.get(r["state"], 9), r["ticker"]))

            self.finished.emit(results)

        except Exception as e:
            import traceback
            logger.error(traceback.format_exc())
            self.error.emit(str(e))

    @staticmethod
    def _quick_atr(df, period: int = 14) -> float:
        """Lightweight ATR from a daily DataFrame."""
        if len(df) < 2:
            return 0.0
        df2 = df.copy()
        df2["h_l"] = df2["high"] - df2["low"]
        df2["h_pc"] = (df2["high"] - df2["close"].shift(1)).abs()
        df2["l_pc"] = (df2["low"] - df2["close"].shift(1)).abs()
        df2["tr"] = df2[["h_l", "h_pc", "l_pc"]].max(axis=1)
        return float(df2["tr"].ewm(span=period, adjust=False).mean().iloc[-1])


# =============================================================================
# TAB
# =============================================================================

class StructureScreenerTab(BaseTab):
    """
    Market Structure Screener — pre-market D1 structure scan.

    Pulls the dynamic ticker universe (same as scanner.py, gap filter
    removed), runs the v3 market structure calculation on each ticker,
    and classifies the current price state.
    """

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Title
        title = QLabel("MARKET STRUCTURE SCREENER")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(title)

        subtitle = QLabel(
            "D1 structure scan — classifies each ticker vs its strong / weak range"
        )
        subtitle.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        layout.addWidget(subtitle)

        # ── Control Panel ────────────────────────────────────────────────
        ctrl_frame, ctrl_layout = self.create_section_frame("Scan Configuration")
        layout.addWidget(ctrl_frame)

        grid = QGridLayout()
        grid.setSpacing(12)
        ctrl_layout.addLayout(grid)

        # Row 0 — Ticker list
        grid.addWidget(QLabel("Ticker List:"), 0, 0)
        self.ticker_list_combo = QComboBox()
        self.ticker_list_combo.addItems([
            "S&P 500", "NASDAQ 100", "DOW 30",
            "Russell 2000", "All US Equities",
        ])
        self.ticker_list_combo.setCurrentIndex(0)
        self.ticker_list_combo.setMinimumWidth(200)
        grid.addWidget(self.ticker_list_combo, 0, 1)

        # Row 0 — Min Price
        grid.addWidget(QLabel("Min Price ($):"), 0, 2)
        self.min_price_spin = QDoubleSpinBox()
        self.min_price_spin.setRange(0, 1000)
        self.min_price_spin.setValue(10.0)
        self.min_price_spin.setDecimals(2)
        self.min_price_spin.setSingleStep(5.0)
        self.min_price_spin.setMinimumWidth(100)
        grid.addWidget(self.min_price_spin, 0, 3)

        # Row 1 — Min ATR
        grid.addWidget(QLabel("Min ATR ($):"), 1, 0)
        self.min_atr_spin = QDoubleSpinBox()
        self.min_atr_spin.setRange(0, 50)
        self.min_atr_spin.setValue(2.0)
        self.min_atr_spin.setDecimals(2)
        self.min_atr_spin.setSingleStep(0.25)
        self.min_atr_spin.setMinimumWidth(100)
        grid.addWidget(self.min_atr_spin, 1, 1)

        # Row 1 — Workers
        grid.addWidget(QLabel("Workers:"), 1, 2)
        self.workers_spin = QDoubleSpinBox()
        self.workers_spin.setRange(1, 20)
        self.workers_spin.setValue(10)
        self.workers_spin.setDecimals(0)
        self.workers_spin.setSingleStep(1)
        self.workers_spin.setMinimumWidth(100)
        grid.addWidget(self.workers_spin, 1, 3)

        grid.setColumnStretch(4, 1)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        ctrl_layout.addLayout(btn_row)

        self.run_button = QPushButton("Run Scan")
        self.run_button.setObjectName("primaryButton")
        self.run_button.setMinimumWidth(120)
        self.run_button.clicked.connect(self._on_run)
        btn_row.addWidget(self.run_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.setObjectName("dangerButton")
        self.stop_button.setMinimumWidth(80)
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self._on_stop)
        btn_row.addWidget(self.stop_button)

        self.clear_button = QPushButton("Clear Results")
        self.clear_button.setMinimumWidth(100)
        self.clear_button.clicked.connect(self._on_clear)
        btn_row.addWidget(self.clear_button)

        btn_row.addStretch()

        # Progress
        prog_row = QHBoxLayout()
        prog_row.setSpacing(12)
        ctrl_layout.addLayout(prog_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumWidth(300)
        self.progress_bar.setValue(0)
        prog_row.addWidget(self.progress_bar)

        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        prog_row.addWidget(self.status_label)
        prog_row.addStretch()

        # ── Summary Metrics ──────────────────────────────────────────────
        self.metrics_frame, self.metrics_layout = self.create_section_frame("Summary")
        layout.addWidget(self.metrics_frame)

        self.metrics_row = QHBoxLayout()
        self.metrics_row.setSpacing(24)
        self.metrics_layout.addLayout(self.metrics_row)

        self._metric_labels: Dict[str, QLabel] = {}
        for key, label in [
            ("total", "Total"),
            ("bull", "Bull"),
            ("bear", "Bear"),
            ("out_strong", "Out - Strong"),
            ("out_weak", "Out - Weak"),
            ("neutral", "Neutral"),
        ]:
            lbl = QLabel(f"{label}: —")
            lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
            self.metrics_row.addWidget(lbl)
            self._metric_labels[key] = lbl
        self.metrics_row.addStretch()

        # ── Results Table ────────────────────────────────────────────────
        results_frame, results_layout = self.create_section_frame("Scan Results")
        layout.addWidget(results_frame)

        self.results_summary = QLabel("No scan results yet")
        self.results_summary.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 12px;"
        )
        results_layout.addWidget(self.results_summary)

        self.results_table = self.create_table(
            headers=[
                "Ticker", "Price", "Direction", "Strong", "Weak",
                "State", "Prior D1", "ATR",
            ],
            column_widths=[80, 90, 90, 100, 100, 120, 90, 80],
        )
        results_layout.addWidget(self.results_table)

        layout.addStretch()

        # Worker reference
        self._worker: Optional[StructureScreenerWorker] = None
        self._live_results: List[dict] = []

    # ── Combo → Enum ─────────────────────────────────────────────────────

    _TICKER_MAP = {
        0: TickerList.SP500,
        1: TickerList.NASDAQ100,
        2: TickerList.DOW30,
        3: TickerList.RUSSELL2000,
        4: TickerList.ALL_US_EQUITIES,
    }

    def _get_ticker_list(self) -> TickerList:
        return self._TICKER_MAP.get(
            self.ticker_list_combo.currentIndex(), TickerList.SP500
        )

    # ── Button Handlers ──────────────────────────────────────────────────

    def _on_run(self):
        if self._worker and self._worker.isRunning():
            QMessageBox.warning(self, "Scan Running", "A scan is already in progress.")
            return

        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Starting scan...")
        self.results_summary.setText("Scanning...")
        self.results_table.setRowCount(0)
        self._live_results = []

        self._worker = StructureScreenerWorker(
            ticker_list=self._get_ticker_list(),
            min_price=self.min_price_spin.value(),
            min_atr=self.min_atr_spin.value(),
            parallel_workers=int(self.workers_spin.value()),
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.ticker_result.connect(self._on_ticker_result)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_stop(self):
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self.status_label.setText("Cancelling...")
            self.stop_button.setEnabled(False)

    def _on_clear(self):
        self.results_table.setRowCount(0)
        self.results_summary.setText("No scan results")
        self.progress_bar.setValue(0)
        self.status_label.setText("Ready")
        self._live_results = []
        self._update_metrics([])

    # ── Callbacks ────────────────────────────────────────────────────────

    def _on_progress(self, completed: int, total: int, ticker: str):
        pct = int(completed / total * 100) if total else 0
        self.progress_bar.setValue(pct)
        self.status_label.setText(f"Processing {ticker} ({completed}/{total})")

    def _on_ticker_result(self, row: dict):
        """Append a single result to the live table as it arrives."""
        self._live_results.append(row)

    def _on_finished(self, results: list):
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setValue(100)

        if not results:
            self.status_label.setText("No tickers matched filters")
            self.results_summary.setText("0 tickers matched filters")
            self._update_metrics([])
            return

        self._populate_results(results)
        self._update_metrics(results)
        self.status_label.setText(f"Scan complete — {len(results)} results")
        self.results_summary.setText(f"{len(results)} tickers classified")

    def _on_error(self, msg: str):
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.status_label.setText(f"Error: {msg}")
        QMessageBox.critical(self, "Scan Error", f"Error:\n{msg}")

    # ── Table Population ─────────────────────────────────────────────────

    _STATE_COLORS = {
        "Bull": COLORS["bull"],
        "Bull (Low)": "#66bb6a",       # lighter green
        "Bear": COLORS["bear"],
        "Bear (High)": "#ff8a80",      # lighter red
        "Out - Strong": "#ffc107",     # amber
        "Out - Weak": "#2196f3",       # blue
        "Neutral": COLORS["text_muted"],
    }

    def _populate_results(self, results: list):
        table_data = []
        colors = []

        for r in results:
            strong_str = f"${r['strong']:.2f}" if r["strong"] is not None else "—"
            weak_str = f"${r['weak']:.2f}" if r["weak"] is not None else "pending"

            table_data.append([
                r["ticker"],
                f"${r['price']:.2f}",
                r["direction"],
                strong_str,
                weak_str,
                r["state"],
                r.get("prior_d1_body", "—"),
                f"${r['atr']:.2f}",
            ])
            colors.append(self._STATE_COLORS.get(r["state"]))

        self.populate_table(self.results_table, table_data, colors)

    def _update_metrics(self, results: list):
        counts = {
            "total": len(results),
            "bull": sum(1 for r in results if r["state"] in ("Bull", "Bull (Low)")),
            "bear": sum(1 for r in results if r["state"] in ("Bear", "Bear (High)")),
            "out_strong": sum(1 for r in results if r["state"] == "Out - Strong"),
            "out_weak": sum(1 for r in results if r["state"] == "Out - Weak"),
            "neutral": sum(1 for r in results if r["state"] == "Neutral"),
        }

        label_colors = {
            "total": COLORS["text_primary"],
            "bull": COLORS["bull"],
            "bear": COLORS["bear"],
            "out_strong": "#ffc107",
            "out_weak": "#2196f3",
            "neutral": COLORS["text_muted"],
        }

        display_names = {
            "total": "Total",
            "bull": "Bull",
            "bear": "Bear",
            "out_strong": "Out - Strong",
            "out_weak": "Out - Weak",
            "neutral": "Neutral",
        }

        for key, lbl in self._metric_labels.items():
            c = label_colors.get(key, COLORS["text_secondary"])
            name = display_names[key]
            lbl.setText(f"{name}: {counts.get(key, 0)}")
            lbl.setStyleSheet(f"color: {c}; font-size: 12px; font-weight: bold;")

    # ── BaseTab Required ─────────────────────────────────────────────────

    def on_results_updated(self, results: Dict[str, Any]):
        pass  # This tab is self-contained; doesn't react to pipeline results
