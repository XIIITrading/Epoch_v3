"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
H1 Bars - Polygon API Fetcher
XIII Trading LLC
================================================================================

Fetches 1-hour bar data from Polygon API.
Handles rate limiting, retries, and timezone conversion to Eastern Time.

Version: 1.0.0
================================================================================
"""

from dataclasses import dataclass
from datetime import datetime, date, time, timedelta
from typing import List, Dict, Optional, Any
import time as time_module
import logging
import requests
import pytz

try:
    from .config import (
        POLYGON_API_KEY,
        POLYGON_BASE_URL,
        API_DELAY,
        API_RETRIES,
        API_RETRY_DELAY,
        MARKET_OPEN,
        MARKET_CLOSE,
        H1_LOOKBACK_DAYS
    )
except ImportError:
    from config import (
        POLYGON_API_KEY,
        POLYGON_BASE_URL,
        API_DELAY,
        API_RETRIES,
        API_RETRY_DELAY,
        MARKET_OPEN,
        MARKET_CLOSE,
        H1_LOOKBACK_DAYS
    )


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class H1Bar:
    """Single H1 bar from Polygon API."""
    timestamp: datetime     # Bar timestamp in Eastern Time
    open: float
    high: float
    low: float
    close: float
    volume: int
    vwap: Optional[float] = None
    transactions: Optional[int] = None


# =============================================================================
# TIMEZONE HANDLING
# =============================================================================

ET = pytz.timezone('America/New_York')
UTC = pytz.UTC


def _convert_polygon_timestamp(ts_ms: int) -> datetime:
    """
    Convert Polygon millisecond timestamp to Eastern Time datetime.

    Args:
        ts_ms: Milliseconds since Unix epoch (UTC)

    Returns:
        datetime in Eastern Time (America/New_York)
    """
    # Polygon returns milliseconds since epoch in UTC
    utc_dt = datetime.utcfromtimestamp(ts_ms / 1000.0).replace(tzinfo=UTC)
    # Convert to Eastern Time
    et_dt = utc_dt.astimezone(ET)
    return et_dt


# =============================================================================
# H1 FETCHER CLASS
# =============================================================================

class H1Fetcher:
    """
    Fetches H1 (1-hour) bar data from Polygon API.

    Handles:
    - Rate limiting between API calls
    - Retry logic for failed requests
    - Timezone conversion to Eastern Time
    - Caching of fetched data
    """

    def __init__(
        self,
        api_key: str = None,
        rate_limit_delay: float = None
    ):
        """
        Initialize the H1 fetcher.

        Args:
            api_key: Polygon API key (defaults to config)
            rate_limit_delay: Delay between API calls in seconds
        """
        self.api_key = api_key or POLYGON_API_KEY
        self.rate_limit_delay = rate_limit_delay if rate_limit_delay is not None else API_DELAY
        self.logger = logging.getLogger(__name__)

        # Request session for connection pooling
        self.session = requests.Session()

        # Last API call timestamp for rate limiting
        self._last_api_call: Optional[float] = None

        # Cache: {cache_key: List[H1Bar]}
        self._cache: Dict[str, List[H1Bar]] = {}

    def _rate_limit(self):
        """Enforce rate limiting between API calls."""
        if self._last_api_call is not None and self.rate_limit_delay > 0:
            elapsed = time_module.time() - self._last_api_call
            if elapsed < self.rate_limit_delay:
                time_module.sleep(self.rate_limit_delay - elapsed)
        self._last_api_call = time_module.time()

    def _get_cache_key(self, ticker: str, from_date: date, to_date: date) -> str:
        """Generate cache key for a ticker-date range."""
        return f"{ticker}_{from_date.isoformat()}_{to_date.isoformat()}"

    def fetch_bars_raw(
        self,
        ticker: str,
        from_date: date,
        to_date: date
    ) -> List[H1Bar]:
        """
        Fetch raw H1 bars from Polygon API.

        Args:
            ticker: Stock symbol
            from_date: Start date (inclusive)
            to_date: End date (inclusive)

        Returns:
            List of H1Bar objects
        """
        self._rate_limit()

        url = f"{POLYGON_BASE_URL}/v2/aggs/ticker/{ticker}/range/1/hour/{from_date.isoformat()}/{to_date.isoformat()}"

        params = {
            "apiKey": self.api_key,
            "adjusted": "true",
            "sort": "asc",
            "limit": 50000  # H1 bars are limited, this is plenty
        }

        bars = []

        for attempt in range(API_RETRIES):
            try:
                response = self.session.get(url, params=params, timeout=30)

                if response.status_code == 429:
                    # Rate limited - wait and retry
                    self.logger.warning(f"Rate limited on {ticker}, attempt {attempt + 1}")
                    time_module.sleep(API_RETRY_DELAY * (attempt + 1))
                    continue

                response.raise_for_status()
                data = response.json()

                if data.get("status") != "OK":
                    self.logger.warning(f"Polygon returned status: {data.get('status')} for {ticker}")
                    return []

                results = data.get("results", [])

                for r in results:
                    try:
                        bar = H1Bar(
                            timestamp=_convert_polygon_timestamp(r["t"]),
                            open=float(r["o"]),
                            high=float(r["h"]),
                            low=float(r["l"]),
                            close=float(r["c"]),
                            volume=int(r["v"]),
                            vwap=float(r["vw"]) if "vw" in r else None,
                            transactions=int(r["n"]) if "n" in r else None
                        )
                        bars.append(bar)
                    except (KeyError, ValueError, TypeError) as e:
                        self.logger.warning(f"Error parsing bar: {e}")
                        continue

                return bars

            except requests.exceptions.Timeout:
                self.logger.warning(f"Timeout on {ticker}, attempt {attempt + 1}")
                time_module.sleep(API_RETRY_DELAY)
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Request error on {ticker}: {e}")
                time_module.sleep(API_RETRY_DELAY)

        return bars

    def fetch_h1_bars_for_structure(
        self,
        ticker: str,
        trade_date: date,
        lookback_days: int = None
    ) -> List[H1Bar]:
        """
        Fetch H1 bars for structure calculation.

        Fetches H1 bars from (trade_date - lookback_days) through trade_date.
        This provides enough H1 data for structure analysis at any point
        during the trading day.

        Args:
            ticker: Stock symbol
            trade_date: The trade date
            lookback_days: Number of days to look back (defaults to config)

        Returns:
            List of H1Bar objects sorted by timestamp
        """
        lookback_days = lookback_days or H1_LOOKBACK_DAYS

        from_date = trade_date - timedelta(days=lookback_days)
        to_date = trade_date

        # Check cache
        cache_key = self._get_cache_key(ticker, from_date, to_date)
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Fetch from API
        bars = self.fetch_bars_raw(ticker, from_date, to_date)

        # Sort by timestamp
        bars.sort(key=lambda b: b.timestamp)

        # Cache the result
        self._cache[cache_key] = bars

        return bars

    def fetch_h1_bars_for_date(
        self,
        ticker: str,
        trade_date: date
    ) -> List[H1Bar]:
        """
        Fetch H1 bars for a single date only.

        Args:
            ticker: Stock symbol
            trade_date: The date to fetch

        Returns:
            List of H1Bar objects for that date
        """
        bars = self.fetch_bars_raw(ticker, trade_date, trade_date)
        return sorted(bars, key=lambda b: b.timestamp)

    def get_bars_up_to_time(
        self,
        bars: List[H1Bar],
        end_time: time
    ) -> List[H1Bar]:
        """
        Filter bars to only include those up to a specific time.

        Args:
            bars: List of H1Bar objects
            end_time: Maximum bar time (exclusive)

        Returns:
            Filtered list of H1Bar objects
        """
        return [b for b in bars if b.timestamp.time() < end_time]

    def clear_cache(self):
        """Clear the internal cache."""
        self._cache.clear()

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {
            "cached_date_ranges": len(self._cache),
            "total_bars_cached": sum(len(bars) for bars in self._cache.values())
        }


# =============================================================================
# STANDALONE TEST
# =============================================================================

if __name__ == "__main__":
    print("H1 Fetcher - Standalone Test")
    print("=" * 60)

    fetcher = H1Fetcher()

    test_ticker = "SPY"
    test_date = date(2025, 1, 10)

    print(f"\nFetching H1 bars for {test_ticker} (7 days before {test_date})...")

    bars = fetcher.fetch_h1_bars_for_structure(test_ticker, test_date)

    if bars:
        print(f"  Fetched {len(bars)} H1 bars")
        print(f"  First bar: {bars[0].timestamp}")
        print(f"  Last bar: {bars[-1].timestamp}")

        print("\nFirst 5 bars:")
        for bar in bars[:5]:
            print(f"  {bar.timestamp}: O={bar.open:.2f} H={bar.high:.2f} L={bar.low:.2f} C={bar.close:.2f} V={bar.volume:,}")

        print("\nLast 5 bars:")
        for bar in bars[-5:]:
            print(f"  {bar.timestamp}: O={bar.open:.2f} H={bar.high:.2f} L={bar.low:.2f} C={bar.close:.2f} V={bar.volume:,}")

        print(f"\nCache stats: {fetcher.get_cache_stats()}")
    else:
        print("  No bars found")

    print("\nDone.")
