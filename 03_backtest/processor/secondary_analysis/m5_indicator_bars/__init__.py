"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
M5 Indicator Bars Package
XIII Trading LLC
================================================================================

Direction-agnostic M5 bars with full indicators for all ticker+dates.
Provides foundation data that can be reused across multiple analyses.

Usage:
    # Run from command line
    python runner.py --schema           # Create database table
    python runner.py --dry-run --limit 5  # Test run
    python runner.py                    # Full batch run
    python runner.py --status           # Show status

    # Use programmatically
    from m5_indicator_bars import M5IndicatorBarsCalculator
    calculator = M5IndicatorBarsCalculator()
    results = calculator.calculate_for_ticker_date('SPY', date(2025, 12, 30))

Version: 1.0.0
================================================================================
"""

from .config import (
    DB_CONFIG,
    TARGET_TABLE,
    CALCULATION_VERSION
)

from .m5_fetcher import M5Fetcher, M5Bar
from .indicators import M5IndicatorCalculator, IndicatorSnapshot
from .structure import StructureAnalyzer, StructureResult, MarketStructureCalculator
from .calculator import M5IndicatorBarsCalculator, M5IndicatorBarResult
from .populator import M5IndicatorBarsPopulator

__version__ = "1.0.0"

__all__ = [
    # Config
    'DB_CONFIG',
    'TARGET_TABLE',
    'CALCULATION_VERSION',

    # Fetcher
    'M5Fetcher',
    'M5Bar',

    # Indicators
    'M5IndicatorCalculator',
    'IndicatorSnapshot',

    # Structure
    'StructureAnalyzer',
    'StructureResult',
    'MarketStructureCalculator',

    # Calculator
    'M5IndicatorBarsCalculator',
    'M5IndicatorBarResult',

    # Populator
    'M5IndicatorBarsPopulator',
]
