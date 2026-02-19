"""
================================================================================
EPOCH TRADING SYSTEM - VOLUME ROC (Canonical)
Percentage Format
XIII Trading LLC
================================================================================

Formula:
    baseline_avg = mean(volume[-N-1:-1])     (exclude current bar)
    roc = ((current_volume - baseline_avg) / baseline_avg) * 100

Output is PERCENTAGE: 0% = average, 30% = elevated, 50% = high

================================================================================
"""

import numpy as np
import pandas as pd
from typing import List, Optional, Any

from ..config import CONFIG
from ..types import VolumeROCResult
from .._utils import get_volume


# =============================================================================
# NUMPY CORE
# =============================================================================

def _volume_roc_core(volume: np.ndarray, period: int) -> np.ndarray:
    """
    Calculate volume ROC as percentage for each bar.

    Args:
        volume: numpy array of volume values
        period: baseline lookback period

    Returns:
        numpy array of ROC percentages (NaN where insufficient data)
    """
    n = len(volume)
    result = np.full(n, np.nan)

    for i in range(period, n):
        baseline = volume[i - period:i]
        avg = baseline.mean()
        if avg == 0:
            result[i] = 0.0
        else:
            result[i] = ((volume[i] - avg) / avg) * 100.0

    return result


# =============================================================================
# DATAFRAME WRAPPER
# =============================================================================

def volume_roc_df(
    df: pd.DataFrame,
    period: Optional[int] = None,
    volume_col: str = "volume",
) -> pd.Series:
    """
    Calculate volume ROC as percentage for a DataFrame.

    Args:
        df: DataFrame with volume data
        period: baseline period (default from config)
        volume_col: column name for volume

    Returns:
        Series of ROC percentages
    """
    period = period or CONFIG.volume_roc.baseline_period
    return pd.Series(
        _volume_roc_core(df[volume_col].values.astype(np.float64), period),
        index=df.index,
        name="vol_roc",
    )


# =============================================================================
# BAR-LIST WRAPPER
# =============================================================================

def calculate_volume_roc(
    bars: List[Any],
    up_to_index: Optional[int] = None,
    baseline_period: Optional[int] = None,
) -> VolumeROCResult:
    """
    Calculate Volume ROC vs baseline average.

    Args:
        bars: List of bar data
        up_to_index: Calculate up to this index (inclusive)
        baseline_period: Number of bars for baseline

    Returns:
        VolumeROCResult with roc (percentage), signal, current_volume, baseline_avg
    """
    baseline = baseline_period or CONFIG.volume_roc.baseline_period

    if not bars:
        return VolumeROCResult(roc=None, signal="Average", current_volume=0, baseline_avg=None)

    end_index = up_to_index if up_to_index is not None else len(bars) - 1
    end_index = min(end_index, len(bars) - 1)

    if end_index < baseline:
        return VolumeROCResult(
            roc=None, signal="Average",
            current_volume=get_volume(bars[end_index]),
            baseline_avg=None,
        )

    current_volume = get_volume(bars[end_index])
    start_idx = end_index - baseline
    baseline_volumes = [get_volume(bars[i]) for i in range(start_idx, end_index)]

    if not baseline_volumes:
        return VolumeROCResult(roc=None, signal="Average", current_volume=current_volume, baseline_avg=None)

    baseline_avg = sum(baseline_volumes) / len(baseline_volumes)

    if baseline_avg == 0:
        return VolumeROCResult(roc=0.0, signal="Average", current_volume=current_volume, baseline_avg=baseline_avg)

    roc = ((current_volume - baseline_avg) / baseline_avg) * 100.0
    signal = classify_volume_roc(roc)

    return VolumeROCResult(roc=roc, signal=signal, current_volume=current_volume, baseline_avg=baseline_avg)


# =============================================================================
# CLASSIFICATION HELPERS
# =============================================================================

def classify_volume_roc(roc: Optional[float]) -> str:
    """Classify volume ROC into signal categories."""
    if roc is None:
        return "Average"
    if roc > CONFIG.volume_roc.above_avg_threshold:
        return "Above Avg"
    elif roc < CONFIG.volume_roc.below_avg_threshold:
        return "Below Avg"
    return "Average"


def is_elevated_volume(volume_roc: float) -> bool:
    """Check if volume ROC indicates elevated volume (>=30%)."""
    return volume_roc >= CONFIG.volume_roc.elevated_threshold


def is_high_volume(volume_roc: float) -> bool:
    """Check if volume ROC indicates high volume (>=50%)."""
    return volume_roc >= CONFIG.volume_roc.high_threshold
