"""
================================================================================
EPOCH TRADING SYSTEM - RAMP-UP INDICATOR ANALYSIS
Analysis Module
XIII Trading LLC
================================================================================

Calculates derivative analysis metrics from ramp_up_macro and ramp_up_progression
tables. Results are stored in Supabase analysis tables for Claude Code review.

================================================================================
"""

from .run_analysis import run_all_analysis
from .calculators import (
    DirectionAnalyzer,
    TradeTypeAnalyzer,
    ModelAnalyzer,
    ModelDirectionAnalyzer,
    IndicatorTrendAnalyzer,
    IndicatorMomentumAnalyzer,
    StructureConsistencyAnalyzer,
    EntrySnapshotAnalyzer,
    ProgressionAvgAnalyzer,
)

__all__ = [
    'run_all_analysis',
    'DirectionAnalyzer',
    'TradeTypeAnalyzer',
    'ModelAnalyzer',
    'ModelDirectionAnalyzer',
    'IndicatorTrendAnalyzer',
    'IndicatorMomentumAnalyzer',
    'StructureConsistencyAnalyzer',
    'EntrySnapshotAnalyzer',
    'ProgressionAvgAnalyzer',
]
