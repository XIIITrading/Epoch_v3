"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 03: SHARED INDICATORS
Health Score Calculation
XIII Trading LLC
================================================================================

10-Factor DOW_AI Health Score:
1-4:  Multi-timeframe structure (H4, H1, M15, M5)
5-7:  Volume analysis (ROC, Delta, CVD)
8-9:  SMA analysis (Alignment, Spread Momentum)
10:   VWAP location

Score Interpretation:
- 8-10: STRONG, 6-7: MODERATE, 4-5: WEAK, 0-3: CRITICAL

================================================================================
"""

from typing import Dict, Optional, Any
import sys
from pathlib import Path

# Add parent to path for relative imports within shared library
_LIB_DIR = Path(__file__).parent.parent
if str(_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_LIB_DIR))

from _internal import HealthResult
from indicator_types import HealthScoreResult
from .thresholds import THRESHOLDS, get_health_label

# Import safe_float - need to add to _internal
def safe_float(value, default=0.0):
    """Safe float conversion."""
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def calculate_health_score(
    direction: str,
    h4_structure: str,
    h1_structure: str,
    m15_structure: str,
    m5_structure: str,
    volume_roc: Optional[float],
    volume_delta: float,
    cvd_slope: float,
    sma9: Optional[float],
    sma21: Optional[float],
    sma_momentum: str,
    price: float,
    vwap: Optional[float],
) -> HealthScoreResult:
    """
    Calculate 10-factor health score.

    Args:
        direction: Trade direction ('LONG' or 'SHORT')
        h4_structure: H4 structure ('BULL', 'BEAR', 'NEUTRAL')
        h1_structure: H1 structure
        m15_structure: M15 structure
        m5_structure: M5 structure
        volume_roc: Volume rate of change percentage
        volume_delta: Rolling volume delta
        cvd_slope: Normalized CVD slope
        sma9: Fast SMA value
        sma21: Slow SMA value
        sma_momentum: SMA momentum ('WIDENING', 'NARROWING', 'FLAT')
        price: Current price
        vwap: VWAP value

    Returns:
        HealthScoreResult with score, label, and individual factor states
    """
    is_long = direction.upper() == "LONG"
    target_structure = "BULL" if is_long else "BEAR"

    score = 0
    result = HealthScoreResult(score=0, max_score=10, label="CRITICAL")

    # Structure (4 points)
    result.h4_structure_healthy = (h4_structure == target_structure)
    if result.h4_structure_healthy:
        score += 1

    result.h1_structure_healthy = (h1_structure == target_structure)
    if result.h1_structure_healthy:
        score += 1

    result.m15_structure_healthy = (m15_structure == target_structure)
    if result.m15_structure_healthy:
        score += 1

    result.m5_structure_healthy = (m5_structure == target_structure)
    if result.m5_structure_healthy:
        score += 1

    # Volume (3 points)
    vol_roc_threshold = THRESHOLDS["volume_roc"]
    if volume_roc is not None:
        result.volume_roc_healthy = (volume_roc > vol_roc_threshold)
    if result.volume_roc_healthy:
        score += 1

    result.volume_delta_healthy = (volume_delta > 0) if is_long else (volume_delta < 0)
    if result.volume_delta_healthy:
        score += 1

    cvd_threshold = THRESHOLDS["cvd_slope"]
    result.cvd_healthy = (cvd_slope > cvd_threshold) if is_long else (cvd_slope < -cvd_threshold)
    if result.cvd_healthy:
        score += 1

    # SMA (2 points)
    if sma9 is not None and sma21 is not None:
        result.sma_alignment_healthy = (sma9 > sma21) if is_long else (sma9 < sma21)
    if result.sma_alignment_healthy:
        score += 1

    result.sma_momentum_healthy = (sma_momentum == "WIDENING")
    if result.sma_momentum_healthy:
        score += 1

    # VWAP (1 point)
    if vwap is not None:
        result.vwap_healthy = (price > vwap) if is_long else (price < vwap)
    if result.vwap_healthy:
        score += 1

    # Alignment groups
    result.htf_aligned = result.h4_structure_healthy and result.h1_structure_healthy
    result.mtf_aligned = result.m15_structure_healthy and result.m5_structure_healthy
    result.volume_aligned = result.volume_roc_healthy and result.volume_delta_healthy and result.cvd_healthy
    result.indicator_aligned = result.sma_alignment_healthy and result.vwap_healthy

    result.score = score
    result.label = get_health_label(score)

    return result


def calculate_health_from_bar(bar: Dict[str, Any], direction: str) -> HealthScoreResult:
    """
    Calculate health score from a bar dictionary.

    Convenience function for calculating health from a bar that contains
    all pre-calculated indicator values.

    Args:
        bar: Dictionary with indicator values
        direction: Trade direction ('LONG' or 'SHORT')

    Returns:
        HealthScoreResult
    """
    return calculate_health_score(
        direction=direction,
        h4_structure=str(bar.get("h4_structure", "NEUTRAL")),
        h1_structure=str(bar.get("h1_structure", "NEUTRAL")),
        m15_structure=str(bar.get("m15_structure", "NEUTRAL")),
        m5_structure=str(bar.get("m5_structure", "NEUTRAL")),
        volume_roc=safe_float(bar.get("vol_roc")),
        volume_delta=safe_float(bar.get("vol_delta"), 0.0),
        cvd_slope=safe_float(bar.get("cvd_slope"), 0.0),
        sma9=safe_float(bar.get("sma9")),
        sma21=safe_float(bar.get("sma21")),
        sma_momentum=str(bar.get("sma_momentum", "FLAT")),
        price=safe_float(bar.get("close_price") or bar.get("close"), 0.0),
        vwap=safe_float(bar.get("vwap")),
    )
