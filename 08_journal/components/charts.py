"""
Plotly chart builder for the Epoch Trading Journal.
Direct copy of 06_training/components/charts.py layout.

Layout (2 rows, 3 charts):
    Row 1: M1 Execution (full width, colspan=2, 55% height)
    Row 2: H1 (left, 45%) + M15 (right, 45%) — context timeframes

Differences from 06_training:
    - M1 replaces M5 as the execution timeframe
    - M1 shows individual fill markers (entries, adds, partials, exits)

Modes (matching 06_training):
    - evaluate: Pre-trade view — bars sliced to entry, no exit/R-levels/MFE
    - reveal: Post-trade view — full trade with MFE/MAE markers + R-crossing diamonds
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, time
from typing import List, Dict, Optional

from config import CHART_CONFIG

# Zone rank colors (from 06_training/config.py)
RANK_COLORS = {
    'L5': '#00C853',
    'L4': '#2196F3',
    'L3': '#FFC107',
    'L2': '#9E9E9E',
    'L1': '#616161',
}


# =============================================================================
# Main entry point
# =============================================================================

def build_journal_chart(
    bars_1m: pd.DataFrame,
    bars_15m: pd.DataFrame,
    bars_1h: pd.DataFrame,
    trade,
    zones: List[Dict],
    mode: str = 'reveal',
    show_mfe_mae: bool = False,
    trade_metrics=None,
) -> go.Figure:
    """
    Build multi-timeframe chart for journal trade review.
    Matches 06_training/components/charts.py build_review_chart() layout.

    Layout:
        Row 1: M1 (full width, half height) — execution timeframe
        Row 2: H1 (left half) + M15 (right half) — context timeframes

    Args:
        bars_1m: M1 candlestick DataFrame
        bars_15m: M15 candlestick DataFrame
        bars_1h: H1 candlestick DataFrame
        trade: Trade model or JournalTradeWithMetrics
        zones: List of zone dicts
        mode: 'evaluate' (pre-trade, bars sliced to entry) or 'reveal' (full trade)
        show_mfe_mae: Whether to show MFE/MAE markers (reveal mode only)
        trade_metrics: JournalTradeWithMetrics for MFE/MAE/R-crossing data
    """
    fig = make_subplots(
        rows=2,
        cols=2,
        shared_xaxes=False,
        vertical_spacing=0.08,
        horizontal_spacing=0.03,
        row_heights=[0.55, 0.45],
        column_widths=[0.5, 0.5],
        specs=[
            [{"colspan": 2}, None],   # M1 spans both columns
            [{}, {}]                    # H1 and M15 side by side
        ],
        subplot_titles=('M1 (Execution)', 'H1 (Market Context)', 'M15 (Structure)')
    )

    # M1 in row 1, spanning both columns (60 bars max)
    _add_candlestick_trace(fig, bars_1m, row=1, col=1, name='M1', max_bars=60)
    # H1 in row 2, left column (120 bars max)
    _add_candlestick_trace(fig, bars_1h, row=2, col=1, name='H1', max_bars=120)
    # M15 in row 2, right column (120 bars max)
    _add_candlestick_trace(fig, bars_15m, row=2, col=2, name='M15', max_bars=120)

    # Add zones to each subplot
    for row, col in [(1, 1), (2, 1), (2, 2)]:
        _add_zones(fig, zones, trade, row=row, col=col)

    # Entry marker on all subplots (always shown in both modes)
    _add_entry_exit_markers(fig, trade, row=1, col=1, show_label=True, mode=mode)
    _add_entry_exit_markers(fig, trade, row=2, col=1, show_label=False, mode=mode)
    _add_entry_exit_markers(fig, trade, row=2, col=2, show_label=False, mode=mode)

    # Reveal mode: show fill markers, R-levels, exit, MFE/MAE, R-crossing diamonds
    if mode == 'reveal':
        # Add fill markers to M1 (entry/exit fills — journal-specific detail)
        _add_fill_markers(fig, trade, row=1, col=1)

        # R-level lines on M1 chart (only if stop_price is set)
        if trade.stop_price is not None:
            _add_r_levels(fig, trade, row=1, col=1)

        # MFE/MAE markers on M1 chart only (requires trade_metrics)
        if show_mfe_mae and trade_metrics is not None:
            _add_mfe_mae_markers(fig, trade_metrics, row=1, col=1)
            _add_r_crossing_markers(fig, trade_metrics, row=1, col=1)

    # Layout
    _apply_layout(fig, trade, mode)

    return fig


# =============================================================================
# Candlestick rendering (matches training _add_candlestick_trace exactly)
# =============================================================================

def _add_candlestick_trace(
    fig: go.Figure,
    df: pd.DataFrame,
    row: int,
    col: int,
    name: str,
    max_bars: int = 120,
):
    """Add candlestick trace to figure."""
    if df.empty:
        return

    # Limit bars (M1=60, H1/M15=120)
    if len(df) > max_bars:
        df = df.tail(max_bars)

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
            showlegend=False,
        ),
        row=row,
        col=col,
    )


# =============================================================================
# Zone overlays (matches training _add_zones)
# =============================================================================

def _add_zones(
    fig: go.Figure,
    zones: List[Dict],
    trade,
    row: int,
    col: int,
):
    """
    Add zone rectangles to a subplot.
    Matches 06_training/components/charts.py _add_zones() exactly.

    Only shows zones that have a setup_type (PRIMARY or SECONDARY) from the
    setups table — these are the curated 2-per-ticker-per-day assignments.
    Zones without a setup_type are NOT displayed (matching training behavior).

    Colors:
    - PRIMARY → blue (#90bff9)
    - SECONDARY → red (#faa1a4)

    The trade's assigned zone (trade.zone_id) also gets a midpoint line.
    """
    if not zones:
        return

    trade_zone_id = getattr(trade, 'zone_id', None)

    for zone in zones:
        zone_high = float(zone.get('zone_high', 0))
        zone_low = float(zone.get('zone_low', 0))

        if zone_high == 0 or zone_low == 0:
            continue

        # Only show zones that are in the setups table (PRIMARY or SECONDARY)
        # This matches training behavior: only the curated setup zones are shown
        setup_type = zone.get('setup_type')  # 'PRIMARY', 'SECONDARY', or None
        if setup_type not in ('PRIMARY', 'SECONDARY'):
            continue

        # Color by setup_type
        if setup_type == 'PRIMARY':
            zone_color = CHART_CONFIG['primary_zone_color']    # Blue
        else:
            zone_color = CHART_CONFIG['secondary_zone_color']  # Red

        fig.add_hrect(
            y0=zone_low,
            y1=zone_high,
            fillcolor=zone_color,
            opacity=CHART_CONFIG['zone_opacity'],
            line_width=1,
            line_color=zone_color,
            row=row,
            col=col,
        )

        # Add midpoint line for the trade's assigned zone
        zone_id = zone.get('zone_id', '')
        is_trade_zone = trade_zone_id and zone_id == trade_zone_id

        if is_trade_zone:
            zone_mid = (zone_high + zone_low) / 2
            fig.add_hline(
                y=zone_mid,
                line_color=zone_color,
                line_width=1.5,
                opacity=0.8,
                row=row,
                col=col,
            )


# =============================================================================
# Individual fill markers (M1 chart only — journal-specific)
# =============================================================================

def _add_fill_markers(fig: go.Figure, trade, row: int, col: int):
    """
    Plot individual fill markers on the M1 execution chart.
    Each fill gets its own triangle at exact time/price.

    Entry/add fills: green triangles
    Exit/partial fills: purple/eod triangles
    Direction follows trade direction.
    """
    from core.models import TradeDirection

    entry_color = CHART_CONFIG['entry_color']
    exit_color = CHART_CONFIG.get('eod_color', CHART_CONFIG['exit_color'])

    is_long = trade.direction == TradeDirection.LONG

    # Entry fills (including adds)
    if trade.entry_leg and trade.entry_leg.fills:
        for fill in trade.entry_leg.fills:
            fill_dt = datetime.combine(trade.trade_date, fill.time)
            symbol = 'triangle-up' if is_long else 'triangle-down'
            text_pos = 'top center' if is_long else 'bottom center'
            label = f"${fill.price:.2f} x {fill.qty}"

            fig.add_trace(
                go.Scatter(
                    x=[fill_dt],
                    y=[fill.price],
                    mode='markers+text',
                    marker=dict(symbol=symbol, size=8, color=entry_color,
                                line=dict(color=entry_color, width=1)),
                    text=[label],
                    textposition=text_pos,
                    textfont=dict(color=entry_color, size=9),
                    hoverinfo='text',
                    hovertext=f"ENTRY {label}",
                    showlegend=False,
                ),
                row=row, col=col,
            )

    # Exit fills (including partials)
    if trade.exit_leg and trade.exit_leg.fills:
        for fill in trade.exit_leg.fills:
            fill_dt = datetime.combine(trade.trade_date, fill.time)
            symbol = 'triangle-down' if is_long else 'triangle-up'
            text_pos = 'bottom center' if is_long else 'top center'
            label = f"${fill.price:.2f} x {fill.qty}"

            fig.add_trace(
                go.Scatter(
                    x=[fill_dt],
                    y=[fill.price],
                    mode='markers+text',
                    marker=dict(symbol=symbol, size=8, color=exit_color,
                                line=dict(color=exit_color, width=1)),
                    text=[label],
                    textposition=text_pos,
                    textfont=dict(color=exit_color, size=9),
                    hoverinfo='text',
                    hovertext=f"EXIT {label}",
                    showlegend=False,
                ),
                row=row, col=col,
            )


# =============================================================================
# Entry/exit markers for H1/M15 (matches training _add_marker_triangle)
# =============================================================================

def _add_entry_exit_markers(
    fig: go.Figure,
    trade,
    row: int,
    col: int,
    show_label: bool = False,
    mode: str = 'reveal',
):
    """
    Add entry and exit triangle markers.
    Matches 06_training _add_marker_triangle() pattern exactly.

    Entry: green triangle, labeled 'ENTRY' on execution chart (always shown)
    Exit: purple (eod_color) triangle, labeled 'EOD $price (±R)' on execution chart (reveal only)
    """
    from core.models import TradeDirection

    entry_color = CHART_CONFIG['entry_color']
    exit_color = CHART_CONFIG['eod_color']
    is_long = trade.direction == TradeDirection.LONG

    # Entry marker
    if trade.entry_time is not None and trade.entry_price is not None:
        entry_dt = datetime.combine(trade.trade_date, trade.entry_time)
        entry_symbol = 'triangle-up' if is_long else 'triangle-down'
        entry_text_pos = 'top center' if is_long else 'bottom center'

        fig.add_trace(
            go.Scatter(
                x=[entry_dt],
                y=[trade.entry_price],
                mode='markers+text',
                marker=dict(symbol=entry_symbol, size=8, color=entry_color,
                            line=dict(color=entry_color, width=1)),
                text=['ENTRY'] if show_label else None,
                textposition=entry_text_pos,
                textfont=dict(color=entry_color, size=9),
                showlegend=False,
                hoverinfo='text',
                hovertext=f"Entry ${trade.entry_price:.2f}",
            ),
            row=row, col=col,
        )

    # Exit marker (matches training EOD format) — reveal mode only
    if mode == 'reveal' and trade.exit_time is not None and trade.exit_price is not None:
        exit_dt = datetime.combine(trade.trade_date, trade.exit_time)
        exit_symbol = 'triangle-down' if is_long else 'triangle-up'
        exit_text_pos = 'bottom center' if is_long else 'top center'

        # Build exit label matching training: "EOD $price (±R)"
        exit_label = None
        if show_label:
            exit_label = f"EOD {trade.exit_price:.2f}"
            pnl_r = getattr(trade, 'pnl_r', None)
            if pnl_r is not None:
                exit_label += f" ({pnl_r:+.2f}R)"

        fig.add_trace(
            go.Scatter(
                x=[exit_dt],
                y=[trade.exit_price],
                mode='markers+text',
                marker=dict(symbol=exit_symbol, size=8, color=exit_color,
                            line=dict(color=exit_color, width=1)),
                text=[exit_label] if exit_label else None,
                textposition=exit_text_pos,
                textfont=dict(color=exit_color, size=9),
                showlegend=False,
                hoverinfo='text',
                hovertext=exit_label or f"Exit ${trade.exit_price:.2f}",
            ),
            row=row, col=col,
        )


# =============================================================================
# R-level lines (matches training _add_r_levels)
# =============================================================================

def _add_r_levels(fig: go.Figure, trade, row: int, col: int):
    """
    Add R-level horizontal lines to chart.
    Matches 06_training/components/charts.py _add_r_levels().
    """
    from core.models import TradeDirection

    if trade.stop_price is None or trade.entry_price is None:
        return

    is_long = trade.direction == TradeDirection.LONG
    risk = abs(trade.entry_price - trade.stop_price)
    if risk == 0:
        return

    # Entry line
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
        row=row, col=col,
    )

    # Stop line
    fig.add_hline(
        y=trade.stop_price,
        line_color=CHART_CONFIG['stop_color'],
        line_width=1.5,
        line_dash='dash',
        opacity=0.8,
        annotation_text=f"Stop ${trade.stop_price:.2f}",
        annotation_position="right",
        annotation_font_color=CHART_CONFIG['stop_color'],
        annotation_font_size=9,
        row=row, col=col,
    )

    # 1R target
    r1 = trade.entry_price + risk if is_long else trade.entry_price - risk
    fig.add_hline(
        y=r1,
        line_color=CHART_CONFIG['r1_color'],
        line_width=1, line_dash='dot', opacity=0.7,
        annotation_text=f"1R ${r1:.2f}",
        annotation_position="right",
        annotation_font_color=CHART_CONFIG['r1_color'],
        annotation_font_size=9,
        row=row, col=col,
    )

    # 2R target
    r2 = trade.entry_price + 2 * risk if is_long else trade.entry_price - 2 * risk
    fig.add_hline(
        y=r2,
        line_color=CHART_CONFIG['r2_color'],
        line_width=1, line_dash='dot', opacity=0.7,
        annotation_text=f"2R ${r2:.2f}",
        annotation_position="right",
        annotation_font_color=CHART_CONFIG['r2_color'],
        annotation_font_size=9,
        row=row, col=col,
    )

    # 3R target
    r3 = trade.entry_price + 3 * risk if is_long else trade.entry_price - 3 * risk
    fig.add_hline(
        y=r3,
        line_color=CHART_CONFIG['r3_color'],
        line_width=1, line_dash='dot', opacity=0.7,
        annotation_text=f"3R ${r3:.2f}",
        annotation_position="right",
        annotation_font_color=CHART_CONFIG['r3_color'],
        annotation_font_size=9,
        row=row, col=col,
    )


# =============================================================================
# MFE/MAE markers (from 06_training — reveal mode only)
# =============================================================================

def _add_mfe_mae_markers(fig: go.Figure, trade_metrics, row: int, col: int):
    """
    Add MFE/MAE triangle markers on M1 chart.
    Matches 06_training _add_marker_triangle() pattern for MFE/MAE.

    MFE: bright green triangle in favorable direction
    MAE: bright red triangle in adverse direction
    """
    from core.models import TradeDirection

    trade_date = getattr(trade_metrics, 'date', None)
    if trade_date is None:
        return

    direction = getattr(trade_metrics, 'direction', None)
    is_long = direction == TradeDirection.LONG if hasattr(TradeDirection, 'LONG') else str(direction).upper() == 'LONG'

    # MFE marker
    mfe_time = getattr(trade_metrics, 'mfe_time', None)
    mfe_price = getattr(trade_metrics, 'mfe_price', None)
    if mfe_time and mfe_price:
        mfe_dt = datetime.combine(trade_date, mfe_time)
        mfe_dir = 'up' if is_long else 'down'
        mfe_symbol = 'triangle-up' if mfe_dir == 'up' else 'triangle-down'
        text_pos = 'top center' if mfe_dir == 'up' else 'bottom center'

        # Build label with R-multiple
        mfe_r = getattr(trade_metrics, 'mfe_r', None)
        mfe_label = 'MFE'
        if mfe_r is not None:
            mfe_label += f' +{abs(mfe_r):.2f}R'
        mfe_points = getattr(trade_metrics, 'mfe_points', None)
        if mfe_points is not None:
            mfe_label += f' (+{abs(mfe_points):.2f})'

        fig.add_trace(
            go.Scatter(
                x=[mfe_dt], y=[mfe_price],
                mode='markers+text',
                marker=dict(symbol=mfe_symbol, size=10, color=CHART_CONFIG['mfe_color'],
                            line=dict(color=CHART_CONFIG['mfe_color'], width=1)),
                text=[mfe_label],
                textposition=text_pos,
                textfont=dict(color=CHART_CONFIG['mfe_color'], size=9),
                showlegend=False,
                hoverinfo='text',
                hovertext=mfe_label,
            ),
            row=row, col=col,
        )

    # MAE marker
    mae_time = getattr(trade_metrics, 'mae_time', None)
    mae_price = getattr(trade_metrics, 'mae_price', None)
    if mae_time and mae_price:
        mae_dt = datetime.combine(trade_date, mae_time)
        mae_dir = 'down' if is_long else 'up'
        mae_symbol = 'triangle-down' if mae_dir == 'down' else 'triangle-up'
        text_pos = 'bottom center' if mae_dir == 'down' else 'top center'

        # Build label with R-multiple
        mae_r = getattr(trade_metrics, 'mae_r', None)
        mae_label = 'MAE'
        if mae_r is not None:
            mae_label += f' {mae_r:.2f}R'
        mae_points = getattr(trade_metrics, 'mae_points', None)
        if mae_points is not None:
            mae_label += f' ({mae_points:.2f})'

        fig.add_trace(
            go.Scatter(
                x=[mae_dt], y=[mae_price],
                mode='markers+text',
                marker=dict(symbol=mae_symbol, size=10, color=CHART_CONFIG['mae_color'],
                            line=dict(color=CHART_CONFIG['mae_color'], width=1)),
                text=[mae_label],
                textposition=text_pos,
                textfont=dict(color=CHART_CONFIG['mae_color'], size=9),
                showlegend=False,
                hoverinfo='text',
                hovertext=mae_label,
            ),
            row=row, col=col,
        )


# =============================================================================
# R-crossing diamond markers (from 06_training — reveal mode only)
# =============================================================================

def _add_r_crossing_markers(fig: go.Figure, trade_metrics, row: int, col: int):
    """
    Add diamond markers at R-level crossing points.
    Shows diamond markers at the exact time when each R-level was crossed,
    with health score information.
    """
    trade_date = getattr(trade_metrics, 'date', None)
    if trade_date is None:
        return

    # R1 crossing
    r1_hit = getattr(trade_metrics, 'r1_hit', False)
    r1_time = getattr(trade_metrics, 'r1_hit_time', None)
    r1_price = getattr(trade_metrics, 'r1_price', None)
    if r1_hit and r1_time and r1_price:
        r1_dt = datetime.combine(trade_date, r1_time)
        r1_label = "1R"
        r1_health = getattr(trade_metrics, 'r1_health', None)
        r1_delta = getattr(trade_metrics, 'r1_health_delta', None)
        if r1_health is not None:
            delta_str = ""
            if r1_delta is not None:
                delta_str = f" ({r1_delta:+d})" if isinstance(r1_delta, int) else f" ({r1_delta:+.0f})"
            r1_label += f" H:{r1_health}{delta_str}"
        _add_marker_diamond(fig, r1_dt, r1_price, row, col, CHART_CONFIG['r1_color'], r1_label)

    # R2 crossing
    r2_hit = getattr(trade_metrics, 'r2_hit', False)
    r2_time = getattr(trade_metrics, 'r2_hit_time', None)
    r2_price = getattr(trade_metrics, 'r2_price', None)
    if r2_hit and r2_time and r2_price:
        r2_dt = datetime.combine(trade_date, r2_time)
        r2_label = "2R"
        r2_health = getattr(trade_metrics, 'r2_health', None)
        r2_delta = getattr(trade_metrics, 'r2_health_delta', None)
        if r2_health is not None:
            delta_str = ""
            if r2_delta is not None:
                delta_str = f" ({r2_delta:+d})" if isinstance(r2_delta, int) else f" ({r2_delta:+.0f})"
            r2_label += f" H:{r2_health}{delta_str}"
        _add_marker_diamond(fig, r2_dt, r2_price, row, col, CHART_CONFIG['r2_color'], r2_label)

    # R3 crossing
    r3_hit = getattr(trade_metrics, 'r3_hit', False)
    r3_time = getattr(trade_metrics, 'r3_hit_time', None)
    r3_price = getattr(trade_metrics, 'r3_price', None)
    if r3_hit and r3_time and r3_price:
        r3_dt = datetime.combine(trade_date, r3_time)
        r3_label = "3R"
        r3_health = getattr(trade_metrics, 'r3_health', None)
        r3_delta = getattr(trade_metrics, 'r3_health_delta', None)
        if r3_health is not None:
            delta_str = ""
            if r3_delta is not None:
                delta_str = f" ({r3_delta:+d})" if isinstance(r3_delta, int) else f" ({r3_delta:+.0f})"
            r3_label += f" H:{r3_health}{delta_str}"
        _add_marker_diamond(fig, r3_dt, r3_price, row, col, CHART_CONFIG['r3_color'], r3_label)


def _add_marker_diamond(
    fig: go.Figure,
    x: datetime,
    y: float,
    row: int,
    col: int,
    color: str,
    label: Optional[str] = None,
):
    """Add diamond marker at R-level crossing point."""
    fig.add_trace(
        go.Scatter(
            x=[x], y=[y],
            mode='markers+text',
            marker=dict(symbol='diamond', size=10, color=color,
                        line=dict(color='white', width=1)),
            text=[label] if label else None,
            textposition='top center',
            textfont=dict(color=color, size=8),
            showlegend=False,
            hoverinfo='text',
            hovertext=label,
        ),
        row=row, col=col,
    )


# =============================================================================
# Layout (matches training _apply_layout)
# =============================================================================

def _apply_layout(fig: go.Figure, trade, mode: str = 'reveal'):
    """
    Apply layout settings to figure.
    Matches 06_training/components/charts.py _apply_layout().
    """
    from core.models import TradeDirection

    direction_str = "LONG" if trade.direction == TradeDirection.LONG else "SHORT"
    mode_label = "EVALUATE" if mode == 'evaluate' else "REVEAL"
    title = f"{trade.symbol} | {trade.trade_date} | {direction_str}"

    # Model label (if available)
    model = getattr(trade, 'model', None)
    if model:
        title += f" | {model}"

    # P&L only in reveal mode
    if mode == 'reveal':
        pnl_r = getattr(trade, 'pnl_r', None)
        if pnl_r is not None:
            pnl_color = "green" if pnl_r > 0 else "red"
            title += f" | <span style='color:{pnl_color}'>{pnl_r:+.2f}R</span>"
        elif trade.pnl_total is not None:
            pnl_color = "green" if trade.pnl_total > 0 else "red"
            title += f" | <span style='color:{pnl_color}'>${trade.pnl_total:+,.2f}</span>"

    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=16, color=CHART_CONFIG['text_color']),
            x=0.5,
            xanchor='center',
        ),
        height=CHART_CONFIG.get('chart_height', 900),
        paper_bgcolor=CHART_CONFIG['paper_color'],
        plot_bgcolor=CHART_CONFIG['background_color'],
        font=dict(color=CHART_CONFIG['text_color']),
        showlegend=False,
        margin=dict(l=60, r=40, t=60, b=40),
    )

    # Rangebreaks: hide weekends and overnight
    rangebreaks = [
        dict(bounds=["sat", "mon"]),
        dict(bounds=[20, 4], pattern="hour"),
    ]

    # Row 1, Col 1 (M1 — spans both columns)
    fig.update_xaxes(
        gridcolor=CHART_CONFIG['grid_color'],
        showgrid=True, zeroline=False,
        rangeslider_visible=False,
        rangebreaks=rangebreaks,
        type='date', tickformat='%H:%M',
        row=1, col=1,
    )
    fig.update_yaxes(
        gridcolor=CHART_CONFIG['grid_color'],
        showgrid=True, zeroline=False, side='right',
        row=1, col=1,
    )

    # Row 2, Col 1 (H1)
    fig.update_xaxes(
        gridcolor=CHART_CONFIG['grid_color'],
        showgrid=True, zeroline=False,
        rangeslider_visible=False,
        rangebreaks=rangebreaks,
        type='date', tickformat='%m/%d %H:%M',
        row=2, col=1,
    )
    fig.update_yaxes(
        gridcolor=CHART_CONFIG['grid_color'],
        showgrid=True, zeroline=False, side='right',
        row=2, col=1,
    )

    # Row 2, Col 2 (M15)
    fig.update_xaxes(
        gridcolor=CHART_CONFIG['grid_color'],
        showgrid=True, zeroline=False,
        rangeslider_visible=False,
        rangebreaks=rangebreaks,
        type='date', tickformat='%m/%d %H:%M',
        row=2, col=2,
    )
    fig.update_yaxes(
        gridcolor=CHART_CONFIG['grid_color'],
        showgrid=True, zeroline=False, side='right',
        row=2, col=2,
    )

    # Style subplot title annotations
    for annotation in fig.layout.annotations:
        annotation.font.color = CHART_CONFIG['text_muted']
        annotation.font.size = 11
