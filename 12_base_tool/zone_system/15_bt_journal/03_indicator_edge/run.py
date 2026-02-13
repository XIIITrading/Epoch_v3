"""
Epoch Backtest Journal - Indicator Edge Module Runner
Pulls trade data from Supabase, calculates indicator edge statistics
by model type and direction, and writes results to bt_journal.xlsx.

Usage:
    python run.py           # Calculate and write indicator edge stats
    python run.py --quiet   # Print without header formatting
"""

import argparse
import sys
from pathlib import Path

# Add current directory and parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from calculator import IndicatorEdgeCalculator


def run(verbose: bool = True) -> dict:
    """
    Run indicator edge statistics calculation.

    1. Connects to Supabase database
    2. Pulls all trades with entry event data
    3. Segments by model (EPCH1-4) and direction (LONG/SHORT)
    4. Calculates win rates for each indicator state per segment
    5. Identifies top indicators by edge per segment
    6. Writes results to Excel
    7. Prints results to console

    Args:
        verbose: Print formatted output with headers.

    Returns:
        Dictionary containing indicator edge statistics summary.
    """
    if verbose:
        print("[1/3] Connecting to database...")

    calculator = IndicatorEdgeCalculator()

    if verbose:
        print("[2/3] Calculating indicator edge statistics...")

    data = calculator.calculate()

    if verbose:
        print("[3/3] Writing to Excel...")

    calculator.write_to_excel(data)
    calculator.print_results(data, verbose=verbose)

    # Return summary as dictionary
    summary = {}
    for (model, direction), segment in data.segments.items():
        key = f"{model}_{direction}"
        summary[key] = {
            "trades": segment.trades,
            "wins": segment.wins,
            "win_rate": segment.win_rate,
            "model_type": segment.model_type,
            "top_indicators": [
                {
                    "indicator": e.indicator,
                    "best_state": e.best_state,
                    "edge": e.edge
                }
                for e in data.segment_edges.get((model, direction), [])[:3]
            ]
        }
    
    return summary


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Epoch Indicator Edge Statistics Calculator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run.py           # Calculate and write indicator edge stats
    python run.py --quiet   # Print stats without headers

Output Location:
    bt_journal.xlsx -> analysis sheet -> cells H9:AF40

Analysis Structure:
    - 8 segments: EPCH1-4 × LONG/SHORT
    - Continuation models (EPCH1, EPCH3): Expect momentum alignment
    - Reversal models (EPCH2, EPCH4): Expect exhaustion signals
    - Edge = best_state_win_rate - worst_state_win_rate
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