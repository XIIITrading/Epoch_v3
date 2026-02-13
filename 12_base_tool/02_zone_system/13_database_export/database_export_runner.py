"""
Epoch Trading System - Database Export Runner
Module 11: Exports epoch_v1.xlsm data to Supabase PostgreSQL database.

Connects to already-open workbook via xlwings and keeps it open after export.

Usage:
    python database_export_runner.py              # Export current day's data
    python database_export_runner.py --validate   # Validate only, don't export
    python database_export_runner.py --dry-run    # Show what would be exported

Author: XIII Trading LLC
Version: 3.0.0 - Removed entry/exit events, added trade_bars export
"""

import sys
import argparse
import psycopg2
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add module to path
sys.path.insert(0, str(Path(__file__).parent))

from config import DB_CONFIG, EXCEL_PATH, EXPORT_VERSION
from utils.excel_reader import ExcelReader
from exporters import (
    MarketStructureExporter,
    BarDataExporter,
    HvnPocsExporter,
    ZonesExporter,
    SetupsExporter,
    TradesExporter,
    TradeBarsExporter,
    OptionsAnalysisExporter,
    OptimalTradeExporter
)


class DatabaseExportRunner:
    """
    Main runner for exporting Epoch data to Supabase.
    Reads from epoch_v1.xlsx and exports to PostgreSQL tables.
    """

    def __init__(self, dry_run: bool = False, validate_only: bool = False):
        self.dry_run = dry_run
        self.validate_only = validate_only
        self.conn = None
        self.reader = None
        self.session_date = None
        self.stats = {
            "daily_sessions": 0,
            "market_structure": 0,
            "bar_data": 0,
            "hvn_pocs": 0,
            "zones": 0,
            "setups": 0,
            "trades": 0,
            "trade_bars": 0,
            "optimal_trade": 0,
            "options_analysis": 0,
        }
        self.errors = []

    def run(self) -> bool:
        """
        Execute the full export process.

        Returns:
            True if successful, False if errors occurred
        """
        print("=" * 60)
        print("Epoch Trading System - Database Export")
        print(f"Version: {EXPORT_VERSION}")
        print("=" * 60)
        print()

        try:
            # Step 1: Connect to Excel workbook (uses already-open if available)
            print("[1/11] Connecting to Excel workbook...")
            self.reader = ExcelReader(EXCEL_PATH)
            self.reader.open()
            self.session_date = self.reader.get_session_date()
            print(f"  Session Date: {self.session_date}")
            print()

            # Step 1b: Connect to database
            if not self.dry_run and not self.validate_only:
                print("[1/11] Connecting to Supabase...")
                self.conn = psycopg2.connect(**DB_CONFIG)
                print("  Connected successfully")
                print()

                # Clean up existing data for this session date
                self._cleanup_session_data()

            # Step 3-11: Export each data type
            self._export_daily_session()
            self._export_market_structure()
            self._export_bar_data()
            self._export_hvn_pocs()
            self._export_zones()
            self._export_setups()
            self._export_trades()
            self._export_trade_bars()
            self._export_optimal_trade()
            self._export_options_analysis()

            # Commit transaction
            if self.conn and not self.validate_only:
                print("\n[Commit] Committing transaction...")
                self.conn.commit()
                print("  Transaction committed successfully")

            # Print summary
            self._print_summary()

            return len(self.errors) == 0

        except Exception as e:
            self.errors.append(f"Fatal error: {str(e)}")
            if self.conn:
                self.conn.rollback()
            raise

        finally:
            # Disconnect from Excel (but keep workbook open for user)
            if self.reader:
                self.reader.close()
            # Close database connection
            if self.conn:
                self.conn.close()

    def _cleanup_session_data(self):
        """Delete all existing data for the session date before re-importing."""
        print("[CLEANUP] Removing existing data for session date...")

        with self.conn.cursor() as cur:
            # Options analysis (has entry_date column)
            cur.execute("""
                DELETE FROM options_analysis
                WHERE entry_date = %s
            """, (self.session_date,))
            if cur.rowcount > 0:
                print(f"  Deleted {cur.rowcount} rows from options_analysis")

            # Optimal trade (has date column)
            cur.execute("""
                DELETE FROM optimal_trade
                WHERE date = %s
            """, (self.session_date,))
            if cur.rowcount > 0:
                print(f"  Deleted {cur.rowcount} rows from optimal_trade")

            # Trade bars (has date column)
            cur.execute("""
                DELETE FROM trade_bars
                WHERE date = %s
            """, (self.session_date,))
            if cur.rowcount > 0:
                print(f"  Deleted {cur.rowcount} rows from trade_bars")

            # Tables with date column, in dependency order
            tables_with_date = [
                "trades",
                "setups",
                "zones",
                "hvn_pocs",
                "bar_data",
                "market_structure",
                "daily_sessions",
            ]

            for table in tables_with_date:
                cur.execute(f"DELETE FROM {table} WHERE date = %s", (self.session_date,))
                if cur.rowcount > 0:
                    print(f"  Deleted {cur.rowcount} rows from {table}")

        print("  Cleanup complete")
        print()

    def _export_daily_session(self):
        """Export/create daily session record."""
        print("[2/11] Exporting daily_sessions...")

        if self.dry_run or self.validate_only:
            print("  [DRY-RUN] Would create session for", self.session_date)
            self.stats["daily_sessions"] = 1
            return

        # Read summary data
        market_data = self.reader.read_market_structure_indices()
        tickers = self.reader.read_market_structure_tickers()

        # Get SPY composite for market_composite
        spy_composite = None
        for m in market_data:
            if m.get("ticker") == "SPY":
                spy_composite = m.get("composite_direction")
                break

        ticker_list = [t.get("ticker") for t in tickers if t.get("ticker")]

        # Insert daily session
        query = """
            INSERT INTO daily_sessions (
                date, tickers_analyzed, ticker_count, market_composite,
                export_source, export_version
            ) VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (date) DO UPDATE SET
                tickers_analyzed = EXCLUDED.tickers_analyzed,
                ticker_count = EXCLUDED.ticker_count,
                market_composite = EXCLUDED.market_composite,
                export_version = EXCLUDED.export_version,
                updated_at = NOW()
        """

        with self.conn.cursor() as cur:
            cur.execute(query, (
                self.session_date,
                ",".join(ticker_list),
                len(ticker_list),
                spy_composite,
                EXCEL_PATH.name,
                EXPORT_VERSION
            ))

        self.stats["daily_sessions"] = 1
        print(f"  Exported: 1 session")

    def _export_market_structure(self):
        """Export market structure data."""
        print("[3/11] Exporting market_structure...")

        # Read data
        indices = self.reader.read_market_structure_indices()
        tickers = self.reader.read_market_structure_tickers()
        all_data = indices + tickers

        if self.validate_only:
            exporter = MarketStructureExporter()
            valid, errors = exporter.validate(all_data)
            if not valid:
                self.errors.extend(errors)
                print(f"  VALIDATION FAILED: {len(errors)} errors")
            else:
                print(f"  Validated: {len(all_data)} records")
            return

        if self.dry_run:
            print(f"  [DRY-RUN] Would export {len(all_data)} records")
            self.stats["market_structure"] = len(all_data)
            return

        exporter = MarketStructureExporter(self.conn)
        count = exporter.export(all_data, self.session_date)
        self.stats["market_structure"] = count
        print(f"  Exported: {count} records")

    def _export_bar_data(self):
        """Export bar data."""
        print("[4/11] Exporting bar_data...")

        data = self.reader.read_bar_data()

        if self.validate_only:
            exporter = BarDataExporter()
            valid, errors = exporter.validate(data)
            if not valid:
                self.errors.extend(errors)
                print(f"  VALIDATION FAILED: {len(errors)} errors")
            else:
                print(f"  Validated: {len(data)} records")
            return

        if self.dry_run:
            print(f"  [DRY-RUN] Would export {len(data)} records")
            self.stats["bar_data"] = len(data)
            return

        exporter = BarDataExporter(self.conn)
        count = exporter.export(data, self.session_date)
        self.stats["bar_data"] = count
        print(f"  Exported: {count} records")

    def _export_hvn_pocs(self):
        """Export HVN POC data."""
        print("[5/11] Exporting hvn_pocs...")

        data = self.reader.read_hvn_pocs()

        if self.validate_only:
            exporter = HvnPocsExporter()
            valid, errors = exporter.validate(data)
            if not valid:
                self.errors.extend(errors)
                print(f"  VALIDATION FAILED: {len(errors)} errors")
            else:
                print(f"  Validated: {len(data)} records")
            return

        if self.dry_run:
            print(f"  [DRY-RUN] Would export {len(data)} records")
            self.stats["hvn_pocs"] = len(data)
            return

        exporter = HvnPocsExporter(self.conn)
        count = exporter.export(data, self.session_date)
        self.stats["hvn_pocs"] = count
        print(f"  Exported: {count} records")

    def _export_zones(self):
        """Export zones data (raw + filtered)."""
        print("[6/11] Exporting zones...")

        raw_zones = self.reader.read_raw_zones()
        filtered_zones = self.reader.read_zone_results()

        if self.validate_only:
            exporter = ZonesExporter()
            valid1, errors1 = exporter.validate(raw_zones)
            valid2, errors2 = exporter.validate(filtered_zones)
            if not valid1 or not valid2:
                self.errors.extend(errors1 + errors2)
                print(f"  VALIDATION FAILED: {len(errors1) + len(errors2)} errors")
            else:
                print(f"  Validated: {len(raw_zones)} raw + {len(filtered_zones)} filtered")
            return

        if self.dry_run:
            print(f"  [DRY-RUN] Would export {len(raw_zones)} raw + {len(filtered_zones)} filtered zones")
            self.stats["zones"] = len(raw_zones) + len(filtered_zones)
            return

        exporter = ZonesExporter(self.conn)
        count = exporter.export_combined(raw_zones, filtered_zones, self.session_date)
        self.stats["zones"] = count
        print(f"  Exported: {count} records")

    def _export_setups(self):
        """Export setup data."""
        print("[7/11] Exporting setups...")

        data = self.reader.read_setups()

        if self.validate_only:
            exporter = SetupsExporter()
            valid, errors = exporter.validate(data)
            if not valid:
                self.errors.extend(errors)
                print(f"  VALIDATION FAILED: {len(errors)} errors")
            else:
                print(f"  Validated: {len(data)} records")
            return

        if self.dry_run:
            print(f"  [DRY-RUN] Would export {len(data)} records")
            self.stats["setups"] = len(data)
            return

        exporter = SetupsExporter(self.conn)
        count = exporter.export(data, self.session_date)
        self.stats["setups"] = count
        print(f"  Exported: {count} records")

    def _export_trades(self):
        """Export trades data."""
        print("[8/11] Exporting trades...")

        data = self.reader.read_trades()

        if self.validate_only:
            exporter = TradesExporter()
            valid, errors = exporter.validate(data)
            if not valid:
                self.errors.extend(errors)
                print(f"  VALIDATION FAILED: {len(errors)} errors")
            else:
                print(f"  Validated: {len(data)} records")
            return

        if self.dry_run:
            print(f"  [DRY-RUN] Would export {len(data)} records")
            self.stats["trades"] = len(data)
            return

        exporter = TradesExporter(self.conn)
        count = exporter.export(data, self.session_date)
        self.stats["trades"] = count
        print(f"  Exported: {count} records")

    def _export_trade_bars(self):
        """Export trade bars data (v1.2.0 - 33 columns)."""
        print("[9/11] Exporting trade_bars...")

        data = self.reader.read_trade_bars()

        if not data:
            print("  No trade_bars data found (worksheet may not exist)")
            self.stats["trade_bars"] = 0
            return

        if self.validate_only:
            exporter = TradeBarsExporter()
            valid, errors = exporter.validate(data)
            if not valid:
                self.errors.extend(errors)
                print(f"  VALIDATION FAILED: {len(errors)} errors")
            else:
                print(f"  Validated: {len(data)} records")
            return

        if self.dry_run:
            print(f"  [DRY-RUN] Would export {len(data)} records")
            self.stats["trade_bars"] = len(data)
            return

        exporter = TradeBarsExporter(self.conn)
        count = exporter.export(data, self.session_date)
        self.stats["trade_bars"] = count
        print(f"  Exported: {count} records")

    def _export_optimal_trade(self):
        """Export optimal trade analysis data (v5.0.0)."""
        print("[10/11] Exporting optimal_trade...")

        data = self.reader.read_optimal_trade()

        if not data:
            print("  No optimal_trade data found (worksheet may not exist)")
            self.stats["optimal_trade"] = 0
            return

        if self.validate_only:
            exporter = OptimalTradeExporter()
            valid, errors = exporter.validate(data)
            if not valid:
                self.errors.extend(errors)
                print(f"  VALIDATION FAILED: {len(errors)} errors")
            else:
                print(f"  Validated: {len(data)} records")
            return

        if self.dry_run:
            print(f"  [DRY-RUN] Would export {len(data)} records")
            self.stats["optimal_trade"] = len(data)
            return

        exporter = OptimalTradeExporter(self.conn)
        count = exporter.export(data, self.session_date)
        self.stats["optimal_trade"] = count
        print(f"  Exported: {count} records")

    def _export_options_analysis(self):
        """Export options analysis data (v1.0)."""
        print("[11/11] Exporting options_analysis...")

        data = self.reader.read_options_analysis()

        if not data:
            print("  No options_analysis data found (worksheet may not exist)")
            self.stats["options_analysis"] = 0
            return

        if self.validate_only:
            exporter = OptionsAnalysisExporter()
            valid, errors = exporter.validate(data)
            if not valid:
                self.errors.extend(errors)
                print(f"  VALIDATION FAILED: {len(errors)} errors")
            else:
                print(f"  Validated: {len(data)} records")
            return

        if self.dry_run:
            print(f"  [DRY-RUN] Would export {len(data)} records")
            self.stats["options_analysis"] = len(data)
            return

        exporter = OptionsAnalysisExporter(self.conn)
        count = exporter.export(data, self.session_date)
        self.stats["options_analysis"] = count
        print(f"  Exported: {count} records")

    def _print_summary(self):
        """Print export summary."""
        print()
        print("=" * 60)
        print("EXPORT SUMMARY")
        print("=" * 60)
        print(f"Session Date: {self.session_date}")
        print()

        if self.dry_run:
            print("MODE: DRY-RUN (no data written)")
        elif self.validate_only:
            print("MODE: VALIDATE ONLY")
        else:
            print("MODE: FULL EXPORT")

        print()
        print("Records by Table:")
        print("-" * 40)
        total = 0
        for table, count in self.stats.items():
            print(f"  {table:25} {count:>6}")
            total += count
        print("-" * 40)
        print(f"  {'TOTAL':25} {total:>6}")

        if self.errors:
            print()
            print("ERRORS:")
            print("-" * 40)
            for error in self.errors:
                print(f"  ! {error}")

        print()
        print("=" * 60)
        if self.errors:
            print("COMPLETED WITH ERRORS")
        else:
            print("COMPLETED SUCCESSFULLY")
        print("=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Export Epoch trading data to Supabase"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be exported without writing to database"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate data only, don't export"
    )

    args = parser.parse_args()

    runner = DatabaseExportRunner(
        dry_run=args.dry_run,
        validate_only=args.validate
    )

    try:
        success = runner.run()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
