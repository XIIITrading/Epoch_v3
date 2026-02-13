"""
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Health Score Calculation - Delegated to shared library
XIII Trading LLC
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "03_indicators" / "python"))

from indicator_types import HealthScoreResult
from health.health_score import calculate_health_score, calculate_health_from_bar

__all__ = ["HealthScoreResult", "calculate_health_score", "calculate_health_from_bar"]
