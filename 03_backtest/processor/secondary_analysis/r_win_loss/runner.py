#!/usr/bin/env python3
"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
R Win/Loss Calculator - CLI Runner
XIII Trading LLC
================================================================================

Command-line interface for running the R Win/Loss calculation.

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

from config import DB_CONFIG, SCHEMA_DIR, R_LEVELS, ATR_PERIOD, ATR_MULTIPLIER
from calculator import RWinLossCalculator


def setup_logging(verbose: bool = False):
    """Configure logging based on verbosity."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def run_schema():
    """Execute the schema SQL to create the r_win_loss table."""
    import psycopg2

    schema_file = SCHEMA_DIR / "r_win_loss.sql"

    if not schema_file.exists():
        print(f"ERROR: Schema file not found: {schema_file}")
        return False

    print("=" * 60)
    print("R Win/Loss - Schema Creation")
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


def show_info():
    """Display information about the R Win/Loss processor."""
    print()
    print("=" * 60)
    print("R WIN/LOSS PROCESSOR")
    print("=" * 60)
    print()
    print("PURPOSE:")
    print("  Evaluate trades using M5 ATR-based stop and R-multiple targets")
    print("  to determine win/loss outcomes at each R-level (1R-5R).")
    print()
    print("ATR CONFIGURATION:")
    print(f"  ATR Period:     {ATR_PERIOD}")
    print(f"  ATR Multiplier: {ATR_MULTIPLIER}")
    print(f"  Stop = entry -/+ (ATR * {ATR_MULTIPLIER})")
    print()
    print("R-LEVEL TARGETS:")
    for r in R_LEVELS:
        print(f"  R{r}: entry +/- ({r} * stop_distance)")
    print()
    print("WIN/LOSS RULES:")
    print("  WIN:  R1+ target hit (price touch) BEFORE stop (close-based)")
    print("  LOSS: Stop triggered (M1 close beyond stop) BEFORE R1")
    print("  WIN:  No R1/stop by 15:30 and price > entry (EOD_WIN)")
    print("  LOSS: No R1/stop by 15:30 and price <= entry (EOD_LOSS)")
    print()
    print("SAME-CANDLE CONFLICT:")
    print("  If M1 bar shows R-level hit AND close beyond stop => LOSS")
    print()
    print("DATA SOURCES:")
    print("  - trades (trade metadata)")
    print("  - m1_bars (M1 candle data for simulation)")
    print("  - m5_trade_bars (M5 bars for ATR calculation)")
    print("  - m5_indicator_bars (M5 bars for ATR, pre-entry)")
    print()
    print("=" * 60)


def run_calculation(args):
    """Run the R Win/Loss calculation."""
    print()
    print("=" * 60)
    print("EPOCH TRADING SYSTEM")
    print("R Win/Loss Calculator v1.0.0")
    print("=" * 60)
    print()
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Mode: {'DRY-RUN' if args.dry_run else 'FULL RUN'}")
    if args.limit:
        print(f"Limit: {args.limit} trades")
    print()

    # Create calculator
    calculator = RWinLossCalculator(verbose=args.verbose)

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
        description='Calculate R Win/Loss outcomes using M5 ATR stop and R-multiple targets',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python runner.py              # Full batch run
  python runner.py --dry-run    # Test without saving
  python runner.py --limit 50   # Process 50 trades
  python runner.py --schema     # Create database table
  python runner.py --info       # Show processor information

Output:
  Results are written to the r_win_loss table in Supabase.
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
        help='Run schema creation only (create r_win_loss table)'
    )

    parser.add_argument(
        '--info',
        action='store_true',
        help='Display information about the R Win/Loss processor'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)

    # Show info if requested
    if args.info:
        show_info()
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
