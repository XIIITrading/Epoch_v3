"""
Data Worker (QThread)
Epoch Trading System v1 - XIII Trading LLC

Handles async data fetching to prevent UI blocking.
"""
import sys
from pathlib import Path

# Ensure entry_qualifier is at the front of sys.path
_entry_qualifier_dir = str(Path(__file__).parent.parent.resolve())
if _entry_qualifier_dir not in sys.path:
    sys.path.insert(0, _entry_qualifier_dir)
elif sys.path[0] != _entry_qualifier_dir:
    sys.path.remove(_entry_qualifier_dir)
    sys.path.insert(0, _entry_qualifier_dir)

from PyQt6.QtCore import QThread, pyqtSignal
from typing import Dict, List, Any

from data.api_client import PolygonClient
from calculations.volume_delta import calculate_all_deltas
from calculations.candle_range import calculate_all_candle_ranges
from calculations.volume_roc import calculate_all_volume_roc
from calculations.sma_config import calculate_all_sma_configs
from calculations.h1_structure import (
    calculate_structure_for_bars,
    H1StructureCache,
    StructureCache,
    MarketStructure
)
from eq_config import PREFETCH_BARS, VOL_DELTA_ROLL_PERIOD, VOL_ROC_LOOKBACK, H1_BARS_NEEDED, M5_BARS_NEEDED, M15_BARS_NEEDED


# Global structure caches (shared across workers)
_h1_cache = H1StructureCache()
_m5_cache = StructureCache(300_000)    # 5 minutes in ms
_m15_cache = StructureCache(900_000)   # 15 minutes in ms


class DataWorker(QThread):
    """
    Worker thread for fetching ticker data asynchronously.

    Emits signals when data is ready or errors occur.
    """

    # Signals
    data_ready = pyqtSignal(str, list)  # ticker, processed_bars
    error_occurred = pyqtSignal(str, str)  # ticker, error_message
    validation_result = pyqtSignal(str, bool)  # ticker, is_valid

    def __init__(self, parent=None):
        super().__init__(parent)
        self.client = PolygonClient()
        self._tickers_to_fetch: List[str] = []
        self._validate_ticker: str = None
        self._running = True
        self._force_h1_refresh = False  # Flag to force H1 refresh

    def add_ticker_to_fetch(self, ticker: str):
        """Add a ticker to the fetch queue."""
        ticker = ticker.upper().strip()
        if ticker and ticker not in self._tickers_to_fetch:
            self._tickers_to_fetch.append(ticker)

    def set_tickers_to_fetch(self, tickers: List[str]):
        """Set the list of tickers to fetch."""
        self._tickers_to_fetch = [t.upper().strip() for t in tickers if t]

    def validate_ticker(self, ticker: str):
        """Set a ticker to validate (runs before normal fetch)."""
        self._validate_ticker = ticker.upper().strip()

    def stop(self):
        """Stop the worker thread."""
        self._running = False

    def run(self):
        """Main worker loop - fetches data for queued tickers."""
        # Handle validation request first
        if self._validate_ticker:
            ticker = self._validate_ticker
            self._validate_ticker = None
            is_valid = self.client.validate_ticker(ticker)
            self.validation_result.emit(ticker, is_valid)

        # Fetch data for all queued tickers
        tickers_to_process = self._tickers_to_fetch.copy()
        self._tickers_to_fetch.clear()

        for ticker in tickers_to_process:
            if not self._running:
                break

            self._fetch_and_process(ticker)

    def _fetch_and_process(self, ticker: str):
        """Fetch and process data for a single ticker."""
        # Fetch raw bars
        result = self.client.fetch_m1_bars(ticker, bars_needed=PREFETCH_BARS)

        if result.get('error'):
            error_msg = self._get_error_message(result['error'])
            self.error_occurred.emit(ticker, error_msg)
            return

        bars = result.get('bars', [])
        if not bars:
            self.error_occurred.emit(ticker, "No data available")
            return

        # Calculate deltas
        delta_results = calculate_all_deltas(bars, roll_period=VOL_DELTA_ROLL_PERIOD)

        # Calculate candle ranges
        range_results = calculate_all_candle_ranges(bars)

        # Calculate volume ROC
        vol_roc_results = calculate_all_volume_roc(bars, lookback=VOL_ROC_LOOKBACK)

        # Calculate SMA configurations
        sma_results = calculate_all_sma_configs(bars)

        # Fetch/use cached structure bars and calculate structure for each timeframe
        h1_results = self._get_h1_structure(ticker, bars)
        m5_results = self._get_m5_structure(ticker, bars)
        m15_results = self._get_m15_structure(ticker, bars)

        # Combine bar data with calculations
        processed_bars = []
        for i, (bar, delta, candle_range, vol_roc, sma, h1, m5, m15) in enumerate(
            zip(bars, delta_results, range_results, vol_roc_results, sma_results, h1_results, m5_results, m15_results)
        ):
            processed_bars.append({
                'timestamp': bar['timestamp'],
                'open': bar['open'],
                'high': bar['high'],
                'low': bar['low'],
                'close': bar['close'],
                'volume': bar['volume'],
                'raw_delta': delta['raw_delta'],
                'roll_delta': delta['roll_delta'],
                'candle_range_pct': candle_range['candle_range_pct'],
                'is_absorption': candle_range['is_absorption'],
                'volume_roc': vol_roc['volume_roc'],
                'is_elevated_volume': vol_roc['is_elevated'],
                'sma_config': sma['sma_config'],
                'sma_spread_pct': sma['sma_spread_pct'],
                'sma_display': sma['sma_display'],
                'price_position': sma['price_position'],
                'm5_structure': m5['h1_structure'],    # reuses h1_structure key from calculate_structure_for_bars
                'm5_display': m5['h1_display'],
                'm15_structure': m15['h1_structure'],
                'm15_display': m15['h1_display'],
                'h1_structure': h1['h1_structure'],
                'h1_display': h1['h1_display']
            })

        # Emit the processed data
        self.data_ready.emit(ticker, processed_bars)

    def _get_h1_structure(self, ticker: str, m1_bars: List[dict]) -> List[dict]:
        """
        Get H1 structure data, using cache when possible.

        Fetches H1 bars on first call or when a new H1 candle has closed.
        """
        global _h1_cache

        # Check if we have M1 data to determine current hour
        if not m1_bars:
            return [{'h1_structure': MarketStructure.NEUTRAL, 'h1_display': 'N'}]

        # Get current H1 bar timestamp (floor to hour)
        latest_m1_ts = m1_bars[-1].get('timestamp', 0)
        hour_ms = 3600000
        current_h1_ts = (latest_m1_ts // hour_ms) * hour_ms

        # Check if we need to refresh H1 data
        h1_bars = _h1_cache.get_bars(ticker)
        needs_refresh = (
            h1_bars is None or
            self._force_h1_refresh or
            _h1_cache.needs_refresh(ticker, current_h1_ts)
        )

        if needs_refresh:
            # Fetch H1 bars from API
            result = self.client.fetch_h1_bars(ticker, bars_needed=H1_BARS_NEEDED)
            if not result.get('error') and result.get('bars'):
                h1_bars = result['bars']
                _h1_cache.set_bars(ticker, h1_bars)
            elif h1_bars is None:
                # No cached data and fetch failed - return neutral
                return [{'h1_structure': MarketStructure.NEUTRAL, 'h1_display': 'N'}
                        for _ in m1_bars]

        # Calculate structure for each M1 bar
        return calculate_structure_for_bars(h1_bars, m1_bars)

    def _get_m5_structure(self, ticker: str, m1_bars: List[dict]) -> List[dict]:
        """
        Get M5 structure data, using cache when possible.

        Fetches M5 bars on first call or when a new M5 candle has closed.
        """
        global _m5_cache

        if not m1_bars:
            return [{'h1_structure': MarketStructure.NEUTRAL, 'h1_display': 'N'}]

        # Get current M5 bar timestamp (floor to 5-minute boundary)
        latest_m1_ts = m1_bars[-1].get('timestamp', 0)
        m5_ms = 300_000
        current_m5_ts = (latest_m1_ts // m5_ms) * m5_ms

        # Check if we need to refresh M5 data
        m5_bars = _m5_cache.get_bars(ticker)
        needs_refresh = (
            m5_bars is None or
            _m5_cache.needs_refresh(ticker, current_m5_ts)
        )

        if needs_refresh:
            result = self.client.fetch_m5_bars(ticker, bars_needed=M5_BARS_NEEDED)
            if not result.get('error') and result.get('bars'):
                m5_bars = result['bars']
                _m5_cache.set_bars(ticker, m5_bars)
            elif m5_bars is None:
                return [{'h1_structure': MarketStructure.NEUTRAL, 'h1_display': 'N'}
                        for _ in m1_bars]

        return calculate_structure_for_bars(m5_bars, m1_bars)

    def _get_m15_structure(self, ticker: str, m1_bars: List[dict]) -> List[dict]:
        """
        Get M15 structure data, using cache when possible.

        Fetches M15 bars on first call or when a new M15 candle has closed.
        """
        global _m15_cache

        if not m1_bars:
            return [{'h1_structure': MarketStructure.NEUTRAL, 'h1_display': 'N'}]

        # Get current M15 bar timestamp (floor to 15-minute boundary)
        latest_m1_ts = m1_bars[-1].get('timestamp', 0)
        m15_ms = 900_000
        current_m15_ts = (latest_m1_ts // m15_ms) * m15_ms

        # Check if we need to refresh M15 data
        m15_bars = _m15_cache.get_bars(ticker)
        needs_refresh = (
            m15_bars is None or
            _m15_cache.needs_refresh(ticker, current_m15_ts)
        )

        if needs_refresh:
            result = self.client.fetch_m15_bars(ticker, bars_needed=M15_BARS_NEEDED)
            if not result.get('error') and result.get('bars'):
                m15_bars = result['bars']
                _m15_cache.set_bars(ticker, m15_bars)
            elif m15_bars is None:
                return [{'h1_structure': MarketStructure.NEUTRAL, 'h1_display': 'N'}
                        for _ in m1_bars]

        return calculate_structure_for_bars(m15_bars, m1_bars)

    def set_force_h1_refresh(self, force: bool = True):
        """Set flag to force H1 data refresh on next fetch."""
        self._force_h1_refresh = force

    def _get_error_message(self, error: str) -> str:
        """Convert error code to user-friendly message."""
        error_messages = {
            'timeout': 'API Timeout',
            'network': 'Network Error',
            'api_error': 'API Error',
            'no_data': 'No Data Available',
            'rate_limit': 'Rate Limited'
        }
        return error_messages.get(error, f"Error: {error}")


class TickerValidationWorker(QThread):
    """
    Separate worker just for ticker validation.
    Runs independently to not block the fetch queue.
    """

    validation_complete = pyqtSignal(str, bool, str)  # ticker, is_valid, error_msg

    def __init__(self, ticker: str, parent=None):
        super().__init__(parent)
        self.ticker = ticker.upper().strip()
        self.client = PolygonClient()

    def run(self):
        """Validate the ticker."""
        try:
            result = self.client.fetch_m1_bars(self.ticker, bars_needed=5)

            if result.get('error'):
                error_msg = result['error']
                if error_msg == 'no_data':
                    error_msg = f"'{self.ticker}' - No data found. Invalid ticker or no recent trading."
                elif error_msg == 'timeout':
                    error_msg = "API timeout. Please try again."
                elif error_msg == 'network':
                    error_msg = "Network error. Check your connection."
                else:
                    error_msg = f"Error validating ticker: {error_msg}"

                self.validation_complete.emit(self.ticker, False, error_msg)
            else:
                bars = result.get('bars', [])
                if len(bars) < 5:
                    self.validation_complete.emit(
                        self.ticker,
                        False,
                        f"'{self.ticker}' - Insufficient data. Ticker may be invalid or have limited trading."
                    )
                else:
                    self.validation_complete.emit(self.ticker, True, "")
        except Exception as e:
            self.validation_complete.emit(self.ticker, False, f"Error: {str(e)}")
