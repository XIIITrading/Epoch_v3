"""
Volume Delta Calculations
Epoch Trading System v1 - XIII Trading LLC

Calculates volume delta (buying vs selling pressure) from OHLCV bar data.
"""
from typing import List, Optional


def calculate_bar_delta(
    open_price: float,
    high: float,
    low: float,
    close: float,
    volume: float
) -> float:
    """
    Estimate volume delta for a single bar using bar position method.

    The bar position method estimates buying/selling pressure based on
    where the close falls within the bar's range:
    - Close at high = +1 (all buying)
    - Close at low = -1 (all selling)
    - Close at midpoint = 0 (neutral)

    Args:
        open_price: Bar open price
        high: Bar high price
        low: Bar low price
        close: Bar close price
        volume: Bar volume

    Returns:
        Estimated net volume (positive = buying, negative = selling)
    """
    bar_range = high - low

    if bar_range == 0:
        return 0.0

    # Calculate position: -1 to +1 based on where close is in range
    position = (2 * (close - low) / bar_range) - 1

    return position * volume


def calculate_rolling_delta(
    raw_deltas: List[float],
    period: int = 5
) -> Optional[float]:
    """
    Calculate rolling sum of bar deltas.

    Args:
        raw_deltas: List of raw volume delta values
        period: Number of bars for rolling sum

    Returns:
        Sum of last N bar deltas, or None if insufficient data
    """
    if len(raw_deltas) < period:
        return None

    return sum(raw_deltas[-period:])


def calculate_all_deltas(
    bars: List[dict],
    roll_period: int = 5
) -> List[dict]:
    """
    Calculate raw and rolling deltas for all bars.

    Args:
        bars: List of bar dictionaries with o, h, l, c, v keys
        roll_period: Period for rolling delta calculation

    Returns:
        List of dicts with 'raw_delta' and 'roll_delta' keys
    """
    results = []
    raw_deltas = []

    for bar in bars:
        # Calculate raw delta for this bar
        raw_delta = calculate_bar_delta(
            open_price=bar.get('open', bar.get('o', 0)),
            high=bar.get('high', bar.get('h', 0)),
            low=bar.get('low', bar.get('l', 0)),
            close=bar.get('close', bar.get('c', 0)),
            volume=bar.get('volume', bar.get('v', 0))
        )
        raw_deltas.append(raw_delta)

        # Calculate rolling delta
        roll_delta = calculate_rolling_delta(raw_deltas, roll_period)

        results.append({
            'raw_delta': raw_delta,
            'roll_delta': roll_delta
        })

    return results
