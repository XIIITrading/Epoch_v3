"""
Epoch Trading System - Options Analysis Exporter (v1.0)
Exports options_analysis worksheet to options_analysis table.

Options overlay analysis for hypothetical options trades based on equity entry/exit signals.
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


def excel_date_to_python_date(excel_date) -> date:
    """Convert Excel date to Python date object."""
    if excel_date is None:
        return None
    if isinstance(excel_date, date):
        return excel_date
    if isinstance(excel_date, datetime):
        return excel_date.date()
    if isinstance(excel_date, (int, float)):
        # Excel serial date (days since 1899-12-30)
        from datetime import timedelta
        base_date = date(1899, 12, 30)
        return base_date + timedelta(days=int(excel_date))
    if isinstance(excel_date, str):
        # Try common date formats
        for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y"]:
            try:
                return datetime.strptime(excel_date, fmt).date()
            except ValueError:
                continue
    return None


class OptionsAnalysisExporter(BaseExporter):
    """Exports options analysis data (1:1 with trades) - v1.0."""

    TABLE_NAME = "options_analysis"
    PRIMARY_KEY = ["trade_id"]

    def export(self, data: List[Dict[str, Any]], session_date: date) -> int:
        """
        Export options analysis data.

        Args:
            data: List of options analysis records (1 per trade)
            session_date: The trading date

        Returns:
            Number of records exported
        """
        if not data:
            return 0

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

        # Helper to safely convert to string
        def safe_str(val):
            if val is None or val == "":
                return None
            return str(val).strip()

        # Deduplicate by trade_id - keep last occurrence
        seen_keys = set()
        records = []
        for row in reversed(data):
            trade_id = row.get("trade_id")

            # Skip rows without trade_id
            if not trade_id:
                continue

            if trade_id in seen_keys:
                continue
            seen_keys.add(trade_id)

            # Convert date and time fields
            entry_date = excel_date_to_python_date(row.get("entry_date"))
            expiration = excel_date_to_python_date(row.get("expiration"))
            entry_time = excel_time_to_python_time(row.get("entry_time"))
            option_entry_time = excel_time_to_python_time(row.get("option_entry_time"))
            option_exit_time = excel_time_to_python_time(row.get("option_exit_time"))

            records.append({
                # Trade Identification (A-F)
                "trade_id": trade_id,
                "ticker": safe_str(row.get("ticker")),
                "direction": safe_str(row.get("direction")),
                "entry_date": entry_date or session_date,  # Fallback to session_date
                "entry_time": entry_time,
                "entry_price": safe_float(row.get("entry_price")),

                # Contract Selection (G-J)
                "options_ticker": safe_str(row.get("options_ticker")),
                "strike": safe_float(row.get("strike")),
                "expiration": expiration,
                "contract_type": safe_str(row.get("contract_type")),

                # Options Trade Data (K-N)
                "option_entry_price": safe_float(row.get("option_entry_price")),
                "option_entry_time": option_entry_time,
                "option_exit_price": safe_float(row.get("option_exit_price")),
                "option_exit_time": option_exit_time,

                # P&L Metrics (O-R)
                "pnl_dollars": safe_float(row.get("pnl_dollars")),
                "pnl_percent": safe_float(row.get("pnl_percent")),
                "option_r": safe_float(row.get("option_r")),
                "net_return": safe_float(row.get("net_return")),

                # Comparison Metrics (S-U)
                "underlying_r": safe_float(row.get("underlying_r")),
                "r_multiplier": safe_float(row.get("r_multiplier")),
                "win": safe_int(row.get("win")),

                # Status (V)
                "status": safe_str(row.get("status")),
            })

        # Reverse back to original order
        records.reverse()

        if not records:
            return 0

        return self.upsert_many(records)

    def delete_by_date(self, session_date: date) -> int:
        """
        Delete all options analysis records for a given date.

        Args:
            session_date: The date to delete records for

        Returns:
            Number of records deleted
        """
        query = f"DELETE FROM {self.TABLE_NAME} WHERE entry_date = %s"
        with self._conn.cursor() as cur:
            cur.execute(query, (session_date,))
            return cur.rowcount

    def validate(self, data: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """Validate options analysis data."""
        errors = []

        if not data:
            return True, []

        valid_directions = ["LONG", "SHORT", None]
        valid_contract_types = ["CALL", "PUT", None]
        valid_statuses = [
            "SUCCESS",
            "INVALID_DATA",
            "NO_CHAIN",
            "NO_CONTRACT",
            "NO_ENTRY_BARS",
            "NO_EXIT_BARS",
            "NO_MATCHING_BARS",
            None
        ]

        for i, row in enumerate(data):
            if not row.get("trade_id"):
                errors.append(f"Row {i}: Missing trade_id")

            direction = row.get("direction")
            if direction and direction not in valid_directions:
                errors.append(f"Row {i}: Invalid direction: {direction}")

            contract_type = row.get("contract_type")
            if contract_type and contract_type not in valid_contract_types:
                errors.append(f"Row {i}: Invalid contract_type: {contract_type}")

            status = row.get("status")
            if status and status not in valid_statuses:
                errors.append(f"Row {i}: Invalid status: {status}")

            # Validate win is 0 or 1
            win = row.get("win")
            if win is not None and win not in [0, 1, "0", "1", 0.0, 1.0]:
                errors.append(f"Row {i}: Invalid win value: {win} (must be 0 or 1)")

            # If status is SUCCESS, should have options data
            if status == "SUCCESS":
                if not row.get("options_ticker"):
                    errors.append(f"Row {i}: SUCCESS status but missing options_ticker")
                if row.get("option_entry_price") is None:
                    errors.append(f"Row {i}: SUCCESS status but missing option_entry_price")

        return len(errors) == 0, errors
