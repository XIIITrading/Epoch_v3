"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Stop Type Selector Component
XIII Trading LLC
================================================================================

PURPOSE:
    UI component for selecting which stop type to use for downstream calculations.
    Default: Zone + 5% Buffer

WORKFLOW CONTEXT:
    Phase 1: Stop Analysis (CALC-009) -> Find which stop types have edge
    Phase 2: Indicator Analysis -> Test if indicators improve winning stop types
    Phase 3: Vehicle Validation -> Confirm options don't destroy the edge

    The stop type selector bridges Phase 1 and Phase 2 by ensuring all indicator
    analysis uses REALISTIC win/loss definitions based on actual stop placement.

================================================================================
"""

import streamlit as st
from typing import Dict, List, Any, Optional


# =============================================================================
# STOP TYPE CONFIGURATION
# =============================================================================

# Stop type display names (full version for dropdown)
STOP_TYPE_DISPLAY_NAMES = {
    'zone_buffer': 'Zone + 5% Buffer (Default)',
    'prior_m1': 'Prior M1 H/L',
    'prior_m5': 'Prior M5 H/L',
    'm5_atr': 'M5 ATR (1.1x)',
    'm15_atr': 'M15 ATR (1.1x)',
    'fractal': 'M5 Fractal H/L'
}

# Short display names (for table headers, metrics, etc.)
STOP_TYPE_SHORT_NAMES = {
    'zone_buffer': 'Zone+5%',
    'prior_m1': 'Prior M1',
    'prior_m5': 'Prior M5',
    'm5_atr': 'M5 ATR',
    'm15_atr': 'M15 ATR',
    'fractal': 'Fractal'
}

# Default stop type - Zone + 5% Buffer
# Rationale:
# - Core thesis stop: Zone validity is the foundation of the trading system
# - Structural meaning: Stop hit = "zone failed to hold"
# - Consistent logic: Same calculation method across all trades
# - Aligned with backtest: Matches 09_backtest/models/entry_models.py exactly
DEFAULT_STOP_TYPE = 'zone_buffer'


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_stop_type_display_name(stop_type: str, short: bool = False) -> str:
    """
    Get display name for a stop type key.

    Parameters:
    -----------
    stop_type : str
        Stop type key (e.g., 'zone_buffer', 'prior_m1')
    short : bool
        If True, return short name for compact display

    Returns:
    --------
    str: Human-readable display name
    """
    if short:
        return STOP_TYPE_SHORT_NAMES.get(stop_type, stop_type)
    return STOP_TYPE_DISPLAY_NAMES.get(stop_type, stop_type)


def get_all_stop_types() -> List[str]:
    """Return list of all stop type keys in display order."""
    return list(STOP_TYPE_DISPLAY_NAMES.keys())


# =============================================================================
# SESSION STATE MANAGEMENT
# =============================================================================

def initialize_stop_type_state() -> None:
    """
    Initialize session state for stop type selection.

    Creates the following session state keys if they don't exist:
    - selected_stop_type: Currently selected stop type key
    - stop_analysis_results: Results dict from CALC-009 (by stop type)
    - stop_analysis_summary: Summary DataFrame from CALC-009
    """
    if 'selected_stop_type' not in st.session_state:
        st.session_state.selected_stop_type = DEFAULT_STOP_TYPE

    if 'stop_analysis_results' not in st.session_state:
        st.session_state.stop_analysis_results = None

    if 'stop_analysis_summary' not in st.session_state:
        st.session_state.stop_analysis_summary = None


def store_stop_analysis_results(analysis_results: Dict[str, Any]) -> None:
    """
    Store stop analysis results in session state after CALC-009 completes.

    Parameters:
    -----------
    analysis_results : Dict
        Full results from render_stop_analysis_section_simple()
        Contains: results (Dict), summary (DataFrame), best_stop (Dict), total_trades (int)
    """
    if analysis_results:
        st.session_state.stop_analysis_results = analysis_results.get('results', {})
        st.session_state.stop_analysis_summary = analysis_results.get('summary')


# =============================================================================
# UI COMPONENT
# =============================================================================

def render_stop_type_selector() -> str:
    """
    Render the stop type selector UI component.

    Displays:
    - Dropdown to select stop type
    - Info box explaining current selection
    - Performance metrics for selected stop type (if available)

    Returns:
    --------
    str: Selected stop type key
    """
    st.markdown("---")
    st.markdown("### Stop Type for Downstream Analysis")

    col1, col2 = st.columns([1, 2])

    with col1:
        # Get current selection index
        stop_types = get_all_stop_types()
        current_stop = st.session_state.get('selected_stop_type', DEFAULT_STOP_TYPE)

        try:
            current_index = stop_types.index(current_stop)
        except ValueError:
            current_index = 0

        # Render dropdown
        selected = st.selectbox(
            "Select Stop Type",
            options=stop_types,
            format_func=lambda x: STOP_TYPE_DISPLAY_NAMES.get(x, x),
            index=current_index,
            key='stop_type_selector_widget',
            help="All metrics below use this stop type for win/loss calculations"
        )

        # Update session state
        st.session_state.selected_stop_type = selected

    with col2:
        # Show info box with current selection
        display_name = get_stop_type_display_name(selected, short=True)
        st.info(
            f"**All metrics below use {display_name} stop type**\n\n"
            f"Win = 1R profit reached before stop hit\n\n"
            f"Loss = Stop hit before reaching 1R"
        )

    # Show summary stats for selected stop type if available
    summary_df = st.session_state.get('stop_analysis_summary')

    if summary_df is not None and not summary_df.empty:
        # Find the row for selected stop type
        if 'stop_type_key' in summary_df.columns:
            selected_row = summary_df[summary_df['stop_type_key'] == selected]
        else:
            # Try to match by Stop Type display name
            display_name_full = get_stop_type_display_name(selected, short=False).replace(' (Default)', '')
            selected_row = summary_df[summary_df['Stop Type'].str.contains(display_name_full.split(' (')[0], na=False)]

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
                avg_r = row.get('Avg R (All)', 0)
                st.metric("Avg R (All)", f"{avg_r:+.2f}R")

    st.markdown("---")

    return selected


# =============================================================================
# DATA ACCESS FUNCTIONS
# =============================================================================

def get_selected_stop_outcomes() -> List[Dict[str, Any]]:
    """
    Get outcomes for the currently selected stop type.

    Returns:
    --------
    List[Dict]: Outcome records for selected stop type
        Each record has: trade_id, model, direction, outcome, r_achieved
    """
    results = st.session_state.get('stop_analysis_results', {})
    selected = st.session_state.get('selected_stop_type', DEFAULT_STOP_TYPE)

    return results.get(selected, [])


def get_default_stop_outcomes() -> List[Dict[str, Any]]:
    """
    Get outcomes for the DEFAULT stop type (Zone + 5% Buffer).
    Used for Monte AI prompt generation to ensure consistency.

    Returns:
    --------
    List[Dict]: Outcome records for default stop type
    """
    results = st.session_state.get('stop_analysis_results', {})
    return results.get(DEFAULT_STOP_TYPE, [])


def get_stop_type_outcomes(stop_type: str) -> List[Dict[str, Any]]:
    """
    Get outcomes for a specific stop type.

    Parameters:
    -----------
    stop_type : str
        Stop type key (e.g., 'zone_buffer', 'prior_m1')

    Returns:
    --------
    List[Dict]: Outcome records for specified stop type
    """
    results = st.session_state.get('stop_analysis_results', {})
    return results.get(stop_type, [])


def has_stop_analysis_data() -> bool:
    """Check if stop analysis data is available."""
    results = st.session_state.get('stop_analysis_results', {})
    return bool(results)
