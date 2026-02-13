"""
Epoch Backtest Journal - Main Runner
Run this file to execute analysis modules with default settings.

Usage:
    python run_analysis.py                    # Run all modules with all data
    python run_analysis.py prim_v_sec         # Run specific module
    python run_analysis.py prim_v_sec --day   # Run with date filter
    python run_analysis.py --help             # Show help

Available Modules:
    prim_v_sec    Primary vs Secondary Zone Analysis
    (more modules will be added here)

Outputs:
    - PDF report with one page per module
    - Excel workbook with one worksheet per module (raw data + results)
"""

import argparse
from datetime import date, datetime, timedelta
from pathlib import Path
import sys

# Ensure module directory is in path
MODULE_DIR = Path(__file__).parent
sys.path.insert(0, str(MODULE_DIR))

from matplotlib.backends.backend_pdf import PdfPages


def parse_date(date_str: str) -> date:
    """Parse date string in various formats."""
    formats = ["%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%Y%m%d"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Could not parse date: {date_str}")


def run_prim_v_sec(
    start_date: date = None,
    end_date: date = None,
    verbose: bool = True,
    pdf: PdfPages = None,
    excel_exporter = None
):
    """Run Primary vs Secondary analysis."""
    from prim_v_sec.run import run
    return run(
        start_date=start_date,
        end_date=end_date,
        verbose=verbose,
        pdf=pdf,
        excel_exporter=excel_exporter
    )


def run_entry_impact(
    start_date: date = None,
    end_date: date = None,
    verbose: bool = True,
    pdf: PdfPages = None,
    excel_exporter = None
):
    """Run Entry Factor Impact analysis."""
    from entry_impact.run import run
    return run(
        start_date=start_date,
        end_date=end_date,
        verbose=verbose,
        pdf=pdf,
        excel_exporter=excel_exporter
    )


def run_confluence(
    start_date: date = None,
    end_date: date = None,
    verbose: bool = True,
    pdf: PdfPages = None,
    excel_exporter = None
):
    """Run Confluence analysis."""
    from confluence_analysis.run import run
    return run(
        start_date=start_date,
        end_date=end_date,
        verbose=verbose,
        pdf=pdf,
        excel_exporter=excel_exporter
    )


# Module registry - add new modules here
MODULES = {
    "prim_v_sec": {
        "name": "Primary vs Secondary Zone Analysis",
        "run": run_prim_v_sec,
        "description": "Compares EPCH1/2 (Primary) vs EPCH3/4 (Secondary) zone performance"
    },
    "entry_impact": {
        "name": "Entry Factor Impact Analysis",
        "run": run_entry_impact,
        "description": "Analyzes which entry criteria most strongly predict trade success"
    },
    "confluence": {
        "name": "Confluence Analysis",
        "run": run_confluence,
        "description": "Direction-relative factor alignment impact on win rate"
    },
}


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Epoch Backtest Journal - Trade Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_analysis.py                         # Run all modules, all data
  python run_analysis.py prim_v_sec              # Run specific module
  python run_analysis.py prim_v_sec --day        # Most recent day
  python run_analysis.py --week                  # Last 7 days
  python run_analysis.py --month                 # Last 30 days
  python run_analysis.py --start 2025-12-01 --end 2025-12-12

Available Modules:
""" + "\n".join(f"  {k:15} {v['description']}" for k, v in MODULES.items())
    )

    # Module selection
    parser.add_argument(
        "module",
        nargs="?",
        choices=list(MODULES.keys()) + ["all"],
        default="all",
        help="Module to run (default: all)"
    )

    # Date selection options
    date_group = parser.add_mutually_exclusive_group()
    date_group.add_argument(
        "--day",
        nargs="?",
        const="today",
        metavar="DATE",
        help="Analyze a single day (default: most recent)"
    )
    date_group.add_argument(
        "--week",
        action="store_true",
        help="Analyze last 7 days"
    )
    date_group.add_argument(
        "--month",
        action="store_true",
        help="Analyze last 30 days"
    )
    date_group.add_argument(
        "--all",
        action="store_true",
        help="Analyze all available data (default)"
    )

    # Custom date range
    parser.add_argument(
        "--start",
        type=str,
        metavar="DATE",
        help="Start date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--end",
        type=str,
        metavar="DATE",
        help="End date (YYYY-MM-DD)"
    )

    # Options
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress progress messages"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List available modules and exit"
    )

    args = parser.parse_args()

    # List modules
    if args.list:
        print("\nAvailable Modules:")
        print("-" * 60)
        for key, info in MODULES.items():
            print(f"  {key:15} {info['name']}")
            print(f"  {' '*15} {info['description']}")
            print()
        return

    # Determine date range
    start_date = None
    end_date = None
    today = date.today()

    if args.start and args.end:
        start_date = parse_date(args.start)
        end_date = parse_date(args.end)
    elif args.day:
        if args.day == "today":
            # Get most recent day from database
            from db.connection import EpochDatabase
            db = EpochDatabase()
            dates = db.get_available_dates()
            if dates:
                start_date = end_date = max(dates)
            else:
                start_date = end_date = today
        else:
            start_date = end_date = parse_date(args.day)
    elif args.week:
        end_date = today
        start_date = today - timedelta(days=7)
    elif args.month:
        end_date = today
        start_date = today - timedelta(days=30)
    # else: all data (start_date and end_date remain None)

    verbose = not args.quiet

    # Run selected module(s)
    modules_to_run = list(MODULES.keys()) if args.module == "all" else [args.module]

    if verbose:
        print()
        print("=" * 60)
        print("EPOCH BACKTEST JOURNAL")
        print("=" * 60)
        if start_date and end_date:
            if start_date == end_date:
                print(f"Date: {start_date}")
            else:
                print(f"Date Range: {start_date} to {end_date}")
        else:
            print("Date Range: All Available Data")
        print(f"Modules: {', '.join(modules_to_run)}")
        print("=" * 60)
        print()

    # Setup shared PDF and Excel outputs
    from config.settings import REPORTS_DIR
    from utils.excel_export import ExcelExporter

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if start_date and end_date:
        if start_date == end_date:
            date_str = start_date.strftime("%Y-%m-%d")
        else:
            date_str = f"{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}"
    else:
        date_str = "all_data"

    pdf_path = REPORTS_DIR / f"bt_journal_{date_str}_{timestamp}.pdf"
    excel_path = REPORTS_DIR / f"bt_journal_{date_str}_{timestamp}.xlsx"

    # Ensure reports directory exists
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    results = {}

    # Open shared PDF and Excel for all modules
    with PdfPages(pdf_path) as pdf:
        excel_exporter = ExcelExporter(excel_path)
        excel_exporter.open(create_if_missing=True)

        try:
            for module_name in modules_to_run:
                if verbose:
                    print(f"\n{'='*60}")
                    print(f"Running: {MODULES[module_name]['name']}")
                    print(f"{'='*60}\n")

                try:
                    result = MODULES[module_name]["run"](
                        start_date=start_date,
                        end_date=end_date,
                        verbose=verbose,
                        pdf=pdf,
                        excel_exporter=excel_exporter
                    )
                    results[module_name] = {"success": True, "output": result}
                except Exception as e:
                    results[module_name] = {"success": False, "error": str(e)}
                    if verbose:
                        print(f"ERROR in {module_name}: {e}")
                        import traceback
                        traceback.print_exc()
        finally:
            # Save Excel workbook
            excel_exporter.save()
            excel_exporter.close()

    # Summary
    if verbose:
        print("\n" + "=" * 60)
        print("OUTPUTS")
        print("=" * 60)
        print(f"  PDF Report: {pdf_path}")
        print(f"  Excel Data: {excel_path}")

        if len(modules_to_run) > 1:
            print("\n" + "=" * 60)
            print("MODULE SUMMARY")
            print("=" * 60)
            for module_name, result in results.items():
                status = "OK" if result["success"] else "FAILED"
                print(f"  {module_name:20} [{status}]")

    # Exit with error if any module failed
    if any(not r["success"] for r in results.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
