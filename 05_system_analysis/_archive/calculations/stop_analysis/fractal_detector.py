"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Calculation: Fractal Detector for Stop Analysis (CALC-009)
XIII Trading LLC
================================================================================

PURPOSE:
    Detect fractal swing highs and lows for market structure stop placement.
    Used for Stop Type 6: M5 Fractal High/Low stops.

FRACTAL DEFINITION:
    Fractal High: Bar where high > high of N bars before AND N bars after
    Fractal Low: Bar where low < low of N bars before AND N bars after

    Default fractal_length = 2 (Williams fractals)
    - Requires 2 bars on each side for confirmation
    - Most recent confirmed fractal is at least 2 bars old

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


def find_fractal_highs(
    bars: List[Dict[str, Any]],
    fractal_length: int = 2
) -> List[Dict[str, Any]]:
    """
    Find all fractal highs in a bar series.

    A fractal high is a bar where:
    - high > high of all N bars before
    - high > high of all N bars after

    Parameters:
    -----------
    bars : List[Dict[str, Any]]
        List of bar records with 'high', 'bars_from_entry'
    fractal_length : int
        Number of bars on each side to check (default 2)

    Returns:
    --------
    List[Dict[str, Any]]
        List of fractal records with 'type', 'price', 'bars_from_entry', 'index'
    """
    if not bars or len(bars) < (2 * fractal_length + 1):
        return []

    # Sort by bars_from_entry to ensure correct order
    sorted_bars = sorted(bars, key=lambda x: x.get('bars_from_entry', 0))

    fractals = []

    for i in range(fractal_length, len(sorted_bars) - fractal_length):
        bar = sorted_bars[i]
        bar_high = _safe_float(bar.get('high'))

        is_fractal = True

        # Check bars before
        for j in range(1, fractal_length + 1):
            if bar_high <= _safe_float(sorted_bars[i - j].get('high')):
                is_fractal = False
                break

        # Check bars after
        if is_fractal:
            for j in range(1, fractal_length + 1):
                if bar_high <= _safe_float(sorted_bars[i + j].get('high')):
                    is_fractal = False
                    break

        if is_fractal:
            fractals.append({
                'type': 'high',
                'price': bar_high,
                'bars_from_entry': bar.get('bars_from_entry', 0),
                'index': i
            })

    return fractals


def find_fractal_lows(
    bars: List[Dict[str, Any]],
    fractal_length: int = 2
) -> List[Dict[str, Any]]:
    """
    Find all fractal lows in a bar series.

    A fractal low is a bar where:
    - low < low of all N bars before
    - low < low of all N bars after

    Parameters:
    -----------
    bars : List[Dict[str, Any]]
        List of bar records with 'low', 'bars_from_entry'
    fractal_length : int
        Number of bars on each side to check (default 2)

    Returns:
    --------
    List[Dict[str, Any]]
        List of fractal records with 'type', 'price', 'bars_from_entry', 'index'
    """
    if not bars or len(bars) < (2 * fractal_length + 1):
        return []

    # Sort by bars_from_entry to ensure correct order
    sorted_bars = sorted(bars, key=lambda x: x.get('bars_from_entry', 0))

    fractals = []

    for i in range(fractal_length, len(sorted_bars) - fractal_length):
        bar = sorted_bars[i]
        bar_low = _safe_float(bar.get('low'))

        is_fractal = True

        # Check bars before
        for j in range(1, fractal_length + 1):
            if bar_low >= _safe_float(sorted_bars[i - j].get('low')):
                is_fractal = False
                break

        # Check bars after
        if is_fractal:
            for j in range(1, fractal_length + 1):
                if bar_low >= _safe_float(sorted_bars[i + j].get('low')):
                    is_fractal = False
                    break

        if is_fractal:
            fractals.append({
                'type': 'low',
                'price': bar_low,
                'bars_from_entry': bar.get('bars_from_entry', 0),
                'index': i
            })

    return fractals


def get_most_recent_fractal(
    fractals: List[Dict[str, Any]],
    direction: str
) -> Optional[Dict[str, Any]]:
    """
    Get the most recent confirmed fractal for stop placement.

    For LONG trades: Need most recent fractal LOW (stop below)
    For SHORT trades: Need most recent fractal HIGH (stop above)

    Parameters:
    -----------
    fractals : List[Dict[str, Any]]
        List of fractal records
    direction : str
        Trade direction ('LONG' or 'SHORT')

    Returns:
    --------
    Dict or None
        Most recent fractal record, or None if not found
    """
    if not fractals:
        return None

    is_long = direction.upper() == 'LONG'
    fractal_type = 'low' if is_long else 'high'

    # Filter by type
    relevant_fractals = [f for f in fractals if f.get('type') == fractal_type]

    if not relevant_fractals:
        return None

    # Get most recent (highest bars_from_entry, closest to entry)
    return max(relevant_fractals, key=lambda x: x.get('bars_from_entry', -999))


def calculate_fractal_stop_price(
    m5_bars: List[Dict[str, Any]],
    direction: str,
    fractal_length: int = 2
) -> Optional[float]:
    """
    Calculate fractal-based stop price for a trade.

    For LONG: Stop at most recent confirmed swing low
    For SHORT: Stop at most recent confirmed swing high

    Note: Fractals need 'fractal_length' bars after to confirm, so
    most recent confirmed fractal is at least 'fractal_length' bars
    before entry.

    Parameters:
    -----------
    m5_bars : List[Dict[str, Any]]
        List of M5 bar records
    direction : str
        Trade direction ('LONG' or 'SHORT')
    fractal_length : int
        Bars on each side for fractal detection (default 2)

    Returns:
    --------
    float or None
        Stop price at fractal level, or None if no fractal found
    """
    if not m5_bars:
        return None

    # Filter to bars that can be confirmed (need bars after for confirmation)
    # bars_from_entry <= -fractal_length ensures we have confirmation bars
    confirmable_bars = [
        b for b in m5_bars
        if b.get('bars_from_entry', 0) <= -fractal_length
    ]

    if len(confirmable_bars) < (2 * fractal_length + 1):
        return None

    is_long = direction.upper() == 'LONG'

    if is_long:
        fractals = find_fractal_lows(confirmable_bars, fractal_length)
    else:
        fractals = find_fractal_highs(confirmable_bars, fractal_length)

    if not fractals:
        return None

    # Get most recent fractal
    most_recent = get_most_recent_fractal(fractals, direction)

    if most_recent:
        return most_recent['price']

    return None


# =============================================================================
# TESTING
# =============================================================================
if __name__ == "__main__":
    # Test data: M5 bars with swing highs and lows
    test_m5_bars = [
        {'bars_from_entry': -12, 'high': 100.50, 'low': 99.80},
        {'bars_from_entry': -11, 'high': 100.80, 'low': 100.00},
        {'bars_from_entry': -10, 'high': 101.20, 'low': 100.30},  # Potential swing high
        {'bars_from_entry': -9, 'high': 100.90, 'low': 100.10},
        {'bars_from_entry': -8, 'high': 100.60, 'low': 99.70},
        {'bars_from_entry': -7, 'high': 100.30, 'low': 99.40},   # Potential swing low
        {'bars_from_entry': -6, 'high': 100.50, 'low': 99.60},
        {'bars_from_entry': -5, 'high': 100.70, 'low': 99.90},
        {'bars_from_entry': -4, 'high': 101.00, 'low': 100.20},
        {'bars_from_entry': -3, 'high': 101.30, 'low': 100.50},  # Potential swing high
        {'bars_from_entry': -2, 'high': 101.10, 'low': 100.40},
        {'bars_from_entry': -1, 'high': 100.90, 'low': 100.20},
        {'bars_from_entry': 0, 'high': 101.00, 'low': 100.30},   # Entry bar
    ]

    print("Fractal Detection Test")
    print("=" * 50)

    # Find all fractals
    highs = find_fractal_highs(test_m5_bars, fractal_length=2)
    lows = find_fractal_lows(test_m5_bars, fractal_length=2)

    print(f"\nFractal Highs found: {len(highs)}")
    for f in highs:
        print(f"  - Price: {f['price']:.2f} at bars_from_entry: {f['bars_from_entry']}")

    print(f"\nFractal Lows found: {len(lows)}")
    for f in lows:
        print(f"  - Price: {f['price']:.2f} at bars_from_entry: {f['bars_from_entry']}")

    # Calculate stops
    long_stop = calculate_fractal_stop_price(test_m5_bars, 'LONG')
    short_stop = calculate_fractal_stop_price(test_m5_bars, 'SHORT')

    print(f"\nLONG stop (fractal low): {long_stop:.2f}" if long_stop else "\nLONG stop: None")
    print(f"SHORT stop (fractal high): {short_stop:.2f}" if short_stop else "SHORT stop: None")
