"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Chart Components (Plotly)
XIII Trading LLC
================================================================================
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import List, Dict, Any
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import CHART_CONFIG


def _get_layout(title: str = "", height: int = None):
    """Get standard chart layout."""
    return dict(
        title=title,
        paper_bgcolor=CHART_CONFIG["paper_color"],
        plot_bgcolor=CHART_CONFIG["background_color"],
        font=dict(color=CHART_CONFIG["text_color"]),
        height=height or CHART_CONFIG["default_height"],
        margin=dict(l=50, r=50, t=50, b=50)
    )


def render_win_rate_chart(model_stats: List[Dict[str, Any]]):
    """Render win rate by model bar chart."""
    if not model_stats:
        st.info("No data available")
        return

    df = pd.DataFrame(model_stats)

    fig = go.Figure()

    # Add bars
    colors = []
    for _, row in df.iterrows():
        if row["trade_type"] == "continuation":
            colors.append(CHART_CONFIG["continuation_color"])
        else:
            colors.append(CHART_CONFIG["rejection_color"])

    fig.add_trace(go.Bar(
        x=df["model"],
        y=df["win_rate"],
        marker_color=colors,
        text=[f"{wr:.1f}%" for wr in df["win_rate"]],
        textposition="auto"
    ))

    # Add 50% line
    fig.add_hline(y=50, line_dash="dash", line_color=CHART_CONFIG["text_muted"])

    fig.update_layout(**_get_layout("Win Rate by Model"))
    fig.update_yaxes(title="Win Rate (%)", range=[0, 100])

    st.plotly_chart(fig, use_container_width=True)


def render_indicator_distribution(
    data: List[Dict[str, Any]],
    indicator: str,
    title: str = ""
):
    """Render indicator distribution histogram by outcome."""
    if not data:
        st.info("No data available")
        return

    df = pd.DataFrame(data)

    if indicator not in df.columns:
        st.warning(f"Indicator '{indicator}' not found")
        return

    # Determine win column
    win_col = "win" if "win" in df.columns else "is_winner"
    if win_col not in df.columns:
        st.warning("No outcome column found")
        return

    # Convert indicator to numeric
    df[indicator] = pd.to_numeric(df[indicator], errors="coerce")

    # Split by outcome
    if win_col == "win":
        winners = df[df[win_col] == 1][indicator].dropna()
        losers = df[df[win_col] == 0][indicator].dropna()
    else:
        winners = df[df[win_col] == True][indicator].dropna()
        losers = df[df[win_col] == False][indicator].dropna()

    fig = go.Figure()

    fig.add_trace(go.Histogram(
        x=winners,
        name="Winners",
        marker_color=CHART_CONFIG["win_color"],
        opacity=0.7
    ))

    fig.add_trace(go.Histogram(
        x=losers,
        name="Losers",
        marker_color=CHART_CONFIG["loss_color"],
        opacity=0.7
    ))

    fig.update_layout(**_get_layout(title or f"{indicator} Distribution"))
    fig.update_layout(barmode="overlay")

    st.plotly_chart(fig, use_container_width=True)


def render_health_heatmap(data: List[Dict[str, Any]]):
    """Render health score heatmap by model and outcome."""
    if not data:
        st.info("No data available")
        return

    df = pd.DataFrame(data)

    if "health_score" not in df.columns or "model" not in df.columns:
        st.warning("Required columns not found")
        return

    win_col = "win" if "win" in df.columns else "is_winner"

    # Create pivot table
    pivot_data = []
    for model in ["EPCH1", "EPCH2", "EPCH3", "EPCH4"]:
        model_df = df[df["model"] == model]
        if len(model_df) == 0:
            continue

        for score in range(0, 11):
            score_df = model_df[model_df["health_score"] == score]
            if len(score_df) == 0:
                continue

            if win_col == "win":
                wins = len(score_df[score_df[win_col] == 1])
            else:
                wins = len(score_df[score_df[win_col] == True])

            total = len(score_df)
            win_rate = wins / total * 100 if total > 0 else 0

            pivot_data.append({
                "model": model,
                "health_score": score,
                "win_rate": win_rate,
                "count": total
            })

    if not pivot_data:
        st.info("No health score data available")
        return

    pivot_df = pd.DataFrame(pivot_data)
    pivot_table = pivot_df.pivot(index="model", columns="health_score", values="win_rate")

    fig = px.imshow(
        pivot_table,
        labels=dict(x="Health Score", y="Model", color="Win Rate %"),
        color_continuous_scale=["#ef5350", "#FFC107", "#26a69a"],
        aspect="auto"
    )

    fig.update_layout(**_get_layout("Win Rate by Health Score and Model"))

    st.plotly_chart(fig, use_container_width=True)


def render_indicator_by_event(
    event_stats: Dict[str, Dict[str, Any]],
    indicator: str
):
    """Render indicator values by event type."""
    if not event_stats:
        st.info("No data available")
        return

    events = ["ENTRY", "MFE", "MAE", "EXIT"]
    means = []
    colors = [CHART_CONFIG["long_color"], CHART_CONFIG["win_color"],
              CHART_CONFIG["loss_color"], CHART_CONFIG["short_color"]]

    for event in events:
        if event in event_stats and event_stats[event].get("mean") is not None:
            means.append(event_stats[event]["mean"])
        else:
            means.append(0)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=events,
        y=means,
        marker_color=colors,
        text=[f"{m:.2f}" for m in means],
        textposition="auto"
    ))

    fig.update_layout(**_get_layout(f"{indicator} by Event Type"))

    st.plotly_chart(fig, use_container_width=True)


def render_comparison_chart(
    continuation_stats: Dict[str, Any],
    rejection_stats: Dict[str, Any]
):
    """Render continuation vs rejection comparison."""
    metrics = ["win_rate", "avg_r", "total"]
    labels = ["Win Rate (%)", "Avg R", "Total Trades"]

    fig = make_subplots(rows=1, cols=3, subplot_titles=labels)

    for i, (metric, label) in enumerate(zip(metrics, labels), 1):
        cont_val = continuation_stats.get(metric, 0)
        rej_val = rejection_stats.get(metric, 0)

        fig.add_trace(
            go.Bar(
                x=["Continuation", "Rejection"],
                y=[cont_val, rej_val],
                marker_color=[CHART_CONFIG["continuation_color"], CHART_CONFIG["rejection_color"]],
                text=[f"{cont_val:.1f}", f"{rej_val:.1f}"],
                textposition="auto",
                showlegend=False
            ),
            row=1, col=i
        )

    fig.update_layout(**_get_layout("Continuation vs Rejection", height=350))

    st.plotly_chart(fig, use_container_width=True)
