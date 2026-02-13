"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Calculation: UI Components for Stop Analysis (CALC-009)
XIII Trading LLC
================================================================================

PURPOSE:
    Streamlit UI components for displaying stop type analysis results.
    Renders summary cards, comparison tables, and visualizations.

PLACEMENT:
    Second row of Metrics Overview tab (after summary cards, before CALC-001)

================================================================================
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import List, Dict, Any, Optional
from decimal import Decimal

from .stop_calculator import calculate_all_stop_prices
from .outcome_simulator import simulate_all_outcomes
from .results_aggregator import (
    aggregate_by_stop_type,
    aggregate_by_model_type,
    aggregate_by_direction,
    aggregate_by_model_direction,
    find_best_stop_type
)


# Chart colors matching dashboard theme
CHART_COLORS = {
    "win": "#26a69a",
    "loss": "#ef5350",
    "neutral": "#7e57c2",
    "background": "#1a1a2e",
    "paper": "#16213e",
    "text": "#e0e0e0",
    "grid": "#2a2a4e"
}


def _safe_float(value, default: float = 0.0) -> float:
    """Safely convert value to float."""
    if value is None:
        return default
    try:
        if isinstance(value, Decimal):
            return float(value)
        return float(value)
    except (ValueError, TypeError):
        return default


def render_stop_summary_cards(
    summary_df: pd.DataFrame,
    best_stop: Dict[str, Any],
    total_trades: int
) -> None:
    """
    Render top-level summary metric cards.

    Displays 4 cards:
    - Best Stop Type (by expectancy)
    - Best Win Rate
    - Best Expectancy
    - Trades Analyzed

    Parameters:
    -----------
    summary_df : pd.DataFrame
        Output from aggregate_by_stop_type()
    best_stop : Dict
        Output from find_best_stop_type()
    total_trades : int
        Total trades analyzed
    """
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Best Stop Type",
            value=best_stop.get('stop_type', 'N/A')
        )

    with col2:
        # Best win rate
        if not summary_df.empty and 'Win Rate %' in summary_df.columns:
            valid_df = summary_df[summary_df['n'] > 0]
            if not valid_df.empty:
                best_wr = valid_df['Win Rate %'].max()
                st.metric(label="Best Win Rate", value=f"{best_wr:.1f}%")
            else:
                st.metric(label="Best Win Rate", value="N/A")
        else:
            st.metric(label="Best Win Rate", value="N/A")

    with col3:
        # Best expectancy
        exp_value = best_stop.get('expectancy', 0)
        st.metric(
            label="Best Expectancy",
            value=f"{exp_value:+.3f}R" if exp_value != 0 else "N/A"
        )

    with col4:
        st.metric(label="Trades Analyzed", value=f"{total_trades:,}")


def render_stop_comparison_table(summary_df: pd.DataFrame) -> None:
    """
    Render the main stop type comparison table.

    Parameters:
    -----------
    summary_df : pd.DataFrame
        Output from aggregate_by_stop_type()
    """
    if summary_df.empty:
        st.info("No stop analysis data available")
        return

    # Format for display
    display_df = summary_df.copy()

    # Drop the key column if present
    if 'stop_type_key' in display_df.columns:
        display_df = display_df.drop(columns=['stop_type_key'])

    # Format columns
    if 'Avg Stop %' in display_df.columns:
        display_df['Avg Stop %'] = display_df['Avg Stop %'].apply(lambda x: f"{x:.2f}%")
    if 'Stop Hit %' in display_df.columns:
        display_df['Stop Hit %'] = display_df['Stop Hit %'].apply(lambda x: f"{x:.1f}%")
    if 'Win Rate %' in display_df.columns:
        display_df['Win Rate %'] = display_df['Win Rate %'].apply(lambda x: f"{x:.1f}%")
    if 'Avg R (Win)' in display_df.columns:
        display_df['Avg R (Win)'] = display_df['Avg R (Win)'].apply(lambda x: f"{x:+.2f}R")
    if 'Avg R (All)' in display_df.columns:
        display_df['Avg R (All)'] = display_df['Avg R (All)'].apply(lambda x: f"{x:+.2f}R")
    if 'Net R (MFE)' in display_df.columns:
        display_df['Net R (MFE)'] = display_df['Net R (MFE)'].apply(lambda x: f"{x:+.2f}R")
    if 'Expectancy' in display_df.columns:
        display_df['Expectancy'] = display_df['Expectancy'].apply(lambda x: f"{x:+.3f}")

    st.dataframe(display_df, use_container_width=True, hide_index=True)


def render_win_rate_chart(summary_df: pd.DataFrame) -> None:
    """
    Render horizontal bar chart showing win rate by stop type.
    """
    if summary_df.empty:
        return

    valid_df = summary_df[summary_df['n'] > 0].copy()
    if valid_df.empty:
        return

    # Sort by win rate
    valid_df = valid_df.sort_values('Win Rate %', ascending=True)

    # Color based on win rate
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

    # Add 50% reference line
    fig.add_vline(x=50, line_dash="dash", line_color=CHART_COLORS['text'],
                  annotation_text="50%", annotation_position="top")

    fig.update_layout(
        title="Win Rate by Stop Type",
        xaxis_title="Win Rate %",
        yaxis_title="",
        paper_bgcolor=CHART_COLORS['paper'],
        plot_bgcolor=CHART_COLORS['background'],
        font=dict(color=CHART_COLORS['text']),
        height=350,
        margin=dict(l=120, r=30, t=50, b=40)
    )

    st.plotly_chart(fig, use_container_width=True)


def render_expectancy_chart(summary_df: pd.DataFrame) -> None:
    """
    Render horizontal bar chart showing expectancy by stop type.
    """
    if summary_df.empty:
        return

    valid_df = summary_df[summary_df['n'] > 0].copy()
    if valid_df.empty:
        return

    # Sort by expectancy
    valid_df = valid_df.sort_values('Expectancy', ascending=True)

    # Color based on positive/negative
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

    # Add zero reference line
    fig.add_vline(x=0, line_dash="dash", line_color=CHART_COLORS['text'])

    fig.update_layout(
        title="Expectancy by Stop Type",
        xaxis_title="Expectancy (R)",
        yaxis_title="",
        paper_bgcolor=CHART_COLORS['paper'],
        plot_bgcolor=CHART_COLORS['background'],
        font=dict(color=CHART_COLORS['text']),
        height=350,
        margin=dict(l=120, r=30, t=50, b=40)
    )

    st.plotly_chart(fig, use_container_width=True)


def render_stop_distance_chart(summary_df: pd.DataFrame) -> None:
    """
    Render chart showing average stop distance vs win rate.
    """
    if summary_df.empty:
        return

    valid_df = summary_df[summary_df['n'] > 0].copy()
    if valid_df.empty:
        return

    fig = go.Figure()

    # Bubble size based on expectancy (normalized)
    exp_min = valid_df['Expectancy'].min()
    exp_max = valid_df['Expectancy'].max()
    exp_range = exp_max - exp_min if exp_max != exp_min else 1

    sizes = [(e - exp_min) / exp_range * 30 + 10 for e in valid_df['Expectancy']]

    # Color based on expectancy
    colors = [CHART_COLORS['win'] if x >= 0 else CHART_COLORS['loss']
              for x in valid_df['Expectancy']]

    fig.add_trace(go.Scatter(
        x=valid_df['Avg Stop %'],
        y=valid_df['Win Rate %'],
        mode='markers+text',
        marker=dict(
            size=sizes,
            color=colors,
            line=dict(width=1, color=CHART_COLORS['text'])
        ),
        text=valid_df['Stop Type'],
        textposition='top center',
        textfont=dict(size=9, color=CHART_COLORS['text']),
        hovertemplate=(
            "<b>%{text}</b><br>" +
            "Stop: %{x:.2f}%<br>" +
            "Win Rate: %{y:.1f}%<br>" +
            "<extra></extra>"
        )
    ))

    # Add 50% reference line
    fig.add_hline(y=50, line_dash="dash", line_color=CHART_COLORS['text'],
                  annotation_text="50% WR", annotation_position="right")

    fig.update_layout(
        title="Risk vs Reward by Stop Type",
        xaxis_title="Avg Stop Distance %",
        yaxis_title="Win Rate %",
        paper_bgcolor=CHART_COLORS['paper'],
        plot_bgcolor=CHART_COLORS['background'],
        font=dict(color=CHART_COLORS['text']),
        height=400,
        margin=dict(l=50, r=30, t=50, b=50)
    )

    st.plotly_chart(fig, use_container_width=True)


def render_stop_charts(summary_df: pd.DataFrame) -> None:
    """
    Render all stop analysis charts.
    """
    col1, col2 = st.columns(2)

    with col1:
        render_win_rate_chart(summary_df)

    with col2:
        render_expectancy_chart(summary_df)


def render_breakdown_expanders(
    results: Dict[str, List[Dict[str, Any]]]
) -> None:
    """
    Render expandable breakdown sections.
    """
    # By Model Type
    with st.expander("View by Model Type (Continuation vs Rejection)"):
        model_type_df = aggregate_by_model_type(results)
        if not model_type_df.empty:
            # Format
            display_df = model_type_df.copy()
            display_df['Win Rate %'] = display_df['Win Rate %'].apply(lambda x: f"{x:.1f}%")
            display_df['Expectancy'] = display_df['Expectancy'].apply(lambda x: f"{x:+.3f}")
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("No data available")

    # By Direction
    with st.expander("View by Direction (LONG vs SHORT)"):
        direction_df = aggregate_by_direction(results)
        if not direction_df.empty:
            display_df = direction_df.copy()
            display_df['Win Rate %'] = display_df['Win Rate %'].apply(lambda x: f"{x:.1f}%")
            display_df['Expectancy'] = display_df['Expectancy'].apply(lambda x: f"{x:+.3f}")
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("No data available")

    # By Model-Direction
    with st.expander("View by Model-Direction (8 combinations)"):
        model_dir_df = aggregate_by_model_direction(results)
        if not model_dir_df.empty:
            st.dataframe(model_dir_df, use_container_width=True, hide_index=True)
        else:
            st.info("No data available")


def calculate_stop_analysis(
    mfe_mae_data: List[Dict[str, Any]],
    trades_data: List[Dict[str, Any]],
    m5_bars_by_trade: Dict[str, List[Dict[str, Any]]],
    m1_bars_by_ticker_date: Dict[tuple, List[Dict[str, Any]]]
) -> Dict[str, Any]:
    """
    Main calculation function for stop analysis.

    Parameters:
    -----------
    mfe_mae_data : List[Dict]
        MFE/MAE potential data with entry_price, mfe_potential_price/time, mae_potential_price/time
    trades_data : List[Dict]
        Trades data with zone_low, zone_high
    m5_bars_by_trade : Dict[str, List[Dict]]
        M5 trade bars grouped by trade_id
    m1_bars_by_ticker_date : Dict[tuple, List[Dict]]
        M1 bars grouped by (ticker, date)

    Returns:
    --------
    Dict with 'summary', 'results', 'best_stop', 'total_trades'
    """
    # Build lookup for trades (zone data)
    trades_lookup = {t.get('trade_id'): t for t in trades_data}

    # Build combined trade records
    trades_with_data = []

    for mfe_mae in mfe_mae_data:
        trade_id = mfe_mae.get('trade_id')
        ticker = mfe_mae.get('ticker')
        trade_date = mfe_mae.get('date')

        # Get zone data from trades
        trade_info = trades_lookup.get(trade_id, {})

        # Build complete trade record
        trade = {
            'trade_id': trade_id,
            'entry_price': mfe_mae.get('entry_price'),
            'direction': mfe_mae.get('direction'),
            'entry_time': mfe_mae.get('entry_time'),
            'model': mfe_mae.get('model'),
            'ticker': ticker,
            'date': trade_date,
            'mfe_potential_price': mfe_mae.get('mfe_potential_price'),
            'mfe_potential_time': mfe_mae.get('mfe_potential_time'),
            'mae_potential_price': mfe_mae.get('mae_potential_price'),
            'mae_potential_time': mfe_mae.get('mae_potential_time'),
            'zone_low': trade_info.get('zone_low'),
            'zone_high': trade_info.get('zone_high')
        }

        # Get bars
        m5_bars = m5_bars_by_trade.get(trade_id, [])
        m1_bars = m1_bars_by_ticker_date.get((ticker, trade_date), [])

        # Calculate stop prices
        stops = calculate_all_stop_prices(trade, m1_bars, m5_bars)

        trades_with_data.append({
            'trade': trade,
            'm1_bars': m1_bars,
            'm5_bars': m5_bars,
            'stops': stops
        })

    # Simulate outcomes
    results = simulate_all_outcomes(trades_with_data)

    # Aggregate results
    summary_df = aggregate_by_stop_type(results)

    # Find best stop type
    best_stop = find_best_stop_type(summary_df, metric='Expectancy')

    # Count total trades processed
    total_trades = len(trades_with_data)

    return {
        'summary': summary_df,
        'results': results,
        'best_stop': best_stop,
        'total_trades': total_trades
    }


def render_stop_analysis_section(
    mfe_mae_data: List[Dict[str, Any]],
    trades_data: List[Dict[str, Any]],
    m5_bars_by_trade: Dict[str, List[Dict[str, Any]]],
    m1_bars_by_ticker_date: Dict[tuple, List[Dict[str, Any]]]
) -> Optional[Dict[str, Any]]:
    """
    Main entry point for stop analysis UI.

    Renders the complete CALC-009 section including:
    - Summary cards
    - Comparison table
    - Charts
    - Breakdown expanders

    Parameters:
    -----------
    mfe_mae_data : List[Dict]
        MFE/MAE potential data
    trades_data : List[Dict]
        Trades data with zone boundaries
    m5_bars_by_trade : Dict[str, List[Dict]]
        M5 trade bars grouped by trade_id
    m1_bars_by_ticker_date : Dict[tuple, List[Dict]]
        M1 bars grouped by (ticker, date)

    Returns:
    --------
    Dict with calculation results, or None if no data
    """
    st.subheader("Stop Type Analysis")
    st.markdown("*Foundation analysis: Which stop placement method provides best risk-adjusted returns?*")

    # Check for data
    if not mfe_mae_data:
        st.warning("No MFE/MAE potential data available for stop analysis")
        return None

    # Show progress
    with st.spinner("Analyzing stop types..."):
        # Calculate
        analysis = calculate_stop_analysis(
            mfe_mae_data=mfe_mae_data,
            trades_data=trades_data,
            m5_bars_by_trade=m5_bars_by_trade,
            m1_bars_by_ticker_date=m1_bars_by_ticker_date
        )

    summary_df = analysis.get('summary', pd.DataFrame())
    results = analysis.get('results', {})
    best_stop = analysis.get('best_stop', {})
    total_trades = analysis.get('total_trades', 0)

    if summary_df.empty or total_trades == 0:
        st.warning("No stop analysis results available. Ensure M5 trade bars and M1 bars are populated.")
        return None

    # Render summary cards
    render_stop_summary_cards(summary_df, best_stop, total_trades)

    st.markdown("---")

    # Render comparison table
    st.markdown("**Stop Type Comparison**")
    render_stop_comparison_table(summary_df)

    st.markdown("---")

    # Render charts
    render_stop_charts(summary_df)

    st.markdown("---")

    # Render breakdowns
    render_breakdown_expanders(results)

    return analysis


# =============================================================================
# SIMPLIFIED VERSION FOR INITIAL INTEGRATION
# =============================================================================
def render_stop_analysis_section_simple(
    mfe_mae_data: List[Dict[str, Any]],
    trades_data: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """
    Simplified stop analysis that doesn't require M1/M5 bar data.

    Uses MFE/MAE from mfe_mae_potential to estimate stop outcomes
    without walking individual bars. This is faster but less accurate.

    Good for initial testing while M1 bar fetching is implemented.
    """
    st.subheader("Stop Type Analysis")
    st.markdown("*Foundation analysis: Which stop placement method provides best risk-adjusted returns?*")

    if not mfe_mae_data:
        st.warning("No MFE/MAE potential data available for stop analysis")
        return None

    # Build trades lookup
    trades_lookup = {t.get('trade_id'): t for t in trades_data}

    # Simplified analysis using MAE as proxy for stop hits
    results = {
        'zone_buffer': [],
        'prior_m1': [],
        'prior_m5': [],
        'm5_atr': [],
        'm15_atr': [],
        'fractal': []
    }

    for mfe_mae in mfe_mae_data:
        trade_id = mfe_mae.get('trade_id')
        trade_info = trades_lookup.get(trade_id, {})

        entry_price = _safe_float(mfe_mae.get('entry_price'))
        direction = mfe_mae.get('direction', 'LONG')
        is_long = direction.upper() == 'LONG'

        mfe_price = _safe_float(mfe_mae.get('mfe_potential_price'))
        mae_price = _safe_float(mfe_mae.get('mae_potential_price'))
        zone_low = _safe_float(trade_info.get('zone_low'))
        zone_high = _safe_float(trade_info.get('zone_high'))

        if entry_price <= 0:
            continue

        # Estimate stop prices (simplified)
        if is_long:
            zone_distance = entry_price - zone_low if zone_low > 0 else entry_price * 0.005
            zone_buffer_stop = zone_low - (zone_distance * 0.05) if zone_low > 0 else entry_price * 0.99
            # Estimate other stops as percentages
            estimated_stops = {
                'zone_buffer': zone_buffer_stop,
                'prior_m1': entry_price * 0.997,  # ~0.3% below
                'prior_m5': entry_price * 0.995,  # ~0.5% below
                'm5_atr': entry_price * 0.992,    # ~0.8% below
                'm15_atr': entry_price * 0.988,   # ~1.2% below
                'fractal': entry_price * 0.99,    # ~1.0% below
            }
            mae_direction = -1 if mae_price < entry_price else 1
        else:
            zone_distance = zone_high - entry_price if zone_high > 0 else entry_price * 0.005
            zone_buffer_stop = zone_high + (zone_distance * 0.05) if zone_high > 0 else entry_price * 1.01
            estimated_stops = {
                'zone_buffer': zone_buffer_stop,
                'prior_m1': entry_price * 1.003,
                'prior_m5': entry_price * 1.005,
                'm5_atr': entry_price * 1.008,
                'm15_atr': entry_price * 1.012,
                'fractal': entry_price * 1.01,
            }
            mae_direction = 1 if mae_price > entry_price else -1

        # Determine outcomes based on MAE
        for stop_type, stop_price in estimated_stops.items():
            stop_distance = abs(entry_price - stop_price)
            stop_distance_pct = (stop_distance / entry_price) * 100 if entry_price > 0 else 0

            # Check if stop would be hit (MAE exceeds stop)
            if is_long:
                stop_hit = mae_price <= stop_price
                mfe_distance = max(0, mfe_price - entry_price)
            else:
                stop_hit = mae_price >= stop_price
                mfe_distance = max(0, entry_price - mfe_price)

            # Calculate R
            if stop_distance > 0:
                if stop_hit:
                    r_achieved = -1.0
                    outcome = 'LOSS'
                else:
                    r_achieved = mfe_distance / stop_distance
                    outcome = 'WIN' if r_achieved >= 1.0 else 'PARTIAL'
            else:
                r_achieved = 0
                outcome = 'PARTIAL'

            results[stop_type].append({
                'trade_id': trade_id,
                'direction': direction,
                'model': mfe_mae.get('model'),
                'stop_type': stop_type,
                'entry_price': entry_price,
                'stop_price': stop_price,
                'stop_distance': stop_distance,
                'stop_distance_pct': stop_distance_pct,
                'stop_hit': stop_hit,
                'mfe_price': mfe_price,
                'mfe_distance': mfe_distance,
                'r_achieved': r_achieved,
                'outcome': outcome
            })

    # Aggregate and display
    summary_df = aggregate_by_stop_type(results)
    best_stop = find_best_stop_type(summary_df, metric='Expectancy')
    total_trades = len(mfe_mae_data)

    # Render
    render_stop_summary_cards(summary_df, best_stop, total_trades)
    st.markdown("---")

    st.markdown("**Stop Type Comparison**")
    st.caption("*Estimated using MFE/MAE data - full analysis requires M1/M5 bar data*")
    render_stop_comparison_table(summary_df)

    st.markdown("---")
    render_stop_charts(summary_df)

    st.markdown("---")
    render_breakdown_expanders(results)

    return {
        'summary': summary_df,
        'results': results,
        'best_stop': best_stop,
        'total_trades': total_trades,
        'source': 'estimated'
    }


# =============================================================================
# SUPABASE-BACKED VERSION (PRODUCTION)
# =============================================================================
def _convert_supabase_to_results_format(
    stop_analysis_data: List[Dict[str, Any]]
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Convert Supabase stop_analysis records into the results dict format
    expected by the aggregation and rendering functions.

    Parameters:
    -----------
    stop_analysis_data : List[Dict]
        Raw records from stop_analysis table

    Returns:
    --------
    Dict[str, List[Dict]]
        Results grouped by stop_type
    """
    results = {
        'zone_buffer': [],
        'prior_m1': [],
        'prior_m5': [],
        'm5_atr': [],
        'm15_atr': [],
        'fractal': []
    }

    for record in stop_analysis_data:
        stop_type = record.get('stop_type')
        if stop_type not in results:
            continue

        results[stop_type].append({
            'trade_id': record.get('trade_id'),
            'direction': record.get('direction'),
            'model': record.get('model'),
            'stop_type': stop_type,
            'entry_price': _safe_float(record.get('entry_price')),
            'stop_price': _safe_float(record.get('stop_price')),
            'stop_distance': _safe_float(record.get('stop_distance')),
            'stop_distance_pct': _safe_float(record.get('stop_distance_pct')),
            'stop_hit': record.get('stop_hit'),
            'mfe_price': _safe_float(record.get('mfe_price')),
            'mfe_distance': _safe_float(record.get('mfe_distance')),
            'r_achieved': _safe_float(record.get('r_achieved')),
            'outcome': record.get('outcome')
        })

    return results


def render_stop_analysis_from_supabase(
    mfe_mae_data: List[Dict[str, Any]],
    trades_data: List[Dict[str, Any]],
    preloaded_data: Optional[tuple] = None
) -> Optional[Dict[str, Any]]:
    """
    Render stop analysis using pre-calculated data from Supabase.

    This function:
    1. Checks if stop_analysis table has data
    2. If yes, fetches and displays the pre-calculated accurate results
    3. If no, falls back to the simplified estimation method

    Benefits of using Supabase data:
    - Accurate stop prices (actual ATR, fractals, prior bar H/L)
    - Accurate outcomes (bar-by-bar simulation)
    - Fast (no Polygon API calls, just SQL query)
    - Consistent (same results every load)

    Parameters:
    -----------
    mfe_mae_data : List[Dict]
        MFE/MAE potential data (used for fallback only)
    trades_data : List[Dict]
        Trades data (used for fallback only)
    preloaded_data : Optional[tuple]
        Optional pre-loaded data from load_stop_analysis_data() as (records, count).
        If provided, skips the database query for better caching.

    Returns:
    --------
    Dict with calculation results, or None if no data
    """
    from data.supabase_client import get_client

    st.subheader("Stop Type Analysis")
    st.markdown("*Foundation analysis: Which stop placement method provides best risk-adjusted returns?*")

    # Use preloaded data if provided, otherwise fetch from database
    if preloaded_data is not None:
        stop_analysis_data, stop_count = preloaded_data
    else:
        # Check if stop_analysis table has data
        client = get_client()
        stop_count = client.get_stop_analysis_count()

        if stop_count == 0:
            stop_analysis_data = []
        else:
            # Fetch pre-calculated data from Supabase
            with st.spinner("Loading stop analysis data from Supabase..."):
                stop_analysis_data = client.fetch_stop_analysis()

    if stop_count == 0 or not stop_analysis_data:
        # Fall back to simplified calculation
        st.info(
            "**Note:** Using estimated stop analysis. For accurate results based on "
            "actual bar data, run the stop analysis processor:\n\n"
            "```bash\n"
            "cd 02_zone_system/09_backtest/processor/secondary_analysis/stop_analysis\n"
            "python runner.py\n"
            "```"
        )
        # Call the simple version but skip the header since we already rendered it
        return _render_stop_analysis_simple_no_header(mfe_mae_data, trades_data)

    # Convert to results format for aggregation
    results = _convert_supabase_to_results_format(stop_analysis_data)

    # Count unique trades (each trade has 6 stop types)
    unique_trade_ids = set(r.get('trade_id') for r in stop_analysis_data)
    total_trades = len(unique_trade_ids)

    # Aggregate results
    summary_df = aggregate_by_stop_type(results)
    best_stop = find_best_stop_type(summary_df, metric='Expectancy')

    # Render UI
    render_stop_summary_cards(summary_df, best_stop, total_trades)
    st.markdown("---")

    st.markdown("**Stop Type Comparison**")
    st.caption(f"*Pre-calculated from {stop_count:,} stop analysis records using actual M1/M5 bar data*")
    render_stop_comparison_table(summary_df)

    st.markdown("---")
    render_stop_charts(summary_df)

    st.markdown("---")
    render_breakdown_expanders(results)

    return {
        'summary': summary_df,
        'results': results,
        'best_stop': best_stop,
        'total_trades': total_trades,
        'source': 'supabase'
    }


def _render_stop_analysis_simple_no_header(
    mfe_mae_data: List[Dict[str, Any]],
    trades_data: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """
    Simplified stop analysis without rendering the header.
    Used as fallback when Supabase data is not available.
    """
    if not mfe_mae_data:
        st.warning("No MFE/MAE potential data available for stop analysis")
        return None

    # Build trades lookup
    trades_lookup = {t.get('trade_id'): t for t in trades_data}

    # Simplified analysis using MAE as proxy for stop hits
    results = {
        'zone_buffer': [],
        'prior_m1': [],
        'prior_m5': [],
        'm5_atr': [],
        'm15_atr': [],
        'fractal': []
    }

    for mfe_mae in mfe_mae_data:
        trade_id = mfe_mae.get('trade_id')
        trade_info = trades_lookup.get(trade_id, {})

        entry_price = _safe_float(mfe_mae.get('entry_price'))
        direction = mfe_mae.get('direction', 'LONG')
        is_long = direction.upper() == 'LONG'

        mfe_price = _safe_float(mfe_mae.get('mfe_potential_price'))
        mae_price = _safe_float(mfe_mae.get('mae_potential_price'))
        zone_low = _safe_float(trade_info.get('zone_low'))
        zone_high = _safe_float(trade_info.get('zone_high'))

        if entry_price <= 0:
            continue

        # Estimate stop prices (simplified)
        if is_long:
            zone_distance = entry_price - zone_low if zone_low > 0 else entry_price * 0.005
            zone_buffer_stop = zone_low - (zone_distance * 0.05) if zone_low > 0 else entry_price * 0.99
            estimated_stops = {
                'zone_buffer': zone_buffer_stop,
                'prior_m1': entry_price * 0.997,
                'prior_m5': entry_price * 0.995,
                'm5_atr': entry_price * 0.992,
                'm15_atr': entry_price * 0.988,
                'fractal': entry_price * 0.99,
            }
        else:
            zone_distance = zone_high - entry_price if zone_high > 0 else entry_price * 0.005
            zone_buffer_stop = zone_high + (zone_distance * 0.05) if zone_high > 0 else entry_price * 1.01
            estimated_stops = {
                'zone_buffer': zone_buffer_stop,
                'prior_m1': entry_price * 1.003,
                'prior_m5': entry_price * 1.005,
                'm5_atr': entry_price * 1.008,
                'm15_atr': entry_price * 1.012,
                'fractal': entry_price * 1.01,
            }

        # Determine outcomes based on MAE
        for stop_type, stop_price in estimated_stops.items():
            stop_distance = abs(entry_price - stop_price)
            stop_distance_pct = (stop_distance / entry_price) * 100 if entry_price > 0 else 0

            if is_long:
                stop_hit = mae_price <= stop_price
                mfe_distance = max(0, mfe_price - entry_price)
            else:
                stop_hit = mae_price >= stop_price
                mfe_distance = max(0, entry_price - mfe_price)

            if stop_distance > 0:
                if stop_hit:
                    r_achieved = -1.0
                    outcome = 'LOSS'
                else:
                    r_achieved = mfe_distance / stop_distance
                    outcome = 'WIN' if r_achieved >= 1.0 else 'PARTIAL'
            else:
                r_achieved = 0
                outcome = 'PARTIAL'

            results[stop_type].append({
                'trade_id': trade_id,
                'direction': direction,
                'model': mfe_mae.get('model'),
                'stop_type': stop_type,
                'entry_price': entry_price,
                'stop_price': stop_price,
                'stop_distance': stop_distance,
                'stop_distance_pct': stop_distance_pct,
                'stop_hit': stop_hit,
                'mfe_price': mfe_price,
                'mfe_distance': mfe_distance,
                'r_achieved': r_achieved,
                'outcome': outcome
            })

    # Aggregate and display
    summary_df = aggregate_by_stop_type(results)
    best_stop = find_best_stop_type(summary_df, metric='Expectancy')
    total_trades = len(mfe_mae_data)

    # Render
    render_stop_summary_cards(summary_df, best_stop, total_trades)
    st.markdown("---")

    st.markdown("**Stop Type Comparison**")
    st.caption("*Estimated using MFE/MAE data - full analysis requires M1/M5 bar data*")
    render_stop_comparison_table(summary_df)

    st.markdown("---")
    render_stop_charts(summary_df)

    st.markdown("---")
    render_breakdown_expanders(results)

    return {
        'summary': summary_df,
        'results': results,
        'best_stop': best_stop,
        'total_trades': total_trades,
        'source': 'estimated'
    }