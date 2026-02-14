"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Calculation: Options Simulated Outcomes (CALC-O05)
XIII Trading LLC
================================================================================

PURPOSE:
    Simulate options trade outcomes across a grid of stop/target combinations.
    Identifies optimal parameters for options trading by model.

    Grid Analysis:
    - Stop levels: 10%, 15%, 20%, 25%, 30%, 50%
    - Target levels: 25%, 50%, 75%, 100%, 150%, 200%
    - Shows best combination per model

DATA SOURCE:
    Uses the `op_mfe_mae_potential` table EXCLUSIVELY.

    Key columns needed:
    - option_entry_price: Entry price of option
    - mfe_pct: Maximum favorable excursion (% gain)
    - mae_pct: Maximum adverse excursion (% loss)
    - mfe_time: When MFE occurred
    - mae_time: When MAE occurred
    - model: EPCH01-04
    - contract_type: CALL or PUT

================================================================================
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from decimal import Decimal
import streamlit as st
import plotly.graph_objects as go


# =============================================================================
# CONFIGURATION
# =============================================================================
MODELS = ["EPCH01", "EPCH02", "EPCH03", "EPCH04"]

# Default ranges for grid search
DEFAULT_STOP_RANGE = [10, 15, 20, 25, 30, 50]  # % loss from entry
DEFAULT_TARGET_RANGE = [25, 50, 75, 100, 150, 200]  # % gain from entry

CHART_COLORS = {
    "win": "#26a69a",
    "loss": "#ef5350",
    "optimal": "#ffc107",
    "background": "#1a1a2e",
    "paper": "#16213e",
    "text": "#e0e0e0",
    "grid": "#2a2a4e"
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def _safe_float(value, default: float = None) -> Optional[float]:
    """Safely convert value to float."""
    if value is None:
        return default
    try:
        if isinstance(value, Decimal):
            return float(value)
        return float(value)
    except (ValueError, TypeError):
        return default


def _normalize_model(model_name: str) -> str:
    """Convert EPCH1 -> EPCH01, etc."""
    if model_name is None:
        return None
    if model_name in MODELS:
        return model_name
    model_map = {
        "EPCH1": "EPCH01", "EPCH2": "EPCH02",
        "EPCH3": "EPCH03", "EPCH4": "EPCH04"
    }
    return model_map.get(model_name, model_name)


# =============================================================================
# CORE CALCULATION FUNCTIONS
# =============================================================================
def simulate_options_outcome(
    mfe_pct: float,
    mae_pct: float,
    exit_pct: float,
    stop_pct: float,
    target_pct: float,
    mfe_first: bool = None
) -> Dict[str, Any]:
    """
    Simulate outcome for a single trade at given stop/target.

    Parameters:
    -----------
    mfe_pct : float
        Maximum favorable excursion (% gain, positive)
    mae_pct : float
        Maximum adverse excursion (% loss, positive value)
    exit_pct : float
        Exit percentage at 15:30 ET
    stop_pct : float
        Stop level (% loss from entry)
    target_pct : float
        Target level (% gain from entry)
    mfe_first : bool, optional
        Whether MFE occurred before MAE. If None, assume stop hit first.

    Returns:
    --------
    Dict with keys: outcome, r_achieved, stop_hit, target_reached
    """
    stop_hit = mae_pct >= stop_pct
    target_reached = mfe_pct >= target_pct

    if target_reached and not stop_hit:
        # Target reached, stop never hit - WIN
        outcome = 'WIN'
        r_achieved = target_pct / stop_pct  # R = target / risk
    elif stop_hit and not target_reached:
        # Stop hit, target never reached - LOSS
        outcome = 'LOSS'
        r_achieved = -1.0
    elif target_reached and stop_hit:
        # Both triggered - need to determine which was first
        if mfe_first is True:
            outcome = 'WIN'
            r_achieved = target_pct / stop_pct
        elif mfe_first is False:
            outcome = 'LOSS'
            r_achieved = -1.0
        else:
            # Unknown order - conservative assumption: stop hit first
            outcome = 'LOSS'
            r_achieved = -1.0
    else:
        # Neither triggered - use exit_pct at 15:30
        if exit_pct > 0:
            outcome = 'WIN'
            r_achieved = exit_pct / stop_pct
        else:
            outcome = 'LOSS'
            r_achieved = exit_pct / stop_pct  # Negative

    return {
        'outcome': outcome,
        'r_achieved': r_achieved,
        'stop_hit': stop_hit,
        'target_reached': target_reached
    }


def calculate_simulated_stats(
    data: List[Dict[str, Any]],
    stop_pct: float,
    target_pct: float
) -> Dict[str, Any]:
    """
    Calculate win rate and expectancy at a specific stop/target combination.
    """
    if not data:
        return {
            'n': 0, 'wins': 0, 'losses': 0,
            'win_rate': 0.0, 'avg_r': 0.0, 'expectancy': 0.0,
            'stop_pct': stop_pct, 'target_pct': target_pct
        }

    results = []

    for trade in data:
        mfe_pct = _safe_float(trade.get('mfe_pct'), 0)
        mae_pct = _safe_float(trade.get('mae_pct'), 0)
        exit_pct = _safe_float(trade.get('exit_pct'), 0)

        # Determine if MFE was first
        mfe_time = trade.get('mfe_time')
        mae_time = trade.get('mae_time')
        mfe_first = None
        if mfe_time and mae_time:
            mfe_first = mfe_time < mae_time

        outcome = simulate_options_outcome(
            mfe_pct, mae_pct, exit_pct, stop_pct, target_pct, mfe_first
        )
        results.append(outcome)

    n = len(results)
    wins = sum(1 for r in results if r['outcome'] == 'WIN')
    losses = sum(1 for r in results if r['outcome'] == 'LOSS')
    r_values = [r['r_achieved'] for r in results]

    win_rate = (wins / n) * 100 if n > 0 else 0
    avg_r = sum(r_values) / n if n > 0 else 0

    return {
        'n': n,
        'wins': wins,
        'losses': losses,
        'win_rate': win_rate,
        'avg_r': avg_r,
        'expectancy': avg_r,
        'stop_pct': stop_pct,
        'target_pct': target_pct,
        'r_ratio': target_pct / stop_pct
    }


def generate_stop_target_grid(
    data: List[Dict[str, Any]],
    stop_range: List[float] = None,
    target_range: List[float] = None
) -> pd.DataFrame:
    """
    Generate a grid of results across stop/target combinations.
    """
    if stop_range is None:
        stop_range = DEFAULT_STOP_RANGE
    if target_range is None:
        target_range = DEFAULT_TARGET_RANGE

    results = []

    for stop_pct in stop_range:
        for target_pct in target_range:
            stats = calculate_simulated_stats(data, stop_pct, target_pct)
            results.append(stats)

    return pd.DataFrame(results)


def generate_grid_by_model(
    data: List[Dict[str, Any]],
    stop_range: List[float] = None,
    target_range: List[float] = None
) -> pd.DataFrame:
    """
    Generate grid results for each model separately.

    Returns DataFrame with columns: model, stop_pct, target_pct, n, wins, losses,
                                    win_rate, expectancy, r_ratio
    """
    if stop_range is None:
        stop_range = DEFAULT_STOP_RANGE
    if target_range is None:
        target_range = DEFAULT_TARGET_RANGE

    results = []

    # Group data by model
    df = pd.DataFrame(data)
    if 'model' not in df.columns:
        return pd.DataFrame()

    df['model'] = df['model'].apply(_normalize_model)

    for model in MODELS:
        model_data = df[df['model'] == model].to_dict('records')
        if not model_data:
            continue

        for stop_pct in stop_range:
            for target_pct in target_range:
                stats = calculate_simulated_stats(model_data, stop_pct, target_pct)
                stats['model'] = model
                results.append(stats)

    return pd.DataFrame(results)


def find_optimal_by_model(
    grid_df: pd.DataFrame,
    metric: str = 'expectancy'
) -> pd.DataFrame:
    """
    Find optimal stop/target parameters for each model.

    Returns DataFrame with: model, optimal_stop, optimal_target, win_rate, expectancy, n
    """
    if grid_df.empty or 'model' not in grid_df.columns:
        return pd.DataFrame()

    results = []

    for model in MODELS:
        model_df = grid_df[grid_df['model'] == model]
        if model_df.empty:
            continue

        # Find best by metric
        best_idx = model_df[metric].idxmax()
        best_row = model_df.loc[best_idx]

        results.append({
            'Model': model,
            'Optimal Stop': f"{best_row['stop_pct']:.0f}%",
            'Optimal Target': f"{best_row['target_pct']:.0f}%",
            'R:R': f"{best_row['r_ratio']:.1f}:1",
            'Win Rate': best_row['win_rate'],
            'Expectancy': best_row['expectancy'],
            'n': best_row['n'],
            'stop_pct': best_row['stop_pct'],
            'target_pct': best_row['target_pct']
        })

    return pd.DataFrame(results)


def find_overall_optimal(
    grid_df: pd.DataFrame,
    metric: str = 'expectancy'
) -> Dict[str, Any]:
    """
    Find overall optimal stop/target parameters.
    """
    if grid_df.empty:
        return {
            'stop_pct': 25, 'target_pct': 50, 'expectancy': 0,
            'win_rate': 0, 'n': 0, 'found': False
        }

    best_idx = grid_df[metric].idxmax()
    best_row = grid_df.loc[best_idx]

    return {
        'stop_pct': best_row['stop_pct'],
        'target_pct': best_row['target_pct'],
        'expectancy': best_row['expectancy'],
        'win_rate': best_row['win_rate'],
        'n': best_row['n'],
        'r_ratio': best_row['r_ratio'],
        'found': True
    }


# =============================================================================
# STREAMLIT DISPLAY FUNCTIONS
# =============================================================================
def render_optimal_summary_cards(optimal: Dict[str, Any], total_trades: int) -> None:
    """Render summary cards for optimal parameters."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Optimal Stop",
            f"{optimal.get('stop_pct', 0):.0f}%"
        )

    with col2:
        st.metric(
            "Optimal Target",
            f"{optimal.get('target_pct', 0):.0f}%"
        )

    with col3:
        st.metric(
            "Win Rate",
            f"{optimal.get('win_rate', 0):.1f}%"
        )

    with col4:
        exp = optimal.get('expectancy', 0)
        st.metric(
            "Expectancy",
            f"{exp:+.3f}R"
        )


def render_model_optimal_table(optimal_df: pd.DataFrame) -> None:
    """Render table showing optimal parameters for each model."""
    if optimal_df.empty:
        st.info("No model data available")
        return

    display_df = optimal_df.copy()
    display_df['Win Rate'] = display_df['Win Rate'].apply(lambda x: f"{x:.1f}%")
    display_df['Expectancy'] = display_df['Expectancy'].apply(lambda x: f"{x:+.3f}R")

    st.dataframe(
        display_df[['Model', 'Optimal Stop', 'Optimal Target', 'R:R', 'Win Rate', 'Expectancy', 'n']],
        use_container_width=True,
        hide_index=True
    )


def render_heatmap(
    grid_df: pd.DataFrame,
    metric: str = 'expectancy',
    title_suffix: str = ""
) -> None:
    """Render heatmap of stop/target grid."""
    if grid_df.empty:
        st.warning("No grid data available")
        return

    # If model column exists, aggregate across all models first
    if 'model' in grid_df.columns:
        # Group by stop/target and average the metric
        pivot_data = grid_df.groupby(['stop_pct', 'target_pct'])[metric].mean().reset_index()
        pivot = pivot_data.pivot(index='stop_pct', columns='target_pct', values=metric)
    else:
        pivot = grid_df.pivot(index='stop_pct', columns='target_pct', values=metric)

    # Reverse rows so smaller stops at top
    pivot = pivot.iloc[::-1]

    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=[f"{int(c)}%" for c in pivot.columns],
        y=[f"{int(r)}%" for r in pivot.index],
        colorscale='RdYlGn',
        text=[[f"{v:.2f}" for v in row] for row in pivot.values],
        texttemplate="%{text}",
        textfont={"size": 11},
        hovertemplate=(
            f"Stop: %{{y}}<br>"
            f"Target: %{{x}}<br>"
            f"{metric.title()}: %{{z:.3f}}<extra></extra>"
        )
    ))

    title_map = {
        'expectancy': 'Expectancy (R)',
        'win_rate': 'Win Rate (%)'
    }

    fig.update_layout(
        title=f"Stop/Target Grid - {title_map.get(metric, metric)} {title_suffix}",
        xaxis_title="Target (%)",
        yaxis_title="Stop (%)",
        paper_bgcolor=CHART_COLORS['paper'],
        plot_bgcolor=CHART_COLORS['background'],
        font=dict(color=CHART_COLORS['text']),
        height=450
    )

    st.plotly_chart(fig, use_container_width=True)


def render_model_heatmaps(
    grid_df: pd.DataFrame,
    metric: str = 'expectancy'
) -> None:
    """Render heatmaps for each model in a 2x2 grid."""
    if grid_df.empty or 'model' not in grid_df.columns:
        st.warning("No model grid data available")
        return

    # Create 2x2 grid
    col1, col2 = st.columns(2)
    cols = [col1, col2, col1, col2]

    for i, model in enumerate(MODELS):
        model_df = grid_df[grid_df['model'] == model]
        if model_df.empty:
            continue

        with cols[i]:
            pivot = model_df.pivot(index='stop_pct', columns='target_pct', values=metric)
            pivot = pivot.iloc[::-1]

            fig = go.Figure(data=go.Heatmap(
                z=pivot.values,
                x=[f"{int(c)}%" for c in pivot.columns],
                y=[f"{int(r)}%" for r in pivot.index],
                colorscale='RdYlGn',
                text=[[f"{v:.2f}" for v in row] for row in pivot.values],
                texttemplate="%{text}",
                textfont={"size": 9},
                showscale=False
            ))

            fig.update_layout(
                title=f"{model}",
                xaxis_title="Target",
                yaxis_title="Stop",
                paper_bgcolor=CHART_COLORS['paper'],
                plot_bgcolor=CHART_COLORS['background'],
                font=dict(color=CHART_COLORS['text'], size=10),
                height=300,
                margin=dict(l=50, r=20, t=40, b=40)
            )

            st.plotly_chart(fig, use_container_width=True)


def render_simulated_outcomes_section(
    data: List[Dict[str, Any]],
    stop_range: List[float] = None,
    target_range: List[float] = None
) -> Dict[str, Any]:
    """
    Main entry point for CALC-O05 section.

    Parameters:
    -----------
    data : List[Dict]
        Options MFE/MAE data from op_mfe_mae_potential

    Returns:
    --------
    Dict with optimal parameters and grid results
    """
    st.subheader("Options Simulated Outcomes")
    st.markdown("*Find optimal stop/target combination for options by model*")

    if not data:
        st.warning("No options data available for simulation")
        return {}

    # Use default ranges
    if stop_range is None:
        stop_range = DEFAULT_STOP_RANGE
    if target_range is None:
        target_range = DEFAULT_TARGET_RANGE

    total_trades = len(data)

    # Run simulation
    with st.spinner("Running grid simulation..."):
        # Overall grid
        overall_grid = generate_stop_target_grid(data, stop_range, target_range)
        overall_optimal = find_overall_optimal(overall_grid)

        # Grid by model
        model_grid = generate_grid_by_model(data, stop_range, target_range)
        model_optimal = find_optimal_by_model(model_grid)

    st.markdown("---")

    # Overall optimal summary
    st.markdown("#### Overall Optimal Parameters")
    render_optimal_summary_cards(overall_optimal, total_trades)

    st.markdown("---")

    # Overall heatmap
    st.markdown("#### Stop/Target Grid (All Models)")

    metric = st.radio(
        "Heatmap Metric",
        options=['expectancy', 'win_rate'],
        format_func=lambda x: 'Expectancy (R)' if x == 'expectancy' else 'Win Rate (%)',
        horizontal=True,
        key="op_sim_metric"
    )

    render_heatmap(overall_grid, metric)

    st.markdown("---")

    # Optimal by model table
    st.markdown("#### Optimal Parameters by Model")
    st.caption("Best stop/target combination for each model based on expectancy")

    render_model_optimal_table(model_optimal)

    st.markdown("---")

    # Model heatmaps
    st.markdown("#### Model-Specific Grids")
    st.caption(f"Showing {metric.replace('_', ' ').title()} for each model")

    render_model_heatmaps(model_grid, metric)

    st.markdown("---")

    # Full grid table
    with st.expander("View Full Grid Results"):
        if not model_grid.empty:
            display_df = model_grid.copy()
            display_df['stop_pct'] = display_df['stop_pct'].apply(lambda x: f"{x:.0f}%")
            display_df['target_pct'] = display_df['target_pct'].apply(lambda x: f"{x:.0f}%")
            display_df['win_rate'] = display_df['win_rate'].apply(lambda x: f"{x:.1f}%")
            display_df['expectancy'] = display_df['expectancy'].apply(lambda x: f"{x:+.3f}R")
            display_df['r_ratio'] = display_df['r_ratio'].apply(lambda x: f"{x:.1f}:1")

            display_df = display_df.rename(columns={
                'model': 'Model',
                'stop_pct': 'Stop',
                'target_pct': 'Target',
                'win_rate': 'Win Rate',
                'expectancy': 'Expectancy',
                'r_ratio': 'R:R'
            })

            st.dataframe(
                display_df[['Model', 'Stop', 'Target', 'R:R', 'n', 'wins', 'losses', 'Win Rate', 'Expectancy']],
                use_container_width=True,
                hide_index=True
            )

    return {
        'overall_grid': overall_grid,
        'overall_optimal': overall_optimal,
        'model_grid': model_grid,
        'model_optimal': model_optimal,
        'stop_range': stop_range,
        'target_range': target_range,
        'total_trades': total_trades
    }


# =============================================================================
# EXAMPLE USAGE
# =============================================================================
if __name__ == "__main__":
    # Sample data
    sample_data = [
        {"mfe_pct": 45.0, "mae_pct": 12.0, "exit_pct": 30.0, "model": "EPCH02"},
        {"mfe_pct": 22.0, "mae_pct": 35.0, "exit_pct": -15.0, "model": "EPCH02"},
        {"mfe_pct": 80.0, "mae_pct": 8.0, "exit_pct": 55.0, "model": "EPCH04"},
        {"mfe_pct": 15.0, "mae_pct": 28.0, "exit_pct": -20.0, "model": "EPCH01"},
        {"mfe_pct": 55.0, "mae_pct": 18.0, "exit_pct": 40.0, "model": "EPCH03"},
    ]

    print("\nSimulated Stats at 25% Stop, 50% Target:")
    stats = calculate_simulated_stats(sample_data, 25, 50)
    print(f"  Trades: {stats['n']}")
    print(f"  Win Rate: {stats['win_rate']:.1f}%")
    print(f"  Expectancy: {stats['expectancy']:+.2f}R")

    print("\n\nGrid Search Results:")
    grid = generate_stop_target_grid(sample_data, [20, 25, 30], [50, 75, 100])
    print(grid.to_string(index=False))

    print("\n\nOptimal Parameters:")
    optimal = find_overall_optimal(grid)
    print(f"  Stop: {optimal['stop_pct']}%")
    print(f"  Target: {optimal['target_pct']}%")
    print(f"  Expectancy: {optimal['expectancy']:+.2f}R")
