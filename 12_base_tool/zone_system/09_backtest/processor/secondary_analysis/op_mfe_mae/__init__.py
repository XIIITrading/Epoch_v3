"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
Options MFE/MAE Potential Calculator
XIII Trading LLC
================================================================================

Calculates MFE (Max Favorable Excursion) and MAE (Max Adverse Excursion)
for OPTIONS trades, measuring from entry time to 15:30 ET.

This mirrors the share-based mfe_mae/ module but for options contracts.
All measurements are in POINTS (price movement) and PERCENTAGE of entry.

Version: 1.0.0
================================================================================
"""

from .op_mfe_mae_calc import OpMFEMAECalculator, OpMFEMAEResult
from .options_bar_fetcher import OptionsBarFetcher

__all__ = ['OpMFEMAECalculator', 'OpMFEMAEResult', 'OptionsBarFetcher']
__version__ = '1.0.0'
