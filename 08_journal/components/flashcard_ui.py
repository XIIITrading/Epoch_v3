"""
Epoch Trading Journal - Flashcard UI Component
Toggle between Pre-Trade and Post-Trade views for trade review.

Adapted from 06_training/components/flashcard_ui.py.
Uses JournalTradeWithMetrics and JournalTrainingDB instead of
TradeWithMetrics and SupabaseClient.

Differences from 06_training:
    - No DOW AI prediction
    - No Bookmap viewer
    - Uses user-set stop_price for R-levels
    - M1 execution timeframe (not M5)
    - JournalTrainingDB for review persistence
    - BarCache uses BarData objects (not dict slices)
"""

import streamlit as st
from datetime import datetime
from typing import Dict, Optional
import pandas as pd
import pytz

from config import CHART_CONFIG
from core.training_models import JournalTradeWithMetrics
from data.training_db import JournalTrainingDB
from data.cache_manager import BarCache
from components.charts import build_journal_chart
from components.stats_panel import render_stats_panel, render_event_indicators_table
from components.rampup_chart import render_rampup_chart

ET = pytz.timezone('America/New_York')


def render_flashcard_ui(
    trade: JournalTradeWithMetrics,
    bar_data,
    zones: list,
    training_db: JournalTrainingDB,
    cache: BarCache,
):
    """
    Render the flashcard UI for a single trade.
    Toggle between Pre-Trade and Post-Trade views.

    Args:
        trade: JournalTradeWithMetrics to review
        bar_data: BarData object from cache (has .bars_1m, .bars_15m, .bars_1h)
        zones: List of zone dicts
        training_db: JournalTrainingDB for review persistence
        cache: Bar cache for bar slicing
    """
    # Initialize state
    _init_flashcard_state()

    # Get current view mode
    view_mode = st.session_state.view_mode

    # Render toggle
    _render_view_toggle()

    if view_mode == 'pre_trade':
        _render_pre_trade_view(trade, bar_data, zones, cache, training_db)
    elif view_mode == 'post_trade':
        _render_post_trade_view(trade, bar_data, zones, training_db, cache)


def _init_flashcard_state():
    """Initialize flashcard session state."""
    if 'view_mode' not in st.session_state:
        st.session_state.view_mode = 'pre_trade'


def _render_view_toggle():
    """Render the Pre-Trade / Post-Trade toggle."""
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        view_mode = st.session_state.view_mode
        toggle_col1, toggle_col2 = st.columns(2)

        with toggle_col1:
            if st.button(
                "Pre-Trade",
                key="btn_pre_trade",
                use_container_width=True,
                type="primary" if view_mode == 'pre_trade' else "secondary",
            ):
                st.session_state.view_mode = 'pre_trade'
                st.rerun()

        with toggle_col2:
            if st.button(
                "Post-Trade",
                key="btn_post_trade",
                use_container_width=True,
                type="primary" if view_mode == 'post_trade' else "secondary",
            ):
                st.session_state.view_mode = 'post_trade'
                st.rerun()

    st.markdown("---")


def _render_trade_info(trade: JournalTradeWithMetrics):
    """Render trade info panel with compact 20px styling."""
    col1, col2, col3, col4 = st.columns(4)

    label_style = "font-size:12px;color:#888;margin-bottom:2px;"
    value_style = "font-size:20px;font-weight:bold;color:#fff;"

    with col1:
        st.markdown(
            f"<div style='{label_style}'>Model</div>"
            f"<div style='{value_style}'>{trade.model or 'N/A'}</div>",
            unsafe_allow_html=True,
        )

    with col2:
        direction_str = str(trade.direction).upper() if trade.direction else "N/A"
        dir_color = "#00C853" if "LONG" in direction_str else "#FF1744" if "SHORT" in direction_str else "#fff"
        st.markdown(
            f"<div style='{label_style}'>Direction</div>"
            f"<div style='{value_style};color:{dir_color}'>{direction_str}</div>",
            unsafe_allow_html=True,
        )

    with col3:
        entry_value = f"${trade.entry_price:.2f}" if trade.entry_price else "N/A"
        st.markdown(
            f"<div style='{label_style}'>Entry</div>"
            f"<div style='{value_style}'>{entry_value}</div>",
            unsafe_allow_html=True,
        )

    with col4:
        health = trade.entry_health
        if health is not None:
            if health >= 8:
                h_color = "#00C853"
            elif health >= 6:
                h_color = "#FFC107"
            elif health >= 4:
                h_color = "#FF9800"
            else:
                h_color = "#FF1744"
            st.markdown(
                f"<div style='{label_style}'>Health at Entry</div>"
                f"<div style='{value_style};color:{h_color}'>{health}/10</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"<div style='{label_style}'>Health at Entry</div>"
                f"<div style='{value_style};color:#555'>--</div>",
                unsafe_allow_html=True,
            )


def _render_pre_trade_view(
    trade: JournalTradeWithMetrics,
    bar_data,
    zones: list,
    cache: BarCache,
    training_db: JournalTrainingDB,
):
    """Render the pre-trade view (right-edge, before outcome)."""
    # Trade info panel at TOP
    _render_trade_info(trade)

    # Slice bars to entry time
    if bar_data and trade.entry_time:
        sliced = cache.slice_bars_to_time(
            bar_data,
            end_time=trade.entry_time,
            include_end=True,
        )
        bars_1m = sliced.get('bars_1m', pd.DataFrame())
        bars_15m = sliced.get('bars_15m', pd.DataFrame())
        bars_1h = sliced.get('bars_1h', pd.DataFrame())
    elif bar_data:
        bars_1m = bar_data.bars_1m
        bars_15m = bar_data.bars_15m
        bars_1h = bar_data.bars_1h
    else:
        bars_1m = bars_15m = bars_1h = pd.DataFrame()

    # Build and display chart (evaluate mode — no exit, no R-levels, no MFE/MAE)
    fig = build_journal_chart(
        bars_1m=bars_1m,
        bars_15m=bars_15m,
        bars_1h=bars_1h,
        trade=trade.trade,
        zones=zones,
        mode='evaluate',
        show_mfe_mae=False,
        trade_metrics=None,
    )

    st.plotly_chart(fig, use_container_width=True, key='pre_trade_chart')

    # M1 Ramp-Up Chart (below main chart)
    if trade.entry_time and trade.ticker and trade.date:
        try:
            direction_str = str(trade.direction).upper() if trade.direction else 'LONG'
            rampup_fig = render_rampup_chart(
                ticker=trade.ticker,
                trade_date=trade.date,
                entry_time=trade.entry_time,
                direction=direction_str,
            )
            if rampup_fig:
                st.plotly_chart(rampup_fig, use_container_width=True, key='rampup_chart')
        except Exception as e:
            st.caption(f"M1 ramp-up chart unavailable: {e}")

    # Entry indicators table (only ENTRY column in pre-trade view)
    st.markdown("---")
    events = training_db.fetch_optimal_trade_events(trade.trade_id)
    render_event_indicators_table(events, trade, show_all_events=False)


def _render_post_trade_view(
    trade: JournalTradeWithMetrics,
    bar_data,
    zones: list,
    training_db: JournalTrainingDB,
    cache: BarCache,
):
    """Render the post-trade view (full trade with outcome)."""
    # Trade info header
    _render_trade_info(trade)

    # Slice bars for post-trade view (entry through exit + buffer)
    if bar_data and trade.entry_time and trade.exit_time:
        reveal = cache.slice_bars_for_reveal(
            bar_data=bar_data,
            entry_time=trade.entry_time,
            exit_time=trade.exit_time,
            context_bars=60,
            buffer_bars=10,
        )
        bars_1m = reveal.get('bars_1m', pd.DataFrame())
        bars_15m = reveal.get('bars_15m', pd.DataFrame())
        bars_1h = reveal.get('bars_1h', pd.DataFrame())
    elif bar_data:
        bars_1m = bar_data.bars_1m
        bars_15m = bar_data.bars_15m
        bars_1h = bar_data.bars_1h
    else:
        bars_1m = bars_15m = bars_1h = pd.DataFrame()

    # Build and display full chart with MFE/MAE
    fig = build_journal_chart(
        bars_1m=bars_1m,
        bars_15m=bars_15m,
        bars_1h=bars_1h,
        trade=trade.trade,
        zones=zones,
        mode='reveal',
        show_mfe_mae=True,
        trade_metrics=trade,
    )

    st.plotly_chart(fig, use_container_width=True, key='post_trade_chart')

    # Stats panel
    render_stats_panel(trade)

    # Event indicators table (all events: ENTRY, R1_CROSS, R2_CROSS, R3_CROSS, MAE, MFE, EXIT)
    st.markdown("---")
    events = training_db.fetch_optimal_trade_events(trade.trade_id)
    render_event_indicators_table(events, trade, show_all_events=True)

    # Review form
    st.markdown("---")

    # Load existing review if available
    _load_existing_review(trade.trade_id, training_db)

    # --- GOOD/BAD TRADE TOGGLE (prominent, top of review) ---
    gt_col1, gt_col2, gt_col3 = st.columns([1, 2, 1])
    with gt_col2:
        good_trade = st.toggle(
            "Good Trade",
            key='good_trade',
            help="Was this a good trade regardless of outcome? (Good process, good setup, good execution)",
        )

    st.markdown("---")

    # --- REVIEW CHECKBOXES ---
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown("**Accuracy**")
        st.checkbox("Accuracy", key='accuracy')
        st.checkbox("Tape Confirm", key='tape_confirmation')

    with col2:
        st.markdown("**Signal**")
        st.checkbox("Signal Aligned", key='signal_aligned')
        st.checkbox("Confirmation Req", key='confirmation_required')

    with col3:
        st.markdown("**Stop Placement**")
        st.checkbox("Prior Candle", key='prior_candle_stop')
        st.checkbox("Two Candle", key='two_candle_stop')
        st.checkbox("ATR Stop", key='atr_stop')
        st.checkbox("Zone Edge", key='zone_edge_stop')

    with col4:
        st.markdown("**Context**")
        st.checkbox("With Trend", key='with_trend')
        st.checkbox("Counter Trend", key='counter_trend')
        st.checkbox("Stopped by Wick", key='stopped_by_wick')

    with col5:
        st.markdown("**Entry Attempt**")
        attempt_options = ["--", "1st", "2nd", "3rd"]
        current_attempt = st.session_state.get('entry_attempt')
        default_idx = current_attempt if current_attempt and isinstance(current_attempt, int) and current_attempt <= 3 else 0
        selected = st.selectbox(
            "Attempt",
            options=attempt_options,
            index=default_idx,
            key='entry_attempt_select',
            label_visibility="collapsed",
        )
        st.session_state.entry_attempt = attempt_options.index(selected) if selected != "--" else None

    # --- JOURNAL NOTES (4 prompts matching Notion Section 10) ---
    st.markdown("---")
    st.markdown("### Journal Notes")

    notes_col1, notes_col2 = st.columns(2)
    with notes_col1:
        st.text_area(
            "What did I learn from this trade?",
            key='trade_notes',
            height=80,
            placeholder="Key takeaway from this trade...",
        )
        st.text_area(
            "Pattern recognition notes",
            key='notes_pattern',
            height=80,
            placeholder="What patterns do I see? How does this compare to other setups?",
        )

    with notes_col2:
        st.text_area(
            "What would I do differently?",
            key='notes_differently',
            height=80,
            placeholder="If I could take this trade again...",
        )
        st.text_area(
            "Additional observations",
            key='notes_observations',
            height=80,
            placeholder="Anything else worth noting...",
        )

    # Navigation buttons
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        if st.button(
            "Next Trade",
            key="btn_next",
            use_container_width=True,
            type="primary",
        ):
            # Save review before advancing
            if _save_review(trade, training_db):
                st.toast("Review saved", icon="✅")
            else:
                st.toast("Failed to save review", icon="⚠️")
            # Advance to next trade
            _advance_to_next_trade()


def _advance_to_next_trade():
    """Advance to the next trade in the queue."""
    if 'current_trade_index' in st.session_state:
        st.session_state.current_trade_index += 1

    # Reset flashcard state
    st.session_state.view_mode = 'pre_trade'

    # Clear review fields
    review_keys = [
        'trade_notes', 'notes_differently', 'notes_pattern', 'notes_observations',
        'accuracy', 'tape_confirmation',
        'good_trade', 'signal_aligned', 'confirmation_required',
        'prior_candle_stop', 'two_candle_stop', 'atr_stop', 'zone_edge_stop',
        'entry_attempt', 'entry_attempt_select', 'with_trend', 'counter_trend',
        'stopped_by_wick', '_review_loaded_for',
    ]
    for key in review_keys:
        if key in st.session_state:
            del st.session_state[key]

    st.rerun()


def _save_review(trade: JournalTradeWithMetrics, training_db: JournalTrainingDB) -> bool:
    """
    Save trade review to journal_trade_reviews table.

    Args:
        trade: Current trade being reviewed
        training_db: JournalTrainingDB client

    Returns:
        True if saved successfully
    """
    # Determine actual outcome
    if trade.is_winner_r:
        actual_outcome = 'winner'
    elif trade.pnl_r is not None and trade.pnl_r == 0:
        actual_outcome = 'breakeven'
    else:
        actual_outcome = 'loser'

    review_data = {
        'actual_outcome': actual_outcome,
        'notes': st.session_state.get('trade_notes', ''),
        'notes_differently': st.session_state.get('notes_differently', ''),
        'notes_pattern': st.session_state.get('notes_pattern', ''),
        'notes_observations': st.session_state.get('notes_observations', ''),
        'accuracy': st.session_state.get('accuracy', False),
        'tape_confirmation': st.session_state.get('tape_confirmation', False),
        'good_trade': st.session_state.get('good_trade', False),
        'signal_aligned': st.session_state.get('signal_aligned', False),
        'confirmation_required': st.session_state.get('confirmation_required', False),
        'prior_candle_stop': st.session_state.get('prior_candle_stop', False),
        'two_candle_stop': st.session_state.get('two_candle_stop', False),
        'atr_stop': st.session_state.get('atr_stop', False),
        'zone_edge_stop': st.session_state.get('zone_edge_stop', False),
        'entry_attempt': st.session_state.get('entry_attempt'),
        'with_trend': st.session_state.get('with_trend', False),
        'counter_trend': st.session_state.get('counter_trend', False),
        'stopped_by_wick': st.session_state.get('stopped_by_wick', False),
    }

    return training_db.upsert_review(trade.trade_id, review_data)


def _load_existing_review(trade_id: str, training_db: JournalTrainingDB):
    """
    Load existing review into session state if not already loaded.

    Args:
        trade_id: Trade ID to load review for
        training_db: JournalTrainingDB client
    """
    # Check if we already loaded for this trade
    if st.session_state.get('_review_loaded_for') == trade_id:
        return

    # Fetch existing review
    review = training_db.fetch_review(trade_id)

    if review:
        st.session_state.trade_notes = review.get('notes', '') or ''
        st.session_state.notes_differently = review.get('notes_differently', '') or ''
        st.session_state.notes_pattern = review.get('notes_pattern', '') or ''
        st.session_state.notes_observations = review.get('notes_observations', '') or ''
        st.session_state.accuracy = review.get('accuracy', False) or False
        st.session_state.tape_confirmation = review.get('tape_confirmation', False) or False
        st.session_state.good_trade = review.get('good_trade', False) or False
        st.session_state.signal_aligned = review.get('signal_aligned', False) or False
        st.session_state.confirmation_required = review.get('confirmation_required', False) or False
        st.session_state.prior_candle_stop = review.get('prior_candle_stop', False) or False
        st.session_state.two_candle_stop = review.get('two_candle_stop', False) or False
        st.session_state.atr_stop = review.get('atr_stop', False) or False
        st.session_state.zone_edge_stop = review.get('zone_edge_stop', False) or False
        st.session_state.entry_attempt = review.get('entry_attempt')
        st.session_state.with_trend = review.get('with_trend', False) or False
        st.session_state.counter_trend = review.get('counter_trend', False) or False
        st.session_state.stopped_by_wick = review.get('stopped_by_wick', False) or False
    else:
        # Initialize with defaults if no existing review
        defaults = {
            'trade_notes': '',
            'notes_differently': '',
            'notes_pattern': '',
            'notes_observations': '',
            'accuracy': False,
            'tape_confirmation': False,
            'good_trade': False,
            'signal_aligned': False,
            'confirmation_required': False,
            'prior_candle_stop': False,
            'two_candle_stop': False,
            'atr_stop': False,
            'zone_edge_stop': False,
            'entry_attempt': None,
            'with_trend': False,
            'counter_trend': False,
            'stopped_by_wick': False,
        }
        for key, default_val in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default_val

    # Mark as loaded for this trade
    st.session_state._review_loaded_for = trade_id


def reset_flashcard_state():
    """Reset flashcard state (call when changing queues)."""
    st.session_state.view_mode = 'pre_trade'
    # Clear review fields
    review_keys = [
        'trade_notes', 'notes_differently', 'notes_pattern', 'notes_observations',
        'accuracy', 'tape_confirmation',
        'good_trade', 'signal_aligned', 'confirmation_required',
        'prior_candle_stop', 'two_candle_stop', 'atr_stop', 'zone_edge_stop',
        'entry_attempt', 'entry_attempt_select', 'with_trend', 'counter_trend',
        'stopped_by_wick', '_review_loaded_for',
    ]
    for key in review_keys:
        if key in st.session_state:
            del st.session_state[key]
