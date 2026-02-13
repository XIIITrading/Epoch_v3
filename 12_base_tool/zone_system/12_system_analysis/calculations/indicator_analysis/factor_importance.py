"""
================================================================================
EPOCH TRADING SYSTEM - INDICATOR ANALYSIS
CALC-006: Individual Indicator Predictiveness
XIII Trading LLC
================================================================================

Analyzes each Health Score factor independently to determine which factors
have genuine predictive power.

Core Question: "Of the 10 Health Score factors, which ones have independent
predictive power?"

Purpose:
    1. Factor Ranking - Which factors matter most?
    2. Dead Factor Identification - Which factors add no value?
    3. Weight Recommendations - How should DOW AI weight each factor?
    4. Interaction Analysis - Do factors work better in combination?

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
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import streamlit as st

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import INDICATOR_ANALYSIS_CONFIG


# =============================================================================
# FACTOR DEFINITIONS
# =============================================================================

FACTORS = {
    'h4_structure_healthy': {
        'name': 'H4 Structure',
        'group': 'structure',
        'description': 'H4 timeframe trend alignment'
    },
    'h1_structure_healthy': {
        'name': 'H1 Structure',
        'group': 'structure',
        'description': 'H1 timeframe trend alignment'
    },
    'm15_structure_healthy': {
        'name': 'M15 Structure',
        'group': 'structure',
        'description': 'M15 timeframe trend alignment'
    },
    'm5_structure_healthy': {
        'name': 'M5 Structure',
        'group': 'structure',
        'description': 'M5 timeframe trend alignment'
    },
    'vol_roc_healthy': {
        'name': 'Volume ROC',
        'group': 'volume',
        'description': 'Volume above 20% of baseline'
    },
    'vol_delta_healthy': {
        'name': 'Volume Delta',
        'group': 'volume',
        'description': 'Delta aligned with trade direction'
    },
    'cvd_slope_healthy': {
        'name': 'CVD Slope',
        'group': 'volume',
        'description': 'Cumulative volume delta trend'
    },
    'sma_alignment_healthy': {
        'name': 'SMA Alignment',
        'group': 'price',
        'description': 'SMA9 vs SMA21 position'
    },
    'sma_momentum_healthy': {
        'name': 'SMA Momentum',
        'group': 'price',
        'description': 'SMA spread widening'
    },
    'vwap_healthy': {
        'name': 'VWAP Position',
        'group': 'price',
        'description': 'Price vs VWAP alignment'
    }
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class FactorAnalysis:
    """Analysis results for a single factor."""
    factor_key: str
    factor_name: str
    factor_group: str

    # Sample sizes
    total_trades: int
    healthy_trades: int
    unhealthy_trades: int
    prevalence: float  # % of trades where factor is healthy

    # Win rates
    overall_win_rate: float
    healthy_win_rate: float
    unhealthy_win_rate: float
    lift: float  # healthy - unhealthy

    # Statistical measures
    correlation: float
    correlation_pvalue: float
    information_gain: float

    # Confidence intervals
    healthy_ci_lower: float
    healthy_ci_upper: float
    unhealthy_ci_lower: float
    unhealthy_ci_upper: float

    # Significance flag
    statistically_significant: bool


@dataclass
class FactorImportanceResult:
    """Container for all factor importance analysis results."""
    total_trades: int
    overall_win_rate: float

    # Individual factor analyses
    factor_analyses: List[FactorAnalysis]

    # Ranked factors
    ranked_by_lift: pd.DataFrame
    ranked_by_correlation: pd.DataFrame

    # Factor group summaries
    group_summary: pd.DataFrame

    # Factor correlation matrix
    factor_correlation_matrix: pd.DataFrame

    # Top recommendations
    top_factors: List[str]
    dead_factors: List[str]


# =============================================================================
# STATISTICAL FUNCTIONS
# =============================================================================

def wilson_ci(wins: int, total: int, confidence: float = 0.95) -> Tuple[float, float]:
    """
    Calculate Wilson score confidence interval.

    More accurate than normal approximation for small samples or extreme proportions.

    Args:
        wins: Number of successful trades
        total: Total number of trades
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


def calculate_information_gain(
    healthy_wins: int,
    healthy_total: int,
    unhealthy_wins: int,
    unhealthy_total: int,
    total_wins: int,
    total_trades: int
) -> float:
    """
    Calculate information gain (entropy reduction) for a factor.

    Higher values indicate the factor provides more information about outcome.

    Args:
        healthy_wins: Wins when factor is healthy
        healthy_total: Total trades when factor is healthy
        unhealthy_wins: Wins when factor is unhealthy
        unhealthy_total: Total trades when factor is unhealthy
        total_wins: Total wins across all trades
        total_trades: Total number of trades

    Returns:
        Information gain value (0 to 1, higher is better)
    """
    if total_trades == 0:
        return 0.0

    def entropy(wins, total):
        if total == 0 or wins == 0 or wins == total:
            return 0.0
        p = wins / total
        return -p * np.log2(p) - (1 - p) * np.log2(1 - p)

    # Overall entropy
    h_overall = entropy(total_wins, total_trades)

    # Weighted entropy after split
    h_healthy = entropy(healthy_wins, healthy_total) if healthy_total > 0 else 0
    h_unhealthy = entropy(unhealthy_wins, unhealthy_total) if unhealthy_total > 0 else 0

    w_healthy = healthy_total / total_trades
    w_unhealthy = unhealthy_total / total_trades

    h_after = w_healthy * h_healthy + w_unhealthy * h_unhealthy

    return h_overall - h_after


# =============================================================================
# FACTOR ANALYSIS FUNCTIONS
# =============================================================================

def analyze_single_factor(
    df: pd.DataFrame,
    factor_key: str,
    overall_win_rate: float
) -> Optional[FactorAnalysis]:
    """
    Analyze a single factor's predictiveness.

    Args:
        df: DataFrame with factor column and is_winner
        factor_key: Column name for the factor (e.g., 'vwap_healthy')
        overall_win_rate: Baseline win rate

    Returns:
        FactorAnalysis or None if insufficient data
    """
    factor_info = FACTORS.get(factor_key)
    if not factor_info:
        return None

    # Filter to rows where factor is not null AND is_winner is not null
    # is_winner may be None for trades without stop analysis data
    df_valid = df[df[factor_key].notna() & df['is_winner'].notna()].copy()

    if len(df_valid) == 0:
        return None

    total_trades = len(df_valid)
    total_wins = int(df_valid['is_winner'].sum())

    # Split by factor state
    healthy = df_valid[df_valid[factor_key] == True]
    unhealthy = df_valid[df_valid[factor_key] == False]

    healthy_trades = len(healthy)
    unhealthy_trades = len(unhealthy)

    # Need minimum samples in both groups
    min_trades = INDICATOR_ANALYSIS_CONFIG['min_trades_for_analysis']
    if healthy_trades < min_trades or unhealthy_trades < min_trades:
        statistically_significant = False
    else:
        statistically_significant = True

    # Calculate win rates
    healthy_wins = int(healthy['is_winner'].sum()) if healthy_trades > 0 else 0
    unhealthy_wins = int(unhealthy['is_winner'].sum()) if unhealthy_trades > 0 else 0

    healthy_win_rate = (healthy_wins / healthy_trades * 100) if healthy_trades > 0 else 0
    unhealthy_win_rate = (unhealthy_wins / unhealthy_trades * 100) if unhealthy_trades > 0 else 0
    lift = healthy_win_rate - unhealthy_win_rate

    # Confidence intervals
    healthy_ci = wilson_ci(healthy_wins, healthy_trades)
    unhealthy_ci = wilson_ci(unhealthy_wins, unhealthy_trades)

    # Correlation
    try:
        factor_numeric = df_valid[factor_key].astype(int)
        winner_numeric = df_valid['is_winner'].astype(int)
        corr, pvalue = stats.pearsonr(factor_numeric, winner_numeric)
    except Exception:
        corr, pvalue = 0.0, 1.0

    # Information gain
    ig = calculate_information_gain(
        healthy_wins, healthy_trades,
        unhealthy_wins, unhealthy_trades,
        total_wins, total_trades
    )

    # Prevalence
    prevalence = (healthy_trades / total_trades * 100) if total_trades > 0 else 0

    return FactorAnalysis(
        factor_key=factor_key,
        factor_name=factor_info['name'],
        factor_group=factor_info['group'],
        total_trades=total_trades,
        healthy_trades=healthy_trades,
        unhealthy_trades=unhealthy_trades,
        prevalence=prevalence,
        overall_win_rate=overall_win_rate,
        healthy_win_rate=healthy_win_rate,
        unhealthy_win_rate=unhealthy_win_rate,
        lift=lift,
        correlation=corr,
        correlation_pvalue=pvalue,
        information_gain=ig,
        healthy_ci_lower=healthy_ci[0],
        healthy_ci_upper=healthy_ci[1],
        unhealthy_ci_lower=unhealthy_ci[0],
        unhealthy_ci_upper=unhealthy_ci[1],
        statistically_significant=statistically_significant
    )


def calculate_factor_correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate correlation matrix between all factors.

    Identifies multicollinearity and redundant factors.

    Args:
        df: DataFrame with factor columns

    Returns:
        Correlation matrix DataFrame with friendly names
    """
    factor_cols = [k for k in FACTORS.keys() if k in df.columns]

    # Convert to numeric
    factor_df = df[factor_cols].copy()
    for col in factor_cols:
        factor_df[col] = factor_df[col].astype(float)

    # Calculate correlation matrix
    corr_matrix = factor_df.corr()

    # Rename columns/index to friendly names
    name_map = {k: v['name'] for k, v in FACTORS.items()}
    corr_matrix = corr_matrix.rename(columns=name_map, index=name_map)

    return corr_matrix


def calculate_group_summary(factor_analyses: List[FactorAnalysis]) -> pd.DataFrame:
    """
    Summarize factor performance by group (structure, volume, price).

    Args:
        factor_analyses: List of FactorAnalysis objects

    Returns:
        DataFrame with group-level summary statistics
    """
    groups = {}

    for fa in factor_analyses:
        group = fa.factor_group
        if group not in groups:
            groups[group] = {
                'factors': [],
                'avg_lift': [],
                'avg_ig': []
            }
        groups[group]['factors'].append(fa.factor_name)
        groups[group]['avg_lift'].append(fa.lift)
        groups[group]['avg_ig'].append(fa.information_gain)

    results = []
    for group, data in groups.items():
        results.append({
            'group': group.upper(),
            'factor_count': len(data['factors']),
            'avg_lift': np.mean(data['avg_lift']),
            'max_lift': max(data['avg_lift']),
            'avg_information_gain': np.mean(data['avg_ig']),
            'best_factor': data['factors'][np.argmax(data['avg_lift'])]
        })

    return pd.DataFrame(results)


# =============================================================================
# MAIN ANALYSIS FUNCTION
# =============================================================================

def analyze_factor_importance(df: pd.DataFrame) -> FactorImportanceResult:
    """
    Main analysis function for CALC-006.

    Analyzes all 10 Health Score factors to determine which have
    independent predictive power.

    Args:
        df: DataFrame with all factor columns and is_winner

    Returns:
        FactorImportanceResult with all analysis outputs
    """
    # Filter to rows with valid is_winner (from stop analysis)
    df_with_outcome = df[df['is_winner'].notna()].copy()

    if len(df_with_outcome) == 0:
        raise ValueError("No valid data for factor importance analysis. Ensure stop_analysis table is populated.")

    # Overall stats
    total_trades = len(df_with_outcome)
    overall_wins = int(df_with_outcome['is_winner'].sum())
    overall_win_rate = (overall_wins / total_trades * 100) if total_trades > 0 else 0

    # Analyze each factor
    factor_analyses = []
    for factor_key in FACTORS.keys():
        if factor_key in df.columns:
            analysis = analyze_single_factor(df, factor_key, overall_win_rate)
            if analysis:
                factor_analyses.append(analysis)

    if not factor_analyses:
        raise ValueError("No valid factors to analyze")

    # Create ranking DataFrames
    ranking_data = [{
        'factor': fa.factor_name,
        'group': fa.factor_group,
        'healthy_win_rate': fa.healthy_win_rate,
        'unhealthy_win_rate': fa.unhealthy_win_rate,
        'lift': fa.lift,
        'correlation': fa.correlation,
        'correlation_pvalue': fa.correlation_pvalue,
        'information_gain': fa.information_gain,
        'prevalence': fa.prevalence,
        'healthy_trades': fa.healthy_trades,
        'unhealthy_trades': fa.unhealthy_trades,
        'significant': fa.statistically_significant
    } for fa in factor_analyses]

    ranking_df = pd.DataFrame(ranking_data)

    # Rank by lift
    ranked_by_lift = ranking_df.sort_values('lift', ascending=False).reset_index(drop=True)
    ranked_by_lift['rank'] = ranked_by_lift.index + 1

    # Rank by correlation
    ranked_by_correlation = ranking_df.sort_values('correlation', ascending=False).reset_index(drop=True)

    # Group summary
    group_summary = calculate_group_summary(factor_analyses)

    # Factor correlation matrix
    factor_corr_matrix = calculate_factor_correlation_matrix(df)

    # Identify top and dead factors
    significant_factors = ranked_by_lift[ranked_by_lift['significant']]
    top_factors = significant_factors[significant_factors['lift'] > 5]['factor'].tolist()[:3]
    dead_factors = significant_factors[significant_factors['lift'].abs() < 2]['factor'].tolist()

    return FactorImportanceResult(
        total_trades=total_trades,
        overall_win_rate=overall_win_rate,
        factor_analyses=factor_analyses,
        ranked_by_lift=ranked_by_lift,
        ranked_by_correlation=ranked_by_correlation,
        group_summary=group_summary,
        factor_correlation_matrix=factor_corr_matrix,
        top_factors=top_factors,
        dead_factors=dead_factors
    )


# =============================================================================
# STREAMLIT RENDERING FUNCTIONS
# =============================================================================

def render_factor_summary_cards(result: FactorImportanceResult):
    """Render summary cards for factor analysis."""
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
        st.metric(
            label="Factors Analyzed",
            value=len(result.factor_analyses)
        )

    with col4:
        if result.top_factors:
            st.metric(
                label="Top Factor",
                value=result.top_factors[0] if result.top_factors else "N/A"
            )
        else:
            st.metric(
                label="Top Factor",
                value="N/A"
            )


def render_factor_importance_chart(result: FactorImportanceResult):
    """Render horizontal bar chart of factor importance (lift)."""
    import plotly.graph_objects as go

    df = result.ranked_by_lift.copy()

    # Color by group
    group_colors = {
        'structure': '#7c3aed',  # Purple
        'volume': '#3b82f6',     # Blue
        'price': '#10b981'       # Green
    }
    colors = [group_colors.get(g, '#888') for g in df['group']]

    # Add significance markers
    markers = ['' if s else '' for s in df['significant']]
    labels = [f"{f} {m}" for f, m in zip(df['factor'], markers)]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=labels[::-1],  # Reverse for top-to-bottom ranking
        x=df['lift'][::-1],
        orientation='h',
        marker_color=colors[::-1],
        text=[f"{l:+.1f}pp" for l in df['lift'][::-1]],
        textposition='outside'
    ))

    # Zero line
    fig.add_vline(x=0, line_color='#e0e0e0', line_width=1)

    fig.update_layout(
        title="Factor Importance Ranking (Lift)",
        xaxis_title="Win Rate Lift (percentage points)",
        yaxis_title="",
        template="plotly_dark",
        paper_bgcolor="#16213e",
        plot_bgcolor="#1a1a2e",
        font=dict(color="#e0e0e0"),
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)


def render_factor_comparison_chart(result: FactorImportanceResult):
    """Render grouped bar chart comparing healthy vs unhealthy win rates."""
    import plotly.graph_objects as go

    df = result.ranked_by_lift.head(10)  # Top 10 factors

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name='Healthy',
        x=df['factor'],
        y=df['healthy_win_rate'],
        marker_color='#26a69a',
        text=[f"{v:.1f}%" for v in df['healthy_win_rate']],
        textposition='outside'
    ))

    fig.add_trace(go.Bar(
        name='Unhealthy',
        x=df['factor'],
        y=df['unhealthy_win_rate'],
        marker_color='#ef5350',
        text=[f"{v:.1f}%" for v in df['unhealthy_win_rate']],
        textposition='outside'
    ))

    # Baseline reference
    fig.add_hline(
        y=result.overall_win_rate,
        line_dash="dash",
        line_color="#ffa726",
        annotation_text=f"Baseline: {result.overall_win_rate:.1f}%"
    )

    fig.update_layout(
        title="Win Rate: Healthy vs Unhealthy State",
        xaxis_title="Factor",
        yaxis_title="Win Rate (%)",
        barmode='group',
        template="plotly_dark",
        paper_bgcolor="#16213e",
        plot_bgcolor="#1a1a2e",
        font=dict(color="#e0e0e0"),
        yaxis=dict(range=[0, 100]),
        xaxis_tickangle=-45
    )

    st.plotly_chart(fig, use_container_width=True)


def render_factor_correlation_heatmap(result: FactorImportanceResult):
    """Render correlation matrix heatmap between factors."""
    import plotly.express as px

    fig = px.imshow(
        result.factor_correlation_matrix,
        labels=dict(color="Correlation"),
        color_continuous_scale='RdBu_r',
        color_continuous_midpoint=0,
        aspect='auto',
        text_auto='.2f'
    )

    fig.update_layout(
        title="Factor Correlation Matrix",
        template="plotly_dark",
        paper_bgcolor="#16213e",
        plot_bgcolor="#1a1a2e",
        font=dict(color="#e0e0e0"),
        height=500
    )

    st.plotly_chart(fig, use_container_width=True)


def render_group_summary_chart(result: FactorImportanceResult):
    """Render factor group summary chart."""
    import plotly.graph_objects as go

    df = result.group_summary

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df['group'],
        y=df['avg_lift'],
        name='Avg Lift',
        marker_color='#7c3aed',
        text=[f"{v:.1f}pp" for v in df['avg_lift']],
        textposition='outside'
    ))

    fig.update_layout(
        title="Average Lift by Factor Group",
        xaxis_title="Factor Group",
        yaxis_title="Average Lift (pp)",
        template="plotly_dark",
        paper_bgcolor="#16213e",
        plot_bgcolor="#1a1a2e",
        font=dict(color="#e0e0e0")
    )

    st.plotly_chart(fig, use_container_width=True)


def render_detailed_factor_table(result: FactorImportanceResult):
    """Render detailed factor analysis table."""
    df = result.ranked_by_lift[[
        'rank', 'factor', 'group', 'healthy_win_rate', 'unhealthy_win_rate',
        'lift', 'prevalence', 'healthy_trades', 'unhealthy_trades', 'significant'
    ]].copy()

    df.columns = [
        'Rank', 'Factor', 'Group', 'Healthy Win%', 'Unhealthy Win%',
        'Lift (pp)', 'Prevalence %', 'Healthy n', 'Unhealthy n', 'Significant'
    ]

    # Format columns
    df['Healthy Win%'] = df['Healthy Win%'].apply(lambda x: f"{x:.1f}%")
    df['Unhealthy Win%'] = df['Unhealthy Win%'].apply(lambda x: f"{x:.1f}%")
    df['Lift (pp)'] = df['Lift (pp)'].apply(lambda x: f"+{x:.1f}" if x > 0 else f"{x:.1f}")
    df['Prevalence %'] = df['Prevalence %'].apply(lambda x: f"{x:.1f}%")
    df['Significant'] = df['Significant'].apply(lambda x: '' if x else '')

    st.dataframe(df, use_container_width=True, hide_index=True)


def generate_key_findings(result: FactorImportanceResult) -> List[str]:
    """Generate key findings from factor importance analysis."""
    findings = []

    # Top factors
    if result.top_factors:
        findings.append(f"**Top Predictive Factors:** {', '.join(result.top_factors)}")

    # Dead factors
    if result.dead_factors:
        findings.append(f"**Low-Value Factors:** {', '.join(result.dead_factors)} (consider removing)")

    # Group insights
    if len(result.group_summary) > 0:
        best_group = result.group_summary.loc[result.group_summary['avg_lift'].idxmax()]
        findings.append(f"**Best Factor Group:** {best_group['group']} (avg lift: +{best_group['avg_lift']:.1f}pp)")

    return findings


def render_calc_006_section(df: pd.DataFrame) -> Optional[FactorImportanceResult]:
    """
    Main render function for CALC-006 section in Streamlit.

    Args:
        df: DataFrame from fetch_entry_indicators with mfe_mae_potential join

    Returns:
        FactorImportanceResult or None on error
    """
    st.subheader("CALC-006: Individual Indicator Predictiveness")
    st.markdown("*Which of the 10 Health Score factors actually matter?*")

    try:
        result = analyze_factor_importance(df)

        # Summary cards
        render_factor_summary_cards(result)

        st.divider()

        # Factor importance ranking
        st.markdown("### Factor Importance Ranking")
        render_factor_importance_chart(result)

        # Two column layout
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Healthy vs Unhealthy Comparison")
            render_factor_comparison_chart(result)

        with col2:
            st.markdown("### Group Performance")
            render_group_summary_chart(result)

        st.divider()

        # Factor correlation matrix
        with st.expander("Factor Correlation Matrix", expanded=False):
            st.markdown("*Identifies multicollinearity between factors*")
            render_factor_correlation_heatmap(result)

        # Detailed table
        st.markdown("### Detailed Factor Analysis")
        render_detailed_factor_table(result)

        # Key findings
        st.divider()
        st.markdown("### Key Findings")

        findings = generate_key_findings(result)
        for finding in findings:
            st.markdown(f"- {finding}")

        # DOW AI recommendations
        st.markdown("### DOW AI Recommendations")

        recommendations = []

        # Weight recommendations based on lift
        ranked = result.ranked_by_lift[result.ranked_by_lift['significant']]
        if len(ranked) >= 3:
            top_3 = ranked.head(3)['factor'].tolist()
            recommendations.append(f"**Weight 2x:** {', '.join(top_3)}")

        if result.dead_factors:
            recommendations.append(f"**Consider Removing:** {', '.join(result.dead_factors)}")

        for rec in recommendations:
            st.markdown(f"- {rec}")

        return result

    except Exception as e:
        st.error(f"Error in CALC-006 analysis: {e}")
        import traceback
        st.code(traceback.format_exc())
        return None
