"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
M5 Trade Bars Package
XIII Trading LLC
================================================================================

Trade-specific M5 bars from entry to 15:30 with health scoring and
MFE/MAE event marking.

Usage:
    # Run from command line
    python runner.py --schema           # Create database table
    python runner.py --dry-run --limit 5  # Test run
    python runner.py                    # Full batch run
    python runner.py --status           # Show status

    # Use programmatically
    from m5_trade_bars import M5TradeBarsCalculator
    calculator = M5TradeBarsCalculator()
    results = calculator.calculate_for_trade(trade, mfe_time, mae_time)

Version: 1.0.0
================================================================================
"""

from .config import (
    DB_CONFIG,
    TARGET_TABLE,
    CALCULATION_VERSION,
    HEALTH_BUCKETS
)

from .m5_fetcher import M5Fetcher, M5Bar
from .indicators import M5IndicatorCalculator, IndicatorSnapshot
from .structure import StructureAnalyzer, StructureResult, MarketStructureCalculator
from .health import HealthCalculator, HealthResult
from .calculator import M5TradeBarsCalculator, M5TradeBarResult
from .populator import M5TradeBarsPopulator

__version__ = "1.0.0"

__all__ = [
    # Config
    'DB_CONFIG',
    'TARGET_TABLE',
    'CALCULATION_VERSION',
    'HEALTH_BUCKETS',

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

    # Health
    'HealthCalculator',
    'HealthResult',

    # Calculator
    'M5TradeBarsCalculator',
    'M5TradeBarResult',

    # Populator
    'M5TradeBarsPopulator',
]
