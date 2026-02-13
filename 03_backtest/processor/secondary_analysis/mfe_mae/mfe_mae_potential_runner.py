#!/usr/bin/env python3
"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
MFE/MAE Potential Calculator - CLI Runner
XIII Trading LLC
================================================================================

Command-line interface for running the MFE/MAE Potential calculation.

Usage:
    python mfe_mae_potential_runner.py              # Full batch run
    python mfe_mae_potential_runner.py --dry-run    # Calculate but don't save
    python mfe_mae_potential_runner.py --limit 50   # Process max 50 trades
    python mfe_mae_potential_runner.py --verbose    # Detailed logging
    python mfe_mae_potential_runner.py --schema     # Run schema creation only

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
from mfe_mae_potential_calc import MFEMAEPotentialCalculator
from m1_fetcher import M1Fetcher


def setup_logging(verbose: bool = False):
    """Configure logging based on verbosity."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def run_schema():
    """Execute the schema SQL to create the mfe_mae_potential table."""
    import psycopg2

    schema_file = SCHEMA_DIR / "mfe_mae_potential.sql"

    if not schema_file.exists():
        print(f"ERROR: Schema file not found: {schema_file}")
        return False

    print("=" * 60)
    print("MFE/MAE Potential - Schema Creation")
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


def run_calculation(args):
    """Run the MFE/MAE potential calculation."""
    print()
    print("=" * 60)
    print("EPOCH TRADING SYSTEM")
    print("MFE/MAE Potential Calculator v1.0.0")
    print("=" * 60)
    print()
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Mode: {'DRY-RUN' if args.dry_run else 'FULL RUN'}")
    if args.limit:
        print(f"Limit: {args.limit} trades")
    print()

    # Create fetcher and calculator
    fetcher = M1Fetcher()
    calculator = MFEMAEPotentialCalculator(
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


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Calculate MFE/MAE Potential for all trades',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python mfe_mae_potential_runner.py              # Full batch run
  python mfe_mae_potential_runner.py --dry-run    # Test without saving
  python mfe_mae_potential_runner.py --limit 50   # Process 50 trades
  python mfe_mae_potential_runner.py --schema     # Create database table

Output:
  Results are written to the mfe_mae_potential table in Supabase.
  Each trade gets one row with potential MFE/MAE from entry to 15:30 ET.
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
        help='Run schema creation only (create mfe_mae_potential table)'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)

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
