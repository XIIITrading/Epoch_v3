"""
Epoch Trading System - M15 Context Chart Builder
15-minute candlestick showing intermediate context. No entry marker.
Shows zone overlay. No POC lines.
"""

import plotly.graph_objects as go
import pandas as pd
from typing import List, Optional

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import CHART_COLORS
from models.highlight import HighlightTrade
from charts.volume_profile import create_chart_with_vbp, add_volume_profile, add_volume_profile_from_dict
from charts.poc_lines import add_zone_poc_lines
# Ensure TV Dark template is registered
import charts.theme  # noqa: F401


def build_m15_chart(
    bars_m15: pd.DataFrame,
    highlight: HighlightTrade,
    zones: Optional[List[dict]] = None,
    vbp_bars: Optional[pd.DataFrame] = None,
    pocs: Optional[List[float]] = None,
    volume_profile_dict: Optional[dict] = None,
) -> go.Figure:
    """
    Build M15 candlestick chart showing intermediate context.

    Args:
        bars_m15: DataFrame with OHLCV, datetime index
        highlight: HighlightTrade object
        zones: Optional list of zone dicts
        vbp_bars: Optional M15 bars from epoch for VbP calculation
        pocs: Optional list of HVN POC prices

    Returns:
        Plotly Figure
    """
    fig = create_chart_with_vbp(height=380)

    df = pd.DataFrame()

    # Candlestick trace
    if bars_m15 is not None and not bars_m15.empty:
        df = bars_m15.tail(90) if len(bars_m15) > 90 else bars_m15

    # Volume by Price overlay (added first so candles render on top)
    if volume_profile_dict:
        y_lo = float(df['low'].min()) if not df.empty else None
        y_hi = float(df['high'].max()) if not df.empty else None
        add_volume_profile_from_dict(fig, volume_profile_dict, y_min=y_lo, y_max=y_hi)
    else:
        vbp_source = vbp_bars if (vbp_bars is not None and not vbp_bars.empty) else df
        if vbp_source is not None and not vbp_source.empty:
            add_volume_profile(fig, vbp_source)

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
            name='M15',
        ))

    # Zone HVN POC lines (blue=primary, red=secondary)
    add_zone_poc_lines(fig, zones, highlight)

    # Layout
    title_text = f"15-Minute  |  {highlight.ticker}  |  {highlight.date}"

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
        tickformat='%m/%d %H:%M',
        showgrid=False,
    )

    fig.update_yaxes(side='right')

    return fig
