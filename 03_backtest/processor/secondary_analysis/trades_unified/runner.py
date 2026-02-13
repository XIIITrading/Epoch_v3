#!/usr/bin/env python3
"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
Trades Unified (trades_m5_r_win) - CLI Runner
XIII Trading LLC
================================================================================

Command-line interface for building the trades_m5_r_win canonical outcomes table.

Usage:
    python runner.py              # Full batch run
    python runner.py --dry-run    # Calculate but don't save
    python runner.py --limit 50   # Process max 50 trades
    python runner.py --verbose    # Detailed logging
    python runner.py --schema     # Run schema creation only
    python runner.py --info       # Show processor information

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

from config import DB_CONFIG, SCHEMA_DIR, ZONE_BUFFER_PCT, EOD_CUTOFF, TARGET_TABLE
from calculator import TradesUnifiedCalculator


def setup_logging(verbose: bool = False):
    """Configure logging based on verbosity."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def run_schema():
    """Execute the schema SQL to create the trades_m5_r_win table."""
    import psycopg2

    schema_file = SCHEMA_DIR / "trades_m5_r_win.sql"

    if not schema_file.exists():
        print(f"ERROR: Schema file not found: {schema_file}")
        return False

    print("=" * 60)
    print("Trades Unified - Schema Creation")
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
        print(f"  Table: {TARGET_TABLE}")
        print("  Indexes: created")
        print("  Views: created")
        print("  Trigger: created")

        conn.close()
        return True

    except Exception as e:
        print(f"\nERROR: {e}")
        return False


def show_info():
    """Display information about the Trades Unified processor."""
    print()
    print("=" * 60)
    print("TRADES UNIFIED PROCESSOR (trades_m5_r_win)")
    print("=" * 60)
    print()
    print("PURPOSE:")
    print("  Build the canonical trade outcomes table by merging:")
    print("  - trades table (metadata, zone boundaries, original outcomes)")
    print("  - r_win_loss table (ATR-based outcomes for ~5,415 trades)")
    print("  - Zone buffer fallback (for ~25 trades without r_win_loss)")
    print()
    print("OUTCOME PRIORITY:")
    print("  1. r_win_loss ATR outcome (outcome_method = 'atr_r_target')")
    print("  2. Zone buffer fallback  (outcome_method = 'zone_buffer_fallback')")
    print()
    print("ATR WIN/LOSS RULES (from r_win_loss):")
    print("  WIN:  R1+ target hit (price touch) BEFORE stop (close-based)")
    print("  LOSS: Stop triggered (M1 close beyond stop) BEFORE R1")
    print("  WIN:  No R1/stop by 15:30 and price > entry (EOD_WIN)")
    print("  LOSS: No R1/stop by 15:30 and price <= entry (EOD_LOSS)")
    print()
    print("ZONE BUFFER FALLBACK RULES:")
    print(f"  Stop: zone_low - (zone_distance * {ZONE_BUFFER_PCT}) for LONG")
    print(f"  Stop: zone_high + (zone_distance * {ZONE_BUFFER_PCT}) for SHORT")
    print("  1R = abs(entry_price - stop_price)")
    print("  R1 target = entry +/- 1R")
    print("  Stop detection: CLOSE-based (matching ATR methodology)")
    print("  Exit reasons: ZB_R_TARGET, ZB_STOP, ZB_EOD_WIN, ZB_EOD_LOSS")
    print()
    print("CONVENIENCE FIELDS:")
    print("  is_winner:    outcome = 'WIN' (canonical boolean)")
    print("  pnl_r:        Continuous R-multiple")
    print("  reached_2r:   r2_hit (boolean)")
    print("  reached_3r:   r3_hit (boolean)")
    print("  minutes_to_r1: r1_bars_from_entry (M1 = 1 minute)")
    print()
    print("DATA SOURCES:")
    print("  - trades (trade metadata)")
    print("  - r_win_loss (ATR-based outcomes)")
    print("  - m1_bars (for zone_buffer fallback simulation)")
    print()
    print("DOWNSTREAM CONSUMERS:")
    print("  - 02_dow_ai: TradeLoaderV3, DualPassAnalyzer")
    print("  - 05_system_analysis: Trade stats, Indicator analysis, Monte AI")
    print("  - 06_training: Trade model, StatsPanel, FlashcardUI")
    print()
    print("=" * 60)


def run_calculation(args):
    """Run the Trades Unified calculation."""
    print()
    print("=" * 60)
    print("EPOCH TRADING SYSTEM")
    print("Trades Unified Calculator v1.0.0")
    print("=" * 60)
    print()
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Mode: {'DRY-RUN' if args.dry_run else 'FULL RUN'}")
    if args.limit:
        print(f"Limit: {args.limit} trades")
    print()

    # Create calculator
    calculator = TradesUnifiedCalculator(verbose=args.verbose)

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
    print(f"  ATR Records:       {results['atr_records']}")
    print(f"  Fallback Records:  {results['fallback_records']}")
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
        description='Build trades_m5_r_win canonical outcomes table',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python runner.py              # Full batch run
  python runner.py --dry-run    # Test without saving
  python runner.py --limit 50   # Process 50 trades
  python runner.py --schema     # Create database table
  python runner.py --info       # Show processor information

Output:
  Results are written to the trades_m5_r_win table in Supabase.
  Each trade gets 1 row with canonical outcome and convenience fields.
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
        help='Run schema creation only (create trades_m5_r_win table)'
    )

    parser.add_argument(
        '--info',
        action='store_true',
        help='Display information about the Trades Unified processor'
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
