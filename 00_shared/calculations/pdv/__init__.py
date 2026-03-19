"""
Prior Day Value (PDV) Calculation Module
=========================================

Calculates prior day volume profile levels (POC, VAH, VAL) and determines
value alignment relative to current price and market structure direction.

Usage:
    from shared.calculations.pdv import calculate_pdv

    result = calculate_pdv("AAPL", date(2026, 3, 14))
"""

from .calculator import calculate_pdv, PDVResult, Alignment

__all__ = ["calculate_pdv", "PDVResult", "Alignment"]
