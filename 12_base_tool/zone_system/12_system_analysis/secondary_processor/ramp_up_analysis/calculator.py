"""
================================================================================
EPOCH TRADING SYSTEM - RAMP-UP ANALYSIS
Calculator - Compute macro metrics (avgs, trends, momentum)
XIII Trading LLC
================================================================================

Calculates ramp-up metrics from raw M1 indicator bars:
- Averages across the ramp period
- Trends via linear regression
- Momentum via first-half vs second-half comparison
- Structure consistency for categorical indicators

================================================================================
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import time
import logging

from .ramp_config import (
    LOOKBACK_BARS,
    INDICATORS,
    NUMERIC_INDICATORS,
    CATEGORICAL_INDICATORS,
    TREND_THRESHOLD,
    MOMENTUM_THRESHOLD,
    MOMENTUM_SPLIT_BAR,
    TREND_LABELS,
    MOMENTUM_LABELS,
    STRUCTURE_CONSISTENCY_LABELS,
    MIN_BARS_REQUIRED,
)

logger = logging.getLogger(__name__)


@dataclass
class RampUpMacro:
    """
    Summary metrics for a single trade's ramp-up period.
    Corresponds to one row in ramp_up_macro table.
    """
    # Trade identity
    trade_id: str
    date: Any  # date object
    ticker: str
    model: str
    direction: str
    entry_time: time
    stop_type: str
    lookback_bars: int

    # Outcome metrics
    outcome: str
    mfe_distance: Optional[float]
    r_achieved: Optional[float]

    # Entry bar snapshot (bar 0)
    entry_candle_range_pct: Optional[float] = None
    entry_vol_delta: Optional[float] = None
    entry_vol_roc: Optional[float] = None
    entry_sma_spread: Optional[float] = None
    entry_sma_momentum_ratio: Optional[float] = None
    entry_m15_structure: Optional[str] = None
    entry_h1_structure: Optional[str] = None
    entry_long_score: Optional[int] = None
    entry_short_score: Optional[int] = None

    # Ramp averages
    ramp_avg_candle_range_pct: Optional[float] = None
    ramp_avg_vol_delta: Optional[float] = None
    ramp_avg_vol_roc: Optional[float] = None
    ramp_avg_sma_spread: Optional[float] = None
    ramp_avg_sma_momentum_ratio: Optional[float] = None
    ramp_avg_long_score: Optional[float] = None
    ramp_avg_short_score: Optional[float] = None

    # Ramp trends (linear regression)
    ramp_trend_candle_range_pct: Optional[str] = None
    ramp_trend_vol_delta: Optional[str] = None
    ramp_trend_vol_roc: Optional[str] = None
    ramp_trend_sma_spread: Optional[str] = None
    ramp_trend_sma_momentum_ratio: Optional[str] = None
    ramp_trend_long_score: Optional[str] = None
    ramp_trend_short_score: Optional[str] = None

    # Ramp momentum (first-half vs second-half)
    ramp_momentum_candle_range_pct: Optional[str] = None
    ramp_momentum_vol_delta: Optional[str] = None
    ramp_momentum_vol_roc: Optional[str] = None
    ramp_momentum_sma_spread: Optional[str] = None
    ramp_momentum_sma_momentum_ratio: Optional[str] = None
    ramp_momentum_long_score: Optional[str] = None
    ramp_momentum_short_score: Optional[str] = None

    # Structure consistency
    ramp_structure_m15: Optional[str] = None
    ramp_structure_h1: Optional[str] = None

    # Metadata
    bars_analyzed: int = 0


@dataclass
class RampUpProgression:
    """
    Single bar in the ramp-up progression.
    Corresponds to one row in ramp_up_progression table.
    """
    trade_id: str
    bars_to_entry: int  # -15 to 0
    bar_time: time

    # Raw indicator values
    candle_range_pct: Optional[float] = None
    vol_delta: Optional[float] = None
    vol_roc: Optional[float] = None
    sma_spread: Optional[float] = None
    sma_momentum_ratio: Optional[float] = None
    m15_structure: Optional[str] = None
    h1_structure: Optional[str] = None
    long_score: Optional[int] = None
    short_score: Optional[int] = None


class RampUpCalculator:
    """
    Calculates ramp-up metrics from raw bar data.
    """

    def __init__(self, stop_type: str, lookback_bars: int = LOOKBACK_BARS):
        self.stop_type = stop_type
        self.lookback_bars = lookback_bars

    def calculate(
        self,
        trade: Dict[str, Any]
    ) -> Tuple[Optional[RampUpMacro], List[RampUpProgression]]:
        """
        Calculate ramp-up metrics for a single trade.

        Parameters:
            trade: Trade dict with m1_bars list

        Returns:
            Tuple of (RampUpMacro, list of RampUpProgression)
            Returns (None, []) if insufficient data
        """
        bars = trade.get('m1_bars', [])

        # Validate minimum bars
        if len(bars) < MIN_BARS_REQUIRED:
            logger.debug(
                f"Skipping {trade['trade_id']}: only {len(bars)} bars "
                f"(need {MIN_BARS_REQUIRED})"
            )
            return None, []

        # Calculate bars_to_entry for each bar
        # Last bar is entry (bar 0), work backwards
        num_bars = len(bars)
        for i, bar in enumerate(bars):
            bar['bars_to_entry'] = i - (num_bars - 1)  # -15, -14, ..., 0

        # Separate entry bar (bar 0) from ramp bars (bar -15 to -1)
        entry_bar = bars[-1]  # Last bar is entry
        ramp_bars = bars[:-1]  # All bars except entry

        # Build progression records
        progression = self._build_progression(trade['trade_id'], bars)

        # Build macro record
        macro = self._build_macro(trade, entry_bar, ramp_bars)

        return macro, progression

    def _build_progression(
        self,
        trade_id: str,
        bars: List[Dict[str, Any]]
    ) -> List[RampUpProgression]:
        """
        Build progression records from bars.
        """
        progression = []
        for bar in bars:
            prog = RampUpProgression(
                trade_id=trade_id,
                bars_to_entry=bar['bars_to_entry'],
                bar_time=bar['bar_time'],
                candle_range_pct=self._safe_float(bar.get('candle_range_pct')),
                vol_delta=self._safe_float(bar.get('vol_delta')),
                vol_roc=self._safe_float(bar.get('vol_roc')),
                sma_spread=self._safe_float(bar.get('sma_spread')),
                sma_momentum_ratio=self._safe_float(bar.get('sma_momentum_ratio')),
                m15_structure=bar.get('m15_structure'),
                h1_structure=bar.get('h1_structure'),
                long_score=self._safe_int(bar.get('long_score')),
                short_score=self._safe_int(bar.get('short_score')),
            )
            progression.append(prog)
        return progression

    def _build_macro(
        self,
        trade: Dict[str, Any],
        entry_bar: Dict[str, Any],
        ramp_bars: List[Dict[str, Any]]
    ) -> RampUpMacro:
        """
        Build macro summary record.
        """
        # Initialize macro with trade identity
        macro = RampUpMacro(
            trade_id=trade['trade_id'],
            date=trade['date'],
            ticker=trade['ticker'],
            model=trade['model'],
            direction=trade['direction'],
            entry_time=trade['entry_time'],
            stop_type=self.stop_type,
            lookback_bars=self.lookback_bars,
            outcome=trade['outcome'],
            mfe_distance=self._safe_float(trade.get('mfe_distance')),
            r_achieved=self._safe_float(trade.get('r_achieved')),
            bars_analyzed=len(ramp_bars) + 1,  # +1 for entry bar
        )

        # Entry bar snapshot
        macro.entry_candle_range_pct = self._safe_float(entry_bar.get('candle_range_pct'))
        macro.entry_vol_delta = self._safe_float(entry_bar.get('vol_delta'))
        macro.entry_vol_roc = self._safe_float(entry_bar.get('vol_roc'))
        macro.entry_sma_spread = self._safe_float(entry_bar.get('sma_spread'))
        macro.entry_sma_momentum_ratio = self._safe_float(entry_bar.get('sma_momentum_ratio'))
        macro.entry_m15_structure = entry_bar.get('m15_structure')
        macro.entry_h1_structure = entry_bar.get('h1_structure')
        macro.entry_long_score = self._safe_int(entry_bar.get('long_score'))
        macro.entry_short_score = self._safe_int(entry_bar.get('short_score'))

        # Calculate metrics for each numeric indicator
        for indicator in NUMERIC_INDICATORS:
            values = self._extract_values(ramp_bars, indicator)
            if values:
                # Average
                avg = np.mean(values)
                setattr(macro, f'ramp_avg_{indicator}', float(avg))

                # Trend (linear regression)
                trend = self._calculate_trend(values)
                setattr(macro, f'ramp_trend_{indicator}', trend)

                # Momentum (first-half vs second-half)
                momentum = self._calculate_momentum(ramp_bars, indicator)
                setattr(macro, f'ramp_momentum_{indicator}', momentum)

        # Calculate structure consistency for categorical indicators
        macro.ramp_structure_m15 = self._calculate_structure_consistency(
            ramp_bars, 'm15_structure'
        )
        macro.ramp_structure_h1 = self._calculate_structure_consistency(
            ramp_bars, 'h1_structure'
        )

        return macro

    def _extract_values(
        self,
        bars: List[Dict[str, Any]],
        indicator: str
    ) -> List[float]:
        """
        Extract non-null numeric values for an indicator.
        """
        values = []
        for bar in bars:
            val = bar.get(indicator)
            if val is not None:
                try:
                    values.append(float(val))
                except (ValueError, TypeError):
                    pass
        return values

    def _calculate_trend(self, values: List[float]) -> str:
        """
        Calculate trend using linear regression slope.

        Returns: RISING, FALLING, or FLAT
        """
        if len(values) < 3:
            return TREND_LABELS['flat']

        # Fit linear regression
        x = np.arange(len(values))
        slope, _ = np.polyfit(x, values, 1)

        # Normalize slope by value range
        value_range = max(values) - min(values)
        if value_range == 0:
            return TREND_LABELS['flat']

        normalized_slope = slope * len(values) / value_range

        # Classify
        if normalized_slope > TREND_THRESHOLD:
            return TREND_LABELS['rising']
        elif normalized_slope < -TREND_THRESHOLD:
            return TREND_LABELS['falling']
        else:
            return TREND_LABELS['flat']

    def _calculate_momentum(
        self,
        bars: List[Dict[str, Any]],
        indicator: str
    ) -> str:
        """
        Calculate momentum by comparing first-half vs second-half averages.

        Returns: BUILDING, FADING, or STABLE
        """
        # Split bars into first half and second half
        first_half = []
        second_half = []

        for bar in bars:
            val = bar.get(indicator)
            if val is None:
                continue
            try:
                val = float(val)
            except (ValueError, TypeError):
                continue

            # bars_to_entry is negative (-15 to -1)
            if bar['bars_to_entry'] <= MOMENTUM_SPLIT_BAR:
                first_half.append(val)
            else:
                second_half.append(val)

        if not first_half or not second_half:
            return MOMENTUM_LABELS['stable']

        first_avg = np.mean(first_half)
        second_avg = np.mean(second_half)

        # Calculate percentage change
        if first_avg == 0:
            if second_avg == 0:
                return MOMENTUM_LABELS['stable']
            else:
                return MOMENTUM_LABELS['building'] if second_avg > 0 else MOMENTUM_LABELS['fading']

        pct_change = (second_avg - first_avg) / abs(first_avg)

        # Classify
        if pct_change > MOMENTUM_THRESHOLD:
            return MOMENTUM_LABELS['building']
        elif pct_change < -MOMENTUM_THRESHOLD:
            return MOMENTUM_LABELS['fading']
        else:
            return MOMENTUM_LABELS['stable']

    def _calculate_structure_consistency(
        self,
        bars: List[Dict[str, Any]],
        indicator: str
    ) -> str:
        """
        Calculate structure consistency for categorical indicators.

        Returns: CONSISTENT_BULL, CONSISTENT_BEAR, MIXED, FLIP_TO_BULL, etc.
        """
        values = [bar.get(indicator) for bar in bars if bar.get(indicator)]

        if not values:
            return STRUCTURE_CONSISTENCY_LABELS['mixed']

        # Count occurrences
        counts = {}
        for v in values:
            counts[v] = counts.get(v, 0) + 1

        total = len(values)
        dominant = max(counts, key=counts.get)
        dominant_pct = counts[dominant] / total

        # Check for consistency (>80% same value)
        if dominant_pct >= 0.8:
            if dominant == 'BULL':
                return STRUCTURE_CONSISTENCY_LABELS['consistent_bull']
            elif dominant == 'BEAR':
                return STRUCTURE_CONSISTENCY_LABELS['consistent_bear']
            else:
                return STRUCTURE_CONSISTENCY_LABELS['consistent_neutral']

        # Check for flip pattern (different at start vs end)
        if len(values) >= 3:
            start_val = values[0]
            end_val = values[-1]

            if start_val != end_val:
                if end_val == 'BULL':
                    return STRUCTURE_CONSISTENCY_LABELS['flip_to_bull']
                elif end_val == 'BEAR':
                    return STRUCTURE_CONSISTENCY_LABELS['flip_to_bear']

        return STRUCTURE_CONSISTENCY_LABELS['mixed']

    def _safe_float(self, val: Any) -> Optional[float]:
        """Safely convert to float."""
        if val is None:
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    def _safe_int(self, val: Any) -> Optional[int]:
        """Safely convert to int."""
        if val is None:
            return None
        try:
            return int(val)
        except (ValueError, TypeError):
            return None


def calculate_for_trades(
    trades: List[Dict[str, Any]],
    stop_type: str,
    lookback_bars: int = LOOKBACK_BARS
) -> Tuple[List[RampUpMacro], List[RampUpProgression]]:
    """
    Calculate ramp-up metrics for multiple trades.

    Parameters:
        trades: List of trade dicts with m1_bars
        stop_type: Stop type used for outcomes
        lookback_bars: Number of bars to analyze

    Returns:
        Tuple of (list of RampUpMacro, list of RampUpProgression)
    """
    calculator = RampUpCalculator(stop_type=stop_type, lookback_bars=lookback_bars)

    all_macros = []
    all_progressions = []

    for trade in trades:
        macro, progressions = calculator.calculate(trade)
        if macro:
            all_macros.append(macro)
            all_progressions.extend(progressions)

    return all_macros, all_progressions
