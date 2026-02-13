#!/usr/bin/env python3
"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
M1 Indicator Bars - CLI Runner
XIII Trading LLC
================================================================================

Command-line interface for running the M1 Indicator Bars population.

Usage:
    python runner.py                    # Full batch run
    python runner.py --dry-run          # Calculate but don't save
    python runner.py --limit 10         # Process max 10 ticker-dates
    python runner.py --verbose          # Detailed logging
    python runner.py --schema           # Create database table
    python runner.py --status           # Show current status

Version: 1.0.0
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
    """Execute the schema SQL to create the m1_indicator_bars table."""
    import psycopg2

    schema_file = SCHEMA_DIR / "m1_indicator_bars.sql"

    if not schema_file.exists():
        print(f"ERROR: Schema file not found: {schema_file}")
        return False

    print("=" * 60)
    print("M1 Indicator Bars - Schema Creation")
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


def run_migrate():
    """Execute the migration SQL to add EPCH v1.0 columns and update existing data."""
    import psycopg2

    migrate_file = SCHEMA_DIR / "add_epch_columns.sql"

    if not migrate_file.exists():
        print(f"ERROR: Migration file not found: {migrate_file}")
        return False

    print("=" * 60)
    print("M1 Indicator Bars - Add EPCH v1.0 Columns")
    print("=" * 60)

    try:
        print("\n[1/3] Reading migration file...")
        with open(migrate_file, 'r') as f:
            migrate_sql = f.read()
        print(f"  Read {len(migrate_sql)} bytes")

        print("\n[2/3] Connecting to Supabase...")
        conn = psycopg2.connect(**DB_CONFIG)
        print("  Connected successfully")

        print("\n[3/3] Executing migration...")
        print("  - Adding columns: candle_range_pct, long_score, short_score")
        print("  - Updating existing rows with calculated values...")

        with conn.cursor() as cur:
            cur.execute(migrate_sql)
            # Get the verification result
            cur.execute("""
                SELECT
                    COUNT(*) as total_rows,
                    COUNT(candle_range_pct) as rows_with_candle_range,
                    COUNT(long_score) as rows_with_long_score,
                    COUNT(short_score) as rows_with_short_score
                FROM m1_indicator_bars
            """)
            result = cur.fetchone()

        conn.commit()

        print("\n  Migration completed successfully!")
        print(f"\n  Verification:")
        print(f"    Total rows:              {result[0]:,}")
        print(f"    Rows with candle_range:  {result[1]:,}")
        print(f"    Rows with long_score:    {result[2]:,}")
        print(f"    Rows with short_score:   {result[3]:,}")

        conn.close()
        return True

    except Exception as e:
        print(f"\nERROR: {e}")
        return False


def run_status():
    """Show current status of the m1_indicator_bars table."""
    import psycopg2

    print("=" * 60)
    print("M1 Indicator Bars - Status")
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

        conn.close()
        return True

    except Exception as e:
        print(f"\nERROR: {e}")
        return False


def run_population(args):
    """Run the M1 indicator bars population."""
    print()
    print("=" * 60)
    print("EPOCH TRADING SYSTEM")
    print("M1 Indicator Bars Calculator v1.0.0")
    print("=" * 60)
    print()
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
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
    print(f"  Bars Inserted:           {results['bars_inserted']}")
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
        description='Calculate M1 Indicator Bars for all ticker-dates',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python runner.py                    # Full batch run
  python runner.py --dry-run          # Test without saving
  python runner.py --limit 10         # Process 10 ticker-dates
  python runner.py --schema           # Create database table
  python runner.py --status           # Show current status

Output:
  Results are written to the m1_indicator_bars table in Supabase.
  Each ticker-date produces ~480 rows (one per M1 bar 08:00-16:00).
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
        help='Run schema creation only (create m1_indicator_bars table)'
    )

    parser.add_argument(
        '--status',
        action='store_true',
        help='Show current status of m1_indicator_bars table'
    )

    parser.add_argument(
        '--migrate',
        action='store_true',
        help='Add EPCH v1.0 columns (candle_range_pct, long_score, short_score) and update existing rows'
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

    # Run migration if requested
    if args.migrate:
        success = run_migrate()
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
