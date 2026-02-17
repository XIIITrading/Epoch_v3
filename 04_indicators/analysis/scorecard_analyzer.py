"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 04: INDICATOR ANALYSIS v2.0
Scorecard Analyzer - Orchestrates data loading, segmentation, and ranking
XIII Trading LLC
================================================================================

Produces complete trade-type scorecards by:
1. Loading entry + ramp-up data from Supabase via DataProvider
2. Segmenting trades into 4 types (Long/Short × Continuation/Rejection)
3. Running statistical tier ranking on all 11 indicators per trade type
4. Computing ramp-up divergence and acceleration for continuous indicators
5. Selecting top N indicators per trade type
6. Comparing against prior run for degradation detection
"""
import json
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from analysis.tier_ranker import TierRanker, IndicatorScore
from config import (
    ALL_DEEP_DIVE_INDICATORS,
    RAMP_UP_ACCEL_BARS,
    RAMP_UP_ANALYSIS_BARS,
    SCORECARD_TOP_N,
    TRADE_TYPES,
)
from data.provider import DataProvider


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class TradeTypeResult:
    """Complete analysis result for a single trade type."""

    trade_type_key: str         # e.g., 'long_continuation'
    label: str                  # e.g., 'Long Continuation'
    direction: str              # 'LONG' or 'SHORT'
    models: List[str]           # ['EPCH1', 'EPCH3']
    total_trades: int
    winners: int
    losers: int
    win_rate: float
    avg_r: float
    all_scores: List[IndicatorScore]    # all 11 indicators ranked
    top_scores: List[IndicatorScore]    # top N by tier ranking


@dataclass
class DegradationFlag:
    """A single degradation observation."""

    indicator_col: str
    indicator_label: str
    trade_type_key: str
    flag_type: str          # 'tier_drop', 'effect_drop', 'top5_demotion'
    message: str
    prior_value: str
    current_value: str


@dataclass
class ScorecardResult:
    """Full scorecard analysis output."""

    run_date: str
    date_from: Optional[str]
    date_to: Optional[str]
    total_trades: int
    trade_type_results: Dict[str, TradeTypeResult]
    degradation_flags: List[DegradationFlag] = field(default_factory=list)


# =============================================================================
# SCORECARD ANALYZER
# =============================================================================


class ScorecardAnalyzer:
    """Produces scorecards for all 4 trade types."""

    def __init__(self, provider: DataProvider, verbose: bool = False):
        self._provider = provider
        self._ranker = TierRanker()
        self._verbose = verbose

    def analyze(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        prior_results_dir: Optional[Path] = None,
    ) -> ScorecardResult:
        """
        Run full scorecard analysis across all 4 trade types.

        Parameters
        ----------
        date_from : date, optional
            Start date filter. Uses all available data if None.
        date_to : date, optional
            End date filter. Uses all available data if None.
        prior_results_dir : Path, optional
            Path to a previous scorecard run for degradation comparison.

        Returns
        -------
        ScorecardResult with all 4 trade type analyses.
        """
        self._log("Starting scorecard analysis...")

        # Load ALL entry data once (we'll filter in Python per trade type)
        self._log("Loading entry data from Supabase...")
        all_entry_data = self._provider.get_entry_data(
            date_from=date_from, date_to=date_to,
        )
        total_trades = len(all_entry_data)
        self._log(f"  Loaded {total_trades:,} total trades")

        if total_trades == 0:
            self._log("WARNING: No trades found for the specified date range.")
            return ScorecardResult(
                run_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                date_from=str(date_from) if date_from else None,
                date_to=str(date_to) if date_to else None,
                total_trades=0,
                trade_type_results={},
            )

        # Analyze each trade type
        results: Dict[str, TradeTypeResult] = {}
        for tt_key, tt_config in TRADE_TYPES.items():
            self._log(f"\nAnalyzing {tt_config['label']}...")
            result = self._analyze_trade_type(
                tt_key, tt_config, all_entry_data,
            )
            results[tt_key] = result
            self._log(
                f"  {result.total_trades} trades, "
                f"{result.win_rate:.1f}% WR, "
                f"top tier: {result.top_scores[0].tier if result.top_scores else 'N/A'}"
            )

        # Degradation check
        degradation_flags: List[DegradationFlag] = []
        if prior_results_dir:
            self._log(f"\nChecking degradation vs {prior_results_dir}...")
            prior_data = self._load_prior_results(prior_results_dir)
            if prior_data:
                degradation_flags = self._compute_degradation(results, prior_data)
                self._log(f"  {len(degradation_flags)} degradation flag(s) found")
            else:
                self._log("  No prior results found, skipping degradation check")

        return ScorecardResult(
            run_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            date_from=str(date_from) if date_from else None,
            date_to=str(date_to) if date_to else None,
            total_trades=total_trades,
            trade_type_results=results,
            degradation_flags=degradation_flags,
        )

    # ------------------------------------------------------------------
    # Per trade type analysis
    # ------------------------------------------------------------------
    def _analyze_trade_type(
        self,
        tt_key: str,
        tt_config: dict,
        all_entry_data: pd.DataFrame,
    ) -> TradeTypeResult:
        """Analyze a single trade type (e.g., long_continuation)."""
        direction = tt_config["direction"]
        models = tt_config["models"]

        # Filter entry data for this trade type
        mask = (
            (all_entry_data["direction"] == direction)
            & (all_entry_data["model"].isin(models))
        )
        entry_data = all_entry_data[mask].copy()
        total_trades = len(entry_data)

        if total_trades == 0:
            return TradeTypeResult(
                trade_type_key=tt_key,
                label=tt_config["label"],
                direction=direction,
                models=models,
                total_trades=0,
                winners=0,
                losers=0,
                win_rate=0.0,
                avg_r=0.0,
                all_scores=[],
                top_scores=[],
            )

        # Baseline stats
        winners = int(entry_data["is_winner"].sum())
        losers = total_trades - winners
        win_rate = winners / total_trades * 100
        avg_r = entry_data["pnl_r"].mean() if "pnl_r" in entry_data.columns else 0.0

        # Get trade IDs for ramp-up queries
        trade_ids = entry_data["trade_id"].tolist()

        # Rank all 11 indicators
        all_scores: List[IndicatorScore] = []

        for col, label, ind_type in ALL_DEEP_DIVE_INDICATORS:
            if col not in entry_data.columns:
                continue

            # Compute ramp-up metrics for continuous indicators
            ramp_div = 0.0
            ramp_accel = 0.0
            if ind_type == "continuous":
                ramp_div, ramp_accel = self._compute_ramp_divergence(
                    trade_ids, col,
                )

            # Rank the indicator
            if ind_type == "categorical":
                score = self._ranker.rank_categorical(
                    entry_data, col, label, win_rate, direction,
                    ramp_divergence=ramp_div,
                    ramp_acceleration=ramp_accel,
                )
            else:
                score = self._ranker.rank_continuous(
                    entry_data, col, label, win_rate, direction,
                    ramp_divergence=ramp_div,
                    ramp_acceleration=ramp_accel,
                )

            all_scores.append(score)

        # Sort: by tier rank (S=0 first), then by effect size descending
        all_scores.sort(key=lambda s: (s.tier_rank, -s.effect_size))

        # Always select top N — include all tiers (even Rejected)
        # so every scorecard has a consistent 5-indicator structure
        top_scores = all_scores[:SCORECARD_TOP_N]

        return TradeTypeResult(
            trade_type_key=tt_key,
            label=tt_config["label"],
            direction=direction,
            models=models,
            total_trades=total_trades,
            winners=winners,
            losers=losers,
            win_rate=round(win_rate, 1),
            avg_r=round(avg_r, 2),
            all_scores=all_scores,
            top_scores=top_scores,
        )

    # ------------------------------------------------------------------
    # Ramp-up divergence and acceleration
    # ------------------------------------------------------------------
    def _compute_ramp_divergence(
        self, trade_ids: List[str], indicator_col: str,
    ) -> Tuple[float, float]:
        """
        Compute ramp-up winner vs loser divergence and acceleration.

        Returns (divergence, acceleration) where:
        - divergence = mean(winner_avg for bars 15-24) - mean(loser_avg for bars 15-24)
        - acceleration = slope(winner bars 20-24) - slope(loser bars 20-24)
        """
        if not trade_ids:
            return 0.0, 0.0

        try:
            phase_df = self._provider.get_three_phase_averages(
                trade_ids, indicator_col,
            )
        except Exception:
            return 0.0, 0.0

        if phase_df.empty:
            return 0.0, 0.0

        # Filter to ramp-up phase only
        ramp = phase_df[phase_df["phase"] == "ramp_up"]
        if ramp.empty:
            return 0.0, 0.0

        # Split winners and losers
        w_ramp = ramp[ramp["is_winner"] == True]
        l_ramp = ramp[ramp["is_winner"] == False]

        if w_ramp.empty or l_ramp.empty:
            return 0.0, 0.0

        # Divergence: avg of last 10 bars
        analysis_bars = list(RAMP_UP_ANALYSIS_BARS)
        w_analysis = w_ramp[w_ramp["bar_sequence"].isin(analysis_bars)]
        l_analysis = l_ramp[l_ramp["bar_sequence"].isin(analysis_bars)]

        w_avg = w_analysis["avg_value"].mean() if not w_analysis.empty else 0.0
        l_avg = l_analysis["avg_value"].mean() if not l_analysis.empty else 0.0
        divergence = w_avg - l_avg

        # Acceleration: slope of last 5 bars
        accel_bars = list(RAMP_UP_ACCEL_BARS)
        w_accel = w_ramp[w_ramp["bar_sequence"].isin(accel_bars)].sort_values("bar_sequence")
        l_accel = l_ramp[l_ramp["bar_sequence"].isin(accel_bars)].sort_values("bar_sequence")

        w_slope = self._linear_slope(w_accel["bar_sequence"].values, w_accel["avg_value"].values)
        l_slope = self._linear_slope(l_accel["bar_sequence"].values, l_accel["avg_value"].values)
        acceleration = w_slope - l_slope

        return divergence, acceleration

    @staticmethod
    def _linear_slope(x: np.ndarray, y: np.ndarray) -> float:
        """Compute linear regression slope. Returns 0.0 if insufficient data."""
        if len(x) < 2 or len(y) < 2:
            return 0.0
        try:
            coeffs = np.polyfit(x.astype(float), y.astype(float), 1)
            return float(coeffs[0])
        except (np.linalg.LinAlgError, ValueError):
            return 0.0

    # ------------------------------------------------------------------
    # Degradation tracking
    # ------------------------------------------------------------------
    def _load_prior_results(self, prior_dir: Path) -> Optional[Dict]:
        """
        Load _prior.json from a previous scorecard run.

        Returns dict mapping:
            trade_type -> indicator_col -> {tier, effect_size, top5}
        """
        prior_json = prior_dir / "_prior.json"
        if not prior_json.exists():
            return None

        try:
            with open(prior_json, "r") as f:
                data = json.load(f)
            return data.get("trade_types", {})
        except (json.JSONDecodeError, IOError):
            return None

    def _compute_degradation(
        self,
        current_results: Dict[str, TradeTypeResult],
        prior_data: Dict,
    ) -> List[DegradationFlag]:
        """
        Compare current indicator scores to prior run.

        Flags:
        - Tier drop (e.g., A -> B)
        - Effect size drop by >3pp
        - Top-5 demotion (was top-5, now isn't)
        """
        flags: List[DegradationFlag] = []
        tier_to_rank = {"S": 0, "A": 1, "B": 2, "C": 3, "Rejected": 4}

        for tt_key, tt_result in current_results.items():
            prior_tt = prior_data.get(tt_key, {})
            prior_indicators = prior_tt.get("indicators", {})
            top5_cols = {s.indicator_col for s in tt_result.top_scores}

            for score in tt_result.all_scores:
                prior_ind = prior_indicators.get(score.indicator_col, {})
                if not prior_ind:
                    continue

                prior_tier = prior_ind.get("tier", "Rejected")
                prior_effect = prior_ind.get("effect_size", 0.0)
                prior_top5 = prior_ind.get("top5", False)

                # Tier drop
                curr_rank = tier_to_rank.get(score.tier, 4)
                prior_rank = tier_to_rank.get(prior_tier, 4)
                if curr_rank > prior_rank:
                    flags.append(DegradationFlag(
                        indicator_col=score.indicator_col,
                        indicator_label=score.indicator_label,
                        trade_type_key=tt_key,
                        flag_type="tier_drop",
                        message=(
                            f"{score.indicator_label} in "
                            f"{TRADE_TYPES[tt_key]['label']}: "
                            f"{prior_tier} -> {score.tier}"
                        ),
                        prior_value=prior_tier,
                        current_value=score.tier,
                    ))

                # Effect size drop >3pp
                if prior_effect - score.effect_size > 3.0:
                    flags.append(DegradationFlag(
                        indicator_col=score.indicator_col,
                        indicator_label=score.indicator_label,
                        trade_type_key=tt_key,
                        flag_type="effect_drop",
                        message=(
                            f"{score.indicator_label} in "
                            f"{TRADE_TYPES[tt_key]['label']}: "
                            f"effect {prior_effect:.1f}pp -> {score.effect_size:.1f}pp"
                        ),
                        prior_value=f"{prior_effect:.1f}pp",
                        current_value=f"{score.effect_size:.1f}pp",
                    ))

                # Top-5 demotion
                if prior_top5 and score.indicator_col not in top5_cols:
                    flags.append(DegradationFlag(
                        indicator_col=score.indicator_col,
                        indicator_label=score.indicator_label,
                        trade_type_key=tt_key,
                        flag_type="top5_demotion",
                        message=(
                            f"{score.indicator_label} in "
                            f"{TRADE_TYPES[tt_key]['label']}: "
                            f"dropped from top-5"
                        ),
                        prior_value="top-5",
                        current_value="not top-5",
                    ))

        return flags

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------
    def _log(self, msg: str):
        if self._verbose:
            print(f"[ScorecardAnalyzer] {msg}")
