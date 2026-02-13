"""
Epoch Trading System - Training Module
Flash Card Review System for Deliberate Practice

Main Streamlit application entry point.

Usage:
    streamlit run app.py

Author: XIII Trading LLC
Version: 1.0.0
"""

import streamlit as st
import random
from datetime import datetime

import sys
from pathlib import Path

# Add module directory to path
MODULE_DIR = Path(__file__).parent
sys.path.insert(0, str(MODULE_DIR))

from config import CHART_CONFIG
from data.supabase_client import get_supabase_client, SupabaseClient
from data.cache_manager import get_bar_cache, BarCache
from models.trade import TradeWithMetrics
from components.flashcard_ui import render_flashcard_ui, reset_flashcard_state
from components.navigation import (
    render_sidebar_filters,
    render_trade_counter,
    render_queue_info,
    render_shuffle_button,
    render_jump_to_trade
)


# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="Epoch Trade Review",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme
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
    /* Assessment button styling */
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
def get_clients():
    """Get database and cache clients."""
    supabase = get_supabase_client()
    cache = get_bar_cache()
    return supabase, cache


supabase, cache = get_clients()


# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    st.title("🎯 Epoch Review")
    st.caption("Flash Card Training System")
    st.markdown("---")

    # Filters
    filters = render_sidebar_filters(supabase)

    st.markdown("---")

    # Load/Refresh queue button
    if st.button("🔄 Load Trades", type="primary", use_container_width=True):
        with st.spinner("Loading trades..."):
            trades = supabase.fetch_trades_with_metrics(
                date_from=filters['date_from'],
                date_to=filters['date_to'],
                ticker=filters['ticker'],
                model=filters['model'],
                unreviewed_only=filters.get('unreviewed_only', False),
                ai_validated_only=filters.get('ai_validated_only', False),
                limit=500
            )

            if trades:
                # Shuffle to prevent temporal memory leakage
                random.shuffle(trades)
                st.session_state.review_queue = trades
                st.session_state.current_trade_index = 0
                st.session_state.queue_loaded = True
                st.session_state.last_filters = filters.copy()
                reset_flashcard_state()
                st.success(f"Loaded {len(trades)} trades")
            else:
                st.warning("No trades found matching filters")
                st.session_state.review_queue = []
                st.session_state.queue_loaded = False

    # Queue info
    if st.session_state.queue_loaded and st.session_state.review_queue:
        st.markdown("---")
        queue = st.session_state.review_queue
        current_idx = st.session_state.current_trade_index

        # Progress
        st.metric("Queue Size", len(queue))
        reviewed = current_idx
        st.progress(reviewed / len(queue) if queue else 0)
        st.caption(f"{reviewed} of {len(queue)} reviewed this session")

        # Shuffle button
        if render_shuffle_button():
            random.shuffle(st.session_state.review_queue)
            st.session_state.current_trade_index = 0
            reset_flashcard_state()
            st.rerun()

        # Jump to trade
        jump_idx = render_jump_to_trade(len(queue))
        if jump_idx is not None:
            st.session_state.current_trade_index = jump_idx
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
    st.title("Epoch Trade Review System")

    st.markdown("""
    ### Welcome to the Training Module

    This system helps you develop intuition for trade evaluation
    through deliberate practice with historical trades.

    **How it works:**
    1. **Load trades** using the sidebar filters
    2. **Pre-Trade view** - See the setup at the right edge (before outcome)
    3. **Post-Trade view** - Toggle to see the full trade with MFE/MAE/Exit
    4. **Toggle freely** - Go back and forth to study the setup vs outcome
    5. **Take notes** - Record your observations for future reference

    **Key Features:**
    - Multi-timeframe charts (H1, M15, M5)
    - MFE/MAE markers in post-trade view
    - Footprint analysis at entry
    - Bookmap snapshot integration (when available)

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
        render_trade_counter(current_idx, len(queue), current_trade)

        # Fetch bars (cached)
        bar_data = cache.get_bars_for_trade(
            ticker=current_trade.ticker,
            trade_date=current_trade.date,
            candle_count=CHART_CONFIG['candle_count']
        )

        if bar_data is None or not bar_data.is_valid:
            st.error(f"Failed to fetch bar data for {current_trade.ticker} on {current_trade.date}")
            st.info("Skipping to next trade...")

            if st.button("Skip Trade"):
                st.session_state.current_trade_index += 1
                st.rerun()
        else:
            # Get zones for this trade
            zones = supabase.fetch_zones_for_trade(
                ticker=current_trade.ticker,
                trade_date=current_trade.date
            )

            # Prepare bar dict for chart
            bars = {
                '5m': bar_data.bars_5m,
                '15m': bar_data.bars_15m,
                '1h': bar_data.bars_1h
            }

            # Render flashcard UI (handles evaluate/reveal flow)
            render_flashcard_ui(
                trade=current_trade,
                bars=bars,
                zones=zones,
                supabase=supabase,
                cache=cache
            )

            # Prefetch upcoming trades
            if current_idx + 1 < len(queue):
                upcoming = queue[current_idx + 1:current_idx + 4]
                cache.prefetch_for_trades(upcoming)
