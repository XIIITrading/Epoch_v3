"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Calculation: Options vs Underlying Comparison (CALC-O04)
XIII Trading LLC
================================================================================

PURPOSE:
    Compare OPTIONS price movement to UNDERLYING stock price movement.
    Calculates effective leverage and helps understand options behavior
    relative to the underlying asset.

    Core Questions:
    - What is the effective leverage of our options trades?
    - How do options MFE/MAE compare to underlying MFE/MAE?
    - Are we capturing the expected leverage?

DATA SOURCE:
    This module uses the `op_mfe_mae_potential` table EXCLUSIVELY.

    Key columns:
    - mfe_pct: Options MFE as % of options entry price
    - mae_pct: Options MAE as % of options entry price
    - exit_pct: Options exit as % of options entry price
    - underlying_mfe_pct: Underlying MFE as % (from mfe_mae_potential)
    - underlying_mae_pct: Underlying MAE as % (from mfe_mae_potential)
    - underlying_exit_pct: Underlying exit as % (from mfe_mae_potential)

METRICS CALCULATED:
    - MFE Leverage: options_mfe_pct / underlying_mfe_pct
    - MAE Leverage: options_mae_pct / underlying_mae_pct
    - Exit Leverage: options_exit_pct / underlying_exit_pct
    - Leverage efficiency: Are we getting expected leverage?

================================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
import pandas as pd
from typing import List, Dict, Any, Optional
from decimal import Decimal
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go


# =============================================================================
# CONFIGURATION
# =============================================================================
MODELS = ["EPCH01", "EPCH02", "EPCH03", "EPCH04"]

CHART_COLORS = {
    "options": "#2E86AB",
    "underlying": "#E94F37",
    "call": "#26a69a",
    "put": "#ef5350",
    "background": "#1a1a2e",
    "paper": "#16213e",
    "text": "#e0e0e0",
    "grid": "#2a2a4e",
    "reference": "#ffc107"
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def _safe_float(value, default: float = None) -> Optional[float]:
    """Safely convert a value to float, handling Decimal types."""
    if value is None:
        return default
    try:
        if isinstance(value, Decimal):
            return float(value)
        return float(value)
    except (ValueError, TypeError):
        return default


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


def _prepare_comparison_dataframe(data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Prepare DataFrame with leverage calculations.

    Parameters:
    -----------
    data : List[Dict[str, Any]]
        List of records from op_mfe_mae_potential table

    Returns:
    --------
    pd.DataFrame
        DataFrame with leverage columns added
    """
    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    # Convert numeric columns
    numeric_cols = ['mfe_pct', 'mae_pct', 'exit_pct',
                    'underlying_mfe_pct', 'underlying_mae_pct', 'underlying_exit_pct']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].apply(_safe_float)

    # Normalize model names
    if 'model' in df.columns:
        df['model'] = df['model'].apply(_normalize_model)

    # Calculate leverage metrics (only where underlying > 0)
    if 'underlying_mfe_pct' in df.columns and 'mfe_pct' in df.columns:
        df['mfe_leverage'] = df.apply(
            lambda row: row['mfe_pct'] / row['underlying_mfe_pct']
            if row.get('underlying_mfe_pct') and row['underlying_mfe_pct'] > 0
            else None,
            axis=1
        )

    if 'underlying_mae_pct' in df.columns and 'mae_pct' in df.columns:
        df['mae_leverage'] = df.apply(
            lambda row: row['mae_pct'] / row['underlying_mae_pct']
            if row.get('underlying_mae_pct') and row['underlying_mae_pct'] > 0
            else None,
            axis=1
        )

    if 'underlying_exit_pct' in df.columns and 'exit_pct' in df.columns:
        df['exit_leverage'] = df.apply(
            lambda row: abs(row['exit_pct'] / row['underlying_exit_pct'])
            if row.get('underlying_exit_pct') and abs(row['underlying_exit_pct']) > 0.01
            else None,
            axis=1
        )

    return df


# =============================================================================
# CORE CALCULATION FUNCTIONS
# =============================================================================
def calculate_leverage_comparison(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate leverage statistics comparing options to underlying.

    Parameters:
    -----------
    data : List[Dict[str, Any]]
        List of records from op_mfe_mae_potential table

    Returns:
    --------
    Dict[str, Any]
        Dictionary containing leverage statistics
    """
    empty_result = {
        "median_mfe_leverage": 0.0,
        "median_mae_leverage": 0.0,
        "median_exit_leverage": 0.0,
        "mean_mfe_leverage": 0.0,
        "mean_mae_leverage": 0.0,
        "median_options_mfe": 0.0,
        "median_underlying_mfe": 0.0,
        "median_options_mae": 0.0,
        "median_underlying_mae": 0.0,
        "median_options_exit": 0.0,
        "median_underlying_exit": 0.0,
        "trades_with_comparison": 0,
        "total_trades": 0
    }

    if not data:
        return empty_result

    df = _prepare_comparison_dataframe(data)

    if df.empty:
        return empty_result

    total_trades = len(df)

    # Filter to trades with valid underlying comparison
    df_comparison = df.dropna(subset=['underlying_mfe_pct', 'underlying_mae_pct'])
    trades_with_comparison = len(df_comparison)

    if trades_with_comparison == 0:
        return {**empty_result, 'total_trades': total_trades}

    # Options metrics
    median_options_mfe = df_comparison['mfe_pct'].median() if 'mfe_pct' in df_comparison.columns else 0.0
    median_options_mae = df_comparison['mae_pct'].median() if 'mae_pct' in df_comparison.columns else 0.0
    median_options_exit = df_comparison['exit_pct'].median() if 'exit_pct' in df_comparison.columns else 0.0

    # Underlying metrics
    median_underlying_mfe = df_comparison['underlying_mfe_pct'].median()
    median_underlying_mae = df_comparison['underlying_mae_pct'].median()
    median_underlying_exit = df_comparison['underlying_exit_pct'].median() if 'underlying_exit_pct' in df_comparison.columns else 0.0

    # Leverage metrics
    mfe_leverage = df_comparison['mfe_leverage'].dropna() if 'mfe_leverage' in df_comparison.columns else pd.Series([])
    mae_leverage = df_comparison['mae_leverage'].dropna() if 'mae_leverage' in df_comparison.columns else pd.Series([])
    exit_leverage = df_comparison['exit_leverage'].dropna() if 'exit_leverage' in df_comparison.columns else pd.Series([])

    return {
        "median_mfe_leverage": float(mfe_leverage.median()) if len(mfe_leverage) > 0 else 0.0,
        "median_mae_leverage": float(mae_leverage.median()) if len(mae_leverage) > 0 else 0.0,
        "median_exit_leverage": float(exit_leverage.median()) if len(exit_leverage) > 0 else 0.0,
        "mean_mfe_leverage": float(mfe_leverage.mean()) if len(mfe_leverage) > 0 else 0.0,
        "mean_mae_leverage": float(mae_leverage.mean()) if len(mae_leverage) > 0 else 0.0,
        "median_options_mfe": float(median_options_mfe),
        "median_underlying_mfe": float(median_underlying_mfe),
        "median_options_mae": float(median_options_mae),
        "median_underlying_mae": float(median_underlying_mae),
        "median_options_exit": float(median_options_exit),
        "median_underlying_exit": float(median_underlying_exit),
        "trades_with_comparison": int(trades_with_comparison),
        "total_trades": int(total_trades)
    }


def calculate_options_vs_underlying_summary(data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Calculate summary comparison by model and contract type.

    Parameters:
    -----------
    data : List[Dict[str, Any]]
        List of records from op_mfe_mae_potential table

    Returns:
    --------
    pd.DataFrame
        Summary statistics by model and contract type
    """
    df = _prepare_comparison_dataframe(data)

    if df.empty:
        return pd.DataFrame()

    # Filter to trades with valid comparison
    df = df.dropna(subset=['underlying_mfe_pct', 'underlying_mae_pct'])

    if df.empty:
        return pd.DataFrame()

    results = []

    for model in MODELS:
        for contract in ['CALL', 'PUT']:
            if 'contract_type' in df.columns:
                mask = (df['model'] == model) & (df['contract_type'].str.upper() == contract)
            else:
                mask = (df['model'] == model)

            subset = df[mask]

            if len(subset) == 0:
                continue

            mfe_lev = subset['mfe_leverage'].dropna()
            mae_lev = subset['mae_leverage'].dropna()

            results.append({
                'Model': model,
                'Contract': contract,
                'Trades': len(subset),
                'Opt MFE%': round(subset['mfe_pct'].median(), 1),
                'Und MFE%': round(subset['underlying_mfe_pct'].median(), 2),
                'MFE Leverage': round(mfe_lev.median(), 1) if len(mfe_lev) > 0 else 0,
                'Opt MAE%': round(subset['mae_pct'].median(), 1),
                'Und MAE%': round(subset['underlying_mae_pct'].median(), 2),
                'MAE Leverage': round(mae_lev.median(), 1) if len(mae_lev) > 0 else 0,
            })

    return pd.DataFrame(results)


# =============================================================================
# STREAMLIT DISPLAY FUNCTIONS
# =============================================================================
def render_leverage_summary_cards(stats: Dict[str, Any]) -> None:
    """Display leverage summary statistics as Streamlit metric cards."""
    if not stats or stats.get('trades_with_comparison', 0) == 0:
        st.info("No options vs underlying comparison data available")
        return

    st.markdown("**Leverage Summary**")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "MFE Leverage",
            f"{stats['median_mfe_leverage']:.1f}x",
            help="Options MFE % / Underlying MFE %"
        )
    with col2:
        st.metric(
            "MAE Leverage",
            f"{stats['median_mae_leverage']:.1f}x",
            help="Options MAE % / Underlying MAE %"
        )
    with col3:
        st.metric(
            "Exit Leverage",
            f"{stats['median_exit_leverage']:.1f}x",
            help="Options Exit % / Underlying Exit %"
        )
    with col4:
        st.metric(
            "Trades Compared",
            f"{stats['trades_with_comparison']:,}",
            help="Trades with both options and underlying data"
        )

    st.markdown("**Median Movement Comparison**")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Options MFE",
            f"{stats['median_options_mfe']:.1f}%",
            help="Median options MFE %"
        )
    with col2:
        st.metric(
            "Underlying MFE",
            f"{stats['median_underlying_mfe']:.2f}%",
            help="Median underlying MFE %"
        )
    with col3:
        st.metric(
            "Options MAE",
            f"{stats['median_options_mae']:.1f}%",
            help="Median options MAE %"
        )
    with col4:
        st.metric(
            "Underlying MAE",
            f"{stats['median_underlying_mae']:.2f}%",
            help="Median underlying MAE %"
        )


def render_leverage_comparison_chart(data: List[Dict[str, Any]]) -> None:
    """Bar chart comparing options vs underlying MFE/MAE."""
    stats = calculate_leverage_comparison(data)

    if stats.get('trades_with_comparison', 0) == 0:
        st.info("No comparison data available for chart")
        return

    # Create comparison data
    comparison_data = {
        'Metric': ['MFE', 'MFE', 'MAE', 'MAE', 'Exit', 'Exit'],
        'Type': ['Options', 'Underlying', 'Options', 'Underlying', 'Options', 'Underlying'],
        'Value': [
            stats['median_options_mfe'],
            stats['median_underlying_mfe'],
            stats['median_options_mae'],
            stats['median_underlying_mae'],
            abs(stats['median_options_exit']),
            abs(stats['median_underlying_exit'])
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
        color_discrete_map={'Options': CHART_COLORS['options'], 'Underlying': CHART_COLORS['underlying']}
    )

    fig.update_layout(
        paper_bgcolor=CHART_COLORS['paper'],
        plot_bgcolor=CHART_COLORS['background'],
        font=dict(color=CHART_COLORS['text']),
        height=400,
        margin=dict(l=50, r=50, t=80, b=50),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig.update_xaxes(gridcolor=CHART_COLORS['grid'])
    fig.update_yaxes(gridcolor=CHART_COLORS['grid'])

    st.plotly_chart(fig, use_container_width=True)


def render_options_vs_underlying_scatter(data: List[Dict[str, Any]], metric: str = 'mfe') -> None:
    """Scatter plot: Options metric vs Underlying metric."""
    df = _prepare_comparison_dataframe(data)

    if df.empty:
        st.info(f"No data available for {metric.upper()} scatter plot")
        return

    if metric == 'mfe':
        x_col, y_col = 'underlying_mfe_pct', 'mfe_pct'
        title = 'Options MFE vs Underlying MFE'
        x_label = 'Underlying MFE (%)'
        y_label = 'Options MFE (%)'
    elif metric == 'mae':
        x_col, y_col = 'underlying_mae_pct', 'mae_pct'
        title = 'Options MAE vs Underlying MAE'
        x_label = 'Underlying MAE (%)'
        y_label = 'Options MAE (%)'
    else:
        x_col, y_col = 'underlying_exit_pct', 'exit_pct'
        title = 'Options Exit vs Underlying Exit'
        x_label = 'Underlying Exit (%)'
        y_label = 'Options Exit (%)'

    if x_col not in df.columns or y_col not in df.columns:
        st.info(f"Missing columns for {metric.upper()} scatter plot")
        return

    scatter_df = df.dropna(subset=[x_col, y_col])

    if scatter_df.empty:
        st.info(f"No valid data for {metric.upper()} scatter plot")
        return

    color_col = 'contract_type' if 'contract_type' in scatter_df.columns else 'model'

    fig = px.scatter(
        scatter_df,
        x=x_col,
        y=y_col,
        color=color_col,
        title=title,
        labels={x_col: x_label, y_col: y_label},
        hover_data=['ticker', 'model'] if 'ticker' in scatter_df.columns else None,
        color_discrete_map={'CALL': CHART_COLORS['call'], 'PUT': CHART_COLORS['put']} if color_col == 'contract_type' else None
    )

    # Add reference lines for different leverage levels
    max_underlying = scatter_df[x_col].max()
    for leverage in [5, 10, 20]:
        fig.add_trace(
            go.Scatter(
                x=[0, max_underlying],
                y=[0, max_underlying * leverage],
                mode='lines',
                line=dict(color='gray', dash='dot', width=1),
                name=f'{leverage}x leverage',
                showlegend=True
            )
        )

    fig.update_layout(
        paper_bgcolor=CHART_COLORS['paper'],
        plot_bgcolor=CHART_COLORS['background'],
        font=dict(color=CHART_COLORS['text']),
        height=500,
        margin=dict(l=50, r=50, t=80, b=50),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig.update_xaxes(gridcolor=CHART_COLORS['grid'])
    fig.update_yaxes(gridcolor=CHART_COLORS['grid'])

    st.plotly_chart(fig, use_container_width=True)


def render_options_vs_underlying_table(data: List[Dict[str, Any]]) -> None:
    """Display comparison table by model and contract type."""
    comparison_df = calculate_options_vs_underlying_summary(data)

    if comparison_df.empty:
        st.info("No comparison data available")
        return

    st.dataframe(comparison_df, use_container_width=True, hide_index=True)


# =============================================================================
# MAIN SECTION RENDERER
# =============================================================================
def render_options_vs_underlying_section(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Main entry point to render the complete CALC-O04 section.

    Parameters:
    -----------
    data : List[Dict[str, Any]]
        List of records from op_mfe_mae_potential table

    Returns:
    --------
    Dict[str, Any]
        The leverage comparison statistics
    """
    st.subheader("Options vs Underlying Comparison")
    st.markdown("*How do options movements compare to underlying stock movements?*")

    if not data:
        st.warning("No options data available.")
        return {}

    # Check for underlying comparison columns
    df_check = pd.DataFrame(data)
    if 'underlying_mfe_pct' not in df_check.columns:
        st.warning("No underlying comparison data available. Ensure op_mfe_mae_potential table has underlying_mfe_pct column.")
        return {}

    # Calculate and display leverage stats
    stats = calculate_leverage_comparison(data)
    render_leverage_summary_cards(stats)

    st.markdown("---")

    # Leverage bar chart
    render_leverage_comparison_chart(data)

    st.markdown("---")

    # Scatter plots
    st.markdown("#### MFE Leverage Analysis")
    st.markdown("*Lines show 5x, 10x, and 20x leverage reference*")
    render_options_vs_underlying_scatter(data, 'mfe')

    st.markdown("#### MAE Leverage Analysis")
    render_options_vs_underlying_scatter(data, 'mae')

    st.markdown("---")

    # Summary table
    st.markdown("#### Leverage by Model and Contract Type")
    render_options_vs_underlying_table(data)

    return stats


# =============================================================================
# EXAMPLE USAGE (for testing)
# =============================================================================
if __name__ == "__main__":
    sample_data = [
        {
            "trade_id": "T1",
            "model": "EPCH02",
            "contract_type": "CALL",
            "ticker": "SPY",
            "mfe_pct": 45.0,
            "mae_pct": 12.0,
            "exit_pct": 25.0,
            "underlying_mfe_pct": 0.85,
            "underlying_mae_pct": 0.22,
            "underlying_exit_pct": 0.45,
        },
        {
            "trade_id": "T2",
            "model": "EPCH02",
            "contract_type": "CALL",
            "ticker": "SPY",
            "mfe_pct": 22.0,
            "mae_pct": 35.0,
            "exit_pct": -18.0,
            "underlying_mfe_pct": 0.55,
            "underlying_mae_pct": 0.75,
            "underlying_exit_pct": -0.35,
        },
        {
            "trade_id": "T3",
            "model": "EPCH04",
            "contract_type": "PUT",
            "ticker": "QQQ",
            "mfe_pct": 80.0,
            "mae_pct": 8.0,
            "exit_pct": 55.0,
            "underlying_mfe_pct": 1.20,
            "underlying_mae_pct": 0.15,
            "underlying_exit_pct": 0.85,
        },
    ]

    print("\nOptions vs Underlying Leverage Statistics:")
    print("=" * 60)
    stats = calculate_leverage_comparison(sample_data)
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")

    print("\n\nComparison by Model + Contract:")
    print("=" * 60)
    comparison_df = calculate_options_vs_underlying_summary(sample_data)
    if not comparison_df.empty:
        print(comparison_df.to_string(index=False))
