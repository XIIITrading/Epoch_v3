"""
Epoch Trading System - Volume ROC Indicator
============================================

Volume Rate of Change calculations.

Usage:
    from shared.indicators.core import volume_roc

    # Calculate volume ROC
    df['vol_roc'] = volume_roc(df)
"""

import pandas as pd
import numpy as np
from typing import Union, Optional


def volume_roc(
    df: pd.DataFrame,
    period: int = 20,
    volume_col: str = "volume",
) -> pd.Series:
    """
    Calculate Volume Rate of Change (current volume vs average).

    Args:
        df: DataFrame with volume data
        period: Baseline period for average volume
        volume_col: Column name for volume

    Returns:
        Series of ROC values (1.0 = average, 2.0 = 2x average)
    """
    avg_vol = df[volume_col].rolling(window=period, min_periods=1).mean()
    roc = df[volume_col] / avg_vol
    return roc.replace([np.inf, -np.inf], np.nan)


def volume_roc_pct(
    df: pd.DataFrame,
    period: int = 20,
    volume_col: str = "volume",
) -> pd.Series:
    """
    Calculate Volume ROC as percentage change from average.

    Args:
        df: DataFrame with volume data
        period: Baseline period
        volume_col: Column name for volume

    Returns:
        Series of percentage values (0 = average, 100 = 2x average)
    """
    roc = volume_roc(df, period, volume_col)
    return (roc - 1) * 100


def get_volume_intensity(roc: float) -> str:
    """
    Get volume intensity classification.

    Args:
        roc: Volume ROC value

    Returns:
        "HIGH" if > 1.5x, "ABOVE_AVG" if > 1.0x, "BELOW_AVG" if < 1.0x, "LOW" if < 0.5x
    """
    if roc >= 1.5:
        return "HIGH"
    elif roc >= 1.0:
        return "ABOVE_AVG"
    elif roc >= 0.5:
        return "BELOW_AVG"
    else:
        return "LOW"


def is_volume_healthy(roc: float, min_threshold: float = 0.8) -> bool:
    """
    Check if volume is healthy for trading.

    Args:
        roc: Volume ROC value
        min_threshold: Minimum ROC threshold

    Returns:
        True if volume is above threshold
    """
    return roc >= min_threshold
