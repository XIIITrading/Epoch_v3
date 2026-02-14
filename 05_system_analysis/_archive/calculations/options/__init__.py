"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Options Analysis Calculations
XIII Trading LLC
================================================================================

Calculation modules for Options Analysis tab.
Mirrors the structure of trade_management/ for underlying (share) analysis.

CALC-O01: Options Win Rate by Model
CALC-O02: Options MFE/MAE Distribution
CALC-O03: Options MFE/MAE Sequence (Timing)
CALC-O04: Options vs Underlying Comparison

================================================================================
"""

from .op_win_rate_by_model import (
    calculate_options_win_rate_by_model,
    render_options_model_summary_table,
    render_options_model_win_loss_chart,
    render_options_model_breakdown
)

from .op_mfe_mae_stats import (
    calculate_options_mfe_mae_summary,
    calculate_options_mfe_mae_by_model,
    render_options_mfe_mae_summary_cards,
    render_options_mfe_histogram,
    render_options_mae_histogram,
    render_options_mfe_mae_scatter,
    render_options_model_mfe_mae_table,
    render_options_trade_management_analysis
)

from .op_mfe_mae_sequence import (
    calculate_options_sequence_summary,
    calculate_options_sequence_by_model,
    generate_options_monte_carlo_params,
    render_options_sequence_analysis_section
)

from .op_vs_underlying import (
    calculate_leverage_comparison,
    calculate_options_vs_underlying_summary,
    render_leverage_comparison_chart,
    render_options_vs_underlying_scatter,
    render_options_vs_underlying_section
)

__all__ = [
    # CALC-O01
    'calculate_options_win_rate_by_model',
    'render_options_model_summary_table',
    'render_options_model_win_loss_chart',
    'render_options_model_breakdown',
    # CALC-O02
    'calculate_options_mfe_mae_summary',
    'calculate_options_mfe_mae_by_model',
    'render_options_mfe_mae_summary_cards',
    'render_options_mfe_histogram',
    'render_options_mae_histogram',
    'render_options_mfe_mae_scatter',
    'render_options_model_mfe_mae_table',
    'render_options_trade_management_analysis',
    # CALC-O03
    'calculate_options_sequence_summary',
    'calculate_options_sequence_by_model',
    'generate_options_monte_carlo_params',
    'render_options_sequence_analysis_section',
    # CALC-O04
    'calculate_leverage_comparison',
    'calculate_options_vs_underlying_summary',
    'render_leverage_comparison_chart',
    'render_options_vs_underlying_scatter',
    'render_options_vs_underlying_section'
]
