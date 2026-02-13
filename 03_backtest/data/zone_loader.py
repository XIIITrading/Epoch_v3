"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 03: BACKTEST RUNNER v3.0
Zone Loader - Zone Data Structure
XIII Trading LLC
================================================================================

Provides the ZoneData dataclass used by all zone loaders.
================================================================================
"""
from typing import Optional
from dataclasses import dataclass


@dataclass
class ZoneData:
    """Zone data structure"""
    ticker: str
    ticker_id: str  # String format like "AMZN_120525"
    zone_id: Optional[str]  # Can be string like "Z1" or int
    direction: str  # 'Bull', 'Bear', etc.
    hvn_poc: float
    zone_high: float
    zone_low: float
    tier: Optional[str]  # T1, T2, T3
    target_id: Optional[str]
    target: Optional[float]
    rr: Optional[float]
    zone_type: str  # 'PRIMARY' or 'SECONDARY'
