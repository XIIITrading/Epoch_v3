"""
Epoch Trading System - Shared Indicator Library
================================================

Centralized indicator calculations used across all Epoch modules.

Core Indicators:
- ATR (Average True Range)
- SMA (Simple Moving Averages)
- VWAP (Volume-Weighted Average Price)
- Volume Delta
- Volume ROC (Rate of Change)
- CVD (Cumulative Volume Delta)
- Candle Range

Market Structure:
- Fractal detection
- Swing detection
- Structure labeling (BULL/BEAR/NEUTRAL)

Health Scoring:
- 10-factor health score
- Threshold management

Usage:
    from shared.indicators.core import sma, vwap, atr, volume_delta
    from shared.indicators.structure import detect_fractals, get_structure
    from shared.indicators.health import calculate_health_score
"""

from .core import sma, vwap, atr, volume_delta, volume_roc, cvd, candle_range
from .structure import detect_fractals, get_market_structure
from .health import calculate_health_score

__all__ = [
    # Core indicators
    "sma",
    "vwap",
    "atr",
    "volume_delta",
    "volume_roc",
    "cvd",
    "candle_range",
    # Structure
    "detect_fractals",
    "get_market_structure",
    # Health
    "calculate_health_score",
]
