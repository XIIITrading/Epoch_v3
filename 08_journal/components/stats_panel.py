"""
Epoch Trading Journal - Stats Panel Component
Displays trade statistics and event indicators in reveal mode.

Adapted from 06_training/components/stats_panel.py.
Uses JournalTradeWithMetrics instead of TradeWithMetrics.

Differences from 06_training:
    - Uses user-set stop_price (not ATR-calculated)
    - M1 timeframe (not M5) in event indicators
    - No zone_tier / zone_rank (journal tracks zone_id only)
    - Duration based on actual exit (not fixed EOD 15:30)
"""

import streamlit as st
from datetime import time, datetime
from typing import Dict, Any, Optional

from core.training_models import JournalTradeWithMetrics


def render_stats_panel(trade: JournalTradeWithMetrics):
    """
    Display trade statistics in a clean, readable format.
    Only shown in REVEAL mode.

    Args:
        trade: JournalTradeWithMetrics object with all metrics
    """
    st.markdown("### Trade Statistics")

    # Main metrics row - R-multiples as primary
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        pnl_r = trade.pnl_r
        is_winner = trade.is_winner_r
        delta_color = "normal" if is_winner else "inverse"

        if pnl_r is not None:
            # Dollar P&L as secondary
            pnl_total = getattr(trade.trade, 'pnl_total', None)
            delta_str = f"{'Winner' if is_winner else 'Loser'}"
            if pnl_total is not None:
                delta_str += f" (${pnl_total:+,.2f})"

            st.metric(
                label="P&L (R)",
                value=f"{pnl_r:+.2f}R",
                delta=delta_str,
                delta_color=delta_color,
            )
        else:
            pnl_total = getattr(trade.trade, 'pnl_total', 0) or 0
            st.metric(
                label="P&L",
                value=f"${pnl_total:+,.2f}",
                delta="Winner" if pnl_total > 0 else "Loser",
                delta_color="normal" if pnl_total >= 0 else "inverse",
            )

    with col2:
        mfe_r = trade.mfe_r
        mfe_points = trade.mfe_points

        if mfe_r is not None:
            bar_str = f"Bar {trade.mfe_bar_index}" if trade.mfe_bar_index else ""
            pts_str = f" (+{abs(mfe_points):.2f} pts)" if mfe_points is not None else ""
            delta_text = f"{bar_str}{pts_str}" if bar_str or pts_str else None

            st.metric(
                label="MFE (R)",
                value=f"+{abs(mfe_r):.2f}R",
                delta=delta_text,
                help="Maximum Favorable Excursion — best movement from entry to exit",
            )
        else:
            st.metric(label="MFE", value="N/A", help="Requires stop_price to calculate R-multiples")

    with col3:
        mae_r = trade.mae_r
        mae_points = trade.mae_points

        if mae_r is not None:
            bar_str = f"Bar {trade.mae_bar_index}" if trade.mae_bar_index else ""
            pts_str = f" ({mae_points:.2f} pts)" if mae_points is not None else ""
            delta_text = f"{bar_str}{pts_str}" if bar_str or pts_str else None

            st.metric(
                label="MAE (R)",
                value=f"{mae_r:.2f}R",
                delta=delta_text,
                help="Maximum Adverse Excursion — worst movement from entry to exit",
            )
        else:
            st.metric(label="MAE", value="N/A", help="Requires stop_price to calculate R-multiples")

    with col4:
        duration = trade.duration_minutes
        if duration:
            if duration >= 60:
                duration_str = f"{duration // 60}h {duration % 60}m"
            else:
                duration_str = f"{duration}m"
        else:
            duration_str = "N/A"

        temporal_win = getattr(trade, 'temporal_win', None)
        temporal_str = "MFE before MAE" if temporal_win else "MAE before MFE" if temporal_win is False else None

        st.metric(
            label="Duration",
            value=duration_str,
            delta=temporal_str,
        )

    # R-Levels info row
    st.markdown("---")
    st.markdown("**R-Levels (User-defined Stop)**")
    r_col1, r_col2, r_col3, r_col4, r_col5 = st.columns(5)

    with r_col1:
        stop = trade.stop_price
        st.markdown(f"**Stop:** ${stop:.2f}" if stop else "**Stop:** N/A")

    with r_col2:
        entry = trade.entry_price
        st.markdown(f"**Entry:** ${entry:.2f}" if entry else "**Entry:** N/A")

    with r_col3:
        r1 = trade.r1_price
        st.markdown(f"**1R:** ${r1:.2f}" if r1 else "**1R:** N/A")

    with r_col4:
        r2 = trade.r2_price
        st.markdown(f"**2R:** ${r2:.2f}" if r2 else "**2R:** N/A")

    with r_col5:
        r3 = trade.r3_price
        st.markdown(f"**3R:** ${r3:.2f}" if r3 else "**3R:** N/A")

    # R-Level Crossings row
    if trade.r1_hit or trade.r2_hit or trade.r3_hit:
        st.markdown("---")
        st.markdown("**R-Level Crossings** (Health at crossing)")
        cross_col1, cross_col2, cross_col3 = st.columns(3)

        with cross_col1:
            if trade.r1_hit:
                health_str = f"{trade.r1_health}/10" if trade.r1_health is not None else "N/A"
                delta_str = ""
                if trade.r1_health_delta is not None:
                    delta_str = f" ({trade.r1_health_delta:+.0f})"
                time_str = trade.r1_hit_time.strftime("%H:%M") if trade.r1_hit_time else "N/A"
                st.markdown(f"**1R:** {time_str} | Health: {health_str}{delta_str}")
            else:
                st.markdown("**1R:** Not reached")

        with cross_col2:
            if trade.r2_hit:
                health_str = f"{trade.r2_health}/10" if trade.r2_health is not None else "N/A"
                delta_str = ""
                if trade.r2_health_delta is not None:
                    delta_str = f" ({trade.r2_health_delta:+.0f})"
                time_str = trade.r2_hit_time.strftime("%H:%M") if trade.r2_hit_time else "N/A"
                st.markdown(f"**2R:** {time_str} | Health: {health_str}{delta_str}")
            else:
                st.markdown("**2R:** Not reached")

        with cross_col3:
            if trade.r3_hit:
                health_str = f"{trade.r3_health}/10" if trade.r3_health is not None else "N/A"
                delta_str = ""
                if trade.r3_health_delta is not None:
                    delta_str = f" ({trade.r3_health_delta:+.0f})"
                time_str = trade.r3_hit_time.strftime("%H:%M") if trade.r3_hit_time else "N/A"
                st.markdown(f"**3R:** {time_str} | Health: {health_str}{delta_str}")
            else:
                st.markdown("**3R:** Not reached")

    # Additional details in expander
    with st.expander("Full Trade Details", expanded=False):
        detail_col1, detail_col2, detail_col3 = st.columns(3)

        with detail_col1:
            st.markdown("**Trade Info**")
            st.write(f"Trade ID: {trade.trade_id}")
            st.write(f"Model: {trade.model or 'N/A'}")
            st.write(f"Direction: {trade.direction}")
            st.write(f"Ticker: {trade.ticker}")
            st.write(f"Date: {trade.date}")

        with detail_col2:
            st.markdown("**Entry/Exit**")
            st.write(f"Entry: ${trade.entry_price:.2f}" if trade.entry_price else "Entry: N/A")
            st.write(f"Entry Time: {_format_time(trade.entry_time)}")
            st.write(f"Exit: ${trade.exit_price:.2f}" if trade.exit_price else "Exit: N/A")
            st.write(f"Exit Time: {_format_time(trade.exit_time)}")

        with detail_col3:
            st.markdown("**Risk Metrics**")
            risk = trade.risk_per_share
            st.write(f"Risk/Share: ${risk:.2f}" if risk else "Risk/Share: N/A")
            stop = trade.stop_price
            st.write(f"Stop Price: ${stop:.2f}" if stop else "Stop Price: N/A")
            st.write(f"Outcome: {trade.outcome_r}")
            st.write(f"Win (R>0): {'Yes' if trade.is_winner_r else 'No'}")
            st.write(f"Max R Achieved: {trade.max_r_achieved:.2f}R" if trade.max_r_achieved else "Max R: N/A")

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

        # Zone info (if available)
        if trade.zone_high or trade.zone_low:
            st.markdown("---")
            st.markdown("**Zone Boundaries**")
            zone_col1, zone_col2, zone_col3 = st.columns(3)
            with zone_col1:
                st.write(f"Zone High: ${trade.zone_high:.2f}" if trade.zone_high else "Zone High: N/A")
            with zone_col2:
                zm = trade.zone_mid
                st.write(f"Zone POC: ${zm:.2f}" if zm else "Zone POC: N/A")
            with zone_col3:
                st.write(f"Zone Low: ${trade.zone_low:.2f}" if trade.zone_low else "Zone Low: N/A")


def render_quick_stats(trade: JournalTradeWithMetrics):
    """
    Render minimal stats for sidebar or compact display.

    Args:
        trade: JournalTradeWithMetrics object
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
            pnl_total = getattr(trade.trade, 'pnl_total', 0) or 0
            pnl_color = "green" if pnl_total > 0 else "red" if pnl_total < 0 else "gray"
            st.markdown(f"**P&L:** <span style='color:{pnl_color}'>${pnl_total:+,.2f}</span>", unsafe_allow_html=True)

    with col2:
        mfe_str = f"+{abs(mfe_r):.2f}R" if mfe_r is not None else "N/A"
        mae_str = f"{mae_r:.2f}R" if mae_r is not None else "N/A"
        st.markdown(f"**MFE:** {mfe_str} | **MAE:** {mae_str}")


def render_event_indicators_table(
    events: Optional[Dict[str, Dict[str, Any]]],
    trade: JournalTradeWithMetrics,
    show_all_events: bool = False,
):
    """
    Render indicator metrics table from optimal_trade events.

    In evaluate mode (show_all_events=False): Shows only ENTRY column
    In reveal mode (show_all_events=True): Shows ENTRY + R-crossings + MAE/MFE/EXIT

    Args:
        events: Dict keyed by event_type (ENTRY, MAE, MFE, EXIT, R1_CROSS, etc.)
        trade: JournalTradeWithMetrics for context
        show_all_events: If True, show all event columns; if False, only ENTRY
    """
    if not events:
        st.caption("Indicator data not available")
        return

    direction = str(trade.direction).upper() if trade.direction else "LONG"

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
        score = int(score) if score is not None else 0
        if score >= 8:
            return "#00C853"
        elif score >= 6:
            return "#FFC107"
        elif score >= 4:
            return "#FF9800"
        else:
            return "#FF1744"

    def get_structure_color(structure: str) -> str:
        if not structure:
            return "#888888"
        s = structure.upper()
        if 'LONG' in direction:
            if s == 'BULL':
                return "#00C853"
            elif s == 'BEAR':
                return "#FF1744"
        else:
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

    # Define which events to show
    if show_all_events:
        event_order = ['ENTRY']
        if 'R1_CROSS' in events:
            event_order.append('R1_CROSS')
        if 'R2_CROSS' in events:
            event_order.append('R2_CROSS')
        if 'R3_CROSS' in events:
            event_order.append('R3_CROSS')
        event_order.extend(['MAE', 'MFE', 'EXIT'])

        event_labels = {
            'ENTRY': 'Entry',
            'R1_CROSS': '1R',
            'R2_CROSS': '2R',
            'R3_CROSS': '3R',
            'MAE': 'MAE',
            'MFE': 'MFE',
            'EXIT': 'Exit',
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
        if 'LONG' in direction:
            pnl = price - entry
        else:
            pnl = entry - price
        return pnl / trade.risk_per_share

    def format_r(val) -> str:
        if val is None:
            return "-"
        return f"{float(val):+.2f}R"

    # Define metrics to display (M1 instead of M5)
    metrics = [
        ('Time', 'event_time', format_time, None),
        ('Price', 'price_at_event', format_price, None),
        ('R-Multiple', 'price_at_event', lambda x: format_r(calculate_r_for_price(x)), None),
        ('Points', 'points_at_event', format_points, None),
        ('Health', 'health_score', lambda x: f"{int(x)}/10" if x is not None else "-", get_health_color),
        ('VWAP', 'vwap', format_price, None),
        ('SMA9', 'sma9', format_price, None),
        ('SMA21', 'sma21', format_price, None),
        ('SMA Spread', 'sma_spread', format_spread, None),
        ('SMA Mom', 'sma_momentum_label', lambda x: x or "-", get_momentum_color),
        ('Vol ROC', 'vol_roc', format_pct, None),
        ('M1', 'm1_structure', lambda x: x or "-", get_structure_color),
        ('M15', 'm15_structure', lambda x: x or "-", get_structure_color),
        ('H1', 'h1_structure', lambda x: x or "-", get_structure_color),
        ('H4', 'h4_structure', lambda x: x or "-", get_structure_color),
    ]

    # Build HTML table
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
        label = event_labels.get(event_type, event_type)
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


def _format_time(t) -> str:
    """Format time for display."""
    if t is None:
        return "N/A"
    if hasattr(t, 'strftime'):
        return t.strftime("%H:%M:%S ET")
    return str(t)
