"""
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
M15 (15-Minute) Structure Detection - Delegated to shared library
XIII Trading LLC
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "03_indicators" / "python"))

from indicator_types import StructureResult
from structure.market_structure import detect_structure, is_structure_healthy

TIMEFRAME = "M15"
TIMEFRAME_MINUTES = 15


def detect_m15_structure(bars, up_to_index=None, fractal_length=None):
    """Detect M15 structure - delegates to shared library."""
    return detect_structure(bars, up_to_index, fractal_length)


def is_m15_healthy(structure, direction):
    """Check if M15 structure supports trade direction."""
    return is_structure_healthy(structure, direction)


__all__ = ["StructureResult", "detect_m15_structure", "is_m15_healthy", "TIMEFRAME", "TIMEFRAME_MINUTES"]
