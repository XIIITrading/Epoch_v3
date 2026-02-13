"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: BACKTEST PROCESSOR
R-Level Crossing Events - Secondary Analysis
XIII Trading LLC
================================================================================

Detects when trades cross R-level thresholds (1R, 2R, 3R) and captures
indicator snapshots at those moments.

Uses M1 indicator bars for precise crossing detection.
Adds R1_CROSS, R2_CROSS, R3_CROSS events to optimal_trade table.

NOTE: This module ADDS new event types without modifying existing
ENTRY, MFE, MAE, EXIT events. Fully backward compatible.
================================================================================
"""

from .detector import RLevelCrossingDetector
from .calculator import RLevelEventsCalculator

__all__ = ['RLevelCrossingDetector', 'RLevelEventsCalculator']
