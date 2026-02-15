"""
Epoch Trading System - M1 Ramp-Up Chart Builder
M1 candlestick showing 180 bars leading up to entry.
Zone HVN POC lines. Intraday Value VbP sidebar (04:00 ET → entry).
"""

import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from typing import List, Optional, Dict
import pytz

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import CHART_COLORS, DISPLAY_TIMEZONE

_TZ = pytz.timezone(DISPLAY_TIMEZONE)
from models.highlight import HighlightTrade
from charts.poc_lines import add_zone_poc_lines
from charts.volume_profile import build_volume_profile, add_volume_profile_from_dict

# Ensure TV Dark template is registered
import charts.theme  # noqa: F401

# Number of M1 candles to show on the ramp-up chart
RAMPUP_CHART_BARS = 180


def _slice_rampup_window(bars_m1: pd.DataFrame, highlight: HighlightTrade) -> pd.DataFrame:
    """Slice M1 bars: 180 bars before entry + entry bar (181 total)."""
    if bars_m1 is None or bars_m1.empty or not highlight.entry_time:
        return pd.DataFrame()

    entry_dt = _TZ.localize(datetime.combine(highlight.date, highlight.entry_time))

    # Find bars at or before entry
    mask = bars_m1.index <= entry_dt
    bars_up_to_entry = bars_m1[mask]

    if bars_up_to_entry.empty:
        return pd.DataFrame()

    # Take last RAMPUP_CHART_BARS + 1 (180 before + entry bar)
    return bars_up_to_entry.tail(RAMPUP_CHART_BARS + 1)


def build_m1_rampup_chart(
    bars_m1: pd.DataFrame,
    highlight: HighlightTrade,
    zones: Optional[List[dict]] = None,
    pocs: Optional[List[float]] = None,
    intraday_vbp_dict: Optional[Dict[float, float]] = None,
) -> go.Figure:
    """
    Build M1 ramp-up candlestick chart showing 180 bars before entry.

    Args:
        bars_m1: Full M1 DataFrame from Polygon (datetime-indexed, tz-aware)
        highlight: HighlightTrade object
        zones: Optional zone dicts
        pocs: Optional list of HVN POC prices
        intraday_vbp_dict: Optional pre-computed volume profile dict (04:00→entry)

    Returns:
        Plotly Figure
    """
    fig = go.Figure()

    df = _slice_rampup_window(bars_m1, highlight)

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
            name='M1',
        ))

    # Zone HVN POC lines (blue=primary, red=secondary)
    add_zone_poc_lines(fig, zones, highlight)

    # Calculate Y-range from visible candle data
    y_range = None
    if not df.empty:
        data_low = float(df['low'].min())
        data_high = float(df['high'].max())
        price_range = data_high - data_low
        if price_range > 0:
            buffer = price_range * 0.02
            y_range = [data_low - buffer, data_high + buffer]

    # Intraday Value VbP sidebar (04:00 ET → entry)
    if intraday_vbp_dict and y_range:
        add_volume_profile_from_dict(fig, intraday_vbp_dict, y_min=y_range[0], y_max=y_range[1])
    elif intraday_vbp_dict:
        add_volume_profile_from_dict(fig, intraday_vbp_dict)

    # Layout
    title_text = f"1-Minute Ramp-Up  |  {highlight.ticker}  |  {highlight.date}"

    fig.update_layout(
        title=dict(text=title_text, font=dict(size=14), x=0.5, xanchor='center'),
        height=380,
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
