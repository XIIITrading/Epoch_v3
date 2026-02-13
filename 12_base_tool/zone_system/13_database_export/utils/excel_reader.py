"""
Epoch Trading System - Database Export Excel Reader
Reads worksheet data from epoch_v1.xlsm for database export.

Uses xlwings to read from live Excel instance (consistent with other EPOCH modules).
Works whether workbook is open or closed.

Version: 3.0.0 - Removed entry_events and exit_events (deprecated)
                 Added trade_bars v1.2.0 (33 columns)
"""

from datetime import datetime, date, time
from typing import List, Dict, Any, Optional
from pathlib import Path
import xlwings as xw
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import EXCEL_PATH, WORKSHEETS


class ExcelReader:
    """
    Reads data from EPOCH Excel workbook using xlwings.

    Connects to open workbook if available, otherwise opens the file.
    This ensures we read live data even if the workbook hasn't been saved.
    """

    def __init__(self, workbook_path: Path = None):
        self.workbook_path = workbook_path or EXCEL_PATH
        self._wb = None
        self._app = None
        self._opened_by_us = False

    def open(self):
        """Open or connect to the workbook."""
        if self._wb is not None:
            return

        workbook_name = self.workbook_path.name

        # First, try to connect to already-open workbook
        try:
            for app in xw.apps:
                for book in app.books:
                    if book.name.lower() == workbook_name.lower():
                        self._wb = book
                        self._app = app
                        self._opened_by_us = False
                        print(f"  Connected to open workbook: {workbook_name}")
                        return
        except Exception:
            pass

        # If not open, open it ourselves
        try:
            self._wb = xw.Book(str(self.workbook_path))
            self._app = self._wb.app
            self._opened_by_us = True
            print(f"  Opened workbook: {self.workbook_path}")
        except Exception as e:
            raise FileNotFoundError(f"Could not open workbook: {self.workbook_path}\n{e}")

    def close(self):
        """Close workbook only if we opened it (keep user's open workbook open)."""
        if self._wb and self._opened_by_us:
            try:
                self._wb.close()
                print("  Closed workbook")
            except Exception:
                pass
        self._wb = None
        self._app = None

    def get_sheet(self, sheet_name: str) -> xw.Sheet:
        """Get a worksheet by name."""
        if self._wb is None:
            self.open()

        # Try exact name first, then try from WORKSHEETS mapping
        try:
            return self._wb.sheets[sheet_name]
        except KeyError:
            mapped_name = WORKSHEETS.get(sheet_name, sheet_name)
            return self._wb.sheets[mapped_name]

    def read_range(self, sheet_name: str, range_str: str) -> List[List[Any]]:
        """Read a range of cells as a 2D list."""
        sheet = self.get_sheet(sheet_name)
        data = sheet.range(range_str).value

        # Ensure we always return a 2D list
        if data is None:
            return []
        if not isinstance(data, list):
            return [[data]]
        if data and not isinstance(data[0], list):
            return [data]
        return data

    def get_session_date(self) -> date:
        """
        Get the session date from the backtest worksheet.
        Reads from the first trade's date column.
        """
        sheet = self.get_sheet("backtest")

        # Date is in column B, row 2 (first data row after header)
        date_val = sheet.range("B2").value

        if date_val is None:
            # Fallback to today
            return date.today()

        if isinstance(date_val, datetime):
            return date_val.date()
        if isinstance(date_val, date):
            return date_val

        # Try to parse string date
        if isinstance(date_val, str):
            for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y"]:
                try:
                    return datetime.strptime(date_val, fmt).date()
                except ValueError:
                    continue

        return date.today()

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _safe_float(self, val, default: float = None) -> Optional[float]:
        """Convert value to float safely."""
        if val is None or val == "" or val == "N/A":
            return default
        try:
            return float(val)
        except (ValueError, TypeError):
            return default

    def _safe_int(self, val, default: int = None) -> Optional[int]:
        """Convert value to int safely.

        Handles Excel quirk where integer columns formatted as dates
        come in as datetime objects (e.g., 0 -> 1899-12-30, 1 -> 1899-12-31).
        """
        if val is None or val == "" or val == "N/A":
            return default
        if isinstance(val, datetime):
            # Excel serial date conversion: dates near 1899-12-30 are actually small integers
            # 1899-12-30 = 0, 1899-12-31 = 1, 1900-01-01 = 2, etc.
            base_date = datetime(1899, 12, 30)
            days_diff = (val - base_date).days
            # If it's a "date" close to the Excel epoch, it's likely an integer
            if -1 <= days_diff <= 10000:  # Reasonable range for event_seq, bars_from_entry, etc.
                return days_diff
            return default
        try:
            return int(val)
        except (ValueError, TypeError):
            return default

    def _safe_str(self, val, default: str = None) -> Optional[str]:
        """Convert value to string safely."""
        if val is None or val == "":
            return default
        return str(val).strip()

    def _safe_bool(self, val) -> Optional[bool]:
        """Convert value to bool, handling various formats."""
        if val is None:
            return None
        if isinstance(val, bool):
            return val
        if isinstance(val, (int, float)):
            return val == 1
        if isinstance(val, str):
            return val.upper() in ('TRUE', '1', 'YES', 'W', 'WIN')
        return None

    def _format_time(self, val) -> Optional[time]:
        """Convert Excel time to Python time object."""
        if val is None:
            return None
        if isinstance(val, time):
            return val
        if isinstance(val, datetime):
            return val.time()
        if isinstance(val, (int, float)):
            # Excel serial time (fraction of day)
            total_seconds = int(val * 24 * 3600)
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            return time(hour=hours % 24, minute=minutes, second=seconds)
        return None

    def _format_date(self, val) -> Optional[date]:
        """Convert Excel date to Python date object."""
        if val is None:
            return None
        if isinstance(val, date):
            return val
        if isinstance(val, datetime):
            return val.date()
        if isinstance(val, (int, float)):
            # Excel serial date
            from datetime import timedelta
            base_date = date(1899, 12, 30)
            return base_date + timedelta(days=int(val))
        if isinstance(val, str):
            for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y"]:
                try:
                    return datetime.strptime(val, fmt).date()
                except ValueError:
                    continue
        return None

    # =========================================================================
    # Market Structure Reading
    # =========================================================================

    def read_market_structure_indices(self) -> List[Dict[str, Any]]:
        """Read market structure for indices (SPY, QQQ, IWM, DIA) from market_overview."""
        sheet = self.get_sheet("market_overview")

        # Indices are in rows 5-8 (SPY, QQQ, IWM, DIA)
        data = sheet.range("B5:R8").value
        if not data:
            return []

        results = []
        for row in data:
            if row and row[1]:  # Has ticker (column C, index 1)
                results.append({
                    "ticker_id": self._safe_str(row[0]),
                    "ticker": self._safe_str(row[1]),
                    "date": self._format_date(row[2]),
                    "price": self._safe_float(row[3]),
                    "d1_direction": self._safe_str(row[4]),
                    "d1_structure": self._safe_str(row[5]),
                    "d1_trend": self._safe_str(row[6]),
                    "h4_direction": self._safe_str(row[7]),
                    "h4_structure": self._safe_str(row[8]),
                    "h4_trend": self._safe_str(row[9]),
                    "h1_direction": self._safe_str(row[10]),
                    "h1_structure": self._safe_str(row[11]),
                    "h1_trend": self._safe_str(row[12]),
                    "m15_direction": self._safe_str(row[13]),
                    "m15_structure": self._safe_str(row[14]),
                    "m15_trend": self._safe_str(row[15]),
                    "composite_direction": self._safe_str(row[16]),
                })
        return results

    def read_market_structure_tickers(self) -> List[Dict[str, Any]]:
        """Read market structure for user tickers from market_overview."""
        sheet = self.get_sheet("market_overview")

        # User tickers are in rows 36-45
        data = sheet.range("B36:R45").value
        if not data:
            return []

        results = []
        for row in data:
            if row and row[1]:  # Has ticker
                results.append({
                    "ticker_id": self._safe_str(row[0]),
                    "ticker": self._safe_str(row[1]),
                    "date": self._format_date(row[2]),
                    "price": self._safe_float(row[3]),
                    "d1_direction": self._safe_str(row[4]),
                    "d1_structure": self._safe_str(row[5]),
                    "d1_trend": self._safe_str(row[6]),
                    "h4_direction": self._safe_str(row[7]),
                    "h4_structure": self._safe_str(row[8]),
                    "h4_trend": self._safe_str(row[9]),
                    "h1_direction": self._safe_str(row[10]),
                    "h1_structure": self._safe_str(row[11]),
                    "h1_trend": self._safe_str(row[12]),
                    "m15_direction": self._safe_str(row[13]),
                    "m15_structure": self._safe_str(row[14]),
                    "m15_trend": self._safe_str(row[15]),
                    "composite_direction": self._safe_str(row[16]),
                })
        return results

    # =========================================================================
    # Bar Data Reading (Wide Format - All Metrics Per Ticker)
    # =========================================================================

    def read_bar_data(self) -> List[Dict[str, Any]]:
        """
        Read bar data from bar_data worksheet (wide format).

        The bar_data worksheet has 5 sections at different row ranges:
        - ticker_structure (rows 4-13): ticker_id, ticker, date, price
        - monthly_metrics (rows 17-26): M1 OHLC current + prior
        - weekly_metrics (rows 31-40): W1 OHLC current + prior
        - daily_metrics (rows 45-54): D1 OHLC current + prior
        - on_options_metrics (rows 73-82): Overnight, Options, ATR
        - add_metrics (rows 86-95): Camarilla pivots D1/W1/M1

        Returns one record per ticker with all metrics merged.
        """
        sheet = self.get_sheet("bar_data")

        # Read all 5 sections (10 rows each, columns B onwards)
        # ticker_structure: B4:E13 (ticker_id, ticker, date, price)
        ticker_data = sheet.range("B4:E13").value

        # monthly_metrics: B17:L26 (ticker_id, ticker, date, m1_open..m1_prior_close)
        monthly_data = sheet.range("B17:L26").value

        # weekly_metrics: B31:L40
        weekly_data = sheet.range("B31:L40").value

        # daily_metrics: B45:L54
        daily_data = sheet.range("B45:L54").value

        # on_options_metrics: B73:T82 (ticker_id, ticker, date, onh, onl, op_01-10, ATRs)
        on_options_data = sheet.range("B73:T82").value

        # add_metrics (Camarilla): B86:V95
        camarilla_data = sheet.range("B86:V95").value

        if not ticker_data:
            return []

        results = []
        for i in range(10):  # 10 tickers max (t1-t10)
            ticker_row = ticker_data[i] if i < len(ticker_data) else None
            if not ticker_row or not ticker_row[0]:  # No ticker_id
                continue

            # Extract ticker_id properly (format: "t1", "t2", etc.)
            raw_ticker_id = self._safe_str(ticker_row[0])
            # Handle cases like "NVDA_112825" -> extract just ticker, or "t1" -> keep as is
            if raw_ticker_id and "_" in raw_ticker_id:
                # This is likely the ticker_date format, extract position
                ticker_id = f"t{i+1}"
            else:
                ticker_id = raw_ticker_id if raw_ticker_id else f"t{i+1}"

            # Build record with all metrics
            record = {
                "ticker_id": ticker_id,
                "ticker": self._safe_str(ticker_row[1]),
                "price": self._safe_float(ticker_row[3]),
            }

            # Monthly metrics (row i from monthly_data)
            if monthly_data and i < len(monthly_data):
                m = monthly_data[i]
                if m:
                    record.update({
                        "m1_open": self._safe_float(m[3]) if len(m) > 3 else None,
                        "m1_high": self._safe_float(m[4]) if len(m) > 4 else None,
                        "m1_low": self._safe_float(m[5]) if len(m) > 5 else None,
                        "m1_close": self._safe_float(m[6]) if len(m) > 6 else None,
                        "m1_prior_open": self._safe_float(m[7]) if len(m) > 7 else None,
                        "m1_prior_high": self._safe_float(m[8]) if len(m) > 8 else None,
                        "m1_prior_low": self._safe_float(m[9]) if len(m) > 9 else None,
                        "m1_prior_close": self._safe_float(m[10]) if len(m) > 10 else None,
                    })

            # Weekly metrics
            if weekly_data and i < len(weekly_data):
                w = weekly_data[i]
                if w:
                    record.update({
                        "w1_open": self._safe_float(w[3]) if len(w) > 3 else None,
                        "w1_high": self._safe_float(w[4]) if len(w) > 4 else None,
                        "w1_low": self._safe_float(w[5]) if len(w) > 5 else None,
                        "w1_close": self._safe_float(w[6]) if len(w) > 6 else None,
                        "w1_prior_open": self._safe_float(w[7]) if len(w) > 7 else None,
                        "w1_prior_high": self._safe_float(w[8]) if len(w) > 8 else None,
                        "w1_prior_low": self._safe_float(w[9]) if len(w) > 9 else None,
                        "w1_prior_close": self._safe_float(w[10]) if len(w) > 10 else None,
                    })

            # Daily metrics
            if daily_data and i < len(daily_data):
                d = daily_data[i]
                if d:
                    record.update({
                        "d1_open": self._safe_float(d[3]) if len(d) > 3 else None,
                        "d1_high": self._safe_float(d[4]) if len(d) > 4 else None,
                        "d1_low": self._safe_float(d[5]) if len(d) > 5 else None,
                        "d1_close": self._safe_float(d[6]) if len(d) > 6 else None,
                        "d1_prior_open": self._safe_float(d[7]) if len(d) > 7 else None,
                        "d1_prior_high": self._safe_float(d[8]) if len(d) > 8 else None,
                        "d1_prior_low": self._safe_float(d[9]) if len(d) > 9 else None,
                        "d1_prior_close": self._safe_float(d[10]) if len(d) > 10 else None,
                    })

            # Overnight, Options, ATR metrics
            if on_options_data and i < len(on_options_data):
                o = on_options_data[i]
                if o:
                    record.update({
                        "d1_overnight_high": self._safe_float(o[3]) if len(o) > 3 else None,
                        "d1_overnight_low": self._safe_float(o[4]) if len(o) > 4 else None,
                        "op_01": self._safe_float(o[5]) if len(o) > 5 else None,
                        "op_02": self._safe_float(o[6]) if len(o) > 6 else None,
                        "op_03": self._safe_float(o[7]) if len(o) > 7 else None,
                        "op_04": self._safe_float(o[8]) if len(o) > 8 else None,
                        "op_05": self._safe_float(o[9]) if len(o) > 9 else None,
                        "op_06": self._safe_float(o[10]) if len(o) > 10 else None,
                        "op_07": self._safe_float(o[11]) if len(o) > 11 else None,
                        "op_08": self._safe_float(o[12]) if len(o) > 12 else None,
                        "op_09": self._safe_float(o[13]) if len(o) > 13 else None,
                        "op_10": self._safe_float(o[14]) if len(o) > 14 else None,
                        "m5_atr": self._safe_float(o[15]) if len(o) > 15 else None,
                        "m15_atr": self._safe_float(o[16]) if len(o) > 16 else None,
                        "h1_atr": self._safe_float(o[17]) if len(o) > 17 else None,
                        "d1_atr": self._safe_float(o[18]) if len(o) > 18 else None,
                    })

            # Camarilla metrics
            if camarilla_data and i < len(camarilla_data):
                c = camarilla_data[i]
                if c:
                    record.update({
                        # Daily Camarilla (cols E-J, indices 3-8)
                        "d1_cam_s6": self._safe_float(c[3]) if len(c) > 3 else None,
                        "d1_cam_s4": self._safe_float(c[4]) if len(c) > 4 else None,
                        "d1_cam_s3": self._safe_float(c[5]) if len(c) > 5 else None,
                        "d1_cam_r3": self._safe_float(c[6]) if len(c) > 6 else None,
                        "d1_cam_r4": self._safe_float(c[7]) if len(c) > 7 else None,
                        "d1_cam_r6": self._safe_float(c[8]) if len(c) > 8 else None,
                        # Weekly Camarilla (cols K-P, indices 9-14)
                        "w1_cam_s6": self._safe_float(c[9]) if len(c) > 9 else None,
                        "w1_cam_s4": self._safe_float(c[10]) if len(c) > 10 else None,
                        "w1_cam_s3": self._safe_float(c[11]) if len(c) > 11 else None,
                        "w1_cam_r3": self._safe_float(c[12]) if len(c) > 12 else None,
                        "w1_cam_r4": self._safe_float(c[13]) if len(c) > 13 else None,
                        "w1_cam_r6": self._safe_float(c[14]) if len(c) > 14 else None,
                        # Monthly Camarilla (cols Q-V, indices 15-20)
                        "m1_cam_s6": self._safe_float(c[15]) if len(c) > 15 else None,
                        "m1_cam_s4": self._safe_float(c[16]) if len(c) > 16 else None,
                        "m1_cam_s3": self._safe_float(c[17]) if len(c) > 17 else None,
                        "m1_cam_r3": self._safe_float(c[18]) if len(c) > 18 else None,
                        "m1_cam_r4": self._safe_float(c[19]) if len(c) > 19 else None,
                        "m1_cam_r6": self._safe_float(c[20]) if len(c) > 20 else None,
                    })

            results.append(record)

        return results

    # =========================================================================
    # HVN POCs Reading
    # =========================================================================

    def read_hvn_pocs(self) -> List[Dict[str, Any]]:
        """
        Read HVN POC data from bar_data worksheet (time_hvn section).

        The time_hvn section is in rows 59-68 with columns:
        B: ticker_id, C: ticker, D: date, E: epoch_start_date
        F-O: poc_1 through poc_10 (10 POC price levels)

        Returns one record per ticker with all 10 POC columns.
        """
        sheet = self.get_sheet("bar_data")

        # time_hvn section: rows 59-68, columns B-O
        data = sheet.range("B59:O68").value
        if not data:
            return []

        results = []
        for i, row in enumerate(data):
            if row and row[1]:  # Has ticker (column C, index 1)
                # Extract ticker_id - handle format variations
                raw_ticker_id = self._safe_str(row[0])
                if raw_ticker_id and "_" in raw_ticker_id:
                    ticker_id = f"t{i+1}"
                else:
                    ticker_id = raw_ticker_id if raw_ticker_id else f"t{i+1}"

                results.append({
                    "ticker_id": ticker_id,
                    "ticker": self._safe_str(row[1]),
                    "date": self._format_date(row[2]),
                    "epoch_start_date": self._format_date(row[3]),
                    "poc_1": self._safe_float(row[4]) if len(row) > 4 else None,
                    "poc_2": self._safe_float(row[5]) if len(row) > 5 else None,
                    "poc_3": self._safe_float(row[6]) if len(row) > 6 else None,
                    "poc_4": self._safe_float(row[7]) if len(row) > 7 else None,
                    "poc_5": self._safe_float(row[8]) if len(row) > 8 else None,
                    "poc_6": self._safe_float(row[9]) if len(row) > 9 else None,
                    "poc_7": self._safe_float(row[10]) if len(row) > 10 else None,
                    "poc_8": self._safe_float(row[11]) if len(row) > 11 else None,
                    "poc_9": self._safe_float(row[12]) if len(row) > 12 else None,
                    "poc_10": self._safe_float(row[13]) if len(row) > 13 else None,
                })
        return results

    # =========================================================================
    # Zones Reading
    # =========================================================================

    def read_raw_zones(self) -> List[Dict[str, Any]]:
        """Read raw zones from raw_zones worksheet."""
        try:
            sheet = self.get_sheet("raw_zones")
        except Exception:
            return []

        last_row = sheet.range("A1").end("down").row
        if last_row <= 1:
            return []

        data = sheet.range(f"A2:M{last_row}").value
        if not data:
            return []

        results = []
        for row in data:
            if row and row[0]:
                results.append({
                    "ticker_id": self._safe_str(row[0]),
                    "ticker": self._safe_str(row[1]),
                    "date": self._format_date(row[2]),
                    "price": self._safe_float(row[3]),
                    "direction": self._safe_str(row[4]),
                    "zone_id": self._safe_str(row[5]),
                    "hvn_poc": self._safe_float(row[6]),
                    "zone_high": self._safe_float(row[7]),
                    "zone_low": self._safe_float(row[8]),
                    "overlaps": self._safe_int(row[9]),
                    "score": self._safe_float(row[10]),
                    "rank": self._safe_str(row[11]),  # L1, L2, L3, L4, L5 - string not int
                    "confluences": self._safe_str(row[12]),
                    "is_filtered": False,  # Raw zones are not filtered
                })
        return results

    def read_zone_results(self) -> List[Dict[str, Any]]:
        """
        Read filtered zones from zone_results worksheet.

        Columns A-T (20 columns):
        A: ticker_id, B: ticker, C: date, D: price, E: direction,
        F: zone_id, G: hvn_poc, H: zone_high, I: zone_low, J: overlaps,
        K: score, L: rank, M: confluences, N: tier,
        O: epch_bull, P: epch_bear, Q: epch_bull_price, R: epch_bear_price,
        S: epch_bull_target, T: epch_bear_target
        """
        try:
            sheet = self.get_sheet("zone_results")
        except Exception:
            return []

        last_row = sheet.range("A1").end("down").row
        if last_row <= 1:
            return []

        # Read columns A-T (20 columns)
        data = sheet.range(f"A2:T{last_row}").value
        if not data:
            return []

        results = []
        for row in data:
            if row and row[0]:
                # Determine is_epch_bull and is_epch_bear from the marker columns
                epch_bull_marker = self._safe_str(row[14]) if len(row) > 14 else None
                epch_bear_marker = self._safe_str(row[15]) if len(row) > 15 else None

                results.append({
                    "ticker_id": self._safe_str(row[0]),
                    "ticker": self._safe_str(row[1]),
                    "date": self._format_date(row[2]),
                    "price": self._safe_float(row[3]),
                    "direction": self._safe_str(row[4]),
                    "zone_id": self._safe_str(row[5]),
                    "hvn_poc": self._safe_float(row[6]),
                    "zone_high": self._safe_float(row[7]),
                    "zone_low": self._safe_float(row[8]),
                    "overlaps": self._safe_int(row[9]),
                    "score": self._safe_float(row[10]),
                    "rank": self._safe_str(row[11]),  # L1, L2, L3, L4, L5 - string not int
                    "confluences": self._safe_str(row[12]),
                    "tier": self._safe_str(row[13]) if len(row) > 13 else None,
                    "is_filtered": True,  # These are filtered zones
                    "is_epch_bull": epch_bull_marker is not None and epch_bull_marker != "",
                    "is_epch_bear": epch_bear_marker is not None and epch_bear_marker != "",
                    "epch_bull_price": self._safe_float(row[16]) if len(row) > 16 else None,
                    "epch_bear_price": self._safe_float(row[17]) if len(row) > 17 else None,
                    "epch_bull_target": self._safe_float(row[18]) if len(row) > 18 else None,
                    "epch_bear_target": self._safe_float(row[19]) if len(row) > 19 else None,
                })
        return results

    # =========================================================================
    # Setups Reading
    # =========================================================================

    def read_setups(self) -> List[Dict[str, Any]]:
        """Read setup data from Analysis worksheet."""
        sheet = self.get_sheet("analysis")

        results = []

        # Primary setups: rows 31-40, columns B-L
        primary_data = sheet.range("B31:L40").value
        if primary_data:
            for row in primary_data:
                if row and row[0]:  # Has ticker
                    results.append({
                        "ticker": self._safe_str(row[0]),
                        "direction": self._safe_str(row[1]),
                        "ticker_id": self._safe_str(row[2]),
                        "zone_id": self._safe_str(row[3]),
                        "hvn_poc": self._safe_float(row[4]),
                        "zone_high": self._safe_float(row[5]),
                        "zone_low": self._safe_float(row[6]),
                        "tier": self._safe_str(row[7]),
                        "target_id": self._safe_str(row[8]),
                        "target": self._safe_float(row[9]),
                        "rr_ratio": self._safe_float(row[10]),
                        "setup_type": "PRIMARY",
                    })

        # Secondary setups: rows 31-40, columns N-X
        secondary_data = sheet.range("N31:X40").value
        if secondary_data:
            for row in secondary_data:
                if row and row[0]:  # Has ticker
                    results.append({
                        "ticker": self._safe_str(row[0]),
                        "direction": self._safe_str(row[1]),
                        "ticker_id": self._safe_str(row[2]),
                        "zone_id": self._safe_str(row[3]),
                        "hvn_poc": self._safe_float(row[4]),
                        "zone_high": self._safe_float(row[5]),
                        "zone_low": self._safe_float(row[6]),
                        "tier": self._safe_str(row[7]),
                        "target_id": self._safe_str(row[8]),
                        "target": self._safe_float(row[9]),
                        "rr_ratio": self._safe_float(row[10]),
                        "setup_type": "SECONDARY",
                    })

        return results

    # =========================================================================
    # Trades Reading
    # =========================================================================

    def read_trades(self) -> List[Dict[str, Any]]:
        """Read trades from backtest worksheet (v2.3 format with trade_id)."""
        sheet = self.get_sheet("backtest")
        last_row = sheet.range("A1").end("down").row
        if last_row <= 1:
            return []

        # Columns A-U (21 columns)
        data = sheet.range(f"A2:U{last_row}").value
        if not data:
            return []

        results = []
        for row in data:
            if row and row[0]:  # Has trade_id
                results.append({
                    "trade_id": self._safe_str(row[0]),
                    "date": self._format_date(row[1]),
                    "ticker": self._safe_str(row[2]),
                    "model": self._safe_str(row[3]),
                    "zone_type": self._safe_str(row[4]),
                    "direction": self._safe_str(row[5]),
                    "zone_high": self._safe_float(row[6]),
                    "zone_low": self._safe_float(row[7]),
                    "entry_price": self._safe_float(row[8]),
                    "entry_time": self._format_time(row[9]),
                    "stop_price": self._safe_float(row[10]),
                    "target_3r": self._safe_float(row[11]),
                    "target_calc": self._safe_float(row[12]),
                    "target_used": self._safe_float(row[13]),
                    "exit_price": self._safe_float(row[14]),
                    "exit_time": self._format_time(row[15]),
                    "exit_reason": self._safe_str(row[16]),
                    "pnl_dollars": self._safe_float(row[17]),
                    "pnl_r": self._safe_float(row[18]),
                    "risk": self._safe_float(row[19]),
                    "is_winner": self._safe_bool(row[20]),
                })
        return results

    # =========================================================================
    # Trade Bars Reading (v1.2.0 - 33 columns)
    # =========================================================================

    def read_trade_bars(self) -> List[Dict[str, Any]]:
        """Read trade bars from trade_bars worksheet (v1.2.0 - 33 columns A-AG).

        Returns all M5 bars within each trade with full indicator snapshots.
        Multiple rows per trade (ENTRY, IN_TRADE, EXIT events).
        """
        try:
            sheet = self.get_sheet("trade_bars")
        except Exception:
            return []

        last_row = sheet.range("A1").end("down").row
        if last_row <= 1:
            return []

        # v1.2.0: 33 columns A-AG
        data = sheet.range(f"A2:AG{last_row}").value
        if not data:
            return []

        results = []
        for row in data:
            if row and row[0]:  # Has trade_id
                results.append({
                    # Trade Identification (A-B)
                    "trade_id": self._safe_str(row[0]),
                    "date": self._format_date(row[1]),

                    # Bar Identification (C-F)
                    "event_seq": self._safe_int(row[2]),
                    "event_time": self._format_time(row[3]),
                    "bars_from_entry": self._safe_int(row[4]),
                    "event_type": self._safe_str(row[5]),

                    # OHLCV (G-K)
                    "open_price": self._safe_float(row[6]),
                    "high_price": self._safe_float(row[7]),
                    "low_price": self._safe_float(row[8]),
                    "close_price": self._safe_float(row[9]),
                    "volume": self._safe_int(row[10]),

                    # R-Value (L)
                    "r_at_event": self._safe_float(row[11]),

                    # Health Score (M)
                    "health_score": self._safe_int(row[12]),

                    # Price Indicators (N-P)
                    "vwap": self._safe_float(row[13]),
                    "sma9": self._safe_float(row[14]),
                    "sma21": self._safe_float(row[15]),

                    # Volume Indicators (Q-S)
                    "vol_roc": self._safe_float(row[16]),
                    "vol_delta": self._safe_float(row[17]),
                    "cvd_slope": self._safe_float(row[18]),

                    # SMA Analysis (T-U)
                    "sma_spread": self._safe_float(row[19]),
                    "sma_momentum": self._safe_str(row[20]),

                    # Structure (V-Y)
                    "m5_structure": self._safe_str(row[21]),
                    "m15_structure": self._safe_str(row[22]),
                    "h1_structure": self._safe_str(row[23]),
                    "h4_structure": self._safe_str(row[24]),

                    # Health Summary (Z)
                    "health_summary": self._safe_str(row[25]),

                    # Trade Context (AA-AG)
                    "ticker": self._safe_str(row[26]),
                    "direction": self._safe_str(row[27]),
                    "model": self._safe_str(row[28]),
                    "win": self._safe_int(row[29]),
                    "actual_r": self._safe_float(row[30]),
                    "exit_reason": self._safe_str(row[31]),
                    "entry_health": self._safe_int(row[32]),
                })
        return results

    # =========================================================================
    # Options Analysis Reading (v1.0 - 22 columns)
    # =========================================================================

    def read_options_analysis(self) -> List[Dict[str, Any]]:
        """Read options analysis from options_analysis worksheet (v1.0)."""
        try:
            sheet = self.get_sheet("options_analysis")
        except Exception:
            return []

        last_row = sheet.range("A1").end("down").row
        if last_row <= 1:
            return []

        # v1.0: 22 columns A-V
        data = sheet.range(f"A2:V{last_row}").value
        if not data:
            return []

        results = []
        for row in data:
            if row and row[0]:  # Has trade_id
                results.append({
                    # Trade Identification (A-F)
                    "trade_id": self._safe_str(row[0]),
                    "ticker": self._safe_str(row[1]),
                    "direction": self._safe_str(row[2]),
                    "entry_date": self._format_date(row[3]),
                    "entry_time": self._format_time(row[4]),
                    "entry_price": self._safe_float(row[5]),

                    # Contract Selection (G-J)
                    "options_ticker": self._safe_str(row[6]),
                    "strike": self._safe_float(row[7]),
                    "expiration": self._format_date(row[8]),
                    "contract_type": self._safe_str(row[9]),

                    # Options Trade Data (K-N)
                    "option_entry_price": self._safe_float(row[10]),
                    "option_entry_time": self._format_time(row[11]),
                    "option_exit_price": self._safe_float(row[12]),
                    "option_exit_time": self._format_time(row[13]),

                    # P&L Metrics (O-R)
                    "pnl_dollars": self._safe_float(row[14]),
                    "pnl_percent": self._safe_float(row[15]),
                    "option_r": self._safe_float(row[16]),
                    "net_return": self._safe_float(row[17]),

                    # Comparison Metrics (S-U)
                    "underlying_r": self._safe_float(row[18]),
                    "r_multiplier": self._safe_float(row[19]),
                    "win": self._safe_int(row[20]),

                    # Status (V)
                    "status": self._safe_str(row[21]),
                })
        return results

    # =========================================================================
    # Optimal Trade Reading (v4.0.0 - 28 columns)
    # =========================================================================

    def read_optimal_trade(self) -> List[Dict[str, Any]]:
        """Read optimal trade analysis from optimal_trade worksheet (v4.0.0).

        Returns 4 rows per trade (ENTRY, MFE, MAE, EXIT) with 28 columns.
        """
        try:
            sheet = self.get_sheet("optimal_trade")
        except Exception:
            return []

        last_row = sheet.range("A1").end("down").row
        if last_row <= 1:
            return []

        # v4.0.0: 28 columns A-AB
        data = sheet.range(f"A2:AB{last_row}").value
        if not data:
            return []

        results = []
        for row in data:
            if row and row[0]:  # Has trade_id
                results.append({
                    # Trade Identification (A-F)
                    "trade_id": self._safe_str(row[0]),
                    "date": self._format_date(row[1]),
                    "ticker": self._safe_str(row[2]),
                    "direction": self._safe_str(row[3]),
                    "model": self._safe_str(row[4]),
                    "win": self._safe_int(row[5]),

                    # Event Identification (G-K)
                    "event_type": self._safe_str(row[6]),
                    "event_time": self._format_time(row[7]),
                    "bars_from_entry": self._safe_int(row[8]),
                    "price_at_event": self._safe_float(row[9]),
                    "r_at_event": self._safe_float(row[10]),

                    # Health Metrics (L-N)
                    "health_score": self._safe_int(row[11]),
                    "health_delta": self._safe_int(row[12]),
                    "health_summary": self._safe_str(row[13]),

                    # Indicator Values (O-R)
                    "vwap": self._safe_float(row[14]),
                    "sma9": self._safe_float(row[15]),
                    "sma21": self._safe_float(row[16]),
                    "sma_spread": self._safe_float(row[17]),

                    # SMA & Volume Analysis (S-U)
                    "sma_momentum": self._safe_str(row[18]),
                    "vol_roc": self._safe_float(row[19]),
                    "vol_delta": self._safe_float(row[20]),

                    # CVD (V)
                    "cvd_slope": self._safe_float(row[21]),

                    # Structure (W-Z)
                    "m5_structure": self._safe_str(row[22]),
                    "m15_structure": self._safe_str(row[23]),
                    "h1_structure": self._safe_str(row[24]),
                    "h4_structure": self._safe_str(row[25]),

                    # Trade Outcome (AA-AB)
                    "actual_r": self._safe_float(row[26]),
                    "exit_reason": self._safe_str(row[27]),
                })
        return results
