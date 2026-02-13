"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
M1 Indicator Bars - Calculator
XIII Trading LLC
================================================================================

Core calculator that computes all M1 indicator bars for a single ticker-date.
Combines M1 bar fetching, indicator calculations, and structure detection.

Produces direction-agnostic bars for pre-market + regular hours (08:00 to 16:00 ET).

Version: 1.0.0
================================================================================
"""

from dataclasses import dataclass
from datetime import datetime, date, time, timedelta
from typing import Dict, List, Optional, Any
import logging
import pandas as pd
import numpy as np

# Use explicit path imports to avoid collisions with 03_indicators modules
import importlib.util
from pathlib import Path

_MODULE_DIR = Path(__file__).resolve().parent

# Load local config
_config_spec = importlib.util.spec_from_file_location("local_config", _MODULE_DIR / "config.py")
_config = importlib.util.module_from_spec(_config_spec)
_config_spec.loader.exec_module(_config)
PREMARKET_START = _config.PREMARKET_START
MARKET_CLOSE = _config.MARKET_CLOSE
CALCULATION_VERSION = _config.CALCULATION_VERSION

# Load local m1_fetcher
_fetcher_spec = importlib.util.spec_from_file_location("m1_fetcher", _MODULE_DIR / "m1_fetcher.py")
_fetcher_mod = importlib.util.module_from_spec(_fetcher_spec)
_fetcher_spec.loader.exec_module(_fetcher_mod)
M1Fetcher = _fetcher_mod.M1Fetcher

# Load local indicators (already handles its own path issues)
_indicators_spec = importlib.util.spec_from_file_location("indicators", _MODULE_DIR / "indicators.py")
_indicators_mod = importlib.util.module_from_spec(_indicators_spec)
_indicators_spec.loader.exec_module(_indicators_mod)
M1IndicatorCalculator = _indicators_mod.M1IndicatorCalculator

# Load local structure
_structure_spec = importlib.util.spec_from_file_location("local_structure", _MODULE_DIR / "structure.py")
_structure_mod = importlib.util.module_from_spec(_structure_spec)
_structure_spec.loader.exec_module(_structure_mod)
StructureAnalyzer = _structure_mod.StructureAnalyzer
StructureResult = _structure_mod.StructureResult


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class M1IndicatorBarResult:
    """Complete M1 indicator bar result for database insertion."""
    # Primary Key
    ticker: str
    bar_date: date
    bar_time: time

    # OHLCV
    open: float
    high: float
    low: float
    close: float
    volume: int

    # Price Indicators (direction-agnostic)
    vwap: Optional[float]
    sma9: Optional[float]
    sma21: Optional[float]
    sma_spread: Optional[float]
    sma_momentum_ratio: Optional[float]
    sma_momentum_label: Optional[str]

    # Volume Indicators (direction-agnostic)
    vol_roc: Optional[float]
    vol_delta: Optional[float]
    cvd_slope: Optional[float]

    # Structure (direction-agnostic labels)
    h4_structure: Optional[str]
    h1_structure: Optional[str]
    m15_structure: Optional[str]
    m5_structure: Optional[str]
    m1_structure: Optional[str]

    # Health Score (0-10)
    health_score: Optional[int]

    # Entry Qualifier Indicators (EPCH v1.0)
    candle_range_pct: Optional[float]  # (high-low)/close * 100
    long_score: Optional[int]          # 0-7 composite score
    short_score: Optional[int]         # 0-7 composite score

    # Metadata
    bars_in_calculation: int


# =============================================================================
# MAIN CALCULATOR CLASS
# =============================================================================

class M1IndicatorBarsCalculator:
    """
    Calculates M1 indicator bars for a full trading day.

    Produces one row per 1-minute bar in the 08:00-16:00 window,
    with all indicators and structure calculated at each bar.
    """

    def __init__(
        self,
        m1_fetcher: M1Fetcher = None,
        indicator_calculator: M1IndicatorCalculator = None,
        structure_analyzer: StructureAnalyzer = None,
        verbose: bool = True
    ):
        """
        Initialize the calculator.

        Args:
            m1_fetcher: M1Fetcher instance
            indicator_calculator: M1IndicatorCalculator instance
            structure_analyzer: StructureAnalyzer instance
            verbose: Enable verbose logging
        """
        self.m1_fetcher = m1_fetcher or M1Fetcher()
        self.indicator_calculator = indicator_calculator or M1IndicatorCalculator()
        self.structure_analyzer = structure_analyzer or StructureAnalyzer()
        self.verbose = verbose
        self.logger = logging.getLogger(__name__)

    def _log(self, message: str, level: str = 'info'):
        """Log message if verbose mode enabled."""
        if self.verbose:
            prefix = {'error': '!', 'warning': '?', 'info': ' ', 'debug': '  '}
            print(f"  {prefix.get(level, ' ')} {message}")

    def calculate_for_ticker_date(
        self,
        ticker: str,
        trade_date: date
    ) -> List[M1IndicatorBarResult]:
        """
        Calculate all M1 indicator bars for a single ticker-date.

        Args:
            ticker: Stock symbol
            trade_date: Trading date

        Returns:
            List of M1IndicatorBarResult objects (one per bar in trading day)
        """
        self._log(f"Calculating M1 indicator bars for {ticker} on {trade_date}")

        # Fetch extended M1 bars (includes prior day for indicator calculation)
        df = self.m1_fetcher.fetch_extended_trading_day(ticker, trade_date)

        if df.empty:
            self._log(f"No M1 bars found for {ticker} on {trade_date}", 'warning')
            return []

        self._log(f"Fetched {len(df)} M1 bars (including extended lookback)")

        # Add all indicators to the DataFrame
        df = self.indicator_calculator.add_all_indicators(df)

        # Filter to only trading day bars (08:00-16:00) for output
        trading_day_df = df[
            (df['bar_date'] == trade_date) &
            (df['bar_time'] >= PREMARKET_START) &
            (df['bar_time'] <= MARKET_CLOSE)
        ].copy()

        if trading_day_df.empty:
            self._log(f"No trading day bars for {ticker} on {trade_date}", 'warning')
            return []

        self._log(f"Processing {len(trading_day_df)} trading day bars")

        # Calculate structure and build results for each bar
        results = []

        for idx, row in trading_day_df.iterrows():
            bar_time = row['bar_time']

            # Get structure at this bar time
            structures = self.structure_analyzer.get_all_structures(
                ticker=ticker,
                trade_date=trade_date,
                bar_time=bar_time
            )

            # Calculate bars_in_calculation (all bars up to this point)
            bars_before = len(df[
                ((df['bar_date'] < trade_date) |
                 ((df['bar_date'] == trade_date) & (df['bar_time'] <= bar_time)))
            ])

            # Build result
            result = M1IndicatorBarResult(
                ticker=ticker,
                bar_date=trade_date,
                bar_time=bar_time,

                # OHLCV
                open=float(row['open']),
                high=float(row['high']),
                low=float(row['low']),
                close=float(row['close']),
                volume=int(row['volume']),

                # Price Indicators
                vwap=self._safe_float(row.get('vwap_calc')),
                sma9=self._safe_float(row.get('sma9')),
                sma21=self._safe_float(row.get('sma21')),
                sma_spread=self._safe_float(row.get('sma_spread')),
                sma_momentum_ratio=self._safe_float(row.get('sma_momentum_ratio')),
                sma_momentum_label=row.get('sma_momentum_label'),

                # Volume Indicators
                vol_roc=self._safe_float(row.get('vol_roc')),
                vol_delta=self._safe_float(row.get('vol_delta')),
                cvd_slope=self._safe_float(row.get('cvd_slope')),

                # Structure (including M1)
                h4_structure=structures['H4'].direction_label if structures.get('H4') else None,
                h1_structure=structures['H1'].direction_label if structures.get('H1') else None,
                m15_structure=structures['M15'].direction_label if structures.get('M15') else None,
                m5_structure=structures['M5'].direction_label if structures.get('M5') else None,
                m1_structure=structures['M1'].direction_label if structures.get('M1') else None,

                # Health Score
                health_score=self._safe_int(row.get('health_score')),

                # Entry Qualifier Indicators
                candle_range_pct=self._safe_float(row.get('candle_range_pct')),
                long_score=self._safe_int(row.get('long_score')),
                short_score=self._safe_int(row.get('short_score')),

                # Metadata
                bars_in_calculation=bars_before
            )

            results.append(result)

        self._log(f"Calculated {len(results)} M1 indicator bars")

        return results

    def calculate_bars_before_entry(
        self,
        ticker: str,
        trade_date: date,
        entry_time: time,
        num_bars: int = 15
    ) -> List[M1IndicatorBarResult]:
        """
        Calculate M1 indicator bars for a specific number of bars before entry.

        Optimized for ramp-up chart display where we only need ~15 bars
        immediately before entry time.

        Args:
            ticker: Stock symbol
            trade_date: Trading date
            entry_time: Entry time
            num_bars: Number of bars before entry to calculate

        Returns:
            List of M1IndicatorBarResult objects
        """
        self._log(f"Calculating {num_bars} M1 bars before {entry_time} for {ticker} on {trade_date}")

        # Fetch bars before entry time
        df = self.m1_fetcher.fetch_bars_before_time(ticker, trade_date, entry_time)

        if df.empty:
            self._log(f"No M1 bars found for {ticker} on {trade_date}", 'warning')
            return []

        # Add all indicators to the DataFrame
        df = self.indicator_calculator.add_all_indicators(df)

        # Take the last N bars (closest to entry)
        if len(df) > num_bars:
            df = df.tail(num_bars).copy()
        else:
            df = df.copy()

        self._log(f"Processing {len(df)} bars before entry")

        # Calculate structure and build results
        results = []

        for idx, row in df.iterrows():
            bar_date = row['bar_date']
            bar_time = row['bar_time']

            # Get structure at this bar time
            structures = self.structure_analyzer.get_all_structures(
                ticker=ticker,
                trade_date=bar_date,
                bar_time=bar_time
            )

            # Build result
            result = M1IndicatorBarResult(
                ticker=ticker,
                bar_date=bar_date,
                bar_time=bar_time,

                # OHLCV
                open=float(row['open']),
                high=float(row['high']),
                low=float(row['low']),
                close=float(row['close']),
                volume=int(row['volume']),

                # Price Indicators
                vwap=self._safe_float(row.get('vwap_calc')),
                sma9=self._safe_float(row.get('sma9')),
                sma21=self._safe_float(row.get('sma21')),
                sma_spread=self._safe_float(row.get('sma_spread')),
                sma_momentum_ratio=self._safe_float(row.get('sma_momentum_ratio')),
                sma_momentum_label=row.get('sma_momentum_label'),

                # Volume Indicators
                vol_roc=self._safe_float(row.get('vol_roc')),
                vol_delta=self._safe_float(row.get('vol_delta')),
                cvd_slope=self._safe_float(row.get('cvd_slope')),

                # Structure
                h4_structure=structures['H4'].direction_label if structures.get('H4') else None,
                h1_structure=structures['H1'].direction_label if structures.get('H1') else None,
                m15_structure=structures['M15'].direction_label if structures.get('M15') else None,
                m5_structure=structures['M5'].direction_label if structures.get('M5') else None,
                m1_structure=structures['M1'].direction_label if structures.get('M1') else None,

                # Health Score
                health_score=self._safe_int(row.get('health_score')),

                # Entry Qualifier Indicators
                candle_range_pct=self._safe_float(row.get('candle_range_pct')),
                long_score=self._safe_int(row.get('long_score')),
                short_score=self._safe_int(row.get('short_score')),

                # Metadata
                bars_in_calculation=idx + 1
            )

            results.append(result)

        self._log(f"Calculated {len(results)} M1 indicator bars before entry")

        return results

    def _safe_float(self, value) -> Optional[float]:
        """Convert value to float, returning None for NaN."""
        if value is None:
            return None
        if isinstance(value, float) and (np.isnan(value) or np.isinf(value)):
            return None
        try:
            return round(float(value), 6)
        except (ValueError, TypeError):
            return None

    def _safe_int(self, value) -> Optional[int]:
        """Convert value to int, returning None for NaN."""
        if value is None:
            return None
        if isinstance(value, float) and np.isnan(value):
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    def clear_caches(self):
        """Clear all internal caches."""
        self.m1_fetcher.clear_cache()
        self.structure_analyzer.clear_cache()


# =============================================================================
# STANDALONE TEST
# =============================================================================

if __name__ == "__main__":
    print("M1 Indicator Bars - Calculator Test")
    print("=" * 60)

    calculator = M1IndicatorBarsCalculator(verbose=True)

    test_ticker = "SPY"
    test_date = date(2025, 12, 30)

    print(f"\nCalculating M1 indicator bars for {test_ticker} on {test_date}...")

    results = calculator.calculate_for_ticker_date(test_ticker, test_date)

    if results:
        print(f"\n{'='*60}")
        print(f"Results: {len(results)} bars")
        print(f"{'='*60}")

        # Show first few bars
        print("\nFirst 3 bars:")
        for r in results[:3]:
            print(f"  {r.bar_time}: C=${r.close:.2f} SMA9={r.sma9:.2f if r.sma9 else 'N/A'} "
                  f"M1={r.m1_structure} H={r.health_score}")

        # Show last few bars
        print("\nLast 3 bars:")
        for r in results[-3:]:
            print(f"  {r.bar_time}: C=${r.close:.2f} SMA9={r.sma9:.2f if r.sma9 else 'N/A'} "
                  f"M1={r.m1_structure} H={r.health_score}")

        # Test calculate_bars_before_entry
        print("\n" + "="*60)
        print("Testing calculate_bars_before_entry (15 bars before 10:30)...")
        entry_time = time(10, 30)
        entry_bars = calculator.calculate_bars_before_entry(test_ticker, test_date, entry_time, num_bars=15)
        print(f"Got {len(entry_bars)} bars before entry")
        if entry_bars:
            print(f"  First bar: {entry_bars[0].bar_time}")
            print(f"  Last bar: {entry_bars[-1].bar_time}")
    else:
        print("No results (may be holiday or weekend)")

    calculator.clear_caches()
    print("\nDone.")
