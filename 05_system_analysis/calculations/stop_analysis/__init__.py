"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Calculation: Stop Type Analysis (CALC-009)
XIII Trading LLC
================================================================================

PURPOSE:
    Analyze 6 different stop placement methods to determine which provides
    the best risk-adjusted returns. This calculation becomes the FOUNDATION
    for all downstream indicator analysis.

STOP TYPES:
    1. Zone Boundary + 5% Buffer - Stop beyond zone with buffer
    2. Prior M1 Bar High/Low - Tightest structural stop
    3. Prior M5 Bar High/Low - Short-term structure stop
    4. M5 ATR (1.1x) - Volatility-normalized, close-based
    5. M15 ATR (1.1x) - Wider volatility stop, close-based
    6. M5 Fractal High/Low - Market structure swing stop

USAGE:
    from calculations.stop_analysis import (
        calculate_stop_analysis,
        render_stop_analysis_section
    )

    # Calculate and render
    stop_stats = render_stop_analysis_section(
        mfe_mae_data=mfe_mae_potential_data,
        trades_data=trades_data,
        m5_bars_dict=m5_bars_dict,
        m1_bars_dict=m1_bars_dict
    )

================================================================================
"""

from .stop_calculator import (
    calculate_zone_buffer_stop,
    calculate_prior_m1_stop,
    calculate_prior_m5_stop,
    calculate_m5_atr_stop,
    calculate_m15_atr_stop,
    calculate_fractal_stop,
    calculate_all_stop_prices
)

from .atr_calculator import (
    calculate_true_range,
    calculate_atr_m5,
    calculate_atr_m15,
    aggregate_m5_to_m15
)

from .fractal_detector import (
    find_fractal_highs,
    find_fractal_lows,
    get_most_recent_fractal,
    calculate_fractal_stop_price
)

from .outcome_simulator import (
    simulate_outcome,
    check_price_based_stop,
    check_close_based_stop,
    find_stop_hit_time,
    simulate_all_outcomes
)

from .results_aggregator import (
    aggregate_by_stop_type,
    aggregate_by_model_type,
    aggregate_by_direction,
    aggregate_by_model_direction,
    find_best_stop_type
)

from .ui_components import (
    render_stop_analysis_section,
    render_stop_analysis_section_simple,
    render_stop_analysis_from_supabase,
    render_stop_summary_cards,
    render_stop_comparison_table,
    render_stop_charts
)

from .stop_selector import (
    STOP_TYPE_DISPLAY_NAMES,
    STOP_TYPE_SHORT_NAMES,
    DEFAULT_STOP_TYPE,
    get_stop_type_display_name,
    get_all_stop_types,
    initialize_stop_type_state,
    store_stop_analysis_results,
    render_stop_type_selector,
    get_selected_stop_outcomes,
    get_default_stop_outcomes,
    get_stop_type_outcomes,
    has_stop_analysis_data
)

__all__ = [
    # Stop calculation
    'calculate_zone_buffer_stop',
    'calculate_prior_m1_stop',
    'calculate_prior_m5_stop',
    'calculate_m5_atr_stop',
    'calculate_m15_atr_stop',
    'calculate_fractal_stop',
    'calculate_all_stop_prices',
    # ATR calculation
    'calculate_true_range',
    'calculate_atr_m5',
    'calculate_atr_m15',
    'aggregate_m5_to_m15',
    # Fractal detection
    'find_fractal_highs',
    'find_fractal_lows',
    'get_most_recent_fractal',
    'calculate_fractal_stop_price',
    # Outcome simulation
    'simulate_outcome',
    'check_price_based_stop',
    'check_close_based_stop',
    'find_stop_hit_time',
    'simulate_all_outcomes',
    # Results aggregation
    'aggregate_by_stop_type',
    'aggregate_by_model_type',
    'aggregate_by_direction',
    'aggregate_by_model_direction',
    'find_best_stop_type',
    # UI components
    'render_stop_analysis_section',
    'render_stop_analysis_section_simple',
    'render_stop_analysis_from_supabase',
    'render_stop_summary_cards',
    'render_stop_comparison_table',
    'render_stop_charts',
    # Stop type selector
    'STOP_TYPE_DISPLAY_NAMES',
    'STOP_TYPE_SHORT_NAMES',
    'DEFAULT_STOP_TYPE',
    'get_stop_type_display_name',
    'get_all_stop_types',
    'initialize_stop_type_state',
    'store_stop_analysis_results',
    'render_stop_type_selector',
    'get_selected_stop_outcomes',
    'get_default_stop_outcomes',
    'get_stop_type_outcomes',
    'has_stop_analysis_data',
]
