"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Calculation: Options MFE/MAE Sequence Analysis (CALC-O03)
XIII Trading LLC
================================================================================

PURPOSE:
    Analyze the temporal sequence of MFE and MAE events for OPTIONS trades.
    Establishes probability distributions by model for Monte Carlo simulation.

    Core Question: "For options trades with EPCH0X entry conditions, what is the
    probability of favorable movement occurring before adverse movement?"

DATA SOURCE:
    This module uses the `op_mfe_mae_potential` table EXCLUSIVELY.

    Key columns:
    - entry_time: Trade entry timestamp (ET)
    - mfe_time: Timestamp when max favorable excursion occurred
    - mae_time: Timestamp when max adverse excursion occurred
    - contract_type: CALL or PUT
    - model: EPCH01-04

METRICS CALCULATED:
    - P(MFE First): Probability that MFE occurs before MAE
    - Time to MFE: Minutes from entry to maximum favorable excursion
    - Time to MAE: Minutes from entry to maximum adverse excursion
    - Time Delta: Difference between time-to-MAE and time-to-MFE
    - Monte Carlo parameters by model-contract combination

================================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from decimal import Decimal
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import json
from datetime import time as dt_time, datetime as dt_datetime, timedelta as dt_timedelta


# =============================================================================
# CONFIGURATION
# =============================================================================
MODELS = ["EPCH01", "EPCH02", "EPCH03", "EPCH04"]

CHART_COLORS = {
    "mfe_first": "#26a69a",
    "mae_first": "#ef5350",
    "call": "#26a69a",
    "put": "#ef5350",
    "background": "#1a1a2e",
    "paper": "#16213e",
    "text": "#e0e0e0",
    "grid": "#2a2a4e",
    "reference": "#ffc107"
}

MC_CONFIDENCE_THRESHOLDS = {
    "high": 200,
    "medium": 100,
    "low": 50
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


def _get_mc_confidence(n: int) -> str:
    """Determine Monte Carlo confidence rating based on sample size."""
    if n >= MC_CONFIDENCE_THRESHOLDS["high"]:
        return "HIGH"
    elif n >= MC_CONFIDENCE_THRESHOLDS["medium"]:
        return "MEDIUM"
    elif n >= MC_CONFIDENCE_THRESHOLDS["low"]:
        return "LOW"
    else:
        return "INSUFFICIENT"


def _time_to_minutes(time_val) -> Optional[float]:
    """Convert a time value to minutes from midnight."""
    if time_val is None:
        return None

    try:
        if isinstance(time_val, dt_timedelta):
            return time_val.total_seconds() / 60

        if isinstance(time_val, dt_time):
            return time_val.hour * 60 + time_val.minute + time_val.second / 60

        if isinstance(time_val, dt_datetime):
            return time_val.hour * 60 + time_val.minute + time_val.second / 60

        if hasattr(time_val, 'hour') and hasattr(time_val, 'minute'):
            return time_val.hour * 60 + time_val.minute + (time_val.second if hasattr(time_val, 'second') else 0) / 60

        if isinstance(time_val, str):
            try:
                parsed = pd.to_datetime(time_val)
                return parsed.hour * 60 + parsed.minute + parsed.second / 60
            except Exception:
                pass

        return None
    except Exception:
        return None


def _compare_times(mfe_time, mae_time) -> Optional[bool]:
    """Compare two time values to determine which occurred first."""
    mfe_minutes = _time_to_minutes(mfe_time)
    mae_minutes = _time_to_minutes(mae_time)

    if mfe_minutes is None or mae_minutes is None:
        return None

    return mfe_minutes < mae_minutes


# =============================================================================
# CORE CALCULATION FUNCTIONS
# =============================================================================
def calculate_time_to_mfe(df: pd.DataFrame) -> pd.Series:
    """Calculate minutes from entry to MFE for each options trade."""
    entry_minutes = df['entry_time'].apply(_time_to_minutes)
    mfe_minutes = df['mfe_time'].apply(_time_to_minutes)
    return mfe_minutes - entry_minutes


def calculate_time_to_mae(df: pd.DataFrame) -> pd.Series:
    """Calculate minutes from entry to MAE for each options trade."""
    entry_minutes = df['entry_time'].apply(_time_to_minutes)
    mae_minutes = df['mae_time'].apply(_time_to_minutes)
    return mae_minutes - entry_minutes


def calculate_options_sequence_summary(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate OPTIONS MFE/MAE sequence summary statistics.

    Returns unfiltered probability metrics for Monte Carlo baseline.

    Parameters:
    -----------
    data : List[Dict[str, Any]]
        List of records from op_mfe_mae_potential table

    Returns:
    --------
    Dict[str, Any]
        Dictionary containing sequence statistics
    """
    empty_result = {
        'mfe_first_rate': 0.0,
        'mfe_first_count': 0,
        'mae_first_count': 0,
        'median_time_to_mfe': 0.0,
        'median_time_to_mae': 0.0,
        'mean_time_to_mfe': 0.0,
        'mean_time_to_mae': 0.0,
        'median_time_delta': 0.0,
        'pct_mfe_under_30min': 0.0,
        'pct_mfe_under_60min': 0.0,
        'pct_mae_under_30min': 0.0,
        'total_trades': 0
    }

    if not data:
        return empty_result

    df = pd.DataFrame(data)

    required_cols = ['entry_time', 'mfe_time', 'mae_time']
    if not all(col in df.columns for col in required_cols):
        return empty_result

    if 'model' in df.columns:
        df['model'] = df['model'].apply(_normalize_model)

    try:
        df['time_to_mfe'] = calculate_time_to_mfe(df)
        df['time_to_mae'] = calculate_time_to_mae(df)
        df['time_delta'] = df['time_to_mae'] - df['time_to_mfe']

        df['mfe_first'] = df.apply(
            lambda row: _compare_times(row['mfe_time'], row['mae_time']),
            axis=1
        )

        df_valid = df.dropna(subset=['time_to_mfe', 'time_to_mae', 'mfe_first'])

        if df_valid.empty:
            return empty_result

        total_trades = len(df_valid)

        return {
            'mfe_first_rate': float(df_valid['mfe_first'].mean()),
            'mfe_first_count': int(df_valid['mfe_first'].sum()),
            'mae_first_count': int((~df_valid['mfe_first']).sum()),
            'median_time_to_mfe': float(df_valid['time_to_mfe'].median()),
            'median_time_to_mae': float(df_valid['time_to_mae'].median()),
            'mean_time_to_mfe': float(df_valid['time_to_mfe'].mean()),
            'mean_time_to_mae': float(df_valid['time_to_mae'].mean()),
            'median_time_delta': float(df_valid['time_delta'].median()),
            'pct_mfe_under_30min': float((df_valid['time_to_mfe'] <= 30).mean() * 100),
            'pct_mfe_under_60min': float((df_valid['time_to_mfe'] <= 60).mean() * 100),
            'pct_mae_under_30min': float((df_valid['time_to_mae'] <= 30).mean() * 100),
            'total_trades': int(total_trades)
        }
    except Exception:
        return empty_result


def calculate_options_sequence_by_model(data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Calculate OPTIONS sequence statistics grouped by Model and Contract Type.

    PRIMARY OUTPUT for Monte Carlo parameters.

    Parameters:
    -----------
    data : List[Dict[str, Any]]
        List of records from op_mfe_mae_potential table

    Returns:
    --------
    pd.DataFrame
        Statistics grouped by model and contract type
    """
    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    required_cols = ['entry_time', 'mfe_time', 'mae_time', 'model']
    if not all(col in df.columns for col in required_cols):
        return pd.DataFrame()

    df['model'] = df['model'].apply(_normalize_model)

    try:
        df['time_to_mfe'] = calculate_time_to_mfe(df)
        df['time_to_mae'] = calculate_time_to_mae(df)
        df['time_delta'] = df['time_to_mae'] - df['time_to_mfe']

        df['mfe_first'] = df.apply(
            lambda row: _compare_times(row['mfe_time'], row['mae_time']),
            axis=1
        )

        if 'contract_type' in df.columns:
            df['contract_type'] = df['contract_type'].str.upper()

        df_valid = df.dropna(subset=['time_to_mfe', 'time_to_mae', 'mfe_first'])

        if df_valid.empty:
            return pd.DataFrame()

        # Group by model and contract_type
        group_cols = ['model', 'contract_type'] if 'contract_type' in df_valid.columns else ['model']

        grouped = df_valid.groupby(group_cols).agg(
            n_trades=('trade_id', 'count') if 'trade_id' in df_valid.columns else ('entry_time', 'count'),
            p_mfe_first=('mfe_first', 'mean'),
            mfe_first_count=('mfe_first', 'sum'),
            median_time_mfe=('time_to_mfe', 'median'),
            median_time_mae=('time_to_mae', 'median'),
            mean_time_mfe=('time_to_mfe', 'mean'),
            mean_time_mae=('time_to_mae', 'mean'),
            median_time_delta=('time_delta', 'median'),
            std_time_mfe=('time_to_mfe', 'std'),
            std_time_mae=('time_to_mae', 'std')
        ).reset_index()

        # Monte Carlo confidence rating
        grouped['mc_confidence'] = grouped['n_trades'].apply(_get_mc_confidence)

        # Sort by p_mfe_first descending
        grouped = grouped.sort_values('p_mfe_first', ascending=False)

        return grouped

    except Exception:
        return pd.DataFrame()


def generate_options_monte_carlo_params(data: List[Dict[str, Any]]) -> Dict[str, Dict]:
    """
    Generate Monte Carlo simulation parameters for OPTIONS by model-contract.

    Parameters:
    -----------
    data : List[Dict[str, Any]]
        List of records from op_mfe_mae_potential table

    Returns:
    --------
    Dict[str, Dict]
        Dict keyed by "MODEL_CONTRACT" with simulation parameters
    """
    model_df = calculate_options_sequence_by_model(data)

    if model_df.empty:
        return {}

    params = {}
    for _, row in model_df.iterrows():
        if 'contract_type' in row:
            key = f"{row['model']}_{row['contract_type']}"
        else:
            key = f"{row['model']}"

        params[key] = {
            'p_win': round(float(row['p_mfe_first']), 4),
            'n_samples': int(row['n_trades']),
            'confidence': row['mc_confidence'],
            'time_to_mfe_median': round(float(row['median_time_mfe']), 1),
            'time_to_mfe_std': round(float(row['std_time_mfe']), 1) if pd.notna(row['std_time_mfe']) else 0,
            'time_to_mae_median': round(float(row['median_time_mae']), 1),
            'time_to_mae_std': round(float(row['std_time_mae']), 1) if pd.notna(row['std_time_mae']) else 0,
            'mfe_typically_first': bool(row['p_mfe_first'] > 0.5)
        }

    return params


# =============================================================================
# STREAMLIT DISPLAY FUNCTIONS
# =============================================================================
def render_options_sequence_summary_cards(summary: Dict[str, Any]) -> None:
    """Render 4 summary metric cards for options sequence analysis."""
    if not summary or summary.get('total_trades', 0) == 0:
        st.info("No options sequence data available for analysis")
        return

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="P(MFE First)",
            value=f"{summary['mfe_first_rate']:.1%}",
            help="Probability that favorable movement occurs before adverse"
        )

    with col2:
        st.metric(
            label="Median Time to MFE",
            value=f"{summary['median_time_to_mfe']:.0f} min",
            help="Typical time for max favorable excursion"
        )

    with col3:
        st.metric(
            label="Median Time to MAE",
            value=f"{summary['median_time_to_mae']:.0f} min",
            help="Typical time for max adverse excursion"
        )

    with col4:
        st.metric(
            label="Options Analyzed",
            value=f"{summary['total_trades']:,}",
            help="Total options trades in sample"
        )


def render_options_model_probability_table(df: pd.DataFrame) -> None:
    """Render the primary Monte Carlo probability table for options."""
    if df.empty:
        st.warning("No data available for probability table.")
        return

    display_df = df.copy()
    display_df['P(MFE First)'] = display_df['p_mfe_first'].apply(lambda x: f"{x:.1%}")
    display_df['Med Time MFE'] = display_df['median_time_mfe'].apply(lambda x: f"{x:.0f} min")
    display_df['Med Time MAE'] = display_df['median_time_mae'].apply(lambda x: f"{x:.0f} min")
    display_df['Time Delta'] = display_df['median_time_delta'].apply(lambda x: f"{x:+.0f} min")

    cols_to_show = ['model']
    if 'contract_type' in display_df.columns:
        cols_to_show.append('contract_type')
    cols_to_show.extend(['n_trades', 'P(MFE First)', 'Med Time MFE', 'Med Time MAE', 'Time Delta', 'mc_confidence'])

    display_df = display_df[cols_to_show]

    col_names = ['Model']
    if 'contract_type' in df.columns:
        col_names.append('Contract')
    col_names.extend(['Trades', 'P(MFE First)', 'Med Time MFE', 'Med Time MAE', 'Time Delta', 'MC Confidence'])
    display_df.columns = col_names

    st.dataframe(display_df, use_container_width=True, hide_index=True)


def render_options_model_probability_chart(df: pd.DataFrame) -> None:
    """Grouped bar chart showing P(MFE First) by Model-Contract."""
    if df.empty:
        st.warning("No data available for probability chart.")
        return

    try:
        color_col = 'contract_type' if 'contract_type' in df.columns else None

        fig = px.bar(
            df,
            x='model',
            y='p_mfe_first',
            color=color_col,
            barmode='group',
            title='Options P(MFE First) by Model and Contract - Monte Carlo Baseline',
            labels={
                'model': 'Entry Model',
                'p_mfe_first': 'P(MFE First)',
                'contract_type': 'Contract'
            },
            color_discrete_map={'CALL': CHART_COLORS['call'], 'PUT': CHART_COLORS['put']} if color_col else None
        )

        fig.update_layout(yaxis_tickformat='.0%')

        fig.add_hline(
            y=0.5,
            line_dash="dash",
            line_color=CHART_COLORS['reference'],
            annotation_text="50% (random)",
            annotation_position="right"
        )

        fig.update_layout(
            template='plotly_dark',
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

    except Exception as e:
        st.warning(f"Error rendering probability chart: {str(e)}")


def render_options_time_histogram(data: List[Dict[str, Any]], metric: str = 'mfe') -> None:
    """Render histogram of Time-to-MFE or Time-to-MAE distribution for options."""
    if not data:
        st.warning(f"No data available for {metric.upper()} histogram.")
        return

    df = pd.DataFrame(data)

    time_col = 'mfe_time' if metric == 'mfe' else 'mae_time'
    if 'entry_time' not in df.columns or time_col not in df.columns:
        st.warning(f"Missing required time columns for {metric.upper()} histogram.")
        return

    if 'model' in df.columns:
        df['model'] = df['model'].apply(_normalize_model)

    try:
        if metric == 'mfe':
            df['time_metric'] = calculate_time_to_mfe(df)
            title = 'Options Time to MFE Distribution'
        else:
            df['time_metric'] = calculate_time_to_mae(df)
            title = 'Options Time to MAE Distribution'

        df_valid = df.dropna(subset=['time_metric'])

        if df_valid.empty:
            st.warning(f"No valid time data for {metric.upper()} histogram.")
            return

        color_col = 'contract_type' if 'contract_type' in df_valid.columns else 'model'

        fig = px.histogram(
            df_valid,
            x='time_metric',
            color=color_col,
            nbins=24,
            title=title,
            labels={'time_metric': 'Minutes from Entry', 'count': 'Trade Count'},
            barmode='overlay',
            opacity=0.7
        )

        fig.add_vline(x=30, line_dash="dash", line_color=CHART_COLORS['reference'],
                      annotation_text="30 min")
        fig.add_vline(x=60, line_dash="dash", line_color="#ff9800",
                      annotation_text="60 min")

        fig.update_layout(
            template='plotly_dark',
            paper_bgcolor=CHART_COLORS['paper'],
            plot_bgcolor=CHART_COLORS['background'],
            font=dict(color=CHART_COLORS['text']),
            height=400,
            margin=dict(l=50, r=50, t=80, b=50)
        )
        fig.update_xaxes(gridcolor=CHART_COLORS['grid'])
        fig.update_yaxes(gridcolor=CHART_COLORS['grid'])

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.warning(f"Error rendering {metric.upper()} histogram: {str(e)}")


# =============================================================================
# MAIN SECTION RENDERER
# =============================================================================
def render_options_sequence_analysis_section(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Main entry point to render the complete CALC-O03 section.

    Parameters:
    -----------
    data : List[Dict[str, Any]]
        List of records from op_mfe_mae_potential table

    Returns:
    --------
    Dict[str, Any]
        The sequence summary statistics (for Monte AI integration)
    """
    st.subheader("Options MFE/MAE Sequence Analysis")
    st.markdown("*Monte Carlo Baseline - When does favorable/adverse movement occur for options?*")

    if not data:
        st.warning("No options MFE/MAE data available.")
        return {}

    df_check = pd.DataFrame(data)
    required_cols = ['entry_time', 'mfe_time', 'mae_time']

    missing_cols = [col for col in required_cols if col not in df_check.columns]
    if missing_cols:
        st.warning(f"Missing required columns: {missing_cols}")
        return {}

    # Calculate summaries
    summary = calculate_options_sequence_summary(data)
    model_df = calculate_options_sequence_by_model(data)

    # Summary cards
    render_options_sequence_summary_cards(summary)

    st.markdown("---")

    # Model probability chart
    render_options_model_probability_chart(model_df)

    # Model probability table
    st.markdown("#### Monte Carlo Parameters by Model-Contract")
    render_options_model_probability_table(model_df)

    st.markdown("---")

    # Time distribution section
    st.markdown("#### Time Distribution Analysis")
    col1, col2 = st.columns(2)

    with col1:
        render_options_time_histogram(data, 'mfe')

    with col2:
        render_options_time_histogram(data, 'mae')

    # Monte Carlo export section
    st.markdown("---")
    st.markdown("#### Monte Carlo Export")

    mc_params = generate_options_monte_carlo_params(data)

    if mc_params:
        with st.expander("View Monte Carlo Parameters (JSON)"):
            st.json(mc_params)

        mc_json = json.dumps(mc_params, indent=2)
        st.download_button(
            label="Download Options MC Parameters",
            data=mc_json,
            file_name="options_monte_carlo_params.json",
            mime="application/json"
        )

    return summary


# =============================================================================
# EXAMPLE USAGE (for testing)
# =============================================================================
if __name__ == "__main__":
    from datetime import datetime, timedelta

    base_time = datetime(2025, 12, 15, 9, 30)

    sample_data = [
        {
            "trade_id": "T1",
            "model": "EPCH02",
            "contract_type": "CALL",
            "entry_time": base_time,
            "mfe_time": base_time + timedelta(minutes=45),
            "mae_time": base_time + timedelta(minutes=120),
        },
        {
            "trade_id": "T2",
            "model": "EPCH02",
            "contract_type": "CALL",
            "entry_time": base_time,
            "mfe_time": base_time + timedelta(minutes=90),
            "mae_time": base_time + timedelta(minutes=20),
        },
        {
            "trade_id": "T3",
            "model": "EPCH04",
            "contract_type": "PUT",
            "entry_time": base_time,
            "mfe_time": base_time + timedelta(minutes=30),
            "mae_time": base_time + timedelta(minutes=150),
        },
    ]

    print("\nOptions MFE/MAE Sequence Summary Statistics:")
    print("=" * 60)
    summary = calculate_options_sequence_summary(sample_data)
    for key, value in summary.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.3f}")
        else:
            print(f"  {key}: {value}")

    print("\n\nModel + Contract Breakdown:")
    print("=" * 60)
    model_stats = calculate_options_sequence_by_model(sample_data)
    if not model_stats.empty:
        print(model_stats.to_string(index=False))

    print("\n\nMonte Carlo Parameters:")
    print("=" * 60)
    mc_params = generate_options_monte_carlo_params(sample_data)
    print(json.dumps(mc_params, indent=2))
