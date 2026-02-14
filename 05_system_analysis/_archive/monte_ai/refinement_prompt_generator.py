"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Monte AI - Indicator Refinement Prompt Generator (CALC-010)
XIII Trading LLC
================================================================================

Generates analysis prompts for Continuation/Rejection qualification scores.

================================================================================
"""

import pandas as pd
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .refinement_prompts import (
    REFINEMENT_ANALYSIS_SYSTEM_PROMPT,
    CONTINUATION_ANALYSIS_TEMPLATE,
    REJECTION_ANALYSIS_TEMPLATE,
    REFINEMENT_SYNTHESIS_TEMPLATE,
    CONTINUATION_DATA_FORMAT,
    REJECTION_DATA_FORMAT,
    COMBINED_DATA_FORMAT
)


@dataclass
class RefinementAnalysisPrompt:
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
# SCORE THRESHOLDS
# =============================================================================

CONTINUATION_THRESHOLDS = {
    'STRONG': (8, 10),
    'GOOD': (6, 7),
    'WEAK': (4, 5),
    'AVOID': (0, 3)
}

REJECTION_THRESHOLDS = {
    'STRONG': (9, 11),
    'GOOD': (6, 8),
    'WEAK': (4, 5),
    'AVOID': (0, 3)
}


# =============================================================================
# DATA FORMATTING HELPERS
# =============================================================================

def format_score_label_table(df: pd.DataFrame, score_col: str, thresholds: Dict, baseline_wr: float) -> str:
    """Format win rate by score label as markdown table."""
    if df is None or df.empty:
        return "No data available"

    rows = []
    for label, (min_val, max_val) in thresholds.items():
        bucket_df = df[(df[score_col] >= min_val) & (df[score_col] <= max_val)]
        if len(bucket_df) > 0:
            win_rate = bucket_df['is_winner'].sum() / len(bucket_df) * 100
            lift = win_rate - baseline_wr
            lift_str = f"+{lift:.1f}pp" if lift > 0 else f"{lift:.1f}pp"
            rows.append(f"| {label} | {min_val}-{max_val} | {len(bucket_df):,} | {win_rate:.1f}% | {lift_str} |")

    return "\n".join(rows) if rows else "Insufficient data"


def format_indicator_table(df: pd.DataFrame, indicators: List[tuple]) -> str:
    """Format indicator contribution table."""
    if df is None or df.empty:
        return "No data available"

    winners = df[df['is_winner'] == True]
    losers = df[df['is_winner'] == False]

    rows = []
    for col, name, max_pts in indicators:
        if col in df.columns:
            win_avg = pd.to_numeric(winners[col], errors='coerce').mean()
            loss_avg = pd.to_numeric(losers[col], errors='coerce').mean()

            win_avg = win_avg if pd.notna(win_avg) else 0
            loss_avg = loss_avg if pd.notna(loss_avg) else 0
            delta = win_avg - loss_avg

            delta_str = f"+{delta:.2f}" if delta > 0 else f"{delta:.2f}"
            rows.append(f"| {name} | {max_pts} | {win_avg:.2f} | {loss_avg:.2f} | {delta_str} |")

    return "\n".join(rows) if rows else "No indicator data"


# =============================================================================
# PROMPT GENERATORS
# =============================================================================

def generate_continuation_prompt(df: pd.DataFrame) -> RefinementAnalysisPrompt:
    """
    Generate prompt for Continuation trade analysis.

    Args:
        df: DataFrame with continuation trades from indicator_refinement

    Returns:
        RefinementAnalysisPrompt ready for Claude
    """
    if df is None or df.empty:
        return RefinementAnalysisPrompt(
            system_prompt=REFINEMENT_ANALYSIS_SYSTEM_PROMPT,
            user_prompt="No continuation trade data available.",
            analysis_type="Continuation Analysis",
            data_summary="No data",
            estimated_tokens=100
        )

    # Calculate statistics
    total_trades = len(df)
    overall_win_rate = df['is_winner'].sum() / total_trades * 100 if total_trades > 0 else 0
    avg_score = df['continuation_score'].mean() if 'continuation_score' in df.columns else 0

    # Format score label table
    score_label_table = format_score_label_table(
        df, 'continuation_score', CONTINUATION_THRESHOLDS, overall_win_rate
    )

    # Define continuation indicators
    indicators = [
        ('mtf_alignment_points', 'MTF Alignment (CONT-01)', 4),
        ('sma_momentum_points', 'SMA Momentum (CONT-02)', 2),
        ('volume_thrust_points', 'Volume Thrust (CONT-03)', 2),
        ('pullback_quality_points', 'Pullback Quality (CONT-04)', 2)
    ]

    indicator_table = format_indicator_table(df, indicators)

    data_summary = CONTINUATION_DATA_FORMAT.format(
        total_trades=total_trades,
        overall_win_rate=overall_win_rate,
        avg_score=avg_score,
        score_label_table=score_label_table,
        indicator_table=indicator_table
    )

    user_prompt = CONTINUATION_ANALYSIS_TEMPLATE.format(data_summary=data_summary)
    full_prompt = f"{REFINEMENT_ANALYSIS_SYSTEM_PROMPT}\n\n{user_prompt}"

    return RefinementAnalysisPrompt(
        system_prompt=REFINEMENT_ANALYSIS_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        analysis_type="Continuation Score Analysis",
        data_summary=data_summary,
        estimated_tokens=estimate_tokens(full_prompt)
    )


def generate_rejection_prompt(df: pd.DataFrame) -> RefinementAnalysisPrompt:
    """
    Generate prompt for Rejection trade analysis.

    Args:
        df: DataFrame with rejection trades from indicator_refinement

    Returns:
        RefinementAnalysisPrompt ready for Claude
    """
    if df is None or df.empty:
        return RefinementAnalysisPrompt(
            system_prompt=REFINEMENT_ANALYSIS_SYSTEM_PROMPT,
            user_prompt="No rejection trade data available.",
            analysis_type="Rejection Analysis",
            data_summary="No data",
            estimated_tokens=100
        )

    # Calculate statistics
    total_trades = len(df)
    overall_win_rate = df['is_winner'].sum() / total_trades * 100 if total_trades > 0 else 0
    avg_score = df['rejection_score'].mean() if 'rejection_score' in df.columns else 0

    # Format score label table
    score_label_table = format_score_label_table(
        df, 'rejection_score', REJECTION_THRESHOLDS, overall_win_rate
    )

    # Define rejection indicators
    indicators = [
        ('structure_divergence_points', 'Structure Divergence (REJ-01)', 3),
        ('sma_exhaustion_points', 'SMA Exhaustion (REJ-02)', 2),
        ('delta_absorption_points', 'Delta Absorption (REJ-03)', 2),
        ('volume_climax_points', 'Volume Climax (REJ-04)', 2),
        ('cvd_extreme_points', 'CVD Extreme (REJ-05)', 2)
    ]

    indicator_table = format_indicator_table(df, indicators)

    data_summary = REJECTION_DATA_FORMAT.format(
        total_trades=total_trades,
        overall_win_rate=overall_win_rate,
        avg_score=avg_score,
        score_label_table=score_label_table,
        indicator_table=indicator_table
    )

    user_prompt = REJECTION_ANALYSIS_TEMPLATE.format(data_summary=data_summary)
    full_prompt = f"{REFINEMENT_ANALYSIS_SYSTEM_PROMPT}\n\n{user_prompt}"

    return RefinementAnalysisPrompt(
        system_prompt=REFINEMENT_ANALYSIS_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        analysis_type="Rejection Score Analysis",
        data_summary=data_summary,
        estimated_tokens=estimate_tokens(full_prompt)
    )


def generate_refinement_synthesis_prompt(
    cont_df: pd.DataFrame,
    rej_df: pd.DataFrame
) -> RefinementAnalysisPrompt:
    """
    Generate comprehensive synthesis prompt for both trade types.

    Args:
        cont_df: DataFrame with continuation trades
        rej_df: DataFrame with rejection trades

    Returns:
        RefinementAnalysisPrompt with synthesis template
    """
    # Continuation stats
    cont_trades = len(cont_df) if cont_df is not None and not cont_df.empty else 0
    cont_wr = cont_df['is_winner'].sum() / cont_trades * 100 if cont_trades > 0 else 0
    cont_avg = cont_df['continuation_score'].mean() if cont_trades > 0 and 'continuation_score' in cont_df.columns else 0

    # Rejection stats
    rej_trades = len(rej_df) if rej_df is not None and not rej_df.empty else 0
    rej_wr = rej_df['is_winner'].sum() / rej_trades * 100 if rej_trades > 0 else 0
    rej_avg = rej_df['rejection_score'].mean() if rej_trades > 0 and 'rejection_score' in rej_df.columns else 0

    # Continuation indicator details
    cont_indicators = [
        ('mtf_alignment_points', 'MTF Alignment (CONT-01)', 4),
        ('sma_momentum_points', 'SMA Momentum (CONT-02)', 2),
        ('volume_thrust_points', 'Volume Thrust (CONT-03)', 2),
        ('pullback_quality_points', 'Pullback Quality (CONT-04)', 2)
    ]

    # Rejection indicator details
    rej_indicators = [
        ('structure_divergence_points', 'Structure Divergence (REJ-01)', 3),
        ('sma_exhaustion_points', 'SMA Exhaustion (REJ-02)', 2),
        ('delta_absorption_points', 'Delta Absorption (REJ-03)', 2),
        ('volume_climax_points', 'Volume Climax (REJ-04)', 2),
        ('cvd_extreme_points', 'CVD Extreme (REJ-05)', 2)
    ]

    # Format tables
    cont_score_table = format_score_label_table(
        cont_df, 'continuation_score', CONTINUATION_THRESHOLDS, cont_wr
    ) if cont_trades > 0 else "No continuation data"

    rej_score_table = format_score_label_table(
        rej_df, 'rejection_score', REJECTION_THRESHOLDS, rej_wr
    ) if rej_trades > 0 else "No rejection data"

    cont_indicator_table = format_indicator_table(cont_df, cont_indicators) if cont_trades > 0 else "No data"
    rej_indicator_table = format_indicator_table(rej_df, rej_indicators) if rej_trades > 0 else "No data"

    continuation_details = f"""
**Indicator Breakdown:**
| Indicator | Max Pts | Winners Avg | Losers Avg | Delta |
|-----------|---------|-------------|------------|-------|
{cont_indicator_table}
"""

    rejection_details = f"""
**Indicator Breakdown:**
| Indicator | Max Pts | Winners Avg | Losers Avg | Delta |
|-----------|---------|-------------|------------|-------|
{rej_indicator_table}
"""

    data_summary = COMBINED_DATA_FORMAT.format(
        cont_trades=cont_trades,
        cont_wr=cont_wr,
        cont_avg=cont_avg,
        rej_trades=rej_trades,
        rej_wr=rej_wr,
        rej_avg=rej_avg,
        continuation_details=continuation_details,
        rejection_details=rejection_details,
        cont_score_table=cont_score_table,
        rej_score_table=rej_score_table
    )

    user_prompt = REFINEMENT_SYNTHESIS_TEMPLATE.format(data_summary=data_summary)
    full_prompt = f"{REFINEMENT_ANALYSIS_SYSTEM_PROMPT}\n\n{user_prompt}"

    return RefinementAnalysisPrompt(
        system_prompt=REFINEMENT_ANALYSIS_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        analysis_type="Refinement Synthesis",
        data_summary=data_summary,
        estimated_tokens=estimate_tokens(full_prompt)
    )
