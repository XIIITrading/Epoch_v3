"""
================================================================================
EPOCH TRADING SYSTEM - INDICATOR UTILITIES
Bar accessor helpers and math utilities.
XIII Trading LLC
================================================================================

Provides a universal interface for extracting OHLCV values from:
- dict-style bars ({"high": 100.0, ...})
- object-style bars (bar.high_price)
- pandas DataFrames

================================================================================
"""

import numpy as np
from typing import Any, Optional, Union


# =============================================================================
# SAFE TYPE CONVERSION
# =============================================================================

def safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    """Safely convert a value to float."""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """Safely convert a value to int."""
    if value is None:
        return default
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default


# =============================================================================
# BAR VALUE ACCESSORS
# =============================================================================

def get_bar_value(bar: Union[dict, Any], *keys: str, default: Any = None) -> Any:
    """
    Get a value from a bar using multiple possible key names.
    Supports dict-style and attribute-style access.
    Tries each key in order until one succeeds.
    """
    for key in keys:
        if isinstance(bar, dict):
            if key in bar:
                return bar[key]
        else:
            if hasattr(bar, key):
                return getattr(bar, key)
    return default


def get_open(bar: Union[dict, Any], default: Optional[float] = None) -> Optional[float]:
    """Get open price from bar."""
    return safe_float(get_bar_value(bar, "open_price", "open", default=default), default)


def get_high(bar: Union[dict, Any], default: Optional[float] = None) -> Optional[float]:
    """Get high price from bar."""
    return safe_float(get_bar_value(bar, "high_price", "high", default=default), default)


def get_low(bar: Union[dict, Any], default: Optional[float] = None) -> Optional[float]:
    """Get low price from bar."""
    return safe_float(get_bar_value(bar, "low_price", "low", default=default), default)


def get_close(bar: Union[dict, Any], default: Optional[float] = None) -> Optional[float]:
    """Get close price from bar."""
    return safe_float(get_bar_value(bar, "close_price", "close", default=default), default)


def get_volume(bar: Union[dict, Any], default: int = 0) -> int:
    """Get volume from bar."""
    return safe_int(get_bar_value(bar, "volume", default=default), default)


# =============================================================================
# BAR LIST -> NUMPY ARRAY EXTRACTION
# =============================================================================

def bars_to_arrays(bars, up_to_index=None):
    """
    Extract OHLCV numpy arrays from a list of bar dicts/objects.

    Args:
        bars: List of bar data (dict or object)
        up_to_index: Extract up to this index (inclusive). None = all.

    Returns:
        Tuple of (open, high, low, close, volume) as numpy arrays
    """
    end = (up_to_index + 1) if up_to_index is not None else len(bars)
    end = min(end, len(bars))

    opens = np.empty(end, dtype=np.float64)
    highs = np.empty(end, dtype=np.float64)
    lows = np.empty(end, dtype=np.float64)
    closes = np.empty(end, dtype=np.float64)
    volumes = np.empty(end, dtype=np.float64)

    for i in range(end):
        opens[i] = get_open(bars[i], 0.0)
        highs[i] = get_high(bars[i], 0.0)
        lows[i] = get_low(bars[i], 0.0)
        closes[i] = get_close(bars[i], 0.0)
        volumes[i] = get_volume(bars[i], 0)

    return opens, highs, lows, closes, volumes


# =============================================================================
# MATH UTILITIES
# =============================================================================

def linear_regression_slope(values: np.ndarray) -> float:
    """
    Calculate the slope of a linear regression line.

    Uses least squares: slope = sum((x - x_mean)(y - y_mean)) / sum((x - x_mean)^2)
    where x = [0, 1, 2, ...].

    Args:
        values: numpy array of y values

    Returns:
        Slope of the regression line
    """
    n = len(values)
    if n < 2:
        return 0.0

    x = np.arange(n, dtype=np.float64)
    x_mean = x.mean()
    y_mean = values.mean()

    numerator = np.sum((x - x_mean) * (values - y_mean))
    denominator = np.sum((x - x_mean) ** 2)

    if denominator == 0:
        return 0.0

    return float(numerator / denominator)
