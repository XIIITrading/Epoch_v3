"""
Epoch Trading System - Bar Cache Manager
Caches Polygon bar data to minimize API calls.
"""

import streamlit as st
import pandas as pd
from datetime import date, datetime
from typing import Dict, Optional, List
import logging
import pytz

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import PREFETCH_COUNT, DISPLAY_TIMEZONE
from data.polygon_client import PolygonClient, BarData, get_polygon_client
from models.trade import TradeWithMetrics

logger = logging.getLogger(__name__)


class BarCache:
    """
    Manages bar data caching in Streamlit session state.

    Key insight: Trades on the same symbol/date share the same bar data.
    We cache by symbol+date and slice differently per trade.
    """

    def __init__(self, polygon_client: Optional[PolygonClient] = None):
        """Initialize cache with polygon client."""
        self.polygon = polygon_client or get_polygon_client()
        self._init_cache()

    def _init_cache(self):
        """Initialize cache in session state."""
        if 'bar_cache' not in st.session_state:
            st.session_state.bar_cache = {}
        if 'cache_stats' not in st.session_state:
            st.session_state.cache_stats = {'hits': 0, 'misses': 0}

    def _cache_key(self, ticker: str, trade_date: date) -> str:
        """Generate cache key for symbol+date."""
        return f"{ticker.upper()}_{trade_date.isoformat()}"

    def get_bars_for_trade(
        self,
        ticker: str,
        trade_date: date,
        candle_count: int = 120
    ) -> Optional[BarData]:
        """
        Get bar data for a trade, using cache when available.

        Args:
            ticker: Stock symbol
            trade_date: Date of the trade
            candle_count: Number of candles per timeframe

        Returns:
            BarData object or None if fetch fails
        """
        self._init_cache()
        cache_key = self._cache_key(ticker, trade_date)

        # Check cache
        if cache_key in st.session_state.bar_cache:
            st.session_state.cache_stats['hits'] += 1
            logger.debug(f"Cache hit for {cache_key}")
            return st.session_state.bar_cache[cache_key]

        # Fetch from Polygon
        st.session_state.cache_stats['misses'] += 1
        logger.debug(f"Cache miss for {cache_key}, fetching...")

        bar_data = self.polygon.fetch_bars_for_trade(
            ticker=ticker,
            trade_date=trade_date,
            candle_count=candle_count
        )

        if bar_data and bar_data.is_valid:
            st.session_state.bar_cache[cache_key] = bar_data
            return bar_data

        logger.warning(f"Failed to fetch bars for {cache_key}")
        return None

    def prefetch_for_trades(self, upcoming_trades: List[TradeWithMetrics]):
        """
        Prefetch bar data for upcoming trades.
        Call this while user is reviewing current trade.

        Args:
            upcoming_trades: List of upcoming trades to prefetch
        """
        self._init_cache()

        # Get unique symbol+date combinations
        seen = set()
        to_fetch = []

        for trade in upcoming_trades[:PREFETCH_COUNT]:
            key = (trade.ticker, trade.date)
            if key not in seen:
                seen.add(key)
                cache_key = self._cache_key(trade.ticker, trade.date)
                if cache_key not in st.session_state.bar_cache:
                    to_fetch.append(key)

        # Fetch in background (will block but that's OK during reveal mode)
        for ticker, trade_date in to_fetch:
            logger.info(f"Prefetching bars for {ticker} on {trade_date}")
            self.get_bars_for_trade(ticker, trade_date)

    def _make_tz_aware(self, dt: datetime) -> datetime:
        """Make a datetime timezone-aware using the display timezone."""
        if dt.tzinfo is None:
            tz = pytz.timezone(DISPLAY_TIMEZONE)
            return tz.localize(dt)
        return dt

    def slice_bars_to_time(
        self,
        bar_data: BarData,
        end_time: datetime,
        include_end: bool = True,
        max_bars: int = 120
    ) -> Dict[str, pd.DataFrame]:
        """
        Slice bar data to end at a specific time.
        Used for evaluate mode to hide future bars.
        Returns up to max_bars ending at or before end_time.

        Args:
            bar_data: Full bar data
            end_time: Time to slice to
            include_end: Whether to include the bar at end_time
            max_bars: Maximum number of bars to return per timeframe

        Returns:
            Dict with sliced DataFrames for each timeframe
        """
        result = {}

        # Make end_time timezone-aware if needed
        end_time = self._make_tz_aware(end_time)

        for tf_name, df in [
            ('5m', bar_data.bars_5m),
            ('15m', bar_data.bars_15m),
            ('1h', bar_data.bars_1h)
        ]:
            if df.empty:
                result[tf_name] = df
                continue

            if include_end:
                sliced = df[df.index <= end_time]
            else:
                sliced = df[df.index < end_time]

            # Limit to max_bars (take the most recent ones before end_time)
            if len(sliced) > max_bars:
                sliced = sliced.tail(max_bars)

            result[tf_name] = sliced

        return result

    def slice_bars_for_reveal(
        self,
        bar_data: BarData,
        entry_time: datetime,
        exit_time: datetime,
        context_bars: int = 60,
        buffer_bars: int = 10
    ) -> Dict[str, pd.DataFrame]:
        """
        Slice bar data for reveal mode.
        Shows context before entry through exit + buffer.

        Args:
            bar_data: Full bar data
            entry_time: Trade entry time
            exit_time: Trade exit time
            context_bars: How many bars of context before entry
            buffer_bars: How many bars after exit to show

        Returns:
            Dict with sliced DataFrames for each timeframe
        """
        result = {}

        # Make times timezone-aware if needed
        entry_time = self._make_tz_aware(entry_time)
        exit_time = self._make_tz_aware(exit_time)

        for tf_name, df in [
            ('5m', bar_data.bars_5m),
            ('15m', bar_data.bars_15m),
            ('1h', bar_data.bars_1h)
        ]:
            if df.empty:
                result[tf_name] = df
                continue

            # Find entry index
            entry_mask = df.index <= entry_time
            if not entry_mask.any():
                result[tf_name] = df
                continue

            entry_idx = entry_mask.sum() - 1

            # Calculate start and end indices
            start_idx = max(0, entry_idx - context_bars)

            # Find exit index and add buffer
            exit_mask = df.index <= exit_time
            exit_idx = exit_mask.sum()
            end_idx = min(len(df), exit_idx + buffer_bars)

            result[tf_name] = df.iloc[start_idx:end_idx]

        return result

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache hit/miss statistics."""
        self._init_cache()
        return dict(st.session_state.cache_stats)

    def clear_cache(self):
        """Clear the bar cache."""
        if 'bar_cache' in st.session_state:
            st.session_state.bar_cache = {}
        if 'cache_stats' in st.session_state:
            st.session_state.cache_stats = {'hits': 0, 'misses': 0}
        logger.info("Bar cache cleared")


# Singleton instance
_cache = None


def get_bar_cache() -> BarCache:
    """Get or create the bar cache singleton."""
    global _cache
    if _cache is None:
        _cache = BarCache()
    return _cache
