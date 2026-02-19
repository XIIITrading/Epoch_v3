"""
================================================================================
EPOCH TRADING SYSTEM - MARKET STRUCTURE (Canonical)
Fractal-Based Detection
XIII Trading LLC
================================================================================

Method:
    1. Detect fractal highs/lows (bar high/low > all bars within N on each side)
    2. Extract swing points from fractals
    3. Compare last two swings: HH+HL = BULL, LH+LL = BEAR, else NEUTRAL

Labels:
    direction: 1 (BULL), -1 (BEAR), 0 (NEUTRAL)
    label: "BULL", "BEAR", "NEUTRAL"

================================================================================
"""

import numpy as np
import pandas as pd
from typing import Tuple, Optional, List, Any

from ..config import CONFIG
from ..types import StructureResult
from .._utils import get_high, get_low


# =============================================================================
# STRUCTURE LABELS
# =============================================================================

STRUCTURE_LABELS = {1: "BULL", -1: "BEAR", 0: "NEUTRAL"}


# =============================================================================
# NUMPY CORE
# =============================================================================

def _detect_fractals_core(
    high: np.ndarray,
    low: np.ndarray,
    length: int,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Detect fractal highs and lows.

    A fractal high is a bar where high > all bars within `length` on each side.

    Returns:
        Tuple of (fractal_highs, fractal_lows) as boolean arrays
    """
    n = len(high)
    frac_highs = np.zeros(n, dtype=bool)
    frac_lows = np.zeros(n, dtype=bool)

    if n < 2 * length + 1:
        return frac_highs, frac_lows

    for i in range(length, n - length):
        # Check fractal high
        is_high = True
        for j in range(1, length + 1):
            if high[i] <= high[i - j] or high[i] <= high[i + j]:
                is_high = False
                break
        frac_highs[i] = is_high

        # Check fractal low
        is_low = True
        for j in range(1, length + 1):
            if low[i] >= low[i - j] or low[i] >= low[i + j]:
                is_low = False
                break
        frac_lows[i] = is_low

    return frac_highs, frac_lows


def _get_structure_from_swings(
    swing_highs: List[float],
    swing_lows: List[float],
) -> Tuple[int, str, bool, bool]:
    """
    Determine structure from swing points.

    Returns:
        (direction, label, higher_highs, higher_lows)
    """
    if len(swing_highs) < 2 or len(swing_lows) < 2:
        return 0, "NEUTRAL", False, False

    higher_highs = swing_highs[-1] > swing_highs[-2]
    higher_lows = swing_lows[-1] > swing_lows[-2]
    lower_highs = swing_highs[-1] < swing_highs[-2]
    lower_lows = swing_lows[-1] < swing_lows[-2]

    if higher_highs and higher_lows:
        return 1, "BULL", True, True
    elif lower_highs and lower_lows:
        return -1, "BEAR", False, False
    else:
        return 0, "NEUTRAL", higher_highs, higher_lows


# =============================================================================
# DATAFRAME WRAPPER
# =============================================================================

def detect_fractals(
    df: pd.DataFrame,
    length: Optional[int] = None,
    high_col: str = "high",
    low_col: str = "low",
) -> Tuple[pd.Series, pd.Series]:
    """
    Detect fractal highs and lows in a DataFrame.

    Returns:
        Tuple of (fractal_highs, fractal_lows) as boolean Series
    """
    length = length or CONFIG.structure.fractal_length
    fh, fl = _detect_fractals_core(
        df[high_col].values.astype(np.float64),
        df[low_col].values.astype(np.float64),
        length,
    )
    return (
        pd.Series(fh, index=df.index, name="fractal_high"),
        pd.Series(fl, index=df.index, name="fractal_low"),
    )


def get_swing_points(
    df: pd.DataFrame,
    length: Optional[int] = None,
) -> Tuple[List[float], List[float]]:
    """Get lists of swing high and swing low prices."""
    frac_highs, frac_lows = detect_fractals(df, length)
    swing_highs = df.loc[frac_highs, "high"].tolist()
    swing_lows = df.loc[frac_lows, "low"].tolist()
    return swing_highs, swing_lows


def get_market_structure(
    df: pd.DataFrame,
    length: Optional[int] = None,
) -> StructureResult:
    """
    Analyze market structure from a DataFrame.

    Returns:
        StructureResult with direction, label, swing info
    """
    swing_highs, swing_lows = get_swing_points(df, length)
    direction, label, hh, hl = _get_structure_from_swings(swing_highs, swing_lows)

    return StructureResult(
        direction=direction,
        label=label,
        last_swing_high=swing_highs[-1] if swing_highs else None,
        last_swing_low=swing_lows[-1] if swing_lows else None,
        higher_highs=hh,
        higher_lows=hl,
    )


# =============================================================================
# BAR-LIST WRAPPER
# =============================================================================

def calculate_structure_from_bars(
    bars: List[Any],
    length: Optional[int] = None,
    up_to_index: Optional[int] = None,
) -> StructureResult:
    """
    Calculate market structure from a list of bars.

    Args:
        bars: List of bar data (dict or object)
        length: Fractal length (bars each side)
        up_to_index: Analyze up to this index (inclusive)

    Returns:
        StructureResult
    """
    length = length or CONFIG.structure.fractal_length

    if not bars:
        return StructureResult(
            direction=0, label="NEUTRAL",
            last_swing_high=None, last_swing_low=None,
            higher_highs=False, higher_lows=False,
        )

    end = (up_to_index + 1) if up_to_index is not None else len(bars)
    end = min(end, len(bars))

    highs = np.array([get_high(bars[i], 0.0) for i in range(end)], dtype=np.float64)
    lows = np.array([get_low(bars[i], 0.0) for i in range(end)], dtype=np.float64)

    frac_highs, frac_lows = _detect_fractals_core(highs, lows, length)

    swing_highs = highs[frac_highs].tolist()
    swing_lows = lows[frac_lows].tolist()

    direction, label, hh, hl = _get_structure_from_swings(swing_highs, swing_lows)

    return StructureResult(
        direction=direction,
        label=label,
        last_swing_high=swing_highs[-1] if swing_highs else None,
        last_swing_low=swing_lows[-1] if swing_lows else None,
        higher_highs=hh,
        higher_lows=hl,
    )


# =============================================================================
# UTILITY HELPERS
# =============================================================================

def get_structure_label(direction: int) -> str:
    """Get structure label from direction integer."""
    return STRUCTURE_LABELS.get(direction, "NEUTRAL")


def is_structure_aligned(structure_direction: int, trade_direction: str) -> bool:
    """Check if structure aligns with trade direction."""
    is_long = trade_direction.upper() in ("LONG", "BULL", "BULLISH")
    return structure_direction == 1 if is_long else structure_direction == -1
