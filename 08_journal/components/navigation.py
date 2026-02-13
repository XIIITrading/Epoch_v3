"""
Sidebar navigation for the journal review page.
Filters: date, ticker, account, model.
Trade list with selection and prev/next.
"""

import streamlit as st
from datetime import date
from typing import Dict, List, Optional

from data.journal_db import JournalDB


def render_sidebar_filters(db: JournalDB) -> Dict:
    """
    Render sidebar filter controls.

    Returns:
        Dict with keys: date, ticker, account, model
    """
    # --- Date picker ---
    available_dates = db.get_all_dates()
    if not available_dates:
        st.sidebar.warning("No trades in database yet.")
        return {}

    selected_date = st.sidebar.date_input(
        "Trade Date",
        value=available_dates[0],  # Most recent
    )

    # --- Load trades for selected date to populate filter options ---
    all_trades = db.get_trades_by_date(selected_date)

    if not all_trades:
        st.sidebar.info(f"No trades on {selected_date}")
        return {"date": selected_date, "trades": []}

    # --- Ticker filter ---
    symbols = sorted(set(t['symbol'] for t in all_trades))
    ticker_options = ["All"] + symbols
    selected_ticker = st.sidebar.selectbox("Ticker", ticker_options)

    # --- Account filter ---
    accounts = sorted(set(t['account'] for t in all_trades if t.get('account')))
    if accounts:
        account_options = ["All"] + accounts
        selected_account = st.sidebar.selectbox("Account", account_options)
    else:
        selected_account = "All"

    # --- Model filter ---
    model_options = ["All", "EPCH_01", "EPCH_02", "EPCH_03", "EPCH_04"]
    selected_model = st.sidebar.selectbox("Model", model_options)

    # --- Apply filters ---
    filtered = all_trades
    if selected_ticker != "All":
        filtered = [t for t in filtered if t['symbol'] == selected_ticker]
    if selected_account != "All":
        filtered = [t for t in filtered if t.get('account') == selected_account]
    if selected_model != "All":
        filtered = [t for t in filtered if t.get('model') == selected_model]

    return {
        "date": selected_date,
        "ticker": selected_ticker if selected_ticker != "All" else None,
        "account": selected_account if selected_account != "All" else None,
        "model": selected_model if selected_model != "All" else None,
        "trades": filtered,
    }


def render_trade_list(trades: List[Dict]) -> Optional[int]:
    """
    Render selectable trade list in sidebar with prev/next navigation.

    Returns:
        Index of selected trade, or None if no trades.
    """
    if not trades:
        return None

    # Initialize selection index
    if "selected_trade_index" not in st.session_state:
        st.session_state["selected_trade_index"] = 0

    idx = st.session_state["selected_trade_index"]
    idx = max(0, min(idx, len(trades) - 1))

    st.sidebar.divider()

    # --- Progress ---
    st.sidebar.markdown(f"**Trade {idx + 1} of {len(trades)}**")
    st.sidebar.progress((idx + 1) / len(trades))

    # --- Prev / Next ---
    col_prev, col_next = st.sidebar.columns(2)
    with col_prev:
        if st.button("< Prev", disabled=(idx == 0), use_container_width=True):
            st.session_state["selected_trade_index"] = idx - 1
            st.rerun()
    with col_next:
        if st.button("Next >", disabled=(idx >= len(trades) - 1), use_container_width=True):
            st.session_state["selected_trade_index"] = idx + 1
            st.rerun()

    st.sidebar.divider()

    # --- Trade list (clickable) ---
    for i, t in enumerate(trades):
        pnl = float(t.get('pnl_total', 0) or 0)
        pnl_str = f"${pnl:+,.0f}" if pnl != 0 else "$0"
        direction = t.get('direction', '')
        symbol = t.get('symbol', '')
        label = f"{symbol} {direction} {pnl_str}"

        # Highlight selected trade
        if i == idx:
            st.sidebar.markdown(f"**> {label}**")
        else:
            if st.sidebar.button(label, key=f"trade_select_{i}", use_container_width=True):
                st.session_state["selected_trade_index"] = i
                st.rerun()

    st.session_state["selected_trade_index"] = idx
    return idx
