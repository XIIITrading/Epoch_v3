"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 03: SHARED INDICATORS
Volume Delta Calculation (Bar Position Method)
XIII Trading LLC
================================================================================

Formula:
  bar_position = (close - low) / (high - low)
  delta_multiplier = (2 * bar_position) - 1
  bar_delta = volume * delta_multiplier

Health Factor: LONG: positive delta, SHORT: negative delta

================================================================================
"""

from typing import List, Optional, Any
import sys
from pathlib import Path

# Add parent to path for relative imports within shared library
_LIB_DIR = Path(__file__).parent.parent
if str(_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_LIB_DIR))

from _internal import VOLUME_DELTA_CONFIG, VolumeDeltaResult, get_open, get_high, get_low, get_close, get_volume

# Import RollingDeltaResult directly (not in _internal)
from indicator_types import RollingDeltaResult


def calculate_bar_delta(
    open_price: float,
    high: float,
    low: float,
    close: float,
    volume: int
) -> VolumeDeltaResult:
    """
    Calculate volume delta for a single bar using bar position method.

    The bar position represents where the close is within the bar's range.
    Close at high = position 1.0 = all buying pressure
    Close at low = position 0.0 = all selling pressure

    Args:
        open_price: Bar open price
        high: Bar high price
        low: Bar low price
        close: Bar close price
        volume: Bar volume

    Returns:
        VolumeDeltaResult with bar_delta, bar_position, delta_multiplier
    """
    bar_range = high - low

    if bar_range == 0:
        # Doji bar - use direction from open to close
        if close >= open_price:
            return VolumeDeltaResult(
                bar_delta=float(volume),
                bar_position=1.0,
                delta_multiplier=1.0
            )
        else:
            return VolumeDeltaResult(
                bar_delta=-float(volume),
                bar_position=0.0,
                delta_multiplier=-1.0
            )

    bar_position = (close - low) / bar_range
    delta_multiplier = (2 * bar_position) - 1
    bar_delta = volume * delta_multiplier

    return VolumeDeltaResult(
        bar_delta=bar_delta,
        bar_position=bar_position,
        delta_multiplier=delta_multiplier
    )


def calculate_bar_delta_from_bar(bar: Any) -> VolumeDeltaResult:
    """
    Calculate bar delta from a bar dict or object.

    Args:
        bar: Bar data (dict or object)

    Returns:
        VolumeDeltaResult
    """
    open_price = get_open(bar, 0.0)
    high = get_high(bar, 0.0)
    low = get_low(bar, 0.0)
    close = get_close(bar, 0.0)
    volume = get_volume(bar, 0)

    return calculate_bar_delta(open_price, high, low, close, volume)


def calculate_rolling_delta(
    bars: List[Any],
    up_to_index: Optional[int] = None,
    rolling_period: Optional[int] = None
) -> RollingDeltaResult:
    """
    Calculate rolling volume delta over N bars.

    Args:
        bars: List of bar data
        up_to_index: Calculate up to this index (inclusive)
        rolling_period: Number of bars for rolling calculation

    Returns:
        RollingDeltaResult with rolling_delta, signal, bar_count
    """
    period = rolling_period or VOLUME_DELTA_CONFIG["rolling_period"]

    if not bars:
        return RollingDeltaResult(rolling_delta=0.0, signal="Neutral", bar_count=0)

    end_index = up_to_index if up_to_index is not None else len(bars) - 1
    end_index = min(end_index, len(bars) - 1)
    start_idx = max(0, end_index - period + 1)
    bar_count = end_index - start_idx + 1

    rolling_delta = 0.0
    for i in range(start_idx, end_index + 1):
        result = calculate_bar_delta_from_bar(bars[i])
        rolling_delta += result.bar_delta

    if rolling_delta > 0:
        signal = "Bullish"
    elif rolling_delta < 0:
        signal = "Bearish"
    else:
        signal = "Neutral"

    return RollingDeltaResult(
        rolling_delta=rolling_delta,
        signal=signal,
        bar_count=bar_count
    )


def is_volume_delta_healthy(bar_delta: float, direction: str) -> bool:
    """
    Check if volume delta supports trade direction.

    Args:
        bar_delta: Volume delta value
        direction: Trade direction ('LONG' or 'SHORT')

    Returns:
        True if delta supports direction
    """
    is_long = direction.upper() == "LONG"
    return bar_delta > 0 if is_long else bar_delta < 0
