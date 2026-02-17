"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 04: INDICATOR ANALYSIS v2.0
Tier Ranker - Statistical tier ranking engine for indicator edge evaluation
XIII Trading LLC
================================================================================

Uses chi-square (categorical) and Mann-Whitney U (continuous) tests to rank
indicators into S/A/B/C/Rejected tiers per trade type. Effect size is measured
as the spread in win rate (pp) between best and worst indicator states.

Always runs calculations regardless of sample size. Flags LOW_DATA confidence
when groups are below minimum thresholds so scorecards have consistent
structure across all trade types.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

from config import TIER_THRESHOLDS, MIN_SAMPLE_SIZE, MIN_GROUP_SIZE


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class IndicatorScore:
    """Score for a single indicator within a single trade type."""

    indicator_col: str          # e.g., 'sma_config'
    indicator_label: str        # e.g., 'SMA Configuration'
    indicator_type: str         # 'continuous' or 'categorical'
    tier: str                   # 'S', 'A', 'B', 'C', 'Rejected'
    confidence: str             # 'HIGH', 'LOW_DATA'
    effect_size: float          # best WR - worst WR (pp)
    p_value: float              # statistical significance
    baseline_win_rate: float    # overall win rate for this trade type
    best_state: str             # best-performing state/quintile
    best_state_win_rate: float  # win rate of best state
    best_state_trades: int      # trades in best state
    worst_state: str            # worst-performing state/quintile
    worst_state_win_rate: float # win rate of worst state
    worst_state_trades: int     # trades in worst state
    total_trades: int           # total trades analyzed
    min_group_size: int         # smallest group in analysis
    ramp_divergence: float      # winner-loser delta in last 10 ramp bars
    ramp_acceleration: float    # rate of change delta in last 5 ramp bars
    binary_signal: str          # e.g., "TAKE when h1_structure = BEAR"
    binary_avoid: str           # e.g., "SKIP when h1_structure = BULL"

    @property
    def tier_rank(self) -> int:
        """Numeric rank for sorting: S=0, A=1, B=2, C=3, Rejected=4."""
        return {"S": 0, "A": 1, "B": 2, "C": 3, "Rejected": 4}.get(self.tier, 4)


# =============================================================================
# TIER RANKING ENGINE
# =============================================================================


class TierRanker:
    """Ranks indicators by statistical edge for a specific trade type."""

    TIER_ORDER = ["S", "A", "B", "C"]  # checked in order, first match wins

    def __init__(self, tier_thresholds: Optional[Dict] = None,
                 min_sample_size: int = MIN_SAMPLE_SIZE,
                 min_group_size: int = MIN_GROUP_SIZE):
        self._thresholds = tier_thresholds or TIER_THRESHOLDS
        self._min_sample = min_sample_size
        self._min_group = min_group_size

    # ------------------------------------------------------------------
    # Public: Rank a categorical indicator
    # ------------------------------------------------------------------
    def rank_categorical(
        self,
        entry_data: pd.DataFrame,
        indicator_col: str,
        indicator_label: str,
        baseline_win_rate: float,
        trade_direction: str,
        ramp_divergence: float = 0.0,
        ramp_acceleration: float = 0.0,
    ) -> IndicatorScore:
        """
        Rank a categorical indicator using chi-square test.

        Always runs calculations. Flags LOW_DATA confidence when sample
        sizes are below thresholds rather than returning empty scores.
        """
        df = entry_data.dropna(subset=[indicator_col, 'is_winner']).copy()
        total_trades = len(df)

        # If truly no data, return minimal score
        if total_trades < 2:
            return self._no_data_score(
                indicator_col, indicator_label, 'categorical',
                baseline_win_rate, total_trades,
                ramp_divergence, ramp_acceleration,
            )

        # Group by indicator state
        groups = df.groupby(indicator_col).agg(
            trades=('is_winner', 'count'),
            wins=('is_winner', 'sum'),
        ).reset_index()
        groups['win_rate'] = (groups['wins'] / groups['trades'] * 100)

        # Use ALL groups that have at least 1 trade for analysis
        # (we flag confidence separately)
        valid = groups[groups['trades'] >= 1]
        if len(valid) < 2:
            return self._no_data_score(
                indicator_col, indicator_label, 'categorical',
                baseline_win_rate, total_trades,
                ramp_divergence, ramp_acceleration,
            )

        # Determine confidence level
        min_group = int(valid['trades'].min())
        low_data = (total_trades < self._min_sample or min_group < self._min_group)
        confidence = "LOW_DATA" if low_data else "HIGH"

        # Chi-square test on contingency table
        p_value = self._chi_square(df, indicator_col)

        # Effect size: best WR - worst WR
        best_row = valid.loc[valid['win_rate'].idxmax()]
        worst_row = valid.loc[valid['win_rate'].idxmin()]
        effect_size = best_row['win_rate'] - worst_row['win_rate']

        # Tier assignment (uses standard thresholds regardless of confidence)
        tier = self._assign_tier(effect_size, p_value)

        # Binary signals
        binary_signal, binary_avoid = self._extract_binary_signal_categorical(
            indicator_col, str(best_row[indicator_col]),
            str(worst_row[indicator_col]), trade_direction,
        )

        return IndicatorScore(
            indicator_col=indicator_col,
            indicator_label=indicator_label,
            indicator_type='categorical',
            tier=tier,
            confidence=confidence,
            effect_size=round(effect_size, 1),
            p_value=round(p_value, 6),
            baseline_win_rate=round(baseline_win_rate, 1),
            best_state=str(best_row[indicator_col]),
            best_state_win_rate=round(best_row['win_rate'], 1),
            best_state_trades=int(best_row['trades']),
            worst_state=str(worst_row[indicator_col]),
            worst_state_win_rate=round(worst_row['win_rate'], 1),
            worst_state_trades=int(worst_row['trades']),
            total_trades=total_trades,
            min_group_size=min_group,
            ramp_divergence=round(ramp_divergence, 6),
            ramp_acceleration=round(ramp_acceleration, 6),
            binary_signal=binary_signal,
            binary_avoid=binary_avoid,
        )

    # ------------------------------------------------------------------
    # Public: Rank a continuous indicator
    # ------------------------------------------------------------------
    def rank_continuous(
        self,
        entry_data: pd.DataFrame,
        indicator_col: str,
        indicator_label: str,
        baseline_win_rate: float,
        trade_direction: str,
        ramp_divergence: float = 0.0,
        ramp_acceleration: float = 0.0,
    ) -> IndicatorScore:
        """
        Rank a continuous indicator using quintile analysis + Mann-Whitney U.

        Always runs calculations. Uses fewer bins (tertiles) when sample
        is too small for quintiles. Flags LOW_DATA confidence.
        """
        df = entry_data.dropna(subset=[indicator_col, 'is_winner']).copy()
        total_trades = len(df)

        if total_trades < 2:
            return self._no_data_score(
                indicator_col, indicator_label, 'continuous',
                baseline_win_rate, total_trades,
                ramp_divergence, ramp_acceleration,
            )

        # Adaptive binning: quintiles if enough data, tertiles if small
        n_bins = 5 if total_trades >= 25 else 3
        bin_labels = list(range(1, n_bins + 1))

        try:
            df['quintile'] = pd.qcut(
                df[indicator_col], q=n_bins, labels=bin_labels, duplicates='drop'
            )
        except ValueError:
            # Not enough unique values — try fewer bins
            try:
                df['quintile'] = pd.qcut(
                    df[indicator_col], q=2, labels=[1, 2], duplicates='drop'
                )
                n_bins = 2
            except ValueError:
                return self._no_data_score(
                    indicator_col, indicator_label, 'continuous',
                    baseline_win_rate, total_trades,
                    ramp_divergence, ramp_acceleration,
                )

        groups = df.groupby('quintile', observed=True).agg(
            trades=('is_winner', 'count'),
            wins=('is_winner', 'sum'),
            range_min=(indicator_col, 'min'),
            range_max=(indicator_col, 'max'),
        ).reset_index()
        groups['win_rate'] = (groups['wins'] / groups['trades'] * 100)

        valid = groups[groups['trades'] >= 1]
        if len(valid) < 2:
            return self._no_data_score(
                indicator_col, indicator_label, 'continuous',
                baseline_win_rate, total_trades,
                ramp_divergence, ramp_acceleration,
            )

        # Determine confidence level
        min_group = int(valid['trades'].min())
        low_data = (total_trades < self._min_sample or min_group < self._min_group)
        confidence = "LOW_DATA" if low_data else "HIGH"

        # Mann-Whitney U test: winners vs losers
        winners_vals = df[df['is_winner'] == True][indicator_col].values
        losers_vals = df[df['is_winner'] == False][indicator_col].values

        if len(winners_vals) < 3 or len(losers_vals) < 3:
            p_value = 1.0
        else:
            try:
                _, p_value = stats.mannwhitneyu(
                    winners_vals, losers_vals, alternative='two-sided'
                )
            except ValueError:
                p_value = 1.0

        # Effect size from bins
        best_row = valid.loc[valid['win_rate'].idxmax()]
        worst_row = valid.loc[valid['win_rate'].idxmin()]
        effect_size = best_row['win_rate'] - worst_row['win_rate']

        tier = self._assign_tier(effect_size, p_value)

        # Binary signals — use Q for quintiles, T for tertiles
        bin_prefix = "Q" if n_bins == 5 else ("T" if n_bins == 3 else "H")
        best_q = int(best_row['quintile'])
        worst_q = int(worst_row['quintile'])
        best_range = f"{best_row['range_min']:.4f} to {best_row['range_max']:.4f}"
        worst_range = f"{worst_row['range_min']:.4f} to {worst_row['range_max']:.4f}"

        binary_signal = f"TAKE when {indicator_col} in {bin_prefix}{best_q} ({best_range})"
        binary_avoid = f"SKIP when {indicator_col} in {bin_prefix}{worst_q} ({worst_range})"

        return IndicatorScore(
            indicator_col=indicator_col,
            indicator_label=indicator_label,
            indicator_type='continuous',
            tier=tier,
            confidence=confidence,
            effect_size=round(effect_size, 1),
            p_value=round(p_value, 6),
            baseline_win_rate=round(baseline_win_rate, 1),
            best_state=f"{bin_prefix}{best_q} ({best_range})",
            best_state_win_rate=round(best_row['win_rate'], 1),
            best_state_trades=int(best_row['trades']),
            worst_state=f"{bin_prefix}{worst_q} ({worst_range})",
            worst_state_win_rate=round(worst_row['win_rate'], 1),
            worst_state_trades=int(worst_row['trades']),
            total_trades=total_trades,
            min_group_size=min_group,
            ramp_divergence=round(ramp_divergence, 6),
            ramp_acceleration=round(ramp_acceleration, 6),
            binary_signal=binary_signal,
            binary_avoid=binary_avoid,
        )

    # ------------------------------------------------------------------
    # Internal: Tier assignment
    # ------------------------------------------------------------------
    def _assign_tier(self, effect_size: float, p_value: float) -> str:
        """Map effect size + p-value to tier. Returns S/A/B/C/Rejected."""
        for tier_name in self.TIER_ORDER:
            thresholds = self._thresholds[tier_name]
            if (effect_size >= thresholds["min_effect_size"]
                    and p_value <= thresholds["max_p_value"]):
                return tier_name
        return "Rejected"

    # ------------------------------------------------------------------
    # Internal: Chi-square test
    # ------------------------------------------------------------------
    def _chi_square(self, df: pd.DataFrame, indicator_col: str) -> float:
        """Run chi-square test on indicator state vs outcome."""
        try:
            contingency = pd.crosstab(df[indicator_col], df['is_winner'])
            if contingency.shape[0] < 2 or contingency.shape[1] < 2:
                return 1.0
            chi2, p_value, _, _ = stats.chi2_contingency(contingency)
            return p_value
        except Exception:
            return 1.0

    # ------------------------------------------------------------------
    # Internal: Binary signal extraction
    # ------------------------------------------------------------------
    def _extract_binary_signal_categorical(
        self, indicator_col: str, best_state: str,
        worst_state: str, trade_direction: str,
    ) -> Tuple[str, str]:
        """Generate binary TAKE/SKIP signal for categorical indicator."""
        signal = f"TAKE when {indicator_col} = {best_state}"
        avoid = f"SKIP when {indicator_col} = {worst_state}"
        return signal, avoid

    # ------------------------------------------------------------------
    # Internal: No data score (truly zero/one trade)
    # ------------------------------------------------------------------
    def _no_data_score(
        self, col: str, label: str, ind_type: str,
        baseline: float, total: int,
        ramp_div: float = 0.0, ramp_accel: float = 0.0,
    ) -> IndicatorScore:
        """Return a Rejected/LOW_DATA score when data is truly insufficient."""
        return IndicatorScore(
            indicator_col=col,
            indicator_label=label,
            indicator_type=ind_type,
            tier="Rejected",
            confidence="LOW_DATA",
            effect_size=0.0,
            p_value=1.0,
            baseline_win_rate=round(baseline, 1),
            best_state="N/A",
            best_state_win_rate=0.0,
            best_state_trades=0,
            worst_state="N/A",
            worst_state_win_rate=0.0,
            worst_state_trades=0,
            total_trades=total,
            min_group_size=0,
            ramp_divergence=round(ramp_div, 6),
            ramp_acceleration=round(ramp_accel, 6),
            binary_signal="INSUFFICIENT DATA",
            binary_avoid="INSUFFICIENT DATA",
        )
