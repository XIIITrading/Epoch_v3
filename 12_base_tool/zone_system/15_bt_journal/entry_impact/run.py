"""
Epoch Backtest Journal - Confluence Analysis Module Runner
Run this file directly or import and call run().
XIII Trading LLC
"""

import argparse
from datetime import date, datetime, timedelta
from pathlib import Path
import sys
from typing import Optional

from matplotlib.backends.backend_pdf import PdfPages

sys.path.insert(0, str(Path(__file__).parent.parent))

from db.connection import EpochDatabase
from confluence_analysis.analyzer import ConfluenceAnalyzer
from confluence_analysis.report import ConfluenceReport
from utils.excel_export import ExcelExporter


def parse_date(date_str: str) -> date:
    """Parse date string in various formats."""
    formats = ["%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%Y%m%d"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Could not parse date: {date_str}")


def run(
    start_date: date = None,
    end_date: date = None,
    output_path: Path = None,
    verbose: bool = True,
    pdf: Optional[PdfPages] = None,
    excel_exporter: Optional[ExcelExporter] = None
) -> Path:
    """
    Run Confluence analysis and generate reports.

    Args:
        start_date: Start date for analysis (None for all data)
        end_date: End date for analysis (None for all data)
        output_path: Output PDF path (None for auto-generated, ignored if pdf provided)
        verbose: Print progress messages
        pdf: Shared PdfPages object for multi-module reports
        excel_exporter: Shared ExcelExporter for multi-module workbook

    Returns:
        Path to generated PDF report (or None if using shared pdf)
    """
    standalone = pdf is None

    if verbose and standalone:
        print("=" * 60)
        print("EPOCH BACKTEST JOURNAL")
        print("Confluence Analysis - Direction-Relative Alignment")
        print("=" * 60)
        print()

    # Initialize database
    if verbose:
        print("[1/3] Connecting to database...")
    db = EpochDatabase()

    # Check available data
    available_dates = db.get_available_dates()
    if not available_dates:
        print("ERROR: No data found in database.")
        return None

    if verbose:
        print(f"  Found {len(available_dates)} trading days in database")
        print(f"  Date range: {min(available_dates)} to {max(available_dates)}")
        print()

    # Run analysis
    if verbose:
        if start_date or end_date:
            print(f"[2/3] Analyzing confluence from {start_date or 'start'} to {end_date or 'end'}...")
        else:
            print("[2/3] Analyzing confluence for all available trades...")

    analyzer = ConfluenceAnalyzer(db)
    result = analyzer.analyze(start_date=start_date, end_date=end_date)

    if verbose:
        print(f"  Loaded {result.total_trades} trades ({result.trades_with_entry_data} with entry data)")
        
        if result.factor_alignments:
            print(f"  Calculating direction-relative alignments...")
            print()
            print("  Factor Alignment Edges:")
            for f in result.factor_alignments[:5]:  # Top 5
                print(f"    {f.factor_name}: {f.alignment_edge*100:+.1f}% edge "
                      f"(aligned {f.aligned_win_rate*100:.0f}% vs misaligned {f.misaligned_win_rate*100:.0f}%)")
            print()
            
            if result.confluence_buckets:
                print("  Confluence Curve:")
                print(f"    Score 6+: {result.score_6_plus_win_rate*100:.0f}% win rate ({result.score_6_plus_trades} trades)")
                print(f"    Score 5+: {result.score_5_plus_win_rate*100:.0f}% win rate ({result.score_5_plus_trades} trades)")
                if result.min_score_for_positive_expectancy:
                    print(f"    Min score for positive expectancy: {result.min_score_for_positive_expectancy}")
        else:
            print("  No entry event data found for the specified date range")
        print()

    # Generate report
    if verbose:
        print("[3/3] Generating reports...")

    report = ConfluenceReport(result)

    # Export to shared or standalone outputs
    if standalone:
        # Standalone mode: generate individual PDF and Excel
        output_file = report.generate(output_path)

        # Also create standalone Excel file
        excel_path = output_file.with_suffix('.xlsx')
        standalone_exporter = ExcelExporter(excel_path)
        standalone_exporter.open(create_if_missing=True)
        report.export_to_excel(standalone_exporter)
        standalone_exporter.save()
        standalone_exporter.close()

        if verbose:
            print()
            print("=" * 60)
            print("COMPLETE")
            print(f"PDF Report: {output_file}")
            print(f"Excel Data: {excel_path}")
            print("=" * 60)
        return output_file
    else:
        # Shared mode: add page to PDF and worksheet to Excel
        report.generate_pdf_page(pdf)
        if verbose:
            print("  Added PDF page: Confluence Analysis")

        if excel_exporter:
            report.export_to_excel(excel_exporter)

        return None


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Epoch Confluence Analysis - Direction-Relative Alignment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py                    # Analyze all data
  python run.py --day              # Analyze today (or most recent)
  python run.py --day 2025-12-12   # Analyze specific day
  python run.py --week             # Analyze last 7 days
  python run.py --month            # Analyze last 30 days
  python run.py --start 2025-12-01 --end 2025-12-12  # Custom range
        """
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

    # Output options
    parser.add_argument(
        "--output", "-o",
        type=str,
        metavar="PATH",
        help="Output PDF path"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress progress messages"
    )

    args = parser.parse_args()

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

    # Run analysis
    output_path = Path(args.output) if args.output else None

    try:
        result = run(
            start_date=start_date,
            end_date=end_date,
            output_path=output_path,
            verbose=not args.quiet
        )
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()