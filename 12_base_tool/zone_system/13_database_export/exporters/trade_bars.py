"""
Epoch Trading System - Trade Bars Exporter
Exports trade_bars worksheet to trade_bars table.

Version: 1.0.0 - Initial release (sources from trade_bars v1.2.0)

The trade_bars table is the granular source of truth for all trade analysis.
Contains ALL M5 bars within each trade with full indicator snapshots.
Enables SQL-based derivative calculations (MFE/MAE, patterns, ML training).
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
        total_seconds = int(excel_time * 24 * 3600)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return time(hour=hours % 24, minute=minutes, second=seconds)
    return None


class TradeBarsExporter(BaseExporter):
    """
    Exports trade bar data (many:1 with trades) - v1.2.0 schema.

    Each trade has multiple bars (ENTRY, IN_TRADE, EXIT).
    Primary key is (trade_id, event_seq) for uniqueness.
    """

    TABLE_NAME = "trade_bars"
    PRIMARY_KEY = ["trade_id", "event_seq"]

    def export(self, data: List[Dict[str, Any]], session_date: date) -> int:
        """
        Export trade bars data.

        Args:
            data: List of trade bar records (multiple per trade)
            session_date: The trading date

        Returns:
            Number of records exported
        """
        if not data:
            return 0

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

        def safe_float(val):
            if val is None or val == "" or val == "N/A":
                return None
            if isinstance(val, (int, float)):
                return float(val)
            try:
                return float(val)
            except (ValueError, TypeError):
                return None

        def safe_str(val):
            if val is None or val == "":
                return None
            return str(val).strip()

        def safe_date(val):
            if val is None:
                return None
            if isinstance(val, date):
                return val
            if isinstance(val, datetime):
                return val.date()
            return None

        # Deduplicate by primary key (trade_id, event_seq)
        seen_keys = set()
        records = []

        for row in data:
            trade_id = row.get("trade_id")
            event_seq = safe_int(row.get("event_seq"))

            if not trade_id or event_seq is None:
                continue

            key = (trade_id, event_seq)
            if key in seen_keys:
                continue
            seen_keys.add(key)

            event_time = excel_time_to_python_time(row.get("event_time"))

            records.append({
                # Trade Identification (A-B)
                "trade_id": trade_id,
                "date": safe_date(row.get("date")) or session_date,

                # Bar Identification (C-F)
                "event_seq": event_seq,
                "event_time": event_time,
                "bars_from_entry": safe_int(row.get("bars_from_entry")),
                "event_type": safe_str(row.get("event_type")),

                # OHLCV (G-K)
                "open_price": safe_float(row.get("open_price")),
                "high_price": safe_float(row.get("high_price")),
                "low_price": safe_float(row.get("low_price")),
                "close_price": safe_float(row.get("close_price")),
                "volume": safe_int(row.get("volume")),

                # R-Value (L)
                "r_at_event": safe_float(row.get("r_at_event")),

                # Health Score (M)
                "health_score": safe_int(row.get("health_score")),

                # Price Indicators (N-P)
                "vwap": safe_float(row.get("vwap")),
                "sma9": safe_float(row.get("sma9")),
                "sma21": safe_float(row.get("sma21")),

                # Volume Indicators (Q-S)
                "vol_roc": safe_float(row.get("vol_roc")),
                "vol_delta": safe_float(row.get("vol_delta")),
                "cvd_slope": safe_float(row.get("cvd_slope")),

                # SMA Analysis (T-U)
                "sma_spread": safe_float(row.get("sma_spread")),
                "sma_momentum": safe_str(row.get("sma_momentum")),

                # Structure (V-Y)
                "m5_structure": safe_str(row.get("m5_structure")),
                "m15_structure": safe_str(row.get("m15_structure")),
                "h1_structure": safe_str(row.get("h1_structure")),
                "h4_structure": safe_str(row.get("h4_structure")),

                # Health Summary (Z)
                "health_summary": safe_str(row.get("health_summary")),

                # Trade Context (AA-AG)
                "ticker": safe_str(row.get("ticker")),
                "direction": safe_str(row.get("direction")),
                "model": safe_str(row.get("model")),
                "win": safe_int(row.get("win")),
                "actual_r": safe_float(row.get("actual_r")),
                "exit_reason": safe_str(row.get("exit_reason")),
                "entry_health": safe_int(row.get("entry_health")),
            })

        if not records:
            return 0

        return self.upsert_many(records)

    def delete_by_trade_ids(self, trade_ids: List[str]) -> int:
        """
        Delete all trade bars for given trade IDs.

        Args:
            trade_ids: List of trade IDs to delete bars for

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
        """Validate trade bars data."""
        errors = []

        if not data:
            return True, []

        valid_event_types = ["ENTRY", "IN_TRADE", "EXIT", None]
        valid_structures = ["BULL", "BEAR", "NEUTRAL", None]
        valid_sma_momentum = ["WIDENING", "NARROWING", "FLAT", None]
        valid_health_summary = ["STRONG", "MODERATE", "WEAK", "CRITICAL", None]
        valid_directions = ["LONG", "SHORT", None]

        for i, row in enumerate(data):
            if not row.get("trade_id"):
                errors.append(f"Row {i}: Missing trade_id")

            event_seq = row.get("event_seq")
            if event_seq is None:
                errors.append(f"Row {i}: Missing event_seq")

            event_type = row.get("event_type")
            if event_type and event_type not in valid_event_types:
                errors.append(f"Row {i}: Invalid event_type: {event_type}")

            for field, valid_values, field_name in [
                (row.get("m5_structure"), valid_structures, "m5_structure"),
                (row.get("m15_structure"), valid_structures, "m15_structure"),
                (row.get("h1_structure"), valid_structures, "h1_structure"),
                (row.get("h4_structure"), valid_structures, "h4_structure"),
                (row.get("sma_momentum"), valid_sma_momentum, "sma_momentum"),
                (row.get("health_summary"), valid_health_summary, "health_summary"),
                (row.get("direction"), valid_directions, "direction"),
            ]:
                if field and field not in valid_values:
                    errors.append(f"Row {i}: Invalid {field_name}: {field}")

            health_score = row.get("health_score")
            if health_score is not None:
                try:
                    hs = int(health_score)
                    if hs < 0 or hs > 10:
                        errors.append(f"Row {i}: Invalid health_score: {health_score} (must be 0-10)")
                except (ValueError, TypeError):
                    errors.append(f"Row {i}: Invalid health_score type: {health_score}")

            win = row.get("win")
            if win is not None and win not in [0, 1, "0", "1", 0.0, 1.0]:
                errors.append(f"Row {i}: Invalid win value: {win} (must be 0 or 1)")

        return len(errors) == 0, errors
