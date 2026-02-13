"""
Epoch Trading System - Indicator Analysis
Health score calculation modules.
"""

from .thresholds import THRESHOLDS, get_health_label
from .health_score import calculate_health_score, calculate_health_from_bar, HealthScoreResult
