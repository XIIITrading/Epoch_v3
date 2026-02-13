import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone, time
from typing import Dict, List, Optional, Tuple
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from ..data import PolygonDataFetcher, TickerManager, TickerList
    from ..filters.two_phase_filter import FilterPhase, RankingWeights
    from ..data.overnight_fetcher import OvernightDataFetcher
    from ..data.short_interest_fetcher import ShortInterestFetcher
    from ..config import config
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from data import PolygonDataFetcher, TickerManager, TickerList
    from filters.two_phase_filter import FilterPhase, RankingWeights
    from data.overnight_fetcher import OvernightDataFetcher
    from data.short_interest_fetcher import ShortInterestFetcher
    from config import config

logger = logging.getLogger(__name__)

class TwoPhaseScanner:
    """
    Two-phase scanner with targeted short interest loading.
    """
    
    def __init__(self,
                 ticker_list=None,
                 filter_phase=None,
                 ranking_weights=None,
                 parallel_workers=10):
        
        self.ticker_list = ticker_list
        self.filter_phase = filter_phase or FilterPhase()
        self.ranking_weights = ranking_weights or RankingWeights()
        self.parallel_workers = parallel_workers
        
        # Initialize data fetchers
        self.ticker_manager = TickerManager()
        self.polygon_fetcher = PolygonDataFetcher()
        self.overnight_fetcher = OvernightDataFetcher(self.polygon_fetcher)
        self.short_fetcher = ShortInterestFetcher(config.POLYGON_API_KEY)
        
        # Load tickers
        self.tickers = self.ticker_manager.get_tickers(ticker_list)
        logger.info(f"Loaded {len(self.tickers)} tickers from {ticker_list.value if ticker_list else 'all'}")
        
        # Don't pre-load short interest here - will load in run_scan with date
    
    def run_scan(self, scan_date: datetime = None, progress_callback=None) -> pd.DataFrame:
        """
        Run the two-phase scan.
        """
        if scan_date is None:
            scan_date = datetime.now(timezone.utc).replace(hour=12, minute=0, second=0, microsecond=0)
        else:
            # Ensure we're using 12:00 UTC on the specified date
            scan_date = scan_date.replace(hour=12, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
        
        logger.info(f"Starting two-phase scan for {scan_date.strftime('%Y-%m-%d')} at 12:00 UTC")
        
        # Load short interest data for ONLY the tickers we're scanning and the specific date
        logger.info(f"Loading short interest data for {len(self.tickers)} tickers as of {scan_date.date()}")
        self.short_fetcher.load_short_data_for_tickers(self.tickers, scan_date)
        
        # Phase 1: Fetch data and apply filters
        filtered_data = self._phase1_filter(scan_date, progress_callback)
        
        if filtered_data.empty:
            logger.warning("No tickers passed Phase 1 filters")
            return pd.DataFrame()
        
        logger.info(f"Phase 1 complete: {len(filtered_data)} tickers passed filters")
        
        # Phase 2: Calculate ranking metrics and sort
        ranked_data = self._phase2_rank(filtered_data)
        
        # Add metadata
        ranked_data['scan_date'] = scan_date
        ranked_data['ticker_list'] = self.ticker_list.value if self.ticker_list else 'all'
        
        logger.info(f"Phase 2 complete: Ranked {len(ranked_data)} tickers")
        
        return ranked_data
    
    def _phase1_filter(self, scan_date: datetime, progress_callback=None) -> pd.DataFrame:
        """Phase 1: Apply hard filters."""
        passed_tickers = []
        
        with ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
            futures = {
                executor.submit(self._process_ticker, ticker, scan_date): ticker 
                for ticker in self.tickers
            }
            
            completed = 0
            for future in as_completed(futures):
                ticker = futures[future]
                completed += 1
                
                if progress_callback:
                    progress_callback(completed, len(self.tickers), ticker)
                
                try:
                    ticker_data = future.result()
                    if ticker_data is not None:
                        passed_tickers.append(ticker_data)
                except Exception as e:
                    logger.error(f"Error processing {ticker}: {e}")
                
                if completed % 50 == 0:
                    logger.info(f"Processed {completed}/{len(self.tickers)} tickers...")
        
        return pd.DataFrame(passed_tickers)
    
    def _process_ticker(self, ticker: str, scan_date: datetime) -> Optional[Dict]:
        """Process a single ticker through Phase 1 filters."""
        try:
            # Get prior day's daily data for ATR and closing price
            history_end = scan_date - timedelta(days=1)
            history_start = history_end - timedelta(days=20)
            
            historical_df = self.polygon_fetcher.fetch_historical(
                ticker,
                history_start,
                history_end
            )
            
            if historical_df.empty or len(historical_df) < 2:
                return None
            
            # Calculate ATR
            atr = self._calculate_atr(historical_df)
            
            # Apply ATR filter early
            if atr < self.filter_phase.min_atr:
                return None
            
            prior_close = historical_df['close'].iloc[-1]
            
            # Get overnight volumes and current price
            overnight_data = self.overnight_fetcher.fetch_overnight_volumes(ticker, scan_date)
            current_price = overnight_data['current_price']
            
            if current_price == 0:
                return None
            
            # Apply price filter
            if current_price < self.filter_phase.min_price:
                return None
            
            # Calculate gap
            gap_percent = ((current_price - prior_close) / prior_close * 100) if prior_close > 0 else 0
            
            # Apply gap filter
            if abs(gap_percent) < self.filter_phase.min_gap_percent:
                return None
            
            # Get short interest (from cached data)
            short_data = self.short_fetcher.fetch_short_interest(ticker, scan_date)
            
            # Ticker passed all filters, return data
            return {
                'ticker': ticker,
                'current_price': current_price,
                'prior_close': prior_close,
                'gap_percent': gap_percent,
                'atr': atr,
                'current_overnight_volume': overnight_data['current_overnight_volume'],
                'prior_overnight_volume': overnight_data['prior_overnight_volume'],
                'prior_regular_volume': overnight_data['prior_regular_volume'],
                'short_interest': short_data['short_interest_percent'],
                'short_interest_shares': short_data['short_interest_shares'],
                'days_to_cover': short_data['days_to_cover'],
                'short_data_date': short_data['data_date']
            }
            
        except Exception as e:
            logger.debug(f"Error processing {ticker}: {e}")
            return None
    
    def _phase2_rank(self, filtered_df: pd.DataFrame) -> pd.DataFrame:
        """Phase 2: Calculate ranking metrics and sort."""
        
        # Calculate relative volume metrics
        filtered_df['relative_overnight_volume'] = np.where(
            filtered_df['prior_overnight_volume'] > 0,
            filtered_df['current_overnight_volume'] / filtered_df['prior_overnight_volume'],
            0
        )
        
        filtered_df['relative_volume'] = np.where(
            filtered_df['prior_regular_volume'] > 0,
            filtered_df['current_overnight_volume'] / filtered_df['prior_regular_volume'],
            0
        )
        
        filtered_df['gap_magnitude'] = filtered_df['gap_percent'].abs()
        
        # Normalize each metric to 0-100 scale for fair comparison
        def normalize_column(col):
            if col.max() > col.min():
                return 100 * (col - col.min()) / (col.max() - col.min())
            return pd.Series([50] * len(col), index=col.index)
        
        # Create normalized scores
        filtered_df['norm_overnight_vol'] = normalize_column(filtered_df['current_overnight_volume'])
        filtered_df['norm_rel_overnight'] = normalize_column(filtered_df['relative_overnight_volume'])
        filtered_df['norm_rel_volume'] = normalize_column(filtered_df['relative_volume'])
        filtered_df['norm_gap'] = normalize_column(filtered_df['gap_magnitude'])
        filtered_df['norm_short'] = normalize_column(filtered_df['short_interest'])
        
        # Calculate composite score with normalized values
        filtered_df['ranking_score'] = (
            self.ranking_weights.overnight_volume * filtered_df['norm_overnight_vol'] +
            self.ranking_weights.relative_overnight_volume * filtered_df['norm_rel_overnight'] +
            self.ranking_weights.relative_volume * filtered_df['norm_rel_volume'] +
            self.ranking_weights.gap_magnitude * filtered_df['norm_gap'] +
            self.ranking_weights.short_interest * filtered_df['norm_short']
        )
        
        # Primary sort by overnight volume, then by composite score
        filtered_df = filtered_df.sort_values(
            by=['current_overnight_volume', 'ranking_score'],
            ascending=[False, False]
        )
        
        # Add rank
        filtered_df['rank'] = range(1, len(filtered_df) + 1)
        
        return filtered_df
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range."""
        if len(df) < 2:
            return 0.0
        
        df = df.copy()
        df['h_l'] = df['high'] - df['low']
        df['h_pc'] = abs(df['high'] - df['close'].shift(1))
        df['l_pc'] = abs(df['low'] - df['close'].shift(1))
        
        df['true_range'] = df[['h_l', 'h_pc', 'l_pc']].max(axis=1)
        atr = df['true_range'].ewm(span=period, adjust=False).mean()
        
        return float(atr.iloc[-1]) if not atr.empty else 0.0