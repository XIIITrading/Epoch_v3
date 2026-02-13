"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 03: SHARED INDICATORS
CVD (Cumulative Volume Delta) Slope Calculation
XIII Trading LLC
================================================================================

Process:
1. Calculate bar deltas (bar_position method)
2. Cumulative sum for CVD series
3. Linear regression slope on last N bars
4. Normalize by CVD range
5. Classify: Rising (>0.1), Falling (<-0.1), Flat

Health Factor: LONG: Rising, SHORT: Falling

================================================================================
"""

from typing import List, Optional, Any
import sys
from pathlib import Path

# Add parent to path for relative imports within shared library
_LIB_DIR = Path(__file__).parent.parent
if str(_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_LIB_DIR))

from _internal import CVD_CONFIG, CVDResult, calculate_linear_slope
from .volume_delta import calculate_bar_delta_from_bar


def calculate_cvd_slope(
    bars: List[Any],
    up_to_index: Optional[int] = None,
    window: Optional[int] = None
) -> CVDResult:
    """
    Calculate CVD (Cumulative Volume Delta) slope.

    The slope is normalized by the CVD range to make it comparable
    across different volume scales.

    Args:
        bars: List of bar data
        up_to_index: Calculate up to this index (inclusive)
        window: Number of bars for slope calculation

    Returns:
        CVDResult with slope, trend, cvd_values, window_size
    """
    cvd_window = window or CVD_CONFIG["window"]

    if not bars:
        return CVDResult(slope=0.0, trend="Flat", cvd_values=[], window_size=0)

    end_index = up_to_index if up_to_index is not None else len(bars) - 1
    end_index = min(end_index, len(bars) - 1)

    if end_index < cvd_window:
        return CVDResult(slope=0.0, trend="Flat", cvd_values=[], window_size=0)

    # Calculate bar deltas
    bar_deltas = []
    for i in range(end_index + 1):
        result = calculate_bar_delta_from_bar(bars[i])
        bar_deltas.append(result.bar_delta)

    # Calculate cumulative volume delta
    cvd_series = []
    cumsum = 0.0
    for delta in bar_deltas:
        cumsum += delta
        cvd_series.append(cumsum)

    # Get recent CVD values for slope calculation
    recent_cvd = cvd_series[-cvd_window:]

    if len(recent_cvd) < 3:
        return CVDResult(
            slope=0.0,
            trend="Flat",
            cvd_values=recent_cvd,
            window_size=len(recent_cvd)
        )

    # Calculate linear regression slope
    slope = calculate_linear_slope(recent_cvd)

    # Normalize by CVD range
    cvd_range = max(recent_cvd) - min(recent_cvd)

    if cvd_range == 0:
        normalized_slope = 0.0
    else:
        normalized_slope = slope / cvd_range * len(recent_cvd)

    # Clamp to reasonable range
    normalized_slope = max(-2.0, min(2.0, normalized_slope))

    trend = classify_cvd_trend(normalized_slope)

    return CVDResult(
        slope=normalized_slope,
        trend=trend,
        cvd_values=recent_cvd,
        window_size=len(recent_cvd)
    )


def classify_cvd_trend(
    slope: float,
    rising_threshold: Optional[float] = None,
    falling_threshold: Optional[float] = None
) -> str:
    """
    Classify CVD slope into trend categories.

    Args:
        slope: Normalized CVD slope
        rising_threshold: Threshold for "Rising" classification
        falling_threshold: Threshold for "Falling" classification

    Returns:
        Classification: "Rising", "Falling", or "Flat"
    """
    rising = rising_threshold if rising_threshold is not None else CVD_CONFIG["rising_threshold"]
    falling = falling_threshold if falling_threshold is not None else CVD_CONFIG["falling_threshold"]

    if slope > rising:
        return "Rising"
    elif slope < falling:
        return "Falling"
    return "Flat"


def is_cvd_healthy(
    slope: float,
    direction: str,
    threshold: Optional[float] = None
) -> bool:
    """
    Check if CVD slope supports trade direction.

    Args:
        slope: Normalized CVD slope
        direction: Trade direction ('LONG' or 'SHORT')
        threshold: Threshold for healthy classification

    Returns:
        True if CVD slope supports direction
    """
    thresh = threshold if threshold is not None else CVD_CONFIG["rising_threshold"]
    is_long = direction.upper() == "LONG"
    return slope > thresh if is_long else slope < -thresh
