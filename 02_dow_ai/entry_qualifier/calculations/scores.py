"""
DEPRECATED — February 2026
This module is no longer imported or used. LONG/SHORT composite scores have been
replaced by multi-timeframe fractal structure direction (M5, M15, H1).
See RAMPUP_MIGRATION_GUIDE.txt for details.

Composite Score Calculations
Epoch Trading System v1 - XIII Trading LLC

Calculates LONG and SHORT composite scores based on EPCH Indicators v1.0 spec.
"""
from typing import Optional, Any


def calculate_long_score(
    candle_range_pct: float,
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
    if candle_range_pct is not None and candle_range_pct >= 0.15:
        score += 2

    # H1 NEUTRAL: +2
    if h1_structure is not None:
        h1_value = h1_structure.value if hasattr(h1_structure, 'value') else str(h1_structure)
        if h1_value == 'N':
            score += 2

    # Vol ROC >= 30%: +1
    if volume_roc is not None and volume_roc >= 30:
        score += 1

    # High magnitude Vol Delta: +1
    # For LONG, we look for high magnitude (either direction)
    if volume_delta is not None and abs(volume_delta) > 100000:  # 100k threshold
        score += 1

    # Wide SMA spread (>= 0.15%): +1
    if sma_spread_pct is not None and sma_spread_pct >= 0.15:
        score += 1

    return score


def calculate_short_score(
    candle_range_pct: float,
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
    if candle_range_pct is not None and candle_range_pct >= 0.15:
        score += 2

    # H1 NEUTRAL: +2
    if h1_structure is not None:
        h1_value = h1_structure.value if hasattr(h1_structure, 'value') else str(h1_structure)
        if h1_value == 'N':
            score += 2

    # Vol ROC >= 30%: +1
    if volume_roc is not None and volume_roc >= 30:
        score += 1

    # Vol Delta POSITIVE (paradox): +1
    # For SHORT, positive delta indicates exhausted buyers
    if volume_delta is not None and volume_delta > 0:
        score += 1

    # SMA BULLISH (paradox): +1
    # For SHORT, bullish SMA config indicates we're catching a failed rally
    if sma_config is not None:
        sma_value = sma_config.value if hasattr(sma_config, 'value') else str(sma_config)
        if sma_value == 'B+':
            score += 1

    return score


def calculate_all_scores(bars: list) -> list:
    """
    Calculate LONG and SHORT scores for all bars.

    Args:
        bars: List of processed bar dictionaries with indicator values

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
