"""
Epoch Trading System - Volume Delta Indicator
==============================================

Volume delta and cumulative delta calculations.

Usage:
    from shared.indicators.core import volume_delta, cumulative_delta

    # Calculate volume delta
    df['delta'] = volume_delta(df)
"""

import pandas as pd
import numpy as np
from typing import Union, Optional


def volume_delta(
    df: pd.DataFrame,
    open_col: str = "open",
    close_col: str = "close",
    volume_col: str = "volume",
) -> pd.Series:
    """
    Calculate volume delta (buy vs sell pressure).

    Uses candle direction to estimate:
    - Up candle (close > open): Volume is buying
    - Down candle (close < open): Volume is selling

    Args:
        df: DataFrame with OHLCV data
        open_col: Column name for open prices
        close_col: Column name for close prices
        volume_col: Column name for volume

    Returns:
        Series of delta values (positive = buying, negative = selling)
    """
    direction = np.sign(df[close_col] - df[open_col])
    return direction * df[volume_col]


def cumulative_delta(
    df: pd.DataFrame,
    reset_daily: bool = True,
) -> pd.Series:
    """
    Calculate cumulative volume delta.

    Args:
        df: DataFrame with OHLCV data
        reset_daily: Reset cumulative delta at start of each day

    Returns:
        Series of cumulative delta values
    """
    delta = volume_delta(df)

    if reset_daily and "timestamp" in df.columns:
        df = df.copy()
        df["_date"] = pd.to_datetime(df["timestamp"]).dt.date
        df["_delta"] = delta
        cvd = df.groupby("_date")["_delta"].cumsum()
    else:
        cvd = delta.cumsum()

    return cvd


def delta_rolling(
    df: pd.DataFrame,
    window: int = 5,
) -> pd.Series:
    """
    Calculate rolling sum of volume delta.

    Args:
        df: DataFrame with OHLCV data
        window: Rolling window size

    Returns:
        Series of rolling delta values
    """
    delta = volume_delta(df)
    return delta.rolling(window=window, min_periods=1).sum()


def get_delta_bias(delta: float) -> str:
    """
    Get delta bias as string.

    Args:
        delta: Delta value

    Returns:
        "BUY" if positive, "SELL" if negative, "NEUTRAL" if zero
    """
    if delta > 0:
        return "BUY"
    elif delta < 0:
        return "SELL"
    else:
        return "NEUTRAL"
