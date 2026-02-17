"""
Epoch Trading System - Trade Reel Main Window
TradeReelWindow with 3 QThreads for DB loading, bar fetching, and exporting.
"""

import logging
from typing import List, Optional
from pathlib import Path

import pandas as pd
import requests
import time as time_module
from datetime import datetime, date, timedelta

from PyQt6.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QWidget, QSplitter, QMessageBox,
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt

import sys
import types
import importlib.util

MODULE_DIR = Path(__file__).parent.parent
SHARED_DIR = MODULE_DIR.parent / '00_shared'


# 11_trade_reel/ui/ and 00_shared/ui/ both exist as 'ui' packages.
# Load BaseWindow from 00_shared/ui/ via explicit file path to avoid collision.
def _load_base_window():
    shared_ui_dir = str(SHARED_DIR / 'ui')
    pkg = types.ModuleType('_shared_ui')
    pkg.__path__ = [shared_ui_dir]
    pkg.__package__ = '_shared_ui'
    sys.modules['_shared_ui'] = pkg

    for name in ('styles', 'base_window'):
        spec = importlib.util.spec_from_file_location(
            f'_shared_ui.{name}',
            str(SHARED_DIR / 'ui' / f'{name}.py'),
        )
        mod = importlib.util.module_from_spec(spec)
        mod.__package__ = '_shared_ui'
        sys.modules[f'_shared_ui.{name}'] = mod
        spec.loader.exec_module(mod)

    return sys.modules['_shared_ui.base_window'].BaseWindow


BaseWindow = _load_base_window()

# Module-level imports (app.py adds MODULE_DIR to sys.path)
import pytz

from config import (
    TV_DARK_QSS, POLYGON_API_KEY, API_DELAY, API_RETRIES,
    API_RETRY_DELAY, DISPLAY_TIMEZONE, EXPORT_DIR, TV_COLORS,
)

_TZ = pytz.timezone(DISPLAY_TIMEZONE)
from data.highlight_loader import get_highlight_loader, HighlightLoader
from models.highlight import HighlightTrade
from charts import theme  # noqa: F401 - registers tradingview_dark template
from charts.volume_profile import build_volume_profile
from charts.weekly_chart import build_weekly_chart
from charts.daily_chart import build_daily_chart
from charts.h1_chart import build_h1_chart
from charts.m15_chart import build_m15_chart
from charts.m5_entry_chart import build_m5_entry_chart
from charts.m1_chart import build_m1_chart
from charts.m1_rampup_chart import build_m1_rampup_chart
from export.image_exporter import export_highlight_image

from ui.filter_panel import FilterPanel
from ui.highlight_table import HighlightTable, COL_WIDTHS
from ui.chart_preview import ChartPreview
from ui.export_bar import ExportBar, PLATFORM_STYLES
from ui.rampup_table import fetch_rampup_data
from ui.posttrade_table import fetch_posttrade_data

logger = logging.getLogger(__name__)


# =============================================================================
# BAR FETCHER (inline - adapted from 06_training/data/polygon_client.py)
# =============================================================================

def _fetch_bars(ticker: str, end_date: date, tf_minutes: int, lookback_days: int) -> pd.DataFrame:
    """Fetch bars from Polygon API for a single timeframe."""
    start = end_date - timedelta(days=lookback_days)
    url = (
        f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range"
        f"/{tf_minutes}/minute/{start:%Y-%m-%d}/{end_date:%Y-%m-%d}"
    )
    params = {'apiKey': POLYGON_API_KEY, 'adjusted': 'true', 'sort': 'asc', 'limit': 50000}

    for attempt in range(API_RETRIES):
        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            if data.get('status') != 'OK' or not data.get('results'):
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
            logger.warning(f"Bar fetch attempt {attempt + 1} failed: {e}")
            if attempt < API_RETRIES - 1:
                time_module.sleep(API_RETRY_DELAY)
        except Exception as e:
            logger.error(f"Unexpected bar fetch error: {e}")
            break

    return pd.DataFrame()


def _fetch_daily_bars(ticker: str, start_date: date, end_date: date) -> pd.DataFrame:
    """Fetch daily bars from Polygon API for a date range."""
    url = (
        f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range"
        f"/1/day/{start_date:%Y-%m-%d}/{end_date:%Y-%m-%d}"
    )
    params = {'apiKey': POLYGON_API_KEY, 'adjusted': 'true', 'sort': 'asc', 'limit': 50000}

    for attempt in range(API_RETRIES):
        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            if data.get('status') != 'OK' or not data.get('results'):
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
            logger.warning(f"Daily bar fetch attempt {attempt + 1} failed: {e}")
            if attempt < API_RETRIES - 1:
                time_module.sleep(API_RETRY_DELAY)
        except Exception as e:
            logger.error(f"Unexpected daily bar fetch error: {e}")
            break

    return pd.DataFrame()


def _fetch_weekly_bars(ticker: str, end_date: date, lookback_weeks: int = 100) -> pd.DataFrame:
    """Fetch weekly bars from Polygon API."""
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

            if data.get('status') != 'OK' or not data.get('results'):
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

def _compute_intraday_vbp(bars_m1: pd.DataFrame, highlight: HighlightTrade) -> dict:
    """
    Compute intraday value volume profile from M1 bars: 04:00 ET → entry_time.

    Slices the already-fetched Polygon M1 bars to the pre-entry window and
    builds a volume profile dict for the M1 ramp-up chart sidebar.

    Args:
        bars_m1: Full M1 DataFrame from Polygon (datetime-indexed, tz-aware)
        highlight: HighlightTrade with entry_time and date

    Returns:
        Dict mapping price_level -> volume, or {} if insufficient data
    """
    if bars_m1 is None or bars_m1.empty or not highlight.entry_time:
        return {}

    try:
        # 04:00 ET on trade date
        start_dt = _TZ.localize(datetime.combine(
            highlight.date,
            datetime.min.time().replace(hour=4, minute=0),
        ))
        # Entry time on trade date (exclusive upper bound)
        entry_dt = _TZ.localize(datetime.combine(highlight.date, highlight.entry_time))

        # Slice to pre-entry window
        mask = (bars_m1.index >= start_dt) & (bars_m1.index < entry_dt)
        intraday_bars = bars_m1.loc[mask]

        if intraday_bars.empty:
            return {}

        return build_volume_profile(intraday_bars)
    except Exception as e:
        logger.warning(f"Intraday VbP computation failed: {e}")
        return {}


# =============================================================================
# H1 PRIOR BUILDER (shared by preview and export)
# =============================================================================

def _build_h1_prior_fig(bars_h1, highlight, zones, pocs, vp_dict):
    """Build H1 chart sliced to end at the 08:00 bar (covering 08:00-09:00).

    Fixed cutoff at 08:00 regardless of entry time.
    Polygon H1 bars use bar start time as timestamp.
    """
    if bars_h1 is None or (isinstance(bars_h1, pd.DataFrame) and bars_h1.empty):
        return build_h1_chart(bars_h1, highlight, zones, pocs=pocs, volume_profile_dict=vp_dict)

    # Fixed cutoff: 08:00 bar (covers 08:00-09:00)
    cutoff = _TZ.localize(datetime.combine(
        highlight.date,
        datetime.min.time().replace(hour=8, minute=0),
    ))
    h1_prior = bars_h1[bars_h1.index <= cutoff]

    if h1_prior.empty:
        return build_h1_chart(bars_h1, highlight, zones, pocs=pocs, volume_profile_dict=vp_dict)

    return build_h1_chart(h1_prior, highlight, zones, pocs=pocs, volume_profile_dict=vp_dict)


def _build_m15_prior_fig(bars_m15, highlight, zones, pocs, vp_dict):
    """Build M15 chart sliced to end at the 09:15 bar (covering 09:15-09:30).

    Fixed cutoff at 09:15 regardless of entry time.
    Polygon M15 bars use bar start time as timestamp.
    """
    if bars_m15 is None or (isinstance(bars_m15, pd.DataFrame) and bars_m15.empty):
        return build_m15_chart(bars_m15, highlight, zones, pocs=pocs, volume_profile_dict=vp_dict)

    # Fixed cutoff: 09:15 bar (covers 09:15-09:30)
    cutoff = _TZ.localize(datetime.combine(
        highlight.date,
        datetime.min.time().replace(hour=9, minute=15),
    ))
    m15_prior = bars_m15[bars_m15.index <= cutoff]

    if m15_prior.empty:
        return build_m15_chart(bars_m15, highlight, zones, pocs=pocs, volume_profile_dict=vp_dict)

    return build_m15_chart(m15_prior, highlight, zones, pocs=pocs, volume_profile_dict=vp_dict)


# =============================================================================
# BACKGROUND THREADS
# =============================================================================

class HighlightLoadThread(QThread):
    """Load highlights from database in background."""

    finished = pyqtSignal(list)   # List[HighlightTrade]
    error = pyqtSignal(str)

    def __init__(self, loader: HighlightLoader, filters: dict, parent=None):
        super().__init__(parent)
        self._loader = loader
        self._filters = filters

    def run(self):
        try:
            highlights = self._loader.fetch_highlights(
                date_from=self._filters.get('date_from'),
                date_to=self._filters.get('date_to'),
                min_r=self._filters.get('min_r', 3),
                model=self._filters.get('model'),
                direction=self._filters.get('direction'),
                ticker=self._filters.get('ticker'),
            )
            self.finished.emit(highlights)
        except Exception as e:
            self.error.emit(str(e))


class BarFetchThread(QThread):
    """Fetch Weekly/Daily/H1/M15/M5/M1 bars + zones + POCs + rampup + posttrade + VbP from Polygon + DB."""

    # bars_weekly, bars_daily, bars_h1, bars_m15, bars_m5, bars_m1, zones, pocs, rampup_df, posttrade_df, vbp_bars, anchor_date
    finished = pyqtSignal(object, object, object, object, object, object, list, list, object, object, object, object)
    error = pyqtSignal(str)

    def __init__(self, highlight: HighlightTrade, loader: HighlightLoader, parent=None):
        super().__init__(parent)
        self._hl = highlight
        self._loader = loader

    def run(self):
        try:
            ticker = self._hl.ticker.upper().strip()
            trade_date = self._hl.date

            # Fetch anchor date first (needed for daily chart + VbP)
            anchor_date = self._loader.fetch_epoch_start_date(ticker, trade_date)

            # Fetch weekly bars (90 weeks lookback)
            bars_weekly = _fetch_weekly_bars(ticker, trade_date, lookback_weeks=100)
            logger.info(f"Weekly: {ticker} ({len(bars_weekly)} bars)")

            # Fetch daily bars: epoch_start_date → day before trade
            bars_daily = pd.DataFrame()
            if anchor_date:
                day_before = trade_date - timedelta(days=1)
                bars_daily = _fetch_daily_bars(ticker, anchor_date, day_before)
                logger.info(f"Daily: {ticker} {anchor_date} → {day_before} ({len(bars_daily)} bars)")

            # Fetch intraday bars for 4 timeframes
            bars_h1 = _fetch_bars(ticker, trade_date, tf_minutes=60, lookback_days=50)
            bars_m15 = _fetch_bars(ticker, trade_date, tf_minutes=15, lookback_days=18)
            bars_m5 = _fetch_bars(ticker, trade_date, tf_minutes=5, lookback_days=3)
            bars_m1 = _fetch_bars(ticker, trade_date, tf_minutes=1, lookback_days=2)

            # Fetch zones
            zones = self._loader.fetch_zones_for_trade(ticker, trade_date)

            # Fetch HVN POC prices
            pocs = self._loader.fetch_hvn_pocs(ticker, trade_date)
            logger.info(f"POCs: {ticker} {trade_date} → {len(pocs)} POCs")

            # Fetch M1 ramp-up indicator data (up to entry)
            rampup_df = None
            if self._hl.entry_time:
                rampup_df = fetch_rampup_data(ticker, trade_date, self._hl.entry_time)

            # Fetch M1 post-trade indicator data (entry onward)
            posttrade_df = None
            if self._hl.entry_time:
                posttrade_df = fetch_posttrade_data(ticker, trade_date, self._hl.entry_time)

            # Fetch VbP bars from epoch_start_date (anchor) → trade_date
            # Uses M15 bars for granularity (same as 01_application)
            vbp_bars = pd.DataFrame()
            if anchor_date:
                lookback = (trade_date - anchor_date).days + 1
                vbp_bars = _fetch_bars(ticker, trade_date, tf_minutes=15, lookback_days=lookback)
                logger.info(f"VbP: {ticker} anchor={anchor_date} → {trade_date} ({lookback}d, {len(vbp_bars)} bars)")
            else:
                logger.warning(f"No epoch_start_date found for {ticker} {trade_date}, VbP will use display bars")

            self.finished.emit(bars_weekly, bars_daily, bars_h1, bars_m15, bars_m5, bars_m1, zones, pocs, rampup_df, posttrade_df, vbp_bars, anchor_date)
        except Exception as e:
            self.error.emit(str(e))


class ExportThread(QThread):
    """Export highlight images in background."""

    progress = pyqtSignal(int, int)       # current, total
    finished = pyqtSignal(int, str)       # count, output_dir
    error = pyqtSignal(str)

    def __init__(
        self,
        highlights: List[HighlightTrade],
        loader: HighlightLoader,
        platform: str,
        parent=None,
    ):
        super().__init__(parent)
        self._highlights = highlights
        self._loader = loader
        self._platform = platform

    def run(self):
        try:
            exported = 0
            total = len(self._highlights)
            out_dir = EXPORT_DIR / self._platform
            out_dir.mkdir(parents=True, exist_ok=True)

            for i, hl in enumerate(self._highlights):
                self.progress.emit(i + 1, total)

                ticker = hl.ticker.upper().strip()
                trade_date = hl.date

                # Fetch anchor date for daily + VbP
                anchor_date = self._loader.fetch_epoch_start_date(ticker, trade_date)

                # Fetch weekly bars from Polygon
                bars_weekly = _fetch_weekly_bars(ticker, trade_date, lookback_weeks=100)

                # Fetch daily bars
                bars_daily = pd.DataFrame()
                if anchor_date:
                    day_before = trade_date - timedelta(days=1)
                    bars_daily = _fetch_daily_bars(ticker, anchor_date, day_before)

                # Fetch intraday bars
                bars_h1 = _fetch_bars(ticker, trade_date, tf_minutes=60, lookback_days=50)
                bars_m15 = _fetch_bars(ticker, trade_date, tf_minutes=15, lookback_days=18)
                bars_m5 = _fetch_bars(ticker, trade_date, tf_minutes=5, lookback_days=3)
                bars_m1 = _fetch_bars(ticker, trade_date, tf_minutes=1, lookback_days=2)
                zones = self._loader.fetch_zones_for_trade(ticker, trade_date)
                pocs = self._loader.fetch_hvn_pocs(ticker, trade_date)

                # Fetch ramp-up data
                rampup_df = None
                if hl.entry_time:
                    rampup_df = fetch_rampup_data(ticker, trade_date, hl.entry_time)

                # Fetch VbP bars from epoch anchor
                vbp_bars = pd.DataFrame()
                if anchor_date:
                    lookback = (trade_date - anchor_date).days + 1
                    vbp_bars = _fetch_bars(ticker, trade_date, tf_minutes=15, lookback_days=lookback)

                if bars_m5.empty:
                    logger.warning(f"No M5 bars for {ticker}, skipping")
                    continue

                # Compute volume profile ONCE for this highlight
                vbp_source = vbp_bars if not vbp_bars.empty else None
                vp_dict = build_volume_profile(vbp_source) if vbp_source is not None else {}

                # Build all 7 charts
                weekly_fig = build_weekly_chart(bars_weekly, hl, zones)
                daily_fig = build_daily_chart(bars_daily, hl, zones, pocs=pocs, anchor_date=anchor_date, volume_profile_dict=vp_dict)
                h1_prior_fig = _build_h1_prior_fig(bars_h1, hl, zones, pocs, vp_dict)
                m15_prior_fig = _build_m15_prior_fig(bars_m15, hl, zones, pocs, vp_dict)
                m5_entry_fig = build_m5_entry_chart(bars_m5, hl, zones, pocs=pocs, volume_profile_dict=vp_dict)
                m1_fig = build_m1_chart(bars_m1, hl, zones)

                # Compute intraday value VbP (04:00 ET → entry) for M1 ramp-up chart
                intraday_vbp = _compute_intraday_vbp(bars_m1, hl)
                m1_rampup_fig = build_m1_rampup_chart(bars_m1, hl, zones, pocs=pocs, intraday_vbp_dict=intraday_vbp)

                # Export composite (returns list of paths)
                paths = export_highlight_image(
                    weekly_fig, daily_fig, h1_prior_fig, m15_prior_fig, m5_entry_fig, m1_fig,
                    m1_rampup_fig, hl, self._platform, out_dir,
                    rampup_df=rampup_df,
                )
                if paths:
                    exported += 1

            self.finished.emit(exported, str(out_dir))
        except Exception as e:
            self.error.emit(str(e))


# =============================================================================
# MAIN WINDOW
# =============================================================================

class TradeReelWindow(BaseWindow):
    """Trade Reel - Highlight trades viewer and image exporter."""

    def __init__(self):
        super().__init__(title="Epoch Trade Reel", width=1600, height=950)
        self.setStyleSheet(TV_DARK_QSS)

        self._loader = get_highlight_loader()
        self._current_highlight: Optional[HighlightTrade] = None
        self._current_bars = {}  # Cache: {trade_id: (weekly, daily, h1, m15, m5, m1, zones, pocs, rampup_df, posttrade_df, vbp_bars, anchor_date)}
        self._active_threads: list = []

        self._setup_trade_reel_ui()
        self._connect_signals()

    def _setup_trade_reel_ui(self):
        """Build the main layout."""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top area: filter + table + chart preview
        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Left side: Filter panel + highlight table
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        self._filter_panel = FilterPanel()
        left_layout.addWidget(self._filter_panel)

        # Right side: Chart preview
        self._chart_preview = ChartPreview()

        # Splitter for table + preview
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: filter + table combined
        left_combined = QWidget()
        left_combined_layout = QHBoxLayout(left_combined)
        left_combined_layout.setContentsMargins(0, 0, 0, 0)
        left_combined_layout.setSpacing(0)

        left_combined_layout.addWidget(self._filter_panel)

        self._highlight_table = HighlightTable()
        left_combined_layout.addWidget(self._highlight_table)

        # Lock left side to exact width of its fixed-width children
        left_combined.setFixedWidth(260 + sum(COL_WIDTHS.values()) + 2)

        splitter.addWidget(left_combined)
        splitter.addWidget(self._chart_preview)
        splitter.setSizes([500, 1100])

        content_layout.addWidget(splitter)
        main_layout.addWidget(content, stretch=1)

        # Bottom: Export bar
        self._export_bar = ExportBar()
        main_layout.addWidget(self._export_bar)

    def _connect_signals(self):
        """Wire up all panel signals."""
        # Filter -> load highlights
        self._filter_panel.load_requested.connect(self._on_load_highlights)

        # Table row click -> fetch bars + preview
        self._highlight_table.selection_changed.connect(self._on_highlight_selected)

        # Checkbox changes -> enable/disable export
        self._highlight_table.checked_changed.connect(self._on_checked_changed)

        # Export bar buttons
        self._export_bar.export_requested.connect(self._on_export_requested)
        self._export_bar.export_all_requested.connect(self._on_export_all_requested)
        self._export_bar.select_all_btn.clicked.connect(self._highlight_table.select_all)
        self._export_bar.deselect_btn.clicked.connect(self._highlight_table.deselect_all)

    # -------------------------------------------------------------------------
    # LOAD HIGHLIGHTS
    # -------------------------------------------------------------------------

    def _on_load_highlights(self, filters: dict):
        """Start background highlight loading."""
        self._filter_panel.set_loading(True)
        self._chart_preview.show_placeholder()
        self._export_bar.clear_status()

        thread = HighlightLoadThread(self._loader, filters, parent=self)
        thread.finished.connect(self._on_highlights_loaded)
        thread.error.connect(self._on_highlights_error)
        thread.finished.connect(lambda: self._cleanup_thread(thread))
        thread.error.connect(lambda: self._cleanup_thread(thread))
        self._active_threads.append(thread)
        thread.start()

    def _on_highlights_loaded(self, highlights: List[HighlightTrade]):
        """Handle loaded highlights (deduplicated to 1 per minute)."""
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

        self._highlight_table.set_highlights(highlights)
        self._filter_panel.update_results_info(len(highlights))
        self._export_bar.set_export_enabled(False)

        # Update ticker dropdown
        tickers = sorted(set(hl.ticker for hl in highlights))
        self._filter_panel.set_tickers(tickers)

        if highlights:
            self.statusBar().showMessage(f"Loaded {len(highlights)} highlight trades")
        else:
            self.statusBar().showMessage("No highlights found for the selected filters")

    def _on_highlights_error(self, error: str):
        """Handle highlight loading error."""
        self._filter_panel.set_loading(False)
        self.statusBar().showMessage(f"Error: {error}")
        logger.error(f"Highlight load error: {error}")

    # -------------------------------------------------------------------------
    # SELECT HIGHLIGHT -> FETCH BARS -> RENDER CHARTS
    # -------------------------------------------------------------------------

    def _on_highlight_selected(self, highlight):
        """Handle table row selection - fetch bars and render charts."""
        if highlight is None:
            self._chart_preview.show_placeholder()
            self._current_highlight = None
            return

        self._current_highlight = highlight

        # Check cache
        if highlight.trade_id in self._current_bars:
            weekly, daily, h1, m15, m5, m1, zones, pocs, rampup_df, posttrade_df, vbp_bars, anchor_date = self._current_bars[highlight.trade_id]
            self._render_charts(highlight, weekly, daily, h1, m15, m5, m1, zones, pocs, rampup_df, posttrade_df, vbp_bars, anchor_date)
            return

        # Fetch bars in background
        self._chart_preview.show_loading()
        self.statusBar().showMessage(f"Fetching bars for {highlight.ticker} {highlight.date}...")

        thread = BarFetchThread(highlight, self._loader, parent=self)
        thread.finished.connect(
            lambda w, d, h1, m15, m5, m1, z, p, r, pt, vbp, anch: self._on_bars_fetched(highlight, w, d, h1, m15, m5, m1, z, p, r, pt, vbp, anch)
        )
        thread.error.connect(self._on_bars_error)
        thread.finished.connect(lambda *_: self._cleanup_thread(thread))
        thread.error.connect(lambda: self._cleanup_thread(thread))
        self._active_threads.append(thread)
        thread.start()

    def _on_bars_fetched(self, highlight, bars_weekly, bars_daily, bars_h1, bars_m15, bars_m5, bars_m1, zones, pocs, rampup_df, posttrade_df, vbp_bars, anchor_date):
        """Handle fetched bar data."""
        # Cache the bars
        self._current_bars[highlight.trade_id] = (bars_weekly, bars_daily, bars_h1, bars_m15, bars_m5, bars_m1, zones, pocs, rampup_df, posttrade_df, vbp_bars, anchor_date)

        # Only render if this is still the selected highlight
        if self._current_highlight and self._current_highlight.trade_id == highlight.trade_id:
            self._render_charts(highlight, bars_weekly, bars_daily, bars_h1, bars_m15, bars_m5, bars_m1, zones, pocs, rampup_df, posttrade_df, vbp_bars, anchor_date)

    def _render_charts(self, highlight, bars_weekly, bars_daily, bars_h1, bars_m15, bars_m5, bars_m1, zones, pocs=None, rampup_df=None, posttrade_df=None, vbp_bars=None, anchor_date=None):
        """Build and display charts for a highlight."""
        try:
            if bars_m5 is None or (isinstance(bars_m5, pd.DataFrame) and bars_m5.empty):
                self._chart_preview.show_error("No M5 bar data available")
                return

            # Compute volume profile ONCE from VbP source bars
            vbp_source = vbp_bars if (vbp_bars is not None and not vbp_bars.empty) else None
            vp_dict = build_volume_profile(vbp_source) if vbp_source is not None else {}

            # Build all 7 charts
            weekly_fig = build_weekly_chart(bars_weekly, highlight, zones)
            daily_fig = build_daily_chart(bars_daily, highlight, zones, pocs=pocs, anchor_date=anchor_date, volume_profile_dict=vp_dict)
            h1_prior_fig = self._build_h1_prior(bars_h1, highlight, zones, pocs, vp_dict)
            m15_prior_fig = self._build_m15_prior(bars_m15, highlight, zones, pocs, vp_dict)
            m5_entry_fig = build_m5_entry_chart(bars_m5, highlight, zones, pocs=pocs, volume_profile_dict=vp_dict)
            m1_fig = build_m1_chart(bars_m1, highlight, zones)

            # Compute intraday value VbP (04:00 ET → entry) for M1 ramp-up chart
            intraday_vbp = _compute_intraday_vbp(bars_m1, highlight)
            m1_rampup_fig = build_m1_rampup_chart(bars_m1, highlight, zones, pocs=pocs, intraday_vbp_dict=intraday_vbp)

            self._chart_preview.show_charts(
                weekly_fig, daily_fig, h1_prior_fig, m15_prior_fig,
                m5_entry_fig, m1_rampup_fig, m1_fig, highlight,
            )

            # Show ramp-up indicator table
            if rampup_df is not None:
                self._chart_preview.show_rampup(rampup_df)

            # Show post-trade indicator table
            if posttrade_df is not None:
                self._chart_preview.show_posttrade(posttrade_df)

            self.statusBar().showMessage(
                f"{highlight.ticker} {highlight.date} - {highlight.star_display} | "
                f"{highlight.direction} | {highlight.exit_reason}"
            )
        except Exception as e:
            self._chart_preview.show_error(str(e))
            logger.error(f"Chart render error: {e}")

    def _build_h1_prior(self, bars_h1, highlight, zones, pocs, vp_dict):
        """Delegate to module-level function."""
        return _build_h1_prior_fig(bars_h1, highlight, zones, pocs, vp_dict)

    def _build_m15_prior(self, bars_m15, highlight, zones, pocs, vp_dict):
        """Delegate to module-level function."""
        return _build_m15_prior_fig(bars_m15, highlight, zones, pocs, vp_dict)

    def _on_bars_error(self, error: str):
        """Handle bar fetch error."""
        self._chart_preview.show_error(error)
        self.statusBar().showMessage(f"Error fetching bars: {error}")

    # -------------------------------------------------------------------------
    # EXPORT
    # -------------------------------------------------------------------------

    def _on_checked_changed(self, checked_ids: list):
        """Enable/disable export based on selections."""
        self._export_bar.set_export_enabled(len(checked_ids) > 0)

    def _on_export_requested(self, platform: str):
        """Start export for selected highlights."""
        checked = self._highlight_table.get_checked_highlights()
        if not checked:
            self.statusBar().showMessage("No highlights selected for export")
            return

        self._export_bar.set_exporting(True)
        self.statusBar().showMessage(f"Exporting {len(checked)} highlights for {platform}...")

        thread = ExportThread(checked, self._loader, platform, parent=self)
        thread.progress.connect(self._export_bar.show_export_progress)
        thread.finished.connect(lambda count, path: self._on_export_finished(count, path, platform))
        thread.error.connect(self._on_export_error)
        thread.finished.connect(lambda *_: self._cleanup_thread(thread))
        thread.error.connect(lambda: self._cleanup_thread(thread))
        self._active_threads.append(thread)
        thread.start()

    def _on_export_all_requested(self):
        """Export checked highlights for all platforms sequentially."""
        checked = self._highlight_table.get_checked_highlights()
        if not checked:
            self.statusBar().showMessage("No highlights selected for export")
            return

        self._export_all_platforms = list(PLATFORM_STYLES.keys())
        self._export_all_total = len(self._export_all_platforms)
        self._export_all_done = 0
        self._export_bar.set_exporting(True)
        self.statusBar().showMessage(
            f"Exporting {len(checked)} highlights for all platforms..."
        )
        self._run_next_export_all()

    def _run_next_export_all(self):
        """Kick off the next platform in the export-all queue."""
        if not self._export_all_platforms:
            # All done
            self._export_bar.set_exporting(False)
            self.statusBar().showMessage(
                f"Exported all {self._export_all_total} platforms"
            )
            return

        platform = self._export_all_platforms.pop(0)
        checked = self._highlight_table.get_checked_highlights()
        self.statusBar().showMessage(
            f"Exporting {platform} ({self._export_all_done + 1}/{self._export_all_total})..."
        )

        thread = ExportThread(checked, self._loader, platform, parent=self)
        thread.progress.connect(self._export_bar.show_export_progress)
        thread.finished.connect(
            lambda count, path: self._on_export_all_platform_done(count, path, platform)
        )
        thread.error.connect(self._on_export_error)
        thread.finished.connect(lambda *_: self._cleanup_thread(thread))
        thread.error.connect(lambda: self._cleanup_thread(thread))
        self._active_threads.append(thread)
        thread.start()

    def _on_export_all_platform_done(self, count: int, output_dir: str, platform: str):
        """One platform finished — move to next."""
        self._export_all_done += 1
        self._export_bar.show_export_result(
            count, f"{output_dir} ({self._export_all_done}/{self._export_all_total})"
        )
        self._run_next_export_all()

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

    # -------------------------------------------------------------------------
    # CLEANUP
    # -------------------------------------------------------------------------

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
