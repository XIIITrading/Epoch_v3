"""
Options Stop Analysis UI Components

Streamlit rendering functions for CALC-O09.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List, Any, Optional

from .stop_types import OPTIONS_STOP_TYPES, DEFAULT_OPTIONS_STOP_TYPE
from .outcome_simulator import simulate_all_outcomes
from .results_aggregator import (
    aggregate_by_stop_type,
    aggregate_by_model_contract,
    find_best_stop_type
)


CHART_COLORS = {
    "win": "#26a69a",
    "loss": "#ef5350",
    "background": "#1a1a2e",
    "paper": "#16213e",
    "text": "#e0e0e0",
    "grid": "#2a2a4e"
}


def render_op_stop_summary_cards(
    summary_df: pd.DataFrame,
    best_stop: Dict[str, Any],
    total_trades: int
) -> None:
    """Render summary metric cards."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Best Stop Type",
            value=best_stop.get('stop_type', 'N/A')
        )

    with col2:
        if not summary_df.empty:
            best_wr = summary_df['Win Rate %'].max()
            st.metric(label="Best Win Rate", value=f"{best_wr:.1f}%")
        else:
            st.metric(label="Best Win Rate", value="N/A")

    with col3:
        exp_value = best_stop.get('expectancy', 0)
        st.metric(
            label="Best Expectancy",
            value=f"{exp_value:+.2f}R" if exp_value != 0 else "N/A"
        )

    with col4:
        st.metric(label="Options Analyzed", value=f"{total_trades:,}")


def render_op_stop_comparison_table(summary_df: pd.DataFrame) -> None:
    """Render the stop type comparison table."""
    if summary_df.empty:
        st.info("No options stop analysis data available")
        return

    display_df = summary_df.copy()

    if 'stop_type_key' in display_df.columns:
        display_df = display_df.drop(columns=['stop_type_key'])

    # Format columns
    display_df['Stop %'] = display_df['Stop %'].apply(lambda x: f"{x:.0f}%")
    display_df['Win Rate %'] = display_df['Win Rate %'].apply(lambda x: f"{x:.1f}%")
    display_df['Stop Hit %'] = display_df['Stop Hit %'].apply(lambda x: f"{x:.1f}%")
    display_df['Avg R (Win)'] = display_df['Avg R (Win)'].apply(lambda x: f"{x:+.2f}R")
    display_df['Avg R (All)'] = display_df['Avg R (All)'].apply(lambda x: f"{x:+.2f}R")
    display_df['Expectancy'] = display_df['Expectancy'].apply(lambda x: f"{x:+.3f}")

    st.dataframe(display_df, use_container_width=True, hide_index=True)


def render_op_stop_charts(summary_df: pd.DataFrame) -> None:
    """Render win rate and expectancy charts."""
    if summary_df.empty:
        return

    col1, col2 = st.columns(2)

    with col1:
        # Win Rate Chart
        valid_df = summary_df[summary_df['n'] > 0].copy()
        valid_df = valid_df.sort_values('Win Rate %', ascending=True)

        colors = [CHART_COLORS['win'] if x >= 50 else CHART_COLORS['loss']
                  for x in valid_df['Win Rate %']]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=valid_df['Win Rate %'],
            y=valid_df['Stop Type'],
            orientation='h',
            marker_color=colors,
            text=valid_df['Win Rate %'].apply(lambda x: f"{x:.1f}%"),
            textposition='auto'
        ))

        fig.add_vline(x=50, line_dash="dash", line_color=CHART_COLORS['text'])

        fig.update_layout(
            title="Win Rate by Stop Type",
            xaxis_title="Win Rate %",
            yaxis_title="",
            paper_bgcolor=CHART_COLORS['paper'],
            plot_bgcolor=CHART_COLORS['background'],
            font=dict(color=CHART_COLORS['text']),
            height=350
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Expectancy Chart
        valid_df = summary_df[summary_df['n'] > 0].copy()
        valid_df = valid_df.sort_values('Expectancy', ascending=True)

        colors = [CHART_COLORS['win'] if x >= 0 else CHART_COLORS['loss']
                  for x in valid_df['Expectancy']]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=valid_df['Expectancy'],
            y=valid_df['Stop Type'],
            orientation='h',
            marker_color=colors,
            text=valid_df['Expectancy'].apply(lambda x: f"{x:+.3f}R"),
            textposition='auto'
        ))

        fig.add_vline(x=0, line_dash="dash", line_color=CHART_COLORS['text'])

        fig.update_layout(
            title="Expectancy by Stop Type",
            xaxis_title="Expectancy (R)",
            yaxis_title="",
            paper_bgcolor=CHART_COLORS['paper'],
            plot_bgcolor=CHART_COLORS['background'],
            font=dict(color=CHART_COLORS['text']),
            height=350
        )

        st.plotly_chart(fig, use_container_width=True)


def render_op_stop_analysis_section(
    options_data: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """
    Main entry point for options stop analysis UI.

    Renders the complete CALC-O09 section.

    Parameters:
    -----------
    options_data : List[Dict]
        Options MFE/MAE data from op_mfe_mae_potential table

    Returns:
    --------
    Dict with analysis results for downstream use (Monte AI, etc.)
    """
    st.subheader("Options Stop Type Analysis")
    st.markdown("*Foundation analysis: Which stop level provides best risk-adjusted returns?*")
    st.caption("Target = 1R (same % as stop) | Win = Target reached before stop hit")

    if not options_data:
        st.warning("No options MFE/MAE data available for stop analysis")
        return None

    with st.spinner("Analyzing options stop types..."):
        results = simulate_all_outcomes(options_data)
        summary_df = aggregate_by_stop_type(results)
        best_stop = find_best_stop_type(summary_df)
        total_trades = len(options_data)

    if summary_df.empty:
        st.warning("No stop analysis results available")
        return None

    # Render UI
    render_op_stop_summary_cards(summary_df, best_stop, total_trades)

    st.markdown("---")

    st.markdown("**Stop Type Comparison**")
    render_op_stop_comparison_table(summary_df)

    st.markdown("---")

    render_op_stop_charts(summary_df)

    # Model-Contract breakdown
    st.markdown("---")
    with st.expander("View by Model and Contract Type"):
        model_df = aggregate_by_model_contract(results)
        if not model_df.empty:
            # Format for display
            display_model_df = model_df.copy()
            if 'stop_type_key' in display_model_df.columns:
                display_model_df = display_model_df.drop(columns=['stop_type_key'])
            display_model_df['Win Rate %'] = display_model_df['Win Rate %'].apply(lambda x: f"{x:.1f}%")
            display_model_df['Expectancy'] = display_model_df['Expectancy'].apply(lambda x: f"{x:+.3f}")
            st.dataframe(display_model_df, use_container_width=True, hide_index=True)
        else:
            st.info("No model breakdown available")

    return {
        'summary': summary_df,
        'results': results,
        'best_stop': best_stop,
        'total_trades': total_trades,
        'model_breakdown': aggregate_by_model_contract(results)
    }
