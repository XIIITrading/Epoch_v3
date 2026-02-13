"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Calculation: MFE/MAE Sequence Analysis (CALC-003)
XIII Trading LLC
================================================================================

PURPOSE:
    Analyze the temporal sequence of MFE and MAE events to establish
    unfiltered probability distributions by model for Monte Carlo simulation.

    Core Question: "Given that EPCH0X entry conditions were met, what is the
    probability of favorable movement occurring before adverse movement?"

DATA SOURCE:
    This module uses the `mfe_mae_potential` table EXCLUSIVELY.

    Key columns:
    - entry_time: Trade entry timestamp (ET)
    - mfe_potential_time: Timestamp when max favorable excursion occurred
    - mae_potential_time: Timestamp when max adverse excursion occurred
    - direction: LONG or SHORT
    - model: EPCH01-04

METRICS CALCULATED:
    - P(MFE First): Probability that MFE occurs before MAE
    - Time to MFE: Minutes from entry to maximum favorable excursion
    - Time to MAE: Minutes from entry to maximum adverse excursion
    - Time Delta: Difference between time-to-MAE and time-to-MFE
    - Monte Carlo parameters by model-direction combination

USAGE:
    from calculations.trade_management.mfe_mae_sequence import (
        calculate_sequence_summary,
        calculate_sequence_by_model,
        generate_monte_carlo_params,
        render_sequence_analysis_section
    )

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


# =============================================================================
# CONFIGURATION
# =============================================================================
MODELS = ["EPCH01", "EPCH02", "EPCH03", "EPCH04"]

CHART_COLORS = {
    "mfe_first": "#26a69a",      # Teal green - favorable
    "mae_first": "#ef5350",      # Red - unfavorable
    "long": "#26a69a",           # Teal green (matches win color)
    "short": "#ef5350",          # Red (matches loss color)
    "background": "#1a1a2e",
    "paper": "#16213e",
    "text": "#e0e0e0",
    "grid": "#2a2a4e",
    "reference": "#ffc107"       # Yellow for reference lines
}

# Monte Carlo confidence thresholds
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


# =============================================================================
# CORE CALCULATION FUNCTIONS
# =============================================================================
def _time_to_minutes(time_val) -> Optional[float]:
    """
    Convert a time value to minutes from midnight.

    Handles:
    - datetime.time objects
    - datetime.timedelta objects (from psycopg2)
    - datetime.datetime objects
    - String representations

    Parameters:
    -----------
    time_val : various
        Time value in various formats

    Returns:
    --------
    float or None
        Minutes from midnight, or None if conversion fails
    """
    from datetime import time as dt_time, datetime as dt_datetime, timedelta as dt_timedelta

    if time_val is None:
        return None

    try:
        # Handle timedelta (common from psycopg2 for TIME columns)
        if isinstance(time_val, dt_timedelta):
            return time_val.total_seconds() / 60

        # Handle time objects
        if isinstance(time_val, dt_time):
            return time_val.hour * 60 + time_val.minute + time_val.second / 60

        # Handle datetime objects
        if isinstance(time_val, dt_datetime):
            return time_val.hour * 60 + time_val.minute + time_val.second / 60

        # Handle pandas Timestamp
        if hasattr(time_val, 'hour') and hasattr(time_val, 'minute'):
            return time_val.hour * 60 + time_val.minute + (time_val.second if hasattr(time_val, 'second') else 0) / 60

        # Try parsing as string
        if isinstance(time_val, str):
            # Try datetime parsing first
            try:
                parsed = pd.to_datetime(time_val)
                return parsed.hour * 60 + parsed.minute + parsed.second / 60
            except Exception:
                pass

        return None
    except Exception:
        return None


def calculate_time_to_mfe(df: pd.DataFrame) -> pd.Series:
    """
    Calculate minutes from entry to MFE for each trade.

    Handles various time formats including TIME columns from PostgreSQL.

    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with entry_time and mfe_potential_time columns

    Returns:
    --------
    pd.Series
        Time to MFE in minutes
    """
    entry_minutes = df['entry_time'].apply(_time_to_minutes)
    mfe_minutes = df['mfe_potential_time'].apply(_time_to_minutes)

    # Time difference (MFE - entry)
    return mfe_minutes - entry_minutes


def calculate_time_to_mae(df: pd.DataFrame) -> pd.Series:
    """
    Calculate minutes from entry to MAE for each trade.

    Handles various time formats including TIME columns from PostgreSQL.

    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with entry_time and mae_potential_time columns

    Returns:
    --------
    pd.Series
        Time to MAE in minutes
    """
    entry_minutes = df['entry_time'].apply(_time_to_minutes)
    mae_minutes = df['mae_potential_time'].apply(_time_to_minutes)

    # Time difference (MAE - entry)
    return mae_minutes - entry_minutes


def _compare_times(mfe_time, mae_time) -> Optional[bool]:
    """
    Compare two time values to determine which occurred first.

    Parameters:
    -----------
    mfe_time : various
        MFE potential time in various formats
    mae_time : various
        MAE potential time in various formats

    Returns:
    --------
    bool or None
        True if MFE occurred before MAE, False otherwise, None if comparison fails
    """
    mfe_minutes = _time_to_minutes(mfe_time)
    mae_minutes = _time_to_minutes(mae_time)

    if mfe_minutes is None or mae_minutes is None:
        return None

    return mfe_minutes < mae_minutes


def calculate_sequence_summary(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate MFE/MAE sequence summary statistics.

    Returns unfiltered probability metrics for Monte Carlo baseline.

    Parameters:
    -----------
    data : List[Dict[str, Any]]
        List of records from mfe_mae_potential table

    Returns:
    --------
    Dict[str, Any]
        Dictionary containing sequence statistics:
        - mfe_first_rate: P(MFE before MAE)
        - mfe_first_count: Count of MFE-first trades
        - mae_first_count: Count of MAE-first trades
        - median_time_to_mfe: Median minutes to MFE
        - median_time_to_mae: Median minutes to MAE
        - mean_time_to_mfe: Mean minutes to MFE
        - mean_time_to_mae: Mean minutes to MAE
        - median_time_delta: Median (time_to_mae - time_to_mfe)
        - pct_mfe_under_30min: % trades with MFE within 30 minutes
        - pct_mfe_under_60min: % trades with MFE within 60 minutes
        - pct_mae_under_30min: % trades with MAE within 30 minutes
        - total_trades: Sample size
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

    # Check required columns exist
    required_cols = ['entry_time', 'mfe_potential_time', 'mae_potential_time']
    if not all(col in df.columns for col in required_cols):
        return empty_result

    # Normalize model names
    if 'model' in df.columns:
        df['model'] = df['model'].apply(_normalize_model)

    # Calculate time metrics
    try:
        df['time_to_mfe'] = calculate_time_to_mfe(df)
        df['time_to_mae'] = calculate_time_to_mae(df)
        df['time_delta'] = df['time_to_mae'] - df['time_to_mfe']

        # MFE first indicator - use the robust comparison function
        df['mfe_first'] = df.apply(
            lambda row: _compare_times(row['mfe_potential_time'], row['mae_potential_time']),
            axis=1
        )

        # Drop rows with invalid time calculations
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


def calculate_sequence_by_model(data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Calculate sequence statistics grouped by Model and Direction.

    PRIMARY OUTPUT for Monte Carlo parameters.

    Parameters:
    -----------
    data : List[Dict[str, Any]]
        List of records from mfe_mae_potential table

    Returns:
    --------
    pd.DataFrame
        Statistics grouped by model and direction with columns:
        - model, direction, n_trades
        - p_mfe_first (Monte Carlo win probability)
        - median_time_mfe, median_time_mae
        - mean_time_mfe, mean_time_mae
        - median_time_delta
        - std_time_mfe, std_time_mae
        - pct_mfe_under_30, pct_mfe_under_60
        - mc_confidence
    """
    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    # Check required columns
    required_cols = ['entry_time', 'mfe_potential_time', 'mae_potential_time', 'model', 'direction']
    if not all(col in df.columns for col in required_cols):
        return pd.DataFrame()

    # Normalize model names
    df['model'] = df['model'].apply(_normalize_model)

    # Calculate derived columns
    try:
        df['time_to_mfe'] = calculate_time_to_mfe(df)
        df['time_to_mae'] = calculate_time_to_mae(df)
        df['time_delta'] = df['time_to_mae'] - df['time_to_mfe']

        # MFE first indicator - use the robust comparison function
        df['mfe_first'] = df.apply(
            lambda row: _compare_times(row['mfe_potential_time'], row['mae_potential_time']),
            axis=1
        )

        # Normalize direction
        df['direction'] = df['direction'].str.upper()

        # Drop invalid rows
        df_valid = df.dropna(subset=['time_to_mfe', 'time_to_mae', 'mfe_first'])

        if df_valid.empty:
            return pd.DataFrame()

        # Group by model and direction
        grouped = df_valid.groupby(['model', 'direction']).agg(
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

        # Calculate percentage metrics per group
        pct_mfe_30 = df_valid.groupby(['model', 'direction']).apply(
            lambda x: (x['time_to_mfe'] <= 30).mean() * 100,
            include_groups=False
        ).reset_index(name='pct_mfe_under_30')

        pct_mfe_60 = df_valid.groupby(['model', 'direction']).apply(
            lambda x: (x['time_to_mfe'] <= 60).mean() * 100,
            include_groups=False
        ).reset_index(name='pct_mfe_under_60')

        # Merge percentage metrics
        grouped = grouped.merge(pct_mfe_30, on=['model', 'direction'])
        grouped = grouped.merge(pct_mfe_60, on=['model', 'direction'])

        # Monte Carlo confidence rating
        grouped['mc_confidence'] = grouped['n_trades'].apply(_get_mc_confidence)

        # Sort by p_mfe_first descending
        grouped = grouped.sort_values('p_mfe_first', ascending=False)

        return grouped

    except Exception:
        return pd.DataFrame()


def generate_monte_carlo_params(data: List[Dict[str, Any]]) -> Dict[str, Dict]:
    """
    Generate Monte Carlo simulation parameters by model-direction.

    Output format designed for direct use in Monte Carlo simulation.

    Parameters:
    -----------
    data : List[Dict[str, Any]]
        List of records from mfe_mae_potential table

    Returns:
    --------
    Dict[str, Dict]
        Dict keyed by "MODEL_DIRECTION" with simulation parameters:
        {
            "EPCH02_SHORT": {
                "p_win": 0.62,
                "n_samples": 305,
                "confidence": "HIGH",
                "time_to_mfe_median": 47,
                "time_to_mfe_std": 35,
                "time_to_mae_median": 82,
                "time_to_mae_std": 45,
                "mfe_typically_first": True
            },
            ...
        }
    """
    model_df = calculate_sequence_by_model(data)

    if model_df.empty:
        return {}

    params = {}
    for _, row in model_df.iterrows():
        key = f"{row['model']}_{row['direction']}"
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
def render_sequence_summary_cards(summary: Dict[str, Any]) -> None:
    """
    Render 4 summary metric cards for sequence analysis.

    Parameters:
    -----------
    summary : Dict[str, Any]
        Output from calculate_sequence_summary()
    """
    if not summary or summary.get('total_trades', 0) == 0:
        st.info("No sequence data available for analysis")
        return

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="P(MFE First)",
            value=f"{summary['mfe_first_rate']:.1%}",
            help="Probability that favorable movement occurs before adverse movement"
        )

    with col2:
        st.metric(
            label="Median Time to MFE",
            value=f"{summary['median_time_to_mfe']:.0f} min",
            help="Typical time for maximum favorable excursion to occur"
        )

    with col3:
        st.metric(
            label="Median Time to MAE",
            value=f"{summary['median_time_to_mae']:.0f} min",
            help="Typical time for maximum adverse excursion to occur"
        )

    with col4:
        st.metric(
            label="Trades Analyzed",
            value=f"{summary['total_trades']:,}",
            help="Total sample size for Monte Carlo baseline"
        )


def render_model_probability_table(df: pd.DataFrame) -> None:
    """
    Render the primary Monte Carlo probability table.

    Parameters:
    -----------
    df : pd.DataFrame
        Output from calculate_sequence_by_model()
    """
    if df.empty:
        st.warning("No data available for probability table.")
        return

    # Format for display
    display_df = df.copy()
    display_df['P(MFE First)'] = display_df['p_mfe_first'].apply(lambda x: f"{x:.1%}")
    display_df['Med Time MFE'] = display_df['median_time_mfe'].apply(lambda x: f"{x:.0f} min")
    display_df['Med Time MAE'] = display_df['median_time_mae'].apply(lambda x: f"{x:.0f} min")
    display_df['Time Delta'] = display_df['median_time_delta'].apply(lambda x: f"{x:+.0f} min")

    # Select and rename columns
    display_df = display_df[[
        'model', 'direction', 'n_trades', 'P(MFE First)',
        'Med Time MFE', 'Med Time MAE', 'Time Delta', 'mc_confidence'
    ]]
    display_df.columns = [
        'Model', 'Direction', 'Trades', 'P(MFE First)',
        'Med Time MFE', 'Med Time MAE', 'Time Delta', 'MC Confidence'
    ]

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )


def render_time_to_mfe_histogram(data: List[Dict[str, Any]]) -> None:
    """
    Render histogram of Time-to-MFE distribution.

    Parameters:
    -----------
    data : List[Dict[str, Any]]
        List of records from mfe_mae_potential table
    """
    if not data:
        st.warning("No data available for MFE histogram.")
        return

    df = pd.DataFrame(data)

    # Check required columns
    if 'entry_time' not in df.columns or 'mfe_potential_time' not in df.columns:
        st.warning("Missing required time columns for MFE histogram.")
        return

    # Normalize model names
    if 'model' in df.columns:
        df['model'] = df['model'].apply(_normalize_model)

    try:
        df['time_to_mfe'] = calculate_time_to_mfe(df)
        df_valid = df.dropna(subset=['time_to_mfe'])

        if df_valid.empty:
            st.warning("No valid time data for MFE histogram.")
            return

        fig = px.histogram(
            df_valid,
            x='time_to_mfe',
            color='model' if 'model' in df_valid.columns else None,
            nbins=24,
            title='Time to MFE Distribution by Model',
            labels={'time_to_mfe': 'Minutes from Entry', 'count': 'Trade Count'},
            barmode='overlay',
            opacity=0.7
        )

        # Add reference lines
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
        st.warning(f"Error rendering MFE histogram: {str(e)}")


def render_time_to_mae_histogram(data: List[Dict[str, Any]]) -> None:
    """
    Render histogram of Time-to-MAE distribution.

    Parameters:
    -----------
    data : List[Dict[str, Any]]
        List of records from mfe_mae_potential table
    """
    if not data:
        st.warning("No data available for MAE histogram.")
        return

    df = pd.DataFrame(data)

    # Check required columns
    if 'entry_time' not in df.columns or 'mae_potential_time' not in df.columns:
        st.warning("Missing required time columns for MAE histogram.")
        return

    # Normalize model names
    if 'model' in df.columns:
        df['model'] = df['model'].apply(_normalize_model)

    try:
        df['time_to_mae'] = calculate_time_to_mae(df)
        df_valid = df.dropna(subset=['time_to_mae'])

        if df_valid.empty:
            st.warning("No valid time data for MAE histogram.")
            return

        fig = px.histogram(
            df_valid,
            x='time_to_mae',
            color='model' if 'model' in df_valid.columns else None,
            nbins=24,
            title='Time to MAE Distribution by Model',
            labels={'time_to_mae': 'Minutes from Entry', 'count': 'Trade Count'},
            barmode='overlay',
            opacity=0.7
        )

        # Add reference lines
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
        st.warning(f"Error rendering MAE histogram: {str(e)}")


def render_mfe_mae_timing_scatter(data: List[Dict[str, Any]]) -> None:
    """
    Scatter plot: Time-to-MFE vs Time-to-MAE.

    Points BELOW diagonal = MFE occurred first (favorable)
    Points ABOVE diagonal = MAE occurred first (unfavorable)

    Parameters:
    -----------
    data : List[Dict[str, Any]]
        List of records from mfe_mae_potential table
    """
    if not data:
        st.warning("No data available for timing scatter plot.")
        return

    df = pd.DataFrame(data)

    # Check required columns
    required_cols = ['entry_time', 'mfe_potential_time', 'mae_potential_time']
    if not all(col in df.columns for col in required_cols):
        st.warning("Missing required time columns for scatter plot.")
        return

    # Normalize model names
    if 'model' in df.columns:
        df['model'] = df['model'].apply(_normalize_model)

    try:
        df['time_to_mfe'] = calculate_time_to_mfe(df)
        df['time_to_mae'] = calculate_time_to_mae(df)

        df_valid = df.dropna(subset=['time_to_mfe', 'time_to_mae'])

        if df_valid.empty:
            st.warning("No valid time data for scatter plot.")
            return

        fig = px.scatter(
            df_valid,
            x='time_to_mfe',
            y='time_to_mae',
            color='model' if 'model' in df_valid.columns else None,
            title='MFE vs MAE Timing (Below Diagonal = MFE First)',
            labels={
                'time_to_mfe': 'Time to MFE (minutes)',
                'time_to_mae': 'Time to MAE (minutes)'
            },
            opacity=0.6
        )

        # Add diagonal reference line (MFE time = MAE time)
        max_val = max(df_valid['time_to_mfe'].max(), df_valid['time_to_mae'].max())
        fig.add_trace(
            go.Scatter(
                x=[0, max_val],
                y=[0, max_val],
                mode='lines',
                line=dict(color='white', dash='dash'),
                name='MFE = MAE timing',
                showlegend=True
            )
        )

        fig.update_layout(
            template='plotly_dark',
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

    except Exception as e:
        st.warning(f"Error rendering timing scatter plot: {str(e)}")


def render_model_probability_chart(df: pd.DataFrame) -> None:
    """
    Grouped bar chart showing P(MFE First) by Model-Direction.

    KEY VISUALIZATION for Monte Carlo inputs.

    Parameters:
    -----------
    df : pd.DataFrame
        Output from calculate_sequence_by_model()
    """
    if df.empty:
        st.warning("No data available for probability chart.")
        return

    try:
        fig = px.bar(
            df,
            x='model',
            y='p_mfe_first',
            color='direction',
            barmode='group',
            title='P(MFE First) by Model and Direction - Monte Carlo Baseline',
            labels={
                'model': 'Entry Model',
                'p_mfe_first': 'P(MFE First)',
                'direction': 'Direction'
            },
            color_discrete_map={'LONG': CHART_COLORS['long'], 'SHORT': CHART_COLORS['short']}
        )

        # Format y-axis as percentage
        fig.update_layout(yaxis_tickformat='.0%')

        # Add 50% reference line (random chance)
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


# =============================================================================
# MAIN SECTION RENDERER
# =============================================================================
def render_sequence_analysis_section(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Main entry point to render the complete CALC-003 section.

    Call this from app.py to display the full sequence analysis.

    Parameters:
    -----------
    data : List[Dict[str, Any]]
        List of records from mfe_mae_potential table

    Returns:
    --------
    Dict[str, Any]
        The sequence summary statistics (for Monte AI integration)
    """
    st.subheader("MFE/MAE Sequence Analysis")
    st.markdown("*Monte Carlo Baseline - When does favorable/adverse movement occur?*")

    if not data:
        st.warning("No MFE/MAE data available. Ensure mfe_mae_potential table has data.")
        return {}

    # Check if required time columns have data
    df_check = pd.DataFrame(data)
    required_cols = ['entry_time', 'mfe_potential_time', 'mae_potential_time']

    missing_cols = [col for col in required_cols if col not in df_check.columns]
    if missing_cols:
        st.warning(f"Missing required columns: {missing_cols}")
        return {}

    # Check for NULL values in time columns
    null_counts = {
        'entry_time': df_check['entry_time'].isna().sum(),
        'mfe_potential_time': df_check['mfe_potential_time'].isna().sum(),
        'mae_potential_time': df_check['mae_potential_time'].isna().sum()
    }

    total_rows = len(df_check)
    valid_rows = total_rows - max(null_counts.values())

    if valid_rows == 0:
        st.warning(
            f"Time columns contain no valid data. "
            f"Total rows: {total_rows}. "
            f"NULL counts - entry_time: {null_counts['entry_time']}, "
            f"mfe_potential_time: {null_counts['mfe_potential_time']}, "
            f"mae_potential_time: {null_counts['mae_potential_time']}. "
            f"Ensure the mfe_mae_potential table has timestamp data populated."
        )
        return {}

    # Calculate summaries
    summary = calculate_sequence_summary(data)
    model_df = calculate_sequence_by_model(data)

    # Summary cards
    render_sequence_summary_cards(summary)

    st.markdown("---")

    # Model probability chart (primary visualization)
    render_model_probability_chart(model_df)

    # Model probability table
    st.markdown("#### Monte Carlo Parameters by Model-Direction")
    render_model_probability_table(model_df)

    st.markdown("---")

    # Time distribution section
    st.markdown("#### Time Distribution Analysis")
    col1, col2 = st.columns(2)

    with col1:
        render_time_to_mfe_histogram(data)

    with col2:
        render_time_to_mae_histogram(data)

    # Timing scatter plot
    render_mfe_mae_timing_scatter(data)

    # Monte Carlo export section
    st.markdown("---")
    st.markdown("#### Monte Carlo Export")

    mc_params = generate_monte_carlo_params(data)

    if mc_params:
        with st.expander("View Monte Carlo Parameters (JSON)"):
            st.json(mc_params)

        # Download button for MC params
        mc_json = json.dumps(mc_params, indent=2)
        st.download_button(
            label="Download MC Parameters",
            data=mc_json,
            file_name="monte_carlo_sequence_params.json",
            mime="application/json"
        )

    return summary


# =============================================================================
# EXAMPLE USAGE (for testing)
# =============================================================================
if __name__ == "__main__":
    from datetime import datetime, timedelta

    # Example mfe_mae_potential data with time-based columns
    base_time = datetime(2025, 12, 15, 9, 30)

    sample_data = [
        # Trade 1: MFE occurred first (45 min), MAE later (120 min)
        {
            "trade_id": "T1",
            "date": "2025-12-15",
            "ticker": "SPY",
            "direction": "LONG",
            "model": "EPCH02",
            "entry_time": base_time,
            "entry_price": 450.00,
            "mfe_potential_price": 456.75,
            "mfe_potential_time": base_time + timedelta(minutes=45),
            "mae_potential_price": 448.65,
            "mae_potential_time": base_time + timedelta(minutes=120),
        },
        # Trade 2: MAE occurred first (20 min), MFE later (90 min)
        {
            "trade_id": "T2",
            "date": "2025-12-15",
            "ticker": "SPY",
            "direction": "LONG",
            "model": "EPCH02",
            "entry_time": base_time,
            "entry_price": 450.00,
            "mfe_potential_price": 451.80,
            "mfe_potential_time": base_time + timedelta(minutes=90),
            "mae_potential_price": 446.40,
            "mae_potential_time": base_time + timedelta(minutes=20),
        },
        # Trade 3: SHORT - MFE first (30 min), MAE later (150 min)
        {
            "trade_id": "T3",
            "date": "2025-12-16",
            "ticker": "QQQ",
            "direction": "SHORT",
            "model": "EPCH04",
            "entry_time": base_time,
            "entry_price": 400.00,
            "mfe_potential_price": 392.00,
            "mfe_potential_time": base_time + timedelta(minutes=30),
            "mae_potential_price": 402.00,
            "mae_potential_time": base_time + timedelta(minutes=150),
        },
        # Trade 4: LONG - MAE first (15 min), MFE later (180 min)
        {
            "trade_id": "T4",
            "date": "2025-12-16",
            "ticker": "QQQ",
            "direction": "LONG",
            "model": "EPCH01",
            "entry_time": base_time,
            "entry_price": 400.00,
            "mfe_potential_price": 401.20,
            "mfe_potential_time": base_time + timedelta(minutes=180),
            "mae_potential_price": 395.20,
            "mae_potential_time": base_time + timedelta(minutes=15),
        },
    ]

    print("\nMFE/MAE Sequence Summary Statistics:")
    print("=" * 60)
    summary = calculate_sequence_summary(sample_data)
    for key, value in summary.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.3f}")
        else:
            print(f"  {key}: {value}")

    print("\n\nModel + Direction Breakdown:")
    print("=" * 60)
    model_stats = calculate_sequence_by_model(sample_data)
    if not model_stats.empty:
        print(model_stats.to_string(index=False))

    print("\n\nMonte Carlo Parameters:")
    print("=" * 60)
    mc_params = generate_monte_carlo_params(sample_data)
    print(json.dumps(mc_params, indent=2))
