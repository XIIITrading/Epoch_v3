"""
Polygon API client wrapper.
Provides unified interface for all market data fetching.

Ported and consolidated from:
- 02_zone_system/01_market_structure/polygon_data_fetcher.py
- 02_zone_system/10_training/data/polygon_client.py
- 02_zone_system/03_bar_data/calculations/options_calculator.py
"""
import logging
import time
from datetime import date, datetime, timedelta, timezone
from typing import List, Dict, Optional, Tuple

import pandas as pd
from polygon import RESTClient

from config import POLYGON_API_KEY, VERBOSE

logger = logging.getLogger(__name__)


class PolygonClient:
    """
    Unified wrapper for Polygon.io API calls.
    Handles rate limiting, retries, and data normalization.
    """

    # API Configuration
    BASE_URL = "https://api.polygon.io"
    RATE_LIMIT_DELAY = 0.25  # 4 calls per second for free tier
    MAX_RETRIES = 3
    RETRY_DELAY = 2.0

    def __init__(self, api_key: str = None):
        """
        Initialize Polygon client.

        Args:
            api_key: Polygon API key (uses config if not provided)
        """
        self.api_key = api_key or POLYGON_API_KEY
        if not self.api_key:
            raise ValueError(
                "POLYGON_API_KEY not set. Add to .env file or pass directly."
            )
        self.client = RESTClient(self.api_key)
        self._last_call_time = 0

        if VERBOSE:
            logger.info("Polygon client initialized")

    def _rate_limit(self):
        """Enforce rate limiting between API calls."""
        elapsed = time.time() - self._last_call_time
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self._last_call_time = time.time()

    # =========================================================================
    # DAILY BAR DATA
    # =========================================================================

    def fetch_daily_bars(
        self,
        ticker: str,
        start_date: date,
        end_date: date = None
    ) -> pd.DataFrame:
        """
        Fetch daily OHLCV bars.

        Args:
            ticker: Stock symbol
            start_date: Start date
            end_date: End date (defaults to today)

        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume, date
        """
        end_date = end_date or date.today()
        self._rate_limit()

        for attempt in range(self.MAX_RETRIES):
            try:
                aggs = list(self.client.list_aggs(
                    ticker=ticker.upper(),
                    multiplier=1,
                    timespan="day",
                    from_=start_date.isoformat(),
                    to=end_date.isoformat(),
                    adjusted=True,
                    limit=50000
                ))

                if not aggs:
                    logger.warning(f"No daily data for {ticker}")
                    return pd.DataFrame()

                data = [{
                    'timestamp': datetime.fromtimestamp(a.timestamp / 1000),
                    'open': a.open,
                    'high': a.high,
                    'low': a.low,
                    'close': a.close,
                    'volume': a.volume
                } for a in aggs]

                df = pd.DataFrame(data)
                df['date'] = df['timestamp'].dt.date
                return df.sort_values('timestamp').reset_index(drop=True)

            except Exception as e:
                logger.warning(f"Daily bars attempt {attempt + 1} failed: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY)
                else:
                    logger.error(f"Error fetching daily bars for {ticker}: {e}")
                    return pd.DataFrame()

        return pd.DataFrame()

    # =========================================================================
    # MINUTE BAR DATA
    # =========================================================================

    def fetch_minute_bars(
        self,
        ticker: str,
        start_date: date,
        end_date: date = None,
        multiplier: int = 1,
        end_timestamp: datetime = None
    ) -> pd.DataFrame:
        """
        Fetch minute-level bars.

        Args:
            ticker: Stock symbol
            start_date: Start date
            end_date: End date (ignored if end_timestamp provided)
            multiplier: Bar size in minutes (1, 5, 15, 60)
            end_timestamp: Optional precise end timestamp (timezone-aware)

        Returns:
            DataFrame with OHLCV data
        """
        # Use end_timestamp if provided, otherwise fall back to end_date
        # Polygon API requires Unix timestamp in milliseconds for precise time cutoffs
        # Subtract 1ms to make the cutoff exclusive (exclude bars starting at exactly end_timestamp)
        if end_timestamp is not None:
            to_param = int(end_timestamp.timestamp() * 1000) - 1  # Unix ms, exclusive
        else:
            end_date = end_date or date.today()
            to_param = end_date.isoformat()

        self._rate_limit()

        for attempt in range(self.MAX_RETRIES):
            try:
                aggs = list(self.client.list_aggs(
                    ticker=ticker.upper(),
                    multiplier=multiplier,
                    timespan="minute",
                    from_=start_date.isoformat(),
                    to=to_param,
                    adjusted=True,
                    limit=50000
                ))

                if not aggs:
                    logger.warning(f"No {multiplier}m data for {ticker}")
                    return pd.DataFrame()

                data = [{
                    'timestamp': datetime.fromtimestamp(a.timestamp / 1000, tz=timezone.utc),
                    'open': a.open,
                    'high': a.high,
                    'low': a.low,
                    'close': a.close,
                    'volume': a.volume
                } for a in aggs]

                return pd.DataFrame(data).sort_values('timestamp').reset_index(drop=True)

            except Exception as e:
                logger.warning(f"Minute bars attempt {attempt + 1} failed: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY)
                else:
                    logger.error(f"Error fetching {multiplier}m bars for {ticker}: {e}")
                    return pd.DataFrame()

        return pd.DataFrame()

    def fetch_minute_bars_chunked(
        self,
        ticker: str,
        start_date: date,
        end_date: date = None,
        multiplier: int = 1,
        chunk_days: int = 5,
        end_timestamp: datetime = None
    ) -> pd.DataFrame:
        """
        Fetch minute bars in chunks to handle large date ranges.
        Polygon has limits on data returned per request.

        Args:
            ticker: Stock symbol
            start_date: Start date
            end_date: End date (ignored if end_timestamp provided)
            multiplier: Bar size in minutes
            chunk_days: Days per chunk
            end_timestamp: Optional precise end timestamp (timezone-aware)

        Returns:
            Combined DataFrame with all bars
        """
        # Determine actual end date for chunking
        if end_timestamp is not None:
            actual_end_date = end_timestamp.date()
        else:
            actual_end_date = end_date or date.today()

        all_data = []

        current_start = start_date
        while current_start <= actual_end_date:
            current_end = min(current_start + timedelta(days=chunk_days), actual_end_date)

            # On the last chunk, use end_timestamp if provided
            is_last_chunk = current_end >= actual_end_date
            chunk_end_timestamp = end_timestamp if (is_last_chunk and end_timestamp) else None

            chunk = self.fetch_minute_bars(
                ticker, current_start, current_end, multiplier,
                end_timestamp=chunk_end_timestamp
            )
            if not chunk.empty:
                all_data.append(chunk)

            current_start = current_end + timedelta(days=1)

        if not all_data:
            return pd.DataFrame()

        df = pd.concat(all_data, ignore_index=True).drop_duplicates(
            subset=['timestamp']
        ).sort_values('timestamp').reset_index(drop=True)

        # Filter by end_timestamp if provided (belt and suspenders)
        # Use < (not <=) to exclude bars starting exactly at end_timestamp
        if end_timestamp is not None and not df.empty:
            df = df[df['timestamp'] < end_timestamp]

        return df

    # =========================================================================
    # HOURLY BAR DATA
    # =========================================================================

    def fetch_4h_bars(
        self,
        ticker: str,
        start_date: date,
        end_date: date = None,
        end_timestamp: datetime = None
    ) -> pd.DataFrame:
        """
        Fetch 4-hour bars directly from Polygon.

        This matches the Excel system which uses multiplier=4, timespan=hour
        rather than resampling 1H bars.

        Args:
            ticker: Stock symbol
            start_date: Start date
            end_date: End date (ignored if end_timestamp provided)
            end_timestamp: Optional precise end timestamp (timezone-aware)

        Returns:
            DataFrame with OHLCV data
        """
        # Use end_timestamp if provided, otherwise fall back to end_date
        # Polygon API requires Unix timestamp in milliseconds for precise time cutoffs
        # Subtract 1ms to make the cutoff exclusive (exclude bars starting at exactly end_timestamp)
        if end_timestamp is not None:
            to_param = int(end_timestamp.timestamp() * 1000) - 1  # Unix ms, exclusive
        else:
            end_date = end_date or date.today()
            to_param = end_date.isoformat()

        self._rate_limit()

        for attempt in range(self.MAX_RETRIES):
            try:
                aggs = list(self.client.list_aggs(
                    ticker=ticker.upper(),
                    multiplier=4,
                    timespan="hour",
                    from_=start_date.isoformat(),
                    to=to_param,
                    adjusted=True,
                    limit=50000
                ))

                if not aggs:
                    logger.warning(f"No 4H data for {ticker}")
                    return pd.DataFrame()

                data = [{
                    'timestamp': datetime.fromtimestamp(a.timestamp / 1000, tz=timezone.utc),
                    'open': a.open,
                    'high': a.high,
                    'low': a.low,
                    'close': a.close,
                    'volume': a.volume
                } for a in aggs]

                return pd.DataFrame(data).sort_values('timestamp').reset_index(drop=True)

            except Exception as e:
                logger.warning(f"4H bars attempt {attempt + 1} failed: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY)
                else:
                    logger.error(f"Error fetching 4H bars for {ticker}: {e}")
                    return pd.DataFrame()

        return pd.DataFrame()

    def fetch_hourly_bars(
        self,
        ticker: str,
        start_date: date,
        end_date: date = None,
        end_timestamp: datetime = None
    ) -> pd.DataFrame:
        """
        Fetch hourly bars.

        Args:
            ticker: Stock symbol
            start_date: Start date
            end_date: End date (ignored if end_timestamp provided)
            end_timestamp: Optional precise end timestamp (timezone-aware)

        Returns:
            DataFrame with OHLCV data
        """
        # Use end_timestamp if provided, otherwise fall back to end_date
        # Polygon API requires Unix timestamp in milliseconds for precise time cutoffs
        # Subtract 1ms to make the cutoff exclusive (exclude bars starting at exactly end_timestamp)
        if end_timestamp is not None:
            to_param = int(end_timestamp.timestamp() * 1000) - 1  # Unix ms, exclusive
        else:
            end_date = end_date or date.today()
            to_param = end_date.isoformat()

        self._rate_limit()

        for attempt in range(self.MAX_RETRIES):
            try:
                aggs = list(self.client.list_aggs(
                    ticker=ticker.upper(),
                    multiplier=1,
                    timespan="hour",
                    from_=start_date.isoformat(),
                    to=to_param,
                    adjusted=True,
                    limit=50000
                ))

                if not aggs:
                    logger.warning(f"No hourly data for {ticker}")
                    return pd.DataFrame()

                data = [{
                    'timestamp': datetime.fromtimestamp(a.timestamp / 1000, tz=timezone.utc),
                    'open': a.open,
                    'high': a.high,
                    'low': a.low,
                    'close': a.close,
                    'volume': a.volume
                } for a in aggs]

                return pd.DataFrame(data).sort_values('timestamp').reset_index(drop=True)

            except Exception as e:
                logger.warning(f"Hourly bars attempt {attempt + 1} failed: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY)
                else:
                    logger.error(f"Error fetching hourly bars for {ticker}: {e}")
                    return pd.DataFrame()

        return pd.DataFrame()

    # =========================================================================
    # OPTIONS DATA
    # =========================================================================

    def fetch_options_levels(
        self,
        ticker: str,
        current_price: float,
        reference_date: date = None,
        num_levels: int = 10,
        price_range_pct: float = 0.15
    ) -> Dict[str, float]:
        """
        Fetch top options strike levels by open interest.

        Args:
            ticker: Stock symbol
            current_price: Current stock price
            reference_date: Reference date for finding expirations
            num_levels: Number of top strike levels to return
            price_range_pct: Percentage range around current price

        Returns:
            Dictionary with opt_01 through opt_10 keys
        """
        reference_date = reference_date or date.today()

        try:
            # Get next 4 expiration dates (Fridays)
            expiration_dates = self._get_nearest_expirations(reference_date, count=4)

            # Aggregate open interest by strike across expirations
            all_strikes_data: Dict[float, int] = {}

            for exp_date in expiration_dates:
                strikes_for_exp = self._fetch_options_for_expiration(
                    ticker, exp_date, current_price, price_range_pct
                )
                for strike, oi in strikes_for_exp.items():
                    all_strikes_data[strike] = all_strikes_data.get(strike, 0) + oi

            # Sort by total open interest and take top N
            sorted_strikes = sorted(
                all_strikes_data.items(),
                key=lambda x: x[1],
                reverse=True
            )[:num_levels]

            # Format results
            results = {}
            for i, (strike, oi) in enumerate(sorted_strikes, 1):
                results[f'op_{i:02d}'] = float(strike)

            # Fill remaining slots with None
            for i in range(len(sorted_strikes) + 1, num_levels + 1):
                results[f'op_{i:02d}'] = None

            logger.info(f"Found {len(sorted_strikes)} options levels for {ticker}")
            return results

        except Exception as e:
            logger.error(f"Error fetching options levels for {ticker}: {e}")
            return {f'op_{i:02d}': None for i in range(1, num_levels + 1)}

    def _fetch_options_for_expiration(
        self,
        ticker: str,
        exp_date: str,
        current_price: float,
        price_range_pct: float
    ) -> Dict[float, int]:
        """Fetch options data for a specific expiration date."""
        strikes_data = {}
        self._rate_limit()

        try:
            min_strike = current_price * (1 - price_range_pct)
            max_strike = current_price * (1 + price_range_pct)

            contracts = list(self.client.list_options_contracts(
                underlying_ticker=ticker.upper(),
                expiration_date=exp_date,
                strike_price_gte=min_strike,
                strike_price_lte=max_strike,
                limit=500
            ))

            for contract in contracts:
                try:
                    self._rate_limit()
                    snapshot = self.client.get_snapshot_option(
                        ticker.upper(),
                        contract.ticker
                    )

                    if snapshot and hasattr(snapshot, 'open_interest'):
                        oi = snapshot.open_interest
                        if oi and oi > 0:
                            strike = float(contract.strike_price)
                            strikes_data[strike] = strikes_data.get(strike, 0) + int(oi)

                except Exception:
                    continue

        except Exception as e:
            logger.warning(f"Error fetching options for {exp_date}: {e}")

        return strikes_data

    def _get_nearest_expirations(self, reference_date: date, count: int = 4) -> List[str]:
        """Get the nearest option expiration dates (Fridays)."""
        expirations = []
        current_date = reference_date

        while len(expirations) < count:
            # Calculate days until next Friday (weekday 4)
            days_ahead = 4 - current_date.weekday()
            if days_ahead <= 0:
                days_ahead += 7

            next_friday = current_date + timedelta(days=days_ahead)
            expirations.append(next_friday.strftime("%Y-%m-%d"))
            current_date = next_friday + timedelta(days=1)

        return expirations

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def get_previous_close(self, ticker: str) -> Optional[float]:
        """Get previous day's close price."""
        self._rate_limit()

        try:
            prev = self.client.get_previous_close_agg(ticker.upper())

            # Handle different response structures from Polygon API
            if prev:
                # Try direct results attribute
                if hasattr(prev, 'results') and prev.results:
                    return float(prev.results[0].close)
                # Try as list/iterable
                if hasattr(prev, '__iter__'):
                    results = list(prev)
                    if results and hasattr(results[0], 'close'):
                        return float(results[0].close)
                # Try as single Agg object
                if hasattr(prev, 'close'):
                    return float(prev.close)

            # Fallback: get most recent daily bar
            return self.get_current_price(ticker)

        except Exception as e:
            logger.error(f"Error fetching prev close for {ticker}: {e}")
            # Fallback to current price
            return self.get_current_price(ticker)

    def get_current_price(
        self,
        ticker: str,
        end_timestamp: datetime = None
    ) -> Optional[float]:
        """
        Get current/latest price for ticker.

        Args:
            ticker: Stock symbol
            end_timestamp: Optional precise end timestamp for pre/post market mode.
                          If provided, returns the close price of the last bar
                          before this timestamp instead of the current price.

        Returns:
            Price as float, or None if not available
        """
        # If end_timestamp provided, get price at that specific time
        if end_timestamp is not None:
            return self.get_price_at_timestamp(ticker, end_timestamp)

        self._rate_limit()

        try:
            # Try to get recent daily data
            for days_back in range(5):
                check_date = date.today() - timedelta(days=days_back)
                df = self.fetch_daily_bars(ticker, check_date, check_date)
                if not df.empty:
                    return float(df.iloc[-1]['close'])
            return None
        except Exception as e:
            logger.error(f"Could not fetch price for {ticker}: {e}")
            return None

    def get_price_at_timestamp(
        self,
        ticker: str,
        end_timestamp: datetime
    ) -> Optional[float]:
        """
        Get the closing price at a specific timestamp.

        Uses hourly bars to find the last closed bar before end_timestamp.

        Args:
            ticker: Stock symbol
            end_timestamp: Cutoff timestamp (timezone-aware)

        Returns:
            Close price of the last bar before the timestamp, or None
        """
        try:
            # Fetch the last day of hourly data up to end_timestamp
            start_date = end_timestamp.date() - timedelta(days=2)
            df = self.fetch_hourly_bars(
                ticker, start_date, end_timestamp=end_timestamp
            )
            if df.empty:
                logger.warning(f"No price data for {ticker} at {end_timestamp}")
                return None
            return float(df.iloc[-1]['close'])
        except Exception as e:
            logger.error(f"Error getting price at timestamp for {ticker}: {e}")
            return None

    def fetch_weekly_bars(
        self,
        ticker: str,
        start_date: date,
        end_date: date = None
    ) -> pd.DataFrame:
        """
        Fetch weekly OHLCV bars.

        Args:
            ticker: Stock symbol
            start_date: Start date
            end_date: End date

        Returns:
            DataFrame with OHLCV data
        """
        end_date = end_date or date.today()
        self._rate_limit()

        for attempt in range(self.MAX_RETRIES):
            try:
                aggs = list(self.client.list_aggs(
                    ticker=ticker.upper(),
                    multiplier=1,
                    timespan="week",
                    from_=start_date.isoformat(),
                    to=end_date.isoformat(),
                    adjusted=True,
                    limit=50000
                ))

                if not aggs:
                    logger.warning(f"No weekly data for {ticker}")
                    return pd.DataFrame()

                data = [{
                    'timestamp': datetime.fromtimestamp(a.timestamp / 1000),
                    'open': a.open,
                    'high': a.high,
                    'low': a.low,
                    'close': a.close,
                    'volume': a.volume
                } for a in aggs]

                df = pd.DataFrame(data)
                df['date'] = df['timestamp'].dt.date
                return df.sort_values('timestamp').reset_index(drop=True)

            except Exception as e:
                logger.warning(f"Weekly bars attempt {attempt + 1} failed: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY)
                else:
                    logger.error(f"Error fetching weekly bars for {ticker}: {e}")
                    return pd.DataFrame()

        return pd.DataFrame()

    def fetch_monthly_bars(
        self,
        ticker: str,
        start_date: date,
        end_date: date = None
    ) -> pd.DataFrame:
        """
        Fetch monthly OHLCV bars.

        Args:
            ticker: Stock symbol
            start_date: Start date
            end_date: End date

        Returns:
            DataFrame with OHLCV data
        """
        end_date = end_date or date.today()
        self._rate_limit()

        for attempt in range(self.MAX_RETRIES):
            try:
                aggs = list(self.client.list_aggs(
                    ticker=ticker.upper(),
                    multiplier=1,
                    timespan="month",
                    from_=start_date.isoformat(),
                    to=end_date.isoformat(),
                    adjusted=True,
                    limit=50000
                ))

                if not aggs:
                    logger.warning(f"No monthly data for {ticker}")
                    return pd.DataFrame()

                data = [{
                    'timestamp': datetime.fromtimestamp(a.timestamp / 1000),
                    'open': a.open,
                    'high': a.high,
                    'low': a.low,
                    'close': a.close,
                    'volume': a.volume
                } for a in aggs]

                df = pd.DataFrame(data)
                df['date'] = df['timestamp'].dt.date
                return df.sort_values('timestamp').reset_index(drop=True)

            except Exception as e:
                logger.warning(f"Monthly bars attempt {attempt + 1} failed: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY)
                else:
                    logger.error(f"Error fetching monthly bars for {ticker}: {e}")
                    return pd.DataFrame()

        return pd.DataFrame()


# Singleton instance
_client: Optional[PolygonClient] = None


def get_polygon_client() -> PolygonClient:
    """Get or create the Polygon client singleton."""
    global _client
    if _client is None:
        _client = PolygonClient()
    return _client
