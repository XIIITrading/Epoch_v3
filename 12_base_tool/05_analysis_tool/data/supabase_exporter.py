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

            # Clean up existing data for this date
            self._cleanup_session_data(session_date)

            # Process index ticker results (SPY, QQQ, DIA)
            index_results = results.get("index", [])
            for result in index_results:
                if result.get("success"):
                    self._export_ticker_result(result, session_date, is_index=True)

            # Process custom ticker results
            custom_results = results.get("custom", [])
            for result in custom_results:
                if result.get("success"):
                    self._export_ticker_result(result, session_date, is_index=False)

            # Commit transaction
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
        # Try custom results first
        for result in results.get("custom", []):
            if result.get("success"):
                bar_data = result.get("bar_data")
                if bar_data and hasattr(bar_data, 'analysis_date'):
                    return bar_data.analysis_date

        # Try index results
        for result in results.get("index", []):
            if result.get("success"):
                bar_data = result.get("bar_data")
                if bar_data and hasattr(bar_data, 'analysis_date'):
                    return bar_data.analysis_date

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
        """Delete existing data for the session date before re-importing."""
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
            }
        else:
            # Dict format (fallback)
            record = {
                "date": session_date,
                "ticker_id": bar_data.get("ticker_id"),
                "ticker": bar_data.get("ticker"),
                "price": bar_data.get("price"),
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
            # Dict format (fallback)
            record = {
                "date": session_date,
                "ticker_id": hvn_result.get("ticker_id"),
                "ticker": hvn_result.get("ticker"),
                "epoch_start_date": hvn_result.get("epoch_start_date"),
                "poc_1": hvn_result.get("poc_1"),
                "poc_2": hvn_result.get("poc_2"),
                "poc_3": hvn_result.get("poc_3"),
                "poc_4": hvn_result.get("poc_4"),
                "poc_5": hvn_result.get("poc_5"),
                "poc_6": hvn_result.get("poc_6"),
                "poc_7": hvn_result.get("poc_7"),
                "poc_8": hvn_result.get("poc_8"),
                "poc_9": hvn_result.get("poc_9"),
                "poc_10": hvn_result.get("poc_10"),
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
            }
        else:
            # Dict format (fallback)
            record = {
                "date": session_date,
                "ticker": market_structure.get("ticker"),
                "ticker_id": market_structure.get("ticker_id"),
                "is_index": market_structure.get("is_index", False),
                "scan_price": market_structure.get("price"),
                "d1_direction": market_structure.get("d1_direction"),
                "d1_strong": market_structure.get("d1_strong"),
                "d1_weak": market_structure.get("d1_weak"),
                "h4_direction": market_structure.get("h4_direction"),
                "h4_strong": market_structure.get("h4_strong"),
                "h4_weak": market_structure.get("h4_weak"),
                "h1_direction": market_structure.get("h1_direction"),
                "h1_strong": market_structure.get("h1_strong"),
                "h1_weak": market_structure.get("h1_weak"),
                "m15_direction": market_structure.get("m15_direction"),
                "m15_strong": market_structure.get("m15_strong"),
                "m15_weak": market_structure.get("m15_weak"),
                "composite_direction": market_structure.get("composite_direction"),
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
