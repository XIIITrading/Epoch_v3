#!/usr/bin/env python
"""
Run the two-phase market scanner with date selection.
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

from scanners.two_phase_scanner import TwoPhaseScanner
from filters.two_phase_filter import FilterPhase, RankingWeights
from data import TickerList

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Run two-phase market scanner')
    
    parser.add_argument('--date', type=str, default=None,
                       help='Scan date (YYYY-MM-DD). Defaults to today.')
    parser.add_argument('--list', type=str, default='sp500',
                       choices=['sp500', 'nasdaq100', 'russell2000', 'all'],
                       help='Ticker list to scan')
    parser.add_argument('--min-atr', type=float, default=2.0,
                       help='Minimum ATR filter (default: $2.00)')
    parser.add_argument('--min-price', type=float, default=10.0,
                       help='Minimum price filter (default: $10.00)')
    parser.add_argument('--min-gap', type=float, default=2.0,
                       help='Minimum gap percentage filter (default: 2%)')
    parser.add_argument('--output', type=str, nargs='+',
                       default=['console', 'csv'],
                       choices=['console', 'csv'],
                       help='Output formats')
    parser.add_argument('--top', type=int, default=20,
                       help='Number of top stocks to display')
    
    args = parser.parse_args()
    
    # Parse date
    if args.date:
        scan_date = datetime.strptime(args.date, '%Y-%m-%d')
        scan_date = scan_date.replace(tzinfo=timezone.utc)
    else:
        scan_date = datetime.now(timezone.utc)
    
    print("=" * 100)
    print("TWO-PHASE MARKET SCANNER".center(100))
    print("=" * 100)
    print(f"Scan Date: {scan_date.strftime('%Y-%m-%d')}")
    print(f"Data Point: 12:00 UTC")
    print(f"Ticker List: {args.list.upper()}")
    print()
    print("PHASE 1 FILTERS:")
    print(f"  - ATR >= ${args.min_atr:.2f}")
    print(f"  - Price >= ${args.min_price:.2f}")
    print(f"  - Gap >= ±{args.min_gap:.1f}%")
    print()
    print("PHASE 2 RANKING METRICS:")
    print("  1. Current Overnight Volume (20:01 UTC prior day to 12:00 UTC current day)")
    print("  2. Relative Overnight Volume (current vs prior overnight)")
    print("  3. Relative Volume (overnight vs regular hours)")
    print("  4. Gap Magnitude")
    print("  5. Short Interest %")
    print("=" * 100)
    
    try:
        # Initialize scanner
        filter_phase = FilterPhase(
            min_atr=args.min_atr,
            min_price=args.min_price,
            min_gap_percent=args.min_gap
        )
        
        ranking_weights = RankingWeights()  # All weights = 1.0
        
        ticker_list = TickerList(args.list) if args.list != 'all' else TickerList.ALL_US_EQUITIES
        
        scanner = TwoPhaseScanner(
            ticker_list=ticker_list,
            filter_phase=filter_phase,
            ranking_weights=ranking_weights
        )
        
        # Progress callback
        def progress(completed, total, ticker):
            if completed % 10 == 0 or completed == total:
                print(f"  Progress: {completed}/{total} ({completed/total*100:.1f}%) - Processing: {ticker}")
        
        # Run scan
        print("\nStarting scan...")
        results = scanner.run_scan(scan_date=scan_date, progress_callback=progress)
        
        if results.empty:
            print("\nX No stocks passed Phase 1 filters")
            print("Try adjusting filters (lower ATR, price, or gap requirements)")
            return
        
        print(f"\n> {len(results)} stocks passed filters and were ranked")
        
        # Output results
        for output_format in args.output:
            if output_format == 'console':
                print("\n" + "=" * 140)  # Increased width for new columns
                print("TOP RANKED STOCKS BY OVERNIGHT VOLUME")
                print("-" * 140)
                print(f"{'Rank':<5} {'Ticker':<8} {'Price':<10} {'Gap%':<8} "
                      f"{'Curr O/N Vol':<15} {'Prior O/N Vol':<15} {'Rel O/N':<10} {'Rel Vol':<10} "
                      f"{'Short%':<8} {'DTC':<6} {'Score':<8}")
                print("-" * 140)
                
                for _, row in results.head(args.top).iterrows():
                    # Format gap with direction indicator
                    gap_indicator = "+" if row['gap_percent'] > 0 else "-"
                    
                    # Highlight high short interest
                    short_flag = "*" if row['short_interest'] > 10 else " "
                    
                    print(f"{row['rank']:<5} {row['ticker']:<8} "
                          f"${row['current_price']:<9.2f} "
                          f"{gap_indicator}{abs(row['gap_percent']):>6.2f}% "
                          f"{row['current_overnight_volume']:>14,.0f} "  # Current O/N Vol
                          f"{row['prior_overnight_volume']:>14,.0f} "    # Prior O/N Vol (NEW)
                          f"{row.get('relative_overnight_volume', 0):>9.2f}x "
                          f"{row.get('relative_volume', 0):>9.2f}x "
                          f"{row.get('short_interest', 0):>6.1f}%{short_flag} "
                          f"{row.get('days_to_cover', 0):>5.1f} "
                          f"{row.get('ranking_score', 0):>7.1f}")
                
                print("\n* = Short interest > 10%")
                print("DTC = Days to Cover")
                
                if 'short_data_date' in results.columns and results['short_data_date'].notna().any():
                    latest_date = results['short_data_date'].dropna().iloc[0] if len(results) > 0 else None
                    if latest_date:
                        print(f"Short interest data as of: {latest_date}")
            
            elif output_format == 'csv':
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"two_phase_scan_{scan_date.strftime('%Y%m%d')}_{timestamp}.csv"
                output_dir = os.path.join(scanner_root, 'outputs', 'reports')
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, filename)
                
                # Select columns for export (UPDATED to include both ON volumes)
                export_columns = [
                    'rank', 'ticker', 'current_price', 'gap_percent',
                    'current_overnight_volume', 'prior_overnight_volume',  # Both ON volumes
                    'relative_overnight_volume', 'relative_volume', 
                    'short_interest', 'days_to_cover',
                    'ranking_score', 'atr', 'prior_close'
                ]
                export_df = results[export_columns]
                export_df.to_csv(output_path, index=False)
                print(f"\n> CSV saved to: {output_path}")
        
        # Summary statistics
        print("\n" + "=" * 100)
        print("SUMMARY STATISTICS")
        print("-" * 100)
        print(f"  Total Scanned: {len(scanner.tickers)} tickers")
        print(f"  Passed Filters: {len(results)} tickers")
        print(f"  Pass Rate: {len(results)/len(scanner.tickers)*100:.1f}%")
        print(f"  Average Gap: {results['gap_percent'].mean():.2f}%")
        print(f"  Average O/N Volume: {results['current_overnight_volume'].mean():,.0f}")
        print(f"  Average Short Interest: {results['short_interest'].mean():.1f}%")
        print(f"  Top 5 Tickers: {', '.join(results.head(5)['ticker'].tolist())}")
        print("=" * 100)
        
    except Exception as e:
        logger.error(f"Error during scan: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())