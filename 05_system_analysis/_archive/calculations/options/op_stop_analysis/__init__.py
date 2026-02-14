"""
Options Stop Type Analysis (CALC-O09)

Analyzes different stop placement methods for options trades.
All stops are percentage-based from option entry price.

Stop Types:
- 10% Stop: Tight stop, highest stop-out rate
- 15% Stop: Tight stop with breathing room
- 20% Stop: Moderate stop level
- 25% Stop: Recommended default (balances protection vs premature exits)
- 30% Stop: Wider stop for volatile options
- 50% Stop: Very wide stop

Win Condition: Target (1R) reached before stop hit
- Target = same percentage as stop (e.g., 25% stop = 25% target)
- If neither hit by 15:30 ET, use exit_pct to determine outcome
"""

from .stop_types import (
    OPTIONS_STOP_TYPES,
    DEFAULT_OPTIONS_STOP_TYPE,
    STOP_TYPE_ORDER,
    get_stop_type_display_name,
    get_stop_loss_pct
)
from .stop_calculator import (
    calculate_option_stop_price,
    calculate_all_stop_prices,
    check_stop_hit,
    check_stop_hit_by_pct,
    calculate_stop_distance_pct
)
from .outcome_simulator import (
    simulate_single_trade,
    simulate_all_outcomes
)
from .results_aggregator import (
    aggregate_by_stop_type,
    aggregate_by_model_contract,
    find_best_stop_type
)
from .ui_components import (
    render_op_stop_analysis_section,
    render_op_stop_summary_cards,
    render_op_stop_comparison_table,
    render_op_stop_charts
)

__all__ = [
    # Stop Types
    'OPTIONS_STOP_TYPES',
    'DEFAULT_OPTIONS_STOP_TYPE',
    'STOP_TYPE_ORDER',
    'get_stop_type_display_name',
    'get_stop_loss_pct',
    # Calculator
    'calculate_option_stop_price',
    'calculate_all_stop_prices',
    'check_stop_hit',
    'check_stop_hit_by_pct',
    'calculate_stop_distance_pct',
    # Simulator
    'simulate_single_trade',
    'simulate_all_outcomes',
    # Aggregator
    'aggregate_by_stop_type',
    'aggregate_by_model_contract',
    'find_best_stop_type',
    # UI
    'render_op_stop_analysis_section',
    'render_op_stop_summary_cards',
    'render_op_stop_comparison_table',
    'render_op_stop_charts'
]
