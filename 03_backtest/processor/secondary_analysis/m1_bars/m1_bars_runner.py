#!/usr/bin/env python3
"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
M1 Bars Storage - CLI Runner
XIII Trading LLC
================================================================================

Command-line interface for storing 1-minute bar data from Polygon to Supabase.
Fetches prior day 16:00 ET through trade day 16:00 ET for each ticker-date.

Usage:
    python m1_bars_runner.py                    # Full batch run
    python m1_bars_runner.py --dry-run          # Fetch but don't save
    python m1_bars_runner.py --limit 10         # Process max 10 ticker-dates
    python m1_bars_runner.py --verbose          # Detailed logging
    python m1_bars_runner.py --schema           # Create database table
    python m1_bars_runner.py --status           # Show storage status

Version: 2.0.0
================================================================================
"""

import argparse
import sys
import logging
from pathlib import Path
from datetime import datetime

# Ensure we import from our local module first
MODULE_DIR = Path(__file__).parent
sys.path.insert(0, str(MODULE_DIR))

# Import from local config
from config import DB_CONFIG, SCHEMA_DIR, SOURCE_TABLE, TARGET_TABLE

from m1_bars_storage import M1BarsStorage, M1BarFetcher


def setup_logging(verbose: bool = False):
    """Configure logging based on verbosity."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def run_schema():
    """Execute the schema SQL to create the m1_bars table."""
    import psycopg2

    schema_file = SCHEMA_DIR / "m1_bars.sql"

    if not schema_file.exists():
        print(f"ERROR: Schema file not found: {schema_file}")
        return False

    print("=" * 60)
    print("M1 Bars - Schema Creation")
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


def show_status():
    """Show current storage status."""
    import psycopg2

    print("=" * 60)
    print("M1 Bars - Storage Status")
    print("=" * 60)

    try:
        conn = psycopg2.connect(**DB_CONFIG)

        with conn.cursor() as cur:
            # Total bars stored
            cur.execute(f"SELECT COUNT(*) FROM {TARGET_TABLE}")
            total_bars = cur.fetchone()[0]

            # Unique ticker-dates
            cur.execute(f"SELECT COUNT(DISTINCT (ticker, bar_date)) FROM {TARGET_TABLE}")
            unique_ticker_dates = cur.fetchone()[0]

            # Unique tickers
            cur.execute(f"SELECT COUNT(DISTINCT ticker) FROM {TARGET_TABLE}")
            unique_tickers = cur.fetchone()[0]

            # Date range
            cur.execute(f"SELECT MIN(bar_date), MAX(bar_date) FROM {TARGET_TABLE}")
            date_range = cur.fetchone()

            # Required ticker-dates from trades_2
            cur.execute(f"SELECT COUNT(DISTINCT (ticker, date)) FROM {SOURCE_TABLE}")
            required_ticker_dates = cur.fetchone()[0]

            # Missing ticker-dates
            cur.execute(f"""
                SELECT COUNT(*) FROM (
                    SELECT DISTINCT ticker, date FROM {SOURCE_TABLE}
                    EXCEPT
                    SELECT DISTINCT ticker, bar_date FROM {TARGET_TABLE}
                ) missing
            """)
            missing_ticker_dates = cur.fetchone()[0]

        conn.close()

        print(f"\n  Total Bars Stored:     {total_bars:,}")
        print(f"  Unique Ticker-Dates:   {unique_ticker_dates:,}")
        print(f"  Unique Tickers:        {unique_tickers:,}")
        print(f"  Date Range:            {date_range[0]} to {date_range[1]}")
        print()
        print(f"  Required (from {SOURCE_TABLE}): {required_ticker_dates:,}")
        print(f"  Missing:               {missing_ticker_dates:,}")
        print(f"  Coverage:              {(unique_ticker_dates / required_ticker_dates * 100) if required_ticker_dates > 0 else 0:.1f}%")

        return True

    except psycopg2.errors.UndefinedTable:
        print(f"\n  Table '{TARGET_TABLE}' does not exist.")
        print("  Run with --schema to create it.")
        return False

    except Exception as e:
        print(f"\nERROR: {e}")
        return False


def run_storage(args):
    """Run the M1 bars storage process."""
    print()
    print("=" * 60)
    print("EPOCH TRADING SYSTEM")
    print("M1 Bars Storage v2.0.0")
    print("Prior Day 16:00 ET -> Trade Day 16:00 ET")
    print("=" * 60)
    print()
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Source: {SOURCE_TABLE}")
    print(f"Mode: {'DRY-RUN' if args.dry_run else 'FULL RUN'}")
    if args.limit:
        print(f"Limit: {args.limit} ticker-dates")
    print()

    # Create fetcher and storage manager
    fetcher = M1BarFetcher()
    storage = M1BarsStorage(fetcher=fetcher, verbose=args.verbose)

    # Run storage
    results = storage.run_batch_storage(
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
    print(f"  API Calls Made:          {results['api_calls_made']}")
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
        description='Store 1-minute bar data from Polygon to Supabase',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python m1_bars_runner.py                    # Full batch run
  python m1_bars_runner.py --dry-run          # Test without saving
  python m1_bars_runner.py --limit 10         # Process 10 ticker-dates
  python m1_bars_runner.py --schema           # Create database table
  python m1_bars_runner.py --status           # Show storage status

Output:
  Bars are written to the m1_bars table in Supabase.
  Each unique (ticker, date) gets bars from prior day 16:00 to trade day 16:00 ET.
        """
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Fetch from Polygon but do not save to database'
    )

    parser.add_argument(
        '--limit',
        type=int,
        metavar='N',
        help='Maximum number of ticker-date pairs to process'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    parser.add_argument(
        '--schema',
        action='store_true',
        help='Run schema creation only (create m1_bars table)'
    )

    parser.add_argument(
        '--status',
        action='store_true',
        help='Show current storage status'
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
        success = show_status()
        sys.exit(0 if success else 1)

    # Run storage
    try:
        success = run_storage(args)
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
