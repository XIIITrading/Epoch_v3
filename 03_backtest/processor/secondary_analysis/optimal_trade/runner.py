"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
Optimal Trade Calculator - Runner
XIII Trading LLC
================================================================================

Command-line runner for the Optimal Trade Calculator.

Usage:
    python runner.py                    # Incremental run (new trades only)
    python runner.py --rebuild          # Full rebuild (truncate + all trades)
    python runner.py --limit 10         # Process only 10 trades
    python runner.py --dry-run          # Calculate without writing to DB

Version: 2.1.0
================================================================================
"""

import sys
import argparse
from datetime import datetime

from calculator import OptimalTradeCalculator


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Optimal Trade Calculator (Points-Based) v2.1.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python runner.py                      Incremental run (new trades only)
    python runner.py --rebuild            Full rebuild (truncate + all trades)
    python runner.py --limit 10           Process only 10 trades
    python runner.py --dry-run            Test without writing to database
    python runner.py --limit 5 --dry-run  Test 5 trades without writing
    python runner.py --quiet              Minimal output
        """
    )

    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Maximum number of trades to process (default: all)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Calculate but do not write to database'
    )

    parser.add_argument(
        '--rebuild',
        action='store_true',
        help='Full rebuild: truncate table and reprocess all trades'
    )

    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Minimal output (no per-trade logging)'
    )

    args = parser.parse_args()

    print()
    print("=" * 70)
    print("EPOCH TRADING SYSTEM - OPTIMAL TRADE CALCULATOR")
    print("Points-Based Calculation (v2.1.0)")
    print("=" * 70)
    print()
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Show configuration
    print("Configuration:")
    print(f"  Mode: {'REBUILD (full)' if args.rebuild else 'INCREMENTAL'}")
    print(f"  Limit: {args.limit if args.limit else 'All trades'}")
    print(f"  Dry Run: {args.dry_run}")
    print(f"  Verbose: {not args.quiet}")
    print()

    # Run calculation
    calculator = OptimalTradeCalculator(verbose=not args.quiet)

    try:
        result = calculator.run_calculation(
            limit=args.limit,
            dry_run=args.dry_run,
            rebuild=args.rebuild
        )

        # Exit with appropriate code
        if result['errors']:
            print(f"\nCompleted with {len(result['errors'])} error(s)")
            sys.exit(1)
        else:
            print("\nCompleted successfully!")
            sys.exit(0)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(130)

    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
