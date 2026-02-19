"""
================================================================================
EPOCH TRADING SYSTEM - Canonical Indicator Library
================================================================================

Single source of truth for all indicator calculations.
Every module in the system imports from here.

Architecture:
    - config.py    : Single canonical configuration (frozen dataclasses)
    - types.py     : All result dataclasses
    - _utils.py    : Bar accessor helpers + math utilities
    - core/        : 7 indicator modules (numpy core + DataFrame/bar-list wrappers)
    - structure/   : Fractal-based market structure detection

Algorithms (canonical, per SWH-6):
    - Volume Delta  : Bar position method
    - Volume ROC    : Percentage format (0% = average)
    - CVD Slope     : Linear regression, normalized, clamped [-2, 2]
    - ATR           : True Range, SMA smoothing
    - SMA           : 9/21 spread with momentum detection
    - VWAP          : Cumulative TP*V / V
    - Candle Range  : (high-low)/close * 100
    - Structure     : Fractal-based (HH+HL=BULL, LH+LL=BEAR)

Usage:
    from shared.indicators.config import CONFIG
    from shared.indicators.types import VolumeDeltaResult, ATRResult, ...
    from shared.indicators.core.volume_delta import volume_delta_df, calculate_bar_delta
    from shared.indicators.core.atr import atr_df, calculate_atr
    from shared.indicators.structure import get_market_structure

================================================================================
"""

# Configuration
from .config import CONFIG

# Result types
from .types import (
    VolumeDeltaResult,
    RollingDeltaResult,
    VolumeROCResult,
    CVDResult,
    ATRResult,
    SMAResult,
    SMAMomentumResult,
    VWAPResult,
    CandleRangeResult,
    StructureResult,
)

# Core indicators (most common imports)
from .core import (
    # DataFrame wrappers
    volume_delta_df, rolling_delta_df, cumulative_delta_df,
    volume_roc_df,
    cvd_df, cvd_slope_df,
    atr_df, atr_pct_df,
    sma_df, ema_df, sma_spread_df,
    vwap_df,
    candle_range_pct_df, candle_range_df, relative_candle_range_df,
    # Bar-list wrappers
    calculate_bar_delta, calculate_bar_delta_from_bar, calculate_rolling_delta,
    calculate_volume_roc, classify_volume_roc, is_elevated_volume, is_high_volume,
    calculate_cvd_slope, classify_cvd_trend,
    calculate_atr, calculate_atr_series, calculate_true_range, get_atr_multiple,
    calculate_sma, calculate_sma_spread, calculate_sma_momentum,
    calculate_sma_spread_pct, get_sma_config_str, get_price_position, is_wide_spread,
    calculate_vwap, calculate_vwap_metrics,
    calculate_candle_range_pct, calculate_candle_range_from_bar,
    is_absorption_zone, get_range_classification, is_candle_range_healthy,
)

# Structure
from .structure import (
    detect_fractals,
    get_swing_points,
    get_market_structure,
    calculate_structure_from_bars,
    get_structure_label,
    is_structure_aligned,
)

__all__ = [
    "CONFIG",
    # Types
    "VolumeDeltaResult", "RollingDeltaResult", "VolumeROCResult", "CVDResult",
    "ATRResult", "SMAResult", "SMAMomentumResult", "VWAPResult",
    "CandleRangeResult", "StructureResult",
    # DataFrame wrappers
    "volume_delta_df", "rolling_delta_df", "cumulative_delta_df",
    "volume_roc_df", "cvd_df", "cvd_slope_df",
    "atr_df", "atr_pct_df", "sma_df", "ema_df", "sma_spread_df", "vwap_df",
    "candle_range_pct_df", "candle_range_df", "relative_candle_range_df",
    # Bar-list wrappers
    "calculate_bar_delta", "calculate_bar_delta_from_bar", "calculate_rolling_delta",
    "calculate_volume_roc", "classify_volume_roc", "is_elevated_volume", "is_high_volume",
    "calculate_cvd_slope", "classify_cvd_trend",
    "calculate_atr", "calculate_atr_series", "calculate_true_range", "get_atr_multiple",
    "calculate_sma", "calculate_sma_spread", "calculate_sma_momentum",
    "calculate_sma_spread_pct", "get_sma_config_str", "get_price_position", "is_wide_spread",
    "calculate_vwap", "calculate_vwap_metrics",
    "calculate_candle_range_pct", "calculate_candle_range_from_bar",
    "is_absorption_zone", "get_range_classification", "is_candle_range_healthy",
    # Structure
    "detect_fractals", "get_swing_points", "get_market_structure",
    "calculate_structure_from_bars", "get_structure_label", "is_structure_aligned",
]
