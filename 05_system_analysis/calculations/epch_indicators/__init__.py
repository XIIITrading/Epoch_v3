"""
================================================================================
EPOCH TRADING SYSTEM - EPCH Indicators Edge Analysis
XII Trading LLC
================================================================================

Aggregate edge analysis for the 5 EPCH v1.0 indicators plus composite scores.
Analyzes which indicator conditions correlate with higher win rates.

Indicators Analyzed:
1. Candle Range (candle_range_pct)
2. Volume Delta (vol_delta)
3. Volume ROC (vol_roc)
4. SMA Config (sma_spread, sma9, sma21)
5. H1 Structure (h1_structure)
6. LONG Score (long_score)
7. SHORT Score (short_score)

Version: 1.0.0
================================================================================
"""

from .base_tester import (
    EdgeTestResult,
    fetch_epch_indicator_data,
    calculate_win_rates,
    chi_square_test,
    spearman_monotonic_test,
    get_confidence_level,
    determine_edge,
    run_all_tests
)

from .ui_components import (
    render_epch_indicators_section
)

__all__ = [
    # Data structures
    'EdgeTestResult',

    # Data fetching
    'fetch_epch_indicator_data',

    # Statistical functions
    'calculate_win_rates',
    'chi_square_test',
    'spearman_monotonic_test',
    'get_confidence_level',
    'determine_edge',

    # Test runner
    'run_all_tests',

    # UI
    'render_epch_indicators_section',
]
