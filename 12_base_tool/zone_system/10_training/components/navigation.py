"""
Epoch Trading System - Navigation Components
Sidebar filters and trade queue navigation.
"""

import streamlit as st
from datetime import date, timedelta
from typing import Dict, Optional, List

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.trade import TradeWithMetrics
from data.supabase_client import SupabaseClient


def render_sidebar_filters(supabase: SupabaseClient) -> Dict:
    """
    Render filter controls in sidebar.

    Args:
        supabase: Supabase client for fetching options

    Returns:
        Dict with filter values
    """
    st.markdown("### Filters")

    # Date range
    col1, col2 = st.columns(2)

    with col1:
        date_from = st.date_input(
            "From",
            value=date.today() - timedelta(days=30),
            key="filter_date_from"
        )

    with col2:
        date_to = st.date_input(
            "To",
            value=date.today(),
            key="filter_date_to"
        )

    # Ticker filter
    available_tickers = supabase.get_available_tickers(date_from=date_from)
    ticker_options = ["All Tickers"] + available_tickers

    selected_ticker = st.selectbox(
        "Ticker",
        options=ticker_options,
        index=0,
        key="filter_ticker"
    )
    ticker = None if selected_ticker == "All Tickers" else selected_ticker

    # Model filter
    model_options = ["All Models", "EPCH1", "EPCH2", "EPCH3", "EPCH4"]
    selected_model = st.selectbox(
        "Model",
        options=model_options,
        index=0,
        key="filter_model"
    )
    model = None if selected_model == "All Models" else selected_model

    # Review status filter
    st.markdown("---")
    unreviewed_only = st.checkbox(
        "Unreviewed Only",
        value=False,
        key="filter_unreviewed",
        help="Only show trades that haven't been reviewed yet"
    )

    return {
        'date_from': date_from,
        'date_to': date_to,
        'ticker': ticker,
        'model': model,
        'unreviewed_only': unreviewed_only
    }


def render_trade_counter(
    current_index: int,
    total_trades: int,
    trade: Optional[TradeWithMetrics] = None
):
    """
    Render trade counter header.

    Args:
        current_index: Current position in queue (0-indexed)
        total_trades: Total trades in queue
        trade: Optional current trade for additional info
    """
    # Progress display
    position = current_index + 1
    progress = position / total_trades if total_trades > 0 else 0

    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown(f"### Trade {position} of {total_trades}")

    with col2:
        st.progress(progress)

    # Trade info subheader
    if trade:
        direction_emoji = "🟢" if trade.direction == 'LONG' else "🔴"
        st.markdown(
            f"**{trade.ticker}** | {trade.date} | {trade.model} | "
            f"{direction_emoji} {trade.direction} | {trade.zone_type}"
        )


def render_queue_info(queue: List[TradeWithMetrics]):
    """
    Render queue statistics.

    Args:
        queue: List of trades in queue
    """
    if not queue:
        st.warning("No trades in queue")
        return

    st.markdown("### Queue Info")

    # Basic stats
    total = len(queue)
    st.metric("Trades in Queue", total)

    # Breakdown by outcome (if reviewed)
    winners = sum(1 for t in queue if t.is_winner)
    losers = total - winners

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Winners", winners)
    with col2:
        st.metric("Losers", losers)

    # Breakdown by model
    model_counts = {}
    for t in queue:
        model = t.model or "Unknown"
        model_counts[model] = model_counts.get(model, 0) + 1

    if model_counts:
        st.markdown("**By Model:**")
        for model, count in sorted(model_counts.items()):
            st.caption(f"{model}: {count}")

    # Breakdown by ticker
    ticker_counts = {}
    for t in queue:
        ticker_counts[t.ticker] = ticker_counts.get(t.ticker, 0) + 1

    if len(ticker_counts) <= 10:
        st.markdown("**By Ticker:**")
        for ticker, count in sorted(ticker_counts.items(), key=lambda x: -x[1]):
            st.caption(f"{ticker}: {count}")


def render_shuffle_button() -> bool:
    """
    Render shuffle queue button.

    Returns:
        True if shuffle was requested
    """
    return st.button(
        "🔀 Shuffle Queue",
        key="btn_shuffle",
        help="Randomize the order of trades in the queue"
    )


def render_jump_to_trade(total_trades: int) -> Optional[int]:
    """
    Render jump-to-trade control.

    Args:
        total_trades: Total trades in queue

    Returns:
        Trade number to jump to (0-indexed), or None
    """
    if total_trades <= 1:
        return None

    with st.expander("Jump to Trade"):
        jump_to = st.number_input(
            "Trade #",
            min_value=1,
            max_value=total_trades,
            value=1,
            key="jump_to_input"
        )

        if st.button("Go", key="btn_jump"):
            return jump_to - 1  # Convert to 0-indexed

    return None
