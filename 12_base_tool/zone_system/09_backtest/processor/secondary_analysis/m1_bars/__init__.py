"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
M1 Bars Storage Package
XIII Trading LLC
================================================================================

This package fetches and stores 1-minute (M1) bar data from Polygon API to
Supabase for accurate stop/target simulation in CALC-004.

Key Concepts:
    The mfe_mae_potential table stores WHEN the maximum MFE/MAE occurred,
    but not the bar-by-bar price data needed to determine if a specific
    stop or target level was hit first.

    This module stores the full M1 bar series so that CALC-004 can:
    1. Walk bars chronologically from entry time
    2. Check each bar's high/low against stop/target levels
    3. Determine which level was breached first

Usage:
    # CLI Usage
    python m1_bars_runner.py                    # Full batch run
    python m1_bars_runner.py --dry-run          # Test without saving
    python m1_bars_runner.py --limit 10         # Process 10 ticker-dates
    python m1_bars_runner.py --schema           # Create database table
    python m1_bars_runner.py --status           # Show storage status

    # Programmatic Usage
    from m1_bars import M1BarsStorage

    storage = M1BarsStorage()
    results = storage.run_batch_storage()

Components:
    config.py           - Configuration (Supabase, Polygon, parameters)
    m1_bars_storage.py  - Core storage class
    m1_bars_runner.py   - CLI runner script
    schema/             - SQL schema for m1_bars table

Dependencies:
    - Uses M1Fetcher from ../mfe_mae/ for Polygon API calls
    - Reads (ticker, date) pairs from trades table
    - Writes to m1_bars table

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
    TARGET_TABLE,
    BATCH_INSERT_SIZE
)

from .m1_bars_storage import M1BarsStorage

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
    'BATCH_INSERT_SIZE',

    # Storage
    'M1BarsStorage',
]
