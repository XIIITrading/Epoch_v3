"""
Epoch Trading System - Chart Builder for Training Module
Creates multi-timeframe Plotly charts for trade review.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, time
from typing import Dict, List, Optional, Tuple

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import CHART_CONFIG, RANK_COLORS
from models.trade import TradeWithMetrics, Zone


def build_review_chart(
    bars: Dict[str, pd.DataFrame],
    trade: TradeWithMetrics,
    zones: List[Zone],
    mode: str = 'evaluate',
    show_mfe_mae: bool = True
) -> go.Figure:
    """
    Build multi-timeframe chart for trade review.

    Layout:
    - Row 1: M5 (full width, half height) - execution timeframe
    - Row 2: H1 (left half) + M15 (right half) - context timeframes

    Args:
        bars: Dict with '5m', '15m', '1h' DataFrames
        trade: TradeWithMetrics object
        zones: List of Zone objects to render
        mode: 'evaluate' (right-edge) or 'reveal' (full trade)
        show_mfe_mae: Whether to show MFE/MAE markers (reveal only)

    Returns:
        Plotly Figure object
    """
    # Create subplots:
    # Row 1: M5 spans both columns (full width, half height)
    # Row 2: H1 (left), M15 (right) - each quarter of page
    fig = make_subplots(
        rows=2,
        cols=2,
        shared_xaxes=False,
        vertical_spacing=0.08,
        horizontal_spacing=0.03,
        row_heights=[0.55, 0.45],  # M5 gets more height
        column_widths=[0.5, 0.5],
        specs=[
            [{"colspan": 2}, None],  # M5 spans both columns
            [{}, {}]  # H1 and M15 side by side
        ],
        subplot_titles=('M5 (Execution)', 'H1 (Market Context)', 'M15 (Structure)')
    )

    # Build each timeframe
    # M5 in row 1, spanning both columns
    _add_candlestick_trace(fig, bars.get('5m', pd.DataFrame()), row=1, col=1, name='M5')
    # H1 in row 2, left column
    _add_candlestick_trace(fig, bars.get('1h', pd.DataFrame()), row=2, col=1, name='H1')
    # M15 in row 2, right column
    _add_candlestick_trace(fig, bars.get('15m', pd.DataFrame()), row=2, col=2, name='M15')

    # Add zones to each subplot
    # Row 1 col 1 = M5, Row 2 col 1 = H1, Row 2 col 2 = M15
    for row, col in [(1, 1), (2, 1), (2, 2)]:
        _add_zones(fig, zones, trade, row=row, col=col)

    # Add entry marker to all timeframes
    if trade.entry_time and trade.entry_price:
        entry_dt = datetime.combine(trade.date, trade.entry_time)
        # Triangle direction based on trade direction
        entry_dir = 'up' if trade.direction == 'LONG' else 'down'
        for row, col, show_label in [(1, 1, True), (2, 1, False), (2, 2, False)]:
            _add_marker_triangle(
                fig,
                x=entry_dt,
                y=trade.entry_price,
                row=row,
                col=col,
                color=CHART_CONFIG['entry_color'],
                label='ENTRY' if show_label else None,
                direction=entry_dir
            )

    # In reveal mode, show exit, R-levels, and MFE/MAE
    if mode == 'reveal':
        # Add R-level horizontal lines to M5 chart (row 1, col 1)
        # v2.1.0: Stop = zone edge + 5% buffer, R-levels based on risk
        _add_r_levels(fig, trade, row=1, col=1)

        if trade.exit_time and trade.exit_price:
            exit_dt = datetime.combine(trade.date, trade.exit_time)
            # Exit triangle opposite to entry direction
            exit_dir = 'down' if trade.direction == 'LONG' else 'up'

            # Calculate R-multiple for exit label
            exit_r = trade.pnl_r
            exit_label = f'EOD {trade.exit_price:.2f}'
            if exit_r is not None:
                exit_label += f' ({exit_r:+.2f}R)'

            for row, col, show_label in [(1, 1, True), (2, 1, False), (2, 2, False)]:
                _add_marker_triangle(
                    fig,
                    x=exit_dt,
                    y=trade.exit_price,
                    row=row,
                    col=col,
                    color=CHART_CONFIG['eod_color'],
                    label=exit_label if show_label else None,
                    direction=exit_dir
                )

        # Add MFE/MAE markers on M5 chart only (row 1, col 1)
        # v2.1.0: Shows both R-multiples and points
        if show_mfe_mae:
            if trade.mfe_time and trade.mfe_price:
                mfe_dt = datetime.combine(trade.date, trade.mfe_time)
                # MFE is favorable, so up for LONG, down for SHORT
                mfe_dir = 'up' if trade.direction == 'LONG' else 'down'

                # Build label with R-multiple
                mfe_r = trade.mfe_r
                mfe_label = f'MFE'
                if mfe_r is not None:
                    mfe_label += f' +{abs(mfe_r):.2f}R'
                if trade.mfe_points is not None:
                    mfe_label += f' (+{abs(trade.mfe_points):.2f})'

                _add_marker_triangle(
                    fig,
                    x=mfe_dt,
                    y=trade.mfe_price,
                    row=1,
                    col=1,
                    color=CHART_CONFIG['mfe_color'],
                    label=mfe_label,
                    direction=mfe_dir
                )

            if trade.mae_time and trade.mae_price:
                mae_dt = datetime.combine(trade.date, trade.mae_time)
                # MAE is adverse, so down for LONG, up for SHORT
                mae_dir = 'down' if trade.direction == 'LONG' else 'up'

                # Build label with R-multiple
                mae_r = trade.mae_r
                mae_label = f'MAE'
                if mae_r is not None:
                    mae_label += f' {mae_r:.2f}R'
                if trade.mae_points is not None:
                    mae_label += f' ({trade.mae_points:.2f})'

                _add_marker_triangle(
                    fig,
                    x=mae_dt,
                    y=trade.mae_price,
                    row=1,
                    col=1,
                    color=CHART_CONFIG['mae_color'],
                    label=mae_label,
                    direction=mae_dir
                )

            # Add R-level crossing markers (v2.2.0)
            _add_r_crossing_markers(fig, trade, row=1, col=1)

    # Update layout
    _apply_layout(fig, trade, mode)

    return fig


def _add_candlestick_trace(
    fig: go.Figure,
    df: pd.DataFrame,
    row: int,
    col: int,
    name: str
):
    """Add candlestick trace to figure."""
    if df.empty:
        return

    # Limit to 120 bars max
    if len(df) > 120:
        df = df.tail(120)

    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name=name,
            increasing_line_color=CHART_CONFIG['candle_up_color'],
            decreasing_line_color=CHART_CONFIG['candle_down_color'],
            increasing_fillcolor=CHART_CONFIG['candle_up_color'],
            decreasing_fillcolor=CHART_CONFIG['candle_down_color'],
            showlegend=False
        ),
        row=row,
        col=col
    )


def _add_zones(
    fig: go.Figure,
    zones: List[Zone],
    trade: TradeWithMetrics,
    row: int,
    col: int
):
    """Add zone rectangles to a subplot."""
    # Add trade's zone if available
    if trade.zone_high and trade.zone_low:
        zone_color = (
            CHART_CONFIG['primary_zone_color']
            if trade.zone_type == 'PRIMARY'
            else CHART_CONFIG['secondary_zone_color']
        )

        fig.add_hrect(
            y0=trade.zone_low,
            y1=trade.zone_high,
            fillcolor=zone_color,
            opacity=CHART_CONFIG['zone_opacity'],
            line_width=1,
            line_color=zone_color,
            row=row,
            col=col
        )

        # Add zone midpoint line
        zone_mid = (trade.zone_high + trade.zone_low) / 2
        fig.add_hline(
            y=zone_mid,
            line_color=zone_color,
            line_width=1.5,
            opacity=0.8,
            row=row,
            col=col
        )

    # Add other zones from list (filtered zones only) - controlled by config toggle
    if CHART_CONFIG.get('show_other_zones', False):
        for zone in zones:
            if zone.is_filtered and zone.zone_id != f"{trade.ticker}_{trade.zone_type}":
                # Use rank colors for zone borders
                rank_color = RANK_COLORS.get(zone.rank, '#888888')

                fig.add_hrect(
                    y0=zone.zone_low,
                    y1=zone.zone_high,
                    fillcolor=rank_color,
                    opacity=0.08,
                    line_width=0.5,
                    line_color=rank_color,
                    row=row,
                    col=col
                )


def _add_marker_triangle(
    fig: go.Figure,
    x: datetime,
    y: float,
    row: int,
    col: int,
    color: str,
    label: Optional[str] = None,
    direction: str = 'up'
):
    """Add small triangle marker with tag label.

    Args:
        fig: Plotly figure
        x: X position (datetime)
        y: Y position (price level)
        row: Subplot row
        col: Subplot column
        color: Marker color
        label: Text label for the tag
        direction: 'up' or 'down' for triangle direction
    """
    # Select triangle symbol based on direction
    symbol = 'triangle-up' if direction == 'up' else 'triangle-down'

    # Add triangle marker
    fig.add_trace(
        go.Scatter(
            x=[x],
            y=[y],
            mode='markers+text',
            marker=dict(
                symbol=symbol,
                size=8,
                color=color,
                line=dict(color=color, width=1)
            ),
            text=[label] if label else None,
            textposition='top center' if direction == 'up' else 'bottom center',
            textfont=dict(color=color, size=9),
            showlegend=False,
            hoverinfo='text',
            hovertext=label
        ),
        row=row,
        col=col
    )


def _add_r_levels(
    fig: go.Figure,
    trade: TradeWithMetrics,
    row: int,
    col: int
):
    """
    Add R-level horizontal lines to chart (v2.1.0).

    Displays:
    - Entry (green)
    - Stop (red) - Zone edge + 5% buffer
    - 1R (light green)
    - 2R (lighter green)
    - 3R (lime)

    Args:
        fig: Plotly figure
        trade: TradeWithMetrics object with R-level calculations
        row: Subplot row
        col: Subplot column
    """
    # Entry line
    if trade.entry_price:
        fig.add_hline(
            y=trade.entry_price,
            line_color=CHART_CONFIG['entry_color'],
            line_width=1.5,
            line_dash='solid',
            opacity=0.8,
            annotation_text=f"Entry ${trade.entry_price:.2f}",
            annotation_position="right",
            annotation_font_color=CHART_CONFIG['entry_color'],
            annotation_font_size=9,
            row=row,
            col=col
        )

    # Stop line (Zone edge + 5% buffer)
    stop_price = trade.default_stop_price
    if stop_price:
        fig.add_hline(
            y=stop_price,
            line_color=CHART_CONFIG['stop_color'],
            line_width=1.5,
            line_dash='dash',
            opacity=0.8,
            annotation_text=f"Stop ${stop_price:.2f}",
            annotation_position="right",
            annotation_font_color=CHART_CONFIG['stop_color'],
            annotation_font_size=9,
            row=row,
            col=col
        )

    # 1R target line
    r1_price = trade.r1_price
    if r1_price:
        fig.add_hline(
            y=r1_price,
            line_color=CHART_CONFIG['r1_color'],
            line_width=1,
            line_dash='dot',
            opacity=0.7,
            annotation_text=f"1R ${r1_price:.2f}",
            annotation_position="right",
            annotation_font_color=CHART_CONFIG['r1_color'],
            annotation_font_size=9,
            row=row,
            col=col
        )

    # 2R target line
    r2_price = trade.r2_price
    if r2_price:
        fig.add_hline(
            y=r2_price,
            line_color=CHART_CONFIG['r2_color'],
            line_width=1,
            line_dash='dot',
            opacity=0.7,
            annotation_text=f"2R ${r2_price:.2f}",
            annotation_position="right",
            annotation_font_color=CHART_CONFIG['r2_color'],
            annotation_font_size=9,
            row=row,
            col=col
        )

    # 3R target line
    r3_price = trade.r3_price
    if r3_price:
        fig.add_hline(
            y=r3_price,
            line_color=CHART_CONFIG['r3_color'],
            line_width=1,
            line_dash='dot',
            opacity=0.7,
            annotation_text=f"3R ${r3_price:.2f}",
            annotation_position="right",
            annotation_font_color=CHART_CONFIG['r3_color'],
            annotation_font_size=9,
            row=row,
            col=col
        )


def _add_r_crossing_markers(
    fig: go.Figure,
    trade: TradeWithMetrics,
    row: int,
    col: int
):
    """
    Add markers at R-level crossing points (v2.2.0).

    Shows diamond markers at the exact time when each R-level was crossed,
    with health score information.

    Args:
        fig: Plotly figure
        trade: TradeWithMetrics object with R-level crossing data
        row: Subplot row
        col: Subplot column
    """
    # Direction for markers (favorable = up for LONG)
    marker_dir = 'up' if trade.direction == 'LONG' else 'down'

    # R1 crossing marker
    if trade.r1_crossed and trade.r1_time and trade.r1_price:
        r1_dt = datetime.combine(trade.date, trade.r1_time)
        # Build label with health info
        r1_label = "1R"
        if trade.r1_health is not None:
            delta_str = ""
            if trade.r1_health_delta is not None:
                delta_sign = "+" if trade.r1_health_delta >= 0 else ""
                delta_str = f" ({delta_sign}{trade.r1_health_delta})"
            r1_label += f" H:{trade.r1_health}{delta_str}"

        _add_marker_diamond(
            fig,
            x=r1_dt,
            y=trade.r1_price,
            row=row,
            col=col,
            color=CHART_CONFIG['r1_color'],
            label=r1_label
        )

    # R2 crossing marker
    if trade.r2_crossed and trade.r2_time and trade.r2_price:
        r2_dt = datetime.combine(trade.date, trade.r2_time)
        r2_label = "2R"
        if trade.r2_health is not None:
            delta_str = ""
            if trade.r2_health_delta is not None:
                delta_sign = "+" if trade.r2_health_delta >= 0 else ""
                delta_str = f" ({delta_sign}{trade.r2_health_delta})"
            r2_label += f" H:{trade.r2_health}{delta_str}"

        _add_marker_diamond(
            fig,
            x=r2_dt,
            y=trade.r2_price,
            row=row,
            col=col,
            color=CHART_CONFIG['r2_color'],
            label=r2_label
        )

    # R3 crossing marker
    if trade.r3_crossed and trade.r3_time and trade.r3_price:
        r3_dt = datetime.combine(trade.date, trade.r3_time)
        r3_label = "3R"
        if trade.r3_health is not None:
            delta_str = ""
            if trade.r3_health_delta is not None:
                delta_sign = "+" if trade.r3_health_delta >= 0 else ""
                delta_str = f" ({delta_sign}{trade.r3_health_delta})"
            r3_label += f" H:{trade.r3_health}{delta_str}"

        _add_marker_diamond(
            fig,
            x=r3_dt,
            y=trade.r3_price,
            row=row,
            col=col,
            color=CHART_CONFIG['r3_color'],
            label=r3_label
        )


def _add_marker_diamond(
    fig: go.Figure,
    x: datetime,
    y: float,
    row: int,
    col: int,
    color: str,
    label: Optional[str] = None
):
    """Add diamond marker at R-level crossing point.

    Args:
        fig: Plotly figure
        x: X position (datetime)
        y: Y position (price level)
        row: Subplot row
        col: Subplot column
        color: Marker color
        label: Text label
    """
    fig.add_trace(
        go.Scatter(
            x=[x],
            y=[y],
            mode='markers+text',
            marker=dict(
                symbol='diamond',
                size=10,
                color=color,
                line=dict(color='white', width=1)
            ),
            text=[label] if label else None,
            textposition='top center',
            textfont=dict(color=color, size=8),
            showlegend=False,
            hoverinfo='text',
            hovertext=label
        ),
        row=row,
        col=col
    )


def _apply_layout(fig: go.Figure, trade: TradeWithMetrics, mode: str):
    """Apply layout settings to figure.

    v2.1.0: Uses R-multiples (aligned with System Analysis)
    """
    # Title
    mode_label = "EVALUATE" if mode == 'evaluate' else "REVEAL"
    direction_emoji = "🟢" if trade.direction == 'LONG' else "🔴"

    title = f"{trade.ticker} | {trade.date} | {trade.model} | {direction_emoji} {trade.direction}"

    # v2.1.0: Show R-multiple as primary, points as secondary
    if mode == 'reveal':
        pnl_r = trade.pnl_r
        if pnl_r is not None:
            pnl_color = "green" if pnl_r > 0 else "red"
            title += f" | <span style='color:{pnl_color}'>{pnl_r:+.2f}R</span>"
            if trade.pnl_points is not None:
                title += f" <span style='color:{pnl_color}'>({trade.pnl_points:+.2f} pts)</span>"
        elif trade.pnl_points is not None:
            pnl_color = "green" if trade.pnl_points > 0 else "red"
            title += f" | <span style='color:{pnl_color}'>{trade.pnl_points:+.2f} pts</span>"

    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=16, color=CHART_CONFIG['text_color']),
            x=0.5,
            xanchor='center'
        ),
        height=CHART_CONFIG['chart_height'],
        paper_bgcolor=CHART_CONFIG['paper_color'],
        plot_bgcolor=CHART_CONFIG['background_color'],
        font=dict(color=CHART_CONFIG['text_color']),
        showlegend=False,
        margin=dict(l=60, r=40, t=60, b=40),
    )

    # Define rangebreaks to hide weekends and non-trading hours
    # Extended hours: 4:00 AM - 8:00 PM ET (pre-market 4-9:30, regular 9:30-4, after-hours 4-8)
    # Hide: weekends (Saturday=6, Sunday=0) and overnight (8PM - 4AM)
    rangebreaks = [
        dict(bounds=["sat", "mon"]),  # Hide weekends
        dict(bounds=[20, 4], pattern="hour"),  # Hide overnight (8PM to 4AM)
    ]

    # Update axes for all subplots in the 2x2 layout
    # Row 1, Col 1 (M5 - spans both columns)
    fig.update_xaxes(
        gridcolor=CHART_CONFIG['grid_color'],
        showgrid=True,
        zeroline=False,
        rangeslider_visible=False,
        rangebreaks=rangebreaks,
        type='date',
        tickformat='%H:%M',
        row=1,
        col=1
    )
    fig.update_yaxes(
        gridcolor=CHART_CONFIG['grid_color'],
        showgrid=True,
        zeroline=False,
        side='right',
        row=1,
        col=1
    )

    # Row 2, Col 1 (H1)
    fig.update_xaxes(
        gridcolor=CHART_CONFIG['grid_color'],
        showgrid=True,
        zeroline=False,
        rangeslider_visible=False,
        rangebreaks=rangebreaks,
        type='date',
        tickformat='%m/%d %H:%M',
        row=2,
        col=1
    )
    fig.update_yaxes(
        gridcolor=CHART_CONFIG['grid_color'],
        showgrid=True,
        zeroline=False,
        side='right',
        row=2,
        col=1
    )

    # Row 2, Col 2 (M15)
    fig.update_xaxes(
        gridcolor=CHART_CONFIG['grid_color'],
        showgrid=True,
        zeroline=False,
        rangeslider_visible=False,
        rangebreaks=rangebreaks,
        type='date',
        tickformat='%m/%d %H:%M',
        row=2,
        col=2
    )
    fig.update_yaxes(
        gridcolor=CHART_CONFIG['grid_color'],
        showgrid=True,
        zeroline=False,
        side='right',
        row=2,
        col=2
    )

    # Update subplot title colors
    for annotation in fig.layout.annotations:
        annotation.font.color = CHART_CONFIG['text_muted']
        annotation.font.size = 11


def build_simple_chart(
    bars: pd.DataFrame,
    timeframe: str,
    trade: TradeWithMetrics,
    mode: str = 'evaluate'
) -> go.Figure:
    """
    Build a single-timeframe chart.
    Simpler alternative for performance.

    Args:
        bars: DataFrame with OHLCV data
        timeframe: Timeframe label (e.g., 'M5')
        trade: TradeWithMetrics object
        mode: 'evaluate' or 'reveal'

    Returns:
        Plotly Figure object
    """
    fig = go.Figure()

    if not bars.empty:
        fig.add_trace(
            go.Candlestick(
                x=bars.index,
                open=bars['open'],
                high=bars['high'],
                low=bars['low'],
                close=bars['close'],
                increasing_line_color=CHART_CONFIG['candle_up_color'],
                decreasing_line_color=CHART_CONFIG['candle_down_color'],
                increasing_fillcolor=CHART_CONFIG['candle_up_color'],
                decreasing_fillcolor=CHART_CONFIG['candle_down_color'],
            )
        )

    # Add zone
    if trade.zone_high and trade.zone_low:
        zone_color = (
            CHART_CONFIG['primary_zone_color']
            if trade.zone_type == 'PRIMARY'
            else CHART_CONFIG['secondary_zone_color']
        )

        fig.add_hrect(
            y0=trade.zone_low,
            y1=trade.zone_high,
            fillcolor=zone_color,
            opacity=CHART_CONFIG['zone_opacity'],
            line_width=1,
            line_color=zone_color
        )

    # Add entry
    if trade.entry_time:
        entry_dt = datetime.combine(trade.date, trade.entry_time)
        fig.add_vline(
            x=entry_dt,
            line_color=CHART_CONFIG['entry_color'],
            line_width=2,
            annotation_text='ENTRY',
            annotation_position='top'
        )

    # Add exit in reveal mode
    if mode == 'reveal' and trade.exit_time:
        exit_dt = datetime.combine(trade.date, trade.exit_time)
        fig.add_vline(
            x=exit_dt,
            line_color=CHART_CONFIG['exit_color'],
            line_width=2,
            line_dash='dash',
            annotation_text='EXIT',
            annotation_position='top'
        )

    # Layout
    fig.update_layout(
        title=f"{trade.ticker} {timeframe} - {trade.date}",
        height=400,
        paper_bgcolor=CHART_CONFIG['paper_color'],
        plot_bgcolor=CHART_CONFIG['background_color'],
        font=dict(color=CHART_CONFIG['text_color']),
        xaxis_rangeslider_visible=False,
        showlegend=False
    )

    # Define rangebreaks to hide weekends and non-trading hours
    rangebreaks = [
        dict(bounds=["sat", "mon"]),  # Hide weekends
        dict(bounds=[20, 4], pattern="hour"),  # Hide overnight (8PM to 4AM)
    ]

    fig.update_xaxes(
        gridcolor=CHART_CONFIG['grid_color'],
        rangebreaks=rangebreaks,
        type='date',
        tickformat='%H:%M'
    )
    fig.update_yaxes(gridcolor=CHART_CONFIG['grid_color'], side='right')

    return fig
