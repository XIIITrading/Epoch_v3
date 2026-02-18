"""
Epoch Trading System - Journal Viewer Main Window
XIII Trading LLC

1:1 clone of 11_trade_reel/ui/main_window.py adapted for journal trades.
Uses FilterPanel + TradeTable (left) | ChartPreview (right, scrollable).

Layout:
    JournalViewerWindow (QMainWindow, 1600x950)
    +-- Left Combined (fixed width)
    |   +-- FilterPanel (260px)
    |   +-- TradeTable (fixed columns, with checkboxes)
    +-- Right Panel (expandable, scrollable)
    |   +-- ChartPreview (6-row layout)
    +-- ExportBar (Discord export button, select/deselect)
    +-- Status Bar

Threading:
    - TradeLoadThread:  Background DB query via JournalTradeLoader
    - BarFetchThread:   Fetch Weekly/Daily/H1/M15/M5/M1 bars + zones + POCs
                        + rampup + posttrade indicator data + VbP
    - ExportThread:     Export checked trades as Discord images (4 PNGs each)
    - Cache:            {trade_id: full bar/chart data tuple} for instant revisit
    - Figure Cache:     {trade_id: built Plotly figures + DataFrames} for export

Charts (imported from 11_trade_reel):
    - Weekly, Daily, H1 Prior, M15 Prior, M5 Entry, M1 Ramp-Up

Journal-specific chart:
    - M1 Action (from charts/m1_journal_chart.py) with multiple exit triangles,
      all R-level lines drawn, window = entry-30 to last_exit+30
"""

import sys
import logging
from typing import List, Optional, Dict
from pathlib import Path
from datetime import datetime, date, time, timedelta

import pandas as pd
import pytz

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QStatusBar,
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont

from .config import TV_COLORS, TV_DARK_QSS, DISPLAY_TIMEZONE, TRADE_REEL_DIR, EXPORT_DIR
from .filter_panel import FilterPanel
from .trade_table import TradeTable, COL_WIDTHS
from .chart_preview import ChartPreview
from .export_bar import ExportBar
from .trade_adapter import build_journal_highlight, JournalHighlight
from .bar_fetcher import fetch_bars, fetch_daily_bars
from .rampup_table import fetch_rampup_data
from .posttrade_table import fetch_posttrade_data

# Add 11_trade_reel to path for chart imports
sys.path.insert(0, str(TRADE_REEL_DIR))

# Import chart builders from 11_trade_reel (no duplication)
from charts import theme  # noqa: F401 - registers tradingview_dark template
from charts.volume_profile import build_volume_profile
from charts.weekly_chart import build_weekly_chart
from charts.daily_chart import build_daily_chart
from charts.h1_chart import build_h1_chart
from charts.m15_chart import build_m15_chart
from charts.m5_entry_chart import build_m5_entry_chart
from charts.m1_rampup_chart import build_m1_rampup_chart
from export.image_exporter import export_highlight_image

# Import journal-specific M1 chart via importlib to avoid namespace collision
# (both 11_trade_reel/charts/ and 08_journal/charts/ would conflict as 'charts')
import importlib.util as _ilu
_journal_chart_path = Path(__file__).parent.parent / "charts" / "m1_journal_chart.py"
_spec = _ilu.spec_from_file_location("m1_journal_chart", str(_journal_chart_path))
_m1_journal_mod = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_m1_journal_mod)
build_m1_journal_chart = _m1_journal_mod.build_m1_journal_chart

# Import JournalTradeLoader
sys.path.insert(0, str(Path(__file__).parent.parent))
from data.journal_loader import get_journal_loader, JournalTradeLoader

logger = logging.getLogger(__name__)

_TZ = pytz.timezone(DISPLAY_TIMEZONE)


# =============================================================================
# WEEKLY BAR FETCHER (Polygon API)
# =============================================================================

def _fetch_weekly_bars(ticker: str, end_date: date, lookback_weeks: int = 100) -> pd.DataFrame:
    """Fetch weekly bars from Polygon API."""
    import requests
    import time as time_module
    from .config import POLYGON_API_KEY, API_DELAY, API_RETRIES, API_RETRY_DELAY

    start = end_date - timedelta(weeks=lookback_weeks)
    url = (
        f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range"
        f"/1/week/{start:%Y-%m-%d}/{end_date:%Y-%m-%d}"
    )
    params = {'apiKey': POLYGON_API_KEY, 'adjusted': 'true', 'sort': 'asc', 'limit': 50000}

    for attempt in range(API_RETRIES):
        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            if data.get('status') not in ('OK', 'DELAYED') or not data.get('results'):
                return pd.DataFrame()

            df = pd.DataFrame(data['results'])
            df = df.rename(columns={'t': 'timestamp', 'o': 'open', 'h': 'high', 'l': 'low', 'c': 'close', 'v': 'volume'})
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
            df['timestamp'] = df['timestamp'].dt.tz_convert(DISPLAY_TIMEZONE)
            df.set_index('timestamp', inplace=True)
            df = df[['open', 'high', 'low', 'close', 'volume']]

            time_module.sleep(API_DELAY)
            return df

        except requests.exceptions.RequestException as e:
            logger.warning(f"Weekly bar fetch attempt {attempt + 1} failed: {e}")
            if attempt < API_RETRIES - 1:
                time_module.sleep(API_RETRY_DELAY)
        except Exception as e:
            logger.error(f"Unexpected weekly bar fetch error: {e}")
            break

    return pd.DataFrame()


# =============================================================================
# INTRADAY VBP HELPER
# =============================================================================

def _compute_intraday_vbp(bars_m1: pd.DataFrame, highlight: JournalHighlight) -> dict:
    """
    Compute intraday value volume profile from M1 bars: 04:00 ET -> entry_time.
    Used for the M1 ramp-up chart sidebar.
    """
    if bars_m1 is None or bars_m1.empty or not highlight.entry_time:
        return {}

    try:
        start_dt = _TZ.localize(datetime.combine(
            highlight.date,
            datetime.min.time().replace(hour=4, minute=0),
        ))
        entry_dt = _TZ.localize(datetime.combine(highlight.date, highlight.entry_time))

        mask = (bars_m1.index >= start_dt) & (bars_m1.index < entry_dt)
        intraday_bars = bars_m1.loc[mask]

        if intraday_bars.empty:
            return {}

        return build_volume_profile(intraday_bars)
    except Exception as e:
        logger.warning(f"Intraday VbP computation failed: {e}")
        return {}


# =============================================================================
# H1 / M15 PRIOR BUILDERS
# =============================================================================

def _build_h1_prior_fig(bars_h1, highlight, zones, pocs, vp_dict):
    """Build H1 chart sliced to end at 08:00 bar (covering 08:00-09:00).
    Fixed cutoff at 08:00 regardless of entry time.
    """
    if bars_h1 is None or (isinstance(bars_h1, pd.DataFrame) and bars_h1.empty):
        logger.warning(f"H1 prior: no bars available for {highlight.ticker}")
        return build_h1_chart(bars_h1, highlight, zones, pocs=pocs, volume_profile_dict=vp_dict)

    cutoff = _TZ.localize(datetime.combine(
        highlight.date,
        datetime.min.time().replace(hour=8, minute=0),
    ))
    h1_prior = bars_h1[bars_h1.index <= cutoff]

    if h1_prior.empty:
        logger.warning(f"H1 prior: cutoff {cutoff} filtered out all {len(bars_h1)} bars, showing all")
        return build_h1_chart(bars_h1, highlight, zones, pocs=pocs, volume_profile_dict=vp_dict)

    h1_hours = h1_prior.index.hour
    premarket_count = int((h1_hours < 9).sum())
    afterhours_count = int((h1_hours >= 16).sum())
    logger.info(
        f"H1 prior: {len(h1_prior)} bars after cutoff (tail 120), "
        f"premarket={premarket_count}, afterhours={afterhours_count}, "
        f"range={h1_prior.index[0]} -> {h1_prior.index[-1]}"
    )
    return build_h1_chart(h1_prior, highlight, zones, pocs=pocs, volume_profile_dict=vp_dict)


def _build_m15_prior_fig(bars_m15, highlight, zones, pocs, vp_dict):
    """Build M15 chart sliced to end at 09:15 bar (covering 09:15-09:30).
    Fixed cutoff at 09:15 regardless of entry time.
    """
    if bars_m15 is None or (isinstance(bars_m15, pd.DataFrame) and bars_m15.empty):
        logger.warning(f"M15 prior: no bars available for {highlight.ticker}")
        return build_m15_chart(bars_m15, highlight, zones, pocs=pocs, volume_profile_dict=vp_dict)

    cutoff = _TZ.localize(datetime.combine(
        highlight.date,
        datetime.min.time().replace(hour=9, minute=15),
    ))
    m15_prior = bars_m15[bars_m15.index <= cutoff]

    if m15_prior.empty:
        logger.warning(f"M15 prior: cutoff {cutoff} filtered out all {len(bars_m15)} bars, showing all")
        return build_m15_chart(bars_m15, highlight, zones, pocs=pocs, volume_profile_dict=vp_dict)

    m15_hours = m15_prior.index.hour
    premarket_count = int((m15_hours < 9).sum())
    afterhours_count = int((m15_hours >= 16).sum())
    logger.info(
        f"M15 prior: {len(m15_prior)} bars after cutoff (tail 90), "
        f"premarket={premarket_count}, afterhours={afterhours_count}, "
        f"range={m15_prior.index[0]} -> {m15_prior.index[-1]}"
    )
    return build_m15_chart(m15_prior, highlight, zones, pocs=pocs, volume_profile_dict=vp_dict)


# =============================================================================
# BACKGROUND THREADS
# =============================================================================

class TradeLoadThread(QThread):
    """Load journal trades from database in background via JournalTradeLoader."""

    finished = pyqtSignal(list)     # List[JournalHighlight]
    error = pyqtSignal(str)

    def __init__(self, loader: JournalTradeLoader, filters: dict, parent=None):
        super().__init__(parent)
        self._loader = loader
        self._filters = filters

    def run(self):
        try:
            rows = self._loader.fetch_trades(
                date_from=self._filters.get('date_from'),
                date_to=self._filters.get('date_to'),
                symbol=self._filters.get('ticker'),
                direction=self._filters.get('direction'),
                account=self._filters.get('account'),
            )

            # Convert raw DB rows into JournalHighlight objects
            highlights = []
            for row in rows:
                try:
                    hl = build_journal_highlight(row=row)
                    highlights.append(hl)
                except Exception as e:
                    logger.warning(f"Failed to build highlight for {row.get('trade_id', '?')}: {e}")

            self.finished.emit(highlights)
        except Exception as e:
            self.error.emit(str(e))


class BarFetchThread(QThread):
    """
    Fetch Weekly/Daily/H1/M15/M5/M1 bars + zones + POCs + rampup + posttrade
    + VbP from Polygon + DB.

    Emits 12 objects matching trade_reel pattern:
        bars_weekly, bars_daily, bars_h1, bars_m15, bars_m5, bars_m1,
        zones, pocs, rampup_df, posttrade_df, vbp_bars, anchor_date
    """

    finished = pyqtSignal(
        object, object, object, object, object, object,
        list, list, object, object, object, object,
    )
    error = pyqtSignal(str)

    def __init__(self, highlight: JournalHighlight, loader: JournalTradeLoader, parent=None):
        super().__init__(parent)
        self._hl = highlight
        self._loader = loader

    def run(self):
        try:
            ticker = self._hl.ticker.upper().strip()
            trade_date = self._hl.date

            # Fetch anchor date (needed for daily chart + VbP)
            anchor_date = self._loader.fetch_epoch_start_date(ticker, trade_date)

            # Fetch weekly bars (100 weeks lookback)
            bars_weekly = _fetch_weekly_bars(ticker, trade_date, lookback_weeks=100)
            logger.info(f"Weekly: {ticker} ({len(bars_weekly)} bars)")

            # Fetch daily bars: epoch_start_date -> day before trade
            bars_daily = pd.DataFrame()
            if anchor_date:
                day_before = trade_date - timedelta(days=1)
                bars_daily = fetch_daily_bars(ticker, anchor_date, day_before)
                logger.info(f"Daily: {ticker} {anchor_date} -> {day_before} ({len(bars_daily)} bars)")

            # Fetch intraday bars for 4 timeframes
            bars_h1 = fetch_bars(ticker, trade_date, tf_minutes=60, lookback_days=50)
            if not bars_h1.empty:
                h1_hours = bars_h1.index.hour
                h1_premarket = int((h1_hours < 9).sum())
                h1_afterhours = int((h1_hours >= 16).sum())
                logger.info(
                    f"H1: {ticker} ({len(bars_h1)} bars, "
                    f"first={bars_h1.index[0]}, last={bars_h1.index[-1]}, "
                    f"premarket={h1_premarket}, afterhours={h1_afterhours})"
                )
            else:
                logger.warning(f"H1: {ticker} - NO BARS returned from Polygon")

            bars_m15 = fetch_bars(ticker, trade_date, tf_minutes=15, lookback_days=18)
            if not bars_m15.empty:
                m15_hours = bars_m15.index.hour
                m15_premarket = int((m15_hours < 9).sum())
                m15_afterhours = int((m15_hours >= 16).sum())
                logger.info(
                    f"M15: {ticker} ({len(bars_m15)} bars, "
                    f"first={bars_m15.index[0]}, last={bars_m15.index[-1]}, "
                    f"premarket={m15_premarket}, afterhours={m15_afterhours})"
                )
            else:
                logger.warning(f"M15: {ticker} - NO BARS returned from Polygon")

            bars_m5 = fetch_bars(ticker, trade_date, tf_minutes=5, lookback_days=3)
            bars_m1 = fetch_bars(ticker, trade_date, tf_minutes=1, lookback_days=2)

            # Fetch zones
            zones = self._loader.fetch_zones_for_trade(ticker, trade_date)

            # Fetch HVN POC prices
            pocs = self._loader.fetch_hvn_pocs(ticker, trade_date)
            logger.info(f"POCs: {ticker} {trade_date} -> {len(pocs)} POCs")

            # Fetch M1 ramp-up indicator data (up to entry)
            rampup_df = None
            if self._hl.entry_time:
                rampup_df = fetch_rampup_data(ticker, trade_date, self._hl.entry_time)

            # Fetch M1 post-trade indicator data (entry onward)
            posttrade_df = None
            if self._hl.entry_time:
                posttrade_df = fetch_posttrade_data(ticker, trade_date, self._hl.entry_time)

            # Fetch VbP bars from epoch anchor -> trade_date (M15 granularity)
            vbp_bars = pd.DataFrame()
            if anchor_date:
                lookback = (trade_date - anchor_date).days + 1
                vbp_bars = fetch_bars(ticker, trade_date, tf_minutes=15, lookback_days=lookback)
                logger.info(f"VbP: {ticker} anchor={anchor_date} -> {trade_date} ({lookback}d, {len(vbp_bars)} bars)")
            else:
                logger.warning(f"No epoch_start_date found for {ticker} {trade_date}, VbP will use display bars")

            self.finished.emit(
                bars_weekly, bars_daily, bars_h1, bars_m15, bars_m5, bars_m1,
                zones, pocs, rampup_df, posttrade_df, vbp_bars, anchor_date,
            )

        except Exception as e:
            logger.error(f"BarFetchThread error: {e}", exc_info=True)
            self.error.emit(str(e))


class ExportThread(QThread):
    """Export journal trade images in background.

    Uses pre-built figures from the UI cache when available.
    Falls back to full fetch + build for uncached highlights.
    Modeled on 11_trade_reel/ui/main_window.py ExportThread.
    """

    progress = pyqtSignal(int, int)       # current, total
    finished = pyqtSignal(int, str)       # count, output_dir
    error = pyqtSignal(str)

    def __init__(
        self,
        highlights: List[JournalHighlight],
        loader: 'JournalTradeLoader',
        platform: str,
        figs_cache: Optional[dict] = None,
        parent=None,
    ):
        super().__init__(parent)
        self._highlights = highlights
        self._loader = loader
        self._platform = platform
        self._figs_cache = figs_cache or {}

    def run(self):
        try:
            exported = 0
            total = len(self._highlights)
            out_dir = EXPORT_DIR / self._platform
            out_dir.mkdir(parents=True, exist_ok=True)

            for i, hl in enumerate(self._highlights):
                self.progress.emit(i + 1, total)

                # Use cached figures if available (built during UI preview)
                cached = self._figs_cache.get(hl.trade_id)
                if cached:
                    logger.info(f"Export {hl.ticker} {hl.date}: using cached figures")
                    paths = export_highlight_image(
                        cached['weekly_fig'],
                        cached['daily_fig'],
                        cached['h1_prior_fig'],
                        cached['m15_prior_fig'],
                        cached['m5_entry_fig'],
                        cached['m1_fig'],
                        cached['m1_rampup_fig'],
                        hl,
                        self._platform,
                        out_dir,
                        rampup_df=cached.get('rampup_df'),
                        posttrade_df=cached.get('posttrade_df'),
                    )
                    if paths:
                        exported += 1
                    continue

                # Fallback: full fetch + build for uncached highlights
                logger.info(f"Export {hl.ticker} {hl.date}: fetching data (not cached)")
                ticker = hl.ticker.upper().strip()
                trade_date = hl.date

                anchor_date = self._loader.fetch_epoch_start_date(ticker, trade_date)

                bars_weekly = _fetch_weekly_bars(ticker, trade_date, lookback_weeks=100)

                bars_daily = pd.DataFrame()
                if anchor_date:
                    day_before = trade_date - timedelta(days=1)
                    bars_daily = fetch_daily_bars(ticker, anchor_date, day_before)

                bars_h1 = fetch_bars(ticker, trade_date, tf_minutes=60, lookback_days=50)
                bars_m15 = fetch_bars(ticker, trade_date, tf_minutes=15, lookback_days=18)
                bars_m5 = fetch_bars(ticker, trade_date, tf_minutes=5, lookback_days=3)
                bars_m1 = fetch_bars(ticker, trade_date, tf_minutes=1, lookback_days=2)
                zones = self._loader.fetch_zones_for_trade(ticker, trade_date)
                pocs = self._loader.fetch_hvn_pocs(ticker, trade_date)

                rampup_df = None
                if hl.entry_time:
                    rampup_df = fetch_rampup_data(ticker, trade_date, hl.entry_time)

                posttrade_df = None
                if hl.entry_time:
                    posttrade_df = fetch_posttrade_data(ticker, trade_date, hl.entry_time)

                vbp_bars = pd.DataFrame()
                if anchor_date:
                    lookback = (trade_date - anchor_date).days + 1
                    vbp_bars = fetch_bars(ticker, trade_date, tf_minutes=15, lookback_days=lookback)

                if bars_m5.empty:
                    logger.warning(f"No M5 bars for {ticker}, skipping")
                    continue

                vbp_source = vbp_bars if not vbp_bars.empty else None
                vp_dict = build_volume_profile(vbp_source) if vbp_source is not None else {}

                weekly_fig = build_weekly_chart(bars_weekly, hl, zones)
                daily_fig = build_daily_chart(bars_daily, hl, zones, pocs=pocs, anchor_date=anchor_date, volume_profile_dict=vp_dict)
                h1_prior_fig = _build_h1_prior_fig(bars_h1, hl, zones, pocs, vp_dict)
                m15_prior_fig = _build_m15_prior_fig(bars_m15, hl, zones, pocs, vp_dict)
                m5_entry_fig = build_m5_entry_chart(bars_m5, hl, zones, pocs=pocs, volume_profile_dict=vp_dict)

                intraday_vbp = _compute_intraday_vbp(bars_m1, hl)
                m1_rampup_fig = build_m1_rampup_chart(bars_m1, hl, zones, pocs=pocs, intraday_vbp_dict=intraday_vbp)
                m1_fig = build_m1_journal_chart(bars_m1, hl, zones, pocs=pocs)

                paths = export_highlight_image(
                    weekly_fig, daily_fig, h1_prior_fig, m15_prior_fig, m5_entry_fig, m1_fig,
                    m1_rampup_fig, hl, self._platform, out_dir,
                    rampup_df=rampup_df,
                    posttrade_df=posttrade_df,
                )
                if paths:
                    exported += 1

            self.finished.emit(exported, str(out_dir))
        except Exception as e:
            self.error.emit(str(e))


# =============================================================================
# MAIN WINDOW
# =============================================================================

class JournalViewerWindow(QMainWindow):
    """Journal Viewer - Trade chart viewer for FIFO journal trades.

    1:1 layout clone of TradeReelWindow with journal-specific data sources.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Epoch Journal Viewer")
        self.resize(1600, 950)
        self.setStyleSheet(TV_DARK_QSS)

        self._loader = get_journal_loader()
        self._current_highlight: Optional[JournalHighlight] = None
        self._current_bars: Dict = {}  # {trade_id: (weekly, daily, h1, m15, m5, m1, zones, pocs, rampup_df, posttrade_df, vbp_bars, anchor_date)}
        self._current_figs: Dict = {}  # {trade_id: dict with built figures + DataFrames ready for export}
        self._active_threads: list = []

        self._setup_ui()
        self._connect_signals()

    # =========================================================================
    # UI SETUP
    # =========================================================================

    def _setup_ui(self):
        """Build the main layout matching trade_reel exactly."""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Splitter: left (filter + table) | right (chart preview)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ---- Left Combined: FilterPanel + TradeTable ----
        left_combined = QWidget()
        left_combined_layout = QHBoxLayout(left_combined)
        left_combined_layout.setContentsMargins(0, 0, 0, 0)
        left_combined_layout.setSpacing(0)

        self._filter_panel = FilterPanel()
        left_combined_layout.addWidget(self._filter_panel)

        self._trade_table = TradeTable()
        left_combined_layout.addWidget(self._trade_table)

        # Lock left side to exact width of its fixed-width children
        left_combined.setFixedWidth(260 + sum(COL_WIDTHS.values()) + 2)

        # ---- Right: Chart Preview ----
        self._chart_preview = ChartPreview()

        splitter.addWidget(left_combined)
        splitter.addWidget(self._chart_preview)
        splitter.setSizes([500, 1100])

        main_layout.addWidget(splitter, stretch=1)

        # Bottom: Export bar
        self._export_bar = ExportBar()
        main_layout.addWidget(self._export_bar)

        # Status bar
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready - Select date range and click LOAD TRADES")

    def _connect_signals(self):
        """Wire up all panel signals."""
        # Filter -> load trades
        self._filter_panel.load_requested.connect(self._on_load_trades)

        # Table row click -> fetch bars + preview
        self._trade_table.selection_changed.connect(self._on_trade_selected)

        # Checkbox changes -> enable/disable export
        self._trade_table.checked_changed.connect(self._on_checked_changed)

        # Export bar buttons
        self._export_bar.export_requested.connect(self._on_export_requested)
        self._export_bar.select_all_btn.clicked.connect(self._trade_table.select_all)
        self._export_bar.deselect_btn.clicked.connect(self._trade_table.deselect_all)

    # =========================================================================
    # LOAD TRADES
    # =========================================================================

    def _on_load_trades(self, filters: dict):
        """Start background trade loading."""
        self._filter_panel.set_loading(True)
        self._chart_preview.show_placeholder()
        self._export_bar.clear_status()

        thread = TradeLoadThread(self._loader, filters, parent=self)
        thread.finished.connect(self._on_trades_loaded)
        thread.error.connect(self._on_trades_error)
        thread.finished.connect(lambda: self._cleanup_thread(thread))
        thread.error.connect(lambda: self._cleanup_thread(thread))
        self._active_threads.append(thread)
        thread.start()

    def _on_trades_loaded(self, highlights: List[JournalHighlight]):
        """Handle loaded highlights."""
        self._filter_panel.set_loading(False)

        # Deduplicate: roll entry_time up to the minute, keep first per group
        seen = set()
        unique = []
        for hl in highlights:
            key = (hl.date, hl.ticker, hl.direction,
                   hl.entry_time.hour if hl.entry_time else None,
                   hl.entry_time.minute if hl.entry_time else None)
            if key not in seen:
                seen.add(key)
                unique.append(hl)
        highlights = unique

        self._trade_table.set_trades(highlights)
        self._filter_panel.update_results_info(len(highlights))
        self._export_bar.set_export_enabled(False)

        # Update ticker dropdown from results
        tickers = sorted(set(hl.ticker for hl in highlights))
        self._filter_panel.populate_tickers(tickers)

        # Update account dropdown from results
        # (accounts come from the loader, not highlights)
        try:
            accounts = self._loader.get_available_accounts()
            self._filter_panel.populate_accounts(accounts)
        except Exception:
            pass

        if highlights:
            self.statusBar().showMessage(f"Loaded {len(highlights)} journal trades")
        else:
            self.statusBar().showMessage("No trades found for the selected filters")

    def _on_trades_error(self, error: str):
        """Handle trade loading error."""
        self._filter_panel.set_loading(False)
        self.statusBar().showMessage(f"Error: {error}")
        logger.error(f"Trade load error: {error}")

    # =========================================================================
    # SELECT TRADE -> FETCH BARS -> RENDER CHARTS
    # =========================================================================

    def _on_trade_selected(self, highlight):
        """Handle table row selection - fetch bars and render charts."""
        if highlight is None:
            self._chart_preview.show_placeholder()
            self._current_highlight = None
            return

        self._current_highlight = highlight

        # Check cache
        if highlight.trade_id in self._current_bars:
            cached = self._current_bars[highlight.trade_id]
            weekly, daily, h1, m15, m5, m1, zones, pocs, rampup_df, posttrade_df, vbp_bars, anchor_date = cached
            self._render_charts(
                highlight, weekly, daily, h1, m15, m5, m1,
                zones, pocs, rampup_df, posttrade_df, vbp_bars, anchor_date,
            )
            return

        # Fetch bars in background
        self._chart_preview.show_loading()
        self.statusBar().showMessage(f"Fetching bars for {highlight.ticker} {highlight.date}...")

        thread = BarFetchThread(highlight, self._loader, parent=self)
        thread.finished.connect(
            lambda w, d, h1, m15, m5, m1, z, p, r, pt, vbp, anch:
                self._on_bars_fetched(highlight, w, d, h1, m15, m5, m1, z, p, r, pt, vbp, anch)
        )
        thread.error.connect(self._on_bars_error)
        thread.finished.connect(lambda *_: self._cleanup_thread(thread))
        thread.error.connect(lambda: self._cleanup_thread(thread))
        self._active_threads.append(thread)
        thread.start()

    def _on_bars_fetched(self, highlight, bars_weekly, bars_daily, bars_h1, bars_m15,
                         bars_m5, bars_m1, zones, pocs, rampup_df, posttrade_df,
                         vbp_bars, anchor_date):
        """Handle fetched bar data."""
        # Cache the bars
        self._current_bars[highlight.trade_id] = (
            bars_weekly, bars_daily, bars_h1, bars_m15, bars_m5, bars_m1,
            zones, pocs, rampup_df, posttrade_df, vbp_bars, anchor_date,
        )

        # If highlight didn't have pre-computed ATR data, compute on-the-fly
        if highlight.stop_price is None and bars_m5 is not None and not bars_m5.empty:
            highlight = build_journal_highlight(
                row=self._highlight_to_row(highlight),
                bars_m5=bars_m5,
                bars_m1=bars_m1,
                zones=zones,
            )
            # Update cache with enriched highlight
            self._current_bars[highlight.trade_id] = (
                bars_weekly, bars_daily, bars_h1, bars_m15, bars_m5, bars_m1,
                zones, pocs, rampup_df, posttrade_df, vbp_bars, anchor_date,
            )

        # Only render if this is still the selected highlight
        if self._current_highlight and self._current_highlight.trade_id == highlight.trade_id:
            self._current_highlight = highlight
            self._render_charts(
                highlight, bars_weekly, bars_daily, bars_h1, bars_m15, bars_m5, bars_m1,
                zones, pocs, rampup_df, posttrade_df, vbp_bars, anchor_date,
            )

    def _render_charts(self, highlight, bars_weekly, bars_daily, bars_h1, bars_m15,
                       bars_m5, bars_m1, zones, pocs=None, rampup_df=None,
                       posttrade_df=None, vbp_bars=None, anchor_date=None):
        """Build and display all charts for a highlight."""
        try:
            if bars_m5 is None or (isinstance(bars_m5, pd.DataFrame) and bars_m5.empty):
                self._chart_preview.show_error("No M5 bar data available")
                return

            # Compute volume profile ONCE from VbP source bars
            vbp_source = vbp_bars if (vbp_bars is not None and not vbp_bars.empty) else None
            vp_dict = build_volume_profile(vbp_source) if vbp_source is not None else {}

            # Build all 7 charts

            # Row 1: Weekly + Daily
            weekly_fig = build_weekly_chart(bars_weekly, highlight, zones)
            daily_fig = build_daily_chart(
                bars_daily, highlight, zones,
                pocs=pocs, anchor_date=anchor_date, volume_profile_dict=vp_dict,
            )

            # Row 2: H1 Prior + M15 Prior
            h1_prior_fig = _build_h1_prior_fig(bars_h1, highlight, zones, pocs, vp_dict)
            m15_prior_fig = _build_m15_prior_fig(bars_m15, highlight, zones, pocs, vp_dict)

            # Row 3: M5 Entry + M1 Ramp-Up
            m5_entry_fig = build_m5_entry_chart(
                bars_m5, highlight, zones,
                pocs=pocs, volume_profile_dict=vp_dict,
            )

            # Compute intraday VbP (04:00 ET -> entry) for M1 ramp-up chart
            intraday_vbp = _compute_intraday_vbp(bars_m1, highlight)
            m1_rampup_fig = build_m1_rampup_chart(
                bars_m1, highlight, zones,
                pocs=pocs, intraday_vbp_dict=intraday_vbp,
            )

            # Row 6: M1 Journal Action chart (journal-specific, not trade_reel M1)
            m1_fig = build_m1_journal_chart(bars_m1, highlight, zones, pocs=pocs)

            # Render all charts to the preview panel
            self._chart_preview.show_charts(
                weekly_fig, daily_fig, h1_prior_fig, m15_prior_fig,
                m5_entry_fig, m1_rampup_fig, m1_fig, highlight,
            )

            # Cache built figures for export (avoids re-fetching + rebuilding)
            self._current_figs[highlight.trade_id] = {
                'weekly_fig': weekly_fig,
                'daily_fig': daily_fig,
                'h1_prior_fig': h1_prior_fig,
                'm15_prior_fig': m15_prior_fig,
                'm5_entry_fig': m5_entry_fig,
                'm1_fig': m1_fig,
                'm1_rampup_fig': m1_rampup_fig,
                'rampup_df': rampup_df,
                'posttrade_df': posttrade_df,
                'highlight': highlight,
            }

            # Row 4: Ramp-up indicator table
            if rampup_df is not None:
                self._chart_preview.show_rampup(rampup_df)

            # Row 5: Post-trade indicator table
            if posttrade_df is not None:
                self._chart_preview.show_posttrade(posttrade_df)

            # Status bar summary
            dir_str = highlight.direction
            pnl_str = f"{highlight.pnl_r:+.2f}R" if highlight.pnl_r else ""
            pnl_dollar_str = f"${highlight.pnl_dollars:+.2f}" if highlight.pnl_dollars else ""
            atr_str = f"ATR ${highlight.m5_atr_value:.4f}" if highlight.m5_atr_value else "ATR N/A"

            self.statusBar().showMessage(
                f"{highlight.ticker} {highlight.date} - {highlight.star_display} | "
                f"{dir_str} | Entry ${highlight.entry_price:.2f} | "
                f"{atr_str} | {pnl_str} {pnl_dollar_str}"
            )

        except Exception as e:
            self._chart_preview.show_error(str(e))
            logger.error(f"Chart render error: {e}", exc_info=True)

    def _on_bars_error(self, error: str):
        """Handle bar fetch error."""
        self._chart_preview.show_error(error)
        self.statusBar().showMessage(f"Error fetching bars: {error}")

    # =========================================================================
    # EXPORT
    # =========================================================================

    def _on_checked_changed(self, checked_ids: list):
        """Enable/disable export based on selections."""
        self._export_bar.set_export_enabled(len(checked_ids) > 0)

    def _on_export_requested(self, platform: str):
        """Start export for selected highlights."""
        checked = self._trade_table.get_checked_highlights()
        if not checked:
            self.statusBar().showMessage("No trades selected for export")
            return

        self._export_bar.set_exporting(True)
        self.statusBar().showMessage(f"Exporting {len(checked)} trades for {platform}...")

        thread = ExportThread(checked, self._loader, platform, figs_cache=self._current_figs, parent=self)
        thread.progress.connect(self._export_bar.show_export_progress)
        thread.finished.connect(lambda count, path: self._on_export_finished(count, path, platform))
        thread.error.connect(self._on_export_error)
        thread.finished.connect(lambda *_: self._cleanup_thread(thread))
        thread.error.connect(lambda: self._cleanup_thread(thread))
        self._active_threads.append(thread)
        thread.start()

    def _on_export_finished(self, count: int, output_dir: str, platform: str):
        """Handle export completion."""
        self._export_bar.set_exporting(False)
        self._export_bar.show_export_result(count, output_dir)
        self.statusBar().showMessage(f"Exported {count} images for {platform}")

    def _on_export_error(self, error: str):
        """Handle export error."""
        self._export_bar.set_exporting(False)
        self.statusBar().showMessage(f"Export error: {error}")
        logger.error(f"Export error: {error}")

    # =========================================================================
    # HELPERS
    # =========================================================================

    @staticmethod
    def _highlight_to_row(hl: JournalHighlight) -> Dict:
        """Convert a JournalHighlight back to a dict for re-processing through build_journal_highlight."""
        import json
        row = {
            'trade_id': hl.trade_id,
            'trade_date': hl.date,
            'symbol': hl.ticker,
            'direction': hl.direction,
            'entry_price': hl.entry_price,
            'entry_time': hl.entry_time,
            'exit_price': hl.exit_price,
            'exit_time': hl.exit_time,
            'pnl_dollars': hl.pnl_dollars,
            'entry_qty': hl.entry_qty,
            'exit_portions_json': json.dumps(hl.exit_portions) if hl.exit_portions else None,
        }
        # Carry over any pre-computed ATR data
        if hl.m5_atr_value is not None:
            row['m5_atr_value'] = hl.m5_atr_value
            row['stop_price'] = hl.stop_price
            row['stop_distance'] = hl.stop_distance
            row['r1_price'] = hl.r1_price
            row['r2_price'] = hl.r2_price
            row['r3_price'] = hl.r3_price
            row['r4_price'] = hl.r4_price
            row['r5_price'] = hl.r5_price
            row['r1_hit'] = hl.r1_hit
            row['r2_hit'] = hl.r2_hit
            row['r3_hit'] = hl.r3_hit
            row['r4_hit'] = hl.r4_hit
            row['r5_hit'] = hl.r5_hit
            row['r1_time'] = hl.r1_time
            row['r2_time'] = hl.r2_time
            row['r3_time'] = hl.r3_time
            row['r4_time'] = hl.r4_time
            row['r5_time'] = hl.r5_time
            row['stop_hit'] = hl.stop_hit
            row['stop_hit_time'] = hl.stop_hit_time
            row['max_r_achieved'] = hl.max_r_achieved
            row['pnl_r'] = hl.pnl_r
        return row

    # =========================================================================
    # CLEANUP
    # =========================================================================

    def _cleanup_thread(self, thread):
        """Remove finished thread from active list."""
        if thread in self._active_threads:
            self._active_threads.remove(thread)

    def closeEvent(self, event):
        """Clean up on window close."""
        # Wait for active threads
        for thread in self._active_threads:
            thread.quit()
            thread.wait(2000)
        self._active_threads.clear()

        # Disconnect DB
        if self._loader:
            self._loader.disconnect()

        super().closeEvent(event)
