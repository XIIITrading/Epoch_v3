"""
================================================================================
EPOCH TRADING SYSTEM - RAMP-UP ANALYSIS
Indicator Progression Analysis for Trade Entry Decisions
XIII Trading LLC
================================================================================

Analyzes indicator progression in the bars leading up to trade entry.
Simulates the trader's perspective watching the far right edge build conviction.

Outputs:
- ramp_up_macro: Summary metrics per trade (avgs, trends, momentum)
- ramp_up_progression: Bar-by-bar indicator values (16 rows per trade)

================================================================================
"""

from .ramp_config import (
    STOP_TYPE,
    LOOKBACK_BARS,
    INDICATORS,
    TREND_THRESHOLD,
    MOMENTUM_THRESHOLD,
)
