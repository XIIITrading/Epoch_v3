"""
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
SMA Calculations - Delegated to shared library
XIII Trading LLC
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "03_indicators" / "python"))

from indicator_types import SMAResult, SMAMomentumResult
from core.sma import (
    calculate_sma,
    calculate_sma_spread,
    calculate_sma_momentum,
    is_sma_alignment_healthy,
    is_sma_momentum_healthy
)

__all__ = [
    "SMAResult", "SMAMomentumResult",
    "calculate_sma", "calculate_sma_spread", "calculate_sma_momentum",
    "is_sma_alignment_healthy", "is_sma_momentum_healthy"
]
