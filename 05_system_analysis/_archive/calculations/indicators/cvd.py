"""
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
CVD Slope Calculation - Delegated to shared library
XIII Trading LLC
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "03_indicators" / "python"))

from indicator_types import CVDResult
from core.cvd import calculate_cvd_slope, classify_cvd_trend, is_cvd_healthy

__all__ = ["CVDResult", "calculate_cvd_slope", "classify_cvd_trend", "is_cvd_healthy"]
