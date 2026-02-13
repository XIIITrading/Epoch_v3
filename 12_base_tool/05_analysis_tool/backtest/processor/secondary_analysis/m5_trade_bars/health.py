"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
M5 Trade Bars - Direction-Specific Health Scoring
XIII Trading LLC
================================================================================

Health score calculation with direction context for trade bars.
Calculates whether each indicator factor is "healthy" based on trade direction.

10-Factor Health Score:
- Structure (4 points): H4, H1, M15, M5
- Volume (3 points): vol_roc, vol_delta, cvd_slope
- Price (3 points): sma_alignment, sma_momentum, vwap_position

Version: 1.0.0
================================================================================
"""

from typing import Dict, Optional, NamedTuple
import numpy as np

from config import (
    VOLUME_ROC_ABOVE_AVG_THRESHOLD,
    CVD_RISING_THRESHOLD,
    CVD_FALLING_THRESHOLD,
    HEALTH_BUCKETS
)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

class HealthResult(NamedTuple):
    """Complete health scoring result for a bar."""
    # Structure health
    h4_structure_healthy: Optional[bool]
    h1_structure_healthy: Optional[bool]
    m15_structure_healthy: Optional[bool]
    m5_structure_healthy: Optional[bool]

    # Volume health
    vol_roc_healthy: Optional[bool]
    vol_delta_healthy: Optional[bool]
    cvd_slope_healthy: Optional[bool]

    # Price health
    sma_alignment: Optional[str]  # BULL or BEAR
    sma_alignment_healthy: Optional[bool]
    sma_momentum_healthy: Optional[bool]
    vwap_position: Optional[str]  # ABOVE or BELOW
    vwap_healthy: Optional[bool]

    # Composite scores
    health_score: int
    health_label: str
    structure_score: int
    volume_score: int
    price_score: int


# =============================================================================
# HEALTH DETERMINATION FUNCTIONS
# =============================================================================

def is_structure_healthy(structure: Optional[str], trade_direction: str) -> Optional[bool]:
    """
    Determine if structure is healthy for the trade direction.

    LONG trades: healthy if structure is BULL
    SHORT trades: healthy if structure is BEAR
    """
    if structure is None or trade_direction is None:
        return None

    structure = structure.upper()
    direction = trade_direction.upper()

    if direction == 'LONG':
        return structure == 'BULL'
    elif direction == 'SHORT':
        return structure == 'BEAR'
    return None


def is_vol_roc_healthy(vol_roc: Optional[float]) -> Optional[bool]:
    """
    Volume ROC is healthy if above average (positive ROC above threshold).
    Higher volume at entry = more conviction.
    """
    if vol_roc is None:
        return None
    if np.isnan(vol_roc):
        return None
    return vol_roc >= VOLUME_ROC_ABOVE_AVG_THRESHOLD


def is_vol_delta_healthy(vol_delta: Optional[float], trade_direction: str) -> Optional[bool]:
    """
    Volume delta is healthy if it aligns with trade direction.

    LONG: healthy if positive delta (more buying)
    SHORT: healthy if negative delta (more selling)
    """
    if vol_delta is None or trade_direction is None:
        return None
    if np.isnan(vol_delta):
        return None

    direction = trade_direction.upper()

    if direction == 'LONG':
        return vol_delta > 0
    elif direction == 'SHORT':
        return vol_delta < 0
    return None


def is_cvd_slope_healthy(cvd_slope: Optional[float], trade_direction: str) -> Optional[bool]:
    """
    CVD slope is healthy if it aligns with trade direction.

    LONG: healthy if rising CVD (bullish)
    SHORT: healthy if falling CVD (bearish)
    """
    if cvd_slope is None or trade_direction is None:
        return None
    if np.isnan(cvd_slope):
        return None

    direction = trade_direction.upper()

    if direction == 'LONG':
        return cvd_slope >= CVD_RISING_THRESHOLD
    elif direction == 'SHORT':
        return cvd_slope <= CVD_FALLING_THRESHOLD
    return None


def get_sma_alignment(sma9: Optional[float], sma21: Optional[float]) -> Optional[str]:
    """
    Determine SMA alignment (BULL or BEAR).

    BULL: SMA9 > SMA21
    BEAR: SMA9 < SMA21
    """
    if sma9 is None or sma21 is None:
        return None
    if np.isnan(sma9) or np.isnan(sma21):
        return None

    if sma9 > sma21:
        return 'BULL'
    else:
        return 'BEAR'


def is_sma_alignment_healthy(sma_alignment: Optional[str], trade_direction: str) -> Optional[bool]:
    """
    SMA alignment is healthy if it matches trade direction.

    LONG: healthy if SMA alignment is BULL
    SHORT: healthy if SMA alignment is BEAR
    """
    if sma_alignment is None or trade_direction is None:
        return None

    alignment = sma_alignment.upper()
    direction = trade_direction.upper()

    if direction == 'LONG':
        return alignment == 'BULL'
    elif direction == 'SHORT':
        return alignment == 'BEAR'
    return None


def is_sma_momentum_healthy(sma_momentum_label: Optional[str]) -> Optional[bool]:
    """
    SMA momentum is healthy if spread is WIDENING (indicating trend strength).
    """
    if sma_momentum_label is None:
        return None
    return sma_momentum_label.upper() == 'WIDENING'


def get_vwap_position(close: Optional[float], vwap: Optional[float]) -> Optional[str]:
    """
    Determine price position relative to VWAP.

    ABOVE: price > VWAP
    BELOW: price < VWAP
    """
    if close is None or vwap is None:
        return None
    if np.isnan(close) or np.isnan(vwap):
        return None

    if close > vwap:
        return 'ABOVE'
    else:
        return 'BELOW'


def is_vwap_healthy(vwap_position: Optional[str], trade_direction: str) -> Optional[bool]:
    """
    VWAP position is healthy if it matches trade direction.

    LONG: healthy if price is ABOVE VWAP
    SHORT: healthy if price is BELOW VWAP
    """
    if vwap_position is None or trade_direction is None:
        return None

    position = vwap_position.upper()
    direction = trade_direction.upper()

    if direction == 'LONG':
        return position == 'ABOVE'
    elif direction == 'SHORT':
        return position == 'BELOW'
    return None


def get_health_label(score: int) -> str:
    """Get health label from score."""
    for label, (min_val, max_val) in HEALTH_BUCKETS.items():
        if min_val <= score <= max_val:
            return label
    return 'UNKNOWN'


# =============================================================================
# MAIN HEALTH CALCULATOR CLASS
# =============================================================================

class HealthCalculator:
    """
    Calculates direction-specific health scores for trade bars.
    """

    def calculate(
        self,
        direction: str,
        h4_structure: Optional[str],
        h1_structure: Optional[str],
        m15_structure: Optional[str],
        m5_structure: Optional[str],
        vol_roc: Optional[float],
        vol_delta: Optional[float],
        cvd_slope: Optional[float],
        sma9: Optional[float],
        sma21: Optional[float],
        sma_momentum_label: Optional[str],
        close: Optional[float],
        vwap: Optional[float]
    ) -> HealthResult:
        """
        Calculate complete health scoring for a bar.

        Args:
            direction: Trade direction ('LONG' or 'SHORT')
            h4_structure: H4 structure label
            h1_structure: H1 structure label
            m15_structure: M15 structure label
            m5_structure: M5 structure label
            vol_roc: Volume ROC
            vol_delta: Volume delta
            cvd_slope: CVD slope
            sma9: SMA9 value
            sma21: SMA21 value
            sma_momentum_label: SMA momentum label
            close: Close price
            vwap: VWAP value

        Returns:
            HealthResult with all health factors and composite score
        """
        # Structure health
        h4_healthy = is_structure_healthy(h4_structure, direction)
        h1_healthy = is_structure_healthy(h1_structure, direction)
        m15_healthy = is_structure_healthy(m15_structure, direction)
        m5_healthy = is_structure_healthy(m5_structure, direction)

        # Volume health
        vol_roc_healthy = is_vol_roc_healthy(vol_roc)
        vol_delta_healthy = is_vol_delta_healthy(vol_delta, direction)
        cvd_slope_healthy = is_cvd_slope_healthy(cvd_slope, direction)

        # Price health
        sma_alignment = get_sma_alignment(sma9, sma21)
        sma_alignment_healthy = is_sma_alignment_healthy(sma_alignment, direction)
        sma_momentum_healthy = is_sma_momentum_healthy(sma_momentum_label)
        vwap_position = get_vwap_position(close, vwap)
        vwap_healthy = is_vwap_healthy(vwap_position, direction)

        # Calculate structure score (0-4)
        structure_score = sum([
            1 if h4_healthy else 0,
            1 if h1_healthy else 0,
            1 if m15_healthy else 0,
            1 if m5_healthy else 0,
        ])

        # Calculate volume score (0-3)
        volume_score = sum([
            1 if vol_roc_healthy else 0,
            1 if vol_delta_healthy else 0,
            1 if cvd_slope_healthy else 0,
        ])

        # Calculate price score (0-3)
        price_score = sum([
            1 if sma_alignment_healthy else 0,
            1 if sma_momentum_healthy else 0,
            1 if vwap_healthy else 0,
        ])

        # Total health score (0-10)
        health_score = structure_score + volume_score + price_score
        health_label = get_health_label(health_score)

        return HealthResult(
            h4_structure_healthy=h4_healthy,
            h1_structure_healthy=h1_healthy,
            m15_structure_healthy=m15_healthy,
            m5_structure_healthy=m5_healthy,
            vol_roc_healthy=vol_roc_healthy,
            vol_delta_healthy=vol_delta_healthy,
            cvd_slope_healthy=cvd_slope_healthy,
            sma_alignment=sma_alignment,
            sma_alignment_healthy=sma_alignment_healthy,
            sma_momentum_healthy=sma_momentum_healthy,
            vwap_position=vwap_position,
            vwap_healthy=vwap_healthy,
            health_score=health_score,
            health_label=health_label,
            structure_score=structure_score,
            volume_score=volume_score,
            price_score=price_score
        )


# =============================================================================
# STANDALONE TEST
# =============================================================================

if __name__ == "__main__":
    print("M5 Trade Bars - Health Calculator Test")
    print("=" * 60)

    calc = HealthCalculator()

    # Test LONG trade with bullish indicators
    result = calc.calculate(
        direction='LONG',
        h4_structure='BULL',
        h1_structure='BULL',
        m15_structure='BEAR',
        m5_structure='BULL',
        vol_roc=35.0,
        vol_delta=15000.0,
        cvd_slope=0.15,
        sma9=100.5,
        sma21=100.0,
        sma_momentum_label='WIDENING',
        close=101.0,
        vwap=100.2
    )

    print("\nLONG Trade - Bullish Indicators:")
    print(f"  Health Score: {result.health_score}/10 ({result.health_label})")
    print(f"  Structure: {result.structure_score}/4")
    print(f"  Volume: {result.volume_score}/3")
    print(f"  Price: {result.price_score}/3")

    # Test SHORT trade with bearish indicators
    result2 = calc.calculate(
        direction='SHORT',
        h4_structure='BEAR',
        h1_structure='BEAR',
        m15_structure='BEAR',
        m5_structure='BEAR',
        vol_roc=45.0,
        vol_delta=-20000.0,
        cvd_slope=-0.2,
        sma9=99.5,
        sma21=100.0,
        sma_momentum_label='WIDENING',
        close=99.0,
        vwap=99.8
    )

    print("\nSHORT Trade - Bearish Indicators:")
    print(f"  Health Score: {result2.health_score}/10 ({result2.health_label})")
    print(f"  Structure: {result2.structure_score}/4")
    print(f"  Volume: {result2.volume_score}/3")
    print(f"  Price: {result2.price_score}/3")
