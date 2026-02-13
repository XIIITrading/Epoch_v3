"""
Epoch Trading System - CVD Indicator
=====================================

Cumulative Volume Delta and slope calculations.

Usage:
    from shared.indicators.core import cvd, cvd_slope

    # Calculate CVD
    df['cvd'] = cvd(df)
"""

import pandas as pd
import numpy as np
from typing import Union, Optional


def cvd(
    df: pd.DataFrame,
    open_col: str = "open",
    close_col: str = "close",
    volume_col: str = "volume",
    reset_daily: bool = True,
) -> pd.Series:
    """
    Calculate Cumulative Volume Delta.

    Args:
        df: DataFrame with OHLCV data
        open_col: Column name for open prices
        close_col: Column name for close prices
        volume_col: Column name for volume
        reset_daily: Reset CVD at start of each day

    Returns:
        Series of CVD values
    """
    # Calculate delta per bar
    direction = np.sign(df[close_col] - df[open_col])
    delta = direction * df[volume_col]

    if reset_daily and "timestamp" in df.columns:
        df = df.copy()
        df["_date"] = pd.to_datetime(df["timestamp"]).dt.date
        df["_delta"] = delta
        cvd_values = df.groupby("_date")["_delta"].cumsum()
    else:
        cvd_values = delta.cumsum()

    return cvd_values


def cvd_slope(
    df: pd.DataFrame,
    window: int = 5,
) -> pd.Series:
    """
    Calculate CVD slope (trend direction).

    Args:
        df: DataFrame with OHLCV data
        window: Window for slope calculation

    Returns:
        Series of slope values (positive = rising, negative = falling)
    """
    cvd_values = cvd(df)
    return cvd_values.diff(window)


def cvd_slope_normalized(
    df: pd.DataFrame,
    window: int = 5,
) -> pd.Series:
    """
    Calculate normalized CVD slope.

    Args:
        df: DataFrame with OHLCV data
        window: Window for slope calculation

    Returns:
        Series of normalized slope values (-1 to +1)
    """
    slope = cvd_slope(df, window)
    # Normalize by rolling max absolute value
    max_abs = slope.abs().rolling(window=window * 4, min_periods=1).max()
    return slope / max_abs.replace(0, 1)


def get_cvd_trend(slope: float) -> str:
    """
    Get CVD trend classification.

    Args:
        slope: CVD slope value

    Returns:
        "RISING" if positive, "FALLING" if negative, "FLAT" if near zero
    """
    if slope > 0:
        return "RISING"
    elif slope < 0:
        return "FALLING"
    else:
        return "FLAT"


def is_cvd_aligned(
    cvd_trend: str,
    trade_direction: str,
) -> bool:
    """
    Check if CVD trend aligns with trade direction.

    Args:
        cvd_trend: CVD trend ("RISING", "FALLING", "FLAT")
        trade_direction: Trade direction ("LONG", "SHORT")

    Returns:
        True if CVD supports trade direction
    """
    is_long = trade_direction.upper() in ("LONG", "BULL", "BULLISH")

    if is_long:
        return cvd_trend == "RISING"
    else:
        return cvd_trend == "FALLING"
