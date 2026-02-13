"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
M5 Indicator Bars - Calculator
XIII Trading LLC
================================================================================

Core calculator that computes all M5 indicator bars for a single ticker-date.
Combines M5 bar fetching, indicator calculations, and structure detection.

Produces direction-agnostic bars for the full trading day (09:30 to 16:00 ET).

Version: 1.0.0
================================================================================
"""

from dataclasses import dataclass
from datetime import datetime, date, time, timedelta
from typing import Dict, List, Optional, Any
import logging
import pandas as pd
import numpy as np

from config import (
    MARKET_OPEN,
    MARKET_CLOSE,
    CALCULATION_VERSION
)

from m5_fetcher import M5Fetcher
from indicators import M5IndicatorCalculator
from structure import StructureAnalyzer, StructureResult


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class M5IndicatorBarResult:
    """Complete M5 indicator bar result for database insertion."""
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

    # Metadata
    bars_in_calculation: int


# =============================================================================
# MAIN CALCULATOR CLASS
# =============================================================================

class M5IndicatorBarsCalculator:
    """
    Calculates M5 indicator bars for a full trading day.

    Produces one row per 5-minute bar in the 09:30-16:00 window,
    with all indicators and structure calculated at each bar.
    """

    def __init__(
        self,
        m5_fetcher: M5Fetcher = None,
        indicator_calculator: M5IndicatorCalculator = None,
        structure_analyzer: StructureAnalyzer = None,
        verbose: bool = True
    ):
        """
        Initialize the calculator.

        Args:
            m5_fetcher: M5Fetcher instance
            indicator_calculator: M5IndicatorCalculator instance
            structure_analyzer: StructureAnalyzer instance
            verbose: Enable verbose logging
        """
        self.m5_fetcher = m5_fetcher or M5Fetcher()
        self.indicator_calculator = indicator_calculator or M5IndicatorCalculator()
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
    ) -> List[M5IndicatorBarResult]:
        """
        Calculate all M5 indicator bars for a single ticker-date.

        Args:
            ticker: Stock symbol
            trade_date: Trading date

        Returns:
            List of M5IndicatorBarResult objects (one per bar in trading day)
        """
        self._log(f"Calculating M5 indicator bars for {ticker} on {trade_date}")

        # Fetch extended M5 bars (includes prior day for indicator calculation)
        df = self.m5_fetcher.fetch_extended_trading_day(ticker, trade_date)

        if df.empty:
            self._log(f"No M5 bars found for {ticker} on {trade_date}", 'warning')
            return []

        self._log(f"Fetched {len(df)} M5 bars (including extended lookback)")

        # Add all indicators to the DataFrame
        df = self.indicator_calculator.add_all_indicators(df)

        # Filter to only trading day bars (09:30-16:00) for output
        trading_day_df = df[
            (df['bar_date'] == trade_date) &
            (df['bar_time'] >= MARKET_OPEN) &
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
            result = M5IndicatorBarResult(
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

                # Structure
                h4_structure=structures['H4'].direction_label if structures.get('H4') else None,
                h1_structure=structures['H1'].direction_label if structures.get('H1') else None,
                m15_structure=structures['M15'].direction_label if structures.get('M15') else None,
                m5_structure=structures['M5'].direction_label if structures.get('M5') else None,

                # Metadata
                bars_in_calculation=bars_before
            )

            results.append(result)

        self._log(f"Calculated {len(results)} M5 indicator bars")

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

    def clear_caches(self):
        """Clear all internal caches."""
        self.m5_fetcher.clear_cache()
        self.structure_analyzer.clear_cache()


# =============================================================================
# STANDALONE TEST
# =============================================================================

if __name__ == "__main__":
    print("M5 Indicator Bars - Calculator Test")
    print("=" * 60)

    calculator = M5IndicatorBarsCalculator(verbose=True)

    test_ticker = "SPY"
    test_date = date(2025, 12, 30)

    print(f"\nCalculating M5 indicator bars for {test_ticker} on {test_date}...")

    results = calculator.calculate_for_ticker_date(test_ticker, test_date)

    if results:
        print(f"\n{'='*60}")
        print(f"Results: {len(results)} bars")
        print(f"{'='*60}")

        # Show first few bars
        print("\nFirst 3 bars:")
        for r in results[:3]:
            print(f"  {r.bar_time}: C=${r.close:.2f} SMA9={r.sma9:.2f if r.sma9 else 'N/A'} "
                  f"M5={r.m5_structure} H1={r.h1_structure}")

        # Show last few bars
        print("\nLast 3 bars:")
        for r in results[-3:]:
            print(f"  {r.bar_time}: C=${r.close:.2f} SMA9={r.sma9:.2f if r.sma9 else 'N/A'} "
                  f"M5={r.m5_structure} H1={r.h1_structure}")
    else:
        print("No results (may be holiday or weekend)")

    calculator.clear_caches()
    print("\nDone.")
