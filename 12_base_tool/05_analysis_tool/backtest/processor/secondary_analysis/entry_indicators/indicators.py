"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
Entry Indicators - Indicator Calculations
XIII Trading LLC
================================================================================

Self-contained indicator calculation functions for entry analysis.
Calculates SMA, VWAP, Volume ROC, Volume Delta, and CVD Slope.

All functions expect a list of bar dictionaries with keys:
    - open, high, low, close, volume
    - Optional: vwap (for VWAP calculations)

Version: 1.0.0
================================================================================
"""

from typing import List, Dict, Optional, NamedTuple
import sys
from pathlib import Path

# Add shared indicators library
_SHARED_LIB = Path(__file__).parent.parent.parent.parent.parent.parent / "03_indicators" / "python"
sys.path.insert(0, str(_SHARED_LIB))

from indicator_types import SMAResult as _SMAResult, SMAMomentumResult as _SMAMomentumResult
from indicator_types import VWAPResult as _VWAPResult, VolumeROCResult as _VolumeROCResult
from indicator_types import VolumeDeltaResult as _VolumeDeltaResult, CVDResult as _CVDResult
from core.sma import calculate_sma as _calc_sma, calculate_sma_spread as _calc_spread, calculate_sma_momentum as _calc_momentum
from core.vwap import calculate_vwap as _calc_vwap, calculate_vwap_metrics as _calc_vwap_metrics
from core.volume_roc import calculate_volume_roc as _calc_vol_roc
from core.volume_delta import calculate_bar_delta as _calc_bar_delta, calculate_rolling_delta as _calc_rolling_delta
from core.cvd import calculate_cvd_slope as _calc_cvd


# =============================================================================
# RESULT DATA STRUCTURES
# =============================================================================

class SMAResult(NamedTuple):
    """Result of SMA calculation."""
    sma9: float
    sma21: float
    spread: float
    alignment: str  # 'BULL' or 'BEAR'


class SMAMomentumResult(NamedTuple):
    """Result of SMA momentum calculation."""
    current_spread: float
    previous_spread: float
    ratio: float
    momentum: str  # 'WIDENING', 'NARROWING', or 'STABLE'


class VWAPResult(NamedTuple):
    """Result of VWAP calculation."""
    vwap: float
    price: float
    side: str  # 'ABOVE' or 'BELOW'


class VolumeROCResult(NamedTuple):
    """Result of Volume ROC calculation."""
    current_volume: float
    baseline_avg: float
    roc: float  # Percentage above/below baseline


class VolumeDeltaResult(NamedTuple):
    """Result of Volume Delta calculation."""
    bar_delta: float
    rolling_delta: float


class CVDResult(NamedTuple):
    """Result of CVD Slope calculation."""
    cvd_values: List[float]
    slope: float


# =============================================================================
# SMA CALCULATIONS
# =============================================================================

def calculate_sma(bars: List[Dict], index: int = -1) -> Optional[SMAResult]:
    """
    Calculate SMA9 and SMA21 at a given bar index using shared library.

    Args:
        bars: List of bar dictionaries with 'close' key
        index: Bar index to calculate at (-1 for last bar)

    Returns:
        SMAResult or None if insufficient data
    """
    if index == -1:
        index = len(bars) - 1
    result = _calc_spread(bars, up_to_index=index)
    if result.sma9 is None:
        return None
    return SMAResult(
        sma9=result.sma9,
        sma21=result.sma21,
        spread=result.spread,
        alignment='BULL' if result.alignment == 'BULLISH' else 'BEAR'
    )


def calculate_sma_momentum(bars: List[Dict], index: int = -1) -> Optional[SMAMomentumResult]:
    """
    Calculate SMA spread momentum using shared library.

    Args:
        bars: List of bar dictionaries
        index: Bar index to calculate at (-1 for last bar)

    Returns:
        SMAMomentumResult or None if insufficient data
    """
    if index == -1:
        index = len(bars) - 1
    result = _calc_momentum(bars, up_to_index=index)
    if result.spread_now is None:
        return None
    # Map WIDENING/NARROWING/FLAT to WIDENING/NARROWING/STABLE
    momentum = result.momentum if result.momentum != 'FLAT' else 'STABLE'
    return SMAMomentumResult(
        current_spread=result.spread_now,
        previous_spread=result.spread_prev,
        ratio=result.ratio,
        momentum=momentum
    )


# =============================================================================
# VWAP CALCULATIONS
# =============================================================================

def calculate_vwap(bars: List[Dict], index: int = -1, price: float = None) -> Optional[VWAPResult]:
    """
    Calculate VWAP using shared library.

    Args:
        bars: List of bar dictionaries with OHLCV data
        index: Bar index to calculate at (-1 for last bar)
        price: Current price (uses close if None)

    Returns:
        VWAPResult or None if insufficient data
    """
    if index == -1:
        index = len(bars) - 1
    if price is None:
        price = bars[index].get('close', 0)
    result = _calc_vwap_metrics(bars, price, up_to_index=index)
    if result.vwap is None:
        return None
    return VWAPResult(
        vwap=result.vwap,
        price=price,
        side=result.side
    )


# =============================================================================
# VOLUME ROC CALCULATIONS
# =============================================================================

def calculate_volume_roc(bars: List[Dict], index: int = -1) -> Optional[VolumeROCResult]:
    """
    Calculate Volume ROC using shared library.

    Args:
        bars: List of bar dictionaries with 'volume' key
        index: Bar index to calculate at (-1 for last bar)

    Returns:
        VolumeROCResult or None if insufficient data
    """
    if index == -1:
        index = len(bars) - 1
    result = _calc_vol_roc(bars, up_to_index=index)
    if result.roc is None:
        return None
    return VolumeROCResult(
        current_volume=result.current_volume,
        baseline_avg=result.baseline_avg,
        roc=result.roc
    )


# =============================================================================
# VOLUME DELTA CALCULATIONS
# =============================================================================

def calculate_bar_delta(bar: Dict) -> float:
    """
    Calculate volume delta for a single bar using shared library.

    Args:
        bar: Bar dictionary with open, high, low, close, volume

    Returns:
        Volume delta value
    """
    result = _calc_bar_delta(
        bar.get('open', 0),
        bar.get('high', 0),
        bar.get('low', 0),
        bar.get('close', 0),
        int(bar.get('volume', 0))
    )
    return result.bar_delta


def calculate_volume_delta(bars: List[Dict], index: int = -1) -> Optional[VolumeDeltaResult]:
    """
    Calculate rolling volume delta using shared library.

    Args:
        bars: List of bar dictionaries
        index: Bar index to calculate at (-1 for last bar)

    Returns:
        VolumeDeltaResult
    """
    if index == -1:
        index = len(bars) - 1
    result = _calc_rolling_delta(bars, up_to_index=index)
    return VolumeDeltaResult(
        bar_delta=calculate_bar_delta(bars[index]),
        rolling_delta=result.rolling_delta
    )


# =============================================================================
# CVD (CUMULATIVE VOLUME DELTA) CALCULATIONS
# =============================================================================

def calculate_cvd_slope(bars: List[Dict], index: int = -1) -> Optional[CVDResult]:
    """
    Calculate CVD slope using shared library.

    Args:
        bars: List of bar dictionaries
        index: Bar index to calculate at (-1 for last bar)

    Returns:
        CVDResult
    """
    if index == -1:
        index = len(bars) - 1
    result = _calc_cvd(bars, up_to_index=index)
    return CVDResult(
        cvd_values=result.cvd_values,
        slope=result.slope
    )
