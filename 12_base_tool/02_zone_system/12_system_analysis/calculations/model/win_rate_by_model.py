"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Calculation: Win Rate by Model (CALC-001)
XIII Trading LLC
================================================================================

PURPOSE:
    Calculate win/loss statistics for each trading model (EPCH01-04).
    This is a foundational metric for Monte Carlo simulation that shows
    the performance breakdown between different entry models.

WIN CONDITION (Stop-Based):
    Win = MFE reached (>=1R) before stop hit
    Loss = Stop hit before reaching 1R
    Partial = Stop hit after some MFE but < 1R

    Uses pre-computed outcomes from stop_analysis table.
    Default stop type: Zone + 5% Buffer

MODELS:
    - EPCH01: Primary Zone Continuation
    - EPCH02: Primary Zone Rejection
    - EPCH03: Secondary Zone Continuation
    - EPCH04: Secondary Zone Rejection

DATA SOURCE:
    Uses stop_analysis table for win/loss classification.
    Merged with entry_indicators for indicator data.

USAGE:
    from calculations.model.win_rate_by_model import (
        calculate_win_rate_by_model,
        render_model_summary_table,
        render_model_win_loss_chart,
        render_model_breakdown
    )

    # Get the statistics (pass stop outcomes)
    model_stats = calculate_win_rate_by_model(stop_outcomes, stop_type_name)

    # Display in Streamlit
    render_model_breakdown(stop_outcomes, stop_type_name)

Updated: 2026-01-11
- Removed temporal mfe_time < mae_time logic
- Now uses stop-based outcomes exclusively
- Default stop type: Zone + 5% Buffer
================================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
import pandas as pd
from typing import List, Dict, Any, Optional
import streamlit as st
import plotly.graph_objects as go


# =============================================================================
# CONFIGURATION
# =============================================================================
MODELS = ["EPCH01", "EPCH02", "EPCH03", "EPCH04"]

CHART_COLORS = {
    "win": "#26a69a",
    "loss": "#ef5350",
    "background": "#1a1a2e",
    "paper": "#16213e",
    "text": "#e0e0e0"
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def _normalize_model(model_name: str) -> str:
    """Convert EPCH1 -> EPCH01, EPCH2 -> EPCH02, etc."""
    if model_name is None:
        return None
    if model_name in MODELS:
        return model_name
    model_map = {
        "EPCH1": "EPCH01", "EPCH2": "EPCH02",
        "EPCH3": "EPCH03", "EPCH4": "EPCH04"
    }
    return model_map.get(model_name, model_name)


def _safe_float(value, default: float = 0.0) -> float:
    """Safely convert value to float."""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


# =============================================================================
# MAIN CALCULATION FUNCTION
# =============================================================================
def calculate_win_rate_by_model(
    stop_outcomes: List[Dict[str, Any]],
    stop_type_name: str = "Zone + 5% Buffer"
) -> pd.DataFrame:
    """
    Calculate win rate by model using stop-based outcomes.

    WIN CONDITION:
        Win = MFE reached (>=1R) before stop hit (outcome == 'WIN')
        Loss = Stop hit before reaching 1R (outcome == 'LOSS')
        Partial = Stop hit after some MFE but < 1R (outcome == 'PARTIAL')

    Parameters:
    -----------
    stop_outcomes : List[Dict]
        Outcome records from stop_analysis for selected stop type.
        Each record should have:
        - trade_id: Trade identifier
        - model: EPCH01-04
        - direction: LONG/SHORT
        - outcome: WIN/LOSS/PARTIAL
        - r_achieved: R-multiple achieved

    stop_type_name : str
        Display name of stop type for labeling

    Returns:
    --------
    pd.DataFrame with columns:
        Model, Wins, Losses, Partials, Total, Win%, Expectancy, Avg R (Win), Avg R (All)
    """
    if not stop_outcomes:
        return pd.DataFrame(columns=[
            "Model", "Wins", "Losses", "Partials", "Total",
            "Win%", "Expectancy", "Avg R (Win)", "Avg R (All)"
        ])

    df = pd.DataFrame(stop_outcomes)

    # Normalize model names
    if 'model' in df.columns:
        df['model'] = df['model'].apply(_normalize_model)

    # Group by model and calculate statistics
    results = []

    for model in MODELS:
        model_df = df[df['model'] == model] if 'model' in df.columns else pd.DataFrame()

        if model_df.empty:
            results.append({
                'Model': model,
                'Wins': 0,
                'Losses': 0,
                'Partials': 0,
                'Total': 0,
                'Win%': 0.0,
                'Expectancy': 0.0,
                'Avg R (Win)': 0.0,
                'Avg R (All)': 0.0
            })
            continue

        total = len(model_df)
        wins = len(model_df[model_df['outcome'] == 'WIN'])
        losses = len(model_df[model_df['outcome'] == 'LOSS'])
        partials = len(model_df[model_df['outcome'] == 'PARTIAL'])

        win_rate = (wins / total * 100) if total > 0 else 0
        loss_rate = losses / total if total > 0 else 0

        # Calculate R metrics
        total_r = 0.0
        win_r_sum = 0.0
        win_count = 0

        for _, row in model_df.iterrows():
            outcome = row.get('outcome', 'PARTIAL')
            r_achieved = _safe_float(row.get('r_achieved', 0))

            if outcome == 'WIN':
                total_r += 1.0
                win_r_sum += 1.0
                win_count += 1
            elif outcome == 'LOSS':
                total_r -= 1.0
            else:  # PARTIAL
                total_r += r_achieved
                if r_achieved > 0:
                    win_r_sum += r_achieved
                    win_count += 1

        avg_r_all = total_r / total if total > 0 else 0
        avg_r_win = win_r_sum / win_count if win_count > 0 else 0

        # Expectancy formula: E = (win% * avg_win_r) - (loss% * 1R)
        expectancy = ((win_rate / 100) * avg_r_win) - (loss_rate * 1.0)

        results.append({
            'Model': model,
            'Wins': wins,
            'Losses': losses,
            'Partials': partials,
            'Total': total,
            'Win%': round(win_rate, 1),
            'Expectancy': round(expectancy, 3),
            'Avg R (Win)': round(avg_r_win, 2),
            'Avg R (All)': round(avg_r_all, 2)
        })

    return pd.DataFrame(results)


# =============================================================================
# STREAMLIT DISPLAY FUNCTIONS
# =============================================================================
def render_model_summary_table(model_stats: pd.DataFrame) -> None:
    """
    Display the model statistics as a formatted Streamlit table.

    Parameters:
    -----------
    model_stats : pd.DataFrame
        Output from calculate_win_rate_by_model()
    """
    if model_stats.empty:
        st.info("No trade data available for model breakdown")
        return

    display_df = model_stats.copy()
    display_df['Win%'] = display_df['Win%'].apply(lambda x: f"{x:.1f}%")
    display_df['Expectancy'] = display_df['Expectancy'].apply(lambda x: f"{x:+.3f}")
    display_df['Avg R (Win)'] = display_df['Avg R (Win)'].apply(lambda x: f"{x:+.2f}")
    display_df['Avg R (All)'] = display_df['Avg R (All)'].apply(lambda x: f"{x:+.2f}")

    columns_to_show = ['Model', 'Wins', 'Losses', 'Win%', 'Expectancy', 'Avg R (All)']
    st.dataframe(
        display_df[columns_to_show],
        use_container_width=True,
        hide_index=True
    )


def render_model_win_loss_chart(model_stats: pd.DataFrame) -> None:
    """
    Display a grouped bar chart showing wins and losses per model.

    Parameters:
    -----------
    model_stats : pd.DataFrame
        Output from calculate_win_rate_by_model()
    """
    if model_stats.empty:
        st.info("No trade data available for chart")
        return

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name='Wins',
        x=model_stats['Model'],
        y=model_stats['Wins'],
        marker_color=CHART_COLORS['win'],
        text=model_stats['Wins'],
        textposition='auto'
    ))

    fig.add_trace(go.Bar(
        name='Losses',
        x=model_stats['Model'],
        y=model_stats['Losses'],
        marker_color=CHART_COLORS['loss'],
        text=model_stats['Losses'],
        textposition='auto'
    ))

    fig.update_layout(
        barmode='group',
        paper_bgcolor=CHART_COLORS['paper'],
        plot_bgcolor=CHART_COLORS['background'],
        font=dict(color=CHART_COLORS['text']),
        height=350,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=50, r=50, t=50, b=50)
    )

    fig.update_xaxes(title="Model")
    fig.update_yaxes(title="Number of Trades")

    st.plotly_chart(fig, use_container_width=True)


def render_model_breakdown(
    stop_outcomes: List[Dict[str, Any]],
    stop_type_name: str = "Zone + 5% Buffer"
) -> Optional[pd.DataFrame]:
    """
    Render CALC-001 section using stop-based outcomes.

    Parameters:
    -----------
    stop_outcomes : List[Dict]
        Outcome records from selected stop type
    stop_type_name : str
        Display name for header

    Returns:
    --------
    pd.DataFrame: The calculated model stats, or None if no data
    """
    st.subheader("Win Rate by Model")
    st.caption(f"Using: **{stop_type_name}** | Win = 1R reached before stop hit")

    if not stop_outcomes:
        st.warning("No stop analysis data available. Ensure stop_analysis table is populated.")
        return None

    df = calculate_win_rate_by_model(stop_outcomes, stop_type_name)

    if df.empty or df['Total'].sum() == 0:
        st.warning("No model data available")
        return None

    # Summary cards
    total_trades = df['Total'].sum()
    total_wins = df['Wins'].sum()
    total_losses = df['Losses'].sum()
    overall_win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0

    # Calculate overall expectancy (weighted by trade count)
    total_r = sum(
        row['Avg R (All)'] * row['Total']
        for _, row in df.iterrows()
    )
    overall_expectancy = total_r / total_trades if total_trades > 0 else 0

    cols = st.columns(5)
    with cols[0]:
        st.metric("Total Trades", f"{total_trades:,}")
    with cols[1]:
        st.metric("Wins", f"{total_wins:,}")
    with cols[2]:
        st.metric("Losses", f"{total_losses:,}")
    with cols[3]:
        st.metric("Win Rate", f"{overall_win_rate:.1f}%")
    with cols[4]:
        st.metric("Avg Expectancy", f"{overall_expectancy:+.3f}R")

    st.markdown("---")

    # Display table and chart side by side
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("**Summary Table**")
        render_model_summary_table(df)

    with col2:
        st.markdown("**Win/Loss Distribution**")
        render_model_win_loss_chart(df)

    return df


# =============================================================================
# EXAMPLE USAGE (for testing)
# =============================================================================
if __name__ == "__main__":
    # Example stop outcomes data for testing
    sample_stop_outcomes = [
        # EPCH01: 2 wins, 1 loss
        {"trade_id": "T001", "model": "EPCH01", "direction": "LONG", "outcome": "WIN", "r_achieved": 1.5},
        {"trade_id": "T002", "model": "EPCH01", "direction": "LONG", "outcome": "WIN", "r_achieved": 2.0},
        {"trade_id": "T003", "model": "EPCH01", "direction": "SHORT", "outcome": "LOSS", "r_achieved": -1.0},
        # EPCH02: 1 win, 2 losses
        {"trade_id": "T004", "model": "EPCH02", "direction": "LONG", "outcome": "WIN", "r_achieved": 1.2},
        {"trade_id": "T005", "model": "EPCH02", "direction": "SHORT", "outcome": "LOSS", "r_achieved": -1.0},
        {"trade_id": "T006", "model": "EPCH02", "direction": "SHORT", "outcome": "LOSS", "r_achieved": -1.0},
        # EPCH03: 1 win
        {"trade_id": "T007", "model": "EPCH03", "direction": "LONG", "outcome": "WIN", "r_achieved": 1.8},
        # EPCH04: 1 loss
        {"trade_id": "T008", "model": "EPCH04", "direction": "SHORT", "outcome": "LOSS", "r_achieved": -1.0},
    ]

    # Calculate and print results
    result = calculate_win_rate_by_model(sample_stop_outcomes, "Zone + 5% Buffer")
    print("\nModel Win Rate Statistics (Stop-Based):")
    print("=" * 70)
    print(result.to_string(index=False))
    print("\nExpected output:")
    print("  EPCH01: 2 wins, 1 loss, 66.7%")
    print("  EPCH02: 1 win, 2 losses, 33.3%")
    print("  EPCH03: 1 win, 0 losses, 100%")
    print("  EPCH04: 0 wins, 1 loss, 0%")
