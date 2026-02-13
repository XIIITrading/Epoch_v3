"""
Epoch Trading System - Core Indicators
=======================================

Core technical indicator calculations.

All indicators follow a consistent interface:
- Accept pandas DataFrame or Series as input
- Return pandas Series or scalar values
- Handle NaN values gracefully
- Are optimized for performance

Usage:
    from shared.indicators.core import sma, vwap, atr

    # Calculate 20-period SMA
    df['sma_20'] = sma(df['close'], period=20)

    # Calculate VWAP
    df['vwap'] = vwap(df)

    # Calculate ATR
    df['atr'] = atr(df, period=14)
"""

from .sma import sma, ema
from .vwap import vwap
from .atr import atr
from .volume_delta import volume_delta, cumulative_delta
from .volume_roc import volume_roc
from .cvd import cvd, cvd_slope
from .candle_range import candle_range, relative_candle_range

__all__ = [
    "sma",
    "ema",
    "vwap",
    "atr",
    "volume_delta",
    "cumulative_delta",
    "volume_roc",
    "cvd",
    "cvd_slope",
    "candle_range",
    "relative_candle_range",
]
