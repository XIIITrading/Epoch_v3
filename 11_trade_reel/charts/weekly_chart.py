"""
Epoch Trading System - Weekly Context Chart Builder
90-candle weekly chart from Polygon weekly bars.
Zone POC lines, volume bars. No VbP overlay.
"""

import plotly.graph_objects as go
import pandas as pd
from typing import List, Optional

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import CHART_COLORS
from models.highlight import HighlightTrade
from charts.volume_profile import add_volume_bars, CANDLE_DOMAIN_BOTTOM, VOL_CLEARANCE_FRAC

# Ensure TV Dark template is registered
import charts.theme  # noqa: F401

# Constants
WEEKLY_BARS = 90
BUFFER_PX = 10


def build_weekly_chart(
    bars_weekly: pd.DataFrame,
    highlight: HighlightTrade,
    zones: Optional[List[dict]] = None,
) -> go.Figure:
    """
    Build 90-candle weekly chart from Polygon weekly bars.

    Args:
        bars_weekly: Weekly OHLCV DataFrame from Polygon
        highlight: HighlightTrade object
        zones: Optional zone dicts

    Returns:
        Plotly Figure
    """
    fig = go.Figure()

    # Take last 90 weekly bars
    if bars_weekly is not None and not bars_weekly.empty:
        df = bars_weekly.tail(WEEKLY_BARS) if len(bars_weekly) > WEEKLY_BARS else bars_weekly
    else:
        df = pd.DataFrame()

    if not df.empty:
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            increasing_line_color=CHART_COLORS['candle_up'],
            decreasing_line_color=CHART_COLORS['candle_down'],
            increasing_fillcolor=CHART_COLORS['candle_up'],
            decreasing_fillcolor=CHART_COLORS['candle_down'],
            showlegend=False,
            name='W1',
        ))

    # Volume bars (TradingView-style, bottom of chart)
    if not df.empty:
        add_volume_bars(fig, df)

    # Y-range with 10px buffer
    y_range = _calc_y_range(df, 380, BUFFER_PX)

    # Layout
    title_text = f"Weekly  |  {highlight.ticker}  |  {highlight.date}"

    fig.update_layout(
        title=dict(text=title_text, font=dict(size=14), x=0.5, xanchor='center'),
        height=380,
        showlegend=False,
        margin=dict(l=10, r=60, t=45, b=30),
        xaxis_rangeslider_visible=False,
        yaxis=dict(domain=[CANDLE_DOMAIN_BOTTOM, 1.0]),
    )

    fig.update_xaxes(
        type='date',
        dtick='M1',
        tickformat='%b',
        tickangle=0,
        showgrid=False,
    )

    if y_range:
        fig.update_yaxes(side='right', range=y_range)
    else:
        fig.update_yaxes(side='right')

    return fig


def _calc_y_range(df: pd.DataFrame, chart_height: int, buffer_px: int):
    """Calculate Y-axis range with pixel buffer and volume bar clearance.

    Extends the bottom of the y-range so the lowest candle sits above the
    volume bars (which occupy the bottom VOL_BAR_MAX_HEIGHT of the chart).
    Top gets a standard pixel buffer.
    """
    if df is None or df.empty:
        return None

    data_low = df['low'].min()
    data_high = df['high'].max()
    price_range = data_high - data_low

    if price_range <= 0:
        return None

    # Top buffer: convert pixels to price units
    usable_px = chart_height - 45 - 30  # subtract top/bottom margins
    if usable_px <= 0:
        usable_px = chart_height
    price_per_px = price_range / usable_px
    top_buffer = buffer_px * price_per_px

    # Bottom buffer: extend y-range so data_low maps to VOL_CLEARANCE_FRAC
    # of chart height (above volume bars).  Formula: if data occupies the
    # range [data_low, data_high+top] and we want data_low at frac from
    # bottom, then total_range = visible_range / (1 - frac).
    visible_range = price_range + top_buffer
    total_range = visible_range / (1.0 - VOL_CLEARANCE_FRAC)
    bottom_extension = total_range - visible_range

    return [data_low - bottom_extension, data_high + top_buffer]
