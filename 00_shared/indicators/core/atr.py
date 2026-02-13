"""
Epoch Trading System - ATR Indicator
=====================================

Average True Range calculations for volatility measurement.

Usage:
    from shared.indicators.core import atr

    # Calculate 14-period ATR
    df['atr'] = atr(df, period=14)
"""

import pandas as pd
import numpy as np
from typing import Union, Optional


def atr(
    df: pd.DataFrame,
    period: int = 14,
    high_col: str = "high",
    low_col: str = "low",
    close_col: str = "close",
) -> pd.Series:
    """
    Calculate Average True Range.

    Args:
        df: DataFrame with OHLCV data
        period: ATR period (default 14)
        high_col: Column name for high prices
        low_col: Column name for low prices
        close_col: Column name for close prices

    Returns:
        Series of ATR values
    """
    high = df[high_col]
    low = df[low_col]
    close = df[close_col]

    # Calculate True Range components
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))

    # True Range is the max of the three
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # ATR is the rolling mean of True Range
    atr_values = tr.rolling(window=period, min_periods=period).mean()

    return atr_values


def atr_pct(
    df: pd.DataFrame,
    period: int = 14,
    price_col: str = "close",
) -> pd.Series:
    """
    Calculate ATR as percentage of price.

    Args:
        df: DataFrame with OHLCV data
        period: ATR period
        price_col: Column name for reference price

    Returns:
        Series of ATR percentage values
    """
    atr_values = atr(df, period)
    return (atr_values / df[price_col]) * 100


def get_atr_multiple(
    price_distance: float,
    atr_value: float,
) -> float:
    """
    Calculate how many ATRs a price distance represents.

    Args:
        price_distance: Distance in price units
        atr_value: ATR value

    Returns:
        Multiple of ATR (e.g., 1.5 = 1.5 ATRs)
    """
    if atr_value == 0:
        return 0.0
    return abs(price_distance) / atr_value
