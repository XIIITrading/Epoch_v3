"""
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
M5 (5-Minute) Structure Detection - Delegated to shared library
XIII Trading LLC
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "03_indicators" / "python"))

from indicator_types import StructureResult
from structure.market_structure import detect_structure, is_structure_healthy

TIMEFRAME = "M5"
TIMEFRAME_MINUTES = 5


def detect_m5_structure(bars, up_to_index=None, fractal_length=None):
    """Detect M5 structure - delegates to shared library."""
    return detect_structure(bars, up_to_index, fractal_length)


def is_m5_healthy(structure, direction):
    """Check if M5 structure supports trade direction."""
    return is_structure_healthy(structure, direction)


__all__ = ["StructureResult", "detect_m5_structure", "is_m5_healthy", "TIMEFRAME", "TIMEFRAME_MINUTES"]
