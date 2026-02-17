"""
Epoch Trading System - M1 Action Chart Builder
1-minute candlestick: 30 bars before entry, full trade, 30 bars after max R hit.
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
from charts.poc_lines import add_zone_poc_lines
from charts.volume_profile import add_volume_bars, CANDLE_DOMAIN_BOTTOM, VOL_CLEARANCE_FRAC

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

# How many bars of context before entry and after max R hit
BARS_BEFORE_ENTRY = 30
BARS_AFTER_MAX_R = 30


def build_m1_chart(
    bars_m1: pd.DataFrame,
    highlight: HighlightTrade,
    zones: Optional[List[dict]] = None
) -> go.Figure:
    """
    Build M1 candlestick chart: 30 bars before entry, full trade, 30 bars after max R hit.

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

    # Volume bars (TradingView-style, bottom of chart)
    if not df.empty:
        add_volume_bars(fig, df)

    # Zone HVN POC lines (teal=primary, cyan=secondary)
    add_zone_poc_lines(fig, zones, highlight)

    # Entry marker — direction-colored triangle (green up / red down)
    if highlight.entry_time and highlight.entry_price:
        entry_dt = _TZ.localize(datetime.combine(highlight.date, highlight.entry_time))
        is_long = highlight.direction == 'LONG'
        entry_symbol = 'triangle-up' if is_long else 'triangle-down'
        entry_color = CHART_COLORS.get('bull', '#089981') if is_long else CHART_COLORS.get('bear', '#F23645')

        fig.add_trace(go.Scatter(
            x=[entry_dt],
            y=[highlight.entry_price],
            mode='markers',
            marker=dict(symbol=entry_symbol, size=6, color=entry_color,
                        line=dict(color='white', width=0.5)),
            showlegend=False,
            hoverinfo='text',
            hovertext=f"Entry ${highlight.entry_price:.2f}",
        ))

    # Exit/VWAP marker — direction-colored triangle (green up / red down)
    if highlight.exit_price and highlight.exit_time:
        exit_dt = _TZ.localize(datetime.combine(highlight.date, highlight.exit_time))
        is_long = highlight.direction == 'LONG'
        exit_symbol = 'triangle-up' if is_long else 'triangle-down'
        exit_color = CHART_COLORS.get('bull', '#089981') if is_long else CHART_COLORS.get('bear', '#F23645')

        fig.add_trace(go.Scatter(
            x=[exit_dt],
            y=[highlight.exit_price],
            mode='markers',
            marker=dict(symbol=exit_symbol, size=6, color=exit_color,
                        line=dict(color='white', width=0.5)),
            showlegend=False,
            hoverinfo='text',
            hovertext=f"Exit VWAP ${highlight.exit_price:.2f}",
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

    # R-level hit markers — highest R gets text label, all use small diamonds
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
                    symbol='diamond',
                    size=7,
                    color=color,
                    line=dict(color='white', width=0.5),
                ),
                text=[f"R{r_num}" if is_highest else ''],
                textposition='top center',
                textfont=dict(color=color, size=11,
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
        yaxis=dict(domain=[CANDLE_DOMAIN_BOTTOM, 1.0]),
    )

    fig.update_xaxes(
        rangebreaks=[
            dict(bounds=["sat", "mon"]),
            dict(bounds=[20, 4], pattern="hour"),
        ],
        type='date',
        tickformat='%H:%M',
        tickangle=0,
        showgrid=False,
    )

    # Auto Y-range with 10px buffer
    y_range = _calc_y_range(df, 380, 10)
    if y_range:
        fig.update_yaxes(side='right', range=y_range)
    else:
        fig.update_yaxes(side='right')

    return fig


def _slice_to_window(
    bars_m1: pd.DataFrame,
    highlight: HighlightTrade
) -> pd.DataFrame:
    """
    Slice M1 bars to window:
      - 30 bars before entry
      - All candles of the trade
      - 30 bars after the max R level hit time

    Fallback: 60 bars after entry if no max R hit time available.
    """
    if bars_m1.empty:
        return bars_m1

    entry_dt = _TZ.localize(datetime.combine(highlight.date, highlight.entry_time))
    start_dt = entry_dt - timedelta(minutes=BARS_BEFORE_ENTRY)

    # Use max R hit time as the anchor for the end of window
    max_r_time = highlight.highest_r_hit_time
    if max_r_time:
        max_r_dt = _TZ.localize(datetime.combine(highlight.date, max_r_time))
        end_dt = max_r_dt + timedelta(minutes=BARS_AFTER_MAX_R)
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
    usable_px = chart_height - 45 - 30
    if usable_px <= 0:
        usable_px = chart_height
    price_per_px = price_range / usable_px
    top_buffer = buffer_px * price_per_px

    # Bottom buffer: extend y-range so data_low maps to VOL_CLEARANCE_FRAC
    visible_range = price_range + top_buffer
    total_range = visible_range / (1.0 - VOL_CLEARANCE_FRAC)
    bottom_extension = total_range - visible_range

    return [data_low - bottom_extension, data_high + top_buffer]
