"""
Market Overview Page - Index and Ticker Structure Display

Replicates the market_overview sheet from Excel with:
- Section A: Index Structure (SPY, QQQ, DIA)
- Section B: Ticker Structure (user-defined tickers)

Displays D1/H4/H1/M15 direction and strong/weak levels with composite direction.
"""
import streamlit as st
from datetime import date
from typing import Dict, List, Optional

from core.state_manager import get_state
from components.data_tables import render_market_structure_table


def render_market_overview():
    """Render the market overview page."""
    st.header("Market Overview")
    st.markdown("Market structure analysis across multiple timeframes.")

    # Get analysis results from session state
    results = get_state("analysis_results", {})

    if not results:
        st.info("No analysis results available. Run analysis from the sidebar to see market structure.")
        return

    # Section A: Index Structure
    st.markdown("---")
    index_results = results.get("index", [])

    if index_results:
        index_data = _format_structure_data(index_results, is_index=True)
        render_market_structure_table(index_data, "Index Structure (Prior Month)")
    else:
        st.warning("No index structure data available")

    # Section B: Ticker Structure
    st.markdown("---")
    custom_results = results.get("custom", [])

    if custom_results:
        ticker_data = _format_structure_data(custom_results, is_index=False)
        render_market_structure_table(ticker_data, "Ticker Structure (Custom Anchor)")

        # Show detailed zone summary per ticker
        st.markdown("---")
        st.subheader("Zone Summary")

        for result in custom_results:
            if result.get("success"):
                _render_ticker_summary(result)
    else:
        st.info("No custom ticker results available")


def _format_structure_data(results: List[Dict], is_index: bool = False) -> List[Dict]:
    """
    Format results for market structure table display.

    Args:
        results: List of result dictionaries
        is_index: Whether these are index tickers

    Returns:
        List of formatted dictionaries for table rendering
    """
    formatted = []

    for result in results:
        if not result.get("success", False):
            # Include failed tickers with error indication
            formatted.append({
                "ticker": result.get("ticker", "???"),
                "price": None,
                "d1_direction": "ERROR",
                "d1_strong": None,
                "d1_weak": None,
                "h4_direction": "ERROR",
                "h4_strong": None,
                "h4_weak": None,
                "h1_direction": "ERROR",
                "h1_strong": None,
                "h1_weak": None,
                "m15_direction": "ERROR",
                "composite": "ERROR",
            })
            continue

        # Get market structure if available
        market_structure = result.get("market_structure")
        bar_data = result.get("bar_data")

        if market_structure:
            # Full market structure available
            formatted.append({
                "ticker": result.get("ticker", ""),
                "price": market_structure.price,
                "d1_direction": market_structure.d1.direction.value,
                "d1_strong": market_structure.d1.strong,
                "d1_weak": market_structure.d1.weak,
                "h4_direction": market_structure.h4.direction.value,
                "h4_strong": market_structure.h4.strong,
                "h4_weak": market_structure.h4.weak,
                "h1_direction": market_structure.h1.direction.value,
                "h1_strong": market_structure.h1.strong,
                "h1_weak": market_structure.h1.weak,
                "m15_direction": market_structure.m15.direction.value,
                "m15_strong": market_structure.m15.strong,
                "m15_weak": market_structure.m15.weak,
                "composite": market_structure.composite.value,
            })
        else:
            # Simplified view (just direction from pipeline)
            formatted.append({
                "ticker": result.get("ticker", ""),
                "price": result.get("price") or (bar_data.price if bar_data else None),
                "d1_direction": result.get("direction", "—"),
                "d1_strong": None,
                "d1_weak": None,
                "h4_direction": "—",
                "h4_strong": None,
                "h4_weak": None,
                "h1_direction": "—",
                "h1_strong": None,
                "h1_weak": None,
                "m15_direction": "—",
                "m15_strong": None,
                "m15_weak": None,
                "composite": result.get("direction", "—"),
            })

    return formatted


def _render_ticker_summary(result: Dict) -> None:
    """
    Render a summary card for a single ticker's results.

    Args:
        result: Result dictionary for a ticker
    """
    ticker = result.get("ticker", "")
    zones_count = result.get("zones_count", 0)
    bull_poc = result.get("bull_poc", "N/A")
    bear_poc = result.get("bear_poc", "N/A")
    direction = result.get("direction", "Neutral")
    price = result.get("price", 0)
    anchor_date = result.get("anchor_date", "")

    with st.expander(f"{ticker} - {zones_count} zones", expanded=False):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Price", f"${price:,.2f}" if price else "—")
            st.caption(f"Anchor: {anchor_date}")

        with col2:
            st.metric("Bull POC", bull_poc)

        with col3:
            st.metric("Bear POC", bear_poc)

        # Show filtered zones if available
        filtered_zones = result.get("filtered_zones", [])
        if filtered_zones:
            st.markdown("**Filtered Zones:**")
            from components.data_tables import render_zones_table
            render_zones_table(filtered_zones, title="")


# Page entry point
if __name__ == "__main__":
    render_market_overview()
else:
    # When imported as a Streamlit page
    render_market_overview()
