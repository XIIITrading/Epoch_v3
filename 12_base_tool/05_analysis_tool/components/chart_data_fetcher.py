"""
Chart Data Fetcher for Epoch Analysis Tool PDF Reports.

Ported from: 02_zone_system/08_visualization/data_readers/polygon_fetcher.py

Fetches H1 candle data and epoch volume profile from Polygon API
for visualization in PDF reports.

Supports market time mode (Pre-Market/Post-Market/Live) via end_timestamp
parameter to ensure data cutoff at the correct time.
"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime, date, timedelta
from math import floor, ceil
from typing import Dict, Optional, Tuple

import pandas as pd

from data import get_polygon_client
from config.visualization_config import (
    CANDLE_BAR_COUNT, CANDLE_TIMEFRAME,
    VBP_TIMEFRAME, VBP_GRANULARITY
)

logger = logging.getLogger(__name__)


@dataclass
class ChartData:
    """Container for chart-ready data."""
    ticker: str
    candle_bars: pd.DataFrame       # H1 OHLCV for candlesticks
    volume_profile: Dict[float, float]  # Full epoch VbP at $0.01
    epoch_start_date: str           # User-defined start date
    epoch_high: float               # Highest price in epoch
    epoch_low: float                # Lowest price in epoch
    candle_count: int
    vbp_bar_count: int

    @property
    def candle_price_range(self) -> Tuple[float, float]:
        """Get price range from visible candles."""
        if self.candle_bars.empty:
            return (0, 0)
        return (self.candle_bars['low'].min(), self.candle_bars['high'].max())

    @property
    def current_price(self) -> float:
        """Get current price (last close)."""
        if self.candle_bars.empty:
            return 0
        return float(self.candle_bars['close'].iloc[-1])


class ChartDataFetcher:
    """
    Fetch H1 candle data and volume profile from Polygon API.

    Matches Excel system: 02_zone_system/08_visualization/data_readers/polygon_fetcher.py
    """

    # API rate limiting
    API_DELAY = 0.25  # Seconds between API calls

    def __init__(self):
        """Initialize with Polygon client."""
        self.client = get_polygon_client()

    def fetch_chart_data(
        self,
        ticker: str,
        epoch_start_date: date,
        candle_bars: int = CANDLE_BAR_COUNT,
        candle_tf: int = CANDLE_TIMEFRAME,
        vbp_tf: int = VBP_TIMEFRAME,
        end_timestamp: datetime = None
    ) -> ChartData:
        """
        Fetch all data needed for chart visualization.

        Args:
            ticker: Stock symbol (e.g., "TSLA")
            epoch_start_date: Start date for VbP calculation
            candle_bars: Number of H1 candles (default 120)
            candle_tf: Candle timeframe in minutes (default 60)
            vbp_tf: VbP bar timeframe in minutes (default 15)
            end_timestamp: Optional precise end timestamp for pre/post market mode.
                          If provided, data is filtered to only include bars
                          before this timestamp.

        Returns:
            ChartData with candles and epoch VbP
        """
        ticker = ticker.upper().strip()
        end_date = date.today()

        logger.info(f"Fetching chart data for {ticker}")
        if end_timestamp:
            logger.debug(f"  Epoch: {epoch_start_date} to {end_timestamp}")
        else:
            logger.debug(f"  Epoch: {epoch_start_date} to {end_date}")

        # Fetch H1 candles (recent bars for display)
        logger.debug(f"  Fetching {candle_bars} H1 candles...")
        candles = self._fetch_recent_bars(ticker, candle_bars, candle_tf, end_timestamp)
        logger.debug(f"  Got {len(candles)} candles")

        # Fetch VbP bars for full epoch
        logger.debug(f"  Fetching M{vbp_tf} bars for epoch VbP...")
        vbp_bars = self._fetch_epoch_bars(ticker, epoch_start_date, end_date, vbp_tf, end_timestamp)
        logger.debug(f"  Got {len(vbp_bars)} VbP bars")

        # Calculate epoch high/low from VbP bars
        if not vbp_bars.empty:
            epoch_high = float(vbp_bars['high'].max())
            epoch_low = float(vbp_bars['low'].min())
        else:
            epoch_high = 0
            epoch_low = 0

        logger.debug(f"  Epoch range: ${epoch_low:.2f} - ${epoch_high:.2f}")

        # Build volume profile at $0.01 granularity
        volume_profile = self._build_volume_profile(vbp_bars, VBP_GRANULARITY)
        logger.debug(f"  Built VbP with {len(volume_profile)} price levels")

        return ChartData(
            ticker=ticker,
            candle_bars=candles,
            volume_profile=volume_profile,
            epoch_start_date=epoch_start_date.strftime('%Y-%m-%d') if isinstance(epoch_start_date, date) else str(epoch_start_date),
            epoch_high=epoch_high,
            epoch_low=epoch_low,
            candle_count=len(candles),
            vbp_bar_count=len(vbp_bars)
        )

    def _fetch_recent_bars(
        self,
        ticker: str,
        n_bars: int,
        timeframe_minutes: int,
        end_timestamp: datetime = None
    ) -> pd.DataFrame:
        """
        Fetch the most recent N bars for candlestick display.

        Args:
            ticker: Stock symbol
            n_bars: Number of bars to fetch
            timeframe_minutes: Bar size in minutes (60 for H1)
            end_timestamp: Optional precise end timestamp for pre/post market mode

        Returns:
            DataFrame with OHLCV data
        """
        end_date = date.today()
        # For 120 H1 bars, need ~20 calendar days (accounting for weekends/holidays)
        days_needed = max(30, (n_bars * timeframe_minutes) // (6.5 * 60) + 10)
        start_date = end_date - timedelta(days=days_needed)

        bars = self._fetch_bars(ticker, start_date, end_date, timeframe_minutes, end_timestamp)

        if not bars.empty:
            bars = bars.tail(n_bars).copy()

        return bars

    def _fetch_epoch_bars(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
        timeframe_minutes: int,
        end_timestamp: datetime = None
    ) -> pd.DataFrame:
        """
        Fetch bars for the full epoch period (for VbP calculation).
        Uses chunked requests for long periods.

        Args:
            ticker: Stock symbol
            start_date: Epoch start date
            end_date: End date
            timeframe_minutes: Bar size in minutes
            end_timestamp: Optional precise end timestamp for pre/post market mode

        Returns:
            DataFrame with OHLCV data for full epoch
        """
        all_data = []
        current_start = start_date
        chunk_days = 30  # Fetch in 30-day chunks

        # Determine actual end date for chunking
        if end_timestamp is not None:
            actual_end_date = end_timestamp.date()
        else:
            actual_end_date = end_date

        while current_start < actual_end_date:
            chunk_end = min(current_start + timedelta(days=chunk_days), actual_end_date)

            # On the last chunk, use end_timestamp if provided
            is_last_chunk = chunk_end >= actual_end_date
            chunk_end_timestamp = end_timestamp if (is_last_chunk and end_timestamp) else None

            try:
                chunk_data = self._fetch_bars(
                    ticker,
                    current_start,
                    chunk_end,
                    timeframe_minutes,
                    chunk_end_timestamp
                )

                if not chunk_data.empty:
                    all_data.append(chunk_data)

                # Rate limiting
                time.sleep(self.API_DELAY)

            except Exception as e:
                logger.warning(f"Chunk failed for {ticker}: {e}")

            current_start = chunk_end

        if all_data:
            combined = pd.concat(all_data)
            combined = combined[~combined.index.duplicated(keep='first')]
            combined = combined.sort_index()
            return combined

        return pd.DataFrame()

    def _fetch_bars(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
        timeframe_minutes: int,
        end_timestamp: datetime = None
    ) -> pd.DataFrame:
        """
        Fetch bars from Polygon API.

        Args:
            ticker: Stock symbol
            start_date: Start date
            end_date: End date
            timeframe_minutes: Bar size in minutes
            end_timestamp: Optional precise end timestamp for pre/post market mode

        Returns:
            DataFrame with OHLCV data
        """
        try:
            # Use the underlying Polygon client
            raw_client = self.client.client

            # Determine timespan
            if timeframe_minutes >= 60:
                multiplier = timeframe_minutes // 60
                timespan = "hour"
            else:
                multiplier = timeframe_minutes
                timespan = "minute"

            # Determine to_param: use Unix ms if end_timestamp provided
            if end_timestamp is not None:
                to_param = int(end_timestamp.timestamp() * 1000)  # Unix ms
            else:
                to_param = end_date.strftime('%Y-%m-%d')

            # Fetch aggregates
            aggs = raw_client.get_aggs(
                ticker=ticker,
                multiplier=multiplier,
                timespan=timespan,
                from_=start_date.strftime('%Y-%m-%d'),
                to=to_param,
                adjusted=True,
                sort="asc",
                limit=50000
            )

            if not aggs:
                return pd.DataFrame()

            # Convert to DataFrame
            data = []
            for agg in aggs:
                data.append({
                    'timestamp': pd.to_datetime(agg.timestamp, unit='ms', utc=True),
                    'open': agg.open,
                    'high': agg.high,
                    'low': agg.low,
                    'close': agg.close,
                    'volume': agg.volume
                })

            df = pd.DataFrame(data)

            if df.empty:
                return df

            # Convert timestamp to Eastern time
            df['timestamp'] = df['timestamp'].dt.tz_convert('America/New_York')
            df.set_index('timestamp', inplace=True)

            return df

        except Exception as e:
            logger.warning(f"Failed to fetch bars for {ticker}: {e}")
            return pd.DataFrame()

    def _build_volume_profile(
        self,
        bars: pd.DataFrame,
        granularity: float = 0.01
    ) -> Dict[float, float]:
        """
        Build volume profile at specified price granularity.

        Distributes each bar's volume proportionally across all price levels
        touched by that bar.

        Args:
            bars: OHLCV DataFrame
            granularity: Price level granularity (default $0.01)

        Returns:
            Dict mapping price level to accumulated volume
        """
        volume_profile = {}

        if bars.empty:
            return volume_profile

        for _, bar in bars.iterrows():
            bar_low = bar['low']
            bar_high = bar['high']
            bar_volume = bar['volume']

            # Skip invalid bars
            if bar_volume <= 0 or bar_high <= bar_low:
                continue
            if pd.isna(bar_low) or pd.isna(bar_high) or pd.isna(bar_volume):
                continue

            # Round to granularity boundaries
            low_level = floor(bar_low / granularity) * granularity
            high_level = ceil(bar_high / granularity) * granularity

            # Count number of levels
            num_levels = int(round((high_level - low_level) / granularity)) + 1

            if num_levels <= 0:
                continue

            # Distribute volume evenly
            volume_per_level = bar_volume / num_levels

            # Add volume to each level
            current = low_level
            for _ in range(num_levels):
                price_key = round(current, 2)
                volume_profile[price_key] = volume_profile.get(price_key, 0) + volume_per_level
                current += granularity

        return volume_profile


# =========================================================================
# CONVENIENCE FUNCTION
# =========================================================================

def fetch_chart_data(
    ticker: str,
    epoch_start_date: date,
    candle_bars: int = CANDLE_BAR_COUNT,
    vbp_tf: int = VBP_TIMEFRAME,
    end_timestamp: datetime = None
) -> ChartData:
    """
    Fetch chart data for PDF visualization.

    Args:
        ticker: Stock symbol
        epoch_start_date: Epoch start date for volume profile
        candle_bars: Number of H1 candles (default 120)
        vbp_tf: VbP timeframe in minutes (default 15)
        end_timestamp: Optional precise end timestamp for pre/post market mode.
                      If provided, data is filtered to only include bars
                      before this timestamp.

    Returns:
        ChartData with candles and volume profile
    """
    fetcher = ChartDataFetcher()
    return fetcher.fetch_chart_data(
        ticker=ticker,
        epoch_start_date=epoch_start_date,
        candle_bars=candle_bars,
        vbp_tf=vbp_tf,
        end_timestamp=end_timestamp
    )
