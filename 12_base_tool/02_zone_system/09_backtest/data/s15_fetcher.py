"""
================================================================================
EPOCH TRADING SYSTEM - S15 BAR DATA FETCHER
Backtest Module - Polygon API Integration for 15-Second Bars
XIII Trading LLC
================================================================================

PURPOSE:
    Fetches 15-second (S15) bar data from Polygon API for refined entry detection.
    Used in hybrid model where:
        - S15 bars: Entry trigger detection (close-based)
        - M5 bars: Exit management (Stop, Target, CHoCH)

USAGE:
    from data.s15_fetcher import S15Fetcher
    fetcher = S15Fetcher(api_key='your_key')
    bars = fetcher.fetch_bars_extended('AAPL', '2025-12-20')

API ENDPOINT:
    /v2/aggs/ticker/{ticker}/range/15/second/{from_date}/{to_date}

NOTE:
    S15 generates ~1,560 bars per ticker per trading day vs ~78 for M5.
    Extended fetch includes prior day after-hours for sufficient lookback.

================================================================================
"""

import requests
import time as time_module
from datetime import datetime, date, time, timedelta
from dataclasses import dataclass
from typing import List, Optional
import pytz


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
    Entry triggers on S15 close, exits managed on M5 timeframe.
    """

    BASE_URL = "https://api.polygon.io"
    EASTERN = pytz.timezone('America/New_York')

    # Minimum bars needed before RTH for price origin detection
    # S15 has 20x more bars than M5, so we need proportionally more
    MIN_PREMARKET_BARS = 800  # ~50 M5 bars equivalent

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
                   to_time: str = "23:59") -> List[S15Bar]:
        """
        Fetch S15 bars from Polygon API.

        Args:
            ticker: Stock symbol
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            from_time: Start time (HH:MM) - not used but kept for API compatibility
            to_time: End time (HH:MM) - not used but kept for API compatibility

        Returns:
            List of S15Bar objects
        """
        # S15 endpoint: range/15/second
        url = f"{self.BASE_URL}/v2/aggs/ticker/{ticker}/range/15/second/{from_date}/{to_date}"

        params = {
            'apiKey': self.api_key,
            'adjusted': 'true',
            'sort': 'asc',
            'limit': 50000  # S15 generates many more bars, may need pagination
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
                # Convert timestamp from milliseconds to datetime
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

    def fetch_bars_extended(self,
                            ticker: str,
                            trade_date: str,
                            include_premarket: bool = True,
                            include_afterhours: bool = True) -> List[S15Bar]:
        """
        Fetch S15 bars with extended hours, starting from prior day 16:00.

        This ensures sufficient bars for price origin detection at market open.
        S15 generates ~20x more bars than M5, so we fetch from prior day
        to ensure adequate lookback for the entry detector.

        Args:
            ticker: Stock symbol
            trade_date: Trading date (YYYY-MM-DD or date object)
            include_premarket: Include premarket (04:00-09:30)
            include_afterhours: Include after-hours (16:00-20:00)

        Returns:
            List of S15Bar objects with extended coverage
        """
        trade_dt = self._parse_date(trade_date)

        # =====================================================================
        # Start from prior trading day 16:00 for sufficient lookback bars
        # =====================================================================
        prior_day = self._get_prior_trading_day(trade_dt)

        # Fetch from prior day 16:00 to trade day end
        from_date = prior_day.strftime('%Y-%m-%d')
        to_date = trade_dt.strftime('%Y-%m-%d')

        # Fetch all bars in date range
        all_bars = self.fetch_bars(ticker, from_date, to_date)

        if not all_bars:
            print(f"  No S15 bars fetched for {ticker}")
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

            print(f"  Fetched {len(filtered_bars)} S15 bars for {ticker} (extended hours)")

            if prior_day_count > 0 or premarket_count > 0:
                print(f"    Prior day AH: {prior_day_count} bars, Trade day premarket: {premarket_count} bars")

        return filtered_bars

    def fetch_rth_only(self, ticker: str, trade_date: str) -> List[S15Bar]:
        """
        Fetch only regular trading hours (09:30-16:00).

        Args:
            ticker: Stock symbol
            trade_date: Trading date (YYYY-MM-DD)

        Returns:
            List of S15Bar objects for RTH only
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

    def get_bar_at_time(self, bars: List[S15Bar], target_time: time) -> Optional[S15Bar]:
        """
        Find the bar at or just before a specific time.

        Args:
            bars: List of S15Bar objects
            target_time: Target time to find

        Returns:
            S15Bar at or just before target_time, or None
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
    print("S15 Fetcher - 15-Second Bar Data for Entry Detection")
    print("=" * 60)
    print("\nUsed in hybrid backtest model:")
    print("  - S15: Entry trigger detection (close-based)")
    print("  - M5:  Exit management (Stop, Target, CHoCH)")
    print("\nCoverage:")
    print("  Prior day 16:00-20:00: ~960 bars (after-hours)")
    print("  Trade day 04:00-09:30: ~1,320 bars (premarket)")
    print("  Trade day 09:30-16:00: ~1,560 bars (RTH)")
    print("  Total per day:         ~3,840 bars")
    print("\nUsage:")
    print("  from s15_fetcher import S15Fetcher")
    print("  fetcher = S15Fetcher(api_key='your_key')")
    print("  bars = fetcher.fetch_bars_extended('AAPL', '2025-12-20')")
    print("  print(f'Fetched {len(bars)} S15 bars')")
