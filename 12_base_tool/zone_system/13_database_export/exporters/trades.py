"""
Epoch Trading System - Trades Exporter
Exports backtest worksheet trade log to trades table.
"""

from datetime import date, datetime, time, timedelta
from typing import Any, Dict, List, Tuple
from .base_exporter import BaseExporter


def excel_time_to_python_time(excel_time) -> time:
    """Convert Excel serial time (fraction of day) to Python time object."""
    if excel_time is None:
        return None
    if isinstance(excel_time, time):
        return excel_time
    if isinstance(excel_time, datetime):
        return excel_time.time()
    if isinstance(excel_time, (int, float)):
        # Excel stores time as fraction of day (0.5 = 12:00 noon)
        total_seconds = int(excel_time * 24 * 3600)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return time(hour=hours % 24, minute=minutes, second=seconds)
    return None


class TradesExporter(BaseExporter):
    """Exports trade log from backtest."""

    TABLE_NAME = "trades"
    PRIMARY_KEY = ["trade_id"]

    def export(self, data: List[Dict[str, Any]], session_date: date) -> int:
        """
        Export trades data.

        Args:
            data: List of trade records
            session_date: The trading date

        Returns:
            Number of records exported
        """
        if not data:
            return 0

        # Deduplicate by trade_id - keep last occurrence
        seen_keys = set()
        records = []
        for row in reversed(data):
            trade_id = row.get("trade_id")
            if not trade_id:
                continue

            if trade_id in seen_keys:
                continue
            seen_keys.add(trade_id)

            # Convert time fields (Excel stores as fraction of day)
            entry_time = excel_time_to_python_time(row.get("entry_time"))
            exit_time = excel_time_to_python_time(row.get("exit_time"))

            records.append({
                "trade_id": trade_id,
                "date": session_date,
                "ticker": row.get("ticker"),
                "model": row.get("model"),
                "zone_type": row.get("zone_type"),
                "direction": row.get("direction"),
                "zone_high": row.get("zone_high"),
                "zone_low": row.get("zone_low"),
                "entry_price": row.get("entry_price"),
                "entry_time": entry_time,
                "stop_price": row.get("stop_price"),
                "target_3r": row.get("target_3r"),
                "target_calc": row.get("target_calc"),
                "target_used": row.get("target_used"),
                "exit_price": row.get("exit_price"),
                "exit_time": exit_time,
                "exit_reason": row.get("exit_reason"),
                "pnl_dollars": row.get("pnl_dollars"),
                "pnl_r": row.get("pnl_r"),
                "risk": row.get("risk"),
                "is_winner": row.get("is_winner", False),
            })

        # Reverse back to original order
        records.reverse()

        if not records:
            return 0

        return self.upsert_many(records)

    def validate(self, data: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """Validate trades data."""
        errors = []

        if not data:
            # Empty trades is valid (no signals for the day)
            return True, []

        valid_models = ["EPCH1", "EPCH2", "EPCH3", "EPCH4"]
        valid_zone_types = ["PRIMARY", "SECONDARY", None]
        valid_directions = ["LONG", "SHORT", None]
        valid_exit_reasons = ["STOP", "TARGET_3R", "TARGET_CALC", "CHOCH", "EOD", None]

        for i, row in enumerate(data):
            if not row.get("trade_id"):
                errors.append(f"Row {i}: Missing trade_id")
            if not row.get("ticker"):
                errors.append(f"Row {i}: Missing ticker")

            model = row.get("model")
            if model and model not in valid_models:
                errors.append(f"Row {i}: Invalid model: {model}")

            zone_type = row.get("zone_type")
            if zone_type and zone_type not in valid_zone_types:
                errors.append(f"Row {i}: Invalid zone_type: {zone_type}")

            direction = row.get("direction")
            if direction and direction not in valid_directions:
                errors.append(f"Row {i}: Invalid direction: {direction}")

            exit_reason = row.get("exit_reason")
            if exit_reason and exit_reason not in valid_exit_reasons:
                errors.append(f"Row {i}: Invalid exit_reason: {exit_reason}")

        return len(errors) == 0, errors
