"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
M1 Bars Storage Package
XIII Trading LLC
================================================================================

This package fetches and stores 1-minute (M1) bar data from Polygon API to
Supabase for downstream secondary processors.

Time Range: Prior day 16:00 ET through trade day 16:00 ET
- After-hours, overnight, pre-market, and full regular session
- Single source of truth for all M1 bar data needs

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
    m1_bars_storage.py  - Core storage class + M1BarFetcher
    m1_bars_runner.py   - CLI runner script
    schema/             - SQL schema for m1_bars table

Dependencies:
    - Reads (ticker, date) pairs from trades_2 table
    - Writes to m1_bars table

Version: 2.0.0
================================================================================
"""

from .config import (
    DB_CONFIG,
    POLYGON_API_KEY,
    PRIOR_DAY_START,
    TRADE_DAY_END,
    SOURCE_TABLE,
    TARGET_TABLE,
    BATCH_INSERT_SIZE
)

from .m1_bars_storage import M1BarsStorage, M1BarFetcher

__version__ = "2.0.0"
__author__ = "XIII Trading LLC"

__all__ = [
    # Config
    'DB_CONFIG',
    'POLYGON_API_KEY',
    'PRIOR_DAY_START',
    'TRADE_DAY_END',
    'SOURCE_TABLE',
    'TARGET_TABLE',
    'BATCH_INSERT_SIZE',

    # Storage
    'M1BarsStorage',
    'M1BarFetcher',
]
