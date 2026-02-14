"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Calculation: Simulated Outcome Analysis (CALC-004)
XIII Trading LLC
================================================================================

PURPOSE:
    Simulate trade outcomes based on M1 bar data at configurable stop and target
    levels. Uses bar-by-bar chronological analysis to accurately determine
    which level (stop or target) was hit first.

    Core Question: "At a given stop and target level, what percentage
    of trades would have been winners?"

DATA SOURCES:
    - mfe_mae_potential: Trade metadata (entry_price, entry_time, direction, etc.)
    - m1_bars: 1-minute OHLC bars for accurate stop/target simulation

SIMULATION LOGIC:
    For each trade, walk through M1 bars chronologically from entry_time to 15:30:
    - LONG: Check if bar.low <= stop_price (LOSS) or bar.high >= target_price (WIN)
    - SHORT: Check if bar.high >= stop_price (LOSS) or bar.low <= target_price (WIN)
    - First level breached determines outcome
    - If neither breached by EOD -> EOD_EXIT

METRICS CALCULATED:
    - Simulated Win Rate at given stop/target levels
    - EOD Exit Rate (trades where neither stop nor target was hit)
    - Expectancy in R-multiples
    - Optimal stop/target parameters by model-direction

================================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
from datetime import time, timedelta
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import json
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================
MODELS = ["EPCH01", "EPCH02", "EPCH03", "EPCH04"]

CHART_COLORS = {
    "win": "#26a69a",           # Teal green - favorable
    "loss": "#ef5350",          # Red - unfavorable
    "eod": "#ffa726",           # Orange - EOD exit
    "long": "#26a69a",          # Teal green
    "short": "#ef5350",         # Red
    "background": "#1a1a2e",
    "paper": "#16213e",
    "text": "#e0e0e0",
    "grid": "#2a2a4e",
    "reference": "#ffc107"      # Yellow for reference lines
}

# Default simulation parameters
DEFAULT_STOP_PCT = 1.0
DEFAULT_TARGET_PCT = 1.5

# Fixed R:R ratios to analyze (target multiples of stop)
R_RATIOS = [1.0, 2.0, 3.0, 4.0, 5.0]  # 1R, 2R, 3R, 4R, 5R targets


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


def _time_to_str(time_val) -> Optional[str]:
    """Convert a time value to HH:MM:SS string format."""
    if time_val is None:
        return None

    try:
        # Handle timedelta (common from psycopg2 for TIME columns)
        if isinstance(time_val, timedelta):
            total_seconds = int(time_val.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        # Handle time objects
        if isinstance(time_val, time):
            return time_val.strftime("%H:%M:%S")

        # Handle string
        if isinstance(time_val, str):
            return time_val

        # Handle pandas Timestamp or datetime
        if hasattr(time_val, 'strftime'):
            return time_val.strftime("%H:%M:%S")

        return None
    except Exception:
        return None


def _time_to_comparable(time_val) -> Optional[int]:
    """Convert time to comparable integer (seconds from midnight)."""
    if time_val is None:
        return None

    try:
        if isinstance(time_val, timedelta):
            return int(time_val.total_seconds())
        if isinstance(time_val, time):
            return time_val.hour * 3600 + time_val.minute * 60 + time_val.second
        if isinstance(time_val, str):
            parts = time_val.split(':')
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2] if len(parts) > 2 else 0)
        return None
    except Exception:
        return None


# =============================================================================
# CORE SIMULATION FUNCTIONS (Using M1 Bars)
# =============================================================================
def simulate_trade_with_bars(
    entry_price: float,
    direction: str,
    stop_pct: float,
    target_pct: float,
    bars: List[Dict],
    entry_time_str: Optional[str] = None
) -> Tuple[str, str, Optional[str]]:
    """
    Simulate a single trade outcome by walking through M1 bars chronologically.

    Args:
        entry_price: Trade entry price
        direction: 'LONG' or 'SHORT'
        stop_pct: Stop distance as percentage (e.g., 1.0 for 1%)
        target_pct: Target distance as percentage (e.g., 1.5 for 1.5%)
        bars: List of bar dicts with 'bar_time', 'high', 'low' keys
        entry_time_str: Optional entry time to filter bars

    Returns:
        Tuple of (outcome, reason, exit_time):
            outcome: 'WIN', 'LOSS', or 'EOD_EXIT'
            reason: 'target_hit', 'stop_hit', 'eod_exit', 'no_bars'
            exit_time: Time when outcome was determined (or None)
    """
    if not bars:
        return ('EOD_EXIT', 'no_bars', None)

    direction = direction.upper()

    # Calculate stop and target prices
    if direction == 'LONG':
        stop_price = entry_price * (1 - stop_pct / 100)
        target_price = entry_price * (1 + target_pct / 100)
    else:  # SHORT
        stop_price = entry_price * (1 + stop_pct / 100)
        target_price = entry_price * (1 - target_pct / 100)

    # Filter bars to those at or after entry time
    entry_seconds = _time_to_comparable(entry_time_str) if entry_time_str else 0

    for bar in bars:
        bar_time = bar.get('bar_time')
        bar_seconds = _time_to_comparable(bar_time)

        # Skip bars before entry
        if bar_seconds is not None and entry_seconds is not None:
            if bar_seconds < entry_seconds:
                continue

        high = _safe_float(bar.get('high'))
        low = _safe_float(bar.get('low'))

        if high is None or low is None:
            continue

        bar_time_str = _time_to_str(bar_time)

        # Check for stop/target hits
        if direction == 'LONG':
            # For LONG: low touches stop, high touches target
            stop_hit = low <= stop_price
            target_hit = high >= target_price

            if stop_hit and target_hit:
                # Both hit in same bar - conservative: assume stop hit first
                # unless we have more granular data
                return ('LOSS', 'stop_first_same_bar', bar_time_str)
            elif stop_hit:
                return ('LOSS', 'stop_hit', bar_time_str)
            elif target_hit:
                return ('WIN', 'target_hit', bar_time_str)

        else:  # SHORT
            # For SHORT: high touches stop, low touches target
            stop_hit = high >= stop_price
            target_hit = low <= target_price

            if stop_hit and target_hit:
                # Both hit in same bar - conservative: assume stop hit first
                return ('LOSS', 'stop_first_same_bar', bar_time_str)
            elif stop_hit:
                return ('LOSS', 'stop_hit', bar_time_str)
            elif target_hit:
                return ('WIN', 'target_hit', bar_time_str)

    # Neither hit by end of bars (EOD)
    return ('EOD_EXIT', 'eod_exit', None)


def simulate_outcomes_with_m1_bars(
    trades_data: List[Dict],
    stop_pct: float,
    target_pct: float,
    bars_by_ticker_date: Dict[Tuple, List[Dict]]
) -> pd.DataFrame:
    """
    Simulate trade outcomes using M1 bar data for accurate stop/target detection.

    Args:
        trades_data: List of trade dicts from mfe_mae_potential table
        stop_pct: Stop distance as percentage
        target_pct: Target distance as percentage
        bars_by_ticker_date: Dict mapping (ticker, date) to list of M1 bars

    Returns:
        DataFrame with simulation results including:
            - sim_outcome: 'WIN', 'LOSS', or 'EOD_EXIT'
            - sim_reason: Detailed outcome reason
            - sim_exit_time: Time when outcome was determined
            - sim_r: Simulated R-multiple
    """
    if not trades_data:
        return pd.DataFrame()

    results = []
    r_ratio = target_pct / stop_pct if stop_pct > 0 else 0

    for trade in trades_data:
        ticker = trade.get('ticker', '').upper()
        trade_date = trade.get('date')
        entry_price = _safe_float(trade.get('entry_price'))
        direction = trade.get('direction', '').upper()
        entry_time = trade.get('entry_time')
        entry_time_str = _time_to_str(entry_time)

        # Get bars for this ticker-date
        key = (ticker, trade_date)
        bars = bars_by_ticker_date.get(key, [])

        if entry_price is None or direction not in ('LONG', 'SHORT'):
            outcome, reason, exit_time = ('EOD_EXIT', 'invalid_trade', None)
        elif not bars:
            outcome, reason, exit_time = ('EOD_EXIT', 'no_bar_data', None)
        else:
            outcome, reason, exit_time = simulate_trade_with_bars(
                entry_price=entry_price,
                direction=direction,
                stop_pct=stop_pct,
                target_pct=target_pct,
                bars=bars,
                entry_time_str=entry_time_str
            )

        # Calculate R-multiple
        if outcome == 'WIN':
            sim_r = r_ratio
        elif outcome == 'LOSS':
            sim_r = -1.0
        else:
            sim_r = 0.0

        result = {
            **trade,
            'sim_outcome': outcome,
            'sim_reason': reason,
            'sim_exit_time': exit_time,
            'sim_r': sim_r
        }
        results.append(result)

    df = pd.DataFrame(results)

    # Normalize model names
    if 'model' in df.columns:
        df['model'] = df['model'].apply(_normalize_model)

    return df


# =============================================================================
# STATISTICS CALCULATION FUNCTIONS
# =============================================================================
def calculate_simulated_stats_from_df(df: pd.DataFrame, stop_pct: float, target_pct: float) -> Dict[str, Any]:
    """
    Calculate win rate and expectancy from a simulated outcomes DataFrame.

    Args:
        df: DataFrame with 'sim_outcome' and 'sim_r' columns
        stop_pct: Stop distance percentage (for reporting)
        target_pct: Target distance percentage (for reporting)

    Returns:
        Dict with simulation statistics
    """
    if df.empty:
        return _empty_simulated_stats(stop_pct, target_pct)

    wins = (df['sim_outcome'] == 'WIN').sum()
    losses = (df['sim_outcome'] == 'LOSS').sum()
    eod_exits = (df['sim_outcome'] == 'EOD_EXIT').sum()
    total = len(df)
    resolved = wins + losses

    win_rate = (wins / resolved * 100) if resolved > 0 else 0.0
    eod_rate = (eod_exits / total * 100) if total > 0 else 0.0

    total_r = df['sim_r'].sum()
    expectancy_r = total_r / total if total > 0 else 0.0

    return {
        'total_trades': int(total),
        'wins': int(wins),
        'losses': int(losses),
        'eod_exits': int(eod_exits),
        'resolved_trades': int(resolved),
        'win_rate': float(win_rate),
        'eod_rate': float(eod_rate),
        'expectancy_r': float(expectancy_r),
        'total_r': float(total_r),
        'risk_reward': target_pct / stop_pct if stop_pct > 0 else 0,
        'stop_pct': stop_pct,
        'target_pct': target_pct
    }


def _empty_simulated_stats(stop_pct: float, target_pct: float) -> Dict[str, Any]:
    """Return empty stats structure."""
    return {
        'total_trades': 0,
        'wins': 0,
        'losses': 0,
        'eod_exits': 0,
        'resolved_trades': 0,
        'win_rate': 0.0,
        'eod_rate': 0.0,
        'expectancy_r': 0.0,
        'total_r': 0.0,
        'risk_reward': target_pct / stop_pct if stop_pct > 0 else 0,
        'stop_pct': stop_pct,
        'target_pct': target_pct
    }


def calculate_simulated_by_model_from_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate simulated statistics grouped by Model and Direction.

    Args:
        df: DataFrame with simulation results

    Returns:
        DataFrame with grouped statistics
    """
    if df.empty or 'model' not in df.columns or 'direction' not in df.columns:
        return pd.DataFrame()

    # Group by model and direction
    grouped = df.groupby(['model', 'direction']).agg(
        total_trades=('sim_outcome', 'count'),
        wins=('sim_outcome', lambda x: (x == 'WIN').sum()),
        losses=('sim_outcome', lambda x: (x == 'LOSS').sum()),
        eod_exits=('sim_outcome', lambda x: (x == 'EOD_EXIT').sum()),
        total_r=('sim_r', 'sum')
    ).reset_index()

    # Calculate derived metrics
    grouped['resolved'] = grouped['wins'] + grouped['losses']
    grouped['win_rate'] = grouped.apply(
        lambda row: (row['wins'] / row['resolved'] * 100)
        if row['resolved'] > 0 else 0.0,
        axis=1
    )
    grouped['expectancy_r'] = grouped['total_r'] / grouped['total_trades']

    # Sort by expectancy descending
    grouped = grouped.sort_values('expectancy_r', ascending=False)

    return grouped


# =============================================================================
# WRAPPER FUNCTIONS (for backwards compatibility and convenience)
# =============================================================================
def calculate_simulated_stats(
    data: List[Dict],
    stop_pct: float,
    target_pct: float,
    db_client=None
) -> Dict[str, Any]:
    """
    Calculate win rate and expectancy at given stop/target levels.

    This is the main entry point for CALC-004 simulation.

    Args:
        data: List of dicts from mfe_mae_potential table
        stop_pct: Stop distance percentage
        target_pct: Target distance percentage
        db_client: Optional database client (will create one if not provided)

    Returns:
        Dict with simulation statistics
    """
    if not data:
        return _empty_simulated_stats(stop_pct, target_pct)

    # Get database client
    if db_client is None:
        from data.supabase_client import get_client
        db_client = get_client()

    # Get unique ticker-date combinations
    ticker_dates = list(set(
        (t.get('ticker', '').upper(), t.get('date'))
        for t in data
        if t.get('ticker') and t.get('date')
    ))

    # Fetch M1 bars in batch
    bars_by_ticker_date = db_client.fetch_m1_bars_batch(ticker_dates)

    # Run simulation
    df = simulate_outcomes_with_m1_bars(data, stop_pct, target_pct, bars_by_ticker_date)

    return calculate_simulated_stats_from_df(df, stop_pct, target_pct)


def calculate_simulated_by_model(
    data: List[Dict],
    stop_pct: float,
    target_pct: float,
    db_client=None
) -> pd.DataFrame:
    """
    Calculate simulated statistics grouped by Model and Direction.

    Args:
        data: List of dicts from mfe_mae_potential table
        stop_pct: Stop distance percentage
        target_pct: Target distance percentage
        db_client: Optional database client

    Returns:
        DataFrame with grouped statistics
    """
    if not data:
        return pd.DataFrame()

    # Get database client
    if db_client is None:
        from data.supabase_client import get_client
        db_client = get_client()

    # Get unique ticker-date combinations
    ticker_dates = list(set(
        (t.get('ticker', '').upper(), t.get('date'))
        for t in data
        if t.get('ticker') and t.get('date')
    ))

    # Fetch M1 bars in batch
    bars_by_ticker_date = db_client.fetch_m1_bars_batch(ticker_dates)

    # Run simulation
    df = simulate_outcomes_with_m1_bars(data, stop_pct, target_pct, bars_by_ticker_date)

    return calculate_simulated_by_model_from_df(df)


def generate_stop_target_grid(
    data: List[Dict],
    stop_range: tuple = (0.25, 2.0, 0.25),
    target_range: tuple = (0.5, 3.0, 0.5),
    group_by: Optional[str] = None,
    db_client=None
) -> pd.DataFrame:
    """
    Generate performance grid across stop/target combinations.

    Args:
        data: List of dicts from mfe_mae_potential table
        stop_range: (min, max, step) for stop levels
        target_range: (min, max, step) for target levels
        group_by: Optional grouping ('model', 'direction', 'model_direction')
        db_client: Optional database client

    Returns:
        DataFrame with grid results
    """
    if not data:
        return pd.DataFrame()

    # Get database client
    if db_client is None:
        from data.supabase_client import get_client
        db_client = get_client()

    # Get unique ticker-date combinations and fetch bars once
    ticker_dates = list(set(
        (t.get('ticker', '').upper(), t.get('date'))
        for t in data
        if t.get('ticker') and t.get('date')
    ))
    bars_by_ticker_date = db_client.fetch_m1_bars_batch(ticker_dates)

    # Generate parameter ranges
    stops = np.arange(stop_range[0], stop_range[1] + stop_range[2] / 2, stop_range[2])
    targets = np.arange(target_range[0], target_range[1] + target_range[2] / 2, target_range[2])

    results = []

    for stop_pct in stops:
        for target_pct in targets:
            # Skip invalid combinations
            if target_pct <= stop_pct * 0.5:
                continue

            # Run simulation for this stop/target combination
            df = simulate_outcomes_with_m1_bars(data, stop_pct, target_pct, bars_by_ticker_date)

            if df.empty:
                continue

            if group_by == 'model_direction':
                for (model, direction), group_df in df.groupby(['model', 'direction']):
                    stats = calculate_simulated_stats_from_df(group_df, stop_pct, target_pct)
                    stats['model'] = model
                    stats['direction'] = direction
                    results.append(stats)
            elif group_by == 'model':
                for model, group_df in df.groupby('model'):
                    stats = calculate_simulated_stats_from_df(group_df, stop_pct, target_pct)
                    stats['model'] = model
                    results.append(stats)
            elif group_by == 'direction':
                for direction, group_df in df.groupby('direction'):
                    stats = calculate_simulated_stats_from_df(group_df, stop_pct, target_pct)
                    stats['direction'] = direction
                    results.append(stats)
            else:
                stats = calculate_simulated_stats_from_df(df, stop_pct, target_pct)
                results.append(stats)

    return pd.DataFrame(results)


def find_optimal_parameters(
    data: List[Dict],
    stop_range: tuple = (0.25, 2.0, 0.25),
    target_range: tuple = (0.5, 3.0, 0.5),
    min_trades: int = 50,
    optimize_by: str = 'expectancy_r',
    db_client=None
) -> pd.DataFrame:
    """
    Find optimal stop/target parameters by model-direction.

    Args:
        data: List of dicts from mfe_mae_potential table
        stop_range: (min, max, step) for stop levels
        target_range: (min, max, step) for target levels
        min_trades: Minimum trades required for valid result
        optimize_by: Metric to optimize ('expectancy_r' or 'win_rate')
        db_client: Optional database client

    Returns:
        DataFrame with optimal parameters per model-direction
    """
    grid_df = generate_stop_target_grid(
        data, stop_range, target_range, group_by='model_direction', db_client=db_client
    )

    if grid_df.empty:
        return pd.DataFrame()

    # Filter by minimum trades
    grid_df = grid_df[grid_df['total_trades'] >= min_trades]

    if grid_df.empty:
        return pd.DataFrame()

    # Find optimal for each model-direction
    idx = grid_df.groupby(['model', 'direction'])[optimize_by].idxmax()
    optimal = grid_df.loc[idx].copy()

    optimal = optimal.rename(columns={
        'stop_pct': 'optimal_stop',
        'target_pct': 'optimal_target'
    })

    # Sort by expectancy
    optimal = optimal.sort_values('expectancy_r', ascending=False)

    return optimal[[
        'model', 'direction', 'optimal_stop', 'optimal_target',
        'win_rate', 'expectancy_r', 'total_r', 'total_trades'
    ]]


# =============================================================================
# STREAMLIT DISPLAY FUNCTIONS
# =============================================================================
def render_simulated_summary_cards(stats: Dict) -> None:
    """
    Render summary metric cards for simulated outcomes.

    Row 1: Wins | Losses | EOD Exits | Sim Win Rate
    Row 2: Expectancy | Total R | R:R Ratio
    """
    if not stats or stats.get('total_trades', 0) == 0:
        st.info("No simulation data available")
        return

    # Row 1
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Simulated Wins",
            value=f"{stats['wins']:,}",
            help="Trades where target was hit before stop"
        )

    with col2:
        st.metric(
            label="Simulated Losses",
            value=f"{stats['losses']:,}",
            help="Trades where stop was hit before target"
        )

    with col3:
        st.metric(
            label="EOD Exits",
            value=f"{stats['eod_exits']:,}",
            help="Trades where neither stop nor target was hit"
        )

    with col4:
        st.metric(
            label="Sim Win Rate",
            value=f"{stats['win_rate']:.1f}%",
            help="Win rate excluding EOD exits"
        )

    # Row 2
    col5, col6, col7 = st.columns(3)

    with col5:
        st.metric(
            label="Expectancy",
            value=f"{stats['expectancy_r']:+.3f}R",
            help="Expected R per trade"
        )

    with col6:
        st.metric(
            label="Total R",
            value=f"{stats['total_r']:+.1f}R",
            help="Sum of simulated R-multiples"
        )

    with col7:
        st.metric(
            label="Risk:Reward",
            value=f"1:{stats['risk_reward']:.2f}",
            help=f"Stop: {stats['stop_pct']}% / Target: {stats['target_pct']}%"
        )


def render_simulated_model_table(df: pd.DataFrame, stop_pct: float, target_pct: float) -> None:
    """
    Render simulated outcomes table by model-direction.
    """
    if df.empty:
        st.warning("No data available for model breakdown.")
        return

    # Format for display
    display_df = df.copy()
    display_df['Win%'] = display_df['win_rate'].apply(lambda x: f"{x:.1f}%")
    display_df['Exp R'] = display_df['expectancy_r'].apply(lambda x: f"{x:+.3f}R")
    display_df['Total R'] = display_df['total_r'].apply(lambda x: f"{x:+.1f}R")

    display_df = display_df[[
        'model', 'direction', 'total_trades', 'wins', 'losses',
        'eod_exits', 'Win%', 'Exp R', 'Total R'
    ]]
    display_df.columns = [
        'Model', 'Direction', 'Trades', 'Wins', 'Losses',
        'EOD', 'Win%', 'Exp R', 'Total R'
    ]

    st.caption(f"Simulated at Stop: {stop_pct}% | Target: {target_pct}% (using M1 bar data)")
    st.dataframe(display_df, use_container_width=True, hide_index=True)


def render_stop_target_heatmap(
    grid_df: pd.DataFrame,
    metric: str = 'expectancy_r',
    title: str = 'Expectancy by Stop/Target'
) -> None:
    """
    Interactive heatmap showing metric across stop/target combinations.
    """
    if grid_df.empty:
        st.warning("No grid data available for heatmap.")
        return

    # Pivot for heatmap
    pivot_df = grid_df.pivot(
        index='stop_pct',
        columns='target_pct',
        values=metric
    )

    # Create heatmap
    fig = px.imshow(
        pivot_df,
        labels=dict(x="Target %", y="Stop %", color=metric),
        title=title,
        color_continuous_scale='RdYlGn',
        aspect='auto'
    )

    # Add text annotations
    fig.update_traces(
        text=pivot_df.round(2).values,
        texttemplate="%{text}",
        textfont={"size": 10}
    )

    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor=CHART_COLORS['paper'],
        plot_bgcolor=CHART_COLORS['background'],
        font_color=CHART_COLORS['text'],
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)


def render_optimal_parameters_table(optimal_df: pd.DataFrame) -> None:
    """
    Render table of optimal stop/target by model-direction.
    """
    if optimal_df.empty:
        st.warning("No optimal parameters found. Check minimum trade requirements.")
        return

    # Format for display
    display_df = optimal_df.copy()
    display_df['Stop'] = display_df['optimal_stop'].apply(lambda x: f"{x:.2f}%")
    display_df['Target'] = display_df['optimal_target'].apply(lambda x: f"{x:.2f}%")
    display_df['Win%'] = display_df['win_rate'].apply(lambda x: f"{x:.1f}%")
    display_df['Exp R'] = display_df['expectancy_r'].apply(lambda x: f"{x:+.3f}R")
    display_df['Total R'] = display_df['total_r'].apply(lambda x: f"{x:+.1f}R")

    display_df = display_df[[
        'model', 'direction', 'Stop', 'Target',
        'Win%', 'Exp R', 'Total R', 'total_trades'
    ]]
    display_df.columns = [
        'Model', 'Direction', 'Optimal Stop', 'Optimal Target',
        'Win%', 'Exp R', 'Total R', 'Trades'
    ]

    st.dataframe(display_df, use_container_width=True, hide_index=True)


def render_outcome_distribution_chart(df: pd.DataFrame) -> None:
    """
    Stacked bar chart showing WIN/LOSS/EOD breakdown by model-direction.
    """
    if df.empty:
        st.warning("No data available for outcome distribution chart.")
        return

    # Prepare data for stacked bar
    chart_df = df.copy()
    chart_df['model_direction'] = chart_df['model'] + ' ' + chart_df['direction']

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name='Wins',
        x=chart_df['model_direction'],
        y=chart_df['wins'],
        marker_color=CHART_COLORS['win']
    ))

    fig.add_trace(go.Bar(
        name='Losses',
        x=chart_df['model_direction'],
        y=chart_df['losses'],
        marker_color=CHART_COLORS['loss']
    ))

    fig.add_trace(go.Bar(
        name='EOD Exits',
        x=chart_df['model_direction'],
        y=chart_df['eod_exits'],
        marker_color=CHART_COLORS['eod']
    ))

    fig.update_layout(
        barmode='stack',
        title='Simulated Outcome Distribution by Model-Direction',
        xaxis_title='Model / Direction',
        yaxis_title='Trade Count',
        template='plotly_dark',
        paper_bgcolor=CHART_COLORS['paper'],
        plot_bgcolor=CHART_COLORS['background'],
        font_color=CHART_COLORS['text'],
        height=400
    )
    fig.update_xaxes(gridcolor=CHART_COLORS['grid'])
    fig.update_yaxes(gridcolor=CHART_COLORS['grid'])

    st.plotly_chart(fig, use_container_width=True)


def render_expectancy_by_model_chart(df: pd.DataFrame) -> None:
    """
    Grouped bar chart showing expectancy by model and direction.
    """
    if df.empty:
        st.warning("No data available for expectancy chart.")
        return

    fig = px.bar(
        df,
        x='model',
        y='expectancy_r',
        color='direction',
        barmode='group',
        title='Simulated Expectancy by Model and Direction',
        labels={
            'model': 'Entry Model',
            'expectancy_r': 'Expectancy (R)',
            'direction': 'Direction'
        },
        color_discrete_map={'LONG': CHART_COLORS['loss'], 'SHORT': CHART_COLORS['win']}
    )

    # Add zero reference line
    fig.add_hline(
        y=0,
        line_dash="dash",
        line_color=CHART_COLORS['reference'],
        annotation_text="Breakeven",
        annotation_position="right"
    )

    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor=CHART_COLORS['paper'],
        plot_bgcolor=CHART_COLORS['background'],
        font_color=CHART_COLORS['text'],
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig.update_xaxes(gridcolor=CHART_COLORS['grid'])
    fig.update_yaxes(gridcolor=CHART_COLORS['grid'])

    st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# MULTI-R RATIO ANALYSIS FUNCTIONS
# =============================================================================
def calculate_multi_r_stats(
    data: List[Dict],
    stop_pct: float,
    r_ratios: List[float] = None,
    db_client=None
) -> pd.DataFrame:
    """
    Calculate simulation statistics for multiple R:R ratios.

    Args:
        data: List of dicts from mfe_mae_potential table
        stop_pct: Stop distance percentage (fixed)
        r_ratios: List of R multiples for targets (e.g., [1.0, 2.0, 3.0, 4.0, 5.0])
        db_client: Optional database client

    Returns:
        DataFrame with stats for each R ratio
    """
    if r_ratios is None:
        r_ratios = R_RATIOS

    if not data:
        return pd.DataFrame()

    # Get database client
    if db_client is None:
        from data.supabase_client import get_client
        db_client = get_client()

    # Get unique ticker-date combinations and fetch bars ONCE
    ticker_dates = list(set(
        (t.get('ticker', '').upper(), t.get('date'))
        for t in data
        if t.get('ticker') and t.get('date')
    ))
    bars_by_ticker_date = db_client.fetch_m1_bars_batch(ticker_dates)

    results = []
    for r_ratio in r_ratios:
        target_pct = stop_pct * r_ratio

        # Run simulation
        df = simulate_outcomes_with_m1_bars(data, stop_pct, target_pct, bars_by_ticker_date)
        stats = calculate_simulated_stats_from_df(df, stop_pct, target_pct)

        # Add R ratio info
        stats['r_ratio'] = r_ratio
        stats['r_label'] = f"{int(r_ratio)}R" if r_ratio == int(r_ratio) else f"{r_ratio}R"
        results.append(stats)

    return pd.DataFrame(results)


def render_multi_r_comparison_table(df: pd.DataFrame, stop_pct: float) -> None:
    """
    Render comparison table for multiple R:R ratios.
    Highlights the best expectancy row.
    """
    if df.empty:
        st.warning("No multi-R data available.")
        return

    # Find best expectancy
    best_idx = df['expectancy_r'].idxmax()
    best_r = df.loc[best_idx, 'r_ratio']

    # Format for display
    display_df = df.copy()
    display_df['Target %'] = display_df['target_pct'].apply(lambda x: f"{x:.2f}%")
    display_df['R:R'] = display_df['r_ratio'].apply(lambda x: f"1:{x:.0f}" if x == int(x) else f"1:{x:.1f}")
    display_df['Wins'] = display_df['wins'].apply(lambda x: f"{x:,}")
    display_df['Losses'] = display_df['losses'].apply(lambda x: f"{x:,}")
    display_df['EOD'] = display_df['eod_exits'].apply(lambda x: f"{x:,}")
    display_df['Win Rate'] = display_df['win_rate'].apply(lambda x: f"{x:.1f}%")
    display_df['Expectancy'] = display_df['expectancy_r'].apply(lambda x: f"{x:+.3f}R")
    display_df['Total R'] = display_df['total_r'].apply(lambda x: f"{x:+.1f}R")

    # Add best indicator
    display_df['Best'] = display_df['r_ratio'].apply(lambda x: "★" if x == best_r else "")

    # Select and rename columns
    display_df = display_df[[
        'r_label', 'Target %', 'Wins', 'Losses', 'EOD', 'Win Rate', 'Expectancy', 'Total R', 'Best'
    ]]
    display_df.columns = ['Target', 'Target %', 'Wins', 'Losses', 'EOD', 'Win Rate', 'Expectancy', 'Total R', '']

    st.caption(f"Fixed Stop: {stop_pct:.2f}% | Comparing target levels at 1R through 5R")
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    # Show best recommendation
    best_row = df.loc[best_idx]
    st.success(
        f"**Best R:R Ratio: 1:{best_r:.0f}** — "
        f"Win Rate: {best_row['win_rate']:.1f}%, "
        f"Expectancy: {best_row['expectancy_r']:+.3f}R, "
        f"Total R: {best_row['total_r']:+.1f}R"
    )


def render_multi_r_expectancy_chart(df: pd.DataFrame) -> None:
    """
    Bar chart showing expectancy at each R:R ratio.
    """
    if df.empty:
        return

    # Find best for highlighting
    best_idx = df['expectancy_r'].idxmax()

    # Create colors - highlight best
    colors = [
        CHART_COLORS['win'] if i == best_idx else '#4a90d9'
        for i in range(len(df))
    ]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df['r_label'],
        y=df['expectancy_r'],
        marker_color=colors,
        text=df['expectancy_r'].apply(lambda x: f"{x:+.3f}R"),
        textposition='outside'
    ))

    # Add zero line
    fig.add_hline(
        y=0,
        line_dash="dash",
        line_color=CHART_COLORS['reference'],
        annotation_text="Breakeven",
        annotation_position="right"
    )

    fig.update_layout(
        title='Expectancy by Target R-Multiple',
        xaxis_title='Target (R-Multiple)',
        yaxis_title='Expectancy (R)',
        template='plotly_dark',
        paper_bgcolor=CHART_COLORS['paper'],
        plot_bgcolor=CHART_COLORS['background'],
        font_color=CHART_COLORS['text'],
        height=350,
        showlegend=False
    )
    fig.update_xaxes(gridcolor=CHART_COLORS['grid'])
    fig.update_yaxes(gridcolor=CHART_COLORS['grid'])

    st.plotly_chart(fig, use_container_width=True)


def render_multi_r_win_rate_chart(df: pd.DataFrame) -> None:
    """
    Bar chart showing win rate at each R:R ratio.
    """
    if df.empty:
        return

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df['r_label'],
        y=df['win_rate'],
        marker_color='#4a90d9',
        text=df['win_rate'].apply(lambda x: f"{x:.1f}%"),
        textposition='outside'
    ))

    fig.update_layout(
        title='Win Rate by Target R-Multiple',
        xaxis_title='Target (R-Multiple)',
        yaxis_title='Win Rate (%)',
        template='plotly_dark',
        paper_bgcolor=CHART_COLORS['paper'],
        plot_bgcolor=CHART_COLORS['background'],
        font_color=CHART_COLORS['text'],
        height=350,
        showlegend=False
    )
    fig.update_xaxes(gridcolor=CHART_COLORS['grid'])
    fig.update_yaxes(gridcolor=CHART_COLORS['grid'])

    st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# MAIN SECTION RENDERER
# =============================================================================
def render_simulated_outcomes_section(data: List[Dict]) -> Dict[str, Any]:
    """
    Main entry point to render the complete CALC-004 section.

    Call this from app.py to display the full simulated outcomes analysis.

    Args:
        data: List of dicts from mfe_mae_potential table

    Returns:
        Dict containing simulation statistics for Monte AI integration
    """
    st.subheader("Simulated Outcome Analysis")
    st.markdown("*Fixed R:R analysis using M1 bar data*")

    if not data:
        st.warning("No MFE/MAE data available. Ensure mfe_mae_potential table has data.")
        return {}

    # Check M1 bars coverage
    from data.supabase_client import get_client
    db_client = get_client()

    ticker_dates = list(set(
        (t.get('ticker', '').upper(), t.get('date'))
        for t in data
        if t.get('ticker') and t.get('date')
    ))

    coverage = db_client.check_m1_bars_coverage(ticker_dates)

    # Show coverage info
    if coverage['coverage_pct'] < 100:
        st.info(
            f"M1 bar coverage: {coverage['total_available']}/{coverage['total_requested']} "
            f"ticker-dates ({coverage['coverage_pct']:.1f}%). "
            f"Trades without bar data will show as EOD_EXIT."
        )

    # Use fixed stop percentage
    stop_pct = DEFAULT_STOP_PCT

    # =================================================================
    # Multi-R Analysis (1R through 5R targets)
    # =================================================================
    st.markdown("#### R:R Comparison Analysis")
    st.caption(
        f"Comparing 1R, 2R, 3R, 4R, and 5R targets with {stop_pct:.1f}% stop distance"
    )

    # Calculate results for all R ratios
    with st.spinner("Simulating outcomes for 1R-5R targets..."):
        multi_r_df = calculate_multi_r_stats(data, stop_pct, R_RATIOS, db_client)

    if multi_r_df.empty:
        st.warning("No simulation data available.")
        return {}

    # Render comparison table
    render_multi_r_comparison_table(multi_r_df, stop_pct)

    st.markdown("---")

    # Charts side by side
    col1, col2 = st.columns(2)
    with col1:
        render_multi_r_expectancy_chart(multi_r_df)
    with col2:
        render_multi_r_win_rate_chart(multi_r_df)

    st.markdown("---")

    # =================================================================
    # Best R:R - Detailed Model Breakdown
    # =================================================================
    best_idx = multi_r_df['expectancy_r'].idxmax()
    best_r = multi_r_df.loc[best_idx, 'r_ratio']
    best_target_pct = stop_pct * best_r

    st.markdown(f"#### Model Breakdown at Best R:R (1:{best_r:.0f})")

    with st.spinner(f"Loading model breakdown for 1:{best_r:.0f} R:R..."):
        model_df = calculate_simulated_by_model(data, stop_pct, best_target_pct, db_client)

    # Expectancy chart by model
    render_expectancy_by_model_chart(model_df)

    # Model breakdown table
    render_simulated_model_table(model_df, stop_pct, best_target_pct)

    # Outcome distribution chart
    render_outcome_distribution_chart(model_df)

    st.markdown("---")

    # =================================================================
    # Get stats for best R:R for Monte AI
    # =================================================================
    best_stats = multi_r_df.loc[best_idx].to_dict()

    # Monte Carlo Export
    st.markdown("#### Monte Carlo Export")

    mc_params = {
        'simulation_parameters': {
            'stop_pct': stop_pct,
            'r_ratios_analyzed': R_RATIOS,
            'best_r_ratio': best_r,
            'best_target_pct': best_target_pct,
            'simulation_method': 'm1_bars'
        },
        'multi_r_results': multi_r_df.to_dict('records'),
        'best_r_stats': {
            'r_ratio': best_r,
            'target_pct': best_target_pct,
            'win_rate': best_stats['win_rate'],
            'expectancy_r': best_stats['expectancy_r'],
            'total_trades': best_stats['total_trades'],
            'eod_rate': best_stats['eod_rate']
        },
        'm1_bars_coverage': coverage,
        'by_model_direction': model_df.to_dict('records') if not model_df.empty else []
    }

    with st.expander("View Monte Carlo Parameters (JSON)"):
        st.json(mc_params)

    mc_json = json.dumps(mc_params, indent=2)
    st.download_button(
        label="Download Simulation Results",
        data=mc_json,
        file_name=f"simulated_outcomes_stop{stop_pct}_multi_r.json",
        mime="application/json",
        key="calc004_download"
    )

    # Return best stats for Monte AI prompt
    return {
        'total_trades': int(best_stats['total_trades']),
        'wins': int(best_stats['wins']),
        'losses': int(best_stats['losses']),
        'eod_exits': int(best_stats['eod_exits']),
        'resolved_trades': int(best_stats['resolved_trades']),
        'win_rate': float(best_stats['win_rate']),
        'eod_rate': float(best_stats['eod_rate']),
        'expectancy_r': float(best_stats['expectancy_r']),
        'risk_reward': float(best_r),
        'stop_pct': float(stop_pct),
        'target_pct': float(best_target_pct),
        'best_r_ratio': float(best_r),
        'multi_r_summary': [
            {
                'r_ratio': row['r_ratio'],
                'win_rate': row['win_rate'],
                'expectancy_r': row['expectancy_r']
            }
            for _, row in multi_r_df.iterrows()
        ]
    }
