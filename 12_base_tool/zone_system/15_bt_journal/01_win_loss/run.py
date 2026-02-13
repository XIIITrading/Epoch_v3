"""
Epoch Backtest Journal - Win/Loss Module Runner
Pulls trade data from Supabase, calculates win/loss statistics,
and writes results to bt_journal.xlsx.

Usage:
    python run.py           # Calculate and write win/loss stats
    python run.py --quiet   # Print without header formatting
"""

import argparse
import sys
from pathlib import Path

# Add current directory and parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from calculator import WinLossCalculator


def run(verbose: bool = True) -> dict:
    """
    Run win/loss statistics calculation.

    1. Connects to Supabase database
    2. Pulls all trades
    3. Calculates win/loss statistics
    4. Writes results to Excel
    5. Prints results to console

    Args:
        verbose: Print formatted output with headers.

    Returns:
        Dictionary containing win/loss statistics.
    """
    if verbose:
        print("[1/3] Connecting to database...")

    calculator = WinLossCalculator()

    if verbose:
        print("[2/3] Calculating win/loss statistics...")

    data = calculator.calculate()

    if verbose:
        print("[3/3] Writing to Excel...")

    calculator.write_to_excel(data)
    calculator.print_results(data, verbose=verbose)

    return {
        "total_trades": data.total_trades,
        "total_wins": data.total_wins,
        "total_losses": data.total_losses,
        "percent_wins": data.percent_wins,
        "percent_losses": data.percent_losses
    }


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Epoch Win/Loss Statistics Calculator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run.py           # Calculate and write win/loss stats
    python run.py --quiet   # Print stats without headers
        """
    )

    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress header formatting"
    )

    args = parser.parse_args()

    try:
        run(verbose=not args.quiet)
        sys.exit(0)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
