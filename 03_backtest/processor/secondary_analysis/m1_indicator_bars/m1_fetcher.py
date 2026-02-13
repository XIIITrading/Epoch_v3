"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
M1 (1-Minute) Bar Data Fetcher
XIII Trading LLC
================================================================================

Fetches 1-minute bar data from Polygon.io API for M1 indicator calculation.
Independent implementation for m1_indicator_bars module.

Key Features:
- Fetches M1 bars directly from Polygon
- Extended fetch: From 08:00 ET for indicator calculation at market open
- Full trading day: 08:00 to 16:00 ET (~480 bars per ticker-date)
- Caching by ticker-date for efficient batch processing

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

# Use explicit path imports to avoid collisions with 03_indicators modules
import importlib.util
from pathlib import Path

_MODULE_DIR = Path(__file__).resolve().parent

# Load local config
_config_spec = importlib.util.spec_from_file_location("local_config", _MODULE_DIR / "config.py")
_config = importlib.util.module_from_spec(_config_spec)
_config_spec.loader.exec_module(_config)

POLYGON_API_KEY = _config.POLYGON_API_KEY
POLYGON_BASE_URL = _config.POLYGON_BASE_URL
API_DELAY = _config.API_DELAY
API_RETRIES = _config.API_RETRIES
API_RETRY_DELAY = _config.API_RETRY_DELAY
PREMARKET_START = _config.PREMARKET_START
MARKET_OPEN = _config.MARKET_OPEN
MARKET_CLOSE = _config.MARKET_CLOSE
PRIOR_DAY_START = _config.PRIOR_DAY_START


@dataclass
class M1Bar:
    """Single 1-minute bar data structure."""
    timestamp: datetime
    bar_date: date
    bar_time: time
    open: float
    high: float
    low: float
    close: float
    volume: int
    vwap: Optional[float] = None
    transactions: Optional[int] = None


class M1Fetcher:
    """
    Fetches 1-minute bar data from Polygon.io API.

    Designed for M1 indicator bars calculation where we need full trading day
    data starting from pre-market for indicator calculation.
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
        self._cache: Dict[str, pd.DataFrame] = {}  # Cache: {ticker_date: DataFrame}

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
            if '-' in date_input:
                return datetime.strptime(date_input[:10], '%Y-%m-%d').date()
            elif '/' in date_input:
                parts = date_input.split('/')
                if len(parts[2]) == 4:
                    return datetime.strptime(date_input, '%m/%d/%Y').date()
                else:
                    return datetime.strptime(date_input, '%m/%d/%y').date()
        raise ValueError(f"Cannot parse date: {date_input}")

    def _get_prior_trading_day(self, trade_date: date) -> date:
        """Get the prior trading day (skip weekends)."""
        prior = trade_date - timedelta(days=1)
        while prior.weekday() >= 5:  # Saturday = 5, Sunday = 6
            prior -= timedelta(days=1)
        return prior

    def _convert_polygon_timestamp(self, ts_ms: int) -> datetime:
        """
        Convert Polygon millisecond timestamp to ET datetime.

        Polygon returns timestamps in milliseconds since Unix epoch (UTC).
        We convert to Eastern Time for consistency.
        """
        utc_dt = datetime.utcfromtimestamp(ts_ms / 1000).replace(tzinfo=self.UTC)
        return utc_dt.astimezone(self.ET)

    def _get_cache_key(self, ticker: str, trade_date: date, extended: bool = False) -> str:
        """Generate cache key for ticker-date combination."""
        suffix = "_extended" if extended else ""
        return f"{ticker}_{trade_date.strftime('%Y%m%d')}{suffix}"

    def fetch_bars_raw(
        self,
        ticker: str,
        from_date: str,
        to_date: str
    ) -> List[M1Bar]:
        """
        Fetch 1-minute bars from Polygon API.

        Args:
            ticker: Stock symbol
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)

        Returns:
            List of M1Bar objects
        """
        url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/1/minute/{from_date}/{to_date}"

        params = {
            'apiKey': self.api_key,
            'adjusted': 'true',
            'sort': 'asc',
            'limit': 50000
        }

        for attempt in range(API_RETRIES):
            try:
                self._rate_limit()
                response = requests.get(url, params=params, timeout=30)

                if response.status_code == 429:  # Rate limited
                    wait_time = API_RETRY_DELAY * (attempt + 1)
                    print(f"  Rate limited, waiting {wait_time}s...")
                    time_module.sleep(wait_time)
                    continue

                if response.status_code != 200:
                    print(f"  API error: {response.status_code} - {response.text[:100]}")
                    return []

                data = response.json()

                if data.get('status') not in ['OK', 'DELAYED']:
                    print(f"  API status: {data.get('status')}")
                    return []

                if 'results' not in data or not data['results']:
                    return []

                bars = []
                for result in data['results']:
                    ts = self._convert_polygon_timestamp(result['t'])

                    bar = M1Bar(
                        timestamp=ts,
                        bar_date=ts.date(),
                        bar_time=ts.time(),
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

            except requests.exceptions.Timeout:
                print(f"  Timeout on attempt {attempt + 1}, retrying...")
                time_module.sleep(API_RETRY_DELAY)
            except Exception as e:
                print(f"  Fetch error: {e}")
                return []

        return []

    def fetch_trading_day(
        self,
        ticker: str,
        trade_date,
        start_time: time = None,
        end_time: time = None
    ) -> pd.DataFrame:
        """
        Fetch 1-minute bars for a trading day, with optional time filtering.

        Args:
            ticker: Stock symbol
            trade_date: Trading date (various formats accepted)
            start_time: Optional start time filter (ET), defaults to PREMARKET_START (08:00)
            end_time: Optional end time filter (ET), defaults to MARKET_CLOSE (16:00)

        Returns:
            DataFrame with columns: timestamp, bar_date, bar_time, open, high, low, close, volume, vwap
        """
        trade_dt = self._parse_date(trade_date)
        cache_key = self._get_cache_key(ticker, trade_dt)

        # Default time range: 08:00 to 16:00
        start_time = start_time or PREMARKET_START
        end_time = end_time or MARKET_CLOSE

        # Check cache first
        if cache_key in self._cache:
            df = self._cache[cache_key].copy()
        else:
            # Fetch from API
            date_str = trade_dt.strftime('%Y-%m-%d')
            bars = self.fetch_bars_raw(ticker, date_str, date_str)

            if not bars:
                return pd.DataFrame()

            # Convert to DataFrame
            df = pd.DataFrame([
                {
                    'timestamp': bar.timestamp,
                    'bar_date': bar.bar_date,
                    'bar_time': bar.bar_time,
                    'open': bar.open,
                    'high': bar.high,
                    'low': bar.low,
                    'close': bar.close,
                    'volume': bar.volume,
                    'vwap': bar.vwap
                }
                for bar in bars
            ])

            # Filter to extended trading hours (08:00 - 16:00) for cache
            df = df[(df['bar_time'] >= PREMARKET_START) & (df['bar_time'] <= MARKET_CLOSE)]
            df = df.sort_values('timestamp').reset_index(drop=True)

            # Cache the result
            self._cache[cache_key] = df.copy()

        # Apply time filters if specified
        df = df.copy()
        df = df[(df['bar_time'] >= start_time) & (df['bar_time'] <= end_time)]
        df = df.reset_index(drop=True)

        return df

    def fetch_extended_trading_day(
        self,
        ticker: str,
        trade_date
    ) -> pd.DataFrame:
        """
        Fetch 1-minute bars with extended lookback from prior day 16:00.

        This ensures sufficient bars for SMA21 calculation at market open.

        Args:
            ticker: Stock symbol
            trade_date: Trading date

        Returns:
            DataFrame with M1 bars from prior day 16:00 through trade day 16:00
        """
        trade_dt = self._parse_date(trade_date)
        prior_day = self._get_prior_trading_day(trade_dt)
        cache_key = self._get_cache_key(ticker, trade_dt, extended=True)

        # Check cache first
        if cache_key in self._cache:
            return self._cache[cache_key].copy()

        # Fetch from API - prior day through trade day
        from_date = prior_day.strftime('%Y-%m-%d')
        to_date = trade_dt.strftime('%Y-%m-%d')

        bars = self.fetch_bars_raw(ticker, from_date, to_date)

        if not bars:
            return pd.DataFrame()

        # Convert to DataFrame
        df = pd.DataFrame([
            {
                'timestamp': bar.timestamp,
                'bar_date': bar.bar_date,
                'bar_time': bar.bar_time,
                'open': bar.open,
                'high': bar.high,
                'low': bar.low,
                'close': bar.close,
                'volume': bar.volume,
                'vwap': bar.vwap
            }
            for bar in bars
        ])

        # Filter to relevant time windows:
        # Prior day: 16:00 onwards (after-hours)
        # Trade day: 08:00 to 16:00 (pre-market + regular hours)
        filtered_rows = []
        for _, row in df.iterrows():
            bar_date = row['bar_date']
            bar_time = row['bar_time']

            if bar_date == prior_day and bar_time >= PRIOR_DAY_START:
                filtered_rows.append(row)
            elif bar_date == trade_dt and PREMARKET_START <= bar_time <= MARKET_CLOSE:
                filtered_rows.append(row)

        if not filtered_rows:
            return pd.DataFrame()

        result_df = pd.DataFrame(filtered_rows)
        result_df = result_df.sort_values('timestamp').reset_index(drop=True)

        # Cache the result
        self._cache[cache_key] = result_df.copy()

        return result_df

    def fetch_bars_before_time(
        self,
        ticker: str,
        trade_date,
        before_time: time,
        num_bars: int = None
    ) -> pd.DataFrame:
        """
        Get M1 bars up to (but not including) a specific time.

        Uses extended bar fetching from prior day 16:00 to ensure sufficient
        bars for indicator calculation even for early morning entries.

        Args:
            ticker: Stock symbol
            trade_date: Trading date
            before_time: Get bars strictly before this time
            num_bars: Optional limit on number of bars to return (most recent N)

        Returns:
            DataFrame of M1 bars sorted by time
        """
        trade_dt = self._parse_date(trade_date)

        # Get extended bars
        df = self.fetch_extended_trading_day(ticker, trade_dt)

        if df.empty:
            return df

        # Filter to bars before the specified time on trade day
        # Include all prior day bars + trade day bars before entry
        filtered_rows = []
        for _, row in df.iterrows():
            bar_date = row['bar_date']
            bar_time = row['bar_time']

            # Include all bars from prior day
            if bar_date < trade_dt:
                filtered_rows.append(row)
            # Include trade day bars before entry time
            elif bar_date == trade_dt and bar_time < before_time:
                filtered_rows.append(row)

        if not filtered_rows:
            return pd.DataFrame()

        result_df = pd.DataFrame(filtered_rows).reset_index(drop=True)

        # Optionally limit to most recent N bars
        if num_bars is not None and len(result_df) > num_bars:
            result_df = result_df.tail(num_bars).reset_index(drop=True)

        return result_df

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
    print("M1 Fetcher - 1-Minute Bar Data for M1 Indicator Bars")
    print("=" * 60)

    fetcher = M1Fetcher()

    # Test fetch for a specific date
    test_ticker = "SPY"
    test_date = "2025-12-30"

    print(f"\nFetching 1-minute bars for {test_ticker} on {test_date}...")
    df = fetcher.fetch_trading_day(test_ticker, test_date)

    if not df.empty:
        print(f"  Fetched {len(df)} bars")
        print(f"  First bar: {df.iloc[0]['timestamp']}")
        print(f"  Last bar: {df.iloc[-1]['timestamp']}")
        print(f"  High of day: ${df['high'].max():.2f}")
        print(f"  Low of day: ${df['low'].min():.2f}")

        # Test extended fetch
        print("\nFetching extended bars (includes prior day 16:00+)...")
        df_extended = fetcher.fetch_extended_trading_day(test_ticker, test_date)
        print(f"  Extended: {len(df_extended)} bars")
        if not df_extended.empty:
            print(f"  First bar: {df_extended.iloc[0]['timestamp']}")

        # Check cache
        stats = fetcher.get_cache_stats()
        print(f"\nCache stats: {stats}")
    else:
        print("  No data returned (may be holiday or weekend)")

    print("\nUsage:")
    print("  from m1_fetcher import M1Fetcher")
    print("  fetcher = M1Fetcher()")
    print("  df = fetcher.fetch_extended_trading_day('SPY', '2025-12-30')")
