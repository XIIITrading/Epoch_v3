"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 03: SHARED INDICATORS
VWAP Calculation
XIII Trading LLC
================================================================================

VWAP = Cumulative(Typical Price * Volume) / Cumulative(Volume)
Typical Price = (High + Low + Close) / 3

Health Factor: Price above VWAP = bullish, below = bearish

================================================================================
"""

from typing import List, Dict, Optional, Union, Any
import sys
from pathlib import Path

# Add parent to path for relative imports within shared library
_LIB_DIR = Path(__file__).parent.parent
if str(_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_LIB_DIR))

from _internal import VWAPResult, get_high, get_low, get_close, get_volume


def calculate_vwap(bars: List[Any], up_to_index: Optional[int] = None) -> Optional[float]:
    """
    Calculate VWAP (Volume Weighted Average Price) from bars.

    Formula: VWAP = Cumulative(TP * Volume) / Cumulative(Volume)
    where TP = (High + Low + Close) / 3

    Args:
        bars: List of bar data (dicts or objects with high, low, close, volume)
        up_to_index: Calculate up to this index (inclusive). None = use all bars.

    Returns:
        VWAP value or None if calculation not possible
    """
    if not bars:
        return None

    end_index = up_to_index if up_to_index is not None else len(bars) - 1
    end_index = min(end_index, len(bars) - 1)

    cumulative_tp_vol = 0.0
    cumulative_vol = 0

    for i in range(end_index + 1):
        bar = bars[i]
        high = get_high(bar)
        low = get_low(bar)
        close = get_close(bar)
        volume = get_volume(bar)

        if high is None or low is None or close is None:
            continue

        typical_price = (high + low + close) / 3
        cumulative_tp_vol += typical_price * volume
        cumulative_vol += volume

    if cumulative_vol == 0:
        return None

    return cumulative_tp_vol / cumulative_vol


def calculate_vwap_metrics(
    bars: List[Any],
    current_price: float,
    up_to_index: Optional[int] = None
) -> VWAPResult:
    """
    Calculate VWAP with price relationship metrics.

    Args:
        bars: List of bar data
        current_price: Current price to compare against VWAP
        up_to_index: Calculate up to this index (inclusive)

    Returns:
        VWAPResult with vwap, price_diff, price_pct, and side
    """
    vwap = calculate_vwap(bars, up_to_index)

    if vwap is None or vwap == 0:
        return VWAPResult(vwap=None, price_diff=None, price_pct=None, side=None)

    diff = current_price - vwap
    pct = (diff / vwap) * 100

    if abs(diff) < 0.01:
        side = "AT"
    elif diff > 0:
        side = "ABOVE"
    else:
        side = "BELOW"

    return VWAPResult(vwap=vwap, price_diff=diff, price_pct=pct, side=side)


def is_vwap_healthy(price: float, vwap: Optional[float], direction: str) -> bool:
    """
    Check if price vs VWAP is healthy for trade direction.

    Args:
        price: Current price
        vwap: VWAP value
        direction: Trade direction ('LONG' or 'SHORT')

    Returns:
        True if price position supports trade direction
    """
    if vwap is None:
        return False
    is_long = direction.upper() == "LONG"
    return price > vwap if is_long else price < vwap
