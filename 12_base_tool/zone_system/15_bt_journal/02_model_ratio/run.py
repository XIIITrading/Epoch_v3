"""
Epoch Backtest Journal - Model Ratio Module Runner
Pulls trade data from Supabase, calculates win/loss statistics by model,
and writes results to bt_journal.xlsx.

Usage:
    python run.py           # Calculate and write model ratio stats
    python run.py --quiet   # Print without header formatting
"""

import argparse
import sys
from pathlib import Path

# Add current directory and parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from calculator import ModelRatioCalculator


def run(verbose: bool = True) -> dict:
    """
    Run model ratio statistics calculation.

    1. Connects to Supabase database
    2. Pulls all trades
    3. Calculates win/loss statistics by model (EPCH1-4)
    4. Writes results to Excel
    5. Prints results to console

    Args:
        verbose: Print formatted output with headers.

    Returns:
        Dictionary containing model ratio statistics.
    """
    if verbose:
        print("[1/3] Connecting to database...")

    calculator = ModelRatioCalculator()

    if verbose:
        print("[2/3] Calculating model ratio statistics...")

    data = calculator.calculate()

    if verbose:
        print("[3/3] Writing to Excel...")

    calculator.write_to_excel(data)
    calculator.print_results(data, verbose=verbose)

    # Return results as dictionary
    return {
        model_stats.model: {
            "count": model_stats.count,
            "win_count": model_stats.win_count,
            "loss_count": model_stats.loss_count,
            "win_rate": model_stats.win_rate
        }
        for model_stats in data.get_all()
    }


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Epoch Model Ratio Statistics Calculator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run.py           # Calculate and write model ratio stats
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
