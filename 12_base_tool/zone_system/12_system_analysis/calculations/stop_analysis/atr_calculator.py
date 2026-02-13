"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Calculation: ATR Calculator for Stop Analysis (CALC-009)
XIII Trading LLC
================================================================================

PURPOSE:
    Calculate Average True Range (ATR) for M5 and M15 timeframes.
    Used for volatility-based stop placement in Stop Type Analysis.

ATR FORMULA:
    True Range = max(
        high - low,
        abs(high - prev_close),
        abs(low - prev_close)
    )
    ATR = Simple Moving Average of True Range over N periods

TIMEFRAMES:
    - M5 ATR: 14-period ATR on 5-minute bars
    - M15 ATR: 14-period ATR on aggregated 15-minute bars (3 M5 bars each)

================================================================================
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal


def _safe_float(value, default: float = 0.0) -> float:
    """Safely convert value to float, handling Decimal types."""
    if value is None:
        return default
    try:
        if isinstance(value, Decimal):
            return float(value)
        return float(value)
    except (ValueError, TypeError):
        return default


def calculate_true_range(
    high: float,
    low: float,
    prev_close: Optional[float] = None
) -> float:
    """
    Calculate True Range for a single bar.

    True Range = max(
        high - low,
        abs(high - prev_close),
        abs(low - prev_close)
    )

    Parameters:
    -----------
    high : float
        Bar high price
    low : float
        Bar low price
    prev_close : float, optional
        Previous bar's close price. If None, uses high-low only.

    Returns:
    --------
    float
        True range value
    """
    high = _safe_float(high)
    low = _safe_float(low)

    # Basic range
    range_hl = high - low

    if prev_close is None:
        return range_hl

    prev_close = _safe_float(prev_close)

    # Full true range calculation
    return max(
        range_hl,
        abs(high - prev_close),
        abs(low - prev_close)
    )


def calculate_atr_m5(
    m5_bars: List[Dict[str, Any]],
    period: int = 14
) -> Optional[float]:
    """
    Calculate 14-period ATR on M5 bars.

    Uses bars at or before entry (bars_from_entry <= 0) to calculate
    ATR at the moment of trade entry.

    Parameters:
    -----------
    m5_bars : List[Dict[str, Any]]
        List of M5 bar records with 'high', 'low', 'close', 'bars_from_entry'
    period : int
        ATR period (default 14)

    Returns:
    --------
    float or None
        ATR value, or None if insufficient data
    """
    if not m5_bars:
        return None

    # Filter to bars at or before entry
    pre_entry_bars = [b for b in m5_bars if b.get('bars_from_entry', 0) <= 0]

    # Sort by bars_from_entry (most negative first, then 0)
    pre_entry_bars.sort(key=lambda x: x.get('bars_from_entry', 0))

    # Need at least 'period' bars
    if len(pre_entry_bars) < period:
        # Fall back to available data if we have at least 2 bars
        if len(pre_entry_bars) < 2:
            return None
        period = len(pre_entry_bars)

    # Take the most recent 'period' bars (closest to entry)
    recent_bars = pre_entry_bars[-period:]

    # Calculate true ranges
    true_ranges = []
    for i, bar in enumerate(recent_bars):
        high = _safe_float(bar.get('high'))
        low = _safe_float(bar.get('low'))

        if i == 0:
            # First bar - no previous close available
            tr = high - low
        else:
            prev_close = _safe_float(recent_bars[i-1].get('close'))
            tr = calculate_true_range(high, low, prev_close)

        true_ranges.append(tr)

    if not true_ranges:
        return None

    # Simple average (SMA) of true ranges
    return sum(true_ranges) / len(true_ranges)


def aggregate_m5_to_m15(m5_bars: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Aggregate M5 bars into M15 bars.

    Every 3 consecutive M5 bars form 1 M15 bar:
    - M15 high = max(3 M5 highs)
    - M15 low = min(3 M5 lows)
    - M15 open = first M5 open
    - M15 close = last M5 close

    Parameters:
    -----------
    m5_bars : List[Dict[str, Any]]
        List of M5 bar records sorted by time

    Returns:
    --------
    List[Dict[str, Any]]
        List of aggregated M15 bars
    """
    if not m5_bars or len(m5_bars) < 3:
        return []

    # Sort by bars_from_entry to ensure correct order
    sorted_bars = sorted(m5_bars, key=lambda x: x.get('bars_from_entry', 0))

    m15_bars = []

    # Group into sets of 3
    for i in range(0, len(sorted_bars) - 2, 3):
        group = sorted_bars[i:i+3]
        if len(group) < 3:
            continue

        m15_bar = {
            'high': max(_safe_float(b.get('high')) for b in group),
            'low': min(_safe_float(b.get('low')) for b in group),
            'open': _safe_float(group[0].get('open')),
            'close': _safe_float(group[-1].get('close')),
            'bars_from_entry': group[-1].get('bars_from_entry', 0)  # Use last bar's position
        }
        m15_bars.append(m15_bar)

    return m15_bars


def calculate_atr_m15(
    m5_bars: List[Dict[str, Any]],
    period: int = 14
) -> Optional[float]:
    """
    Calculate 14-period ATR on M15 timeframe by aggregating M5 bars.

    Need 14 M15 bars = 42 M5 bars for full ATR calculation.
    Falls back to available data if insufficient history.

    Parameters:
    -----------
    m5_bars : List[Dict[str, Any]]
        List of M5 bar records with 'high', 'low', 'close', 'bars_from_entry'
    period : int
        ATR period (default 14)

    Returns:
    --------
    float or None
        ATR value, or None if insufficient data
    """
    if not m5_bars:
        return None

    # Filter to bars at or before entry
    pre_entry_bars = [b for b in m5_bars if b.get('bars_from_entry', 0) <= 0]

    # Sort by bars_from_entry
    pre_entry_bars.sort(key=lambda x: x.get('bars_from_entry', 0))

    # Need at least 6 M5 bars for 2 M15 bars (minimum for ATR)
    if len(pre_entry_bars) < 6:
        return None

    # Aggregate M5 to M15
    m15_bars = aggregate_m5_to_m15(pre_entry_bars)

    if len(m15_bars) < 2:
        return None

    # Adjust period if we don't have enough M15 bars
    actual_period = min(period, len(m15_bars))

    # Take most recent bars
    recent_bars = m15_bars[-actual_period:]

    # Calculate true ranges
    true_ranges = []
    for i, bar in enumerate(recent_bars):
        high = bar['high']
        low = bar['low']

        if i == 0:
            tr = high - low
        else:
            prev_close = recent_bars[i-1]['close']
            tr = calculate_true_range(high, low, prev_close)

        true_ranges.append(tr)

    if not true_ranges:
        return None

    return sum(true_ranges) / len(true_ranges)


# =============================================================================
# TESTING
# =============================================================================
if __name__ == "__main__":
    # Test data: M5 bars with typical price movements
    test_m5_bars = [
        {'bars_from_entry': -13, 'high': 100.50, 'low': 99.80, 'open': 100.00, 'close': 100.20},
        {'bars_from_entry': -12, 'high': 100.80, 'low': 100.00, 'open': 100.20, 'close': 100.60},
        {'bars_from_entry': -11, 'high': 101.00, 'low': 100.30, 'open': 100.60, 'close': 100.50},
        {'bars_from_entry': -10, 'high': 100.70, 'low': 100.10, 'open': 100.50, 'close': 100.40},
        {'bars_from_entry': -9, 'high': 100.60, 'low': 99.90, 'open': 100.40, 'close': 100.20},
        {'bars_from_entry': -8, 'high': 100.40, 'low': 99.70, 'open': 100.20, 'close': 99.90},
        {'bars_from_entry': -7, 'high': 100.30, 'low': 99.60, 'open': 99.90, 'close': 100.10},
        {'bars_from_entry': -6, 'high': 100.50, 'low': 99.90, 'open': 100.10, 'close': 100.30},
        {'bars_from_entry': -5, 'high': 100.70, 'low': 100.20, 'open': 100.30, 'close': 100.50},
        {'bars_from_entry': -4, 'high': 100.90, 'low': 100.40, 'open': 100.50, 'close': 100.70},
        {'bars_from_entry': -3, 'high': 101.10, 'low': 100.50, 'open': 100.70, 'close': 100.90},
        {'bars_from_entry': -2, 'high': 101.20, 'low': 100.70, 'open': 100.90, 'close': 101.00},
        {'bars_from_entry': -1, 'high': 101.30, 'low': 100.80, 'open': 101.00, 'close': 101.10},
        {'bars_from_entry': 0, 'high': 101.40, 'low': 100.90, 'open': 101.10, 'close': 101.20},
    ]

    # Test M5 ATR
    atr_m5 = calculate_atr_m5(test_m5_bars, period=14)
    print(f"M5 ATR (14-period): {atr_m5:.4f}" if atr_m5 else "M5 ATR: None")

    # Test M15 ATR
    atr_m15 = calculate_atr_m15(test_m5_bars, period=14)
    print(f"M15 ATR (14-period): {atr_m15:.4f}" if atr_m15 else "M15 ATR: None")

    # Test aggregation
    m15_bars = aggregate_m5_to_m15(test_m5_bars)
    print(f"\nAggregated {len(test_m5_bars)} M5 bars into {len(m15_bars)} M15 bars")
