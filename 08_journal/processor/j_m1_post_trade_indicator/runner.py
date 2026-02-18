#!/usr/bin/env python3
"""
================================================================================
EPOCH TRADING SYSTEM - JOURNAL PROCESSOR 8
j_m1_post_trade_indicator - CLI Runner
XIII Trading LLC
================================================================================

Command-line interface for the post-trade indicator bars populator.

Usage:
    python runner.py              # Full batch run
    python runner.py --dry-run    # Calculate but don't save
    python runner.py --limit 50   # Process max 50 trades
    python runner.py --verbose    # Detailed logging
    python runner.py --schema     # Run schema creation only
    python runner.py --status     # Show current processing status

Version: 1.0.0
================================================================================
"""

import argparse
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add parent directory to path for db_config import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Add current directory to path for populator import
sys.path.insert(0, str(Path(__file__).resolve().parent))

from db_config import DB_CONFIG, SCHEMA_DIR, J_M1_POST_TRADE_INDICATOR_TABLE, POST_TRADE_BARS
from populator import JM1PostTradeIndicatorPopulator


def setup_logging(verbose: bool = False):
    """Configure logging based on verbosity."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def run_schema():
    """Execute the schema SQL to create the j_m1_post_trade_indicator table."""
    import psycopg2

    schema_file = SCHEMA_DIR / "j_m1_post_trade_indicator.sql"

    if not schema_file.exists():
        print(f"ERROR: Schema file not found: {schema_file}")
        return False

    print("=" * 60)
    print("j_m1_post_trade_indicator - Schema Creation")
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
    """Display current processing status."""
    import psycopg2

    print()
    print("=" * 60)
    print("J_M1 POST-TRADE INDICATOR - Processing Status")
    print("=" * 60)

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        populator = JM1PostTradeIndicatorPopulator(verbose=False)
        status = populator.get_status(conn)
        conn.close()

        print()
        print(f"  Eligible Trades:      {status['total_eligible']}")
        print(f"  Trades Processed:     {status['trades_processed']}")
        print(f"  Total Rows:           {status['total_rows']:,}")
        print(f"  Remaining Trades:     {status['remaining']}")
        print(f"  Bars Per Trade:       {POST_TRADE_BARS}")
        print()
        winners = status.get('winners', 0)
        losers = status.get('losers', 0)
        total = winners + losers
        if total > 0:
            win_rate = (winners / total * 100)
            print(f"  Winners:              {winners}")
            print(f"  Losers:               {losers}")
            print(f"  Win Rate:             {win_rate:.1f}%")
        print()
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\nERROR: {e}")
        return False


def run_population(args):
    """Run the j_m1_post_trade_indicator population."""
    print()
    print("=" * 60)
    print("EPOCH JOURNAL SYSTEM")
    print("j_m1_post_trade_indicator Populator v1.0.0")
    print("=" * 60)
    print()
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Mode: {'DRY-RUN' if args.dry_run else 'FULL RUN'}")
    print(f"Post-Trade Bars: {POST_TRADE_BARS}")
    if args.limit:
        print(f"Limit: {args.limit} trades")
    print()

    populator = JM1PostTradeIndicatorPopulator(verbose=args.verbose)

    results = populator.run_batch_population(
        limit=args.limit,
        dry_run=args.dry_run
    )

    # Print results summary
    print()
    print("=" * 60)
    print("EXECUTION SUMMARY")
    print("=" * 60)
    print(f"  Trades Processed:  {results['trades_processed']}")
    print(f"  Trades Skipped:    {results['trades_skipped']}")
    print(f"  Records Created:   {results['records_created']:,}")
    print(f"  Execution Time:    {results['execution_time_seconds']:.1f}s")

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
    elif results['trades_processed'] == 0:
        print("NO TRADES TO PROCESS")
    else:
        print("COMPLETED SUCCESSFULLY")
    print("=" * 60)

    return len(results['errors']) == 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Populate j_m1_post_trade_indicator with 25 M1 bars after entry',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python runner.py              # Full batch run
  python runner.py --dry-run    # Test without saving
  python runner.py --limit 50   # Process 50 trades
  python runner.py --schema     # Create database table
  python runner.py --status     # Show processing status

Output:
  Results are written to the j_m1_post_trade_indicator table in Supabase.
  Each trade gets up to 25 rows (bar_sequence 0-24), one per M1 bar.
  Outcome (is_winner, pnl_r, max_r_achieved) is stamped on every row.
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
        help='Maximum number of trades to process'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    parser.add_argument(
        '--schema',
        action='store_true',
        help='Run schema creation only (create j_m1_post_trade_indicator table)'
    )

    parser.add_argument(
        '--status',
        action='store_true',
        help='Show current processing status'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)

    # Show status if requested
    if args.status:
        success = show_status()
        sys.exit(0 if success else 1)

    # Run schema creation if requested
    if args.schema:
        success = run_schema()
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
