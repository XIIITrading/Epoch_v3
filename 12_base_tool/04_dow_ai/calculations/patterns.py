"""
DOW AI - Candlestick Pattern Detection
Epoch Trading System v1 - XIII Trading LLC

Detects: Engulfing, Doji, Double Top/Bottom patterns.
"""
import pandas as pd
from typing import List, Dict
from dataclasses import dataclass
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import VERBOSE, debug_print


@dataclass
class PatternResult:
    """Detected candlestick pattern."""
    pattern: str
    price: float
    bars_ago: int
    direction: str  # 'bullish', 'bearish', 'neutral'


class PatternDetector:
    """
    Detects candlestick patterns in bar data.

    Patterns detected:
    - Doji: Small body relative to range (indecision)
    - Bullish Engulfing: Current green candle engulfs previous red
    - Bearish Engulfing: Current red candle engulfs previous green
    - Double Top: Two similar highs (bearish reversal)
    - Double Bottom: Two similar lows (bullish reversal)
    """

    def __init__(self, doji_threshold: float = 0.1, verbose: bool = None):
        """
        Initialize pattern detector.

        Args:
            doji_threshold: Max body/range ratio for doji (default 10%)
            verbose: Enable verbose output
        """
        self.doji_threshold = doji_threshold
        self.verbose = verbose if verbose is not None else VERBOSE

    def _body_size(self, row: pd.Series) -> float:
        """Calculate absolute body size."""
        return abs(row['close'] - row['open'])

    def _range_size(self, row: pd.Series) -> float:
        """Calculate bar range (high - low)."""
        return row['high'] - row['low']

    def _is_bullish(self, row: pd.Series) -> bool:
        """Check if bar is bullish (green)."""
        return row['close'] > row['open']

    def _is_bearish(self, row: pd.Series) -> bool:
        """Check if bar is bearish (red)."""
        return row['close'] < row['open']

    def detect_doji(self, df: pd.DataFrame, lookback: int = 5) -> List[PatternResult]:
        """
        Detect doji candles (small body relative to range).

        Args:
            df: DataFrame with OHLC data
            lookback: Number of recent bars to check

        Returns:
            List of PatternResult for each doji found
        """
        patterns = []
        recent = df.tail(lookback)

        for i, (idx, row) in enumerate(recent.iterrows()):
            bars_ago = lookback - i - 1
            range_size = self._range_size(row)

            if range_size == 0:
                continue

            body_ratio = self._body_size(row) / range_size

            if body_ratio <= self.doji_threshold:
                patterns.append(PatternResult(
                    pattern='Doji',
                    price=row['close'],
                    bars_ago=bars_ago,
                    direction='neutral'
                ))

        return patterns

    def detect_engulfing(self, df: pd.DataFrame, lookback: int = 5) -> List[PatternResult]:
        """
        Detect bullish and bearish engulfing patterns.

        Args:
            df: DataFrame with OHLC data
            lookback: Number of recent bars to check

        Returns:
            List of PatternResult for each engulfing pattern found
        """
        patterns = []
        recent = df.tail(lookback + 1)  # Need one extra for comparison

        for i in range(1, len(recent)):
            bars_ago = lookback - i
            if bars_ago < 0:
                continue

            prev = recent.iloc[i - 1]
            curr = recent.iloc[i]

            # Bullish engulfing: previous red, current green engulfs
            if (self._is_bearish(prev) and self._is_bullish(curr) and
                curr['open'] <= prev['close'] and curr['close'] >= prev['open']):
                patterns.append(PatternResult(
                    pattern='Bullish Engulfing',
                    price=curr['close'],
                    bars_ago=bars_ago,
                    direction='bullish'
                ))

            # Bearish engulfing: previous green, current red engulfs
            if (self._is_bullish(prev) and self._is_bearish(curr) and
                curr['open'] >= prev['close'] and curr['close'] <= prev['open']):
                patterns.append(PatternResult(
                    pattern='Bearish Engulfing',
                    price=curr['close'],
                    bars_ago=bars_ago,
                    direction='bearish'
                ))

        return patterns

    def detect_double_top(self, df: pd.DataFrame, tolerance: float = 0.002) -> List[PatternResult]:
        """
        Detect double top pattern (two similar highs - bearish reversal).

        Args:
            df: DataFrame with OHLC data
            tolerance: Price tolerance for matching highs (default 0.2%)

        Returns:
            List of PatternResult for each double top found
        """
        patterns = []

        if len(df) < 10:
            return patterns

        recent = df.tail(20)
        highs = recent['high'].values

        # Find local peaks
        peaks = []
        for i in range(2, len(highs) - 2):
            if (highs[i] > highs[i-1] and highs[i] > highs[i-2] and
                highs[i] > highs[i+1] and highs[i] > highs[i+2]):
                peaks.append((i, highs[i]))

        # Check for double top (two similar highs)
        for i in range(len(peaks) - 1):
            idx1, high1 = peaks[i]
            idx2, high2 = peaks[i + 1]

            # Check if highs are within tolerance
            if abs(high1 - high2) / high1 <= tolerance:
                bars_ago = len(recent) - idx2 - 1
                patterns.append(PatternResult(
                    pattern='Double Top',
                    price=(high1 + high2) / 2,
                    bars_ago=bars_ago,
                    direction='bearish'
                ))

        return patterns

    def detect_double_bottom(self, df: pd.DataFrame, tolerance: float = 0.002) -> List[PatternResult]:
        """
        Detect double bottom pattern (two similar lows - bullish reversal).

        Args:
            df: DataFrame with OHLC data
            tolerance: Price tolerance for matching lows (default 0.2%)

        Returns:
            List of PatternResult for each double bottom found
        """
        patterns = []

        if len(df) < 10:
            return patterns

        recent = df.tail(20)
        lows = recent['low'].values

        # Find local troughs
        troughs = []
        for i in range(2, len(lows) - 2):
            if (lows[i] < lows[i-1] and lows[i] < lows[i-2] and
                lows[i] < lows[i+1] and lows[i] < lows[i+2]):
                troughs.append((i, lows[i]))

        # Check for double bottom (two similar lows)
        for i in range(len(troughs) - 1):
            idx1, low1 = troughs[i]
            idx2, low2 = troughs[i + 1]

            # Check if lows are within tolerance
            if abs(low1 - low2) / low1 <= tolerance:
                bars_ago = len(recent) - idx2 - 1
                patterns.append(PatternResult(
                    pattern='Double Bottom',
                    price=(low1 + low2) / 2,
                    bars_ago=bars_ago,
                    direction='bullish'
                ))

        return patterns

    def detect_all(self, df: pd.DataFrame) -> List[PatternResult]:
        """
        Run all pattern detections.

        Args:
            df: DataFrame with OHLC data

        Returns:
            List of all detected patterns, sorted by bars_ago
        """
        all_patterns = []
        all_patterns.extend(self.detect_doji(df))
        all_patterns.extend(self.detect_engulfing(df))
        all_patterns.extend(self.detect_double_top(df))
        all_patterns.extend(self.detect_double_bottom(df))

        # Sort by bars_ago (most recent first)
        all_patterns.sort(key=lambda x: x.bars_ago)

        if self.verbose:
            debug_print(f"Detected {len(all_patterns)} patterns")

        return all_patterns

    def detect_multi_timeframe(self, data: Dict[str, pd.DataFrame]) -> Dict[str, List[PatternResult]]:
        """
        Detect patterns across multiple timeframes.

        Args:
            data: Dict mapping timeframe -> DataFrame

        Returns:
            Dict mapping timeframe -> List[PatternResult]
        """
        results = {}
        for tf, df in data.items():
            results[tf] = self.detect_all(df)

        if self.verbose:
            total = sum(len(p) for p in results.values())
            debug_print(f"Detected {total} patterns across {len(results)} timeframes")

        return results


# =============================================================================
# STANDALONE TEST
# =============================================================================
if __name__ == '__main__':
    print("=" * 60)
    print("PATTERN DETECTOR - STANDALONE TEST")
    print("=" * 60)

    # Import polygon fetcher for test data
    from data.polygon_fetcher import PolygonFetcher

    fetcher = PolygonFetcher(verbose=False)
    detector = PatternDetector(verbose=True)

    # Test with SPY M5 data
    print("\n[TEST 1] SPY M5 Pattern Detection...")
    df = fetcher.fetch_bars('SPY', 'M5', bars_needed=50)

    if df is not None:
        patterns = detector.detect_all(df)
        if patterns:
            for p in patterns[:5]:  # Show first 5
                ago = "current bar" if p.bars_ago == 0 else f"{p.bars_ago} bars ago"
                print(f"  {p.pattern}: ${p.price:.2f} ({ago}) - {p.direction}")
        else:
            print("  No patterns detected")
    else:
        print("  FAILED: Could not fetch data")

    # Test with TSLA M15 data
    print("\n[TEST 2] TSLA M15 Pattern Detection...")
    df = fetcher.fetch_bars('TSLA', 'M15', bars_needed=50)

    if df is not None:
        patterns = detector.detect_all(df)
        if patterns:
            for p in patterns[:5]:
                ago = "current bar" if p.bars_ago == 0 else f"{p.bars_ago} bars ago"
                print(f"  {p.pattern}: ${p.price:.2f} ({ago}) - {p.direction}")
        else:
            print("  No patterns detected")
    else:
        print("  FAILED: Could not fetch data")

    # Test multi-timeframe
    print("\n[TEST 3] Multi-Timeframe Pattern Detection (NVDA)...")
    data = fetcher.fetch_multi_timeframe('NVDA', ['M5', 'M15', 'H1'])

    if data:
        results = detector.detect_multi_timeframe(data)
        for tf, patterns in results.items():
            print(f"  {tf}: {len(patterns)} patterns")
            for p in patterns[:2]:  # Show first 2 per TF
                print(f"       - {p.pattern}: ${p.price:.2f} ({p.direction})")
    else:
        print("  FAILED: Could not fetch data")

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
