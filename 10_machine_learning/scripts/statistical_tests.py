"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 10: MACHINE LEARNING
Statistical Tests
XIII Trading LLC
================================================================================

Statistical testing functions for edge validation and hypothesis testing.
All tests compare a group (edge condition) against the baseline (all trades).

Uses scipy.stats for chi-squared and Fisher's exact tests.
"""

import sys
from pathlib import Path
from typing import Dict, Tuple, Optional
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent.parent))

from scipy.stats import chi2_contingency, fisher_exact
import numpy as np

from config import EDGE_CRITERIA


@dataclass
class TestResult:
    """Result of a statistical test."""
    chi2: float
    p_value: float
    effect_size_pp: float
    group_win_rate: float
    baseline_win_rate: float
    group_trades: int
    baseline_trades: int
    confidence: str
    is_significant: bool

    def to_dict(self) -> Dict:
        return {
            "chi2": round(self.chi2, 4),
            "p_value": round(self.p_value, 6),
            "effect_size_pp": round(self.effect_size_pp, 1),
            "group_win_rate": round(self.group_win_rate, 1),
            "baseline_win_rate": round(self.baseline_win_rate, 1),
            "group_trades": self.group_trades,
            "baseline_trades": self.baseline_trades,
            "confidence": self.confidence,
            "is_significant": self.is_significant,
        }


def chi_squared_test(
    group_wins: int,
    group_total: int,
    baseline_wins: int,
    baseline_total: int,
) -> Tuple[float, float]:
    """
    Run chi-squared test of independence.

    Compares group win rate against baseline win rate.
    Falls back to Fisher's exact test if any expected cell count < 5.

    Args:
        group_wins: Number of winners in the edge group
        group_total: Total trades in the edge group
        baseline_wins: Number of winners in the baseline (all trades)
        baseline_total: Total trades in the baseline

    Returns:
        (chi2_statistic, p_value)
    """
    if group_total == 0 or baseline_total == 0:
        return 0.0, 1.0

    group_losses = group_total - group_wins
    baseline_losses = baseline_total - baseline_wins

    # Contingency table:
    #              Win    Loss
    # Group        gw     gl
    # Baseline     bw     bl
    table = np.array([
        [group_wins, group_losses],
        [baseline_wins, baseline_losses],
    ])

    # Check if any expected frequency < 5 → use Fisher's exact
    row_totals = table.sum(axis=1)
    col_totals = table.sum(axis=0)
    grand_total = table.sum()

    min_expected = float("inf")
    for i in range(2):
        for j in range(2):
            expected = row_totals[i] * col_totals[j] / grand_total
            min_expected = min(min_expected, expected)

    if min_expected < 5:
        # Fisher's exact test (2x2 only)
        _, p_value = fisher_exact(table)
        # Approximate chi2 from p-value for consistency
        chi2 = 0.0  # Fisher doesn't produce chi2
        return chi2, p_value

    chi2, p_value, _, _ = chi2_contingency(table, correction=True)
    return chi2, p_value


def effect_size_pp(group_win_rate: float, baseline_win_rate: float) -> float:
    """
    Calculate effect size in percentage points.

    Args:
        group_win_rate: Win rate of the edge group (0-100)
        baseline_win_rate: Win rate of the baseline (0-100)

    Returns:
        Effect size in percentage points (positive = group outperforms)
    """
    return round(group_win_rate - baseline_win_rate, 1)


def confidence_level(sample_size: int) -> str:
    """
    Classify confidence level based on sample size.

    Args:
        sample_size: Number of trades in the group

    Returns:
        'HIGH', 'MEDIUM', or 'LOW'
    """
    if sample_size >= EDGE_CRITERIA["min_sample_high"]:
        return "HIGH"
    elif sample_size >= EDGE_CRITERIA["min_sample_medium"]:
        return "MEDIUM"
    else:
        return "LOW"


def is_significant(
    p_value: float,
    effect_pp: float,
    sample_size: int,
) -> bool:
    """
    Determine if an edge is statistically and practically significant.

    Requires ALL three criteria:
    1. p-value below threshold (statistical significance)
    2. Effect size above threshold (practical significance)
    3. Sample size at least MEDIUM confidence

    Args:
        p_value: p-value from chi-squared test
        effect_pp: Effect size in percentage points (absolute value used)
        sample_size: Number of trades in the group

    Returns:
        True if edge passes all significance criteria
    """
    return (
        p_value < EDGE_CRITERIA["p_value_threshold"]
        and abs(effect_pp) > EDGE_CRITERIA["effect_size_threshold"]
        and sample_size >= EDGE_CRITERIA["min_sample_medium"]
    )


def run_full_test(
    group_wins: int,
    group_total: int,
    baseline_wins: int,
    baseline_total: int,
) -> TestResult:
    """
    Run complete statistical test suite for an edge.

    This is the primary entry point for testing any edge hypothesis.

    Args:
        group_wins: Winners in the edge group
        group_total: Total trades in the edge group
        baseline_wins: Winners in the baseline
        baseline_total: Total trades in the baseline

    Returns:
        TestResult with all statistics and classification
    """
    if group_total == 0 or baseline_total == 0:
        return TestResult(
            chi2=0.0,
            p_value=1.0,
            effect_size_pp=0.0,
            group_win_rate=0.0,
            baseline_win_rate=0.0,
            group_trades=group_total,
            baseline_trades=baseline_total,
            confidence="LOW",
            is_significant=False,
        )

    group_wr = group_wins / group_total * 100
    baseline_wr = baseline_wins / baseline_total * 100

    chi2, p_val = chi_squared_test(group_wins, group_total, baseline_wins, baseline_total)
    effect_pp = effect_size_pp(group_wr, baseline_wr)
    conf = confidence_level(group_total)
    sig = is_significant(p_val, effect_pp, group_total)

    return TestResult(
        chi2=chi2,
        p_value=p_val,
        effect_size_pp=effect_pp,
        group_win_rate=round(group_wr, 1),
        baseline_win_rate=round(baseline_wr, 1),
        group_trades=group_total,
        baseline_trades=baseline_total,
        confidence=conf,
        is_significant=sig,
    )


def classify_edge_health(
    current_effect_pp: float,
    stored_effect_pp: float,
    p_value: float,
    drift_threshold_pp: float = 5.0,
) -> str:
    """
    Classify edge health by comparing current vs stored effect size.

    Args:
        current_effect_pp: Current measured effect (percentage points)
        stored_effect_pp: Stored/expected effect from VALIDATED_EDGES
        p_value: Current p-value
        drift_threshold_pp: How many pp difference triggers WEAKENING

    Returns:
        'HEALTHY': Within drift_threshold of stored value, same sign
        'WEAKENING': Same sign but more than drift_threshold lower
        'DEGRADED': Sign reversed or p > 0.05
        'INCONCLUSIVE': Insufficient data (p > 0.20)
    """
    if p_value > 0.20:
        return "INCONCLUSIVE"

    # Check sign reversal
    if stored_effect_pp > 0 and current_effect_pp <= 0:
        return "DEGRADED"
    if stored_effect_pp < 0 and current_effect_pp >= 0:
        return "DEGRADED"

    # Check magnitude drift
    if stored_effect_pp > 0:
        # Positive edge: current should be within drift threshold
        if current_effect_pp < stored_effect_pp - drift_threshold_pp:
            return "WEAKENING"
    else:
        # Negative edge: current should be within drift threshold (more negative or close)
        if current_effect_pp > stored_effect_pp + drift_threshold_pp:
            return "WEAKENING"

    return "HEALTHY"


if __name__ == "__main__":
    # Quick self-test with realistic numbers
    print("=" * 60)
    print("  Statistical Tests - Self Test")
    print("=" * 60)

    # Example: H1 NEUTRAL edge
    # Group: 749 wins out of 1506 trades (49.7%)
    # Baseline: 1180 wins out of 2307 trades (51.1%)
    result = run_full_test(
        group_wins=749,
        group_total=1506,
        baseline_wins=1180,
        baseline_total=2307,
    )
    print(f"\n  Test: H1 NEUTRAL (this week's data)")
    print(f"  Group WR: {result.group_win_rate}%  Baseline WR: {result.baseline_win_rate}%")
    print(f"  Effect: {result.effect_size_pp:+.1f}pp")
    print(f"  Chi2: {result.chi2:.4f}  p-value: {result.p_value:.6f}")
    print(f"  Confidence: {result.confidence}")
    print(f"  Significant: {result.is_significant}")

    # Classify health vs stored +36pp
    health = classify_edge_health(result.effect_size_pp, 36.0, result.p_value)
    print(f"  Health vs stored +36pp: {health}")

    # Example: Health Score STRONG
    # 21 wins out of 26 trades (80.8%)
    result2 = run_full_test(
        group_wins=21,
        group_total=26,
        baseline_wins=1180,
        baseline_total=2307,
    )
    print(f"\n  Test: Health Score STRONG (8-10)")
    print(f"  Group WR: {result2.group_win_rate}%  Baseline WR: {result2.baseline_win_rate}%")
    print(f"  Effect: {result2.effect_size_pp:+.1f}pp")
    print(f"  p-value: {result2.p_value:.6f}")
    print(f"  Confidence: {result2.confidence}")
    print(f"  Significant: {result2.is_significant}")

    print("\n  Self-test complete")
