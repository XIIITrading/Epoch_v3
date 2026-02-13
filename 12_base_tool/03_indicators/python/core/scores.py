"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 03: SHARED INDICATORS
Composite Score Calculations (LONG and SHORT)
XIII Trading LLC
================================================================================

Calculates LONG and SHORT composite scores based on EPCH Indicators v1.0 spec.

LONG Score (0-7):
    - Candle Range >= 0.15%: +2 points
    - H1 NEUTRAL: +2 points
    - Vol ROC >= 30%: +1 point
    - High magnitude Vol Delta (>100k): +1 point
    - Wide SMA spread (>= 0.15%): +1 point

SHORT Score (0-7) - Note paradoxes:
    - Candle Range >= 0.15%: +2 points
    - H1 NEUTRAL: +2 points
    - Vol ROC >= 30%: +1 point
    - Vol Delta POSITIVE (paradox - exhausted buyers): +1 point
    - SMA BULLISH (paradox - catching failed rally): +1 point

================================================================================
"""

from typing import Optional, Any
from dataclasses import dataclass


# =============================================================================
# THRESHOLDS (from reference implementation)
# =============================================================================

# Candle range threshold for score contribution
CANDLE_RANGE_THRESHOLD = 0.15  # 0.15%

# Volume ROC threshold for elevated volume
VOLUME_ROC_THRESHOLD = 30  # 30%

# Volume delta magnitude threshold
VOLUME_DELTA_MAGNITUDE_THRESHOLD = 100000  # 100k

# SMA spread threshold for wide spread
SMA_SPREAD_THRESHOLD = 0.15  # 0.15%

# H1 Structure value that earns points
H1_NEUTRAL_VALUES = ['NEUT', 'NEUTRAL']


# =============================================================================
# RESULT DATACLASS
# =============================================================================

@dataclass
class ScoreResult:
    """Composite score calculation result."""
    long_score: int
    short_score: int
    max_score: int = 7

    # Component breakdowns
    long_candle_points: int = 0
    long_h1_points: int = 0
    long_vol_roc_points: int = 0
    long_vol_delta_points: int = 0
    long_sma_points: int = 0

    short_candle_points: int = 0
    short_h1_points: int = 0
    short_vol_roc_points: int = 0
    short_vol_delta_points: int = 0
    short_sma_points: int = 0


# =============================================================================
# CORE CALCULATIONS
# =============================================================================

def calculate_long_score(
    candle_range_pct: Optional[float],
    volume_delta: Optional[float],
    volume_roc: Optional[float],
    sma_config: Any,
    sma_spread_pct: Optional[float],
    h1_structure: Any
) -> int:
    """
    Calculate LONG composite score (0-7).

    Scoring (per EPCH Indicators v1.0 spec):
    - Candle Range >= 0.15%: +2 points
    - H1 NEUTRAL: +2 points
    - Vol ROC >= 30%: +1 point
    - High magnitude Vol Delta: +1 point
    - Wide SMA spread (>= 0.15%): +1 point

    Args:
        candle_range_pct: Candle range as percentage
        volume_delta: Rolling volume delta value
        volume_roc: Volume ROC as percentage
        sma_config: SMAConfig enum or string
        sma_spread_pct: SMA spread as percentage
        h1_structure: MarketStructure enum or string

    Returns:
        Integer score from 0-7
    """
    score = 0

    # Candle Range >= 0.15%: +2
    if candle_range_pct is not None and candle_range_pct >= CANDLE_RANGE_THRESHOLD:
        score += 2

    # H1 NEUTRAL: +2
    if h1_structure is not None:
        h1_value = h1_structure.value if hasattr(h1_structure, 'value') else str(h1_structure)
        if h1_value in H1_NEUTRAL_VALUES:
            score += 2

    # Vol ROC >= 30%: +1
    if volume_roc is not None and volume_roc >= VOLUME_ROC_THRESHOLD:
        score += 1

    # High magnitude Vol Delta: +1
    # For LONG, we look for high magnitude (either direction)
    if volume_delta is not None and abs(volume_delta) > VOLUME_DELTA_MAGNITUDE_THRESHOLD:
        score += 1

    # Wide SMA spread (>= 0.15%): +1
    if sma_spread_pct is not None and sma_spread_pct >= SMA_SPREAD_THRESHOLD:
        score += 1

    return score


def calculate_short_score(
    candle_range_pct: Optional[float],
    volume_delta: Optional[float],
    volume_roc: Optional[float],
    sma_config: Any,
    sma_spread_pct: Optional[float],
    h1_structure: Any
) -> int:
    """
    Calculate SHORT composite score (0-7).

    Scoring (per EPCH Indicators v1.0 spec - note paradoxes):
    - Candle Range >= 0.15%: +2 points
    - H1 NEUTRAL: +2 points
    - Vol ROC >= 30%: +1 point
    - Vol Delta POSITIVE (paradox - exhausted buyers): +1 point
    - SMA BULLISH (paradox - catching failed rally): +1 point

    Args:
        candle_range_pct: Candle range as percentage
        volume_delta: Rolling volume delta value
        volume_roc: Volume ROC as percentage
        sma_config: SMAConfig enum or string
        sma_spread_pct: SMA spread as percentage
        h1_structure: MarketStructure enum or string

    Returns:
        Integer score from 0-7
    """
    score = 0

    # Candle Range >= 0.15%: +2
    if candle_range_pct is not None and candle_range_pct >= CANDLE_RANGE_THRESHOLD:
        score += 2

    # H1 NEUTRAL: +2
    if h1_structure is not None:
        h1_value = h1_structure.value if hasattr(h1_structure, 'value') else str(h1_structure)
        if h1_value in H1_NEUTRAL_VALUES:
            score += 2

    # Vol ROC >= 30%: +1
    if volume_roc is not None and volume_roc >= VOLUME_ROC_THRESHOLD:
        score += 1

    # Vol Delta POSITIVE (paradox): +1
    # For SHORT, positive delta indicates exhausted buyers
    if volume_delta is not None and volume_delta > 0:
        score += 1

    # SMA BULLISH (paradox): +1
    # For SHORT, bullish SMA config indicates we're catching a failed rally
    if sma_config is not None:
        sma_value = sma_config.value if hasattr(sma_config, 'value') else str(sma_config)
        if sma_value in ['BULL', 'BULLISH']:
            score += 1

    return score


def calculate_scores(
    candle_range_pct: Optional[float],
    volume_delta: Optional[float],
    volume_roc: Optional[float],
    sma_config: Any,
    sma_spread_pct: Optional[float],
    h1_structure: Any
) -> ScoreResult:
    """
    Calculate both LONG and SHORT composite scores with component breakdown.

    Args:
        candle_range_pct: Candle range as percentage
        volume_delta: Rolling volume delta value
        volume_roc: Volume ROC as percentage
        sma_config: SMAConfig enum or string
        sma_spread_pct: SMA spread as percentage
        h1_structure: MarketStructure enum or string

    Returns:
        ScoreResult with long_score, short_score, and component breakdowns
    """
    result = ScoreResult(
        long_score=0,
        short_score=0
    )

    # LONG score components
    # Candle Range >= 0.15%: +2
    if candle_range_pct is not None and candle_range_pct >= CANDLE_RANGE_THRESHOLD:
        result.long_candle_points = 2
        result.short_candle_points = 2

    # H1 NEUTRAL: +2
    if h1_structure is not None:
        h1_value = h1_structure.value if hasattr(h1_structure, 'value') else str(h1_structure)
        if h1_value in H1_NEUTRAL_VALUES:
            result.long_h1_points = 2
            result.short_h1_points = 2

    # Vol ROC >= 30%: +1
    if volume_roc is not None and volume_roc >= VOLUME_ROC_THRESHOLD:
        result.long_vol_roc_points = 1
        result.short_vol_roc_points = 1

    # LONG: High magnitude Vol Delta: +1
    if volume_delta is not None and abs(volume_delta) > VOLUME_DELTA_MAGNITUDE_THRESHOLD:
        result.long_vol_delta_points = 1

    # SHORT: Vol Delta POSITIVE (paradox): +1
    if volume_delta is not None and volume_delta > 0:
        result.short_vol_delta_points = 1

    # LONG: Wide SMA spread (>= 0.15%): +1
    if sma_spread_pct is not None and sma_spread_pct >= SMA_SPREAD_THRESHOLD:
        result.long_sma_points = 1

    # SHORT: SMA BULLISH (paradox): +1
    if sma_config is not None:
        sma_value = sma_config.value if hasattr(sma_config, 'value') else str(sma_config)
        if sma_value in ['BULL', 'BULLISH']:
            result.short_sma_points = 1

    # Sum up scores
    result.long_score = (
        result.long_candle_points +
        result.long_h1_points +
        result.long_vol_roc_points +
        result.long_vol_delta_points +
        result.long_sma_points
    )

    result.short_score = (
        result.short_candle_points +
        result.short_h1_points +
        result.short_vol_roc_points +
        result.short_vol_delta_points +
        result.short_sma_points
    )

    return result


def calculate_all_scores(bars: list) -> list:
    """
    Calculate LONG and SHORT scores for all bars.

    Args:
        bars: List of processed bar dictionaries with indicator values
              Expected keys: candle_range_pct, roll_delta, volume_roc,
                           sma_config, sma_spread_pct, h1_structure

    Returns:
        List of dicts with 'long_score' and 'short_score' keys
    """
    results = []

    for bar in bars:
        long_score = calculate_long_score(
            candle_range_pct=bar.get('candle_range_pct'),
            volume_delta=bar.get('roll_delta'),
            volume_roc=bar.get('volume_roc'),
            sma_config=bar.get('sma_config'),
            sma_spread_pct=bar.get('sma_spread_pct'),
            h1_structure=bar.get('h1_structure')
        )

        short_score = calculate_short_score(
            candle_range_pct=bar.get('candle_range_pct'),
            volume_delta=bar.get('roll_delta'),
            volume_roc=bar.get('volume_roc'),
            sma_config=bar.get('sma_config'),
            sma_spread_pct=bar.get('sma_spread_pct'),
            h1_structure=bar.get('h1_structure')
        )

        results.append({
            'long_score': long_score,
            'short_score': short_score
        })

    return results
