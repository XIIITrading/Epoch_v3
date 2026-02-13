"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
Indicator Refinement - Core Calculator
XIII Trading LLC
================================================================================

Calculates Continuation and Rejection scores for trades based on the
Epoch Indicator Model Specification v1.0.

Trade Classification:
    - CONTINUATION (EPCH01/EPCH03): With-trend trades, scored 0-10
    - REJECTION (EPCH02/EPCH04): Counter-trend/exhaustion, scored 0-11

Version: 1.0.0
================================================================================
"""

from dataclasses import dataclass
from datetime import date, time
from typing import Dict, List, Optional, Any
import logging

from config import (
    CONTINUATION_MODELS,
    REJECTION_MODELS,
    CONTINUATION_THRESHOLDS,
    REJECTION_THRESHOLDS,
    CALCULATION_VERSION
)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class IndicatorRefinementResult:
    """Complete indicator refinement result for a single trade."""

    # =========================================================================
    # TRADE IDENTIFICATION
    # =========================================================================
    trade_id: str
    date: date
    ticker: str
    direction: str      # LONG, SHORT
    model: str          # EPCH01, EPCH02, EPCH03, EPCH04
    entry_time: time
    entry_price: float

    # Trade classification
    trade_type: str     # CONTINUATION, REJECTION

    # =========================================================================
    # CONTINUATION INDICATORS (CONT-01 to CONT-04)
    # =========================================================================

    # CONT-01: MTF Alignment (0-4 points)
    mtf_align_score: Optional[int]
    mtf_h4_aligned: Optional[bool]
    mtf_h1_aligned: Optional[bool]
    mtf_m15_aligned: Optional[bool]
    mtf_m5_aligned: Optional[bool]

    # CONT-02: SMA Momentum (0-2 points)
    sma_mom_score: Optional[int]
    sma_spread: Optional[float]
    sma_spread_pct: Optional[float]
    sma_spread_roc: Optional[float]
    sma_spread_aligned: Optional[bool]
    sma_spread_expanding: Optional[bool]

    # CONT-03: Volume Thrust (0-2 points)
    vol_thrust_score: Optional[int]
    vol_roc: Optional[float]
    vol_delta_5: Optional[float]
    vol_roc_strong: Optional[bool]
    vol_delta_aligned: Optional[bool]

    # CONT-04: Pullback Quality (0-2 points)
    pullback_score: Optional[int]
    in_pullback: Optional[bool]
    pullback_delta_ratio: Optional[float]

    # Continuation Composite (0-10)
    continuation_score: Optional[int]
    continuation_label: Optional[str]   # STRONG, GOOD, WEAK, AVOID

    # =========================================================================
    # REJECTION INDICATORS (REJ-01 to REJ-05)
    # =========================================================================

    # REJ-01: Structure Divergence (0-2 points)
    struct_div_score: Optional[int]
    htf_aligned: Optional[bool]
    ltf_divergent: Optional[bool]

    # REJ-02: SMA Exhaustion (0-3 points)
    sma_exhst_score: Optional[int]
    sma_spread_contracting: Optional[bool]
    sma_spread_very_tight: Optional[bool]
    sma_spread_tight: Optional[bool]

    # REJ-03: Delta Absorption (0-2 points)
    delta_abs_score: Optional[int]
    absorption_ratio: Optional[float]

    # REJ-04: Volume Climax (0-2 points)
    vol_climax_score: Optional[int]
    vol_roc_q5: Optional[bool]
    vol_declining: Optional[bool]

    # REJ-05: CVD Extreme (0-2 points)
    cvd_extr_score: Optional[int]
    cvd_slope: Optional[float]
    cvd_slope_normalized: Optional[float]
    cvd_extreme: Optional[bool]

    # Rejection Composite (0-11)
    rejection_score: Optional[int]
    rejection_label: Optional[str]      # STRONG, GOOD, WEAK, AVOID

    # =========================================================================
    # OUTCOME (populated later by validation)
    # =========================================================================
    trade_outcome: Optional[str]
    outcome_validated: bool = False

    # =========================================================================
    # METADATA
    # =========================================================================
    calculation_version: str = CALCULATION_VERSION


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_composite_label(score: int, thresholds: Dict[str, tuple]) -> str:
    """Get label from score based on threshold ranges."""
    if score is None:
        return 'UNKNOWN'
    for label, (min_val, max_val) in thresholds.items():
        if min_val <= score <= max_val:
            return label
    return 'UNKNOWN'


def determine_trade_type(model: str) -> str:
    """Determine if trade is CONTINUATION or REJECTION based on model."""
    if model is None:
        return 'UNKNOWN'
    model = model.upper()
    if model in CONTINUATION_MODELS:
        return 'CONTINUATION'
    elif model in REJECTION_MODELS:
        return 'REJECTION'
    else:
        return 'UNKNOWN'


# =============================================================================
# MAIN CALCULATOR CLASS
# =============================================================================

class IndicatorRefinementCalculator:
    """
    Calculates continuation and rejection scores for trades.

    Uses entry_indicators data + M5 bar data for scoring.
    All trades get both scores calculated, but the primary score
    is determined by trade_type (CONTINUATION vs REJECTION).
    """

    def __init__(self, verbose: bool = True):
        """
        Initialize the calculator.

        Args:
            verbose: Enable verbose logging
        """
        self.verbose = verbose
        self.logger = logging.getLogger(__name__)

    def _log(self, message: str, level: str = 'info'):
        """Log message if verbose mode enabled."""
        if self.verbose:
            prefix = {'error': '!', 'warning': '?', 'info': ' ', 'debug': '  '}
            print(f"  {prefix.get(level, ' ')} {message}")

    def calculate(
        self,
        trade: Dict[str, Any],
        entry_indicators: Dict[str, Any],
        m5_bars: List[Dict],
        structure_data: Optional[Dict[str, Any]] = None
    ) -> Optional[IndicatorRefinementResult]:
        """
        Calculate all indicator refinement scores for a trade.

        Args:
            trade: Trade data dict with trade_id, direction, model, etc.
            entry_indicators: Entry indicators data from entry_indicators table
            m5_bars: M5 bars from m5_indicator_bars table
            structure_data: Optional HTF structure data (uses entry_indicators if None)

        Returns:
            IndicatorRefinementResult or None if calculation fails
        """
        # Import calculation modules here to avoid circular imports
        from continuation_calc import (
            calculate_mtf_alignment,
            calculate_sma_momentum,
            calculate_volume_thrust,
            calculate_pullback_quality
        )
        from rejection_calc import (
            calculate_structure_divergence,
            calculate_sma_exhaustion,
            calculate_delta_absorption,
            calculate_volume_climax,
            calculate_cvd_extreme
        )

        trade_id = trade.get('trade_id')
        model = trade.get('model')
        direction = trade.get('direction')
        trade_type = determine_trade_type(model)

        if trade_type == 'UNKNOWN':
            self._log(f"Unknown model type: {model} for {trade_id}", 'warning')
            return None

        # Use entry_indicators for structure if not provided separately
        if structure_data is None:
            structure_data = {
                'h4_structure': entry_indicators.get('h4_structure'),
                'h1_structure': entry_indicators.get('h1_structure'),
                'm15_structure': entry_indicators.get('m15_structure'),
                'm5_structure': entry_indicators.get('m5_structure'),
            }

        # Get entry price
        entry_price = trade.get('entry_price')
        if entry_price is not None:
            entry_price = float(entry_price)

        # Initialize result with trade context
        result = IndicatorRefinementResult(
            trade_id=trade_id,
            date=trade.get('date'),
            ticker=trade.get('ticker'),
            direction=direction,
            model=model,
            entry_time=trade.get('entry_time'),
            entry_price=entry_price,
            trade_type=trade_type,

            # Initialize all scores to None
            mtf_align_score=None, mtf_h4_aligned=None, mtf_h1_aligned=None,
            mtf_m15_aligned=None, mtf_m5_aligned=None,
            sma_mom_score=None, sma_spread=None, sma_spread_pct=None,
            sma_spread_roc=None, sma_spread_aligned=None, sma_spread_expanding=None,
            vol_thrust_score=None, vol_roc=None, vol_delta_5=None,
            vol_roc_strong=None, vol_delta_aligned=None,
            pullback_score=None, in_pullback=None, pullback_delta_ratio=None,
            continuation_score=None, continuation_label=None,

            struct_div_score=None, htf_aligned=None, ltf_divergent=None,
            sma_exhst_score=None, sma_spread_contracting=None,
            sma_spread_very_tight=None, sma_spread_tight=None,
            delta_abs_score=None, absorption_ratio=None,
            vol_climax_score=None, vol_roc_q5=None, vol_declining=None,
            cvd_extr_score=None, cvd_slope=None, cvd_slope_normalized=None,
            cvd_extreme=None, rejection_score=None, rejection_label=None,

            trade_outcome=None, outcome_validated=False,
            calculation_version=CALCULATION_VERSION
        )

        # Calculate CONTINUATION indicators (for all trades)
        self._calculate_continuation_indicators(
            result, entry_indicators, m5_bars, structure_data, direction
        )

        # Calculate REJECTION indicators (for all trades)
        self._calculate_rejection_indicators(
            result, entry_indicators, m5_bars, direction
        )

        # Calculate composite scores
        self._calculate_composite_scores(result)

        return result

    def _calculate_continuation_indicators(
        self,
        result: IndicatorRefinementResult,
        entry_ind: Dict,
        m5_bars: List,
        structure: Dict,
        direction: str
    ):
        """Calculate CONT-01 through CONT-04."""
        from continuation_calc import (
            calculate_mtf_alignment,
            calculate_sma_momentum,
            calculate_volume_thrust,
            calculate_pullback_quality
        )

        # CONT-01: MTF Alignment
        mtf = calculate_mtf_alignment(structure, direction)
        result.mtf_align_score = mtf['score']
        result.mtf_h4_aligned = mtf['h4_aligned']
        result.mtf_h1_aligned = mtf['h1_aligned']
        result.mtf_m15_aligned = mtf['m15_aligned']
        result.mtf_m5_aligned = mtf['m5_aligned']

        # CONT-02: SMA Momentum
        sma_mom = calculate_sma_momentum(entry_ind, m5_bars, direction)
        result.sma_mom_score = sma_mom['score']
        result.sma_spread = sma_mom['spread']
        result.sma_spread_pct = sma_mom['spread_pct']
        result.sma_spread_roc = sma_mom['spread_roc']
        result.sma_spread_aligned = sma_mom['aligned']
        result.sma_spread_expanding = sma_mom['expanding']

        # CONT-03: Volume Thrust
        vol_thrust = calculate_volume_thrust(entry_ind, m5_bars, direction)
        result.vol_thrust_score = vol_thrust['score']
        result.vol_roc = vol_thrust['vol_roc']
        result.vol_delta_5 = vol_thrust['vol_delta_5']
        result.vol_roc_strong = vol_thrust['roc_strong']
        result.vol_delta_aligned = vol_thrust['delta_aligned']

        # CONT-04: Pullback Quality
        pullback = calculate_pullback_quality(entry_ind, m5_bars, direction)
        result.pullback_score = pullback['score']
        result.in_pullback = pullback['in_pullback']
        result.pullback_delta_ratio = pullback['delta_ratio']

    def _calculate_rejection_indicators(
        self,
        result: IndicatorRefinementResult,
        entry_ind: Dict,
        m5_bars: List,
        direction: str
    ):
        """Calculate REJ-01 through REJ-05."""
        from rejection_calc import (
            calculate_structure_divergence,
            calculate_sma_exhaustion,
            calculate_delta_absorption,
            calculate_volume_climax,
            calculate_cvd_extreme
        )

        # REJ-01: Structure Divergence
        struct_div = calculate_structure_divergence(entry_ind, direction)
        result.struct_div_score = struct_div['score']
        result.htf_aligned = struct_div['htf_aligned']
        result.ltf_divergent = struct_div['ltf_divergent']

        # REJ-02: SMA Exhaustion
        sma_exhst = calculate_sma_exhaustion(entry_ind, m5_bars)
        result.sma_exhst_score = sma_exhst['score']
        result.sma_spread_contracting = sma_exhst['contracting']
        result.sma_spread_very_tight = sma_exhst['very_tight']
        result.sma_spread_tight = sma_exhst['tight']

        # REJ-03: Delta Absorption
        delta_abs = calculate_delta_absorption(m5_bars)
        result.delta_abs_score = delta_abs['score']
        result.absorption_ratio = delta_abs['ratio']

        # REJ-04: Volume Climax
        vol_climax = calculate_volume_climax(entry_ind, m5_bars)
        result.vol_climax_score = vol_climax['score']
        result.vol_roc_q5 = vol_climax['roc_q5']
        result.vol_declining = vol_climax['declining']

        # REJ-05: CVD Extreme
        cvd_extr = calculate_cvd_extreme(m5_bars, direction)
        result.cvd_extr_score = cvd_extr['score']
        result.cvd_slope = cvd_extr['slope']
        result.cvd_slope_normalized = cvd_extr['slope_normalized']
        result.cvd_extreme = cvd_extr['extreme']

    def _calculate_composite_scores(self, result: IndicatorRefinementResult):
        """Calculate composite continuation and rejection scores."""

        # Continuation Score = MTF_ALIGN + SMA_MOM + VOL_THRUST + PULLBACK_Q
        cont_score = sum([
            result.mtf_align_score or 0,
            result.sma_mom_score or 0,
            result.vol_thrust_score or 0,
            result.pullback_score or 0
        ])
        result.continuation_score = cont_score
        result.continuation_label = get_composite_label(cont_score, CONTINUATION_THRESHOLDS)

        # Rejection Score = STRUCT_DIV + SMA_EXHST + DELTA_ABS + VOL_CLIMAX + CVD_EXTR
        rej_score = sum([
            result.struct_div_score or 0,
            result.sma_exhst_score or 0,
            result.delta_abs_score or 0,
            result.vol_climax_score or 0,
            result.cvd_extr_score or 0
        ])
        result.rejection_score = rej_score
        result.rejection_label = get_composite_label(rej_score, REJECTION_THRESHOLDS)
