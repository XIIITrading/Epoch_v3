"""
Epoch Trading System - M1 Action Chart Builder
1-minute candlestick from entry to 5 bars after exit.
"""

import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional
import pytz

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import CHART_COLORS, DISPLAY_TIMEZONE

_TZ = pytz.timezone(DISPLAY_TIMEZONE)
from models.highlight import HighlightTrade

# Ensure TV Dark template is registered
import charts.theme  # noqa: F401

# Map R-level number to color
R_COLORS = {
    1: CHART_COLORS['r1'],
    2: CHART_COLORS['r2'],
    3: CHART_COLORS['r3'],
    4: CHART_COLORS['r4'],
    5: CHART_COLORS['r5'],
}

# How many bars after exit to show
BARS_AFTER_EXIT = 5


def build_m1_chart(
    bars_m1: pd.DataFrame,
    highlight: HighlightTrade,
    zones: Optional[List[dict]] = None
) -> go.Figure:
    """
    Build M1 candlestick chart from entry to 5 bars after exit.

    Args:
        bars_m1: Full-day M1 DataFrame with OHLCV, datetime index
        highlight: HighlightTrade object
        zones: Optional zone dicts

    Returns:
        Plotly Figure
    """
    fig = go.Figure()

    # Slice bars to the relevant window
    df = _slice_to_window(bars_m1, highlight)

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

    # Entry marker — prominent (larger, bright)
    if highlight.entry_time and highlight.entry_price:
        entry_dt = _TZ.localize(datetime.combine(highlight.date, highlight.entry_time))
        symbol = 'triangle-up' if highlight.direction == 'LONG' else 'triangle-down'
        text_pos = 'top center' if highlight.direction == 'LONG' else 'bottom center'

        fig.add_trace(go.Scatter(
            x=[entry_dt],
            y=[highlight.entry_price],
            mode='markers+text',
            marker=dict(symbol=symbol, size=14, color=CHART_COLORS['entry'],
                        line=dict(color='white', width=1.5)),
            text=['ENTRY'],
            textposition=text_pos,
            textfont=dict(color=CHART_COLORS['entry'], size=10, family='Arial Black'),
            showlegend=False,
            hoverinfo='text',
            hovertext=f"Entry ${highlight.entry_price:.2f}",
        ))

    # R-level lines — intermediate levels subdued, highest R prominent
    r_levels = [
        (1, highlight.r1_price, highlight.r1_hit),
        (2, highlight.r2_price, highlight.r2_hit),
        (3, highlight.r3_price, highlight.r3_hit),
        (4, highlight.r4_price, highlight.r4_hit),
        (5, highlight.r5_price, highlight.r5_hit),
    ]

    for r_num, price, hit in r_levels:
        if price and hit:
            color = R_COLORS.get(r_num, '#787B86')
            is_highest = (r_num == highlight.max_r_achieved)
            fig.add_hline(
                y=price,
                line_color=color,
                line_width=1.5 if is_highest else 0.8,
                line_dash='solid' if is_highest else 'dot',
                opacity=0.5 if is_highest else 0.2,
                annotation_text=f"R{r_num}",
                annotation_position="right",
                annotation_font_color=color,
                annotation_font_size=10 if is_highest else 8,
            )

    # R-level hit markers — highest R is star (large, bright), others subdued diamonds
    r_hits = [
        (1, highlight.r1_time, highlight.r1_price, highlight.r1_hit),
        (2, highlight.r2_time, highlight.r2_price, highlight.r2_hit),
        (3, highlight.r3_time, highlight.r3_price, highlight.r3_hit),
        (4, highlight.r4_time, highlight.r4_price, highlight.r4_hit),
        (5, highlight.r5_time, highlight.r5_price, highlight.r5_hit),
    ]

    for r_num, r_time, r_price, r_hit in r_hits:
        if r_hit and r_time and r_price:
            r_dt = _TZ.localize(datetime.combine(highlight.date, r_time))
            color = R_COLORS.get(r_num, '#787B86')
            is_highest = (r_num == highlight.max_r_achieved)

            fig.add_trace(go.Scatter(
                x=[r_dt],
                y=[r_price],
                mode='markers+text',
                marker=dict(
                    symbol='star' if is_highest else 'diamond',
                    size=16 if is_highest else 7,
                    color=color,
                    line=dict(color='white', width=2 if is_highest else 0.5),
                ),
                text=[f"R{r_num}" if is_highest else ''],
                textposition='top center',
                textfont=dict(color=color, size=11 if is_highest else 8,
                              family='Arial Black'),
                showlegend=False,
                hovertext=f"R{r_num} hit at {r_time.strftime('%H:%M')} | ${r_price:.2f}",
                hoverinfo='text',
            ))

    # Stop line
    if highlight.stop_price:
        fig.add_hline(
            y=highlight.stop_price,
            line_color=CHART_COLORS['stop'],
            line_width=1,
            line_dash='dash',
            opacity=0.5,
        )

    # Layout
    title_text = f"1-Minute  |  {highlight.ticker}  |  {highlight.date}"

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

    fig.update_yaxes(side='right')

    return fig


def _slice_to_window(
    bars_m1: pd.DataFrame,
    highlight: HighlightTrade
) -> pd.DataFrame:
    """
    Slice M1 bars to window: entry_time to 5 bars after exit.

    Exit is the latest of all R-level hit times (r1-r5) and stop_hit_time.
    Fallback: 60 bars after entry if no times available.
    """
    if bars_m1.empty:
        return bars_m1

    entry_dt = _TZ.localize(datetime.combine(highlight.date, highlight.entry_time))
    # Start 5 bars before entry for context
    start_dt = entry_dt - timedelta(minutes=5)

    # Collect all trade event times to find the true exit (latest event)
    event_times = []
    for rt in [highlight.r1_time, highlight.r2_time, highlight.r3_time,
               highlight.r4_time, highlight.r5_time]:
        if rt:
            event_times.append(rt)
    if highlight.stop_hit and highlight.stop_hit_time:
        event_times.append(highlight.stop_hit_time)

    if event_times:
        exit_time = max(event_times)
        exit_dt = _TZ.localize(datetime.combine(highlight.date, exit_time))
        # Add BARS_AFTER_EXIT minutes (1 bar = 1 min for M1)
        end_dt = exit_dt + timedelta(minutes=BARS_AFTER_EXIT)
    else:
        # Fallback: 60 bars after entry
        end_dt = entry_dt + timedelta(minutes=60)

    # Slice
    mask = (bars_m1.index >= start_dt) & (bars_m1.index <= end_dt)
    sliced = bars_m1.loc[mask]

    # Safety: cap at 400 bars (full trading day is ~390 M1 bars)
    if len(sliced) > 400:
        sliced = sliced.head(400)

    return sliced
