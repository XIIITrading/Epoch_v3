"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Streamlit Filter Components
XIII Trading LLC
================================================================================
"""

import streamlit as st
from datetime import date, datetime, timedelta
from typing import Dict, Any, Optional, Tuple
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DATE_FILTER_CONFIG


def get_date_filter(date_range: Dict[str, date]) -> Tuple[Optional[date], Optional[date]]:
    """Render date filter and return selected range."""
    st.sidebar.subheader("Date Filter")

    filter_type = st.sidebar.selectbox(
        "Range",
        options=list(DATE_FILTER_CONFIG["options"].keys()),
        format_func=lambda x: DATE_FILTER_CONFIG["options"][x],
        index=0
    )

    min_date = date_range.get("min_date")
    max_date = date_range.get("max_date")

    if filter_type == "all":
        return min_date, max_date
    elif filter_type == "year":
        return date(datetime.now().year, 1, 1), max_date
    elif filter_type == "month":
        today = datetime.now()
        return date(today.year, today.month, 1), max_date
    elif filter_type == "week":
        return date.today() - timedelta(days=7), max_date
    elif filter_type == "day":
        return date.today(), date.today()

    return min_date, max_date


def render_filters(
    tickers: list,
    models: list
) -> Dict[str, Any]:
    """Render all sidebar filters and return selections."""
    st.sidebar.header("Filters")

    # Model filter
    st.sidebar.subheader("Models")
    all_models = st.sidebar.checkbox("All Models", value=True)

    if all_models:
        selected_models = models
    else:
        selected_models = st.sidebar.multiselect(
            "Select Models",
            options=models,
            default=models
        )

    # Trade type filter
    st.sidebar.subheader("Trade Type")
    trade_type = st.sidebar.radio(
        "Filter by",
        options=["All", "Continuation", "Rejection"],
        index=0
    )

    if trade_type == "Continuation":
        selected_models = [m for m in selected_models if m in ["EPCH1", "EPCH3"]]
    elif trade_type == "Rejection":
        selected_models = [m for m in selected_models if m in ["EPCH2", "EPCH4"]]

    # Direction filter
    st.sidebar.subheader("Direction")
    direction = st.sidebar.radio(
        "Filter by",
        options=["All", "LONG", "SHORT"],
        index=0
    )

    selected_directions = None
    if direction != "All":
        selected_directions = [direction]

    # Ticker filter
    st.sidebar.subheader("Tickers")
    all_tickers = st.sidebar.checkbox("All Tickers", value=True)

    if all_tickers:
        selected_tickers = None
    else:
        selected_tickers = st.sidebar.multiselect(
            "Select Tickers",
            options=tickers,
            default=[]
        )
        if not selected_tickers:
            selected_tickers = None

    # Outcome filter
    st.sidebar.subheader("Outcome")
    outcome = st.sidebar.radio(
        "Filter by",
        options=["All", "Winners", "Losers"],
        index=0
    )

    return {
        "models": selected_models,
        "directions": selected_directions,
        "tickers": selected_tickers,
        "outcome": outcome,
        "trade_type": trade_type
    }
