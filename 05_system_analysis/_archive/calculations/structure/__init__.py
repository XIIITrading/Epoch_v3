"""
Epoch Trading System - Indicator Analysis
Multi-timeframe structure detection modules.
"""

from .m5_structure import detect_m5_structure, is_m5_healthy
from .m15_structure import detect_m15_structure, is_m15_healthy
from .h1_structure import detect_h1_structure, is_h1_healthy
from .h4_structure import detect_h4_structure, is_h4_healthy
