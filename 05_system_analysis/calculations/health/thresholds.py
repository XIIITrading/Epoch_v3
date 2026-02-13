"""
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Health Score Thresholds - Delegated to shared library
XIII Trading LLC
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "03_indicators" / "python"))

from health.thresholds import THRESHOLDS, get_health_label, get_health_color

__all__ = ["THRESHOLDS", "get_health_label", "get_health_color"]
