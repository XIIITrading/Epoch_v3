"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
Indicator Refinement
XIII Trading LLC
================================================================================

Calculates Continuation and Rejection scores for trades based on the
Epoch Indicator Model Specification v1.0.

Trade Classification:
    - CONTINUATION (EPCH01/EPCH03): With-trend trades, scored 0-10
    - REJECTION (EPCH02/EPCH04): Counter-trend/exhaustion, scored 0-11

Version: 1.0.0
================================================================================
"""

from .calculator import IndicatorRefinementCalculator, IndicatorRefinementResult
from .populator import IndicatorRefinementPopulator

__all__ = [
    'IndicatorRefinementCalculator',
    'IndicatorRefinementResult',
    'IndicatorRefinementPopulator',
]
