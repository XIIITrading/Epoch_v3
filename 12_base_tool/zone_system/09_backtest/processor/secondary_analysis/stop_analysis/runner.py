#!/usr/bin/env python3
"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
Stop Analysis Calculator - CLI Runner
XIII Trading LLC
================================================================================

Command-line interface for running the Stop Analysis calculation.

Usage:
    python runner.py              # Full batch run
    python runner.py --dry-run    # Calculate but don't save
    python runner.py --limit 50   # Process max 50 trades
    python runner.py --verbose    # Detailed logging
    python runner.py --schema     # Run schema creation only

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

from config import DB_CONFIG, SCHEMA_DIR, STOP_TYPES, STOP_TYPE_DISPLAY_NAMES
from stop_analysis_calc import StopAnalysisCalculator


def setup_logging(verbose: bool = False):
    """Configure logging based on verbosity."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def run_schema():
    """Execute the schema SQL to create the stop_analysis table."""
    import psycopg2

    schema_file = SCHEMA_DIR / "stop_analysis.sql"

    if not schema_file.exists():
        print(f"ERROR: Schema file not found: {schema_file}")
        return False

    print("=" * 60)
    print("Stop Analysis - Schema Creation")
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


def show_stop_types():
    """Display information about the 6 stop types."""
    print()
    print("=" * 60)
    print("STOP TYPES ANALYZED")
    print("=" * 60)
    print()

    descriptions = {
        'zone_buffer': 'Zone boundary + 5% buffer. Stop placed beyond the opposite side of the entry zone with a buffer of 5% of the zone distance.',
        'prior_m1': 'Prior M1 bar high/low. Stop at the high/low of the 1-minute candle immediately before entry. Tightest structural stop.',
        'prior_m5': 'Prior M5 bar high/low. Stop at the high/low of the 5-minute bar just before entry (bars_from_entry = -1).',
        'm5_atr': 'M5 ATR-based stop (1.1x multiplier). Volatility-normalized using 14-period ATR. Close-based trigger.',
        'm15_atr': 'M15 ATR-based stop (1.1x multiplier). Wider volatility stop using M15 timeframe ATR. Close-based trigger.',
        'fractal': 'M5 fractal high/low. Stop beyond the most recent confirmed swing high/low (Williams fractal with length=2).'
    }

    trigger_types = {
        'zone_buffer': 'Price-based (triggers on touch)',
        'prior_m1': 'Price-based (triggers on touch)',
        'prior_m5': 'Price-based (triggers on touch)',
        'm5_atr': 'Close-based (triggers on bar close)',
        'm15_atr': 'Close-based (triggers on M15 close)',
        'fractal': 'Price-based (triggers on touch)'
    }

    for i, stop_type in enumerate(STOP_TYPES, 1):
        print(f"{i}. {STOP_TYPE_DISPLAY_NAMES[stop_type]}")
        print(f"   Key: {stop_type}")
        print(f"   Trigger: {trigger_types[stop_type]}")
        print(f"   {descriptions[stop_type]}")
        print()

    print("=" * 60)


def run_calculation(args):
    """Run the stop analysis calculation."""
    print()
    print("=" * 60)
    print("EPOCH TRADING SYSTEM")
    print("Stop Analysis Calculator v1.0.0")
    print("=" * 60)
    print()
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Mode: {'DRY-RUN' if args.dry_run else 'FULL RUN'}")
    if args.limit:
        print(f"Limit: {args.limit} trades")
    print()

    # Create calculator
    calculator = StopAnalysisCalculator(verbose=args.verbose)

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
        description='Calculate Stop Analysis for all trades (6 stop types)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python runner.py              # Full batch run
  python runner.py --dry-run    # Test without saving
  python runner.py --limit 50   # Process 50 trades
  python runner.py --schema     # Create database table
  python runner.py --info       # Show stop type information

Output:
  Results are written to the stop_analysis table in Supabase.
  Each trade gets 6 rows (one per stop type) with calculated prices
  and simulated outcomes.
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
        help='Run schema creation only (create stop_analysis table)'
    )

    parser.add_argument(
        '--info',
        action='store_true',
        help='Display information about the 6 stop types'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)

    # Show stop type info if requested
    if args.info:
        show_stop_types()
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
