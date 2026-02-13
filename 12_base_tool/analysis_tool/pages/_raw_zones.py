"""
Raw Zones Page - Displays all confluence zones before filtering.

Features:
- Grouped by ticker (all zones for each ticker together)
- Fixed tables (page scrolls, not individual tables)
- Columns: Ticker, Price, Direction, Zone_ID, HVN_POC, Zone High, Zone_Low, Overlaps, Score, Rank, Confluences
"""
import streamlit as st
import pandas as pd
from typing import List, Dict, Any, Optional

from core.data_models import RawZone, Direction


def render_raw_zones_page(results: Dict[str, Any]) -> None:
    """
    Render the Raw Zones page.

    Args:
        results: Analysis results containing raw_zones for each ticker
    """
    st.header("Raw Zones")
    st.markdown("All confluence zones before filtering, grouped by ticker.")

    # Get all successful results with raw_zones
    custom_results = results.get("custom", [])
    index_results = results.get("index", [])

    all_results = [
        r for r in (index_results + custom_results)
        if r.get("success") and r.get("raw_zones")
    ]

    if not all_results:
        st.warning("No raw zones available. Run analysis first.")
        return

    # Summary metrics
    total_zones = sum(len(r.get("raw_zones", [])) for r in all_results)
    all_zones = []
    for result in all_results:
        all_zones.extend(result.get("raw_zones", []))

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Zones", total_zones)
    with col2:
        l5_count = sum(1 for z in all_zones if get_rank_value(z.rank) == "L5")
        st.metric("L5 Zones", l5_count)
    with col3:
        l4_count = sum(1 for z in all_zones if get_rank_value(z.rank) == "L4")
        st.metric("L4 Zones", l4_count)
    with col4:
        avg_score = sum(z.score for z in all_zones) / len(all_zones) if all_zones else 0
        st.metric("Avg Score", f"{avg_score:.1f}")

    st.markdown("---")

    # Render each ticker's zones in a separate section
    for result in all_results:
        ticker = result.get("ticker", "Unknown")
        raw_zones = result.get("raw_zones", [])
        price = result.get("price", 0)
        direction = result.get("direction", "Neutral")

        if not raw_zones:
            continue

        # Ticker header
        st.subheader(f"{ticker} ({len(raw_zones)} zones)")

        # Render zones table for this ticker
        render_ticker_zones_table(raw_zones, ticker, price, direction)

        st.markdown("")  # Add spacing between tickers


def get_rank_value(rank) -> str:
    """Extract rank value from Rank enum or string."""
    if hasattr(rank, 'value'):
        return rank.value
    return str(rank)


def get_direction_value(direction) -> str:
    """Extract direction value from Direction enum or string."""
    if hasattr(direction, 'value'):
        return direction.value
    return str(direction)


def format_price(val: Optional[float]) -> str:
    """Format a price value."""
    if val is None:
        return "—"
    return f"{val:,.2f}"


def render_ticker_zones_table(zones: List[RawZone], ticker: str, price: float, direction: str) -> None:
    """
    Render zones table for a single ticker.
    Non-scrollable - page scrolls instead.

    Args:
        zones: List of RawZone objects for this ticker
        ticker: Ticker symbol
        price: Current price
        direction: Market direction
    """
    if not zones:
        st.info("No zones to display")
        return

    # Sort zones by score (highest first)
    sorted_zones = sorted(zones, key=lambda z: z.score, reverse=True)

    # Build DataFrame with specified columns
    rows = []
    for zone in sorted_zones:
        rank_val = get_rank_value(zone.rank)
        dir_val = get_direction_value(zone.direction) if hasattr(zone, 'direction') else direction
        confluences_str = zone.confluences_str if hasattr(zone, 'confluences_str') else ", ".join(zone.confluences)

        row = {
            "Ticker": zone.ticker,
            "Price": format_price(price),
            "Direction": dir_val,
            "Zone_ID": zone.zone_id,
            "HVN_POC": format_price(zone.hvn_poc),
            "Zone High": format_price(zone.zone_high),
            "Zone_Low": format_price(zone.zone_low),
            "Overlaps": zone.overlaps,
            "Score": f"{zone.score:.1f}",
            "Rank": rank_val,
            "Confluences": confluences_str,
        }
        rows.append(row)

    df = pd.DataFrame(rows)

    # Calculate height based on number of rows (no scroll within table)
    # Header (~35px) + rows (~35px each) + padding
    row_height = 35
    header_height = 35
    padding = 10
    table_height = header_height + (len(rows) * row_height) + padding

    # Cap at reasonable max to avoid overly tall single tables
    max_height = 800
    table_height = min(table_height, max_height)

    # Apply rank-based styling
    def highlight_rank(val):
        """Style rank cells with color."""
        rank_colors = {
            "L5": "background-color: #00C853; color: white;",
            "L4": "background-color: #2196F3; color: white;",
            "L3": "background-color: #FFC107; color: black;",
            "L2": "background-color: #9E9E9E; color: white;",
            "L1": "background-color: #616161; color: white;",
        }
        return rank_colors.get(val, "")

    def style_dataframe(df):
        """Apply styling to the dataframe."""
        return df.style.applymap(
            highlight_rank,
            subset=["Rank"]
        )

    styled_df = style_dataframe(df)

    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
        height=table_height
    )


# Standalone page entry point (for Streamlit multipage)
if __name__ == "__main__":
    st.set_page_config(page_title="Raw Zones", layout="wide")

    from core.state_manager import get_state

    results = get_state("analysis_results")
    if results:
        render_raw_zones_page(results)
    else:
        st.warning("No analysis results available. Please run analysis from the main page first.")
