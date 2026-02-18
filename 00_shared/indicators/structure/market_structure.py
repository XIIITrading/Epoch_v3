"""
Epoch Trading System - Market Structure Detection
==================================================

Fractal-based market structure analysis.

Usage:
    from shared.indicators.structure import detect_fractals, get_market_structure
"""

import pandas as pd
import numpy as np
from typing import Tuple, Optional, List, NamedTuple


# =============================================================================
# CONFIGURATION
# =============================================================================
STRUCTURE_CONFIG = {
    "fractal_length": 5,  # Bars each side for fractal detection
}

STRUCTURE_LABELS = {
    1: "B+",
    -1: "B-",
    0: "N",
}


# =============================================================================
# RESULT TYPES
# =============================================================================
class StructureResult(NamedTuple):
    """Result of structure analysis."""
    direction: int  # 1 = B+, -1 = B-, 0 = N
    label: str
    last_swing_high: Optional[float]
    last_swing_low: Optional[float]
    higher_highs: bool
    higher_lows: bool


# =============================================================================
# CORE FUNCTIONS
# =============================================================================
def detect_fractals(
    df: pd.DataFrame,
    length: int = 5,
    high_col: str = "high",
    low_col: str = "low",
) -> Tuple[pd.Series, pd.Series]:
    """
    Detect fractal highs and lows (swing points).

    A fractal high is a bar where the high is higher than
    the `length` bars on each side.

    Args:
        df: DataFrame with OHLCV data
        length: Bars to check on each side
        high_col: Column name for high prices
        low_col: Column name for low prices

    Returns:
        Tuple of (fractal_highs, fractal_lows) as boolean Series
    """
    high = df[high_col]
    low = df[low_col]

    # Initialize
    fractal_highs = pd.Series(False, index=df.index)
    fractal_lows = pd.Series(False, index=df.index)

    # Need at least 2*length + 1 bars
    if len(df) < 2 * length + 1:
        return fractal_highs, fractal_lows

    # Check each bar (excluding edges)
    for i in range(length, len(df) - length):
        # Check for fractal high
        is_high = True
        for j in range(1, length + 1):
            if high.iloc[i] <= high.iloc[i - j] or high.iloc[i] <= high.iloc[i + j]:
                is_high = False
                break
        fractal_highs.iloc[i] = is_high

        # Check for fractal low
        is_low = True
        for j in range(1, length + 1):
            if low.iloc[i] >= low.iloc[i - j] or low.iloc[i] >= low.iloc[i + j]:
                is_low = False
                break
        fractal_lows.iloc[i] = is_low

    return fractal_highs, fractal_lows


def get_swing_points(
    df: pd.DataFrame,
    length: int = 5,
) -> Tuple[List[float], List[float]]:
    """
    Get list of swing high and low prices.

    Args:
        df: DataFrame with OHLCV data
        length: Fractal length

    Returns:
        Tuple of (swing_highs, swing_lows) as lists of prices
    """
    fractal_highs, fractal_lows = detect_fractals(df, length)

    swing_highs = df.loc[fractal_highs, "high"].tolist()
    swing_lows = df.loc[fractal_lows, "low"].tolist()

    return swing_highs, swing_lows


def get_market_structure(
    df: pd.DataFrame,
    length: int = 5,
) -> StructureResult:
    """
    Analyze market structure from swing points.

    Returns BULL if making higher highs and higher lows.
    Returns BEAR if making lower highs and lower lows.
    Returns NEUTRAL otherwise.

    Args:
        df: DataFrame with OHLCV data
        length: Fractal length

    Returns:
        StructureResult with direction and swing info
    """
    swing_highs, swing_lows = get_swing_points(df, length)

    # Need at least 2 of each
    if len(swing_highs) < 2 or len(swing_lows) < 2:
        return StructureResult(
            direction=0,
            label="N",
            last_swing_high=swing_highs[-1] if swing_highs else None,
            last_swing_low=swing_lows[-1] if swing_lows else None,
            higher_highs=False,
            higher_lows=False,
        )

    # Check last two swing points
    higher_highs = swing_highs[-1] > swing_highs[-2]
    higher_lows = swing_lows[-1] > swing_lows[-2]
    lower_highs = swing_highs[-1] < swing_highs[-2]
    lower_lows = swing_lows[-1] < swing_lows[-2]

    # Determine structure
    if higher_highs and higher_lows:
        direction = 1
        label = "B+"
    elif lower_highs and lower_lows:
        direction = -1
        label = "B-"
    else:
        direction = 0
        label = "N"

    return StructureResult(
        direction=direction,
        label=label,
        last_swing_high=swing_highs[-1],
        last_swing_low=swing_lows[-1],
        higher_highs=higher_highs,
        higher_lows=higher_lows,
    )


def get_structure_label(direction: int) -> str:
    """
    Get structure label from direction.

    Args:
        direction: 1 for bull, -1 for bear, 0 for neutral

    Returns:
        "B+", "B-", or "N"
    """
    return STRUCTURE_LABELS.get(direction, "N")


def is_structure_aligned(
    structure_direction: int,
    trade_direction: str,
) -> bool:
    """
    Check if structure aligns with trade direction.

    Args:
        structure_direction: 1 for bull, -1 for bear
        trade_direction: "LONG" or "SHORT"

    Returns:
        True if structure supports trade
    """
    is_long = trade_direction.upper() in ("LONG", "BULL", "BULLISH")

    if is_long:
        return structure_direction == 1
    else:
        return structure_direction == -1
