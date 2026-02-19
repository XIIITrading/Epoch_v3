"""
================================================================================
EPOCH TRADING SYSTEM - CANONICAL INDICATOR RESULT TYPES
Unified dataclasses for all indicator outputs.
XIII Trading LLC
================================================================================

All modules MUST use these types for consistency.

================================================================================
"""

from dataclasses import dataclass
from typing import List, Optional


# =============================================================================
# VOLUME DELTA
# =============================================================================
@dataclass
class VolumeDeltaResult:
    """Single bar volume delta result (bar position method)."""
    bar_delta: float
    bar_position: float      # 0.0 (close at low) to 1.0 (close at high)
    delta_multiplier: float   # -1.0 to +1.0


@dataclass
class RollingDeltaResult:
    """Rolling volume delta over N bars."""
    rolling_delta: float
    signal: str   # "Bullish", "Bearish", "Neutral"
    bar_count: int


# =============================================================================
# VOLUME ROC
# =============================================================================
@dataclass
class VolumeROCResult:
    """Volume Rate of Change result (percentage format)."""
    roc: Optional[float]       # percentage (0% = average, 30% = elevated)
    signal: str                # "Above Avg", "Below Avg", "Average"
    current_volume: int
    baseline_avg: Optional[float]


# =============================================================================
# CVD
# =============================================================================
@dataclass
class CVDResult:
    """CVD slope result (linear regression, normalized, clamped)."""
    slope: float               # normalized slope, clamped [-2, 2]
    trend: str                 # "Rising", "Falling", "Flat"
    cvd_values: List[float]
    window_size: int


# =============================================================================
# ATR
# =============================================================================
@dataclass
class ATRResult:
    """Average True Range result."""
    atr: Optional[float]
    true_range: Optional[float]   # last bar's true range
    period: int


# =============================================================================
# SMA
# =============================================================================
@dataclass
class SMAResult:
    """SMA spread calculation result."""
    sma9: Optional[float]
    sma21: Optional[float]
    spread: Optional[float]
    alignment: Optional[str]       # "BULLISH", "BEARISH"
    cross_estimate: Optional[float]


@dataclass
class SMAMomentumResult:
    """SMA spread momentum result."""
    spread_now: Optional[float]
    spread_prev: Optional[float]
    momentum: str                  # "WIDENING", "NARROWING", "FLAT"
    ratio: Optional[float]


# =============================================================================
# VWAP
# =============================================================================
@dataclass
class VWAPResult:
    """VWAP calculation result."""
    vwap: Optional[float]
    price_diff: Optional[float]
    price_pct: Optional[float]
    side: Optional[str]            # "ABOVE", "BELOW", "AT"


# =============================================================================
# CANDLE RANGE
# =============================================================================
@dataclass
class CandleRangeResult:
    """Candle range calculation result."""
    candle_range_pct: float
    classification: str            # "ABSORPTION", "LOW", "NORMAL", "HIGH"
    is_absorption: bool
    has_momentum: bool             # True if >= normal_threshold (0.15%)


# =============================================================================
# MARKET STRUCTURE
# =============================================================================
@dataclass
class StructureResult:
    """Market structure detection result."""
    direction: int                 # 1 = BULL, -1 = BEAR, 0 = NEUTRAL
    label: str                     # "BULL", "BEAR", "NEUTRAL"
    last_swing_high: Optional[float]
    last_swing_low: Optional[float]
    higher_highs: bool
    higher_lows: bool
