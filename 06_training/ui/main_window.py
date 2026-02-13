"""
Epoch Trading System - Training Module Main Window
BaseWindow subclass with sidebar + flashcard content + QThread loading.
"""

import random
import logging
from typing import List, Optional

from PyQt6.QtWidgets import QHBoxLayout, QWidget, QVBoxLayout
from PyQt6.QtCore import QThread, pyqtSignal

import sys
import types
import importlib.util
from pathlib import Path

MODULE_DIR = Path(__file__).parent.parent
SHARED_DIR = MODULE_DIR.parent / '00_shared'

# 06_training/ui/ and 00_shared/ui/ both exist as 'ui' packages.
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
from config import CHART_CONFIG
from data.supabase_client import get_supabase_client, SupabaseClient
from data.cache_manager import get_bar_cache, BarCache
from models.trade import TradeWithMetrics

from ui.filter_panel import FilterPanel
from ui.flashcard_panel import FlashcardPanel

logger = logging.getLogger(__name__)


# =============================================================================
# BACKGROUND THREADS
# =============================================================================

class TradeLoadThread(QThread):
    """Load trades from database in background."""

    finished = pyqtSignal(list)   # Emits list of TradeWithMetrics
    error = pyqtSignal(str)       # Emits error message

    def __init__(self, supabase: SupabaseClient, filters: dict, parent=None):
        super().__init__(parent)
        self._supabase = supabase
        self._filters = filters

    def run(self):
        try:
            trades = self._supabase.fetch_trades_with_metrics(
                date_from=self._filters['date_from'],
                date_to=self._filters['date_to'],
                ticker=self._filters.get('ticker'),
                model=self._filters.get('model'),
                unreviewed_only=self._filters.get('unreviewed_only', False),
                ai_validated_only=self._filters.get('ai_validated_only', False),
                limit=20
            )
            if trades:
                random.shuffle(trades)
            self.finished.emit(trades or [])
        except Exception as e:
            logger.error(f"Trade load error: {e}")
            self.error.emit(str(e))


class BarFetchThread(QThread):
    """Fetch bar data and zones for a single trade in background."""

    finished = pyqtSignal(object, dict, list)  # bar_data, bars_dict, zones
    error = pyqtSignal(str)

    def __init__(self, cache: BarCache, supabase: SupabaseClient, trade: TradeWithMetrics, parent=None):
        super().__init__(parent)
        self._cache = cache
        self._supabase = supabase
        self._trade = trade

    def run(self):
        try:
            bar_data = self._cache.get_bars_for_trade(
                ticker=self._trade.ticker,
                trade_date=self._trade.date,
                candle_count=CHART_CONFIG['candle_count']
            )

            bars = {}
            if bar_data and bar_data.is_valid:
                bars = {
                    '5m': bar_data.bars_5m,
                    '15m': bar_data.bars_15m,
                    '1h': bar_data.bars_1h
                }

            zones = self._supabase.fetch_zones_for_trade(
                ticker=self._trade.ticker,
                trade_date=self._trade.date
            )

            self.finished.emit(bar_data, bars, zones or [])
        except Exception as e:
            logger.error(f"Bar fetch error: {e}")
            self.error.emit(str(e))


class PrefetchThread(QThread):
    """Prefetch bar data for upcoming trades."""

    def __init__(self, cache: BarCache, trades: List[TradeWithMetrics], parent=None):
        super().__init__(parent)
        self._cache = cache
        self._trades = trades

    def run(self):
        try:
            self._cache.prefetch_for_trades(self._trades)
        except Exception as e:
            logger.debug(f"Prefetch error (non-critical): {e}")


# =============================================================================
# MAIN WINDOW
# =============================================================================

class TrainingWindow(BaseWindow):
    """Main training module window with sidebar + flashcard content."""

    def __init__(self):
        super().__init__(
            title="Epoch Trade Review - Training Module",
            width=2400,
            height=1400
        )

        # Data clients
        self._supabase = get_supabase_client()
        self._cache = get_bar_cache()

        # State
        self._review_queue: List[TradeWithMetrics] = []
        self._current_index: int = 0
        self._active_threads: list = []

        # Build UI
        self._setup_training_ui()

    def _setup_training_ui(self):
        """Set up the main content area: sidebar + flashcard panel."""
        # Replace the default main_layout with a horizontal split
        container = QWidget()
        h_layout = QHBoxLayout(container)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(0)

        # Sidebar
        self._filter_panel = FilterPanel()
        self._filter_panel.load_requested.connect(self._on_load_trades)
        self._filter_panel.shuffle_requested.connect(self._on_shuffle)
        self._filter_panel.jump_requested.connect(self._on_jump)
        h_layout.addWidget(self._filter_panel)

        # Main content
        self._flashcard_panel = FlashcardPanel(self._supabase, self._cache)
        self._flashcard_panel.next_trade.connect(self._on_next_trade)
        self._flashcard_panel.show_welcome()
        h_layout.addWidget(self._flashcard_panel, 1)

        self.main_layout.addWidget(container, 1)

        # Populate tickers
        self._load_tickers()

    def _load_tickers(self):
        """Fetch available tickers for filter dropdown."""
        try:
            filters = self._filter_panel.get_filters()
            tickers = self._supabase.get_available_tickers(date_from=filters['date_from'])
            self._filter_panel.set_tickers(tickers)
        except Exception as e:
            logger.warning(f"Failed to load tickers: {e}")

    # =========================================================================
    # SIGNAL HANDLERS
    # =========================================================================

    def _on_load_trades(self, filters: dict):
        """Handle load trades request from sidebar."""
        self._filter_panel.set_loading(True)
        self.set_status("Loading trades...")

        thread = TradeLoadThread(self._supabase, filters, self)
        thread.finished.connect(self._on_trades_loaded)
        thread.error.connect(self._on_trade_load_error)
        thread.finished.connect(lambda: self._filter_panel.set_loading(False))
        thread.error.connect(lambda: self._filter_panel.set_loading(False))
        self._active_threads.append(thread)
        thread.start()

    def _on_trades_loaded(self, trades: list):
        """Handle trades loaded from background thread."""
        if not trades:
            self.set_status("No trades found matching filters")
            self._review_queue = []
            self._current_index = 0
            self._filter_panel.update_queue_info(0, 0)
            self._flashcard_panel.show_welcome()
            return

        self._review_queue = trades
        self._current_index = 0
        self.set_status(f"Loaded {len(trades)} trades")
        self._filter_panel.update_queue_info(0, len(trades))
        self._load_current_trade()

    def _on_trade_load_error(self, error_msg: str):
        """Handle trade loading error."""
        self.show_error("Load Error", f"Failed to load trades: {error_msg}")
        self.set_status("Load failed")

    def _on_next_trade(self):
        """Advance to next trade in queue."""
        self._current_index += 1
        self._filter_panel.update_queue_info(self._current_index, len(self._review_queue))

        if self._current_index >= len(self._review_queue):
            self._flashcard_panel.show_completion(len(self._review_queue))
            self.set_status("Session complete!")
            return

        self._load_current_trade()

    def _on_shuffle(self):
        """Shuffle the queue and restart."""
        if self._review_queue:
            random.shuffle(self._review_queue)
            self._current_index = 0
            self._filter_panel.update_queue_info(0, len(self._review_queue))
            self._load_current_trade()

    def _on_jump(self, index: int):
        """Jump to specific trade in queue."""
        if 0 <= index < len(self._review_queue):
            self._current_index = index
            self._filter_panel.update_queue_info(index, len(self._review_queue))
            self._load_current_trade()

    # =========================================================================
    # TRADE LOADING
    # =========================================================================

    def _load_current_trade(self):
        """Load bar data and zones for the current trade."""
        if self._current_index >= len(self._review_queue):
            return

        trade = self._review_queue[self._current_index]
        self._flashcard_panel.show_loading()
        self.set_status(f"Loading {trade.ticker} {trade.date}...")

        thread = BarFetchThread(self._cache, self._supabase, trade, self)
        thread.finished.connect(self._on_bars_loaded)
        thread.error.connect(self._on_bar_load_error)
        self._active_threads.append(thread)
        thread.start()

    def _on_bars_loaded(self, bar_data, bars: dict, zones: list):
        """Handle bar data loaded."""
        if self._current_index >= len(self._review_queue):
            return

        trade = self._review_queue[self._current_index]

        if not bar_data or not getattr(bar_data, 'is_valid', False):
            self.set_status(f"Failed to fetch bars for {trade.ticker}")
            # Skip to next
            self._current_index += 1
            self._filter_panel.update_queue_info(self._current_index, len(self._review_queue))
            if self._current_index < len(self._review_queue):
                self._load_current_trade()
            else:
                self._flashcard_panel.show_completion(len(self._review_queue))
            return

        self._flashcard_panel.show_trade_panels()
        self._flashcard_panel.update_trade(
            trade=trade,
            bars=bars,
            zones=zones,
            current_index=self._current_index,
            total=len(self._review_queue)
        )
        self.set_status(f"Trade {self._current_index + 1}/{len(self._review_queue)}: {trade.ticker} {trade.date}")

        # Prefetch upcoming
        self._prefetch_upcoming()

    def _on_bar_load_error(self, error_msg: str):
        """Handle bar loading error - skip trade."""
        self.set_status(f"Bar load error: {error_msg}")
        self._current_index += 1
        self._filter_panel.update_queue_info(self._current_index, len(self._review_queue))
        if self._current_index < len(self._review_queue):
            self._load_current_trade()
        else:
            self._flashcard_panel.show_completion(len(self._review_queue))

    def _prefetch_upcoming(self):
        """Prefetch bar data for upcoming trades."""
        next_idx = self._current_index + 1
        if next_idx < len(self._review_queue):
            upcoming = self._review_queue[next_idx:next_idx + 3]
            thread = PrefetchThread(self._cache, upcoming, self)
            self._active_threads.append(thread)
            thread.start()

    # =========================================================================
    # OVERRIDES
    # =========================================================================

    def on_refresh(self):
        """Refresh tickers and reload current trade."""
        self._load_tickers()
        if self._review_queue and self._current_index < len(self._review_queue):
            self._load_current_trade()
        self.set_status("Refreshed", 2000)

    def closeEvent(self, event):
        """Clean up threads on close."""
        for thread in self._active_threads:
            if thread.isRunning():
                thread.quit()
                thread.wait(2000)
        super().closeEvent(event)
