#!/usr/bin/env python
"""
Main script to run market scanner.
"""
import sys
import os

# Add the parent of market_scanner to Python path
scanner_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
meridian_root = os.path.dirname(scanner_root)
sys.path.insert(0, meridian_root)

import argparse
from datetime import datetime
import logging

# Now import from local market scanner package
sys.path.insert(0, scanner_root)
from config import config
from data import TickerList
from filters import FilterCriteria, InterestScoreWeights
from scanners import PremarketScanner
from outputs import CSVExporter, SupabaseExporter, MarkdownExporter, ReportFormatter

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Run market scanner')
    parser.add_argument('--list', type=str, default='sp500', 
                       choices=['sp500', 'nasdaq100', 'russell2000', 'dow30', 'all'],
                       help='Ticker list to scan (use "all" for all US equities)')
    parser.add_argument('--profile', type=str, default='relaxed',
                       choices=['strict', 'relaxed', 'momentum', 'penny_stocks', 
                               'gap_up', 'gap_down', 'large_gap'],
                       help='Filter profile to use')
    parser.add_argument('--output', type=str, nargs='+', 
                       default=['console', 'csv'],
                       choices=['console', 'csv', 'markdown', 'supabase'],
                       help='Output formats')
    parser.add_argument('--top', type=int, default=20,
                       help='Number of top stocks to display')
    parser.add_argument('--workers', type=int, default=None,
                       help='Number of parallel workers for data fetching')
    
    args = parser.parse_args()
    
    print("Market Scanner")
    print("=" * 70)
    print(f"Scan Time: {datetime.now()}")
    print(f"Ticker List: {'ALL US EQUITIES' if args.list == 'all' else args.list.upper()}")
    print(f"Filter Profile: {args.profile}")
    
    # Check if gap profile
    is_gap_scan = args.profile in ['gap_up', 'gap_down', 'large_gap']
    if is_gap_scan:
        print(f"Gap Scan: {'UP' if 'up' in args.profile else 'DOWN' if 'down' in args.profile else 'BOTH'}")
    print()
    
    # Initialize scanner
    try:
        # Set ticker list
        if args.list == 'all':
            ticker_list = TickerList.ALL_US_EQUITIES
        else:
            ticker_list = TickerList(args.list)
        
        # Get filter criteria
        criteria = FilterCriteria.from_profile(args.profile)
        
        # Use gap-optimized weights for gap scans
        weights = InterestScoreWeights.for_gap_scan() if is_gap_scan else None
        
        scanner = PremarketScanner(
            ticker_list=ticker_list,
            filter_criteria=criteria,
            score_weights=weights,
            parallel_workers=args.workers
        )
        
        # Progress callback
        def progress(completed, total, ticker):
            if completed % 10 == 0 or completed == total:
                print(f"  Progress: {completed}/{total} ({completed/total*100:.1f}%) - Current: {ticker}")
        
        # Run scan
        print("Starting scan...")
        scan_results = scanner.run_scan(progress_callback=progress)
        
        if scan_results.empty:
            print("\nNo stocks passed filters.")
            return
        
        # Get summary
        summary = scanner.get_summary_stats(scan_results)
        
        # Output results
        for output_format in args.output:
            if output_format == 'console':
                # Modified console output for gap scans
                if is_gap_scan and 'gap_percent' in scan_results.columns:
                    print("\nTop Gapping Stocks:")
                    print("-" * 100)
                    print(f"{'Rank':<5} {'Ticker':<8} {'Price':<10} {'Gap %':<10} {'Score':<8} {'PM Vol':<12} {'ATR %':<8}")
                    print("-" * 100)
                    
                    for _, row in scan_results.head(args.top).iterrows():
                        gap_direction = "↑" if row['gap_percent'] > 0 else "↓"
                        print(
                            f"{row['rank']:<5} {row['ticker']:<8} ${row['price']:<9.2f} "
                            f"{gap_direction}{abs(row['gap_percent']):>8.2f}% "
                            f"{row['interest_score']:<8.2f} {row['premarket_volume']:>11,.0f} "
                            f"{row['atr_percent']:>7.2f}%"
                        )
                else:
                    print(ReportFormatter.format_console_output(scan_results, args.top))
                
                # Show score explanation for top stock
                if len(scan_results) > 0:
                    top_stock = scan_results.iloc[0]
                    explanation = scanner.filter.explain_score(top_stock)
                    print(f"\nScore explanation for {top_stock['ticker']}:")
                    print(ReportFormatter.format_score_explanation(explanation))
            
            elif output_format == 'csv':
                path = CSVExporter.export(scan_results)
                print(f"\n✅ CSV exported to: {path}")
            
            elif output_format == 'markdown':
                path = MarkdownExporter.export(
                    scan_results, 
                    summary, 
                    criteria.to_dict()
                )
                print(f"\n✅ Markdown report exported to: {path}")
            
            elif output_format == 'supabase':
                success = SupabaseExporter.export(scan_results, datetime.now())
                if success:
                    print("\n✅ Results pushed to Supabase")
                else:
                    print("\n❌ Failed to push to Supabase")
        
        # Print summary
        print(f"\nScan Summary:")
        print(f"  Ticker list: {'ALL US EQUITIES' if args.list == 'all' else args.list.upper()}")
        print(f"  Total scanned: {summary.get('total_scanned', 0)}")
        print(f"  Pass rate: {summary['pass_rate']}")
        print(f"  Avg interest score: {summary.get('avg_interest_score', 0):.2f}")
        
        if 'avg_gap_percent' in summary:
            print(f"  Avg gap: {summary['avg_gap_percent']}")
            print(f"  Max gap: {summary['max_gap_percent']}")
            
        print(f"  Top 5: {', '.join(summary.get('top_5_tickers', []))}")
        
    except Exception as e:
        logger.error(f"Error during scan: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())