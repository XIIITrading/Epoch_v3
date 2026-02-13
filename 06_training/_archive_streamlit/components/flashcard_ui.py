"""
Epoch Trading System - Flashcard UI Component
Toggle between Pre-Trade and Post-Trade views for trade review.
"""

import streamlit as st
from datetime import datetime
from typing import Dict
import pandas as pd
import pytz

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import CHART_CONFIG
from models.trade import TradeWithMetrics, Zone, TradeReview
from data.supabase_client import SupabaseClient
from data.cache_manager import BarCache
from components.charts import build_review_chart
from components.stats_panel import render_stats_panel, render_event_indicators_table
from components.bookmap_viewer import render_bookmap_viewer
from components.dow_ai.ui import render_pre_trade_dow_ai, render_post_trade_dow_ai
from components.dow_ai.prediction_display import render_batch_prediction
from components.rampup_chart import render_rampup_chart

ET = pytz.timezone('America/New_York')


def render_flashcard_ui(
    trade: TradeWithMetrics,
    bars: Dict[str, pd.DataFrame],
    zones: list,
    supabase: SupabaseClient,
    cache: BarCache
):
    """
    Render the flashcard UI for a single trade.
    Toggle between Pre-Trade and Post-Trade views.

    Args:
        trade: TradeWithMetrics to review
        bars: Dict with sliced bar data for each timeframe
        zones: List of Zone objects
        supabase: Supabase client for database operations
        cache: Bar cache for prefetching
    """
    # Initialize state
    _init_flashcard_state()

    # Get current view mode
    view_mode = st.session_state.view_mode

    # Render toggle
    _render_view_toggle()

    if view_mode == 'pre_trade':
        _render_pre_trade_view(trade, bars, zones, cache, supabase)
    elif view_mode == 'post_trade':
        _render_post_trade_view(trade, bars, zones, supabase, cache)


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
                "📊 Pre-Trade",
                key="btn_pre_trade",
                use_container_width=True,
                type="primary" if view_mode == 'pre_trade' else "secondary"
            ):
                st.session_state.view_mode = 'pre_trade'
                st.rerun()

        with toggle_col2:
            if st.button(
                "📈 Post-Trade",
                key="btn_post_trade",
                use_container_width=True,
                type="primary" if view_mode == 'post_trade' else "secondary"
            ):
                st.session_state.view_mode = 'post_trade'
                st.rerun()

    st.markdown("---")


def _render_pre_trade_view(
    trade: TradeWithMetrics,
    bars: Dict[str, pd.DataFrame],
    zones: list,
    cache: BarCache,
    supabase: SupabaseClient = None
):
    """Render the pre-trade view (right-edge, before outcome)."""
    # Fetch AI prediction for inline header display
    ai_prediction = None
    if supabase:
        try:
            ai_prediction = supabase.fetch_ai_prediction(trade.trade_id)
        except Exception:
            pass

    # Trade info panel at TOP (before chart) - with AI prediction inline
    _render_trade_info(trade, ai_prediction=ai_prediction)

    # Slice bars to entry time only
    if trade.entry_time:
        entry_dt = datetime.combine(trade.date, trade.entry_time)
        sliced_bars = cache.slice_bars_to_time(
            cache.get_bars_for_trade(trade.ticker, trade.date),
            end_time=entry_dt,
            include_end=True
        )
    else:
        sliced_bars = bars

    # Build and display chart
    fig = build_review_chart(
        bars=sliced_bars,
        trade=trade,
        zones=zones,
        mode='evaluate',
        show_mfe_mae=False
    )

    st.plotly_chart(fig, use_container_width=True, key='pre_trade_chart')

    # M1 Ramp-Up Chart (below main chart)
    if trade.entry_time:
        try:
            rampup_fig = render_rampup_chart(
                ticker=trade.ticker,
                trade_date=trade.date,
                entry_time=trade.entry_time,
                direction=trade.direction
            )
            if rampup_fig:
                st.plotly_chart(rampup_fig, use_container_width=True, key='rampup_chart')
        except Exception as e:
            st.caption(f"M1 ramp-up chart unavailable: {e}")

    # Entry indicators table (only ENTRY column in pre-trade view)
    st.markdown("---")
    events = None
    if supabase:
        events = supabase.fetch_optimal_trade_events(trade.trade_id)
        render_event_indicators_table(events, trade, show_all_events=False)

    # AI Prediction detail - only show if prediction exists
    if ai_prediction:
        st.markdown("---")
        try:
            with st.expander("DOW AI Prediction Detail", expanded=True):
                render_batch_prediction(trade.trade_id, supabase)
        except Exception as e:
            st.warning(f"DOW AI section unavailable: {e}")


def _render_trade_info(trade: TradeWithMetrics, ai_prediction: dict = None):
    """Render trade info panel with compact 20px styling and inline AI prediction."""
    col1, col2, col3, col4, col5 = st.columns(5)

    # 20px font styling for compact display
    label_style = "font-size:12px;color:#888;margin-bottom:2px;"
    value_style = "font-size:20px;font-weight:bold;color:#fff;"

    with col1:
        st.markdown(
            f"<div style='{label_style}'>Model</div>"
            f"<div style='{value_style}'>{trade.model or 'N/A'}</div>",
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"<div style='{label_style}'>Zone Type</div>"
            f"<div style='{value_style}'>{trade.zone_type or 'N/A'}</div>",
            unsafe_allow_html=True
        )

    with col3:
        zone_mid = trade.trade.zone_mid
        zone_value = f"${zone_mid:.2f}" if zone_mid else "N/A"
        st.markdown(
            f"<div style='{label_style}'>Zone POC</div>"
            f"<div style='{value_style}'>{zone_value}</div>",
            unsafe_allow_html=True
        )

    with col4:
        entry_value = f"${trade.entry_price:.2f}" if trade.entry_price else "N/A"
        st.markdown(
            f"<div style='{label_style}'>Entry</div>"
            f"<div style='{value_style}'>{entry_value}</div>",
            unsafe_allow_html=True
        )

    with col5:
        if ai_prediction:
            pred = ai_prediction.get('prediction', 'N/A')
            conf = ai_prediction.get('confidence', '')

            # Color for prediction
            if pred == 'TRADE':
                pred_color = '#4CAF50'
            elif pred == 'NO_TRADE':
                pred_color = '#FF5252'
            else:
                pred_color = '#888'

            # Color for confidence
            conf_colors = {'HIGH': '#4CAF50', 'MEDIUM': '#FFD700', 'LOW': '#FF9800'}
            conf_color = conf_colors.get(conf, '#888')

            st.markdown(
                f"<div style='{label_style}'>AI Prediction</div>"
                f"<div style='{value_style}'>"
                f"<span style='color:{pred_color};'>{pred}</span>"
                f" <span style='font-size:14px;color:{conf_color};'>({conf})</span>"
                f"</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"<div style='{label_style}'>AI Prediction</div>"
                f"<div style='{value_style};color:#555;'>--</div>",
                unsafe_allow_html=True
            )


def _render_post_trade_view(
    trade: TradeWithMetrics,
    bars: Dict[str, pd.DataFrame],
    zones: list,
    supabase: SupabaseClient,
    cache: BarCache = None
):
    """Render the post-trade view (full trade with outcome)."""
    # Fetch AI prediction for inline header display
    ai_prediction = None
    try:
        ai_prediction = supabase.fetch_ai_prediction(trade.trade_id)
    except Exception:
        pass

    # Trade info header with AI prediction inline
    _render_trade_info(trade, ai_prediction=ai_prediction)

    # Slice bars for post-trade view (entry through exit + buffer)
    if cache and trade.entry_time and trade.exit_time:
        bar_data = cache.get_bars_for_trade(trade.ticker, trade.date)
        if bar_data:
            entry_dt = datetime.combine(trade.date, trade.entry_time)
            exit_dt = datetime.combine(trade.date, trade.exit_time)
            reveal_bars = cache.slice_bars_for_reveal(
                bar_data=bar_data,
                entry_time=entry_dt,
                exit_time=exit_dt,
                context_bars=60,
                buffer_bars=10
            )
        else:
            reveal_bars = bars
    else:
        reveal_bars = bars

    # Build and display full chart
    fig = build_review_chart(
        bars=reveal_bars,
        trade=trade,
        zones=zones,
        mode='reveal',
        show_mfe_mae=True
    )

    st.plotly_chart(fig, use_container_width=True, key='post_trade_chart')

    # Stats panel
    render_stats_panel(trade)

    # Event indicators table (all 4 events: ENTRY, MAE, MFE, EXIT)
    st.markdown("---")
    events = supabase.fetch_optimal_trade_events(trade.trade_id)
    render_event_indicators_table(events, trade, show_all_events=True)

    # Bookmap viewer (if available)
    if trade.bookmap_url:
        render_bookmap_viewer(trade.bookmap_url)

    # Notes and review toggles
    st.markdown("---")

    # Load existing review if available
    _load_existing_review(trade.trade_id, supabase)

    # Multi-column review layout
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown("**Accuracy**")
        st.checkbox("Accuracy", key='accuracy')
        st.checkbox("Tape Confirm", key='tape_confirmation')

    with col2:
        st.markdown("**Quality**")
        st.checkbox("Good Trade", key='good_trade')
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
        default_idx = current_attempt if current_attempt and current_attempt <= 3 else 0
        selected = st.selectbox(
            "Attempt",
            options=attempt_options,
            index=default_idx,
            key='entry_attempt_select',
            label_visibility="collapsed"
        )
        # Convert selection to int or None
        st.session_state.entry_attempt = attempt_options.index(selected) if selected != "--" else None

    # Notes section
    st.text_area(
        "Notes:",
        key='trade_notes',
        height=80,
        placeholder="What did you learn from this trade?"
    )

    # Navigation buttons
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        if st.button(
            "Next Trade  ➡️",
            key="btn_next",
            use_container_width=True,
            type="primary"
        ):
            # Save review before advancing
            if _save_review(trade, supabase):
                st.toast("Review saved", icon="✅")
            else:
                st.toast("Failed to save review", icon="⚠️")
            # Advance to next trade
            _advance_to_next_trade()

    # Keyboard hint
    st.caption("Keyboard: **→** or **Space** = Next Trade")

    # DOW AI sections at the bottom, collapsed by default
    st.markdown("---")

    # AI Prediction detail (collapsed) - reuse prediction fetched for header
    if ai_prediction:
        with st.expander("DOW AI Prediction Detail", expanded=False):
            try:
                render_batch_prediction(trade.trade_id, supabase)
            except Exception as e:
                st.warning(f"AI Prediction unavailable: {e}")

    # DOW AI Post-Trade Review (collapsed)
    try:
        with st.expander("DOW AI Post-Trade Review", expanded=False):
            render_post_trade_dow_ai(
                trade=trade,
                events=events,
                supabase_client=supabase
            )
    except Exception as e:
        st.warning(f"DOW AI section unavailable: {e}")


def _advance_to_next_trade():
    """Advance to the next trade in the queue."""
    # Increment index
    if 'current_trade_index' in st.session_state:
        st.session_state.current_trade_index += 1

    # Reset flashcard state
    st.session_state.view_mode = 'pre_trade'

    # Clear review fields
    review_keys = [
        'trade_notes', 'accuracy', 'tape_confirmation',
        'good_trade', 'signal_aligned', 'confirmation_required',
        'prior_candle_stop', 'two_candle_stop', 'atr_stop', 'zone_edge_stop',
        'entry_attempt', 'entry_attempt_select', 'with_trend', 'counter_trend',
        'stopped_by_wick', '_review_loaded_for'
    ]
    for key in review_keys:
        if key in st.session_state:
            del st.session_state[key]

    st.rerun()


def _save_review(trade: TradeWithMetrics, supabase: SupabaseClient) -> bool:
    """
    Save trade review to database.

    Args:
        trade: Current trade being reviewed
        supabase: Database client

    Returns:
        True if saved successfully
    """
    # Determine actual outcome from trade
    if trade.is_winner:
        actual_outcome = 'winner'
    else:
        actual_outcome = 'loser'

    # Create review object from session state
    review = TradeReview(
        trade_id=trade.trade_id,
        actual_outcome=actual_outcome,
        notes=st.session_state.get('trade_notes', ''),
        # Accuracy & Confirmation
        accuracy=st.session_state.get('accuracy', False),
        tape_confirmation=st.session_state.get('tape_confirmation', False),
        # Trade Quality
        good_trade=st.session_state.get('good_trade', False),
        signal_aligned=st.session_state.get('signal_aligned', False),
        confirmation_required=st.session_state.get('confirmation_required', False),
        # Stop Placement
        prior_candle_stop=st.session_state.get('prior_candle_stop', False),
        two_candle_stop=st.session_state.get('two_candle_stop', False),
        atr_stop=st.session_state.get('atr_stop', False),
        zone_edge_stop=st.session_state.get('zone_edge_stop', False),
        # Entry Attempt
        entry_attempt=st.session_state.get('entry_attempt'),
        # Trade Context
        with_trend=st.session_state.get('with_trend', False),
        counter_trend=st.session_state.get('counter_trend', False),
        # Outcome Details
        stopped_by_wick=st.session_state.get('stopped_by_wick', False),
    )

    return supabase.upsert_review(review)


def _load_existing_review(trade_id: str, supabase: SupabaseClient):
    """
    Load existing review into session state if not already loaded.

    Args:
        trade_id: Trade ID to load review for
        supabase: Database client
    """
    # Check if we already loaded for this trade
    if st.session_state.get('_review_loaded_for') == trade_id:
        return

    # Fetch existing review
    review = supabase.fetch_review(trade_id)

    if review:
        # Populate session state with existing values
        st.session_state.trade_notes = review.notes or ''
        # Accuracy & Confirmation
        st.session_state.accuracy = review.accuracy
        st.session_state.tape_confirmation = review.tape_confirmation
        # Trade Quality
        st.session_state.good_trade = review.good_trade
        st.session_state.signal_aligned = review.signal_aligned
        st.session_state.confirmation_required = review.confirmation_required
        # Stop Placement
        st.session_state.prior_candle_stop = review.prior_candle_stop
        st.session_state.two_candle_stop = review.two_candle_stop
        st.session_state.atr_stop = review.atr_stop
        st.session_state.zone_edge_stop = review.zone_edge_stop
        # Entry Attempt
        st.session_state.entry_attempt = review.entry_attempt
        # Trade Context
        st.session_state.with_trend = review.with_trend
        st.session_state.counter_trend = review.counter_trend
        # Outcome Details
        st.session_state.stopped_by_wick = review.stopped_by_wick
    else:
        # Initialize with defaults if no existing review
        defaults = {
            'trade_notes': '',
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
