"""
Export functionality for scan results.
"""
import os
from datetime import datetime
from typing import Optional
import pandas as pd
import logging

# Import local config
try:
    from ..config import config
except ImportError:
    # Fallback for when running as script
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from config import config

logger = logging.getLogger(__name__)

class CSVExporter:
    """Export scan results to CSV."""
    
    @staticmethod
    def export(scan_results: pd.DataFrame, filename: Optional[str] = None) -> str:
        """Export to CSV file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"scan_results_{timestamp}.csv"
        
        output_path = config.OUTPUT_DIR / filename
        scan_results.to_csv(output_path, index=False)
        logger.info(f"Results exported to {output_path}")
        return str(output_path)

class SupabaseExporter:
    """Export scan results to Supabase."""
    
    @staticmethod
    def export(scan_results: pd.DataFrame, scan_date: datetime) -> bool:
        """Push scan results to Supabase."""
        try:
            from supabase import create_client, Client
        except ImportError:
            logger.error("Supabase client not installed. Install with: pip install supabase")
            return False
        
        if not config.SUPABASE_URL or not config.SUPABASE_KEY:
            logger.error("Supabase credentials not found in environment variables.")
            return False
        
        try:
            # Initialize Supabase client
            supabase: Client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
            
            # Format scan date for database
            scan_date_str = scan_date.strftime('%Y-%m-%d')
            
            # Check for existing records for this date and delete them
            try:
                existing = supabase.table('premarket_scans').select('id').eq('scan_date', scan_date_str).execute()
                if existing.data:
                    logger.info(f"Deleting {len(existing.data)} existing records for {scan_date_str}")
                    supabase.table('premarket_scans').delete().eq('scan_date', scan_date_str).execute()
            except Exception as e:
                logger.warning(f"Could not check/delete existing records: {e}")
            
            # Prepare records
            records = []
            for _, row in scan_results.iterrows():
                record = {
                    'ticker': str(row['ticker']),
                    'ticker_id': str(row.get('ticker_id', '')),  # Add ticker_id field
                    'ticker_list': str(row.get('ticker_list', 'sp500')),
                    'price': float(row['price']),
                    'rank': int(row['rank']),
                    'premarket_volume': int(row['premarket_volume']),
                    'avg_daily_volume': int(row['avg_daily_volume']),
                    'dollar_volume': float(row['dollar_volume']),
                    'atr': float(row['atr']),
                    'atr_percent': float(row['atr_percent']),
                    'interest_score': float(row['interest_score']),
                    'pm_vol_ratio_score': float(row['pm_vol_ratio_score']),
                    'atr_percent_score': float(row['atr_percent_score']),
                    'dollar_vol_score': float(row['dollar_vol_score']),
                    'pm_vol_abs_score': float(row['pm_vol_abs_score']),
                    'price_atr_bonus': float(row['price_atr_bonus']),
                    'scan_date': scan_date_str,
                    'scan_time': row['scan_time'].isoformat() if pd.notna(row.get('scan_time')) else None,
                    'passed_filters': True,
                    'market_session': 'pre-market',
                    'active': True  # Mark current scan as active
                }
                
                # Add optional fields if they exist
                if 'previous_close' in row and pd.notna(row['previous_close']):
                    record['previous_close'] = float(row['previous_close'])
                
                if 'gap_percent' in row and pd.notna(row['gap_percent']):
                    record['gap_percent'] = float(row['gap_percent'])
                
                if 'gap_magnitude_score' in row and pd.notna(row['gap_magnitude_score']):
                    record['gap_magnitude_score'] = float(row['gap_magnitude_score'])
                
                if 'market_cap' in row and pd.notna(row['market_cap']):
                    record['market_cap'] = int(float(row['market_cap']))
                
                if 'fetch_time' in row and pd.notna(row['fetch_time']):
                    if hasattr(row['fetch_time'], 'isoformat'):
                        record['fetch_time'] = row['fetch_time'].isoformat()
                    else:
                        record['fetch_time'] = str(row['fetch_time'])
                
                records.append(record)
            
            # First, mark all previous records as inactive
            try:
                supabase.table('premarket_scans').update({'active': False}).eq('scan_date', scan_date_str).execute()
            except:
                pass  # OK if this fails, might not have previous records
            
            # Insert new records in batches
            batch_size = 100
            total_inserted = 0
            
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                try:
                    result = supabase.table('premarket_scans').insert(batch).execute()
                    if result.data:
                        total_inserted += len(result.data)
                    logger.debug(f"Inserted batch {i//batch_size + 1}: {len(batch)} records")
                except Exception as e:
                    logger.error(f"Failed to insert batch {i//batch_size + 1}: {e}")
                    # Continue with remaining batches
            
            logger.info(f"Successfully pushed {total_inserted} records to Supabase")
            return total_inserted > 0
            
        except Exception as e:
            logger.error(f"Error pushing to Supabase: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    @staticmethod
    def verify_export(scan_date: datetime, expected_count: int) -> bool:
        """Verify that the export was successful."""
        try:
            from supabase import create_client, Client
            
            if not config.SUPABASE_URL or not config.SUPABASE_KEY:
                return False
                
            supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
            scan_date_str = scan_date.strftime('%Y-%m-%d')
            
            result = supabase.table('premarket_scans').select('count', count='exact').eq('scan_date', scan_date_str).eq('active', True).execute()
            
            actual_count = result.count if result.count is not None else 0
            logger.info(f"Verification: Expected {expected_count}, Found {actual_count}")
            
            return actual_count == expected_count
            
        except Exception as e:
            logger.error(f"Error verifying export: {e}")
            return False

class MarkdownExporter:
    """Export scan results to Markdown report."""
    
    @staticmethod
    def export(scan_results: pd.DataFrame, 
              summary: dict,
              criteria: dict,
              filename: Optional[str] = None) -> str:
        """Export to Markdown file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"scan_report_{timestamp}.md"
        
        output_path = config.OUTPUT_DIR / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            # Header
            f.write(f"# Market Scanner Report - {summary.get('ticker_list', 'Unknown').upper()}\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Scanner Type:** Pre-market Scanner\n\n")
            
            # Summary
            f.write("## Summary\n\n")
            f.write("| Metric | Value |\n")
            f.write("|--------|-------|\n")
            f.write(f"| Ticker List | {summary.get('ticker_list', 'Unknown').upper()} |\n")
            f.write(f"| Total Scanned | {summary.get('total_scanned', 0)} |\n")
            f.write(f"| Passed Filters | {summary.get('passed_filters', 0)} |\n")
            f.write(f"| Pass Rate | {summary.get('pass_rate', '0.0%')} |\n")
            if summary.get('avg_interest_score'):
                f.write(f"| Avg Interest Score | {summary.get('avg_interest_score'):.2f} |\n")
            
            # Add gap-specific summary if applicable
            if 'avg_gap_percent' in summary:
                f.write(f"| Avg Gap % | {summary.get('avg_gap_percent')} |\n")
                f.write(f"| Max Gap % | {summary.get('max_gap_percent')} |\n")
                if 'gap_distribution' in summary:
                    f.write(f"| Gap Distribution | {summary.get('gap_distribution')} |\n")
            
            f.write("\n")
            
            # Filter Criteria
            f.write("## Filter Criteria\n\n")
            f.write("| Criterion | Value |\n")
            f.write("|-----------|-------|\n")
            for key, value in criteria.items():
                f.write(f"| {key} | {value} |\n")
            f.write("\n")
            
            # Results
            if scan_results.empty:
                f.write("## Results\n\n")
                f.write("❌ **No stocks passed all filters**\n")
            else:
                # Check if this is a gap scan
                is_gap_scan = 'gap_percent' in scan_results.columns and any(criteria.get(key, '') for key in ['Gap Direction', 'Min Gap %'])
                
                if is_gap_scan:
                    f.write(f"## Top {min(50, len(scan_results))} Gapping Stocks by Interest Score\n\n")
                    f.write("| Rank | Ticker | Ticker ID | Price | Gap % | Score | PM Volume | PM % | ATR % |\n")
                    f.write("|:----:|:------:|:---------:|------:|------:|------:|----------:|-----:|------:|\n")
                    
                    for _, row in scan_results.head(50).iterrows():
                        pm_vol_pct = (row['premarket_volume'] / row['avg_daily_volume'] * 100)
                        gap_direction = "↑" if row['gap_percent'] > 0 else "↓"
                        
                        # Highlight top 3
                        ticker = row['ticker']
                        if row['rank'] == 1:
                            ticker = f"🥇 **{ticker}**"
                        elif row['rank'] == 2:
                            ticker = f"🥈 **{ticker}**"
                        elif row['rank'] == 3:
                            ticker = f"🥉 **{ticker}**"
                        
                        ticker_id = row.get('ticker_id', 'N/A')
                        
                        f.write(f"| {row['rank']} | {ticker} | {ticker_id} | ${row['price']:.2f} | ")
                        f.write(f"{gap_direction}{abs(row['gap_percent']):.2f}% | ")
                        f.write(f"{row['interest_score']:.1f} | {row['premarket_volume']:,.0f} | ")
                        f.write(f"{pm_vol_pct:.2f}% | {row['atr_percent']:.2f}% |\n")
                else:
                    f.write(f"## Top {min(50, len(scan_results))} Stocks by Interest Score\n\n")
                    f.write("| Rank | Ticker | Ticker ID | Price | Score | PM Volume | PM % | ATR % |\n")
                    f.write("|:----:|:------:|:---------:|------:|------:|----------:|-----:|------:|\n")
                    
                    for _, row in scan_results.head(50).iterrows():
                        pm_vol_pct = (row['premarket_volume'] / row['avg_daily_volume'] * 100)
                        
                        # Highlight top 3
                        ticker = row['ticker']
                        if row['rank'] == 1:
                            ticker = f"🥇 **{ticker}**"
                        elif row['rank'] == 2:
                            ticker = f"🥈 **{ticker}**"
                        elif row['rank'] == 3:
                            ticker = f"🥉 **{ticker}**"
                        
                        ticker_id = row.get('ticker_id', 'N/A')
                        
                        f.write(f"| {row['rank']} | {ticker} | {ticker_id} | ${row['price']:.2f} | ")
                        f.write(f"{row['interest_score']:.1f} | {row['premarket_volume']:,.0f} | ")
                        f.write(f"{pm_vol_pct:.2f}% | {row['atr_percent']:.2f}% |\n")
        
        logger.info(f"Report exported to {output_path}")
        return str(output_path)