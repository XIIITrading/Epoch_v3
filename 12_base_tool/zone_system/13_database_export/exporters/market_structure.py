"""
Epoch Trading System - Market Structure Exporter
Exports market_overview data (indices + user tickers) to market_structure table.
"""

from datetime import date
from typing import Any, Dict, List, Tuple
from .base_exporter import BaseExporter


class MarketStructureExporter(BaseExporter):
    """Exports market structure data for indices and user tickers."""

    TABLE_NAME = "market_structure"
    PRIMARY_KEY = ["date", "ticker"]

    def export(self, data: List[Dict[str, Any]], session_date: date) -> int:
        """
        Export market structure data.

        Args:
            data: List of market structure records (indices + tickers)
            session_date: The trading date

        Returns:
            Number of records exported
        """
        if not data:
            return 0

        # Deduplicate by (date, ticker) - keep last occurrence
        seen_keys = set()
        records = []
        for row in reversed(data):
            ticker = row.get("ticker")
            if not ticker:
                continue

            key = (session_date, ticker)
            if key in seen_keys:
                continue
            seen_keys.add(key)

            records.append({
                "date": session_date,
                "ticker": ticker,
                "ticker_id": row.get("ticker_id"),
                "is_index": row.get("is_index", False),
                "scan_price": row.get("scan_price") or row.get("price"),
                "d1_direction": row.get("d1_direction"),
                "d1_strong": row.get("d1_strong"),
                "d1_weak": row.get("d1_weak"),
                "h4_direction": row.get("h4_direction"),
                "h4_strong": row.get("h4_strong"),
                "h4_weak": row.get("h4_weak"),
                "h1_direction": row.get("h1_direction"),
                "h1_strong": row.get("h1_strong"),
                "h1_weak": row.get("h1_weak"),
                "m15_direction": row.get("m15_direction"),
                "m15_strong": row.get("m15_strong"),
                "m15_weak": row.get("m15_weak"),
                "composite_direction": row.get("composite_direction"),
            })

        # Reverse back to original order
        records.reverse()

        if not records:
            return 0

        return self.upsert_many(records)

    def validate(self, data: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """Validate market structure data."""
        errors = []

        if not data:
            errors.append("No market structure data provided")
            return False, errors

        valid_directions = ["Bull", "Bull+", "Bear", "Bear+", "Neutral", "ERROR", None]

        for i, row in enumerate(data):
            if not row.get("ticker"):
                errors.append(f"Row {i}: Missing ticker")

            # Validate direction values
            for field in ["d1_direction", "h4_direction", "h1_direction",
                         "m15_direction", "composite_direction"]:
                value = row.get(field)
                if value and value not in valid_directions:
                    errors.append(f"Row {i}: Invalid {field} value: {value}")

        return len(errors) == 0, errors
