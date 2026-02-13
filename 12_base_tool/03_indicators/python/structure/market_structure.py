"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 03: SHARED INDICATORS
Market Structure Detection
XIII Trading LLC
================================================================================

Structure Detection Methods:

SIMPLE METHOD (EPCH Indicators v1.0 Reference):
- Divides lookback window into first half and second half
- Compares max high and min low of each half
- BULL: Higher high AND higher low
- BEAR: Lower high AND lower low
- NEUT: Mixed signals

FRACTAL METHOD (Advanced):
- Uses swing high/low (fractal) detection
- More robust for longer timeframes
- Returns confidence levels

Works for any timeframe (M5, M15, H1, H4).
Health Factor: Structure aligned with trade direction = healthy

================================================================================
"""

from typing import List, Optional, Any
import sys
from pathlib import Path

# Add parent to path for relative imports within shared library
_LIB_DIR = Path(__file__).parent.parent
if str(_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_LIB_DIR))

from _internal import STRUCTURE_CONFIG, StructureResult, get_high, get_low
from .swing_detection import find_swing_highs, find_swing_lows


# =============================================================================
# SIMPLE STRUCTURE DETECTION (EPCH Indicators v1.0 Reference Algorithm)
# =============================================================================

def detect_structure_simple(
    bars: List[Any],
    up_to_index: Optional[int] = None,
    lookback: Optional[int] = None
) -> str:
    """
    Detect market structure using simple half-bar comparison.

    This is the EPCH Indicators v1.0 reference algorithm.

    Method:
    - Takes last N bars (lookback period)
    - Divides into first half and second half
    - Compares max high and min low of each half
    - BULL: second half has higher high AND higher low
    - BEAR: second half has lower high AND lower low
    - NEUT: Mixed signals

    Args:
        bars: List of bar data
        up_to_index: Calculate up to this index (inclusive)
        lookback: Number of bars for analysis (default 5)

    Returns:
        Structure string: "BULL", "BEAR", or "NEUT"
    """
    lookback_period = lookback or STRUCTURE_CONFIG.get("lookback", 5)

    if not bars:
        return "NEUT"

    end_index = up_to_index if up_to_index is not None else len(bars) - 1
    end_index = min(end_index, len(bars) - 1)

    # Need at least lookback bars
    if end_index < lookback_period - 1:
        return "NEUT"

    # Get the lookback window
    start_index = end_index - lookback_period + 1
    window_bars = bars[start_index:end_index + 1]

    if len(window_bars) < lookback_period:
        return "NEUT"

    # Split into first half and second half
    mid_point = len(window_bars) // 2
    first_half = window_bars[:mid_point]
    second_half = window_bars[mid_point:]

    if not first_half or not second_half:
        return "NEUT"

    # Get highs and lows for each half
    first_half_highs = [get_high(bar, 0.0) for bar in first_half]
    first_half_lows = [get_low(bar, float('inf')) for bar in first_half]
    second_half_highs = [get_high(bar, 0.0) for bar in second_half]
    second_half_lows = [get_low(bar, float('inf')) for bar in second_half]

    first_max_high = max(first_half_highs)
    first_min_low = min(first_half_lows)
    second_max_high = max(second_half_highs)
    second_min_low = min(second_half_lows)

    # Compare halves
    higher_high = second_max_high > first_max_high
    higher_low = second_min_low > first_min_low
    lower_high = second_max_high < first_max_high
    lower_low = second_min_low < first_min_low

    # Determine structure
    if higher_high and higher_low:
        return "BULL"
    elif lower_high and lower_low:
        return "BEAR"
    else:
        return "NEUT"


def detect_h1_structure(
    bars: List[Any],
    up_to_index: Optional[int] = None,
    lookback: Optional[int] = None
) -> str:
    """
    Detect H1 (hourly) market structure.

    Convenience function using the simple method (EPCH reference).

    Args:
        bars: List of H1 bar data
        up_to_index: Calculate up to this index (inclusive)
        lookback: Number of bars for analysis (default 5)

    Returns:
        Structure string: "BULL", "BEAR", or "NEUT"
    """
    return detect_structure_simple(bars, up_to_index, lookback)


def detect_structure(
    bars: List[Any],
    up_to_index: Optional[int] = None,
    fractal_length: Optional[int] = None
) -> StructureResult:
    """
    Detect market structure (BULL/BEAR/NEUTRAL) from bar data.

    Uses swing high/low comparison to determine structure:
    - BULL: Higher high AND higher low
    - BEAR: Lower high AND lower low
    - NEUTRAL: Mixed signals or insufficient data

    Args:
        bars: List of bar data
        up_to_index: Calculate up to this index (inclusive)
        fractal_length: Fractal detection window (default from config)

    Returns:
        StructureResult with structure, swings, and confidence
    """
    length = fractal_length or STRUCTURE_CONFIG["fractal_length"]

    if not bars:
        return StructureResult(
            structure="NEUTRAL",
            swing_high=None,
            swing_low=None,
            prev_swing_high=None,
            prev_swing_low=None,
            confidence="LOW"
        )

    end_index = up_to_index if up_to_index is not None else len(bars) - 1
    end_index = min(end_index, len(bars) - 1)

    # Need enough bars for fractal detection
    min_bars_needed = length * 4
    if end_index < min_bars_needed:
        return StructureResult(
            structure="NEUTRAL",
            swing_high=None,
            swing_low=None,
            prev_swing_high=None,
            prev_swing_low=None,
            confidence="LOW"
        )

    # Find swing points
    swing_highs = find_swing_highs(bars, end_index, length)
    swing_lows = find_swing_lows(bars, end_index, length)

    # Need at least 2 swings of each type to determine structure
    if len(swing_highs) < 2 or len(swing_lows) < 2:
        return StructureResult(
            structure="NEUTRAL",
            swing_high=swing_highs[-1] if swing_highs else None,
            swing_low=swing_lows[-1] if swing_lows else None,
            prev_swing_high=swing_highs[-2] if len(swing_highs) >= 2 else None,
            prev_swing_low=swing_lows[-2] if len(swing_lows) >= 2 else None,
            confidence="LOW"
        )

    # Compare most recent swings
    current_high, prev_high = swing_highs[-1], swing_highs[-2]
    current_low, prev_low = swing_lows[-1], swing_lows[-2]

    higher_high = current_high > prev_high
    higher_low = current_low > prev_low
    lower_high = current_high < prev_high
    lower_low = current_low < prev_low

    # Determine structure and confidence
    if higher_high and higher_low:
        structure, confidence = "BULL", "HIGH"
    elif lower_high and lower_low:
        structure, confidence = "BEAR", "HIGH"
    elif higher_high or higher_low:
        structure, confidence = "BULL", "MEDIUM"
    elif lower_high or lower_low:
        structure, confidence = "BEAR", "MEDIUM"
    else:
        structure, confidence = "NEUTRAL", "LOW"

    return StructureResult(
        structure=structure,
        swing_high=current_high,
        swing_low=current_low,
        prev_swing_high=prev_high,
        prev_swing_low=prev_low,
        confidence=confidence
    )


def is_structure_healthy(structure: str, direction: str) -> bool:
    """
    Check if market structure supports trade direction.

    Args:
        structure: Market structure ('BULL', 'BEAR', 'NEUTRAL', 'NEUT')
        direction: Trade direction ('LONG' or 'SHORT')

    Returns:
        True if structure supports direction
    """
    is_long = direction.upper() == "LONG"
    target = "BULL" if is_long else "BEAR"
    return structure == target


def is_structure_neutral(structure: str) -> bool:
    """
    Check if market structure is neutral.

    Handles both "NEUT" (simple method) and "NEUTRAL" (fractal method).

    Args:
        structure: Market structure string

    Returns:
        True if structure is neutral
    """
    return structure in ["NEUT", "NEUTRAL"]
