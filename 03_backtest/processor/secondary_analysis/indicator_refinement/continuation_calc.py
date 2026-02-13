"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
Indicator Refinement - Continuation Calculations
XIII Trading LLC
================================================================================

Continuation indicator calculations (CONT-01 through CONT-04).
Based on Epoch Indicator Model Specification v1.0.

CONT-01: Multi-Timeframe Alignment (0-4 points)
CONT-02: SMA Momentum (0-2 points)
CONT-03: Volume Thrust (0-2 points)
CONT-04: Pullback Quality (0-2 points)

Total Continuation Score: 0-10

Version: 1.0.0
================================================================================
"""

from typing import Dict, List, Any, Optional

from config import (
    SMA_SPREAD_ROC_THRESHOLD,
    SMA_SPREAD_LOOKBACK,
    VOLUME_ROC_STRONG_THRESHOLD,
    VOLUME_DELTA_PERIOD,
    PULLBACK_BARS,
    PULLBACK_DELTA_THRESHOLD_HIGH,
    PULLBACK_DELTA_THRESHOLD_MOD
)


# =============================================================================
# CONT-01: MULTI-TIMEFRAME ALIGNMENT
# =============================================================================

def calculate_mtf_alignment(structure: Dict[str, Any], direction: str) -> Dict[str, Any]:
    """
    CONT-01: Multi-Timeframe Alignment Score

    Measures how well the trade direction aligns with structure across timeframes.

    Scoring (0-4 points):
        4 = Full alignment (STRONG) - All timeframes aligned
        3 = Minor divergence (ACCEPTABLE) - One timeframe divergent
        2 = Split alignment (WEAK) - Two timeframes divergent
        0-1 = Counter-trend (AVOID for continuation)

    Args:
        structure: Dict with h4_structure, h1_structure, m15_structure, m5_structure
        direction: Trade direction ('LONG' or 'SHORT')

    Returns:
        Dict with score and individual alignment flags
    """
    if direction is None:
        return {
            'score': 0,
            'h4_aligned': None,
            'h1_aligned': None,
            'm15_aligned': None,
            'm5_aligned': None
        }

    direction = direction.upper()
    target_structure = 'BULL' if direction == 'LONG' else 'BEAR'

    # Check alignment for each timeframe
    h4_struct = (structure.get('h4_structure') or '').upper()
    h1_struct = (structure.get('h1_structure') or '').upper()
    m15_struct = (structure.get('m15_structure') or '').upper()
    m5_struct = (structure.get('m5_structure') or '').upper()

    h4_aligned = h4_struct == target_structure
    h1_aligned = h1_struct == target_structure
    m15_aligned = m15_struct == target_structure
    m5_aligned = m5_struct == target_structure

    # Sum aligned timeframes
    score = sum([h4_aligned, h1_aligned, m15_aligned, m5_aligned])

    return {
        'score': score,
        'h4_aligned': h4_aligned,
        'h1_aligned': h1_aligned,
        'm15_aligned': m15_aligned,
        'm5_aligned': m5_aligned
    }


# =============================================================================
# CONT-02: SMA MOMENTUM
# =============================================================================

def calculate_sma_momentum(
    entry_ind: Dict[str, Any],
    m5_bars: List[Dict],
    direction: str
) -> Dict[str, Any]:
    """
    CONT-02: SMA Momentum Score

    Measures SMA spread alignment and expansion rate.

    Scoring (0-2 points):
        2 = Strong momentum (spread aligned AND widening)
        1 = Partial momentum (aligned OR expanding, not both)
        0 = No momentum confirmation

    Args:
        entry_ind: Entry indicators dict with sma9, sma21, entry_price
        m5_bars: List of M5 bar dicts for ROC calculation
        direction: Trade direction ('LONG' or 'SHORT')

    Returns:
        Dict with score and component values
    """
    # Get SMA values from entry_indicators
    sma9 = entry_ind.get('sma9')
    sma21 = entry_ind.get('sma21')
    entry_price = entry_ind.get('entry_price')

    if sma9 is None or sma21 is None:
        return {
            'score': 0, 'spread': None, 'spread_pct': None,
            'spread_roc': None, 'aligned': None, 'expanding': None
        }

    sma9 = float(sma9)
    sma21 = float(sma21)
    spread = sma9 - sma21

    # Calculate spread as percentage of price
    if entry_price and float(entry_price) > 0:
        spread_pct = (spread / float(entry_price)) * 100
    else:
        spread_pct = 0.0

    # Calculate spread ROC from M5 bars if available
    spread_roc = _calculate_spread_roc(m5_bars, spread)

    # Determine alignment and expansion based on direction
    direction = (direction or '').upper()

    if direction == 'LONG':
        aligned = spread > 0
        expanding = spread_roc is not None and spread_roc > SMA_SPREAD_ROC_THRESHOLD
    elif direction == 'SHORT':
        aligned = spread < 0
        expanding = spread_roc is not None and spread_roc < -SMA_SPREAD_ROC_THRESHOLD
    else:
        aligned = False
        expanding = False

    # Score calculation
    if aligned and expanding:
        score = 2
    elif aligned or expanding:
        score = 1
    else:
        score = 0

    return {
        'score': score,
        'spread': spread,
        'spread_pct': spread_pct,
        'spread_roc': spread_roc,
        'aligned': aligned,
        'expanding': expanding
    }


def _calculate_spread_roc(m5_bars: List[Dict], current_spread: float) -> Optional[float]:
    """Calculate rate of change in SMA spread from M5 bars."""
    if not m5_bars or len(m5_bars) < SMA_SPREAD_LOOKBACK + 1:
        return None

    # Get SMA values from lookback bar
    lookback_idx = -(SMA_SPREAD_LOOKBACK + 1)
    prev_bar = m5_bars[lookback_idx]

    prev_sma9 = prev_bar.get('sma9')
    prev_sma21 = prev_bar.get('sma21')

    if prev_sma9 is None or prev_sma21 is None:
        return None

    prev_spread = float(prev_sma9) - float(prev_sma21)

    # Calculate ROC
    if abs(prev_spread) > 0.0001:
        spread_roc = ((current_spread - prev_spread) / abs(prev_spread)) * 100
        return spread_roc

    return 0.0


# =============================================================================
# CONT-03: VOLUME THRUST
# =============================================================================

def calculate_volume_thrust(
    entry_ind: Dict[str, Any],
    m5_bars: List[Dict],
    direction: str
) -> Dict[str, Any]:
    """
    CONT-03: Volume Thrust Score

    Measures volume strength and delta alignment with trade direction.

    Scoring (0-2 points):
        2 = Strong volume confirmation (ROC strong AND delta aligned)
        1 = Partial confirmation (ROC moderate + delta aligned OR ROC strong alone)
        0 = No volume support

    Args:
        entry_ind: Entry indicators dict with vol_roc, vol_delta
        m5_bars: List of M5 bar dicts for delta calculation
        direction: Trade direction ('LONG' or 'SHORT')

    Returns:
        Dict with score and component values
    """
    direction = (direction or '').upper()

    # Get volume ROC from entry_indicators
    vol_roc = entry_ind.get('vol_roc')
    if vol_roc is None:
        vol_roc = 0.0
    else:
        vol_roc = float(vol_roc)

    # Calculate 5-bar delta sum from M5 bars
    vol_delta_5 = _calculate_delta_sum(m5_bars, entry_ind)

    # Determine thresholds
    roc_strong = vol_roc > VOLUME_ROC_STRONG_THRESHOLD
    roc_moderate = vol_roc > 0

    # Delta alignment
    if direction == 'LONG':
        delta_aligned = vol_delta_5 > 0
    elif direction == 'SHORT':
        delta_aligned = vol_delta_5 < 0
    else:
        delta_aligned = False

    # Score calculation
    if roc_strong and delta_aligned:
        score = 2
    elif (roc_moderate and delta_aligned) or roc_strong:
        score = 1
    else:
        score = 0

    return {
        'score': score,
        'vol_roc': vol_roc,
        'vol_delta_5': vol_delta_5,
        'roc_strong': roc_strong,
        'delta_aligned': delta_aligned
    }


def _calculate_delta_sum(m5_bars: List[Dict], entry_ind: Dict) -> float:
    """Calculate sum of volume delta over VOLUME_DELTA_PERIOD bars."""
    vol_delta_5 = 0.0

    if m5_bars and len(m5_bars) >= VOLUME_DELTA_PERIOD:
        for bar in m5_bars[-VOLUME_DELTA_PERIOD:]:
            bar_delta = bar.get('vol_delta', 0) or 0
            vol_delta_5 += float(bar_delta)
    else:
        # Fallback to entry_indicators vol_delta
        vol_delta = entry_ind.get('vol_delta')
        if vol_delta is not None:
            vol_delta_5 = float(vol_delta)

    return vol_delta_5


# =============================================================================
# CONT-04: PULLBACK QUALITY
# =============================================================================

def calculate_pullback_quality(
    entry_ind: Dict[str, Any],
    m5_bars: List[Dict],
    direction: str
) -> Dict[str, Any]:
    """
    CONT-04: Pullback Quality Score

    Measures quality of pullback based on delta absorption ratio.

    Scoring (0-2 points):
        2 = High quality pullback (delta_ratio < 0.3, indicates accumulation)
        1 = Acceptable pullback OR not in pullback (baseline)
        0 = Poor pullback quality (delta_ratio > 0.5, reversal risk)

    Args:
        entry_ind: Entry indicators dict with sma21
        m5_bars: List of M5 bar dicts for pullback detection
        direction: Trade direction ('LONG' or 'SHORT')

    Returns:
        Dict with score and component values
    """
    direction = (direction or '').upper()

    # Need enough bars for pullback analysis
    min_bars_needed = PULLBACK_BARS + 6
    if not m5_bars or len(m5_bars) < min_bars_needed:
        return {'score': 1, 'in_pullback': None, 'delta_ratio': None}

    # Get price data
    current_close = _safe_float(m5_bars[-1].get('close'))
    prior_close = _safe_float(m5_bars[-PULLBACK_BARS].get('close'))
    sma21 = entry_ind.get('sma21')

    if current_close is None or prior_close is None or sma21 is None:
        return {'score': 1, 'in_pullback': None, 'delta_ratio': None}

    sma21 = float(sma21)

    # Detect if in pullback
    # LONG pullback: price dropped from prior but still above SMA21
    # SHORT pullback: price rose from prior but still below SMA21
    if direction == 'LONG':
        in_pullback = current_close < prior_close and current_close > sma21
    elif direction == 'SHORT':
        in_pullback = current_close > prior_close and current_close < sma21
    else:
        in_pullback = False

    if not in_pullback:
        # Not in pullback = acceptable baseline
        return {'score': 1, 'in_pullback': False, 'delta_ratio': None}

    # Calculate delta ratio
    delta_ratio = _calculate_delta_ratio(m5_bars)

    # Score calculation based on delta ratio
    if delta_ratio is not None:
        if delta_ratio < PULLBACK_DELTA_THRESHOLD_HIGH:
            score = 2  # Very low delta = strong accumulation
        elif delta_ratio < PULLBACK_DELTA_THRESHOLD_MOD:
            score = 1  # Moderate
        else:
            score = 0  # High delta = potential reversal
    else:
        score = 1  # Unknown = baseline

    return {
        'score': score,
        'in_pullback': in_pullback,
        'delta_ratio': delta_ratio
    }


def _calculate_delta_ratio(m5_bars: List[Dict]) -> Optional[float]:
    """Calculate pullback delta ratio (pullback_delta / thrust_delta)."""
    if len(m5_bars) < PULLBACK_BARS + 5:
        return None

    # Pullback delta (last N bars)
    pullback_delta = 0.0
    for bar in m5_bars[-PULLBACK_BARS:]:
        bar_delta = bar.get('vol_delta', 0) or 0
        pullback_delta += abs(float(bar_delta))

    # Thrust delta (prior 5 bars before pullback)
    thrust_delta = 0.0
    thrust_start = -(PULLBACK_BARS + 5)
    thrust_end = -PULLBACK_BARS
    for bar in m5_bars[thrust_start:thrust_end]:
        bar_delta = bar.get('vol_delta', 0) or 0
        thrust_delta += abs(float(bar_delta))

    # Avoid division by zero
    if thrust_delta == 0:
        return 1.0

    return pullback_delta / thrust_delta


def _safe_float(value) -> Optional[float]:
    """Safely convert value to float."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None
