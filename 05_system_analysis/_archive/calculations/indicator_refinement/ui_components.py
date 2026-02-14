"""
================================================================================
EPOCH TRADING SYSTEM - INDICATOR REFINEMENT UI COMPONENTS
Streamlit components for displaying Continuation/Rejection score analysis
================================================================================
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Any, Optional
from decimal import Decimal

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import CHART_CONFIG

# Score thresholds for labels
CONTINUATION_SCORE_THRESHOLDS = {
    'STRONG': (8, 10),
    'GOOD': (6, 7),
    'WEAK': (4, 5),
    'AVOID': (0, 3)
}

REJECTION_SCORE_THRESHOLDS = {
    'STRONG': (9, 11),
    'GOOD': (6, 8),
    'WEAK': (4, 5),
    'AVOID': (0, 3)
}

# Colors
SCORE_COLORS = {
    'STRONG': '#00C853',
    'GOOD': '#8BC34A',
    'WEAK': '#FF9800',
    'AVOID': '#FF1744'
}


def convert_decimals(data: List[Dict]) -> List[Dict]:
    """Convert Decimal values to float for Plotly compatibility."""
    result = []
    for row in data:
        converted = {}
        for k, v in row.items():
            if isinstance(v, Decimal):
                converted[k] = float(v)
            else:
                converted[k] = v
        result.append(converted)
    return result


def get_score_label(score: float, trade_type: str) -> str:
    """Get the label (STRONG, GOOD, WEAK, AVOID) for a given score."""
    if score is None:
        return 'UNKNOWN'

    thresholds = CONTINUATION_SCORE_THRESHOLDS if trade_type == 'CONTINUATION' else REJECTION_SCORE_THRESHOLDS

    for label, (min_val, max_val) in thresholds.items():
        if min_val <= score <= max_val:
            return label
    return 'UNKNOWN'


def render_indicator_refinement_section(
    refinement_data: List[Dict[str, Any]],
    date_from=None,
    date_to=None
) -> Optional[Dict[str, Any]]:
    """
    Render the complete indicator refinement analysis section.

    Args:
        refinement_data: List of indicator refinement records
        date_from: Start date filter
        date_to: End date filter

    Returns:
        Dict with analysis results for Monte AI prompt
    """
    if not refinement_data:
        st.warning("No indicator refinement data available.")
        st.info("""
        **To populate indicator_refinement table:**
        ```bash
        cd C:\\XIIITradingSystems\\Epoch\\02_zone_system\\09_backtest\\processor\\secondary_analysis\\indicator_refinement
        python runner.py --schema  # Create table first
        python runner.py           # Full calculation
        ```
        """)
        return None

    # Convert decimals
    data = convert_decimals(refinement_data)
    df = pd.DataFrame(data)

    # Ensure is_winner is boolean (handle None values)
    if 'is_winner' in df.columns:
        df['is_winner'] = df['is_winner'].fillna(False).astype(bool)
    else:
        df['is_winner'] = False

    # Summary metrics
    st.subheader("Indicator Refinement Summary")
    st.markdown("*Continuation (0-10) and Rejection (0-11) trade qualification scores*")

    # Split by trade type
    cont_df = df[df['trade_type'] == 'CONTINUATION'].copy()
    rej_df = df[df['trade_type'] == 'REJECTION'].copy()

    # Calculate averages safely
    cont_avg = cont_df['continuation_score'].mean() if len(cont_df) > 0 and cont_df['continuation_score'].notna().any() else 0
    rej_avg = rej_df['rejection_score'].mean() if len(rej_df) > 0 and rej_df['rejection_score'].notna().any() else 0

    # Summary cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Continuation Trades",
            f"{len(cont_df):,}",
            f"Avg Score: {cont_avg:.1f}/10" if len(cont_df) > 0 else None
        )

    with col2:
        cont_winners = cont_df['is_winner'].sum() if len(cont_df) > 0 else 0
        cont_wr = (cont_winners / len(cont_df) * 100) if len(cont_df) > 0 else 0
        st.metric(
            "Continuation Win Rate",
            f"{cont_wr:.1f}%",
            None
        )

    with col3:
        st.metric(
            "Rejection Trades",
            f"{len(rej_df):,}",
            f"Avg Score: {rej_avg:.1f}/11" if len(rej_df) > 0 else None
        )

    with col4:
        rej_winners = rej_df['is_winner'].sum() if len(rej_df) > 0 else 0
        rej_wr = (rej_winners / len(rej_df) * 100) if len(rej_df) > 0 else 0
        st.metric(
            "Rejection Win Rate",
            f"{rej_wr:.1f}%",
            None
        )

    st.markdown("---")

    # Two-column layout for continuation vs rejection
    col_cont, col_rej = st.columns(2)

    with col_cont:
        st.markdown("### Continuation Analysis")
        if len(cont_df) > 0:
            render_score_distribution(cont_df, 'continuation_score', 'Continuation Score', 10)
            st.markdown("---")
            render_win_rate_by_score(cont_df, 'continuation_score', 'CONTINUATION')
            st.markdown("---")
            render_indicator_breakdown_table(cont_df, 'CONTINUATION')
        else:
            st.info("No continuation trades in selected period")

    with col_rej:
        st.markdown("### Rejection Analysis")
        if len(rej_df) > 0:
            render_score_distribution(rej_df, 'rejection_score', 'Rejection Score', 11)
            st.markdown("---")
            render_win_rate_by_score(rej_df, 'rejection_score', 'REJECTION')
            st.markdown("---")
            render_indicator_breakdown_table(rej_df, 'REJECTION')
        else:
            st.info("No rejection trades in selected period")

    # Return results for Monte AI
    return {
        'continuation': {
            'count': len(cont_df),
            'avg_score': cont_df['continuation_score'].mean() if len(cont_df) > 0 else 0,
            'win_rate': cont_wr
        },
        'rejection': {
            'count': len(rej_df),
            'avg_score': rej_df['rejection_score'].mean() if len(rej_df) > 0 else 0,
            'win_rate': rej_wr
        }
    }


def render_score_distribution(
    df: pd.DataFrame,
    score_column: str,
    title: str,
    max_score: int
):
    """Render histogram of score distribution."""
    fig = px.histogram(
        df,
        x=score_column,
        nbins=max_score + 1,
        color='is_winner',
        color_discrete_map={True: CHART_CONFIG['win_color'], False: CHART_CONFIG['loss_color']},
        barmode='stack',
        title=f"{title} Distribution"
    )

    fig.update_layout(
        plot_bgcolor=CHART_CONFIG['background_color'],
        paper_bgcolor=CHART_CONFIG['paper_color'],
        font_color=CHART_CONFIG['text_color'],
        height=300,
        showlegend=True,
        legend=dict(
            title="Outcome",
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis_title=score_column.replace('_', ' ').title(),
        yaxis_title="Count"
    )

    fig.update_traces(
        name="Winner",
        selector=dict(name="True")
    )
    fig.update_traces(
        name="Loser",
        selector=dict(name="False")
    )

    st.plotly_chart(fig, use_container_width=True)


def render_win_rate_by_score(
    df: pd.DataFrame,
    score_column: str,
    trade_type: str
):
    """Render win rate chart by score bucket."""
    thresholds = CONTINUATION_SCORE_THRESHOLDS if trade_type == 'CONTINUATION' else REJECTION_SCORE_THRESHOLDS

    # Calculate win rate for each bucket
    buckets = []
    for label, (min_val, max_val) in thresholds.items():
        bucket_df = df[(df[score_column] >= min_val) & (df[score_column] <= max_val)]
        if len(bucket_df) > 0:
            win_rate = bucket_df['is_winner'].sum() / len(bucket_df) * 100
            buckets.append({
                'label': label,
                'score_range': f"{min_val}-{max_val}",
                'trades': len(bucket_df),
                'win_rate': win_rate,
                'color': SCORE_COLORS[label]
            })

    if not buckets:
        st.caption("Insufficient data for win rate analysis")
        return

    bucket_df = pd.DataFrame(buckets)

    # Create bar chart
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=bucket_df['label'],
        y=bucket_df['win_rate'],
        marker_color=bucket_df['color'],
        text=[f"{wr:.1f}%<br>n={n}" for wr, n in zip(bucket_df['win_rate'], bucket_df['trades'])],
        textposition='outside',
        hovertemplate="<b>%{x}</b><br>Win Rate: %{y:.1f}%<br>Trades: %{customdata}<extra></extra>",
        customdata=bucket_df['trades']
    ))

    fig.update_layout(
        title="Win Rate by Score Label",
        plot_bgcolor=CHART_CONFIG['background_color'],
        paper_bgcolor=CHART_CONFIG['paper_color'],
        font_color=CHART_CONFIG['text_color'],
        height=300,
        yaxis_title="Win Rate %",
        yaxis=dict(range=[0, 100]),
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)

    # Show numeric breakdown
    st.caption("Score Labels: STRONG = Highest, AVOID = Skip trade")


def render_indicator_breakdown_table(
    df: pd.DataFrame,
    trade_type: str
):
    """Render table showing individual indicator contributions."""
    st.markdown("**Indicator Breakdown (Average Points)**")

    if trade_type == 'CONTINUATION':
        indicators = [
            ('mtf_alignment_points', 'MTF Alignment', 4),
            ('sma_momentum_points', 'SMA Momentum', 2),
            ('volume_thrust_points', 'Volume Thrust', 2),
            ('pullback_quality_points', 'Pullback Quality', 2)
        ]
    else:  # REJECTION
        indicators = [
            ('structure_divergence_points', 'Structure Divergence', 3),
            ('sma_exhaustion_points', 'SMA Exhaustion', 2),
            ('delta_absorption_points', 'Delta Absorption', 2),
            ('volume_climax_points', 'Volume Climax', 2),
            ('cvd_extreme_points', 'CVD Extreme', 2)
        ]

    # Calculate averages for winners vs losers
    winners = df[df['is_winner'] == True]
    losers = df[df['is_winner'] == False]

    rows = []
    for col, name, max_pts in indicators:
        if col in df.columns and df[col].notna().any():
            # Convert to numeric, handling None values
            win_vals = pd.to_numeric(winners[col], errors='coerce')
            loss_vals = pd.to_numeric(losers[col], errors='coerce')
            all_vals = pd.to_numeric(df[col], errors='coerce')

            win_avg = win_vals.mean() if len(win_vals.dropna()) > 0 else 0
            loss_avg = loss_vals.mean() if len(loss_vals.dropna()) > 0 else 0
            all_avg = all_vals.mean() if len(all_vals.dropna()) > 0 else 0

            # Handle NaN values
            win_avg = win_avg if pd.notna(win_avg) else 0
            loss_avg = loss_avg if pd.notna(loss_avg) else 0
            all_avg = all_avg if pd.notna(all_avg) else 0

            rows.append({
                'Indicator': name,
                'Max': max_pts,
                'Winners': f"{win_avg:.2f}",
                'Losers': f"{loss_avg:.2f}",
                'All': f"{all_avg:.2f}",
                'Delta': f"{win_avg - loss_avg:+.2f}"
            })

    if rows:
        table_df = pd.DataFrame(rows)
        st.dataframe(
            table_df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.caption("Indicator breakdown not available")


def render_score_vs_outcome_scatter(
    df: pd.DataFrame,
    trade_type: str
):
    """Render scatter plot of score vs MFE."""
    score_col = 'continuation_score' if trade_type == 'CONTINUATION' else 'rejection_score'
    max_score = 10 if trade_type == 'CONTINUATION' else 11

    if score_col not in df.columns or 'mfe_r_potential' not in df.columns:
        st.caption("Insufficient data for scatter plot")
        return

    fig = px.scatter(
        df,
        x=score_col,
        y='mfe_r_potential',
        color='is_winner',
        color_discrete_map={True: CHART_CONFIG['win_color'], False: CHART_CONFIG['loss_color']},
        title=f"{trade_type.title()} Score vs MFE",
        hover_data=['ticker', 'date', 'model']
    )

    fig.update_layout(
        plot_bgcolor=CHART_CONFIG['background_color'],
        paper_bgcolor=CHART_CONFIG['paper_color'],
        font_color=CHART_CONFIG['text_color'],
        height=400,
        xaxis_title=score_col.replace('_', ' ').title(),
        yaxis_title="MFE (R)",
        xaxis=dict(range=[-0.5, max_score + 0.5])
    )

    st.plotly_chart(fig, use_container_width=True)
