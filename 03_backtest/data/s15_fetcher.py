"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 03: BACKTEST RUNNER v3.0
S15 Bar Data Fetcher - Polygon API Integration for 15-Second Bars
XIII Trading LLC
================================================================================

Fetches S15 (15-second) bar data from Polygon API for refined entry detection.
Used in hybrid model where S15 bars trigger entries and M5 bars manage exits.
================================================================================
"""
import sys
from pathlib import Path
import requests
import time as time_module
from datetime import datetime, date, time, timedelta
from dataclasses import dataclass
from typing import List, Optional
import pytz

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import POLYGON_API_KEY


@dataclass
class S15Bar:
    """Single S15 (15-second) bar data structure."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    vwap: Optional[float] = None
    transactions: Optional[int] = None


class S15Fetcher:
    """
    Fetches S15 (15-second) bar data from Polygon.io API.
    Used for refined entry detection in the hybrid backtest model.
    """

    BASE_URL = "https://api.polygon.io"
    EASTERN = pytz.timezone('America/New_York')
    MIN_PREMARKET_BARS = 800

    def __init__(self, api_key: str = None, rate_limit_delay: float = 0.25):
        self.api_key = api_key or POLYGON_API_KEY
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0

    def _rate_limit(self):
        """Enforce rate limiting between API calls."""
        elapsed = time_module.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time_module.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time_module.time()

    def _get_prior_trading_day(self, trade_date: date) -> date:
        """Get the prior trading day (skip weekends)."""
        prior = trade_date - timedelta(days=1)
        while prior.weekday() >= 5:
            prior -= timedelta(days=1)
        return prior

    def _parse_date(self, date_input) -> date:
        """Parse various date formats to date object."""
        if isinstance(date_input, date):
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

    def fetch_bars(self, ticker: str, from_date: str, to_date: str,
                   from_time: str = "00:00", to_time: str = "23:59") -> List[S15Bar]:
        """Fetch S15 bars from Polygon API."""
        url = f"{self.BASE_URL}/v2/aggs/ticker/{ticker}/range/15/second/{from_date}/{to_date}"

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
                print(f"  S15 API error: {response.status_code}")
                return []

            data = response.json()

            if data.get('status') not in ['OK', 'DELAYED']:
                print(f"  S15 API status: {data.get('status')}")
                return []

            if 'results' not in data or not data['results']:
                return []

            bars = []
            for result in data['results']:
                ts = datetime.fromtimestamp(result['t'] / 1000, tz=self.EASTERN)
                bar = S15Bar(
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
            print(f"  S15 fetch error: {e}")
            return []

    def fetch_bars_extended(self, ticker: str, trade_date: str,
                            include_premarket: bool = True,
                            include_afterhours: bool = True) -> List[S15Bar]:
        """Fetch S15 bars with extended hours, starting from prior day 16:00."""
        trade_dt = self._parse_date(trade_date)
        prior_day = self._get_prior_trading_day(trade_dt)

        from_date = prior_day.strftime('%Y-%m-%d')
        to_date = trade_dt.strftime('%Y-%m-%d')

        all_bars = self.fetch_bars(ticker, from_date, to_date)

        if not all_bars:
            print(f"  No S15 bars fetched for {ticker}")
            return []

        filtered_bars = []

        for bar in all_bars:
            bar_date = bar.timestamp.date()
            bar_time = bar.timestamp.time()

            if bar_date == prior_day:
                if time(16, 0) <= bar_time <= time(20, 0):
                    filtered_bars.append(bar)
            elif bar_date == trade_dt:
                if time(9, 30) <= bar_time <= time(16, 0):
                    filtered_bars.append(bar)
                elif include_premarket and time(4, 0) <= bar_time < time(9, 30):
                    filtered_bars.append(bar)
                elif include_afterhours and time(16, 0) < bar_time <= time(20, 0):
                    filtered_bars.append(bar)

        filtered_bars.sort(key=lambda x: x.timestamp)

        if filtered_bars:
            premarket_count = sum(
                1 for b in filtered_bars
                if b.timestamp.date() == trade_dt and b.timestamp.time() < time(9, 30)
            )
            prior_day_count = sum(
                1 for b in filtered_bars
                if b.timestamp.date() == prior_day
            )

            print(f"  Fetched {len(filtered_bars)} S15 bars for {ticker} (extended hours)")

        return filtered_bars

    def fetch_rth_only(self, ticker: str, trade_date: str) -> List[S15Bar]:
        """Fetch only regular trading hours (09:30-16:00)."""
        trade_dt = self._parse_date(trade_date)
        date_str = trade_dt.strftime('%Y-%m-%d')

        all_bars = self.fetch_bars(ticker, date_str, date_str)

        rth_bars = [
            bar for bar in all_bars
            if time(9, 30) <= bar.timestamp.time() <= time(16, 0)
        ]

        return rth_bars

    def get_bar_at_time(self, bars: List[S15Bar], target_time: time) -> Optional[S15Bar]:
        """Find the bar at or just before a specific time."""
        if not bars:
            return None

        matching_bar = None
        for bar in bars:
            bar_time = bar.timestamp.time()
            if bar_time <= target_time:
                matching_bar = bar
            else:
                break

        return matching_bar
