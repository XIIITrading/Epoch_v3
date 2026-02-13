"""
Epoch Trading System - Setups Exporter
Exports Analysis worksheet setups to setups table.
"""

from datetime import date
from typing import Any, Dict, List, Tuple
from .base_exporter import BaseExporter


class SetupsExporter(BaseExporter):
    """Exports primary and secondary setups."""

    TABLE_NAME = "setups"
    PRIMARY_KEY = ["date", "ticker_id", "setup_type"]

    def export(self, data: List[Dict[str, Any]], session_date: date) -> int:
        """
        Export setups data.

        Args:
            data: List of setup records (primary and secondary)
            session_date: The trading date

        Returns:
            Number of records exported
        """
        if not data:
            return 0

        # Helper to safely get numeric values (filter out non-numeric strings)
        def safe_numeric(val):
            if val is None or val == "":
                return None
            if isinstance(val, (int, float)):
                return float(val)
            # It's a string - try to convert, return None if not numeric
            try:
                return float(val)
            except (ValueError, TypeError):
                return None

        # Deduplicate by primary key (ticker_id, setup_type) - last one wins
        seen_keys = set()
        records = []
        for row in data:
            # Skip rows with missing required fields
            if not row.get("ticker_id") or not row.get("ticker"):
                continue

            # Create unique key for deduplication
            key = (row.get("ticker_id"), row.get("setup_type"))
            if key in seen_keys:
                continue
            seen_keys.add(key)

            records.append({
                "date": session_date,
                "ticker_id": row.get("ticker_id"),
                "setup_type": row.get("setup_type"),
                "ticker": row.get("ticker"),
                "direction": row.get("direction"),
                "zone_id": row.get("zone_id"),
                "hvn_poc": safe_numeric(row.get("hvn_poc")),
                "zone_high": safe_numeric(row.get("zone_high")),
                "zone_low": safe_numeric(row.get("zone_low")),
                "target_id": row.get("target_id"),
                "target_price": safe_numeric(row.get("target_price")),
                "risk_reward": safe_numeric(row.get("risk_reward")),
                "pinescript_6": row.get("pinescript_6"),
                "pinescript_16": row.get("pinescript_16"),
            })

        if not records:
            return 0

        return self.upsert_many(records)

    def validate(self, data: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """Validate setups data."""
        errors = []

        if not data:
            # Empty setups is valid
            return True, []

        valid_setup_types = ["PRIMARY", "SECONDARY"]
        valid_directions = ["Bull", "Bear", None]

        for i, row in enumerate(data):
            if not row.get("ticker_id"):
                errors.append(f"Row {i}: Missing ticker_id")
            if not row.get("ticker"):
                errors.append(f"Row {i}: Missing ticker")

            setup_type = row.get("setup_type")
            if setup_type not in valid_setup_types:
                errors.append(f"Row {i}: Invalid setup_type: {setup_type}")

            direction = row.get("direction")
            if direction and direction not in valid_directions:
                errors.append(f"Row {i}: Invalid direction: {direction}")

        return len(errors) == 0, errors
