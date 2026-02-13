"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 03: SHARED INDICATORS
Candle Range Calculations
XIII Trading LLC
================================================================================

Formula:
    candle_range_pct = (high - low) / close * 100

Thresholds:
    ABSORPTION: < 0.12% (skip trades)
    LOW: 0.12% - 0.15%
    NORMAL: 0.15% - 0.20%
    HIGH: >= 0.20%

Health Factor: Range >= 0.15% indicates momentum, < 0.12% indicates absorption

================================================================================
"""

from typing import List, Optional, Any
import sys
from pathlib import Path

# Add parent to path for relative imports within shared library
_LIB_DIR = Path(__file__).parent.parent
if str(_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_LIB_DIR))

from _internal import get_high, get_low, get_close

# =============================================================================
# THRESHOLDS (from reference implementation)
# =============================================================================

# Absorption Zone threshold - skip trades below this
ABSORPTION_THRESHOLD = 0.12  # 0.12%

# Normal range threshold - trades above this have edge
NORMAL_THRESHOLD = 0.15  # 0.15%

# High range threshold - strong signal
HIGH_THRESHOLD = 0.20  # 0.20%


# =============================================================================
# RESULT DATACLASS
# =============================================================================

from dataclasses import dataclass


@dataclass
class CandleRangeResult:
    """Candle range calculation result."""
    candle_range_pct: float
    classification: str  # 'ABSORPTION', 'LOW', 'NORMAL', 'HIGH'
    is_absorption: bool
    has_momentum: bool  # True if >= NORMAL_THRESHOLD


# =============================================================================
# CORE CALCULATIONS
# =============================================================================

def calculate_candle_range_pct(
    high: float,
    low: float,
    close: float
) -> float:
    """
    Calculate candle range as percentage of price.

    Formula: (high - low) / close * 100

    Args:
        high: Bar high price
        low: Bar low price
        close: Bar close price (used as reference)

    Returns:
        Candle range as percentage (e.g., 0.15 for 0.15%)
    """
    if close <= 0:
        return 0.0

    range_value = high - low
    return (range_value / close) * 100


def calculate_candle_range_from_bar(bar: Any) -> CandleRangeResult:
    """
    Calculate candle range from a bar dict or object.

    Args:
        bar: Bar data (dict or object with high, low, close)

    Returns:
        CandleRangeResult with percentage, classification, and flags
    """
    high = get_high(bar, 0.0)
    low = get_low(bar, 0.0)
    close = get_close(bar, 0.0)

    candle_range_pct = calculate_candle_range_pct(high, low, close)
    classification = get_range_classification(candle_range_pct)
    is_absorption = is_absorption_zone(candle_range_pct)
    has_momentum = candle_range_pct >= NORMAL_THRESHOLD

    return CandleRangeResult(
        candle_range_pct=candle_range_pct,
        classification=classification,
        is_absorption=is_absorption,
        has_momentum=has_momentum
    )


def is_absorption_zone(candle_range_pct: float) -> bool:
    """
    Check if candle range indicates absorption zone (should skip).

    Args:
        candle_range_pct: Candle range as percentage

    Returns:
        True if this is an absorption zone (< 0.12%)
    """
    return candle_range_pct < ABSORPTION_THRESHOLD


def get_range_classification(candle_range_pct: float) -> str:
    """
    Classify candle range for display/logging.

    Args:
        candle_range_pct: Candle range as percentage

    Returns:
        Classification string: 'ABSORPTION', 'LOW', 'NORMAL', 'HIGH'
    """
    if candle_range_pct < ABSORPTION_THRESHOLD:
        return 'ABSORPTION'
    elif candle_range_pct < NORMAL_THRESHOLD:
        return 'LOW'
    elif candle_range_pct < HIGH_THRESHOLD:
        return 'NORMAL'
    else:
        return 'HIGH'


def is_candle_range_healthy(candle_range_pct: float) -> bool:
    """
    Check if candle range indicates healthy momentum.

    Args:
        candle_range_pct: Candle range as percentage

    Returns:
        True if range >= 0.15% (not absorption, has momentum)
    """
    return candle_range_pct >= NORMAL_THRESHOLD


def calculate_all_candle_ranges(
    bars: List[Any],
    up_to_index: Optional[int] = None
) -> List[CandleRangeResult]:
    """
    Calculate candle range for all bars up to a given index.

    Args:
        bars: List of bar data
        up_to_index: Calculate up to this index (inclusive), default all

    Returns:
        List of CandleRangeResult for each bar
    """
    if not bars:
        return []

    end_index = up_to_index if up_to_index is not None else len(bars) - 1
    end_index = min(end_index, len(bars) - 1)

    results = []
    for i in range(end_index + 1):
        result = calculate_candle_range_from_bar(bars[i])
        results.append(result)

    return results
