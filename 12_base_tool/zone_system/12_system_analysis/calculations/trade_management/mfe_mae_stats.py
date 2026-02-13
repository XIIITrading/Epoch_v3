"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Calculation: MFE/MAE Distribution Analysis (CALC-002)
XIII Trading LLC
================================================================================

PURPOSE:
    Analyze trade behavior through Maximum Favorable Excursion (MFE) and
    Maximum Adverse Excursion (MAE) from entry to end-of-day (15:30 ET).

    Uses PERCENTAGE-BASED analysis (not R-values) to inform stop placement
    research without dependency on arbitrary stop levels.

DATA SOURCE:
    This module uses the `mfe_mae_potential` table EXCLUSIVELY.

    Key columns:
    - entry_price: Trade entry price
    - mfe_potential_price: Price at maximum favorable excursion
    - mae_potential_price: Price at maximum adverse excursion
    - direction: LONG or SHORT
    - model: EPCH01-04

METRICS CALCULATED:
    - MFE %: Maximum favorable movement as % of entry price
    - MAE %: Maximum adverse movement as % of entry price
    - MFE/MAE Ratio: Favorable vs adverse movement (higher = better)
    - Distribution percentiles for stop placement research

USAGE:
    from calculations.trade_management.mfe_mae_stats import (
        calculate_mfe_mae_summary,
        calculate_mfe_mae_by_model,
        render_mfe_mae_summary_cards,
        render_mfe_histogram,
        render_mae_histogram,
        render_mfe_mae_scatter,
        render_model_mfe_mae_table
    )

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

PCT_THRESHOLDS = {
    "small_move": 0.25,   # 0.25% move
    "medium_move": 0.50,  # 0.50% move
    "large_move": 1.00,   # 1.00% move
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


def _calc_mfe_pct(row) -> Optional[float]:
    """Calculate MFE as percentage of entry price."""
    entry = row.get('entry_price')
    mfe_price = row.get('mfe_potential_price')
    direction = row.get('direction', '').upper()

    if not entry or not mfe_price or entry == 0:
        return None

    if direction == 'LONG':
        return (mfe_price - entry) / entry * 100
    elif direction == 'SHORT':
        return (entry - mfe_price) / entry * 100
    return None


def _calc_mae_pct(row) -> Optional[float]:
    """Calculate MAE as percentage of entry price."""
    entry = row.get('entry_price')
    mae_price = row.get('mae_potential_price')
    direction = row.get('direction', '').upper()

    if not entry or not mae_price or entry == 0:
        return None

    if direction == 'LONG':
        return (entry - mae_price) / entry * 100
    elif direction == 'SHORT':
        return (mae_price - entry) / entry * 100
    return None


def _prepare_dataframe(data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Prepare DataFrame from mfe_mae_potential data.

    Calculates MFE/MAE as percentage of entry price.

    Parameters:
    -----------
    data : List[Dict[str, Any]]
        List of records from mfe_mae_potential table

    Returns:
    --------
    pd.DataFrame
        DataFrame with mfe_pct, mae_pct, and mfe_mae_ratio columns
    """
    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    # Convert Decimal columns to float
    numeric_cols = ['entry_price', 'mfe_potential_price', 'mae_potential_price']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].apply(_safe_float)

    # Normalize model names (EPCH1 -> EPCH01, etc.)
    if 'model' in df.columns:
        df['model'] = df['model'].apply(_normalize_model)

    # Calculate MFE/MAE as percentage of entry price
    df['mfe_pct'] = df.apply(lambda row: _calc_mfe_pct(row), axis=1)
    df['mae_pct'] = df.apply(lambda row: _calc_mae_pct(row), axis=1)

    # Calculate MFE/MAE ratio
    df['mfe_mae_ratio'] = df.apply(
        lambda row: row['mfe_pct'] / row['mae_pct'] if row['mae_pct'] and row['mae_pct'] > 0 else None,
        axis=1
    )

    return df


# =============================================================================
# PART 1: SUMMARY STATISTICS
# =============================================================================
def calculate_mfe_mae_summary(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate core MFE/MAE statistics using percentage-based analysis.

    No R-values or winner/loser analysis - pure price movement statistics.

    Parameters:
    -----------
    data : List[Dict[str, Any]]
        List of records from mfe_mae_potential table
        Required columns: entry_price, mfe_potential_price, mae_potential_price, direction

    Returns:
    --------
    Dict[str, Any]
        Dictionary containing all MFE/MAE statistics
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
        "pct_mfe_above_0_5": 0.0,  # % trades with MFE > 0.5%
        "pct_mfe_above_1_0": 0.0,  # % trades with MFE > 1.0%
        "pct_mae_below_0_5": 0.0,  # % trades with MAE < 0.5%
        "total_trades": 0
    }

    if not data:
        return empty_result

    df = _prepare_dataframe(data)

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

    # MFE/MAE ratio
    ratio_valid = df_valid['mfe_mae_ratio'].dropna()
    median_ratio = ratio_valid.quantile(0.5) if len(ratio_valid) > 0 else 0.0

    # Threshold analysis
    pct_mfe_above_0_5 = (mfe_pct >= 0.5).mean() * 100
    pct_mfe_above_1_0 = (mfe_pct >= 1.0).mean() * 100
    pct_mae_below_0_5 = (mae_pct <= 0.5).mean() * 100

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
        "pct_mfe_above_0_5": float(pct_mfe_above_0_5),
        "pct_mfe_above_1_0": float(pct_mfe_above_1_0),
        "pct_mae_below_0_5": float(pct_mae_below_0_5),
        "total_trades": int(total_trades)
    }


# =============================================================================
# PART 2: MODEL COMPARISON
# =============================================================================
def calculate_mfe_mae_by_model(data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Group MFE/MAE statistics by model AND direction.

    Uses percentage-based analysis for stop placement research.

    Parameters:
    -----------
    data : List[Dict[str, Any]]
        List of records from mfe_mae_potential table

    Returns:
    --------
    pd.DataFrame
        Statistics grouped by model and direction
    """
    df = _prepare_dataframe(data)

    if df.empty or 'model' not in df.columns:
        return pd.DataFrame(columns=[
            'Model', 'Direction', 'Trades', 'Med MFE%', 'Med MAE%',
            'MAE P75%', 'MFE/MAE Ratio'
        ])

    results = []

    for model in MODELS:
        for direction in ['LONG', 'SHORT']:
            mask = (df['model'] == model) & (df['direction'].str.upper() == direction)
            model_df = df[mask]

            if len(model_df) == 0:
                continue

            trade_count = len(model_df)
            mfe_pct = model_df['mfe_pct'].dropna()
            mae_pct = model_df['mae_pct'].dropna()

            median_mfe = mfe_pct.quantile(0.5) if len(mfe_pct) > 0 else 0.0
            median_mae = mae_pct.quantile(0.5) if len(mae_pct) > 0 else 0.0
            mae_p75 = mae_pct.quantile(0.75) if len(mae_pct) > 0 else 0.0

            # MFE/MAE ratio
            ratio_valid = model_df['mfe_mae_ratio'].dropna()
            median_ratio = ratio_valid.quantile(0.5) if len(ratio_valid) > 0 else 0.0

            results.append({
                'Model': model,
                'Direction': direction,
                'Trades': trade_count,
                'Med MFE%': round(median_mfe, 3),
                'Med MAE%': round(median_mae, 3),
                'MAE P75%': round(mae_p75, 3),
                'MFE/MAE Ratio': round(median_ratio, 2)
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
        st.metric(
            "Median MFE",
            f"{stats['median_mfe_pct']:.2f}%",
            help="Typical max favorable movement from entry"
        )
    with col2:
        st.metric(
            "Median MAE",
            f"{stats['median_mae_pct']:.2f}%",
            help="Typical max adverse movement from entry"
        )
    with col3:
        st.metric(
            "MFE/MAE Ratio",
            f"{stats['median_mfe_mae_ratio']:.2f}",
            help="Favorable vs adverse movement (higher = better)"
        )
    with col4:
        st.metric(
            "Trades",
            f"{stats['total_trades']:,}",
            help="Total trades analyzed"
        )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "MFE > 0.5%",
            f"{stats['pct_mfe_above_0_5']:.1f}%",
            help="Trades reaching 0.5% favorable move"
        )
    with col2:
        st.metric(
            "MFE > 1.0%",
            f"{stats['pct_mfe_above_1_0']:.1f}%",
            help="Trades reaching 1.0% favorable move"
        )
    with col3:
        st.metric(
            "MAE < 0.5%",
            f"{stats['pct_mae_below_0_5']:.1f}%",
            help="Trades with less than 0.5% adverse move"
        )
    with col4:
        st.metric(
            "MAE Range",
            f"{stats['mae_pct_q25']:.2f}% - {stats['mae_pct_q75']:.2f}%",
            help="25th to 75th percentile MAE"
        )


def render_mfe_histogram(data: List[Dict[str, Any]]) -> None:
    """Display MFE distribution as a histogram (percentage-based)."""
    df = _prepare_dataframe(data)

    if df.empty or 'mfe_pct' not in df.columns:
        st.info("No MFE data available")
        return

    fig = px.histogram(
        df.dropna(subset=['mfe_pct']),
        x='mfe_pct',
        nbins=40,
        title='MFE Distribution (% from Entry to 15:30)',
        labels={'mfe_pct': 'MFE (% of entry price)'},
        color_discrete_sequence=[CHART_COLORS['mfe']]
    )

    # Add reference lines
    fig.add_vline(x=0.5, line_dash="dash", line_color="#2ECC71",
                  annotation_text="0.5%", annotation_position="top")
    fig.add_vline(x=1.0, line_dash="dash", line_color="#27AE60",
                  annotation_text="1.0%", annotation_position="top")

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


def render_mae_histogram(data: List[Dict[str, Any]]) -> None:
    """Display MAE distribution as a histogram (percentage-based)."""
    df = _prepare_dataframe(data)

    if df.empty or 'mae_pct' not in df.columns:
        st.info("No MAE data available")
        return

    fig = px.histogram(
        df.dropna(subset=['mae_pct']),
        x='mae_pct',
        nbins=40,
        title='MAE Distribution (% from Entry to 15:30)',
        labels={'mae_pct': 'MAE (% of entry price)'},
        color_discrete_sequence=[CHART_COLORS['mae']]
    )

    # Add reference lines for potential stop levels
    fig.add_vline(x=0.25, line_dash="dash", line_color="#F39C12",
                  annotation_text="0.25%", annotation_position="top")
    fig.add_vline(x=0.50, line_dash="dash", line_color="#E67E22",
                  annotation_text="0.50%", annotation_position="top")
    fig.add_vline(x=1.0, line_dash="dash", line_color="#E74C3C",
                  annotation_text="1.0%", annotation_position="top")

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


def render_mfe_mae_scatter(data: List[Dict[str, Any]]) -> None:
    """Display MFE vs MAE scatter plot (percentage-based, colored by model)."""
    df = _prepare_dataframe(data)

    if df.empty or 'mfe_pct' not in df.columns or 'mae_pct' not in df.columns:
        st.info("No MFE/MAE data available for scatter plot")
        return

    scatter_df = df.dropna(subset=['mfe_pct', 'mae_pct'])

    if scatter_df.empty:
        st.info("No MFE/MAE data available for scatter plot")
        return

    hover_cols = ['ticker', 'direction'] if 'ticker' in scatter_df.columns else None

    fig = px.scatter(
        scatter_df,
        x='mae_pct',
        y='mfe_pct',
        color='model',
        title='MFE vs MAE by Model (Entry to 15:30)',
        labels={
            'mae_pct': 'MAE (% adverse from entry)',
            'mfe_pct': 'MFE (% favorable from entry)'
        },
        hover_data=hover_cols
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


def render_model_mfe_mae_table(data: List[Dict[str, Any]]) -> None:
    """Display MFE/MAE statistics by model and direction as a table."""
    model_stats = calculate_mfe_mae_by_model(data)

    if model_stats.empty:
        st.info("No model data available")
        return

    st.dataframe(model_stats, use_container_width=True, hide_index=True)


def render_trade_management_analysis(data: List[Dict[str, Any]]) -> None:
    """Render the complete MFE/MAE trade management analysis."""
    st.subheader("MFE/MAE Distribution Analysis")
    st.markdown("*Price movement analysis from entry to 15:30 ET (percentage-based)*")

    stats = calculate_mfe_mae_summary(data)
    render_mfe_mae_summary_cards(stats)

    st.markdown("---")

    # Histograms side by side
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**MFE Distribution (Favorable Movement)**")
        render_mfe_histogram(data)

    with col2:
        st.markdown("**MAE Distribution (Adverse Movement)**")
        render_mae_histogram(data)

    st.markdown("---")

    # Scatter plot (full width)
    st.markdown("**MFE vs MAE Scatter (Above diagonal = favorable)**")
    render_mfe_mae_scatter(data)

    st.markdown("---")

    # Model breakdown table
    st.markdown("**MFE/MAE by Model and Direction**")
    render_model_mfe_mae_table(data)


# =============================================================================
# EXAMPLE USAGE (for testing)
# =============================================================================
if __name__ == "__main__":
    # Example mfe_mae_potential data with price-based columns
    sample_potential_data = [
        # Trade 1: LONG - price went up 1.5% then pulled back 0.3%
        {
            "trade_id": "T1",
            "date": "2025-12-15",
            "ticker": "SPY",
            "direction": "LONG",
            "model": "EPCH02",
            "entry_price": 450.00,
            "mfe_potential_price": 456.75,  # +1.5%
            "mae_potential_price": 448.65,  # -0.3%
        },
        # Trade 2: LONG - price pulled back 0.8% then recovered to +0.4%
        {
            "trade_id": "T2",
            "date": "2025-12-15",
            "ticker": "SPY",
            "direction": "LONG",
            "model": "EPCH02",
            "entry_price": 450.00,
            "mfe_potential_price": 451.80,  # +0.4%
            "mae_potential_price": 446.40,  # -0.8%
        },
        # Trade 3: SHORT - price dropped 2.0% then bounced 0.5%
        {
            "trade_id": "T3",
            "date": "2025-12-16",
            "ticker": "QQQ",
            "direction": "SHORT",
            "model": "EPCH04",
            "entry_price": 400.00,
            "mfe_potential_price": 392.00,  # +2.0% (favorable for short)
            "mae_potential_price": 402.00,  # -0.5% (adverse for short)
        },
        # Trade 4: LONG - tough trade, pulled back 1.2% then only got +0.3%
        {
            "trade_id": "T4",
            "date": "2025-12-16",
            "ticker": "QQQ",
            "direction": "LONG",
            "model": "EPCH01",
            "entry_price": 400.00,
            "mfe_potential_price": 401.20,  # +0.3%
            "mae_potential_price": 395.20,  # -1.2%
        },
    ]

    print("\nMFE/MAE Summary Statistics (Percentage-Based):")
    print("=" * 60)
    stats = calculate_mfe_mae_summary(sample_potential_data)
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.3f}")
        else:
            print(f"  {key}: {value}")

    print("\n\nModel + Direction Breakdown:")
    print("=" * 60)
    model_stats = calculate_mfe_mae_by_model(sample_potential_data)
    print(model_stats.to_string(index=False))
