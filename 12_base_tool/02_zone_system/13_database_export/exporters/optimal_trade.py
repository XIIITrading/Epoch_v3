"""
Epoch Trading System - Optimal Trade Exporter (v4.0.0)
Exports optimal_trade worksheet to optimal_trade table.

Simplified 4-row analysis view per trade (ENTRY, MFE, MAE, EXIT).
28 columns (A-AB) capturing indicator state at key moments.
"""

from datetime import date, datetime, time
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


class OptimalTradeExporter(BaseExporter):
    """Exports simplified 4-row analysis view (v4.0.0)."""

    TABLE_NAME = "optimal_trade"
    PRIMARY_KEY = ["trade_id", "event_type"]

    def export(self, data: List[Dict[str, Any]], session_date: date) -> int:
        """
        Export optimal trade analysis data.

        Args:
            data: List of optimal trade records (4 per trade: ENTRY, MFE, MAE, EXIT)
            session_date: The trading date

        Returns:
            Number of records exported
        """
        if not data:
            return 0

        # Helper to safely convert to integer
        def safe_int(val):
            if val is None:
                return None
            if isinstance(val, int):
                return val
            if isinstance(val, float):
                return int(val)
            if isinstance(val, datetime):
                return None
            try:
                return int(val)
            except (ValueError, TypeError):
                return None

        # Helper to safely convert to float
        def safe_float(val):
            if val is None or val == "" or val == "N/A":
                return None
            if isinstance(val, (int, float)):
                return float(val)
            try:
                return float(val)
            except (ValueError, TypeError):
                return None

        # Helper to safely convert to string
        def safe_str(val):
            if val is None or val == "":
                return None
            return str(val).strip()

        # Deduplicate by primary key (trade_id, event_type) - first one wins
        seen_keys = set()
        records = []
        for row in data:
            trade_id = row.get("trade_id")
            event_type = safe_str(row.get("event_type"))

            # Skip invalid rows
            if not trade_id or not event_type:
                continue

            # Deduplicate
            key = (trade_id, event_type)
            if key in seen_keys:
                continue
            seen_keys.add(key)

            # Convert event_time (Excel stores as fraction of day)
            event_time = excel_time_to_python_time(row.get("event_time"))

            # Handle date - use session_date if not provided or invalid
            row_date = row.get("date")
            if isinstance(row_date, date):
                record_date = row_date
            elif isinstance(row_date, datetime):
                record_date = row_date.date()
            else:
                record_date = session_date

            records.append({
                # Trade Identification (A-F)
                "trade_id": trade_id,
                "date": record_date,
                "ticker": safe_str(row.get("ticker")),
                "direction": safe_str(row.get("direction")),
                "model": safe_str(row.get("model")),
                "win": safe_int(row.get("win")),

                # Event Identification (G-K)
                "event_type": event_type,
                "event_time": event_time,
                "bars_from_entry": safe_int(row.get("bars_from_entry")),
                "price_at_event": safe_float(row.get("price_at_event")),
                "r_at_event": safe_float(row.get("r_at_event")),

                # Health Metrics (L-N)
                "health_score": safe_int(row.get("health_score")),
                "health_delta": safe_int(row.get("health_delta")),
                "health_summary": safe_str(row.get("health_summary")),

                # Indicator Values (O-R)
                "vwap": safe_float(row.get("vwap")),
                "sma9": safe_float(row.get("sma9")),
                "sma21": safe_float(row.get("sma21")),
                "sma_spread": safe_float(row.get("sma_spread")),

                # SMA & Volume Analysis (S-U)
                "sma_momentum": safe_str(row.get("sma_momentum")),
                "vol_roc": safe_float(row.get("vol_roc")),
                "vol_delta": safe_float(row.get("vol_delta")),

                # CVD (V)
                "cvd_slope": safe_float(row.get("cvd_slope")),

                # Structure (W-Z)
                "m5_structure": safe_str(row.get("m5_structure")),
                "m15_structure": safe_str(row.get("m15_structure")),
                "h1_structure": safe_str(row.get("h1_structure")),
                "h4_structure": safe_str(row.get("h4_structure")),

                # Trade Outcome (AA-AB)
                "actual_r": safe_float(row.get("actual_r")),
                "exit_reason": safe_str(row.get("exit_reason")),
            })

        if not records:
            return 0

        return self.upsert_many(records)

    def delete_by_trade_ids(self, trade_ids: List[str]) -> int:
        """
        Delete all optimal trade rows for given trade IDs.
        Useful for re-processing trades.

        Args:
            trade_ids: List of trade IDs to delete rows for

        Returns:
            Number of records deleted
        """
        if not trade_ids:
            return 0

        placeholders = ", ".join(["%s"] * len(trade_ids))
        query = f"DELETE FROM {self.TABLE_NAME} WHERE trade_id IN ({placeholders})"

        with self._conn.cursor() as cur:
            cur.execute(query, tuple(trade_ids))
            return cur.rowcount

    def validate(self, data: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """Validate optimal trade data."""
        errors = []

        if not data:
            return True, []

        # Valid event types (only 4 for optimal_trade)
        valid_event_types = ["ENTRY", "MFE", "MAE", "EXIT"]
        valid_directions = ["LONG", "SHORT", None]
        valid_models = ["EPCH1", "EPCH2", "EPCH3", "EPCH4", None]
        valid_structures = ["BULL", "BEAR", "NEUTRAL", None]
        valid_sma_momentum = ["WIDENING", "NARROWING", "FLAT", None]
        valid_health_summary = ["IMPROVING", "DEGRADING", "STABLE", None]
        valid_exit_reasons = ["STOP", "TARGET_3R", "TARGET_CALC", "CHOCH", "EOD", None]

        for i, row in enumerate(data):
            if not row.get("trade_id"):
                errors.append(f"Row {i}: Missing trade_id")

            event_type = row.get("event_type")
            if not event_type:
                errors.append(f"Row {i}: Missing event_type")
            elif event_type not in valid_event_types:
                errors.append(f"Row {i}: Invalid event_type: {event_type} (must be ENTRY, MFE, MAE, or EXIT)")

            direction = row.get("direction")
            if direction and direction not in valid_directions:
                errors.append(f"Row {i}: Invalid direction: {direction}")

            model = row.get("model")
            if model and model not in valid_models:
                errors.append(f"Row {i}: Invalid model: {model}")

            # Structure validations
            for field, field_name in [
                (row.get("m5_structure"), "m5_structure"),
                (row.get("m15_structure"), "m15_structure"),
                (row.get("h1_structure"), "h1_structure"),
                (row.get("h4_structure"), "h4_structure"),
            ]:
                if field and field not in valid_structures:
                    errors.append(f"Row {i}: Invalid {field_name}: {field}")

            sma_momentum = row.get("sma_momentum")
            if sma_momentum and sma_momentum not in valid_sma_momentum:
                errors.append(f"Row {i}: Invalid sma_momentum: {sma_momentum}")

            health_summary = row.get("health_summary")
            if health_summary and health_summary not in valid_health_summary:
                errors.append(f"Row {i}: Invalid health_summary: {health_summary}")

            exit_reason = row.get("exit_reason")
            if exit_reason and exit_reason not in valid_exit_reasons:
                errors.append(f"Row {i}: Invalid exit_reason: {exit_reason}")

            win = row.get("win")
            if win is not None and win not in [0, 1, "0", "1", 0.0, 1.0]:
                errors.append(f"Row {i}: Invalid win value: {win} (must be 0 or 1)")

        return len(errors) == 0, errors
