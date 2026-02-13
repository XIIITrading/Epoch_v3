"""
Epoch Trading System - HVN POCs Exporter
Exports HVN Point of Control data to hvn_pocs table.

Reads from bar_data worksheet time_hvn section (rows 59-68).
Each ticker has up to 10 POC price levels (poc_1 through poc_10).
"""

from datetime import date
from typing import Any, Dict, List, Tuple
from .base_exporter import BaseExporter


class HvnPocsExporter(BaseExporter):
    """Exports HVN POC levels for each ticker."""

    TABLE_NAME = "hvn_pocs"
    PRIMARY_KEY = ["date", "ticker_id"]

    def export(self, data: List[Dict[str, Any]], session_date: date) -> int:
        """
        Export HVN POC data.

        Args:
            data: List of HVN POC records (one per ticker with poc_1 through poc_10)
            session_date: The trading date

        Returns:
            Number of records exported
        """
        if not data:
            return 0

        # Deduplicate by (date, ticker_id) - keep last occurrence
        seen_keys = set()
        records = []
        for row in reversed(data):
            ticker_id = row.get("ticker_id")
            if not ticker_id:
                continue

            key = (session_date, ticker_id)
            if key in seen_keys:
                continue
            seen_keys.add(key)

            # Convert epoch_start_date if present
            epoch_start = row.get("epoch_start_date")
            if epoch_start and hasattr(epoch_start, 'date'):
                epoch_start = epoch_start.date()

            records.append({
                "date": session_date,
                "ticker_id": ticker_id,
                "ticker": row.get("ticker"),
                "epoch_start_date": epoch_start,
                "poc_1": row.get("poc_1"),
                "poc_2": row.get("poc_2"),
                "poc_3": row.get("poc_3"),
                "poc_4": row.get("poc_4"),
                "poc_5": row.get("poc_5"),
                "poc_6": row.get("poc_6"),
                "poc_7": row.get("poc_7"),
                "poc_8": row.get("poc_8"),
                "poc_9": row.get("poc_9"),
                "poc_10": row.get("poc_10"),
            })

        # Reverse back to original order
        records.reverse()

        if not records:
            return 0

        return self.upsert_many(records)

    def validate(self, data: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """Validate HVN POC data."""
        errors = []

        if not data:
            # Empty data is OK - some sessions may not have POC data
            return True, []

        for i, row in enumerate(data):
            if not row.get("ticker_id"):
                errors.append(f"Row {i}: Missing ticker_id")
            if not row.get("ticker"):
                errors.append(f"Row {i}: Missing ticker")

            # Check if at least one POC is present (warning only, not error)
            has_any_poc = any(row.get(f"poc_{j}") for j in range(1, 11))
            if not has_any_poc:
                # This is a warning, not an error - some tickers may not have POCs yet
                pass

        return len(errors) == 0, errors
