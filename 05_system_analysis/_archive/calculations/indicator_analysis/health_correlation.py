"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
CALC-005: Health Score Correlation Analysis
XIII Trading LLC
================================================================================

Analyzes correlation between Health Score at entry and trade outcomes.
Validates the DOW AI scoring system.

Core Question: "If DOW AI sees Health Score 8+ at entry, should it
recommend the trade more confidently?"

WIN CONDITION (Stop-Based):
    Win = MFE reached (>=1R) before stop hit
    Loss = Stop hit before reaching 1R

    The is_winner flag must be pre-computed from stop_analysis table
    and merged into the data before calling these functions.
    Default stop type: Zone + 5% Buffer

Version: 1.1.0
Updated: 2026-01-11
- Removed temporal mfe_time < mae_time logic
- Now uses stop-based is_winner exclusively
================================================================================
"""

import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import streamlit as st

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import INDICATOR_ANALYSIS_CONFIG


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class HealthCorrelationResult:
    """Container for health correlation analysis results."""
    # Overall statistics
    total_trades: int
    overall_win_rate: float
    correlation_coefficient: float
    correlation_pvalue: float

    # By score (0-10)
    score_distribution: pd.DataFrame  # [health_score, trades, wins, win_rate, ci_lower, ci_upper]

    # By bucket
    bucket_distribution: pd.DataFrame  # [bucket, trades, wins, win_rate, lift, ci_lower, ci_upper]

    # By model-direction
    model_direction_breakdown: pd.DataFrame  # [model, direction, health_bucket, trades, win_rate, lift]

    # Optimal threshold analysis
    threshold_analysis: pd.DataFrame  # [threshold, trades_above, win_rate_above, lift, trades_excluded]
    optimal_threshold: int
    optimal_threshold_lift: float


# =============================================================================
# STATISTICAL FUNCTIONS
# =============================================================================

def wilson_confidence_interval(wins: int, total: int, confidence: float = 0.95) -> Tuple[float, float]:
    """
    Calculate Wilson score confidence interval for a proportion.

    More accurate than normal approximation for small samples or extreme proportions.

    Args:
        wins: Number of successes
        total: Total trials
        confidence: Confidence level (default 0.95)

    Returns:
        Tuple of (lower_bound, upper_bound) as percentages
    """
    if total == 0:
        return (0.0, 0.0)

    z = stats.norm.ppf(1 - (1 - confidence) / 2)
    p = wins / total

    denominator = 1 + z**2 / total
    center = (p + z**2 / (2 * total)) / denominator
    margin = z * np.sqrt((p * (1 - p) + z**2 / (4 * total)) / total) / denominator

    return (max(0, center - margin) * 100, min(1, center + margin) * 100)


def calculate_correlation(df: pd.DataFrame) -> Tuple[float, float]:
    """
    Calculate Pearson correlation between health score and win rate.

    Args:
        df: DataFrame with columns [health_score, is_winner]

    Returns:
        Tuple of (correlation_coefficient, p_value)
    """
    if len(df) < 3:
        return (0.0, 1.0)

    # Convert is_winner to numeric
    wins = df['is_winner'].astype(int)
    scores = df['health_score']

    try:
        correlation, pvalue = stats.pearsonr(scores, wins)
        return (correlation, pvalue)
    except Exception:
        return (0.0, 1.0)


# =============================================================================
# CALCULATION FUNCTIONS
# =============================================================================

def calculate_win_rate_by_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate win rate for each health score value (0-10).

    Args:
        df: DataFrame with columns [health_score, is_winner]

    Returns:
        DataFrame with [health_score, trades, wins, losses, win_rate, ci_lower, ci_upper]
    """
    results = []

    for score in range(11):  # 0 to 10
        score_data = df[df['health_score'] == score]
        trades = len(score_data)
        wins = int(score_data['is_winner'].sum()) if trades > 0 else 0
        losses = trades - wins
        win_rate = (wins / trades * 100) if trades > 0 else 0

        ci_lower, ci_upper = wilson_confidence_interval(wins, trades)

        results.append({
            'health_score': score,
            'trades': trades,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper
        })

    return pd.DataFrame(results)


def calculate_win_rate_by_bucket(
    df: pd.DataFrame,
    baseline_win_rate: float
) -> pd.DataFrame:
    """
    Calculate win rate for each health score bucket.

    Args:
        df: DataFrame with columns [health_score, is_winner]
        baseline_win_rate: Overall win rate for lift calculation

    Returns:
        DataFrame with [bucket, bucket_range, trades, wins, win_rate, lift, ci_lower, ci_upper]
    """
    buckets = INDICATOR_ANALYSIS_CONFIG['health_buckets']
    results = []

    for bucket_name, (low, high) in buckets.items():
        bucket_data = df[(df['health_score'] >= low) & (df['health_score'] <= high)]
        trades = len(bucket_data)
        wins = int(bucket_data['is_winner'].sum()) if trades > 0 else 0
        win_rate = (wins / trades * 100) if trades > 0 else 0
        lift = win_rate - baseline_win_rate

        ci_lower, ci_upper = wilson_confidence_interval(wins, trades)

        results.append({
            'bucket': bucket_name,
            'bucket_label': f"{bucket_name} ({low}-{high})",
            'low': low,
            'high': high,
            'trades': trades,
            'wins': wins,
            'win_rate': win_rate,
            'lift': lift,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper
        })

    # Sort by bucket order
    bucket_order = ['CRITICAL', 'WEAK', 'MODERATE', 'STRONG']
    result_df = pd.DataFrame(results)
    result_df['bucket'] = pd.Categorical(result_df['bucket'], categories=bucket_order, ordered=True)
    return result_df.sort_values('bucket')


def calculate_model_direction_breakdown(
    df: pd.DataFrame,
    baseline_win_rate: float
) -> pd.DataFrame:
    """
    Calculate win rate by health bucket for each model-direction combination.

    Args:
        df: DataFrame with columns [health_score, is_winner, model, direction]
        baseline_win_rate: Overall win rate for lift calculation

    Returns:
        DataFrame with breakdown by model, direction, and bucket
    """
    buckets = INDICATOR_ANALYSIS_CONFIG['health_buckets']
    results = []

    for model in df['model'].dropna().unique():
        for direction in df['direction'].dropna().unique():
            subset = df[(df['model'] == model) & (df['direction'] == direction)]

            if len(subset) == 0:
                continue

            model_baseline = (subset['is_winner'].sum() / len(subset) * 100) if len(subset) > 0 else 0

            for bucket_name, (low, high) in buckets.items():
                bucket_data = subset[(subset['health_score'] >= low) & (subset['health_score'] <= high)]
                trades = len(bucket_data)
                wins = int(bucket_data['is_winner'].sum()) if trades > 0 else 0
                win_rate = (wins / trades * 100) if trades > 0 else 0
                lift_vs_overall = win_rate - baseline_win_rate
                lift_vs_model = win_rate - model_baseline

                results.append({
                    'model': model,
                    'direction': direction,
                    'bucket': bucket_name,
                    'trades': trades,
                    'wins': wins,
                    'win_rate': win_rate,
                    'model_baseline': model_baseline,
                    'lift_vs_overall': lift_vs_overall,
                    'lift_vs_model': lift_vs_model
                })

    return pd.DataFrame(results)


def calculate_threshold_analysis(
    df: pd.DataFrame,
    baseline_win_rate: float
) -> Tuple[pd.DataFrame, int, float]:
    """
    Analyze win rate at different minimum health score thresholds.
    Find optimal threshold that maximizes lift while maintaining sample size.

    Args:
        df: DataFrame with columns [health_score, is_winner]
        baseline_win_rate: Overall win rate

    Returns:
        Tuple of (threshold_df, optimal_threshold, optimal_lift)
    """
    min_trades = INDICATOR_ANALYSIS_CONFIG['min_trades_for_analysis']
    results = []

    total_trades = len(df)

    for threshold in range(11):  # 0 to 10
        above = df[df['health_score'] >= threshold]
        trades_above = len(above)
        wins_above = int(above['is_winner'].sum()) if trades_above > 0 else 0
        win_rate_above = (wins_above / trades_above * 100) if trades_above > 0 else 0
        lift = win_rate_above - baseline_win_rate
        trades_excluded = total_trades - trades_above
        pct_excluded = (trades_excluded / total_trades * 100) if total_trades > 0 else 0

        # Statistical significance check
        statistically_valid = trades_above >= min_trades

        results.append({
            'threshold': threshold,
            'trades_above': trades_above,
            'wins_above': wins_above,
            'win_rate_above': win_rate_above,
            'lift': lift,
            'trades_excluded': trades_excluded,
            'pct_excluded': pct_excluded,
            'statistically_valid': statistically_valid
        })

    result_df = pd.DataFrame(results)

    # Find optimal threshold (maximize lift while maintaining statistical validity)
    # Also don't exclude more than 50% of trades
    valid_thresholds = result_df[
        (result_df['statistically_valid']) &
        (result_df['pct_excluded'] <= 50)
    ]

    if len(valid_thresholds) > 0:
        optimal_idx = valid_thresholds['lift'].idxmax()
        optimal_threshold = int(result_df.loc[optimal_idx, 'threshold'])
        optimal_lift = result_df.loc[optimal_idx, 'lift']
    else:
        optimal_threshold = 0
        optimal_lift = 0.0

    return result_df, optimal_threshold, optimal_lift


# =============================================================================
# MAIN ANALYSIS FUNCTION
# =============================================================================

def analyze_health_correlation(df: pd.DataFrame) -> HealthCorrelationResult:
    """
    Main analysis function for CALC-005.

    Args:
        df: DataFrame with columns [health_score, is_winner, model, direction]

    Returns:
        HealthCorrelationResult with all analysis outputs
    """
    # Filter to valid data - must have both health_score AND is_winner
    # is_winner may be None for trades without stop analysis data
    df_valid = df[df['health_score'].notna() & df['is_winner'].notna()].copy()

    if len(df_valid) == 0:
        raise ValueError("No valid data for health correlation analysis. Ensure stop_analysis table is populated.")

    # Overall statistics
    total_trades = len(df_valid)
    overall_wins = int(df_valid['is_winner'].sum())
    overall_win_rate = (overall_wins / total_trades * 100) if total_trades > 0 else 0

    # Correlation
    corr_coef, corr_pvalue = calculate_correlation(df_valid)

    # By score
    score_dist = calculate_win_rate_by_score(df_valid)

    # By bucket
    bucket_dist = calculate_win_rate_by_bucket(df_valid, overall_win_rate)

    # By model-direction
    model_dir_breakdown = calculate_model_direction_breakdown(df_valid, overall_win_rate)

    # Threshold analysis
    threshold_df, optimal_thresh, optimal_lift = calculate_threshold_analysis(df_valid, overall_win_rate)

    return HealthCorrelationResult(
        total_trades=total_trades,
        overall_win_rate=overall_win_rate,
        correlation_coefficient=corr_coef,
        correlation_pvalue=corr_pvalue,
        score_distribution=score_dist,
        bucket_distribution=bucket_dist,
        model_direction_breakdown=model_dir_breakdown,
        threshold_analysis=threshold_df,
        optimal_threshold=optimal_thresh,
        optimal_threshold_lift=optimal_lift
    )


# =============================================================================
# STREAMLIT RENDERING FUNCTIONS
# =============================================================================

def render_correlation_summary_cards(result: HealthCorrelationResult):
    """Render summary metric cards for correlation analysis."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Trades",
            value=f"{result.total_trades:,}"
        )

    with col2:
        st.metric(
            label="Baseline Win Rate",
            value=f"{result.overall_win_rate:.1f}%"
        )

    with col3:
        significance = "p<0.05" if result.correlation_pvalue < 0.05 else "not significant"
        st.metric(
            label="Correlation (r)",
            value=f"{result.correlation_coefficient:.3f}",
            delta=significance
        )

    with col4:
        st.metric(
            label="Optimal Threshold",
            value=f">= {result.optimal_threshold}",
            delta=f"+{result.optimal_threshold_lift:.1f}pp lift"
        )


def render_score_curve_chart(result: HealthCorrelationResult):
    """Render win rate by health score curve with confidence bands."""
    from components.indicator_charts import render_health_correlation_curve

    fig = render_health_correlation_curve(result.score_distribution)
    st.plotly_chart(fig, use_container_width=True)


def render_bucket_comparison_chart(result: HealthCorrelationResult):
    """Render win rate by health bucket bar chart."""
    import plotly.graph_objects as go

    df = result.bucket_distribution

    # Color based on lift
    colors = ['#ef5350' if x < 0 else '#26a69a' for x in df['lift']]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df['bucket_label'],
        y=df['win_rate'],
        marker_color=colors,
        text=[f"{wr:.1f}%<br>n={n}" for wr, n in zip(df['win_rate'], df['trades'])],
        textposition='outside',
        error_y=dict(
            type='data',
            symmetric=False,
            array=df['ci_upper'] - df['win_rate'],
            arrayminus=df['win_rate'] - df['ci_lower'],
            color='rgba(255,255,255,0.3)'
        )
    ))

    # Baseline reference line
    fig.add_hline(
        y=result.overall_win_rate,
        line_dash="dash",
        line_color="#ffa726",
        annotation_text=f"Baseline: {result.overall_win_rate:.1f}%"
    )

    fig.update_layout(
        title="Win Rate by Health Score Bucket",
        xaxis_title="Health Score Bucket",
        yaxis_title="Win Rate (%)",
        template="plotly_dark",
        paper_bgcolor="#16213e",
        plot_bgcolor="#1a1a2e",
        font=dict(color="#e0e0e0"),
        yaxis=dict(range=[0, max(100, df['ci_upper'].max() + 10)])
    )

    st.plotly_chart(fig, use_container_width=True)


def render_model_direction_heatmap(result: HealthCorrelationResult):
    """Render heatmap of win rate by model-direction-bucket."""
    import plotly.express as px

    df = result.model_direction_breakdown

    if len(df) == 0:
        st.warning("Insufficient data for model-direction breakdown")
        return

    # Create pivot for heatmap
    df['model_dir'] = df['model'].astype(str) + ' ' + df['direction'].astype(str)

    pivot = df.pivot(
        index='model_dir',
        columns='bucket',
        values='win_rate'
    )

    # Reorder columns
    bucket_order = ['CRITICAL', 'WEAK', 'MODERATE', 'STRONG']
    pivot = pivot.reindex(columns=[b for b in bucket_order if b in pivot.columns])

    fig = px.imshow(
        pivot,
        labels=dict(x="Health Bucket", y="Model-Direction", color="Win Rate %"),
        color_continuous_scale='RdYlGn',
        aspect='auto',
        text_auto='.1f'
    )

    fig.update_layout(
        title="Win Rate Heatmap: Model-Direction vs Health Bucket",
        template="plotly_dark",
        paper_bgcolor="#16213e",
        plot_bgcolor="#1a1a2e",
        font=dict(color="#e0e0e0")
    )

    st.plotly_chart(fig, use_container_width=True)


def render_threshold_analysis_chart(result: HealthCorrelationResult):
    """Render threshold analysis showing trade-off between lift and sample size."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    df = result.threshold_analysis

    fig = make_subplots(
        rows=1, cols=1,
        specs=[[{"secondary_y": True}]]
    )

    # Win rate above threshold
    fig.add_trace(
        go.Scatter(
            x=df['threshold'],
            y=df['win_rate_above'],
            mode='lines+markers',
            name='Win Rate >= Threshold',
            line=dict(color='#26a69a', width=3),
            marker=dict(size=10)
        ),
        secondary_y=False
    )

    # Trades excluded (secondary axis)
    fig.add_trace(
        go.Bar(
            x=df['threshold'],
            y=df['pct_excluded'],
            name='% Trades Excluded',
            marker_color='rgba(239, 83, 80, 0.5)',
            opacity=0.5
        ),
        secondary_y=True
    )

    # Optimal threshold marker
    fig.add_vline(
        x=result.optimal_threshold,
        line_dash="dash",
        line_color="#ffa726",
        annotation_text=f"Optimal: {result.optimal_threshold}"
    )

    # Baseline reference
    fig.add_hline(
        y=result.overall_win_rate,
        line_dash="dot",
        line_color="#7c3aed",
        annotation_text="Baseline"
    )

    fig.update_layout(
        title="Threshold Analysis: Win Rate vs Trades Excluded",
        xaxis_title="Minimum Health Score Threshold",
        template="plotly_dark",
        paper_bgcolor="#16213e",
        plot_bgcolor="#1a1a2e",
        font=dict(color="#e0e0e0"),
        xaxis=dict(tickmode='linear', tick0=0, dtick=1)
    )

    fig.update_yaxes(title_text="Win Rate (%)", secondary_y=False)
    fig.update_yaxes(title_text="% Trades Excluded", secondary_y=True)

    st.plotly_chart(fig, use_container_width=True)


def render_lift_table(result: HealthCorrelationResult):
    """Render detailed lift analysis table."""
    df = result.bucket_distribution[['bucket_label', 'trades', 'wins', 'win_rate', 'lift', 'ci_lower', 'ci_upper']].copy()

    df.columns = ['Bucket', 'Trades', 'Wins', 'Win Rate %', 'Lift (pp)', 'CI Lower', 'CI Upper']

    # Format
    df['Win Rate %'] = df['Win Rate %'].apply(lambda x: f"{x:.1f}%")
    df['Lift (pp)'] = df['Lift (pp)'].apply(lambda x: f"+{x:.1f}" if x > 0 else f"{x:.1f}")
    df['95% CI'] = df.apply(lambda r: f"[{r['CI Lower']:.1f}%, {r['CI Upper']:.1f}%]", axis=1)

    df = df[['Bucket', 'Trades', 'Wins', 'Win Rate %', 'Lift (pp)', '95% CI']]

    st.dataframe(df, use_container_width=True, hide_index=True)


def render_key_findings(result: HealthCorrelationResult):
    """Render auto-generated key findings."""
    findings = []

    # Correlation finding
    if result.correlation_coefficient > 0.1 and result.correlation_pvalue < 0.05:
        findings.append(f"**Positive correlation** (r={result.correlation_coefficient:.3f}, p<0.05) - Health Score has predictive value")
    elif result.correlation_coefficient > 0.05:
        findings.append(f"**Weak positive correlation** (r={result.correlation_coefficient:.3f}) - Health Score has limited predictive value")
    else:
        findings.append(f"**No correlation** (r={result.correlation_coefficient:.3f}) - Health Score does not predict outcomes")

    # Spread finding
    strong_bucket = result.bucket_distribution[result.bucket_distribution['bucket'] == 'STRONG']
    critical_bucket = result.bucket_distribution[result.bucket_distribution['bucket'] == 'CRITICAL']

    if len(strong_bucket) > 0 and len(critical_bucket) > 0:
        strong_wr = strong_bucket.iloc[0]['win_rate']
        critical_wr = critical_bucket.iloc[0]['win_rate']
        spread = strong_wr - critical_wr

        if spread > 10:
            findings.append(f"**{spread:.1f}pp spread** between STRONG and CRITICAL buckets - significant differentiation")
        elif spread > 5:
            findings.append(f"**{spread:.1f}pp spread** between STRONG and CRITICAL - moderate differentiation")
        else:
            findings.append(f"**Only {spread:.1f}pp spread** - Health Score may not differentiate outcomes well")

    # Optimal threshold finding
    if result.optimal_threshold_lift > 5:
        findings.append(f"**Optimal filter at >={result.optimal_threshold}** provides +{result.optimal_threshold_lift:.1f}pp lift")
    elif result.optimal_threshold_lift > 0:
        findings.append(f"**Filter at >={result.optimal_threshold}** provides modest +{result.optimal_threshold_lift:.1f}pp lift")

    return findings


def render_calc_005_section(df: pd.DataFrame) -> Optional[HealthCorrelationResult]:
    """
    Main render function for CALC-005 section in Streamlit.

    Args:
        df: DataFrame from fetch_entry_indicators with mfe_mae_potential join

    Returns:
        HealthCorrelationResult or None on error
    """
    try:
        result = analyze_health_correlation(df)

        # Summary cards
        render_correlation_summary_cards(result)

        st.divider()

        # Two column layout
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Win Rate by Score")
            render_score_curve_chart(result)

        with col2:
            st.markdown("### Win Rate by Bucket")
            render_bucket_comparison_chart(result)

        st.divider()

        # Full width sections
        st.markdown("### Model-Direction Breakdown")
        render_model_direction_heatmap(result)

        st.markdown("### Threshold Analysis")
        render_threshold_analysis_chart(result)

        st.markdown("### Detailed Lift Table")
        render_lift_table(result)

        # Key findings
        st.divider()
        st.markdown("### Key Findings")

        findings = render_key_findings(result)
        for finding in findings:
            st.markdown(f"- {finding}")

        return result

    except Exception as e:
        st.error(f"Error in CALC-005 analysis: {e}")
        return None
