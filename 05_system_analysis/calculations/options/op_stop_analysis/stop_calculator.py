"""
Options Stop Price Calculator

Calculates stop prices for each stop type and determines
whether the stop would have been triggered based on MAE.
"""

from typing import Dict, Optional
from decimal import Decimal

from .stop_types import OPTIONS_STOP_TYPES, get_stop_loss_pct


def _safe_float(value, default: float = None) -> Optional[float]:
    """Safely convert value to float."""
    if value is None:
        return default
    try:
        if isinstance(value, Decimal):
            return float(value)
        return float(value)
    except (ValueError, TypeError):
        return default


def calculate_option_stop_price(
    entry_price: float,
    stop_type: str
) -> float:
    """
    Calculate the stop price for an option trade.

    Parameters:
    -----------
    entry_price : float
        Option entry price (e.g., $5.00)
    stop_type : str
        Stop type key (e.g., "stop_25pct")

    Returns:
    --------
    float
        Stop price (e.g., $3.75 for 25% stop on $5.00 entry)
    """
    loss_pct = get_stop_loss_pct(stop_type)
    return entry_price * (1 - loss_pct / 100)


def calculate_all_stop_prices(entry_price: float) -> Dict[str, float]:
    """
    Calculate stop prices for all stop types.

    Returns dict of {stop_type: stop_price}
    """
    return {
        stop_type: calculate_option_stop_price(entry_price, stop_type)
        for stop_type in OPTIONS_STOP_TYPES
    }


def check_stop_hit(
    entry_price: float,
    mae_price: float,
    stop_type: str
) -> bool:
    """
    Check if a stop would have been hit based on MAE.

    Options always go LONG (you buy the option), so adverse movement
    is always the option price going DOWN.

    Parameters:
    -----------
    entry_price : float
        Option entry price
    mae_price : float
        Minimum price reached (max adverse excursion)
    stop_type : str
        Stop type to check

    Returns:
    --------
    bool
        True if stop was hit, False otherwise
    """
    stop_price = calculate_option_stop_price(entry_price, stop_type)

    # Stop is hit if price dropped to or below stop level
    return mae_price <= stop_price


def check_stop_hit_by_pct(
    mae_pct: float,
    stop_type: str
) -> bool:
    """
    Check if a stop would have been hit based on MAE percentage.

    Parameters:
    -----------
    mae_pct : float
        Maximum adverse excursion as percentage (positive value, e.g., 25 means -25%)
    stop_type : str
        Stop type to check

    Returns:
    --------
    bool
        True if stop was hit, False otherwise
    """
    stop_loss_pct = get_stop_loss_pct(stop_type)

    # Stop is hit if MAE% >= stop loss %
    # mae_pct is stored as positive value (e.g., 25 means option dropped 25%)
    return mae_pct >= stop_loss_pct


def calculate_stop_distance_pct(
    entry_price: float,
    stop_type: str
) -> float:
    """
    Calculate stop distance as percentage of entry.
    This is simply the loss_pct for the stop type.
    """
    return get_stop_loss_pct(stop_type)
