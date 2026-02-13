"""
Epoch Trading System - SMA Indicators
======================================

Simple Moving Average calculations.

Health Factors:
- SMA Alignment: SMA9 > SMA21 for LONG, SMA9 < SMA21 for SHORT
- SMA Momentum: WIDENING spread = healthy

Usage:
    from shared.indicators.core import sma, ema

    # Calculate SMA on a Series
    df['sma_20'] = sma(df['close'], period=20)

    # Calculate SMA spread
    spread = calculate_sma_spread(df['close'], fast=9, slow=21)
"""

import pandas as pd
import numpy as np
from typing import Union, Optional, List, Any, NamedTuple


# =============================================================================
# CONFIGURATION
# =============================================================================
SMA_CONFIG = {
    "fast_period": 9,
    "slow_period": 21,
    "momentum_lookback": 3,
    "widening_threshold": 1.10,
    "narrowing_threshold": 0.90,
    "wide_spread_threshold": 0.15,
}


# =============================================================================
# RESULT TYPES
# =============================================================================
class SMAResult(NamedTuple):
    """Result of SMA spread calculation."""
    sma9: Optional[float]
    sma21: Optional[float]
    spread: Optional[float]
    alignment: Optional[str]  # "BULLISH" or "BEARISH"
    cross_estimate: Optional[float]


class SMAMomentumResult(NamedTuple):
    """Result of SMA momentum calculation."""
    spread_now: Optional[float]
    spread_prev: Optional[float]
    momentum: str  # "WIDENING", "NARROWING", or "FLAT"
    ratio: Optional[float]


# =============================================================================
# CORE FUNCTIONS
# =============================================================================
def sma(
    data: Union[pd.Series, List[float], np.ndarray],
    period: int = 20,
) -> Union[pd.Series, float, None]:
    """
    Calculate Simple Moving Average.

    Args:
        data: Price data (Series, list, or array)
        period: Number of periods for SMA

    Returns:
        Series of SMA values (if input is Series)
        Float (if input is list/array and calculating single value)
    """
    if isinstance(data, pd.Series):
        return data.rolling(window=period, min_periods=period).mean()
    elif isinstance(data, (list, np.ndarray)):
        arr = np.array(data)
        if len(arr) < period:
            return None
        return float(np.mean(arr[-period:]))
    else:
        raise TypeError(f"Unsupported data type: {type(data)}")


def ema(
    data: Union[pd.Series, List[float], np.ndarray],
    period: int = 20,
) -> Union[pd.Series, float, None]:
    """
    Calculate Exponential Moving Average.

    Args:
        data: Price data (Series, list, or array)
        period: Number of periods for EMA

    Returns:
        Series of EMA values (if input is Series)
        Float (if input is list/array)
    """
    if isinstance(data, pd.Series):
        return data.ewm(span=period, adjust=False).mean()
    elif isinstance(data, (list, np.ndarray)):
        arr = np.array(data)
        if len(arr) < period:
            return None
        series = pd.Series(arr)
        return float(series.ewm(span=period, adjust=False).mean().iloc[-1])
    else:
        raise TypeError(f"Unsupported data type: {type(data)}")


# =============================================================================
# SPREAD & ALIGNMENT FUNCTIONS
# =============================================================================
def calculate_sma_spread(
    data: Union[pd.Series, List[float]],
    fast: int = 9,
    slow: int = 21,
) -> SMAResult:
    """
    Calculate SMA spread and alignment.

    Args:
        data: Price data
        fast: Fast SMA period (default 9)
        slow: Slow SMA period (default 21)

    Returns:
        SMAResult with sma9, sma21, spread, alignment, cross_estimate
    """
    sma_fast = sma(data, fast)
    sma_slow = sma(data, slow)

    # Get the latest values
    if isinstance(sma_fast, pd.Series):
        sma_fast_val = sma_fast.iloc[-1] if not sma_fast.empty else None
        sma_slow_val = sma_slow.iloc[-1] if not sma_slow.empty else None
    else:
        sma_fast_val = sma_fast
        sma_slow_val = sma_slow

    if sma_fast_val is None or sma_slow_val is None or pd.isna(sma_fast_val) or pd.isna(sma_slow_val):
        return SMAResult(
            sma9=sma_fast_val,
            sma21=sma_slow_val,
            spread=None,
            alignment=None,
            cross_estimate=None,
        )

    spread = sma_fast_val - sma_slow_val
    alignment = "BULLISH" if sma_fast_val > sma_slow_val else "BEARISH"
    cross_estimate = (sma_fast_val + sma_slow_val) / 2

    return SMAResult(
        sma9=sma_fast_val,
        sma21=sma_slow_val,
        spread=spread,
        alignment=alignment,
        cross_estimate=cross_estimate,
    )


def calculate_sma_spread_pct(
    sma9: float,
    sma21: float,
    price: float,
) -> float:
    """
    Calculate spread between SMA9 and SMA21 as percentage of price.

    Args:
        sma9: SMA9 value
        sma21: SMA21 value
        price: Reference price for percentage calculation

    Returns:
        Spread as percentage (e.g., 0.15 for 0.15%)
    """
    if price <= 0:
        return 0.0
    spread = abs(sma9 - sma21)
    return (spread / price) * 100


# =============================================================================
# HEALTH CHECK FUNCTIONS
# =============================================================================
def is_sma_alignment_healthy(
    sma9: Optional[float],
    sma21: Optional[float],
    direction: str,
) -> bool:
    """
    Check if SMA alignment supports trade direction.

    Args:
        sma9: Fast SMA value
        sma21: Slow SMA value
        direction: Trade direction ('LONG' or 'SHORT')

    Returns:
        True if alignment supports direction
    """
    if sma9 is None or sma21 is None:
        return False
    is_long = direction.upper() in ("LONG", "BULL", "BULLISH")
    return sma9 > sma21 if is_long else sma9 < sma21


def is_wide_spread(spread_pct: float) -> bool:
    """
    Check if SMA spread indicates strong trend.

    Args:
        spread_pct: Spread as percentage

    Returns:
        True if spread >= 0.15%
    """
    return spread_pct >= SMA_CONFIG["wide_spread_threshold"]


def get_sma_config_str(sma9: float, sma21: float) -> str:
    """
    Get SMA configuration as string.

    Args:
        sma9: SMA9 value
        sma21: SMA21 value

    Returns:
        "BULL" if SMA9 > SMA21, "BEAR" if SMA9 < SMA21, "FLAT" if equal
    """
    if sma9 > sma21:
        return "BULL"
    elif sma9 < sma21:
        return "BEAR"
    else:
        return "FLAT"


def get_price_position(price: float, sma9: float, sma21: float) -> str:
    """
    Determine price position relative to SMAs.

    Args:
        price: Current price
        sma9: SMA9 value
        sma21: SMA21 value

    Returns:
        "ABOVE" if price > both, "BELOW" if price < both, "BTWN" if between
    """
    higher_sma = max(sma9, sma21)
    lower_sma = min(sma9, sma21)

    if price > higher_sma:
        return "ABOVE"
    elif price < lower_sma:
        return "BELOW"
    else:
        return "BTWN"
