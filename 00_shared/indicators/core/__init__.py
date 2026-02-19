"""
Epoch Trading System - Core Indicators (Canonical)
===================================================

All indicators use numpy core + DataFrame/bar-list wrappers.
Import from here for the canonical implementations.

Usage:
    from shared.indicators.core.volume_delta import volume_delta_df, calculate_bar_delta
    from shared.indicators.core.volume_roc import volume_roc_df, calculate_volume_roc
    from shared.indicators.core.cvd import cvd_df, cvd_slope_df, calculate_cvd_slope
    from shared.indicators.core.atr import atr_df, calculate_atr, calculate_true_range
    from shared.indicators.core.sma import sma_df, calculate_sma, calculate_sma_spread
    from shared.indicators.core.vwap import vwap_df, calculate_vwap
    from shared.indicators.core.candle_range import candle_range_pct_df, calculate_candle_range_pct
"""

# DataFrame wrappers
from .volume_delta import volume_delta_df, rolling_delta_df, cumulative_delta_df
from .volume_roc import volume_roc_df
from .cvd import cvd_df, cvd_slope_df
from .atr import atr_df, atr_pct_df
from .sma import sma_df, ema_df, sma_spread_df
from .vwap import vwap_df
from .candle_range import candle_range_pct_df, candle_range_df, relative_candle_range_df

# Bar-list wrappers
from .volume_delta import calculate_bar_delta, calculate_bar_delta_from_bar, calculate_rolling_delta
from .volume_roc import calculate_volume_roc, classify_volume_roc, is_elevated_volume, is_high_volume
from .cvd import calculate_cvd_slope, classify_cvd_trend
from .atr import calculate_atr, calculate_atr_series, calculate_true_range, get_atr_multiple
from .sma import (
    calculate_sma, calculate_sma_spread, calculate_sma_momentum,
    calculate_sma_spread_pct, get_sma_config_str, get_price_position, is_wide_spread,
)
from .vwap import calculate_vwap, calculate_vwap_metrics
from .candle_range import (
    calculate_candle_range_pct, calculate_candle_range_from_bar,
    is_absorption_zone, get_range_classification, is_candle_range_healthy,
)

__all__ = [
    # DataFrame wrappers
    "volume_delta_df", "rolling_delta_df", "cumulative_delta_df",
    "volume_roc_df",
    "cvd_df", "cvd_slope_df",
    "atr_df", "atr_pct_df",
    "sma_df", "ema_df", "sma_spread_df",
    "vwap_df",
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
]
