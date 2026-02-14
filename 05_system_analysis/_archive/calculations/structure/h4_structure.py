"""
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
H4 (4-Hour) Structure Detection - Delegated to shared library
XIII Trading LLC
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "03_indicators" / "python"))

from indicator_types import StructureResult
from structure.market_structure import detect_structure, is_structure_healthy

TIMEFRAME = "H4"
TIMEFRAME_MINUTES = 240


def detect_h4_structure(bars, up_to_index=None, fractal_length=None):
    """Detect H4 structure - delegates to shared library."""
    return detect_structure(bars, up_to_index, fractal_length)


def is_h4_healthy(structure, direction):
    """Check if H4 structure supports trade direction."""
    return is_structure_healthy(structure, direction)


__all__ = ["StructureResult", "detect_h4_structure", "is_h4_healthy", "TIMEFRAME", "TIMEFRAME_MINUTES"]
