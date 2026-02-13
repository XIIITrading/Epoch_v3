"""
Epoch Trading System - Zones Exporter
Exports raw_zones and zone_results data to zones table.
"""

from datetime import date
from typing import Any, Dict, List, Tuple
from .base_exporter import BaseExporter


class ZonesExporter(BaseExporter):
    """Exports all zones (both raw and filtered) to zones table."""

    TABLE_NAME = "zones"
    PRIMARY_KEY = ["date", "zone_id"]

    def export(self, data: List[Dict[str, Any]], session_date: date) -> int:
        """
        Export zones data.

        Args:
            data: List of zone records (combined raw + filtered)
            session_date: The trading date

        Returns:
            Number of records exported
        """
        if not data:
            return 0

        # Helper to safely get numeric values (filter out "X" markers)
        def safe_numeric(val):
            if val is None or val == "X" or val == "":
                return None
            try:
                return float(val)
            except (ValueError, TypeError):
                return None

        records = []
        for row in data:
            records.append({
                "date": session_date,
                "zone_id": row.get("zone_id"),
                "ticker_id": row.get("ticker_id"),
                "ticker": row.get("ticker"),
                "price": safe_numeric(row.get("price")),
                "hvn_poc": safe_numeric(row.get("hvn_poc")),
                "zone_high": safe_numeric(row.get("zone_high")),
                "zone_low": safe_numeric(row.get("zone_low")),
                "direction": row.get("direction"),
                "rank": row.get("rank"),
                "score": safe_numeric(row.get("score")),
                "overlap_count": row.get("overlaps"),
                "confluences": row.get("confluences"),
                "is_filtered": row.get("is_filtered", False),
                "is_epch_bull": row.get("is_epch_bull", False),
                "is_epch_bear": row.get("is_epch_bear", False),
                "epch_bull_price": safe_numeric(row.get("epch_bull_price")),
                "epch_bear_price": safe_numeric(row.get("epch_bear_price")),
                "epch_bull_target": safe_numeric(row.get("epch_bull_target")),
                "epch_bear_target": safe_numeric(row.get("epch_bear_target")),
            })

        return self.upsert_many(records)

    def export_combined(self, raw_zones: List[Dict[str, Any]],
                       filtered_zones: List[Dict[str, Any]],
                       session_date: date) -> int:
        """
        Export combined raw and filtered zones.
        Filtered zones update the is_filtered flag and add setup markers.

        Args:
            raw_zones: All zones from raw_zones worksheet
            filtered_zones: Filtered zones from zone_results worksheet
            session_date: The trading date

        Returns:
            Number of records exported
        """
        # Merge data - filtered zones take precedence, deduplicate by zone_id
        merged = []
        seen_zones = set()

        # First add all filtered zones (they have the complete data)
        # Also deduplicate within filtered_zones itself
        for zone in filtered_zones:
            zone_id = zone.get("zone_id")
            if zone_id and zone_id not in seen_zones:
                seen_zones.add(zone_id)
                merged.append(zone)

        # Then add raw zones that weren't in filtered
        for zone in raw_zones:
            zone_id = zone.get("zone_id")
            if zone_id and zone_id not in seen_zones:
                seen_zones.add(zone_id)
                merged.append(zone)

        return self.export(merged, session_date)

    def validate(self, data: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """Validate zones data."""
        errors = []

        if not data:
            # Empty zones is valid (might be a day with no zones)
            return True, []

        valid_ranks = ["L1", "L2", "L3", "L4", "L5", None]
        valid_directions = ["Bull", "Bear", None]

        for i, row in enumerate(data):
            if not row.get("zone_id"):
                errors.append(f"Row {i}: Missing zone_id")
            if not row.get("ticker"):
                errors.append(f"Row {i}: Missing ticker")

            rank = row.get("rank")
            if rank and rank not in valid_ranks:
                errors.append(f"Row {i}: Invalid rank: {rank}")

            direction = row.get("direction")
            if direction and direction not in valid_directions:
                errors.append(f"Row {i}: Invalid direction: {direction}")

        return len(errors) == 0, errors
