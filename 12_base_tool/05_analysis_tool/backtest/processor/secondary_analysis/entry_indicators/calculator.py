"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
Entry Indicators - Calculator
XIII Trading LLC
================================================================================

Core calculator that computes all entry indicators for a single trade.
Combines M1 bar data, indicator calculations, and structure detection.

Version: 1.0.0
================================================================================
"""

from dataclasses import dataclass
from datetime import datetime, date, time, timedelta
from typing import Dict, List, Optional, Any
import logging

from config import (
    SMA_WIDENING_THRESHOLD,
    VOLUME_ROC_ABOVE_AVG_THRESHOLD,
    CVD_RISING_THRESHOLD,
    CVD_FALLING_THRESHOLD,
    HEALTH_BUCKETS,
    CALCULATION_VERSION
)

from m1_data import M1DataProvider, aggregate_to_m5
from indicators import (
    calculate_sma,
    calculate_sma_momentum,
    calculate_vwap,
    calculate_volume_roc,
    calculate_volume_delta,
    calculate_cvd_slope
)
from entry_ind_structure import StructureAnalyzer, StructureResult


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class EntryIndicatorsResult:
    """Complete entry indicators result for a single trade."""
    # Trade identification
    trade_id: str
    date: date
    ticker: str
    direction: str
    model: Optional[str]
    entry_time: time
    entry_price: float

    # Indicator bar reference
    indicator_bar_time: Optional[time]
    indicator_methodology: str

    # Structure factors (4 factors)
    h4_structure: Optional[str]
    h4_structure_healthy: Optional[bool]
    h1_structure: Optional[str]
    h1_structure_healthy: Optional[bool]
    m15_structure: Optional[str]
    m15_structure_healthy: Optional[bool]
    m5_structure: Optional[str]
    m5_structure_healthy: Optional[bool]

    # Volume factors (3 factors)
    vol_roc: Optional[float]
    vol_roc_healthy: Optional[bool]
    vol_delta: Optional[float]
    vol_delta_healthy: Optional[bool]
    cvd_slope: Optional[float]
    cvd_slope_healthy: Optional[bool]

    # Price/SMA factors (3 factors)
    sma9: Optional[float]
    sma21: Optional[float]
    sma_spread: Optional[float]
    sma_alignment: Optional[str]
    sma_alignment_healthy: Optional[bool]
    sma_momentum: Optional[float]
    sma_momentum_label: Optional[str]
    sma_momentum_healthy: Optional[bool]
    vwap: Optional[float]
    vwap_position: Optional[str]
    vwap_healthy: Optional[bool]

    # Composite scores
    health_score: Optional[int]
    health_label: Optional[str]
    structure_score: Optional[int]
    volume_score: Optional[int]
    price_score: Optional[int]

    # Metadata
    bars_used: int
    calculation_version: str


# =============================================================================
# HEALTH DETERMINATION FUNCTIONS
# =============================================================================

def is_structure_healthy(structure: str, trade_direction: str) -> bool:
    """
    Determine if structure is healthy for the trade direction.

    LONG trades: healthy if structure is BULL
    SHORT trades: healthy if structure is BEAR
    """
    if structure is None or trade_direction is None:
        return False

    structure = structure.upper()
    direction = trade_direction.upper()

    if direction == 'LONG':
        return structure == 'BULL'
    elif direction == 'SHORT':
        return structure == 'BEAR'
    return False


def is_vol_roc_healthy(vol_roc: float) -> bool:
    """
    Volume ROC is healthy if above average (positive ROC above threshold).
    Higher volume at entry = more conviction.
    """
    if vol_roc is None:
        return False
    return vol_roc >= VOLUME_ROC_ABOVE_AVG_THRESHOLD


def is_vol_delta_healthy(vol_delta: float, trade_direction: str) -> bool:
    """
    Volume delta is healthy if it aligns with trade direction.

    LONG: healthy if positive delta (more buying)
    SHORT: healthy if negative delta (more selling)
    """
    if vol_delta is None or trade_direction is None:
        return False

    direction = trade_direction.upper()

    if direction == 'LONG':
        return vol_delta > 0
    elif direction == 'SHORT':
        return vol_delta < 0
    return False


def is_cvd_slope_healthy(cvd_slope: float, trade_direction: str) -> bool:
    """
    CVD slope is healthy if it aligns with trade direction.

    LONG: healthy if rising CVD (bullish)
    SHORT: healthy if falling CVD (bearish)
    """
    if cvd_slope is None or trade_direction is None:
        return False

    direction = trade_direction.upper()

    if direction == 'LONG':
        return cvd_slope >= CVD_RISING_THRESHOLD
    elif direction == 'SHORT':
        return cvd_slope <= CVD_FALLING_THRESHOLD
    return False


def is_sma_alignment_healthy(sma_alignment: str, trade_direction: str) -> bool:
    """
    SMA alignment is healthy if SMA9 > SMA21 for LONG, SMA9 < SMA21 for SHORT.
    """
    if sma_alignment is None or trade_direction is None:
        return False

    alignment = sma_alignment.upper()
    direction = trade_direction.upper()

    if direction == 'LONG':
        return alignment == 'BULL'
    elif direction == 'SHORT':
        return alignment == 'BEAR'
    return False


def is_sma_momentum_healthy(sma_momentum_label: str) -> bool:
    """
    SMA momentum is healthy if spread is WIDENING (indicating trend strength).
    """
    if sma_momentum_label is None:
        return False
    return sma_momentum_label.upper() == 'WIDENING'


def is_vwap_healthy(vwap_position: str, trade_direction: str) -> bool:
    """
    VWAP position is healthy if price is above VWAP for LONG, below for SHORT.
    """
    if vwap_position is None or trade_direction is None:
        return False

    position = vwap_position.upper()
    direction = trade_direction.upper()

    if direction == 'LONG':
        return position == 'ABOVE'
    elif direction == 'SHORT':
        return position == 'BELOW'
    return False


def calculate_health_score(result: EntryIndicatorsResult) -> int:
    """
    Calculate composite health score (0-10).

    Structure: 4 points (H4, H1, M15, M5)
    Volume: 3 points (vol_roc, vol_delta, cvd_slope)
    Price: 3 points (sma_alignment, sma_momentum, vwap_position)
    """
    score = 0

    # Structure factors (4 points)
    if result.h4_structure_healthy:
        score += 1
    if result.h1_structure_healthy:
        score += 1
    if result.m15_structure_healthy:
        score += 1
    if result.m5_structure_healthy:
        score += 1

    # Volume factors (3 points)
    if result.vol_roc_healthy:
        score += 1
    if result.vol_delta_healthy:
        score += 1
    if result.cvd_slope_healthy:
        score += 1

    # Price factors (3 points)
    if result.sma_alignment_healthy:
        score += 1
    if result.sma_momentum_healthy:
        score += 1
    if result.vwap_healthy:
        score += 1

    return score


def get_health_label(score: int) -> str:
    """Get health label from score."""
    for label, (min_val, max_val) in HEALTH_BUCKETS.items():
        if min_val <= score <= max_val:
            return label
    return 'UNKNOWN'


def calculate_group_scores(result: EntryIndicatorsResult) -> Dict[str, int]:
    """Calculate scores for each factor group."""
    structure_score = sum([
        1 if result.h4_structure_healthy else 0,
        1 if result.h1_structure_healthy else 0,
        1 if result.m15_structure_healthy else 0,
        1 if result.m5_structure_healthy else 0,
    ])

    volume_score = sum([
        1 if result.vol_roc_healthy else 0,
        1 if result.vol_delta_healthy else 0,
        1 if result.cvd_slope_healthy else 0,
    ])

    price_score = sum([
        1 if result.sma_alignment_healthy else 0,
        1 if result.sma_momentum_healthy else 0,
        1 if result.vwap_healthy else 0,
    ])

    return {
        'structure_score': structure_score,
        'volume_score': volume_score,
        'price_score': price_score
    }


# =============================================================================
# MAIN CALCULATOR CLASS
# =============================================================================

class EntryIndicatorsCalculator:
    """
    Calculates entry indicators for a single trade.

    Uses M1 bars to calculate indicators at the bar immediately prior to entry.
    Uses HTF bars (M15, H1, H4) for structure detection.
    """

    def __init__(
        self,
        m1_provider: M1DataProvider = None,
        structure_analyzer: StructureAnalyzer = None,
        verbose: bool = True
    ):
        """
        Initialize the calculator.

        Args:
            m1_provider: M1DataProvider instance
            structure_analyzer: StructureAnalyzer instance
            verbose: Enable verbose logging
        """
        self.m1_provider = m1_provider or M1DataProvider()
        self.structure_analyzer = structure_analyzer or StructureAnalyzer()
        self.verbose = verbose
        self.logger = logging.getLogger(__name__)

    def _log(self, message: str, level: str = 'info'):
        """Log message if verbose mode enabled."""
        if self.verbose:
            prefix = {'error': '!', 'warning': '?', 'info': ' ', 'debug': '  '}
            print(f"  {prefix.get(level, ' ')} {message}")

    def calculate(self, trade: Dict[str, Any]) -> Optional[EntryIndicatorsResult]:
        """
        Calculate all entry indicators for a trade.

        Args:
            trade: Trade dictionary with keys:
                - trade_id, date, ticker, direction, model
                - entry_time, entry_price

        Returns:
            EntryIndicatorsResult or None if calculation fails
        """
        trade_id = trade.get('trade_id')
        ticker = trade.get('ticker')
        trade_date = trade.get('date')
        direction = trade.get('direction')
        model = trade.get('model')
        entry_time = trade.get('entry_time')
        entry_price = trade.get('entry_price')

        # Handle entry_time as timedelta (from psycopg2)
        if isinstance(entry_time, timedelta):
            total_seconds = int(entry_time.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            entry_time = time(hours, minutes, seconds)

        if entry_price:
            entry_price = float(entry_price)

        # Validate required fields
        if not all([trade_id, ticker, trade_date, direction, entry_time]):
            self._log(f"Missing required fields for {trade_id}", 'warning')
            return None

        # Get M1 bars up to entry time
        m1_bars = self.m1_provider.get_bars_before_time(
            ticker=ticker,
            trade_date=trade_date,
            before_time=entry_time
        )

        if not m1_bars:
            self._log(f"No M1 bars for {ticker} on {trade_date} before {entry_time}", 'warning')
            return None

        # Get the indicator bar (last complete M1 bar before entry)
        indicator_bar = m1_bars[-1]
        indicator_bar_time = indicator_bar.get('bar_time')

        # Aggregate to M5 for indicator calculations
        m5_bars = aggregate_to_m5(m1_bars)

        if len(m5_bars) < 25:  # Need enough bars for SMA21 + momentum lookback
            self._log(f"Insufficient M5 bars ({len(m5_bars)}) for {trade_id}", 'warning')
            return None

        # Calculate indicators on M5 bars
        sma_result = calculate_sma(m5_bars)
        sma_momentum_result = calculate_sma_momentum(m5_bars)

        # VWAP calculation on M1 bars (more accurate)
        vwap_result = calculate_vwap(m1_bars, price=entry_price)

        # Volume calculations on M5 bars
        vol_roc_result = calculate_volume_roc(m5_bars)
        vol_delta_result = calculate_volume_delta(m5_bars)
        cvd_result = calculate_cvd_slope(m5_bars)

        # Structure calculations
        structures = self.structure_analyzer.get_all_structures(
            ticker=ticker,
            trade_date=trade_date,
            entry_time=entry_time
        )

        # Extract values
        h4_structure = structures.get('H4')
        h1_structure = structures.get('H1')
        m15_structure = structures.get('M15')
        m5_structure = structures.get('M5')

        # Build partial result for health calculations
        partial_result = EntryIndicatorsResult(
            trade_id=trade_id,
            date=trade_date,
            ticker=ticker,
            direction=direction,
            model=model,
            entry_time=entry_time,
            entry_price=entry_price,
            indicator_bar_time=indicator_bar_time,
            indicator_methodology='M1_PRIOR',

            # Structure
            h4_structure=h4_structure.direction_label if h4_structure else None,
            h4_structure_healthy=None,
            h1_structure=h1_structure.direction_label if h1_structure else None,
            h1_structure_healthy=None,
            m15_structure=m15_structure.direction_label if m15_structure else None,
            m15_structure_healthy=None,
            m5_structure=m5_structure.direction_label if m5_structure else None,
            m5_structure_healthy=None,

            # Volume
            vol_roc=vol_roc_result.roc if vol_roc_result else None,
            vol_roc_healthy=None,
            vol_delta=vol_delta_result.rolling_delta if vol_delta_result else None,
            vol_delta_healthy=None,
            cvd_slope=cvd_result.slope if cvd_result else None,
            cvd_slope_healthy=None,

            # Price/SMA
            sma9=sma_result.sma9 if sma_result else None,
            sma21=sma_result.sma21 if sma_result else None,
            sma_spread=sma_result.spread if sma_result else None,
            sma_alignment=sma_result.alignment if sma_result else None,
            sma_alignment_healthy=None,
            sma_momentum=sma_momentum_result.ratio if sma_momentum_result else None,
            sma_momentum_label=sma_momentum_result.momentum if sma_momentum_result else None,
            sma_momentum_healthy=None,
            vwap=vwap_result.vwap if vwap_result else None,
            vwap_position=vwap_result.side if vwap_result else None,
            vwap_healthy=None,

            # Scores (to be calculated)
            health_score=None,
            health_label=None,
            structure_score=None,
            volume_score=None,
            price_score=None,

            # Metadata
            bars_used=len(m1_bars),
            calculation_version=CALCULATION_VERSION
        )

        # Calculate health for each factor
        partial_result.h4_structure_healthy = is_structure_healthy(partial_result.h4_structure, direction)
        partial_result.h1_structure_healthy = is_structure_healthy(partial_result.h1_structure, direction)
        partial_result.m15_structure_healthy = is_structure_healthy(partial_result.m15_structure, direction)
        partial_result.m5_structure_healthy = is_structure_healthy(partial_result.m5_structure, direction)

        partial_result.vol_roc_healthy = is_vol_roc_healthy(partial_result.vol_roc)
        partial_result.vol_delta_healthy = is_vol_delta_healthy(partial_result.vol_delta, direction)
        partial_result.cvd_slope_healthy = is_cvd_slope_healthy(partial_result.cvd_slope, direction)

        partial_result.sma_alignment_healthy = is_sma_alignment_healthy(partial_result.sma_alignment, direction)
        partial_result.sma_momentum_healthy = is_sma_momentum_healthy(partial_result.sma_momentum_label)
        partial_result.vwap_healthy = is_vwap_healthy(partial_result.vwap_position, direction)

        # Calculate composite scores
        partial_result.health_score = calculate_health_score(partial_result)
        partial_result.health_label = get_health_label(partial_result.health_score)

        group_scores = calculate_group_scores(partial_result)
        partial_result.structure_score = group_scores['structure_score']
        partial_result.volume_score = group_scores['volume_score']
        partial_result.price_score = group_scores['price_score']

        return partial_result

    def close(self):
        """Close resources."""
        self.m1_provider.close()
        self.structure_analyzer.clear_cache()
