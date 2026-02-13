from datetime import datetime, timedelta, time, timezone
import pandas as pd
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class OvernightDataFetcher:
    """Fetches and calculates overnight volume metrics."""
    
    def __init__(self, polygon_fetcher):
        self.fetcher = polygon_fetcher
    
    def fetch_overnight_volumes(self, ticker: str, scan_date: datetime) -> Dict:
        """
        Fetch overnight volumes for current and prior day.
        
        Returns:
            Dict with:
            - current_overnight_volume
            - prior_overnight_volume  
            - prior_regular_volume
            - current_price
        """
        # Ensure timezone aware
        if scan_date.tzinfo is None:
            scan_date = scan_date.replace(tzinfo=timezone.utc)
            
        # Define time windows (all in UTC)
        # Current overnight: Prior day 20:01 to current day 12:00
        current_overnight_start = datetime.combine(
            scan_date - timedelta(days=1), 
            time(20, 1, 0),
            tzinfo=timezone.utc
        )
        current_overnight_end = datetime.combine(
            scan_date, 
            time(12, 0, 0),
            tzinfo=timezone.utc
        )
        
        # Prior overnight: 2 days ago 20:01 to 1 day ago 12:00
        prior_overnight_start = current_overnight_start - timedelta(days=1)
        prior_overnight_end = current_overnight_end - timedelta(days=1)
        
        # Prior regular hours: 1 day ago 13:30 to 20:00
        prior_regular_start = datetime.combine(
            scan_date - timedelta(days=1),
            time(13, 30, 0),
            tzinfo=timezone.utc
        )
        prior_regular_end = datetime.combine(
            scan_date - timedelta(days=1),
            time(20, 0, 0),
            tzinfo=timezone.utc
        )
        
        try:
            # Fetch current overnight volume
            current_overnight_df = self.fetcher.fetch_intraday(
                ticker,
                current_overnight_start,
                current_overnight_end,
                timeframe='1min'
            )
            current_overnight_vol = current_overnight_df['volume'].sum() if not current_overnight_df.empty else 0
            
            # Fetch prior overnight volume
            prior_overnight_df = self.fetcher.fetch_intraday(
                ticker,
                prior_overnight_start,
                prior_overnight_end,
                timeframe='1min'
            )
            prior_overnight_vol = prior_overnight_df['volume'].sum() if not prior_overnight_df.empty else 0
            
            # Fetch prior regular hours volume
            prior_regular_df = self.fetcher.fetch_intraday(
                ticker,
                prior_regular_start,
                prior_regular_end,
                timeframe='1min'
            )
            prior_regular_vol = prior_regular_df['volume'].sum() if not prior_regular_df.empty else 0
            
            # Get current price (last price at 12:00 UTC)
            if not current_overnight_df.empty:
                current_price = current_overnight_df['close'].iloc[-1]
            else:
                current_price = 0
            
            return {
                'current_overnight_volume': current_overnight_vol,
                'prior_overnight_volume': prior_overnight_vol,
                'prior_regular_volume': prior_regular_vol,
                'current_price': current_price
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch overnight volumes for {ticker}: {e}")
            return {
                'current_overnight_volume': 0,
                'prior_overnight_volume': 0,
                'prior_regular_volume': 0,
                'current_price': 0
            }