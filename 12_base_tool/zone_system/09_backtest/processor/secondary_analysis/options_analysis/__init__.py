"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
Options Analysis Module
XIII Trading LLC
================================================================================

This module provides options analysis for completed backtest trades,
reading from the trades table and writing to the options_analysis table.

Components:
- config.py: Configuration settings (DB, API, parameters)
- fetcher.py: Polygon.io options API client
- contract_selector.py: Contract selection logic (modifiable)
- calculator.py: Options analysis calculations
- populator.py: Database batch populator
- runner.py: CLI runner with argparse

Usage (CLI):
    python runner.py                    # Full batch run
    python runner.py --dry-run          # Test without saving
    python runner.py --limit 50         # Process 50 trades
    python runner.py --verbose          # Detailed logging
    python runner.py --schema           # Create database table

Usage (Programmatic):
    from secondary_analysis.options_analysis import OptionsAnalysisPopulator

    populator = OptionsAnalysisPopulator(verbose=True)
    results = populator.run_batch_population(limit=100)

Version: 1.0.0
================================================================================
"""

# Configuration
from .config import (
    DB_CONFIG,
    POLYGON_API_KEY,
    POLYGON_BASE_URL,
    SOURCE_TABLE,
    TARGET_TABLE,
    ENTRY_BAR_MULTIPLIER,
    ENTRY_BAR_TIMESPAN,
    EXIT_BAR_MULTIPLIER,
    EXIT_BAR_TIMESPAN,
    MIN_DAYS_TO_EXPIRY,
    DEFAULT_STRIKE_METHOD,
    CALCULATION_VERSION
)

# Fetcher
from .fetcher import (
    OptionsFetcher,
    OptionsBar,
    OptionsContract,
    OptionsChain,
    build_options_ticker,
    parse_options_ticker
)

# Contract Selection
from .contract_selector import (
    select_contract,
    select_expiration,
    select_first_itm,
    select_atm,
    select_first_otm,
    select_by_delta,
    select_by_strike,
    SelectedContract,
    SELECTION_METHOD
)

# Calculator
from .calculator import (
    OptionsAnalysisCalculator,
    OptionsAnalysisResult,
    OptionsTradeResult,
    OptionsSummaryStats,
    calculate_options_pnl,
    calculate_summary_stats
)

# Populator
from .populator import OptionsAnalysisPopulator

__version__ = "1.0.0"
__author__ = "XIII Trading LLC"

__all__ = [
    # Configuration
    'DB_CONFIG',
    'POLYGON_API_KEY',
    'POLYGON_BASE_URL',
    'SOURCE_TABLE',
    'TARGET_TABLE',
    'ENTRY_BAR_MULTIPLIER',
    'ENTRY_BAR_TIMESPAN',
    'EXIT_BAR_MULTIPLIER',
    'EXIT_BAR_TIMESPAN',
    'MIN_DAYS_TO_EXPIRY',
    'DEFAULT_STRIKE_METHOD',
    'CALCULATION_VERSION',

    # Fetcher
    'OptionsFetcher',
    'OptionsBar',
    'OptionsContract',
    'OptionsChain',
    'build_options_ticker',
    'parse_options_ticker',

    # Contract Selection
    'select_contract',
    'select_expiration',
    'select_first_itm',
    'select_atm',
    'select_first_otm',
    'select_by_delta',
    'select_by_strike',
    'SelectedContract',
    'SELECTION_METHOD',

    # Calculator
    'OptionsAnalysisCalculator',
    'OptionsAnalysisResult',
    'OptionsTradeResult',
    'OptionsSummaryStats',
    'calculate_options_pnl',
    'calculate_summary_stats',

    # Populator
    'OptionsAnalysisPopulator',
]
