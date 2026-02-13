#!/usr/bin/env python
"""
Primary Epoch v1 market scanner - runs with defaults, customizable via args.
"""
import sys
import os

# Add paths
scanner_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
meridian_root = os.path.dirname(scanner_root)
sys.path.insert(0, meridian_root)
sys.path.insert(0, scanner_root)

import argparse
from datetime import datetime, timezone
import logging
from pathlib import Path

from scanners.two_phase_scanner import TwoPhaseScanner
from filters.two_phase_filter import FilterPhase, RankingWeights
from data import TickerList
from outputs.excel_exporter import ExcelExporter

# ============================================================================
# DEFAULT CONFIGURATION - CUSTOMIZE THESE VALUES
# ============================================================================
DEFAULT_EXCEL_PATH = r"C:\XIIITradingSystems\Epoch\epoch_v1.xlsm"
DEFAULT_TICKER_LIST = "sp500"
DEFAULT_MIN_ATR = 2.0
DEFAULT_MIN_PRICE = 10.0
DEFAULT_MIN_GAP = 2.0
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(
        description='Epoch v1 Market Scanner - Run with defaults or customize',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with all defaults (just press F5 in VSCode!)
  python scan_runner.py
  
  # Scan a specific date
  python scan_runner.py --date 2025-11-20
  
  # Change filters
  python scan_runner.py --min-atr 3.0 --min-gap 3.0
  
  # Scan NASDAQ 100 instead
  python scan_runner.py --list nasdaq100
  
  # View existing scan summary
  python scan_runner.py --summary
        """
    )
    
    parser.add_argument('--excel-path', type=str, default=DEFAULT_EXCEL_PATH,
                       help=f'Path to Excel file (default: {DEFAULT_EXCEL_PATH})')
    parser.add_argument('--date', type=str, default=None,
                       help='Scan date (YYYY-MM-DD). Defaults to today at 12:00 UTC.')
    parser.add_argument('--list', type=str, default=DEFAULT_TICKER_LIST,
                       choices=['sp500', 'nasdaq100', 'russell2000'],
                       help=f'Ticker list to scan (default: {DEFAULT_TICKER_LIST})')
    parser.add_argument('--min-atr', type=float, default=DEFAULT_MIN_ATR,
                       help=f'Minimum ATR filter (default: ${DEFAULT_MIN_ATR})')
    parser.add_argument('--min-price', type=float, default=DEFAULT_MIN_PRICE,
                       help=f'Minimum price filter (default: ${DEFAULT_MIN_PRICE})')
    parser.add_argument('--min-gap', type=float, default=DEFAULT_MIN_GAP,
                       help=f'Minimum gap percentage filter (default: {DEFAULT_MIN_GAP}%)')
    parser.add_argument('--summary', action='store_true',
                       help='Show summary of existing scan data and exit')
    parser.add_argument('--quiet', action='store_true',
                       help='Reduce output verbosity')
    
    args = parser.parse_args()
    
    excel_path = Path(args.excel_path)
    
    # Summary mode - just read and display
    if args.summary:
        print("Reading scan summary from Excel...")
        summary = ExcelExporter.get_scan_summary(str(excel_path))
        
        if 'error' in summary:
            print(f"❌ Error: {summary['error']}")
            return 1
        
        print("\n" + "=" * 60)
        print("SCANNER RESULTS SUMMARY")
        print("=" * 60)
        print(f"Total Stocks: {summary.get('count', 0)}")
        print(f"Scan Date: {summary.get('scan_date', 'N/A')}")
        print(f"Scan Time: {summary.get('scan_time', 'N/A')}")
        if summary.get('top_5_tickers'):
            print(f"Top 5: {', '.join(summary['top_5_tickers'])}")
        if summary.get('avg_gap') is not None:
            print(f"Avg Gap: {summary['avg_gap']:.2f}%")
        if summary.get('avg_score') is not None:
            print(f"Avg Score: {summary['avg_score']:.2f}")
        print("=" * 60)
        return 0
    
    # Verify Excel file exists
    if not excel_path.exists():
        logger.error(f"Excel file not found: {excel_path}")
        print(f"\n❌ Excel file not found: {excel_path}")
        print("Please check the DEFAULT_EXCEL_PATH at the top of scan_runner.py")
        return 1
    
    # Parse date
    if args.date:
        scan_date = datetime.strptime(args.date, '%Y-%m-%d')
        scan_date = scan_date.replace(hour=12, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
    else:
        scan_date = datetime.now(timezone.utc).replace(hour=12, minute=0, second=0, microsecond=0)
    
    # Display configuration
    if not args.quiet:
        print("=" * 80)
        print("EPOCH V1 MARKET SCANNER".center(80))
        print("=" * 80)
        print(f"Scan Date: {scan_date.strftime('%Y-%m-%d %H:%M UTC')}")
        print(f"Ticker List: {args.list.upper()}")
        print(f"Excel Output: {excel_path.name}")
        print(f"Target Range: scanner_results (B3:Q3 headers, B4+ data)")
        print()
        print("FILTERS:")
        print(f"  ATR >= ${args.min_atr:.2f}")
        print(f"  Price >= ${args.min_price:.2f}")
        print(f"  Gap >= ±{args.min_gap:.1f}%")
        print("=" * 80)
    
    try:
        # Initialize scanner
        filter_phase = FilterPhase(
            min_atr=args.min_atr,
            min_price=args.min_price,
            min_gap_percent=args.min_gap
        )
        
        ranking_weights = RankingWeights()
        ticker_list = TickerList(args.list)
        
        scanner = TwoPhaseScanner(
            ticker_list=ticker_list,
            filter_phase=filter_phase,
            ranking_weights=ranking_weights
        )
        
        # Progress callback
        def progress(completed, total, ticker):
            if not args.quiet and (completed % 10 == 0 or completed == total):
                print(f"  Progress: {completed}/{total} ({completed/total*100:.1f}%)")
        
        # Run scan
        if not args.quiet:
            print("\nRunning scan...")
        
        results = scanner.run_scan(scan_date=scan_date, progress_callback=progress)
        
        if results.empty:
            print("\n❌ No stocks passed filters")
            print("\nTips:")
            print("  - Markets may be closed (try --date 2025-11-20)")
            print("  - Try relaxing filters (--min-atr 1.5 --min-gap 1.5)")
            print("  - Check if it's a market holiday")
            return 1
        
        print(f"\n✅ {len(results)} stocks passed filters")
        
        # Add scan metadata
        results['scan_time'] = scan_date.strftime('%Y-%m-%d %H:%M UTC')
        
        # Export to Excel using named range
        if not args.quiet:
            print(f"\nExporting to scanner_results range...")
        
        success = ExcelExporter.export_to_epoch(
            scan_results=results,
            workbook_path=str(excel_path)
        )
        
        if success:
            print(f"\n✅ Successfully exported to scanner_results")
            if not args.quiet:
                print(f"   Location: market_overview worksheet, columns B-Q")
                print(f"   Rows written: {len(results)}")
            print(f"   Top 5: {', '.join(results.head(5)['ticker'].tolist())}")
            
            # Display top 3 stocks with key metrics
            if not args.quiet and len(results) >= 3:
                print("\n" + "=" * 80)
                print("TOP 3 STOCKS")
                print("-" * 80)
                print(f"{'Rank':<5} {'Ticker':<8} {'Price':<10} {'Gap%':<8} {'O/N Vol':<15} {'Short%':<8}")
                print("-" * 80)
                for _, row in results.head(3).iterrows():
                    gap_sign = "+" if row['gap_percent'] > 0 else ""
                    print(f"{row['rank']:<5} {row['ticker']:<8} "
                          f"${row['current_price']:<9.2f} "
                          f"{gap_sign}{row['gap_percent']:>6.2f}% "
                          f"{row['current_overnight_volume']:>14,.0f} "
                          f"{row.get('short_interest', 0):>6.1f}%")
                print("=" * 80)
        else:
            print("\n❌ Failed to export to Excel")
            return 1
        
    except Exception as e:
        logger.error(f"Error during scan: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())