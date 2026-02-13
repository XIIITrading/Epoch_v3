"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Indicator Analysis Chart Components
XIII Trading LLC
================================================================================

Plotly chart rendering functions for indicator analysis with dark theme.
"""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import CHART_CONFIG

# Theme Configuration (matching existing charts.py)
THEME = {
    "background": CHART_CONFIG["background_color"],
    "paper": CHART_CONFIG["paper_color"],
    "text": CHART_CONFIG["text_color"],
    "grid": CHART_CONFIG["grid_color"],
    "win_color": CHART_CONFIG["win_color"],
    "loss_color": CHART_CONFIG["loss_color"],
    "neutral_color": "#ffa726",
    "primary": "#7c3aed",
    "secondary": "#3b82f6",
    "accent": "#10b981"
}


def _get_layout(title: str = "", height: int = None) -> dict:
    """Get standard chart layout matching existing theme."""
    return dict(
        title=title,
        paper_bgcolor=THEME["paper"],
        plot_bgcolor=THEME["background"],
        font=dict(color=THEME["text"]),
        height=height or CHART_CONFIG["default_height"],
        margin=dict(l=50, r=50, t=50, b=50)
    )


def render_health_correlation_curve(df: pd.DataFrame) -> go.Figure:
    """
    Line chart showing win rate by health score with confidence bands.

    Parameters:
        df: DataFrame with columns [health_score, win_rate, trades, ci_lower, ci_upper]

    Returns:
        Plotly Figure object
    """
    fig = go.Figure()

    # Confidence band
    fig.add_trace(go.Scatter(
        x=list(df['health_score']) + list(df['health_score'][::-1]),
        y=list(df['ci_upper']) + list(df['ci_lower'][::-1]),
        fill='toself',
        fillcolor='rgba(124, 58, 237, 0.2)',
        line=dict(color='rgba(255,255,255,0)'),
        name='95% CI',
        showlegend=True
    ))

    # Main line
    fig.add_trace(go.Scatter(
        x=df['health_score'],
        y=df['win_rate'],
        mode='lines+markers',
        name='Win Rate',
        line=dict(color=THEME['primary'], width=3),
        marker=dict(size=10, color=THEME['primary'])
    ))

    # 50% reference line
    fig.add_hline(
        y=50,
        line_dash="dash",
        line_color=THEME['neutral_color'],
        annotation_text="50% Baseline"
    )

    fig.update_layout(
        **_get_layout("Win Rate by Health Score"),
        xaxis_title="Health Score at Entry",
        yaxis_title="Win Rate (%)",
        xaxis=dict(
            tickmode='linear',
            tick0=0,
            dtick=1,
            range=[-0.5, 10.5]
        ),
        yaxis=dict(range=[0, 100])
    )

    return fig


def render_health_bucket_bars(df: pd.DataFrame) -> go.Figure:
    """
    Grouped bar chart showing win rate by health bucket and model.

    Parameters:
        df: DataFrame with columns [health_bucket, model, win_rate, trades]

    Returns:
        Plotly Figure object
    """
    fig = px.bar(
        df,
        x='health_bucket',
        y='win_rate',
        color='model',
        barmode='group',
        text='trades',
        category_orders={
            'health_bucket': ['CRITICAL (0-3)', 'WEAK (4-5)', 'MODERATE (6-7)', 'STRONG (8-10)']
        }
    )

    fig.update_traces(texttemplate='n=%{text}', textposition='outside')

    fig.update_layout(
        **_get_layout("Win Rate by Health Score Bucket"),
        xaxis_title="Health Score Bucket",
        yaxis_title="Win Rate (%)",
        yaxis=dict(range=[0, 100])
    )

    # Add 50% reference line
    fig.add_hline(y=50, line_dash="dash", line_color=THEME['neutral_color'])

    return fig


def render_factor_importance_bars(df: pd.DataFrame) -> go.Figure:
    """
    Horizontal bar chart showing factor importance ranking.

    Parameters:
        df: DataFrame with columns [factor, lift, healthy_win_rate, unhealthy_win_rate]

    Returns:
        Plotly Figure object
    """
    df_sorted = df.sort_values('lift', ascending=True)

    colors = [THEME['win_color'] if x > 0 else THEME['loss_color'] for x in df_sorted['lift']]

    fig = go.Figure(go.Bar(
        x=df_sorted['lift'],
        y=df_sorted['factor'],
        orientation='h',
        marker_color=colors,
        text=[f"+{x:.1f}pp" if x > 0 else f"{x:.1f}pp" for x in df_sorted['lift']],
        textposition='outside'
    ))

    fig.add_vline(x=0, line_color=THEME['text'], line_width=1)

    fig.update_layout(
        **_get_layout("Indicator Predictiveness (Lift vs Baseline)"),
        xaxis_title="Win Rate Lift (percentage points)",
        yaxis_title="Indicator"
    )

    return fig


def render_time_to_mfe_histogram(df: pd.DataFrame, model_type: str = "all") -> go.Figure:
    """
    Histogram showing time-to-MFE distribution.

    Parameters:
        df: DataFrame with column [time_to_mfe_minutes]
        model_type: Filter label for title

    Returns:
        Plotly Figure object
    """
    fig = px.histogram(
        df,
        x='time_to_mfe_minutes',
        nbins=30,
        color_discrete_sequence=[THEME['primary']]
    )

    # Add vertical lines for buckets
    fig.add_vline(x=5, line_dash="dash", line_color=THEME['win_color'],
                  annotation_text="1 M5 bar")
    fig.add_vline(x=15, line_dash="dash", line_color=THEME['neutral_color'],
                  annotation_text="3 M5 bars")
    fig.add_vline(x=30, line_dash="dash", line_color=THEME['loss_color'],
                  annotation_text="6 M5 bars")

    fig.update_layout(
        **_get_layout(f"Time to MFE Distribution ({model_type})"),
        xaxis_title="Minutes from Entry to MFE",
        yaxis_title="Trade Count"
    )

    return fig


def render_indicator_progression_lines(df: pd.DataFrame) -> go.Figure:
    """
    Line chart showing indicator progression from entry to MFE/MAE.

    Parameters:
        df: DataFrame with columns [event, indicator_value, outcome]

    Returns:
        Plotly Figure object
    """
    fig = go.Figure()

    # Winners path
    winners = df[df['outcome'] == 'WIN']
    fig.add_trace(go.Scatter(
        x=winners['event'],
        y=winners['indicator_value'],
        mode='lines+markers',
        name='Winners',
        line=dict(color=THEME['win_color'], width=3),
        marker=dict(size=10)
    ))

    # Losers path
    losers = df[df['outcome'] == 'LOSS']
    fig.add_trace(go.Scatter(
        x=losers['event'],
        y=losers['indicator_value'],
        mode='lines+markers',
        name='Losers',
        line=dict(color=THEME['loss_color'], width=3),
        marker=dict(size=10)
    ))

    fig.update_layout(
        **_get_layout("Indicator Progression: Winners vs Losers"),
        xaxis_title="Event",
        yaxis_title="Indicator Value"
    )

    return fig
