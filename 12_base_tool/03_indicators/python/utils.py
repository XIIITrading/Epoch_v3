"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 03: SHARED INDICATORS
Utility Functions
XIII Trading LLC
================================================================================

Common utility functions used across indicator calculations.

================================================================================
"""

from typing import List, Optional, Union, Any


def safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    """
    Safely convert a value to float.

    Args:
        value: Value to convert
        default: Default value if conversion fails

    Returns:
        Float value or default
    """
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """
    Safely convert a value to int.

    Args:
        value: Value to convert
        default: Default value if conversion fails

    Returns:
        Int value or default
    """
    if value is None:
        return default
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default


def calculate_linear_slope(values: List[float]) -> float:
    """
    Calculate the slope of a linear regression line through values.

    Uses the least squares method:
    slope = sum((x - x_mean) * (y - y_mean)) / sum((x - x_mean)^2)

    Args:
        values: List of y values (x is assumed to be 0, 1, 2, ...)

    Returns:
        Slope of the regression line
    """
    n = len(values)
    if n < 2:
        return 0.0

    x_mean = (n - 1) / 2
    y_mean = sum(values) / n

    numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
    denominator = sum((i - x_mean) ** 2 for i in range(n))

    if denominator == 0:
        return 0.0

    return numerator / denominator


def get_bar_value(bar: Union[dict, Any], *keys: str, default: Any = None) -> Any:
    """
    Get a value from a bar using multiple possible key names.

    Supports both dict-style access and attribute access.
    Tries each key in order until one succeeds.

    Args:
        bar: Bar data (dict or object with attributes)
        *keys: Key names to try in order
        default: Default value if no key found

    Returns:
        Value from bar or default

    Example:
        >>> get_bar_value(bar, "high_price", "high")  # tries high_price first, then high
    """
    for key in keys:
        # Try dict-style access
        if isinstance(bar, dict):
            if key in bar:
                return bar[key]
        else:
            # Try attribute access
            if hasattr(bar, key):
                return getattr(bar, key)
    return default


def get_high(bar: Union[dict, Any], default: Optional[float] = None) -> Optional[float]:
    """Get high price from bar."""
    value = get_bar_value(bar, "high_price", "high", default=default)
    return safe_float(value, default)


def get_low(bar: Union[dict, Any], default: Optional[float] = None) -> Optional[float]:
    """Get low price from bar."""
    value = get_bar_value(bar, "low_price", "low", default=default)
    return safe_float(value, default)


def get_open(bar: Union[dict, Any], default: Optional[float] = None) -> Optional[float]:
    """Get open price from bar."""
    value = get_bar_value(bar, "open_price", "open", default=default)
    return safe_float(value, default)


def get_close(bar: Union[dict, Any], default: Optional[float] = None) -> Optional[float]:
    """Get close price from bar."""
    value = get_bar_value(bar, "close_price", "close", default=default)
    return safe_float(value, default)


def get_volume(bar: Union[dict, Any], default: int = 0) -> int:
    """Get volume from bar."""
    value = get_bar_value(bar, "volume", default=default)
    return safe_int(value, default)
