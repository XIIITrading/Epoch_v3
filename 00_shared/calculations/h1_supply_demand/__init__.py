"""
H1 Supply & Demand Zone Calculation Module
============================================

Pivot-based supply/demand zone detection fixed to 1-Hour timeframe.
Designed to run independently and layer with HVN zones, PDV, and
Market Structure v3 for confluence scoring.

Usage:
    from shared.calculations.h1_supply_demand import calculate_h1_zones

    result = calculate_h1_zones(df_h1, ticker="MU")
    for zone in result.all_zones:
        print(f"{zone.zone_type.value}: {zone.bottom:.2f} - {zone.top:.2f}")
"""

from .calculator import (
    calculate_h1_zones,
    calculate_h1_zones_from_bars,
    H1SupplyDemandResult,
    Zone,
    ZoneType,
    ZoneStatus,
)

__all__ = [
    "calculate_h1_zones",
    "calculate_h1_zones_from_bars",
    "H1SupplyDemandResult",
    "Zone",
    "ZoneType",
    "ZoneStatus",
]
