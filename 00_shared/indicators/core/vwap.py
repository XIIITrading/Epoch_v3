"""
================================================================================
EPOCH TRADING SYSTEM - VWAP (Canonical)
Volume-Weighted Average Price
XIII Trading LLC
================================================================================

Formula:
    Typical Price = (High + Low + Close) / 3
    VWAP = Cumulative(TP * Volume) / Cumulative(Volume)

================================================================================
"""

import numpy as np
import pandas as pd
from typing import List, Optional, Any

from ..types import VWAPResult
from .._utils import get_high, get_low, get_close, get_volume


# =============================================================================
# NUMPY CORE
# =============================================================================

def _vwap_core(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    volume: np.ndarray,
) -> np.ndarray:
    """
    Calculate cumulative VWAP (no daily reset).

    Returns:
        numpy array of VWAP values
    """
    tp = (high + low + close) / 3.0
    cum_tp_vol = np.cumsum(tp * volume)
    cum_vol = np.cumsum(volume)

    # Avoid division by zero
    safe_cum_vol = np.where(cum_vol == 0, 1.0, cum_vol)
    return cum_tp_vol / safe_cum_vol


# =============================================================================
# DATAFRAME WRAPPER
# =============================================================================

def vwap_df(
    df: pd.DataFrame,
    high_col: str = "high",
    low_col: str = "low",
    close_col: str = "close",
    volume_col: str = "volume",
    reset_daily: bool = True,
) -> pd.Series:
    """
    Calculate VWAP for a DataFrame.

    Args:
        df: DataFrame with OHLCV data
        reset_daily: If True and 'timestamp' or 'bar_date' column exists,
                     reset VWAP at start of each trading day

    Returns:
        Series of VWAP values
    """
    tp = (df[high_col] + df[low_col] + df[close_col]) / 3.0

    if reset_daily:
        # Try to find a date grouping column
        date_col = None
        if "bar_date" in df.columns:
            date_col = "bar_date"
        elif "timestamp" in df.columns:
            date_col = "timestamp"

        if date_col is not None:
            df_work = df.copy()
            if date_col == "timestamp":
                df_work["_date"] = pd.to_datetime(df_work[date_col]).dt.date
            else:
                df_work["_date"] = df_work[date_col]
            df_work["_tp_vol"] = tp * df_work[volume_col]
            df_work["_cum_tp_vol"] = df_work.groupby("_date")["_tp_vol"].cumsum()
            df_work["_cum_vol"] = df_work.groupby("_date")[volume_col].cumsum()
            vwap_values = df_work["_cum_tp_vol"] / df_work["_cum_vol"].replace(0, np.nan)
            return vwap_values.rename("vwap")

    # Simple cumulative VWAP (no reset)
    return pd.Series(
        _vwap_core(
            df[high_col].values.astype(np.float64),
            df[low_col].values.astype(np.float64),
            df[close_col].values.astype(np.float64),
            df[volume_col].values.astype(np.float64),
        ),
        index=df.index,
        name="vwap",
    )


# =============================================================================
# BAR-LIST WRAPPER
# =============================================================================

def calculate_vwap(
    bars: List[Any],
    up_to_index: Optional[int] = None,
) -> Optional[float]:
    """
    Calculate VWAP from a list of bars (no daily reset).

    Args:
        bars: List of bar data
        up_to_index: Calculate up to this index (inclusive)

    Returns:
        VWAP value or None
    """
    if not bars:
        return None

    end_index = up_to_index if up_to_index is not None else len(bars) - 1
    end_index = min(end_index, len(bars) - 1)

    cumulative_tp_vol = 0.0
    cumulative_vol = 0

    for i in range(end_index + 1):
        bar = bars[i]
        high = get_high(bar)
        low = get_low(bar)
        close = get_close(bar)
        volume = get_volume(bar)

        if high is None or low is None or close is None:
            continue

        tp = (high + low + close) / 3.0
        cumulative_tp_vol += tp * volume
        cumulative_vol += volume

    if cumulative_vol == 0:
        return None

    return cumulative_tp_vol / cumulative_vol


def calculate_vwap_metrics(
    bars: List[Any],
    current_price: float,
    up_to_index: Optional[int] = None,
) -> VWAPResult:
    """
    Calculate VWAP with price relationship metrics.

    Returns:
        VWAPResult with vwap, price_diff, price_pct, side
    """
    vwap_val = calculate_vwap(bars, up_to_index)

    if vwap_val is None or vwap_val == 0:
        return VWAPResult(vwap=None, price_diff=None, price_pct=None, side=None)

    diff = current_price - vwap_val
    pct = (diff / vwap_val) * 100

    if abs(diff) < 0.01:
        side = "AT"
    elif diff > 0:
        side = "ABOVE"
    else:
        side = "BELOW"

    return VWAPResult(vwap=vwap_val, price_diff=diff, price_pct=pct, side=side)
