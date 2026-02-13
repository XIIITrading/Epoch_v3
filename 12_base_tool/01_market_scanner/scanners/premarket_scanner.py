"""
Pre-market scanner implementation.
Coordinates data fetching, filtering, and scoring.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone, time, date
from typing import Dict, List, Optional, Tuple
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio
from asyncio import Semaphore

from .base_scanner import BaseScanner
# Import local modules
try:
    from ..data import PolygonDataFetcher, TickerManager, TickerList
    from ..filters import PremarketFilter, FilterCriteria, InterestScoreWeights
    from ..config import config
    from ..utils.market_timing import MarketTiming
except ImportError:
    # Fallback for when running as script
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from data import PolygonDataFetcher, TickerManager, TickerList
    from filters import PremarketFilter, FilterCriteria, InterestScoreWeights
    from config import config
    from utils.market_timing import MarketTiming

logger = logging.getLogger(__name__)

def generate_ticker_id(ticker: str, date_obj) -> str:
    """
    Generate ticker_id in format: Ticker.MMDDYY
    
    Args:
        ticker: Stock ticker symbol
        date_obj: datetime.date or datetime.datetime object
        
    Returns:
        str: Formatted ticker_id (e.g., "AAPL.081125")
    """
    # Handle both datetime and date objects
    if isinstance(date_obj, datetime):
        date_obj = date_obj.date()
    elif isinstance(date_obj, date):
        pass
    else:
        # If it's a string, try to parse it
        if isinstance(date_obj, str):
            date_obj = datetime.strptime(date_obj, '%Y-%m-%d').date()
        else:
            raise ValueError(f"Unsupported date type: {type(date_obj)}")
    
    # Format as MMDDYY
    formatted_date = date_obj.strftime('%m%d%y')
    
    return f"{ticker}.{formatted_date}"

class PremarketScanner(BaseScanner):
    """
    Pre-market scanner for S&P 500 and other indices.
    Coordinates data fetching, metric calculations, and filtering.
    """
    
    def __init__(self,
                 ticker_list: Optional[TickerList] = TickerList.SP500,
                 filter_criteria: Optional[FilterCriteria] = None,
                 score_weights: Optional[InterestScoreWeights] = None,
                 cache_enabled: bool = True,
                 parallel_workers: int = None):
        """Initialize the pre-market scanner."""
        # Data components
        self.ticker_list = ticker_list
        self.data_fetcher = PolygonDataFetcher(cache_enabled=cache_enabled)
        self.ticker_manager = TickerManager()
        
        # Filter components - use gap weights if gap criteria present
        if filter_criteria and filter_criteria.min_gap_percent > 0 and score_weights is None:
            score_weights = InterestScoreWeights.for_gap_scan()
            
        self.filter = PremarketFilter(
            criteria=filter_criteria,
            weights=score_weights
        )
        
        # Configuration
        self.parallel_workers = parallel_workers or config.DEFAULT_PARALLEL_WORKERS
        
        # Load tickers
        self.tickers = self.ticker_manager.get_tickers(ticker_list)
        if ticker_list == TickerList.ALL_US_EQUITIES:
            logger.info(f"Loaded {len(self.tickers)} US equity tickers")
        else:
            logger.info(f"Loaded {len(self.tickers)} {ticker_list.value if ticker_list else 'all'} tickers")
        
        # Cache for storing fetched data
        self.data_cache = {}
    
    def run_scan(self, 
                scan_time: Optional[datetime] = None,
                lookback_days: int = None,
                progress_callback: Optional[callable] = None) -> pd.DataFrame:
        """Run the complete pre-market scan."""
        if scan_time is None:
            scan_time = datetime.now(timezone.utc)
        else:
            # Ensure timezone aware
            if scan_time.tzinfo is None:
                scan_time = scan_time.replace(tzinfo=timezone.utc)
        
        lookback_days = lookback_days or config.DEFAULT_LOOKBACK_DAYS
        
        logger.info(f"Starting pre-market scan at {scan_time}")
        
        # Determine market dates
        market_dates = self._get_market_dates(scan_time, lookback_days)
        
        # Fetch data for all tickers
        market_data = self._fetch_all_ticker_data(
            market_dates=market_dates,
            scan_time=scan_time,
            progress_callback=progress_callback
        )
        
        if market_data.empty:
            logger.warning("No market data fetched")
            return pd.DataFrame()
        
        logger.info(f"Fetched data for {len(market_data)} tickers")
        
        # Apply filters and calculate scores
        filtered_data = self.filter.apply_filters(market_data)
        
        # Rank by interest score
        ranked_data = self.filter.rank_by_interest(filtered_data)
        
        # Add scan metadata
        ranked_data['scan_time'] = scan_time
        ranked_data['ticker_list'] = self.ticker_list.value if self.ticker_list else 'all_us_equities'
        
        # Generate ticker_id for each row
        scan_date = scan_time.date()
        ranked_data['ticker_id'] = ranked_data['ticker'].apply(
            lambda ticker: generate_ticker_id(ticker, scan_date)
        )
        
        logger.info(f"Scan complete: {len(ranked_data)} stocks passed filters")
        
        return ranked_data
    
    def _get_market_dates(self, scan_time: datetime, lookback_days: int) -> Dict[str, datetime]:
        """Determine relevant market dates for data fetching."""
        # For historical data (ATR calculation)
        history_end = scan_time.replace(hour=0, minute=0, second=0, microsecond=0)
        history_start = history_end - timedelta(days=lookback_days + 5)  # Extra days for weekends
        
        # For pre-market data (4:00 AM to scan time)
        premarket_date = scan_time.date()
        premarket_start = datetime.combine(
            premarket_date, 
            time(config.PREMARKET_START_HOUR, config.PREMARKET_START_MINUTE, 0)
        ).replace(tzinfo=timezone.utc)
        
        return {
            'history_start': history_start,
            'history_end': history_end,
            'premarket_start': premarket_start,
            'premarket_end': scan_time
        }
    
    def _fetch_all_ticker_data(self,
                              market_dates: Dict[str, datetime],
                              scan_time: datetime,
                              progress_callback: Optional[callable] = None) -> pd.DataFrame:
        """Fetch data for all tickers in parallel."""
        all_data = []
        failed_tickers = []
        
        # Use ThreadPoolExecutor for parallel fetching
        with ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
            # Submit all tasks
            future_to_ticker = {
                executor.submit(
                    self._fetch_single_ticker_data,
                    ticker,
                    market_dates,
                    scan_time
                ): ticker
                for ticker in self.tickers
            }
            
            # Process completed tasks
            completed = 0
            for future in as_completed(future_to_ticker):
                ticker = future_to_ticker[future]
                completed += 1
                
                try:
                    ticker_data = future.result()
                    if ticker_data is not None:
                        all_data.append(ticker_data)
                except Exception as e:
                    logger.error(f"Failed to fetch data for {ticker}: {e}")
                    failed_tickers.append(ticker)
                
                # Progress callback
                if progress_callback:
                    progress_callback(completed, len(self.tickers), ticker)
                
                # Log progress every 50 tickers
                if completed % 50 == 0:
                    logger.info(f"Progress: {completed}/{len(self.tickers)} tickers processed")
        
        if failed_tickers:
            logger.warning(f"Failed to fetch data for {len(failed_tickers)} tickers: {failed_tickers[:10]}...")
        
        # Combine all data into DataFrame
        if all_data:
            return pd.DataFrame(all_data)
        else:
            return pd.DataFrame()
    
    def _fetch_single_ticker_data(self,
                                 ticker: str,
                                 market_dates: Dict[str, datetime],
                                 scan_time: datetime) -> Optional[Dict]:
        """Fetch and calculate all required data for a single ticker."""
        try:
            # Fetch historical data for ATR and average volume
            historical_df = self.data_fetcher.fetch_historical(
                ticker,
                market_dates['history_start'],
                market_dates['history_end']
            )
            
            if historical_df.empty or len(historical_df) < 2:
                return None
            
            # Calculate metrics from historical data
            atr = self._calculate_atr(historical_df, period=14)
            avg_daily_volume = self._calculate_avg_volume(historical_df, period=20)
            current_price = historical_df['close'].iloc[-1]
            previous_close = historical_df['close'].iloc[-2] if len(historical_df) > 1 else current_price
            
            # Skip if price outside range (early filter)
            if current_price < self.filter.criteria.min_price or \
               current_price > self.filter.criteria.max_price:
                return None
            
            # Fetch pre-market data
            premarket_data = self._fetch_premarket_data(
                ticker,
                market_dates['premarket_start'],
                market_dates['premarket_end']
            )
            
            premarket_volume = premarket_data['volume']
            premarket_price = premarket_data['price'] if premarket_data['price'] > 0 else current_price
            
            # Calculate gap percentage
            gap_percent = ((premarket_price - previous_close) / previous_close * 100) if previous_close > 0 else 0
            
            # Early gap filter to save processing
            if self.filter.criteria.min_gap_percent > 0:
                if self.filter.criteria.gap_direction == 'up' and gap_percent < self.filter.criteria.min_gap_percent:
                    return None
                elif self.filter.criteria.gap_direction == 'down' and gap_percent > -self.filter.criteria.min_gap_percent:
                    return None
                elif self.filter.criteria.gap_direction == 'both' and abs(gap_percent) < self.filter.criteria.min_gap_percent:
                    return None
            
            # Calculate derived metrics
            dollar_volume = current_price * avg_daily_volume
            atr_percent = (atr / current_price) * 100 if current_price > 0 else 0
            
            # Fetch market cap if filtering all equities
            market_cap = None
            if self.ticker_list == TickerList.ALL_US_EQUITIES:
                market_cap = self._fetch_market_cap(ticker)
                if market_cap and self.filter.criteria.min_market_cap:
                    if market_cap < self.filter.criteria.min_market_cap:
                        return None
            
            # Return data dictionary
            return {
                'ticker': ticker,
                'ticker_id': generate_ticker_id(ticker, scan_time.date()),
                'price': premarket_price,
                'previous_close': previous_close,
                'gap_percent': gap_percent,
                'avg_daily_volume': avg_daily_volume,
                'premarket_volume': premarket_volume,
                'dollar_volume': dollar_volume,
                'atr': atr,
                'atr_percent': atr_percent,
                'market_cap': market_cap,
                'fetch_time': scan_time
            }
            
        except Exception as e:
            logger.debug(f"Error fetching data for {ticker}: {e}")
            return None
    
    def _fetch_premarket_data(self,
                             ticker: str,
                             start_time: datetime,
                             end_time: datetime) -> Dict[str, float]:
        """Fetch pre-market volume and price for a ticker."""
        try:
            # Fetch 1-minute bars for pre-market session
            df = self.data_fetcher.fetch_intraday(
                ticker,
                start_time,
                end_time,
                timeframe='1min'
            )
            
            if df.empty:
                return {'volume': 0.0, 'price': 0.0}
            
            # Sum volume and get last price
            total_volume = float(df['volume'].sum())
            last_price = float(df['close'].iloc[-1])
            
            return {'volume': total_volume, 'price': last_price}
            
        except Exception as e:
            logger.debug(f"Failed to fetch pre-market data for {ticker}: {e}")
            return {'volume': 0.0, 'price': 0.0}
    
    def _fetch_market_cap(self, ticker: str) -> Optional[float]:
        """Fetch market cap for a ticker."""
        try:
            from polygon import RESTClient
            client = RESTClient(config.POLYGON_API_KEY)
            
            details = client.get_ticker_details(ticker)
            if hasattr(details, 'market_cap'):
                return float(details.market_cap)
            
            return None
            
        except Exception as e:
            logger.debug(f"Failed to fetch market cap for {ticker}: {e}")
            return None
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range (ATR)."""
        if len(df) < period:
            return 0.0
        
        # Calculate True Range
        df['h_l'] = df['high'] - df['low']
        df['h_pc'] = abs(df['high'] - df['close'].shift(1))
        df['l_pc'] = abs(df['low'] - df['close'].shift(1))
        
        df['true_range'] = df[['h_l', 'h_pc', 'l_pc']].max(axis=1)
        
        # Calculate ATR using EMA
        atr = df['true_range'].ewm(span=period, adjust=False).mean()
        
        return float(atr.iloc[-1]) if not atr.empty else 0.0
    
    def _calculate_avg_volume(self, df: pd.DataFrame, period: int = 20) -> float:
        """Calculate average daily volume."""
        if len(df) < period:
            # Use all available data if less than period
            return float(df['volume'].mean()) if not df.empty else 0.0
        
        # Use most recent N days
        return float(df['volume'].tail(period).mean())
    
    def get_summary_stats(self, scan_results: pd.DataFrame) -> Dict:
        """Generate summary statistics for scan results."""
        if scan_results.empty:
            return {
                'ticker_list': self.ticker_list.value if self.ticker_list else 'all_us_equities',
                'total_scanned': len(self.tickers),
                'passed_filters': 0,
                'pass_rate': '0.0%',
                'top_sectors': []
            }
        
        summary = {
            'ticker_list': self.ticker_list.value if self.ticker_list else 'all_us_equities',
            'total_scanned': len(self.tickers),
            'passed_filters': len(scan_results),
            'pass_rate': f"{(len(scan_results) / len(self.tickers) * 100):.1f}%",
            'avg_interest_score': scan_results['interest_score'].mean(),
            'interest_score_std': scan_results['interest_score'].std(),
            'top_5_tickers': scan_results.head(5)['ticker'].tolist(),
            'avg_premarket_volume': scan_results['premarket_volume'].mean(),
            'avg_atr_percent': scan_results['atr_percent'].mean()
        }
        
        # Add gap-specific stats if applicable
        if 'gap_percent' in scan_results.columns and self.filter.criteria.min_gap_percent > 0:
            summary['avg_gap_percent'] = f"{scan_results['gap_percent'].mean():.2f}%"
            summary['max_gap_percent'] = f"{scan_results['gap_percent'].abs().max():.2f}%"
            
            # Count up vs down gaps
            up_gaps = (scan_results['gap_percent'] > 0).sum()
            down_gaps = (scan_results['gap_percent'] < 0).sum()
            summary['gap_distribution'] = f"{up_gaps} up, {down_gaps} down"
        
        return summary
    
    def export_results(self, scan_results: pd.DataFrame, output_path: str):
        """Export scan results to file."""
        # Prepare display columns
        display_columns = [
            'rank', 'ticker', 'ticker_id', 'price', 'interest_score',
            'premarket_volume', 'avg_daily_volume',
            'atr', 'atr_percent', 'dollar_volume'
        ]
        
        # Add gap columns if it's a gap scan
        if 'gap_percent' in scan_results.columns and self.filter.criteria.min_gap_percent > 0:
            # Insert gap_percent after price
            idx = display_columns.index('price') + 1
            display_columns.insert(idx, 'gap_percent')
            display_columns.insert(idx + 1, 'previous_close')
        
        # Add market cap if available
        if 'market_cap' in scan_results.columns and scan_results['market_cap'].notna().any():
            display_columns.append('market_cap')
        
        # Select only available columns
        available_columns = [col for col in display_columns if col in scan_results.columns]
        formatted_df = scan_results[available_columns].copy()
        
        # Format numeric columns
        if 'price' in formatted_df.columns:
            formatted_df['price'] = formatted_df['price'].apply(lambda x: f"${x:.2f}")
        if 'previous_close' in formatted_df.columns:
            formatted_df['previous_close'] = formatted_df['previous_close'].apply(lambda x: f"${x:.2f}")
        if 'gap_percent' in formatted_df.columns:
            formatted_df['gap_percent'] = formatted_df['gap_percent'].apply(lambda x: f"{x:+.2f}%")
        if 'premarket_volume' in formatted_df.columns:
            formatted_df['premarket_volume'] = formatted_df['premarket_volume'].apply(lambda x: f"{x:,.0f}")
        if 'avg_daily_volume' in formatted_df.columns:
            formatted_df['avg_daily_volume'] = formatted_df['avg_daily_volume'].apply(lambda x: f"{x:,.0f}")
        if 'atr' in formatted_df.columns:
            formatted_df['atr'] = formatted_df['atr'].apply(lambda x: f"${x:.2f}")
        if 'atr_percent' in formatted_df.columns:
            formatted_df['atr_percent'] = formatted_df['atr_percent'].apply(lambda x: f"{x:.2f}%")
        if 'dollar_volume' in formatted_df.columns:
            formatted_df['dollar_volume'] = formatted_df['dollar_volume'].apply(lambda x: f"${x:,.0f}")
        if 'market_cap' in formatted_df.columns:
            formatted_df['market_cap'] = formatted_df['market_cap'].apply(
                lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A"
            )
        
        # Save to CSV
        formatted_df.to_csv(output_path, index=False)
        logger.info(f"Results exported to {output_path}")