"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Streamlit Application Entry Point
XIII Trading LLC
================================================================================

Main entry point for the Indicator Analysis Streamlit application.
Provides comprehensive analysis of trading indicators across entry models.

Run with: streamlit run app.py --server.port 8502

================================================================================
"""

import streamlit as st
import pandas as pd
from datetime import date
from decimal import Decimal
import logging


def convert_decimals_in_df(df: pd.DataFrame) -> pd.DataFrame:
    """Convert Decimal columns to float for Arrow serialization compatibility."""
    for col in df.columns:
        if df[col].dtype == object:
            # Check if column contains Decimals
            sample = df[col].dropna().head(1)
            if len(sample) > 0 and isinstance(sample.iloc[0], Decimal):
                df[col] = df[col].apply(lambda x: float(x) if isinstance(x, Decimal) else x)
    return df

from config import (
    STREAMLIT_CONFIG, CHART_CONFIG, ENTRY_MODELS,
    CONTINUATION_MODELS, REJECTION_MODELS, ANALYSIS_CONFIG,
    WIN_CONDITION_CONFIG
)
from data.supabase_client import get_client
from components.filters import render_filters, get_date_filter
from components.summary_cards import render_summary_cards, render_model_cards, render_indicator_card
from components.charts import (
    render_win_rate_chart, render_indicator_distribution,
    render_health_heatmap, render_indicator_by_event, render_comparison_chart
)
from analysis.trade_stats import (
    get_trade_statistics, get_stats_by_model,
    get_stats_by_direction, get_stats_by_exit_reason
)
from analysis.indicator_stats import (
    get_indicator_averages, get_indicator_stats_by_event,
    get_indicator_comparison_by_outcome
)
from analysis.model_comparison import (
    compare_continuation_vs_rejection,
    compare_primary_vs_secondary,
    get_indicator_comparison_by_trade_type
)
from components.prompt_generator import (
    generate_overview_prompt,
    generate_continuation_prompt,
    generate_rejection_prompt,
    generate_indicator_prompt,
    generate_health_prompt,
    render_analysis_prompt
)
# CALC-009: Stop Type Analysis (Foundation for downstream analysis)
from calculations.stop_analysis.ui_components import (
    render_stop_analysis_section,
    render_stop_analysis_section_simple,
    render_stop_analysis_from_supabase
)
from calculations.stop_analysis.stop_selector import (
    initialize_stop_type_state,
    render_stop_type_selector,
    store_stop_analysis_results,
    get_selected_stop_outcomes,
    get_stop_type_display_name,
    DEFAULT_STOP_TYPE
)

# CALC-001: Win Rate by Model (YOUR file - build step by step!)
from calculations.model.win_rate_by_model import (
    calculate_win_rate_by_model,
    render_model_summary_table,
    render_model_win_loss_chart,
    render_model_breakdown
)

# CALC-002: MFE/MAE Distribution Analysis (Percentage-based)
from calculations.trade_management.mfe_mae_stats import (
    calculate_mfe_mae_summary,
    calculate_mfe_mae_by_model,
    render_mfe_mae_summary_cards,
    render_mfe_histogram,
    render_mae_histogram,
    render_mfe_mae_scatter,
    render_model_mfe_mae_table
)

# CALC-003: MFE/MAE Sequence Analysis (Monte Carlo baseline)
from calculations.trade_management.mfe_mae_sequence import (
    calculate_sequence_summary,
    calculate_sequence_by_model,
    generate_monte_carlo_params,
    render_sequence_analysis_section
)

# CALC-004: Simulated Outcome Analysis (Stop/Target simulation)
from calculations.trade_management.simulated_outcomes import (
    calculate_simulated_stats,
    calculate_simulated_by_model,
    generate_stop_target_grid,
    find_optimal_parameters,
    render_simulated_outcomes_section
)

# Monte AI - Research Assistant for System Optimization
from monte_ai.ui import render_metrics_overview_monte_ai

# OPTIONS ANALYSIS IMPORTS
# CALC-O01 through CALC-O05: Options Analysis

# Options Stop Analysis (CALC-O09) - Foundation for downstream analysis
from calculations.options.op_stop_analysis import (
    render_op_stop_analysis_section
)
from calculations.options.op_stop_selector import (
    initialize_op_stop_type_state,
    render_op_stop_type_selector,
    store_op_stop_analysis_results,
    get_selected_op_stop_outcomes,
    get_default_op_stop_outcomes,
    get_op_stop_type_display_name,
    DEFAULT_OPTIONS_STOP_TYPE
)

# Options Win Rate by Model (CALC-O01) - Updated to use stop-based outcomes
from calculations.options.op_win_rate_by_model import (
    calculate_options_win_rate_by_model,
    render_options_model_summary_table,
    render_options_model_win_loss_chart,
    render_options_model_breakdown
)

# Options Simulated Outcomes (CALC-O05)
from calculations.options.op_simulated_outcomes import (
    render_simulated_outcomes_section as render_op_simulated_outcomes_section
)
from calculations.options.op_mfe_mae_stats import (
    calculate_options_mfe_mae_summary,
    calculate_options_mfe_mae_by_model,
    render_options_mfe_mae_summary_cards,
    render_options_mfe_histogram,
    render_options_mae_histogram,
    render_options_mfe_mae_scatter,
    render_options_model_mfe_mae_table,
    render_options_trade_management_analysis
)
from calculations.options.op_mfe_mae_sequence import (
    calculate_options_sequence_summary,
    calculate_options_sequence_by_model,
    generate_options_monte_carlo_params,
    render_options_sequence_analysis_section
)
from calculations.options.op_vs_underlying import (
    calculate_leverage_comparison,
    calculate_options_vs_underlying_summary,
    render_options_vs_underlying_section
)
from monte_ai.options_prompt_generator import (
    generate_options_overview_prompt,
    get_options_prompt_stats
)

# Indicator Refinement Analysis (Continuation/Rejection Scores) - DEPRECATED
from calculations.indicator_refinement import (
    render_indicator_refinement_section
)

# EPCH Indicators Edge Analysis (CALC-011) - Replaces Indicator Refinement
from calculations.epch_indicators import (
    render_epch_indicators_section
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# Page Configuration
# =============================================================================
st.set_page_config(
    page_title=STREAMLIT_CONFIG["page_title"],
    page_icon=STREAMLIT_CONFIG["page_icon"],
    layout=STREAMLIT_CONFIG["layout"]
)

# Custom CSS
st.markdown(f"""
<style>
    .main {{
        background-color: {CHART_CONFIG["background_color"]};
    }}
    .stMetric {{
        background-color: #2a2a4e;
        padding: 10px;
        border-radius: 5px;
    }}
    .stMetric label {{
        color: {CHART_CONFIG["text_muted"]};
    }}
    .stMetric .css-1wivap2 {{
        color: {CHART_CONFIG["text_color"]};
    }}
    .stTabs [data-baseweb="tab-list"] {{
        gap: 2px;
    }}
    .stTabs [data-baseweb="tab"] {{
        background-color: #2a2a4e;
        color: {CHART_CONFIG["text_color"]};
        padding: 10px 20px;
        border-radius: 5px 5px 0 0;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: #3a3a6e;
    }}
</style>
""", unsafe_allow_html=True)


# =============================================================================
# Data Loading
# =============================================================================
@st.cache_data(ttl=300)
def load_trades(date_from, date_to, models, directions, tickers):
    """Load trades from database with caching."""
    client = get_client()
    return client.fetch_trades(
        date_from=date_from,
        date_to=date_to,
        models=models,
        directions=directions,
        tickers=tickers
    )


@st.cache_data(ttl=300)
def load_optimal_trades(date_from, date_to, models, event_types):
    """Load optimal_trade data from database with caching."""
    client = get_client()
    return client.fetch_optimal_trades(
        date_from=date_from,
        date_to=date_to,
        models=models,
        event_types=event_types
    )


@st.cache_data(ttl=300)
def load_mfe_mae_potential(date_from, date_to, models):
    """
    Load MFE/MAE potential data from database with caching.

    This fetches POTENTIAL MFE/MAE (entry to 15:30 ET) from the
    mfe_mae_potential table, as opposed to REALIZED MFE/MAE
    (entry to exit) from the optimal_trade table.

    Returns data with mfe_r, mae_r column aliases for compatibility
    with mfe_mae_stats.py calculation functions.
    """
    client = get_client()
    return client.fetch_mfe_mae_potential(
        date_from=date_from,
        date_to=date_to,
        models=models
    )


@st.cache_data(ttl=300)
def load_trade_bars(date_from, date_to):
    """Load trade_bars data from database with caching."""
    client = get_client()
    return client.fetch_trade_bars(
        date_from=date_from,
        date_to=date_to
    )


@st.cache_data(ttl=300)
def load_m5_trade_bars_with_outcomes(date_from, date_to, models=None, directions=None):
    """Load m5_trade_bars with outcomes for CALC-007 progression analysis."""
    client = get_client()
    return client.fetch_m5_trade_bars_with_outcomes(
        date_from=date_from,
        date_to=date_to,
        models=models,
        directions=directions
    )


@st.cache_data(ttl=300)
def load_options_mfe_mae_potential(date_from, date_to, models=None, directions=None, contract_types=None):
    """
    Load OPTIONS MFE/MAE potential data from database with caching.

    This fetches options price movement data (entry to 15:30 ET) from the
    op_mfe_mae_potential table created by the op_mfe_mae module.
    """
    client = get_client()
    return client.fetch_op_mfe_mae_potential(
        date_from=date_from,
        date_to=date_to,
        models=models,
        directions=directions,
        contract_types=contract_types
    )


@st.cache_data(ttl=600)
def get_metadata():
    """Get available tickers, models, and date range."""
    client = get_client()
    return {
        "tickers": client.get_available_tickers(),
        "models": client.get_available_models(),
        "date_range": client.get_date_range(),
        "trade_count": client.get_trade_count()
    }


@st.cache_data(ttl=600)
def load_stop_analysis_data():
    """
    Load pre-calculated stop analysis data from Supabase with caching.

    This data is calculated once by the backtest processor and stored in
    the stop_analysis table. Loading from Supabase is fast and eliminates
    the need for Polygon API calls on each dashboard load.

    Returns:
        Tuple of (stop_analysis_records, record_count)
    """
    client = get_client()
    count = client.get_stop_analysis_count()
    if count == 0:
        return [], 0
    data = client.fetch_stop_analysis()
    return data, count


@st.cache_data(ttl=300)
def load_indicator_refinement(date_from, date_to, models=None, directions=None):
    """
    Load indicator refinement data (Continuation/Rejection scores) with caching.

    Returns:
        List of indicator refinement records
    """
    client = get_client()
    return client.fetch_indicator_refinement(
        date_from=date_from,
        date_to=date_to,
        models=models,
        directions=directions
    )


@st.cache_data(ttl=300)
def load_stop_outcomes_for_indicator_tab(
    stop_type: str,
    date_from,
    date_to,
    models=None,
    directions=None
):
    """
    Load stop analysis outcomes indexed by trade_id for the Indicator Analysis tab.

    This is used to compute is_winner for all indicator analysis calculations
    based on the selected stop type.

    Parameters:
        stop_type: Stop type key (e.g., 'zone_buffer')
        date_from: Start date
        date_to: End date
        models: Optional list of models to filter
        directions: Optional list of directions to filter

    Returns:
        Dict mapping trade_id to outcome info {is_winner, outcome, r_achieved}
    """
    client = get_client()
    return client.fetch_stop_outcomes_by_trade(
        stop_type=stop_type,
        date_from=date_from,
        date_to=date_to,
        models=models,
        directions=directions
    )


# =============================================================================
# Main Application
# =============================================================================
def main():
    st.title("Epoch Indicator Analysis")
    st.markdown("*Analyzing indicator performance across entry models*")

    # Load metadata
    metadata = get_metadata()

    if metadata["trade_count"] == 0:
        st.warning("No trades found in database. Please ensure data has been exported.")
        return

    # Sidebar filters
    date_range = metadata.get("date_range", {})
    date_from, date_to = get_date_filter(date_range)

    filters = render_filters(
        tickers=metadata.get("tickers", []),
        models=metadata.get("models", ["EPCH1", "EPCH2", "EPCH3", "EPCH4"])
    )

    # Apply outcome filter to direction if needed
    selected_models = filters.get("models", [])
    selected_directions = filters.get("directions")
    selected_tickers = filters.get("tickers")
    outcome_filter = filters.get("outcome", "All")

    # Load data
    with st.spinner("Loading data..."):
        trades = load_trades(
            date_from=date_from,
            date_to=date_to,
            models=selected_models,
            directions=selected_directions,
            tickers=selected_tickers
        )

        optimal_trades = load_optimal_trades(
            date_from=date_from,
            date_to=date_to,
            models=selected_models,
            event_types=ANALYSIS_CONFIG["event_types"]
        )

    # Apply outcome filter
    if outcome_filter == "Winners":
        trades = [t for t in trades if t.get("is_winner") or t.get("win") == 1]
        optimal_trades = [t for t in optimal_trades if t.get("win") == 1]
    elif outcome_filter == "Losers":
        trades = [t for t in trades if not t.get("is_winner") and t.get("win") != 1]
        optimal_trades = [t for t in optimal_trades if t.get("win") != 1]

    # Show data count
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Trades loaded:** {len(trades):,}")
    st.sidebar.markdown(f"**Optimal events:** {len(optimal_trades):,}")

    # Main content tabs
    tab_metrics, tab_options, tab_indicators, tab_epch, tab_archive = st.tabs([
        "Metrics Overview",
        "Options Analysis",
        "Indicator Analysis",
        "EPCH Indicators",
        "Archived Analysis"
    ])

    # ==========================================================================
    # Tab 1: Metrics Overview (Learning Sandbox)
    # ==========================================================================
    with tab_metrics:
        st.header("Metrics Overview")
        st.markdown("*Your analysis sandbox - build calculations here*")

        # Initialize stop type session state
        initialize_stop_type_state()

        # =================================================================
        # Load MFE/MAE potential data FIRST (used by multiple calculations)
        # =================================================================
        # This data is used for:
        # - Summary Cards: Overall stats (Win = MFE before MAE, Points)
        # - CALC-001: Win Rate by Model (now uses stop-based outcomes)
        # - CALC-002: MFE/MAE Distribution Analysis (raw market behavior)
        # - CALC-003: MFE/MAE Sequence Analysis
        # - CALC-004: Simulated Outcome Analysis
        with st.spinner("Loading trade analysis data..."):
            mfe_mae_potential_data = load_mfe_mae_potential(
                date_from=date_from,
                date_to=date_to,
                models=None  # No model filter - full system view
            )

        # Note: overall_stats still needed for Monte AI prompt (legacy support)
        overall_stats = get_trade_statistics(mfe_mae_potential_data)

        # =================================================================
        # CALC-009: Stop Type Analysis (FIRST ROW - Foundation Analysis)
        # =================================================================
        # Analyzes 6 different stop placement methods to determine which
        # provides the best risk-adjusted returns. This becomes the foundation
        # for all downstream indicator analysis.

        # Load trades with zone data for stop analysis (used as fallback)
        with st.spinner("Loading trade data..."):
            trades_with_zones = load_trades(
                date_from=date_from,
                date_to=date_to,
                models=None,
                directions=None,
                tickers=None
            )

        # Load pre-calculated stop analysis data (cached for 10 min)
        # This data was calculated by the backtest processor and stored in Supabase
        stop_analysis_preloaded = load_stop_analysis_data()

        # Render stop analysis from Supabase (pre-calculated, accurate data)
        # Falls back to simplified estimation if stop_analysis table is empty
        stop_analysis_results = render_stop_analysis_from_supabase(
            mfe_mae_data=mfe_mae_potential_data,
            trades_data=trades_with_zones,
            preloaded_data=stop_analysis_preloaded
        )

        # Store stop analysis results in session state for downstream use
        store_stop_analysis_results(stop_analysis_results)

        # =================================================================
        # STOP TYPE SELECTOR (Bridges CALC-009 and downstream analysis)
        # =================================================================
        # User selects which stop type to use for all metrics below.
        # Default: Zone + 5% Buffer (core thesis stop)
        # Monte AI prompt always uses default regardless of UI selection.
        selected_stop_type = render_stop_type_selector()
        selected_stop_name = get_stop_type_display_name(selected_stop_type, short=True)

        # Get outcomes for selected stop type
        selected_outcomes = get_selected_stop_outcomes()

        # =================================================================
        # CALC-001: Win Rate by Model (Using Selected Stop Type)
        # =================================================================
        # Win Condition: 1R profit reached before selected stop hit
        # This uses REALISTIC stop-based outcomes, not MFE/MAE timing

        # Render stop-based model breakdown
        model_stats = render_model_breakdown(selected_outcomes, selected_stop_name)

        st.markdown("---")

        # =================================================================
        # CALC-002: MFE/MAE Distribution Analysis (Raw Market Behavior)
        # =================================================================
        # This shows RAW MARKET BEHAVIOR - what's possible in the market,
        # NOT what happens with a specific stop. Independent of stop selection.
        st.subheader("MFE/MAE Distribution Analysis")
        st.caption("Raw price movement potential (independent of stop selection) | "
                   "Use this to understand what the market offers, not trading outcomes")

        # Calculate MFE/MAE summary stats (data already loaded above)
        mfe_mae_stats = calculate_mfe_mae_summary(mfe_mae_potential_data)

        # Display summary cards
        render_mfe_mae_summary_cards(mfe_mae_stats)

        st.markdown("---")

        # Histograms side by side
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**MFE Distribution (Profit Available to 15:30)**")
            render_mfe_histogram(mfe_mae_potential_data)

        with col2:
            st.markdown("**MAE Distribution (Heat Taken to 15:30)**")
            render_mae_histogram(mfe_mae_potential_data)

        st.markdown("---")

        # Scatter plot (full width)
        st.markdown("**MFE vs MAE Scatter (Above diagonal = favorable)**")
        render_mfe_mae_scatter(mfe_mae_potential_data)

        st.markdown("---")

        # Model breakdown table
        st.markdown("**MFE/MAE by Model and Direction**")
        render_model_mfe_mae_table(mfe_mae_potential_data)

        st.markdown("---")

        # =================================================================
        # CALC-003: MFE/MAE Sequence Analysis (Monte Carlo Baseline)
        # =================================================================
        # Analyzes WHEN MFE/MAE occur to establish probability of
        # favorable movement happening before adverse movement
        sequence_stats = render_sequence_analysis_section(mfe_mae_potential_data)

        st.markdown("---")

        # =================================================================
        # CALC-004: Simulated Outcome Analysis
        # =================================================================
        # Simulates trade outcomes at configurable stop/target levels
        # Provides validated win rates independent of exit data quality
        simulated_stats = render_simulated_outcomes_section(mfe_mae_potential_data)

        st.markdown("---")

        # =================================================================
        # Monte AI - Research Assistant
        # =================================================================
        # IMPORTANT: Monte AI prompt always uses DEFAULT stop type (Zone + 5% Buffer)
        # for consistency and reproducibility, regardless of UI selection above.

        # Info about Monte AI using default stop
        st.info(
            "**Monte AI Prompt Note:** The generated prompt always uses the default stop type "
            "(Zone + 5% Buffer) for consistency, regardless of your selection above. "
            "This ensures reproducible analysis across sessions."
        )

        # Calculate MFE/MAE by model for Monte AI prompt
        mfe_mae_by_model = calculate_mfe_mae_by_model(mfe_mae_potential_data)

        render_metrics_overview_monte_ai(
            model_stats=model_stats,
            overall_stats=overall_stats,
            filters={
                "date_from": date_from,
                "date_to": date_to,
                "models": selected_models,
                "directions": selected_directions,
                "tickers": selected_tickers,
                "outcome": outcome_filter
            },
            available_calculations=[
                "Stop Type Analysis: Foundation analysis comparing 6 stop placement methods",
                "CALC-001: Win Rate by Model (using selected stop type for UI, default for prompt)",
                "CALC-002: MFE/MAE Distribution Analysis (raw market behavior)",
                "CALC-003: MFE/MAE Sequence Analysis (Monte Carlo baseline - P(MFE First))",
                "CALC-004: Simulated Outcome Analysis (stop/target win rate simulation)"
            ],
            mfe_mae_stats=mfe_mae_stats,
            mfe_mae_by_model=mfe_mae_by_model,
            sequence_stats=sequence_stats,
            simulated_stats=simulated_stats,
            stop_analysis=stop_analysis_results
        )

        st.markdown("---")

        # =================================================================
        # YOUR CALCULATIONS GO BELOW THIS LINE
        # =================================================================

        st.subheader("My Custom Analysis")
        st.info("This is where you'll add your own calculations!")

        # Display available data for reference
        with st.expander("Available Data (for reference)"):
            st.markdown("**trades** - Your trade records")
            st.markdown(f"- Total records: {len(trades)}")
            if trades:
                st.markdown(f"- Columns: {list(trades[0].keys())}")

            st.markdown("---")
            st.markdown("**optimal_trades** - Indicator snapshots at events")
            st.markdown(f"- Total records: {len(optimal_trades)}")
            if optimal_trades:
                st.markdown(f"- Columns: {list(optimal_trades[0].keys())}")

    # ==========================================================================
    # Tab 2: Options Analysis (CALC-O01 through CALC-O05)
    # ==========================================================================
    with tab_options:
        st.header("Options Analysis")
        st.markdown("*Options trade performance from entry to 15:30 ET*")

        # Initialize options stop type session state
        initialize_op_stop_type_state()

        # Load options data
        with st.spinner("Loading options MFE/MAE data..."):
            options_data = load_options_mfe_mae_potential(
                date_from=date_from,
                date_to=date_to,
                models=None,  # Full system view
                directions=None,
                contract_types=None
            )

        if not options_data:
            st.warning("No options data available. Ensure the op_mfe_mae_potential table is populated.")
            st.info("""
            **To populate op_mfe_mae_potential table:**
            ```bash
            cd C:\\XIIITradingSystems\\Epoch\\02_zone_system\\09_backtest\\processor\\secondary_analysis\\op_mfe_mae
            python op_mfe_mae_runner.py --schema  # Create table first
            python op_mfe_mae_runner.py           # Full calculation
            ```
            """)
        else:
            st.sidebar.markdown(f"**Options trades:** {len(options_data):,}")

            # =================================================================
            # CALC-O09: Options Stop Type Analysis (Foundation)
            # =================================================================
            # Analyzes different stop levels to find best risk-adjusted returns
            # This is the foundation for downstream CALC-O01 analysis

            op_stop_analysis_results = render_op_stop_analysis_section(
                options_data=options_data
            )

            # Store results in session state for downstream use
            store_op_stop_analysis_results(op_stop_analysis_results)

            st.markdown("---")

            # =================================================================
            # OPTIONS STOP TYPE SELECTOR
            # =================================================================
            # Bridges CALC-O09 and CALC-O01
            # User selects which stop level to use for win/loss determination

            selected_stop_type = render_op_stop_type_selector()
            selected_stop_name = get_op_stop_type_display_name(selected_stop_type, short=True)

            # Get outcomes for selected stop type
            selected_outcomes = get_selected_op_stop_outcomes()

            st.markdown("---")

            # =================================================================
            # CALC-O01: Options Win Rate by Model (Using Stop-Based Outcomes)
            # =================================================================
            # Now uses stop-based outcomes instead of simple exit_pct > 0
            # Win = Target reached before selected stop hit

            if selected_outcomes:
                options_model_stats = render_options_model_breakdown(
                    selected_outcomes,
                    selected_stop_name
                )
            else:
                # Fallback to original if stop analysis not available
                st.warning("Stop analysis not available. Showing raw exit-based results.")
                st.subheader("Options Win Rate by Model")
                st.markdown("*Win = Exit% > 0 at 15:30 ET*")
                options_model_stats = calculate_options_win_rate_by_model(options_data)

                col1, col2 = st.columns([1, 1])
                with col1:
                    st.markdown("**Summary Table**")
                    render_options_model_summary_table(options_model_stats)
                with col2:
                    st.markdown("**Win/Loss Distribution**")
                    render_options_model_win_loss_chart(options_model_stats)

            st.markdown("---")

            # =================================================================
            # Options MFE/MAE Distribution
            # =================================================================
            st.subheader("Options MFE/MAE Distribution")
            st.markdown("*How much do options move from entry to 15:30 ET?*")

            # Calculate summary stats
            options_mfe_mae_stats = calculate_options_mfe_mae_summary(options_data)
            render_options_mfe_mae_summary_cards(options_mfe_mae_stats)

            st.markdown("---")

            # Histograms side by side
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Options MFE Distribution**")
                render_options_mfe_histogram(options_data)

            with col2:
                st.markdown("**Options MAE Distribution**")
                render_options_mae_histogram(options_data)

            st.markdown("---")

            # Scatter plot
            st.markdown("**Options MFE vs MAE (Above diagonal = favorable)**")
            render_options_mfe_mae_scatter(options_data)

            st.markdown("---")

            # Model breakdown
            st.markdown("**Options MFE/MAE by Model and Contract Type**")
            render_options_model_mfe_mae_table(options_data)

            st.markdown("---")

            # =================================================================
            # CALC-O03: Options MFE/MAE Sequence Analysis
            # =================================================================
            options_sequence_stats = render_options_sequence_analysis_section(options_data)

            st.markdown("---")

            # =================================================================
            # CALC-O05: Options Simulated Outcomes (Grid Search)
            # =================================================================
            simulated_results = render_op_simulated_outcomes_section(options_data)

            st.markdown("---")

            # =================================================================
            # CALC-O04: Options vs Underlying Comparison
            # =================================================================
            options_leverage_stats = render_options_vs_underlying_section(options_data)

            st.markdown("---")

            # =================================================================
            # Monte AI - Options Analysis (Updated with Stop Analysis)
            # =================================================================
            st.subheader("Monte AI - Options Analysis")
            st.markdown("*Copy the prompt below to analyze options performance with Claude*")

            # Note about default stop type
            st.info(
                "**Monte AI Prompt Note:** The generated prompt always uses the default stop type "
                "(25% Stop) for consistency, regardless of your selection above. "
                "This ensures reproducible analysis across sessions."
            )

            # Get model stats for default stop type (for prompt consistency)
            default_outcomes = get_default_op_stop_outcomes()
            default_model_stats = calculate_options_win_rate_by_model(default_outcomes) if default_outcomes else options_model_stats

            # Generate comprehensive prompt
            options_mfe_mae_by_model = calculate_options_mfe_mae_by_model(options_data)

            options_prompt = generate_options_overview_prompt(
                mfe_mae_stats=options_mfe_mae_stats,
                model_stats=default_model_stats,
                sequence_stats=options_sequence_stats,
                leverage_stats=options_leverage_stats,
                stop_analysis=op_stop_analysis_results,
                simulated_stats=simulated_results,
                filters={
                    "date_from": date_from,
                    "date_to": date_to,
                    "models": selected_models,
                    "directions": selected_directions
                },
                stop_name="25%"
            )

            # Show prompt stats
            prompt_stats = get_options_prompt_stats(options_prompt)
            st.caption(f"Prompt: {prompt_stats['characters']:,} chars, ~{prompt_stats['estimated_tokens']:,} tokens")

            # Expandable prompt
            with st.expander("View/Copy Options Analysis Prompt", expanded=False):
                st.text_area(
                    "Options Monte AI Prompt",
                    value=options_prompt,
                    height=500,
                    key="options_monte_ai_prompt_full"
                )
                st.markdown("*Copy the above prompt and paste into Claude for analysis*")

    # ==========================================================================
    # Tab 3: Indicator Analysis (CALC-005 through CALC-008)
    # ==========================================================================
    with tab_indicators:
        st.header("Indicator Analysis")
        st.markdown("*Entry indicator correlation with trade outcomes*")

        # =================================================================
        # STOP TYPE SELECTOR FOR INDICATOR ANALYSIS
        # =================================================================
        # Win condition is determined by selected stop type (default: Zone + 5% Buffer)
        # Uses the SAME data as Metrics Overview for consistency

        st.subheader("Win Condition")
        st.caption("Select stop type to determine win/loss classification for all analyses below")

        # Create columns for stop type selector
        col_stop1, col_stop2 = st.columns([2, 3])

        with col_stop1:
            stop_type_options = WIN_CONDITION_CONFIG["stop_type_order"]
            stop_type_names = WIN_CONDITION_CONFIG["stop_types"]

            indicator_stop_type = st.selectbox(
                "Stop Type",
                options=stop_type_options,
                format_func=lambda x: stop_type_names.get(x, x) + (" (Default)" if x == WIN_CONDITION_CONFIG["default_stop_type"] else ""),
                index=0,  # Zone + 5% Buffer is first in order
                key="indicator_analysis_stop_type"
            )

        with col_stop2:
            st.info(
                f"**Win Condition:** MFE ≥ 1R reached before stop hit\n\n"
                f"Using **{stop_type_names.get(indicator_stop_type, indicator_stop_type)}** for win/loss classification"
            )

        st.markdown("---")

        # Load entry indicators data
        @st.cache_data(ttl=300)
        def load_entry_indicators(_date_from, _date_to, _models, _directions, _tickers):
            client = get_client()
            return client.fetch_entry_indicators(
                date_from=_date_from,
                date_to=_date_to,
                models=_models,
                directions=_directions,
                tickers=_tickers
            )

        entry_data = load_entry_indicators(
            date_from,
            date_to,
            selected_models if selected_models else None,
            selected_directions if selected_directions else None,
            selected_tickers if selected_tickers else None
        )

        # =================================================================
        # USE SAME STOP ANALYSIS DATA AS METRICS OVERVIEW
        # =================================================================
        # Get stop outcomes from session state (loaded by Metrics Overview tab)
        # This ensures consistency between tabs when using the same stop type
        from calculations.stop_analysis.stop_selector import get_stop_type_outcomes, has_stop_analysis_data

        if has_stop_analysis_data():
            # Get outcomes for the selected stop type from session state
            indicator_stop_outcomes = get_stop_type_outcomes(indicator_stop_type)

            # Convert list of outcomes to dict indexed by trade_id for merging
            stop_outcomes_map = {}
            for outcome in indicator_stop_outcomes:
                trade_id = outcome.get('trade_id')
                if trade_id:
                    stop_outcomes_map[trade_id] = {
                        'is_winner': outcome.get('outcome') == 'WIN',
                        'outcome': outcome.get('outcome'),
                        'r_achieved': outcome.get('r_achieved', 0.0)
                    }
        else:
            stop_outcomes_map = {}

        # Check if stop analysis data is available
        if not stop_outcomes_map:
            st.warning("No stop analysis data available. Visit **Metrics Overview** tab first to load stop analysis data.")
            st.info("""
            **If stop_analysis table is not populated:**
            ```bash
            cd C:\\XIIITradingSystems\\Epoch\\02_zone_system\\09_backtest\\processor\\secondary_analysis\\stop_analysis
            python stop_analysis_runner.py
            ```
            """)

        if not entry_data:
            st.warning("No entry indicator data available. Run the entry_indicators population script first.")
            st.info("""
            **To populate entry_indicators table:**
            ```bash
            cd C:\\XIIITradingSystems\\Epoch\\02_zone_system\\12_indicator_analysis
            python -m calculations.indicator_analysis.entry_indicators.runner
            ```
            """)
        else:
            entry_df = convert_decimals_in_df(pd.DataFrame(entry_data))

            # =================================================================
            # MERGE STOP-BASED OUTCOMES INTO ENTRY DATA
            # =================================================================
            # Replace mfe_mae_potential is_winner with stop-based is_winner
            # This ensures all indicator analysis uses the same win condition

            if stop_outcomes_map:
                # Create is_winner column from stop analysis
                def get_stop_based_is_winner(row):
                    trade_id = row.get('trade_id')
                    if trade_id and trade_id in stop_outcomes_map:
                        return stop_outcomes_map[trade_id]['is_winner']
                    return None  # No stop data available for this trade

                entry_df['is_winner'] = entry_df.apply(get_stop_based_is_winner, axis=1)

                # Also add outcome and r_achieved for reference
                entry_df['stop_outcome'] = entry_df.apply(
                    lambda row: stop_outcomes_map.get(row.get('trade_id'), {}).get('outcome'),
                    axis=1
                )
                entry_df['r_achieved'] = entry_df.apply(
                    lambda row: stop_outcomes_map.get(row.get('trade_id'), {}).get('r_achieved'),
                    axis=1
                )

                # Count how many trades have stop data
                trades_with_stop = entry_df['is_winner'].notna().sum()
                total_trades = len(entry_df)
                st.caption(f"Trades with stop analysis: {trades_with_stop:,} / {total_trades:,}")

            else:
                st.warning("Stop analysis data not available. Win/loss classification may be incomplete.")

            # Sub-tabs for different analyses
            calc5, calc6, calc7, calc8 = st.tabs([
                "Health Correlation (005)",
                "Factor Importance (006)",
                "Progression (007)",
                "Rejection Dynamics (008)"
            ])

            with calc5:
                if len(entry_df) > 0:
                    from calculations.indicator_analysis import render_calc_005_section
                    calc_005_result = render_calc_005_section(entry_df)
                    if calc_005_result:
                        st.session_state['calc_005_result'] = calc_005_result
                else:
                    st.subheader("CALC-005: Health Score -> Outcome Correlation")
                    st.markdown("*Does higher Health Score predict higher win rate?*")
                    st.warning("No entry indicator data available for CALC-005 analysis")

            with calc6:
                if len(entry_df) > 0:
                    from calculations.indicator_analysis import render_calc_006_section
                    calc_006_result = render_calc_006_section(entry_df)
                    if calc_006_result:
                        st.session_state['calc_006_result'] = calc_006_result
                else:
                    st.subheader("CALC-006: Individual Indicator Predictiveness")
                    st.markdown("*Which of the 10 factors actually matter?*")
                    st.warning("No entry indicator data available for CALC-006 analysis")

            with calc7:
                st.subheader("CALC-007: Indicator Progression Analysis")
                st.markdown("*What changes between entry and outcome?*")

                # Load m5_trade_bars with outcomes
                with st.spinner("Loading M5 trade bars data..."):
                    m5_trade_bars_data = load_m5_trade_bars_with_outcomes(
                        date_from=date_from,
                        date_to=date_to,
                        models=selected_models if selected_models else None,
                        directions=selected_directions if selected_directions else None
                    )

                if m5_trade_bars_data:
                    from calculations.indicator_analysis import render_calc_007_section
                    m5_df = convert_decimals_in_df(pd.DataFrame(m5_trade_bars_data))

                    # Show data stats
                    st.caption(f"Loaded {len(m5_df):,} bars from {m5_df['trade_id'].nunique():,} trades")

                    calc_007_result = render_calc_007_section(m5_df)
                    if calc_007_result:
                        st.session_state['calc_007_result'] = calc_007_result
                else:
                    st.warning("No m5_trade_bars data available for CALC-007 analysis")
                    st.info("""
                    **Data Source:** m5_trade_bars table

                    This analysis requires the m5_trade_bars table to be populated.
                    Run the populator from:
                    `02_zone_system/09_backtest/processor/secondary_analysis/m5_trade_bars/`

                    ```bash
                    python runner.py  # Full batch run
                    ```
                    """)

            with calc8:
                st.subheader("CALC-008: Rejection Dynamics Analysis")
                st.markdown("*Do rejection trades require different indicators?*")

                if len(entry_df) > 0:
                    # Load MFE/MAE potential data for time-to-MFE analysis
                    with st.spinner("Loading MFE/MAE potential data..."):
                        mfe_mae_data = load_mfe_mae_potential(
                            date_from=date_from,
                            date_to=date_to,
                            models=selected_models if selected_models else None
                        )

                    if mfe_mae_data:
                        from calculations.indicator_analysis import render_calc_008_section
                        mfe_mae_df = convert_decimals_in_df(pd.DataFrame(mfe_mae_data))

                        calc_008_result = render_calc_008_section(entry_df, mfe_mae_df)
                        if calc_008_result:
                            st.session_state['calc_008_result'] = calc_008_result
                    else:
                        st.warning("No MFE/MAE potential data available for CALC-008 analysis")
                        st.info("""
                        **Data Source:** mfe_mae_potential table

                        This analysis requires the mfe_mae_potential table to be populated.
                        Run the calculator from:
                        `02_zone_system/09_backtest/processor/secondary_analysis/mfe_mae/`

                        ```bash
                        python mfe_mae_potential_runner.py
                        ```
                        """)
                else:
                    st.warning("No entry indicator data available for CALC-008 analysis")

            # Monte AI Section at bottom
            st.divider()
            from monte_ai import render_indicator_analysis_monte_ai

            # Get results from session state
            calc_005 = st.session_state.get('calc_005_result', None)
            calc_006 = st.session_state.get('calc_006_result', None)
            calc_007 = st.session_state.get('calc_007_result', None)
            calc_008 = st.session_state.get('calc_008_result', None)

            render_indicator_analysis_monte_ai(
                calc_005_result=calc_005,
                calc_006_result=calc_006,
                calc_007_result=calc_007,
                calc_008_result=calc_008
            )

    # ==========================================================================
    # Tab 4: EPCH Indicators Edge Analysis (CALC-011)
    # ==========================================================================
    with tab_epch:
        # Render the EPCH indicators edge analysis section
        # This analyzes which EPCH v1.0 indicators correlate with higher win rates
        epch_result = render_epch_indicators_section(
            date_from=date_from,
            date_to=date_to
        )

        # Store result for potential downstream use
        if epch_result:
            st.session_state['epch_indicators_result'] = epch_result

    # ==========================================================================
    # Tab 5: Archived Analysis (Original Functionality)
    # ==========================================================================
    with tab_archive:
        st.header("Archived Analysis")
        st.markdown("*Original tabs preserved for reference*")

        # Create sub-tabs for archived content
        arch_overview, arch_cont, arch_rej, arch_ind, arch_health, arch_data = st.tabs([
            "Overview", "Continuation", "Rejection", "Indicators", "Health", "Data"
        ])

        # --- ARCHIVED: Overview ---
        with arch_overview:
            st.subheader("Performance Overview")

            # Summary cards
            arch_overall_stats = get_trade_statistics(trades)
            render_summary_cards(arch_overall_stats)

            st.markdown("---")

            # Model comparison
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Win Rate by Model")
                model_stats = get_stats_by_model(trades)
                render_win_rate_chart(model_stats)

            with col2:
                st.subheader("Continuation vs Rejection")
                comparison = compare_continuation_vs_rejection(trades)
                if comparison:
                    render_comparison_chart(
                        comparison.get("continuation", {}),
                        comparison.get("rejection", {})
                    )

            st.markdown("---")

            # Model cards
            st.subheader("Model Breakdown")
            render_model_cards(model_stats)

            # Claude Analysis Prompt
            st.markdown("---")
            overview_prompt = generate_overview_prompt(
                date_from=date_from,
                date_to=date_to,
                models=selected_models,
                directions=selected_directions,
                tickers=selected_tickers,
                outcome=outcome_filter,
                overall_stats=arch_overall_stats,
                model_stats=model_stats,
                comparison=comparison
            )
            render_analysis_prompt(overview_prompt, "Claude Analysis Prompt - Overview")

        # --- ARCHIVED: Continuation ---
        with arch_cont:
            st.subheader("Continuation Trades (EPCH1 / EPCH3)")
            st.markdown("*Trades through the zone (continuation of momentum)*")

            cont_trades = [t for t in trades if t.get("model") in CONTINUATION_MODELS]
            cont_optimal = [t for t in optimal_trades if t.get("model") in CONTINUATION_MODELS]

            if not cont_trades:
                st.info("No continuation trades found with current filters")
            else:
                # Summary
                cont_stats = get_trade_statistics(cont_trades)
                render_summary_cards(cont_stats)

                st.markdown("---")

                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("By Direction")
                    direction_stats = get_stats_by_direction(cont_trades)
                    if direction_stats:
                        df_dir = convert_decimals_in_df(pd.DataFrame(direction_stats))
                        st.dataframe(df_dir, use_container_width=True)

                with col2:
                    st.subheader("By Exit Reason")
                    exit_stats = get_stats_by_exit_reason(cont_trades)
                    if exit_stats:
                        df_exit = convert_decimals_in_df(pd.DataFrame(exit_stats))
                        st.dataframe(df_exit, use_container_width=True)

                st.markdown("---")

                # Indicator averages at entry
                st.subheader("Indicator Values at Entry (Winners vs Losers)")
                entry_events = [t for t in cont_optimal if t.get("event_type") == "ENTRY"]
                cont_indicator_comparison = {}
                if entry_events:
                    cont_indicator_comparison = get_indicator_comparison_by_outcome(entry_events)
                    if cont_indicator_comparison:
                        indicators = ["vwap", "sma_spread", "sma_momentum", "vol_roc", "vol_delta", "cvd_slope"]
                        cols = st.columns(3)
                        for i, ind in enumerate(indicators):
                            if ind in cont_indicator_comparison.get("winners", {}) and ind in cont_indicator_comparison.get("losers", {}):
                                with cols[i % 3]:
                                    render_indicator_card(
                                        name=ind.upper().replace("_", " "),
                                        win_value=cont_indicator_comparison["winners"][ind],
                                        loss_value=cont_indicator_comparison["losers"][ind]
                                    )

                # Claude Analysis Prompt
                st.markdown("---")
                cont_prompt = generate_continuation_prompt(
                    date_from=date_from,
                    date_to=date_to,
                    models=selected_models,
                    directions=selected_directions,
                    tickers=selected_tickers,
                    outcome=outcome_filter,
                    stats=cont_stats,
                    indicator_comparison=cont_indicator_comparison,
                    direction_stats=direction_stats if direction_stats else {},
                    exit_stats=exit_stats if exit_stats else {}
                )
                render_analysis_prompt(cont_prompt, "Claude Analysis Prompt - Continuation")

        # --- ARCHIVED: Rejection ---
        with arch_rej:
            st.subheader("Rejection Trades (EPCH2 / EPCH4)")
            st.markdown("*Trades from the zone (rejection/reversal)*")

            rej_trades = [t for t in trades if t.get("model") in REJECTION_MODELS]
            rej_optimal = [t for t in optimal_trades if t.get("model") in REJECTION_MODELS]

            if not rej_trades:
                st.info("No rejection trades found with current filters")
            else:
                # Summary
                rej_stats = get_trade_statistics(rej_trades)
                render_summary_cards(rej_stats)

                st.markdown("---")

                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("By Direction")
                    direction_stats = get_stats_by_direction(rej_trades)
                    if direction_stats:
                        df_dir = convert_decimals_in_df(pd.DataFrame(direction_stats))
                        st.dataframe(df_dir, use_container_width=True)

                with col2:
                    st.subheader("By Exit Reason")
                    exit_stats = get_stats_by_exit_reason(rej_trades)
                    if exit_stats:
                        df_exit = convert_decimals_in_df(pd.DataFrame(exit_stats))
                        st.dataframe(df_exit, use_container_width=True)

                st.markdown("---")

                # Indicator averages at entry
                st.subheader("Indicator Values at Entry (Winners vs Losers)")
                entry_events = [t for t in rej_optimal if t.get("event_type") == "ENTRY"]
                rej_indicator_comparison = {}
                if entry_events:
                    rej_indicator_comparison = get_indicator_comparison_by_outcome(entry_events)
                    if rej_indicator_comparison:
                        indicators = ["vwap", "sma_spread", "sma_momentum", "vol_roc", "vol_delta", "cvd_slope"]
                        cols = st.columns(3)
                        for i, ind in enumerate(indicators):
                            if ind in rej_indicator_comparison.get("winners", {}) and ind in rej_indicator_comparison.get("losers", {}):
                                with cols[i % 3]:
                                    render_indicator_card(
                                        name=ind.upper().replace("_", " "),
                                        win_value=rej_indicator_comparison["winners"][ind],
                                        loss_value=rej_indicator_comparison["losers"][ind]
                                    )

                # Claude Analysis Prompt
                st.markdown("---")
                rej_prompt = generate_rejection_prompt(
                    date_from=date_from,
                    date_to=date_to,
                    models=selected_models,
                    directions=selected_directions,
                    tickers=selected_tickers,
                    outcome=outcome_filter,
                    stats=rej_stats,
                    indicator_comparison=rej_indicator_comparison,
                    direction_stats=direction_stats if direction_stats else {},
                    exit_stats=exit_stats if exit_stats else {}
                )
                render_analysis_prompt(rej_prompt, "Claude Analysis Prompt - Rejection")

        # --- ARCHIVED: Indicator Deep Dive ---
        with arch_ind:
            st.subheader("Indicator Deep Dive")

            if not optimal_trades:
                st.info("No optimal trade data found with current filters")
            else:
                # Indicator selector
                indicator_options = [
                    "health_score", "vwap", "sma9", "sma21", "sma_spread", "sma_momentum",
                    "vol_roc", "vol_delta", "cvd_slope",
                    "m5_structure", "m15_structure", "h1_structure", "h4_structure"
                ]

                selected_indicator = st.selectbox(
                    "Select Indicator",
                    options=indicator_options,
                    format_func=lambda x: x.upper().replace("_", " "),
                    key="arch_indicator_select"
                )

                st.markdown("---")

                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("Distribution by Outcome")
                    entry_events = [t for t in optimal_trades if t.get("event_type") == "ENTRY"]
                    render_indicator_distribution(
                        entry_events,
                        selected_indicator,
                        f"{selected_indicator.upper()} at Entry"
                    )

                with col2:
                    st.subheader("Value by Event Type")
                    event_stats = get_indicator_stats_by_event(optimal_trades, selected_indicator)
                    render_indicator_by_event(event_stats, selected_indicator)

                st.markdown("---")

                # Comparison: Continuation vs Rejection
                st.subheader("Continuation vs Rejection Comparison")
                trade_type_comparison = get_indicator_comparison_by_trade_type(optimal_trades, "ENTRY")

                if trade_type_comparison:
                    col1, col2 = st.columns(2)

                    with col1:
                        cont_avgs = trade_type_comparison.get("continuation", {})
                        if cont_avgs:
                            st.markdown("**Continuation (EPCH1/3)**")
                            for key, val in cont_avgs.items():
                                if isinstance(val, (int, float)):
                                    st.text(f"{key}: {val:.3f}")

                    with col2:
                        rej_avgs = trade_type_comparison.get("rejection", {})
                        if rej_avgs:
                            st.markdown("**Rejection (EPCH2/4)**")
                            for key, val in rej_avgs.items():
                                if isinstance(val, (int, float)):
                                    st.text(f"{key}: {val:.3f}")

                # Claude Analysis Prompt
                st.markdown("---")
                indicator_prompt = generate_indicator_prompt(
                    date_from=date_from,
                    date_to=date_to,
                    models=selected_models,
                    directions=selected_directions,
                    tickers=selected_tickers,
                    outcome=outcome_filter,
                    selected_indicator=selected_indicator,
                    event_stats=event_stats if event_stats else {},
                    trade_type_comparison=trade_type_comparison if trade_type_comparison else {}
                )
                render_analysis_prompt(indicator_prompt, f"Claude Analysis Prompt - {selected_indicator.upper()}")

        # --- ARCHIVED: Health Score ---
        with arch_health:
            st.subheader("Health Score Analysis")
            st.markdown("*10-factor health score combining all indicators*")

            if not optimal_trades:
                st.info("No optimal trade data found with current filters")
            else:
                entry_events = [t for t in optimal_trades if t.get("event_type") == "ENTRY"]

                if entry_events:
                    # Health score heatmap
                    st.subheader("Win Rate by Health Score and Model")
                    render_health_heatmap(entry_events)

                    st.markdown("---")

                    # Health score distribution
                    col1, col2 = st.columns(2)

                    with col1:
                        st.subheader("Health Score Distribution")
                        render_indicator_distribution(
                            entry_events,
                            "health_score",
                            "Health Score at Entry"
                        )

                    with col2:
                        st.subheader("Health Score Statistics")
                        df = convert_decimals_in_df(pd.DataFrame(entry_events))
                        if "health_score" in df.columns:
                            df["health_score"] = pd.to_numeric(df["health_score"], errors="coerce")

                            win_col = "win" if "win" in df.columns else None
                            if win_col:
                                winners = df[df[win_col] == 1]["health_score"]
                                losers = df[df[win_col] != 1]["health_score"]

                                stats_df = pd.DataFrame({
                                    "Metric": ["Mean", "Median", "Std Dev", "Min", "Max"],
                                    "Winners": [
                                        f"{winners.mean():.2f}",
                                        f"{winners.median():.2f}",
                                        f"{winners.std():.2f}",
                                        f"{winners.min():.0f}",
                                        f"{winners.max():.0f}"
                                    ],
                                    "Losers": [
                                        f"{losers.mean():.2f}",
                                        f"{losers.median():.2f}",
                                        f"{losers.std():.2f}",
                                        f"{losers.min():.0f}",
                                        f"{losers.max():.0f}"
                                    ]
                                })
                                st.dataframe(stats_df, use_container_width=True, hide_index=True)

                    st.markdown("---")

                    # Health score by threshold
                    st.subheader("Win Rate by Health Score Threshold")

                    threshold = st.slider("Health Score Threshold", 0, 10, 6, key="arch_health_threshold")

                    df = convert_decimals_in_df(pd.DataFrame(entry_events))
                    if "health_score" in df.columns and "win" in df.columns:
                        df["health_score"] = pd.to_numeric(df["health_score"], errors="coerce")

                        above = df[df["health_score"] >= threshold]
                        below = df[df["health_score"] < threshold]

                        above_wins = len(above[above["win"] == 1])
                        below_wins = len(below[below["win"] == 1])

                        above_wr = (above_wins / len(above) * 100) if len(above) > 0 else 0
                        below_wr = (below_wins / len(below) * 100) if len(below) > 0 else 0

                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric(
                                f"Health >= {threshold}",
                                f"{above_wr:.1f}%",
                                f"{len(above)} trades"
                            )
                        with col2:
                            st.metric(
                                f"Health < {threshold}",
                                f"{below_wr:.1f}%",
                                f"{len(below)} trades"
                            )

                        # Claude Analysis Prompt
                        st.markdown("---")

                        # Gather health stats for prompt
                        winners_df = df[df["win"] == 1]["health_score"]
                        losers_df = df[df["win"] != 1]["health_score"]

                        winner_stats = {
                            "mean": winners_df.mean() if len(winners_df) > 0 else 0,
                            "median": winners_df.median() if len(winners_df) > 0 else 0,
                            "std": winners_df.std() if len(winners_df) > 0 else 0,
                            "min": winners_df.min() if len(winners_df) > 0 else 0,
                            "max": winners_df.max() if len(winners_df) > 0 else 0
                        }

                        loser_stats = {
                            "mean": losers_df.mean() if len(losers_df) > 0 else 0,
                            "median": losers_df.median() if len(losers_df) > 0 else 0,
                            "std": losers_df.std() if len(losers_df) > 0 else 0,
                            "min": losers_df.min() if len(losers_df) > 0 else 0,
                            "max": losers_df.max() if len(losers_df) > 0 else 0
                        }

                        threshold_analysis = {
                            "threshold": threshold,
                            "above_count": len(above),
                            "above_win_rate": above_wr,
                            "below_count": len(below),
                            "below_win_rate": below_wr
                        }

                        health_prompt = generate_health_prompt(
                            date_from=date_from,
                            date_to=date_to,
                            models=selected_models,
                            directions=selected_directions,
                            tickers=selected_tickers,
                            outcome=outcome_filter,
                            winner_stats=winner_stats,
                            loser_stats=loser_stats,
                            threshold_analysis=threshold_analysis
                        )
                        render_analysis_prompt(health_prompt, "Claude Analysis Prompt - Health Score")

        # --- ARCHIVED: Raw Data ---
        with arch_data:
            st.subheader("Raw Data Explorer")

            data_type = st.radio(
                "Select data type",
                ["Trades", "Optimal Trade Events"],
                horizontal=True,
                key="arch_data_type"
            )

            if data_type == "Trades":
                if trades:
                    df = convert_decimals_in_df(pd.DataFrame(trades))
                    st.dataframe(df, use_container_width=True, height=600)
                    st.download_button(
                        "Download CSV",
                        df.to_csv(index=False),
                        "trades_export.csv",
                        "text/csv",
                        key="arch_trades_download"
                    )
                else:
                    st.info("No trades to display")

            else:
                if optimal_trades:
                    df = convert_decimals_in_df(pd.DataFrame(optimal_trades))
                    st.dataframe(df, use_container_width=True, height=600)
                    st.download_button(
                        "Download CSV",
                        df.to_csv(index=False),
                        "optimal_trades_export.csv",
                        "text/csv",
                        key="arch_optimal_download"
                    )
                else:
                    st.info("No optimal trade events to display")


if __name__ == "__main__":
    main()
