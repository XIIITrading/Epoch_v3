"""
DOW AI - Market Structure Calculator
Epoch Trading System v1 - XIII Trading LLC

Calculates BOS/ChoCH, strong/weak levels using fractal-based analysis.
Duplicated from 02_zone_system for standalone use.
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import FRACTAL_LENGTH, STRUCTURE_LABELS, VERBOSE, debug_print

# Add shared library - append to avoid config conflicts
_SHARED_LIB = str(Path(__file__).parent.parent.parent / "03_indicators" / "python")
if _SHARED_LIB not in sys.path:
    sys.path.append(_SHARED_LIB)
from structure.swing_detection import find_swing_highs as _shared_swing_highs, find_swing_lows as _shared_swing_lows


@dataclass
class StructureResult:
    """Market structure calculation result."""
    direction: str  # 'BULL', 'BEAR', 'NEUTRAL'
    strong_level: Optional[float]  # Invalidation level
    weak_level: Optional[float]  # Continuation target
    last_break: Optional[str]  # 'BOS' or 'ChoCH'
    last_break_price: Optional[float]


class MarketStructureCalculator:
    """
    Calculates market structure (BOS/ChoCH) for any timeframe.

    Uses fractal detection to identify swing highs/lows, then tracks
    structure breaks to determine bullish/bearish bias.
    """

    def __init__(self, fractal_length: int = None, verbose: bool = None):
        """
        Initialize market structure calculator.

        Args:
            fractal_length: Number of bars for fractal detection (default from config)
            verbose: Enable verbose output (default from config)
        """
        self.fractal_length = fractal_length or FRACTAL_LENGTH
        self.p = self.fractal_length // 2
        self.verbose = verbose if verbose is not None else VERBOSE

    def _detect_fractals(self, df: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
        """
        Detect bullish and bearish fractals using shared library.

        Bullish fractal: Local LOW (swing low) - potential support
        Bearish fractal: Local HIGH (swing high) - potential resistance

        Args:
            df: DataFrame with 'high' and 'low' columns

        Returns:
            Tuple of (bullish_fractals, bearish_fractals) as boolean Series
        """
        n = len(df)
        p = self.p

        bullish_fractals = pd.Series([False] * n, index=df.index)
        bearish_fractals = pd.Series([False] * n, index=df.index)

        if n < self.fractal_length:
            return bullish_fractals, bearish_fractals

        # Convert to list of dicts for shared library
        bars = df.to_dict('records')

        # Get swing points from shared library
        swing_high_values = _shared_swing_highs(bars, n - 1, self.fractal_length)
        swing_low_values = _shared_swing_lows(bars, n - 1, self.fractal_length)

        # Mark fractal positions in the series
        # Note: shared library returns values, not indices
        # We need to find which bars match these values
        for i in range(p, n - p):
            if df.iloc[i]['high'] in swing_high_values:
                bearish_fractals.iloc[i] = True
            if df.iloc[i]['low'] in swing_low_values:
                bullish_fractals.iloc[i] = True

        return bullish_fractals, bearish_fractals

    def calculate(self, df: pd.DataFrame) -> StructureResult:
        """
        Calculate market structure from bar data.

        Args:
            df: DataFrame with columns: open, high, low, close, volume

        Returns:
            StructureResult with direction, levels, and last break info
        """
        # Validate input
        if df is None or len(df) < self.fractal_length + 5:
            if self.verbose:
                debug_print(f"Insufficient data: {len(df) if df is not None else 0} bars")
            return StructureResult(
                direction='NEUTRAL',
                strong_level=None,
                weak_level=None,
                last_break=None,
                last_break_price=None
            )

        df = df.copy().reset_index(drop=True)

        # Detect fractals
        bullish_fractals, bearish_fractals = self._detect_fractals(df)

        # Track structure
        structure = 0  # 1 = Bull, -1 = Bear, 0 = Neutral
        upper_fractal = None  # Last bearish fractal (swing high)
        lower_fractal = None  # Last bullish fractal (swing low)
        upper_crossed = False
        lower_crossed = False
        last_break = None
        last_break_price = None
        bull_weak_high = None  # Highest high in bull structure
        bear_weak_low = None  # Lowest low in bear structure

        for i in range(len(df)):
            close = df.iloc[i]['close']
            high = df.iloc[i]['high']
            low = df.iloc[i]['low']

            # Update fractal levels when new fractals are detected
            if bearish_fractals.iloc[i]:
                upper_fractal = df.iloc[i]['high']
                upper_crossed = False

            if bullish_fractals.iloc[i]:
                lower_fractal = df.iloc[i]['low']
                lower_crossed = False

            # Check for bullish structure break (close above swing high)
            if upper_fractal is not None and not upper_crossed:
                if close > upper_fractal:
                    if structure == -1:
                        last_break = 'ChoCH'  # Change of Character
                    else:
                        last_break = 'BOS'  # Break of Structure
                    last_break_price = upper_fractal
                    structure = 1
                    upper_crossed = True
                    bull_weak_high = high  # Initialize weak level

            # Check for bearish structure break (close below swing low)
            if lower_fractal is not None and not lower_crossed:
                if close < lower_fractal:
                    if structure == 1:
                        last_break = 'ChoCH'
                    else:
                        last_break = 'BOS'
                    last_break_price = lower_fractal
                    structure = -1
                    lower_crossed = True
                    bear_weak_low = low  # Initialize weak level

            # Track continuation levels (weak high/low)
            if structure == 1:  # Bull structure
                if bull_weak_high is None or high > bull_weak_high:
                    bull_weak_high = high
            elif structure == -1:  # Bear structure
                if bear_weak_low is None or low < bear_weak_low:
                    bear_weak_low = low

        # Determine final values
        if structure == 1:
            direction = 'BULL'
            strong_level = lower_fractal  # Support - if broken = ChoCH
            weak_level = bull_weak_high  # Continuation target
        elif structure == -1:
            direction = 'BEAR'
            strong_level = upper_fractal  # Resistance - if broken = ChoCH
            weak_level = bear_weak_low  # Continuation target
        else:
            direction = 'NEUTRAL'
            strong_level = None
            weak_level = None

        if self.verbose:
            debug_print(f"Structure: {direction} | Strong: {strong_level} | Weak: {weak_level}")

        return StructureResult(
            direction=direction,
            strong_level=strong_level,
            weak_level=weak_level,
            last_break=last_break,
            last_break_price=last_break_price
        )

    def calculate_multi_timeframe(
        self,
        data: Dict[str, pd.DataFrame]
    ) -> Dict[str, StructureResult]:
        """
        Calculate structure for multiple timeframes.

        Args:
            data: Dict mapping timeframe -> DataFrame

        Returns:
            Dict mapping timeframe -> StructureResult
        """
        results = {}
        for tf, df in data.items():
            results[tf] = self.calculate(df)

        if self.verbose:
            debug_print(f"Calculated structure for {len(results)} timeframes")

        return results

    def get_price_vs_levels(
        self,
        current_price: float,
        result: StructureResult
    ) -> Dict[str, Optional[float]]:
        """
        Calculate price position relative to strong/weak levels.

        Args:
            current_price: Current stock price
            result: StructureResult from calculate()

        Returns:
            Dict with percentage distances and descriptions
        """
        response = {
            'vs_strong_pct': None,
            'vs_strong_diff': None,
            'vs_strong_desc': 'N/A',
            'vs_weak_pct': None,
            'vs_weak_diff': None,
            'vs_weak_desc': 'N/A'
        }

        if current_price <= 0:
            return response

        if result.strong_level is not None:
            diff = current_price - result.strong_level
            pct = (diff / current_price) * 100
            response['vs_strong_pct'] = pct
            response['vs_strong_diff'] = diff
            response['vs_strong_desc'] = f"{pct:+.1f}% {'above' if diff > 0 else 'below'}"

        if result.weak_level is not None:
            diff = current_price - result.weak_level
            pct = (diff / current_price) * 100
            response['vs_weak_pct'] = pct
            response['vs_weak_diff'] = diff
            response['vs_weak_desc'] = f"{pct:+.1f}% {'above' if diff > 0 else 'below'}"

        return response

    def get_confluence(
        self,
        results: Dict[str, StructureResult],
        timeframes: list = None
    ) -> str:
        """
        Determine confluence across timeframes.

        Args:
            results: Dict of StructureResult by timeframe
            timeframes: List of timeframes to check (default: all)

        Returns:
            'ALIGNED', 'MIXED', or 'OPPOSING'
        """
        if timeframes is None:
            timeframes = list(results.keys())

        directions = [results[tf].direction for tf in timeframes if tf in results]

        if not directions:
            return 'NEUTRAL'

        # Filter out NEUTRAL
        active_directions = [d for d in directions if d != 'NEUTRAL']

        if not active_directions:
            return 'NEUTRAL'

        if all(d == 'BULL' for d in active_directions):
            return 'ALIGNED'
        elif all(d == 'BEAR' for d in active_directions):
            return 'ALIGNED'
        elif len(set(active_directions)) == 1:
            return 'ALIGNED'
        else:
            # Check if opposing or just mixed
            has_bull = 'BULL' in active_directions
            has_bear = 'BEAR' in active_directions

            if has_bull and has_bear:
                return 'OPPOSING'
            else:
                return 'MIXED'


# =============================================================================
# STANDALONE TEST
# =============================================================================
if __name__ == '__main__':
    print("=" * 60)
    print("MARKET STRUCTURE CALCULATOR - STANDALONE TEST")
    print("=" * 60)

    # Import polygon fetcher for test data
    from data.polygon_fetcher import PolygonFetcher

    fetcher = PolygonFetcher(verbose=False)
    calculator = MarketStructureCalculator(verbose=True)

    # Test with SPY M15 data
    print("\n[TEST 1] SPY M15 Market Structure...")
    df = fetcher.fetch_bars('SPY', 'M15', bars_needed=100)

    if df is not None:
        result = calculator.calculate(df)
        print(f"  Direction:   {result.direction}")
        print(f"  Strong Level: ${result.strong_level:.2f}" if result.strong_level else "  Strong Level: N/A")
        print(f"  Weak Level:   ${result.weak_level:.2f}" if result.weak_level else "  Weak Level: N/A")
        print(f"  Last Break:   {result.last_break} @ ${result.last_break_price:.2f}" if result.last_break else "  Last Break: N/A")
    else:
        print("  FAILED: Could not fetch data")

    # Test multi-timeframe
    print("\n[TEST 2] TSLA Multi-Timeframe Structure...")
    data = fetcher.fetch_multi_timeframe('TSLA', ['M5', 'M15', 'H1', 'H4'])

    if data:
        results = calculator.calculate_multi_timeframe(data)
        for tf, res in results.items():
            strong = f"${res.strong_level:.2f}" if res.strong_level else "N/A"
            weak = f"${res.weak_level:.2f}" if res.weak_level else "N/A"
            print(f"  {tf}: {res.direction:<8} Strong: {strong:<12} Weak: {weak}")
    else:
        print("  FAILED: Could not fetch data")

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
