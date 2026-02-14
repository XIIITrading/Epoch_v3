"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Trade Outcome Classification
XIII Trading LLC
================================================================================

Utilities for classifying trade outcomes and calculating R-multiples.
================================================================================
"""

from typing import Optional


def classify_outcome(pnl_r: float) -> str:
    """Classify trade outcome based on R-multiple."""
    if pnl_r > 0:
        return "WIN"
    elif pnl_r < 0:
        return "LOSS"
    return "BREAKEVEN"


def calculate_r_multiple(
    entry_price: float,
    exit_price: float,
    stop_price: float,
    direction: str
) -> Optional[float]:
    """Calculate R-multiple for a trade."""
    risk = abs(entry_price - stop_price)

    if risk == 0:
        return None

    is_long = direction.upper() == "LONG"

    if is_long:
        pnl = exit_price - entry_price
    else:
        pnl = entry_price - exit_price

    return pnl / risk


def is_winner(pnl_r: float) -> bool:
    """Check if trade is a winner."""
    return pnl_r > 0


def get_trade_type(model: str) -> str:
    """Get trade type (continuation or rejection) from model."""
    if model in ["EPCH1", "EPCH3"]:
        return "continuation"
    elif model in ["EPCH2", "EPCH4"]:
        return "rejection"
    return "unknown"


def get_zone_type(model: str) -> str:
    """Get zone type (primary or secondary) from model."""
    if model in ["EPCH1", "EPCH2"]:
        return "primary"
    elif model in ["EPCH3", "EPCH4"]:
        return "secondary"
    return "unknown"
