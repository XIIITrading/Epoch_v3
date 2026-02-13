"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
H1 Bars - Storage Logic
XIII Trading LLC
================================================================================

Stores H1 bar data from Polygon API to Supabase.
Manages the h1_bars table for H1 market structure analysis.

Key Features:
- Queries trades table for unique (ticker, date) pairs
- LEFT JOIN to find pairs not yet in h1_bars
- Fetches H1 bars from Polygon with lookback for structure analysis
- Batch insert with ON CONFLICT handling

Version: 1.0.0
================================================================================
"""

import psycopg2
from psycopg2.extras import execute_values, RealDictCursor
from datetime import datetime, date, time, timedelta
from typing import Dict, List, Tuple, Set, Any, Optional
import logging

try:
    from .config import (
        DB_CONFIG,
        SOURCE_TABLE,
        TARGET_TABLE,
        BATCH_INSERT_SIZE,
        VERBOSE,
        H1_LOOKBACK_DAYS
    )
    from .h1_fetcher import H1Fetcher, H1Bar
except ImportError:
    from config import (
        DB_CONFIG,
        SOURCE_TABLE,
        TARGET_TABLE,
        BATCH_INSERT_SIZE,
        VERBOSE,
        H1_LOOKBACK_DAYS
    )
    from h1_fetcher import H1Fetcher, H1Bar


class H1BarsStorage:
    """
    Manages storage of H1 bars from Polygon API to Supabase.

    Workflow:
    1. Query trades for unique (ticker, date) pairs
    2. LEFT JOIN to h1_bars to find missing pairs
    3. For each missing pair, fetch H1 bars from ~7 days before through trade date
    4. Batch insert results
    """

    def __init__(
        self,
        fetcher: H1Fetcher = None,
        verbose: bool = None
    ):
        """
        Initialize the storage handler.

        Args:
            fetcher: H1Fetcher instance (created if not provided)
            verbose: Enable verbose logging
        """
        self.fetcher = fetcher or H1Fetcher()
        self.verbose = verbose if verbose is not None else VERBOSE
        self.logger = logging.getLogger(__name__)

        # Statistics
        self.stats = {
            'ticker_dates_processed': 0,
            'ticker_dates_skipped': 0,
            'bars_inserted': 0,
            'api_calls_made': 0,
            'errors': []
        }

    def _log(self, message: str, level: str = 'info'):
        """Log message if verbose."""
        if self.verbose or level in ('error', 'warning'):
            prefix = {'error': '!', 'warning': '?', 'info': ' ', 'debug': '  '}
            print(f"  {prefix.get(level, ' ')} {message}")

    # =========================================================================
    # DATABASE QUERIES
    # =========================================================================

    def get_required_ticker_dates(self, conn) -> List[Tuple[str, date]]:
        """
        Get unique (ticker, date) pairs from trades table.

        Args:
            conn: Database connection

        Returns:
            List of (ticker, date) tuples
        """
        query = f"""
            SELECT DISTINCT ticker, date
            FROM {SOURCE_TABLE}
            WHERE date IS NOT NULL
              AND ticker IS NOT NULL
            ORDER BY date DESC, ticker
        """

        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()

        return [(row[0], row[1]) for row in rows]

    def get_loaded_ticker_dates(self, conn) -> Set[Tuple[str, date]]:
        """
        Get (ticker, date) pairs already in h1_bars table.

        Args:
            conn: Database connection

        Returns:
            Set of (ticker, date) tuples
        """
        query = f"""
            SELECT DISTINCT ticker, bar_date
            FROM {TARGET_TABLE}
        """

        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()

        return {(row[0], row[1]) for row in rows}

    def get_missing_ticker_dates(
        self,
        conn,
        limit: int = None
    ) -> List[Tuple[str, date]]:
        """
        Get (ticker, date) pairs that need H1 bar fetching.

        Args:
            conn: Database connection
            limit: Maximum number of pairs to return

        Returns:
            List of (ticker, date) tuples needing processing
        """
        query = f"""
            WITH required AS (
                SELECT DISTINCT ticker, date
                FROM {SOURCE_TABLE}
                WHERE date IS NOT NULL
                  AND ticker IS NOT NULL
            ),
            loaded AS (
                SELECT DISTINCT ticker, bar_date as date
                FROM {TARGET_TABLE}
            )
            SELECT r.ticker, r.date
            FROM required r
            LEFT JOIN loaded l
                ON r.ticker = l.ticker AND r.date = l.date
            WHERE l.ticker IS NULL
            ORDER BY r.date DESC, r.ticker
        """

        if limit:
            query += f" LIMIT {limit}"

        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()

        return [(row[0], row[1]) for row in rows]

    def insert_bars(
        self,
        conn,
        ticker: str,
        bars: List[H1Bar]
    ) -> int:
        """
        Insert H1 bars into the database.

        Args:
            conn: Database connection
            ticker: Stock symbol
            bars: List of H1Bar objects

        Returns:
            Number of bars inserted
        """
        if not bars:
            return 0

        query = f"""
            INSERT INTO {TARGET_TABLE} (
                ticker, bar_date, bar_time, bar_timestamp,
                open, high, low, close, volume,
                vwap, transactions
            ) VALUES %s
            ON CONFLICT (ticker, bar_timestamp) DO NOTHING
        """

        values = []
        for bar in bars:
            row = (
                ticker,
                bar.timestamp.date(),
                bar.timestamp.time(),
                bar.timestamp,
                bar.open,
                bar.high,
                bar.low,
                bar.close,
                bar.volume,
                bar.vwap,
                bar.transactions
            )
            values.append(row)

        with conn.cursor() as cur:
            execute_values(cur, query, values, page_size=BATCH_INSERT_SIZE)

        return len(values)

    def get_status(self, conn) -> Dict[str, Any]:
        """
        Get current status of h1_bars table.

        Args:
            conn: Database connection

        Returns:
            Status dictionary
        """
        status = {}

        # Count total bars
        with conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM {TARGET_TABLE}")
            status['total_bars'] = cur.fetchone()[0]

        # Count unique ticker-dates
        with conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(DISTINCT (ticker, bar_date)) FROM {TARGET_TABLE}")
            status['unique_ticker_dates'] = cur.fetchone()[0]

        # Count unique tickers
        with conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(DISTINCT ticker) FROM {TARGET_TABLE}")
            status['unique_tickers'] = cur.fetchone()[0]

        # Get date range
        with conn.cursor() as cur:
            cur.execute(f"SELECT MIN(bar_date), MAX(bar_date) FROM {TARGET_TABLE}")
            row = cur.fetchone()
            status['min_date'] = row[0]
            status['max_date'] = row[1]

        # Count pending
        pending = self.get_missing_ticker_dates(conn)
        status['pending_ticker_dates'] = len(pending)

        return status

    # =========================================================================
    # MAIN PROCESSING
    # =========================================================================

    def fetch_and_store_bars(
        self,
        conn,
        ticker: str,
        trade_date: date,
        dry_run: bool = False
    ) -> int:
        """
        Fetch H1 bars for a ticker-date and store them.

        Args:
            conn: Database connection
            ticker: Stock symbol
            trade_date: Trade date
            dry_run: If True, fetch but don't store

        Returns:
            Number of bars stored
        """
        # Fetch H1 bars with lookback
        bars = self.fetcher.fetch_h1_bars_for_structure(ticker, trade_date)
        self.stats['api_calls_made'] += 1

        if not bars:
            self._log(f"No H1 bars found for {ticker} on {trade_date}", 'debug')
            return 0

        if dry_run:
            self._log(f"[DRY-RUN] Would insert {len(bars)} H1 bars for {ticker}")
            return len(bars)

        # Insert bars
        inserted = self.insert_bars(conn, ticker, bars)
        conn.commit()

        return inserted

    def run_batch_storage(
        self,
        limit: int = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Main entry point. Process all ticker-dates needing H1 bar storage.

        Args:
            limit: Max ticker-dates to process
            dry_run: If True, fetch but don't store

        Returns:
            Dictionary with execution statistics
        """
        start_time = datetime.now()

        print("=" * 60)
        print("H1 Bars Storage")
        print("=" * 60)
        print(f"Source Table: {SOURCE_TABLE}")
        print(f"Target Table: {TARGET_TABLE}")
        print(f"Lookback Days: {H1_LOOKBACK_DAYS}")
        print(f"Dry Run: {dry_run}")
        if limit:
            print(f"Limit: {limit} ticker-dates")
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
            print("[1/3] Connecting to Supabase...")
            conn = psycopg2.connect(**DB_CONFIG)
            print("  Connected successfully")

            # Get missing ticker-dates
            print("\n[2/3] Querying ticker-dates needing H1 bar storage...")
            ticker_dates = self.get_missing_ticker_dates(conn, limit)
            print(f"  Found {len(ticker_dates)} ticker-dates to process")

            if not ticker_dates:
                print("\n  No ticker-dates need processing. Exiting.")
                return self._build_result(start_time)

            # Process each ticker-date
            print("\n[3/3] Fetching and storing H1 bars...")
            total = len(ticker_dates)

            for i, (ticker, trade_date) in enumerate(ticker_dates, 1):
                self._log(f"\n[{i}/{total}] Processing {ticker} on {trade_date}...")

                try:
                    inserted = self.fetch_and_store_bars(conn, ticker, trade_date, dry_run)

                    if inserted > 0:
                        self.stats['ticker_dates_processed'] += 1
                        self.stats['bars_inserted'] += inserted
                        print(f"  [{i}/{total}] {ticker} {trade_date}: {inserted} bars")
                    else:
                        self.stats['ticker_dates_skipped'] += 1
                        self._log(f"Skipped {ticker} {trade_date} (no bars)", 'debug')

                except Exception as e:
                    conn.rollback()
                    self.stats['ticker_dates_skipped'] += 1
                    self.stats['errors'].append(f"{ticker} {trade_date}: {str(e)}")
                    self._log(f"Error processing {ticker} {trade_date}: {e}", 'error')

                # Clear fetcher cache periodically to manage memory
                if i % 10 == 0:
                    self.fetcher.clear_cache()

            return self._build_result(start_time)

        except Exception as e:
            self.stats['errors'].append(f"Fatal: {str(e)}")
            if conn:
                conn.rollback()
            raise

        finally:
            self.fetcher.clear_cache()
            if conn:
                conn.close()

    def _build_result(self, start_time: datetime) -> Dict[str, Any]:
        """Build the result dictionary."""
        elapsed = (datetime.now() - start_time).total_seconds()
        self.stats['execution_time_seconds'] = round(elapsed, 2)
        return self.stats


# =============================================================================
# STANDALONE TEST
# =============================================================================

if __name__ == "__main__":
    print("H1 Bars Storage - Test Run")
    print("=" * 60)

    storage = H1BarsStorage(verbose=True)

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
        for err in results['errors'][:10]:
            print(f"  ! {err}")
