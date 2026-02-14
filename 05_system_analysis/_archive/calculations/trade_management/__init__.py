"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Trade Management Calculations Package
XIII Trading LLC
================================================================================

This package contains calculations for trade management analysis:
- MFE/MAE Distribution Analysis (CALC-002) - Percentage-based
- MFE/MAE Sequence Analysis (CALC-003) - Temporal sequence for Monte Carlo

Usage:
    from calculations.trade_management.mfe_mae_stats import (
        calculate_mfe_mae_summary,
        calculate_mfe_mae_by_model,
        render_mfe_mae_summary_cards,
        render_mfe_histogram,
        render_mae_histogram,
        render_mfe_mae_scatter,
        render_model_mfe_mae_table,
        render_trade_management_analysis
    )

    from calculations.trade_management.mfe_mae_sequence import (
        calculate_sequence_summary,
        calculate_sequence_by_model,
        generate_monte_carlo_params,
        render_sequence_analysis_section
    )

================================================================================
"""

from .mfe_mae_stats import (
    calculate_mfe_mae_summary,
    calculate_mfe_mae_by_model,
    render_mfe_histogram,
    render_mae_histogram,
    render_mfe_mae_scatter,
    render_mfe_mae_summary_cards,
    render_model_mfe_mae_table,
    render_trade_management_analysis
)

from .mfe_mae_sequence import (
    calculate_sequence_summary,
    calculate_sequence_by_model,
    generate_monte_carlo_params,
    render_sequence_analysis_section
)

__all__ = [
    # CALC-002: MFE/MAE Distribution
    "calculate_mfe_mae_summary",
    "calculate_mfe_mae_by_model",
    "render_mfe_histogram",
    "render_mae_histogram",
    "render_mfe_mae_scatter",
    "render_mfe_mae_summary_cards",
    "render_model_mfe_mae_table",
    "render_trade_management_analysis",
    # CALC-003: MFE/MAE Sequence
    "calculate_sequence_summary",
    "calculate_sequence_by_model",
    "generate_monte_carlo_params",
    "render_sequence_analysis_section"
]
