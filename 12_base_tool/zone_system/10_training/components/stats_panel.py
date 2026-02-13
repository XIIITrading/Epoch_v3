"""
Epoch Trading System - Stats Panel Component
Displays trade statistics in reveal mode.
"""

import streamlit as st
from datetime import time, datetime
from typing import Dict, Any, Optional, Callable

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.trade import TradeWithMetrics


def render_stats_panel(trade: TradeWithMetrics):
    """
    Display trade statistics in a clean, readable format.
    Only shown in REVEAL mode.

    v2.1.0: R-multiple based (aligned with System Analysis)
    Win condition: pnl_r > 0
    Stop: Zone edge + 5% buffer

    Args:
        trade: TradeWithMetrics object with all metrics
    """
    st.markdown("### Trade Statistics")

    # Main metrics row - R-multiples as primary
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        pnl_r = trade.pnl_r
        pnl_points = trade.pnl_points or 0

        # Use R-multiple based win condition
        is_winner = trade.is_winner_r
        delta_color = "normal" if is_winner else "inverse"

        if pnl_r is not None:
            st.metric(
                label="P&L (R)",
                value=f"{pnl_r:+.2f}R",
                delta=f"{'Winner' if is_winner else 'Loser'} ({pnl_points:+.2f} pts)",
                delta_color=delta_color
            )
        else:
            st.metric(
                label="P&L",
                value=f"{pnl_points:+.2f} pts",
                delta="Winner" if pnl_points > 0 else "Loser",
                delta_color="normal" if pnl_points >= 0 else "inverse"
            )

    with col2:
        mfe_r = trade.mfe_r
        mfe_points = trade.mfe_points or 0

        if mfe_r is not None:
            st.metric(
                label="MFE (R)",
                value=f"+{abs(mfe_r):.2f}R",
                delta=f"Bar {trade.mfe_bars} (+{abs(mfe_points):.2f} pts)" if trade.mfe_bars else f"+{abs(mfe_points):.2f} pts",
                help="Maximum Favorable Excursion - best movement from entry to 15:30"
            )
        else:
            st.metric(
                label="MFE",
                value=f"+{abs(mfe_points):.2f} pts",
                delta=f"Bar {trade.mfe_bars}" if trade.mfe_bars else None,
                help="Maximum Favorable Excursion - best movement from entry to 15:30"
            )

    with col3:
        mae_r = trade.mae_r
        mae_points = trade.mae_points or 0

        if mae_r is not None:
            st.metric(
                label="MAE (R)",
                value=f"{mae_r:.2f}R",
                delta=f"Bar {trade.mae_bars} ({mae_points:.2f} pts)" if trade.mae_bars else f"{mae_points:.2f} pts",
                help="Maximum Adverse Excursion - worst movement from entry to 15:30"
            )
        else:
            st.metric(
                label="MAE",
                value=f"{mae_points:.2f} pts",
                delta=f"Bar {trade.mae_bars}" if trade.mae_bars else None,
                help="Maximum Adverse Excursion - worst movement from entry to 15:30"
            )

    with col4:
        duration = trade.duration_minutes
        if duration:
            if duration >= 60:
                duration_str = f"{duration // 60}h {duration % 60}m"
            else:
                duration_str = f"{duration}m"
        else:
            duration_str = "N/A"

        st.metric(
            label="Duration",
            value=duration_str,
            delta="EOD 15:30"
        )

    # R-Levels info row
    st.markdown("---")
    st.markdown("**R-Levels (Stop = Zone + 5% Buffer)**")
    r_col1, r_col2, r_col3, r_col4, r_col5 = st.columns(5)

    with r_col1:
        stop = trade.default_stop_price
        st.markdown(f"**Stop:** ${stop:.2f}" if stop else "**Stop:** N/A")

    with r_col2:
        st.markdown(f"**Entry:** ${trade.entry_price:.2f}" if trade.entry_price else "**Entry:** N/A")

    with r_col3:
        r1 = trade.r1_price
        st.markdown(f"**1R:** ${r1:.2f}" if r1 else "**1R:** N/A")

    with r_col4:
        r2 = trade.r2_price
        st.markdown(f"**2R:** ${r2:.2f}" if r2 else "**2R:** N/A")

    with r_col5:
        r3 = trade.r3_price
        st.markdown(f"**3R:** ${r3:.2f}" if r3 else "**3R:** N/A")

    # R-Level Crossings row (v2.2.0 - shows when each level was hit)
    if trade.r1_crossed or trade.r2_crossed or trade.r3_crossed:
        st.markdown("---")
        st.markdown("**R-Level Crossings** (Health at crossing)")
        cross_col1, cross_col2, cross_col3 = st.columns(3)

        with cross_col1:
            if trade.r1_crossed:
                health_str = f"{trade.r1_health}/10" if trade.r1_health is not None else "N/A"
                delta_str = ""
                if trade.r1_health_delta is not None:
                    delta_sign = "+" if trade.r1_health_delta >= 0 else ""
                    delta_str = f" ({delta_sign}{trade.r1_health_delta})"
                time_str = trade.r1_time.strftime("%H:%M") if trade.r1_time else "N/A"
                st.markdown(f"**1R:** {time_str} | Health: {health_str}{delta_str}")
            else:
                st.markdown("**1R:** Not reached")

        with cross_col2:
            if trade.r2_crossed:
                health_str = f"{trade.r2_health}/10" if trade.r2_health is not None else "N/A"
                delta_str = ""
                if trade.r2_health_delta is not None:
                    delta_sign = "+" if trade.r2_health_delta >= 0 else ""
                    delta_str = f" ({delta_sign}{trade.r2_health_delta})"
                time_str = trade.r2_time.strftime("%H:%M") if trade.r2_time else "N/A"
                st.markdown(f"**2R:** {time_str} | Health: {health_str}{delta_str}")
            else:
                st.markdown("**2R:** Not reached")

        with cross_col3:
            if trade.r3_crossed:
                health_str = f"{trade.r3_health}/10" if trade.r3_health is not None else "N/A"
                delta_str = ""
                if trade.r3_health_delta is not None:
                    delta_sign = "+" if trade.r3_health_delta >= 0 else ""
                    delta_str = f" ({delta_sign}{trade.r3_health_delta})"
                time_str = trade.r3_time.strftime("%H:%M") if trade.r3_time else "N/A"
                st.markdown(f"**3R:** {time_str} | Health: {health_str}{delta_str}")
            else:
                st.markdown("**3R:** Not reached")

    # Additional details in expander
    with st.expander("Full Trade Details", expanded=False):
        detail_col1, detail_col2, detail_col3 = st.columns(3)

        with detail_col1:
            st.markdown("**Trade Info**")
            st.write(f"Model: {trade.model}")
            st.write(f"Zone Type: {trade.zone_type}")
            st.write(f"Direction: {trade.direction}")
            st.write(f"Zone Tier: {trade.zone_tier or 'N/A'}")
            st.write(f"Zone Rank: {trade.zone_rank or 'N/A'}")

        with detail_col2:
            st.markdown("**Entry/Exit**")
            st.write(f"Entry: ${trade.entry_price:.2f}" if trade.entry_price else "Entry: N/A")
            st.write(f"Entry Time: {_format_time(trade.entry_time)}")
            st.write(f"Exit: ${trade.exit_price:.2f}" if trade.exit_price else "Exit: N/A")
            st.write(f"Exit Time: {_format_time(trade.exit_time)}")
            st.write(f"Exit Reason: {trade.exit_reason}")

        with detail_col3:
            st.markdown("**Risk Metrics**")
            risk = trade.risk_per_share
            st.write(f"Risk/Share: ${risk:.2f}" if risk else "Risk/Share: N/A")
            stop = trade.default_stop_price
            st.write(f"Stop Price: ${stop:.2f}" if stop else "Stop Price: N/A")
            st.write(f"Outcome: {trade.outcome_r}")
            st.write(f"Win (R>0): {'Yes' if trade.is_winner_r else 'No'}")

        # Health metrics row
        st.markdown("---")
        st.markdown("**Health Metrics**")
        health_col1, health_col2, health_col3, health_col4 = st.columns(4)
        with health_col1:
            st.write(f"Entry: {trade.entry_health}/10" if trade.entry_health is not None else "Entry: N/A")
        with health_col2:
            st.write(f"MFE: {trade.mfe_health}/10" if trade.mfe_health is not None else "MFE: N/A")
        with health_col3:
            st.write(f"MAE: {trade.mae_health}/10" if trade.mae_health is not None else "MAE: N/A")
        with health_col4:
            st.write(f"Exit: {trade.exit_health}/10" if trade.exit_health is not None else "Exit: N/A")

        # Zone info
        st.markdown("---")
        st.markdown("**Zone Boundaries**")
        zone_col1, zone_col2, zone_col3 = st.columns(3)
        with zone_col1:
            st.write(f"Zone High: ${trade.zone_high:.2f}" if trade.zone_high else "Zone High: N/A")
        with zone_col2:
            zone_mid = trade.trade.zone_mid
            st.write(f"Zone POC: ${zone_mid:.2f}" if zone_mid else "Zone POC: N/A")
        with zone_col3:
            st.write(f"Zone Low: ${trade.zone_low:.2f}" if trade.zone_low else "Zone Low: N/A")


def render_quick_stats(trade: TradeWithMetrics):
    """
    Render minimal stats for sidebar or compact display.

    v2.1.0: R-multiple based (aligned with System Analysis)

    Args:
        trade: TradeWithMetrics object
    """
    pnl_r = trade.pnl_r
    mfe_r = trade.mfe_r
    mae_r = trade.mae_r

    col1, col2 = st.columns(2)

    with col1:
        if pnl_r is not None:
            pnl_color = "green" if pnl_r > 0 else "red" if pnl_r < 0 else "gray"
            st.markdown(f"**P&L:** <span style='color:{pnl_color}'>{pnl_r:+.2f}R</span>", unsafe_allow_html=True)
        else:
            pnl_pts = trade.pnl_points or 0
            pnl_color = "green" if pnl_pts > 0 else "red" if pnl_pts < 0 else "gray"
            st.markdown(f"**P&L:** <span style='color:{pnl_color}'>{pnl_pts:+.2f} pts</span>", unsafe_allow_html=True)

    with col2:
        mfe_str = f"+{abs(mfe_r):.2f}R" if mfe_r is not None else f"+{abs(trade.mfe_points or 0):.2f}"
        mae_str = f"{mae_r:.2f}R" if mae_r is not None else f"{trade.mae_points or 0:.2f}"
        st.markdown(f"**MFE:** {mfe_str} | **MAE:** {mae_str}")


def _format_time(t: time) -> str:
    """Format time for display."""
    if t is None:
        return "N/A"
    return t.strftime("%H:%M:%S ET")


def _calculate_edge_efficiency(trade: TradeWithMetrics) -> float:
    """
    Calculate how much of the MFE was captured.
    Edge Efficiency = P&L / MFE (as percentage)

    v2.1.0: Uses R-multiples when available
    """
    mfe_r = trade.mfe_r
    pnl_r = trade.pnl_r

    if mfe_r is not None and mfe_r > 0 and pnl_r is not None:
        return (pnl_r / mfe_r) * 100

    # Fallback to points
    if not trade.mfe_points or trade.mfe_points <= 0:
        return 0.0

    pnl = trade.pnl_points or 0
    return (pnl / trade.mfe_points) * 100


def render_event_indicators_table(
    events: Optional[Dict[str, Dict[str, Any]]],
    trade: TradeWithMetrics,
    show_all_events: bool = False
):
    """
    Render indicator metrics table from optimal_trade events.

    In evaluate mode (show_all_events=False): Shows only ENTRY column
    In reveal mode (show_all_events=True): Shows ENTRY, MAE, MFE, EXIT columns

    v2.0.0: Uses points instead of R-multiples

    Args:
        events: Dict keyed by event_type (ENTRY, MAE, MFE, EXIT) with indicator values
        trade: TradeWithMetrics for context (direction)
        show_all_events: If True, show all 4 event columns; if False, only ENTRY
    """
    if not events:
        st.caption("Indicator data not available")
        return

    direction = trade.direction or "LONG"

    # Helper functions
    def format_price(val) -> str:
        if val is None:
            return "-"
        return f"${float(val):.2f}"

    def format_points(val) -> str:
        if val is None:
            return "-"
        return f"{float(val):+.2f} pts"

    def format_pct(val) -> str:
        if val is None:
            return "-"
        return f"{float(val):+.1f}%"

    def format_spread(val) -> str:
        if val is None:
            return "-"
        return f"{float(val):.2f}"

    def format_time(val) -> str:
        if val is None:
            return "-"
        if hasattr(val, 'strftime'):
            return val.strftime("%H:%M")
        return str(val)[:5]

    def get_health_color(score) -> str:
        if score is None:
            return "#888888"
        if score >= 8:
            return "#00C853"  # Green
        elif score >= 6:
            return "#FFC107"  # Yellow
        elif score >= 4:
            return "#FF9800"  # Orange
        else:
            return "#FF1744"  # Red

    def get_structure_color(structure: str) -> str:
        if not structure:
            return "#888888"
        s = structure.upper()
        if direction == 'LONG':
            if s == 'BULL':
                return "#00C853"
            elif s == 'BEAR':
                return "#FF1744"
        else:  # SHORT
            if s == 'BEAR':
                return "#00C853"
            elif s == 'BULL':
                return "#FF1744"
        return "#888888"

    def get_momentum_color(momentum: str) -> str:
        if not momentum:
            return "#888888"
        m = momentum.upper()
        if m == 'WIDENING':
            return "#00C853"
        elif m == 'NARROWING':
            return "#FF9800"
        return "#888888"

    # Define which events to show (v2.2.0: Include R-level crossings)
    if show_all_events:
        # Build event order dynamically based on what exists
        event_order = ['ENTRY']

        # Add R-level events if they exist
        if 'R1_CROSS' in events:
            event_order.append('R1_CROSS')
        if 'R2_CROSS' in events:
            event_order.append('R2_CROSS')
        if 'R3_CROSS' in events:
            event_order.append('R3_CROSS')

        # Add remaining core events
        event_order.extend(['MAE', 'MFE', 'EXIT'])

        event_labels = {
            'ENTRY': 'Entry',
            'R1_CROSS': '1R',
            'R2_CROSS': '2R',
            'R3_CROSS': '3R',
            'MAE': 'MAE',
            'MFE': 'MFE',
            'EXIT': 'Exit'
        }
    else:
        event_order = ['ENTRY']
        event_labels = {'ENTRY': 'Entry'}

    # Helper to calculate R-multiple for a price
    def calculate_r_for_price(price_val) -> Optional[float]:
        if price_val is None or not trade.entry_price or not trade.risk_per_share:
            return None
        if trade.risk_per_share == 0:
            return None
        entry = float(trade.entry_price)
        price = float(price_val)
        if trade.direction == 'LONG':
            pnl = price - entry
        else:
            pnl = entry - price
        return pnl / trade.risk_per_share

    def format_r(val) -> str:
        if val is None:
            return "-"
        return f"{float(val):+.2f}R"

    # Define metrics to display (v2.1.0: R-multiples as primary)
    metrics = [
        ('Time', 'event_time', format_time, None),
        ('Price', 'price_at_event', format_price, None),
        ('R-Multiple', 'price_at_event', lambda x: format_r(calculate_r_for_price(x)), None),
        ('Points', 'points_at_event', format_points, None),
        ('Health', 'health_score', lambda x: f"{x}/10" if x is not None else "-", get_health_color),
        ('VWAP', 'vwap', format_price, None),
        ('SMA9', 'sma9', format_price, None),
        ('SMA21', 'sma21', format_price, None),
        ('SMA Spread', 'sma_spread', format_spread, None),
        ('SMA Mom', 'sma_momentum_label', lambda x: x or "-", get_momentum_color),
        ('Vol ROC', 'vol_roc', format_pct, None),
        ('M5', 'm5_structure', lambda x: x or "-", get_structure_color),
        ('M15', 'm15_structure', lambda x: x or "-", get_structure_color),
        ('H1', 'h1_structure', lambda x: x or "-", get_structure_color),
        ('H4', 'h4_structure', lambda x: x or "-", get_structure_color),
    ]

    # Build HTML table
    col_count = len(event_order) + 1  # +1 for metric name column

    table_html = """
    <style>
    .event-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
        margin-top: 10px;
    }
    .event-table th, .event-table td {
        padding: 5px 8px;
        text-align: center;
        border-bottom: 1px solid #333;
    }
    .event-table th {
        background-color: #2a2a4e;
        color: #e0e0e0;
        font-weight: bold;
    }
    .event-table td:first-child {
        text-align: left;
        font-weight: bold;
        color: #888;
    }
    .event-table tr:hover {
        background-color: #252540;
    }
    </style>
    <table class="event-table">
    <tr>
        <th>Metric</th>
    """

    # Add column headers
    for event_type in event_order:
        label = event_labels[event_type]
        table_html += f"<th>{label}</th>"
    table_html += "</tr>"

    # Add rows for each metric
    for metric_name, metric_key, formatter, color_fn in metrics:
        table_html += f"<tr><td>{metric_name}</td>"

        for event_type in event_order:
            event_data = events.get(event_type, {})
            value = event_data.get(metric_key)
            formatted = formatter(value)

            if color_fn:
                color = color_fn(value)
                table_html += f"<td style='color:{color}'>{formatted}</td>"
            else:
                table_html += f"<td>{formatted}</td>"

        table_html += "</tr>"

    table_html += "</table>"

    st.markdown(table_html, unsafe_allow_html=True)
