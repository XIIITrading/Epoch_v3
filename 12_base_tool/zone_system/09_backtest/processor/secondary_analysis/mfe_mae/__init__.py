"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
MFE/MAE Potential Calculator Package
XIII Trading LLC
================================================================================

This package calculates POTENTIAL MFE (Max Favorable Excursion) and MAE
(Max Adverse Excursion) for all trades, measuring from entry time to
end-of-day (15:30 ET).

Key Concepts:
    REALIZED MFE/MAE (in optimal_trade table):
        Measures entry to exit - "What happened during the trade?"

    POTENTIAL MFE/MAE (this module):
        Measures entry to 15:30 ET - "What was possible in the market?"

Usage:
    # CLI Usage
    python mfe_mae_potential_runner.py              # Full batch run
    python mfe_mae_potential_runner.py --dry-run    # Test without saving
    python mfe_mae_potential_runner.py --limit 50   # Process 50 trades
    python mfe_mae_potential_runner.py --schema     # Create database table

    # Programmatic Usage
    from mfe_mae import MFEMAEPotentialCalculator, M1Fetcher

    fetcher = M1Fetcher()
    calculator = MFEMAEPotentialCalculator(fetcher=fetcher)
    results = calculator.run_batch_calculation()

Components:
    config.py                   - Configuration (Supabase, Polygon, parameters)
    m1_fetcher.py              - 1-minute bar data fetcher
    mfe_mae_potential_calc.py  - Core calculator class
    mfe_mae_potential_runner.py - CLI runner script
    schema/                    - SQL schema for mfe_mae_potential table

Version: 1.0.0
================================================================================
"""

from .config import (
    DB_CONFIG,
    POLYGON_API_KEY,
    EOD_CUTOFF,
    MARKET_OPEN,
    MARKET_CLOSE,
    SOURCE_TABLE,
    TARGET_TABLE
)

from .m1_fetcher import M1Fetcher, M1Bar

from .mfe_mae_potential_calc import (
    MFEMAEPotentialCalculator,
    MFEMAEPotentialResult
)

__version__ = "1.0.0"
__author__ = "XIII Trading LLC"

__all__ = [
    # Config
    'DB_CONFIG',
    'POLYGON_API_KEY',
    'EOD_CUTOFF',
    'MARKET_OPEN',
    'MARKET_CLOSE',
    'SOURCE_TABLE',
    'TARGET_TABLE',

    # Fetcher
    'M1Fetcher',
    'M1Bar',

    # Calculator
    'MFEMAEPotentialCalculator',
    'MFEMAEPotentialResult',
]
