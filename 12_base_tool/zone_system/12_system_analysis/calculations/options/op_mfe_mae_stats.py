"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Calculation: Options MFE/MAE Distribution Analysis (CALC-O02)
XIII Trading LLC
================================================================================

PURPOSE:
    Analyze OPTIONS trade behavior through Maximum Favorable Excursion (MFE) and
    Maximum Adverse Excursion (MAE) from entry to 15:30 ET.

    Uses PERCENTAGE-BASED analysis of option price movement.

DATA SOURCE:
    This module uses the `op_mfe_mae_potential` table EXCLUSIVELY.

    Key columns:
    - option_entry_price: Options contract entry price
    - mfe_pct: Maximum favorable movement as % of entry price
    - mae_pct: Maximum adverse movement as % of entry price
    - exit_pct: Final exit movement as % of entry price
    - contract_type: CALL or PUT
    - model: EPCH01-04

METRICS CALCULATED:
    - MFE %: Maximum favorable movement as % of entry price
    - MAE %: Maximum adverse movement as % of entry price
    - MFE/MAE Ratio: Favorable vs adverse movement (higher = better)
    - Distribution percentiles for options stop placement research

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


# =============================================================================
# CONFIGURATION
# =============================================================================
MODELS = ["EPCH01", "EPCH02", "EPCH03", "EPCH04"]

CHART_COLORS = {
    "mfe": "#2E86AB",
    "mae": "#E94F37",
    "background": "#1a1a2e",
    "paper": "#16213e",
    "text": "#e0e0e0",
    "grid": "#2a2a4e"
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


def _prepare_options_dataframe(data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Prepare DataFrame from op_mfe_mae_potential data.

    Parameters:
    -----------
    data : List[Dict[str, Any]]
        List of records from op_mfe_mae_potential table

    Returns:
    --------
    pd.DataFrame
        DataFrame with normalized columns
    """
    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    # Convert Decimal columns to float
    numeric_cols = ['mfe_pct', 'mae_pct', 'exit_pct', 'mfe_points', 'mae_points',
                    'exit_points', 'option_entry_price']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].apply(_safe_float)

    # Normalize model names
    if 'model' in df.columns:
        df['model'] = df['model'].apply(_normalize_model)

    # Calculate MFE/MAE ratio
    df['mfe_mae_ratio'] = df.apply(
        lambda row: row['mfe_pct'] / row['mae_pct'] if row.get('mae_pct') and row['mae_pct'] > 0 else None,
        axis=1
    )

    return df


# =============================================================================
# PART 1: SUMMARY STATISTICS
# =============================================================================
def calculate_options_mfe_mae_summary(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate core OPTIONS MFE/MAE statistics using percentage-based analysis.

    Parameters:
    -----------
    data : List[Dict[str, Any]]
        List of records from op_mfe_mae_potential table

    Returns:
    --------
    Dict[str, Any]
        Dictionary containing all MFE/MAE statistics for options
    """
    empty_result = {
        "median_mfe_pct": 0.0,
        "median_mae_pct": 0.0,
        "mean_mfe_pct": 0.0,
        "mean_mae_pct": 0.0,
        "mfe_pct_q25": 0.0,
        "mfe_pct_q75": 0.0,
        "mae_pct_q25": 0.0,
        "mae_pct_q75": 0.0,
        "median_mfe_mae_ratio": 0.0,
        "median_exit_pct": 0.0,
        "pct_mfe_above_25": 0.0,
        "pct_mfe_above_50": 0.0,
        "pct_mae_below_25": 0.0,
        "total_trades": 0
    }

    if not data:
        return empty_result

    df = _prepare_options_dataframe(data)

    if df.empty or 'mfe_pct' not in df.columns or 'mae_pct' not in df.columns:
        return empty_result

    df_valid = df.dropna(subset=['mfe_pct', 'mae_pct'])

    if df_valid.empty:
        return empty_result

    total_trades = len(df_valid)

    # MFE statistics
    mfe_pct = df_valid['mfe_pct']
    median_mfe_pct = mfe_pct.quantile(0.5)
    mean_mfe_pct = mfe_pct.mean()
    mfe_pct_q25 = mfe_pct.quantile(0.25)
    mfe_pct_q75 = mfe_pct.quantile(0.75)

    # MAE statistics
    mae_pct = df_valid['mae_pct']
    median_mae_pct = mae_pct.quantile(0.5)
    mean_mae_pct = mae_pct.mean()
    mae_pct_q25 = mae_pct.quantile(0.25)
    mae_pct_q75 = mae_pct.quantile(0.75)

    # Exit statistics
    exit_pct = df_valid['exit_pct'] if 'exit_pct' in df_valid.columns else pd.Series([0])
    median_exit_pct = exit_pct.quantile(0.5)

    # MFE/MAE ratio
    ratio_valid = df_valid['mfe_mae_ratio'].dropna()
    median_ratio = ratio_valid.quantile(0.5) if len(ratio_valid) > 0 else 0.0

    # Threshold analysis (options move bigger than underlying, so 25% and 50%)
    pct_mfe_above_25 = (mfe_pct >= 25.0).mean() * 100
    pct_mfe_above_50 = (mfe_pct >= 50.0).mean() * 100
    pct_mae_below_25 = (mae_pct <= 25.0).mean() * 100

    return {
        "median_mfe_pct": float(median_mfe_pct),
        "median_mae_pct": float(median_mae_pct),
        "mean_mfe_pct": float(mean_mfe_pct),
        "mean_mae_pct": float(mean_mae_pct),
        "mfe_pct_q25": float(mfe_pct_q25),
        "mfe_pct_q75": float(mfe_pct_q75),
        "mae_pct_q25": float(mae_pct_q25),
        "mae_pct_q75": float(mae_pct_q75),
        "median_mfe_mae_ratio": float(median_ratio),
        "median_exit_pct": float(median_exit_pct),
        "pct_mfe_above_25": float(pct_mfe_above_25),
        "pct_mfe_above_50": float(pct_mfe_above_50),
        "pct_mae_below_25": float(pct_mae_below_25),
        "total_trades": int(total_trades)
    }


# =============================================================================
# PART 2: MODEL COMPARISON
# =============================================================================
def calculate_options_mfe_mae_by_model(data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Group OPTIONS MFE/MAE statistics by model AND contract type.

    Parameters:
    -----------
    data : List[Dict[str, Any]]
        List of records from op_mfe_mae_potential table

    Returns:
    --------
    pd.DataFrame
        Statistics grouped by model and contract type
    """
    df = _prepare_options_dataframe(data)

    if df.empty or 'model' not in df.columns:
        return pd.DataFrame(columns=[
            'Model', 'Contract', 'Trades', 'Med MFE%', 'Med MAE%',
            'MAE P75%', 'MFE/MAE Ratio'
        ])

    results = []

    for model in MODELS:
        for contract in ['CALL', 'PUT']:
            if 'contract_type' in df.columns:
                mask = (df['model'] == model) & (df['contract_type'].str.upper() == contract)
            else:
                mask = (df['model'] == model)

            model_df = df[mask]

            if len(model_df) == 0:
                continue

            trade_count = len(model_df)
            mfe_pct = model_df['mfe_pct'].dropna()
            mae_pct = model_df['mae_pct'].dropna()

            median_mfe = mfe_pct.quantile(0.5) if len(mfe_pct) > 0 else 0.0
            median_mae = mae_pct.quantile(0.5) if len(mae_pct) > 0 else 0.0
            mae_p75 = mae_pct.quantile(0.75) if len(mae_pct) > 0 else 0.0

            ratio_valid = model_df['mfe_mae_ratio'].dropna()
            median_ratio = ratio_valid.quantile(0.5) if len(ratio_valid) > 0 else 0.0

            results.append({
                'Model': model,
                'Contract': contract,
                'Trades': trade_count,
                'Med MFE%': round(median_mfe, 1),
                'Med MAE%': round(median_mae, 1),
                'MAE P75%': round(mae_p75, 1),
                'MFE/MAE Ratio': round(median_ratio, 2)
            })

    return pd.DataFrame(results)


# =============================================================================
# STREAMLIT DISPLAY FUNCTIONS
# =============================================================================
def render_options_mfe_mae_summary_cards(stats: Dict[str, Any]) -> None:
    """Display summary statistics as Streamlit metric cards."""
    if not stats or stats.get('total_trades', 0) == 0:
        st.info("No options data available for MFE/MAE analysis")
        return

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Median MFE",
            f"{stats['median_mfe_pct']:.1f}%",
            help="Typical max favorable movement for options"
        )
    with col2:
        st.metric(
            "Median MAE",
            f"{stats['median_mae_pct']:.1f}%",
            help="Typical max adverse movement for options"
        )
    with col3:
        st.metric(
            "MFE/MAE Ratio",
            f"{stats['median_mfe_mae_ratio']:.2f}",
            help="Favorable vs adverse movement (higher = better)"
        )
    with col4:
        st.metric(
            "Options Trades",
            f"{stats['total_trades']:,}",
            help="Total options trades analyzed"
        )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Median Exit",
            f"{stats['median_exit_pct']:.1f}%",
            help="Typical P/L at 15:30 ET"
        )
    with col2:
        st.metric(
            "MFE > 25%",
            f"{stats['pct_mfe_above_25']:.1f}%",
            help="Trades reaching 25% favorable move"
        )
    with col3:
        st.metric(
            "MFE > 50%",
            f"{stats['pct_mfe_above_50']:.1f}%",
            help="Trades reaching 50% favorable move"
        )
    with col4:
        st.metric(
            "MAE Range",
            f"{stats['mae_pct_q25']:.1f}% - {stats['mae_pct_q75']:.1f}%",
            help="25th to 75th percentile MAE"
        )


def render_options_mfe_histogram(data: List[Dict[str, Any]]) -> None:
    """Display OPTIONS MFE distribution as a histogram."""
    df = _prepare_options_dataframe(data)

    if df.empty or 'mfe_pct' not in df.columns:
        st.info("No options MFE data available")
        return

    fig = px.histogram(
        df.dropna(subset=['mfe_pct']),
        x='mfe_pct',
        nbins=40,
        title='Options MFE Distribution (% from Entry to 15:30)',
        labels={'mfe_pct': 'MFE (% of entry price)'},
        color_discrete_sequence=[CHART_COLORS['mfe']]
    )

    # Add reference lines (options move bigger, so 25% and 50%)
    fig.add_vline(x=25, line_dash="dash", line_color="#2ECC71",
                  annotation_text="25%", annotation_position="top")
    fig.add_vline(x=50, line_dash="dash", line_color="#27AE60",
                  annotation_text="50%", annotation_position="top")
    fig.add_vline(x=100, line_dash="dash", line_color="#1E8449",
                  annotation_text="100%", annotation_position="top")

    fig.update_layout(
        paper_bgcolor=CHART_COLORS['paper'],
        plot_bgcolor=CHART_COLORS['background'],
        font=dict(color=CHART_COLORS['text']),
        height=400,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    fig.update_xaxes(title="MFE (% of entry)", gridcolor=CHART_COLORS['grid'])
    fig.update_yaxes(title="Number of Trades", gridcolor=CHART_COLORS['grid'])

    st.plotly_chart(fig, use_container_width=True)


def render_options_mae_histogram(data: List[Dict[str, Any]]) -> None:
    """Display OPTIONS MAE distribution as a histogram."""
    df = _prepare_options_dataframe(data)

    if df.empty or 'mae_pct' not in df.columns:
        st.info("No options MAE data available")
        return

    fig = px.histogram(
        df.dropna(subset=['mae_pct']),
        x='mae_pct',
        nbins=40,
        title='Options MAE Distribution (% from Entry to 15:30)',
        labels={'mae_pct': 'MAE (% of entry price)'},
        color_discrete_sequence=[CHART_COLORS['mae']]
    )

    # Add reference lines
    fig.add_vline(x=10, line_dash="dash", line_color="#F39C12",
                  annotation_text="10%", annotation_position="top")
    fig.add_vline(x=25, line_dash="dash", line_color="#E67E22",
                  annotation_text="25%", annotation_position="top")
    fig.add_vline(x=50, line_dash="dash", line_color="#E74C3C",
                  annotation_text="50%", annotation_position="top")

    fig.update_layout(
        paper_bgcolor=CHART_COLORS['paper'],
        plot_bgcolor=CHART_COLORS['background'],
        font=dict(color=CHART_COLORS['text']),
        height=400,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    fig.update_xaxes(title="MAE (% of entry)", gridcolor=CHART_COLORS['grid'])
    fig.update_yaxes(title="Number of Trades", gridcolor=CHART_COLORS['grid'])

    st.plotly_chart(fig, use_container_width=True)


def render_options_mfe_mae_scatter(data: List[Dict[str, Any]]) -> None:
    """Display OPTIONS MFE vs MAE scatter plot."""
    df = _prepare_options_dataframe(data)

    if df.empty or 'mfe_pct' not in df.columns or 'mae_pct' not in df.columns:
        st.info("No options MFE/MAE data available for scatter plot")
        return

    scatter_df = df.dropna(subset=['mfe_pct', 'mae_pct'])

    if scatter_df.empty:
        st.info("No options MFE/MAE data available for scatter plot")
        return

    color_col = 'contract_type' if 'contract_type' in scatter_df.columns else 'model'

    fig = px.scatter(
        scatter_df,
        x='mae_pct',
        y='mfe_pct',
        color=color_col,
        title='Options MFE vs MAE (Entry to 15:30)',
        labels={
            'mae_pct': 'MAE (% adverse from entry)',
            'mfe_pct': 'MFE (% favorable from entry)'
        },
        hover_data=['ticker', 'model'] if 'ticker' in scatter_df.columns else None
    )

    # Add diagonal line (MFE = MAE)
    max_val = max(scatter_df['mae_pct'].max(), scatter_df['mfe_pct'].max())
    fig.add_shape(
        type='line',
        x0=0, y0=0, x1=max_val, y1=max_val,
        line=dict(color='gray', dash='dot', width=1)
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


def render_options_model_mfe_mae_table(data: List[Dict[str, Any]]) -> None:
    """Display OPTIONS MFE/MAE statistics by model and contract type as a table."""
    model_stats = calculate_options_mfe_mae_by_model(data)

    if model_stats.empty:
        st.info("No options model data available")
        return

    st.dataframe(model_stats, use_container_width=True, hide_index=True)


def render_options_trade_management_analysis(data: List[Dict[str, Any]]) -> None:
    """Render the complete OPTIONS MFE/MAE trade management analysis."""
    st.subheader("Options MFE/MAE Distribution Analysis")
    st.markdown("*Options price movement analysis from entry to 15:30 ET (percentage-based)*")

    stats = calculate_options_mfe_mae_summary(data)
    render_options_mfe_mae_summary_cards(stats)

    st.markdown("---")

    # Histograms side by side
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Options MFE Distribution (Favorable Movement)**")
        render_options_mfe_histogram(data)

    with col2:
        st.markdown("**Options MAE Distribution (Adverse Movement)**")
        render_options_mae_histogram(data)

    st.markdown("---")

    # Scatter plot (full width)
    st.markdown("**Options MFE vs MAE Scatter (Above diagonal = favorable)**")
    render_options_mfe_mae_scatter(data)

    st.markdown("---")

    # Model breakdown table
    st.markdown("**Options MFE/MAE by Model and Contract Type**")
    render_options_model_mfe_mae_table(data)


# =============================================================================
# EXAMPLE USAGE (for testing)
# =============================================================================
if __name__ == "__main__":
    sample_data = [
        {
            "trade_id": "T1",
            "date": "2025-12-15",
            "ticker": "SPY",
            "model": "EPCH02",
            "contract_type": "CALL",
            "option_entry_price": 5.00,
            "mfe_pct": 45.0,
            "mae_pct": 12.0,
            "exit_pct": 25.0,
        },
        {
            "trade_id": "T2",
            "date": "2025-12-15",
            "ticker": "SPY",
            "model": "EPCH02",
            "contract_type": "CALL",
            "option_entry_price": 4.50,
            "mfe_pct": 22.0,
            "mae_pct": 35.0,
            "exit_pct": -18.0,
        },
        {
            "trade_id": "T3",
            "date": "2025-12-16",
            "ticker": "QQQ",
            "model": "EPCH04",
            "contract_type": "PUT",
            "option_entry_price": 3.00,
            "mfe_pct": 80.0,
            "mae_pct": 8.0,
            "exit_pct": 55.0,
        },
    ]

    print("\nOptions MFE/MAE Summary Statistics (Percentage-Based):")
    print("=" * 60)
    stats = calculate_options_mfe_mae_summary(sample_data)
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")

    print("\n\nModel + Contract Type Breakdown:")
    print("=" * 60)
    model_stats = calculate_options_mfe_mae_by_model(sample_data)
    print(model_stats.to_string(index=False))
