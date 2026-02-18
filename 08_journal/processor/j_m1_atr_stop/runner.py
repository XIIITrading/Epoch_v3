#!/usr/bin/env python3
"""
================================================================================
EPOCH TRADING SYSTEM - JOURNAL PROCESSOR
J_M1 ATR Stop Processor - CLI Runner
XIII Trading LLC
================================================================================

Command-line interface for running the J_M1 ATR Stop calculation.

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

# Add current directory to path for calculator import
sys.path.insert(0, str(Path(__file__).resolve().parent))

from db_config import DB_CONFIG, SCHEMA_DIR, R_LEVELS, EOD_CUTOFF, SOURCE_TABLE, J_M1_ATR_STOP_TABLE
from calculator import JM1AtrStopCalculator


def setup_logging(verbose: bool = False):
    """Configure logging based on verbosity."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def run_schema():
    """Execute the schema SQL to create the j_m1_atr_stop table."""
    import psycopg2

    schema_file = SCHEMA_DIR / "j_m1_atr_stop.sql"

    if not schema_file.exists():
        print(f"ERROR: Schema file not found: {schema_file}")
        return False

    print("=" * 60)
    print("J_M1 ATR Stop - Schema Creation")
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
    print("J_M1 ATR STOP - Processing Status")
    print("=" * 60)

    try:
        conn = psycopg2.connect(**DB_CONFIG)

        with conn.cursor() as cur:
            # Total journal trades with entry data
            cur.execute(f"""
                SELECT COUNT(*)
                FROM {SOURCE_TABLE}
                WHERE entry_time IS NOT NULL AND entry_price IS NOT NULL
            """)
            total_eligible = cur.fetchone()[0]

            # Already processed
            cur.execute(f"SELECT COUNT(*) FROM {J_M1_ATR_STOP_TABLE}")
            total_processed = cur.fetchone()[0]

            # Remaining
            cur.execute(f"""
                SELECT COUNT(*)
                FROM {SOURCE_TABLE} t
                WHERE t.entry_time IS NOT NULL
                  AND t.entry_price IS NOT NULL
                  AND NOT EXISTS (
                      SELECT 1 FROM {J_M1_ATR_STOP_TABLE} r
                      WHERE r.trade_id = t.trade_id
                  )
            """)
            remaining = cur.fetchone()[0]

            # Win/loss breakdown
            cur.execute(f"""
                SELECT result, COUNT(*)
                FROM {J_M1_ATR_STOP_TABLE}
                GROUP BY result
            """)
            outcomes = dict(cur.fetchall())

        conn.close()

        print()
        print(f"  Eligible Trades:   {total_eligible}")
        print(f"  Processed:         {total_processed}")
        print(f"  Remaining:         {remaining}")
        print()
        if outcomes:
            wins = outcomes.get('WIN', 0)
            losses = outcomes.get('LOSS', 0)
            total = wins + losses
            win_rate = (wins / total * 100) if total > 0 else 0
            print(f"  Wins:              {wins}")
            print(f"  Losses:            {losses}")
            print(f"  Win Rate:          {win_rate:.1f}%")
        print()
        print("=" * 60)

    except Exception as e:
        print(f"\nERROR: {e}")


def run_calculation(args):
    """Run the J_M1 ATR Stop calculation."""
    print()
    print("=" * 60)
    print("EPOCH TRADING SYSTEM")
    print("J_M1 ATR Stop Calculator v1.0.0")
    print("=" * 60)
    print()
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Mode: {'DRY-RUN' if args.dry_run else 'FULL RUN'}")
    if args.limit:
        print(f"Limit: {args.limit} trades")
    print()

    # Create calculator
    calculator = JM1AtrStopCalculator(verbose=args.verbose)

    # Run calculation
    results = calculator.run_batch_calculation(
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
    print(f"  Records Created:   {results['records_created']}")
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
        description='Calculate M1 ATR Stop outcomes for journal trades using M1 ATR(14) stop and R-multiple targets (1R-5R)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python runner.py              # Full batch run
  python runner.py --dry-run    # Test without saving
  python runner.py --limit 50   # Process 50 trades
  python runner.py --schema     # Create database table
  python runner.py --status     # Show processing status

Output:
  Results are written to the j_m1_atr_stop table in Supabase.
  Each trade gets 1 row with R-level hit tracking and outcome.
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
        help='Run schema creation only (create j_m1_atr_stop table)'
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
        show_status()
        sys.exit(0)

    # Run schema creation if requested
    if args.schema:
        success = run_schema()
        sys.exit(0 if success else 1)

    # Run calculation
    try:
        success = run_calculation(args)
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
