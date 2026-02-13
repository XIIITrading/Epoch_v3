"""
Polygon Data Fetcher - Epoch Ticker Structure Module
Epoch Trading System v1 - XIII Trading LLC

Fetches OHLC bar data from Polygon.io API for user-defined tickers.
"""

import requests
import pandas as pd
import time
from datetime import datetime, timedelta
from typing import Dict, Optional
import epoch_ticker_structure_config as config


class PolygonDataFetcher:
    """
    Fetches and processes market data from Polygon.io API.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Polygon data fetcher.
        
        Args:
            api_key: Polygon API key (uses config if not provided)
        """
        self.api_key = api_key or config.POLYGON_API_KEY
        self.base_url = config.POLYGON_BASE_URL
        self.last_request_time = 0
        
        if config.VERBOSE:
            print(f"   ✓ Polygon Data Fetcher initialized")
    
    def _rate_limit(self):
        """Enforce rate limiting between API calls."""
        elapsed = time.time() - self.last_request_time
        if elapsed < config.API_RATE_LIMIT_DELAY:
            time.sleep(config.API_RATE_LIMIT_DELAY - elapsed)
        self.last_request_time = time.time()
    
    def _make_request(self, url: str, params: Dict) -> Optional[Dict]:
        """
        Make API request with retry logic.
        
        Args:
            url: API endpoint URL
            params: Query parameters
        
        Returns:
            JSON response data or None if failed
        """
        params['apiKey'] = self.api_key
        
        for attempt in range(config.API_MAX_RETRIES):
            try:
                self._rate_limit()
                response = requests.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') in ['OK', 'DELAYED']:
                        return data
                    else:
                        if config.VERBOSE:
                            print(f"   ⚠️  API returned invalid status: {data.get('status')}")
                        return None
                
                elif response.status_code == 429:
                    # Rate limit hit
                    if config.VERBOSE:
                        print(f"   ⚠️  Rate limit hit, waiting {config.API_RETRY_DELAY}s...")
                    time.sleep(config.API_RETRY_DELAY)
                    continue
                
                else:
                    if config.VERBOSE:
                        print(f"   ⚠️  API request failed: {response.status_code}")
                    if attempt < config.API_MAX_RETRIES - 1:
                        time.sleep(config.API_RETRY_DELAY)
                        continue
                    return None
            
            except requests.exceptions.RequestException as e:
                if config.VERBOSE:
                    print(f"   ⚠️  Request exception: {e}")
                if attempt < config.API_MAX_RETRIES - 1:
                    time.sleep(config.API_RETRY_DELAY)
                    continue
                return None
        
        return None
    
    def fetch_bars(self, 
                   ticker: str, 
                   timeframe: str,
                   from_date: str,
                   to_date: str) -> Optional[pd.DataFrame]:
        """
        Fetch OHLC bars from Polygon API.
        
        Args:
            ticker: Stock symbol (e.g., 'AMD')
            timeframe: Timeframe code from config (e.g., 'D1', 'H1')
            from_date: Start date (YYYY-MM-DD format)
            to_date: End date (YYYY-MM-DD format)
        
        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
            Returns None if fetch fails
        """
        if timeframe not in config.TIMEFRAMES:
            print(f"   ⚠️  Invalid timeframe: {timeframe}")
            return None
        
        tf_config = config.TIMEFRAMES[timeframe]
        multiplier = tf_config['polygon_multiplier']
        timespan = tf_config['polygon_timespan']
        
        # Build API URL
        url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from_date}/{to_date}"
        
        params = {
            'adjusted': 'true',
            'sort': 'asc',
            'limit': 50000
        }
        
        # Make request
        data = self._make_request(url, params)
        
        if not data or 'results' not in data:
            return None
        
        # Convert to DataFrame
        results = data['results']
        df = pd.DataFrame(results)
        
        if df.empty:
            return None
        
        # Rename columns to match expected format
        column_map = {
            't': 'timestamp',
            'o': 'open',
            'h': 'high',
            'l': 'low',
            'c': 'close',
            'v': 'volume'
        }
        df = df.rename(columns=column_map)
        
        # Convert timestamp from milliseconds to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Select and order columns
        columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        df = df[columns]
        
        # Sort by timestamp
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        return df
    
    def fetch_bars_for_structure(self, 
                                  ticker: str, 
                                  timeframe: str) -> Optional[pd.DataFrame]:
        """
        Fetch sufficient bars for market structure calculation.
        
        Args:
            ticker: Stock symbol
            timeframe: Timeframe code from config
        
        Returns:
            DataFrame with OHLC bars or None if failed
        """
        if timeframe not in config.DATA_LOOKBACK_DAYS:
            print(f"   ⚠️  Timeframe {timeframe} not configured")
            return None
        
        # Calculate date range
        to_date = datetime.now()
        lookback_days = config.DATA_LOOKBACK_DAYS[timeframe]
        from_date = to_date - timedelta(days=lookback_days)
        
        # Format dates for API
        from_str = from_date.strftime('%Y-%m-%d')
        to_str = to_date.strftime('%Y-%m-%d')
        
        # Fetch bars
        df = self.fetch_bars(ticker, timeframe, from_str, to_str)
        
        if df is None:
            return None
        
        # Validate minimum bars
        tf_config = config.TIMEFRAMES[timeframe]
        min_bars = tf_config['bars_needed']
        
        if len(df) < min_bars:
            if config.VERBOSE:
                print(f"   ⚠️  Insufficient bars for {ticker} {timeframe}: {len(df)} < {min_bars}")
            return None
        
        return df