"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
M1 Indicator Bars Module
XIII Trading LLC
================================================================================

Pre-computes 1-minute indicator bars for ramp-up chart analysis.
Similar to M5 indicator bars but at 1-minute resolution.

Usage:
    from m1_indicator_bars import M1IndicatorBarsPopulator, M1IndicatorBarsCalculator

    # Batch populate missing data
    populator = M1IndicatorBarsPopulator()
    populator.run()

    # Calculate for specific ticker/date
    calculator = M1IndicatorBarsCalculator()
    bars = calculator.calculate('SPY', date(2024, 1, 15))

Version: 1.0.0
================================================================================
"""

from .calculator import M1IndicatorBarsCalculator, M1IndicatorBarResult
from .populator import M1IndicatorBarsPopulator
from .m1_fetcher import M1Fetcher
from .indicators import M1IndicatorCalculator, IndicatorSnapshot
from .structure import StructureAnalyzer, StructureResult

__all__ = [
    'M1IndicatorBarsCalculator',
    'M1IndicatorBarResult',
    'M1IndicatorBarsPopulator',
    'M1Fetcher',
    'M1IndicatorCalculator',
    'IndicatorSnapshot',
    'StructureAnalyzer',
    'StructureResult',
]

__version__ = "1.0.0"
