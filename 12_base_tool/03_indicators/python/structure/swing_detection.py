"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 03: SHARED INDICATORS
Swing High/Low Detection (Fractal Method)
XIII Trading LLC
================================================================================

Fractal-based swing detection:
- Swing High: Bar with highest high among N bars on each side
- Swing Low: Bar with lowest low among N bars on each side

Default fractal length: 5 (2 bars each side)

================================================================================
"""

from typing import List, Optional, Any
import sys
from pathlib import Path

# Add parent to path for relative imports within shared library
_LIB_DIR = Path(__file__).parent.parent
if str(_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_LIB_DIR))

from _internal import STRUCTURE_CONFIG, get_high, get_low


def find_swing_highs(
    bars: List[Any],
    end_index: int,
    fractal_length: Optional[int] = None
) -> List[float]:
    """
    Find all swing highs up to end_index.

    A swing high is a bar where the high is greater than the highs
    of all bars within fractal_length/2 bars on each side.

    Args:
        bars: List of bar data
        end_index: Calculate up to this index
        fractal_length: Total fractal window (default from config)

    Returns:
        List of swing high prices in chronological order
    """
    length = fractal_length or STRUCTURE_CONFIG["fractal_length"]
    p = length // 2  # Bars on each side

    swing_highs = []
    check_end = end_index - p

    for i in range(p, check_end + 1):
        high = get_high(bars[i])
        if high is None:
            continue

        is_swing = True

        # Check left side
        for j in range(i - p, i):
            left_high = get_high(bars[j])
            if left_high is not None and left_high >= high:
                is_swing = False
                break

        if not is_swing:
            continue

        # Check right side
        for j in range(i + 1, min(i + p + 1, end_index + 1)):
            right_high = get_high(bars[j])
            if right_high is not None and right_high >= high:
                is_swing = False
                break

        if is_swing:
            swing_highs.append(high)

    return swing_highs


def find_swing_lows(
    bars: List[Any],
    end_index: int,
    fractal_length: Optional[int] = None
) -> List[float]:
    """
    Find all swing lows up to end_index.

    A swing low is a bar where the low is less than the lows
    of all bars within fractal_length/2 bars on each side.

    Args:
        bars: List of bar data
        end_index: Calculate up to this index
        fractal_length: Total fractal window (default from config)

    Returns:
        List of swing low prices in chronological order
    """
    length = fractal_length or STRUCTURE_CONFIG["fractal_length"]
    p = length // 2  # Bars on each side

    swing_lows = []
    check_end = end_index - p

    for i in range(p, check_end + 1):
        low = get_low(bars[i])
        if low is None:
            continue

        is_swing = True

        # Check left side
        for j in range(i - p, i):
            left_low = get_low(bars[j])
            if left_low is not None and left_low <= low:
                is_swing = False
                break

        if not is_swing:
            continue

        # Check right side
        for j in range(i + 1, min(i + p + 1, end_index + 1)):
            right_low = get_low(bars[j])
            if right_low is not None and right_low <= low:
                is_swing = False
                break

        if is_swing:
            swing_lows.append(low)

    return swing_lows
