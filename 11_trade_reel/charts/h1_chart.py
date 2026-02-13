"""
Epoch Trading System - H1 Context Chart Builder
Hourly candlestick showing market context. No entry marker.
Shows zone overlay and HVN POC lines.
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

# Ensure TV Dark template is registered
import charts.theme  # noqa: F401


def build_h1_chart(
    bars_h1: pd.DataFrame,
    highlight: HighlightTrade,
    zones: Optional[List[dict]] = None,
    vbp_bars: Optional[pd.DataFrame] = None,
    pocs: Optional[List[float]] = None,
    volume_profile_dict: Optional[dict] = None,
) -> go.Figure:
    """
    Build H1 candlestick chart showing market context.

    Args:
        bars_h1: DataFrame with OHLCV, datetime index
        highlight: HighlightTrade object
        zones: Optional list of zone dicts
        vbp_bars: Optional M15 bars from epoch for VbP calculation
        pocs: Optional list of HVN POC prices

    Returns:
        Plotly Figure
    """
    fig = create_chart_with_vbp(height=380)

    df = pd.DataFrame()

    # Volume by Price overlay (added first so candles render on top)
    if bars_h1 is not None and not bars_h1.empty:
        df = bars_h1.tail(120) if len(bars_h1) > 120 else bars_h1

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
            name='H1',
        ))

    # Zone overlay
    if highlight.zone_high and highlight.zone_low:
        fig.add_hrect(
            y0=highlight.zone_low,
            y1=highlight.zone_high,
            fillcolor=CHART_COLORS['zone_fill'],
            line_width=1,
            line_color=CHART_COLORS['zone_border'],
            opacity=0.8,
        )

    # Layout
    title_text = f"1-Hour  |  {highlight.ticker}  |  {highlight.date}"

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
