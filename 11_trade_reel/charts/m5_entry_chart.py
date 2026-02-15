"""
Epoch Trading System - M5 Entry Chart Builder
Shows 120 M5 bars before entry + the entry bar as the last candle.
No entry triangle marker. Zone HVN POC lines, VbP overlay.
Y-axis auto-ranged to data min/max with 5px buffer.
"""

import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from typing import List, Optional
import pytz

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import CHART_COLORS, DISPLAY_TIMEZONE

_TZ = pytz.timezone(DISPLAY_TIMEZONE)
from models.highlight import HighlightTrade
from charts.volume_profile import create_chart_with_vbp, add_volume_profile, add_volume_profile_from_dict
from charts.poc_lines import add_poc_lines, add_zone_poc_lines

# Ensure TV Dark template is registered
import charts.theme  # noqa: F401

# Chart pixel height for buffer calculation
M5_CHART_HEIGHT = 420
BUFFER_PX = 5


def _slice_entry_window(bars_m5: pd.DataFrame, highlight: HighlightTrade) -> pd.DataFrame:
    """Slice M5 bars: 120 bars before entry + entry bar (121 total)."""
    if bars_m5 is None or bars_m5.empty or not highlight.entry_time:
        return pd.DataFrame()

    entry_dt = _TZ.localize(datetime.combine(highlight.date, highlight.entry_time))

    # Find bars at or before entry
    mask = bars_m5.index <= entry_dt
    bars_up_to_entry = bars_m5[mask]

    if bars_up_to_entry.empty:
        return pd.DataFrame()

    # Take last 121 bars (120 before + entry bar)
    return bars_up_to_entry.tail(121)


def build_m5_entry_chart(
    bars_m5: pd.DataFrame,
    highlight: HighlightTrade,
    zones: Optional[List[dict]] = None,
    vbp_bars: Optional[pd.DataFrame] = None,
    pocs: Optional[List[float]] = None,
    volume_profile_dict: Optional[dict] = None,
) -> go.Figure:
    """
    Build M5 Entry chart: 120 bars before entry + entry bar as last candle.

    Args:
        bars_m5: Full M5 DataFrame with OHLCV, datetime index
        highlight: HighlightTrade object
        zones: Optional zone dicts
        vbp_bars: Optional M15 bars from epoch for VbP calculation
        pocs: Optional list of HVN POC prices

    Returns:
        Plotly Figure
    """
    fig = create_chart_with_vbp(height=M5_CHART_HEIGHT)

    df = _slice_entry_window(bars_m5, highlight)

    # Volume by Price overlay (added first so candles render on top)
    if volume_profile_dict:
        y_lo = float(df['low'].min()) if not df.empty else None
        y_hi = float(df['high'].max()) if not df.empty else None
        add_volume_profile_from_dict(fig, volume_profile_dict, y_min=y_lo, y_max=y_hi)
    else:
        vbp_source = vbp_bars if (vbp_bars is not None and not vbp_bars.empty) else df
        if vbp_source is not None and not vbp_source.empty:
            add_volume_profile(fig, vbp_source)

    # Candlestick trace
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
            name='M5',
        ))

    # Zone HVN POC lines (blue=primary, red=secondary)
    add_zone_poc_lines(fig, zones, highlight)

    # Auto Y-range from visible data with 5px buffer
    y_range = _calc_y_range(df, M5_CHART_HEIGHT, BUFFER_PX)

    # Layout
    title_text = f"5-Minute Entry  |  {highlight.ticker}  |  {highlight.date}"

    fig.update_layout(
        title=dict(text=title_text, font=dict(size=14), x=0.5, xanchor='center'),
        height=M5_CHART_HEIGHT,
        showlegend=False,
        margin=dict(l=10, r=60, t=45, b=30),
        xaxis_rangeslider_visible=False,
    )

    fig.update_xaxes(
        rangebreaks=[
            dict(bounds=["sat", "mon"]),
            dict(bounds=[20, 4], pattern="hour"),
        ],
        type='date',
        tickformat='%H:%M',
        showgrid=False,
    )

    if y_range:
        fig.update_yaxes(side='right', range=y_range)
    else:
        fig.update_yaxes(side='right')

    return fig


def _calc_y_range(df: pd.DataFrame, chart_height: int, buffer_px: int):
    """
    Calculate Y-axis range from data min/max with pixel buffer.
    Converts pixel buffer to price units based on chart height.

    Returns:
        (y_min, y_max) tuple or None if no data
    """
    if df is None or df.empty:
        return None

    data_low = df['low'].min()
    data_high = df['high'].max()
    price_range = data_high - data_low

    if price_range <= 0:
        return None

    # Convert pixel buffer to price units
    # Chart area height = chart_height - top margin(45) - bottom margin(30) = usable pixels
    usable_px = chart_height - 45 - 30
    if usable_px <= 0:
        usable_px = chart_height

    price_per_px = price_range / usable_px
    buffer_price = buffer_px * price_per_px

    return [data_low - buffer_price, data_high + buffer_price]
