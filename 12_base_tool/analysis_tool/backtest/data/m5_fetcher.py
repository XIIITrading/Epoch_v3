"""
================================================================================
EPOCH TRADING SYSTEM - M5 BAR DATA FETCHER (v2 - Extended Premarket)
Backtest Module - Polygon API Integration
XIII Trading LLC
================================================================================

UPDATED v2: Fetches from prior trading day 16:00 to ensure sufficient bars
for SMA21 calculation at market open.

Previous issue: CRM only had 93 bars starting at 04:55 AM trade day.
At 09:30 (index 15), there weren't enough bars for SMA21.

Fix: Fetch from prior day 16:00 (after-hours) through current day.
This provides 100+ bars before RTH open, ensuring all indicators work.

================================================================================
"""

import requests
import time as time_module
from datetime import datetime, date, time, timedelta
from dataclasses import dataclass
from typing import List, Optional
import pytz


@dataclass
class M5Bar:
    """Single M5 bar data structure."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    vwap: Optional[float] = None
    transactions: Optional[int] = None


class M5Fetcher:
    """
    Fetches M5 bar data from Polygon.io API.
    
    v2: Extended premarket fetch from prior trading day 16:00.
    """
    
    BASE_URL = "https://api.polygon.io"
    EASTERN = pytz.timezone('America/New_York')
    
    # Minimum bars needed before RTH for indicators
    MIN_PREMARKET_BARS = 50  # Enough for SMA21 + buffer
    
    def __init__(self, api_key: str, rate_limit_delay: float = 0.25):
        """
        Initialize the fetcher.
        
        Args:
            api_key: Polygon API key
            rate_limit_delay: Delay between API calls (seconds)
        """
        self.api_key = api_key
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0
    
    def _rate_limit(self):
        """Enforce rate limiting between API calls."""
        elapsed = time_module.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time_module.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time_module.time()
    
    def _get_prior_trading_day(self, trade_date: date) -> date:
        """
        Get the prior trading day (skip weekends).
        
        Args:
            trade_date: The reference trading date
            
        Returns:
            Prior trading day (Friday if trade_date is Monday)
        """
        prior = trade_date - timedelta(days=1)
        
        # Skip weekends
        while prior.weekday() >= 5:  # Saturday = 5, Sunday = 6
            prior -= timedelta(days=1)
        
        return prior
    
    def _parse_date(self, date_input) -> date:
        """Parse various date formats to date object."""
        if isinstance(date_input, date):
            return date_input
        if isinstance(date_input, datetime):
            return date_input.date()
        if isinstance(date_input, str):
            # Handle YYYY-MM-DD format
            if '-' in date_input:
                return datetime.strptime(date_input[:10], '%Y-%m-%d').date()
            # Handle MM/DD/YYYY format
            elif '/' in date_input:
                parts = date_input.split('/')
                if len(parts[2]) == 4:
                    return datetime.strptime(date_input, '%m/%d/%Y').date()
                else:
                    return datetime.strptime(date_input, '%m/%d/%y').date()
        raise ValueError(f"Cannot parse date: {date_input}")
    
    def fetch_bars(self, 
                   ticker: str, 
                   from_date: str, 
                   to_date: str,
                   from_time: str = "00:00",
                   to_time: str = "23:59") -> List[M5Bar]:
        """
        Fetch M5 bars from Polygon API.
        
        Args:
            ticker: Stock symbol
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            from_time: Start time (HH:MM)
            to_time: End time (HH:MM)
            
        Returns:
            List of M5Bar objects
        """
        url = f"{self.BASE_URL}/v2/aggs/ticker/{ticker}/range/5/minute/{from_date}/{to_date}"
        
        params = {
            'apiKey': self.api_key,
            'adjusted': 'true',
            'sort': 'asc',
            'limit': 50000
        }
        
        try:
            self._rate_limit()
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code != 200:
                print(f"  API error: {response.status_code}")
                return []
            
            data = response.json()
            
            if data.get('status') not in ['OK', 'DELAYED']:
                print(f"  API status: {data.get('status')}")
                return []
            
            if 'results' not in data or not data['results']:
                return []
            
            bars = []
            for result in data['results']:
                # Convert timestamp from milliseconds to datetime
                ts = datetime.fromtimestamp(result['t'] / 1000, tz=self.EASTERN)
                
                bar = M5Bar(
                    timestamp=ts,
                    open=result['o'],
                    high=result['h'],
                    low=result['l'],
                    close=result['c'],
                    volume=int(result['v']),
                    vwap=result.get('vw'),
                    transactions=result.get('n')
                )
                bars.append(bar)
            
            return bars
            
        except Exception as e:
            print(f"  Fetch error: {e}")
            return []
    
    def fetch_bars_extended(self, 
                            ticker: str, 
                            trade_date: str,
                            include_premarket: bool = True,
                            include_afterhours: bool = True) -> List[M5Bar]:
        """
        Fetch M5 bars with extended hours, starting from prior day 16:00.
        
        This ensures sufficient bars for SMA21 calculation at market open.
        
        Args:
            ticker: Stock symbol
            trade_date: Trading date (YYYY-MM-DD or date object)
            include_premarket: Include premarket (04:00-09:30)
            include_afterhours: Include after-hours (16:00-20:00)
            
        Returns:
            List of M5Bar objects with extended coverage
        """
        trade_dt = self._parse_date(trade_date)
        
        # =====================================================================
        # FIX: Start from prior trading day 16:00 for sufficient indicator bars
        # =====================================================================
        prior_day = self._get_prior_trading_day(trade_dt)
        
        # Fetch from prior day 16:00 to trade day end
        from_date = prior_day.strftime('%Y-%m-%d')
        to_date = trade_dt.strftime('%Y-%m-%d')
        
        # Fetch all bars in date range
        all_bars = self.fetch_bars(ticker, from_date, to_date)
        
        if not all_bars:
            print(f"  No bars fetched for {ticker}")
            return []
        
        # Filter based on time criteria
        filtered_bars = []
        
        for bar in all_bars:
            bar_date = bar.timestamp.date()
            bar_time = bar.timestamp.time()
            
            # Prior day: only include after-hours (16:00-20:00)
            if bar_date == prior_day:
                if time(16, 0) <= bar_time <= time(20, 0):
                    filtered_bars.append(bar)
            
            # Trade day: include based on flags
            elif bar_date == trade_dt:
                # Regular trading hours always included (09:30-16:00)
                if time(9, 30) <= bar_time <= time(16, 0):
                    filtered_bars.append(bar)
                # Premarket (04:00-09:30)
                elif include_premarket and time(4, 0) <= bar_time < time(9, 30):
                    filtered_bars.append(bar)
                # After-hours (16:00-20:00)
                elif include_afterhours and time(16, 0) < bar_time <= time(20, 0):
                    filtered_bars.append(bar)
        
        # Sort by timestamp
        filtered_bars.sort(key=lambda x: x.timestamp)
        
        # Log coverage
        if filtered_bars:
            first_ts = filtered_bars[0].timestamp
            last_ts = filtered_bars[-1].timestamp
            
            # Count premarket bars (before 09:30 on trade day)
            premarket_count = sum(
                1 for b in filtered_bars 
                if b.timestamp.date() == trade_dt and b.timestamp.time() < time(9, 30)
            )
            prior_day_count = sum(
                1 for b in filtered_bars 
                if b.timestamp.date() == prior_day
            )
            
            print(f"  Fetched {len(filtered_bars)} M5 bars for {ticker} on {trade_date} (extended hours)")
            
            if prior_day_count > 0 or premarket_count < self.MIN_PREMARKET_BARS:
                print(f"    Prior day AH: {prior_day_count} bars, Trade day premarket: {premarket_count} bars")
        
        return filtered_bars
    
    def fetch_rth_only(self, ticker: str, trade_date: str) -> List[M5Bar]:
        """
        Fetch only regular trading hours (09:30-16:00).
        
        Args:
            ticker: Stock symbol
            trade_date: Trading date (YYYY-MM-DD)
            
        Returns:
            List of M5Bar objects for RTH only
        """
        trade_dt = self._parse_date(trade_date)
        date_str = trade_dt.strftime('%Y-%m-%d')
        
        all_bars = self.fetch_bars(ticker, date_str, date_str)
        
        # Filter to RTH only
        rth_bars = [
            bar for bar in all_bars
            if time(9, 30) <= bar.timestamp.time() <= time(16, 0)
        ]
        
        return rth_bars
    
    def get_bar_at_time(self, bars: List[M5Bar], target_time: time) -> Optional[M5Bar]:
        """
        Find the bar at or just before a specific time.
        
        Args:
            bars: List of M5Bar objects
            target_time: Target time to find
            
        Returns:
            M5Bar at or just before target_time, or None
        """
        if not bars:
            return None
        
        # Find bar matching or just before target time
        matching_bar = None
        for bar in bars:
            bar_time = bar.timestamp.time()
            if bar_time <= target_time:
                matching_bar = bar
            else:
                break
        
        return matching_bar


# =============================================================================
# STANDALONE TEST
# =============================================================================

if __name__ == "__main__":
    print("M5 Fetcher v2 - Extended Premarket Coverage")
    print("=" * 60)
    print("\nFixes SMA21=None error by fetching from prior day 16:00")
    print("\nCoverage:")
    print("  Prior day 16:00-20:00: ~48 bars (after-hours)")
    print("  Trade day 04:00-09:30: ~66 bars (premarket)")
    print("  Total before RTH:      100+ bars")
    print("\nThis ensures SMA21 (needs 21 bars) works at 09:30 open.")
    print("\nUsage:")
    print("  from m5_fetcher import M5Fetcher")
    print("  fetcher = M5Fetcher(api_key='your_key')")
    print("  bars = fetcher.fetch_bars_extended('CRM', '2025-12-19')")
    print("  print(f'Fetched {len(bars)} bars')")