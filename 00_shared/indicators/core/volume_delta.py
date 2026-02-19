"""
================================================================================
EPOCH TRADING SYSTEM - VOLUME DELTA (Canonical)
Bar Position Method
XIII Trading LLC
================================================================================

Formula:
    bar_position = (close - low) / (high - low)
    delta_multiplier = (2 * bar_position) - 1
    bar_delta = volume * delta_multiplier

Close at high = +1.0 multiplier (all buying)
Close at low  = -1.0 multiplier (all selling)

================================================================================
"""

import numpy as np
import pandas as pd
from typing import List, Optional, Any, Union

from ..config import CONFIG
from ..types import VolumeDeltaResult, RollingDeltaResult
from .._utils import get_open, get_high, get_low, get_close, get_volume, bars_to_arrays


# =============================================================================
# NUMPY CORE (operates on raw arrays)
# =============================================================================

def _bar_delta_core(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    volume: np.ndarray,
) -> np.ndarray:
    """
    Calculate per-bar volume delta using the bar position method.

    Args:
        high, low, close, volume: numpy arrays of equal length

    Returns:
        numpy array of bar delta values
    """
    bar_range = high - low
    # Handle zero-range (doji) bars: use sign of close vs open midpoint
    # For arrays without open, default to positive for zero-range
    safe_range = np.where(bar_range == 0, 1.0, bar_range)

    position = np.where(
        bar_range == 0,
        0.5,  # neutral for doji when no open available
        (close - low) / safe_range,
    )
    multiplier = 2.0 * position - 1.0
    return volume * multiplier


def _bar_delta_core_with_open(
    open_price: np.ndarray,
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    volume: np.ndarray,
) -> np.ndarray:
    """
    Calculate per-bar volume delta with doji handling via open price.

    Args:
        open_price, high, low, close, volume: numpy arrays of equal length

    Returns:
        numpy array of bar delta values
    """
    bar_range = high - low
    safe_range = np.where(bar_range == 0, 1.0, bar_range)

    position = np.where(
        bar_range == 0,
        np.where(close >= open_price, 1.0, 0.0),
        (close - low) / safe_range,
    )
    multiplier = 2.0 * position - 1.0
    return volume * multiplier


def _rolling_delta_core(bar_deltas: np.ndarray, period: int) -> np.ndarray:
    """
    Calculate rolling sum of bar deltas.

    Args:
        bar_deltas: numpy array of per-bar delta values
        period: rolling window size

    Returns:
        numpy array of rolling delta sums (NaN for insufficient data)
    """
    n = len(bar_deltas)
    result = np.full(n, np.nan)
    cumsum = np.cumsum(bar_deltas)

    for i in range(n):
        if i < period - 1:
            result[i] = cumsum[i]
        else:
            result[i] = cumsum[i] - (cumsum[i - period] if i >= period else 0.0)

    return result


# =============================================================================
# DATAFRAME WRAPPER
# =============================================================================

def volume_delta_df(
    df: pd.DataFrame,
    open_col: str = "open",
    high_col: str = "high",
    low_col: str = "low",
    close_col: str = "close",
    volume_col: str = "volume",
) -> pd.Series:
    """
    Calculate per-bar volume delta for a DataFrame.

    Args:
        df: DataFrame with OHLCV data
        open_col, high_col, low_col, close_col, volume_col: column names

    Returns:
        Series of bar delta values
    """
    return pd.Series(
        _bar_delta_core_with_open(
            df[open_col].values.astype(np.float64),
            df[high_col].values.astype(np.float64),
            df[low_col].values.astype(np.float64),
            df[close_col].values.astype(np.float64),
            df[volume_col].values.astype(np.float64),
        ),
        index=df.index,
        name="volume_delta",
    )


def rolling_delta_df(
    df: pd.DataFrame,
    period: Optional[int] = None,
    open_col: str = "open",
    high_col: str = "high",
    low_col: str = "low",
    close_col: str = "close",
    volume_col: str = "volume",
) -> pd.Series:
    """
    Calculate rolling volume delta sum for a DataFrame.

    Args:
        df: DataFrame with OHLCV data
        period: rolling window size (default from config)

    Returns:
        Series of rolling delta values
    """
    period = period or CONFIG.volume_delta.rolling_period
    deltas = _bar_delta_core_with_open(
        df[open_col].values.astype(np.float64),
        df[high_col].values.astype(np.float64),
        df[low_col].values.astype(np.float64),
        df[close_col].values.astype(np.float64),
        df[volume_col].values.astype(np.float64),
    )
    return pd.Series(
        _rolling_delta_core(deltas, period),
        index=df.index,
        name="volume_delta_roll",
    )


def cumulative_delta_df(
    df: pd.DataFrame,
    open_col: str = "open",
    high_col: str = "high",
    low_col: str = "low",
    close_col: str = "close",
    volume_col: str = "volume",
) -> pd.Series:
    """
    Calculate cumulative volume delta for a DataFrame (no daily reset).

    Args:
        df: DataFrame with OHLCV data

    Returns:
        Series of cumulative delta values
    """
    deltas = _bar_delta_core_with_open(
        df[open_col].values.astype(np.float64),
        df[high_col].values.astype(np.float64),
        df[low_col].values.astype(np.float64),
        df[close_col].values.astype(np.float64),
        df[volume_col].values.astype(np.float64),
    )
    return pd.Series(np.cumsum(deltas), index=df.index, name="cvd")


# =============================================================================
# BAR-LIST WRAPPER
# =============================================================================

def calculate_bar_delta(
    open_price: float,
    high: float,
    low: float,
    close: float,
    volume: int,
) -> VolumeDeltaResult:
    """
    Calculate volume delta for a single bar.

    Args:
        open_price, high, low, close: bar OHLC prices
        volume: bar volume

    Returns:
        VolumeDeltaResult with bar_delta, bar_position, delta_multiplier
    """
    bar_range = high - low

    if bar_range == 0:
        if close >= open_price:
            return VolumeDeltaResult(bar_delta=float(volume), bar_position=1.0, delta_multiplier=1.0)
        else:
            return VolumeDeltaResult(bar_delta=-float(volume), bar_position=0.0, delta_multiplier=-1.0)

    bar_position = (close - low) / bar_range
    delta_multiplier = (2.0 * bar_position) - 1.0
    bar_delta = volume * delta_multiplier

    return VolumeDeltaResult(bar_delta=bar_delta, bar_position=bar_position, delta_multiplier=delta_multiplier)


def calculate_bar_delta_from_bar(bar: Any) -> VolumeDeltaResult:
    """Calculate bar delta from a bar dict or object."""
    return calculate_bar_delta(
        get_open(bar, 0.0), get_high(bar, 0.0),
        get_low(bar, 0.0), get_close(bar, 0.0),
        get_volume(bar, 0),
    )


def calculate_rolling_delta(
    bars: List[Any],
    up_to_index: Optional[int] = None,
    rolling_period: Optional[int] = None,
) -> RollingDeltaResult:
    """
    Calculate rolling volume delta over N bars.

    Args:
        bars: List of bar data
        up_to_index: Calculate up to this index (inclusive)
        rolling_period: Number of bars for rolling window

    Returns:
        RollingDeltaResult with rolling_delta, signal, bar_count
    """
    period = rolling_period or CONFIG.volume_delta.rolling_period

    if not bars:
        return RollingDeltaResult(rolling_delta=0.0, signal="Neutral", bar_count=0)

    end_index = up_to_index if up_to_index is not None else len(bars) - 1
    end_index = min(end_index, len(bars) - 1)
    start_idx = max(0, end_index - period + 1)
    bar_count = end_index - start_idx + 1

    rolling_delta = 0.0
    for i in range(start_idx, end_index + 1):
        result = calculate_bar_delta_from_bar(bars[i])
        rolling_delta += result.bar_delta

    if rolling_delta > 0:
        signal = "Bullish"
    elif rolling_delta < 0:
        signal = "Bearish"
    else:
        signal = "Neutral"

    return RollingDeltaResult(rolling_delta=rolling_delta, signal=signal, bar_count=bar_count)
