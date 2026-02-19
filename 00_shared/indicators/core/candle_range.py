"""
================================================================================
EPOCH TRADING SYSTEM - CANDLE RANGE (Canonical)
XIII Trading LLC
================================================================================

Formula:
    candle_range_pct = (high - low) / close * 100

Thresholds:
    ABSORPTION: < 0.12% (skip trades - 33% WR universal)
    LOW: 0.12% - 0.15%
    NORMAL: 0.15% - 0.20% (has momentum)
    HIGH: >= 0.20% (strong signal)

================================================================================
"""

import numpy as np
import pandas as pd
from typing import List, Optional, Any

from ..config import CONFIG
from ..types import CandleRangeResult
from .._utils import get_high, get_low, get_close


# =============================================================================
# NUMPY CORE
# =============================================================================

def _candle_range_pct_core(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
) -> np.ndarray:
    """
    Calculate candle range as percentage of close for each bar.

    Returns:
        numpy array of range percentages
    """
    safe_close = np.where(close <= 0, 1.0, close)
    return np.where(close <= 0, 0.0, (high - low) / safe_close * 100.0)


# =============================================================================
# DATAFRAME WRAPPER
# =============================================================================

def candle_range_pct_df(
    df: pd.DataFrame,
    high_col: str = "high",
    low_col: str = "low",
    close_col: str = "close",
) -> pd.Series:
    """Calculate candle range percentage for a DataFrame."""
    return pd.Series(
        _candle_range_pct_core(
            df[high_col].values.astype(np.float64),
            df[low_col].values.astype(np.float64),
            df[close_col].values.astype(np.float64),
        ),
        index=df.index,
        name="candle_range_pct",
    )


def candle_range_df(
    df: pd.DataFrame,
    high_col: str = "high",
    low_col: str = "low",
) -> pd.Series:
    """Calculate raw candle range (high - low) for a DataFrame."""
    return pd.Series(df[high_col] - df[low_col], name="candle_range")


def relative_candle_range_df(
    df: pd.DataFrame,
    period: int = 20,
    high_col: str = "high",
    low_col: str = "low",
) -> pd.Series:
    """Calculate candle range relative to average (1.0 = average)."""
    ranges = df[high_col] - df[low_col]
    avg_range = ranges.rolling(window=period, min_periods=1).mean()
    return (ranges / avg_range.replace(0, np.nan)).rename("relative_range")


# =============================================================================
# BAR-LIST WRAPPER
# =============================================================================

def calculate_candle_range_pct(high: float, low: float, close: float) -> float:
    """Calculate candle range as percentage: (high - low) / close * 100."""
    if close <= 0:
        return 0.0
    return (high - low) / close * 100.0


def calculate_candle_range_from_bar(bar: Any) -> CandleRangeResult:
    """Calculate candle range from a bar dict or object."""
    high = get_high(bar, 0.0)
    low = get_low(bar, 0.0)
    close = get_close(bar, 0.0)

    pct = calculate_candle_range_pct(high, low, close)
    classification = get_range_classification(pct)

    return CandleRangeResult(
        candle_range_pct=pct,
        classification=classification,
        is_absorption=is_absorption_zone(pct),
        has_momentum=pct >= CONFIG.candle_range.normal_threshold,
    )


# =============================================================================
# CLASSIFICATION HELPERS
# =============================================================================

def is_absorption_zone(candle_range_pct: float) -> bool:
    """Check if candle range indicates absorption zone (< 0.12% = SKIP)."""
    return candle_range_pct < CONFIG.candle_range.absorption_threshold


def get_range_classification(candle_range_pct: float) -> str:
    """Classify candle range: 'ABSORPTION', 'LOW', 'NORMAL', 'HIGH'."""
    cfg = CONFIG.candle_range
    if candle_range_pct < cfg.absorption_threshold:
        return "ABSORPTION"
    elif candle_range_pct < cfg.normal_threshold:
        return "LOW"
    elif candle_range_pct < cfg.high_threshold:
        return "NORMAL"
    return "HIGH"


def is_candle_range_healthy(candle_range_pct: float) -> bool:
    """Check if candle range indicates healthy momentum (>= 0.15%)."""
    return candle_range_pct >= CONFIG.candle_range.normal_threshold
