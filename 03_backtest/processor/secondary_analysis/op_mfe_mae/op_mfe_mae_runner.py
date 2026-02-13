#!/usr/bin/env python3
"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
Options MFE/MAE Potential Calculator - CLI Runner
XIII Trading LLC
================================================================================

Command-line interface for running the Options MFE/MAE Potential calculation.

Usage:
    python op_mfe_mae_runner.py              # Full batch run
    python op_mfe_mae_runner.py --dry-run    # Calculate but don't save
    python op_mfe_mae_runner.py --limit 50   # Process max 50 trades
    python op_mfe_mae_runner.py --verbose    # Detailed logging
    python op_mfe_mae_runner.py --schema     # Run schema creation only

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

from config import DB_CONFIG, SCHEMA_DIR
from op_mfe_mae_calc import OpMFEMAECalculator
from options_bar_fetcher import OptionsBarFetcher


def setup_logging(verbose: bool = False):
    """Configure logging based on verbosity."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def run_schema():
    """Execute the schema SQL to create the op_mfe_mae_potential table."""
    import psycopg2

    schema_file = SCHEMA_DIR / "op_mfe_mae_potential.sql"

    if not schema_file.exists():
        print(f"ERROR: Schema file not found: {schema_file}")
        return False

    print("=" * 60)
    print("Options MFE/MAE Potential - Schema Creation")
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

        # Verify table exists
        with conn.cursor() as cur:
            cur.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'op_mfe_mae_potential'
                ORDER BY ordinal_position
            """)
            columns = cur.fetchall()
            print(f"\n  Table has {len(columns)} columns:")
            for col_name, col_type in columns[:5]:
                print(f"    - {col_name}: {col_type}")
            if len(columns) > 5:
                print(f"    ... and {len(columns) - 5} more")

        conn.close()
        return True

    except Exception as e:
        print(f"\nERROR: {e}")
        return False


def run_calculation(args):
    """Run the Options MFE/MAE potential calculation."""
    print()
    print("=" * 60)
    print("EPOCH TRADING SYSTEM")
    print("Options MFE/MAE Potential Calculator v1.0.0")
    print("=" * 60)
    print()
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Mode: {'DRY-RUN' if args.dry_run else 'FULL RUN'}")
    if args.limit:
        print(f"Limit: {args.limit} trades")
    print()

    # Create fetcher and calculator
    fetcher = OptionsBarFetcher()
    calculator = OpMFEMAECalculator(
        fetcher=fetcher,
        verbose=args.verbose
    )

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
    print(f"  Trades No Bars:    {results['trades_no_bars']}")
    print(f"  API Calls Made:    {results['api_calls_made']}")
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


def show_status():
    """Show current status of op_mfe_mae_potential table."""
    import psycopg2

    print("=" * 60)
    print("Options MFE/MAE Potential - Status")
    print("=" * 60)

    try:
        conn = psycopg2.connect(**DB_CONFIG)

        with conn.cursor() as cur:
            # Total records
            cur.execute("SELECT COUNT(*) FROM op_mfe_mae_potential")
            total = cur.fetchone()[0]

            # Date range
            cur.execute("SELECT MIN(date), MAX(date) FROM op_mfe_mae_potential")
            min_date, max_date = cur.fetchone()

            # By model
            cur.execute("""
                SELECT model, COUNT(*), AVG(exit_pct)
                FROM op_mfe_mae_potential
                GROUP BY model
                ORDER BY model
            """)
            model_stats = cur.fetchall()

            # Trades needing calculation
            cur.execute("""
                SELECT COUNT(*)
                FROM trades t
                INNER JOIN options_analysis o ON t.trade_id = o.trade_id
                LEFT JOIN op_mfe_mae_potential m ON t.trade_id = m.trade_id
                WHERE m.trade_id IS NULL
                  AND o.options_ticker IS NOT NULL
                  AND o.status = 'SUCCESS'
            """)
            pending = cur.fetchone()[0]

        conn.close()

        print(f"\nTotal Records: {total:,}")
        print(f"Date Range: {min_date} to {max_date}")
        print(f"Trades Pending: {pending:,}")

        if model_stats:
            print(f"\nBy Model:")
            for model, count, avg_exit in model_stats:
                avg_exit_str = f"{avg_exit:.2f}%" if avg_exit else "N/A"
                print(f"  {model or 'NULL'}: {count:,} trades, Avg Exit: {avg_exit_str}")

        return True

    except psycopg2.errors.UndefinedTable:
        print("\nTable op_mfe_mae_potential does not exist.")
        print("Run with --schema to create it.")
        return False
    except Exception as e:
        print(f"\nError: {e}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Calculate Options MFE/MAE Potential for all trades',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python op_mfe_mae_runner.py              # Full batch run
  python op_mfe_mae_runner.py --dry-run    # Test without saving
  python op_mfe_mae_runner.py --limit 50   # Process 50 trades
  python op_mfe_mae_runner.py --schema     # Create database table
  python op_mfe_mae_runner.py --status     # Show table status

Output:
  Results are written to the op_mfe_mae_potential table in Supabase.
  Each trade gets one row with MFE/MAE from entry to 15:30 ET.
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
        help='Run schema creation only (create op_mfe_mae_potential table)'
    )

    parser.add_argument(
        '--status',
        action='store_true',
        help='Show current status of op_mfe_mae_potential table'
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
