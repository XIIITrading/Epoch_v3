"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Calculation: MFE/MAE Distribution Analysis (CALC-002) - REFERENCE FILE
XIII Trading LLC
================================================================================

PURPOSE:
    Analyze trade management efficiency through Maximum Favorable Excursion (MFE)
    and Maximum Adverse Excursion (MAE) metrics. This analysis answers:

    1. Am I leaving money on the table? -> MFE Capture Ratio
    2. Are my stops too tight? -> Winner MAE distribution
    3. Are my stops too loose? -> Loser MAE distribution
    4. What's realistic profit potential? -> MFE distribution by model
    5. Do winners "look different" from losers? -> MFE vs MAE scatter pattern

DEFINITIONS:
    MFE (Max Favorable Excursion): The maximum profit a trade reached before exit
        - Always positive (how much profit was available)
        - Measured in R-multiples

    MAE (Max Adverse Excursion): The maximum drawdown a trade experienced
        - Always positive (how much heat was taken)
        - Measured in R-multiples

    MFE Capture Ratio: pnl_r / mfe_r
        - 1.0 = captured all available profit
        - < 1.0 = exited before max profit
        - > 1.0 = rare (continued past MFE point)

DATA STRUCTURE:
    This module works with optimal_trade data which has events per trade:
    - event_type: 'ENTRY', 'MFE', 'MAE', 'EXIT'
    - r_at_event: R-multiple at that event
    - win: 1 or 0 (trade outcome)
    - actual_r: Final P&L in R-multiples

USAGE:
    from calculations.trade_management.mfe_mae_stats import (
        calculate_mfe_mae_summary,
        render_mfe_mae_summary_cards,
        render_mfe_histogram,
        render_mae_histogram,
        render_mfe_mae_scatter,
        render_mfe_capture_histogram
    )

    # Get optimal_trade data with MFE/MAE events
    optimal_trades = load_optimal_trades(date_from, date_to, models, ['ENTRY', 'MFE', 'MAE', 'EXIT'])

    # Get the statistics
    stats = calculate_mfe_mae_summary(optimal_trades)

    # Display in Streamlit
    render_mfe_mae_summary_cards(stats)
    render_mfe_histogram(optimal_trades)

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
    "mfe": "#2E86AB",
    "mae": "#E94F37",
    "winner": "#2ECC71",
    "loser": "#E74C3C",
    "capture": "#9B59B6",
    "background": "#1a1a2e",
    "paper": "#16213e",
    "text": "#e0e0e0",
    "grid": "#2a2a4e"
}

R_THRESHOLDS = {
    "target_1r": 1.0,
    "target_2r": 2.0,
    "target_3r": 3.0,
    "heat_threshold": 0.5
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


def _pivot_optimal_trades(optimal_trades: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Pivot optimal_trade events to get one row per trade with mfe_r and mae_r columns.

    The optimal_trade table has multiple rows per trade (ENTRY, MFE, MAE, EXIT).
    This function pivots to create a single row per trade with:
    - trade_id
    - model
    - is_winner (from win column)
    - pnl_r (from actual_r)
    - mfe_r (from MFE event's r_at_event, made positive)
    - mae_r (from MAE event's r_at_event, made positive)

    Parameters:
    -----------
    optimal_trades : List[Dict[str, Any]]
        List of optimal_trade events from database

    Returns:
    --------
    pd.DataFrame
        One row per trade with mfe_r, mae_r, pnl_r columns
    """
    if not optimal_trades:
        return pd.DataFrame()

    df = pd.DataFrame(optimal_trades)

    # Convert Decimal columns to float
    for col in ['r_at_event', 'actual_r']:
        if col in df.columns:
            df[col] = df[col].apply(_safe_float)

    # Get MFE events (r_at_event is positive at MFE)
    mfe_events = df[df['event_type'] == 'MFE'][['trade_id', 'r_at_event']].copy()
    mfe_events = mfe_events.rename(columns={'r_at_event': 'mfe_r'})
    # MFE should be positive (it's the max favorable excursion)
    mfe_events['mfe_r'] = mfe_events['mfe_r'].abs()

    # Get MAE events (r_at_event is negative at MAE, we want positive)
    mae_events = df[df['event_type'] == 'MAE'][['trade_id', 'r_at_event']].copy()
    mae_events = mae_events.rename(columns={'r_at_event': 'mae_r'})
    # MAE should be positive (it's the max adverse excursion)
    mae_events['mae_r'] = mae_events['mae_r'].abs()

    # Get trade info from EXIT events (has actual_r and win)
    exit_events = df[df['event_type'] == 'EXIT'][['trade_id', 'model', 'win', 'actual_r']].copy()
    exit_events = exit_events.rename(columns={'actual_r': 'pnl_r', 'win': 'is_winner'})
    exit_events['is_winner'] = exit_events['is_winner'] == 1

    # If no EXIT events, try ENTRY events for model info
    if exit_events.empty:
        entry_events = df[df['event_type'] == 'ENTRY'][['trade_id', 'model', 'win', 'actual_r']].copy()
        entry_events = entry_events.rename(columns={'actual_r': 'pnl_r', 'win': 'is_winner'})
        entry_events['is_winner'] = entry_events['is_winner'] == 1
        exit_events = entry_events

    # Merge all together
    result = exit_events.merge(mfe_events, on='trade_id', how='left')
    result = result.merge(mae_events, on='trade_id', how='left')

    # Normalize model names
    if 'model' in result.columns:
        result['model'] = result['model'].apply(_normalize_model)

    # Create outcome column for display
    result['outcome'] = result['is_winner'].apply(lambda x: 'Winner' if x else 'Loser')

    return result


def _prepare_dataframe(data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Prepare DataFrame from optimal_trade data.

    Parameters:
    -----------
    data : List[Dict[str, Any]]
        List of optimal_trade events OR already pivoted trade data

    Returns:
    --------
    pd.DataFrame
        Prepared DataFrame with mfe_r, mae_r, pnl_r columns
    """
    if not data:
        return pd.DataFrame()

    # Check if this is optimal_trade data (has event_type) or already pivoted
    sample = data[0]
    if 'event_type' in sample:
        # This is optimal_trade data - needs pivoting
        return _pivot_optimal_trades(data)
    elif 'mfe_r' in sample and 'mae_r' in sample:
        # Already has mfe_r and mae_r columns
        df = pd.DataFrame(data)
        # Convert Decimal columns to float
        for col in ['mfe_r', 'mae_r', 'pnl_r']:
            if col in df.columns:
                df[col] = df[col].apply(_safe_float)
        if 'model' in df.columns:
            df['model'] = df['model'].apply(_normalize_model)
        if 'outcome' not in df.columns and 'is_winner' in df.columns:
            df['outcome'] = df['is_winner'].apply(lambda x: 'Winner' if x else 'Loser')
        return df
    else:
        # Unknown format
        return pd.DataFrame()


# =============================================================================
# PART 1: SUMMARY STATISTICS
# =============================================================================
def calculate_mfe_mae_summary(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate core MFE/MAE statistics from optimal_trade data.

    Parameters:
    -----------
    data : List[Dict[str, Any]]
        List of optimal_trade events from database (with ENTRY, MFE, MAE, EXIT events)

    Returns:
    --------
    Dict[str, Any]
        Dictionary containing all MFE/MAE statistics
    """
    # Default empty result
    empty_result = {
        "median_mfe": 0.0, "median_mae": 0.0,
        "mean_mfe": 0.0, "mean_mae": 0.0,
        "mfe_q25": 0.0, "mfe_q75": 0.0,
        "mae_q25": 0.0, "mae_q75": 0.0,
        "pct_reached_1r": 0.0, "pct_reached_2r": 0.0, "pct_reached_3r": 0.0,
        "pct_winners_with_heat": 0.0,
        "avg_mfe_capture": 0.0,
        "total_trades": 0, "total_winners": 0, "total_losers": 0
    }

    if not data:
        return empty_result

    # Prepare DataFrame (handles pivoting if needed)
    df = _prepare_dataframe(data)

    if df.empty or 'mfe_r' not in df.columns or 'mae_r' not in df.columns:
        return empty_result

    # Filter to rows with valid MFE/MAE data
    df_valid = df.dropna(subset=['mfe_r', 'mae_r'])

    if df_valid.empty:
        return empty_result

    # MFE statistics
    mfe_valid = df_valid['mfe_r']
    median_mfe = mfe_valid.quantile(0.5)
    mean_mfe = mfe_valid.mean()
    mfe_q25 = mfe_valid.quantile(0.25)
    mfe_q75 = mfe_valid.quantile(0.75)

    # MAE statistics
    mae_valid = df_valid['mae_r']
    median_mae = mae_valid.quantile(0.5)
    mean_mae = mae_valid.mean()
    mae_q25 = mae_valid.quantile(0.25)
    mae_q75 = mae_valid.quantile(0.75)

    # R-multiple achievement rates
    total_trades = len(df_valid)
    pct_reached_1r = (mfe_valid >= R_THRESHOLDS["target_1r"]).mean() * 100
    pct_reached_2r = (mfe_valid >= R_THRESHOLDS["target_2r"]).mean() * 100
    pct_reached_3r = (mfe_valid >= R_THRESHOLDS["target_3r"]).mean() * 100

    # Winner heat analysis
    if 'is_winner' in df_valid.columns:
        winners = df_valid[df_valid['is_winner'] == True]
        if len(winners) > 0:
            pct_winners_with_heat = (winners['mae_r'] >= R_THRESHOLDS["heat_threshold"]).mean() * 100
        else:
            pct_winners_with_heat = 0.0
        total_winners = int(df_valid['is_winner'].sum())
        total_losers = total_trades - total_winners
    else:
        pct_winners_with_heat = 0.0
        total_winners = 0
        total_losers = 0

    # MFE capture ratio (only for winners - you can only "capture" profit on winners)
    if 'pnl_r' in df_valid.columns and 'is_winner' in df_valid.columns:
        # Filter to winners with positive MFE
        winner_capture_mask = (df_valid['mfe_r'] > 0) & (df_valid['is_winner'] == True)
        if winner_capture_mask.sum() > 0:
            df_capture = df_valid.loc[winner_capture_mask].copy()
            df_capture['capture_ratio'] = df_capture['pnl_r'] / df_capture['mfe_r']
            avg_mfe_capture = df_capture['capture_ratio'].mean()
        else:
            avg_mfe_capture = 0.0
    else:
        avg_mfe_capture = 0.0

    return {
        "median_mfe": float(median_mfe),
        "median_mae": float(median_mae),
        "mean_mfe": float(mean_mfe),
        "mean_mae": float(mean_mae),
        "mfe_q25": float(mfe_q25),
        "mfe_q75": float(mfe_q75),
        "mae_q25": float(mae_q25),
        "mae_q75": float(mae_q75),
        "pct_reached_1r": float(pct_reached_1r),
        "pct_reached_2r": float(pct_reached_2r),
        "pct_reached_3r": float(pct_reached_3r),
        "pct_winners_with_heat": float(pct_winners_with_heat),
        "avg_mfe_capture": float(avg_mfe_capture),
        "total_trades": int(total_trades),
        "total_winners": int(total_winners),
        "total_losers": int(total_losers)
    }


# =============================================================================
# PART 2: DISTRIBUTION DATA
# =============================================================================
def get_mfe_distribution(data: List[Dict[str, Any]]) -> pd.Series:
    """Return MFE values for histogram plotting."""
    df = _prepare_dataframe(data)
    if df.empty or 'mfe_r' not in df.columns:
        return pd.Series(dtype=float)
    return df['mfe_r'].dropna()


def get_mae_distribution(data: List[Dict[str, Any]]) -> pd.Series:
    """Return MAE values for histogram plotting."""
    df = _prepare_dataframe(data)
    if df.empty or 'mae_r' not in df.columns:
        return pd.Series(dtype=float)
    return df['mae_r'].dropna()


# =============================================================================
# PART 3: SCATTER PLOT DATA
# =============================================================================
def get_mfe_mae_scatter_data(data: List[Dict[str, Any]]) -> pd.DataFrame:
    """Prepare data for MFE vs MAE scatter plot."""
    df = _prepare_dataframe(data)

    if df.empty:
        return pd.DataFrame(columns=['mae_r', 'mfe_r', 'outcome', 'pnl_r', 'mfe_mae_ratio'])

    # Calculate MFE/MAE ratio
    df['mfe_mae_ratio'] = df.apply(
        lambda row: row['mfe_r'] / row['mae_r'] if row['mae_r'] > 0 else None,
        axis=1
    )

    result_cols = ['mae_r', 'mfe_r', 'outcome']
    if 'pnl_r' in df.columns:
        result_cols.append('pnl_r')
    result_cols.append('mfe_mae_ratio')
    if 'model' in df.columns:
        result_cols.append('model')

    return df[result_cols].dropna(subset=['mae_r', 'mfe_r'])


# =============================================================================
# PART 4: MFE CAPTURE ANALYSIS
# =============================================================================
def calculate_mfe_capture(data: List[Dict[str, Any]]) -> pd.DataFrame:
    """Calculate MFE capture ratio for each trade."""
    df = _prepare_dataframe(data)

    if df.empty or 'mfe_r' not in df.columns or 'pnl_r' not in df.columns:
        return pd.DataFrame(columns=['model', 'outcome', 'mfe_r', 'pnl_r', 'mfe_capture'])

    df_valid = df[df['mfe_r'] > 0].copy()
    if df_valid.empty:
        return pd.DataFrame(columns=['model', 'outcome', 'mfe_r', 'pnl_r', 'mfe_capture'])

    df_valid['mfe_capture'] = df_valid['pnl_r'] / df_valid['mfe_r']

    result_cols = ['outcome', 'mfe_r', 'pnl_r', 'mfe_capture']
    if 'model' in df_valid.columns:
        result_cols.insert(0, 'model')

    return df_valid[result_cols]


# =============================================================================
# PART 5: MODEL COMPARISON
# =============================================================================
def calculate_mfe_mae_by_model(data: List[Dict[str, Any]]) -> pd.DataFrame:
    """Group MFE/MAE statistics by model."""
    df = _prepare_dataframe(data)

    if df.empty or 'model' not in df.columns:
        return pd.DataFrame(columns=[
            'Model', 'Trades', 'Med MFE', 'Med MAE', 'MFE Capture', '% Hit 1R', 'MFE/MAE'
        ])

    results = []
    for model in MODELS:
        model_df = df[df['model'] == model]
        if len(model_df) == 0:
            continue

        trade_count = len(model_df)
        mfe_valid = model_df['mfe_r'].dropna()
        mae_valid = model_df['mae_r'].dropna()

        median_mfe = mfe_valid.quantile(0.5) if len(mfe_valid) > 0 else 0.0
        median_mae = mae_valid.quantile(0.5) if len(mae_valid) > 0 else 0.0

        # MFE Capture (winners only)
        if 'pnl_r' in model_df.columns and 'is_winner' in model_df.columns:
            capture_mask = (model_df['mfe_r'] > 0) & (model_df['is_winner'] == True)
            if capture_mask.sum() > 0:
                capture_df = model_df.loc[capture_mask].copy()
                capture_df['capture'] = capture_df['pnl_r'] / capture_df['mfe_r']
                avg_capture = capture_df['capture'].mean()
            else:
                avg_capture = 0.0
        else:
            avg_capture = 0.0

        pct_1r = (mfe_valid >= 1.0).mean() * 100 if len(mfe_valid) > 0 else 0.0

        mfe_mae_valid = model_df[(model_df['mfe_r'].notna()) & (model_df['mae_r'] > 0)]
        if len(mfe_mae_valid) > 0:
            mfe_mae_ratio = (mfe_mae_valid['mfe_r'] / mfe_mae_valid['mae_r']).median()
        else:
            mfe_mae_ratio = 0.0

        results.append({
            'Model': model,
            'Trades': trade_count,
            'Med MFE': round(median_mfe, 2),
            'Med MAE': round(median_mae, 2),
            'MFE Capture': round(avg_capture, 2),
            '% Hit 1R': round(pct_1r, 1),
            'MFE/MAE': round(mfe_mae_ratio, 2)
        })

    return pd.DataFrame(results)


# =============================================================================
# STREAMLIT DISPLAY FUNCTIONS
# =============================================================================
def render_mfe_mae_summary_cards(stats: Dict[str, Any]) -> None:
    """Display summary statistics as Streamlit metric cards."""
    if not stats or stats.get('total_trades', 0) == 0:
        st.info("No trade data available for MFE/MAE analysis")
        return

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Median MFE", f"{stats['median_mfe']:.2f}R",
                  help="Typical max profit available per trade")
    with col2:
        st.metric("Median MAE", f"{stats['median_mae']:.2f}R",
                  help="Typical max heat taken per trade")
    with col3:
        st.metric("MFE Capture", f"{stats['avg_mfe_capture']:.0%}",
                  help="Average % of available profit captured")
    with col4:
        st.metric("Trades", f"{stats['total_trades']:,}",
                  help=f"Winners: {stats['total_winners']}, Losers: {stats['total_losers']}")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("% Hit 1R", f"{stats['pct_reached_1r']:.1f}%",
                  help="Trades that reached 1R profit at some point")
    with col2:
        st.metric("% Hit 2R", f"{stats['pct_reached_2r']:.1f}%",
                  help="Trades that reached 2R profit at some point")
    with col3:
        st.metric("% Hit 3R", f"{stats['pct_reached_3r']:.1f}%",
                  help="Trades that reached 3R profit at some point")
    with col4:
        st.metric("Winners w/ Heat", f"{stats['pct_winners_with_heat']:.1f}%",
                  help="Winners that took >0.5R drawdown")


def render_mfe_histogram(data: List[Dict[str, Any]]) -> None:
    """Display MFE distribution as a histogram."""
    df = _prepare_dataframe(data)

    if df.empty or 'mfe_r' not in df.columns:
        st.info("No MFE data available")
        return

    fig = px.histogram(
        df.dropna(subset=['mfe_r']),
        x='mfe_r',
        nbins=30,
        title='MFE Distribution (Max Favorable Excursion)',
        labels={'mfe_r': 'MFE (R-multiples)'},
        color_discrete_sequence=[CHART_COLORS['mfe']]
    )

    fig.add_vline(x=1.0, line_dash="dash", line_color="#2ECC71",
                  annotation_text="1R", annotation_position="top")
    fig.add_vline(x=2.0, line_dash="dash", line_color="#27AE60",
                  annotation_text="2R", annotation_position="top")
    fig.add_vline(x=3.0, line_dash="dash", line_color="#1E8449",
                  annotation_text="3R", annotation_position="top")

    fig.update_layout(
        paper_bgcolor=CHART_COLORS['paper'],
        plot_bgcolor=CHART_COLORS['background'],
        font=dict(color=CHART_COLORS['text']),
        height=400,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    fig.update_xaxes(title="MFE (R-multiples)", gridcolor=CHART_COLORS['grid'])
    fig.update_yaxes(title="Number of Trades", gridcolor=CHART_COLORS['grid'])

    st.plotly_chart(fig, use_container_width=True)


def render_mae_histogram(data: List[Dict[str, Any]]) -> None:
    """Display MAE distribution as a histogram."""
    df = _prepare_dataframe(data)

    if df.empty or 'mae_r' not in df.columns:
        st.info("No MAE data available")
        return

    fig = px.histogram(
        df.dropna(subset=['mae_r']),
        x='mae_r',
        nbins=30,
        title='MAE Distribution (Max Adverse Excursion)',
        labels={'mae_r': 'MAE (R-multiples)'},
        color_discrete_sequence=[CHART_COLORS['mae']]
    )

    fig.add_vline(x=0.5, line_dash="dash", line_color="#F39C12",
                  annotation_text="0.5R Heat", annotation_position="top")
    fig.add_vline(x=1.0, line_dash="dash", line_color="#E74C3C",
                  annotation_text="1R Stop", annotation_position="top")

    fig.update_layout(
        paper_bgcolor=CHART_COLORS['paper'],
        plot_bgcolor=CHART_COLORS['background'],
        font=dict(color=CHART_COLORS['text']),
        height=400,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    fig.update_xaxes(title="MAE (R-multiples)", gridcolor=CHART_COLORS['grid'])
    fig.update_yaxes(title="Number of Trades", gridcolor=CHART_COLORS['grid'])

    st.plotly_chart(fig, use_container_width=True)


def render_mfe_mae_scatter(data: List[Dict[str, Any]]) -> None:
    """Display MFE vs MAE scatter plot."""
    scatter_data = get_mfe_mae_scatter_data(data)

    if scatter_data.empty:
        st.info("No MFE/MAE data available for scatter plot")
        return

    fig = px.scatter(
        scatter_data,
        x='mae_r',
        y='mfe_r',
        color='outcome',
        color_discrete_map={
            'Winner': CHART_COLORS['winner'],
            'Loser': CHART_COLORS['loser']
        },
        title='MFE vs MAE by Trade Outcome',
        labels={
            'mae_r': 'MAE (Adverse Excursion in R)',
            'mfe_r': 'MFE (Favorable Excursion in R)'
        },
        hover_data=['pnl_r'] if 'pnl_r' in scatter_data.columns else None
    )

    max_val = max(scatter_data['mae_r'].max(), scatter_data['mfe_r'].max())
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


def render_mfe_capture_histogram(data: List[Dict[str, Any]]) -> None:
    """Display MFE capture ratio distribution."""
    capture_data = calculate_mfe_capture(data)

    if capture_data.empty:
        st.info("No capture ratio data available")
        return

    fig = px.histogram(
        capture_data,
        x='mfe_capture',
        nbins=40,
        title='MFE Capture Ratio Distribution',
        labels={'mfe_capture': 'Capture Ratio (Actual R / MFE R)'},
        color_discrete_sequence=[CHART_COLORS['capture']]
    )

    fig.add_vline(x=1.0, line_dash="dash", line_color="#2ECC71",
                  annotation_text="Perfect Capture", annotation_position="top")
    fig.add_vline(x=0.5, line_dash="dash", line_color="#F39C12",
                  annotation_text="50% Capture", annotation_position="top")

    fig.update_layout(
        paper_bgcolor=CHART_COLORS['paper'],
        plot_bgcolor=CHART_COLORS['background'],
        font=dict(color=CHART_COLORS['text']),
        height=400,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    fig.update_xaxes(title="Capture Ratio", gridcolor=CHART_COLORS['grid'])
    fig.update_yaxes(title="Number of Trades", gridcolor=CHART_COLORS['grid'])

    st.plotly_chart(fig, use_container_width=True)


def render_model_mfe_mae_table(data: List[Dict[str, Any]]) -> None:
    """Display MFE/MAE statistics by model as a table."""
    model_stats = calculate_mfe_mae_by_model(data)

    if model_stats.empty:
        st.info("No model data available")
        return

    st.dataframe(model_stats, use_container_width=True, hide_index=True)


def render_trade_management_analysis(data: List[Dict[str, Any]]) -> None:
    """Render the complete MFE/MAE trade management analysis."""
    st.subheader("MFE/MAE Distribution Analysis")
    st.markdown("*Trade management efficiency - are you capturing available profits?*")

    stats = calculate_mfe_mae_summary(data)
    render_mfe_mae_summary_cards(stats)

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**MFE Distribution (Profit Available)**")
        render_mfe_histogram(data)
    with col2:
        st.markdown("**MAE Distribution (Heat Taken)**")
        render_mae_histogram(data)

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**MFE vs MAE Scatter**")
        render_mfe_mae_scatter(data)
    with col2:
        st.markdown("**MFE Capture Distribution**")
        render_mfe_capture_histogram(data)

    st.markdown("---")

    st.markdown("**MFE/MAE by Model**")
    render_model_mfe_mae_table(data)


# =============================================================================
# EXAMPLE USAGE (for testing)
# =============================================================================
if __name__ == "__main__":
    # Example optimal_trade data (matching actual database structure)
    sample_optimal_trades = [
        # Trade 1: Winner
        {"trade_id": "T1", "event_type": "ENTRY", "model": "EPCH2", "win": 1, "actual_r": 1.5, "r_at_event": 0.0},
        {"trade_id": "T1", "event_type": "MFE", "model": "EPCH2", "win": 1, "actual_r": 1.5, "r_at_event": 2.0},
        {"trade_id": "T1", "event_type": "MAE", "model": "EPCH2", "win": 1, "actual_r": 1.5, "r_at_event": -0.3},
        {"trade_id": "T1", "event_type": "EXIT", "model": "EPCH2", "win": 1, "actual_r": 1.5, "r_at_event": 1.5},

        # Trade 2: Loser
        {"trade_id": "T2", "event_type": "ENTRY", "model": "EPCH2", "win": 0, "actual_r": -1.0, "r_at_event": 0.0},
        {"trade_id": "T2", "event_type": "MFE", "model": "EPCH2", "win": 0, "actual_r": -1.0, "r_at_event": 0.5},
        {"trade_id": "T2", "event_type": "MAE", "model": "EPCH2", "win": 0, "actual_r": -1.0, "r_at_event": -1.0},
        {"trade_id": "T2", "event_type": "EXIT", "model": "EPCH2", "win": 0, "actual_r": -1.0, "r_at_event": -1.0},

        # Trade 3: Winner
        {"trade_id": "T3", "event_type": "ENTRY", "model": "EPCH1", "win": 1, "actual_r": 2.0, "r_at_event": 0.0},
        {"trade_id": "T3", "event_type": "MFE", "model": "EPCH1", "win": 1, "actual_r": 2.0, "r_at_event": 2.5},
        {"trade_id": "T3", "event_type": "MAE", "model": "EPCH1", "win": 1, "actual_r": 2.0, "r_at_event": -0.2},
        {"trade_id": "T3", "event_type": "EXIT", "model": "EPCH1", "win": 1, "actual_r": 2.0, "r_at_event": 2.0},
    ]

    print("\nMFE/MAE Summary Statistics:")
    print("=" * 50)
    stats = calculate_mfe_mae_summary(sample_optimal_trades)
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")

    print("\n\nModel Breakdown:")
    print("=" * 50)
    model_stats = calculate_mfe_mae_by_model(sample_optimal_trades)
    print(model_stats.to_string(index=False))
