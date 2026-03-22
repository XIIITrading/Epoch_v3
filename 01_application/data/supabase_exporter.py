"""
Epoch Analysis Tool - Supabase Exporter
Exports analysis results (zones, setups, bar_data, hvn_pocs, market_structure) to Supabase.

This module enables the workflow:
  Morning: Run analysis in Streamlit → Export to Supabase
  Evening: Backtest runner pulls from Supabase → Runs backtest

Exports all raw confluence data required by downstream tools:
  - bar_data: OHLC, ATR, Camarilla pivots, Options levels
  - hvn_pocs: HVN POC levels (poc_1 through poc_10)
  - market_structure: Direction and strong/weak levels per timeframe
  - zones: Raw and filtered confluence zones
  - setups: Primary and secondary trading setups

Author: XIII Trading LLC
Version: 2.0.0 - Added bar_data, hvn_pocs, market_structure exports
"""

import psycopg2
from psycopg2.extras import execute_values
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

# Database configuration (same as 13_database_export)
SUPABASE_HOST = "db.pdbmcskznoaiybdiobje.supabase.co"
SUPABASE_PORT = 5432
SUPABASE_DATABASE = "postgres"
SUPABASE_USER = "postgres"
SUPABASE_PASSWORD = "guid-saltation-covet"

DB_CONFIG = {
    "host": SUPABASE_HOST,
    "port": SUPABASE_PORT,
    "database": SUPABASE_DATABASE,
    "user": SUPABASE_USER,
    "password": SUPABASE_PASSWORD,
    "sslmode": "require"
}


@dataclass
class ExportStats:
    """Statistics from an export operation."""
    zones_exported: int = 0
    setups_exported: int = 0
    bar_data_exported: int = 0
    hvn_pocs_exported: int = 0
    market_structure_exported: int = 0
    tickers_processed: int = 0
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []

    @property
    def success(self) -> bool:
        return len(self.errors) == 0

    @property
    def total_records(self) -> int:
        return (self.zones_exported + self.setups_exported +
                self.bar_data_exported + self.hvn_pocs_exported +
                self.market_structure_exported)


class SupabaseExporter:
    """
    Exports analysis results to Supabase.

    Handles:
    - FilteredZone objects → zones table
    - Setup objects → setups table
    """

    def __init__(self):
        self.conn = None
        self.stats = ExportStats()

    def connect(self) -> bool:
        """Establish database connection."""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            return True
        except Exception as e:
            self.stats.errors.append(f"Connection failed: {str(e)}")
            return False

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def export_analysis_results(self, results: Dict[str, Any]) -> ExportStats:
        """
        Export complete analysis results to Supabase.

        Uses savepoints per ticker so one ticker's failure doesn't abort
        the entire batch. If a ticker export fails, its savepoint is rolled
        back (preserving previously deleted data for that ticker) and the
        next ticker proceeds normally.

        Args:
            results: Analysis results dict from pipeline_runner
                     Contains 'custom' and 'index' lists of ticker results

        Returns:
            ExportStats with counts and any errors
        """
        self.stats = ExportStats()

        if not self.connect():
            return self.stats

        try:
            # Get session date from first successful result
            session_date = self._get_session_date(results)
            if not session_date:
                self.stats.errors.append("Could not determine session date from results")
                return self.stats

            # Ensure daily_sessions record exists (foreign key requirement)
            self._ensure_daily_session(session_date)

            # Process each ticker with savepoint isolation
            # If one ticker fails, roll back only that ticker's changes
            all_results = []
            for result in results.get("index", []):
                if result.get("success"):
                    all_results.append((result, True))
            for result in results.get("custom", []):
                if result.get("success"):
                    all_results.append((result, False))

            for result, is_index in all_results:
                ticker = result.get("ticker", "unknown")
                savepoint_name = f"sp_{ticker.replace('-', '_').replace('.', '_')}"

                try:
                    with self.conn.cursor() as cur:
                        cur.execute(f"SAVEPOINT {savepoint_name}")

                    # Clean up existing data for this ticker+date only
                    self._cleanup_ticker_data(session_date, ticker)

                    # Export all tables for this ticker
                    self._export_ticker_result(result, session_date, is_index=is_index)

                    with self.conn.cursor() as cur:
                        cur.execute(f"RELEASE SAVEPOINT {savepoint_name}")

                except Exception as e:
                    # Roll back this ticker only — previous tickers are preserved
                    error_msg = f"{ticker}: {str(e)}"
                    self.stats.errors.append(error_msg)
                    import logging
                    logging.getLogger(__name__).error(f"Export failed for {ticker}: {e}")
                    try:
                        with self.conn.cursor() as cur:
                            cur.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name}")
                    except Exception:
                        pass  # Connection may be in bad state

            # Commit all successful ticker exports
            self.conn.commit()

        except Exception as e:
            self.stats.errors.append(f"Export failed: {str(e)}")
            if self.conn:
                self.conn.rollback()
        finally:
            self.close()

        return self.stats

    def _get_session_date(self, results: Dict[str, Any]) -> Optional[date]:
        """Extract session date from analysis results."""
        from datetime import datetime as dt

        # Check all result lists
        for key in ("custom", "index"):
            for result in results.get(key, []):
                if not result.get("success"):
                    continue

                # Try top-level analysis_date (set by pipeline_runner)
                ad = result.get("analysis_date")
                if ad:
                    if isinstance(ad, str):
                        return dt.strptime(ad, '%Y-%m-%d').date()
                    if isinstance(ad, date):
                        return ad

                # Try bar_data object attribute
                bar_data = result.get("bar_data")
                if bar_data:
                    if hasattr(bar_data, 'analysis_date'):
                        return bar_data.analysis_date
                    if isinstance(bar_data, dict) and bar_data.get("analysis_date"):
                        ad = bar_data["analysis_date"]
                        if isinstance(ad, str):
                            return dt.strptime(ad, '%Y-%m-%d').date()
                        return ad

        # Fall back to today
        return date.today()

    def _ensure_daily_session(self, session_date: date):
        """Ensure a daily_sessions record exists for the date (foreign key requirement)."""
        with self.conn.cursor() as cur:
            # Insert if not exists (only date is required, other columns have defaults)
            cur.execute("""
                INSERT INTO daily_sessions (date, export_source, export_version)
                VALUES (%s, 'analysis_tool', '1.0.0')
                ON CONFLICT (date) DO NOTHING
            """, (session_date,))

    def _cleanup_session_data(self, session_date: date):
        """Delete existing data for the session date before re-importing.
        DEPRECATED: Use _cleanup_ticker_data() for per-ticker savepoint safety.
        Kept for backward compatibility but no longer called by export_analysis_results.
        """
        with self.conn.cursor() as cur:
            # Delete setups first (may have foreign key constraints)
            cur.execute("DELETE FROM setups WHERE date = %s", (session_date,))

            # Delete zones
            cur.execute("DELETE FROM zones WHERE date = %s", (session_date,))

            # Delete bar_data
            cur.execute("DELETE FROM bar_data WHERE date = %s", (session_date,))

            # Delete hvn_pocs
            cur.execute("DELETE FROM hvn_pocs WHERE date = %s", (session_date,))

            # Delete market_structure
            cur.execute("DELETE FROM market_structure WHERE date = %s", (session_date,))

    def _cleanup_ticker_data(self, session_date: date, ticker: str):
        """Delete existing data for a single ticker+date before re-importing.
        Used within savepoint isolation so rollback restores this ticker's data
        if the subsequent insert fails.
        """
        with self.conn.cursor() as cur:
            cur.execute("DELETE FROM setups WHERE date = %s AND ticker = %s", (session_date, ticker))
            cur.execute("DELETE FROM zones WHERE date = %s AND ticker = %s", (session_date, ticker))
            cur.execute("DELETE FROM bar_data WHERE date = %s AND ticker = %s", (session_date, ticker))
            cur.execute("DELETE FROM hvn_pocs WHERE date = %s AND ticker = %s", (session_date, ticker))
            cur.execute("DELETE FROM market_structure WHERE date = %s AND ticker = %s", (session_date, ticker))

    @staticmethod
    def _build_ticker_id(ticker: str, session_date: date) -> str:
        """Build ticker_id from ticker symbol and date. Format: TICKER_MMDDYY"""
        return f"{ticker}_{session_date.strftime('%m%d%y')}"

    def _export_ticker_result(self, result: Dict[str, Any], session_date: date, is_index: bool = False):
        """Export a single ticker's analysis results."""
        ticker = result.get("ticker", "")
        self.stats.tickers_processed += 1

        # Export bar_data (ATR, Camarilla, OHLC, Options)
        bar_data = result.get("bar_data")
        if bar_data:
            self._export_bar_data(bar_data, session_date)
            self.stats.bar_data_exported += 1

        # Export hvn_pocs (HVN POC levels)
        hvn_result = result.get("hvn_result")
        if hvn_result:
            self._export_hvn_pocs(hvn_result, session_date)
            self.stats.hvn_pocs_exported += 1

        # Export market_structure (direction and strong/weak levels)
        market_structure = result.get("market_structure")
        if market_structure:
            self._export_market_structure(market_structure, session_date, is_index=is_index)
            self.stats.market_structure_exported += 1

        # Export filtered zones
        filtered_zones = result.get("filtered_zones", [])
        if filtered_zones:
            zones_count = self._export_zones(filtered_zones, session_date)
            self.stats.zones_exported += zones_count

        # Export setups (primary and secondary)
        primary_setup = result.get("primary_setup")
        secondary_setup = result.get("secondary_setup")

        if primary_setup:
            self._export_setup(primary_setup, session_date, "PRIMARY")
            self.stats.setups_exported += 1

        if secondary_setup:
            self._export_setup(secondary_setup, session_date, "SECONDARY")
            self.stats.setups_exported += 1

    def _export_bar_data(self, bar_data: Any, session_date: date):
        """
        Export BarData object to bar_data table.

        Args:
            bar_data: BarData object with OHLC, ATR, Camarilla, Options
            session_date: Trading date
        """
        if not bar_data:
            return

        # Handle both object and dict formats
        if hasattr(bar_data, 'ticker'):
            record = {
                "date": session_date,
                "ticker_id": bar_data.ticker_id,
                "ticker": bar_data.ticker,
                "price": bar_data.price,
                # Monthly OHLC
                "m1_open": bar_data.m1_current.open if bar_data.m1_current else None,
                "m1_high": bar_data.m1_current.high if bar_data.m1_current else None,
                "m1_low": bar_data.m1_current.low if bar_data.m1_current else None,
                "m1_close": bar_data.m1_current.close if bar_data.m1_current else None,
                "m1_prior_open": bar_data.m1_prior.open if bar_data.m1_prior else None,
                "m1_prior_high": bar_data.m1_prior.high if bar_data.m1_prior else None,
                "m1_prior_low": bar_data.m1_prior.low if bar_data.m1_prior else None,
                "m1_prior_close": bar_data.m1_prior.close if bar_data.m1_prior else None,
                # Weekly OHLC
                "w1_open": bar_data.w1_current.open if bar_data.w1_current else None,
                "w1_high": bar_data.w1_current.high if bar_data.w1_current else None,
                "w1_low": bar_data.w1_current.low if bar_data.w1_current else None,
                "w1_close": bar_data.w1_current.close if bar_data.w1_current else None,
                "w1_prior_open": bar_data.w1_prior.open if bar_data.w1_prior else None,
                "w1_prior_high": bar_data.w1_prior.high if bar_data.w1_prior else None,
                "w1_prior_low": bar_data.w1_prior.low if bar_data.w1_prior else None,
                "w1_prior_close": bar_data.w1_prior.close if bar_data.w1_prior else None,
                # Daily OHLC
                "d1_open": bar_data.d1_current.open if bar_data.d1_current else None,
                "d1_high": bar_data.d1_current.high if bar_data.d1_current else None,
                "d1_low": bar_data.d1_current.low if bar_data.d1_current else None,
                "d1_close": bar_data.d1_current.close if bar_data.d1_current else None,
                "d1_prior_open": bar_data.d1_prior.open if bar_data.d1_prior else None,
                "d1_prior_high": bar_data.d1_prior.high if bar_data.d1_prior else None,
                "d1_prior_low": bar_data.d1_prior.low if bar_data.d1_prior else None,
                "d1_prior_close": bar_data.d1_prior.close if bar_data.d1_prior else None,
                # Overnight
                "d1_overnight_high": bar_data.overnight_high,
                "d1_overnight_low": bar_data.overnight_low,
                # Options (top 10 levels by OI)
                "op_01": bar_data.options_levels[0] if len(bar_data.options_levels) > 0 else None,
                "op_02": bar_data.options_levels[1] if len(bar_data.options_levels) > 1 else None,
                "op_03": bar_data.options_levels[2] if len(bar_data.options_levels) > 2 else None,
                "op_04": bar_data.options_levels[3] if len(bar_data.options_levels) > 3 else None,
                "op_05": bar_data.options_levels[4] if len(bar_data.options_levels) > 4 else None,
                "op_06": bar_data.options_levels[5] if len(bar_data.options_levels) > 5 else None,
                "op_07": bar_data.options_levels[6] if len(bar_data.options_levels) > 6 else None,
                "op_08": bar_data.options_levels[7] if len(bar_data.options_levels) > 7 else None,
                "op_09": bar_data.options_levels[8] if len(bar_data.options_levels) > 8 else None,
                "op_10": bar_data.options_levels[9] if len(bar_data.options_levels) > 9 else None,
                # ATR values
                "m5_atr": bar_data.m5_atr,
                "m15_atr": bar_data.m15_atr,
                "h1_atr": bar_data.h1_atr,
                "d1_atr": bar_data.d1_atr,
                # Camarilla Daily
                "d1_cam_s6": bar_data.camarilla_daily.s6 if bar_data.camarilla_daily else None,
                "d1_cam_s4": bar_data.camarilla_daily.s4 if bar_data.camarilla_daily else None,
                "d1_cam_s3": bar_data.camarilla_daily.s3 if bar_data.camarilla_daily else None,
                "d1_cam_r3": bar_data.camarilla_daily.r3 if bar_data.camarilla_daily else None,
                "d1_cam_r4": bar_data.camarilla_daily.r4 if bar_data.camarilla_daily else None,
                "d1_cam_r6": bar_data.camarilla_daily.r6 if bar_data.camarilla_daily else None,
                # Camarilla Weekly
                "w1_cam_s6": bar_data.camarilla_weekly.s6 if bar_data.camarilla_weekly else None,
                "w1_cam_s4": bar_data.camarilla_weekly.s4 if bar_data.camarilla_weekly else None,
                "w1_cam_s3": bar_data.camarilla_weekly.s3 if bar_data.camarilla_weekly else None,
                "w1_cam_r3": bar_data.camarilla_weekly.r3 if bar_data.camarilla_weekly else None,
                "w1_cam_r4": bar_data.camarilla_weekly.r4 if bar_data.camarilla_weekly else None,
                "w1_cam_r6": bar_data.camarilla_weekly.r6 if bar_data.camarilla_weekly else None,
                # Camarilla Monthly
                "m1_cam_s6": bar_data.camarilla_monthly.s6 if bar_data.camarilla_monthly else None,
                "m1_cam_s4": bar_data.camarilla_monthly.s4 if bar_data.camarilla_monthly else None,
                "m1_cam_s3": bar_data.camarilla_monthly.s3 if bar_data.camarilla_monthly else None,
                "m1_cam_r3": bar_data.camarilla_monthly.r3 if bar_data.camarilla_monthly else None,
                "m1_cam_r4": bar_data.camarilla_monthly.r4 if bar_data.camarilla_monthly else None,
                "m1_cam_r6": bar_data.camarilla_monthly.r6 if bar_data.camarilla_monthly else None,
                # Prior Day Volume Profile
                "pd_vp_poc": bar_data.pd_vp_poc,
                "pd_vp_vah": bar_data.pd_vp_vah,
                "pd_vp_val": bar_data.pd_vp_val,
                # Pre-Market levels (written by Bucket C morning runner)
                "pm_high": getattr(bar_data, 'pm_high', None),
                "pm_low": getattr(bar_data, 'pm_low', None),
                "pm_poc": getattr(bar_data, 'pm_poc', None),
                "pm_vah": getattr(bar_data, 'pm_vah', None),
                "pm_val": getattr(bar_data, 'pm_val', None),
                "pm_price": getattr(bar_data, 'pm_price', None),
            }
        else:
            # Dict format (from model_dump() — handles nested dicts)
            ticker = bar_data.get("ticker", "")
            ticker_id = bar_data.get("ticker_id") or self._build_ticker_id(ticker, session_date)

            # Helper to extract nested OHLC from dict format
            def _ohlc(key):
                val = bar_data.get(key)
                if isinstance(val, dict):
                    return val.get("open"), val.get("high"), val.get("low"), val.get("close")
                return None, None, None, None

            m1c_o, m1c_h, m1c_l, m1c_c = _ohlc("m1_current")
            m1p_o, m1p_h, m1p_l, m1p_c = _ohlc("m1_prior")
            w1c_o, w1c_h, w1c_l, w1c_c = _ohlc("w1_current")
            w1p_o, w1p_h, w1p_l, w1p_c = _ohlc("w1_prior")
            d1c_o, d1c_h, d1c_l, d1c_c = _ohlc("d1_current")
            d1p_o, d1p_h, d1p_l, d1p_c = _ohlc("d1_prior")

            # Helper to extract nested Camarilla from dict format
            def _cam(key):
                val = bar_data.get(key)
                if isinstance(val, dict):
                    return val.get("s6"), val.get("s4"), val.get("s3"), val.get("r3"), val.get("r4"), val.get("r6")
                return None, None, None, None, None, None

            cam_d_s6, cam_d_s4, cam_d_s3, cam_d_r3, cam_d_r4, cam_d_r6 = _cam("camarilla_daily")
            cam_w_s6, cam_w_s4, cam_w_s3, cam_w_r3, cam_w_r4, cam_w_r6 = _cam("camarilla_weekly")
            cam_m_s6, cam_m_s4, cam_m_s3, cam_m_r3, cam_m_r4, cam_m_r6 = _cam("camarilla_monthly")

            # Options levels from list
            options = bar_data.get("options_levels", [])

            record = {
                "date": session_date,
                "ticker_id": ticker_id,
                "ticker": ticker,
                "price": bar_data.get("price"),
                # Monthly OHLC
                "m1_open": bar_data.get("m1_open", m1c_o),
                "m1_high": bar_data.get("m1_high", m1c_h),
                "m1_low": bar_data.get("m1_low", m1c_l),
                "m1_close": bar_data.get("m1_close", m1c_c),
                "m1_prior_open": bar_data.get("m1_prior_open", m1p_o),
                "m1_prior_high": bar_data.get("m1_prior_high", m1p_h),
                "m1_prior_low": bar_data.get("m1_prior_low", m1p_l),
                "m1_prior_close": bar_data.get("m1_prior_close", m1p_c),
                # Weekly OHLC
                "w1_open": bar_data.get("w1_open", w1c_o),
                "w1_high": bar_data.get("w1_high", w1c_h),
                "w1_low": bar_data.get("w1_low", w1c_l),
                "w1_close": bar_data.get("w1_close", w1c_c),
                "w1_prior_open": bar_data.get("w1_prior_open", w1p_o),
                "w1_prior_high": bar_data.get("w1_prior_high", w1p_h),
                "w1_prior_low": bar_data.get("w1_prior_low", w1p_l),
                "w1_prior_close": bar_data.get("w1_prior_close", w1p_c),
                # Daily OHLC
                "d1_open": bar_data.get("d1_open", d1c_o),
                "d1_high": bar_data.get("d1_high", d1c_h),
                "d1_low": bar_data.get("d1_low", d1c_l),
                "d1_close": bar_data.get("d1_close", d1c_c),
                "d1_prior_open": bar_data.get("d1_prior_open", d1p_o),
                "d1_prior_high": bar_data.get("d1_prior_high", d1p_h),
                "d1_prior_low": bar_data.get("d1_prior_low", d1p_l),
                "d1_prior_close": bar_data.get("d1_prior_close", d1p_c),
                # Overnight
                "d1_overnight_high": bar_data.get("overnight_high") or bar_data.get("d1_overnight_high"),
                "d1_overnight_low": bar_data.get("overnight_low") or bar_data.get("d1_overnight_low"),
                # Options
                "op_01": options[0] if len(options) > 0 else bar_data.get("op_01"),
                "op_02": options[1] if len(options) > 1 else bar_data.get("op_02"),
                "op_03": options[2] if len(options) > 2 else bar_data.get("op_03"),
                "op_04": options[3] if len(options) > 3 else bar_data.get("op_04"),
                "op_05": options[4] if len(options) > 4 else bar_data.get("op_05"),
                "op_06": options[5] if len(options) > 5 else bar_data.get("op_06"),
                "op_07": options[6] if len(options) > 6 else bar_data.get("op_07"),
                "op_08": options[7] if len(options) > 7 else bar_data.get("op_08"),
                "op_09": options[8] if len(options) > 8 else bar_data.get("op_09"),
                "op_10": options[9] if len(options) > 9 else bar_data.get("op_10"),
                # ATR
                "m5_atr": bar_data.get("m5_atr"),
                "m15_atr": bar_data.get("m15_atr"),
                "h1_atr": bar_data.get("h1_atr"),
                "d1_atr": bar_data.get("d1_atr"),
                # Camarilla Daily
                "d1_cam_s6": bar_data.get("d1_cam_s6", cam_d_s6),
                "d1_cam_s4": bar_data.get("d1_cam_s4", cam_d_s4),
                "d1_cam_s3": bar_data.get("d1_cam_s3", cam_d_s3),
                "d1_cam_r3": bar_data.get("d1_cam_r3", cam_d_r3),
                "d1_cam_r4": bar_data.get("d1_cam_r4", cam_d_r4),
                "d1_cam_r6": bar_data.get("d1_cam_r6", cam_d_r6),
                # Camarilla Weekly
                "w1_cam_s6": bar_data.get("w1_cam_s6", cam_w_s6),
                "w1_cam_s4": bar_data.get("w1_cam_s4", cam_w_s4),
                "w1_cam_s3": bar_data.get("w1_cam_s3", cam_w_s3),
                "w1_cam_r3": bar_data.get("w1_cam_r3", cam_w_r3),
                "w1_cam_r4": bar_data.get("w1_cam_r4", cam_w_r4),
                "w1_cam_r6": bar_data.get("w1_cam_r6", cam_w_r6),
                # Camarilla Monthly
                "m1_cam_s6": bar_data.get("m1_cam_s6", cam_m_s6),
                "m1_cam_s4": bar_data.get("m1_cam_s4", cam_m_s4),
                "m1_cam_s3": bar_data.get("m1_cam_s3", cam_m_s3),
                "m1_cam_r3": bar_data.get("m1_cam_r3", cam_m_r3),
                "m1_cam_r4": bar_data.get("m1_cam_r4", cam_m_r4),
                "m1_cam_r6": bar_data.get("m1_cam_r6", cam_m_r6),
                # Prior Day Volume Profile
                "pd_vp_poc": bar_data.get("pd_vp_poc"),
                "pd_vp_vah": bar_data.get("pd_vp_vah"),
                "pd_vp_val": bar_data.get("pd_vp_val"),
                # Pre-Market levels
                "pm_high": bar_data.get("pm_high"),
                "pm_low": bar_data.get("pm_low"),
                "pm_poc": bar_data.get("pm_poc"),
                "pm_vah": bar_data.get("pm_vah"),
                "pm_val": bar_data.get("pm_val"),
                "pm_price": bar_data.get("pm_price"),
            }

        self._upsert_bar_data(record)

    def _export_hvn_pocs(self, hvn_result: Any, session_date: date):
        """
        Export HVNResult object to hvn_pocs table.

        Args:
            hvn_result: HVNResult object with POC levels
            session_date: Trading date
        """
        if not hvn_result:
            return

        # Handle both object and dict formats
        if hasattr(hvn_result, 'ticker'):
            # Get POC prices by rank (1-10)
            poc_prices = {}
            for poc in hvn_result.pocs:
                if hasattr(poc, 'rank') and hasattr(poc, 'price'):
                    poc_prices[poc.rank] = poc.price

            # Build ticker_id from ticker and session_date
            ticker_id = f"{hvn_result.ticker}_{session_date.strftime('%m%d%y')}"

            record = {
                "date": session_date,
                "ticker_id": ticker_id,
                "ticker": hvn_result.ticker,
                "epoch_start_date": hvn_result.start_date,
                "poc_1": poc_prices.get(1),
                "poc_2": poc_prices.get(2),
                "poc_3": poc_prices.get(3),
                "poc_4": poc_prices.get(4),
                "poc_5": poc_prices.get(5),
                "poc_6": poc_prices.get(6),
                "poc_7": poc_prices.get(7),
                "poc_8": poc_prices.get(8),
                "poc_9": poc_prices.get(9),
                "poc_10": poc_prices.get(10),
            }
        else:
            # Dict format (from model_dump())
            ticker = hvn_result.get("ticker", "")
            ticker_id = hvn_result.get("ticker_id") or self._build_ticker_id(ticker, session_date)

            # Extract POCs — may be in "pocs" list (from model_dump) or flat poc_1..poc_10
            poc_prices = {}
            pocs_list = hvn_result.get("pocs", [])
            if pocs_list and isinstance(pocs_list, list):
                for poc in pocs_list:
                    if isinstance(poc, dict) and "rank" in poc and "price" in poc:
                        poc_prices[poc["rank"]] = poc["price"]

            record = {
                "date": session_date,
                "ticker_id": ticker_id,
                "ticker": ticker,
                "epoch_start_date": hvn_result.get("start_date") or hvn_result.get("epoch_start_date"),
                "poc_1": poc_prices.get(1) or hvn_result.get("poc_1"),
                "poc_2": poc_prices.get(2) or hvn_result.get("poc_2"),
                "poc_3": poc_prices.get(3) or hvn_result.get("poc_3"),
                "poc_4": poc_prices.get(4) or hvn_result.get("poc_4"),
                "poc_5": poc_prices.get(5) or hvn_result.get("poc_5"),
                "poc_6": poc_prices.get(6) or hvn_result.get("poc_6"),
                "poc_7": poc_prices.get(7) or hvn_result.get("poc_7"),
                "poc_8": poc_prices.get(8) or hvn_result.get("poc_8"),
                "poc_9": poc_prices.get(9) or hvn_result.get("poc_9"),
                "poc_10": poc_prices.get(10) or hvn_result.get("poc_10"),
            }

        self._upsert_hvn_pocs(record)

    def _export_market_structure(self, market_structure: Any, session_date: date, is_index: bool = False):
        """
        Export MarketStructure object to market_structure table.

        Args:
            market_structure: MarketStructure object with direction and levels
            session_date: Trading date
            is_index: Whether this is an index ticker (SPY, QQQ, DIA)
        """
        if not market_structure:
            return

        # Handle both object and dict formats
        if hasattr(market_structure, 'ticker'):
            # Build ticker_id from ticker and session_date
            ticker_id = f"{market_structure.ticker}_{session_date.strftime('%m%d%y')}"

            record = {
                "date": session_date,
                "ticker": market_structure.ticker,
                "ticker_id": ticker_id,
                "is_index": is_index,
                "scan_price": market_structure.price,
                # D1 timeframe
                "d1_direction": market_structure.d1.direction.value if hasattr(market_structure.d1.direction, 'value') else str(market_structure.d1.direction),
                "d1_strong": market_structure.d1.strong,
                "d1_weak": market_structure.d1.weak,
                # H4 timeframe
                "h4_direction": market_structure.h4.direction.value if hasattr(market_structure.h4.direction, 'value') else str(market_structure.h4.direction),
                "h4_strong": market_structure.h4.strong,
                "h4_weak": market_structure.h4.weak,
                # H1 timeframe
                "h1_direction": market_structure.h1.direction.value if hasattr(market_structure.h1.direction, 'value') else str(market_structure.h1.direction),
                "h1_strong": market_structure.h1.strong,
                "h1_weak": market_structure.h1.weak,
                # M15 timeframe
                "m15_direction": market_structure.m15.direction.value if hasattr(market_structure.m15.direction, 'value') else str(market_structure.m15.direction),
                "m15_strong": market_structure.m15.strong,
                "m15_weak": market_structure.m15.weak,
                # Composite
                "composite_direction": market_structure.composite.value if hasattr(market_structure.composite, 'value') else str(market_structure.composite),
                # W1/M1 structure (written by Bucket A weekly runner)
                "w1_direction": getattr(market_structure, 'w1_direction', None),
                "w1_strong": getattr(market_structure, 'w1_strong', None),
                "w1_weak": getattr(market_structure, 'w1_weak', None),
                "m1_direction": getattr(market_structure, 'm1_direction', None),
                "m1_strong": getattr(market_structure, 'm1_strong', None),
                "m1_weak": getattr(market_structure, 'm1_weak', None),
            }
        else:
            # Dict format (from model_dump() — handles nested timeframe dicts)
            ticker = market_structure.get("ticker", "")
            ticker_id = market_structure.get("ticker_id") or self._build_ticker_id(ticker, session_date)

            # Helper to extract direction/strong/weak from nested dict
            def _tf(key):
                val = market_structure.get(key)
                if isinstance(val, dict):
                    d = val.get("direction")
                    if isinstance(d, dict):
                        d = d.get("value", d)
                    elif hasattr(d, 'value'):
                        d = d.value
                    return d, val.get("strong"), val.get("weak")
                return None, None, None

            d1_dir, d1_s, d1_w = _tf("d1")
            h4_dir, h4_s, h4_w = _tf("h4")
            h1_dir, h1_s, h1_w = _tf("h1")
            m15_dir, m15_s, m15_w = _tf("m15")

            # Composite direction
            comp = market_structure.get("composite") or market_structure.get("composite_direction")
            if isinstance(comp, dict):
                comp = comp.get("value", comp)
            elif hasattr(comp, 'value'):
                comp = comp.value

            record = {
                "date": session_date,
                "ticker": ticker,
                "ticker_id": ticker_id,
                "is_index": is_index or market_structure.get("is_index", False),
                "scan_price": market_structure.get("price") or market_structure.get("scan_price"),
                "d1_direction": market_structure.get("d1_direction", d1_dir),
                "d1_strong": market_structure.get("d1_strong", d1_s),
                "d1_weak": market_structure.get("d1_weak", d1_w),
                "h4_direction": market_structure.get("h4_direction", h4_dir),
                "h4_strong": market_structure.get("h4_strong", h4_s),
                "h4_weak": market_structure.get("h4_weak", h4_w),
                "h1_direction": market_structure.get("h1_direction", h1_dir),
                "h1_strong": market_structure.get("h1_strong", h1_s),
                "h1_weak": market_structure.get("h1_weak", h1_w),
                "m15_direction": market_structure.get("m15_direction", m15_dir),
                "m15_strong": market_structure.get("m15_strong", m15_s),
                "m15_weak": market_structure.get("m15_weak", m15_w),
                "composite_direction": market_structure.get("composite_direction", comp),
                # W1/M1 structure
                "w1_direction": market_structure.get("w1_direction"),
                "w1_strong": market_structure.get("w1_strong"),
                "w1_weak": market_structure.get("w1_weak"),
                "m1_direction": market_structure.get("m1_direction"),
                "m1_strong": market_structure.get("m1_strong"),
                "m1_weak": market_structure.get("m1_weak"),
            }

        self._upsert_market_structure(record)

    def _export_zones(self, zones: List[Any], session_date: date) -> int:
        """
        Export FilteredZone objects to zones table.

        Args:
            zones: List of FilteredZone objects
            session_date: Trading date

        Returns:
            Number of zones exported
        """
        if not zones:
            return 0

        records = []
        for zone in zones:
            # Handle both object and dict formats
            if hasattr(zone, 'ticker'):
                # FilteredZone object
                record = {
                    "date": session_date,
                    "zone_id": zone.zone_id,
                    "ticker_id": zone.ticker_id,
                    "ticker": zone.ticker,
                    "price": zone.price,
                    "hvn_poc": zone.hvn_poc,
                    "zone_high": zone.zone_high,
                    "zone_low": zone.zone_low,
                    "direction": zone.direction.value if hasattr(zone.direction, 'value') else str(zone.direction),
                    "rank": zone.rank.value if hasattr(zone.rank, 'value') else str(zone.rank),
                    "score": zone.score,
                    "overlap_count": zone.overlaps,
                    "confluences": zone.confluences_str if hasattr(zone, 'confluences_str') else ", ".join(zone.confluences),
                    "is_filtered": True,
                    "is_epch_bull": zone.is_bull_poc,
                    "is_epch_bear": zone.is_bear_poc,
                    "epch_bull_price": zone.hvn_poc if zone.is_bull_poc else None,
                    "epch_bear_price": zone.hvn_poc if zone.is_bear_poc else None,
                    "epch_bull_target": zone.bull_target if hasattr(zone, 'bull_target') else None,
                    "epch_bear_target": zone.bear_target if hasattr(zone, 'bear_target') else None,
                }
            else:
                # Dict format (fallback)
                record = {
                    "date": session_date,
                    "zone_id": zone.get("zone_id"),
                    "ticker_id": zone.get("ticker_id"),
                    "ticker": zone.get("ticker"),
                    "price": zone.get("price"),
                    "hvn_poc": zone.get("hvn_poc"),
                    "zone_high": zone.get("zone_high"),
                    "zone_low": zone.get("zone_low"),
                    "direction": zone.get("direction"),
                    "rank": zone.get("rank"),
                    "score": zone.get("score"),
                    "overlap_count": zone.get("overlaps"),
                    "confluences": zone.get("confluences"),
                    "is_filtered": True,
                    "is_epch_bull": zone.get("is_bull_poc", False),
                    "is_epch_bear": zone.get("is_bear_poc", False),
                }

            records.append(record)

        return self._upsert_zones(records)

    def _export_setup(self, setup: Any, session_date: date, setup_type: str):
        """
        Export a Setup object to setups table.

        Args:
            setup: Setup object (primary or secondary)
            session_date: Trading date
            setup_type: "PRIMARY" or "SECONDARY"
        """
        if not setup:
            return

        # Handle both object and dict formats
        if hasattr(setup, 'ticker'):
            # Setup object
            record = {
                "date": session_date,
                "ticker_id": setup.ticker_id,
                "setup_type": setup_type,
                "ticker": setup.ticker,
                "direction": setup.direction.value if hasattr(setup.direction, 'value') else str(setup.direction),
                "zone_id": setup.zone_id,
                "hvn_poc": setup.hvn_poc,
                "zone_high": setup.zone_high,
                "zone_low": setup.zone_low,
                "target_id": setup.target_id,
                "target_price": setup.target,
                "risk_reward": setup.risk_reward,
                "pinescript_6": None,  # Can be computed if needed
                "pinescript_16": None,
            }
        else:
            # Dict format (fallback)
            record = {
                "date": session_date,
                "ticker_id": setup.get("ticker_id"),
                "setup_type": setup_type,
                "ticker": setup.get("ticker"),
                "direction": setup.get("direction"),
                "zone_id": setup.get("zone_id"),
                "hvn_poc": setup.get("hvn_poc"),
                "zone_high": setup.get("zone_high"),
                "zone_low": setup.get("zone_low"),
                "target_id": setup.get("target_id"),
                "target_price": setup.get("target"),
                "risk_reward": setup.get("risk_reward"),
            }

        self._upsert_setup(record)

    def _upsert_zones(self, records: List[Dict[str, Any]]) -> int:
        """Insert/update zone records."""
        if not records:
            return 0

        columns = list(records[0].keys())
        col_names = ", ".join(columns)

        # Build upsert query
        pk_cols = "date, zone_id"
        update_cols = [c for c in columns if c not in ["date", "zone_id"]]
        update_clause = ", ".join([f"{c} = EXCLUDED.{c}" for c in update_cols])

        values = [
            tuple(self._convert_value(record.get(col)) for col in columns)
            for record in records
        ]

        query = f"""
            INSERT INTO zones ({col_names})
            VALUES %s
            ON CONFLICT ({pk_cols}) DO UPDATE SET {update_clause}
        """

        with self.conn.cursor() as cur:
            execute_values(cur, query, values)

        return len(records)

    def _upsert_setup(self, record: Dict[str, Any]):
        """Insert/update a single setup record."""
        columns = list(record.keys())
        col_names = ", ".join(columns)
        placeholders = ", ".join(["%s"] * len(columns))

        pk_cols = "date, ticker_id, setup_type"
        update_cols = [c for c in columns if c not in ["date", "ticker_id", "setup_type"]]
        update_clause = ", ".join([f"{c} = EXCLUDED.{c}" for c in update_cols])

        values = tuple(self._convert_value(record.get(col)) for col in columns)

        query = f"""
            INSERT INTO setups ({col_names})
            VALUES ({placeholders})
            ON CONFLICT ({pk_cols}) DO UPDATE SET {update_clause}
        """

        with self.conn.cursor() as cur:
            cur.execute(query, values)

    def _upsert_bar_data(self, record: Dict[str, Any]):
        """Insert/update a single bar_data record."""
        columns = list(record.keys())
        col_names = ", ".join(columns)
        placeholders = ", ".join(["%s"] * len(columns))

        pk_cols = "date, ticker_id"
        update_cols = [c for c in columns if c not in ["date", "ticker_id"]]
        update_clause = ", ".join([f"{c} = EXCLUDED.{c}" for c in update_cols])

        values = tuple(self._convert_value(record.get(col)) for col in columns)

        query = f"""
            INSERT INTO bar_data ({col_names})
            VALUES ({placeholders})
            ON CONFLICT ({pk_cols}) DO UPDATE SET {update_clause}
        """

        with self.conn.cursor() as cur:
            cur.execute(query, values)

    def _upsert_hvn_pocs(self, record: Dict[str, Any]):
        """Insert/update a single hvn_pocs record."""
        columns = list(record.keys())
        col_names = ", ".join(columns)
        placeholders = ", ".join(["%s"] * len(columns))

        pk_cols = "date, ticker_id"
        update_cols = [c for c in columns if c not in ["date", "ticker_id"]]
        update_clause = ", ".join([f"{c} = EXCLUDED.{c}" for c in update_cols])

        values = tuple(self._convert_value(record.get(col)) for col in columns)

        query = f"""
            INSERT INTO hvn_pocs ({col_names})
            VALUES ({placeholders})
            ON CONFLICT ({pk_cols}) DO UPDATE SET {update_clause}
        """

        with self.conn.cursor() as cur:
            cur.execute(query, values)

    def _upsert_market_structure(self, record: Dict[str, Any]):
        """Insert/update a single market_structure record."""
        columns = list(record.keys())
        col_names = ", ".join(columns)
        placeholders = ", ".join(["%s"] * len(columns))

        pk_cols = "date, ticker"
        update_cols = [c for c in columns if c not in ["date", "ticker"]]
        update_clause = ", ".join([f"{c} = EXCLUDED.{c}" for c in update_cols])

        values = tuple(self._convert_value(record.get(col)) for col in columns)

        query = f"""
            INSERT INTO market_structure ({col_names})
            VALUES ({placeholders})
            ON CONFLICT ({pk_cols}) DO UPDATE SET {update_clause}
        """

        with self.conn.cursor() as cur:
            cur.execute(query, values)

    def _convert_value(self, value: Any) -> Any:
        """Convert Python values to PostgreSQL-compatible types."""
        if value is None:
            return None
        if isinstance(value, (datetime, date)):
            return value
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value
        if isinstance(value, str):
            return value.strip() if value else None
        return str(value)


def export_to_supabase(results: Dict[str, Any]) -> ExportStats:
    """
    Convenience function to export analysis results to Supabase.

    Args:
        results: Analysis results dict from pipeline_runner

    Returns:
        ExportStats with export counts and any errors
    """
    exporter = SupabaseExporter()
    return exporter.export_analysis_results(results)
