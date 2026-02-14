"""
Indicator Analysis Module (CALC-005 through CALC-008)

This module analyzes entry indicators and their correlation with trade outcomes.

Modules:
    - health_correlation (CALC-005): Health Score -> Win Rate correlation
    - factor_importance (CALC-006): Individual indicator predictiveness
    - indicator_progression (CALC-007): Entry -> MFE/MAE indicator changes
    - rejection_dynamics (CALC-008): Rejection trade specific analysis
"""

# CALC-005: Health Score Correlation
from .health_correlation import (
    analyze_health_correlation,
    HealthCorrelationResult,
    render_calc_005_section,
    wilson_confidence_interval,
    calculate_win_rate_by_score,
    calculate_win_rate_by_bucket,
    calculate_model_direction_breakdown,
    calculate_threshold_analysis
)

# CALC-006: Factor Importance
from .factor_importance import (
    analyze_factor_importance,
    FactorImportanceResult,
    FactorAnalysis,
    render_calc_006_section,
    FACTORS
)

# CALC-007: Indicator Progression Analysis
from .indicator_progression import (
    analyze_indicator_progression,
    IndicatorProgressionResult,
    ProgressionPath,
    EventSnapshot,
    EarlyWarningSignal,
    FactorDegradationAnalysis,
    render_calc_007_section,
    PROGRESSION_INDICATORS,
    HEALTH_FACTORS
)

# CALC-008: Rejection Dynamics Analysis
from .rejection_dynamics import (
    analyze_rejection_dynamics,
    RejectionDynamicsResult,
    TimeToMFEResult,
    InversionTestResult,
    FactorInversionResult,
    ExhaustionIndicator,
    render_calc_008_section,
    analyze_time_to_mfe,
    test_health_score_inversion,
    analyze_factor_inversion,
    discover_exhaustion_indicators
)

__all__ = [
    # CALC-005
    'analyze_health_correlation',
    'HealthCorrelationResult',
    'render_calc_005_section',
    'wilson_confidence_interval',
    'calculate_win_rate_by_score',
    'calculate_win_rate_by_bucket',
    'calculate_model_direction_breakdown',
    'calculate_threshold_analysis',
    # CALC-006
    'analyze_factor_importance',
    'FactorImportanceResult',
    'FactorAnalysis',
    'render_calc_006_section',
    'FACTORS',
    # CALC-007
    'analyze_indicator_progression',
    'IndicatorProgressionResult',
    'ProgressionPath',
    'EventSnapshot',
    'EarlyWarningSignal',
    'FactorDegradationAnalysis',
    'render_calc_007_section',
    'PROGRESSION_INDICATORS',
    'HEALTH_FACTORS',
    # CALC-008
    'analyze_rejection_dynamics',
    'RejectionDynamicsResult',
    'TimeToMFEResult',
    'InversionTestResult',
    'FactorInversionResult',
    'ExhaustionIndicator',
    'render_calc_008_section',
    'analyze_time_to_mfe',
    'test_health_score_inversion',
    'analyze_factor_inversion',
    'discover_exhaustion_indicators',
]
