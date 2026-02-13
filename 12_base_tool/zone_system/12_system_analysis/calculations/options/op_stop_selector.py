"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Options Stop Type Selector
XIII Trading LLC
================================================================================

PURPOSE:
    Provides a stop type selector for the Options Analysis tab.
    Manages session state for selected stop type and outcomes.

    This bridges CALC-O09 (Stop Analysis) with CALC-O01 (Win Rate by Model)
    by allowing users to select which stop level to use for win/loss determination.

    IMPORTANT: Monte AI always uses the default stop type (25%) regardless of
    user selection, to ensure consistency and reproducibility.

USAGE:
    from calculations.options.op_stop_selector import (
        initialize_op_stop_type_state,
        render_op_stop_type_selector,
        get_selected_op_stop_outcomes,
        get_default_op_stop_outcomes,
        store_op_stop_analysis_results,
        get_op_stop_type_display_name,
        DEFAULT_OPTIONS_STOP_TYPE
    )

================================================================================
"""

import streamlit as st
from typing import Dict, List, Any, Optional

from .op_stop_analysis.stop_types import (
    OPTIONS_STOP_TYPES,
    DEFAULT_OPTIONS_STOP_TYPE,
    STOP_TYPE_ORDER,
    get_stop_type_display_name as _get_display_name
)


# =============================================================================
# SESSION STATE KEYS
# =============================================================================
SESSION_KEY_SELECTED_STOP = "op_selected_stop_type"
SESSION_KEY_STOP_RESULTS = "op_stop_analysis_results"
SESSION_KEY_STOP_OUTCOMES = "op_stop_outcomes_by_type"


# =============================================================================
# INITIALIZATION
# =============================================================================
def initialize_op_stop_type_state() -> None:
    """
    Initialize session state for options stop type selection.

    Should be called at the start of the Options Analysis tab.
    """
    if SESSION_KEY_SELECTED_STOP not in st.session_state:
        st.session_state[SESSION_KEY_SELECTED_STOP] = DEFAULT_OPTIONS_STOP_TYPE

    if SESSION_KEY_STOP_RESULTS not in st.session_state:
        st.session_state[SESSION_KEY_STOP_RESULTS] = None

    if SESSION_KEY_STOP_OUTCOMES not in st.session_state:
        st.session_state[SESSION_KEY_STOP_OUTCOMES] = {}


# =============================================================================
# STORE RESULTS
# =============================================================================
def store_op_stop_analysis_results(results: Dict[str, Any]) -> None:
    """
    Store options stop analysis results in session state.

    Parameters:
    -----------
    results : Dict
        Output from render_op_stop_analysis_section(), containing:
        - summary: DataFrame of aggregated results
        - results: Dict of outcomes by stop type
        - best_stop: Best performing stop type
        - total_trades: Number of trades analyzed
    """
    if results is None:
        return

    st.session_state[SESSION_KEY_STOP_RESULTS] = results

    # Extract outcomes by stop type for quick access
    outcomes_by_type = results.get('results', {})
    st.session_state[SESSION_KEY_STOP_OUTCOMES] = outcomes_by_type


# =============================================================================
# SELECTOR UI
# =============================================================================
def render_op_stop_type_selector() -> str:
    """
    Render the options stop type selector dropdown.

    Returns:
    --------
    str
        Selected stop type key (e.g., "stop_25pct")
    """
    st.markdown("---")
    st.markdown("### Stop Type Selection")

    col1, col2 = st.columns([1, 2])

    with col1:
        # Build options list
        options = []
        for stop_type in STOP_TYPE_ORDER:
            meta = OPTIONS_STOP_TYPES[stop_type]
            options.append({
                'key': stop_type,
                'display': f"{meta['display_name']} - {meta['description']}"
            })

        # Find current selection index
        current = st.session_state.get(SESSION_KEY_SELECTED_STOP, DEFAULT_OPTIONS_STOP_TYPE)
        try:
            current_idx = STOP_TYPE_ORDER.index(current)
        except ValueError:
            current_idx = STOP_TYPE_ORDER.index(DEFAULT_OPTIONS_STOP_TYPE)

        # Render selector
        selected_display = st.selectbox(
            "Stop Type for Win/Loss Calculation",
            options=[o['display'] for o in options],
            index=current_idx,
            key="op_stop_type_selector",
            help="Win = 1R target reached before this stop level is hit"
        )

        # Map back to key
        selected_key = None
        for opt in options:
            if opt['display'] == selected_display:
                selected_key = opt['key']
                break

        if selected_key is None:
            selected_key = DEFAULT_OPTIONS_STOP_TYPE

        # Update session state
        st.session_state[SESSION_KEY_SELECTED_STOP] = selected_key

    with col2:
        # Show info box with current selection
        meta = OPTIONS_STOP_TYPES[selected_key]
        st.info(
            f"**All metrics below use {meta['short_name']} stop type**\n\n"
            f"Win = 1R ({meta['loss_pct']:.0f}% gain) reached before stop hit\n\n"
            f"Loss = Stop hit ({meta['loss_pct']:.0f}% loss) before reaching 1R"
        )

    # Show summary stats for selected stop type if available
    results = st.session_state.get(SESSION_KEY_STOP_RESULTS)

    if results is not None:
        summary_df = results.get('summary')

        if summary_df is not None and not summary_df.empty:
            # Find the row for selected stop type
            if 'stop_type_key' in summary_df.columns:
                selected_row = summary_df[summary_df['stop_type_key'] == selected_key]

                if not selected_row.empty:
                    row = selected_row.iloc[0]

                    st.markdown("**Selected Stop Type Performance:**")
                    cols = st.columns(4)

                    with cols[0]:
                        st.metric("Trades", f"{row.get('n', 0):,}")
                    with cols[1]:
                        win_rate = row.get('Win Rate %', 0)
                        st.metric("Win Rate", f"{win_rate:.1f}%")
                    with cols[2]:
                        expectancy = row.get('Expectancy', 0)
                        st.metric("Expectancy", f"{expectancy:+.3f}R")
                    with cols[3]:
                        stop_hit = row.get('Stop Hit %', 0)
                        st.metric("Stop Hit %", f"{stop_hit:.1f}%")

    st.markdown("---")

    return selected_key


# =============================================================================
# GET SELECTED OUTCOMES
# =============================================================================
def get_selected_op_stop_outcomes() -> List[Dict[str, Any]]:
    """
    Get the outcomes for the currently selected options stop type.

    Returns:
    --------
    List[Dict]
        List of trade outcomes for the selected stop type.
        Each dict contains: trade_id, model, contract_type, outcome, r_achieved, etc.
    """
    selected = st.session_state.get(SESSION_KEY_SELECTED_STOP, DEFAULT_OPTIONS_STOP_TYPE)
    outcomes_by_type = st.session_state.get(SESSION_KEY_STOP_OUTCOMES, {})

    return outcomes_by_type.get(selected, [])


def get_default_op_stop_outcomes() -> List[Dict[str, Any]]:
    """
    Get outcomes for the DEFAULT stop type (25% stop).

    Used for Monte AI prompt generation to ensure consistency
    regardless of user's UI selection.

    Returns:
    --------
    List[Dict]
        List of trade outcomes for the default (25%) stop type.
    """
    outcomes_by_type = st.session_state.get(SESSION_KEY_STOP_OUTCOMES, {})
    return outcomes_by_type.get(DEFAULT_OPTIONS_STOP_TYPE, [])


def get_selected_op_stop_type() -> str:
    """
    Get the currently selected options stop type key.

    Returns:
    --------
    str
        Stop type key (e.g., "stop_25pct")
    """
    return st.session_state.get(SESSION_KEY_SELECTED_STOP, DEFAULT_OPTIONS_STOP_TYPE)


def get_op_stop_type_outcomes(stop_type: str) -> List[Dict[str, Any]]:
    """
    Get outcomes for a specific stop type.

    Parameters:
    -----------
    stop_type : str
        Stop type key (e.g., "stop_25pct", "stop_10pct")

    Returns:
    --------
    List[Dict]
        List of trade outcomes for the specified stop type.
    """
    outcomes_by_type = st.session_state.get(SESSION_KEY_STOP_OUTCOMES, {})
    return outcomes_by_type.get(stop_type, [])


# =============================================================================
# DISPLAY HELPERS
# =============================================================================
def get_op_stop_type_display_name(stop_type: str = None, short: bool = False) -> str:
    """
    Get display name for a stop type.

    Parameters:
    -----------
    stop_type : str, optional
        Stop type key. If None, uses currently selected.
    short : bool
        If True, return short name (e.g., "25%")

    Returns:
    --------
    str
        Display name for the stop type
    """
    if stop_type is None:
        stop_type = get_selected_op_stop_type()

    return _get_display_name(stop_type, short=short)


def get_op_stop_analysis_summary() -> Optional[Dict[str, Any]]:
    """
    Get the full stop analysis summary from session state.

    Returns:
    --------
    Dict or None
        The stored stop analysis results, or None if not available
    """
    return st.session_state.get(SESSION_KEY_STOP_RESULTS, None)


def has_op_stop_analysis_data() -> bool:
    """Check if options stop analysis data is available."""
    outcomes = st.session_state.get(SESSION_KEY_STOP_OUTCOMES, {})
    return bool(outcomes)


# =============================================================================
# EXPORT DEFAULT
# =============================================================================
# Re-export for convenience
DEFAULT_STOP_TYPE = DEFAULT_OPTIONS_STOP_TYPE
