#!/usr/bin/env python3
"""
================================================================================
EPOCH TRADING SYSTEM - JOURNAL PROCESSOR 2
j_m1_indicator_bars - CLI Runner
XIII Trading LLC
================================================================================

Usage:
    python runner.py                    # Full batch run
    python runner.py --dry-run          # Calculate but don't save
    python runner.py --limit 10         # Process 10 ticker-dates
    python runner.py --schema           # Create database table
    python runner.py --status           # Show table status

Version: 1.0.0
================================================================================
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from db_config import DB_CONFIG, SCHEMA_DIR, J_M1_INDICATOR_BARS_TABLE

from calculator import JM1IndicatorBarsPopulator


def run_schema():
    import psycopg2
    schema_file = SCHEMA_DIR / "j_m1_indicator_bars.sql"
    if not schema_file.exists():
        print(f"ERROR: Schema file not found: {schema_file}")
        return False

    print("=" * 60)
    print("j_m1_indicator_bars - Schema Creation")
    print("=" * 60)

    try:
        with open(schema_file, 'r') as f:
            schema_sql = f.read()
        conn = psycopg2.connect(**DB_CONFIG)
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
    import psycopg2
    print("=" * 60)
    print("j_m1_indicator_bars - Status")
    print("=" * 60)

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        populator = JM1IndicatorBarsPopulator(verbose=False)
        status = populator.get_status(conn)
        conn.close()

        print(f"\n  Total Bars:            {status['total_bars']:,}")
        print(f"  Unique Ticker-Dates:   {status['unique_ticker_dates']:,}")
        print(f"  Date Range:            {status['min_date']} to {status['max_date']}")
        print(f"  Pending Ticker-Dates:  {status['pending_ticker_dates']:,}")
        return True
    except Exception as e:
        print(f"\nERROR: {e}")
        return False


def run_population(args):
    print()
    print("=" * 60)
    print("EPOCH JOURNAL SYSTEM")
    print("j_m1_indicator_bars Populator v1.0.0")
    print("=" * 60)
    print()

    populator = JM1IndicatorBarsPopulator(verbose=args.verbose)

    results = populator.run_batch_population(
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
    print(f"  Execution Time:          {results['execution_time_seconds']:.1f}s")

    if results['errors']:
        print("\nERRORS:")
        for err in results['errors'][:10]:
            print(f"  ! {err}")

    return len(results['errors']) == 0


def main():
    parser = argparse.ArgumentParser(description='Populate journal M1 indicator bars')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--limit', type=int, metavar='N')
    parser.add_argument('--verbose', '-v', action='store_true')
    parser.add_argument('--schema', action='store_true')
    parser.add_argument('--status', action='store_true')

    args = parser.parse_args()

    if args.schema:
        sys.exit(0 if run_schema() else 1)
    if args.status:
        sys.exit(0 if show_status() else 1)

    try:
        success = run_population(args)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nInterrupted.")
        sys.exit(130)


if __name__ == "__main__":
    main()
