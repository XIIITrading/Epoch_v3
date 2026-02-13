"""
Epoch Trading System - Ramp-Up Chart Component
Displays M1 candlestick chart with vertical indicator table below each bar.
Similar to TradingView ramp-up chart visualization.

Data is fetched from pre-computed m1_indicator_bars table.
Calculations are performed by 09_backtest/processor/secondary_analysis/m1_indicator_bars.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, date, time
from typing import Dict, List, Optional, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import CHART_CONFIG, DB_CONFIG

# Number of bars to show before entry
RAMPUP_BARS = 45


# =============================================================================
# COLOR CONFIGURATION
# =============================================================================

# Indicator cell colors (based on value thresholds)
COLORS = {
    # Structure (BULL/BEAR/NEUTRAL)
    'structure_bull': '#26a69a',
    'structure_bear': '#ef5350',
    'structure_neutral': '#888888',

    # Volume ROC (positive/negative relative to threshold)
    'vol_roc_high': '#26a69a',     # Above 30%
    'vol_roc_mid': '#ffc107',      # 0-30%
    'vol_roc_low': '#ef5350',      # Negative

    # Volume Delta (positive/negative)
    'vol_delta_positive': '#26a69a',
    'vol_delta_negative': '#ef5350',

    # Candle Range % (good/ok/skip)
    'candle_range_good': '#26a69a',   # >= 0.15%
    'candle_range_ok': '#888888',     # 0.12-0.15%
    'candle_range_skip': '#ef5350',   # < 0.12%

    # SMA Config (BULL/BEAR)
    'sma_bull': '#26a69a',
    'sma_bear': '#ef5350',

    # Composite Score (0-7)
    'score_high': '#26a69a',       # 5-7
    'score_mid': '#ffc107',        # 3-4
    'score_low': '#ef5350',        # 0-2

    # Default
    'default': '#666666',
    'text': '#ffffff',
    'text_muted': '#aaaaaa',
}

# Indicator row labels (displayed vertically below chart)
# Updated based on EPCH Indicators v1.0 spec
INDICATOR_LABELS = [
    'Candle %',    # candle_range_pct - format: 0.18%
    'Vol Delta',   # vol_delta - format: +2.5M, -800k
    'Vol ROC',     # vol_roc - format: +45%, -12%
    'SMA',         # sma config + spread - format: BULL 0.15%
    'H1 Struct',   # h1_structure - format: BULL/BEAR/NEUT
    'LONG',        # long_score - format: 0-7
    'SHORT',       # short_score - format: 0-7
]


# =============================================================================
# DATA FETCHING
# =============================================================================

def fetch_m1_bars_for_rampup(
    ticker: str,
    trade_date: date,
    entry_time: time,
    num_bars: int = RAMPUP_BARS
) -> pd.DataFrame:
    """
    Fetch M1 indicator bars from database for ramp-up chart.

    Args:
        ticker: Stock symbol
        trade_date: Trading date
        entry_time: Entry time
        num_bars: Number of bars before entry to fetch

    Returns:
        DataFrame with M1 bars and indicators
    """
    query = """
        SELECT
            ticker, bar_date, bar_time,
            open, high, low, close, volume,
            vwap, sma9, sma21, sma_spread,
            vol_roc, vol_delta,
            h1_structure,
            candle_range_pct, long_score, short_score
        FROM m1_indicator_bars
        WHERE ticker = %s
          AND bar_date = %s
          AND bar_time < %s
        ORDER BY bar_time DESC
        LIMIT %s
    """

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (ticker, trade_date, entry_time, num_bars))
            rows = cur.fetchall()
        conn.close()

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame([dict(row) for row in rows])
        # Reverse to get chronological order (oldest first)
        df = df.iloc[::-1].reset_index(drop=True)

        return df

    except Exception as e:
        print(f"Error fetching M1 bars: {e}")
        return pd.DataFrame()


# =============================================================================
# COLOR HELPERS
# =============================================================================

def _to_float(val) -> Optional[float]:
    """Convert value to float, handling Decimal and None."""
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def get_candle_range_color(pct) -> str:
    """Get color for candle range percentage."""
    pct = _to_float(pct)
    if pct is None:
        return COLORS['default']
    if pct >= 0.15:
        return COLORS['candle_range_good']
    elif pct >= 0.12:
        return COLORS['candle_range_ok']
    else:
        return COLORS['candle_range_skip']


def get_vol_delta_color(vol_delta) -> str:
    """Get color for volume delta."""
    vol_delta = _to_float(vol_delta)
    if vol_delta is None:
        return COLORS['default']
    if vol_delta > 0:
        return COLORS['vol_delta_positive']
    else:
        return COLORS['vol_delta_negative']


def get_vol_roc_color(vol_roc) -> str:
    """Get color for volume ROC."""
    vol_roc = _to_float(vol_roc)
    if vol_roc is None:
        return COLORS['default']
    if vol_roc >= 30:
        return COLORS['vol_roc_high']
    elif vol_roc >= 0:
        return COLORS['vol_roc_mid']
    else:
        return COLORS['vol_roc_low']


def get_sma_config_color(sma_spread) -> str:
    """Get color for SMA configuration."""
    sma_spread = _to_float(sma_spread)
    if sma_spread is None:
        return COLORS['default']
    if sma_spread > 0:  # SMA9 > SMA21 = bullish
        return COLORS['sma_bull']
    else:
        return COLORS['sma_bear']


def get_structure_color(structure: Optional[str]) -> str:
    """Get color for market structure."""
    if structure == 'BULL':
        return COLORS['structure_bull']
    elif structure == 'BEAR':
        return COLORS['structure_bear']
    else:
        return COLORS['structure_neutral']


def get_score_color(score) -> str:
    """Get color for composite score (0-7)."""
    if score is None:
        return COLORS['default']
    try:
        score = int(score)
    except (TypeError, ValueError):
        return COLORS['default']
    if score >= 5:
        return COLORS['score_high']
    elif score >= 3:
        return COLORS['score_mid']
    else:
        return COLORS['score_low']


# =============================================================================
# VALUE FORMATTERS
# =============================================================================

def format_candle_range(pct) -> str:
    """Format candle range percentage for display."""
    pct = _to_float(pct)
    if pct is None:
        return '-'
    return f"{pct:.2f}"


def format_vol_delta(vol_delta) -> str:
    """Format volume delta for display."""
    vol_delta = _to_float(vol_delta)
    if vol_delta is None:
        return '-'
    # Show abbreviated value with sign
    prefix = '+' if vol_delta > 0 else ''
    abs_val = abs(vol_delta)
    if abs_val >= 1000000:
        return f"{prefix}{vol_delta/1000000:.1f}M"
    elif abs_val >= 1000:
        return f"{prefix}{vol_delta/1000:.0f}K"
    else:
        return f"{prefix}{vol_delta:.0f}"


def format_vol_roc(vol_roc) -> str:
    """Format volume ROC for display."""
    vol_roc = _to_float(vol_roc)
    if vol_roc is None:
        return '-'
    prefix = '+' if vol_roc > 0 else ''
    return f"{prefix}{vol_roc:.0f}%"


def format_sma_config(sma_spread, close) -> str:
    """Format SMA configuration for display (BULL/BEAR + spread %)."""
    sma_spread = _to_float(sma_spread)
    close = _to_float(close)
    if sma_spread is None or close is None or close == 0:
        return '-'
    config = 'B' if sma_spread > 0 else 'S'  # B=Bullish, S=Bearish (short)
    spread_pct = abs(sma_spread) / close * 100
    return f"{config}{spread_pct:.2f}"


def format_structure(structure: Optional[str]) -> str:
    """Format structure for display using triangle symbols."""
    if structure is None:
        return '-'
    if structure.upper() == 'BULL':
        return '▲'  # Upward triangle for bullish
    elif structure.upper() == 'BEAR':
        return '▼'  # Downward triangle for bearish
    else:
        return '─'  # Neutral dash


def format_score(score) -> str:
    """Format composite score for display."""
    if score is None:
        return '-'
    try:
        return str(int(score))
    except (TypeError, ValueError):
        return '-'


# =============================================================================
# CHART BUILDER
# =============================================================================

def build_rampup_chart(
    df: pd.DataFrame,
    trade_date: date,
    entry_time: time,
    direction: str = 'LONG'
) -> go.Figure:
    """
    Build the ramp-up chart with candlesticks and indicator table.

    Args:
        df: DataFrame with M1 bars and indicators
        trade_date: Trading date
        entry_time: Entry time (for title)
        direction: Trade direction ('LONG' or 'SHORT')

    Returns:
        Plotly Figure object
    """
    if df.empty:
        # Return empty figure with message
        fig = go.Figure()
        fig.add_annotation(
            text="No M1 indicator data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=11, color=COLORS['text_muted'])
        )
        fig.update_layout(
            height=300,
            paper_bgcolor=CHART_CONFIG['paper_color'],
            plot_bgcolor=CHART_CONFIG['background_color'],
        )
        return fig

    num_bars = len(df)
    num_indicators = len(INDICATOR_LABELS)

    # Create subplots: candlestick on top, table below
    # Row heights: 60% for chart, 40% for indicator table
    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.6, 0.4],
        vertical_spacing=0.02,
        shared_xaxes=True,
        specs=[
            [{"type": "xy"}],      # Candlestick
            [{"type": "xy"}],      # Indicator table (as heatmap-style)
        ]
    )

    # Create x-axis values (bar indices)
    x_vals = list(range(num_bars))
    x_labels = [row['bar_time'].strftime('%H:%M') if hasattr(row['bar_time'], 'strftime')
                else str(row['bar_time'])[:5] for _, row in df.iterrows()]

    # ==========================================================================
    # ROW 1: CANDLESTICK CHART
    # ==========================================================================

    fig.add_trace(
        go.Candlestick(
            x=x_vals,
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            increasing_line_color=CHART_CONFIG['candle_up_color'],
            decreasing_line_color=CHART_CONFIG['candle_down_color'],
            increasing_fillcolor=CHART_CONFIG['candle_up_color'],
            decreasing_fillcolor=CHART_CONFIG['candle_down_color'],
            showlegend=False,
            name='M1'
        ),
        row=1, col=1
    )

    # Add SMA9 and SMA21 lines if available
    if 'sma9' in df.columns and df['sma9'].notna().any():
        fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=df['sma9'],
                mode='lines',
                line=dict(color='#2196f3', width=1),
                name='SMA9',
                showlegend=False
            ),
            row=1, col=1
        )

    if 'sma21' in df.columns and df['sma21'].notna().any():
        fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=df['sma21'],
                mode='lines',
                line=dict(color='#ff9800', width=1),
                name='SMA21',
                showlegend=False
            ),
            row=1, col=1
        )

    # Add VWAP line if available
    if 'vwap' in df.columns and df['vwap'].notna().any():
        fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=df['vwap'],
                mode='lines',
                line=dict(color='#9c27b0', width=1, dash='dot'),
                name='VWAP',
                showlegend=False
            ),
            row=1, col=1
        )

    # ==========================================================================
    # ROW 2: INDICATOR TABLE (colored text on chart background)
    # ==========================================================================

    # Build indicator values and colors for each bar
    # Use same background as chart with grid lines for consistency
    for indicator_idx, indicator_name in enumerate(INDICATOR_LABELS):
        y_pos = num_indicators - indicator_idx - 0.5  # Position from top

        for bar_idx, (_, row) in enumerate(df.iterrows()):
            # Get value and color based on indicator type
            if indicator_name == 'Candle %':
                value = format_candle_range(row.get('candle_range_pct'))
                text_color = get_candle_range_color(row.get('candle_range_pct'))
            elif indicator_name == 'Vol Delta':
                value = format_vol_delta(row.get('vol_delta'))
                text_color = get_vol_delta_color(row.get('vol_delta'))
            elif indicator_name == 'Vol ROC':
                value = format_vol_roc(row.get('vol_roc'))
                text_color = get_vol_roc_color(row.get('vol_roc'))
            elif indicator_name == 'SMA':
                close = row.get('close')
                sma_spread = row.get('sma_spread')
                value = format_sma_config(sma_spread, close)
                text_color = get_sma_config_color(sma_spread)
            elif indicator_name == 'H1 Struct':
                value = format_structure(row.get('h1_structure'))
                text_color = get_structure_color(row.get('h1_structure'))
            elif indicator_name == 'LONG':
                value = format_score(row.get('long_score'))
                text_color = get_score_color(row.get('long_score'))
            elif indicator_name == 'SHORT':
                value = format_score(row.get('short_score'))
                text_color = get_score_color(row.get('short_score'))
            else:
                value = '-'
                text_color = COLORS['default']

            # Add colored text value (no cell background - uses chart background)
            fig.add_annotation(
                x=bar_idx,
                y=y_pos,
                text=value,
                showarrow=False,
                font=dict(size=16, color=text_color, weight='bold'),
                xref="x2",
                yref="y2"
            )

    # Add indicator labels on the left
    for indicator_idx, indicator_name in enumerate(INDICATOR_LABELS):
        y_pos = num_indicators - indicator_idx - 0.5
        fig.add_annotation(
            x=-1.2,
            y=y_pos,
            text=indicator_name,
            showarrow=False,
            font=dict(size=14, color=COLORS['text_muted']),
            xanchor='right',
            xref="x2",
            yref="y2"
        )

    # ==========================================================================
    # LAYOUT
    # ==========================================================================

    fig.update_layout(
        title=dict(
            text=f"M1 Ramp-Up | Entry: {entry_time.strftime('%H:%M') if hasattr(entry_time, 'strftime') else entry_time}",
            font=dict(size=12, color=CHART_CONFIG['text_color']),
            x=0.5,
            xanchor='center'
        ),
        height=550,
        paper_bgcolor=CHART_CONFIG['paper_color'],
        plot_bgcolor=CHART_CONFIG['background_color'],
        font=dict(color=CHART_CONFIG['text_color']),
        showlegend=False,
        margin=dict(l=80, r=20, t=40, b=30),
    )

    # Update candlestick axes
    fig.update_xaxes(
        showgrid=True,
        gridcolor=CHART_CONFIG['grid_color'],
        showticklabels=False,
        rangeslider_visible=False,
        row=1, col=1
    )

    fig.update_yaxes(
        showgrid=True,
        gridcolor=CHART_CONFIG['grid_color'],
        side='right',
        row=1, col=1
    )

    # Update indicator table axes - enable grid for consistent look
    fig.update_xaxes(
        range=[-1.5, num_bars - 0.5],
        tickmode='array',
        tickvals=x_vals,
        ticktext=x_labels,
        tickfont=dict(size=8),
        showgrid=True,
        gridcolor=CHART_CONFIG['grid_color'],
        row=2, col=1
    )

    fig.update_yaxes(
        range=[0, num_indicators],
        showticklabels=False,
        showgrid=True,
        gridcolor=CHART_CONFIG['grid_color'],
        dtick=1,  # Grid line for each row
        row=2, col=1
    )

    return fig


# =============================================================================
# MAIN RENDER FUNCTION
# =============================================================================

def render_rampup_chart(
    ticker: str,
    trade_date: date,
    entry_time: time,
    direction: str = 'LONG'
) -> Optional[go.Figure]:
    """
    Render the complete ramp-up chart for a trade.

    Args:
        ticker: Stock symbol
        trade_date: Trading date
        entry_time: Entry time
        direction: Trade direction

    Returns:
        Plotly Figure or None if no data
    """
    # Fetch M1 bars
    df = fetch_m1_bars_for_rampup(ticker, trade_date, entry_time, RAMPUP_BARS)

    # Build chart
    fig = build_rampup_chart(df, trade_date, entry_time, direction)

    return fig


# =============================================================================
# STANDALONE TEST
# =============================================================================

if __name__ == "__main__":
    print("Ramp-Up Chart - Standalone Test")
    print("=" * 60)

    # Test with sample data
    test_ticker = "SPY"
    test_date = date(2025, 1, 10)
    test_time = time(10, 30)

    print(f"\nFetching M1 bars for {test_ticker} on {test_date} before {test_time}...")
    df = fetch_m1_bars_for_rampup(test_ticker, test_date, test_time)

    if not df.empty:
        print(f"  Found {len(df)} bars")
        print(f"  First bar: {df.iloc[0]['bar_time']}")
        print(f"  Last bar: {df.iloc[-1]['bar_time']}")

        # Build chart
        fig = build_rampup_chart(df, test_date, test_time, 'LONG')
        print("\nChart built successfully!")

        # Show chart (requires browser)
        fig.show()
    else:
        print("  No data found")

    print("\nDone.")
