"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Options Chart Components (Plotly)
XIII Trading LLC
================================================================================

Chart components specifically for the Options Analysis tab.
Provides visualizations for options MFE/MAE, leverage, and sequence analysis.

================================================================================
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import List, Dict, Any, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import CHART_CONFIG


# =============================================================================
# CONFIGURATION
# =============================================================================
OPTIONS_COLORS = {
    "call": "#26a69a",
    "put": "#ef5350",
    "mfe": "#2E86AB",
    "mae": "#E94F37",
    "options": "#2E86AB",
    "underlying": "#E94F37",
    "win": "#26a69a",
    "loss": "#ef5350"
}


def _get_layout(title: str = "", height: int = None) -> dict:
    """Get standard chart layout for options charts."""
    return dict(
        title=title,
        paper_bgcolor=CHART_CONFIG.get("paper_color", "#16213e"),
        plot_bgcolor=CHART_CONFIG.get("background_color", "#1a1a2e"),
        font=dict(color=CHART_CONFIG.get("text_color", "#e0e0e0")),
        height=height or CHART_CONFIG.get("default_height", 400),
        margin=dict(l=50, r=50, t=50, b=50)
    )


# =============================================================================
# WIN RATE CHARTS
# =============================================================================
def render_options_win_rate_by_model(data: List[Dict[str, Any]]) -> None:
    """
    Render options win rate by model bar chart.

    Parameters:
    -----------
    data : List[Dict[str, Any]]
        Options data from op_mfe_mae_potential table
    """
    if not data:
        st.info("No options data available")
        return

    df = pd.DataFrame(data)

    if 'model' not in df.columns or 'exit_pct' not in df.columns:
        st.warning("Required columns not found")
        return

    # Calculate win rate by model
    df['is_winner'] = df['exit_pct'] > 0
    model_stats = df.groupby('model').agg(
        wins=('is_winner', 'sum'),
        total=('is_winner', 'count')
    ).reset_index()
    model_stats['win_rate'] = (model_stats['wins'] / model_stats['total'] * 100).round(1)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=model_stats['model'],
        y=model_stats['win_rate'],
        marker_color=[OPTIONS_COLORS['call']] * len(model_stats),
        text=[f"{wr:.1f}%" for wr in model_stats['win_rate']],
        textposition="auto"
    ))

    # Add 50% reference line
    fig.add_hline(y=50, line_dash="dash", line_color="#888", annotation_text="50%")

    fig.update_layout(**_get_layout("Options Win Rate by Model"))
    fig.update_yaxes(title="Win Rate (%)", range=[0, 100])
    fig.update_xaxes(title="Model")

    st.plotly_chart(fig, use_container_width=True)


def render_options_win_loss_by_contract(data: List[Dict[str, Any]]) -> None:
    """
    Render grouped bar chart showing wins/losses by contract type.

    Parameters:
    -----------
    data : List[Dict[str, Any]]
        Options data from op_mfe_mae_potential table
    """
    if not data:
        st.info("No options data available")
        return

    df = pd.DataFrame(data)

    if 'contract_type' not in df.columns or 'exit_pct' not in df.columns:
        st.warning("Required columns not found")
        return

    df['is_winner'] = df['exit_pct'] > 0
    df['contract_type'] = df['contract_type'].str.upper()

    contract_stats = df.groupby('contract_type').agg(
        wins=('is_winner', 'sum'),
        total=('is_winner', 'count')
    ).reset_index()
    contract_stats['losses'] = contract_stats['total'] - contract_stats['wins']

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name="Wins",
        x=contract_stats['contract_type'],
        y=contract_stats['wins'],
        marker_color=OPTIONS_COLORS['win'],
        text=contract_stats['wins'],
        textposition="auto"
    ))

    fig.add_trace(go.Bar(
        name="Losses",
        x=contract_stats['contract_type'],
        y=contract_stats['losses'],
        marker_color=OPTIONS_COLORS['loss'],
        text=contract_stats['losses'],
        textposition="auto"
    ))

    fig.update_layout(**_get_layout("Options Wins/Losses by Contract Type"))
    fig.update_layout(barmode="group")
    fig.update_xaxes(title="Contract Type")
    fig.update_yaxes(title="Number of Trades")

    st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# MFE/MAE DISTRIBUTION CHARTS
# =============================================================================
def render_options_mfe_distribution(data: List[Dict[str, Any]], nbins: int = 40) -> None:
    """
    Render options MFE distribution histogram.

    Parameters:
    -----------
    data : List[Dict[str, Any]]
        Options data from op_mfe_mae_potential table
    nbins : int
        Number of histogram bins
    """
    if not data:
        st.info("No options MFE data available")
        return

    df = pd.DataFrame(data)

    if 'mfe_pct' not in df.columns:
        st.warning("MFE column not found")
        return

    df = df.dropna(subset=['mfe_pct'])

    color_col = 'contract_type' if 'contract_type' in df.columns else None

    fig = px.histogram(
        df,
        x='mfe_pct',
        color=color_col,
        nbins=nbins,
        title='Options MFE Distribution',
        labels={'mfe_pct': 'MFE (%)'},
        barmode='overlay',
        opacity=0.7,
        color_discrete_map={'CALL': OPTIONS_COLORS['call'], 'PUT': OPTIONS_COLORS['put']}
    )

    # Add reference lines
    fig.add_vline(x=25, line_dash="dash", line_color="#2ECC71", annotation_text="25%")
    fig.add_vline(x=50, line_dash="dash", line_color="#27AE60", annotation_text="50%")
    fig.add_vline(x=100, line_dash="dash", line_color="#1E8449", annotation_text="100%")

    fig.update_layout(**_get_layout())
    fig.update_xaxes(title="MFE (% of entry)")
    fig.update_yaxes(title="Number of Trades")

    st.plotly_chart(fig, use_container_width=True)


def render_options_mae_distribution(data: List[Dict[str, Any]], nbins: int = 40) -> None:
    """
    Render options MAE distribution histogram.

    Parameters:
    -----------
    data : List[Dict[str, Any]]
        Options data from op_mfe_mae_potential table
    nbins : int
        Number of histogram bins
    """
    if not data:
        st.info("No options MAE data available")
        return

    df = pd.DataFrame(data)

    if 'mae_pct' not in df.columns:
        st.warning("MAE column not found")
        return

    df = df.dropna(subset=['mae_pct'])

    color_col = 'contract_type' if 'contract_type' in df.columns else None

    fig = px.histogram(
        df,
        x='mae_pct',
        color=color_col,
        nbins=nbins,
        title='Options MAE Distribution',
        labels={'mae_pct': 'MAE (%)'},
        barmode='overlay',
        opacity=0.7,
        color_discrete_map={'CALL': OPTIONS_COLORS['call'], 'PUT': OPTIONS_COLORS['put']}
    )

    # Add reference lines
    fig.add_vline(x=10, line_dash="dash", line_color="#F39C12", annotation_text="10%")
    fig.add_vline(x=25, line_dash="dash", line_color="#E67E22", annotation_text="25%")
    fig.add_vline(x=50, line_dash="dash", line_color="#E74C3C", annotation_text="50%")

    fig.update_layout(**_get_layout())
    fig.update_xaxes(title="MAE (% of entry)")
    fig.update_yaxes(title="Number of Trades")

    st.plotly_chart(fig, use_container_width=True)


def render_options_mfe_mae_scatter(data: List[Dict[str, Any]]) -> None:
    """
    Render options MFE vs MAE scatter plot.

    Parameters:
    -----------
    data : List[Dict[str, Any]]
        Options data from op_mfe_mae_potential table
    """
    if not data:
        st.info("No options data available")
        return

    df = pd.DataFrame(data)

    if 'mfe_pct' not in df.columns or 'mae_pct' not in df.columns:
        st.warning("Required columns not found")
        return

    df = df.dropna(subset=['mfe_pct', 'mae_pct'])

    color_col = 'contract_type' if 'contract_type' in df.columns else 'model'

    fig = px.scatter(
        df,
        x='mae_pct',
        y='mfe_pct',
        color=color_col,
        title='Options MFE vs MAE',
        labels={'mae_pct': 'MAE (%)', 'mfe_pct': 'MFE (%)'},
        hover_data=['ticker', 'model'] if 'ticker' in df.columns else None,
        color_discrete_map={'CALL': OPTIONS_COLORS['call'], 'PUT': OPTIONS_COLORS['put']}
    )

    # Add diagonal reference line
    max_val = max(df['mae_pct'].max(), df['mfe_pct'].max())
    fig.add_shape(
        type='line',
        x0=0, y0=0, x1=max_val, y1=max_val,
        line=dict(color='gray', dash='dot', width=1)
    )

    fig.update_layout(**_get_layout(height=500))
    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02))

    st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# LEVERAGE COMPARISON CHARTS
# =============================================================================
def render_leverage_comparison_bars(stats: Dict[str, Any]) -> None:
    """
    Render bar chart comparing options vs underlying movement.

    Parameters:
    -----------
    stats : Dict[str, Any]
        Statistics from calculate_leverage_comparison()
    """
    if not stats or stats.get('trades_with_comparison', 0) == 0:
        st.info("No leverage comparison data available")
        return

    comparison_data = {
        'Metric': ['MFE', 'MFE', 'MAE', 'MAE', 'Exit', 'Exit'],
        'Type': ['Options', 'Underlying', 'Options', 'Underlying', 'Options', 'Underlying'],
        'Value': [
            stats['median_options_mfe'],
            stats['median_underlying_mfe'],
            stats['median_options_mae'],
            stats['median_underlying_mae'],
            abs(stats.get('median_options_exit', 0)),
            abs(stats.get('median_underlying_exit', 0))
        ]
    }

    chart_df = pd.DataFrame(comparison_data)

    fig = px.bar(
        chart_df,
        x='Metric',
        y='Value',
        color='Type',
        barmode='group',
        title='Options vs Underlying Movement Comparison',
        labels={'Value': 'Movement (%)'},
        color_discrete_map={'Options': OPTIONS_COLORS['options'], 'Underlying': OPTIONS_COLORS['underlying']}
    )

    fig.update_layout(**_get_layout())

    st.plotly_chart(fig, use_container_width=True)


def render_leverage_scatter(data: List[Dict[str, Any]], metric: str = 'mfe') -> None:
    """
    Render scatter plot of options vs underlying for specific metric.

    Parameters:
    -----------
    data : List[Dict[str, Any]]
        Options data from op_mfe_mae_potential table
    metric : str
        'mfe', 'mae', or 'exit'
    """
    if not data:
        st.info("No data available")
        return

    df = pd.DataFrame(data)

    if metric == 'mfe':
        x_col, y_col = 'underlying_mfe_pct', 'mfe_pct'
        title = 'Options MFE vs Underlying MFE'
    elif metric == 'mae':
        x_col, y_col = 'underlying_mae_pct', 'mae_pct'
        title = 'Options MAE vs Underlying MAE'
    else:
        x_col, y_col = 'underlying_exit_pct', 'exit_pct'
        title = 'Options Exit vs Underlying Exit'

    if x_col not in df.columns or y_col not in df.columns:
        st.info(f"Missing columns for {metric} comparison")
        return

    df = df.dropna(subset=[x_col, y_col])

    if df.empty:
        st.info(f"No valid data for {metric} comparison")
        return

    color_col = 'contract_type' if 'contract_type' in df.columns else 'model'

    fig = px.scatter(
        df,
        x=x_col,
        y=y_col,
        color=color_col,
        title=title,
        labels={x_col: f'Underlying {metric.upper()} (%)', y_col: f'Options {metric.upper()} (%)'},
        color_discrete_map={'CALL': OPTIONS_COLORS['call'], 'PUT': OPTIONS_COLORS['put']}
    )

    # Add leverage reference lines
    max_underlying = df[x_col].max()
    for leverage in [5, 10, 20]:
        fig.add_trace(
            go.Scatter(
                x=[0, max_underlying],
                y=[0, max_underlying * leverage],
                mode='lines',
                line=dict(color='gray', dash='dot', width=1),
                name=f'{leverage}x',
                showlegend=True
            )
        )

    fig.update_layout(**_get_layout(height=500))

    st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# SEQUENCE / TIMING CHARTS
# =============================================================================
def render_options_sequence_probability_chart(model_df: pd.DataFrame) -> None:
    """
    Render bar chart showing P(MFE First) by model and contract.

    Parameters:
    -----------
    model_df : pd.DataFrame
        Statistics from calculate_options_sequence_by_model()
    """
    if model_df.empty:
        st.info("No sequence data available")
        return

    color_col = 'contract_type' if 'contract_type' in model_df.columns else None

    fig = px.bar(
        model_df,
        x='model',
        y='p_mfe_first',
        color=color_col,
        barmode='group',
        title='P(MFE First) by Model and Contract',
        labels={'model': 'Model', 'p_mfe_first': 'P(MFE First)'},
        color_discrete_map={'CALL': OPTIONS_COLORS['call'], 'PUT': OPTIONS_COLORS['put']}
    )

    # Format as percentage
    fig.update_layout(yaxis_tickformat='.0%')

    # Add 50% reference line
    fig.add_hline(y=0.5, line_dash="dash", line_color="#ffc107", annotation_text="50%")

    fig.update_layout(**_get_layout())

    st.plotly_chart(fig, use_container_width=True)


def render_options_time_to_mfe_histogram(data: List[Dict[str, Any]]) -> None:
    """
    Render histogram of time to MFE for options.

    Parameters:
    -----------
    data : List[Dict[str, Any]]
        Options data from op_mfe_mae_potential table
    """
    if not data:
        st.info("No timing data available")
        return

    df = pd.DataFrame(data)

    if 'entry_time' not in df.columns or 'mfe_time' not in df.columns:
        st.info("Missing time columns")
        return

    # Calculate time to MFE (simplified - assumes time columns are comparable)
    # Full calculation is in op_mfe_mae_sequence.py
    try:
        from calculations.options.op_mfe_mae_sequence import calculate_time_to_mfe
        df['time_to_mfe'] = calculate_time_to_mfe(df)
    except Exception:
        st.info("Could not calculate time to MFE")
        return

    df = df.dropna(subset=['time_to_mfe'])

    if df.empty:
        st.info("No valid time data")
        return

    color_col = 'contract_type' if 'contract_type' in df.columns else None

    fig = px.histogram(
        df,
        x='time_to_mfe',
        color=color_col,
        nbins=24,
        title='Time to MFE Distribution',
        labels={'time_to_mfe': 'Minutes from Entry'},
        barmode='overlay',
        opacity=0.7,
        color_discrete_map={'CALL': OPTIONS_COLORS['call'], 'PUT': OPTIONS_COLORS['put']}
    )

    fig.add_vline(x=30, line_dash="dash", line_color="#ffc107", annotation_text="30 min")
    fig.add_vline(x=60, line_dash="dash", line_color="#ff9800", annotation_text="60 min")

    fig.update_layout(**_get_layout())

    st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# EXIT ANALYSIS CHARTS
# =============================================================================
def render_options_exit_distribution(data: List[Dict[str, Any]], nbins: int = 40) -> None:
    """
    Render options exit percentage distribution histogram.

    Parameters:
    -----------
    data : List[Dict[str, Any]]
        Options data from op_mfe_mae_potential table
    nbins : int
        Number of histogram bins
    """
    if not data:
        st.info("No options exit data available")
        return

    df = pd.DataFrame(data)

    if 'exit_pct' not in df.columns:
        st.warning("Exit column not found")
        return

    df = df.dropna(subset=['exit_pct'])

    color_col = 'contract_type' if 'contract_type' in df.columns else None

    fig = px.histogram(
        df,
        x='exit_pct',
        color=color_col,
        nbins=nbins,
        title='Options Exit Distribution (15:30 ET)',
        labels={'exit_pct': 'Exit (%)'},
        barmode='overlay',
        opacity=0.7,
        color_discrete_map={'CALL': OPTIONS_COLORS['call'], 'PUT': OPTIONS_COLORS['put']}
    )

    # Add zero line
    fig.add_vline(x=0, line_dash="solid", line_color="white", line_width=2)

    fig.update_layout(**_get_layout())
    fig.update_xaxes(title="Exit (% of entry)")
    fig.update_yaxes(title="Number of Trades")

    st.plotly_chart(fig, use_container_width=True)


def render_options_exit_by_model(data: List[Dict[str, Any]]) -> None:
    """
    Render box plot of exit percentage by model.

    Parameters:
    -----------
    data : List[Dict[str, Any]]
        Options data from op_mfe_mae_potential table
    """
    if not data:
        st.info("No options data available")
        return

    df = pd.DataFrame(data)

    if 'exit_pct' not in df.columns or 'model' not in df.columns:
        st.warning("Required columns not found")
        return

    df = df.dropna(subset=['exit_pct'])

    fig = px.box(
        df,
        x='model',
        y='exit_pct',
        color='contract_type' if 'contract_type' in df.columns else None,
        title='Options Exit Distribution by Model',
        labels={'model': 'Model', 'exit_pct': 'Exit (%)'},
        color_discrete_map={'CALL': OPTIONS_COLORS['call'], 'PUT': OPTIONS_COLORS['put']}
    )

    # Add zero line
    fig.add_hline(y=0, line_dash="solid", line_color="white", line_width=2)

    fig.update_layout(**_get_layout(height=450))

    st.plotly_chart(fig, use_container_width=True)
