"""
Epoch Trading System - Bar Data Exporter
Exports bar_data worksheet (OHLC, ATR, Options, Camarilla) to bar_data table.
"""

from datetime import date
from typing import Any, Dict, List, Tuple
from .base_exporter import BaseExporter


class BarDataExporter(BaseExporter):
    """Exports bar data (wide format - all metrics per ticker per day)."""

    TABLE_NAME = "bar_data"
    PRIMARY_KEY = ["date", "ticker_id"]

    def export(self, data: List[Dict[str, Any]], session_date: date) -> int:
        """
        Export bar data.

        Args:
            data: List of bar data records (one per ticker)
            session_date: The trading date

        Returns:
            Number of records exported
        """
        if not data:
            return 0

        records = []
        for row in data:
            records.append({
                "date": session_date,
                "ticker_id": row.get("ticker_id"),
                "ticker": row.get("ticker"),
                "price": row.get("price"),
                # Monthly
                "m1_open": row.get("m1_open"),
                "m1_high": row.get("m1_high"),
                "m1_low": row.get("m1_low"),
                "m1_close": row.get("m1_close"),
                "m1_prior_open": row.get("m1_prior_open"),
                "m1_prior_high": row.get("m1_prior_high"),
                "m1_prior_low": row.get("m1_prior_low"),
                "m1_prior_close": row.get("m1_prior_close"),
                # Weekly
                "w1_open": row.get("w1_open"),
                "w1_high": row.get("w1_high"),
                "w1_low": row.get("w1_low"),
                "w1_close": row.get("w1_close"),
                "w1_prior_open": row.get("w1_prior_open"),
                "w1_prior_high": row.get("w1_prior_high"),
                "w1_prior_low": row.get("w1_prior_low"),
                "w1_prior_close": row.get("w1_prior_close"),
                # Daily
                "d1_open": row.get("d1_open"),
                "d1_high": row.get("d1_high"),
                "d1_low": row.get("d1_low"),
                "d1_close": row.get("d1_close"),
                "d1_prior_open": row.get("d1_prior_open"),
                "d1_prior_high": row.get("d1_prior_high"),
                "d1_prior_low": row.get("d1_prior_low"),
                "d1_prior_close": row.get("d1_prior_close"),
                # Overnight
                "d1_overnight_high": row.get("d1_overnight_high"),
                "d1_overnight_low": row.get("d1_overnight_low"),
                # Options
                "op_01": row.get("op_01"),
                "op_02": row.get("op_02"),
                "op_03": row.get("op_03"),
                "op_04": row.get("op_04"),
                "op_05": row.get("op_05"),
                "op_06": row.get("op_06"),
                "op_07": row.get("op_07"),
                "op_08": row.get("op_08"),
                "op_09": row.get("op_09"),
                "op_10": row.get("op_10"),
                # ATR
                "m5_atr": row.get("m5_atr"),
                "m15_atr": row.get("m15_atr"),
                "h1_atr": row.get("h1_atr"),
                "d1_atr": row.get("d1_atr"),
                # Camarilla Daily
                "d1_cam_s6": row.get("d1_cam_s6"),
                "d1_cam_s4": row.get("d1_cam_s4"),
                "d1_cam_s3": row.get("d1_cam_s3"),
                "d1_cam_r3": row.get("d1_cam_r3"),
                "d1_cam_r4": row.get("d1_cam_r4"),
                "d1_cam_r6": row.get("d1_cam_r6"),
                # Camarilla Weekly
                "w1_cam_s6": row.get("w1_cam_s6"),
                "w1_cam_s4": row.get("w1_cam_s4"),
                "w1_cam_s3": row.get("w1_cam_s3"),
                "w1_cam_r3": row.get("w1_cam_r3"),
                "w1_cam_r4": row.get("w1_cam_r4"),
                "w1_cam_r6": row.get("w1_cam_r6"),
                # Camarilla Monthly
                "m1_cam_s6": row.get("m1_cam_s6"),
                "m1_cam_s4": row.get("m1_cam_s4"),
                "m1_cam_s3": row.get("m1_cam_s3"),
                "m1_cam_r3": row.get("m1_cam_r3"),
                "m1_cam_r4": row.get("m1_cam_r4"),
                "m1_cam_r6": row.get("m1_cam_r6"),
            })

        return self.upsert_many(records)

    def validate(self, data: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """Validate bar data."""
        errors = []

        if not data:
            errors.append("No bar data provided")
            return False, errors

        for i, row in enumerate(data):
            if not row.get("ticker_id"):
                errors.append(f"Row {i}: Missing ticker_id")
            if not row.get("ticker"):
                errors.append(f"Row {i}: Missing ticker")

        return len(errors) == 0, errors
