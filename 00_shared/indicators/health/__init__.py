"""
Epoch Trading System - Health Scoring
======================================

10-factor health score calculation for trade evaluation.

Usage:
    from shared.indicators.health import calculate_health_score
"""

from .health_score import calculate_health_score, HealthResult

__all__ = [
    "calculate_health_score",
    "HealthResult",
]
