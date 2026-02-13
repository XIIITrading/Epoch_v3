"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
M1 Bars Storage - Main Storage Logic
XIII Trading LLC
================================================================================

Fetches 1-minute bar data from Polygon API and stores in Supabase.
Identifies unique (ticker, date) combinations from the trades_2 table and
ensures bar data is available for downstream secondary processors.

Key Features:
- Fetches prior day 16:00 ET through trade day 16:00 ET
- Captures after-hours, overnight, pre-market, and full regular session
- Fetches only missing ticker-date combinations (incremental updates)
- Batch inserts for efficiency
- All bars stored under the trade_date (bar_date = trade_date)

Version: 2.0.0
================================================================================
"""

import requests
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, date, time, timedelta
from typing import List, Dict, Set, Tuple, Any, Optional
import time as time_module
import sys
from pathlib import Path
import pytz

# Ensure we import from our local config
MODULE_DIR = Path(__file__).parent
sys.path.insert(0, str(MODULE_DIR))

# Import from local config
from config import (
    DB_CONFIG,
    POLYGON_API_KEY,
    API_DELAY,
    API_RETRIES,
    API_RETRY_DELAY,
    TARGET_TABLE,
    SOURCE_TABLE,
    BATCH_INSERT_SIZE,
    PRIOR_DAY_START,
    TRADE_DAY_END,
    VERBOSE
)


ET = pytz.timezone('America/New_York')
UTC = pytz.UTC


def _get_prior_trading_day(trade_date: date) -> date:
    """
    Get the prior trading day (skip weekends).
    Does not account for market holidays - Polygon returns no data for holidays
    which is handled gracefully.
    """
    prior = trade_date - timedelta(days=1)
    # Skip weekends
    while prior.weekday() >= 5:  # 5=Saturday, 6=Sunday
        prior -= timedelta(days=1)
    return prior


def _convert_polygon_timestamp(ts_ms: int) -> datetime:
    """Convert Polygon millisecond timestamp to ET datetime."""
    utc_dt = datetime.utcfromtimestamp(ts_ms / 1000).replace(tzinfo=UTC)
    return utc_dt.astimezone(ET)


class M1BarFetcher:
    """
    Fetches M1 bars from Polygon API across a two-day window.
    Prior day 16:00 ET -> Trade day 16:00 ET.
    """

    BASE_URL = "https://api.polygon.io"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or POLYGON_API_KEY
        self.last_request_time = 0

    def _rate_limit(self):
        """Enforce rate limiting between API calls."""
        if API_DELAY > 0:
            elapsed = time_module.time() - self.last_request_time
            if elapsed < API_DELAY:
                time_module.sleep(API_DELAY - elapsed)
        self.last_request_time = time_module.time()

    def _fetch_raw(self, ticker: str, from_date: str, to_date: str) -> List[dict]:
        """
        Fetch raw M1 bars from Polygon API.

        Returns list of bar dicts with 'timestamp', 'open', 'high', 'low',
        'close', 'volume', 'vwap', 'transactions'.
        """
        url = f"{self.BASE_URL}/v2/aggs/ticker/{ticker}/range/1/minute/{from_date}/{to_date}"

        params = {
            'apiKey': self.api_key,
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
                    print(f"    Rate limited, waiting {wait_time}s...")
                    time_module.sleep(wait_time)
                    continue

                if response.status_code != 200:
                    print(f"    API error: {response.status_code}")
                    return []

                data = response.json()

                if data.get('status') not in ['OK', 'DELAYED']:
                    return []

                if 'results' not in data or not data['results']:
                    return []

                bars = []
                for r in data['results']:
                    ts = _convert_polygon_timestamp(r['t'])
                    bars.append({
                        'timestamp': ts,
                        'open': r['o'],
                        'high': r['h'],
                        'low': r['l'],
                        'close': r['c'],
                        'volume': int(r['v']),
                        'vwap': r.get('vw'),
                        'transactions': r.get('n')
                    })

                return bars

            except requests.exceptions.Timeout:
                print(f"    Timeout on attempt {attempt + 1}, retrying...")
                time_module.sleep(API_RETRY_DELAY)
            except Exception as e:
                print(f"    Fetch error: {e}")
                return []

        return []

    def fetch_extended_session(self, ticker: str, trade_date: date) -> List[dict]:
        """
        Fetch M1 bars for the extended session:
        Prior trading day 16:00 ET -> Trade day 16:00 ET.

        Makes one API call spanning both days and filters to the time window.

        Args:
            ticker: Stock symbol
            trade_date: The trade date

        Returns:
            List of bar dicts filtered to the extended session window
        """
        prior_day = _get_prior_trading_day(trade_date)

        # Fetch both days in a single API call
        from_str = prior_day.strftime('%Y-%m-%d')
        to_str = trade_date.strftime('%Y-%m-%d')

        all_bars = self._fetch_raw(ticker, from_str, to_str)

        if not all_bars:
            return []

        # Filter to our window: prior_day >= 16:00 AND trade_day <= 16:00
        filtered = []
        for bar in all_bars:
            bar_date = bar['timestamp'].date()
            bar_time = bar['timestamp'].time()

            if bar_date == prior_day and bar_time >= PRIOR_DAY_START:
                filtered.append(bar)
            elif bar_date == trade_date and bar_time <= TRADE_DAY_END:
                filtered.append(bar)

        return filtered


class M1BarsStorage:
    """
    Manages storage of 1-minute bar data from Polygon to Supabase.

    Workflow:
    1. Query trades_2 table for unique (ticker, date) pairs
    2. Query m1_bars table to find which pairs are already loaded
    3. Fetch missing data from Polygon API (prior day 16:00 -> trade day 16:00)
    4. Insert into m1_bars table
    """

    def __init__(self, fetcher: M1BarFetcher = None, verbose: bool = None):
        """
        Initialize the storage manager.

        Args:
            fetcher: M1BarFetcher instance (creates one if not provided)
            verbose: Enable verbose logging (defaults to config value)
        """
        self.fetcher = fetcher or M1BarFetcher()
        self.verbose = verbose if verbose is not None else VERBOSE
        self.stats = {
            'ticker_dates_processed': 0,
            'ticker_dates_skipped': 0,
            'bars_inserted': 0,
            'api_calls_made': 0,
            'errors': []
        }

    def _log(self, message: str, level: str = 'info'):
        """Log a message if verbose mode is enabled."""
        if self.verbose or level in ('error', 'warning'):
            prefix = {'error': '!', 'warning': '?', 'info': ' ', 'debug': '  '}
            print(f"  {prefix.get(level, ' ')} {message}")

    def get_required_ticker_dates(self, conn) -> List[Tuple[str, date]]:
        """
        Get all unique (ticker, date) pairs from the trades_2 table.

        Args:
            conn: Database connection

        Returns:
            List of (ticker, date) tuples
        """
        query = f"""
            SELECT DISTINCT ticker, date
            FROM {SOURCE_TABLE}
            WHERE ticker IS NOT NULL
              AND date IS NOT NULL
            ORDER BY date DESC, ticker
        """

        with conn.cursor() as cur:
            cur.execute(query)
            results = cur.fetchall()

        return [(row[0], row[1]) for row in results]

    def get_loaded_ticker_dates(self, conn) -> Set[Tuple[str, date]]:
        """
        Get (ticker, date) pairs that already have bars loaded.

        Args:
            conn: Database connection

        Returns:
            Set of (ticker, date) tuples already in m1_bars
        """
        query = f"""
            SELECT DISTINCT ticker, bar_date
            FROM {TARGET_TABLE}
        """

        try:
            with conn.cursor() as cur:
                cur.execute(query)
                results = cur.fetchall()
            return {(row[0], row[1]) for row in results}
        except psycopg2.errors.UndefinedTable:
            # Table doesn't exist yet
            return set()

    def get_missing_ticker_dates(
        self,
        conn,
        limit: int = None
    ) -> List[Tuple[str, date]]:
        """
        Get (ticker, date) pairs that need bar data loaded.

        Args:
            conn: Database connection
            limit: Maximum number of pairs to return

        Returns:
            List of (ticker, date) tuples not yet in m1_bars
        """
        required = self.get_required_ticker_dates(conn)
        loaded = self.get_loaded_ticker_dates(conn)

        missing = [td for td in required if td not in loaded]

        if limit:
            missing = missing[:limit]

        return missing

    def fetch_and_store_bars(
        self,
        conn,
        ticker: str,
        trade_date: date,
        dry_run: bool = False
    ) -> int:
        """
        Fetch bars from Polygon (prior day 16:00 -> trade day 16:00) and store in Supabase.

        All bars are stored with bar_date = trade_date regardless of when
        they occurred. This groups the full extended session under one date.

        Args:
            conn: Database connection
            ticker: Stock symbol
            trade_date: Trading date
            dry_run: If True, fetch but don't insert

        Returns:
            Number of bars inserted (or would be inserted if dry_run)
        """
        self._log(f"Fetching {ticker} for {trade_date}...", 'debug')

        # Fetch extended session from Polygon
        bars = self.fetcher.fetch_extended_session(ticker, trade_date)
        self.stats['api_calls_made'] += 1

        if not bars:
            self._log(f"No bars returned for {ticker} on {trade_date}", 'warning')
            return 0

        bar_count = len(bars)
        self._log(f"Fetched {bar_count} bars for {ticker}", 'debug')

        if dry_run:
            return bar_count

        # Prepare data for insert
        # All bars stored under trade_date as bar_date
        insert_data = []
        for bar in bars:
            insert_data.append((
                ticker,
                trade_date,                              # bar_date = trade date
                bar['timestamp'].time(),                 # bar_time
                bar['timestamp'],                        # bar_timestamp (full)
                round(bar['open'], 4),
                round(bar['high'], 4),
                round(bar['low'], 4),
                round(bar['close'], 4),
                int(bar['volume']),
                round(bar['vwap'], 4) if bar.get('vwap') else None,
                bar.get('transactions')
            ))

        # Batch insert
        insert_query = f"""
            INSERT INTO {TARGET_TABLE}
                (ticker, bar_date, bar_time, bar_timestamp,
                 open, high, low, close, volume, vwap, transactions)
            VALUES %s
            ON CONFLICT (ticker, bar_timestamp) DO NOTHING
        """

        try:
            with conn.cursor() as cur:
                execute_values(cur, insert_query, insert_data, page_size=BATCH_INSERT_SIZE)
            conn.commit()
            self.stats['bars_inserted'] += bar_count
            return bar_count
        except Exception as e:
            conn.rollback()
            self._log(f"Insert error for {ticker} on {trade_date}: {e}", 'error')
            self.stats['errors'].append(f"{ticker}/{trade_date}: {str(e)}")
            return 0

    def run_batch_storage(
        self,
        limit: int = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Main entry point. Fetch and store bars for all missing ticker-dates.

        Args:
            limit: Maximum ticker-date pairs to process
            dry_run: If True, fetch but don't insert

        Returns:
            Dictionary with execution statistics
        """
        start_time = datetime.now()

        print("=" * 60)
        print("M1 Bars Storage v2.0")
        print("Prior Day 16:00 ET -> Trade Day 16:00 ET")
        print("=" * 60)
        print(f"Dry Run: {dry_run}")
        if limit:
            print(f"Limit: {limit} ticker-date pairs")
        print()

        # Reset statistics
        self.stats = {
            'ticker_dates_processed': 0,
            'ticker_dates_skipped': 0,
            'bars_inserted': 0,
            'api_calls_made': 0,
            'errors': []
        }

        conn = None
        try:
            # Connect to database
            print("[1/4] Connecting to Supabase...")
            conn = psycopg2.connect(**DB_CONFIG)
            print("  Connected successfully")

            # Get missing ticker-dates
            print(f"\n[2/4] Finding missing ticker-date pairs (source: {SOURCE_TABLE})...")
            missing = self.get_missing_ticker_dates(conn, limit)
            print(f"  Found {len(missing)} ticker-dates needing bar data")

            if not missing:
                print("\n  All ticker-dates already have bar data. Nothing to do.")
                return self._finalize_stats(start_time)

            # Process each ticker-date
            print(f"\n[3/4] Fetching and storing bars...")
            total = len(missing)

            for i, (ticker, trade_date) in enumerate(missing, 1):
                progress = f"[{i}/{total}]"
                print(f"  {progress} {ticker} {trade_date}...", end=" ", flush=True)

                try:
                    bar_count = self.fetch_and_store_bars(
                        conn, ticker, trade_date, dry_run
                    )

                    if bar_count > 0:
                        self.stats['ticker_dates_processed'] += 1
                        print(f"{bar_count} bars")
                    else:
                        self.stats['ticker_dates_skipped'] += 1
                        print("skipped (no data)")

                except Exception as e:
                    self.stats['ticker_dates_skipped'] += 1
                    self.stats['errors'].append(f"{ticker}/{trade_date}: {str(e)}")
                    print(f"ERROR: {e}")

            # Summary
            print(f"\n[4/4] Complete.")

            return self._finalize_stats(start_time)

        except Exception as e:
            self.stats['errors'].append(f"Fatal: {str(e)}")
            print(f"\nFATAL ERROR: {e}")
            raise

        finally:
            if conn:
                conn.close()

    def _finalize_stats(self, start_time: datetime) -> Dict[str, Any]:
        """Calculate final statistics."""
        end_time = datetime.now()
        self.stats['execution_time_seconds'] = (end_time - start_time).total_seconds()
        return self.stats


# =============================================================================
# STANDALONE TEST
# =============================================================================
if __name__ == "__main__":
    print("M1 Bars Storage - Test Run")
    print("=" * 60)

    storage = M1BarsStorage(verbose=True)

    # Test with dry run, limit 2
    results = storage.run_batch_storage(limit=2, dry_run=True)

    print("\n" + "=" * 60)
    print("TEST RESULTS (DRY RUN)")
    print("=" * 60)
    for key, value in results.items():
        if key != 'errors':
            print(f"  {key}: {value}")

    if results['errors']:
        print("\nErrors:")
        for err in results['errors']:
            print(f"  ! {err}")
