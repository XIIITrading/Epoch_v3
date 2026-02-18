"""
Epoch Trading System - Health Score
====================================

10-factor health scoring for trade evaluation.

The health score evaluates trade quality across 10 factors:
1. SMA Alignment
2. SMA Momentum
3. VWAP Position
4. Volume Delta
5. Volume ROC
6. CVD Slope
7. Candle Range
8. Price Position
9. Structure Alignment
10. Zone Proximity

Usage:
    from shared.indicators.health import calculate_health_score

    result = calculate_health_score(indicators, trade_direction)
"""

from typing import Dict, Optional, NamedTuple, List


class HealthResult(NamedTuple):
    """Result of health score calculation."""
    score: int  # 0-10
    factors: Dict[str, bool]  # Individual factor results
    healthy_count: int
    details: Dict[str, str]  # Human-readable factor status


# =============================================================================
# THRESHOLDS
# =============================================================================
HEALTH_THRESHOLDS = {
    "sma_spread_min": 0.1,       # Minimum spread % for healthy SMA
    "volume_roc_min": 0.8,       # Minimum volume ROC
    "cvd_slope_threshold": 0,   # CVD slope direction threshold
    "range_ratio_min": 0.8,     # Minimum candle range ratio
}


def calculate_health_score(
    indicators: Dict[str, any],
    trade_direction: str,
) -> HealthResult:
    """
    Calculate 10-factor health score.

    Args:
        indicators: Dict with indicator values
        trade_direction: "LONG" or "SHORT"

    Returns:
        HealthResult with score, factors, and details
    """
    is_long = trade_direction.upper() in ("LONG", "BULL", "BULLISH")
    factors = {}
    details = {}

    # 1. SMA Alignment
    sma9 = indicators.get("sma9")
    sma21 = indicators.get("sma21")
    if sma9 is not None and sma21 is not None:
        if is_long:
            factors["sma_alignment"] = sma9 > sma21
            details["sma_alignment"] = f"SMA9 {'>' if sma9 > sma21 else '<'} SMA21"
        else:
            factors["sma_alignment"] = sma9 < sma21
            details["sma_alignment"] = f"SMA9 {'<' if sma9 < sma21 else '>'} SMA21"
    else:
        factors["sma_alignment"] = False
        details["sma_alignment"] = "N/A"

    # 2. SMA Momentum
    sma_momentum = indicators.get("sma_momentum", "FLAT")
    factors["sma_momentum"] = sma_momentum == "WIDENING"
    details["sma_momentum"] = sma_momentum

    # 3. VWAP Position
    price = indicators.get("price")
    vwap = indicators.get("vwap")
    if price is not None and vwap is not None:
        if is_long:
            factors["vwap_position"] = price > vwap
            details["vwap_position"] = f"Price {'above' if price > vwap else 'below'} VWAP"
        else:
            factors["vwap_position"] = price < vwap
            details["vwap_position"] = f"Price {'below' if price < vwap else 'above'} VWAP"
    else:
        factors["vwap_position"] = False
        details["vwap_position"] = "N/A"

    # 4. Volume Delta
    volume_delta = indicators.get("volume_delta", 0)
    if is_long:
        factors["volume_delta"] = volume_delta > 0
        details["volume_delta"] = f"Delta {'positive' if volume_delta > 0 else 'negative'}"
    else:
        factors["volume_delta"] = volume_delta < 0
        details["volume_delta"] = f"Delta {'negative' if volume_delta < 0 else 'positive'}"

    # 5. Volume ROC
    volume_roc = indicators.get("volume_roc", 1.0)
    factors["volume_roc"] = volume_roc >= HEALTH_THRESHOLDS["volume_roc_min"]
    details["volume_roc"] = f"ROC {volume_roc:.2f}x"

    # 6. CVD Slope
    cvd_slope = indicators.get("cvd_slope", 0)
    if is_long:
        factors["cvd_slope"] = cvd_slope > 0
        details["cvd_slope"] = f"CVD {'rising' if cvd_slope > 0 else 'falling'}"
    else:
        factors["cvd_slope"] = cvd_slope < 0
        details["cvd_slope"] = f"CVD {'falling' if cvd_slope < 0 else 'rising'}"

    # 7. Candle Range
    range_ratio = indicators.get("range_ratio", 1.0)
    factors["candle_range"] = range_ratio >= HEALTH_THRESHOLDS["range_ratio_min"]
    details["candle_range"] = f"Range {range_ratio:.2f}x avg"

    # 8. Price Position
    price_position = indicators.get("price_position", "BTWN")
    if is_long:
        factors["price_position"] = price_position == "ABOVE"
    else:
        factors["price_position"] = price_position == "BELOW"
    details["price_position"] = price_position

    # 9. Structure Alignment
    structure = indicators.get("structure", 0)
    if is_long:
        factors["structure"] = structure == 1
    else:
        factors["structure"] = structure == -1
    details["structure"] = {1: "B+", -1: "B-", 0: "N"}.get(structure, "N/A")

    # 10. Zone Proximity
    zone_distance = indicators.get("zone_distance_pct", 0)
    factors["zone_proximity"] = abs(zone_distance) <= 0.5  # Within 0.5% of zone
    details["zone_proximity"] = f"{zone_distance:.2f}% from zone"

    # Calculate score
    healthy_count = sum(1 for v in factors.values() if v)
    score = healthy_count

    return HealthResult(
        score=score,
        factors=factors,
        healthy_count=healthy_count,
        details=details,
    )


def get_health_classification(score: int) -> str:
    """
    Get health classification from score.

    Args:
        score: Health score (0-10)

    Returns:
        "STRONG" (7-10), "MODERATE" (4-6), or "WEAK" (0-3)
    """
    if score >= 7:
        return "STRONG"
    elif score >= 4:
        return "MODERATE"
    else:
        return "WEAK"


def is_trade_healthy(score: int, min_score: int = 5) -> bool:
    """
    Check if trade meets minimum health threshold.

    Args:
        score: Health score (0-10)
        min_score: Minimum acceptable score

    Returns:
        True if score meets threshold
    """
    return score >= min_score
