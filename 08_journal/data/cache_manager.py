"""
Bar data cache using Streamlit session state.
Adapted from 06_training/data/cache_manager.py.

Cache key: {TICKER}_{DATE_ISO}
Stores BarData objects to avoid redundant Polygon API calls.

Includes bar slicing for pre-trade (evaluate) and post-trade (reveal) modes,
and prefetching for upcoming trades in the flashcard queue.
"""

import streamlit as st
import pandas as pd
import pytz
import logging
from datetime import date, datetime, time, timedelta
from typing import Optional, List, Dict

from data.polygon_client import BarData, get_polygon_client

logger = logging.getLogger(__name__)

CACHE_KEY = "bar_cache"
STATS_KEY = "cache_stats"

ET = pytz.timezone('America/New_York')


class BarCache:
    """Session-state cache for bar data with slicing support."""

    def __init__(self):
        if CACHE_KEY not in st.session_state:
            st.session_state[CACHE_KEY] = {}
        if STATS_KEY not in st.session_state:
            st.session_state[STATS_KEY] = {"hits": 0, "misses": 0}

    @staticmethod
    def _make_key(ticker: str, trade_date: date) -> str:
        return f"{ticker.upper()}_{trade_date.isoformat()}"

    def get_bars(
        self,
        ticker: str,
        trade_date: date,
        trade=None,
    ) -> Optional[BarData]:
        """
        Get bar data from cache or fetch from Polygon.

        Args:
            ticker: Stock symbol
            trade_date: Date of the trade
            trade: Optional Trade object for M1 windowing

        Returns:
            BarData or None if fetch fails
        """
        key = self._make_key(ticker, trade_date)
        cache = st.session_state[CACHE_KEY]

        if key in cache:
            st.session_state[STATS_KEY]["hits"] += 1
            return cache[key]

        # Cache miss — fetch from Polygon
        st.session_state[STATS_KEY]["misses"] += 1
        client = get_polygon_client()
        bar_data = client.fetch_bars_for_trade(ticker, trade_date, trade=trade)

        if bar_data.is_valid:
            cache[key] = bar_data
            return bar_data

        logger.warning(f"Failed to fetch valid bar data for {ticker} on {trade_date}")
        return None

    # =========================================================================
    # BAR SLICING — For pre-trade / post-trade modes
    # =========================================================================

    @staticmethod
    def _make_aware(trade_date: date, t: time) -> datetime:
        """Combine date + time into timezone-aware datetime (ET)."""
        naive = datetime.combine(trade_date, t)
        return ET.localize(naive)

    def slice_bars_to_time(
        self,
        bar_data: BarData,
        end_time: time,
        include_end: bool = True,
        max_bars: int = 120,
    ) -> Dict[str, pd.DataFrame]:
        """
        PRE-TRADE MODE: Slice all timeframe bars up to entry time.
        Returns dict with keys: 'bars_1m', 'bars_15m', 'bars_1h'

        M1 is limited to 60 bars; H1/M15 use max_bars (120).
        """
        end_dt = self._make_aware(bar_data.trade_date, end_time)

        # Per-timeframe bar limits: M1 gets fewer bars for readability
        bar_limits = {
            'bars_1m': 60,
            'bars_15m': max_bars,
            'bars_1h': max_bars,
        }

        result = {}
        for key, df in [('bars_1m', bar_data.bars_1m), ('bars_15m', bar_data.bars_15m), ('bars_1h', bar_data.bars_1h)]:
            if df.empty:
                result[key] = df
                continue

            if include_end:
                sliced = df[df.index <= end_dt]
            else:
                sliced = df[df.index < end_dt]

            # Limit bars per timeframe
            limit = bar_limits.get(key, max_bars)
            if len(sliced) > limit:
                sliced = sliced.tail(limit)

            result[key] = sliced

        return result

    def slice_bars_for_reveal(
        self,
        bar_data: BarData,
        entry_time: time,
        exit_time: time,
        context_bars: int = 60,
        buffer_bars: int = 10,
    ) -> Dict[str, pd.DataFrame]:
        """
        POST-TRADE MODE: Show bars from context before entry through exit + buffer.
        Returns dict with keys: 'bars_1m', 'bars_15m', 'bars_1h'
        """
        entry_dt = self._make_aware(bar_data.trade_date, entry_time)
        exit_dt = self._make_aware(bar_data.trade_date, exit_time)

        result = {}
        for key, df in [('bars_1m', bar_data.bars_1m), ('bars_15m', bar_data.bars_15m), ('bars_1h', bar_data.bars_1h)]:
            if df.empty:
                result[key] = df
                continue

            # Find bars before entry for context
            pre_entry = df[df.index <= entry_dt]
            if len(pre_entry) > context_bars:
                start_idx = pre_entry.index[-context_bars]
            elif len(pre_entry) > 0:
                start_idx = pre_entry.index[0]
            else:
                start_idx = df.index[0] if len(df) > 0 else None

            if start_idx is None:
                result[key] = df
                continue

            # Find end: exit + buffer_bars
            post_exit = df[df.index > exit_dt]
            if len(post_exit) >= buffer_bars:
                end_idx = post_exit.index[buffer_bars - 1]
            elif len(post_exit) > 0:
                end_idx = post_exit.index[-1]
            else:
                end_idx = df.index[-1] if len(df) > 0 else exit_dt

            result[key] = df[(df.index >= start_idx) & (df.index <= end_idx)]

        return result

    # =========================================================================
    # PREFETCHING — Load bars for upcoming trades in background
    # =========================================================================

    def prefetch_for_trades(self, upcoming_trades: List) -> None:
        """
        Proactively fetch bar data for upcoming trades.
        Deduplicates by (ticker, date) to avoid redundant API calls.

        Args:
            upcoming_trades: List of JournalTradeWithMetrics objects
        """
        seen = set()
        for twm in upcoming_trades:
            key = self._make_key(twm.ticker, twm.date)
            if key in seen or key in st.session_state[CACHE_KEY]:
                continue
            seen.add(key)

            try:
                self.get_bars(twm.ticker, twm.date)
            except Exception as e:
                logger.warning(f"Prefetch failed for {twm.ticker} on {twm.date}: {e}")

    def clear(self):
        """Clear all cached bar data."""
        st.session_state[CACHE_KEY] = {}
        st.session_state[STATS_KEY] = {"hits": 0, "misses": 0}
