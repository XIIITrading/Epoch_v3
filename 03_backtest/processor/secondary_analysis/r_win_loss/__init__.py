"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
R Win/Loss Processor
XIII Trading LLC
================================================================================

PURPOSE:
    Evaluate trades using M5 ATR-based stop (14-period, 1.1x multiplier) and
    R-multiple targets (1R through 5R). Determines win/loss by checking if
    price reached R1+ before being stopped out, using M1 candle fidelity.

WIN/LOSS RULES:
    WIN:  R1+ target hit (price touch) BEFORE stop (close-based)
    LOSS: Stop triggered (M1 close beyond stop) BEFORE R1
    WIN:  No R1/stop by 15:30 and price > entry (EOD_WIN)
    LOSS: No R1/stop by 15:30 and price <= entry (EOD_LOSS)

USAGE:
    # Command line:
    python runner.py                 # Full batch run
    python runner.py --dry-run       # Test without saving
    python runner.py --limit 50      # Process 50 trades
    python runner.py --schema        # Create database table
    python runner.py --info          # Show processor info

    # Programmatic:
    from r_win_loss import RWinLossCalculator

    calculator = RWinLossCalculator(verbose=True)
    results = calculator.run_batch_calculation(limit=100, dry_run=False)

DATABASE:
    Source Tables:
        - trades (trade metadata)
        - m1_bars (1-minute bar data)
        - m5_trade_bars (5-minute trade bars for ATR)
        - m5_indicator_bars (5-minute indicator bars for ATR)

    Target Table:
        - r_win_loss (primary key: trade_id, 1 row per trade)

Version: 1.0.0
================================================================================
"""

from .config import (
    DB_CONFIG,
    ATR_PERIOD,
    ATR_MULTIPLIER,
    R_LEVELS,
    EOD_CUTOFF,
    SOURCE_TABLES,
    TARGET_TABLE,
)

from .calculator import (
    RWinLossCalculator,
    RWinLossResult,
    calculate_atr_m5,
    calculate_true_range,
)

__all__ = [
    # Configuration
    'DB_CONFIG',
    'ATR_PERIOD',
    'ATR_MULTIPLIER',
    'R_LEVELS',
    'EOD_CUTOFF',
    'SOURCE_TABLES',
    'TARGET_TABLE',
    # Calculator
    'RWinLossCalculator',
    'RWinLossResult',
    # ATR functions
    'calculate_atr_m5',
    'calculate_true_range',
]
