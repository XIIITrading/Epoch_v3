"""
Review page — Trade review with multi-timeframe charts and annotation form.

Flow:
    Sidebar filters → Load trades → Select trade → Fetch bars → Build chart
    → Render review form → Save annotations
"""

import streamlit as st
from datetime import datetime

from core.models import Trade
from data.journal_db import JournalDB
from data.cache_manager import BarCache
from components.charts import build_journal_chart
from components.rampup_chart import render_rampup_chart
from components.navigation import render_sidebar_filters, render_trade_list
from config import CHART_CONFIG


def render_review_page():
    """Render the trade review page."""
    st.header("Review Trades")

    db = JournalDB()
    db.connect()

    # -----------------------------------------------------------------
    # Sidebar: filters + trade list
    # -----------------------------------------------------------------
    filters = render_sidebar_filters(db)

    if not filters or not filters.get("trades"):
        st.info("Select a date with trades to begin review.")
        db.close()
        return

    trades = filters["trades"]
    selected_idx = render_trade_list(trades)

    if selected_idx is None:
        db.close()
        return

    trade_row = trades[selected_idx]

    # -----------------------------------------------------------------
    # Reconstruct Trade object from DB row
    # -----------------------------------------------------------------
    trade = Trade.from_db_row(trade_row)

    # -----------------------------------------------------------------
    # Trade header cards
    # -----------------------------------------------------------------
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Symbol", trade.symbol)
    c2.metric("Direction", trade.direction.value)

    pnl_str = f"${trade.pnl_total:+,.2f}" if trade.pnl_total is not None else "N/A"
    c3.metric("P&L", pnl_str)
    c4.metric("Duration", trade.duration_display or "N/A")
    c5.metric("Account", trade.account or "N/A")

    st.divider()

    # -----------------------------------------------------------------
    # Fetch bar data
    # -----------------------------------------------------------------
    cache = BarCache()

    with st.spinner(f"Loading chart data for {trade.symbol}..."):
        bar_data = cache.get_bars(
            ticker=trade.symbol,
            trade_date=trade.trade_date,
            trade=trade,
        )

    if bar_data is None:
        st.error(f"Could not fetch bar data for {trade.symbol} on {trade.trade_date}")
        db.close()
        return

    # -----------------------------------------------------------------
    # Fetch zones
    # -----------------------------------------------------------------
    zones = db.get_zones_for_ticker(trade.symbol, trade.trade_date)

    # -----------------------------------------------------------------
    # Build and render chart
    # -----------------------------------------------------------------
    fig = build_journal_chart(
        bars_1m=bar_data.bars_1m,
        bars_15m=bar_data.bars_15m,
        bars_1h=bar_data.bars_1h,
        trade=trade,
        zones=zones,
    )

    st.plotly_chart(fig, use_container_width=True)

    # -----------------------------------------------------------------
    # Ramp-Up Chart (M1 indicator table)
    # -----------------------------------------------------------------
    if trade.entry_time is not None:
        rampup_fig = render_rampup_chart(
            ticker=trade.symbol,
            trade_date=trade.trade_date,
            entry_time=trade.entry_time,
            direction=trade.direction.value,
        )
        if rampup_fig is not None:
            st.plotly_chart(rampup_fig, use_container_width=True)

    # -----------------------------------------------------------------
    # Review form
    # -----------------------------------------------------------------
    st.divider()
    st.subheader("Trade Review")

    # --- Zone auto-suggest (only show PRIMARY/SECONDARY setup zones) ---
    setup_zones = [z for z in zones if z.get('setup_type') in ('PRIMARY', 'SECONDARY')]
    zone_options = ["None"] + [
        f"{z.get('zone_id', '')} ({z.get('setup_type')} | Rank: {z.get('rank', 'N/A')}, Score: {z.get('score', 'N/A')})"
        for z in setup_zones
    ]
    zone_ids = [None] + [z.get('zone_id') for z in setup_zones]

    # Pre-select if already reviewed
    current_zone_idx = 0
    if trade.zone_id and trade.zone_id in zone_ids:
        current_zone_idx = zone_ids.index(trade.zone_id)

    col_z, col_m = st.columns(2)

    with col_z:
        zone_selection = st.selectbox(
            "Zone",
            options=zone_options,
            index=current_zone_idx,
        )
        selected_zone_id = zone_ids[zone_options.index(zone_selection)]

    with col_m:
        model_options = ["None", "EPCH_01", "EPCH_02", "EPCH_03", "EPCH_04"]
        current_model_idx = 0
        if trade.model and trade.model in model_options:
            current_model_idx = model_options.index(trade.model)

        selected_model = st.selectbox("Model", model_options, index=current_model_idx)
        if selected_model == "None":
            selected_model = None

    # --- Stop price + R-multiple ---
    col_s, col_r = st.columns(2)

    with col_s:
        stop_price = st.number_input(
            "Stop Price",
            value=float(trade.stop_price) if trade.stop_price else 0.0,
            format="%.4f",
            step=0.01,
        )
        if stop_price == 0.0:
            stop_price = None

    with col_r:
        # Live R-multiple calculation
        if stop_price and trade.pnl_dollars is not None:
            risk = abs(trade.entry_price - stop_price)
            if risk > 0:
                r_multiple = trade.pnl_dollars / risk
                st.metric("R-Multiple", f"{r_multiple:+.2f}R")
            else:
                st.metric("R-Multiple", "N/A")
        else:
            st.metric("R-Multiple", "Set stop to calculate")

    # --- Notes ---
    notes = st.text_area(
        "Notes",
        value=trade.notes or "",
        height=100,
        placeholder="What did you learn from this trade?",
    )

    # --- Save ---
    if st.button("Save Review", type="primary"):
        success = db.update_review_fields(
            trade_id=trade.trade_id,
            zone_id=selected_zone_id,
            model=selected_model,
            stop_price=stop_price,
            notes=notes if notes.strip() else None,
        )
        if success:
            st.success("Review saved.")
        else:
            st.error("Failed to save review.")

    db.close()
