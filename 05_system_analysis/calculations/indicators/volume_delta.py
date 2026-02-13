"""
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Volume Delta Calculation - Delegated to shared library
XIII Trading LLC
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "03_indicators" / "python"))

from indicator_types import VolumeDeltaResult, RollingDeltaResult
from core.volume_delta import (
    calculate_bar_delta,
    calculate_bar_delta_from_bar,
    calculate_rolling_delta,
    is_volume_delta_healthy
)

# Backward compatibility aliases
BarDeltaResult = VolumeDeltaResult
calculate_bar_delta_from_dict = calculate_bar_delta_from_bar

__all__ = [
    "VolumeDeltaResult", "BarDeltaResult", "RollingDeltaResult",
    "calculate_bar_delta", "calculate_bar_delta_from_bar", "calculate_bar_delta_from_dict",
    "calculate_rolling_delta", "is_volume_delta_healthy"
]
