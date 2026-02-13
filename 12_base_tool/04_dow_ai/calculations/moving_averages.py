"""
DOW AI - Moving Average Analysis
Epoch Trading System v1 - XIII Trading LLC

SMA9/SMA21 calculations for trend and momentum analysis.
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional
from dataclasses import dataclass
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import VERBOSE, debug_print

# Add shared library
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "03_indicators" / "python"))
from core.sma import calculate_sma_spread as _shared_sma_spread, calculate_sma_momentum as _shared_sma_momentum


@dataclass
class SMAResult:
    """SMA calculation result for a single timeframe."""
    sma9: float
    sma21: float
    spread: float
    spread_trend: str  # 'WIDENING', 'NARROWING', 'FLAT'
    alignment: str     # 'BULLISH', 'BEARISH', 'NEUTRAL'
    cross_price_estimate: Optional[float] = None


class MovingAverageAnalyzer:
    """
    Analyzes SMA9 and SMA21 for trend and momentum.

    Provides:
    - SMA alignment (bullish/bearish)
    - Spread between SMAs
    - Spread trend (widening = momentum, narrowing = fading)
    - Estimated cross price
    """

    def __init__(self, verbose: bool = None):
        """
        Initialize moving average analyzer.

        Args:
            verbose: Enable verbose output
        """
        self.verbose = verbose if verbose is not None else VERBOSE

    def calculate_smas(self, df: pd.DataFrame) -> SMAResult:
        """
        Calculate SMA9, SMA21, spread, and trends.

        Args:
            df: DataFrame with 'close' column

        Returns:
            SMAResult with all calculations
        """
        if df is None or len(df) < 21:
            if self.verbose:
                debug_print(f"Insufficient data for SMA: {len(df) if df is not None else 0} bars")
            return SMAResult(
                sma9=0.0,
                sma21=0.0,
                spread=0.0,
                spread_trend='FLAT',
                alignment='NEUTRAL',
                cross_price_estimate=None
            )

        # Convert DataFrame to list of dicts for shared library
        bars = df.to_dict('records')

        # Use shared library for spread calculation
        spread_result = _shared_sma_spread(bars)
        momentum_result = _shared_sma_momentum(bars)

        # Map momentum to spread_trend
        spread_trend = momentum_result.momentum  # WIDENING, NARROWING, FLAT

        if self.verbose:
            debug_print(f"SMA9: ${spread_result.sma9:.2f} | SMA21: ${spread_result.sma21:.2f} | {spread_result.alignment} | {spread_trend}")

        return SMAResult(
            sma9=spread_result.sma9 or 0.0,
            sma21=spread_result.sma21 or 0.0,
            spread=spread_result.spread or 0.0,
            spread_trend=spread_trend,
            alignment=spread_result.alignment or 'NEUTRAL',
            cross_price_estimate=spread_result.cross_estimate
        )

    def calculate_multi_timeframe(
        self,
        data: Dict[str, pd.DataFrame]
    ) -> Dict[str, SMAResult]:
        """
        Calculate SMAs for multiple timeframes.

        Args:
            data: Dict mapping timeframe -> DataFrame

        Returns:
            Dict mapping timeframe -> SMAResult
        """
        results = {}
        for tf, df in data.items():
            if tf in ['M5', 'M15']:
                results[tf] = self.calculate_smas(df)

        if self.verbose:
            debug_print(f"Calculated SMAs for {len(results)} timeframes")

        return results

    def get_delta_signal(self, result: SMAResult, direction: str) -> str:
        """
        Get alignment status for a trade direction.

        Args:
            result: SMAResult
            direction: 'long' or 'short'

        Returns:
            '✓' if aligned, '✗' if opposing, '⚠' if neutral
        """
        if result.alignment == 'NEUTRAL':
            return '⚠'

        if direction.lower() == 'long':
            return '✓' if result.alignment == 'BULLISH' else '✗'
        else:  # short
            return '✓' if result.alignment == 'BEARISH' else '✗'


# =============================================================================
# STANDALONE TEST
# =============================================================================
if __name__ == '__main__':
    print("=" * 60)
    print("MOVING AVERAGE ANALYZER - STANDALONE TEST")
    print("=" * 60)

    from data.polygon_fetcher import PolygonFetcher

    fetcher = PolygonFetcher(verbose=False)
    analyzer = MovingAverageAnalyzer(verbose=True)

    # Test with SPY M5 data
    print("\n[TEST 1] SPY M5 SMA Analysis...")
    df = fetcher.fetch_bars('SPY', 'M5', bars_needed=50)

    if df is not None:
        result = analyzer.calculate_smas(df)
        print(f"  SMA9:         ${result.sma9:.2f}")
        print(f"  SMA21:        ${result.sma21:.2f}")
        print(f"  Spread:       ${result.spread:+.2f}")
        print(f"  Alignment:    {result.alignment}")
        print(f"  Spread Trend: {result.spread_trend}")
        print(f"  Cross Est:    ${result.cross_price_estimate:.2f}")
    else:
        print("  FAILED: Could not fetch data")

    # Test multi-timeframe
    print("\n[TEST 2] TSLA Multi-Timeframe SMA...")
    data = fetcher.fetch_multi_timeframe('TSLA', ['M5', 'M15'])

    if data:
        results = analyzer.calculate_multi_timeframe(data)
        for tf, res in results.items():
            print(f"  {tf}: SMA9 ${res.sma9:.2f} | SMA21 ${res.sma21:.2f} | {res.alignment} | {res.spread_trend}")
    else:
        print("  FAILED: Could not fetch data")

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
