"""
Candle Range Calculations
Epoch Trading System v1 - XIII Trading LLC

Calculates candle range percentage from OHLC bar data.
Used as primary skip filter for absorption zones.
"""
from typing import List, Optional


# Absorption Zone threshold - skip trades below this
ABSORPTION_THRESHOLD = 0.0012  # 0.12%

# Normal range threshold - trades above this have edge
NORMAL_THRESHOLD = 0.0015  # 0.15%

# High range threshold - strong signal
HIGH_THRESHOLD = 0.0020  # 0.20%


def calculate_candle_range_pct(
    high: float,
    low: float,
    close: float
) -> float:
    """
    Calculate candle range as percentage of price.

    Formula: (high - low) / close * 100

    Args:
        high: Bar high price
        low: Bar low price
        close: Bar close price (used as reference)

    Returns:
        Candle range as percentage (e.g., 0.15 for 0.15%)
    """
    if close <= 0:
        return 0.0

    range_value = high - low
    return (range_value / close) * 100


def is_absorption_zone(candle_range_pct: float) -> bool:
    """
    Check if candle range indicates absorption zone (should skip).

    Args:
        candle_range_pct: Candle range as percentage

    Returns:
        True if this is an absorption zone (< 0.12%)
    """
    return candle_range_pct < (ABSORPTION_THRESHOLD * 100)


def get_range_classification(candle_range_pct: float) -> str:
    """
    Classify candle range for display/logging.

    Args:
        candle_range_pct: Candle range as percentage

    Returns:
        Classification string: 'ABSORPTION', 'LOW', 'NORMAL', 'HIGH'
    """
    if candle_range_pct < (ABSORPTION_THRESHOLD * 100):
        return 'ABSORPTION'
    elif candle_range_pct < (NORMAL_THRESHOLD * 100):
        return 'LOW'
    elif candle_range_pct < (HIGH_THRESHOLD * 100):
        return 'NORMAL'
    else:
        return 'HIGH'


def calculate_all_candle_ranges(bars: List[dict]) -> List[dict]:
    """
    Calculate candle range percentage for all bars.

    Args:
        bars: List of bar dictionaries with h, l, c keys

    Returns:
        List of dicts with 'candle_range_pct' and 'is_absorption' keys
    """
    results = []

    for bar in bars:
        high = bar.get('high', bar.get('h', 0))
        low = bar.get('low', bar.get('l', 0))
        close = bar.get('close', bar.get('c', 0))

        candle_range_pct = calculate_candle_range_pct(high, low, close)
        is_absorption = is_absorption_zone(candle_range_pct)

        results.append({
            'candle_range_pct': candle_range_pct,
            'is_absorption': is_absorption
        })

    return results
