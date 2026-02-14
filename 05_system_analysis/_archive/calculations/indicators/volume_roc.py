"""
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Volume ROC Calculation - Delegated to shared library
XIII Trading LLC
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "03_indicators" / "python"))

from indicator_types import VolumeROCResult
from core.volume_roc import calculate_volume_roc, classify_volume_roc, is_volume_roc_healthy

__all__ = [
    "VolumeROCResult",
    "calculate_volume_roc", "classify_volume_roc", "is_volume_roc_healthy"
]
