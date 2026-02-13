"""
DOW AI - Polygon Data Fetcher
Epoch Trading System v1 - XIII Trading LLC

Fetches OHLC bar data from Polygon.io API for live and historical analysis.
"""
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import time
import pytz
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    POLYGON_API_KEY,
    POLYGON_BASE_URL,
    API_RATE_LIMIT_DELAY,
    API_MAX_RETRIES,
    API_RETRY_DELAY,
    TIMEFRAMES,
    DATA_LOOKBACK,
    TIMEZONE,
    VERBOSE,
    debug_print
)


class PolygonFetcher:
    """
    Fetches bar data from Polygon.io API.
    Supports both live and historical (backtest) data fetching.
    """

    def __init__(self, api_key: str = None, verbose: bool = None):
        """
        Initialize Polygon data fetcher.

        Args:
            api_key: Polygon API key (uses config if not provided)
            verbose: Enable verbose output (uses config if not provided)
        """
        self.api_key = api_key or POLYGON_API_KEY
        self.base_url = POLYGON_BASE_URL
        self.tz = pytz.timezone(TIMEZONE)
        self._last_request_time = 0
        self.verbose = verbose if verbose is not None else VERBOSE

        if self.verbose:
            debug_print("PolygonFetcher initialized")

    def _rate_limit(self):
        """Enforce rate limiting between API calls."""
        elapsed = time.time() - self._last_request_time
        if elapsed < API_RATE_LIMIT_DELAY:
            time.sleep(API_RATE_LIMIT_DELAY - elapsed)
        self._last_request_time = time.time()

    def _make_request(self, url: str, params: dict) -> Optional[dict]:
        """
        Make API request with retry logic.

        Args:
            url: API endpoint URL
            params: Query parameters

        Returns:
            JSON response data or None if failed
        """
        params['apiKey'] = self.api_key

        for attempt in range(API_MAX_RETRIES):
            try:
                self._rate_limit()
                response = requests.get(url, params=params, timeout=30)

                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') in ['OK', 'DELAYED']:
                        return data
                    else:
                        if self.verbose:
                            debug_print(f"API returned invalid status: {data.get('status')}")
                        return None

                elif response.status_code == 429:
                    # Rate limit hit
                    if self.verbose:
                        debug_print(f"Rate limit hit, waiting {API_RETRY_DELAY}s...")
                    time.sleep(API_RETRY_DELAY * (attempt + 1))
                    continue

                else:
                    if self.verbose:
                        debug_print(f"API error: {response.status_code} - {response.text[:200]}")
                    if attempt < API_MAX_RETRIES - 1:
                        time.sleep(API_RETRY_DELAY)
                        continue
                    return None

            except requests.exceptions.RequestException as e:
                if self.verbose:
                    debug_print(f"Request exception: {e}")
                if attempt < API_MAX_RETRIES - 1:
                    time.sleep(API_RETRY_DELAY)
                    continue
                return None

        return None

    def fetch_bars(
        self,
        ticker: str,
        timeframe: str,
        end_datetime: Optional[datetime] = None,
        bars_needed: int = None
    ) -> Optional[pd.DataFrame]:
        """
        Fetch bar data for a ticker and timeframe.

        Args:
            ticker: Stock symbol (e.g., 'TSLA')
            timeframe: One of 'M1', 'M5', 'M15', 'H1', 'H4'
            end_datetime: End time for data (None = now)
            bars_needed: Number of bars to fetch (uses config default if None)

        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
            Returns None if fetch fails
        """
        # Get timeframe config
        if timeframe not in TIMEFRAMES:
            if self.verbose:
                debug_print(f"Unknown timeframe: {timeframe}")
            return None

        tf_config = TIMEFRAMES[timeframe]
        multiplier = tf_config['multiplier']
        timespan = tf_config['timespan']
        bars_needed = bars_needed or tf_config['bars_needed']

        # Calculate date range
        if end_datetime is None:
            end_datetime = datetime.now(self.tz)
        elif end_datetime.tzinfo is None:
            end_datetime = self.tz.localize(end_datetime)

        lookback_days = DATA_LOOKBACK.get(timeframe, 30)
        start_datetime = end_datetime - timedelta(days=lookback_days)

        # Format dates for API
        from_date = start_datetime.strftime('%Y-%m-%d')
        to_date = end_datetime.strftime('%Y-%m-%d')

        if self.verbose:
            debug_print(f"Fetching {ticker} {timeframe}: {from_date} to {to_date}")

        # Build URL
        url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from_date}/{to_date}"

        params = {
            'adjusted': 'true',
            'sort': 'asc',
            'limit': 50000
        }

        # Make request
        data = self._make_request(url, params)

        if not data or 'results' not in data:
            if self.verbose:
                debug_print(f"No data returned for {ticker} {timeframe}")
            return None

        # Convert to DataFrame
        df = pd.DataFrame(data['results'])

        if df.empty:
            return None

        # Rename columns to match expected format
        df = df.rename(columns={
            't': 'timestamp',
            'o': 'open',
            'h': 'high',
            'l': 'low',
            'c': 'close',
            'v': 'volume'
        })

        # Convert timestamp from milliseconds to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
        df['timestamp'] = df['timestamp'].dt.tz_convert(TIMEZONE)

        # Filter to bars before end_datetime (for backtesting)
        if end_datetime:
            end_dt_aware = end_datetime if end_datetime.tzinfo else self.tz.localize(end_datetime)
            df = df[df['timestamp'] <= end_dt_aware]

        # Select only needed columns
        columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        df = df[columns]

        # Return most recent bars_needed
        df = df.tail(bars_needed).reset_index(drop=True)

        if self.verbose:
            debug_print(f"Fetched {len(df)} bars for {ticker} {timeframe}")

        return df

    def fetch_multi_timeframe(
        self,
        ticker: str,
        timeframes: List[str] = None,
        end_datetime: Optional[datetime] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for multiple timeframes.

        Args:
            ticker: Stock symbol
            timeframes: List of timeframe codes (default: all)
            end_datetime: End time for data (None = now)

        Returns:
            Dict mapping timeframe -> DataFrame
        """
        if timeframes is None:
            timeframes = ['M1', 'M5', 'M15', 'H1', 'H4']

        results = {}
        for tf in timeframes:
            df = self.fetch_bars(ticker, tf, end_datetime)
            if df is not None and not df.empty:
                results[tf] = df

        if self.verbose:
            debug_print(f"Fetched {len(results)} timeframes for {ticker}")

        return results

    def get_current_price(
        self,
        ticker: str,
        at_datetime: Optional[datetime] = None
    ) -> Optional[float]:
        """
        Get the current (or historical) price.

        For live: returns last M1 close
        For backtest: returns M1 close at specified datetime

        Args:
            ticker: Stock symbol
            at_datetime: Specific datetime (None = now)

        Returns:
            Current price or None if unavailable
        """
        df = self.fetch_bars(ticker, 'M1', at_datetime, bars_needed=5)
        if df is not None and not df.empty:
            return float(df.iloc[-1]['close'])
        return None


# =============================================================================
# STANDALONE TEST
# =============================================================================
if __name__ == '__main__':
    print("=" * 60)
    print("POLYGON FETCHER - STANDALONE TEST")
    print("=" * 60)

    fetcher = PolygonFetcher(verbose=True)

    # Test 1: Fetch M5 bars for TSLA
    print("\n[TEST 1] Fetching M5 bars for TSLA...")
    df = fetcher.fetch_bars('TSLA', 'M5')
    if df is not None:
        print(f"  SUCCESS: Got {len(df)} bars")
        print(f"  First bar: {df.iloc[0]['timestamp']}")
        print(f"  Last bar:  {df.iloc[-1]['timestamp']}")
        print(f"  Last close: ${df.iloc[-1]['close']:.2f}")
    else:
        print("  FAILED: No data returned")

    # Test 2: Fetch multiple timeframes
    print("\n[TEST 2] Fetching multi-timeframe for SPY...")
    data = fetcher.fetch_multi_timeframe('SPY', ['M5', 'M15', 'H1'])
    for tf, df in data.items():
        print(f"  {tf}: {len(df)} bars, last close ${df.iloc[-1]['close']:.2f}")

    # Test 3: Get current price
    print("\n[TEST 3] Getting current price for AAPL...")
    price = fetcher.get_current_price('AAPL')
    if price:
        print(f"  SUCCESS: AAPL current price: ${price:.2f}")
    else:
        print("  FAILED: Could not get price")

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
