"""
Epoch Trading System - Polygon Client for Training Module
Fetches bar data for chart rendering.

Reuses patterns from 08_visualization/data_readers/polygon_fetcher.py
"""

import pandas as pd
import requests
import time
import logging
from datetime import datetime, date, timedelta
from typing import Dict, Optional
from dataclasses import dataclass

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    POLYGON_API_KEY, API_DELAY, API_RETRIES, API_RETRY_DELAY,
    DISPLAY_TIMEZONE, MARKET_OPEN_HOUR, MARKET_CLOSE_HOUR
)

logger = logging.getLogger(__name__)


@dataclass
class BarData:
    """Container for fetched bar data."""
    ticker: str
    trade_date: date
    bars_5m: pd.DataFrame
    bars_15m: pd.DataFrame
    bars_1h: pd.DataFrame
    fetch_time: datetime

    @property
    def is_valid(self) -> bool:
        """Check if we have data for all timeframes."""
        return not (self.bars_5m.empty or self.bars_15m.empty or self.bars_1h.empty)


class PolygonClient:
    """
    Polygon API client for fetching bar data.
    Optimized for training module chart rendering.
    """

    def __init__(self, api_key: str = None):
        """Initialize with API key."""
        self.api_key = api_key or POLYGON_API_KEY
        self.base_url = "https://api.polygon.io"

        if not self.api_key:
            logger.warning("No Polygon API key configured")

    def fetch_bars_for_trade(
        self,
        ticker: str,
        trade_date: date,
        candle_count: int = 120
    ) -> BarData:
        """
        Fetch bars for all timeframes for a single trade date.

        Args:
            ticker: Stock symbol
            trade_date: The date of the trade
            candle_count: Number of candles to fetch per timeframe

        Returns:
            BarData with bars for all three timeframes
        """
        ticker = ticker.upper().strip()
        fetch_time = datetime.now()

        logger.info(f"Fetching bars for {ticker} on {trade_date}")

        # For each timeframe, we need to go back far enough to get candle_count bars
        # 5m: 120 bars = 10 hours of trading = 1-2 days
        # 15m: 120 bars = 30 hours = 4-5 days
        # 1h: 120 bars = 120 hours = 18-20 days

        # Fetch 5m bars
        bars_5m = self._fetch_bars(
            ticker,
            trade_date,
            timeframe_minutes=5,
            candle_count=candle_count,
            lookback_days=3
        )

        # Fetch 15m bars
        bars_15m = self._fetch_bars(
            ticker,
            trade_date,
            timeframe_minutes=15,
            candle_count=candle_count,
            lookback_days=8
        )

        # Fetch 1h bars
        bars_1h = self._fetch_bars(
            ticker,
            trade_date,
            timeframe_minutes=60,
            candle_count=candle_count,
            lookback_days=25
        )

        return BarData(
            ticker=ticker,
            trade_date=trade_date,
            bars_5m=bars_5m,
            bars_15m=bars_15m,
            bars_1h=bars_1h,
            fetch_time=fetch_time
        )

    def _fetch_bars(
        self,
        ticker: str,
        end_date: date,
        timeframe_minutes: int,
        candle_count: int,
        lookback_days: int
    ) -> pd.DataFrame:
        """
        Fetch bars from Polygon API.

        Args:
            ticker: Stock symbol
            end_date: End date for data
            timeframe_minutes: Bar size in minutes (5, 15, 60)
            candle_count: Number of bars to return
            lookback_days: How many days back to fetch

        Returns:
            DataFrame with OHLCV data
        """
        start_date = end_date - timedelta(days=lookback_days)
        end_date_str = end_date.strftime('%Y-%m-%d')
        start_date_str = start_date.strftime('%Y-%m-%d')

        endpoint = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/{timeframe_minutes}/minute/{start_date_str}/{end_date_str}"

        params = {
            'apiKey': self.api_key,
            'adjusted': 'true',
            'sort': 'asc',
            'limit': 50000
        }

        for attempt in range(API_RETRIES):
            try:
                response = requests.get(endpoint, params=params, timeout=30)
                response.raise_for_status()

                data = response.json()

                if data.get('status') != 'OK':
                    logger.warning(f"API status: {data.get('status')}")
                    return pd.DataFrame()

                results = data.get('results', [])

                if not results:
                    logger.warning(f"No results for {ticker} {timeframe_minutes}m")
                    return pd.DataFrame()

                # Convert to DataFrame
                df = pd.DataFrame(results)

                # Rename columns
                column_mapping = {
                    't': 'timestamp',
                    'o': 'open',
                    'h': 'high',
                    'l': 'low',
                    'c': 'close',
                    'v': 'volume'
                }
                df = df.rename(columns=column_mapping)

                # Convert timestamp
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
                df['timestamp'] = df['timestamp'].dt.tz_convert(DISPLAY_TIMEZONE)
                df.set_index('timestamp', inplace=True)

                # Keep only OHLCV
                df = df[['open', 'high', 'low', 'close', 'volume']]

                # Don't truncate here - let the chart builder/cache manager slice
                # This ensures we have context before entry time for any trade on this date
                logger.debug(f"Fetched {len(df)} {timeframe_minutes}m bars for {ticker}")

                # Rate limiting
                time.sleep(API_DELAY)

                return df

            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt < API_RETRIES - 1:
                    time.sleep(API_RETRY_DELAY)

            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                break

        return pd.DataFrame()

    def fetch_extended_bars(
        self,
        ticker: str,
        trade_date: date,
        entry_time: datetime,
        exit_time: datetime,
        buffer_bars: int = 10
    ) -> BarData:
        """
        Fetch bars that cover entry through exit with buffer.
        Used for reveal mode to show the complete trade.

        Args:
            ticker: Stock symbol
            trade_date: The date of the trade
            entry_time: Trade entry time
            exit_time: Trade exit time
            buffer_bars: Extra bars to fetch after exit

        Returns:
            BarData with extended bars
        """
        # For reveal mode, we want bars that go past the exit
        # Fetch enough to cover trade + buffer
        trade_duration_minutes = int((exit_time - entry_time).total_seconds() / 60)

        # Calculate how many 5m bars we need
        bars_needed_5m = (trade_duration_minutes // 5) + buffer_bars + 120  # 120 context + trade + buffer

        return self.fetch_bars_for_trade(
            ticker=ticker,
            trade_date=trade_date,
            candle_count=bars_needed_5m
        )


# Singleton instance
_client = None


def get_polygon_client() -> PolygonClient:
    """Get or create the Polygon client singleton."""
    global _client
    if _client is None:
        _client = PolygonClient()
    return _client
