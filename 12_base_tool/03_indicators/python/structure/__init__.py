"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 03: SHARED INDICATORS
Market Structure Detection
XIII Trading LLC
================================================================================

Structure detection modules:
- swing_detection: Fractal-based swing high/low detection
- market_structure: BOS/ChoCH, direction, strong/weak levels

Detection Methods:
- detect_structure_simple: EPCH v1.0 half-bar comparison (reference algorithm)
- detect_h1_structure: Convenience function for H1 structure
- detect_structure: Advanced fractal-based detection with confidence

================================================================================
"""

from .swing_detection import find_swing_highs, find_swing_lows
from .market_structure import (
    detect_structure,
    detect_structure_simple,
    detect_h1_structure,
    is_structure_healthy,
    is_structure_neutral,
)

__all__ = [
    "find_swing_highs",
    "find_swing_lows",
    # Advanced fractal method
    "detect_structure",
    # EPCH v1.0 reference methods
    "detect_structure_simple",
    "detect_h1_structure",
    "is_structure_healthy",
    "is_structure_neutral",
]
