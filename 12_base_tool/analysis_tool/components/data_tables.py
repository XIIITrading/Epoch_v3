"""
Data Tables Component - Styled dataframe displays for analysis output.

Provides consistent formatting and color coding for:
- Market structure tables
- Bar data tables
- Zone tables
"""
import pandas as pd
import streamlit as st
from typing import Dict, List, Optional


# Color definitions for direction styling
DIRECTION_COLORS = {
    "Bull+": "#006400",   # Dark green
    "Bull": "#228B22",    # Forest green
    "Neutral": "#808080", # Gray
    "Bear": "#DC143C",    # Crimson red
    "Bear+": "#8B0000",   # Dark red
    "ERROR": "#FF6347",   # Tomato
}

# Tier colors
TIER_COLORS = {
    "T1": "#FFD700",  # Gold/Yellow
    "T2": "#FFA500",  # Orange
    "T3": "#32CD32",  # Lime green
}

# Rank colors
RANK_COLORS = {
    "L5": "#006400",  # Dark green (best)
    "L4": "#228B22",  # Forest green
    "L3": "#FFD700",  # Gold
    "L2": "#FFA500",  # Orange
    "L1": "#DC143C",  # Red (worst)
}


def style_direction_cell(val: str) -> str:
    """
    Style a direction cell with appropriate background color.

    Args:
        val: Direction value (Bull+, Bull, Neutral, Bear, Bear+)

    Returns:
        CSS style string
    """
    color = DIRECTION_COLORS.get(val, "transparent")
    text_color = "white" if val in ["Bull+", "Bear+", "Bear"] else "black"
    return f"background-color: {color}; color: {text_color}; font-weight: bold;"


def style_tier_cell(val: str) -> str:
    """Style a tier cell."""
    color = TIER_COLORS.get(val, "transparent")
    return f"background-color: {color}; color: black; font-weight: bold;"


def style_rank_cell(val: str) -> str:
    """Style a rank cell."""
    color = RANK_COLORS.get(val, "transparent")
    text_color = "white" if val in ["L5", "L4", "L1"] else "black"
    return f"background-color: {color}; color: {text_color}; font-weight: bold;"


def format_price(val) -> str:
    """Format price values."""
    if pd.isna(val) or val is None:
        return "—"
    return f"${val:,.2f}"


def format_number(val, decimals: int = 2) -> str:
    """Format numeric values."""
    if pd.isna(val) or val is None:
        return "—"
    return f"{val:,.{decimals}f}"


# =========================================================================
# MARKET STRUCTURE TABLE
# =========================================================================

def render_market_structure_table(
    data: List[Dict],
    title: str = "Market Structure"
) -> None:
    """
    Render a market structure table with direction coloring.

    Args:
        data: List of dicts with structure data
        title: Table title
    """
    if not data:
        st.info("No market structure data available")
        return

    st.subheader(title)

    # Build DataFrame
    rows = []
    for item in data:
        row = {
            "Ticker": item.get("ticker", ""),
            "Price": item.get("price", 0),
            "D1 Dir": item.get("d1_direction", "—"),
            "D1 Strong": item.get("d1_strong", None),
            "D1 Weak": item.get("d1_weak", None),
            "H4 Dir": item.get("h4_direction", "—"),
            "H4 Strong": item.get("h4_strong", None),
            "H4 Weak": item.get("h4_weak", None),
            "H1 Dir": item.get("h1_direction", "—"),
            "H1 Strong": item.get("h1_strong", None),
            "H1 Weak": item.get("h1_weak", None),
            "M15 Dir": item.get("m15_direction", "—"),
            "M15 Strong": item.get("m15_strong", None),
            "M15 Weak": item.get("m15_weak", None),
            "Composite": item.get("composite", "—"),
        }
        rows.append(row)

    df = pd.DataFrame(rows)

    # Format price columns
    price_cols = ["Price", "D1 Strong", "D1 Weak", "H4 Strong", "H4 Weak",
                  "H1 Strong", "H1 Weak", "M15 Strong", "M15 Weak"]
    for col in price_cols:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: format_price(x) if x else "—")

    # Apply styling
    direction_cols = ["D1 Dir", "H4 Dir", "H1 Dir", "M15 Dir", "Composite"]

    def style_row(row):
        styles = [""] * len(row)
        for i, col in enumerate(row.index):
            if col in direction_cols:
                styles[i] = style_direction_cell(str(row[col]))
        return styles

    styled = df.style.apply(style_row, axis=1)

    st.dataframe(
        styled,
        use_container_width=True,
        hide_index=True
    )


# =========================================================================
# ZONES TABLE
# =========================================================================

def render_zones_table(
    zones: List,
    title: str = "Zones"
) -> None:
    """
    Render a zones table with tier/rank coloring.

    Args:
        zones: List of FilteredZone or RawZone objects
        title: Table title
    """
    if not zones:
        st.info("No zones available")
        return

    st.subheader(title)

    rows = []
    for zone in zones:
        row = {
            "Zone ID": zone.zone_id,
            "HVN POC": zone.hvn_poc,
            "Zone High": zone.zone_high,
            "Zone Low": zone.zone_low,
            "Score": zone.score,
            "Rank": zone.rank.value if hasattr(zone.rank, 'value') else zone.rank,
            "Confluences": zone.confluences_str if hasattr(zone, 'confluences_str') else ", ".join(zone.confluences),
        }

        # Add filtered zone fields if present
        if hasattr(zone, 'tier'):
            row["Tier"] = zone.tier.value if hasattr(zone.tier, 'value') else zone.tier
        if hasattr(zone, 'is_bull_poc'):
            row["Bull"] = "X" if zone.is_bull_poc else ""
        if hasattr(zone, 'is_bear_poc'):
            row["Bear"] = "X" if zone.is_bear_poc else ""
        if hasattr(zone, 'atr_distance'):
            row["ATR Dist"] = zone.atr_distance

        rows.append(row)

    df = pd.DataFrame(rows)

    # Format price columns
    price_cols = ["HVN POC", "Zone High", "Zone Low"]
    for col in price_cols:
        if col in df.columns:
            df[col] = df[col].apply(format_price)

    # Format score
    if "Score" in df.columns:
        df["Score"] = df["Score"].apply(lambda x: f"{x:.1f}")

    # Format ATR distance
    if "ATR Dist" in df.columns:
        df["ATR Dist"] = df["ATR Dist"].apply(lambda x: f"{x:.2f}" if x else "—")

    # Apply styling
    def style_zones_row(row):
        styles = [""] * len(row)
        for i, col in enumerate(row.index):
            if col == "Rank":
                styles[i] = style_rank_cell(str(row[col]))
            elif col == "Tier":
                styles[i] = style_tier_cell(str(row[col]))
            elif col in ["Bull", "Bear"] and row[col] == "X":
                styles[i] = "background-color: #2962FF; color: white; font-weight: bold;"
        return styles

    styled = df.style.apply(style_zones_row, axis=1)

    st.dataframe(
        styled,
        use_container_width=True,
        hide_index=True
    )


# =========================================================================
# BAR DATA TABLE
# =========================================================================

def render_bar_data_section(
    bar_data,
    section: str
) -> None:
    """
    Render a section of bar data as a table.

    Args:
        bar_data: BarData object
        section: Section name ('monthly', 'weekly', 'daily', 'atr', 'camarilla', 'hvn')
    """
    if section == "monthly":
        _render_ohlc_section(bar_data, "Monthly (M1)", "m1")
    elif section == "weekly":
        _render_ohlc_section(bar_data, "Weekly (W1)", "w1")
    elif section == "daily":
        _render_ohlc_section(bar_data, "Daily (D1)", "d1")
    elif section == "atr":
        _render_atr_section(bar_data)
    elif section == "camarilla":
        _render_camarilla_section(bar_data)
    elif section == "overnight":
        _render_overnight_section(bar_data)


def _render_ohlc_section(bar_data, title: str, prefix: str) -> None:
    """Render OHLC section for a timeframe."""
    current = getattr(bar_data, f"{prefix}_current", None)
    prior = getattr(bar_data, f"{prefix}_prior", None)

    if not current:
        return

    st.markdown(f"**{title}**")

    data = {
        "Period": ["Current", "Prior"],
        "Open": [
            format_price(current.open) if current else "—",
            format_price(prior.open) if prior else "—"
        ],
        "High": [
            format_price(current.high) if current else "—",
            format_price(prior.high) if prior else "—"
        ],
        "Low": [
            format_price(current.low) if current else "—",
            format_price(prior.low) if prior else "—"
        ],
        "Close": [
            format_price(current.close) if current else "—",
            format_price(prior.close) if prior else "—"
        ],
    }

    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)


def _render_atr_section(bar_data) -> None:
    """Render ATR values."""
    st.markdown("**ATR Values**")

    data = {
        "Timeframe": ["M5", "M15", "H1", "D1"],
        "ATR": [
            format_price(bar_data.m5_atr),
            format_price(bar_data.m15_atr),
            format_price(bar_data.h1_atr),
            format_price(bar_data.d1_atr),
        ]
    }

    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)


def _render_camarilla_section(bar_data) -> None:
    """Render Camarilla pivot levels."""
    st.markdown("**Camarilla Pivots**")

    daily = bar_data.camarilla_daily
    weekly = bar_data.camarilla_weekly
    monthly = bar_data.camarilla_monthly

    data = {
        "Level": ["R6", "R4", "R3", "S3", "S4", "S6"],
        "Daily": [
            format_price(daily.r6) if daily else "—",
            format_price(daily.r4) if daily else "—",
            format_price(daily.r3) if daily else "—",
            format_price(daily.s3) if daily else "—",
            format_price(daily.s4) if daily else "—",
            format_price(daily.s6) if daily else "—",
        ],
        "Weekly": [
            format_price(weekly.r6) if weekly else "—",
            format_price(weekly.r4) if weekly else "—",
            format_price(weekly.r3) if weekly else "—",
            format_price(weekly.s3) if weekly else "—",
            format_price(weekly.s4) if weekly else "—",
            format_price(weekly.s6) if weekly else "—",
        ],
        "Monthly": [
            format_price(monthly.r6) if monthly else "—",
            format_price(monthly.r4) if monthly else "—",
            format_price(monthly.r3) if monthly else "—",
            format_price(monthly.s3) if monthly else "—",
            format_price(monthly.s4) if monthly else "—",
            format_price(monthly.s6) if monthly else "—",
        ],
    }

    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)


def _render_overnight_section(bar_data) -> None:
    """Render overnight high/low."""
    st.markdown("**Overnight Session**")

    data = {
        "Level": ["Overnight High", "Overnight Low"],
        "Price": [
            format_price(bar_data.overnight_high),
            format_price(bar_data.overnight_low),
        ]
    }

    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)


# =========================================================================
# HVN POCs TABLE
# =========================================================================

def render_hvn_pocs_table(hvn_result) -> None:
    """
    Render HVN POCs as a table.

    Args:
        hvn_result: HVNResult object
    """
    if not hvn_result or not hvn_result.pocs:
        st.info("No HVN POCs available")
        return

    st.markdown("**HVN POCs (Volume-Ranked)**")

    rows = []
    for poc in sorted(hvn_result.pocs, key=lambda x: x.rank):
        rows.append({
            "Rank": f"POC {poc.rank}",
            "Price": format_price(poc.price),
            "Volume": f"{poc.volume:,.0f}",
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)


# =========================================================================
# MULTI-TICKER BAR DATA TABLE
# =========================================================================

def render_multi_ticker_bar_data(
    results: List[Dict],
    section: str
) -> None:
    """
    Render bar data for multiple tickers in a single table.

    Args:
        results: List of analysis results
        section: Section type ('summary', 'ohlc', 'atr', 'camarilla')
    """
    if not results:
        st.info("No bar data available")
        return

    if section == "summary":
        _render_multi_ticker_summary(results)
    elif section == "ohlc":
        _render_multi_ticker_ohlc(results)
    elif section == "atr":
        _render_multi_ticker_atr(results)
    elif section == "camarilla":
        _render_multi_ticker_camarilla(results)


def _render_multi_ticker_summary(results: List[Dict]) -> None:
    """Render summary table for multiple tickers."""
    rows = []
    for result in results:
        bar_data = result.get("bar_data")
        if not bar_data:
            continue

        rows.append({
            "Ticker": bar_data.ticker,
            "Price": bar_data.price,
            "D1 ATR": bar_data.d1_atr,
            "M15 ATR": bar_data.m15_atr,
            "ON High": bar_data.overnight_high,
            "ON Low": bar_data.overnight_low,
        })

    if not rows:
        st.info("No data")
        return

    df = pd.DataFrame(rows)
    for col in ["Price", "D1 ATR", "M15 ATR", "ON High", "ON Low"]:
        df[col] = df[col].apply(format_price)

    st.dataframe(df, use_container_width=True, hide_index=True)


def _render_multi_ticker_ohlc(results: List[Dict]) -> None:
    """Render OHLC table for multiple tickers."""
    rows = []
    for result in results:
        bar_data = result.get("bar_data")
        if not bar_data:
            continue

        d1_current = bar_data.d1_current
        if d1_current:
            rows.append({
                "Ticker": bar_data.ticker,
                "D1 Open": d1_current.open,
                "D1 High": d1_current.high,
                "D1 Low": d1_current.low,
                "D1 Close": d1_current.close,
            })

    if not rows:
        st.info("No OHLC data")
        return

    df = pd.DataFrame(rows)
    for col in ["D1 Open", "D1 High", "D1 Low", "D1 Close"]:
        df[col] = df[col].apply(format_price)

    st.dataframe(df, use_container_width=True, hide_index=True)


def _render_multi_ticker_atr(results: List[Dict]) -> None:
    """Render ATR table for multiple tickers."""
    rows = []
    for result in results:
        bar_data = result.get("bar_data")
        if not bar_data:
            continue

        rows.append({
            "Ticker": bar_data.ticker,
            "M5 ATR": bar_data.m5_atr,
            "M15 ATR": bar_data.m15_atr,
            "H1 ATR": bar_data.h1_atr,
            "D1 ATR": bar_data.d1_atr,
        })

    if not rows:
        st.info("No ATR data")
        return

    df = pd.DataFrame(rows)
    for col in ["M5 ATR", "M15 ATR", "H1 ATR", "D1 ATR"]:
        df[col] = df[col].apply(format_price)

    st.dataframe(df, use_container_width=True, hide_index=True)


def _render_multi_ticker_camarilla(results: List[Dict]) -> None:
    """Render Camarilla levels table for multiple tickers."""
    rows = []
    for result in results:
        bar_data = result.get("bar_data")
        if not bar_data:
            continue

        daily = bar_data.camarilla_daily
        if daily:
            rows.append({
                "Ticker": bar_data.ticker,
                "D R6": daily.r6,
                "D R4": daily.r4,
                "D R3": daily.r3,
                "D S3": daily.s3,
                "D S4": daily.s4,
                "D S6": daily.s6,
            })

    if not rows:
        st.info("No Camarilla data")
        return

    df = pd.DataFrame(rows)
    for col in ["D R6", "D R4", "D R3", "D S3", "D S4", "D S6"]:
        df[col] = df[col].apply(format_price)

    st.dataframe(df, use_container_width=True, hide_index=True)


# =========================================================================
# MULTI-TICKER ZONES TABLE
# =========================================================================

def render_all_zones_table(
    results: List[Dict],
    zone_type: str = "filtered"
) -> None:
    """
    Render zones from multiple tickers in a single table.

    Args:
        results: List of analysis results
        zone_type: "raw" or "filtered"
    """
    all_zones = []
    for result in results:
        zones_key = "raw_zones" if zone_type == "raw" else "filtered_zones"
        zones = result.get(zones_key, [])
        all_zones.extend(zones)

    if not all_zones:
        st.info(f"No {zone_type} zones available")
        return

    # Sort by score descending
    all_zones.sort(key=lambda z: z.score, reverse=True)

    render_zones_table(all_zones, "")
