"""
================================================================================
EPOCH TRADING SYSTEM - CANONICAL INDICATOR CONFIGURATION
Single source of truth for all indicator parameters.
XIII Trading LLC
================================================================================

All modules MUST import from here. No local overrides.
Changing a value here propagates to every tool in the system.

================================================================================
"""

from dataclasses import dataclass, field


# =============================================================================
# CANDLE RANGE
# =============================================================================
@dataclass(frozen=True)
class CandleRangeConfig:
    """Candle range thresholds (percentage of close)."""
    absorption_threshold: float = 0.12   # Below = absorption zone (SKIP)
    normal_threshold: float = 0.15       # Above = has momentum (TAKE)
    high_threshold: float = 0.20         # Strong signal


# =============================================================================
# SMA (Simple Moving Average)
# =============================================================================
@dataclass(frozen=True)
class SMAConfig:
    """SMA calculation parameters."""
    fast_period: int = 9
    slow_period: int = 21
    momentum_lookback: int = 10
    widening_threshold: float = 1.1      # ratio > this = WIDENING
    narrowing_threshold: float = 0.9     # ratio < this = NARROWING
    wide_spread_threshold: float = 0.15  # spread pct considered "wide"


# =============================================================================
# VOLUME ROC (Rate of Change)
# =============================================================================
@dataclass(frozen=True)
class VolumeROCConfig:
    """Volume ROC parameters. Output is PERCENTAGE (0% = average)."""
    baseline_period: int = 20
    elevated_threshold: float = 30.0     # >= 30% = elevated (momentum confirmation)
    high_threshold: float = 50.0         # >= 50% = high (strong momentum)
    above_avg_threshold: float = 30.0    # classification boundary
    below_avg_threshold: float = -20.0   # classification boundary


# =============================================================================
# VOLUME DELTA
# =============================================================================
@dataclass(frozen=True)
class VolumeDeltaConfig:
    """Volume delta parameters. Uses BAR POSITION method."""
    rolling_period: int = 5
    magnitude_threshold: float = 100_000  # high magnitude for classification


# =============================================================================
# CVD (Cumulative Volume Delta)
# =============================================================================
@dataclass(frozen=True)
class CVDConfig:
    """CVD slope parameters. Uses LINEAR REGRESSION, normalized, clamped [-2, 2]."""
    window: int = 15
    rising_threshold: float = 0.1
    falling_threshold: float = -0.1
    clamp_min: float = -2.0
    clamp_max: float = 2.0


# =============================================================================
# ATR (Average True Range)
# =============================================================================
@dataclass(frozen=True)
class ATRConfig:
    """ATR parameters. Uses TRUE RANGE method everywhere."""
    period: int = 14


# =============================================================================
# MARKET STRUCTURE
# =============================================================================
@dataclass(frozen=True)
class StructureConfig:
    """Fractal-based market structure parameters."""
    fractal_length: int = 5  # bars each side for fractal detection


# =============================================================================
# TIMEZONE
# =============================================================================
DISPLAY_TIMEZONE = "America/New_York"


# =============================================================================
# MASTER CONFIG - single instance used everywhere
# =============================================================================
@dataclass(frozen=True)
class IndicatorConfig:
    """Master configuration holding all indicator parameters."""
    candle_range: CandleRangeConfig = field(default_factory=CandleRangeConfig)
    sma: SMAConfig = field(default_factory=SMAConfig)
    volume_roc: VolumeROCConfig = field(default_factory=VolumeROCConfig)
    volume_delta: VolumeDeltaConfig = field(default_factory=VolumeDeltaConfig)
    cvd: CVDConfig = field(default_factory=CVDConfig)
    atr: ATRConfig = field(default_factory=ATRConfig)
    structure: StructureConfig = field(default_factory=StructureConfig)


# Singleton - import this everywhere
CONFIG = IndicatorConfig()
