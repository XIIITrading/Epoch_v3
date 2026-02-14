"""
Epoch Trading System - Indicator Analysis
Derived calculation modules (MFE/MAE, trade outcomes).
"""

from .mfe_mae import find_mfe_bar, find_mae_bar, MFEMAEResult
from .trade_outcome import classify_outcome, calculate_r_multiple
