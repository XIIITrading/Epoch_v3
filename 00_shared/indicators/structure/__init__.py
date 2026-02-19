"""
Epoch Trading System - Market Structure (Canonical)
====================================================

Fractal-based market structure detection.

Usage:
    from shared.indicators.structure import detect_fractals, get_market_structure
    from shared.indicators.structure import calculate_structure_from_bars
"""

from .market_structure import (
    detect_fractals,
    get_swing_points,
    get_market_structure,
    calculate_structure_from_bars,
    get_structure_label,
    is_structure_aligned,
)

__all__ = [
    "detect_fractals",
    "get_swing_points",
    "get_market_structure",
    "calculate_structure_from_bars",
    "get_structure_label",
    "is_structure_aligned",
]
