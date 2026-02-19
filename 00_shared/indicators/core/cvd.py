"""
================================================================================
EPOCH TRADING SYSTEM - CVD SLOPE (Canonical)
Linear Regression Method, Normalized, Clamped [-2, 2]
XIII Trading LLC
================================================================================

Process:
1. Calculate bar deltas (bar position method)
2. Cumulative sum for CVD series
3. Linear regression slope on last N bars
4. Normalize by CVD range x window
5. Clamp to [-2, 2]
6. Classify: Rising (>0.1), Falling (<-0.1), Flat

================================================================================
"""

import numpy as np
import pandas as pd
from typing import List, Optional, Any

from ..config import CONFIG
from ..types import CVDResult
from .._utils import linear_regression_slope
from .volume_delta import _bar_delta_core_with_open, calculate_bar_delta_from_bar


# =============================================================================
# NUMPY CORE
# =============================================================================

def _cvd_series_core(
    open_price: np.ndarray,
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    volume: np.ndarray,
) -> np.ndarray:
    """Calculate cumulative volume delta series."""
    deltas = _bar_delta_core_with_open(open_price, high, low, close, volume)
    return np.cumsum(deltas)


def _cvd_slope_core(cvd_series: np.ndarray, window: int) -> np.ndarray:
    """
    Calculate normalized CVD slope for each bar using linear regression.

    Returns:
        numpy array of normalized slope values (NaN where insufficient data)
    """
    cfg = CONFIG.cvd
    n = len(cvd_series)
    result = np.full(n, np.nan)

    for i in range(window - 1, n):
        recent = cvd_series[i - window + 1:i + 1]

        if len(recent) < 3:
            result[i] = 0.0
            continue

        slope = linear_regression_slope(recent)
        cvd_range = recent.max() - recent.min()

        if cvd_range == 0:
            result[i] = 0.0
        else:
            normalized = slope / cvd_range * len(recent)
            result[i] = float(np.clip(normalized, cfg.clamp_min, cfg.clamp_max))

    return result


# =============================================================================
# DATAFRAME WRAPPER
# =============================================================================

def cvd_df(
    df: pd.DataFrame,
    open_col: str = "open",
    high_col: str = "high",
    low_col: str = "low",
    close_col: str = "close",
    volume_col: str = "volume",
) -> pd.Series:
    """Calculate CVD series for a DataFrame."""
    cvd = _cvd_series_core(
        df[open_col].values.astype(np.float64),
        df[high_col].values.astype(np.float64),
        df[low_col].values.astype(np.float64),
        df[close_col].values.astype(np.float64),
        df[volume_col].values.astype(np.float64),
    )
    return pd.Series(cvd, index=df.index, name="cvd")


def cvd_slope_df(
    df: pd.DataFrame,
    window: Optional[int] = None,
    open_col: str = "open",
    high_col: str = "high",
    low_col: str = "low",
    close_col: str = "close",
    volume_col: str = "volume",
) -> pd.Series:
    """Calculate normalized CVD slope for a DataFrame (clamped [-2, 2])."""
    window = window or CONFIG.cvd.window
    cvd = _cvd_series_core(
        df[open_col].values.astype(np.float64),
        df[high_col].values.astype(np.float64),
        df[low_col].values.astype(np.float64),
        df[close_col].values.astype(np.float64),
        df[volume_col].values.astype(np.float64),
    )
    return pd.Series(
        _cvd_slope_core(cvd, window),
        index=df.index,
        name="cvd_slope",
    )


# =============================================================================
# BAR-LIST WRAPPER
# =============================================================================

def calculate_cvd_slope(
    bars: List[Any],
    up_to_index: Optional[int] = None,
    window: Optional[int] = None,
) -> CVDResult:
    """
    Calculate CVD slope from a list of bars.

    Args:
        bars: List of bar data
        up_to_index: Calculate up to this index (inclusive)
        window: Number of bars for slope calculation

    Returns:
        CVDResult with slope, trend, cvd_values, window_size
    """
    cvd_window = window or CONFIG.cvd.window

    if not bars:
        return CVDResult(slope=0.0, trend="Flat", cvd_values=[], window_size=0)

    end_index = up_to_index if up_to_index is not None else len(bars) - 1
    end_index = min(end_index, len(bars) - 1)

    if end_index < cvd_window:
        return CVDResult(slope=0.0, trend="Flat", cvd_values=[], window_size=0)

    # Build CVD series from bar deltas
    bar_deltas = []
    for i in range(end_index + 1):
        result = calculate_bar_delta_from_bar(bars[i])
        bar_deltas.append(result.bar_delta)

    cvd_series = []
    cumsum = 0.0
    for delta in bar_deltas:
        cumsum += delta
        cvd_series.append(cumsum)

    recent_cvd = np.array(cvd_series[-cvd_window:])

    if len(recent_cvd) < 3:
        return CVDResult(slope=0.0, trend="Flat", cvd_values=recent_cvd.tolist(), window_size=len(recent_cvd))

    slope = linear_regression_slope(recent_cvd)
    cvd_range = recent_cvd.max() - recent_cvd.min()

    if cvd_range == 0:
        normalized_slope = 0.0
    else:
        normalized_slope = slope / cvd_range * len(recent_cvd)

    cfg = CONFIG.cvd
    normalized_slope = float(np.clip(normalized_slope, cfg.clamp_min, cfg.clamp_max))
    trend = classify_cvd_trend(normalized_slope)

    return CVDResult(
        slope=normalized_slope, trend=trend,
        cvd_values=recent_cvd.tolist(), window_size=len(recent_cvd),
    )


# =============================================================================
# CLASSIFICATION HELPERS
# =============================================================================

def classify_cvd_trend(slope: float) -> str:
    """Classify CVD slope into trend categories."""
    if slope > CONFIG.cvd.rising_threshold:
        return "Rising"
    elif slope < CONFIG.cvd.falling_threshold:
        return "Falling"
    return "Flat"
