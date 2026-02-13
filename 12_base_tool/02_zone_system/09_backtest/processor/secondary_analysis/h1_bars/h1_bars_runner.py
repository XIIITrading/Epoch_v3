#!/usr/bin/env python3
"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
H1 Bars - CLI Runner
XIII Trading LLC
================================================================================

Command-line interface for running the H1 Bars storage.

Usage:
    python h1_bars_runner.py                    # Full batch run
    python h1_bars_runner.py --dry-run          # Fetch but don't save
    python h1_bars_runner.py --limit 10         # Process max 10 ticker-dates
    python h1_bars_runner.py --verbose          # Detailed logging
    python h1_bars_runner.py --schema           # Create database table
    python h1_bars_runner.py --status           # Show current status

Version: 1.0.0
================================================================================
"""

import argparse
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add module to path
sys.path.insert(0, str(Path(__file__).parent))

from config import DB_CONFIG, SCHEMA_DIR, TARGET_TABLE
from h1_bars_storage import H1BarsStorage


def setup_logging(verbose: bool = False):
    """Configure logging based on verbosity."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def run_schema():
    """Execute the schema SQL to create the h1_bars table."""
    import psycopg2

    schema_file = SCHEMA_DIR / "h1_bars.sql"

    if not schema_file.exists():
        print(f"ERROR: Schema file not found: {schema_file}")
        return False

    print("=" * 60)
    print("H1 Bars - Schema Creation")
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
    """Show current status of the h1_bars table."""
    import psycopg2

    print("=" * 60)
    print("H1 Bars - Status")
    print("=" * 60)

    try:
        print("\nConnecting to Supabase...")
        conn = psycopg2.connect(**DB_CONFIG)
        print("  Connected successfully\n")

        storage = H1BarsStorage(verbose=False)
        status = storage.get_status(conn)

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


def run_storage(args):
    """Run the H1 bars storage."""
    print()
    print("=" * 60)
    print("EPOCH TRADING SYSTEM")
    print("H1 Bars Storage v1.0.0")
    print("=" * 60)
    print()
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Mode: {'DRY-RUN' if args.dry_run else 'FULL RUN'}")
    if args.limit:
        print(f"Limit: {args.limit} ticker-dates")
    print()

    # Create storage handler and run
    storage = H1BarsStorage(verbose=args.verbose)

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
    print(f"  Bars Inserted:           {results['bars_inserted']}")
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
        description='Fetch and store H1 bars for all ticker-dates',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python h1_bars_runner.py                    # Full batch run
  python h1_bars_runner.py --dry-run          # Test without saving
  python h1_bars_runner.py --limit 10         # Process 10 ticker-dates
  python h1_bars_runner.py --schema           # Create database table
  python h1_bars_runner.py --status           # Show current status

Output:
  Results are written to the h1_bars table in Supabase.
  Each ticker-date produces ~50-60 H1 bars (lookback + trading day).
        """
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Fetch without saving to database'
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
        help='Run schema creation only (create h1_bars table)'
    )

    parser.add_argument(
        '--status',
        action='store_true',
        help='Show current status of h1_bars table'
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
