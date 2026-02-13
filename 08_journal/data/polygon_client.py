"""
Polygon API client for the Epoch Trading Journal.
Fetches M1, M15, H1 bars for chart rendering.

Adapted from 06_training/data/polygon_client.py with:
- M1 bar fetching for execution chart
- Time-windowed M1 fetch (entry-15min through exit+60min)
- candle_count limiting (default 120) for M15/H1 to match training module
- Same Polygon API patterns, DataFrame format, and timezone handling
"""

import pandas as pd
import requests
import time as time_mod
import logging
from datetime import datetime, date, time, timedelta
from typing import Optional
from dataclasses import dataclass

from config import (
    POLYGON_API_KEY, API_DELAY, API_RETRIES, API_RETRY_DELAY,
    DISPLAY_TIMEZONE, CHART_CONFIG,
)

logger = logging.getLogger(__name__)


@dataclass
class BarData:
    """Container for fetched bar data across all timeframes."""
    ticker: str
    trade_date: date
    bars_1m: pd.DataFrame
    bars_15m: pd.DataFrame
    bars_1h: pd.DataFrame
    fetch_time: datetime

    @property
    def is_valid(self) -> bool:
        """Check if we have data for the core timeframes."""
        return not (self.bars_15m.empty or self.bars_1h.empty)

    @property
    def has_m1(self) -> bool:
        """Check if M1 data was fetched."""
        return not self.bars_1m.empty


class PolygonClient:
    """
    Polygon API client for fetching multi-timeframe bar data.
    Returns DataFrames with DatetimeIndex in Eastern Time.
    Columns: open, high, low, close, volume
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or POLYGON_API_KEY
        self.base_url = "https://api.polygon.io"

    def fetch_bars_for_trade(
        self,
        ticker: str,
        trade_date: date,
        trade=None,
        candle_count: int = 120,
    ) -> BarData:
        """
        Fetch bars for all timeframes for a journal trade.

        Args:
            ticker: Stock symbol
            trade_date: The date of the trade
            trade: Optional Trade object — if provided, M1 bars are windowed
                   around the fill times. If None, M1 fetches full RTH day.
            candle_count: Number of candles to return per timeframe (default 120)

        Returns:
            BarData with M1, M15, H1 DataFrames
        """
        ticker = ticker.upper().strip()
        fetch_time = datetime.now()

        # M1: windowed around fills if trade provided, else full day
        if trade and trade.entry_time and trade.exit_time:
            bars_1m = self._fetch_m1_windowed(ticker, trade_date, trade)
        else:
            bars_1m = self._fetch_bars(ticker, trade_date, timeframe_minutes=1, lookback_days=1)

        # M15: 8-day lookback, last candle_count bars
        bars_15m = self._fetch_bars(
            ticker, trade_date, timeframe_minutes=15,
            lookback_days=8, candle_count=candle_count,
        )

        # H1: 25-day lookback for structure, last candle_count bars
        bars_1h = self._fetch_bars(
            ticker, trade_date, timeframe_minutes=60,
            lookback_days=25, candle_count=candle_count,
        )

        return BarData(
            ticker=ticker,
            trade_date=trade_date,
            bars_1m=bars_1m,
            bars_15m=bars_15m,
            bars_1h=bars_1h,
            fetch_time=fetch_time,
        )

    def _fetch_m1_windowed(self, ticker: str, trade_date: date, trade) -> pd.DataFrame:
        """
        Fetch M1 bars windowed around the trade's fill times.
        Window: first_fill - pre_buffer through last_fill + post_buffer.
        """
        pre_buffer = CHART_CONFIG.get('m1_pre_buffer_minutes', 15)
        post_buffer = CHART_CONFIG.get('m1_post_buffer_minutes', 60)

        # Get the full time range of all fills
        first_fill_time = trade.entry_time
        last_fill_time = trade.exit_time or trade.entry_time

        # Fetch full day of M1 bars then slice
        df = self._fetch_bars(ticker, trade_date, timeframe_minutes=1, lookback_days=1)

        if df.empty:
            return df

        # Build window datetimes
        import pytz
        et = pytz.timezone(DISPLAY_TIMEZONE)
        window_start = et.localize(
            datetime.combine(trade_date, first_fill_time) - timedelta(minutes=pre_buffer)
        )
        window_end = et.localize(
            datetime.combine(trade_date, last_fill_time) + timedelta(minutes=post_buffer)
        )

        # Slice to window
        return df[(df.index >= window_start) & (df.index <= window_end)]

    def _fetch_bars(
        self,
        ticker: str,
        end_date: date,
        timeframe_minutes: int,
        lookback_days: int,
        candle_count: int = None,
    ) -> pd.DataFrame:
        """
        Fetch bars from Polygon API.

        Args:
            ticker: Stock symbol
            end_date: End date for data
            timeframe_minutes: Bar size in minutes (1, 15, 60)
            lookback_days: How many calendar days back to fetch
            candle_count: If set, return only the last N bars

        Returns:
            DataFrame with DatetimeIndex (ET), columns: open, high, low, close, volume
        """
        start_date = end_date - timedelta(days=lookback_days)

        endpoint = (
            f"{self.base_url}/v2/aggs/ticker/{ticker}"
            f"/range/{timeframe_minutes}/minute"
            f"/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
        )

        params = {
            'apiKey': self.api_key,
            'adjusted': 'true',
            'sort': 'asc',
            'limit': 50000,
        }

        for attempt in range(API_RETRIES):
            try:
                response = requests.get(endpoint, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()

                if data.get('status') != 'OK':
                    logger.warning(f"API status: {data.get('status')} for {ticker} {timeframe_minutes}m")
                    return pd.DataFrame()

                results = data.get('results', [])
                if not results:
                    logger.warning(f"No results for {ticker} {timeframe_minutes}m")
                    return pd.DataFrame()

                df = pd.DataFrame(results)
                df = df.rename(columns={
                    't': 'timestamp', 'o': 'open', 'h': 'high',
                    'l': 'low', 'c': 'close', 'v': 'volume',
                })

                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
                df['timestamp'] = df['timestamp'].dt.tz_convert(DISPLAY_TIMEZONE)
                df.set_index('timestamp', inplace=True)
                df = df[['open', 'high', 'low', 'close', 'volume']]

                # Limit to last N bars if candle_count specified
                if candle_count and len(df) > candle_count:
                    df = df.tail(candle_count)

                logger.debug(f"Fetched {len(df)} {timeframe_minutes}m bars for {ticker}")
                time_mod.sleep(API_DELAY)
                return df

            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt < API_RETRIES - 1:
                    time_mod.sleep(API_RETRY_DELAY)
            except Exception as e:
                logger.error(f"Unexpected error fetching {ticker} {timeframe_minutes}m: {e}")
                break

        return pd.DataFrame()


# Singleton
_client = None


def get_polygon_client() -> PolygonClient:
    """Get or create the Polygon client singleton."""
    global _client
    if _client is None:
        _client = PolygonClient()
    return _client
