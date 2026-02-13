"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
M5 Trade Bars - M5 Bar Fetcher
XIII Trading LLC
================================================================================

Fetches 5-minute bar data from Polygon.io API for trade-specific analysis.
Identical to m5_indicator_bars/m5_fetcher.py but self-contained for this module.

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
    MARKET_OPEN,
    MARKET_CLOSE,
    PRIOR_DAY_START
)


@dataclass
class M5Bar:
    """Single 5-minute bar data structure."""
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


class M5Fetcher:
    """
    Fetches 5-minute bar data from Polygon.io API.

    Designed for trade-specific M5 bar calculation.
    """

    ET = pytz.timezone('America/New_York')
    UTC = pytz.UTC

    def __init__(self, api_key: str = None, rate_limit_delay: float = None):
        """
        Initialize the fetcher.

        Args:
            api_key: Polygon API key (defaults to config value)
            rate_limit_delay: Delay between API calls in seconds
        """
        self.api_key = api_key or POLYGON_API_KEY
        self.base_url = POLYGON_BASE_URL
        self.rate_limit_delay = rate_limit_delay if rate_limit_delay is not None else API_DELAY
        self.last_request_time = 0
        self._cache: Dict[str, pd.DataFrame] = {}

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
        while prior.weekday() >= 5:
            prior -= timedelta(days=1)
        return prior

    def _convert_polygon_timestamp(self, ts_ms: int) -> datetime:
        """Convert Polygon millisecond timestamp to ET datetime."""
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
    ) -> List[M5Bar]:
        """
        Fetch 5-minute bars from Polygon API.

        Args:
            ticker: Stock symbol
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)

        Returns:
            List of M5Bar objects
        """
        url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/5/minute/{from_date}/{to_date}"

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

                if response.status_code == 429:
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

                    bar = M5Bar(
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

    def fetch_extended_trading_day(
        self,
        ticker: str,
        trade_date
    ) -> pd.DataFrame:
        """
        Fetch 5-minute bars with extended lookback from prior day 16:00.

        Args:
            ticker: Stock symbol
            trade_date: Trading date

        Returns:
            DataFrame with M5 bars from prior day 16:00 through trade day 16:00
        """
        trade_dt = self._parse_date(trade_date)
        prior_day = self._get_prior_trading_day(trade_dt)
        cache_key = self._get_cache_key(ticker, trade_dt, extended=True)

        # Check cache first
        if cache_key in self._cache:
            return self._cache[cache_key].copy()

        # Fetch from API
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

        # Filter to relevant time windows
        filtered_rows = []
        for _, row in df.iterrows():
            bar_date = row['bar_date']
            bar_time = row['bar_time']

            if bar_date == prior_day and bar_time >= PRIOR_DAY_START:
                filtered_rows.append(row)
            elif bar_date == trade_dt and MARKET_OPEN <= bar_time <= MARKET_CLOSE:
                filtered_rows.append(row)

        if not filtered_rows:
            return pd.DataFrame()

        result_df = pd.DataFrame(filtered_rows)
        result_df = result_df.sort_values('timestamp').reset_index(drop=True)

        # Cache the result
        self._cache[cache_key] = result_df.copy()

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
