"""
Epoch Trading System - Polygon.io Client
=========================================

Centralized Polygon.io API client for market data fetching.
Provides a clean interface for all Epoch modules.

Usage:
    from shared.data.polygon import PolygonClient

    client = PolygonClient()
    df = client.get_bars("AAPL", "5min", "2024-01-01", "2024-01-31")
"""

import time
import requests
import pandas as pd
from datetime import datetime, timedelta, date
from typing import Optional, Dict, List, Any, Union
from pathlib import Path

from ...config.credentials import POLYGON_API_KEY, POLYGON_BASE_URL
from ...config.epoch_config import config as epoch_config


class PolygonClient:
    """
    Centralized Polygon.io API client.

    Handles all market data fetching with:
    - Automatic rate limiting
    - Retry logic
    - Data normalization
    - Caching (optional)
    """

    # Timeframe mappings
    TIMEFRAME_MAP = {
        # User-friendly -> (multiplier, timespan)
        "1min": (1, "minute"),
        "M1": (1, "minute"),
        "5min": (5, "minute"),
        "M5": (5, "minute"),
        "15min": (15, "minute"),
        "M15": (15, "minute"),
        "1hour": (1, "hour"),
        "H1": (1, "hour"),
        "4hour": (4, "hour"),
        "H4": (4, "hour"),
        "1day": (1, "day"),
        "D1": (1, "day"),
        "1week": (1, "week"),
        "W1": (1, "week"),
        # Also support lowercase
        "m1": (1, "minute"),
        "m5": (5, "minute"),
        "m15": (15, "minute"),
        "h1": (1, "hour"),
        "h4": (4, "hour"),
        "d1": (1, "day"),
        "w1": (1, "week"),
        # Second-level for backtesting
        "15sec": (15, "second"),
        "S15": (15, "second"),
        "s15": (15, "second"),
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        rate_limit_delay: float = 0.1,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Initialize Polygon client.

        Args:
            api_key: Polygon API key (uses default from credentials if not provided)
            rate_limit_delay: Seconds between API calls
            max_retries: Max retry attempts on failure
            retry_delay: Seconds between retries
        """
        self.api_key = api_key or POLYGON_API_KEY
        self.base_url = POLYGON_BASE_URL
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Request tracking
        self._last_request_time = 0.0
        self._request_count = 0

        # Session for connection pooling
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "Epoch-Trading-System/2.0",
            "Accept": "application/json",
        })

    def _wait_for_rate_limit(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self._last_request_time = time.time()

    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Make API request with rate limiting and retry logic.

        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters

        Returns:
            JSON response as dict

        Raises:
            Exception: If all retries fail
        """
        if params is None:
            params = {}
        params["apiKey"] = self.api_key

        url = f"{self.base_url}{endpoint}"

        for attempt in range(self.max_retries):
            self._wait_for_rate_limit()
            self._request_count += 1

            try:
                response = self._session.get(url, params=params, timeout=30)

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    # Rate limited - wait longer
                    wait_time = self.retry_delay * (attempt + 2)
                    time.sleep(wait_time)
                    continue
                elif response.status_code == 403:
                    raise PermissionError(
                        f"Polygon API access denied. Check API key permissions."
                    )
                else:
                    response.raise_for_status()

            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                raise

        raise Exception(f"Failed after {self.max_retries} retries: {endpoint}")

    def _parse_date(self, d: Union[str, datetime, date]) -> str:
        """Convert date to YYYY-MM-DD string."""
        if isinstance(d, str):
            return d
        elif isinstance(d, datetime):
            return d.strftime("%Y-%m-%d")
        elif isinstance(d, date):
            return d.strftime("%Y-%m-%d")
        else:
            raise ValueError(f"Invalid date type: {type(d)}")

    def _parse_timeframe(self, timeframe: str) -> tuple:
        """
        Parse timeframe string to (multiplier, timespan).

        Args:
            timeframe: e.g., "5min", "M5", "H1", "D1"

        Returns:
            (multiplier, timespan) tuple
        """
        if timeframe in self.TIMEFRAME_MAP:
            return self.TIMEFRAME_MAP[timeframe]
        else:
            raise ValueError(
                f"Unknown timeframe: {timeframe}. "
                f"Valid options: {list(self.TIMEFRAME_MAP.keys())}"
            )

    def get_bars(
        self,
        symbol: str,
        timeframe: str,
        start_date: Union[str, datetime, date],
        end_date: Union[str, datetime, date],
        adjusted: bool = True,
        limit: int = 50000,
    ) -> pd.DataFrame:
        """
        Fetch OHLCV bar data for a symbol.

        Args:
            symbol: Stock ticker (e.g., "AAPL")
            timeframe: e.g., "5min", "M5", "H1", "D1"
            start_date: Start date
            end_date: End date
            adjusted: Use split-adjusted prices
            limit: Max bars per request

        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume, vwap
        """
        symbol = symbol.upper()
        multiplier, timespan = self._parse_timeframe(timeframe)
        start = self._parse_date(start_date)
        end = self._parse_date(end_date)

        endpoint = f"/v2/aggs/ticker/{symbol}/range/{multiplier}/{timespan}/{start}/{end}"
        params = {
            "adjusted": str(adjusted).lower(),
            "sort": "asc",
            "limit": limit,
        }

        response = self._make_request(endpoint, params)

        if response.get("resultsCount", 0) == 0:
            return pd.DataFrame()

        results = response.get("results", [])

        # Convert to DataFrame
        df = pd.DataFrame(results)

        # Rename columns to standard names
        column_map = {
            "t": "timestamp",
            "o": "open",
            "h": "high",
            "l": "low",
            "c": "close",
            "v": "volume",
            "vw": "vwap",
            "n": "transactions",
        }
        df = df.rename(columns=column_map)

        # Convert timestamp (milliseconds) to datetime
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df["timestamp"] = df["timestamp"].dt.tz_localize("UTC").dt.tz_convert("America/New_York")

        # Sort by timestamp
        df = df.sort_values("timestamp").reset_index(drop=True)

        return df

    def get_daily_bars(
        self,
        symbol: str,
        start_date: Union[str, datetime, date],
        end_date: Union[str, datetime, date],
        adjusted: bool = True,
    ) -> pd.DataFrame:
        """Convenience method for daily bars."""
        return self.get_bars(symbol, "D1", start_date, end_date, adjusted)

    def get_intraday_bars(
        self,
        symbol: str,
        timeframe: str,
        start_date: Union[str, datetime, date],
        end_date: Union[str, datetime, date],
        adjusted: bool = True,
    ) -> pd.DataFrame:
        """Convenience method for intraday bars."""
        return self.get_bars(symbol, timeframe, start_date, end_date, adjusted)

    def get_previous_close(self, symbol: str) -> Dict[str, Any]:
        """
        Get previous day's close data.

        Args:
            symbol: Stock ticker

        Returns:
            Dict with open, high, low, close, volume, vwap
        """
        symbol = symbol.upper()
        endpoint = f"/v2/aggs/ticker/{symbol}/prev"

        response = self._make_request(endpoint)

        if response.get("resultsCount", 0) == 0:
            return {}

        result = response["results"][0]
        return {
            "open": result.get("o"),
            "high": result.get("h"),
            "low": result.get("l"),
            "close": result.get("c"),
            "volume": result.get("v"),
            "vwap": result.get("vw"),
        }

    def get_ticker_details(self, symbol: str) -> Dict[str, Any]:
        """
        Get ticker details (company info, market cap, etc.).

        Args:
            symbol: Stock ticker

        Returns:
            Dict with ticker details
        """
        symbol = symbol.upper()
        endpoint = f"/v3/reference/tickers/{symbol}"

        response = self._make_request(endpoint)
        return response.get("results", {})

    def get_market_status(self) -> Dict[str, Any]:
        """
        Get current market status (open/closed).

        Returns:
            Dict with market status info
        """
        endpoint = "/v1/marketstatus/now"
        return self._make_request(endpoint)

    def close(self):
        """Close the session."""
        self._session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Convenience function for quick access
def get_polygon_client() -> PolygonClient:
    """Get a configured Polygon client instance."""
    return PolygonClient()
