"""
Epoch Trading System - M1 Ramp-Up Chart Builder
M1 candlestick showing the bars leading up to entry (same window as ramp-up table).
Zone overlay, HVN POC lines. No VbP sidebar (plain figure).
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
from charts.poc_lines import add_poc_lines

# Ensure TV Dark template is registered
import charts.theme  # noqa: F401


def build_m1_rampup_chart(
    rampup_df: pd.DataFrame,
    highlight: HighlightTrade,
    zones: Optional[List[dict]] = None,
    pocs: Optional[List[float]] = None,
) -> go.Figure:
    """
    Build M1 ramp-up candlestick chart from the same data as the ramp-up table.
    Shows M1 bars leading up to entry.

    Args:
        rampup_df: DataFrame from fetch_rampup_data() with OHLCV + bar_time columns
        highlight: HighlightTrade object
        zones: Optional zone dicts
        pocs: Optional list of HVN POC prices

    Returns:
        Plotly Figure
    """
    fig = go.Figure()

    if rampup_df is not None and not rampup_df.empty:
        # Build datetime index from bar_date + bar_time
        timestamps = []
        for _, row in rampup_df.iterrows():
            bar_date = row.get('bar_date', highlight.date)
            bar_time = row.get('bar_time')
            if bar_date and bar_time:
                dt = _TZ.localize(datetime.combine(bar_date, bar_time))
                timestamps.append(dt)
            else:
                timestamps.append(None)

        df = rampup_df.copy()
        df['dt'] = timestamps
        df = df.dropna(subset=['dt'])

        if not df.empty:
            fig.add_trace(go.Candlestick(
                x=df['dt'],
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

    # HVN POC lines (no row/col needed — plain figure)
    if pocs:
        for price in pocs:
            if price and price > 0:
                fig.add_hline(
                    y=price,
                    line_color='#FFFFFF',
                    line_width=1.0,
                    line_dash='dot',
                    opacity=0.3,
                )

    # Calculate Y-range from visible candle data (not zones/POCs)
    # Cast to float because DB may return decimal.Decimal
    y_range = None
    if rampup_df is not None and not rampup_df.empty:
        data_low = float(rampup_df['low'].min())
        data_high = float(rampup_df['high'].max())
        price_range = data_high - data_low
        if price_range > 0:
            # Add small buffer (~2% of range) so candles aren't edge-to-edge
            buffer = price_range * 0.02
            y_range = [data_low - buffer, data_high + buffer]

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
