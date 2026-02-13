"""
Epoch Trading System - Market Structure
========================================

Market structure detection and analysis.

Usage:
    from shared.indicators.structure import detect_fractals, get_market_structure
"""

from .market_structure import detect_fractals, get_market_structure, get_structure_label

__all__ = [
    "detect_fractals",
    "get_market_structure",
    "get_structure_label",
]
