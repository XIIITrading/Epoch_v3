"""
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
H1 (1-Hour) Structure Detection - Delegated to shared library
XIII Trading LLC
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "03_indicators" / "python"))

from indicator_types import StructureResult
from structure.market_structure import detect_structure, is_structure_healthy

TIMEFRAME = "H1"
TIMEFRAME_MINUTES = 60


def detect_h1_structure(bars, up_to_index=None, fractal_length=None):
    """Detect H1 structure - delegates to shared library."""
    return detect_structure(bars, up_to_index, fractal_length)


def is_h1_healthy(structure, direction):
    """Check if H1 structure supports trade direction."""
    return is_structure_healthy(structure, direction)


__all__ = ["StructureResult", "detect_h1_structure", "is_h1_healthy", "TIMEFRAME", "TIMEFRAME_MINUTES"]
