"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
Secondary Analysis Package
XIII Trading LLC
================================================================================

This package contains secondary analysis modules that operate on data
stored in Supabase, independent of the Epoch Excel worksheet workflow.

Modules:
    mfe_mae/            - MFE/MAE Potential Calculator (entry to EOD analysis)
    m1_bars/            - M1 Bar Storage (Polygon to Supabase)
    entry_indicators/   - Entry Indicator Snapshots (for CALC-005 through CALC-008)
    m5_indicator_bars/  - Direction-agnostic M5 bars with indicators (CALC-007)
    m5_trade_bars/      - Trade-specific M5 bars with health scoring (CALC-007)

Version: 1.1.0
================================================================================
"""

__version__ = "1.1.0"
