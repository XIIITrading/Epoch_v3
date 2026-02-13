"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
Trades Unified (trades_m5_r_win)
XIII Trading LLC
================================================================================

Builds the trades_m5_r_win canonical outcomes table.
Single source of truth for trade outcomes across all EPOCH modules.

Outcome Priority:
    1. r_win_loss ATR outcome (outcome_method = 'atr_r_target')
    2. Zone buffer fallback   (outcome_method = 'zone_buffer_fallback')

Usage:
    # As CLI:
    python runner.py --schema     # Create table
    python runner.py              # Populate table
    python runner.py --dry-run    # Test without DB writes

    # As module:
    from trades_unified import TradesUnifiedCalculator
    calculator = TradesUnifiedCalculator()
    results = calculator.run_batch_calculation()

Version: 1.0.0
================================================================================
"""

from .config import (
    DB_CONFIG,
    SOURCE_TABLES,
    TARGET_TABLE,
    ZONE_BUFFER_PCT,
    EOD_CUTOFF,
)

from .calculator import (
    TradesUnifiedCalculator,
)

__all__ = [
    'DB_CONFIG',
    'SOURCE_TABLES',
    'TARGET_TABLE',
    'ZONE_BUFFER_PCT',
    'EOD_CUTOFF',
    'TradesUnifiedCalculator',
]
