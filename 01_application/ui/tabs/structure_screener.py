"""
Structure Screener Tab
Epoch Trading System v2.0 - XIII Trading LLC

Pre-market screener that runs D1 market structure v3 across the dynamic
ticker universe (same source as scanner.py, gap filter removed) and
classifies each ticker into one of seven states:

    Bull         – Current price in top 80% of bull range (confirmed)
    Bull (Low)   – Current price in bottom 20% of bull range (uncommitted)
    Bear         – Current price in bottom 80% of bear range (confirmed)
    Bear (High)  – Current price in top 20% of bear range (uncommitted)
    Out - Strong – Current price beyond the Strong level
    Out - Weak   – Current price beyond the Weak level
    Neutral      – No directional structure

Includes composite scoring (Structure + Alignment + Gap + RVOL + Zone)
and Top 10 Bull / Top 10 Bear shortlist.
"""

from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
from zoneinfo import ZoneInfo
import logging

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QComboBox, QDoubleSpinBox, QPushButton,
    QProgressBar, QGridLayout, QMessageBox, QCheckBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ui.tabs.base_tab import BaseTab
from ui.styles import COLORS
from scanner import TickerManager, TickerList

logger = logging.getLogger(__name__)

ET = ZoneInfo("America/New_York")

# =============================================================================
# SCORING WEIGHTS (tunable)
# =============================================================================

W_STRUCTURE = 30   # Structure state quality
W_ALIGNMENT = 20   # D1 body alignment with direction
W_GAP = 20         # Overnight gap alignment
W_RVOL = 25        # Relative volume
W_ZONE = 10        # Price position within zone


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
            # Inside range — check top 80%
            rng = weak - strong
            if rng > 0:
                pct = (current_price - strong) / rng
                if pct >= 0.20:          # top 80% of range
                    return "Bull"
                else:
                    return "Bull (Low)"  # bottom 20% — weakening
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
            # Inside range — check bottom 20%
            rng = strong - weak
            if rng > 0:
                pct = (strong - current_price) / rng
                if pct >= 0.20:          # bottom 80% of range
                    return "Bear"
                else:
                    return "Bear (High)"  # top 20% — weakening
            return "Bear"
        else:
            if current_price > strong:
                return "Out - Strong"
            return "Bear"

    return "Neutral"


# =============================================================================
# MINUTE DATA: 09:00 PRICE + RVOL
# =============================================================================

def fetch_minute_data(ticker: str, polygon, today: date) -> dict:
    """
    Fetch minute bars to get:
      - Last bar close at or before 09:00 ET (current_price)
      - RVOL%: today's 04:00-09:00 volume vs trailing 12-day average

    Returns dict with keys: price_0900, rvol_pct
    """
    result = {"price_0900": None, "rvol_pct": None}

    try:
        rvol_start = today - timedelta(days=25)
        min_df = polygon.fetch_minute_bars(ticker, rvol_start, today)

        if min_df.empty:
            return result

        # Convert UTC timestamps to ET
        min_df["et_time"] = min_df["timestamp"].dt.tz_convert(ET)
        min_df["bar_date"] = min_df["et_time"].dt.date
        min_df["bar_hour"] = min_df["et_time"].dt.hour
        min_df["bar_minute"] = min_df["et_time"].dt.minute

        # ── Price at ~09:00 on today ──
        # Use last bar at or before 09:00 (premarket gaps may skip exact minute)
        today_bars = min_df[min_df["bar_date"] == today].copy()
        if not today_bars.empty:
            pre_0901 = today_bars[
                (today_bars["bar_hour"] < 9) |
                ((today_bars["bar_hour"] == 9) & (today_bars["bar_minute"] == 0))
            ]
            if not pre_0901.empty:
                result["price_0900"] = float(pre_0901["close"].iloc[-1])

        # ── RVOL: 04:00-09:00 volume ──
        premarket = min_df[
            (min_df["bar_hour"] >= 4) & (min_df["bar_hour"] < 9)
        ]
        if premarket.empty:
            return result

        daily_pm_vol = premarket.groupby("bar_date")["volume"].sum()

        today_vol = daily_pm_vol.get(today, 0)

        # Trailing 12 trading days (exclude today)
        prior_vols = daily_pm_vol.drop(today, errors="ignore")
        prior_vols = prior_vols.sort_index().tail(12)

        if len(prior_vols) > 0 and prior_vols.mean() > 0:
            avg_vol = prior_vols.mean()
            result["rvol_pct"] = round((today_vol / avg_vol) * 100, 0)
        else:
            result["rvol_pct"] = 0

    except Exception as exc:
        logger.debug(f"Minute data skip {ticker}: {exc}")

    return result


# =============================================================================
# SCORING ENGINE
# =============================================================================

def score_structure(state: str) -> int:
    """Score structure state quality (0-30 pts)."""
    return {
        "Bull": W_STRUCTURE, "Bear": W_STRUCTURE,
        "Bull (Low)": 15, "Bear (High)": 15,
        "Out - Weak": 5,
        "Out - Strong": 0, "Neutral": 0,
    }.get(state, 0)


def score_alignment(direction: str, prior_d1_body: str) -> int:
    """Score D1 body alignment with structure direction (0-20 pts)."""
    if prior_d1_body == "Inside":
        return 10  # Neutral — no directional signal
    if direction == "BULL":
        return W_ALIGNMENT if prior_d1_body == "Above" else 5
    elif direction == "BEAR":
        return W_ALIGNMENT if prior_d1_body == "Below" else 5
    return 0


def score_gap(direction: str, gap_pct: float, price_source: str) -> int:
    """Score overnight gap alignment (0-20 pts)."""
    if price_source == "D1":
        return 10  # No 09:00 bar — neutral

    if direction == "BULL":
        if gap_pct >= 1.0:   return 20
        if gap_pct >= 0.5:   return 15
        if gap_pct >= 0.0:   return 10
        if gap_pct >= -0.5:  return 5
        return 0
    elif direction == "BEAR":
        if gap_pct <= -1.0:  return 20
        if gap_pct <= -0.5:  return 15
        if gap_pct <= 0.0:   return 10
        if gap_pct <= 0.5:   return 5
        return 0
    return 0


def score_rvol(rvol_pct) -> int:
    """Score relative volume (0-25 pts, tier-based)."""
    if rvol_pct is None or rvol_pct <= 0:
        return 0
    if rvol_pct < 50:   return 5
    if rvol_pct < 100:  return 10
    if rvol_pct < 150:  return 15
    if rvol_pct < 200:  return 20
    return W_RVOL  # 25


def score_zone(state: str, price: float, strong, weak,
               direction: str) -> int:
    """Score price position within the zone (0-10 pts)."""
    if state in ("Out - Weak", "Out - Strong", "Neutral"):
        return 0

    if weak is None:
        return 5  # Pending weak — trend mode, neutral

    if strong is None:
        return 0

    # Calculate zone percentage
    if direction == "BULL":
        rng = weak - strong
    elif direction == "BEAR":
        rng = strong - weak
    else:
        return 0

    if rng <= 0:
        return 5

    if direction == "BULL":
        zone_pct = (price - strong) / rng
    else:
        zone_pct = (strong - price) / rng

    zone_pct = max(0.0, min(1.0, zone_pct))

    if 0.20 <= zone_pct <= 0.45:  return 10  # Sweet spot
    if 0.45 < zone_pct <= 0.70:   return 7   # Mid zone
    if 0.70 < zone_pct <= 1.00:   return 4   # Near weak
    if 0.0 <= zone_pct < 0.20:    return 3   # Uncommitted
    return 0


def score_ticker(result: dict) -> dict:
    """Calculate composite score. Adds 'score' and 'score_detail' to result."""
    s = score_structure(result["state"])
    a = score_alignment(result["direction"], result["prior_d1_body"])
    g = score_gap(result["direction"], result.get("gap_pct", 0.0),
                  result.get("price_source", "D1"))
    r = score_rvol(result.get("rvol_pct"))
    z = score_zone(result["state"], result["price"],
                   result.get("strong"), result.get("weak"),
                   result["direction"])

    result["score"] = s + a + g + r + z
    result["score_detail"] = {"S": s, "A": a, "G": g, "R": r, "Z": z}
    return result


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
                    # ── Phase 1: D1 structure ──
                    df = polygon.fetch_daily_bars(ticker, start_date, end_date)
                    if df.empty or len(df) < 20:
                        return None

                    d1_close = float(df["close"].iloc[-1])

                    # Hard filters (same as scanner minus gap)
                    if d1_close < self.min_price:
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
                        if d1_close > body_hi:
                            prior_d1_body = "Above"
                        elif d1_close < body_lo:
                            prior_d1_body = "Below"
                        else:
                            prior_d1_body = "Inside"
                    else:
                        prior_d1_body = "—"

                    # Run v3 market structure
                    structure = get_market_structure(df)

                    # ── Phase 2: 09:00 price + RVOL ──
                    minute_data = fetch_minute_data(ticker, polygon, end_date)

                    # Use 09:00 bar close if available, otherwise D1 close
                    current_price = minute_data["price_0900"] or d1_close
                    price_source = "09:00" if minute_data["price_0900"] else "D1"

                    # Overnight gap: 09:00 price vs D1 close
                    if price_source == "09:00" and d1_close > 0:
                        gap_pct = round((current_price - d1_close) / d1_close * 100, 2)
                    else:
                        gap_pct = 0.0

                    # Classify using current_price (09:00 bar when available)
                    state = classify_ticker(
                        structure.direction,
                        structure.strong_level,
                        structure.weak_level,
                        current_price,
                    )

                    row = {
                        "ticker": ticker,
                        "price": current_price,
                        "d1_close": d1_close,
                        "price_source": price_source,
                        "gap_pct": gap_pct,
                        "direction": structure.label,
                        "strong": structure.strong_level,
                        "weak": structure.weak_level,
                        "state": state,
                        "atr": round(atr, 2),
                        "prior_d1_body": prior_d1_body,
                        "rvol_pct": minute_data["rvol_pct"],
                    }

                    # Score inline
                    score_ticker(row)

                    return row
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

            # Sort: score descending, then state priority, then ticker
            state_order = {
                "Out - Strong": 0, "Out - Weak": 1,
                "Bull": 2, "Bear": 3,
                "Bull (Low)": 4, "Bear (High)": 5,
                "Neutral": 6,
            }
            results.sort(key=lambda r: (-r.get("score", 0),
                                        state_order.get(r["state"], 9),
                                        r["ticker"]))

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

        # Row 2 — Inside Prior Day filter
        self.hide_inside_check = QCheckBox("Hide Inside Prior Day Bar")
        self.hide_inside_check.setToolTip(
            "Remove tickers whose current price is inside the prior day's open-close body"
        )
        self.hide_inside_check.stateChanged.connect(self._on_filter_changed)
        grid.addWidget(self.hide_inside_check, 2, 0, 1, 2)

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

        # ── Top 10 Shortlist ──────────────────────────────────────────────
        shortlist_frame, shortlist_layout = self.create_section_frame(
            "Top 10 Shortlist  —  Score = S(tructure) + A(lignment) + G(ap) + R(VOL) + Z(one)  max ~105"
        )
        layout.addWidget(shortlist_frame)

        shortlist_row = QHBoxLayout()
        shortlist_row.setSpacing(16)
        shortlist_layout.addLayout(shortlist_row)

        # Bull shortlist
        bull_col = QVBoxLayout()
        bull_label = QLabel("Top 10 BULL")
        bull_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        bull_label.setStyleSheet(f"color: {COLORS['bull']};")
        bull_col.addWidget(bull_label)

        self._shortlist_headers = [
            "#", "Ticker", "Price", "Score",
            "S", "A", "G", "R", "Z",
            "Gap%", "RVOL%", "State",
        ]
        self._shortlist_widths = [30, 65, 80, 50, 30, 30, 30, 30, 30, 60, 60, 100]

        self.bull_table = self.create_table(
            headers=self._shortlist_headers,
            column_widths=self._shortlist_widths,
        )
        self.bull_table.setMaximumHeight(320)
        bull_col.addWidget(self.bull_table)
        shortlist_row.addLayout(bull_col)

        # Bear shortlist
        bear_col = QVBoxLayout()
        bear_label = QLabel("Top 10 BEAR")
        bear_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        bear_label.setStyleSheet(f"color: {COLORS['bear']};")
        bear_col.addWidget(bear_label)

        self.bear_table = self.create_table(
            headers=self._shortlist_headers,
            column_widths=self._shortlist_widths,
        )
        self.bear_table.setMaximumHeight(320)
        bear_col.addWidget(self.bear_table)
        shortlist_row.addLayout(bear_col)

        # ── Results Table ────────────────────────────────────────────────
        results_frame, results_layout = self.create_section_frame("Full Scan Results")
        layout.addWidget(results_frame)

        self.results_summary = QLabel("No scan results yet")
        self.results_summary.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 12px;"
        )
        results_layout.addWidget(self.results_summary)

        self.results_table = self.create_table(
            headers=[
                "Ticker", "Price", "Score", "Direction", "Strong", "Weak",
                "State", "Prior D1", "ATR", "RVOL%", "Gap%",
            ],
            column_widths=[80, 90, 60, 80, 100, 100, 120, 80, 70, 70, 70],
        )
        results_layout.addWidget(self.results_table)

        layout.addStretch()

        # Worker reference
        self._worker: Optional[StructureScreenerWorker] = None
        self._live_results: List[dict] = []
        self._all_results: List[dict] = []

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
        self.bull_table.setRowCount(0)
        self.bear_table.setRowCount(0)
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
        self.bull_table.setRowCount(0)
        self.bear_table.setRowCount(0)
        self.results_summary.setText("No scan results")
        self.progress_bar.setValue(0)
        self.status_label.setText("Ready")
        self._live_results = []
        self._all_results = []
        self._update_metrics([])

    def _apply_filters(self, results: list) -> list:
        """Apply UI filters to results list."""
        filtered = results
        if self.hide_inside_check.isChecked():
            filtered = [r for r in filtered if r.get("prior_d1_body") != "Inside"]
        return filtered

    def _on_filter_changed(self):
        """Re-populate table when filter toggles change."""
        if self._all_results:
            filtered = self._apply_filters(self._all_results)
            self._populate_results(filtered)
            self._update_metrics(filtered)
            self.results_summary.setText(
                f"{len(filtered)} of {len(self._all_results)} tickers shown"
            )
            self.status_label.setText(
                f"Filtered — {len(filtered)} of {len(self._all_results)} results"
            )

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
            self._all_results = []
            self._update_metrics([])
            self.bull_table.setRowCount(0)
            self.bear_table.setRowCount(0)
            return

        self._all_results = results
        filtered = self._apply_filters(results)

        # Populate shortlists (unfiltered — shows best regardless of Inside toggle)
        self._populate_shortlists(results)

        # Populate full results table
        self._populate_results(filtered)
        self._update_metrics(filtered)

        # Price source stats
        p0900 = sum(1 for r in filtered if r.get("price_source") == "09:00")
        p_d1 = sum(1 for r in filtered if r.get("price_source") == "D1")

        self.status_label.setText(f"Scan complete — {len(filtered)} of {len(results)} results")
        self.results_summary.setText(
            f"{len(filtered)} tickers classified  |  "
            f"Price: {p0900} @ 09:00,  {p_d1} @ D1 close"
        )

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

            # RVOL display
            rvol = r.get("rvol_pct")
            rvol_str = f"{rvol:.0f}%" if rvol is not None and rvol > 0 else "—"

            # Gap display
            if r.get("price_source") == "09:00":
                gap_str = f"{r.get('gap_pct', 0.0):+.1f}%"
            else:
                gap_str = "—"

            table_data.append([
                r["ticker"],
                f"${r['price']:.2f}",
                str(r.get("score", 0)),
                r["direction"],
                strong_str,
                weak_str,
                r["state"],
                r.get("prior_d1_body", "—"),
                f"${r['atr']:.2f}",
                rvol_str,
                gap_str,
            ])
            colors.append(self._STATE_COLORS.get(r["state"]))

        self.populate_table(self.results_table, table_data, colors)

    def _populate_shortlists(self, results: list):
        """Populate Top 10 Bull and Top 10 Bear shortlist tables."""
        scoreable = [r for r in results if r.get("score", 0) > 0]

        bulls = sorted([r for r in scoreable if r["direction"] == "BULL"],
                       key=lambda r: r["score"], reverse=True)[:10]
        bears = sorted([r for r in scoreable if r["direction"] == "BEAR"],
                       key=lambda r: r["score"], reverse=True)[:10]

        self._fill_shortlist_table(self.bull_table, bulls)
        self._fill_shortlist_table(self.bear_table, bears)

    def _fill_shortlist_table(self, table, top_list: list):
        """Fill a shortlist table with ranked results."""
        table_data = []
        colors = []

        for rank, r in enumerate(top_list, 1):
            sd = r.get("score_detail", {})

            # Gap display
            if r.get("price_source") == "09:00":
                gap_str = f"{r.get('gap_pct', 0.0):+.1f}%"
            else:
                gap_str = "—"

            # RVOL display
            rvol = r.get("rvol_pct")
            rvol_str = f"{rvol:.0f}%" if rvol is not None and rvol > 0 else "—"

            table_data.append([
                str(rank),
                r["ticker"],
                f"${r['price']:.2f}",
                str(r.get("score", 0)),
                str(sd.get("S", 0)),
                str(sd.get("A", 0)),
                str(sd.get("G", 0)),
                str(sd.get("R", 0)),
                str(sd.get("Z", 0)),
                gap_str,
                rvol_str,
                r["state"],
            ])
            colors.append(self._STATE_COLORS.get(r["state"]))

        self.populate_table(table, table_data, colors)

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
