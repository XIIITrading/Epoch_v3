"""
Market Scanner Page - Session 11

This page provides:
- Scanner input form with ticker list selection
- Filter thresholds (min ATR, min price, min gap %)
- Results table with ranking scores
- "Send to Analysis" button to transfer tickers
"""
import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta, timezone

from calculators.scanner import (
    TwoPhaseScanner,
    FilterPhase,
    RankingWeights,
    get_ticker_list,
    TICKER_LISTS,
)
from components.data_tables import format_price


def render_scanner_page():
    """Render the market scanner page."""
    st.header("Market Scanner")
    st.markdown("Scan for high-potential trading candidates using the two-phase filter system.")

    # Scanner configuration in sidebar-style columns
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Scanner Configuration")

        # Ticker list selection
        ticker_list_name = st.selectbox(
            "Ticker List",
            options=list(TICKER_LISTS.keys()),
            format_func=lambda x: x.upper(),
            index=0,
            help="Select the index to scan"
        )

        # Date selection
        scan_date = st.date_input(
            "Scan Date",
            value=date.today(),
            max_value=date.today(),
            help="Date for the scan (12:00 UTC)"
        )

        st.markdown("---")
        st.markdown("**Filter Thresholds**")

        # Filter inputs
        min_atr = st.number_input(
            "Min ATR ($)",
            min_value=0.0,
            max_value=50.0,
            value=2.0,
            step=0.5,
            help="Minimum Average True Range in dollars"
        )

        min_price = st.number_input(
            "Min Price ($)",
            min_value=0.0,
            max_value=500.0,
            value=10.0,
            step=5.0,
            help="Minimum stock price"
        )

        min_gap = st.number_input(
            "Min Gap (%)",
            min_value=0.0,
            max_value=50.0,
            value=2.0,
            step=0.5,
            help="Minimum absolute gap percentage"
        )

        st.markdown("---")

        # Display ticker count
        tickers = get_ticker_list(ticker_list_name)
        st.metric("Tickers to Scan", len(tickers))

        # Run scan button
        run_scan = st.button(
            "Run Scan",
            type="primary",
            use_container_width=True,
            help="Start the two-phase scan"
        )

    with col2:
        # Results area
        if run_scan:
            _run_scanner(
                ticker_list_name=ticker_list_name,
                scan_date=scan_date,
                min_atr=min_atr,
                min_price=min_price,
                min_gap=min_gap
            )
        elif "scanner_results" in st.session_state and st.session_state.scanner_results is not None:
            # Display previous results
            _display_results(st.session_state.scanner_results)
        else:
            # Welcome message
            st.info("""
            **Two-Phase Scanner**

            **Phase 1 - Hard Filters:**
            - ATR >= minimum threshold
            - Price >= minimum threshold
            - |Gap%| >= minimum threshold

            **Phase 2 - Ranking:**
            - Normalized overnight volume
            - Relative overnight volume (vs prior day)
            - Relative volume (overnight vs regular hours)
            - Gap magnitude

            Click **Run Scan** to start scanning.
            """)


def _run_scanner(
    ticker_list_name: str,
    scan_date: date,
    min_atr: float,
    min_price: float,
    min_gap: float
):
    """Execute the scanner and display results."""
    # Get tickers
    tickers = get_ticker_list(ticker_list_name)

    # Create filter configuration
    filter_phase = FilterPhase(
        min_atr=min_atr,
        min_price=min_price,
        min_gap_percent=min_gap
    )

    # Initialize scanner
    scanner = TwoPhaseScanner(
        tickers=tickers,
        filter_phase=filter_phase,
        ranking_weights=RankingWeights(),
        parallel_workers=10
    )

    # Progress display
    progress_bar = st.progress(0, text="Starting scan...")
    status_text = st.empty()

    def progress_callback(completed, total, ticker):
        progress = completed / total
        progress_bar.progress(progress, text=f"Processing {ticker}...")
        if completed % 20 == 0:
            status_text.text(f"Processed {completed}/{total} tickers")

    # Run scan
    try:
        # Convert date to datetime with timezone
        scan_datetime = datetime.combine(
            scan_date,
            datetime.min.time()
        ).replace(hour=12, minute=0, second=0, tzinfo=timezone.utc)

        results = scanner.run_scan(
            scan_date=scan_datetime,
            progress_callback=progress_callback
        )

        # Clear progress
        progress_bar.empty()
        status_text.empty()

        if results.empty:
            st.warning("No stocks passed the filters. Try relaxing the thresholds.")
            st.session_state.scanner_results = None
            return

        # Store results in session state
        st.session_state.scanner_results = results

        # Display results
        _display_results(results)

    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"Scanner error: {str(e)}")
        st.session_state.scanner_results = None


def _display_results(results: pd.DataFrame):
    """Display scanner results with summary and table."""
    if results.empty:
        st.warning("No results to display")
        return

    # Summary metrics
    st.subheader("Scan Results")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Stocks Found", len(results))
    with col2:
        avg_gap = results['gap_percent'].mean()
        st.metric("Avg Gap", f"{avg_gap:.1f}%")
    with col3:
        avg_score = results['ranking_score'].mean()
        st.metric("Avg Score", f"{avg_score:.1f}")
    with col4:
        scan_date = results['scan_date'].iloc[0] if 'scan_date' in results.columns else "N/A"
        st.metric("Scan Date", str(scan_date))

    st.markdown("---")

    # Top 5 quick view
    st.markdown("**Top 5 Candidates:**")
    top_5 = results.head(5)[['rank', 'ticker', 'current_price', 'gap_percent', 'ranking_score']].copy()
    top_5['current_price'] = top_5['current_price'].apply(lambda x: f"${x:.2f}")
    top_5['gap_percent'] = top_5['gap_percent'].apply(lambda x: f"{x:+.2f}%")
    top_5['ranking_score'] = top_5['ranking_score'].apply(lambda x: f"{x:.1f}")
    top_5.columns = ['Rank', 'Ticker', 'Price', 'Gap', 'Score']
    st.dataframe(top_5, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Full results table with styling
    st.subheader("Full Results")

    # Prepare display dataframe
    display_df = results[[
        'rank', 'ticker', 'ticker_id', 'current_price', 'gap_percent',
        'current_overnight_volume', 'prior_overnight_volume',
        'relative_overnight_volume', 'relative_volume',
        'ranking_score', 'atr'
    ]].copy()

    # Format columns
    display_df['current_price'] = display_df['current_price'].apply(format_price)
    display_df['gap_percent'] = display_df['gap_percent'].apply(lambda x: f"{x:+.2f}%")
    display_df['current_overnight_volume'] = display_df['current_overnight_volume'].apply(lambda x: f"{x:,.0f}")
    display_df['prior_overnight_volume'] = display_df['prior_overnight_volume'].apply(lambda x: f"{x:,.0f}")
    display_df['relative_overnight_volume'] = display_df['relative_overnight_volume'].apply(lambda x: f"{x:.2f}x")
    display_df['relative_volume'] = display_df['relative_volume'].apply(lambda x: f"{x:.2f}x")
    display_df['ranking_score'] = display_df['ranking_score'].apply(lambda x: f"{x:.1f}")
    display_df['atr'] = display_df['atr'].apply(format_price)

    # Rename columns for display
    display_df.columns = [
        'Rank', 'Ticker', 'Ticker ID', 'Price', 'Gap %',
        'ON Volume', 'Prior ON Vol', 'Rel ON Vol', 'Rel Vol',
        'Score', 'ATR'
    ]

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=400
    )

    st.markdown("---")

    # Send to Analysis section
    st.subheader("Send to Analysis")

    # Let user select which tickers to send
    available_tickers = results['ticker'].tolist()

    # Quick select options
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Select Top 5"):
            st.session_state.selected_scanner_tickers = available_tickers[:5]
    with col2:
        if st.button("Select Top 10"):
            st.session_state.selected_scanner_tickers = available_tickers[:10]
    with col3:
        if st.button("Clear Selection"):
            st.session_state.selected_scanner_tickers = []

    # Initialize selected tickers if not exists
    if "selected_scanner_tickers" not in st.session_state:
        st.session_state.selected_scanner_tickers = []

    selected_tickers = st.multiselect(
        "Select tickers to analyze",
        options=available_tickers,
        default=st.session_state.selected_scanner_tickers,
        key="scanner_ticker_select"
    )

    if selected_tickers:
        st.write(f"**Selected:** {', '.join(selected_tickers)}")

        # Create ticker inputs for the main analysis
        if st.button("Send to Analysis", type="primary"):
            # Store selected tickers for transfer
            st.session_state.scanner_to_analysis = selected_tickers
            st.success(f"Sent {len(selected_tickers)} tickers to analysis. Go to sidebar to run analysis.")

    # Export options
    st.markdown("---")
    st.subheader("Export")

    col1, col2 = st.columns(2)
    with col1:
        # CSV export
        csv = results.to_csv(index=False)
        st.download_button(
            "Download CSV",
            data=csv,
            file_name=f"scanner_results_{results['scan_date'].iloc[0]}.csv",
            mime="text/csv"
        )

    with col2:
        # Ticker list export (just tickers, one per line)
        ticker_list = "\n".join(results['ticker'].tolist())
        st.download_button(
            "Download Ticker List",
            data=ticker_list,
            file_name="scanner_tickers.txt",
            mime="text/plain"
        )


def render_scanner_tab(results: dict = None):
    """
    Render scanner within the main app tabs.

    This is called from app.py when Scanner tab is selected.
    """
    render_scanner_page()


# For standalone page access
if __name__ == "__main__":
    st.set_page_config(
        page_title="Market Scanner - Epoch",
        page_icon="",
        layout="wide"
    )
    render_scanner_page()
