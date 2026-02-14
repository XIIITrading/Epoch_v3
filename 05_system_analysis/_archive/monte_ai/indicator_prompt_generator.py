"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Monte AI - Indicator Analysis Prompt Generator
XIII Trading LLC
================================================================================

Generates analysis prompts for CALC-005 through CALC-008 results.

================================================================================
"""

import pandas as pd
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .indicator_prompts import (
    INDICATOR_ANALYSIS_SYSTEM_PROMPT,
    CALC_005_ANALYSIS_TEMPLATE,
    CALC_006_ANALYSIS_TEMPLATE,
    CALC_007_ANALYSIS_TEMPLATE,
    CALC_008_ANALYSIS_TEMPLATE,
    SYNTHESIS_ANALYSIS_TEMPLATE,
    CALC_005_DATA_FORMAT,
    CALC_006_DATA_FORMAT,
    CALC_007_DATA_FORMAT,
    CALC_008_DATA_FORMAT
)


@dataclass
class IndicatorAnalysisPrompt:
    """Generated prompt with metadata."""
    system_prompt: str
    user_prompt: str
    analysis_type: str
    data_summary: str
    estimated_tokens: int


def estimate_tokens(text: str) -> int:
    """Estimate token count (rough approximation)."""
    return int(len(text.split()) * 1.3)


# =============================================================================
# DATA FORMATTING HELPERS
# =============================================================================

def format_bucket_table(bucket_df: pd.DataFrame, baseline_wr: float = 0) -> str:
    """Format health bucket data as markdown table."""
    if bucket_df is None or bucket_df.empty:
        return "No bucket data available"

    rows = []
    for _, row in bucket_df.iterrows():
        wr = row.get('win_rate', 0)
        lift = wr - baseline_wr
        lift_str = f"+{lift:.1f}pp" if lift > 0 else f"{lift:.1f}pp"
        rows.append(
            f"| {row.get('bucket', 'N/A')} | {row.get('trades', 0)} | "
            f"{wr:.1f}% | {lift_str} |"
        )
    return "\n".join(rows)


def format_factor_table(factors: List) -> str:
    """Format factor importance data as markdown table."""
    if not factors:
        return "No factor data available"

    rows = []
    for i, f in enumerate(factors):
        lift = f.lift if hasattr(f, 'lift') else 0
        lift_str = f"+{lift:.1f}pp" if lift > 0 else f"{lift:.1f}pp"

        factor_name = f.factor_name if hasattr(f, 'factor_name') else str(f)
        group = f.group if hasattr(f, 'group') else 'N/A'
        healthy_wr = f.healthy_win_rate if hasattr(f, 'healthy_win_rate') else 0
        unhealthy_wr = f.unhealthy_win_rate if hasattr(f, 'unhealthy_win_rate') else 0

        rows.append(
            f"| {i+1} | {factor_name} | {group} | "
            f"{healthy_wr:.1f}% | {unhealthy_wr:.1f}% | {lift_str} |"
        )
    return "\n".join(rows)


def format_warning_table(warnings: List) -> str:
    """Format early warning signals as markdown table."""
    if not warnings:
        return "No significant warning signals identified"

    rows = []
    for w in warnings[:5]:  # Top 5
        indicator = w.indicator if hasattr(w, 'indicator') else 'N/A'
        threshold = w.threshold if hasattr(w, 'threshold') else 0
        window = w.bars_window if hasattr(w, 'bars_window') else 0
        loser_hit = w.hit_rate_losers if hasattr(w, 'hit_rate_losers') else 0
        winner_hit = w.hit_rate_winners if hasattr(w, 'hit_rate_winners') else 0
        lift = w.lift if hasattr(w, 'lift') else 0

        rows.append(
            f"| {indicator} | <={threshold} | {window} bars | "
            f"{loser_hit:.1f}% | {winner_hit:.1f}% | +{lift:.1f}pp |"
        )
    return "\n".join(rows)


# =============================================================================
# PROMPT GENERATORS BY ANALYSIS TYPE
# =============================================================================

def generate_calc_005_prompt(result) -> IndicatorAnalysisPrompt:
    """
    Generate prompt for CALC-005 Health Score Correlation analysis.

    Parameters:
        result: HealthCorrelationResult from CALC-005

    Returns:
        IndicatorAnalysisPrompt ready for Claude
    """
    # Extract values with safe defaults
    total_trades = getattr(result, 'total_trades', 0)
    overall_win_rate = getattr(result, 'overall_win_rate', 0)
    correlation = getattr(result, 'correlation_coefficient', 0)
    pvalue = getattr(result, 'correlation_pvalue', 1)
    optimal_threshold = getattr(result, 'optimal_threshold', 0)
    optimal_lift = getattr(result, 'optimal_threshold_lift', 0)

    # Format bucket table
    bucket_df = getattr(result, 'bucket_distribution', None)
    bucket_table = format_bucket_table(bucket_df, overall_win_rate)

    # Model breakdown
    model_breakdown = "See detailed breakdown in analysis results."
    if hasattr(result, 'model_direction_breakdown') and result.model_direction_breakdown is not None:
        try:
            model_breakdown = result.model_direction_breakdown.to_string()[:800]
        except:
            pass

    data_summary = CALC_005_DATA_FORMAT.format(
        total_trades=total_trades,
        overall_win_rate=overall_win_rate,
        correlation=correlation,
        pvalue=pvalue,
        optimal_threshold=optimal_threshold,
        optimal_lift=optimal_lift,
        bucket_table=bucket_table,
        model_breakdown=model_breakdown
    )

    user_prompt = CALC_005_ANALYSIS_TEMPLATE.format(data_summary=data_summary)
    full_prompt = f"{INDICATOR_ANALYSIS_SYSTEM_PROMPT}\n\n{user_prompt}"

    return IndicatorAnalysisPrompt(
        system_prompt=INDICATOR_ANALYSIS_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        analysis_type="CALC-005: Health Score Correlation",
        data_summary=data_summary,
        estimated_tokens=estimate_tokens(full_prompt)
    )


def generate_calc_006_prompt(result) -> IndicatorAnalysisPrompt:
    """
    Generate prompt for CALC-006 Factor Importance analysis.

    Parameters:
        result: FactorImportanceResult from CALC-006

    Returns:
        IndicatorAnalysisPrompt ready for Claude
    """
    # Format factor table
    factors = getattr(result, 'factor_analyses', [])
    factor_table = format_factor_table(factors)

    # Group summary
    group_summary = ""
    if hasattr(result, 'group_summary') and result.group_summary is not None:
        try:
            for _, row in result.group_summary.iterrows():
                group_summary += f"| {row['group']} | +{row['avg_lift']:.1f}pp | {row['best_factor']} |\n"
        except:
            group_summary = "Group summary not available"

    top_factors = getattr(result, 'top_factors', [])
    dead_factors = getattr(result, 'dead_factors', [])

    data_summary = CALC_006_DATA_FORMAT.format(
        factor_table=factor_table,
        group_summary=group_summary if group_summary else "N/A",
        top_factors=", ".join(top_factors) if top_factors else "None identified",
        dead_factors=", ".join(dead_factors) if dead_factors else "None identified"
    )

    user_prompt = CALC_006_ANALYSIS_TEMPLATE.format(data_summary=data_summary)

    return IndicatorAnalysisPrompt(
        system_prompt=INDICATOR_ANALYSIS_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        analysis_type="CALC-006: Factor Importance",
        data_summary=data_summary,
        estimated_tokens=estimate_tokens(INDICATOR_ANALYSIS_SYSTEM_PROMPT + user_prompt)
    )


def generate_calc_007_prompt(result) -> IndicatorAnalysisPrompt:
    """
    Generate prompt for CALC-007 Indicator Progression analysis.

    Parameters:
        result: IndicatorProgressionResult from CALC-007

    Returns:
        IndicatorAnalysisPrompt ready for Claude
    """
    # Extract progression data with safe defaults
    winner_path = getattr(result, 'winner_path', None)
    loser_path = getattr(result, 'loser_path', None)

    winner_entry = 0
    winner_peak = 0
    winner_delta = 0
    if winner_path:
        entry_snap = getattr(winner_path, 'entry_snapshot', None)
        peak_snap = getattr(winner_path, 'peak_snapshot', None)
        winner_entry = getattr(entry_snap, 'avg_health_score', 0) if entry_snap else 0
        winner_peak = getattr(peak_snap, 'avg_health_score', 0) if peak_snap else 0
        winner_delta = getattr(winner_path, 'health_delta_to_peak', 0)

    loser_entry = 0
    loser_peak = 0
    loser_delta = 0
    if loser_path:
        entry_snap = getattr(loser_path, 'entry_snapshot', None)
        peak_snap = getattr(loser_path, 'peak_snapshot', None)
        loser_entry = getattr(entry_snap, 'avg_health_score', 0) if entry_snap else 0
        loser_peak = getattr(peak_snap, 'avg_health_score', 0) if peak_snap else 0
        loser_delta = getattr(loser_path, 'health_delta_to_peak', 0)

    warnings = getattr(result, 'early_warnings', [])
    warning_table = format_warning_table(warnings)

    best_warning = "None identified"
    bw = getattr(result, 'best_warning', None)
    if bw:
        indicator = getattr(bw, 'indicator', 'N/A')
        threshold = getattr(bw, 'threshold', 0)
        window = getattr(bw, 'bars_window', 0)
        loser_hit = getattr(bw, 'hit_rate_losers', 0)
        winner_hit = getattr(bw, 'hit_rate_winners', 0)
        best_warning = (
            f"{indicator} drop of {threshold} within {window} bars "
            f"catches {loser_hit:.0f}% of losers with {winner_hit:.0f}% false positives"
        )

    data_summary = CALC_007_DATA_FORMAT.format(
        winner_entry=winner_entry,
        winner_peak=winner_peak,
        winner_delta=winner_delta,
        loser_entry=loser_entry,
        loser_peak=loser_peak,
        loser_delta=loser_delta,
        warning_table=warning_table,
        best_warning=best_warning
    )

    user_prompt = CALC_007_ANALYSIS_TEMPLATE.format(data_summary=data_summary)

    return IndicatorAnalysisPrompt(
        system_prompt=INDICATOR_ANALYSIS_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        analysis_type="CALC-007: Indicator Progression",
        data_summary=data_summary,
        estimated_tokens=estimate_tokens(INDICATOR_ANALYSIS_SYSTEM_PROMPT + user_prompt)
    )


def generate_calc_008_prompt(result) -> IndicatorAnalysisPrompt:
    """
    Generate prompt for CALC-008 Rejection Dynamics analysis.

    Parameters:
        result: RejectionDynamicsResult from CALC-008

    Returns:
        IndicatorAnalysisPrompt ready for Claude
    """
    # Time comparison table
    time_comparison = getattr(result, 'time_comparison', None)
    if time_comparison is not None and not time_comparison.empty:
        time_table = time_comparison.to_string(index=False)
    else:
        time_table = "No time comparison data available"

    # Inversion table
    ci = getattr(result, 'continuation_inversion', None)
    ri = getattr(result, 'rejection_inversion', None)

    if ci and ri:
        inversion_table = f"""| Continuation | {ci.correlation:.3f} | {ci.strong_win_rate:.1f}% | {ci.critical_win_rate:.1f}% | {'YES' if ci.is_inverted else 'No'} |
| Rejection | {ri.correlation:.3f} | {ri.strong_win_rate:.1f}% | {ri.critical_win_rate:.1f}% | {'YES' if ri.is_inverted else 'No'} |"""
    else:
        inversion_table = "Inversion data not available"

    # Factor inversion table
    factor_inversions = getattr(result, 'factor_inversions', [])
    factor_rows = []
    for fi in factor_inversions:
        factor_name = getattr(fi, 'factor_name', 'N/A')
        cont_lift = getattr(fi, 'continuation_lift', 0)
        rej_lift = getattr(fi, 'rejection_lift', 0)
        is_inverted = getattr(fi, 'is_inverted', False)
        factor_rows.append(
            f"| {factor_name} | {cont_lift:+.1f}pp | {rej_lift:+.1f}pp | "
            f"{'YES' if is_inverted else 'No'} |"
        )
    factor_inversion_table = "\n".join(factor_rows) if factor_rows else "No factor data"

    inverted_factors = getattr(result, 'inverted_factors', [])
    requires_different = getattr(result, 'rejection_requires_different_scoring', False)

    verdict = (
        "REJECTION TRADES MAY REQUIRE DIFFERENT SCORING" if requires_different
        else "Current scoring system appears valid for both model types"
    )

    data_summary = CALC_008_DATA_FORMAT.format(
        time_table=time_table,
        inversion_table=inversion_table,
        factor_inversion_table=factor_inversion_table,
        inverted_factors=", ".join(inverted_factors) if inverted_factors else "None",
        verdict=verdict
    )

    user_prompt = CALC_008_ANALYSIS_TEMPLATE.format(data_summary=data_summary)

    return IndicatorAnalysisPrompt(
        system_prompt=INDICATOR_ANALYSIS_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        analysis_type="CALC-008: Rejection Dynamics",
        data_summary=data_summary,
        estimated_tokens=estimate_tokens(INDICATOR_ANALYSIS_SYSTEM_PROMPT + user_prompt)
    )


def generate_synthesis_prompt(
    calc_005_result=None,
    calc_006_result=None,
    calc_007_result=None,
    calc_008_result=None
) -> IndicatorAnalysisPrompt:
    """
    Generate comprehensive synthesis prompt combining all CALC results.
    Includes FULL detailed data from each module for thorough analysis.

    Parameters:
        calc_005_result: HealthCorrelationResult (optional)
        calc_006_result: FactorImportanceResult (optional)
        calc_007_result: IndicatorProgressionResult (optional)
        calc_008_result: RejectionDynamicsResult (optional)

    Returns:
        IndicatorAnalysisPrompt with synthesis template
    """
    sections = []

    # =========================================================================
    # CALC-005: Full Health Score Correlation Data
    # =========================================================================
    if calc_005_result:
        total_trades = getattr(calc_005_result, 'total_trades', 0)
        overall_win_rate = getattr(calc_005_result, 'overall_win_rate', 0)
        correlation = getattr(calc_005_result, 'correlation_coefficient', 0)
        pvalue = getattr(calc_005_result, 'correlation_pvalue', 1)
        optimal_threshold = getattr(calc_005_result, 'optimal_threshold', 0)
        optimal_lift = getattr(calc_005_result, 'optimal_threshold_lift', 0)

        # Full bucket breakdown
        bucket_table = ""
        bucket_df = getattr(calc_005_result, 'bucket_distribution', None)
        if bucket_df is not None and not bucket_df.empty:
            bucket_table = "\n| Bucket | Trades | Win Rate | Lift |\n|--------|--------|----------|------|\n"
            for _, row in bucket_df.iterrows():
                bucket_name = row.get('bucket', 'N/A')
                trades = row.get('trades', 0)
                wr = row.get('win_rate', 0)
                lift = wr - overall_win_rate
                bucket_table += f"| {bucket_name} | {trades} | {wr:.1f}% | {lift:+.1f}pp |\n"

        # Model-direction breakdown
        model_breakdown = ""
        md_df = getattr(calc_005_result, 'model_direction_breakdown', None)
        if md_df is not None and not md_df.empty:
            model_breakdown = "\n**Win Rate by Model and Direction:**\n"
            model_breakdown += "| Model | Direction | Trades | Win Rate |\n|-------|-----------|--------|----------|\n"
            for _, row in md_df.iterrows():
                model_breakdown += f"| {row.get('model', 'N/A')} | {row.get('direction', 'N/A')} | {row.get('trades', 0)} | {row.get('win_rate', 0):.1f}% |\n"

        # Threshold analysis
        threshold_table = ""
        threshold_df = getattr(calc_005_result, 'threshold_analysis', None)
        if threshold_df is not None and not threshold_df.empty:
            threshold_table = "\n**Win Rate by Health Score Threshold:**\n"
            threshold_table += "| Threshold | Trades Above | Win Rate | Lift |\n|-----------|--------------|----------|------|\n"
            for _, row in threshold_df.iterrows():
                threshold_table += f"| >= {row.get('threshold', 0)} | {row.get('trades_above', 0)} | {row.get('win_rate_above', 0):.1f}% | {row.get('lift', 0):+.1f}pp |\n"

        sections.append(f"""
## CALC-005: Health Score Correlation Analysis (FULL DATA)

**Summary Statistics:**
- Total Trades Analyzed: {total_trades:,}
- Overall Win Rate: {overall_win_rate:.1f}%
- Correlation Coefficient: r = {correlation:.3f} (p-value: {pvalue:.4f})
- Optimal Threshold: >= {optimal_threshold} (lift: +{optimal_lift:.1f}pp)

**Win Rate by Health Score Bucket:**
{bucket_table}
{model_breakdown}
{threshold_table}
""")

    # =========================================================================
    # CALC-006: Full Factor Importance Data
    # =========================================================================
    if calc_006_result:
        top_factors = getattr(calc_006_result, 'top_factors', [])
        dead_factors = getattr(calc_006_result, 'dead_factors', [])

        # Full factor analysis table
        factor_table = ""
        factors = getattr(calc_006_result, 'factor_analyses', [])
        if factors:
            factor_table = "\n| Rank | Factor | Group | Healthy WR | Unhealthy WR | Lift | Healthy n | Unhealthy n |\n"
            factor_table += "|------|--------|-------|------------|--------------|------|-----------|-------------|\n"
            for i, f in enumerate(factors):
                factor_name = getattr(f, 'factor_name', 'N/A')
                group = getattr(f, 'group', 'N/A')
                healthy_wr = getattr(f, 'healthy_win_rate', 0)
                unhealthy_wr = getattr(f, 'unhealthy_win_rate', 0)
                lift = getattr(f, 'lift', 0)
                healthy_n = getattr(f, 'healthy_trades', 0)
                unhealthy_n = getattr(f, 'unhealthy_trades', 0)
                factor_table += f"| {i+1} | {factor_name} | {group} | {healthy_wr:.1f}% | {unhealthy_wr:.1f}% | {lift:+.1f}pp | {healthy_n} | {unhealthy_n} |\n"

        # Group summary
        group_table = ""
        group_df = getattr(calc_006_result, 'group_summary', None)
        if group_df is not None and not group_df.empty:
            group_table = "\n**Factor Group Performance:**\n"
            group_table += "| Group | Avg Lift | Best Factor |\n|-------|----------|-------------|\n"
            for _, row in group_df.iterrows():
                group_table += f"| {row.get('group', 'N/A')} | {row.get('avg_lift', 0):+.1f}pp | {row.get('best_factor', 'N/A')} |\n"

        sections.append(f"""
## CALC-006: Factor Importance Analysis (FULL DATA)

**Summary:**
- Top Performing Factors (lift > 5pp): {', '.join(top_factors) if top_factors else 'None'}
- Dead Factors (lift < 2pp): {', '.join(dead_factors) if dead_factors else 'None'}

**Complete Factor Ranking:**
{factor_table}
{group_table}
""")

    # =========================================================================
    # CALC-007: Full Progression Analysis Data
    # =========================================================================
    if calc_007_result:
        winner_path = getattr(calc_007_result, 'winner_path', None)
        loser_path = getattr(calc_007_result, 'loser_path', None)

        # Path comparison
        path_table = "\n| Metric | Winners | Losers | Difference |\n|--------|---------|--------|------------|\n"

        w_entry = w_peak = w_delta = l_entry = l_peak = l_delta = 0
        if winner_path:
            w_snap = getattr(winner_path, 'entry_snapshot', None)
            w_peak_snap = getattr(winner_path, 'peak_snapshot', None)
            w_entry = getattr(w_snap, 'avg_health_score', 0) if w_snap else 0
            w_peak = getattr(w_peak_snap, 'avg_health_score', 0) if w_peak_snap else 0
            w_delta = getattr(winner_path, 'health_delta_to_peak', 0)
        if loser_path:
            l_snap = getattr(loser_path, 'entry_snapshot', None)
            l_peak_snap = getattr(loser_path, 'peak_snapshot', None)
            l_entry = getattr(l_snap, 'avg_health_score', 0) if l_snap else 0
            l_peak = getattr(l_peak_snap, 'avg_health_score', 0) if l_peak_snap else 0
            l_delta = getattr(loser_path, 'health_delta_to_peak', 0)

        path_table += f"| Entry Health Score | {w_entry:.1f} | {l_entry:.1f} | {w_entry - l_entry:+.1f} |\n"
        path_table += f"| Peak Health Score | {w_peak:.1f} | {l_peak:.1f} | {w_peak - l_peak:+.1f} |\n"
        path_table += f"| Delta to Peak | {w_delta:+.1f} | {l_delta:+.1f} | {w_delta - l_delta:+.1f} |\n"

        # Early warning signals
        warning_table = ""
        warnings = getattr(calc_007_result, 'early_warnings', [])
        if warnings:
            warning_table = "\n**Early Warning Signals (All):**\n"
            warning_table += "| Indicator | Threshold | Window | Loser Hit% | Winner Hit% | Lift |\n"
            warning_table += "|-----------|-----------|--------|------------|-------------|------|\n"
            for w in warnings:
                indicator = getattr(w, 'indicator', 'N/A')
                threshold = getattr(w, 'threshold', 0)
                window = getattr(w, 'bars_window', 0)
                loser_hit = getattr(w, 'hit_rate_losers', 0)
                winner_hit = getattr(w, 'hit_rate_winners', 0)
                lift = getattr(w, 'lift', 0)
                warning_table += f"| {indicator} | {threshold} | {window} bars | {loser_hit:.1f}% | {winner_hit:.1f}% | {lift:+.1f}pp |\n"

        # Best warning summary
        best_warning_text = "None identified"
        bw = getattr(calc_007_result, 'best_warning', None)
        if bw:
            best_warning_text = f"{getattr(bw, 'indicator', 'N/A')} <= {getattr(bw, 'threshold', 0)} within {getattr(bw, 'bars_window', 0)} bars (captures {getattr(bw, 'hit_rate_losers', 0):.0f}% losers, {getattr(bw, 'hit_rate_winners', 0):.0f}% false positives)"

        # Factor degradation
        degradation_table = ""
        degradations = getattr(calc_007_result, 'factor_degradations', [])
        if degradations:
            degradation_table = "\n**Factor Degradation Analysis:**\n"
            degradation_table += "| Factor | Winner Degrade% | Loser Degrade% | Difference |\n"
            degradation_table += "|--------|-----------------|----------------|------------|\n"
            for d in degradations:
                factor = getattr(d, 'factor', 'N/A')
                w_deg = getattr(d, 'winner_degradation_pct', 0)
                l_deg = getattr(d, 'loser_degradation_pct', 0)
                degradation_table += f"| {factor} | {w_deg:.1f}% | {l_deg:.1f}% | {l_deg - w_deg:+.1f}pp |\n"

        sections.append(f"""
## CALC-007: Indicator Progression Analysis (FULL DATA)

**Winner vs Loser Path Comparison:**
{path_table}

**Best Early Warning Signal:**
{best_warning_text}
{warning_table}
{degradation_table}
""")

    # =========================================================================
    # CALC-008: Full Rejection Dynamics Data
    # =========================================================================
    if calc_008_result:
        # Time-to-MFE comparison
        time_table = ""
        time_df = getattr(calc_008_result, 'time_comparison', None)
        if time_df is not None and not time_df.empty:
            time_table = "\n**Time-to-MFE Comparison:**\n"
            time_table += time_df.to_string(index=False) + "\n"

        # Health score inversion test
        inversion_table = "\n**Health Score Inversion Test:**\n"
        inversion_table += "| Model Type | Correlation | STRONG Win% | CRITICAL Win% | Inverted? |\n"
        inversion_table += "|------------|-------------|-------------|---------------|----------|\n"

        ci = getattr(calc_008_result, 'continuation_inversion', None)
        ri = getattr(calc_008_result, 'rejection_inversion', None)
        if ci:
            inversion_table += f"| Continuation | {ci.correlation:.3f} | {ci.strong_win_rate:.1f}% (n={ci.strong_trades}) | {ci.critical_win_rate:.1f}% (n={ci.critical_trades}) | {'YES' if ci.is_inverted else 'No'} |\n"
        if ri:
            inversion_table += f"| Rejection | {ri.correlation:.3f} | {ri.strong_win_rate:.1f}% (n={ri.strong_trades}) | {ri.critical_win_rate:.1f}% (n={ri.critical_trades}) | {'YES' if ri.is_inverted else 'No'} |\n"

        # Full factor inversion table
        factor_inv_table = "\n**Factor Inversion Analysis (Continuation vs Rejection):**\n"
        factor_inv_table += "| Factor | Cont. Healthy WR | Cont. Unhealthy WR | Cont. Lift | Rej. Healthy WR | Rej. Unhealthy WR | Rej. Lift | Inverted? | Strength |\n"
        factor_inv_table += "|--------|------------------|--------------------|-----------:|-----------------|-------------------|----------:|-----------|----------|\n"

        factor_inversions = getattr(calc_008_result, 'factor_inversions', [])
        for fi in factor_inversions:
            factor_name = getattr(fi, 'factor_name', 'N/A')
            cont_h_wr = getattr(fi, 'continuation_healthy_wr', 0)
            cont_u_wr = getattr(fi, 'continuation_unhealthy_wr', 0)
            cont_lift = getattr(fi, 'continuation_lift', 0)
            rej_h_wr = getattr(fi, 'rejection_healthy_wr', 0)
            rej_u_wr = getattr(fi, 'rejection_unhealthy_wr', 0)
            rej_lift = getattr(fi, 'rejection_lift', 0)
            is_inv = getattr(fi, 'is_inverted', False)
            strength = getattr(fi, 'inversion_strength', 'NONE')
            factor_inv_table += f"| {factor_name} | {cont_h_wr:.1f}% | {cont_u_wr:.1f}% | {cont_lift:+.1f}pp | {rej_h_wr:.1f}% | {rej_u_wr:.1f}% | {rej_lift:+.1f}pp | {'YES' if is_inv else 'No'} | {strength} |\n"

        # Exhaustion indicators
        exhaustion_table = ""
        exhaust_df = getattr(calc_008_result, 'exhaustion_analysis', None)
        if exhaust_df is not None and not exhaust_df.empty:
            exhaustion_table = "\n**Exhaustion Indicator Discovery (Rejection Trades Only):**\n"
            exhaustion_table += exhaust_df.to_string(index=False) + "\n"

        inverted_factors = getattr(calc_008_result, 'inverted_factors', [])
        requires_different = getattr(calc_008_result, 'rejection_requires_different_scoring', False)

        verdict = "**REJECTION TRADES MAY REQUIRE DIFFERENT SCORING**" if requires_different else "Current scoring system appears valid for both model types"

        sections.append(f"""
## CALC-008: Rejection Dynamics Analysis (FULL DATA)
{time_table}
{inversion_table}
{factor_inv_table}
{exhaustion_table}

**Inverted Factors:** {', '.join(inverted_factors) if inverted_factors else 'None identified'}

**VERDICT:** {verdict}
""")

    data_summary = "\n".join(sections) if sections else "No analysis results available. Run CALC-005 through CALC-008 first."

    user_prompt = SYNTHESIS_ANALYSIS_TEMPLATE.format(data_summary=data_summary)

    return IndicatorAnalysisPrompt(
        system_prompt=INDICATOR_ANALYSIS_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        analysis_type="Synthesis: All Indicator Analyses",
        data_summary=data_summary,
        estimated_tokens=estimate_tokens(INDICATOR_ANALYSIS_SYSTEM_PROMPT + user_prompt)
    )
