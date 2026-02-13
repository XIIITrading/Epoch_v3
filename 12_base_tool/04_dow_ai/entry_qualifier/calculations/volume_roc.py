"""
Volume ROC Calculations
Epoch Trading System v1 - XIII Trading LLC

Calculates Volume Rate of Change vs 20-period average.
Used to confirm momentum/acceleration.
"""
from typing import List, Optional


# Default lookback period for volume average
DEFAULT_LOOKBACK = 20

# Threshold for elevated volume (momentum confirmation)
ELEVATED_THRESHOLD = 30  # 30%

# Threshold for high volume (strong momentum)
HIGH_THRESHOLD = 50  # 50%


def calculate_volume_roc(
    current_volume: float,
    avg_volume: float
) -> float:
    """
    Calculate volume rate of change as percentage.

    Formula: ((current - avg) / avg) * 100

    Args:
        current_volume: Current bar volume
        avg_volume: Average volume over lookback period

    Returns:
        Volume ROC as percentage (e.g., 45.0 for +45%)
    """
    if avg_volume <= 0:
        return 0.0

    return ((current_volume - avg_volume) / avg_volume) * 100


def calculate_volume_average(
    volumes: List[float],
    period: int = DEFAULT_LOOKBACK
) -> Optional[float]:
    """
    Calculate simple moving average of volume.

    Args:
        volumes: List of volume values
        period: Lookback period for average

    Returns:
        Average volume, or None if insufficient data
    """
    if len(volumes) < period:
        return None

    return sum(volumes[-period:]) / period


def is_elevated_volume(volume_roc: float) -> bool:
    """
    Check if volume ROC indicates elevated volume (>=30%).

    Args:
        volume_roc: Volume ROC as percentage

    Returns:
        True if volume is elevated
    """
    return volume_roc >= ELEVATED_THRESHOLD


def is_high_volume(volume_roc: float) -> bool:
    """
    Check if volume ROC indicates high volume (>=50%).

    Args:
        volume_roc: Volume ROC as percentage

    Returns:
        True if volume is high
    """
    return volume_roc >= HIGH_THRESHOLD


def calculate_all_volume_roc(
    bars: List[dict],
    lookback: int = DEFAULT_LOOKBACK
) -> List[dict]:
    """
    Calculate volume ROC for all bars.

    For bars before the lookback period is available, returns None.

    Args:
        bars: List of bar dictionaries with 'volume' or 'v' key
        lookback: Lookback period for average calculation

    Returns:
        List of dicts with 'volume_roc' and 'is_elevated' keys
    """
    results = []
    volumes = []

    for i, bar in enumerate(bars):
        volume = bar.get('volume', bar.get('v', 0))
        volumes.append(volume)

        # Need at least 'lookback' bars to calculate ROC
        # We compare current bar to average of previous 'lookback' bars
        if i < lookback:
            results.append({
                'volume_roc': None,
                'is_elevated': False
            })
        else:
            # Calculate average of previous 'lookback' bars (not including current)
            prev_volumes = volumes[i - lookback:i]
            avg_volume = sum(prev_volumes) / lookback

            volume_roc = calculate_volume_roc(volume, avg_volume)

            results.append({
                'volume_roc': volume_roc,
                'is_elevated': is_elevated_volume(volume_roc)
            })

    return results
