"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 04: INDICATOR ANALYSIS v2.0
Scorecard Analyzer CLI Runner
XIII Trading LLC
================================================================================

CLI entry point for generating trade type scorecards.
Produces Claude Code-ready markdown files with tier rankings
and binary signals for each indicator per trade type.

Usage:
    python 04_indicators/runner.py                            # Full analysis
    python 04_indicators/runner.py --date-from 2026-01-01
    python 04_indicators/runner.py --date-from 2026-01-01 --date-to 2026-02-15
    python 04_indicators/runner.py --compare results/20260215/scorecards
    python 04_indicators/runner.py --info
    python 04_indicators/runner.py -v                         # Verbose output
"""
import sys
import argparse
from datetime import date, datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup — ensure module imports work when running as standalone script
# ---------------------------------------------------------------------------
MODULE_DIR = Path(__file__).parent
ROOT_DIR = MODULE_DIR.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(MODULE_DIR))

from config import (
    DB_CONFIG, MODULE_ROOT, TRADE_TYPES, TIER_THRESHOLDS,
    ALL_DEEP_DIVE_INDICATORS, SCORECARD_TOP_N,
)
from data.provider import DataProvider
from analysis.scorecard_analyzer import ScorecardAnalyzer
from analysis.scorecard_exporter import ScorecardExporter


# =============================================================================
# MAIN FUNCTIONS
# =============================================================================


def run_analysis(
    date_from: date = None,
    date_to: date = None,
    compare_dir: str = None,
    verbose: bool = False,
):
    """Run full scorecard analysis and export results."""
    print("=" * 70)
    print("EPOCH INDICATOR SCORECARD ANALYZER")
    print("=" * 70)
    print()

    # Connect to database
    provider = DataProvider()
    if not provider.connect():
        print("ERROR: Failed to connect to Supabase.")
        sys.exit(1)

    try:
        # Show data availability
        date_range = provider.get_date_range()
        print(f"Database: {date_range['total']:,} trades available")
        print(f"Date range: {date_range['min_date']} to {date_range['max_date']}")

        if date_from:
            print(f"Filter from: {date_from}")
        if date_to:
            print(f"Filter to:   {date_to}")
        print()

        # Resolve comparison directory
        prior_dir = None
        if compare_dir:
            prior_dir = Path(compare_dir)
            if not prior_dir.is_absolute():
                prior_dir = MODULE_ROOT / prior_dir
            if prior_dir.exists():
                print(f"Comparing against: {prior_dir}")
            else:
                print(f"WARNING: Prior results not found at {prior_dir}")
                prior_dir = None
            print()

        # Run analysis
        analyzer = ScorecardAnalyzer(provider, verbose=verbose)
        result = analyzer.analyze(
            date_from=date_from,
            date_to=date_to,
            prior_results_dir=prior_dir,
        )

        if result.total_trades == 0:
            print("No trades found. Nothing to export.")
            return

        # Print summary
        print()
        print("-" * 70)
        print("ANALYSIS COMPLETE")
        print("-" * 70)
        print(f"Total trades analyzed: {result.total_trades:,}")
        print()

        for tt_key, tt_result in result.trade_type_results.items():
            top_label = "none"
            if tt_result.top_scores:
                top = tt_result.top_scores[0]
                top_label = f"{top.indicator_label} ({top.tier}, {top.effect_size:.1f}pp)"

            print(
                f"  {tt_result.label:25s} | "
                f"{tt_result.total_trades:5d} trades | "
                f"{tt_result.win_rate:5.1f}% WR | "
                f"Top: {top_label}"
            )

        if result.degradation_flags:
            print()
            print(f"DEGRADATION: {len(result.degradation_flags)} flag(s)")
            for flag in result.degradation_flags:
                print(f"  [DEGRADED] {flag.message}")

        # Export
        print()
        print("Exporting scorecards...")
        exporter = ScorecardExporter()
        export_dir = exporter.export(result)
        print(f"Exported to: {export_dir}")
        print()

        # List exported files
        for f in sorted(export_dir.iterdir()):
            size = f.stat().st_size
            print(f"  {f.name:30s} ({size:,} bytes)")

        print()
        print("Done. Read CLAUDE.md for instructions on using these scorecards.")

    finally:
        provider.close()


def show_info():
    """Display module info and data availability."""
    print("=" * 70)
    print("EPOCH INDICATOR SCORECARD ANALYZER - INFO")
    print("=" * 70)
    print()
    print(f"Module:     04_indicators")
    print(f"Root:       {MODULE_ROOT}")
    print(f"Database:   {DB_CONFIG['host']}")
    print()

    print("Trade Types:")
    for key, config in TRADE_TYPES.items():
        print(f"  {key:25s} -> {config['direction']} + {config['models']}")
    print()

    print(f"Indicators ({len(ALL_DEEP_DIVE_INDICATORS)}):")
    for col, label, ind_type in ALL_DEEP_DIVE_INDICATORS:
        print(f"  {col:25s} ({ind_type:12s}) -> {label}")
    print()

    print(f"Tier Thresholds:")
    for tier, thresh in TIER_THRESHOLDS.items():
        print(
            f"  {tier}: effect >= {thresh['min_effect_size']:.0f}pp, "
            f"p < {thresh['max_p_value']}"
        )
    print()

    print(f"Scorecard limit: {SCORECARD_TOP_N} indicators per trade type")
    print()

    # Check database
    print("Database check...")
    provider = DataProvider()
    if provider.connect():
        date_range = provider.get_date_range()
        print(f"  Connected: {date_range['total']:,} trades")
        print(f"  Date range: {date_range['min_date']} to {date_range['max_date']}")
        provider.close()
    else:
        print("  ERROR: Could not connect to database")

    # Check existing results
    results_dir = MODULE_ROOT / "results"
    scorecard_dirs = sorted(
        [d for d in results_dir.iterdir() if d.is_dir() and (d / "scorecards").exists()]
    ) if results_dir.exists() else []

    if scorecard_dirs:
        print()
        print(f"Existing scorecard runs ({len(scorecard_dirs)}):")
        for d in scorecard_dirs[-5:]:  # Show last 5
            sc_dir = d / "scorecards"
            prior_json = sc_dir / "_prior.json"
            status = "with _prior.json" if prior_json.exists() else "no _prior.json"
            print(f"  {d.name}/scorecards/ ({status})")


# =============================================================================
# CLI ENTRY POINT
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Generate indicator scorecards for trade type analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python runner.py                            Full analysis with all data
  python runner.py --date-from 2026-02-01     Analysis from Feb 1st onward
  python runner.py --compare results/20260215/scorecards
                                              Compare against prior run
  python runner.py --info                     Show module configuration
        """,
    )
    parser.add_argument(
        "--date-from", type=str, metavar="YYYY-MM-DD",
        help="Start date for trade data",
    )
    parser.add_argument(
        "--date-to", type=str, metavar="YYYY-MM-DD",
        help="End date for trade data",
    )
    parser.add_argument(
        "--compare", type=str, metavar="DIR",
        help="Path to prior scorecard folder for degradation comparison",
    )
    parser.add_argument(
        "--info", action="store_true",
        help="Show module info and configuration",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Enable verbose output during analysis",
    )

    args = parser.parse_args()

    if args.info:
        show_info()
        return

    # Parse dates
    date_from = None
    date_to = None
    if args.date_from:
        try:
            date_from = date.fromisoformat(args.date_from)
        except ValueError:
            print(f"ERROR: Invalid date format: {args.date_from} (use YYYY-MM-DD)")
            sys.exit(1)
    if args.date_to:
        try:
            date_to = date.fromisoformat(args.date_to)
        except ValueError:
            print(f"ERROR: Invalid date format: {args.date_to} (use YYYY-MM-DD)")
            sys.exit(1)

    run_analysis(
        date_from=date_from,
        date_to=date_to,
        compare_dir=args.compare,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    main()
