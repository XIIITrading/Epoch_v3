"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
Indicator Refinement - Rejection Calculations
XIII Trading LLC
================================================================================

Rejection indicator calculations (REJ-01 through REJ-05).
Based on Epoch Indicator Model Specification v1.0.

REJ-01: Structure Divergence (0-2 points)
REJ-02: SMA Exhaustion (0-3 points)
REJ-03: Delta Absorption (0-2 points)
REJ-04: Volume Climax (0-2 points)
REJ-05: CVD Extreme (0-2 points)

Total Rejection Score: 0-11

Version: 1.0.0
================================================================================
"""

from typing import Dict, List, Any, Optional
import numpy as np

from config import (
    SMA_SPREAD_Q1_THRESHOLD,
    SMA_SPREAD_Q2_THRESHOLD,
    SMA_SPREAD_CONTRACTING_THRESHOLD,
    ABSORPTION_Q5_THRESHOLD,
    ABSORPTION_Q4_THRESHOLD,
    PRICE_CHANGE_MIN,
    VOLUME_ROC_Q5_THRESHOLD,
    VOLUME_ROC_Q4_THRESHOLD,
    CVD_SLOPE_PERIOD,
    CVD_Q1_THRESHOLD,
    CVD_Q2_THRESHOLD
)


# =============================================================================
# REJ-01: STRUCTURE DIVERGENCE
# =============================================================================

def calculate_structure_divergence(
    entry_ind: Dict[str, Any],
    direction: str
) -> Dict[str, Any]:
    """
    REJ-01: Structure Divergence Score

    Measures divergence between HTF and LTF structure for exhaustion setups.

    Scoring (0-2 points):
        2 = Ideal exhaustion setup (HTF trend, LTF overextension)
        1 = Partial setup
        0 = No divergence signal

    For LONG rejection (shorting into demand after exhaustion):
        - HTF (H4/H1) should be BEAR (underlying trend)
        - LTF (M5/M15) should be BULL (overextension into supply)

    For SHORT rejection (longing into supply after exhaustion):
        - HTF (H4/H1) should be BULL (underlying trend)
        - LTF (M5/M15) should be BEAR (overextension into demand)

    Args:
        entry_ind: Entry indicators dict with structure fields
        direction: Trade direction ('LONG' or 'SHORT')

    Returns:
        Dict with score and component flags
    """
    direction = (direction or '').upper()

    h4_struct = (entry_ind.get('h4_structure') or '').upper()
    h1_struct = (entry_ind.get('h1_structure') or '').upper()
    m15_struct = (entry_ind.get('m15_structure') or '').upper()
    m5_struct = (entry_ind.get('m5_structure') or '').upper()

    # For LONG rejection: HTF should be BEAR, LTF should be BULL
    # For SHORT rejection: HTF should be BULL, LTF should be BEAR
    if direction == 'LONG':
        htf_aligned = h4_struct == 'BEAR' or h1_struct == 'BEAR'
        ltf_divergent = m5_struct == 'BULL' or m15_struct == 'BULL'
    elif direction == 'SHORT':
        htf_aligned = h4_struct == 'BULL' or h1_struct == 'BULL'
        ltf_divergent = m5_struct == 'BEAR' or m15_struct == 'BEAR'
    else:
        htf_aligned = False
        ltf_divergent = False

    # Score calculation
    if htf_aligned and ltf_divergent:
        score = 2  # Perfect divergence
    elif htf_aligned or ltf_divergent:
        score = 1  # Partial
    else:
        score = 0

    return {
        'score': score,
        'htf_aligned': htf_aligned,
        'ltf_divergent': ltf_divergent
    }


# =============================================================================
# REJ-02: SMA EXHAUSTION
# =============================================================================

def calculate_sma_exhaustion(
    entry_ind: Dict[str, Any],
    m5_bars: List[Dict]
) -> Dict[str, Any]:
    """
    REJ-02: SMA Exhaustion Score

    Measures trend exhaustion via SMA spread tightness and contraction.

    Scoring (0-3 points):
        3 = Strong exhaustion (spread very tight AND contracting)
        2 = Good exhaustion (very tight OR tight + contracting)
        1 = Partial exhaustion (tight OR contracting)
        0 = No exhaustion (trend still strong)

    Args:
        entry_ind: Entry indicators dict with sma9, sma21, entry_price
        m5_bars: List of M5 bar dicts for contraction calculation

    Returns:
        Dict with score and component flags
    """
    sma9 = entry_ind.get('sma9')
    sma21 = entry_ind.get('sma21')
    entry_price = entry_ind.get('entry_price')

    if sma9 is None or sma21 is None or entry_price is None:
        return {
            'score': 0, 'contracting': None,
            'very_tight': None, 'tight': None
        }

    sma9 = float(sma9)
    sma21 = float(sma21)
    entry_price = float(entry_price)

    # Calculate spread (absolute value for exhaustion)
    spread = abs(sma9 - sma21)

    # Spread as percentage of price
    if entry_price > 0:
        spread_pct = (spread / entry_price) * 100
    else:
        spread_pct = 0.0

    # Calculate spread ROC to detect contraction
    spread_roc = _calculate_spread_roc_for_exhaustion(m5_bars, spread)

    # Determine exhaustion flags
    contracting = spread_roc is not None and spread_roc < SMA_SPREAD_CONTRACTING_THRESHOLD
    very_tight = spread_pct < SMA_SPREAD_Q1_THRESHOLD
    tight = spread_pct < SMA_SPREAD_Q2_THRESHOLD

    # Score calculation
    if very_tight and contracting:
        score = 3
    elif very_tight or (tight and contracting):
        score = 2
    elif tight or contracting:
        score = 1
    else:
        score = 0

    return {
        'score': score,
        'contracting': contracting,
        'very_tight': very_tight,
        'tight': tight
    }


def _calculate_spread_roc_for_exhaustion(m5_bars: List[Dict], current_spread: float) -> Optional[float]:
    """Calculate spread rate of change for exhaustion detection."""
    if not m5_bars or len(m5_bars) < 6:
        return None

    # Get previous spread from 5 bars ago
    prev_bar = m5_bars[-6]
    prev_sma9 = prev_bar.get('sma9')
    prev_sma21 = prev_bar.get('sma21')

    if prev_sma9 is None or prev_sma21 is None:
        return None

    prev_spread = abs(float(prev_sma9) - float(prev_sma21))

    if prev_spread > 0.0001:
        return ((current_spread - prev_spread) / prev_spread) * 100

    return 0.0


# =============================================================================
# REJ-03: DELTA ABSORPTION
# =============================================================================

def calculate_delta_absorption(m5_bars: List[Dict]) -> Dict[str, Any]:
    """
    REJ-03: Delta Absorption Score

    Measures absorption of volume delta relative to price movement.
    High absorption = lots of delta but little price movement = exhaustion.

    Scoring (0-2 points):
        2 = Strong absorption (ratio in top 20%)
        1 = Moderate absorption (ratio in top 40%)
        0 = Normal delta/price relationship

    Args:
        m5_bars: List of M5 bar dicts

    Returns:
        Dict with score and absorption ratio
    """
    if not m5_bars or len(m5_bars) < 6:
        return {'score': 0, 'ratio': None}

    # Price change over 5 bars
    current_close = _safe_float(m5_bars[-1].get('close'))
    prev_close = _safe_float(m5_bars[-6].get('close'))

    if current_close is None or prev_close is None:
        return {'score': 0, 'ratio': None}

    avg_price = (current_close + prev_close) / 2
    if avg_price == 0:
        return {'score': 0, 'ratio': None}

    price_change = abs(current_close - prev_close)
    price_change_pct = (price_change / avg_price) * 100

    # Delta sum over 5 bars (absolute values)
    delta_sum = 0.0
    vol_sum = 0.0
    for bar in m5_bars[-5:]:
        bar_delta = bar.get('vol_delta', 0) or 0
        bar_vol = bar.get('volume', 0) or 0
        delta_sum += abs(float(bar_delta))
        vol_sum += float(bar_vol)

    # Normalize delta by average volume
    avg_vol = vol_sum / 5 if vol_sum > 0 else 1
    delta_normalized = delta_sum / avg_vol if avg_vol > 0 else 0

    # Absorption ratio
    if price_change_pct > PRICE_CHANGE_MIN:
        absorption_ratio = delta_normalized / price_change_pct
    else:
        # Very small price move = high absorption
        absorption_ratio = delta_normalized * 10

    # Score calculation
    if absorption_ratio > ABSORPTION_Q5_THRESHOLD:
        score = 2
    elif absorption_ratio > ABSORPTION_Q4_THRESHOLD:
        score = 1
    else:
        score = 0

    return {'score': score, 'ratio': absorption_ratio}


# =============================================================================
# REJ-04: VOLUME CLIMAX
# =============================================================================

def calculate_volume_climax(
    entry_ind: Dict[str, Any],
    m5_bars: List[Dict]
) -> Dict[str, Any]:
    """
    REJ-04: Volume Climax Score

    Detects volume climax signals (spikes or declining from highs).

    Scoring (0-2 points):
        2 = Volume climax (spike > Q5 OR high + declining)
        1 = Partial signal (moderate spike OR declining)
        0 = No climax indication

    Args:
        entry_ind: Entry indicators dict with vol_roc
        m5_bars: List of M5 bar dicts

    Returns:
        Dict with score and component flags
    """
    vol_roc = entry_ind.get('vol_roc')
    if vol_roc is None:
        vol_roc = 0.0
    else:
        vol_roc = float(vol_roc)

    # Check if volume is declining from recent bar
    vol_declining = False
    if m5_bars and len(m5_bars) >= 6:
        current_vol = _safe_float(m5_bars[-1].get('volume'))
        prev_vol = _safe_float(m5_bars[-6].get('volume'))
        if current_vol is not None and prev_vol is not None and prev_vol > 0:
            vol_declining = current_vol < prev_vol

    # Threshold checks
    roc_q5 = vol_roc > VOLUME_ROC_Q5_THRESHOLD
    roc_q4 = vol_roc > VOLUME_ROC_Q4_THRESHOLD

    # Score calculation
    if roc_q5:
        score = 2  # Spike = climax
    elif roc_q4 and vol_declining:
        score = 2  # High but declining = climax
    elif roc_q4 or vol_declining:
        score = 1
    else:
        score = 0

    return {
        'score': score,
        'roc_q5': roc_q5,
        'declining': vol_declining
    }


# =============================================================================
# REJ-05: CVD EXTREME
# =============================================================================

def calculate_cvd_extreme(
    m5_bars: List[Dict],
    direction: str
) -> Dict[str, Any]:
    """
    REJ-05: CVD Extreme Score

    Measures CVD (Cumulative Volume Delta) slope for extreme exhaustion.

    Scoring (0-2 points):
        2 = Extreme CVD (slope in Q1/Q5 depending on direction)
        1 = Moderate extreme
        0 = CVD in normal range

    For LONG rejection: Want extreme selling pressure (negative slope)
    For SHORT rejection: Want extreme buying pressure (positive slope)

    Args:
        m5_bars: List of M5 bar dicts
        direction: Trade direction ('LONG' or 'SHORT')

    Returns:
        Dict with score and CVD values
    """
    direction = (direction or '').upper()

    if not m5_bars or len(m5_bars) < CVD_SLOPE_PERIOD:
        return {'score': 0, 'slope': None, 'slope_normalized': None, 'extreme': None}

    # Calculate CVD from bar deltas
    cvd_values = []
    cumulative = 0.0
    for bar in m5_bars[-CVD_SLOPE_PERIOD:]:
        bar_delta = _safe_float(bar.get('vol_delta')) or 0.0
        cumulative += bar_delta
        cvd_values.append(cumulative)

    if len(cvd_values) < 2:
        return {'score': 0, 'slope': None, 'slope_normalized': None, 'extreme': None}

    # Linear regression slope
    x = np.arange(len(cvd_values))
    cvd_array = np.array(cvd_values)

    try:
        slope = np.polyfit(x, cvd_array, 1)[0]
    except (np.linalg.LinAlgError, ValueError):
        return {'score': 0, 'slope': None, 'slope_normalized': None, 'extreme': None}

    # Normalize slope by CVD range
    cvd_range = np.max(cvd_array) - np.min(cvd_array)
    if cvd_range > 0:
        slope_normalized = (slope / cvd_range) * CVD_SLOPE_PERIOD
    else:
        slope_normalized = 0.0

    # Determine if extreme based on direction
    if direction == 'LONG':
        # For LONG rejection, want extreme selling pressure (negative slope)
        extreme_q1 = slope_normalized < CVD_Q1_THRESHOLD
        extreme_q2 = slope_normalized < CVD_Q2_THRESHOLD
    elif direction == 'SHORT':
        # For SHORT rejection, want extreme buying pressure (positive slope)
        extreme_q1 = slope_normalized > abs(CVD_Q1_THRESHOLD)
        extreme_q2 = slope_normalized > abs(CVD_Q2_THRESHOLD)
    else:
        extreme_q1 = False
        extreme_q2 = False

    # Score calculation
    if extreme_q1:
        score = 2
    elif extreme_q2:
        score = 1
    else:
        score = 0

    return {
        'score': score,
        'slope': float(slope),
        'slope_normalized': float(slope_normalized),
        'extreme': extreme_q1
    }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _safe_float(value) -> Optional[float]:
    """Safely convert value to float."""
    if value is None:
        return None
    try:
        result = float(value)
        if np.isnan(result):
            return None
        return result
    except (ValueError, TypeError):
        return None
