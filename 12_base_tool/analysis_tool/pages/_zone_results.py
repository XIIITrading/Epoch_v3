"""
Zone Results Page - Displays filtered zones with tier classification.

Features:
- Filtered zones table with tier column
- Setup flags (epch_bull, epch_bear marked with 'X')
- Color coding by tier (T1=yellow, T2=orange, T3=green)
- ATR distance grouping
"""
import streamlit as st
import pandas as pd
from typing import List, Dict, Any, Optional

# Import styling functions from data_tables
from components.data_tables import (
    style_rank_cell,
    style_tier_cell,
    format_price,
    TIER_COLORS,
    RANK_COLORS
)


def render_zone_results_page(results: Dict[str, Any]) -> None:
    """
    Render the Zone Results page.

    Args:
        results: Analysis results containing filtered_zones for each ticker
    """
    st.header("Zone Results")
    st.markdown("Filtered zones with tier classification and setup identification.")

    # Get all successful results with filtered_zones
    custom_results = results.get("custom", [])
    index_results = results.get("index", [])

    all_results = [
        r for r in (index_results + custom_results)
        if r.get("success") and r.get("filtered_zones")
    ]

    if not all_results:
        st.warning("No filtered zones available. Run analysis first.")
        return

    # Collect all filtered zones
    all_zones = []
    for result in all_results:
        for zone in result.get("filtered_zones", []):
            all_zones.append(zone)

    if not all_zones:
        st.info("No filtered zones found")
        return

    # Filter controls
    col1, col2, col3 = st.columns(3)

    # Ticker filter
    with col1:
        tickers = sorted(set(z.ticker for z in all_zones))
        selected_tickers = st.multiselect(
            "Filter by Ticker",
            options=tickers,
            default=tickers,
            key="zone_results_ticker_filter"
        )

    # Tier filter
    with col2:
        tiers = ["T3", "T2", "T1"]
        selected_tiers = st.multiselect(
            "Filter by Tier",
            options=tiers,
            default=tiers,
            key="zone_results_tier_filter"
        )

    # Show only setup zones
    with col3:
        show_only_setups = st.checkbox(
            "Show only Bull/Bear POCs",
            value=False,
            key="zone_results_setups_only"
        )

    # Apply filters
    filtered_zones = [
        z for z in all_zones
        if z.ticker in selected_tickers
        and (z.tier.value if hasattr(z.tier, 'value') else z.tier) in selected_tiers
    ]

    if show_only_setups:
        filtered_zones = [z for z in filtered_zones if z.is_bull_poc or z.is_bear_poc]

    # Summary metrics
    st.markdown("---")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Zones", len(filtered_zones))
    with col2:
        t3_count = sum(1 for z in filtered_zones if (z.tier.value if hasattr(z.tier, 'value') else z.tier) == "T3")
        st.metric("T3 (Best)", t3_count)
    with col3:
        t2_count = sum(1 for z in filtered_zones if (z.tier.value if hasattr(z.tier, 'value') else z.tier) == "T2")
        st.metric("T2 (Medium)", t2_count)
    with col4:
        bull_count = sum(1 for z in filtered_zones if z.is_bull_poc)
        st.metric("Bull POCs", bull_count)
    with col5:
        bear_count = sum(1 for z in filtered_zones if z.is_bear_poc)
        st.metric("Bear POCs", bear_count)

    # Main filtered zones table
    st.markdown("---")
    st.subheader("Filtered Zones")
    render_filtered_zones_table(filtered_zones)

    # Setup Summary section
    st.markdown("---")
    st.subheader("Setup Summary")
    render_setup_summary(all_results)


def calculate_table_height(num_rows: int, max_height: int = 800) -> int:
    """
    Calculate table height based on number of rows.
    No scrolling within table - page scrolls instead.

    Args:
        num_rows: Number of data rows
        max_height: Maximum table height in pixels

    Returns:
        Calculated height in pixels
    """
    row_height = 35
    header_height = 35
    padding = 10
    table_height = header_height + (num_rows * row_height) + padding
    return min(table_height, max_height)


def render_filtered_zones_table(zones: List) -> None:
    """
    Render the filtered zones table with tier and setup styling.
    Non-scrollable - page scrolls instead.

    Args:
        zones: List of FilteredZone objects
    """
    if not zones:
        st.info("No zones to display")
        return

    # Build DataFrame
    rows = []
    for zone in zones:
        tier_val = zone.tier.value if hasattr(zone.tier, 'value') else zone.tier
        rank_val = zone.rank.value if hasattr(zone.rank, 'value') else zone.rank

        row = {
            "Ticker": zone.ticker,
            "Zone ID": zone.zone_id,
            "HVN POC": zone.hvn_poc,
            "Zone High": zone.zone_high,
            "Zone Low": zone.zone_low,
            "Score": zone.score,
            "Rank": rank_val,
            "Tier": tier_val,
            "ATR Dist": zone.atr_distance,
            "Group": zone.proximity_group or "—",
            "Bull": "X" if zone.is_bull_poc else "",
            "Bear": "X" if zone.is_bear_poc else "",
        }
        rows.append(row)

    df = pd.DataFrame(rows)

    # Format columns
    price_cols = ["HVN POC", "Zone High", "Zone Low"]
    for col in price_cols:
        df[col] = df[col].apply(format_price)

    df["Score"] = df["Score"].apply(lambda x: f"{x:.1f}")
    df["ATR Dist"] = df["ATR Dist"].apply(lambda x: f"{x:.2f}" if x else "—")

    # Apply styling
    def style_row(row):
        styles = [""] * len(row)
        for i, col in enumerate(row.index):
            if col == "Rank":
                styles[i] = style_rank_cell(str(row[col]))
            elif col == "Tier":
                styles[i] = style_tier_cell(str(row[col]))
            elif col in ["Bull", "Bear"] and row[col] == "X":
                styles[i] = "background-color: #2962FF; color: white; font-weight: bold;"
        return styles

    styled = df.style.apply(style_row, axis=1)

    # Calculate dynamic height based on row count (no internal scrolling)
    table_height = calculate_table_height(len(rows))

    st.dataframe(
        styled,
        use_container_width=True,
        hide_index=True,
        height=table_height
    )


def render_setup_summary(results: List[Dict]) -> None:
    """
    Render a summary of bull/bear POCs per ticker.

    Args:
        results: Analysis results
    """
    rows = []
    for result in results:
        if not result.get("success"):
            continue

        ticker = result.get("ticker", "Unknown")
        filtered_zones = result.get("filtered_zones", [])
        price = result.get("bar_data").price if result.get("bar_data") else None

        # Find bull and bear POCs
        bull_poc = None
        bear_poc = None
        for zone in filtered_zones:
            if zone.is_bull_poc:
                bull_poc = zone
            if zone.is_bear_poc:
                bear_poc = zone

        row = {
            "Ticker": ticker,
            "Price": price,
            "Bull POC": bull_poc.hvn_poc if bull_poc else None,
            "Bull Tier": (bull_poc.tier.value if hasattr(bull_poc.tier, 'value') else bull_poc.tier) if bull_poc else "—",
            "Bull Score": bull_poc.score if bull_poc else None,
            "Bear POC": bear_poc.hvn_poc if bear_poc else None,
            "Bear Tier": (bear_poc.tier.value if hasattr(bear_poc.tier, 'value') else bear_poc.tier) if bear_poc else "—",
            "Bear Score": bear_poc.score if bear_poc else None,
        }
        rows.append(row)

    if not rows:
        st.info("No setup data available")
        return

    df = pd.DataFrame(rows)

    # Format columns
    df["Price"] = df["Price"].apply(format_price)
    df["Bull POC"] = df["Bull POC"].apply(format_price)
    df["Bear POC"] = df["Bear POC"].apply(format_price)
    df["Bull Score"] = df["Bull Score"].apply(lambda x: f"{x:.1f}" if x else "—")
    df["Bear Score"] = df["Bear Score"].apply(lambda x: f"{x:.1f}" if x else "—")

    # Apply tier styling
    def style_setup_row(row):
        styles = [""] * len(row)
        for i, col in enumerate(row.index):
            if col in ["Bull Tier", "Bear Tier"]:
                styles[i] = style_tier_cell(str(row[col]))
        return styles

    styled = df.style.apply(style_setup_row, axis=1)

    # Calculate dynamic height based on row count (no internal scrolling)
    table_height = calculate_table_height(len(rows))

    st.dataframe(
        styled,
        use_container_width=True,
        hide_index=True,
        height=table_height
    )


def render_proximity_groups(results: Dict[str, Any]) -> None:
    """
    Alternative view: show zones grouped by proximity to price.

    Args:
        results: Analysis results
    """
    st.subheader("Zones by Proximity Group")

    custom_results = results.get("custom", [])

    for result in custom_results:
        if not result.get("success") or not result.get("filtered_zones"):
            continue

        ticker = result.get("ticker", "Unknown")
        zones = result.get("filtered_zones", [])

        # Group by proximity
        group1 = [z for z in zones if z.proximity_group == "Group 1"]
        group2 = [z for z in zones if z.proximity_group == "Group 2"]

        with st.expander(f"{ticker} - {len(group1)} in Group 1, {len(group2)} in Group 2"):
            if group1:
                st.markdown("**Group 1 (Within 1 ATR)**")
                render_filtered_zones_table(group1)

            if group2:
                st.markdown("**Group 2 (1-2 ATR)**")
                render_filtered_zones_table(group2)


# Standalone page entry point (for Streamlit multipage)
if __name__ == "__main__":
    st.set_page_config(page_title="Zone Results", layout="wide")

    from core.state_manager import get_state

    results = get_state("analysis_results")
    if results:
        render_zone_results_page(results)
    else:
        st.warning("No analysis results available. Please run analysis from the main page first.")
