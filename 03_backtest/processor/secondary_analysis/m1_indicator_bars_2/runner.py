#!/usr/bin/env python3
"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
M1 Indicator Bars v2 - CLI Runner
XIII Trading LLC
================================================================================

Command-line interface for running the M1 Indicator Bars v2 population.
Reads raw M1 bars from m1_bars_2, calculates entry qualifier standard
indicators + extended analysis, writes to m1_indicator_bars_2.

Usage:
    python runner.py                    # Full batch run
    python runner.py --dry-run          # Calculate but don't save
    python runner.py --limit 10         # Process max 10 ticker-dates
    python runner.py --verbose          # Detailed logging
    python runner.py --schema           # Create database table
    python runner.py --status           # Show current status

Version: 2.0.0
================================================================================
"""

import argparse
import sys
import logging
from pathlib import Path
from datetime import datetime

# Use explicit path imports to avoid collisions with other modules
import importlib.util
_MODULE_DIR = Path(__file__).resolve().parent

# Load local config
_config_spec = importlib.util.spec_from_file_location("local_config", _MODULE_DIR / "config.py")
_config = importlib.util.module_from_spec(_config_spec)
_config_spec.loader.exec_module(_config)
DB_CONFIG = _config.DB_CONFIG
SCHEMA_DIR = _config.SCHEMA_DIR
TARGET_TABLE = _config.TARGET_TABLE
M1_BARS_TABLE = _config.M1_BARS_TABLE
SOURCE_TABLE = _config.SOURCE_TABLE

# Load local populator
_pop_spec = importlib.util.spec_from_file_location("populator", _MODULE_DIR / "populator.py")
_pop_mod = importlib.util.module_from_spec(_pop_spec)
_pop_spec.loader.exec_module(_pop_mod)
M1IndicatorBarsPopulator = _pop_mod.M1IndicatorBarsPopulator


def setup_logging(verbose: bool = False):
    """Configure logging based on verbosity."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def run_schema():
    """Execute the schema SQL to create the m1_indicator_bars_2 table."""
    import psycopg2

    schema_file = SCHEMA_DIR / "m1_indicator_bars_2.sql"

    if not schema_file.exists():
        print(f"ERROR: Schema file not found: {schema_file}")
        return False

    print("=" * 60)
    print("M1 Indicator Bars v2 - Schema Creation")
    print("=" * 60)

    try:
        print("\n[1/3] Reading schema file...")
        with open(schema_file, 'r') as f:
            schema_sql = f.read()
        print(f"  Read {len(schema_sql)} bytes")

        print("\n[2/3] Connecting to Supabase...")
        conn = psycopg2.connect(**DB_CONFIG)
        print("  Connected successfully")

        print("\n[3/3] Executing schema...")
        with conn.cursor() as cur:
            cur.execute(schema_sql)
        conn.commit()
        print("  Schema created successfully")

        conn.close()
        return True

    except Exception as e:
        print(f"\nERROR: {e}")
        return False


def run_status():
    """Show current status of the m1_indicator_bars_2 table."""
    import psycopg2

    print("=" * 60)
    print("M1 Indicator Bars v2 - Status")
    print("=" * 60)

    try:
        print("\nConnecting to Supabase...")
        conn = psycopg2.connect(**DB_CONFIG)
        print("  Connected successfully\n")

        populator = M1IndicatorBarsPopulator(verbose=False)
        status = populator.get_status(conn)

        print("Current Status:")
        print("-" * 40)
        print(f"  Total Bars:           {status.get('total_bars', 0):,}")
        print(f"  Unique Ticker-Dates:  {status.get('unique_ticker_dates', 0):,}")
        print(f"  Unique Tickers:       {status.get('unique_tickers', 0):,}")

        if status.get('min_date'):
            print(f"  Date Range:           {status.get('min_date')} to {status.get('max_date')}")

        print(f"\n  Pending Ticker-Dates: {status.get('pending_ticker_dates', 0):,}")
        print(f"\n  Source: {SOURCE_TABLE}")
        print(f"  M1 Bars: {M1_BARS_TABLE}")
        print(f"  Target: {TARGET_TABLE}")

        conn.close()
        return True

    except psycopg2.errors.UndefinedTable:
        print(f"\n  Table '{TARGET_TABLE}' does not exist.")
        print("  Run with --schema to create it.")
        return False

    except Exception as e:
        print(f"\nERROR: {e}")
        return False


def run_population(args):
    """Run the M1 indicator bars population."""
    print()
    print("=" * 60)
    print("EPOCH TRADING SYSTEM")
    print("M1 Indicator Bars Calculator v2.0.0")
    print("Entry Qualifier Standard + Extended Analysis")
    print("=" * 60)
    print()
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Source: {SOURCE_TABLE} -> {M1_BARS_TABLE} -> {TARGET_TABLE}")
    print(f"Mode: {'DRY-RUN' if args.dry_run else 'FULL RUN'}")
    if args.limit:
        print(f"Limit: {args.limit} ticker-dates")
    print()

    # Create populator and run
    populator = M1IndicatorBarsPopulator(verbose=args.verbose)

    results = populator.run_batch_population(
        limit=args.limit,
        dry_run=args.dry_run
    )

    # Print results summary
    print()
    print("=" * 60)
    print("EXECUTION SUMMARY")
    print("=" * 60)
    print(f"  Ticker-Dates Processed:  {results['ticker_dates_processed']}")
    print(f"  Ticker-Dates Skipped:    {results['ticker_dates_skipped']}")
    print(f"  Bars Inserted:           {results['bars_inserted']:,}")
    print(f"  Execution Time:          {results['execution_time_seconds']:.1f}s")

    if results['errors']:
        print()
        print("ERRORS:")
        print("-" * 40)
        for err in results['errors'][:10]:
            print(f"  ! {err}")
        if len(results['errors']) > 10:
            print(f"  ... and {len(results['errors']) - 10} more errors")

    print()
    print("=" * 60)
    if results['errors']:
        print("COMPLETED WITH ERRORS")
    elif results['ticker_dates_processed'] == 0:
        print("NO TICKER-DATES TO PROCESS")
    else:
        print("COMPLETED SUCCESSFULLY")
    print("=" * 60)

    return len(results['errors']) == 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Calculate M1 Indicator Bars v2 for all ticker-dates',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python runner.py                    # Full batch run
  python runner.py --dry-run          # Test without saving
  python runner.py --limit 10         # Process 10 ticker-dates
  python runner.py --schema           # Create database table
  python runner.py --status           # Show current status

Pipeline:
  trades_2 (entries) -> m1_bars_2 (raw bars) -> m1_indicator_bars_2 (enriched)
        """
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Calculate without saving to database'
    )

    parser.add_argument(
        '--limit',
        type=int,
        metavar='N',
        help='Maximum number of ticker-dates to process'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    parser.add_argument(
        '--schema',
        action='store_true',
        help='Run schema creation only (create m1_indicator_bars_2 table)'
    )

    parser.add_argument(
        '--status',
        action='store_true',
        help='Show current status of m1_indicator_bars_2 table'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)

    # Run schema creation if requested
    if args.schema:
        success = run_schema()
        sys.exit(0 if success else 1)

    # Show status if requested
    if args.status:
        success = run_status()
        sys.exit(0 if success else 1)

    # Run population
    try:
        success = run_population(args)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
