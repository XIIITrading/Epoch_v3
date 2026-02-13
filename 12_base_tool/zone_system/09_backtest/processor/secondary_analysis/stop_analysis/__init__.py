"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
Stop Analysis Processor (CALC-009)
XIII Trading LLC
================================================================================

PURPOSE:
    Calculate 6 different stop placement methods for all trades and simulate
    outcomes. This becomes the FOUNDATION for all downstream indicator analysis.

STOP TYPES:
    1. zone_buffer  - Zone Boundary + 5% Buffer (Default)
    2. prior_m1     - Prior M1 Bar High/Low (Tightest)
    3. prior_m5     - Prior M5 Bar High/Low
    4. m5_atr       - M5 ATR (1.1x), Close-based
    5. m15_atr      - M15 ATR (1.1x), Close-based
    6. fractal      - M5 Fractal High/Low (Market Structure)

USAGE:
    # Command line:
    python runner.py                 # Full batch run
    python runner.py --dry-run       # Test without saving
    python runner.py --limit 50      # Process 50 trades
    python runner.py --schema        # Create database table
    python runner.py --info          # Show stop type info

    # Programmatic:
    from stop_analysis import StopAnalysisCalculator

    calculator = StopAnalysisCalculator(verbose=True)
    results = calculator.run_batch_calculation(limit=100, dry_run=False)

DATABASE:
    Source Tables:
        - trades (trade metadata)
        - mfe_mae_potential (MFE/MAE data)
        - m1_bars (1-minute bar data)
        - m5_trade_bars (5-minute trade bars)

    Target Table:
        - stop_analysis (composite key: trade_id + stop_type)

TRIGGER TYPES:
    - Price-based (zone_buffer, prior_m1, prior_m5, fractal):
      Triggers when price TOUCHES the stop level

    - Close-based (m5_atr, m15_atr):
      Triggers only when bar CLOSES beyond the stop level

Version: 1.0.0
================================================================================
"""

from .config import (
    DB_CONFIG,
    STOP_TYPES,
    STOP_TYPE_DISPLAY_NAMES,
    DEFAULT_STOP_TYPE,
    ZONE_BUFFER_PCT,
    ATR_PERIOD,
    ATR_MULTIPLIER,
    FRACTAL_LENGTH,
    EOD_CUTOFF
)

from .stop_calculator import (
    # Stop calculations
    calculate_zone_buffer_stop,
    calculate_prior_m1_stop,
    calculate_prior_m5_stop,
    calculate_m5_atr_stop,
    calculate_m15_atr_stop,
    calculate_fractal_stop,
    calculate_all_stop_prices,
    # ATR calculations
    calculate_true_range,
    calculate_atr_m5,
    calculate_atr_m15,
    aggregate_m5_to_m15,
    # Fractal detection
    find_fractal_highs,
    find_fractal_lows,
    calculate_fractal_stop_price,
    # Outcome simulation
    check_price_based_stop,
    check_close_based_stop,
    simulate_outcome
)

from .stop_analysis_calc import (
    StopAnalysisCalculator,
    StopAnalysisResult
)

__all__ = [
    # Configuration
    'DB_CONFIG',
    'STOP_TYPES',
    'STOP_TYPE_DISPLAY_NAMES',
    'DEFAULT_STOP_TYPE',
    'ZONE_BUFFER_PCT',
    'ATR_PERIOD',
    'ATR_MULTIPLIER',
    'FRACTAL_LENGTH',
    'EOD_CUTOFF',
    # Stop calculations
    'calculate_zone_buffer_stop',
    'calculate_prior_m1_stop',
    'calculate_prior_m5_stop',
    'calculate_m5_atr_stop',
    'calculate_m15_atr_stop',
    'calculate_fractal_stop',
    'calculate_all_stop_prices',
    # ATR calculations
    'calculate_true_range',
    'calculate_atr_m5',
    'calculate_atr_m15',
    'aggregate_m5_to_m15',
    # Fractal detection
    'find_fractal_highs',
    'find_fractal_lows',
    'calculate_fractal_stop_price',
    # Outcome simulation
    'check_price_based_stop',
    'check_close_based_stop',
    'simulate_outcome',
    # Calculator
    'StopAnalysisCalculator',
    'StopAnalysisResult',
]
