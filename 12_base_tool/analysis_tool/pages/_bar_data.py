"""
Bar Data Page - Displays all technical levels for analyzed tickers.

Sections (fixed 13-row tables, page scrolls):
1. Ticker Structure - Price + Strong/Weak levels per timeframe
2. Monthly Metrics (M1) - Current (01-04) + Prior (PO-PC)
3. Weekly Metrics (W1) - Current (01-04) + Prior (PO-PC)
4. Daily Metrics (D1) - Current (01-04) + Prior (PO-PC)
5. Time Based HVN - Anchor date + 10 POCs
6. ON + Options Metrics - Overnight, Options, ATR values
7. Additional Metrics - All Camarilla levels (D1/W1/M1)
"""
import streamlit as st
import pandas as pd
from typing import List, Dict, Any, Optional


# Fixed table height for 13 rows (header + 12 data rows max)
# Height = header (35px) + rows (35px each) + padding
FIXED_TABLE_HEIGHT = 35 + (12 * 35) + 10  # ~465px


def render_bar_data_page(results: Dict[str, Any]) -> None:
    """
    Render the complete Bar Data page.

    Args:
        results: Analysis results containing bar_data for each ticker
    """
    st.header("Bar Data")
    st.markdown("Technical levels and metrics for all analyzed tickers.")

    # Get all successful results with bar_data
    custom_results = results.get("custom", [])
    index_results = results.get("index", [])

    all_results = [
        r for r in (index_results + custom_results)
        if r.get("success") and r.get("bar_data")
    ]

    if not all_results:
        st.warning("No bar data available. Run analysis first.")
        return

    # Section 1: Ticker Structure (Price + Strong/Weak levels)
    st.subheader("Ticker Structure")
    render_ticker_structure(all_results)

    # Section 2: Monthly Metrics (M1)
    st.subheader("Monthly Metrics")
    render_monthly_metrics(all_results)

    # Section 3: Weekly Metrics (W1)
    st.subheader("Weekly Metrics")
    render_weekly_metrics(all_results)

    # Section 4: Daily Metrics (D1)
    st.subheader("Daily Metrics")
    render_daily_metrics(all_results)

    # Section 5: Time Based HVN
    st.subheader("Time Based HVN")
    render_hvn_pocs(all_results)

    # Section 6: ON + Options Metrics
    st.subheader("ON + Options Metrics")
    render_on_options_atr(all_results)

    # Section 7: Additional Metrics (Camarilla)
    st.subheader("Additional Metrics")
    render_camarilla_all(all_results)


def format_price(val: Optional[float]) -> str:
    """Format a price value."""
    if val is None:
        return "—"
    return f"{val:,.2f}"


def format_atr(val: Optional[float]) -> str:
    """Format ATR value (4 decimals for precision)."""
    if val is None:
        return "—"
    return f"{val:.4f}"


def render_fixed_table(df: pd.DataFrame, height: int = FIXED_TABLE_HEIGHT) -> None:
    """
    Render a dataframe with fixed height (no scroll within table).
    The page itself can scroll, but individual tables show all rows.
    """
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        height=height
    )


def render_ticker_structure(results: List[Dict]) -> None:
    """
    Render Ticker Structure table.
    Columns: Ticker, Price, D1_Strong, D1_Weak, H4_Strong, H4_Weak,
             H1_Strong, H1_Weak, M15_Strong, M15_Weak
    """
    rows = []
    for result in results:
        bar_data = result.get("bar_data")
        market_structure = result.get("market_structure")
        if not bar_data:
            continue

        # Get strong/weak from market_structure if available, else from bar_data
        d1_strong = bar_data.d1_strong
        d1_weak = bar_data.d1_weak
        h4_strong = bar_data.h4_strong
        h4_weak = bar_data.h4_weak
        h1_strong = bar_data.h1_strong
        h1_weak = bar_data.h1_weak
        m15_strong = bar_data.m15_strong
        m15_weak = bar_data.m15_weak

        # Fallback to market_structure if bar_data doesn't have values
        if market_structure:
            if d1_strong is None and market_structure.d1.strong is not None:
                d1_strong = market_structure.d1.strong
            if d1_weak is None and market_structure.d1.weak is not None:
                d1_weak = market_structure.d1.weak
            if h4_strong is None and market_structure.h4.strong is not None:
                h4_strong = market_structure.h4.strong
            if h4_weak is None and market_structure.h4.weak is not None:
                h4_weak = market_structure.h4.weak
            if h1_strong is None and market_structure.h1.strong is not None:
                h1_strong = market_structure.h1.strong
            if h1_weak is None and market_structure.h1.weak is not None:
                h1_weak = market_structure.h1.weak
            if m15_strong is None and market_structure.m15.strong is not None:
                m15_strong = market_structure.m15.strong
            if m15_weak is None and market_structure.m15.weak is not None:
                m15_weak = market_structure.m15.weak

        row = {
            "Ticker": bar_data.ticker,
            "Price": format_price(bar_data.price),
            "D1_Strong": format_price(d1_strong),
            "D1_Weak": format_price(d1_weak),
            "H4_Strong": format_price(h4_strong),
            "H4_Weak": format_price(h4_weak),
            "H1_Strong": format_price(h1_strong),
            "H1_Weak": format_price(h1_weak),
            "M15_Strong": format_price(m15_strong),
            "M15_Weak": format_price(m15_weak),
        }
        rows.append(row)

    if not rows:
        st.info("No ticker data available")
        return

    df = pd.DataFrame(rows)
    render_fixed_table(df)


def render_monthly_metrics(results: List[Dict]) -> None:
    """
    Render Monthly Metrics table.
    Columns: Ticker, M1_01, M1_02, M1_03, M1_04, M1_PO, M1_PH, M1_PL, M1_PC
    """
    rows = []
    for result in results:
        bar_data = result.get("bar_data")
        if not bar_data:
            continue

        current = bar_data.m1_current
        prior = bar_data.m1_prior

        row = {
            "Ticker": bar_data.ticker,
            "M1_01": format_price(current.open if current else None),
            "M1_02": format_price(current.high if current else None),
            "M1_03": format_price(current.low if current else None),
            "M1_04": format_price(current.close if current else None),
            "M1_PO": format_price(prior.open if prior else None),
            "M1_PH": format_price(prior.high if prior else None),
            "M1_PL": format_price(prior.low if prior else None),
            "M1_PC": format_price(prior.close if prior else None),
        }
        rows.append(row)

    if not rows:
        st.info("No monthly data available")
        return

    df = pd.DataFrame(rows)
    render_fixed_table(df)


def render_weekly_metrics(results: List[Dict]) -> None:
    """
    Render Weekly Metrics table.
    Columns: Ticker, W1_01, W1_02, W1_03, W1_04, W1_PO, W1_PH, W1_PL, W1_PC
    """
    rows = []
    for result in results:
        bar_data = result.get("bar_data")
        if not bar_data:
            continue

        current = bar_data.w1_current
        prior = bar_data.w1_prior

        row = {
            "Ticker": bar_data.ticker,
            "W1_01": format_price(current.open if current else None),
            "W1_02": format_price(current.high if current else None),
            "W1_03": format_price(current.low if current else None),
            "W1_04": format_price(current.close if current else None),
            "W1_PO": format_price(prior.open if prior else None),
            "W1_PH": format_price(prior.high if prior else None),
            "W1_PL": format_price(prior.low if prior else None),
            "W1_PC": format_price(prior.close if prior else None),
        }
        rows.append(row)

    if not rows:
        st.info("No weekly data available")
        return

    df = pd.DataFrame(rows)
    render_fixed_table(df)


def render_daily_metrics(results: List[Dict]) -> None:
    """
    Render Daily Metrics table.
    Columns: Ticker, D1_01, D1_02, D1_03, D1_04, D1_PO, D1_PH, D1_PL, D1_PC
    """
    rows = []
    for result in results:
        bar_data = result.get("bar_data")
        if not bar_data:
            continue

        current = bar_data.d1_current
        prior = bar_data.d1_prior

        row = {
            "Ticker": bar_data.ticker,
            "D1_01": format_price(current.open if current else None),
            "D1_02": format_price(current.high if current else None),
            "D1_03": format_price(current.low if current else None),
            "D1_04": format_price(current.close if current else None),
            "D1_PO": format_price(prior.open if prior else None),
            "D1_PH": format_price(prior.high if prior else None),
            "D1_PL": format_price(prior.low if prior else None),
            "D1_PC": format_price(prior.close if prior else None),
        }
        rows.append(row)

    if not rows:
        st.info("No daily data available")
        return

    df = pd.DataFrame(rows)
    render_fixed_table(df)


def render_hvn_pocs(results: List[Dict]) -> None:
    """
    Render Time Based HVN table.
    Columns: Ticker, Anchor_Date, HVN POC1-10
    """
    rows = []
    for result in results:
        hvn_result = result.get("hvn_result")
        bar_data = result.get("bar_data")

        if not bar_data:
            continue

        anchor_date = result.get("anchor_date", "—")

        row = {
            "Ticker": bar_data.ticker,
            "Anchor_Date": anchor_date,
        }

        # Add POCs
        if hvn_result:
            pocs_dict = hvn_result.to_dict()
            for i in range(1, 11):
                poc_price = pocs_dict.get(f"hvn_poc{i}")
                row[f"HVN POC{i}"] = format_price(poc_price)
        else:
            for i in range(1, 11):
                row[f"HVN POC{i}"] = "—"

        rows.append(row)

    if not rows:
        st.info("No HVN POC data available")
        return

    df = pd.DataFrame(rows)
    render_fixed_table(df)


def render_on_options_atr(results: List[Dict]) -> None:
    """
    Render ON + Options Metrics table.
    Columns: Ticker, D1_ONH, D1_ONL, OP_01-10, M5_ATR, M15_ATR, H1_ATR, D1_ATR
    """
    rows = []
    for result in results:
        bar_data = result.get("bar_data")
        if not bar_data:
            continue

        row = {
            "Ticker": bar_data.ticker,
            "D1_ONH": format_price(bar_data.overnight_high),
            "D1_ONL": format_price(bar_data.overnight_low),
        }

        # Add options levels (OP_01 through OP_10)
        options = bar_data.options_levels if bar_data.options_levels else []
        for i in range(1, 11):
            if i <= len(options):
                row[f"OP_{i:02d}"] = format_price(options[i-1])
            else:
                row[f"OP_{i:02d}"] = "—"

        # Add ATR values
        row["M5_ATR"] = format_atr(bar_data.m5_atr)
        row["M15_ATR"] = format_atr(bar_data.m15_atr)
        row["H1_ATR"] = format_atr(bar_data.h1_atr)
        row["D1_ATR"] = format_atr(bar_data.d1_atr)

        rows.append(row)

    if not rows:
        st.info("No ON/Options/ATR data available")
        return

    df = pd.DataFrame(rows)
    render_fixed_table(df)


def render_camarilla_all(results: List[Dict]) -> None:
    """
    Render Additional Metrics table (all Camarilla levels).
    Columns: Ticker, D1_S6, D1_S4, D1_S3, D1_R3, D1_R4, D1_R6,
             W1_S6, W1_S4, W1_S3, W1_R3, W1_R4, W1_R6,
             M1_S6, M1_S4, M1_S3, M1_R3, M1_R4, M1_R6
    """
    rows = []
    for result in results:
        bar_data = result.get("bar_data")
        if not bar_data:
            continue

        cam_d = bar_data.camarilla_daily
        cam_w = bar_data.camarilla_weekly
        cam_m = bar_data.camarilla_monthly

        row = {
            "Ticker": bar_data.ticker,
            # Daily Camarilla
            "D1_S6": format_price(cam_d.s6 if cam_d else None),
            "D1_S4": format_price(cam_d.s4 if cam_d else None),
            "D1_S3": format_price(cam_d.s3 if cam_d else None),
            "D1_R3": format_price(cam_d.r3 if cam_d else None),
            "D1_R4": format_price(cam_d.r4 if cam_d else None),
            "D1_R6": format_price(cam_d.r6 if cam_d else None),
            # Weekly Camarilla
            "W1_S6": format_price(cam_w.s6 if cam_w else None),
            "W1_S4": format_price(cam_w.s4 if cam_w else None),
            "W1_S3": format_price(cam_w.s3 if cam_w else None),
            "W1_R3": format_price(cam_w.r3 if cam_w else None),
            "W1_R4": format_price(cam_w.r4 if cam_w else None),
            "W1_R6": format_price(cam_w.r6 if cam_w else None),
            # Monthly Camarilla
            "M1_S6": format_price(cam_m.s6 if cam_m else None),
            "M1_S4": format_price(cam_m.s4 if cam_m else None),
            "M1_S3": format_price(cam_m.s3 if cam_m else None),
            "M1_R3": format_price(cam_m.r3 if cam_m else None),
            "M1_R4": format_price(cam_m.r4 if cam_m else None),
            "M1_R6": format_price(cam_m.r6 if cam_m else None),
        }
        rows.append(row)

    if not rows:
        st.info("No Camarilla data available")
        return

    df = pd.DataFrame(rows)
    render_fixed_table(df)


# Standalone page entry point (for Streamlit multipage)
if __name__ == "__main__":
    st.set_page_config(page_title="Bar Data", layout="wide")

    from core.state_manager import get_state

    results = get_state("analysis_results")
    if results:
        render_bar_data_page(results)
    else:
        st.warning("No analysis results available. Please run analysis from the main page first.")
