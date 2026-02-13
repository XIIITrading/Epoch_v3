"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 03: SHARED INDICATORS
Python Implementation Library
XIII Trading LLC
================================================================================

Centralized indicator calculations shared across all Epoch modules.
Supports both pandas DataFrame and List[Dict] input formats.

Usage:
    from indicators.python import calculate_vwap, calculate_sma, calculate_health_score
    from indicators.python.core import vwap, sma, volume_delta, volume_roc, cvd
    from indicators.python.structure import market_structure
    from indicators.python.health import health_score

================================================================================
"""

from .config import (
    SMA_CONFIG,
    VOLUME_ROC_CONFIG,
    VOLUME_DELTA_CONFIG,
    CVD_CONFIG,
    STRUCTURE_CONFIG,
    HEALTH_CONFIG,
)

from .indicator_types import (
    VWAPResult,
    SMAResult,
    SMAMomentumResult,
    VolumeROCResult,
    VolumeDeltaResult,
    RollingDeltaResult,
    CVDResult,
    StructureResult,
    HealthScoreResult,
)

from .core.vwap import calculate_vwap, calculate_vwap_metrics, is_vwap_healthy
from .core.sma import calculate_sma, calculate_sma_spread, calculate_sma_momentum, is_sma_alignment_healthy, is_sma_momentum_healthy
from .core.volume_delta import calculate_bar_delta, calculate_rolling_delta, is_volume_delta_healthy
from .core.volume_roc import calculate_volume_roc, classify_volume_roc, is_volume_roc_healthy
from .core.cvd import calculate_cvd_slope, classify_cvd_trend, is_cvd_healthy

from .structure.market_structure import detect_structure, is_structure_healthy
from .health.health_score import calculate_health_score, calculate_health_from_bar

__version__ = "1.0.0"

__all__ = [
    # Config
    "SMA_CONFIG",
    "VOLUME_ROC_CONFIG",
    "VOLUME_DELTA_CONFIG",
    "CVD_CONFIG",
    "STRUCTURE_CONFIG",
    "HEALTH_CONFIG",
    # Types
    "VWAPResult",
    "SMAResult",
    "SMAMomentumResult",
    "VolumeROCResult",
    "VolumeDeltaResult",
    "RollingDeltaResult",
    "CVDResult",
    "StructureResult",
    "HealthScoreResult",
    # VWAP
    "calculate_vwap",
    "calculate_vwap_metrics",
    "is_vwap_healthy",
    # SMA
    "calculate_sma",
    "calculate_sma_spread",
    "calculate_sma_momentum",
    "is_sma_alignment_healthy",
    "is_sma_momentum_healthy",
    # Volume Delta
    "calculate_bar_delta",
    "calculate_rolling_delta",
    "is_volume_delta_healthy",
    # Volume ROC
    "calculate_volume_roc",
    "classify_volume_roc",
    "is_volume_roc_healthy",
    # CVD
    "calculate_cvd_slope",
    "classify_cvd_trend",
    "is_cvd_healthy",
    # Structure
    "detect_structure",
    "is_structure_healthy",
    # Health
    "calculate_health_score",
    "calculate_health_from_bar",
]
