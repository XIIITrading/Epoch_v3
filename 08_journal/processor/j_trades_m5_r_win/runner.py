#!/usr/bin/env python3
"""
================================================================================
EPOCH TRADING SYSTEM - JOURNAL PROCESSOR 5
j_trades_m5_r_win - CLI Runner
XIII Trading LLC
================================================================================

CLI entry point for the journal trades M5 R-Win consolidation processor.
Joins journal_trades + j_m5_atr_stop + j_m1_bars into j_trades_m5_r_win.

Usage:
    python runner.py                    # Full consolidation run
    python runner.py --dry-run          # Preview without saving
    python runner.py --limit 50         # Process 50 trades
    python runner.py --schema           # Create database table
    python runner.py --status           # Show table status
    python runner.py --verbose          # Enable verbose output

Version: 1.0.0
================================================================================
"""

import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime

import psycopg2

# Self-contained imports from shared db_config
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from db_config import (
    DB_CONFIG, SCHEMA_DIR, SOURCE_TABLE,
    J_M5_ATR_STOP_TABLE, J_TRADES_M5_R_WIN_TABLE
)

from calculator import JTradesM5RWinCalculator


# =============================================================================
# SCHEMA CREATION
# =============================================================================

def run_schema():
    """Create the j_trades_m5_r_win table from SQL schema file."""
    schema_file = SCHEMA_DIR / "j_trades_m5_r_win.sql"

    if not schema_file.exists():
        print(f"  ERROR: Schema file not found: {schema_file}")
        return False

    print(f"\n{'='*60}")
    print(f"SCHEMA CREATION: {J_TRADES_M5_R_WIN_TABLE}")
    print(f"{'='*60}")
    print(f"  Schema file: {schema_file}")

    try:
        sql = schema_file.read_text()
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True

        with conn.cursor() as cur:
            cur.execute(sql)

        conn.close()

        print(f"  Schema created successfully")
        return True

    except Exception as e:
        print(f"\n  ERROR: {e}")
        return False


# =============================================================================
# STATUS DISPLAY
# =============================================================================

def show_status():
    """Display current table status with win/loss breakdown and pending count."""
    print(f"\n{'='*60}")
    print(f"j_trades_m5_r_win - Status")
    print(f"{'='*60}")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        calculator = JTradesM5RWinCalculator(verbose=False)
        status = calculator.get_status(conn)
        conn.close()

        total = status['total_trades']

        if isinstance(total, str):
            # Table not found
            print(f"\n  {total}")
            print(f"  Run with --schema to create the table.")
            return True

        win = status['win_count']
        loss = status['loss_count']
        win_rate = (win / total * 100) if total > 0 else 0.0

        print(f"\n  Total Trades:          {total:,}")
        print(f"  Wins:                  {win:,}")
        print(f"  Losses:                {loss:,}")
        print(f"  Win Rate:              {win_rate:.1f}%")
        print(f"  Unique Tickers:        {status['unique_tickers']:,}")

        if status['min_date'] and status['max_date']:
            print(f"  Date Range:            {status['min_date']} to {status['max_date']}")
        else:
            print(f"  Date Range:            N/A")

        print(f"\n  Source Tables:")
        print(f"    journal_trades:      {status['journal_trades_count']:,}")
        print(f"    j_m5_atr_stop:       {status['m5_atr_stop_count']:,}")
        print(f"  Pending:               {status['pending_count']:,}")

        # Exit reason breakdown
        if status.get('exit_reasons'):
            print(f"\n  Exit Reasons:")
            for reason, count in status['exit_reasons'].items():
                pct = count / total * 100 if total > 0 else 0
                print(f"    {reason:<15}  {count:>5}  ({pct:.1f}%)")

        # Account breakdown
        if status.get('accounts'):
            print(f"\n  Accounts:")
            for acct, count in status['accounts'].items():
                print(f"    {acct:<15}  {count:>5}")

        return True

    except Exception as e:
        print(f"\n  ERROR: {e}")
        return False


# =============================================================================
# MAIN CALCULATION
# =============================================================================

def run_calculation(args):
    """Run the consolidation calculation."""
    print()
    print("=" * 60)
    print("EPOCH JOURNAL SYSTEM")
    print("j_trades_m5_r_win Consolidator v1.0.0")
    print("=" * 60)
    print(f"  Mode:   {'DRY RUN' if args.dry_run else 'LIVE'}")
    if args.limit:
        print(f"  Limit:  {args.limit} trades")
    print(f"  Target: {J_TRADES_M5_R_WIN_TABLE}")
    print(f"  Time:   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    calculator = JTradesM5RWinCalculator(verbose=args.verbose)

    stats = calculator.run_batch_calculation(
        limit=args.limit,
        dry_run=args.dry_run
    )

    print()
    print("=" * 60)
    print("EXECUTION SUMMARY")
    print("=" * 60)
    print(f"  Source Trades:        {stats['total_source']}")
    print(f"  Processed:           {stats['processed']}")
    print(f"  Inserted:            {stats['inserted']}")
    print(f"  WIN:                 {stats['win_count']}")
    print(f"  LOSS:                {stats['loss_count']}")
    print(f"  Errors:              {stats['errors']}")
    print(f"  Execution Time:      {stats.get('execution_time_seconds', 0):.1f}s")

    if stats['error_details']:
        print("\nERRORS:")
        for err in stats['error_details'][:10]:
            print(f"  ! {err}")
        if len(stats['error_details']) > 10:
            print(f"  ... and {len(stats['error_details']) - 10} more")

    return stats['errors'] == 0


# =============================================================================
# LOGGING SETUP
# =============================================================================

def setup_logging(verbose: bool = False):
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
        datefmt='%H:%M:%S'
    )


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Consolidate journal_trades + j_m5_atr_stop into j_trades_m5_r_win',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python runner.py                # Full consolidation run
  python runner.py --dry-run      # Preview without saving
  python runner.py --limit 50     # Process 50 trades
  python runner.py --schema       # Create database table
  python runner.py --status       # Show table status

Output:
  Results are written to the j_trades_m5_r_win table in Supabase.
  Each trade gets 1 row with all fields needed for trade analysis.
        """
    )

    parser.add_argument('--dry-run', action='store_true',
                        help='Consolidate without saving to database')
    parser.add_argument('--limit', type=int, metavar='N',
                        help='Maximum number of trades to process')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose output')
    parser.add_argument('--schema', action='store_true',
                        help='Create j_trades_m5_r_win table from schema SQL')
    parser.add_argument('--status', action='store_true',
                        help='Show current table status')

    args = parser.parse_args()

    setup_logging(args.verbose)

    # Handle --schema flag
    if args.schema:
        success = run_schema()
        sys.exit(0 if success else 1)

    # Handle --status flag
    if args.status:
        success = show_status()
        sys.exit(0 if success else 1)

    # Run consolidation
    try:
        success = run_calculation(args)
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(130)

    except Exception as e:
        print(f"\nFATAL: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
