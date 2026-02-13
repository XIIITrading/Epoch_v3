"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 03: SHARED INDICATORS
Health Score Calculations
XIII Trading LLC
================================================================================

Health score modules:
- thresholds: Health factor thresholds and labels
- health_score: 10-factor DOW_AI health score calculation

================================================================================
"""

from .thresholds import THRESHOLDS, get_health_label
from .health_score import calculate_health_score, calculate_health_from_bar

__all__ = [
    "THRESHOLDS",
    "get_health_label",
    "calculate_health_score",
    "calculate_health_from_bar",
]
