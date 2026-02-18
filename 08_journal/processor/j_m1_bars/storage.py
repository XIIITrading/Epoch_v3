"""
================================================================================
EPOCH TRADING SYSTEM - JOURNAL PROCESSOR 1
j_m1_bars - M1 Bar Fetcher & Storage
XIII Trading LLC
================================================================================

Fetches 1-minute bar data from Polygon API and stores in j_m1_bars.
Adapted from 03_backtest/processor/secondary_analysis/m1_bars/m1_bars_storage.py.

Key difference from backtest: Reads (symbol, trade_date) from journal_trades
instead of (ticker, date) from trades_2.

Time Range: Prior day 16:00 ET -> Trade day 16:00 ET

Version: 1.0.0
================================================================================
"""

import requests
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, date, time, timedelta
from typing import List, Dict, Set, Tuple, Any, Optional
import time as time_module
import pytz

import sys
from pathlib import Path

# Import shared config
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from db_config import (
    DB_CONFIG, POLYGON_API_KEY, API_DELAY, API_RETRIES, API_RETRY_DELAY,
    SOURCE_TABLE, J_M1_BARS_TABLE, BATCH_INSERT_SIZE,
    PRIOR_DAY_START, TRADE_DAY_END, VERBOSE,
    JOURNAL_SYMBOL_COL, JOURNAL_DATE_COL
)

ET = pytz.timezone('America/New_York')
UTC = pytz.UTC


def _get_prior_trading_day(trade_date: date) -> date:
    """Get the prior trading day (skip weekends)."""
    prior = trade_date - timedelta(days=1)
    while prior.weekday() >= 5:
        prior -= timedelta(days=1)
    return prior


def _convert_polygon_timestamp(ts_ms: int) -> datetime:
    """Convert Polygon millisecond timestamp to ET datetime."""
    utc_dt = datetime.utcfromtimestamp(ts_ms / 1000).replace(tzinfo=UTC)
    return utc_dt.astimezone(ET)


class M1BarFetcher:
    """Fetches M1 bars from Polygon API across a two-day window."""

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
        """Fetch raw M1 bars from Polygon API."""
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
        Fetch M1 bars for extended session:
        Prior trading day 16:00 ET -> Trade day 16:00 ET.
        """
        prior_day = _get_prior_trading_day(trade_date)

        from_str = prior_day.strftime('%Y-%m-%d')
        to_str = trade_date.strftime('%Y-%m-%d')

        all_bars = self._fetch_raw(ticker, from_str, to_str)

        if not all_bars:
            return []

        # Filter to our window
        filtered = []
        for bar in all_bars:
            bar_date = bar['timestamp'].date()
            bar_time = bar['timestamp'].time()

            if bar_date == prior_day and bar_time >= PRIOR_DAY_START:
                filtered.append(bar)
            elif bar_date == trade_date and bar_time <= TRADE_DAY_END:
                filtered.append(bar)

        return filtered


class JM1BarsStorage:
    """
    Manages storage of M1 bar data from Polygon to j_m1_bars table.

    Reads unique (symbol, trade_date) from journal_trades and stores
    bars under the trade_date.
    """

    def __init__(self, fetcher: M1BarFetcher = None, verbose: bool = None):
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
        if self.verbose or level in ('error', 'warning'):
            prefix = {'error': '!', 'warning': '?', 'info': ' ', 'debug': '  '}
            print(f"  {prefix.get(level, ' ')} {message}")

    def get_required_ticker_dates(self, conn) -> List[Tuple[str, date]]:
        """Get all unique (symbol, trade_date) from journal_trades."""
        query = f"""
            SELECT DISTINCT {JOURNAL_SYMBOL_COL} AS ticker, {JOURNAL_DATE_COL} AS date
            FROM {SOURCE_TABLE}
            WHERE {JOURNAL_SYMBOL_COL} IS NOT NULL
              AND {JOURNAL_DATE_COL} IS NOT NULL
            ORDER BY {JOURNAL_DATE_COL} DESC, {JOURNAL_SYMBOL_COL}
        """

        with conn.cursor() as cur:
            cur.execute(query)
            results = cur.fetchall()

        return [(row[0], row[1]) for row in results]

    def get_loaded_ticker_dates(self, conn) -> Set[Tuple[str, date]]:
        """Get (ticker, bar_date) pairs already loaded in j_m1_bars."""
        query = f"""
            SELECT DISTINCT ticker, bar_date
            FROM {J_M1_BARS_TABLE}
        """

        try:
            with conn.cursor() as cur:
                cur.execute(query)
                results = cur.fetchall()
            return {(row[0], row[1]) for row in results}
        except psycopg2.errors.UndefinedTable:
            conn.rollback()
            return set()

    def get_missing_ticker_dates(self, conn, limit: int = None) -> List[Tuple[str, date]]:
        """Get (ticker, date) pairs that need bar data loaded."""
        required = self.get_required_ticker_dates(conn)
        loaded = self.get_loaded_ticker_dates(conn)

        missing = [td for td in required if td not in loaded]

        if limit:
            missing = missing[:limit]

        return missing

    def fetch_and_store_bars(
        self, conn, ticker: str, trade_date: date, dry_run: bool = False
    ) -> int:
        """Fetch bars from Polygon and store in j_m1_bars."""
        self._log(f"Fetching {ticker} for {trade_date}...", 'debug')

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
        insert_data = []
        for bar in bars:
            insert_data.append((
                ticker,
                trade_date,
                bar['timestamp'].time(),
                bar['timestamp'],
                round(bar['open'], 4),
                round(bar['high'], 4),
                round(bar['low'], 4),
                round(bar['close'], 4),
                int(bar['volume']),
                round(bar['vwap'], 4) if bar.get('vwap') else None,
                bar.get('transactions')
            ))

        insert_query = f"""
            INSERT INTO {J_M1_BARS_TABLE}
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
        self, limit: int = None, dry_run: bool = False, callback=None
    ) -> Dict[str, Any]:
        """
        Main entry point. Fetch and store bars for all missing ticker-dates.

        Args:
            limit: Max ticker-date pairs to process
            dry_run: Fetch but don't insert
            callback: Optional callable(message) for GUI progress

        Returns:
            Dictionary with execution statistics
        """
        start_time = datetime.now()

        # Reset statistics
        self.stats = {
            'ticker_dates_processed': 0,
            'ticker_dates_skipped': 0,
            'bars_inserted': 0,
            'api_calls_made': 0,
            'errors': []
        }

        def _emit(msg):
            print(msg)
            if callback:
                callback(msg)

        _emit("=" * 60)
        _emit("Journal M1 Bars Storage v1.0")
        _emit("Prior Day 16:00 ET -> Trade Day 16:00 ET")
        _emit("=" * 60)
        _emit(f"Source: {SOURCE_TABLE}")
        _emit(f"Target: {J_M1_BARS_TABLE}")
        _emit(f"Mode: {'DRY-RUN' if dry_run else 'FULL RUN'}")
        if limit:
            _emit(f"Limit: {limit} ticker-dates")
        _emit("")

        conn = None
        try:
            _emit("[1/3] Connecting to Supabase...")
            conn = psycopg2.connect(**DB_CONFIG)
            _emit("  Connected successfully")

            _emit(f"\n[2/3] Finding missing ticker-date pairs...")
            missing = self.get_missing_ticker_dates(conn, limit)
            _emit(f"  Found {len(missing)} ticker-dates needing bar data")

            if not missing:
                _emit("\n  All ticker-dates already have bar data. Nothing to do.")
                return self._finalize_stats(start_time)

            _emit(f"\n[3/3] Fetching and storing bars...")
            total = len(missing)

            for i, (ticker, trade_date) in enumerate(missing, 1):
                progress = f"[{i}/{total}]"
                _emit(f"  {progress} {ticker} {trade_date}...")

                try:
                    bar_count = self.fetch_and_store_bars(conn, ticker, trade_date, dry_run)

                    if bar_count > 0:
                        self.stats['ticker_dates_processed'] += 1
                        _emit(f"    -> {bar_count} bars")
                    else:
                        self.stats['ticker_dates_skipped'] += 1
                        _emit(f"    -> skipped (no data)")

                except Exception as e:
                    self.stats['ticker_dates_skipped'] += 1
                    self.stats['errors'].append(f"{ticker}/{trade_date}: {str(e)}")
                    _emit(f"    -> ERROR: {e}")

            return self._finalize_stats(start_time)

        except Exception as e:
            self.stats['errors'].append(f"Fatal: {str(e)}")
            raise

        finally:
            if conn:
                conn.close()

    def _finalize_stats(self, start_time: datetime) -> Dict[str, Any]:
        """Calculate final statistics."""
        end_time = datetime.now()
        self.stats['execution_time_seconds'] = (end_time - start_time).total_seconds()
        return self.stats
