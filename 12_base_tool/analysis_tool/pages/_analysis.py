"""
Analysis Page - Primary and Secondary Trading Setups.

Replicates the Analysis sheet from Excel with:
- Primary Setups Section (B31:L40 equivalent)
- Secondary Setups Section (N31:X40 equivalent)
- Setup Strings Section (B44:C53 equivalent)

Shows trading setups with targets and R:R ratios.
"""
import streamlit as st
import pandas as pd
from typing import Dict, List, Optional

from core import Setup, Direction, Tier, generate_pinescript_6, generate_pinescript_16


def render_analysis_page(results: Dict):
    """
    Render the Analysis page with Primary/Secondary setups.

    Args:
        results: Pipeline results dict with 'custom' key containing ticker results
    """
    st.header("Analysis - Trading Setups")

    custom_results = results.get("custom", [])

    if not custom_results:
        st.info("Run analysis to see trading setups.")
        return

    # Collect all primary and secondary setups
    primary_setups: List[Setup] = []
    secondary_setups: List[Setup] = []

    for result in custom_results:
        if not result.get("success"):
            continue

        primary = result.get("primary_setup")
        secondary = result.get("secondary_setup")

        if primary:
            primary_setups.append(primary)
        if secondary:
            secondary_setups.append(secondary)

    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["Primary Setups", "Secondary Setups", "TradingView Export"])

    with tab1:
        render_setup_table(primary_setups, "Primary", "With-trend setups based on composite direction")

    with tab2:
        render_setup_table(secondary_setups, "Secondary", "Counter-trend setups (opposite direction)")

    with tab3:
        render_setup_strings(primary_setups, secondary_setups, results)


def render_setup_table(setups: List[Setup], title: str, description: str):
    """
    Render a setup table with R:R color coding.

    Args:
        setups: List of Setup objects
        title: Section title
        description: Section description
    """
    st.subheader(f"{title} Setups")
    st.caption(description)

    if not setups:
        st.info(f"No {title.lower()} setups found.")
        return

    # Convert to DataFrame for display
    df = pd.DataFrame([
        {
            "Ticker": s.ticker,
            "Direction": s.direction.value,
            "Ticker ID": s.ticker_id,
            "Zone ID": s.zone_id,
            "HVN POC": f"${s.hvn_poc:.2f}",
            "Zone High": f"${s.zone_high:.2f}",
            "Zone Low": f"${s.zone_low:.2f}",
            "Tier": s.tier.value,
            "Target ID": s.target_id or "N/A",
            "Target": f"${s.target:.2f}" if s.target else "N/A",
            "R:R": f"{s.risk_reward:.2f}" if s.risk_reward else "N/A",
            "_rr_value": s.risk_reward or 0,  # Hidden column for sorting/styling
            "_direction": s.direction.value,
        }
        for s in setups
    ])

    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Setups", len(setups))
    with col2:
        t3_count = sum(1 for s in setups if s.tier == Tier.T3)
        st.metric("T3 (High Quality)", t3_count)
    with col3:
        high_rr = sum(1 for s in setups if s.risk_reward and s.risk_reward >= 4.0)
        st.metric("4R+ Setups", high_rr)
    with col4:
        avg_rr = sum(s.risk_reward for s in setups if s.risk_reward) / len(setups) if setups else 0
        st.metric("Avg R:R", f"{avg_rr:.2f}")

    # Style the dataframe
    display_df = df.drop(columns=["_rr_value", "_direction"])

    # Apply styling
    styled_df = display_df.style.apply(
        lambda row: style_setup_row(row, df.loc[row.name, "_rr_value"], df.loc[row.name, "_direction"]),
        axis=1
    )

    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True
    )


def style_setup_row(row, rr_value: float, direction: str) -> List[str]:
    """
    Apply styling to a setup row based on R:R and direction.

    Args:
        row: DataFrame row
        rr_value: R:R value for this row
        direction: Direction string (Bull/Bear)

    Returns:
        List of CSS styles for each column
    """
    styles = [""] * len(row)

    # Direction column styling
    dir_idx = list(row.index).index("Direction") if "Direction" in row.index else -1
    if dir_idx >= 0:
        if direction in ["Bull", "Bull+"]:
            styles[dir_idx] = "color: #00C853; font-weight: bold"
        elif direction in ["Bear", "Bear+"]:
            styles[dir_idx] = "color: #FF5252; font-weight: bold"

    # Tier column styling
    tier_idx = list(row.index).index("Tier") if "Tier" in row.index else -1
    if tier_idx >= 0:
        tier = row["Tier"]
        if tier == "T3":
            styles[tier_idx] = "background-color: #1B5E20; color: white; font-weight: bold"
        elif tier == "T2":
            styles[tier_idx] = "background-color: #E65100; color: white; font-weight: bold"
        elif tier == "T1":
            styles[tier_idx] = "background-color: #F9A825; color: black; font-weight: bold"

    # R:R column styling (gradient based on value)
    rr_idx = list(row.index).index("R:R") if "R:R" in row.index else -1
    if rr_idx >= 0:
        if rr_value >= 5.0:
            styles[rr_idx] = "background-color: #1B5E20; color: white; font-weight: bold"
        elif rr_value >= 4.0:
            styles[rr_idx] = "background-color: #2E7D32; color: white; font-weight: bold"
        elif rr_value >= 3.0:
            styles[rr_idx] = "background-color: #43A047; color: white"
        elif rr_value >= 2.0:
            styles[rr_idx] = "background-color: #66BB6A; color: white"

    return styles


def render_setup_strings(primary_setups: List[Setup], secondary_setups: List[Setup], results: Dict = None):
    """
    Render setup strings section for TradingView export.

    Matches Excel summary_exporter.py format:
    - Table with Ticker, Ticker_ID, Date, Top_Zone data, Epoch POCs, PineScript strings

    Args:
        primary_setups: List of primary Setup objects
        secondary_setups: List of secondary Setup objects
        results: Full pipeline results for accessing HVN POCs and zone data
    """
    from datetime import datetime

    st.subheader("TradingView Export")
    st.caption("Export data for TradingView Pine Script indicators")

    if not results:
        st.warning("No results available for export")
        return

    custom_results = results.get("custom", [])
    if not custom_results:
        st.info("No ticker data to export")
        return

    # Build export table matching Excel format
    export_rows = []
    export_time = datetime.now().strftime('%m/%d/%Y %H:%M')

    for result in custom_results:
        if not result.get("success"):
            continue

        ticker = result.get("ticker", "")
        bar_data = result.get("bar_data")
        hvn_result = result.get("hvn_result")
        filtered_zones = result.get("filtered_zones", [])
        primary = result.get("primary_setup")
        secondary = result.get("secondary_setup")

        if not bar_data:
            continue

        # Get ticker_id and date
        ticker_id = bar_data.ticker_id if bar_data else f"{ticker}_{datetime.now().strftime('%m%d%y')}"
        analysis_date = bar_data.analysis_date.strftime('%m/%d/%Y') if bar_data and bar_data.analysis_date else ""

        # Top zone data (first/highest scoring filtered zone)
        top_zone_id = ""
        top_zone_poc = 0.0
        top_zone_rank = ""
        top_zone_score = 0.0
        if filtered_zones:
            top_zone = filtered_zones[0]  # Already sorted by score
            top_zone_id = top_zone.zone_id.replace(f"{ticker}_", "") if top_zone.zone_id else ""
            top_zone_poc = top_zone.hvn_poc
            top_zone_rank = top_zone.rank.value if hasattr(top_zone.rank, 'value') else str(top_zone.rank)
            top_zone_score = top_zone.score

        # Epoch start date (anchor date from HVN calculation)
        epoch_start = hvn_result.start_date.strftime('%m/%d/%Y') if hvn_result and hvn_result.start_date else ""

        # Get 10 POCs from HVN result
        pocs = [0.0] * 10
        if hvn_result:
            poc_prices = hvn_result.get_poc_prices()
            for i, price in enumerate(poc_prices[:10]):
                pocs[i] = price

        # Build PineScript strings using helper functions
        pinescript_6 = generate_pinescript_6(primary, secondary)
        pinescript_16 = generate_pinescript_16(primary, secondary, pocs)

        export_rows.append({
            "Ticker": ticker,
            "Ticker_ID": ticker_id,
            "Date": analysis_date,
            "Top_Zone_ID": top_zone_id,
            "Top_Zone_POC": top_zone_poc,
            "Top_Zone_Rank": top_zone_rank,
            "Top_Zone_Score": top_zone_score,
            "Epoch_Start": epoch_start,
            "POC1": pocs[0], "POC2": pocs[1], "POC3": pocs[2], "POC4": pocs[3], "POC5": pocs[4],
            "POC6": pocs[5], "POC7": pocs[6], "POC8": pocs[7], "POC9": pocs[8], "POC10": pocs[9],
            "PineScript_6": pinescript_6,
            "PineScript_16": pinescript_16,
            "Epoch_Time": export_time
        })

    if not export_rows:
        st.info("No data to export")
        return

    # Create DataFrame and display
    df = pd.DataFrame(export_rows)

    # Format price columns
    price_cols = ["Top_Zone_POC", "POC1", "POC2", "POC3", "POC4", "POC5",
                  "POC6", "POC7", "POC8", "POC9", "POC10"]
    for col in price_cols:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: f"{x:.2f}" if x != 0 else "")

    df["Top_Zone_Score"] = df["Top_Zone_Score"].apply(lambda x: f"{x:.2f}" if x != 0 else "")

    # Display table
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Export buttons
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        # CSV download
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv_data,
            file_name=f"epoch_export_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )

    with col2:
        # PineScript 6-value strings only
        pine6_strings = "\n".join([row["PineScript_6"] for row in export_rows])
        st.download_button(
            label="Download PineScript_6",
            data=pine6_strings,
            file_name="pinescript_6.txt",
            mime="text/plain"
        )

    with col3:
        # PineScript 16-value strings only
        pine16_strings = "\n".join([row["PineScript_16"] for row in export_rows])
        st.download_button(
            label="Download PineScript_16",
            data=pine16_strings,
            file_name="pinescript_16.txt",
            mime="text/plain"
        )

    # Show PineScript strings in expandable section
    with st.expander("View PineScript Strings"):
        st.write("**PineScript_6 Format:** `pri_high,pri_low,pri_target,sec_high,sec_low,sec_target`")
        for row in export_rows:
            st.code(f"{row['Ticker']}: {row['PineScript_6']}", language="text")

        st.write("**PineScript_16 Format:** `pine_6 + POC1-POC10`")
        for row in export_rows:
            st.code(f"{row['Ticker']}: {row['PineScript_16']}", language="text")


def render_setup_summary(results: Dict):
    """
    Render a compact setup summary for the Summary tab.

    Args:
        results: Pipeline results dict
    """
    custom_results = results.get("custom", [])

    if not custom_results:
        return

    # Collect all setups
    setups_data = []

    for result in custom_results:
        if not result.get("success"):
            continue

        ticker = result.get("ticker")
        direction = result.get("direction", "N/A")

        primary = result.get("primary_setup")
        secondary = result.get("secondary_setup")

        setups_data.append({
            "Ticker": ticker,
            "Direction": direction,
            "Primary POC": f"${primary.hvn_poc:.2f}" if primary else "N/A",
            "Primary Target": f"${primary.target:.2f}" if primary and primary.target else "N/A",
            "Primary R:R": f"{primary.risk_reward:.2f}" if primary and primary.risk_reward else "N/A",
            "Secondary POC": f"${secondary.hvn_poc:.2f}" if secondary else "N/A",
            "Secondary Target": f"${secondary.target:.2f}" if secondary and secondary.target else "N/A",
            "Secondary R:R": f"{secondary.risk_reward:.2f}" if secondary and secondary.risk_reward else "N/A",
        })

    if setups_data:
        df = pd.DataFrame(setups_data)
        st.dataframe(df, use_container_width=True, hide_index=True)


# =========================================================================
# STANDALONE PAGE (for multi-page Streamlit app)
# =========================================================================

def main():
    """Standalone page entry point."""
    st.set_page_config(page_title="Analysis", page_icon="📊", layout="wide")

    # Check for results in session state
    results = st.session_state.get("results", {})

    if not results:
        st.warning("No analysis results found. Run analysis from the main page first.")
        return

    render_analysis_page(results)


if __name__ == "__main__":
    main()
