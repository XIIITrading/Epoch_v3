"""
Journal M1 Indicator Bars Populator.

Reads journal_trades for unique (ticker, date) pairs, fetches M1 bars from Polygon,
calculates indicators, and stores results in journal_m1_bars and journal_m1_indicator_bars.

Usage:
    python processor/populator.py                 # Process all missing ticker-dates
    python processor/populator.py --limit 5        # Process max 5 ticker-dates
    python processor/populator.py --dry-run        # Calculate but don't write
    python processor/populator.py --status         # Show table status
    python processor/populator.py --ticker SPY --date 2026-01-28  # Process specific
"""

import psycopg2
from psycopg2.extras import execute_values, RealDictCursor
from datetime import datetime, date, time
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd
import sys
import argparse
from pathlib import Path

# Add parent for config
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DB_CONFIG

from processor.m1_fetcher import M1Fetcher, PREMARKET_START, MARKET_CLOSE
from processor.indicators import M1IndicatorCalculator

# Tables
SOURCE_TABLE = "journal_trades"
M1_BARS_TABLE = "journal_m1_bars"
INDICATOR_TABLE = "journal_m1_indicator_bars"

BATCH_INSERT_SIZE = 500


class JournalM1Populator:
    """
    Populates journal_m1_bars and journal_m1_indicator_bars tables.

    Workflow:
    1. Query journal_trades for unique (symbol, trade_date) pairs
    2. LEFT JOIN to journal_m1_indicator_bars to find missing pairs
    3. For each missing pair: fetch M1 bars, calculate indicators
    4. Insert raw bars into journal_m1_bars
    5. Insert indicator bars into journal_m1_indicator_bars
    """

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.fetcher = M1Fetcher()
        self.calculator = M1IndicatorCalculator()
        self.stats = self._reset_stats()

    def _reset_stats(self) -> Dict:
        return {
            'ticker_dates_processed': 0,
            'ticker_dates_skipped': 0,
            'raw_bars_inserted': 0,
            'indicator_bars_inserted': 0,
            'errors': [],
        }

    def _log(self, msg: str, level: str = 'info'):
        if self.verbose or level in ('error', 'warning'):
            prefix = {'error': '!', 'warning': '?', 'info': ' ', 'debug': '  '}
            print(f"  {prefix.get(level, ' ')} {msg}")

    def _convert_numpy(self, value):
        """Convert numpy types to Python native types for DB insertion."""
        if isinstance(value, np.bool_):
            return bool(value)
        elif isinstance(value, np.integer):
            return int(value)
        elif isinstance(value, np.floating):
            return float(value) if not np.isnan(value) else None
        elif isinstance(value, np.ndarray):
            return value.tolist()
        return value

    def _safe_float(self, value) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, float) and (np.isnan(value) or np.isinf(value)):
            return None
        try:
            return round(float(value), 6)
        except (ValueError, TypeError):
            return None

    def _safe_int(self, value) -> Optional[int]:
        if value is None:
            return None
        if isinstance(value, float) and np.isnan(value):
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    # =========================================================================
    # DATABASE QUERIES
    # =========================================================================

    def get_missing_ticker_dates(self, conn, limit: int = None) -> List[Dict]:
        """Find (ticker, date) pairs in journal_trades but not in journal_m1_indicator_bars."""
        query = f"""
            WITH unique_ticker_dates AS (
                SELECT DISTINCT symbol AS ticker, trade_date AS date
                FROM {SOURCE_TABLE}
                WHERE trade_date IS NOT NULL AND symbol IS NOT NULL
            ),
            existing_ticker_dates AS (
                SELECT DISTINCT ticker, bar_date AS date
                FROM {INDICATOR_TABLE}
            )
            SELECT u.ticker, u.date
            FROM unique_ticker_dates u
            LEFT JOIN existing_ticker_dates e
                ON u.ticker = e.ticker AND u.date = e.date
            WHERE e.ticker IS NULL
            ORDER BY u.date DESC, u.ticker
        """
        if limit:
            query += f" LIMIT {limit}"

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            return [dict(row) for row in cur.fetchall()]

    def insert_raw_bars(self, conn, ticker: str, trade_date: date, df: pd.DataFrame) -> int:
        """Insert raw M1 bars into journal_m1_bars."""
        if df.empty:
            return 0

        query = f"""
            INSERT INTO {M1_BARS_TABLE} (
                ticker, bar_date, bar_time, bar_timestamp,
                open, high, low, close, volume,
                vwap, transactions
            ) VALUES %s
            ON CONFLICT (ticker, bar_timestamp) DO NOTHING
        """

        values = []
        for _, row in df.iterrows():
            values.append((
                ticker,
                row['bar_date'],
                row['bar_time'],
                row['timestamp'],
                float(row['open']),
                float(row['high']),
                float(row['low']),
                float(row['close']),
                int(row['volume']),
                self._safe_float(row.get('vwap')),
                self._safe_int(row.get('transactions')),
            ))

        with conn.cursor() as cur:
            execute_values(cur, query, values, page_size=BATCH_INSERT_SIZE)

        return len(values)

    def insert_indicator_bars(self, conn, ticker: str, trade_date: date, df: pd.DataFrame) -> int:
        """Insert calculated indicator bars into journal_m1_indicator_bars."""
        if df.empty:
            return 0

        # Filter to only trading day bars (08:00-16:00)
        day_df = df[
            (df['bar_date'] == trade_date) &
            (df['bar_time'] >= PREMARKET_START) &
            (df['bar_time'] <= MARKET_CLOSE)
        ].copy()

        if day_df.empty:
            return 0

        query = f"""
            INSERT INTO {INDICATOR_TABLE} (
                ticker, bar_date, bar_time,
                open, high, low, close, volume,
                vwap, sma9, sma21, sma_spread,
                sma_momentum_ratio, sma_momentum_label,
                vol_roc, vol_delta, cvd_slope,
                health_score,
                candle_range_pct, long_score, short_score,
                bars_in_calculation
            ) VALUES %s
            ON CONFLICT (ticker, bar_date, bar_time) DO NOTHING
        """

        values = []
        for idx, (_, row) in enumerate(day_df.iterrows()):
            values.append((
                ticker,
                row['bar_date'],
                row['bar_time'],
                self._convert_numpy(row['open']),
                self._convert_numpy(row['high']),
                self._convert_numpy(row['low']),
                self._convert_numpy(row['close']),
                self._convert_numpy(row['volume']),
                self._safe_float(row.get('vwap_calc')),
                self._safe_float(row.get('sma9')),
                self._safe_float(row.get('sma21')),
                self._safe_float(row.get('sma_spread')),
                self._safe_float(row.get('sma_momentum_ratio')),
                row.get('sma_momentum_label'),
                self._safe_float(row.get('vol_roc')),
                self._safe_float(row.get('vol_delta')),
                self._safe_float(row.get('cvd_slope')),
                self._safe_int(row.get('health_score')),
                self._safe_float(row.get('candle_range_pct')),
                self._safe_int(row.get('long_score')),
                self._safe_int(row.get('short_score')),
                idx + 1,
            ))

        with conn.cursor() as cur:
            execute_values(cur, query, values, page_size=BATCH_INSERT_SIZE)

        return len(values)

    # =========================================================================
    # STATUS
    # =========================================================================

    def get_status(self, conn) -> Dict[str, Any]:
        """Get current status of journal M1 tables."""
        status = {}

        with conn.cursor() as cur:
            # Raw bars
            cur.execute(f"SELECT COUNT(*) FROM {M1_BARS_TABLE}")
            status['raw_bars'] = cur.fetchone()[0]

            # Indicator bars
            cur.execute(f"SELECT COUNT(*) FROM {INDICATOR_TABLE}")
            status['indicator_bars'] = cur.fetchone()[0]

            # Unique ticker-dates in indicators
            cur.execute(f"SELECT COUNT(DISTINCT (ticker, bar_date)) FROM {INDICATOR_TABLE}")
            status['indicator_ticker_dates'] = cur.fetchone()[0]

            # Journal trades count
            cur.execute(f"SELECT COUNT(DISTINCT (symbol, trade_date)) FROM {SOURCE_TABLE}")
            status['journal_ticker_dates'] = cur.fetchone()[0]

        # Pending
        pending = self.get_missing_ticker_dates(conn)
        status['pending_ticker_dates'] = len(pending)
        if pending:
            status['pending_list'] = [f"{p['ticker']} {p['date']}" for p in pending[:10]]

        return status

    # =========================================================================
    # MAIN BATCH PROCESSOR
    # =========================================================================

    def run(
        self,
        limit: int = None,
        dry_run: bool = False,
        ticker: str = None,
        trade_date: date = None,
    ) -> Dict:
        """
        Main entry point. Process all missing or specific ticker-dates.

        Args:
            limit: Max ticker-dates to process
            dry_run: Calculate but don't write
            ticker: Specific ticker to process
            trade_date: Specific date to process
        """
        start_time = datetime.now()
        self.stats = self._reset_stats()

        print("=" * 60)
        print("Journal M1 Indicator Bars Populator")
        print("=" * 60)
        print(f"  Source: {SOURCE_TABLE}")
        print(f"  Raw target: {M1_BARS_TABLE}")
        print(f"  Indicator target: {INDICATOR_TABLE}")
        if dry_run:
            print("  Mode: DRY RUN")
        print()

        conn = None
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            print("[1/3] Connected to Supabase")

            # Determine what to process
            if ticker and trade_date:
                ticker_dates = [{'ticker': ticker.upper(), 'date': trade_date}]
                print(f"\n[2/3] Processing specific: {ticker} on {trade_date}")
            else:
                ticker_dates = self.get_missing_ticker_dates(conn, limit)
                print(f"\n[2/3] Found {len(ticker_dates)} ticker-dates needing processing")

            if not ticker_dates:
                print("\n  All ticker-dates are up to date!")
                return self._build_result(start_time)

            # Process each ticker-date
            print(f"\n[3/3] Processing...")
            total = len(ticker_dates)

            for i, td in enumerate(ticker_dates, 1):
                tk = td['ticker']
                dt = td['date']
                print(f"\n  [{i}/{total}] {tk} on {dt}")

                try:
                    # 1. Fetch extended M1 bars
                    df = self.fetcher.fetch_extended_trading_day(tk, dt)
                    if df.empty:
                        self._log(f"No M1 bars found, skipping", 'warning')
                        self.stats['ticker_dates_skipped'] += 1
                        continue

                    self._log(f"Fetched {len(df)} M1 bars (extended)")

                    # 2. Insert raw bars for trade day only
                    if not dry_run:
                        day_bars = df[df['bar_date'] == dt].copy()
                        raw_count = self.insert_raw_bars(conn, tk, dt, day_bars)
                        conn.commit()
                        self.stats['raw_bars_inserted'] += raw_count
                        self._log(f"Inserted {raw_count} raw bars")

                    # 3. Calculate indicators
                    df_with_indicators = self.calculator.add_all_indicators(df)

                    # 4. Insert indicator bars
                    if not dry_run:
                        ind_count = self.insert_indicator_bars(conn, tk, dt, df_with_indicators)
                        conn.commit()
                        self.stats['indicator_bars_inserted'] += ind_count
                        self._log(f"Inserted {ind_count} indicator bars")
                    else:
                        day_count = len(df_with_indicators[
                            (df_with_indicators['bar_date'] == dt) &
                            (df_with_indicators['bar_time'] >= PREMARKET_START) &
                            (df_with_indicators['bar_time'] <= MARKET_CLOSE)
                        ])
                        self._log(f"[DRY-RUN] Would insert {day_count} indicator bars")

                    self.stats['ticker_dates_processed'] += 1

                except Exception as e:
                    conn.rollback()
                    self.stats['ticker_dates_skipped'] += 1
                    self.stats['errors'].append(f"{tk} {dt}: {str(e)}")
                    self._log(f"Error: {e}", 'error')

                # Clear caches between ticker-dates
                self.fetcher.clear_cache()

            return self._build_result(start_time)

        except Exception as e:
            self.stats['errors'].append(f"Fatal: {str(e)}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def _build_result(self, start_time: datetime) -> Dict:
        elapsed = (datetime.now() - start_time).total_seconds()
        self.stats['execution_time_seconds'] = round(elapsed, 2)
        return self.stats


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Journal M1 Indicator Bars Populator")
    parser.add_argument('--limit', type=int, help="Max ticker-dates to process")
    parser.add_argument('--dry-run', action='store_true', help="Calculate but don't write")
    parser.add_argument('--status', action='store_true', help="Show table status")
    parser.add_argument('--ticker', type=str, help="Specific ticker to process")
    parser.add_argument('--date', type=str, help="Specific date (YYYY-MM-DD)")
    args = parser.parse_args()

    populator = JournalM1Populator(verbose=True)

    if args.status:
        conn = psycopg2.connect(**DB_CONFIG)
        status = populator.get_status(conn)
        conn.close()

        print("=" * 60)
        print("Journal M1 Tables - Status")
        print("=" * 60)
        for key, value in status.items():
            if key == 'pending_list':
                print(f"  Pending (first 10):")
                for p in value:
                    print(f"    - {p}")
            else:
                print(f"  {key}: {value}")
        return

    trade_date = None
    if args.date:
        from datetime import datetime as dt
        trade_date = dt.strptime(args.date, '%Y-%m-%d').date()

    results = populator.run(
        limit=args.limit,
        dry_run=args.dry_run,
        ticker=args.ticker,
        trade_date=trade_date,
    )

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    for key, value in results.items():
        if key == 'errors' and value:
            print(f"\n  Errors ({len(value)}):")
            for err in value[:10]:
                print(f"    ! {err}")
        else:
            print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
