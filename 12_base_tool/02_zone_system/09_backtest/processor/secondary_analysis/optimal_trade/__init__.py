"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
Optimal Trade Calculator (Points-Based)
XIII Trading LLC
================================================================================

Calculates optimal_trade events (ENTRY, MFE, MAE, EXIT) using:
- trades table for entry data
- mfe_mae_potential table for MFE/MAE timing
- m5_trade_bars table for indicator values and health scores

Win Condition: mfe_potential_time < mae_potential_time (temporal)
P&L: Points (absolute dollars) instead of R-multiples
Exit: Fixed 15:30 ET

Version: 2.0.0
================================================================================
"""

from .calculator import OptimalTradeCalculator

__all__ = ['OptimalTradeCalculator']
__version__ = '2.0.0'
