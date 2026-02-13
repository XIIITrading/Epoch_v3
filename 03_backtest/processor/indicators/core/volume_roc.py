"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 03: SHARED INDICATORS
Volume ROC (Rate of Change) Calculation
XIII Trading LLC
================================================================================

Formula:
  baseline_avg = mean(volume[-N-1:-1])
  roc = ((current_volume - baseline_avg) / baseline_avg) * 100

EPCH Indicators v1.0 Thresholds:
  Elevated: >= 30% (momentum confirmation)
  High: >= 50% (strong momentum)

Health Factor: Elevated volume (>= 30%) = healthy

================================================================================
"""

from typing import List, Optional, Any
import sys
from pathlib import Path

# Add parent to path for relative imports within shared library
_LIB_DIR = Path(__file__).parent.parent
if str(_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_LIB_DIR))

from _internal import VOLUME_ROC_CONFIG, VolumeROCResult, get_volume


def calculate_volume_roc(
    bars: List[Any],
    up_to_index: Optional[int] = None,
    baseline_period: Optional[int] = None
) -> VolumeROCResult:
    """
    Calculate Volume Rate of Change vs baseline average.

    Args:
        bars: List of bar data
        up_to_index: Calculate up to this index (inclusive)
        baseline_period: Number of bars for baseline average

    Returns:
        VolumeROCResult with roc, signal, current_volume, baseline_avg
    """
    baseline = baseline_period or VOLUME_ROC_CONFIG["baseline_period"]

    if not bars:
        return VolumeROCResult(
            roc=None,
            signal="Average",
            current_volume=0,
            baseline_avg=None
        )

    end_index = up_to_index if up_to_index is not None else len(bars) - 1
    end_index = min(end_index, len(bars) - 1)

    if end_index < baseline:
        return VolumeROCResult(
            roc=None,
            signal="Average",
            current_volume=get_volume(bars[end_index]),
            baseline_avg=None
        )

    current_volume = get_volume(bars[end_index])
    start_idx = end_index - baseline
    baseline_volumes = [get_volume(bars[i]) for i in range(start_idx, end_index)]

    if not baseline_volumes:
        return VolumeROCResult(
            roc=None,
            signal="Average",
            current_volume=current_volume,
            baseline_avg=None
        )

    baseline_avg = sum(baseline_volumes) / len(baseline_volumes)

    if baseline_avg == 0:
        return VolumeROCResult(
            roc=0.0,
            signal="Average",
            current_volume=current_volume,
            baseline_avg=baseline_avg
        )

    roc = ((current_volume - baseline_avg) / baseline_avg) * 100
    signal = classify_volume_roc(roc)

    return VolumeROCResult(
        roc=roc,
        signal=signal,
        current_volume=current_volume,
        baseline_avg=baseline_avg
    )


def classify_volume_roc(
    roc: Optional[float],
    above_threshold: Optional[float] = None,
    below_threshold: Optional[float] = None
) -> str:
    """
    Classify volume ROC into signal categories.

    Args:
        roc: Volume ROC percentage
        above_threshold: Threshold for "Above Avg" classification
        below_threshold: Threshold for "Below Avg" classification

    Returns:
        Classification: "Above Avg", "Below Avg", or "Average"
    """
    if roc is None:
        return "Average"

    above = above_threshold if above_threshold is not None else VOLUME_ROC_CONFIG["above_avg_threshold"]
    below = below_threshold if below_threshold is not None else VOLUME_ROC_CONFIG["below_avg_threshold"]

    if roc > above:
        return "Above Avg"
    elif roc < below:
        return "Below Avg"
    return "Average"


def is_volume_roc_healthy(
    roc: Optional[float],
    threshold: Optional[float] = None
) -> bool:
    """
    Check if volume ROC is healthy (above average).

    Args:
        roc: Volume ROC percentage
        threshold: Threshold for healthy classification

    Returns:
        True if volume is above average
    """
    if roc is None:
        return False
    thresh = threshold if threshold is not None else VOLUME_ROC_CONFIG["above_avg_threshold"]
    return roc > thresh


def is_elevated_volume(volume_roc: float) -> bool:
    """
    Check if volume ROC indicates elevated volume (>=30%).

    Per EPCH Indicators v1.0 spec.

    Args:
        volume_roc: Volume ROC as percentage

    Returns:
        True if volume is elevated
    """
    return volume_roc >= VOLUME_ROC_CONFIG.get("elevated_threshold", 30)


def is_high_volume(volume_roc: float) -> bool:
    """
    Check if volume ROC indicates high volume (>=50%).

    Per EPCH Indicators v1.0 spec.

    Args:
        volume_roc: Volume ROC as percentage

    Returns:
        True if volume is high
    """
    return volume_roc >= VOLUME_ROC_CONFIG.get("high_threshold", 50)
