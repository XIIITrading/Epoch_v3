"""
Journal M1 Bar Fetcher - Fetches 1-minute bars from Polygon API.

Adapted from 03_backtest/processor/secondary_analysis/m1_indicator_bars/m1_fetcher.py
Self-contained — no imports from backtest system.

Fetches M1 bars for the extended trading day (prior day 16:00 through trade day 16:00)
to ensure sufficient lookback for SMA/VWAP calculations at market open.
"""

import requests
import time as time_module
from datetime import datetime, date, time, timedelta
from dataclasses import dataclass
from typing import List, Optional, Dict
import pytz
import pandas as pd
import sys
from pathlib import Path

# Add parent for config
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import POLYGON_API_KEY, API_DELAY, API_RETRIES, API_RETRY_DELAY

# Time constants
PREMARKET_START = time(8, 0)
MARKET_CLOSE = time(16, 0)
PRIOR_DAY_START = time(16, 0)


class M1Fetcher:
    """
    Fetches 1-minute bar data from Polygon.io API.
    Returns DataFrames with columns: timestamp, bar_date, bar_time, open, high, low, close, volume, vwap
    """

    ET = pytz.timezone('America/New_York')
    UTC = pytz.UTC

    def __init__(self, api_key: str = None):
        self.api_key = api_key or POLYGON_API_KEY
        self.base_url = "https://api.polygon.io"
        self._cache: Dict[str, pd.DataFrame] = {}

    def _get_prior_trading_day(self, trade_date: date) -> date:
        """Get the prior trading day (skip weekends)."""
        prior = trade_date - timedelta(days=1)
        while prior.weekday() >= 5:
            prior -= timedelta(days=1)
        return prior

    def _convert_polygon_timestamp(self, ts_ms: int) -> datetime:
        """Convert Polygon ms timestamp to ET datetime."""
        utc_dt = datetime.utcfromtimestamp(ts_ms / 1000).replace(tzinfo=self.UTC)
        return utc_dt.astimezone(self.ET)

    def fetch_bars_raw(self, ticker: str, from_date: str, to_date: str) -> List[Dict]:
        """Fetch raw M1 bars from Polygon API."""
        url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/1/minute/{from_date}/{to_date}"
        params = {
            'apiKey': self.api_key,
            'adjusted': 'true',
            'sort': 'asc',
            'limit': 50000,
        }

        for attempt in range(API_RETRIES):
            try:
                time_module.sleep(API_DELAY)
                response = requests.get(url, params=params, timeout=30)

                if response.status_code == 429:
                    wait = API_RETRY_DELAY * (attempt + 1)
                    print(f"    Rate limited, waiting {wait}s...")
                    time_module.sleep(wait)
                    continue

                if response.status_code != 200:
                    print(f"    API error: {response.status_code}")
                    return []

                data = response.json()
                if data.get('status') not in ['OK', 'DELAYED']:
                    return []

                results = data.get('results', [])
                if not results:
                    return []

                bars = []
                for r in results:
                    ts = self._convert_polygon_timestamp(r['t'])
                    bars.append({
                        'timestamp': ts,
                        'bar_date': ts.date(),
                        'bar_time': ts.time(),
                        'open': r['o'],
                        'high': r['h'],
                        'low': r['l'],
                        'close': r['c'],
                        'volume': int(r['v']),
                        'vwap': r.get('vw'),
                        'transactions': r.get('n'),
                    })
                return bars

            except requests.exceptions.Timeout:
                print(f"    Timeout on attempt {attempt + 1}, retrying...")
                time_module.sleep(API_RETRY_DELAY)
            except Exception as e:
                print(f"    Fetch error: {e}")
                return []

        return []

    def fetch_extended_trading_day(self, ticker: str, trade_date: date) -> pd.DataFrame:
        """
        Fetch M1 bars with extended lookback from prior day 16:00.
        Ensures sufficient bars for SMA21 calculation at market open.

        Returns:
            DataFrame with M1 bars from prior day 16:00 through trade day 16:00
        """
        cache_key = f"{ticker}_{trade_date.isoformat()}_extended"
        if cache_key in self._cache:
            return self._cache[cache_key].copy()

        prior_day = self._get_prior_trading_day(trade_date)
        from_date = prior_day.strftime('%Y-%m-%d')
        to_date = trade_date.strftime('%Y-%m-%d')

        raw_bars = self.fetch_bars_raw(ticker, from_date, to_date)
        if not raw_bars:
            return pd.DataFrame()

        df = pd.DataFrame(raw_bars)

        # Filter to relevant time windows
        filtered = []
        for _, row in df.iterrows():
            bd = row['bar_date']
            bt = row['bar_time']
            if bd == prior_day and bt >= PRIOR_DAY_START:
                filtered.append(row)
            elif bd == trade_date and PREMARKET_START <= bt <= MARKET_CLOSE:
                filtered.append(row)

        if not filtered:
            return pd.DataFrame()

        result_df = pd.DataFrame(filtered).sort_values('timestamp').reset_index(drop=True)
        self._cache[cache_key] = result_df.copy()
        return result_df

    def fetch_trading_day(self, ticker: str, trade_date: date) -> pd.DataFrame:
        """Fetch M1 bars for a single trading day (08:00-16:00 ET)."""
        cache_key = f"{ticker}_{trade_date.isoformat()}"
        if cache_key in self._cache:
            return self._cache[cache_key].copy()

        date_str = trade_date.strftime('%Y-%m-%d')
        raw_bars = self.fetch_bars_raw(ticker, date_str, date_str)
        if not raw_bars:
            return pd.DataFrame()

        df = pd.DataFrame(raw_bars)
        df = df[(df['bar_time'] >= PREMARKET_START) & (df['bar_time'] <= MARKET_CLOSE)]
        df = df.sort_values('timestamp').reset_index(drop=True)
        self._cache[cache_key] = df.copy()
        return df

    def clear_cache(self):
        self._cache.clear()
