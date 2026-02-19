"""
================================================================================
EPOCH TRADING SYSTEM - SMA (Canonical)
Simple Moving Average with Spread, Momentum, and Configuration
XIII Trading LLC
================================================================================

SMA9 / SMA21 spread analysis with momentum detection.

Labels:
    Config: "BULL", "BEAR", "FLAT"
    Momentum: "WIDENING", "NARROWING", "FLAT"
    Price Position: "ABOVE", "BELOW", "BTWN"

================================================================================
"""

import numpy as np
import pandas as pd
from typing import List, Optional, Any, Union

from ..config import CONFIG
from ..types import SMAResult, SMAMomentumResult
from .._utils import get_close


# =============================================================================
# NUMPY CORE
# =============================================================================

def _sma_core(close: np.ndarray, period: int) -> np.ndarray:
    """
    Calculate SMA series.

    Returns:
        numpy array (NaN where insufficient data)
    """
    n = len(close)
    result = np.full(n, np.nan)

    for i in range(period - 1, n):
        result[i] = close[i - period + 1:i + 1].mean()

    return result


def _ema_core(close: np.ndarray, period: int) -> np.ndarray:
    """
    Calculate EMA series.

    Returns:
        numpy array
    """
    n = len(close)
    result = np.full(n, np.nan)

    if n < period:
        return result

    # Seed with SMA
    result[period - 1] = close[:period].mean()
    multiplier = 2.0 / (period + 1)

    for i in range(period, n):
        result[i] = (close[i] - result[i - 1]) * multiplier + result[i - 1]

    return result


# =============================================================================
# DATAFRAME WRAPPER
# =============================================================================

def sma_df(
    df: pd.DataFrame,
    period: int,
    close_col: str = "close",
) -> pd.Series:
    """Calculate SMA series for a DataFrame."""
    return pd.Series(
        _sma_core(df[close_col].values.astype(np.float64), period),
        index=df.index,
        name=f"sma_{period}",
    )


def ema_df(
    df: pd.DataFrame,
    period: int,
    close_col: str = "close",
) -> pd.Series:
    """Calculate EMA series for a DataFrame."""
    return pd.Series(
        _ema_core(df[close_col].values.astype(np.float64), period),
        index=df.index,
        name=f"ema_{period}",
    )


def sma_spread_df(
    df: pd.DataFrame,
    close_col: str = "close",
) -> pd.DataFrame:
    """
    Calculate SMA9, SMA21, spread, and config for a DataFrame.

    Returns DataFrame with columns: sma9, sma21, sma_spread, sma_config, sma_spread_pct
    """
    cfg = CONFIG.sma
    close = df[close_col].values.astype(np.float64)
    sma9 = _sma_core(close, cfg.fast_period)
    sma21 = _sma_core(close, cfg.slow_period)

    spread = sma9 - sma21
    config_arr = np.where(sma9 > sma21, "BULL", np.where(sma9 < sma21, "BEAR", "FLAT"))
    spread_pct = np.where(close > 0, np.abs(spread) / close * 100, 0.0)

    result = pd.DataFrame(index=df.index)
    result["sma9"] = sma9
    result["sma21"] = sma21
    result["sma_spread"] = spread
    result["sma_config"] = config_arr
    result["sma_spread_pct"] = spread_pct
    return result


# =============================================================================
# BAR-LIST WRAPPER
# =============================================================================

def calculate_sma(
    bars: List[Any],
    period: int,
    up_to_index: Optional[int] = None,
) -> Optional[float]:
    """Calculate SMA from bar list. Returns None if insufficient data."""
    if not bars:
        return None

    end_index = up_to_index if up_to_index is not None else len(bars) - 1
    end_index = min(end_index, len(bars) - 1)

    if end_index < period - 1:
        return None

    start_idx = end_index - period + 1
    prices = []
    for i in range(start_idx, end_index + 1):
        price = get_close(bars[i])
        if price is not None:
            prices.append(price)

    if len(prices) < period:
        return None

    return sum(prices) / len(prices)


def calculate_sma_spread(
    bars: List[Any],
    up_to_index: Optional[int] = None,
) -> SMAResult:
    """Calculate SMA9/SMA21 spread and alignment from bar list."""
    cfg = CONFIG.sma
    sma_fast = calculate_sma(bars, cfg.fast_period, up_to_index)
    sma_slow = calculate_sma(bars, cfg.slow_period, up_to_index)

    if sma_fast is None or sma_slow is None:
        return SMAResult(sma9=sma_fast, sma21=sma_slow, spread=None, alignment=None, cross_estimate=None)

    spread = sma_fast - sma_slow
    alignment = "BULLISH" if sma_fast > sma_slow else "BEARISH"
    cross_estimate = (sma_fast + sma_slow) / 2

    return SMAResult(sma9=sma_fast, sma21=sma_slow, spread=spread, alignment=alignment, cross_estimate=cross_estimate)


def calculate_sma_momentum(
    bars: List[Any],
    up_to_index: Optional[int] = None,
) -> SMAMomentumResult:
    """Calculate SMA spread momentum (WIDENING/NARROWING/FLAT)."""
    cfg = CONFIG.sma

    end_index = up_to_index if up_to_index is not None else len(bars) - 1
    end_index = min(end_index, len(bars) - 1)

    current_result = calculate_sma_spread(bars, end_index)
    spread_now = current_result.spread

    if spread_now is None:
        return SMAMomentumResult(spread_now=None, spread_prev=None, momentum="FLAT", ratio=None)

    earlier_index = end_index - cfg.momentum_lookback
    if earlier_index < cfg.slow_period:
        return SMAMomentumResult(spread_now=spread_now, spread_prev=None, momentum="FLAT", ratio=None)

    earlier_result = calculate_sma_spread(bars, earlier_index)
    spread_prev = earlier_result.spread

    if spread_prev is None:
        return SMAMomentumResult(spread_now=spread_now, spread_prev=None, momentum="FLAT", ratio=None)

    abs_now = abs(spread_now)
    abs_prev = abs(spread_prev)

    if abs_prev == 0:
        return SMAMomentumResult(spread_now=spread_now, spread_prev=spread_prev, momentum="FLAT", ratio=None)

    ratio = abs_now / abs_prev

    if ratio > cfg.widening_threshold:
        momentum = "WIDENING"
    elif ratio < cfg.narrowing_threshold:
        momentum = "NARROWING"
    else:
        momentum = "FLAT"

    return SMAMomentumResult(spread_now=spread_now, spread_prev=spread_prev, momentum=momentum, ratio=ratio)


# =============================================================================
# CLASSIFICATION HELPERS
# =============================================================================

def calculate_sma_spread_pct(sma9: float, sma21: float, price: float) -> float:
    """Calculate spread between SMA9 and SMA21 as percentage of price."""
    if price <= 0:
        return 0.0
    return (abs(sma9 - sma21) / price) * 100


def get_sma_config_str(sma9: float, sma21: float) -> str:
    """Get SMA configuration label: 'BULL', 'BEAR', or 'FLAT'."""
    if sma9 > sma21:
        return "BULL"
    elif sma9 < sma21:
        return "BEAR"
    return "FLAT"


def get_price_position(price: float, sma9: float, sma21: float) -> str:
    """Determine price position relative to SMAs: 'ABOVE', 'BELOW', or 'BTWN'."""
    higher_sma = max(sma9, sma21)
    lower_sma = min(sma9, sma21)

    if price > higher_sma:
        return "ABOVE"
    elif price < lower_sma:
        return "BELOW"
    return "BTWN"


def is_wide_spread(spread_pct: float) -> bool:
    """Check if SMA spread indicates strong trend (>= 0.15%)."""
    return spread_pct >= CONFIG.sma.wide_spread_threshold
