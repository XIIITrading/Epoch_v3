#!/usr/bin/env python3
"""
================================================================================
EPOCH TRADING SYSTEM - JOURNAL PROCESSOR 1
j_m1_bars - CLI Runner
XIII Trading LLC
================================================================================

CLI for storing journal M1 bar data from Polygon to Supabase.

Usage:
    python runner.py                    # Full batch run
    python runner.py --dry-run          # Fetch but don't save
    python runner.py --limit 10         # Process 10 ticker-dates
    python runner.py --schema           # Create database table
    python runner.py --status           # Show storage status

Version: 1.0.0
================================================================================
"""

import argparse
import sys
import logging
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from db_config import DB_CONFIG, SCHEMA_DIR, SOURCE_TABLE, J_M1_BARS_TABLE, JOURNAL_SYMBOL_COL, JOURNAL_DATE_COL

from storage import JM1BarsStorage, M1BarFetcher


def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def run_schema():
    """Create the j_m1_bars table."""
    import psycopg2

    schema_file = SCHEMA_DIR / "j_m1_bars.sql"

    if not schema_file.exists():
        print(f"ERROR: Schema file not found: {schema_file}")
        return False

    print("=" * 60)
    print("j_m1_bars - Schema Creation")
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
        conn.close()
        print("  Schema created successfully")
        return True

    except Exception as e:
        print(f"\nERROR: {e}")
        return False


def show_status():
    """Show current storage status."""
    import psycopg2

    print("=" * 60)
    print("j_m1_bars - Storage Status")
    print("=" * 60)

    try:
        conn = psycopg2.connect(**DB_CONFIG)

        with conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM {J_M1_BARS_TABLE}")
            total_bars = cur.fetchone()[0]

            cur.execute(f"SELECT COUNT(DISTINCT (ticker, bar_date)) FROM {J_M1_BARS_TABLE}")
            unique_ticker_dates = cur.fetchone()[0]

            cur.execute(f"SELECT COUNT(DISTINCT ticker) FROM {J_M1_BARS_TABLE}")
            unique_tickers = cur.fetchone()[0]

            cur.execute(f"SELECT MIN(bar_date), MAX(bar_date) FROM {J_M1_BARS_TABLE}")
            date_range = cur.fetchone()

            cur.execute(f"SELECT COUNT(DISTINCT ({JOURNAL_SYMBOL_COL}, {JOURNAL_DATE_COL})) FROM {SOURCE_TABLE}")
            required_ticker_dates = cur.fetchone()[0]

            cur.execute(f"""
                SELECT COUNT(*) FROM (
                    SELECT DISTINCT {JOURNAL_SYMBOL_COL} AS ticker, {JOURNAL_DATE_COL} AS date
                    FROM {SOURCE_TABLE}
                    EXCEPT
                    SELECT DISTINCT ticker, bar_date FROM {J_M1_BARS_TABLE}
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
        coverage = (unique_ticker_dates / required_ticker_dates * 100) if required_ticker_dates > 0 else 0
        print(f"  Coverage:              {coverage:.1f}%")
        return True

    except Exception as e:
        print(f"\nERROR: {e}")
        return False


def run_storage(args):
    """Run the j_m1_bars storage process."""
    print()
    print("=" * 60)
    print("EPOCH JOURNAL SYSTEM")
    print("j_m1_bars Storage v1.0.0")
    print("=" * 60)
    print()

    fetcher = M1BarFetcher()
    storage = JM1BarsStorage(fetcher=fetcher, verbose=args.verbose)

    results = storage.run_batch_storage(
        limit=args.limit,
        dry_run=args.dry_run
    )

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
        for err in results['errors'][:10]:
            print(f"  ! {err}")

    return len(results['errors']) == 0


def main():
    parser = argparse.ArgumentParser(description='Store journal M1 bar data from Polygon')

    parser.add_argument('--dry-run', action='store_true', help='Fetch but do not save')
    parser.add_argument('--limit', type=int, metavar='N', help='Max ticker-date pairs')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--schema', action='store_true', help='Create j_m1_bars table')
    parser.add_argument('--status', action='store_true', help='Show storage status')

    args = parser.parse_args()
    setup_logging(args.verbose)

    if args.schema:
        sys.exit(0 if run_schema() else 1)
    if args.status:
        sys.exit(0 if show_status() else 1)

    try:
        success = run_storage(args)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        sys.exit(130)


if __name__ == "__main__":
    main()
