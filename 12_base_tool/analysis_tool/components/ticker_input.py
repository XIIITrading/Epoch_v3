"""
Ticker Input Component - 10-row input form with individual anchor dates.

Each row has side-by-side:
- Ticker symbol (text input)
- Anchor date (date picker)

Also supports CSV paste input for bulk entry.
"""
import streamlit as st
from datetime import date, datetime
from typing import Dict, List, Optional

from config.settings import MAX_TICKERS


def parse_csv_input(csv_text: str) -> List[Dict]:
    """
    Parse CSV text input into ticker/anchor_date pairs.

    Supports formats:
    - AAPL,2024-01-15
    - AAPL,01/15/2024
    - AAPL,1/15/2024

    Args:
        csv_text: Multi-line CSV text

    Returns:
        List of dicts with 'ticker' and 'anchor_date' keys
    """
    results = []
    lines = csv_text.strip().split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Split by comma
        parts = [p.strip() for p in line.split(',')]
        if len(parts) < 2:
            continue

        ticker = parts[0].upper().strip()
        date_str = parts[1].strip()

        if not ticker:
            continue

        # Try to parse date in various formats
        anchor_date = None
        date_formats = [
            '%Y-%m-%d',      # 2024-01-15
            '%m/%d/%Y',      # 01/15/2024
            '%m-%d-%Y',      # 01-15-2024
            '%d/%m/%Y',      # 15/01/2024 (European)
        ]

        for fmt in date_formats:
            try:
                anchor_date = datetime.strptime(date_str, fmt).date()
                break
            except ValueError:
                continue

        if ticker and anchor_date:
            results.append({
                'ticker': ticker,
                'anchor_date': anchor_date
            })

    return results


def render_ticker_input(prefill_tickers: List[str] = None) -> List[Dict]:
    """
    Render the ticker input form with 10 rows.

    Each row has a ticker input and an anchor date picker side-by-side.
    Returns list of ticker input dictionaries.

    Args:
        prefill_tickers: Optional list of tickers to prefill (from scanner)

    Returns:
        List of dicts with 'ticker' and 'anchor_date' keys
    """
    st.subheader("Custom Tickers")
    st.caption("Enter up to 10 tickers with anchor dates")

    # Initialize session state for ticker rows if not exists
    if "ticker_rows" not in st.session_state:
        st.session_state.ticker_rows = [
            {"ticker": "", "anchor_date": None}
            for _ in range(MAX_TICKERS)
        ]
        # Also initialize widget keys
        for i in range(MAX_TICKERS):
            if f"ticker_{i}" not in st.session_state:
                st.session_state[f"ticker_{i}"] = ""

    # Handle prefill from scanner
    if prefill_tickers and st.session_state.get("prefill_applied") != prefill_tickers:
        # Clear existing and prefill (dates remain empty for manual entry)
        for i in range(MAX_TICKERS):
            if i < len(prefill_tickers):
                st.session_state.ticker_rows[i] = {
                    "ticker": prefill_tickers[i],
                    "anchor_date": None
                }
            else:
                st.session_state.ticker_rows[i] = {"ticker": "", "anchor_date": None}
        st.session_state.prefill_applied = prefill_tickers

    # CSV Paste Input section
    with st.expander("Paste CSV (Ticker,Date)", expanded=False):
        st.caption("Format: TICKER,YYYY-MM-DD (one per line)")
        csv_text = st.text_area(
            "CSV Input",
            value="",
            height=100,
            key="csv_ticker_input",
            label_visibility="collapsed",
            placeholder="AAPL,2024-01-15\nMSFT,2024-02-01\nNVDA,2024-01-20"
        )

        if st.button("Load from CSV", use_container_width=True):
            if csv_text.strip():
                parsed = parse_csv_input(csv_text)
                if parsed:
                    # Clear existing and load parsed data
                    for i in range(MAX_TICKERS):
                        if i < len(parsed):
                            st.session_state.ticker_rows[i] = {
                                "ticker": parsed[i]['ticker'],
                                "anchor_date": parsed[i]['anchor_date']
                            }
                            # Also set the widget key directly so it persists after rerun
                            st.session_state[f"ticker_{i}"] = parsed[i]['ticker']
                        else:
                            st.session_state.ticker_rows[i] = {"ticker": "", "anchor_date": None}
                            st.session_state[f"ticker_{i}"] = ""
                    st.success(f"Loaded {len(parsed)} ticker(s)")
                    st.rerun()
                else:
                    st.error("Could not parse CSV. Use format: TICKER,YYYY-MM-DD")
            else:
                st.warning("Enter CSV data first")

    # Header row
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("**Ticker**")
    with col2:
        st.markdown("**Anchor Date**")

    # Render 10 input rows
    for i in range(MAX_TICKERS):
        col1, col2 = st.columns([1, 1])

        with col1:
            # Ensure widget key is initialized
            if f"ticker_{i}" not in st.session_state:
                st.session_state[f"ticker_{i}"] = st.session_state.ticker_rows[i].get("ticker", "")

            ticker = st.text_input(
                f"Ticker {i+1}",
                key=f"ticker_{i}",
                label_visibility="collapsed",
                placeholder=f"Ticker {i+1}"
            ).upper().strip()
            st.session_state.ticker_rows[i]["ticker"] = ticker

        with col2:
            # Only show date picker if ticker is entered
            if ticker:
                current_date = st.session_state.ticker_rows[i].get("anchor_date")
                anchor = st.date_input(
                    f"Anchor {i+1}",
                    value=current_date,
                    max_value=date.today(),
                    key=f"anchor_{i}",
                    label_visibility="collapsed",
                    format="MM/DD/YYYY"
                )
                st.session_state.ticker_rows[i]["anchor_date"] = anchor
            else:
                # Show disabled placeholder when no ticker
                st.text_input(
                    f"Anchor {i+1}",
                    value="",
                    key=f"anchor_placeholder_{i}",
                    label_visibility="collapsed",
                    placeholder="Enter ticker first",
                    disabled=True
                )
                st.session_state.ticker_rows[i]["anchor_date"] = None

    # Show summary of valid inputs
    valid_count = sum(
        1 for row in st.session_state.ticker_rows
        if row.get("ticker") and row.get("anchor_date")
    )

    st.markdown("---")

    # Quick actions
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Set All Dates", use_container_width=True):
            st.session_state.show_bulk_date = True

    with col2:
        if st.button("Clear All", use_container_width=True):
            for i in range(MAX_TICKERS):
                st.session_state.ticker_rows[i] = {"ticker": "", "anchor_date": None}
                st.session_state[f"ticker_{i}"] = ""
            st.rerun()

    # Bulk date setter (shown when button clicked)
    if st.session_state.get("show_bulk_date", False):
        st.markdown("**Set anchor date for all tickers:**")
        bulk_date = st.date_input(
            "Bulk anchor date",
            value=None,
            max_value=date.today(),
            key="bulk_anchor_date",
            label_visibility="collapsed",
            format="MM/DD/YYYY"
        )
        if st.button("Apply to All", use_container_width=True):
            for i in range(MAX_TICKERS):
                if st.session_state.ticker_rows[i].get("ticker"):
                    st.session_state.ticker_rows[i]["anchor_date"] = bulk_date
            st.session_state.show_bulk_date = False
            st.rerun()

    st.caption(f"Valid inputs: {valid_count} / {MAX_TICKERS}")

    # Show index tickers info
    st.markdown("---")
    st.markdown("**Index Tickers** (automatic)")
    st.caption("SPY, QQQ, DIA - Prior Month anchor")

    # Return the ticker rows
    return [
        {
            "ticker": row.get("ticker", ""),
            "anchor_date": row.get("anchor_date"),
            "analysis_date": date.today()
        }
        for row in st.session_state.ticker_rows
    ]
