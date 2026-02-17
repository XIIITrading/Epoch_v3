"""
Epoch Trading System - M5 Exit Chart Builder
Shows M5 bars from entry through 5 bars after the highest R-level hit.
Includes R-level lines (70% transparent), R hit markers, zone, POCs, VbP.
Y-axis auto-ranged to data min/max with 5px buffer.
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
from charts.volume_profile import create_chart_with_vbp, add_volume_profile, add_volume_bars
from charts.poc_lines import add_poc_lines, add_zone_poc_lines

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

# Chart pixel height for buffer calculation
M5_CHART_HEIGHT = 420
BUFFER_PX = 5


def _slice_exit_window(bars_m5: pd.DataFrame, highlight: HighlightTrade) -> pd.DataFrame:
    """
    Slice M5 bars: from entry bar through 5 bars after the highest R-level hit.
    """
    if bars_m5 is None or bars_m5.empty or not highlight.entry_time:
        return pd.DataFrame()

    entry_dt = _TZ.localize(datetime.combine(highlight.date, highlight.entry_time))

    # Find end: 5 bars after highest R hit
    highest_r_time = highlight.highest_r_hit_time
    if highest_r_time:
        highest_r_dt = _TZ.localize(datetime.combine(highlight.date, highest_r_time))
    else:
        # Fallback: use entry + 30 bars worth of time
        highest_r_dt = entry_dt + timedelta(minutes=150)

    # Get bars from entry onward
    mask_from_entry = bars_m5.index >= entry_dt
    bars_from_entry = bars_m5[mask_from_entry]

    if bars_from_entry.empty:
        return pd.DataFrame()

    # Find index of bar at/after highest R hit, then take 5 more
    mask_after_r = bars_from_entry.index >= highest_r_dt
    if mask_after_r.any():
        r_hit_idx = int(mask_after_r.argmax())  # First True position
        end_idx = min(r_hit_idx + 6, len(bars_from_entry))  # +5 bars after R hit bar
        return bars_from_entry.iloc[:end_idx]
    else:
        # R hit time not found in bars, show all from entry
        return bars_from_entry


def build_m5_exit_chart(
    bars_m5: pd.DataFrame,
    highlight: HighlightTrade,
    zones: Optional[List[dict]] = None,
    vbp_bars: Optional[pd.DataFrame] = None,
    pocs: Optional[List[float]] = None,
) -> go.Figure:
    """
    Build M5 Exit chart: entry through 5 bars after highest R hit.

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

    df = _slice_exit_window(bars_m5, highlight)

    # Volume by Price overlay (added first so candles render on top)
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

    # Volume bars (TradingView-style, bottom of chart)
    if not df.empty:
        add_volume_bars(fig, df)

    # Zone HVN POC lines (teal=primary, cyan=secondary)
    add_zone_poc_lines(fig, zones, highlight)

    # R-level horizontal lines (70% transparent)
    r_levels = [
        (1, highlight.r1_price, highlight.r1_hit),
        (2, highlight.r2_price, highlight.r2_hit),
        (3, highlight.r3_price, highlight.r3_hit),
        (4, highlight.r4_price, highlight.r4_hit),
        (5, highlight.r5_price, highlight.r5_hit),
    ]

    for r_num, price, hit in r_levels:
        if price:
            color = R_COLORS.get(r_num, '#787B86')
            opacity = 0.3 if hit else 0.15
            dash = 'solid' if hit else 'dot'

            fig.add_hline(
                y=price,
                line_color=color,
                line_width=1.5 if hit else 0.8,
                line_dash=dash,
                opacity=opacity,
                annotation_text=f"R{r_num} ${price:.2f}" if hit else f"R{r_num}",
                annotation_position="right",
                annotation_font_color=color,
                annotation_font_size=9 if hit else 8,
            )

    # Stop line
    if highlight.stop_price:
        fig.add_hline(
            y=highlight.stop_price,
            line_color=CHART_COLORS['stop'],
            line_width=1.5,
            line_dash='dash',
            opacity=0.3,
            annotation_text=f"Stop ${highlight.stop_price:.2f}",
            annotation_position="right",
            annotation_font_color=CHART_COLORS['stop'],
            annotation_font_size=9,
        )

    # R-level hit markers (diamonds)
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

            fig.add_trace(go.Scatter(
                x=[r_dt],
                y=[r_price],
                mode='markers+text',
                marker=dict(symbol='diamond', size=10, color=color,
                            line=dict(color='white', width=1)),
                text=[f"R{r_num}"],
                textposition='top center',
                textfont=dict(color=color, size=9, family='Arial Black'),
                showlegend=False,
                hovertext=f"R{r_num} hit at {r_time.strftime('%H:%M')} | ${r_price:.2f}",
                hoverinfo='text',
            ))

    # HVN POC lines
    add_poc_lines(fig, pocs)

    # Auto Y-range from visible data with 5px buffer
    y_range = _calc_y_range(df, highlight, M5_CHART_HEIGHT, BUFFER_PX)

    # Layout
    title_text = f"5-Minute Exit  |  {highlight.ticker}  |  {highlight.date}"

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
        tickformat='%m-%d %H:%M',
        tickangle=0,
        showgrid=False,
    )

    if y_range:
        fig.update_yaxes(side='right', range=y_range)
    else:
        fig.update_yaxes(side='right')

    return fig


def _calc_y_range(df: pd.DataFrame, highlight: HighlightTrade, chart_height: int, buffer_px: int):
    """
    Calculate Y-axis range from visible data min/max with pixel buffer.
    Also considers R-level prices and stop price that fall within the window.
    """
    if df is None or df.empty:
        return None

    data_low = df['low'].min()
    data_high = df['high'].max()

    # Include R-level and stop prices in range calculation
    extra_prices = [highlight.stop_price]
    for r_num in range(1, 6):
        r_price = getattr(highlight, f'r{r_num}_price', None)
        if r_price:
            extra_prices.append(r_price)

    for p in extra_prices:
        if p is not None:
            data_low = min(data_low, p)
            data_high = max(data_high, p)

    price_range = data_high - data_low
    if price_range <= 0:
        return None

    # Convert pixel buffer to price units
    usable_px = chart_height - 45 - 30
    if usable_px <= 0:
        usable_px = chart_height

    price_per_px = price_range / usable_px
    buffer_price = buffer_px * price_per_px

    return [data_low - buffer_price, data_high + buffer_price]
