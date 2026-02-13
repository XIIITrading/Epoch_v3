"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
M1 Bars Storage - Main Storage Logic
XIII Trading LLC
================================================================================

Fetches 1-minute bar data from Polygon API and stores in Supabase.
Identifies unique (ticker, date) combinations from the trades table and
ensures bar data is available for accurate stop/target simulation.

Key Features:
- Fetches only missing ticker-date combinations (incremental updates)
- Batch inserts for efficiency
- Reuses M1Fetcher from mfe_mae module for Polygon API calls
- Full trading day storage (09:30 - 16:00 ET)

Version: 1.0.0
================================================================================
"""

import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, date, time, timedelta
from typing import List, Dict, Set, Tuple, Any
import sys
from pathlib import Path

# Ensure we import from our local config, not mfe_mae's config
MODULE_DIR = Path(__file__).parent
sys.path.insert(0, str(MODULE_DIR))

# Import from local config
from config import (
    DB_CONFIG,
    TARGET_TABLE,
    SOURCE_TABLE,
    BATCH_INSERT_SIZE,
    MARKET_OPEN,
    MARKET_CLOSE,
    VERBOSE
)

# Import M1Fetcher from mfe_mae sibling module
MFE_MAE_DIR = MODULE_DIR.parent / "mfe_mae"
sys.path.insert(0, str(MFE_MAE_DIR))
from m1_fetcher import M1Fetcher


class M1BarsStorage:
    """
    Manages storage of 1-minute bar data from Polygon to Supabase.

    Workflow:
    1. Query trades table for unique (ticker, date) pairs
    2. Query m1_bars table to find which pairs are already loaded
    3. Fetch missing data from Polygon API
    4. Insert into m1_bars table
    """

    def __init__(self, fetcher: M1Fetcher = None, verbose: bool = None):
        """
        Initialize the storage manager.

        Args:
            fetcher: M1Fetcher instance (creates one if not provided)
            verbose: Enable verbose logging (defaults to config value)
        """
        self.fetcher = fetcher or M1Fetcher()
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
        Get all unique (ticker, date) pairs from the trades table.

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
        Fetch bars from Polygon and store in Supabase.

        Args:
            conn: Database connection
            ticker: Stock symbol
            trade_date: Trading date
            dry_run: If True, fetch but don't insert

        Returns:
            Number of bars inserted (or would be inserted if dry_run)
        """
        self._log(f"Fetching {ticker} for {trade_date}...", 'debug')

        # Fetch from Polygon
        df = self.fetcher.fetch_trading_day(
            ticker=ticker,
            trade_date=trade_date,
            start_time=MARKET_OPEN,
            end_time=MARKET_CLOSE
        )

        self.stats['api_calls_made'] += 1

        if df.empty:
            self._log(f"No bars returned for {ticker} on {trade_date}", 'warning')
            return 0

        bar_count = len(df)
        self._log(f"Fetched {bar_count} bars for {ticker}", 'debug')

        if dry_run:
            return bar_count

        # Prepare data for insert
        insert_data = []
        for _, row in df.iterrows():
            ts = row['timestamp']
            insert_data.append((
                ticker,
                trade_date,
                ts.time(),                          # bar_time
                ts,                                  # bar_timestamp (full)
                round(row['open'], 4),
                round(row['high'], 4),
                round(row['low'], 4),
                round(row['close'], 4),
                int(row['volume']),
                round(row['vwap'], 4) if row.get('vwap') else None,
                None  # transactions (not always available)
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
        print("M1 Bars Storage")
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
            print("\n[2/4] Finding missing ticker-date pairs...")
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
