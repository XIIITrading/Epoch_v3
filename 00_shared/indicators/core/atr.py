"""
================================================================================
EPOCH TRADING SYSTEM - ATR (Canonical)
True Range Method, SMA Smoothing
XIII Trading LLC
================================================================================

Formula:
    True Range = max(high - low, |high - prev_close|, |low - prev_close|)
    ATR = SMA(True Range, period)

Standard period: 14

================================================================================
"""

import numpy as np
import pandas as pd
from typing import List, Optional, Any

from ..config import CONFIG
from ..types import ATRResult
from .._utils import get_high, get_low, get_close


# =============================================================================
# NUMPY CORE
# =============================================================================

def _true_range_core(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
) -> np.ndarray:
    """
    Calculate True Range for each bar.

    First element uses high - low (no previous close available).
    """
    n = len(high)
    tr = np.empty(n, dtype=np.float64)
    tr[0] = high[0] - low[0]

    for i in range(1, n):
        tr[i] = max(
            high[i] - low[i],
            abs(high[i] - close[i - 1]),
            abs(low[i] - close[i - 1]),
        )

    return tr


def _atr_core(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    period: int,
) -> np.ndarray:
    """
    Calculate ATR as SMA of True Range.

    Returns:
        numpy array of ATR values (NaN where insufficient data)
    """
    tr = _true_range_core(high, low, close)
    n = len(tr)
    result = np.full(n, np.nan)

    for i in range(period - 1, n):
        result[i] = tr[i - period + 1:i + 1].mean()

    return result


# =============================================================================
# SCALAR HELPER
# =============================================================================

def calculate_true_range(high: float, low: float, prev_close: float) -> float:
    """Calculate True Range for a single bar."""
    return max(
        high - low,
        abs(high - prev_close),
        abs(low - prev_close),
    )


# =============================================================================
# DATAFRAME WRAPPER
# =============================================================================

def atr_df(
    df: pd.DataFrame,
    period: Optional[int] = None,
    high_col: str = "high",
    low_col: str = "low",
    close_col: str = "close",
) -> pd.Series:
    """Calculate ATR for a DataFrame."""
    period = period or CONFIG.atr.period
    return pd.Series(
        _atr_core(
            df[high_col].values.astype(np.float64),
            df[low_col].values.astype(np.float64),
            df[close_col].values.astype(np.float64),
            period,
        ),
        index=df.index,
        name="atr",
    )


def atr_pct_df(
    df: pd.DataFrame,
    period: Optional[int] = None,
    high_col: str = "high",
    low_col: str = "low",
    close_col: str = "close",
) -> pd.Series:
    """Calculate ATR as percentage of close price."""
    atr_values = atr_df(df, period, high_col, low_col, close_col)
    return (atr_values / df[close_col]) * 100


# =============================================================================
# BAR-LIST WRAPPER
# =============================================================================

def calculate_atr(
    bars: List[Any],
    period: Optional[int] = None,
    up_to_index: Optional[int] = None,
) -> ATRResult:
    """
    Calculate ATR from a list of bar dicts/objects.

    Args:
        bars: List of bar data
        period: ATR period (default from config)
        up_to_index: Calculate up to this index (inclusive)

    Returns:
        ATRResult with atr value, last true_range, and period
    """
    period = period or CONFIG.atr.period

    if not bars or len(bars) < 2:
        return ATRResult(atr=None, true_range=None, period=period)

    end_index = up_to_index if up_to_index is not None else len(bars) - 1
    end_index = min(end_index, len(bars) - 1)

    if end_index < 1:
        return ATRResult(atr=None, true_range=None, period=period)

    true_ranges = []
    for i in range(1, end_index + 1):
        high = get_high(bars[i], 0.0)
        low = get_low(bars[i], 0.0)
        prev_close = get_close(bars[i - 1], 0.0)
        tr = calculate_true_range(high, low, prev_close)
        true_ranges.append(tr)

    if len(true_ranges) < period:
        return ATRResult(
            atr=None,
            true_range=true_ranges[-1] if true_ranges else None,
            period=period,
        )

    atr_value = sum(true_ranges[-period:]) / period
    return ATRResult(atr=atr_value, true_range=true_ranges[-1], period=period)


def calculate_atr_series(
    highs: List[float],
    lows: List[float],
    closes: List[float],
    period: Optional[int] = None,
) -> List[Optional[float]]:
    """Calculate ATR for a series of price data. Returns list aligned with input."""
    period = period or CONFIG.atr.period
    n = len(highs)

    if n < 2:
        return [None] * n

    atr_arr = _atr_core(
        np.array(highs, dtype=np.float64),
        np.array(lows, dtype=np.float64),
        np.array(closes, dtype=np.float64),
        period,
    )
    return [None if np.isnan(v) else float(v) for v in atr_arr]


# =============================================================================
# UTILITY HELPERS
# =============================================================================

def get_atr_multiple(price_distance: float, atr_value: float) -> float:
    """Calculate how many ATRs a price distance represents."""
    if atr_value == 0:
        return 0.0
    return abs(price_distance) / atr_value
