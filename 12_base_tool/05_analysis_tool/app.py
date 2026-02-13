"""
Epoch Analysis Tool - Streamlit Application
Main entry point for the analysis tool.

Replaces Excel UI with a web-based interface.
"""
import logging
import streamlit as st
from datetime import date, timedelta

# Suppress noisy warnings from data fetching (e.g., "No daily data for X" on weekends)
logging.getLogger("data.polygon_client").setLevel(logging.ERROR)
logging.getLogger("calculators.bar_data").setLevel(logging.ERROR)
logging.getLogger("calculators.hvn_identifier").setLevel(logging.WARNING)
logging.getLogger("calculators.scanner").setLevel(logging.WARNING)

# Must be the first Streamlit command
st.set_page_config(
    page_title="Epoch Analysis Tool",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Now import other modules
from core.state_manager import (
    init_session_state, get_state, set_state,
    ANCHOR_PRESETS
)
from components.ticker_input import render_ticker_input
from pages._pre_market_report import render_pre_market_report


def inject_custom_css():
    """Inject custom CSS for improved responsiveness and styling."""
    st.markdown("""
    <style>
    /* Mobile-responsive adjustments */
    @media (max-width: 768px) {
        /* Reduce sidebar width on mobile */
        section[data-testid="stSidebar"] {
            width: 280px !important;
        }

        /* Stack columns on mobile */
        .stColumn {
            width: 100% !important;
            flex: 1 1 100% !important;
        }

        /* Reduce padding on mobile */
        .main .block-container {
            padding: 1rem !important;
        }

        /* Smaller headers on mobile */
        h1 { font-size: 1.5rem !important; }
        h2 { font-size: 1.3rem !important; }
        h3 { font-size: 1.1rem !important; }
    }

    /* Better table scrolling */
    .stDataFrame {
        overflow-x: auto;
    }

    /* Metric cards styling */
    [data-testid="stMetric"] {
        background-color: #1a1a1a;
        border-radius: 8px;
        padding: 12px;
        border: 1px solid #333;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
    }

    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        border-radius: 4px 4px 0 0;
    }

    /* Progress bar enhancement */
    .stProgress > div > div {
        background-color: #2962FF;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        font-weight: 600;
        color: #B2B5BE;
    }

    /* Error message styling */
    .stAlert {
        border-radius: 8px;
    }

    /* Button improvements */
    .stButton > button {
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    }

    /* Hide Streamlit branding in footer */
    footer {
        visibility: hidden;
    }
    </style>
    """, unsafe_allow_html=True)


def main():
    """Main application entry point."""
    # Initialize session state
    init_session_state()

    # Inject custom CSS for styling
    inject_custom_css()

    # Header
    st.title("Epoch Analysis Tool")
    st.markdown("---")

    # Top-level mode selection
    mode = st.radio(
        "Mode",
        options=["Analysis", "Scanner"],
        horizontal=True,
        key="app_mode"
    )

    if mode == "Scanner":
        # Render scanner page
        from pages._scanner import render_scanner_page

        # Show navigation in sidebar (always visible)
        with st.sidebar:
            st.markdown("---")
            st.subheader("Analysis Pages")

            page_options = [
                "Dashboard",
                "Pre-Market Report",
                "Market Overview",
                "Bar Data",
                "Raw Zones",
                "Zone Results",
                "Analysis",
                "Summary"
            ]

            current_page = get_state("selected_page", "Dashboard")
            if current_page not in page_options:
                current_page = "Dashboard"
                set_state("selected_page", current_page)

            selected_page = st.radio(
                "Select Page",
                options=page_options,
                index=page_options.index(current_page),
                key="scanner_page_selector",
                label_visibility="collapsed"
            )
            set_state("selected_page", selected_page)

            # Show results status and Go to Analysis button
            has_results = get_state("analysis_results") or get_state("batch_results")
            if has_results:
                st.success("Results available")
            else:
                st.info("No results yet")

            if st.button("Go to Analysis", type="primary", use_container_width=True):
                st.session_state.app_mode = "Analysis"
                st.rerun()

        render_scanner_page()
        return

    # Analysis mode continues below

    # Check if scanner sent tickers to analysis
    if "scanner_to_analysis" in st.session_state and st.session_state.scanner_to_analysis:
        scanner_tickers = st.session_state.scanner_to_analysis
        st.info(f"Tickers from scanner: {', '.join(scanner_tickers)}")
        if st.button("Clear scanner tickers"):
            st.session_state.scanner_to_analysis = []
            st.rerun()

    # Sidebar - Ticker Input and Navigation
    with st.sidebar:
        st.header("Analysis Configuration")

        # If scanner tickers are available, show option to use them
        if "scanner_to_analysis" in st.session_state and st.session_state.scanner_to_analysis:
            st.success(f"{len(st.session_state.scanner_to_analysis)} tickers from scanner")
            use_scanner = st.checkbox("Use scanner tickers", value=True)
        else:
            use_scanner = False

        # Render ticker input form (10 rows with individual anchor dates)
        ticker_inputs = render_ticker_input(
            prefill_tickers=st.session_state.get("scanner_to_analysis", []) if use_scanner else None
        )

        st.markdown("---")

        # Batch Analysis Mode toggle
        batch_mode = st.checkbox(
            "Batch Analysis Mode",
            value=False,
            help="Run analysis for multiple anchor dates"
        )

        if batch_mode:
            st.markdown("**Select Anchor Dates to Analyze:**")
            selected_anchors = st.multiselect(
                "Anchor Presets",
                options=ANCHOR_PRESETS,
                default=["Prior Day", "Prior Week", "Prior Month"],
                label_visibility="collapsed"
            )
            set_state("batch_anchors", selected_anchors)
        else:
            set_state("batch_anchors", None)

        st.markdown("---")

        # Market Time Mode toggle (Pre-Market / Post-Market / Live)
        st.markdown("**Data Cutoff Time**")
        st.radio(
            "Market Time Mode",
            options=["Live", "Pre-Market", "Post-Market"],
            index=0,
            horizontal=True,
            key="market_time_mode",
            label_visibility="collapsed",
            help="Live: Current time | Pre-Market: 09:00 ET | Post-Market: 16:00 ET"
        )
        # Note: No set_state needed - Streamlit auto-manages key="market_time_mode"

        st.markdown("---")

        # Cache Management
        st.markdown("**Cache Management**")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Clear Cache", use_container_width=True, help="Clear all cached data"):
                from core.state_manager import clear_all_caches, get_cache_stats
                counts = clear_all_caches()
                st.success(f"Cleared {counts['file_cache']} files, {counts['session_state']} session items")
                st.rerun()
        with col2:
            if st.button("Cache Stats", use_container_width=True, help="Show cache statistics"):
                from core.state_manager import get_cache_stats
                stats = get_cache_stats()
                st.info(f"Files: {stats['file_count']} | Size: {stats['total_size_mb']} MB")

        st.markdown("---")

        # Run Analysis button
        has_tickers = any(t.get("ticker") for t in ticker_inputs)
        has_batch_anchors = batch_mode and get_state("batch_anchors")

        run_clicked = st.button(
            "Run Batch Analysis" if batch_mode else "Run Analysis",
            type="primary",
            use_container_width=True,
            disabled=not has_tickers or (batch_mode and not has_batch_anchors)
        )

        if run_clicked:
            set_state("run_requested", True)
            set_state("batch_mode", batch_mode)
            set_state("ticker_inputs", ticker_inputs)
            # Clear scanner tickers after using them
            if use_scanner:
                st.session_state.scanner_to_analysis = []

        # Page Navigation (always visible)
        st.markdown("---")
        st.subheader("Navigate")

        page_options = [
            "Dashboard",
            "Pre-Market Report",
            "Market Overview",
            "Bar Data",
            "Raw Zones",
            "Zone Results",
            "Analysis",
            "Summary"
        ]

        # Get current selection, default to Dashboard if invalid
        current_page = get_state("selected_page", "Dashboard")
        if current_page not in page_options:
            current_page = "Dashboard"
            set_state("selected_page", current_page)

        selected_page = st.radio(
            "Select Page",
            options=page_options,
            index=page_options.index(current_page),
            key="page_selector",
            label_visibility="collapsed"
        )
        set_state("selected_page", selected_page)

        # Show results status indicator
        has_results = get_state("analysis_results") or get_state("batch_results")
        if has_results:
            st.success("Results available")
        else:
            st.info("No results yet")

    # Main content area
    if get_state("run_requested"):
        # Run pipeline (progress is shown in terminal)
        run_analysis_pipeline()
    else:
        # Show selected page content
        render_selected_page()


def render_welcome_screen():
    """Display welcome/instructions when no analysis is running."""
    st.markdown("""
    ### Getting Started

    1. **Enter Tickers** - Add up to 10 tickers in the sidebar (one per line)
    2. **Set Anchor Dates** - Each ticker has its own custom anchor date for HVN calculation
    3. **Click Run Analysis** - The pipeline will process all tickers

    ---

    ### Index Tickers (Automatic)

    **SPY, QQQ, DIA** are automatically analyzed with a **Prior Month** anchor date
    for market structure context.

    ---

    ### Pipeline Stages

    | Stage | Description |
    |-------|-------------|
    | 1. Bar Data | OHLC, ATR, Camarilla pivots |
    | 2. HVN Identifier | 10 volume-ranked POCs per ticker |
    | 3. Zone Calculator | Confluence zones with scoring |
    | 4. Zone Filter | Filter, tier, and identify setups |

    """)

    # Show cached data stats if available
    from data.cache_manager import CacheManager
    cache = CacheManager()
    cache_stats = cache.get_cache_stats()

    if cache_stats.get("file_count", 0) > 0:
        st.markdown("---")
        st.markdown("### Cache Status")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Cached Files", cache_stats.get("file_count", 0))
        with col2:
            st.metric("Cache Size", f"{cache_stats.get('total_size_mb', 0):.1f} MB")


def run_analysis_pipeline():
    """Execute the full analysis pipeline (single or batch mode)."""
    from core.pipeline_runner import PipelineRunner

    ticker_inputs = get_state("ticker_inputs", [])
    batch_mode = get_state("batch_mode", False)
    batch_anchors = get_state("batch_anchors", [])

    # Get list of tickers
    tickers = [
        t.get("ticker") for t in ticker_inputs
        if t.get("ticker")
    ]

    if not tickers:
        st.warning("No valid tickers. Please enter at least one ticker.")
        set_state("run_requested", False)
        return

    # Run pipeline with loading spinners
    runner = PipelineRunner()

    try:
        if batch_mode and batch_anchors:
            # Batch mode: run for multiple anchor dates
            with st.spinner(f"Running batch analysis for {len(batch_anchors)} anchor presets..."):
                results = runner.run_batch(
                    tickers=tickers,
                    anchor_presets=batch_anchors
                )
            set_state("batch_results", results)
            set_state("analysis_results", None)
            set_state("run_requested", False)

            # Rerun to update sidebar navigation
            st.rerun()

        else:
            # Single mode: use individual anchor dates from ticker inputs
            valid_inputs = [
                t for t in ticker_inputs
                if t.get("ticker") and t.get("anchor_date")
            ]

            if not valid_inputs:
                st.warning("No valid ticker inputs. Please enter at least one ticker with an anchor date.")
                set_state("run_requested", False)
                return

            with st.spinner(f"Analyzing {len(valid_inputs)} ticker(s)..."):
                results = runner.run(valid_inputs)
            set_state("analysis_results", results)
            set_state("batch_results", None)
            set_state("run_requested", False)

            # Rerun to update sidebar navigation
            st.rerun()

    except ConnectionError as e:
        st.error(f"**Network Error:** Unable to connect to Polygon API. Check your internet connection.\n\nDetails: {str(e)}")
        set_state("run_requested", False)
    except ValueError as e:
        st.error(f"**Data Error:** {str(e)}\n\nTry checking the ticker symbol or date range.")
        set_state("run_requested", False)
    except Exception as e:
        st.error(f"**Pipeline Error:** {str(e)}\n\nIf this persists, try clearing the cache and running again.")
        with st.expander("Technical Details"):
            import traceback
            st.code(traceback.format_exc())
        set_state("run_requested", False)


def render_dashboard(results):
    """
    Render the main dashboard showing pipeline run summary and metrics.
    This provides a complete overview that the analysis ran successfully.
    """
    import pandas as pd
    from datetime import datetime

    st.header("Analysis Dashboard")
    st.caption(f"Pipeline completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Get results
    custom_results = results.get("custom", [])
    index_results = results.get("index", [])

    successful_custom = [r for r in custom_results if r.get("success")]
    successful_index = [r for r in index_results if r.get("success")]
    failed = [r for r in (custom_results + index_results) if not r.get("success")]

    # =========================================================================
    # TOP METRICS ROW
    # =========================================================================
    st.markdown("### Pipeline Summary")
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Total Tickers", len(custom_results) + len(index_results))
    with col2:
        st.metric("Successful", len(successful_custom) + len(successful_index), delta=None)
    with col3:
        st.metric("Failed", len(failed), delta=None, delta_color="inverse" if failed else "off")
    with col4:
        total_zones = sum(r.get("zones_count", 0) for r in successful_custom)
        st.metric("Total Zones", total_zones)
    with col5:
        setups_count = sum(1 for r in successful_custom if r.get("primary_setup") or r.get("secondary_setup"))
        st.metric("Setups Found", setups_count)

    # =========================================================================
    # EXPORT TO SUPABASE SECTION
    # =========================================================================
    st.markdown("---")
    st.markdown("### Export to Supabase")
    st.caption("Export zones and setups for backtesting")

    col_export1, col_export2, col_export3 = st.columns([1, 2, 2])

    with col_export1:
        export_clicked = st.button(
            "Export to Supabase",
            type="primary",
            use_container_width=True,
            disabled=(len(successful_custom) == 0),
            help="Export filtered zones and setups to Supabase for backtesting"
        )

    with col_export2:
        # Show export status
        if "export_stats" in st.session_state and st.session_state.export_stats:
            stats = st.session_state.export_stats
            if stats.success:
                st.success(f"Exported: {stats.zones_exported} zones, {stats.setups_exported} setups")
            else:
                st.error(f"Export failed: {', '.join(stats.errors)}")

    with col_export3:
        if "export_stats" in st.session_state and st.session_state.export_stats:
            stats = st.session_state.export_stats
            st.caption(f"Tickers: {stats.tickers_processed} | Total records: {stats.total_records}")

    if export_clicked:
        with st.spinner("Exporting to Supabase..."):
            from data.supabase_exporter import export_to_supabase
            export_stats = export_to_supabase(results)
            st.session_state.export_stats = export_stats
            st.rerun()

    st.markdown("---")

    # =========================================================================
    # TICKER STATUS TABLE
    # =========================================================================
    st.markdown("### Ticker Analysis Status")

    all_results = index_results + custom_results
    status_rows = []

    for result in all_results:
        ticker = result.get("ticker", "Unknown")
        success = result.get("success", False)
        is_index = result in index_results

        # Get metrics
        bar_data = result.get("bar_data")
        hvn_result = result.get("hvn_result")
        raw_zones = result.get("raw_zones", [])
        filtered_zones = result.get("filtered_zones", [])
        primary_setup = result.get("primary_setup")
        secondary_setup = result.get("secondary_setup")
        market_structure = result.get("market_structure")

        row = {
            "Ticker": ticker,
            "Type": "Index" if is_index else "Custom",
            "Status": "✓ Success" if success else "✗ Failed",
            "Price": f"${bar_data.price:.2f}" if bar_data else "—",
            "Direction": market_structure.composite.value if market_structure and market_structure.composite else "—",
            "Raw Zones": len(raw_zones) if raw_zones else 0,
            "Filtered Zones": len(filtered_zones) if filtered_zones else 0,
            "POCs": hvn_result.poc_count if hvn_result and hasattr(hvn_result, 'poc_count') else (10 if hvn_result else 0),
            "Primary Setup": "✓" if primary_setup and primary_setup.hvn_poc > 0 else "—",
            "Secondary Setup": "✓" if secondary_setup and secondary_setup.hvn_poc > 0 else "—",
        }
        status_rows.append(row)

    if status_rows:
        df_status = pd.DataFrame(status_rows)

        # Style the status column
        def style_status(val):
            if "Success" in str(val):
                return "color: #00C853; font-weight: bold;"
            elif "Failed" in str(val):
                return "color: #FF5252; font-weight: bold;"
            return ""

        def style_setup(val):
            if val == "✓":
                return "color: #2962FF; font-weight: bold;"
            return "color: #666;"

        styled_df = df_status.style.applymap(style_status, subset=["Status"])
        styled_df = styled_df.applymap(style_setup, subset=["Primary Setup", "Secondary Setup"])

        st.dataframe(styled_df, use_container_width=True, hide_index=True, height=min(400, 50 + len(status_rows) * 35))

    st.markdown("---")

    # =========================================================================
    # ZONE METRICS BY TICKER
    # =========================================================================
    st.markdown("### Zone Analysis Breakdown")

    zone_rows = []
    for result in successful_custom + successful_index:
        ticker = result.get("ticker", "Unknown")
        raw_zones = result.get("raw_zones", [])
        filtered_zones = result.get("filtered_zones", [])

        # Count by rank
        l5_count = sum(1 for z in raw_zones if (z.rank.value if hasattr(z.rank, 'value') else z.rank) == "L5")
        l4_count = sum(1 for z in raw_zones if (z.rank.value if hasattr(z.rank, 'value') else z.rank) == "L4")
        l3_count = sum(1 for z in raw_zones if (z.rank.value if hasattr(z.rank, 'value') else z.rank) == "L3")

        # Count by tier
        t3_count = sum(1 for z in filtered_zones if (z.tier.value if hasattr(z.tier, 'value') else z.tier) == "T3")
        t2_count = sum(1 for z in filtered_zones if (z.tier.value if hasattr(z.tier, 'value') else z.tier) == "T2")
        t1_count = sum(1 for z in filtered_zones if (z.tier.value if hasattr(z.tier, 'value') else z.tier) == "T1")

        # Bull/Bear POCs
        bull_count = sum(1 for z in filtered_zones if z.is_bull_poc)
        bear_count = sum(1 for z in filtered_zones if z.is_bear_poc)

        avg_score = sum(z.score for z in raw_zones) / len(raw_zones) if raw_zones else 0

        zone_rows.append({
            "Ticker": ticker,
            "Raw Zones": len(raw_zones),
            "L5": l5_count,
            "L4": l4_count,
            "L3": l3_count,
            "Filtered": len(filtered_zones),
            "T3": t3_count,
            "T2": t2_count,
            "T1": t1_count,
            "Bull POC": bull_count,
            "Bear POC": bear_count,
            "Avg Score": f"{avg_score:.1f}",
        })

    if zone_rows:
        df_zones = pd.DataFrame(zone_rows)
        st.dataframe(df_zones, use_container_width=True, hide_index=True)

    st.markdown("---")

    # =========================================================================
    # SETUP SUMMARY
    # =========================================================================
    st.markdown("### Trading Setups Identified")

    setup_rows = []
    for result in successful_custom:
        ticker = result.get("ticker", "Unknown")
        primary = result.get("primary_setup")
        secondary = result.get("secondary_setup")
        bar_data = result.get("bar_data")
        price = bar_data.price if bar_data else 0

        if primary and primary.hvn_poc > 0:
            tier_val = primary.tier.value if hasattr(primary.tier, 'value') else primary.tier
            setup_rows.append({
                "Ticker": ticker,
                "Setup": "PRIMARY",
                "Direction": primary.direction.value if primary.direction else "—",
                "Zone ID": primary.zone_id.replace(f"{ticker}_", ""),
                "POC": f"${primary.hvn_poc:.2f}",
                "Range": f"${primary.zone_low:.2f} - ${primary.zone_high:.2f}",
                "Target": f"${primary.target:.2f}" if primary.target else "—",
                "R:R": f"{primary.risk_reward:.2f}" if primary.risk_reward else "—",
                "Tier": tier_val,
                "ATR Dist": f"{primary.atr_distance:.2f}" if hasattr(primary, 'atr_distance') and primary.atr_distance else "—",
            })

        if secondary and secondary.hvn_poc > 0:
            tier_val = secondary.tier.value if hasattr(secondary.tier, 'value') else secondary.tier
            setup_rows.append({
                "Ticker": ticker,
                "Setup": "SECONDARY",
                "Direction": secondary.direction.value if secondary.direction else "—",
                "Zone ID": secondary.zone_id.replace(f"{ticker}_", ""),
                "POC": f"${secondary.hvn_poc:.2f}",
                "Range": f"${secondary.zone_low:.2f} - ${secondary.zone_high:.2f}",
                "Target": f"${secondary.target:.2f}" if secondary.target else "—",
                "R:R": f"{secondary.risk_reward:.2f}" if secondary.risk_reward else "—",
                "Tier": tier_val,
                "ATR Dist": f"{secondary.atr_distance:.2f}" if hasattr(secondary, 'atr_distance') and secondary.atr_distance else "—",
            })

    if setup_rows:
        df_setups = pd.DataFrame(setup_rows)

        def style_setup_type(val):
            if val == "PRIMARY":
                return "background-color: #1a237e; color: white; font-weight: bold;"
            elif val == "SECONDARY":
                return "background-color: #b71c1c; color: white; font-weight: bold;"
            return ""

        def style_tier(val):
            if val == "T3":
                return "background-color: #00C853; color: white; font-weight: bold;"
            elif val == "T2":
                return "background-color: #FFD600; color: black; font-weight: bold;"
            elif val == "T1":
                return "background-color: #FF6D00; color: white; font-weight: bold;"
            return ""

        styled_setups = df_setups.style.applymap(style_setup_type, subset=["Setup"])
        styled_setups = styled_setups.applymap(style_tier, subset=["Tier"])

        st.dataframe(styled_setups, use_container_width=True, hide_index=True)
    else:
        st.info("No trading setups identified in current analysis.")

    # =========================================================================
    # HVN POC SUMMARY
    # =========================================================================
    st.markdown("---")
    st.markdown("### HVN POC Prices (Top 5 per Ticker)")

    poc_rows = []
    for result in successful_custom:
        ticker = result.get("ticker", "Unknown")
        hvn_result = result.get("hvn_result")

        if hvn_result:
            pocs = hvn_result.get_poc_prices() if hasattr(hvn_result, 'get_poc_prices') else []
            row = {"Ticker": ticker}
            for i, poc in enumerate(pocs[:5], 1):
                row[f"POC{i}"] = f"${poc:.2f}" if poc > 0 else "—"
            # Fill remaining columns if less than 5 POCs
            for i in range(len(pocs) + 1, 6):
                row[f"POC{i}"] = "—"
            poc_rows.append(row)

    if poc_rows:
        df_pocs = pd.DataFrame(poc_rows)
        st.dataframe(df_pocs, use_container_width=True, hide_index=True)

    # =========================================================================
    # ATR RISK SIZING TABLE
    # =========================================================================
    st.markdown("---")
    st.markdown("### ATR Risk Sizing")

    from config.settings import RISK_PER_TRADE
    st.caption(f"Position sizing based on ${RISK_PER_TRADE:.2f} risk per trade")

    atr_rows = []
    for result in successful_custom + successful_index:
        ticker = result.get("ticker", "Unknown")
        bar_data = result.get("bar_data")

        if bar_data:
            m1_atr = bar_data.m1_atr
            m5_atr = bar_data.m5_atr
            m15_atr = bar_data.m15_atr

            # Calculate shares for each ATR timeframe
            m1_shares = int(RISK_PER_TRADE / m1_atr) if m1_atr and m1_atr > 0 else None
            m5_shares = int(RISK_PER_TRADE / m5_atr) if m5_atr and m5_atr > 0 else None
            m15_shares = int(RISK_PER_TRADE / m15_atr) if m15_atr and m15_atr > 0 else None

            atr_rows.append({
                "Ticker": ticker,
                "M1 ATR": f"${m1_atr:.4f}" if m1_atr else "—",
                "M1 Shares": m1_shares if m1_shares else "—",
                "M5 ATR": f"${m5_atr:.4f}" if m5_atr else "—",
                "M5 Shares": m5_shares if m5_shares else "—",
                "M15 ATR": f"${m15_atr:.4f}" if m15_atr else "—",
                "M15 Shares": m15_shares if m15_shares else "—",
            })

    if atr_rows:
        df_atr = pd.DataFrame(atr_rows)

        def style_shares(val):
            """Style share columns with color based on value."""
            if val == "—":
                return "color: #666;"
            try:
                shares = int(val)
                if shares >= 100:
                    return "color: #00C853; font-weight: bold;"  # Green for larger positions
                elif shares >= 50:
                    return "color: #FFD600; font-weight: bold;"  # Yellow for medium
                else:
                    return "color: #FF6D00; font-weight: bold;"  # Orange for smaller
            except (ValueError, TypeError):
                return ""

        styled_atr = df_atr.style.applymap(
            style_shares,
            subset=["M1 Shares", "M5 Shares", "M15 Shares"]
        )

        st.dataframe(styled_atr, use_container_width=True, hide_index=True)
    else:
        st.info("No ATR data available for risk sizing.")

    # =========================================================================
    # ERRORS (if any)
    # =========================================================================
    if failed:
        st.markdown("---")
        st.markdown("### Errors")
        for result in failed:
            ticker = result.get("ticker", "Unknown")
            error = result.get("error", "Unknown error")
            st.error(f"**{ticker}**: {error}")


def render_selected_page():
    """Render the selected page, handling both results and no-results states."""
    selected_page = get_state("selected_page", "Dashboard")
    results = get_state("analysis_results")
    batch_results = get_state("batch_results")

    # Check if we have any results
    has_results = bool(results) or bool(batch_results)

    # Handle batch results separately
    if batch_results:
        render_batch_results_summary(batch_results)
        return

    # If no results, show appropriate message for each page
    if not has_results:
        _render_no_results_page(selected_page)
        return

    # Render the selected page with results
    render_results_summary(results)


def _render_no_results_page(selected_page: str):
    """Display a 'no results' message for the selected page."""
    st.header(selected_page)
    st.markdown("---")

    st.warning("**No Analysis Results Available**")
    st.markdown("""
    Please run an analysis first:

    1. Enter ticker symbols in the sidebar
    2. Set anchor dates for each ticker
    3. Click **Run Analysis**

    Once analysis completes, results will appear here.
    """)

    # Show the welcome screen content below the warning
    if selected_page == "Dashboard":
        st.markdown("---")
        render_welcome_screen()


def render_results_summary(results):
    """Display analysis results based on sidebar page selection."""
    # Store results in session state for page access
    st.session_state["analysis_results"] = results

    # Get selected page from session state
    selected_page = get_state("selected_page", "Dashboard")

    # Render the selected page
    if selected_page == "Dashboard":
        render_dashboard(results)

    elif selected_page == "Market Overview":
        st.header("Market Overview")
        render_market_overview_tab(results)

    elif selected_page == "Bar Data":
        st.header("Bar Data")
        render_bar_data_tab_new(results)

    elif selected_page == "Raw Zones":
        st.header("Raw Zones")
        render_raw_zones_tab(results)

    elif selected_page == "Zone Results":
        st.header("Zone Results")
        render_zone_results_tab(results)

    elif selected_page == "Analysis":
        st.header("Analysis")
        render_analysis_tab(results)

    elif selected_page == "Summary":
        st.header("Summary")
        render_summary_tab(results)

    elif selected_page == "Pre-Market Report":
        render_pre_market_report_tab(results)


def render_batch_results_summary(batch_results):
    """Display batch analysis results with tabs for each anchor preset."""
    st.markdown("---")
    st.header("Batch Analysis Complete")

    # Summary metrics
    num_presets = len(batch_results)
    total_analyses = sum(
        len(preset_data.get("custom", []))
        for preset_data in batch_results.values()
    )
    successful = sum(
        sum(1 for r in preset_data.get("custom", []) if r.get("success", False))
        for preset_data in batch_results.values()
    )

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Anchor Presets", num_presets)
    with col2:
        st.metric("Total Analyses", total_analyses)
    with col3:
        st.metric("Successful", successful)
    with col4:
        st.metric("Errors", total_analyses - successful)

    st.markdown("---")

    # Create tabs for each anchor preset
    preset_names = list(batch_results.keys())
    tabs = st.tabs(preset_names + ["Comparison"])

    # Render each preset's results
    for i, preset in enumerate(preset_names):
        with tabs[i]:
            preset_data = batch_results[preset]
            render_preset_results(preset, preset_data)

    # Comparison tab
    with tabs[-1]:
        render_anchor_comparison(batch_results)


def render_preset_results(preset: str, preset_data: dict):
    """Render results for a single anchor preset."""
    st.subheader(f"{preset}")
    st.caption(f"Anchor Date: {preset_data.get('anchor_date', 'N/A')}")

    custom_results = preset_data.get("custom", [])

    if not custom_results:
        st.warning("No results for this preset")
        return

    # Summary for this preset
    successful = [r for r in custom_results if r.get("success", False)]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Tickers", len(custom_results))
    with col2:
        st.metric("Successful", len(successful))
    with col3:
        avg_zones = sum(r.get("zones_count", 0) for r in successful) / max(len(successful), 1)
        st.metric("Avg Zones", f"{avg_zones:.1f}")

    # Results table
    if successful:
        import pandas as pd

        table_data = []
        for r in successful:
            table_data.append({
                "Ticker": r.get("ticker", ""),
                "Price": f"${r.get('price', 0):.2f}",
                "Direction": r.get("direction", ""),
                "Zones": r.get("zones_count", 0),
                "Bull POC": r.get("bull_poc", "N/A"),
                "Bear POC": r.get("bear_poc", "N/A"),
            })

        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Expandable details for each ticker
        with st.expander("Zone Details"):
            for r in successful:
                filtered_zones = r.get("filtered_zones", [])
                if filtered_zones:
                    st.markdown(f"**{r.get('ticker')}** - {len(filtered_zones)} zones")
                    zone_data = []
                    for z in filtered_zones[:10]:  # Show top 10
                        zone_data.append({
                            "Zone ID": z.zone_id,
                            "HVN POC": f"${z.hvn_poc:.2f}",
                            "Tier": z.tier,
                            "Bull": "Y" if z.is_bull_poc else "",
                            "Bear": "Y" if z.is_bear_poc else "",
                        })
                    if zone_data:
                        st.dataframe(pd.DataFrame(zone_data), hide_index=True)
                    st.markdown("---")


def render_anchor_comparison(batch_results):
    """Render comparison view across anchor presets."""
    from core.pipeline_runner import compare_zones_across_anchors
    import pandas as pd

    st.subheader("Cross-Anchor Comparison")
    st.markdown("Compare zones that appear across multiple anchor dates.")

    # Get all tickers that were analyzed
    all_tickers = set()
    for preset_data in batch_results.values():
        for r in preset_data.get("custom", []):
            if r.get("success"):
                all_tickers.add(r.get("ticker"))

    if not all_tickers:
        st.warning("No successful analyses to compare")
        return

    # Ticker selector
    selected_ticker = st.selectbox(
        "Select Ticker to Compare",
        options=sorted(all_tickers)
    )

    if selected_ticker:
        # Run comparison
        comparison = compare_zones_across_anchors(batch_results, selected_ticker)

        # Summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Anchors Analyzed", len(comparison.get("anchors", {})))
        with col2:
            st.metric("Common POCs", len(comparison.get("common_pocs", [])))
        with col3:
            total_zones = sum(
                a.get("zones_count", 0)
                for a in comparison.get("anchors", {}).values()
            )
            st.metric("Total Zones", total_zones)

        st.markdown("---")

        # Per-anchor summary
        st.markdown("**Results by Anchor:**")
        anchor_data = []
        for preset, anchor_info in comparison.get("anchors", {}).items():
            anchor_data.append({
                "Anchor": preset,
                "Date": anchor_info.get("anchor_date", ""),
                "Zones": anchor_info.get("zones_count", 0),
                "Bull POC": anchor_info.get("bull_poc", "N/A"),
                "Bear POC": anchor_info.get("bear_poc", "N/A"),
            })

        if anchor_data:
            st.dataframe(pd.DataFrame(anchor_data), use_container_width=True, hide_index=True)

        # Common POCs (zones that appear across multiple anchors)
        common_pocs = comparison.get("common_pocs", [])
        if common_pocs:
            st.markdown("---")
            st.markdown("**POCs Appearing in Multiple Anchors:**")
            st.caption("These price levels have volume confluence across different time frames.")

            poc_data = []
            for poc in common_pocs[:10]:  # Top 10
                poc_data.append({
                    "Price": f"${poc.get('price', 0):.2f}",
                    "Anchors": ", ".join(poc.get("anchors", [])),
                    "Count": poc.get("count", 0),
                })

            st.dataframe(pd.DataFrame(poc_data), use_container_width=True, hide_index=True)

            # Highlight highest confluence
            if common_pocs:
                top_poc = common_pocs[0]
                st.success(
                    f"Highest confluence: ${top_poc.get('price', 0):.2f} "
                    f"(appears in {top_poc.get('count', 0)} anchors)"
                )
        else:
            st.info("No common POCs found across anchor dates")


def render_market_overview_tab(results):
    """Render the market overview tab with structure tables."""
    from components.data_tables import render_market_structure_table

    # Index Structure
    index_results = results.get("index", [])
    if index_results:
        index_data = []
        for result in index_results:
            if result.get("success"):
                ms = result.get("market_structure")
                if ms:
                    index_data.append({
                        "ticker": result.get("ticker"),
                        "price": ms.price,
                        "d1_direction": ms.d1.direction.value,
                        "d1_strong": ms.d1.strong,
                        "d1_weak": ms.d1.weak,
                        "h4_direction": ms.h4.direction.value,
                        "h4_strong": ms.h4.strong,
                        "h4_weak": ms.h4.weak,
                        "h1_direction": ms.h1.direction.value,
                        "h1_strong": ms.h1.strong,
                        "h1_weak": ms.h1.weak,
                        "m15_direction": ms.m15.direction.value,
                        "m15_strong": ms.m15.strong,
                        "m15_weak": ms.m15.weak,
                        "composite": ms.composite.value,
                    })
                else:
                    index_data.append({
                        "ticker": result.get("ticker"),
                        "price": result.get("price"),
                        "d1_direction": result.get("direction", "—"),
                        "composite": result.get("direction", "—"),
                    })

        if index_data:
            render_market_structure_table(index_data, "Index Structure (Prior Month)")

    # Ticker Structure
    st.markdown("---")
    custom_results = results.get("custom", [])
    if custom_results:
        ticker_data = []
        for result in custom_results:
            if result.get("success"):
                ms = result.get("market_structure")
                if ms:
                    ticker_data.append({
                        "ticker": result.get("ticker"),
                        "price": ms.price,
                        "d1_direction": ms.d1.direction.value,
                        "d1_strong": ms.d1.strong,
                        "d1_weak": ms.d1.weak,
                        "h4_direction": ms.h4.direction.value,
                        "h4_strong": ms.h4.strong,
                        "h4_weak": ms.h4.weak,
                        "h1_direction": ms.h1.direction.value,
                        "h1_strong": ms.h1.strong,
                        "h1_weak": ms.h1.weak,
                        "m15_direction": ms.m15.direction.value,
                        "m15_strong": ms.m15.strong,
                        "m15_weak": ms.m15.weak,
                        "composite": ms.composite.value,
                    })
                else:
                    ticker_data.append({
                        "ticker": result.get("ticker"),
                        "price": result.get("price"),
                        "d1_direction": result.get("direction", "—"),
                        "composite": result.get("direction", "—"),
                    })

        if ticker_data:
            render_market_structure_table(ticker_data, "Ticker Structure (Custom Anchor)")


def render_bar_data_tab(results):
    """Render the bar data tab with OHLC and technical data (legacy single-ticker view)."""
    from components.data_tables import (
        render_bar_data_section,
        render_hvn_pocs_table
    )

    custom_results = results.get("custom", [])

    if not custom_results:
        st.info("No bar data available")
        return

    # Let user select which ticker to view
    tickers = [r.get("ticker") for r in custom_results if r.get("success")]
    if not tickers:
        st.warning("No successful ticker analyses")
        return

    selected = st.selectbox("Select Ticker", tickers)

    # Find the selected result
    result = next((r for r in custom_results if r.get("ticker") == selected), None)
    if not result:
        return

    bar_data = result.get("bar_data")
    hvn_result = result.get("hvn_result")

    if bar_data:
        col1, col2 = st.columns(2)

        with col1:
            render_bar_data_section(bar_data, "daily")
            render_bar_data_section(bar_data, "weekly")
            render_bar_data_section(bar_data, "monthly")

        with col2:
            render_bar_data_section(bar_data, "atr")
            render_bar_data_section(bar_data, "overnight")
            render_bar_data_section(bar_data, "camarilla")

    if hvn_result:
        st.markdown("---")
        render_hvn_pocs_table(hvn_result)


def render_bar_data_tab_new(results):
    """Render the bar data tab with multi-ticker view."""
    from pages._bar_data import render_bar_data_page
    render_bar_data_page(results)


def _render_hvn_pocs_grid(results):
    """Render HVN POCs table with 10 columns per ticker."""
    import pandas as pd
    from components.data_tables import format_price

    rows = []
    for result in results:
        hvn_result = result.get("hvn_result")
        bar_data = result.get("bar_data")

        if not hvn_result or not bar_data:
            continue

        row = {"Ticker": bar_data.ticker}

        # Get POCs sorted by rank
        pocs_dict = hvn_result.to_dict()
        for i in range(1, 11):
            poc_price = pocs_dict.get(f"hvn_poc{i}")
            row[f"POC {i}"] = poc_price

        rows.append(row)

    if not rows:
        st.info("No HVN POC data available")
        return

    df = pd.DataFrame(rows)

    # Format POC columns
    poc_cols = [f"POC {i}" for i in range(1, 11)]
    for col in poc_cols:
        if col in df.columns:
            df[col] = df[col].apply(format_price)

    st.dataframe(df, use_container_width=True, hide_index=True)


def render_raw_zones_tab(results):
    """Render the raw zones tab with sortable/filterable table."""
    from pages._raw_zones import render_raw_zones_page
    render_raw_zones_page(results)


def _render_raw_zones_table(zones):
    """Render the raw zones table with styling."""
    from components.data_tables import style_rank_cell, format_price
    import pandas as pd

    if not zones:
        st.info("No zones to display")
        return

    rows = []
    for zone in zones:
        rank_val = zone.rank.value if hasattr(zone.rank, 'value') else zone.rank
        confluences_str = zone.confluences_str if hasattr(zone, 'confluences_str') else ", ".join(zone.confluences)

        row = {
            "Ticker": zone.ticker,
            "Zone ID": zone.zone_id,
            "POC Rank": f"POC {zone.poc_rank}",
            "HVN POC": zone.hvn_poc,
            "Zone High": zone.zone_high,
            "Zone Low": zone.zone_low,
            "Overlaps": zone.overlaps,
            "Score": zone.score,
            "Rank": rank_val,
            "Confluences": confluences_str,
        }
        rows.append(row)

    df = pd.DataFrame(rows)

    # Format columns
    price_cols = ["HVN POC", "Zone High", "Zone Low"]
    for col in price_cols:
        df[col] = df[col].apply(format_price)

    df["Score"] = df["Score"].apply(lambda x: f"{x:.1f}")

    def style_row(row):
        styles = [""] * len(row)
        for i, col in enumerate(row.index):
            if col == "Rank":
                styles[i] = style_rank_cell(str(row[col]))
        return styles

    styled = df.style.apply(style_row, axis=1)

    st.dataframe(
        styled,
        use_container_width=True,
        hide_index=True,
        height=500
    )


def render_zone_results_tab(results):
    """Render the zone results tab with tier classification."""
    from pages._zone_results import render_zone_results_page
    render_zone_results_page(results)


def _render_filtered_zones_table(zones):
    """Render the filtered zones table with tier and setup styling."""
    from components.data_tables import style_rank_cell, style_tier_cell, format_price
    import pandas as pd

    if not zones:
        st.info("No zones to display")
        return

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

    st.dataframe(
        styled,
        use_container_width=True,
        hide_index=True,
        height=400
    )


def _render_setup_summary(results):
    """Render a summary of bull/bear POCs per ticker."""
    from components.data_tables import style_tier_cell, format_price
    import pandas as pd

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

    def style_setup_row(row):
        styles = [""] * len(row)
        for i, col in enumerate(row.index):
            if col in ["Bull Tier", "Bear Tier"]:
                styles[i] = style_tier_cell(str(row[col]))
        return styles

    styled = df.style.apply(style_setup_row, axis=1)

    st.dataframe(
        styled,
        use_container_width=True,
        hide_index=True
    )


def render_zones_tab(results):
    """Render the zones tab with raw and filtered zones."""
    from components.data_tables import render_zones_table

    custom_results = results.get("custom", [])

    if not custom_results:
        st.info("No zones available")
        return

    # Let user select which ticker to view
    tickers = [r.get("ticker") for r in custom_results if r.get("success")]
    if not tickers:
        st.warning("No successful ticker analyses")
        return

    selected = st.selectbox("Select Ticker", tickers, key="zones_ticker_select")

    # Find the selected result
    result = next((r for r in custom_results if r.get("ticker") == selected), None)
    if not result:
        return

    raw_zones = result.get("raw_zones", [])
    filtered_zones = result.get("filtered_zones", [])

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"**Raw Zones ({len(raw_zones)})**")
        if raw_zones:
            render_zones_table(raw_zones, "")

    with col2:
        st.markdown(f"**Filtered Zones ({len(filtered_zones)})**")
        if filtered_zones:
            render_zones_table(filtered_zones, "")


def render_analysis_tab(results):
    """Render the analysis tab with Primary/Secondary setups."""
    from pages import render_analysis_page

    render_analysis_page(results)


def render_summary_tab(results):
    """Render the summary tab with quick overview."""
    # Index results
    index_results = results.get("index", [])
    if index_results:
        st.subheader("Index Structure (Prior Month)")
        for idx_result in index_results:
            ticker = idx_result.get("ticker", "")
            direction = idx_result.get("direction", "N/A")
            st.write(f"**{ticker}**: {direction}")

    st.markdown("---")

    # Custom ticker results
    custom_results = results.get("custom", [])
    if custom_results:
        st.subheader("Custom Ticker Results")
        for result in custom_results:
            ticker = result.get("ticker", "")
            zones_count = result.get("zones_count", 0)
            bull_poc = result.get("bull_poc", "N/A")
            bear_poc = result.get("bear_poc", "N/A")
            direction = result.get("direction", "N/A")

            # Add setup info if available
            primary_setup = result.get("primary_setup")
            secondary_setup = result.get("secondary_setup")

            with st.expander(f"{ticker} - {zones_count} zones - {direction}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Bull POC**: {bull_poc}")
                with col2:
                    st.write(f"**Bear POC**: {bear_poc}")

                # Show setup summary
                if primary_setup or secondary_setup:
                    st.markdown("---")
                    st.write("**Trading Setups:**")
                    col1, col2 = st.columns(2)
                    with col1:
                        if primary_setup:
                            st.write(f"Primary: {primary_setup.direction.value} @ ${primary_setup.hvn_poc:.2f}")
                            st.write(f"Target: ${primary_setup.target:.2f} ({primary_setup.risk_reward:.2f}R)")
                        else:
                            st.write("Primary: N/A")
                    with col2:
                        if secondary_setup:
                            st.write(f"Secondary: {secondary_setup.direction.value} @ ${secondary_setup.hvn_poc:.2f}")
                            st.write(f"Target: ${secondary_setup.target:.2f} ({secondary_setup.risk_reward:.2f}R)")
                        else:
                            st.write("Secondary: N/A")

                if result.get("error"):
                    st.error(result.get("error"))


def render_pre_market_report_tab(results):
    """Render the pre-market report tab with full chart visualization."""
    # Store results in session state for the pre-market report page
    st.session_state["analysis_results"] = results
    render_pre_market_report()


if __name__ == "__main__":
    main()
