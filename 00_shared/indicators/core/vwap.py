"""
Epoch Trading System - VWAP Indicator
======================================

Volume-Weighted Average Price calculations.

Usage:
    from shared.indicators.core import vwap

    # Calculate VWAP
    df['vwap'] = vwap(df)
"""

import pandas as pd
import numpy as np
from typing import Union, Optional


def vwap(
    df: pd.DataFrame,
    high_col: str = "high",
    low_col: str = "low",
    close_col: str = "close",
    volume_col: str = "volume",
    reset_daily: bool = True,
) -> pd.Series:
    """
    Calculate Volume-Weighted Average Price.

    Args:
        df: DataFrame with OHLCV data
        high_col: Column name for high prices
        low_col: Column name for low prices
        close_col: Column name for close prices
        volume_col: Column name for volume
        reset_daily: Reset VWAP at start of each day

    Returns:
        Series of VWAP values
    """
    # Calculate typical price
    typical_price = (df[high_col] + df[low_col] + df[close_col]) / 3

    # Calculate VWAP
    if reset_daily and "timestamp" in df.columns:
        # Group by date and calculate cumulative VWAP
        df = df.copy()
        df["_date"] = pd.to_datetime(df["timestamp"]).dt.date
        df["_tp_vol"] = typical_price * df[volume_col]
        df["_cum_tp_vol"] = df.groupby("_date")["_tp_vol"].cumsum()
        df["_cum_vol"] = df.groupby("_date")[volume_col].cumsum()
        vwap_values = df["_cum_tp_vol"] / df["_cum_vol"]
    else:
        # Simple cumulative VWAP
        tp_vol = typical_price * df[volume_col]
        cum_tp_vol = tp_vol.cumsum()
        cum_vol = df[volume_col].cumsum()
        vwap_values = cum_tp_vol / cum_vol

    return vwap_values


def get_vwap_position(price: float, vwap_val: float) -> str:
    """
    Determine price position relative to VWAP.

    Args:
        price: Current price
        vwap_val: VWAP value

    Returns:
        "ABOVE" if price > VWAP, "BELOW" if price < VWAP, "AT" if equal
    """
    if price > vwap_val:
        return "ABOVE"
    elif price < vwap_val:
        return "BELOW"
    else:
        return "AT"


def vwap_distance_pct(price: float, vwap_val: float) -> float:
    """
    Calculate distance from price to VWAP as percentage.

    Args:
        price: Current price
        vwap_val: VWAP value

    Returns:
        Distance as percentage (positive if above, negative if below)
    """
    if vwap_val == 0:
        return 0.0
    return ((price - vwap_val) / vwap_val) * 100
