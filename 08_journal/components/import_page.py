"""Import page — CSV folder picker, trade processing, and DB save."""

import streamlit as st
from pathlib import Path

from config import TRADE_LOG_DIR
from core.trade_processor import process_session
from data.journal_db import JournalDB


def _scan_csv_files() -> list[Path]:
    """Scan trade_log/ recursively for CSV files, most recent first."""
    if not TRADE_LOG_DIR.exists():
        return []
    files = sorted(TRADE_LOG_DIR.rglob("*.csv"), reverse=True)
    return files


def _display_path(filepath: Path) -> str:
    """Show path relative to trade_log/ for cleaner dropdown labels."""
    try:
        return str(filepath.relative_to(TRADE_LOG_DIR))
    except ValueError:
        return str(filepath)


def render_import_page():
    """Render the CSV import page."""
    st.header("Import Trades")

    # -----------------------------------------------------------------
    # File picker — scan trade_log/ for CSVs
    # -----------------------------------------------------------------
    csv_files = _scan_csv_files()

    if not csv_files:
        st.warning(f"No CSV files found in `{TRADE_LOG_DIR}`")
        return

    selected_label = st.selectbox(
        "Select CSV",
        options=[_display_path(f) for f in csv_files],
    )

    # Map label back to full path
    selected_file = csv_files[[_display_path(f) for f in csv_files].index(selected_label)]

    # -----------------------------------------------------------------
    # Process button
    # -----------------------------------------------------------------
    if st.button("Process CSV", type="primary"):
        with st.spinner("Processing..."):
            log = process_session(selected_file)
            st.session_state["current_log"] = log
            st.session_state["import_saved"] = False

    # -----------------------------------------------------------------
    # Results (only shown after processing)
    # -----------------------------------------------------------------
    log = st.session_state.get("current_log")
    if log is None:
        return

    # --- Summary cards ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Date", log.trade_date.strftime("%m/%d/%Y"))
    c2.metric("Trades", log.trade_count)
    c3.metric("Total P&L", f"${log.total_pnl:,.2f}")
    c4.metric("Win Rate", f"{log.win_rate:.0%}" if log.win_rate is not None else "N/A")

    st.divider()

    # --- Trade table ---
    rows = []
    for t in log.trades:
        rows.append({
            "Trade ID": t.trade_id,
            "Symbol": t.symbol,
            "Direction": t.direction.value,
            "Account": t.account,
            "Entry": f"${t.entry_price:.2f}",
            "Exit": f"${t.exit_price:.2f}" if t.exit_price is not None else "OPEN",
            "Qty": t.total_qty,
            "P&L": f"${t.pnl_total:,.2f}" if t.pnl_total is not None else "",
            "Outcome": t.outcome.value,
            "Duration": t.duration_display or "",
        })

    st.dataframe(rows, use_container_width=True, hide_index=True)

    # --- Parse errors ---
    if log.parse_errors:
        with st.expander(f"Parse Errors ({len(log.parse_errors)})"):
            for err in log.parse_errors:
                st.warning(err)

    # -----------------------------------------------------------------
    # Save button
    # -----------------------------------------------------------------
    st.divider()

    if st.session_state.get("import_saved"):
        st.success("Trades saved to database.")
    else:
        if st.button("Save to Database", type="primary"):
            with st.spinner("Saving..."):
                with JournalDB() as db:
                    count = db.save_daily_log(log)
                st.session_state["import_saved"] = True
                st.success(f"Saved {count} trades to database.")
                st.rerun()
