"""
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
VWAP Calculation - Delegated to shared library
XIII Trading LLC
"""
import sys
from pathlib import Path

# Add shared library to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "03_indicators" / "python"))

from indicator_types import VWAPResult
from core.vwap import calculate_vwap, calculate_vwap_metrics, is_vwap_healthy

# Re-export for backward compatibility
__all__ = ["VWAPResult", "calculate_vwap", "calculate_vwap_metrics", "is_vwap_healthy"]
