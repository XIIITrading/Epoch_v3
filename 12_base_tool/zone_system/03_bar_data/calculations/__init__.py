"""
Epoch Trading System - Bar Data Calculations Package
XIII Trading LLC

This package contains calculation modules for bar data metrics:
- m1_metrics: Monthly OHLC calculator
- w1_metrics: Weekly OHLC calculator
- d1_metrics: Daily OHLC calculator
- on_calculator: Overnight session calculator
- options_calculator: Options levels calculator
- atr_calculator: ATR calculator (M5, M15, H1, D1)
- camarilla_calculator: Camarilla pivot calculator
- credentials: Polygon API key storage

Note: These calculators are copied from the Meridian system and work unchanged.
"""

from .m1_metrics import M1MetricsCalculator
from .w1_metrics import W1MetricsCalculator
from .d1_metrics import D1MetricsCalculator
from .on_calculator import ONMetricsCalculator
from .options_calculator import OptionsLevelsCalculator
from .atr_calculator import (
    calculate_m5_atr,
    calculate_m15_atr,
    calculate_h1_atr,
    calculate_daily_atr
)
from .camarilla_calculator import CamarillaCalculator

__all__ = [
    'M1MetricsCalculator',
    'W1MetricsCalculator',
    'D1MetricsCalculator',
    'ONMetricsCalculator',
    'OptionsLevelsCalculator',
    'CamarillaCalculator',
    'calculate_m5_atr',
    'calculate_m15_atr',
    'calculate_h1_atr',
    'calculate_daily_atr'
]
