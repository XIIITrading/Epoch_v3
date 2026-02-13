"""
Epoch Trading System - Candle Range Indicator
==============================================

Candle range and relative size calculations.

Usage:
    from shared.indicators.core import candle_range, relative_candle_range

    # Calculate candle range
    df['range'] = candle_range(df)
"""

import pandas as pd
import numpy as np
from typing import Union, Optional


def candle_range(
    df: pd.DataFrame,
    high_col: str = "high",
    low_col: str = "low",
) -> pd.Series:
    """
    Calculate candle range (high - low).

    Args:
        df: DataFrame with OHLCV data
        high_col: Column name for high prices
        low_col: Column name for low prices

    Returns:
        Series of range values
    """
    return df[high_col] - df[low_col]


def relative_candle_range(
    df: pd.DataFrame,
    period: int = 20,
    high_col: str = "high",
    low_col: str = "low",
) -> pd.Series:
    """
    Calculate candle range relative to average.

    Args:
        df: DataFrame with OHLCV data
        period: Baseline period for average range
        high_col: Column name for high prices
        low_col: Column name for low prices

    Returns:
        Series of relative range values (1.0 = average)
    """
    ranges = candle_range(df, high_col, low_col)
    avg_range = ranges.rolling(window=period, min_periods=1).mean()
    return ranges / avg_range.replace(0, np.nan)


def candle_body(
    df: pd.DataFrame,
    open_col: str = "open",
    close_col: str = "close",
) -> pd.Series:
    """
    Calculate candle body size (absolute).

    Args:
        df: DataFrame with OHLCV data
        open_col: Column name for open prices
        close_col: Column name for close prices

    Returns:
        Series of body size values (always positive)
    """
    return abs(df[close_col] - df[open_col])


def body_to_range_ratio(
    df: pd.DataFrame,
) -> pd.Series:
    """
    Calculate body to range ratio.

    Args:
        df: DataFrame with OHLCV data

    Returns:
        Series of ratios (0 to 1, higher = more body)
    """
    body = candle_body(df)
    range_val = candle_range(df)
    return body / range_val.replace(0, np.nan)


def get_candle_type(
    open_price: float,
    close_price: float,
    high_price: float,
    low_price: float,
) -> str:
    """
    Classify candle type.

    Args:
        open_price: Open price
        close_price: Close price
        high_price: High price
        low_price: Low price

    Returns:
        Candle type classification
    """
    body = abs(close_price - open_price)
    range_val = high_price - low_price

    if range_val == 0:
        return "DOJI"

    body_ratio = body / range_val

    if body_ratio < 0.1:
        return "DOJI"
    elif body_ratio < 0.3:
        return "SPINNING_TOP"
    elif body_ratio > 0.7:
        if close_price > open_price:
            return "STRONG_BULL"
        else:
            return "STRONG_BEAR"
    else:
        if close_price > open_price:
            return "BULL"
        else:
            return "BEAR"


def is_range_expansion(
    current_range: float,
    avg_range: float,
    threshold: float = 1.5,
) -> bool:
    """
    Check if current range is expanded.

    Args:
        current_range: Current candle range
        avg_range: Average range
        threshold: Expansion threshold

    Returns:
        True if range is expanded
    """
    if avg_range == 0:
        return False
    return current_range / avg_range >= threshold
