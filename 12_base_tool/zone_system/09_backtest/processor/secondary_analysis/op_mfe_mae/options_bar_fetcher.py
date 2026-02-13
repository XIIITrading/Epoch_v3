"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
Options 1-Minute Bar Data Fetcher
XIII Trading LLC
================================================================================

Fetches 1-minute bar data for OPTIONS contracts from Polygon.io API.
This mirrors m1_fetcher.py pattern but for options tickers.

Key Differences from Stock Fetcher:
- Uses options ticker format (O:SYMBOL...)
- Options may have lower volume = fewer bars
- Handles O: prefix automatically

Version: 1.0.0
================================================================================
"""

import requests
import time as time_module
from datetime import datetime, date, time, timedelta
from dataclasses import dataclass
from typing import List, Optional, Dict
import pytz
import pandas as pd

from config import (
    POLYGON_API_KEY,
    POLYGON_BASE_URL,
    API_DELAY,
    API_RETRIES,
    API_RETRY_DELAY,
    REQUEST_TIMEOUT,
    BAR_MULTIPLIER,
    BAR_TIMESPAN
)


@dataclass
class OptionsBar:
    """Single 1-minute options bar data structure."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    vwap: Optional[float] = None
    transactions: Optional[int] = None


class OptionsBarFetcher:
    """
    Fetches 1-minute bar data for OPTIONS contracts from Polygon.io API.

    Designed for options MFE/MAE potential calculation where we need granular
    price data from entry time to end-of-day (15:30 ET).

    Usage:
        fetcher = OptionsBarFetcher()
        df = fetcher.fetch_trading_day("O:AAPL250117C00175000", "2025-12-18")
    """

    ET = pytz.timezone('America/New_York')
    UTC = pytz.UTC

    def __init__(self, api_key: str = None, rate_limit_delay: float = None):
        """
        Initialize the fetcher.

        Args:
            api_key: Polygon API key (defaults to config value)
            rate_limit_delay: Delay between API calls in seconds (defaults to config)
        """
        self.api_key = api_key or POLYGON_API_KEY
        self.base_url = POLYGON_BASE_URL
        self.rate_limit_delay = rate_limit_delay if rate_limit_delay is not None else API_DELAY
        self.last_request_time = 0
        self._cache: Dict[str, pd.DataFrame] = {}  # Cache: {options_ticker_date: DataFrame}

    def _rate_limit(self):
        """Enforce rate limiting between API calls."""
        if self.rate_limit_delay > 0:
            elapsed = time_module.time() - self.last_request_time
            if elapsed < self.rate_limit_delay:
                time_module.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time_module.time()

    def _parse_date(self, date_input) -> date:
        """Parse various date formats to date object."""
        if isinstance(date_input, date) and not isinstance(date_input, datetime):
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

    def _ensure_options_prefix(self, ticker: str) -> str:
        """Ensure options ticker has O: prefix."""
        if not ticker.startswith('O:'):
            return f"O:{ticker}"
        return ticker

    def _convert_polygon_timestamp(self, ts_ms: int) -> datetime:
        """
        Convert Polygon millisecond timestamp to ET datetime.

        Polygon returns timestamps in milliseconds since Unix epoch (UTC).
        We convert to Eastern Time for consistency with trade entry times.
        """
        utc_dt = datetime.utcfromtimestamp(ts_ms / 1000).replace(tzinfo=self.UTC)
        return utc_dt.astimezone(self.ET)

    def _get_cache_key(self, options_ticker: str, trade_date: date) -> str:
        """Generate cache key for ticker-date combination."""
        return f"{options_ticker}_{trade_date.strftime('%Y%m%d')}"

    def fetch_bars_raw(self,
                       options_ticker: str,
                       from_date: str,
                       to_date: str) -> List[OptionsBar]:
        """
        Fetch 1-minute bars from Polygon API for an options contract.

        Args:
            options_ticker: Full options ticker (e.g., O:AAPL250117C00175000)
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)

        Returns:
            List of OptionsBar objects
        """
        # Ensure O: prefix
        options_ticker = self._ensure_options_prefix(options_ticker)

        url = f"{self.base_url}/v2/aggs/ticker/{options_ticker}/range/{BAR_MULTIPLIER}/{BAR_TIMESPAN}/{from_date}/{to_date}"

        params = {
            'apiKey': self.api_key,
            'adjusted': 'true',
            'sort': 'asc',
            'limit': 50000  # More than enough for one day (~390 trading minutes)
        }

        for attempt in range(API_RETRIES):
            try:
                self._rate_limit()
                response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)

                if response.status_code == 429:  # Rate limited
                    wait_time = API_RETRY_DELAY * (attempt + 1)
                    print(f"    Rate limited, waiting {wait_time}s...")
                    time_module.sleep(wait_time)
                    continue

                if response.status_code != 200:
                    print(f"    API error: {response.status_code} - {response.text[:100]}")
                    return []

                data = response.json()

                if data.get('status') not in ['OK', 'DELAYED']:
                    # No data is common for options (low liquidity)
                    if data.get('resultsCount', 0) == 0:
                        return []
                    print(f"    API status: {data.get('status')}")
                    return []

                if 'results' not in data or not data['results']:
                    return []

                bars = []
                for result in data['results']:
                    ts = self._convert_polygon_timestamp(result['t'])

                    bar = OptionsBar(
                        timestamp=ts,
                        open=result['o'],
                        high=result['h'],
                        low=result['l'],
                        close=result['c'],
                        volume=int(result.get('v', 0)),
                        vwap=result.get('vw'),
                        transactions=result.get('n')
                    )
                    bars.append(bar)

                return bars

            except requests.exceptions.Timeout:
                print(f"    Timeout on attempt {attempt + 1}, retrying...")
                time_module.sleep(API_RETRY_DELAY)
            except Exception as e:
                print(f"    Fetch error: {e}")
                return []

        return []

    def fetch_trading_day(self,
                          options_ticker: str,
                          trade_date,
                          start_time: time = None,
                          end_time: time = None) -> pd.DataFrame:
        """
        Fetch 1-minute bars for an options contract on a trading day.

        This is the primary method for MFE/MAE calculation - fetches bars
        for a single day and filters to the specified time range.

        Args:
            options_ticker: Full options ticker (e.g., O:AAPL250117C00175000)
            trade_date: Trading date (various formats accepted)
            start_time: Optional start time filter (ET)
            end_time: Optional end time filter (ET), defaults to 15:30

        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume, vwap
        """
        # Ensure O: prefix
        options_ticker = self._ensure_options_prefix(options_ticker)
        trade_dt = self._parse_date(trade_date)
        cache_key = self._get_cache_key(options_ticker, trade_dt)

        # Check cache first
        if cache_key in self._cache:
            df = self._cache[cache_key].copy()
        else:
            # Fetch from API
            date_str = trade_dt.strftime('%Y-%m-%d')
            bars = self.fetch_bars_raw(options_ticker, date_str, date_str)

            if not bars:
                return pd.DataFrame()

            # Convert to DataFrame
            df = pd.DataFrame([
                {
                    'timestamp': bar.timestamp,
                    'open': bar.open,
                    'high': bar.high,
                    'low': bar.low,
                    'close': bar.close,
                    'volume': bar.volume,
                    'vwap': bar.vwap
                }
                for bar in bars
            ])

            # Filter to regular trading hours (09:30 - 16:00) for cache
            df['time'] = df['timestamp'].apply(lambda x: x.time())
            df = df[(df['time'] >= time(9, 30)) & (df['time'] <= time(16, 0))]
            df = df.drop(columns=['time'])
            df = df.sort_values('timestamp').reset_index(drop=True)

            # Cache the result
            self._cache[cache_key] = df.copy()

        # Apply time filters if specified
        if start_time is not None or end_time is not None:
            df = df.copy()
            df['time'] = df['timestamp'].apply(lambda x: x.time())

            if start_time is not None:
                df = df[df['time'] >= start_time]
            if end_time is not None:
                df = df[df['time'] <= end_time]

            df = df.drop(columns=['time'])
            df = df.reset_index(drop=True)

        return df

    def get_bars_for_trade(self,
                           options_ticker: str,
                           trade_date,
                           entry_time: time,
                           eod_time: time = time(15, 30)) -> pd.DataFrame:
        """
        Get 1-minute bars from entry time to end-of-day for a single trade.

        This is a convenience method specifically for MFE/MAE potential calculation.

        Args:
            options_ticker: Full options ticker
            trade_date: Trading date
            entry_time: Trade entry time (ET)
            eod_time: End of day cutoff (default 15:30 ET)

        Returns:
            DataFrame of 1-minute bars from entry to EOD
        """
        return self.fetch_trading_day(
            options_ticker=options_ticker,
            trade_date=trade_date,
            start_time=entry_time,
            end_time=eod_time
        )

    def clear_cache(self):
        """Clear the bar data cache."""
        self._cache.clear()

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {
            'cached_ticker_dates': len(self._cache),
            'total_bars_cached': sum(len(df) for df in self._cache.values())
        }


# =============================================================================
# STANDALONE TEST
# =============================================================================

if __name__ == "__main__":
    print("Options Bar Fetcher - 1-Minute Bar Data for Options MFE/MAE")
    print("=" * 60)

    fetcher = OptionsBarFetcher()

    # Test with a sample options ticker
    # Using format from options_analysis: O:WDC260102C00175000
    test_ticker = "O:AAPL250117C00175000"
    test_date = "2025-01-10"

    print(f"\nFetching 1-minute bars for {test_ticker} on {test_date}...")
    df = fetcher.fetch_trading_day(test_ticker, test_date)

    if not df.empty:
        print(f"  Fetched {len(df)} bars")
        print(f"  First bar: {df.iloc[0]['timestamp']}")
        print(f"  Last bar: {df.iloc[-1]['timestamp']}")
        print(f"  High of day: ${df['high'].max():.2f}")
        print(f"  Low of day: ${df['low'].min():.2f}")

        # Test filtering from 10:00 to 15:30
        print("\nFiltering to 10:00 - 15:30...")
        df_filtered = fetcher.get_bars_for_trade(
            test_ticker,
            test_date,
            entry_time=time(10, 0),
            eod_time=time(15, 30)
        )
        print(f"  Filtered to {len(df_filtered)} bars")

        # Check cache
        stats = fetcher.get_cache_stats()
        print(f"\nCache stats: {stats}")
    else:
        print("  No data returned (options may have low liquidity or be expired)")

    print("\nUsage:")
    print("  from options_bar_fetcher import OptionsBarFetcher")
    print("  fetcher = OptionsBarFetcher()")
    print("  df = fetcher.get_bars_for_trade('O:AAPL250117C00175000', '2025-01-10', time(10, 7), time(15, 30))")
