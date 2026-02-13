"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
Entry Indicators - M1 Bar Data Access Layer
XIII Trading LLC
================================================================================

Fetches 1-minute bar data from the m1_bars database table.
Falls back to Polygon API if data is not available in the database.

Version: 1.0.0
================================================================================
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, date, time, timedelta
from typing import List, Dict, Optional, Tuple
import requests
import time as time_module
import pytz

from config import (
    DB_CONFIG,
    M1_BARS_TABLE,
    POLYGON_API_KEY,
    POLYGON_BASE_URL,
    API_DELAY,
    API_RETRIES,
    API_RETRY_DELAY,
    MARKET_OPEN,
    MARKET_CLOSE
)

# Extended hours constants for prior day bar fetching
PRIOR_DAY_START = time(16, 0)  # Start from 4 PM prior day
PRIOR_DAY_END = time(20, 0)    # End at 8 PM prior day
PREMARKET_START = time(4, 0)   # 4 AM premarket
AFTERHOURS_END = time(20, 0)   # 8 PM after-hours

# Minimum M5 bars needed for SMA21 calculation
MIN_M5_BARS_NEEDED = 25


class M1DataProvider:
    """
    Provides access to 1-minute bar data from database or API.

    Primary source: m1_bars table in Supabase
    Fallback: Polygon.io API
    """

    ET = pytz.timezone('America/New_York')

    def __init__(self, conn=None, use_api_fallback: bool = True):
        """
        Initialize the M1 data provider.

        Args:
            conn: Optional existing database connection
            use_api_fallback: If True, fetch from Polygon if DB has no data
        """
        self._conn = conn
        self._owns_connection = False
        self.use_api_fallback = use_api_fallback
        self.last_request_time = 0
        self._cache: Dict[str, List[Dict]] = {}

    def _get_connection(self):
        """Get or create database connection."""
        if self._conn is None:
            self._conn = psycopg2.connect(**DB_CONFIG)
            self._owns_connection = True
        return self._conn

    def close(self):
        """Close database connection if we own it."""
        if self._owns_connection and self._conn:
            self._conn.close()
            self._conn = None

    def _get_cache_key(self, ticker: str, trade_date: date) -> str:
        """Generate cache key for ticker-date."""
        return f"{ticker}_{trade_date.strftime('%Y%m%d')}"

    def _rate_limit(self):
        """Enforce rate limiting for API calls."""
        if API_DELAY > 0:
            elapsed = time_module.time() - self.last_request_time
            if elapsed < API_DELAY:
                time_module.sleep(API_DELAY - elapsed)
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
        if isinstance(date_input, date) and not isinstance(date_input, datetime):
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

    # =========================================================================
    # DATABASE FETCHING
    # =========================================================================

    def fetch_from_db(
        self,
        ticker: str,
        trade_date: date,
        start_time: time = None,
        end_time: time = None
    ) -> List[Dict]:
        """
        Fetch M1 bars from the m1_bars database table.

        Args:
            ticker: Stock symbol
            trade_date: Trading date
            start_time: Optional start time filter
            end_time: Optional end time filter

        Returns:
            List of bar dictionaries sorted by time
        """
        conn = self._get_connection()

        query = f"""
            SELECT
                ticker,
                bar_date,
                bar_time,
                bar_timestamp,
                open,
                high,
                low,
                close,
                volume,
                vwap
            FROM {M1_BARS_TABLE}
            WHERE ticker = %s
              AND bar_date = %s
        """
        params = [ticker.upper(), trade_date]

        if start_time:
            query += " AND bar_time >= %s"
            params.append(start_time)

        if end_time:
            query += " AND bar_time <= %s"
            params.append(end_time)

        query += " ORDER BY bar_time ASC"

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                rows = cur.fetchall()

            bars = []
            for row in rows:
                bar = {
                    'timestamp': row['bar_timestamp'],
                    'bar_date': row['bar_date'],
                    'bar_time': row['bar_time'],
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': int(row['volume']),
                    'vwap': float(row['vwap']) if row['vwap'] else None
                }
                bars.append(bar)

            return bars

        except Exception as e:
            print(f"Error fetching M1 bars from DB: {e}")
            return []

    def has_data_in_db(self, ticker: str, trade_date: date) -> bool:
        """
        Check if M1 bar data exists in the database for a ticker-date.

        Args:
            ticker: Stock symbol
            trade_date: Trading date

        Returns:
            True if data exists
        """
        conn = self._get_connection()

        query = f"""
            SELECT COUNT(*) as cnt
            FROM {M1_BARS_TABLE}
            WHERE ticker = %s AND bar_date = %s
        """

        try:
            with conn.cursor() as cur:
                cur.execute(query, [ticker.upper(), trade_date])
                row = cur.fetchone()
                return row[0] > 0
        except Exception:
            return False

    def fetch_extended_from_db(
        self,
        ticker: str,
        trade_date: date,
        include_premarket: bool = True,
        include_afterhours: bool = True
    ) -> List[Dict]:
        """
        Fetch M1 bars with extended hours, starting from prior day 16:00.

        This ensures sufficient bars for SMA21 calculation at market open.
        Fetches from prior trading day 16:00 through trade day end.

        Args:
            ticker: Stock symbol
            trade_date: Trading date
            include_premarket: Include premarket (04:00-09:30)
            include_afterhours: Include after-hours (16:00-20:00)

        Returns:
            List of M1 bar dictionaries with extended coverage
        """
        conn = self._get_connection()
        trade_dt = self._parse_date(trade_date)
        prior_day = self._get_prior_trading_day(trade_dt)

        # Fetch from prior day and trade day
        query = f"""
            SELECT
                ticker,
                bar_date,
                bar_time,
                bar_timestamp,
                open,
                high,
                low,
                close,
                volume,
                vwap
            FROM {M1_BARS_TABLE}
            WHERE ticker = %s
              AND bar_date IN (%s, %s)
            ORDER BY bar_date ASC, bar_time ASC
        """

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, [ticker.upper(), prior_day, trade_dt])
                rows = cur.fetchall()

            if not rows:
                return []

            # Filter based on time criteria
            filtered_bars = []

            for row in rows:
                bar_date = row['bar_date']
                bar_time = row['bar_time']

                # Prior day: only include after-hours (16:00-20:00)
                if bar_date == prior_day:
                    if PRIOR_DAY_START <= bar_time <= PRIOR_DAY_END:
                        bar = self._row_to_bar(row)
                        filtered_bars.append(bar)

                # Trade day: include based on flags
                elif bar_date == trade_dt:
                    # Regular trading hours always included (09:30-16:00)
                    if MARKET_OPEN <= bar_time <= MARKET_CLOSE:
                        bar = self._row_to_bar(row)
                        filtered_bars.append(bar)
                    # Premarket (04:00-09:30)
                    elif include_premarket and PREMARKET_START <= bar_time < MARKET_OPEN:
                        bar = self._row_to_bar(row)
                        filtered_bars.append(bar)
                    # After-hours (16:00-20:00)
                    elif include_afterhours and MARKET_CLOSE < bar_time <= AFTERHOURS_END:
                        bar = self._row_to_bar(row)
                        filtered_bars.append(bar)

            return filtered_bars

        except Exception as e:
            print(f"Error fetching extended M1 bars from DB: {e}")
            return []

    def _row_to_bar(self, row: Dict) -> Dict:
        """Convert a database row to a bar dictionary."""
        return {
            'timestamp': row['bar_timestamp'],
            'bar_date': row['bar_date'],
            'bar_time': row['bar_time'],
            'open': float(row['open']),
            'high': float(row['high']),
            'low': float(row['low']),
            'close': float(row['close']),
            'volume': int(row['volume']),
            'vwap': float(row['vwap']) if row['vwap'] else None
        }

    # =========================================================================
    # POLYGON API FETCHING
    # =========================================================================

    def fetch_from_api(
        self,
        ticker: str,
        trade_date: date,
        start_time: time = None,
        end_time: time = None
    ) -> List[Dict]:
        """
        Fetch M1 bars from Polygon API.

        Args:
            ticker: Stock symbol
            trade_date: Trading date
            start_time: Optional start time filter
            end_time: Optional end time filter

        Returns:
            List of bar dictionaries sorted by time
        """
        date_str = trade_date.strftime('%Y-%m-%d')
        url = f"{POLYGON_BASE_URL}/v2/aggs/ticker/{ticker}/range/1/minute/{date_str}/{date_str}"

        params = {
            'apiKey': POLYGON_API_KEY,
            'adjusted': 'true',
            'sort': 'asc',
            'limit': 50000
        }

        for attempt in range(API_RETRIES):
            try:
                self._rate_limit()
                response = requests.get(url, params=params, timeout=30)

                if response.status_code == 429:
                    wait_time = API_RETRY_DELAY * (attempt + 1)
                    time_module.sleep(wait_time)
                    continue

                if response.status_code != 200:
                    return []

                data = response.json()

                if data.get('status') not in ['OK', 'DELAYED']:
                    return []

                if 'results' not in data or not data['results']:
                    return []

                bars = []
                for result in data['results']:
                    # Convert timestamp to ET
                    ts_ms = result['t']
                    utc_dt = datetime.utcfromtimestamp(ts_ms / 1000)
                    utc_dt = utc_dt.replace(tzinfo=pytz.UTC)
                    et_dt = utc_dt.astimezone(self.ET)
                    bar_date = et_dt.date()
                    bar_time = et_dt.time()

                    # Filter by trading hours
                    if bar_time < MARKET_OPEN or bar_time > MARKET_CLOSE:
                        continue

                    # Filter by specified time range
                    if start_time and bar_time < start_time:
                        continue
                    if end_time and bar_time > end_time:
                        continue

                    bar = {
                        'timestamp': et_dt,
                        'bar_date': bar_date,
                        'bar_time': bar_time,
                        'open': result['o'],
                        'high': result['h'],
                        'low': result['l'],
                        'close': result['c'],
                        'volume': int(result['v']),
                        'vwap': result.get('vw')
                    }
                    bars.append(bar)

                return bars

            except requests.exceptions.Timeout:
                time_module.sleep(API_RETRY_DELAY)
            except Exception as e:
                return []

        return []

    def fetch_extended_from_api(
        self,
        ticker: str,
        trade_date: date,
        include_premarket: bool = True,
        include_afterhours: bool = True
    ) -> List[Dict]:
        """
        Fetch M1 bars from Polygon API with extended hours, starting from prior day 16:00.

        Args:
            ticker: Stock symbol
            trade_date: Trading date
            include_premarket: Include premarket (04:00-09:30)
            include_afterhours: Include after-hours (16:00-20:00)

        Returns:
            List of M1 bar dictionaries with extended coverage
        """
        trade_dt = self._parse_date(trade_date)
        prior_day = self._get_prior_trading_day(trade_dt)

        # Fetch from prior trading day through trade day
        # Use prior_day directly (not prior calendar day) to handle weekends
        from_date = prior_day.strftime('%Y-%m-%d')
        to_date = trade_dt.strftime('%Y-%m-%d')

        url = f"{POLYGON_BASE_URL}/v2/aggs/ticker/{ticker}/range/1/minute/{from_date}/{to_date}"

        params = {
            'apiKey': POLYGON_API_KEY,
            'adjusted': 'true',
            'sort': 'asc',
            'limit': 50000
        }

        for attempt in range(API_RETRIES):
            try:
                self._rate_limit()
                response = requests.get(url, params=params, timeout=30)

                if response.status_code == 429:
                    wait_time = API_RETRY_DELAY * (attempt + 1)
                    time_module.sleep(wait_time)
                    continue

                if response.status_code != 200:
                    return []

                data = response.json()

                if data.get('status') not in ['OK', 'DELAYED']:
                    return []

                if 'results' not in data or not data['results']:
                    return []

                # Filter based on time criteria
                filtered_bars = []

                for result in data['results']:
                    # Convert timestamp to ET
                    ts_ms = result['t']
                    utc_dt = datetime.utcfromtimestamp(ts_ms / 1000)
                    utc_dt = utc_dt.replace(tzinfo=pytz.UTC)
                    et_dt = utc_dt.astimezone(self.ET)
                    bar_date = et_dt.date()
                    bar_time = et_dt.time()

                    # Prior day: only include after-hours (16:00-20:00)
                    if bar_date == prior_day:
                        if PRIOR_DAY_START <= bar_time <= PRIOR_DAY_END:
                            bar = {
                                'timestamp': et_dt,
                                'bar_date': bar_date,
                                'bar_time': bar_time,
                                'open': result['o'],
                                'high': result['h'],
                                'low': result['l'],
                                'close': result['c'],
                                'volume': int(result['v']),
                                'vwap': result.get('vw')
                            }
                            filtered_bars.append(bar)

                    # Trade day: include based on flags
                    elif bar_date == trade_dt:
                        # Regular trading hours always included (09:30-16:00)
                        if MARKET_OPEN <= bar_time <= MARKET_CLOSE:
                            bar = {
                                'timestamp': et_dt,
                                'bar_date': bar_date,
                                'bar_time': bar_time,
                                'open': result['o'],
                                'high': result['h'],
                                'low': result['l'],
                                'close': result['c'],
                                'volume': int(result['v']),
                                'vwap': result.get('vw')
                            }
                            filtered_bars.append(bar)
                        # Premarket (04:00-09:30)
                        elif include_premarket and PREMARKET_START <= bar_time < MARKET_OPEN:
                            bar = {
                                'timestamp': et_dt,
                                'bar_date': bar_date,
                                'bar_time': bar_time,
                                'open': result['o'],
                                'high': result['h'],
                                'low': result['l'],
                                'close': result['c'],
                                'volume': int(result['v']),
                                'vwap': result.get('vw')
                            }
                            filtered_bars.append(bar)
                        # After-hours (16:00-20:00)
                        elif include_afterhours and MARKET_CLOSE < bar_time <= AFTERHOURS_END:
                            bar = {
                                'timestamp': et_dt,
                                'bar_date': bar_date,
                                'bar_time': bar_time,
                                'open': result['o'],
                                'high': result['h'],
                                'low': result['l'],
                                'close': result['c'],
                                'volume': int(result['v']),
                                'vwap': result.get('vw')
                            }
                            filtered_bars.append(bar)

                return filtered_bars

            except requests.exceptions.Timeout:
                time_module.sleep(API_RETRY_DELAY)
            except Exception as e:
                return []

        return []

    # =========================================================================
    # UNIFIED INTERFACE
    # =========================================================================

    def get_bars(
        self,
        ticker: str,
        trade_date: date,
        start_time: time = None,
        end_time: time = None
    ) -> List[Dict]:
        """
        Get M1 bars from database (preferred) or API (fallback).

        Args:
            ticker: Stock symbol
            trade_date: Trading date
            start_time: Optional start time filter
            end_time: Optional end time filter

        Returns:
            List of bar dictionaries sorted by time
        """
        cache_key = self._get_cache_key(ticker, trade_date)

        # Check cache first (full day)
        if cache_key in self._cache:
            bars = self._cache[cache_key]
            return self._filter_bars(bars, start_time, end_time)

        # Try database first
        bars = self.fetch_from_db(ticker, trade_date)

        # Fall back to API if no DB data
        if not bars and self.use_api_fallback:
            bars = self.fetch_from_api(ticker, trade_date)

        # Cache full day result
        if bars:
            self._cache[cache_key] = bars

        return self._filter_bars(bars, start_time, end_time)

    def get_extended_bars(
        self,
        ticker: str,
        trade_date: date,
        include_premarket: bool = True,
        include_afterhours: bool = True
    ) -> List[Dict]:
        """
        Get M1 bars with extended hours, starting from prior day 16:00.

        This ensures sufficient bars for SMA21 calculation at market open.
        Uses caching to minimize database/API calls.

        Args:
            ticker: Stock symbol
            trade_date: Trading date
            include_premarket: Include premarket (04:00-09:30)
            include_afterhours: Include after-hours (16:00-20:00)

        Returns:
            List of M1 bar dictionaries with extended coverage
        """
        trade_dt = self._parse_date(trade_date)
        prior_day = self._get_prior_trading_day(trade_dt)
        cache_key = f"{ticker}_{trade_dt.strftime('%Y%m%d')}_extended"

        # Check cache first
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Try database first
        bars = self.fetch_extended_from_db(ticker, trade_dt, include_premarket, include_afterhours)

        # Check if we have SUFFICIENT prior day bars (need 100+ M1 bars = 20+ M5 bars)
        prior_day_bars = sum(1 for bar in bars if bar.get('bar_date') == prior_day)
        has_sufficient_prior = prior_day_bars >= 100  # ~1.5 hours of M1 data

        # Fall back to API if insufficient prior day data
        if (not has_sufficient_prior or len(bars) < 200) and self.use_api_fallback:
            api_bars = self.fetch_extended_from_api(ticker, trade_dt, include_premarket, include_afterhours)
            # Check prior day count in API bars
            api_prior_count = sum(1 for bar in api_bars if bar.get('bar_date') == prior_day)
            # Use API bars if they have more prior day bars or more total bars
            if api_prior_count > prior_day_bars or len(api_bars) > len(bars):
                bars = api_bars

        # Cache result
        if bars:
            self._cache[cache_key] = bars

        return bars

    def get_bars_before_time(
        self,
        ticker: str,
        trade_date: date,
        before_time: time,
        bar_count: int = None
    ) -> List[Dict]:
        """
        Get M1 bars up to (but not including) a specific time.

        Uses EXTENDED bar fetching from prior day 16:00 to ensure sufficient
        bars for SMA21 calculation even for early morning entries.

        Args:
            ticker: Stock symbol
            trade_date: Trading date
            before_time: Get bars strictly before this time
            bar_count: Optional limit on number of bars (most recent N)

        Returns:
            List of bar dictionaries sorted by time
        """
        trade_dt = self._parse_date(trade_date)

        # Get extended bars (includes prior day after-hours + trade day)
        all_bars = self.get_extended_bars(ticker, trade_dt, include_premarket=True, include_afterhours=False)

        if not all_bars:
            return []

        # Filter to bars before the specified time on trade day
        # Include all prior day bars + trade day bars before entry
        filtered = []
        for bar in all_bars:
            bar_date = bar.get('bar_date')
            bar_time = bar.get('bar_time')

            if bar_date is None or bar_time is None:
                continue

            # Include all bars from prior day
            if bar_date < trade_dt:
                filtered.append(bar)
            # Include trade day bars before entry time
            elif bar_date == trade_dt and bar_time < before_time:
                filtered.append(bar)

        if bar_count and len(filtered) > bar_count:
            filtered = filtered[-bar_count:]

        return filtered

    def _filter_bars(
        self,
        bars: List[Dict],
        start_time: time = None,
        end_time: time = None
    ) -> List[Dict]:
        """Filter bars by time range."""
        if not bars:
            return []

        if start_time is None and end_time is None:
            return bars

        filtered = []
        for bar in bars:
            bar_time = bar.get('bar_time')
            if bar_time is None:
                continue

            if start_time and bar_time < start_time:
                continue
            if end_time and bar_time > end_time:
                continue

            filtered.append(bar)

        return filtered

    def clear_cache(self):
        """Clear the bar cache."""
        self._cache.clear()


# =============================================================================
# BAR AGGREGATION UTILITIES
# =============================================================================

def aggregate_to_m5(m1_bars: List[Dict]) -> List[Dict]:
    """
    Aggregate M1 bars to M5 bars.

    Handles multi-day bar sets (prior day + trade day) by including
    bar_date in the grouping key.

    Args:
        m1_bars: List of 1-minute bar dictionaries

    Returns:
        List of 5-minute bar dictionaries
    """
    if not m1_bars:
        return []

    m5_bars = []
    current_group = []

    def get_group_key(bar: Dict) -> tuple:
        """Get (date, hour, 5-min-bucket) key for grouping."""
        bar_date = bar.get('bar_date')
        bar_time = bar.get('bar_time')
        if bar_time is None:
            return None
        m5_minute = (bar_time.minute // 5) * 5
        return (bar_date, bar_time.hour, m5_minute)

    for bar in m1_bars:
        bar_key = get_group_key(bar)
        if bar_key is None:
            continue

        if not current_group:
            current_group.append(bar)
        else:
            first_key = get_group_key(current_group[0])

            if bar_key == first_key:
                current_group.append(bar)
            else:
                # Aggregate current group
                m5_bar = _aggregate_bars(current_group)
                if m5_bar:
                    m5_bars.append(m5_bar)
                current_group = [bar]

    # Don't forget the last group
    if current_group:
        m5_bar = _aggregate_bars(current_group)
        if m5_bar:
            m5_bars.append(m5_bar)

    return m5_bars


def _aggregate_bars(bars: List[Dict]) -> Optional[Dict]:
    """
    Aggregate a group of bars into one.

    Args:
        bars: List of bars to aggregate

    Returns:
        Single aggregated bar dictionary
    """
    if not bars:
        return None

    return {
        'timestamp': bars[0].get('timestamp'),
        'bar_date': bars[0].get('bar_date'),
        'bar_time': bars[0].get('bar_time'),
        'open': bars[0].get('open'),
        'high': max(float(b.get('high', 0)) for b in bars),
        'low': min(float(b.get('low', float('inf'))) for b in bars),
        'close': bars[-1].get('close'),
        'volume': sum(int(b.get('volume', 0)) for b in bars),
        'vwap': _calculate_vwap_from_bars(bars)
    }


def _calculate_vwap_from_bars(bars: List[Dict]) -> Optional[float]:
    """Calculate VWAP from a group of bars."""
    total_tpv = 0.0
    total_volume = 0.0

    for bar in bars:
        volume = float(bar.get('volume', 0))
        if volume == 0:
            continue

        high = float(bar.get('high', 0))
        low = float(bar.get('low', 0))
        close = float(bar.get('close', 0))
        typical_price = (high + low + close) / 3

        total_tpv += typical_price * volume
        total_volume += volume

    if total_volume == 0:
        return None

    return total_tpv / total_volume
