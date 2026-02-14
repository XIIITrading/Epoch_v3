"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Summary Card Components
XIII Trading LLC
================================================================================
"""

import streamlit as st
from typing import Dict, Any, List
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import CHART_CONFIG


def render_summary_cards(stats: Dict[str, Any]):
    """
    Render overview summary cards.

    Uses MFE<MAE win condition and points-based calculations.

    Stats dict should contain:
    - total: Total trades
    - wins: Number of wins (MFE before MAE)
    - losses: Number of losses (MAE before MFE)
    - win_rate: Win percentage
    - avg_points: Average points per trade
    - total_points: Total points (win points - loss points)
    - median_mfe_pct: Median MFE percentage
    - median_mae_pct: Median MAE percentage
    """
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            label="Total Trades",
            value=f"{stats.get('total', 0):,}"
        )

    with col2:
        st.metric(
            label="Win Rate",
            value=f"{stats.get('win_rate', 0):.1f}%"
        )

    with col3:
        st.metric(
            label="Wins / Losses",
            value=f"{stats.get('wins', 0):,} / {stats.get('losses', 0):,}"
        )

    with col4:
        avg_points = stats.get("avg_points", 0)
        st.metric(
            label="Avg Points",
            value=f"{avg_points:+.2f}" if avg_points else "0.00"
        )

    with col5:
        total_points = stats.get("total_points", 0)
        st.metric(
            label="Total Points",
            value=f"{total_points:+.2f}" if total_points else "0.00"
        )


def render_model_cards(model_stats: List[Dict[str, Any]]):
    """Render cards for each model."""
    if not model_stats:
        st.info("No model data available")
        return

    # Split into continuation and rejection
    continuation = [m for m in model_stats if m.get("trade_type") == "continuation"]
    rejection = [m for m in model_stats if m.get("trade_type") == "rejection"]

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Continuation (Through Zone)")
        for model in continuation:
            _render_model_card(model)

    with col2:
        st.subheader("Rejection (From Zone)")
        for model in rejection:
            _render_model_card(model)


def _render_model_card(model: Dict[str, Any]):
    """Render a single model card with points-based metrics."""
    model_name = model.get("model", "Unknown")
    win_rate = model.get("win_rate", 0)
    total = model.get("total", 0)
    avg_points = model.get("avg_points", 0)
    zone = model.get("zone_type", "").title()

    # Color based on win rate
    if win_rate >= 55:
        color = CHART_CONFIG["win_color"]
    elif win_rate >= 45:
        color = CHART_CONFIG["moderate_color"]
    else:
        color = CHART_CONFIG["loss_color"]

    st.markdown(f"""
    <div style="padding: 10px; border-left: 4px solid {color}; margin-bottom: 10px; background-color: #2a2a4e;">
        <h4 style="margin: 0; color: #e0e0e0;">{model_name} ({zone})</h4>
        <p style="margin: 5px 0; color: #888;">
            {total} trades | <span style="color: {color}">{win_rate:.1f}% win rate</span> | Avg: {avg_points:+.2f} pts
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_indicator_card(
    name: str,
    win_value: float,
    loss_value: float,
    unit: str = ""
):
    """Render an indicator comparison card."""
    diff = win_value - loss_value

    if diff > 0:
        indicator = "↑"
        color = CHART_CONFIG["win_color"]
    elif diff < 0:
        indicator = "↓"
        color = CHART_CONFIG["loss_color"]
    else:
        indicator = "→"
        color = CHART_CONFIG["text_muted"]

    st.markdown(f"""
    <div style="padding: 15px; border: 1px solid #3a3a5e; border-radius: 5px; margin-bottom: 10px;">
        <h4 style="margin: 0 0 10px 0; color: #e0e0e0;">{name}</h4>
        <div style="display: flex; justify-content: space-between;">
            <div>
                <span style="color: {CHART_CONFIG['win_color']}">Winners:</span> {win_value:.2f}{unit}
            </div>
            <div>
                <span style="color: {CHART_CONFIG['loss_color']}">Losers:</span> {loss_value:.2f}{unit}
            </div>
            <div>
                <span style="color: {color}">{indicator} {abs(diff):.2f}{unit}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
