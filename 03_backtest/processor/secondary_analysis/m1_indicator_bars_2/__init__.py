"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
M1 Indicator Bars v2 - Package Init
XIII Trading LLC
================================================================================

Entry Qualifier Standard Indicators + Extended Analysis on M1 bars.
Reads from m1_bars_2 (no Polygon API calls for M1 data).
Writes to m1_indicator_bars_2.

Pipeline: trades_2 -> m1_bars_2 -> m1_indicator_bars_2

Version: 2.0.0
================================================================================
"""

from .calculator import M1IndicatorBarsCalculator, M1IndicatorBarResult
from .populator import M1IndicatorBarsPopulator
from .indicators import M1IndicatorCalculator, IndicatorSnapshot
from .structure import StructureAnalyzer, StructureResult

__all__ = [
    'M1IndicatorBarsCalculator',
    'M1IndicatorBarResult',
    'M1IndicatorBarsPopulator',
    'M1IndicatorCalculator',
    'IndicatorSnapshot',
    'StructureAnalyzer',
    'StructureResult',
]

__version__ = "2.0.0"
