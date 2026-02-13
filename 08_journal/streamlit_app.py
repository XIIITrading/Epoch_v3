"""
Epoch Trading Journal - Flashcard Training System
Main Streamlit application entry point.

Replaces the original 4-tab journal app with a single-purpose
flashcard training flow, mirroring 06_training/streamlit_app.py.

Usage:
    streamlit run streamlit_app.py

Pre-requisites:
    1. Import trades:     python processor/import_trades.py
    2. Populate M1 bars:  python processor/populator.py
    3. Review trades:     Set stop_price in review page (streamlit_review.py)
    4. Run processors:    python processor/run_training_processors.py
    5. Launch flashcard:  streamlit run streamlit_app.py (this file)

Author: XIII Trading LLC
"""

import streamlit as st
import random
from datetime import datetime, date, timedelta

import sys
from pathlib import Path

# Add module directory to path
MODULE_DIR = Path(__file__).parent
sys.path.insert(0, str(MODULE_DIR))

from config import CHART_CONFIG, PREFETCH_COUNT
from data.training_db import JournalTrainingDB
from data.journal_db import JournalDB
from data.cache_manager import BarCache
from core.training_models import JournalTradeWithMetrics
from components.flashcard_ui import render_flashcard_ui, reset_flashcard_state


# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="Epoch Journal",
    page_icon="📓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for dark theme (matches 06_training)
st.markdown("""
<style>
    .stApp {
        background-color: #1a1a2e;
    }
    .stSidebar {
        background-color: #16213e;
    }
    .stMarkdown, .stText {
        color: #e0e0e0;
    }
    div[data-testid="stMetricValue"] {
        color: #e0e0e0;
    }
    .stSelectbox label, .stRadio label, .stTextArea label {
        color: #e0e0e0 !important;
    }
    .stButton button {
        border-radius: 8px;
    }
    .stButton button[kind="primary"] {
        background-color: #00C853;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================

def init_session_state():
    """Initialize session state variables."""
    if 'review_queue' not in st.session_state:
        st.session_state.review_queue = []

    if 'current_trade_index' not in st.session_state:
        st.session_state.current_trade_index = 0

    if 'queue_loaded' not in st.session_state:
        st.session_state.queue_loaded = False

    if 'last_filters' not in st.session_state:
        st.session_state.last_filters = None


init_session_state()


# =============================================================================
# DATA CLIENTS
# =============================================================================

@st.cache_resource
def get_training_db():
    """Get JournalTrainingDB client (persistent across reruns)."""
    return JournalTrainingDB()


@st.cache_resource
def get_journal_db():
    """Get JournalDB client for zone lookups."""
    return JournalDB()


def get_bar_cache():
    """Get BarCache (uses session state internally)."""
    return BarCache()


training_db = get_training_db()
journal_db = get_journal_db()
cache = get_bar_cache()


# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    st.title("Epoch Journal")
    st.caption("Flashcard Training System")
    st.markdown("---")

    # --- Date range filter ---
    st.markdown("**Date Range**")

    # Get available date range from DB
    try:
        date_range = training_db.get_date_range()
        if isinstance(date_range, tuple) and len(date_range) == 2:
            min_date = date_range[0] or date(2025, 1, 1)
            max_date = date_range[1] or date.today()
        elif isinstance(date_range, dict):
            min_date = date_range.get('min_date', date(2025, 1, 1))
            max_date = date_range.get('max_date', date.today())
        else:
            min_date = date(2025, 1, 1)
            max_date = date.today()
    except Exception:
        min_date = date(2025, 1, 1)
        max_date = date.today()

    date_col1, date_col2 = st.columns(2)
    default_from = max(min_date, max_date - timedelta(days=30))
    with date_col1:
        date_from = st.date_input("From", value=default_from, min_value=min_date, max_value=max_date)
    with date_col2:
        date_to = st.date_input("To", value=max_date, min_value=min_date, max_value=max_date)

    # --- Ticker filter ---
    try:
        available_tickers = training_db.get_available_tickers()
    except Exception:
        available_tickers = []

    ticker_options = ["All"] + available_tickers
    selected_ticker = st.selectbox("Ticker", ticker_options)

    # --- Model filter ---
    try:
        available_models = training_db.get_available_models()
    except Exception:
        available_models = []

    model_options = ["All"] + available_models
    selected_model = st.selectbox("Model", model_options)

    # --- Unreviewed only toggle ---
    unreviewed_only = st.checkbox("Unreviewed Only", value=False)

    st.markdown("---")

    # --- Load/Refresh queue button ---
    if st.button("Load Trades", type="primary", use_container_width=True):
        with st.spinner("Loading trades with metrics..."):
            try:
                trades = training_db.fetch_trades_with_metrics(
                    date_from=date_from,
                    date_to=date_to,
                    ticker=selected_ticker if selected_ticker != "All" else None,
                    model=selected_model if selected_model != "All" else None,
                    unreviewed_only=unreviewed_only,
                    limit=500,
                )

                if trades:
                    # Shuffle to prevent temporal memory leakage
                    random.shuffle(trades)
                    st.session_state.review_queue = trades
                    st.session_state.current_trade_index = 0
                    st.session_state.queue_loaded = True
                    st.session_state.last_filters = {
                        'date_from': date_from,
                        'date_to': date_to,
                        'ticker': selected_ticker,
                        'model': selected_model,
                        'unreviewed_only': unreviewed_only,
                    }
                    reset_flashcard_state()
                    st.success(f"Loaded {len(trades)} trades")
                else:
                    st.warning("No trades found matching filters")
                    st.session_state.review_queue = []
                    st.session_state.queue_loaded = False
            except Exception as e:
                st.error(f"Error loading trades: {e}")

    # --- Queue info ---
    if st.session_state.queue_loaded and st.session_state.review_queue:
        st.markdown("---")
        queue = st.session_state.review_queue
        current_idx = st.session_state.current_trade_index

        # Progress
        st.metric("Queue Size", len(queue))
        reviewed = min(current_idx, len(queue))
        st.progress(reviewed / len(queue) if queue else 0)
        st.caption(f"{reviewed} of {len(queue)} reviewed this session")

        # Shuffle button
        if st.button("Shuffle", use_container_width=True):
            random.shuffle(st.session_state.review_queue)
            st.session_state.current_trade_index = 0
            reset_flashcard_state()
            st.rerun()

        # Jump to trade
        st.markdown("**Jump to Trade**")
        jump_input = st.number_input(
            "Trade #",
            min_value=1,
            max_value=len(queue),
            value=min(current_idx + 1, len(queue)),
            step=1,
            key="jump_to_trade",
            label_visibility="collapsed",
        )
        if st.button("Go", key="btn_jump", use_container_width=True):
            new_idx = int(jump_input) - 1
            if new_idx != st.session_state.current_trade_index:
                st.session_state.current_trade_index = new_idx
                reset_flashcard_state()
                st.rerun()

    # Footer
    st.markdown("---")
    st.markdown("*XIII Trading LLC*")
    st.caption(f"*{datetime.now().strftime('%Y-%m-%d %H:%M')}*")


# =============================================================================
# MAIN CONTENT
# =============================================================================

if not st.session_state.queue_loaded:
    # Welcome screen
    st.title("Epoch Journal — Flashcard Training")

    st.markdown("""
    ### Welcome to the Journal Training System

    This system helps you develop intuition for trade evaluation
    through deliberate practice with your own journal trades.

    **How it works:**
    1. **Load trades** using the sidebar filters
    2. **Pre-Trade view** — See the setup at the right edge (before outcome)
    3. **Post-Trade view** — Toggle to see the full trade with MFE/MAE/Exit
    4. **Review** — Record observations using the 14-point review form
    5. **Next Trade** — Advance to the next flashcard

    **Pre-requisites:**
    1. Import trades: `python processor/import_trades.py`
    2. Populate M1 bars: `python processor/populator.py`
    3. Review trades: Set stop_price, model, zone via review page
    4. Run processors: `python processor/run_training_processors.py`

    **Key Features:**
    - Multi-timeframe charts (M1, H1, M15)
    - MFE/MAE markers with R-multiples in post-trade view
    - R-level crossing markers with health scores
    - M1 ramp-up chart with indicator overlay
    - Event indicators table (ENTRY, R1/R2/R3, MAE, MFE, EXIT)
    - 14-point review form with persistence

    ---
    **Get started:** Set your filters in the sidebar and click "Load Trades"
    """)

elif not st.session_state.review_queue:
    st.warning("No trades in queue. Adjust filters and click 'Load Trades'.")

else:
    queue = st.session_state.review_queue
    current_idx = st.session_state.current_trade_index

    # Check if we've completed all trades
    if current_idx >= len(queue):
        st.success("You've reviewed all trades in this queue!")

        st.markdown("### Session Complete")
        st.info(f"Reviewed {len(queue)} trades in this session.")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Start Over", use_container_width=True):
                st.session_state.current_trade_index = 0
                reset_flashcard_state()
                st.rerun()

        with col2:
            if st.button("Load New Queue", use_container_width=True):
                st.session_state.queue_loaded = False
                st.session_state.review_queue = []
                st.rerun()

    else:
        # Get current trade
        current_trade = queue[current_idx]

        # Trade counter header
        direction_str = str(current_trade.direction).upper() if current_trade.direction else ""
        pnl_r = current_trade.pnl_r
        pnl_str = f" | {pnl_r:+.2f}R" if pnl_r is not None and st.session_state.get('view_mode') == 'post_trade' else ""

        st.markdown(
            f"**Trade {current_idx + 1} of {len(queue)}** | "
            f"{current_trade.ticker} | {current_trade.date} | "
            f"{current_trade.model or ''} | {direction_str}{pnl_str}"
        )

        # Fetch bars (cached via BarCache)
        bar_data = cache.get_bars(
            ticker=current_trade.ticker,
            trade_date=current_trade.date,
            trade=current_trade.trade,
        )

        if bar_data is None:
            st.error(f"Failed to fetch bar data for {current_trade.ticker} on {current_trade.date}")
            st.info("Click to skip to the next trade.")

            if st.button("Skip Trade"):
                st.session_state.current_trade_index += 1
                st.rerun()
        else:
            # Get zones for this trade's ticker/date
            zones = journal_db.get_zones_for_ticker(
                ticker=current_trade.ticker,
                trade_date=current_trade.date,
            )

            # Render flashcard UI (handles evaluate/reveal flow)
            render_flashcard_ui(
                trade=current_trade,
                bar_data=bar_data,
                zones=zones,
                training_db=training_db,
                cache=cache,
            )

            # Prefetch upcoming trades
            if current_idx + 1 < len(queue):
                upcoming = queue[current_idx + 1 : current_idx + 1 + PREFETCH_COUNT]
                cache.prefetch_for_trades(upcoming)
