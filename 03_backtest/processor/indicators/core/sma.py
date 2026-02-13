"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 03: SHARED INDICATORS
SMA Calculations
XIII Trading LLC
================================================================================

Calculates SMA9, SMA21, spread, and momentum.

Health Factors:
- SMA Alignment: SMA9 > SMA21 for LONG, SMA9 < SMA21 for SHORT
- SMA Momentum: WIDENING spread = healthy

================================================================================
"""

from typing import List, Optional, Any
import sys
from pathlib import Path

# Add parent to path for relative imports within shared library
_LIB_DIR = Path(__file__).parent.parent
if str(_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_LIB_DIR))

from _internal import SMA_CONFIG, SMAResult, SMAMomentumResult, get_close


def calculate_sma(
    bars: List[Any],
    period: int,
    up_to_index: Optional[int] = None
) -> Optional[float]:
    """
    Calculate Simple Moving Average for a given period.

    Args:
        bars: List of bar data
        period: Number of bars for SMA calculation
        up_to_index: Calculate up to this index (inclusive)

    Returns:
        SMA value or None if insufficient data
    """
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
    fast_period: Optional[int] = None,
    slow_period: Optional[int] = None
) -> SMAResult:
    """
    Calculate SMA9/SMA21 spread and alignment.

    Args:
        bars: List of bar data
        up_to_index: Calculate up to this index (inclusive)
        fast_period: Fast SMA period (default from config)
        slow_period: Slow SMA period (default from config)

    Returns:
        SMAResult with sma9, sma21, spread, alignment, cross_estimate
    """
    fast = fast_period or SMA_CONFIG["fast_period"]
    slow = slow_period or SMA_CONFIG["slow_period"]

    sma_fast = calculate_sma(bars, fast, up_to_index)
    sma_slow = calculate_sma(bars, slow, up_to_index)

    if sma_fast is None or sma_slow is None:
        return SMAResult(
            sma9=sma_fast,
            sma21=sma_slow,
            spread=None,
            alignment=None,
            cross_estimate=None
        )

    spread = sma_fast - sma_slow
    alignment = "BULLISH" if sma_fast > sma_slow else "BEARISH"
    cross_estimate = (sma_fast + sma_slow) / 2

    return SMAResult(
        sma9=sma_fast,
        sma21=sma_slow,
        spread=spread,
        alignment=alignment,
        cross_estimate=cross_estimate
    )


def calculate_sma_momentum(
    bars: List[Any],
    up_to_index: Optional[int] = None,
    lookback: Optional[int] = None
) -> SMAMomentumResult:
    """
    Calculate SMA spread momentum (widening/narrowing).

    Args:
        bars: List of bar data
        up_to_index: Calculate up to this index (inclusive)
        lookback: Bars to look back for momentum comparison

    Returns:
        SMAMomentumResult with spread_now, spread_prev, momentum, ratio
    """
    lookback = lookback or SMA_CONFIG["momentum_lookback"]
    widen_thresh = SMA_CONFIG["widening_threshold"]
    narrow_thresh = SMA_CONFIG["narrowing_threshold"]

    end_index = up_to_index if up_to_index is not None else len(bars) - 1
    end_index = min(end_index, len(bars) - 1)

    current_result = calculate_sma_spread(bars, end_index)
    spread_now = current_result.spread

    if spread_now is None:
        return SMAMomentumResult(
            spread_now=None,
            spread_prev=None,
            momentum="FLAT",
            ratio=None
        )

    earlier_index = end_index - lookback
    if earlier_index < SMA_CONFIG["slow_period"]:
        return SMAMomentumResult(
            spread_now=spread_now,
            spread_prev=None,
            momentum="FLAT",
            ratio=None
        )

    earlier_result = calculate_sma_spread(bars, earlier_index)
    spread_prev = earlier_result.spread

    if spread_prev is None:
        return SMAMomentumResult(
            spread_now=spread_now,
            spread_prev=None,
            momentum="FLAT",
            ratio=None
        )

    abs_now = abs(spread_now)
    abs_prev = abs(spread_prev)

    if abs_prev == 0:
        return SMAMomentumResult(
            spread_now=spread_now,
            spread_prev=spread_prev,
            momentum="FLAT",
            ratio=None
        )

    ratio = abs_now / abs_prev

    if ratio > widen_thresh:
        momentum = "WIDENING"
    elif ratio < narrow_thresh:
        momentum = "NARROWING"
    else:
        momentum = "FLAT"

    return SMAMomentumResult(
        spread_now=spread_now,
        spread_prev=spread_prev,
        momentum=momentum,
        ratio=ratio
    )


def is_sma_alignment_healthy(
    sma9: Optional[float],
    sma21: Optional[float],
    direction: str
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
    is_long = direction.upper() == "LONG"
    return sma9 > sma21 if is_long else sma9 < sma21


def is_sma_momentum_healthy(momentum: str) -> bool:
    """
    Check if SMA momentum is healthy.

    Args:
        momentum: Momentum classification ('WIDENING', 'NARROWING', 'FLAT')

    Returns:
        True if momentum is widening
    """
    return momentum == "WIDENING"


# =============================================================================
# EPCH Indicators v1.0 Reference Functions
# =============================================================================

def calculate_sma_spread_pct(
    sma9: float,
    sma21: float,
    price: float
) -> float:
    """
    Calculate spread between SMA9 and SMA21 as percentage of price.

    Per EPCH Indicators v1.0 spec.

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


def is_wide_spread(spread_pct: float) -> bool:
    """
    Check if SMA spread indicates strong trend.

    Per EPCH Indicators v1.0 spec.

    Args:
        spread_pct: Spread as percentage

    Returns:
        True if spread >= 0.15%
    """
    return spread_pct >= SMA_CONFIG.get("wide_spread_threshold", 0.15)


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


def format_sma_display(config: str, spread_pct: float) -> str:
    """
    Format SMA config and spread for display.

    Args:
        config: SMA configuration ("BULL", "BEAR", "FLAT")
        spread_pct: Spread as percentage

    Returns:
        Formatted string like "BULL 0.15%"
    """
    return f"{config} {spread_pct:.2f}%"
