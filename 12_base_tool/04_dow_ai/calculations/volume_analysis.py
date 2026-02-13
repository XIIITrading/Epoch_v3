"""
DOW AI - Volume Analysis
Epoch Trading System v1 - XIII Trading LLC

Volume Delta, Rate of Change, and Cumulative Volume Delta calculations.
"""
import pandas as pd
import numpy as np
from typing import Tuple, List, Dict
from dataclasses import dataclass
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    VOLUME_DELTA_BARS,
    VOLUME_ROC_BASELINE,
    CVD_WINDOW,
    VERBOSE,
    debug_print
)

# Add shared library
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "03_indicators" / "python"))
from core.volume_delta import calculate_bar_delta as _shared_bar_delta
from core.volume_roc import calculate_volume_roc as _shared_volume_roc
from core.cvd import calculate_cvd_slope as _shared_cvd_slope


@dataclass
class VolumeResult:
    """Volume analysis results."""
    delta_5bar: float
    delta_signal: str  # 'Bullish', 'Bearish', 'Neutral'
    roc_percent: float
    roc_signal: str  # 'Above Avg', 'Below Avg', 'Average'
    cvd_trend: str  # 'Rising', 'Falling', 'Flat'
    cvd_values: List[float]


class VolumeAnalyzer:
    """
    Analyzes volume metrics for trading signals.

    Calculates:
    - Volume Delta: Net buying/selling pressure over N bars
    - Volume ROC: Rate of change vs baseline average
    - CVD: Cumulative Volume Delta trend
    """

    def __init__(
        self,
        delta_bars: int = None,
        roc_baseline: int = None,
        cvd_window: int = None,
        verbose: bool = None
    ):
        """
        Initialize volume analyzer.

        Args:
            delta_bars: Bars for rolling delta calculation
            roc_baseline: Bars for baseline average
            cvd_window: Bars for CVD trend analysis
            verbose: Enable verbose output
        """
        self.delta_bars = delta_bars or VOLUME_DELTA_BARS
        self.roc_baseline = roc_baseline or VOLUME_ROC_BASELINE
        self.cvd_window = cvd_window or CVD_WINDOW
        self.verbose = verbose if verbose is not None else VERBOSE

    def calculate_bar_delta(self, row: pd.Series) -> float:
        """
        Calculate volume delta for a single bar using shared library.

        Args:
            row: Series with open, high, low, close, volume

        Returns:
            Volume delta (positive = buying, negative = selling)
        """
        result = _shared_bar_delta(
            open_price=row['open'],
            high=row['high'],
            low=row['low'],
            close=row['close'],
            volume=int(row['volume'])
        )
        return result.bar_delta

    def calculate_rolling_delta(self, df: pd.DataFrame, bars: int = None) -> float:
        """
        Calculate rolling volume delta over N bars.

        Args:
            df: DataFrame with OHLCV data
            bars: Number of bars (default from config)

        Returns:
            Sum of bar deltas over the period
        """
        bars = bars or self.delta_bars
        recent = df.tail(bars)

        total_delta = sum(self.calculate_bar_delta(row) for _, row in recent.iterrows())
        return total_delta

    def calculate_volume_roc(self, df: pd.DataFrame) -> Tuple[float, float]:
        """
        Calculate volume rate of change using shared library.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            Tuple of (roc_percent, baseline_avg)
        """
        if len(df) < self.roc_baseline + 1:
            return 0.0, 0.0

        bars = df.to_dict('records')
        result = _shared_volume_roc(bars, baseline_period=self.roc_baseline)

        return result.roc or 0.0, result.baseline_avg or 0.0

    def calculate_cvd(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate Cumulative Volume Delta series.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            Series of cumulative delta values
        """
        deltas = df.apply(self.calculate_bar_delta, axis=1)
        return deltas.cumsum()

    def determine_cvd_trend(self, df: pd.DataFrame) -> str:
        """
        Determine CVD trend using shared library.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            'Rising', 'Falling', or 'Flat'
        """
        if len(df) < self.cvd_window:
            return 'Flat'

        bars = df.to_dict('records')
        result = _shared_cvd_slope(bars, window=self.cvd_window)

        return result.trend

    def analyze(self, df: pd.DataFrame) -> VolumeResult:
        """
        Complete volume analysis.

        Args:
            df: DataFrame with OHLCV data (M1 bars recommended)

        Returns:
            VolumeResult with all metrics
        """
        if df is None or len(df) < self.roc_baseline:
            if self.verbose:
                debug_print(f"Insufficient data for volume analysis")
            return VolumeResult(
                delta_5bar=0.0,
                delta_signal='Neutral',
                roc_percent=0.0,
                roc_signal='Average',
                cvd_trend='Flat',
                cvd_values=[]
            )

        # Rolling delta
        delta = self.calculate_rolling_delta(df)
        if delta > 0:
            delta_signal = 'Bullish'
        elif delta < 0:
            delta_signal = 'Bearish'
        else:
            delta_signal = 'Neutral'

        # Volume ROC
        roc, baseline = self.calculate_volume_roc(df)
        if roc > 20:
            roc_signal = 'Above Avg'
        elif roc < -20:
            roc_signal = 'Below Avg'
        else:
            roc_signal = 'Average'

        # CVD trend
        cvd_trend = self.determine_cvd_trend(df)
        cvd_series = self.calculate_cvd(df)
        cvd_values = cvd_series.tail(self.cvd_window).tolist()

        if self.verbose:
            debug_print(f"Volume: Delta={delta:+,.0f} ({delta_signal}) | ROC={roc:+.1f}% | CVD={cvd_trend}")

        return VolumeResult(
            delta_5bar=delta,
            delta_signal=delta_signal,
            roc_percent=roc,
            roc_signal=roc_signal,
            cvd_trend=cvd_trend,
            cvd_values=cvd_values
        )

    def calculate_delta_by_timeframe(
        self,
        data: Dict[str, pd.DataFrame],
        bars: int = 5
    ) -> Dict[str, Dict]:
        """
        Calculate rolling delta for multiple timeframes.

        Args:
            data: Dict mapping timeframe -> DataFrame
            bars: Number of bars for rolling calculation

        Returns:
            Dict mapping timeframe -> {'delta': float, 'signal': str}
        """
        results = {}

        for tf, df in data.items():
            if df is None or len(df) < bars:
                results[tf] = {'delta': 0.0, 'signal': 'Neutral'}
                continue

            delta = self.calculate_rolling_delta(df, bars)

            if delta > 0:
                signal = 'Bullish'
            elif delta < 0:
                signal = 'Bearish'
            else:
                signal = 'Neutral'

            results[tf] = {
                'delta': delta,
                'signal': signal
            }

        if self.verbose:
            debug_print(f"Calculated delta for {len(results)} timeframes")

        return results

    def get_cvd_overall_direction(self, df: pd.DataFrame) -> str:
        """
        Determine overall CVD direction (accumulation vs distribution).

        Args:
            df: DataFrame with OHLCV data

        Returns:
            'ACCUMULATION', 'DISTRIBUTION', or 'FLAT'
        """
        if df is None or len(df) < 10:
            return 'FLAT'

        cvd = self.calculate_cvd(df)

        # Compare first half to second half
        mid = len(cvd) // 2
        first_half_avg = cvd.iloc[:mid].mean()
        second_half_avg = cvd.iloc[mid:].mean()

        if second_half_avg > first_half_avg * 1.1:
            return 'ACCUMULATION'
        elif second_half_avg < first_half_avg * 0.9:
            return 'DISTRIBUTION'
        else:
            return 'FLAT'

    def check_cvd_divergence(
        self,
        df: pd.DataFrame,
        direction: str
    ) -> Dict[str, any]:
        """
        Check for CVD divergence with price.

        Args:
            df: DataFrame with OHLCV data
            direction: Trade direction ('long' or 'short')

        Returns:
            Dict with divergence info
        """
        if df is None or len(df) < 20:
            return {'divergence': False, 'type': None, 'description': 'Insufficient data'}

        cvd = self.calculate_cvd(df)
        prices = df['close']

        # Get recent lows and highs
        recent_half = len(df) // 2
        first_half_price_low = prices.iloc[:recent_half].min()
        second_half_price_low = prices.iloc[recent_half:].min()
        first_half_cvd_low = cvd.iloc[:recent_half].min()
        second_half_cvd_low = cvd.iloc[recent_half:].min()

        first_half_price_high = prices.iloc[:recent_half].max()
        second_half_price_high = prices.iloc[recent_half:].max()
        first_half_cvd_high = cvd.iloc[:recent_half].max()
        second_half_cvd_high = cvd.iloc[recent_half:].max()

        # Bullish divergence: price makes lower low, CVD makes higher low
        if second_half_price_low < first_half_price_low and second_half_cvd_low > first_half_cvd_low:
            return {
                'divergence': True,
                'type': 'bullish',
                'description': 'Price lower low, CVD higher low (bullish divergence)'
            }

        # Bearish divergence: price makes higher high, CVD makes lower high
        if second_half_price_high > first_half_price_high and second_half_cvd_high < first_half_cvd_high:
            return {
                'divergence': True,
                'type': 'bearish',
                'description': 'Price higher high, CVD lower high (bearish divergence)'
            }

        return {'divergence': False, 'type': None, 'description': 'No divergence'}


# =============================================================================
# STANDALONE TEST
# =============================================================================
if __name__ == '__main__':
    print("=" * 60)
    print("VOLUME ANALYZER - STANDALONE TEST")
    print("=" * 60)

    # Import polygon fetcher for test data
    from data.polygon_fetcher import PolygonFetcher

    fetcher = PolygonFetcher(verbose=False)
    analyzer = VolumeAnalyzer(verbose=True)

    # Test with SPY M1 data
    print("\n[TEST 1] SPY M1 Volume Analysis...")
    df = fetcher.fetch_bars('SPY', 'M1', bars_needed=50)

    if df is not None:
        result = analyzer.analyze(df)
        print(f"  Delta (5-bar):  {result.delta_5bar:+,.0f} ({result.delta_signal})")
        print(f"  Volume ROC:     {result.roc_percent:+.1f}% ({result.roc_signal})")
        print(f"  CVD Trend:      {result.cvd_trend}")
        print(f"  CVD Values:     {len(result.cvd_values)} values")
    else:
        print("  FAILED: Could not fetch data")

    # Test with TSLA M1 data
    print("\n[TEST 2] TSLA M1 Volume Analysis...")
    df = fetcher.fetch_bars('TSLA', 'M1', bars_needed=50)

    if df is not None:
        result = analyzer.analyze(df)
        print(f"  Delta (5-bar):  {result.delta_5bar:+,.0f} ({result.delta_signal})")
        print(f"  Volume ROC:     {result.roc_percent:+.1f}% ({result.roc_signal})")
        print(f"  CVD Trend:      {result.cvd_trend}")
    else:
        print("  FAILED: Could not fetch data")

    # Test individual bar delta
    print("\n[TEST 3] Individual Bar Delta Calculation...")
    if df is not None and len(df) > 0:
        last_bar = df.iloc[-1]
        delta = analyzer.calculate_bar_delta(last_bar)
        bar_type = "GREEN" if last_bar['close'] > last_bar['open'] else "RED"
        print(f"  Last bar: {bar_type}")
        print(f"  Open: ${last_bar['open']:.2f}, Close: ${last_bar['close']:.2f}")
        print(f"  Volume: {last_bar['volume']:,.0f}")
        print(f"  Delta:  {delta:+,.0f}")

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
