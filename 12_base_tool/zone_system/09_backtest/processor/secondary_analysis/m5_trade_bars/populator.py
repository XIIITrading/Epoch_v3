"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
M5 Trade Bars - Database Populator
XIII Trading LLC
================================================================================

Batch populator that calculates trade-specific M5 bars and writes results
to the m5_trade_bars table.

Key Features:
- Queries trades from trades table
- Joins to mfe_mae_potential for MFE/MAE times
- Groups by (ticker, date) for efficient API calls
- Batch insert with ON CONFLICT handling

Version: 1.0.0
================================================================================
"""

import psycopg2
from psycopg2.extras import execute_values, RealDictCursor
from datetime import datetime, date, time, timedelta
from typing import Dict, List, Any, Optional
import logging
import numpy as np

from config import (
    DB_CONFIG,
    TRADES_TABLE,
    MFE_MAE_TABLE,
    TARGET_TABLE,
    BATCH_INSERT_SIZE,
    VERBOSE
)
from calculator import M5TradeBarsCalculator, M5TradeBarResult
from m5_fetcher import M5Fetcher
from indicators import M5IndicatorCalculator


class M5TradeBarsPopulator:
    """
    Populates the m5_trade_bars table from trades.

    Workflow:
    1. Query trades from trades table
    2. JOIN to mfe_mae_potential for MFE/MAE times
    3. LEFT JOIN to m5_trade_bars to find trades not yet calculated
    4. Group trades by (ticker, date) for efficient API calls
    5. For each group, calculate all trade bars
    6. Batch insert results
    """

    def __init__(self, verbose: bool = None):
        """
        Initialize the populator.

        Args:
            verbose: Enable verbose logging (defaults to config)
        """
        self.verbose = verbose if verbose is not None else VERBOSE
        self.logger = logging.getLogger(__name__)

        # Statistics
        self.stats = {
            'trades_processed': 0,
            'trades_skipped': 0,
            'bars_inserted': 0,
            'api_calls_made': 0,
            'errors': []
        }

    def _log(self, message: str, level: str = 'info'):
        """Log message if verbose."""
        if self.verbose or level in ('error', 'warning'):
            prefix = {'error': '!', 'warning': '?', 'info': ' ', 'debug': '  '}
            print(f"  {prefix.get(level, ' ')} {message}")

    def _convert_numpy(self, value):
        """Convert numpy types to Python native types for database insertion."""
        if isinstance(value, np.bool_):
            return bool(value)
        elif isinstance(value, np.integer):
            return int(value)
        elif isinstance(value, np.floating):
            return float(value) if not np.isnan(value) else None
        elif isinstance(value, np.ndarray):
            return value.tolist()
        return value

    def _convert_time(self, value) -> Optional[time]:
        """Convert timedelta or time to time object."""
        if value is None:
            return None
        if isinstance(value, time):
            return value
        if isinstance(value, timedelta):
            total_seconds = int(value.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return time(hours, minutes, 0)
        return None

    # =========================================================================
    # DATABASE OPERATIONS
    # =========================================================================

    def get_trades_needing_calculation(
        self,
        conn,
        limit: int = None
    ) -> List[Dict[str, Any]]:
        """
        Get trades that need M5 trade bar calculation.

        Args:
            conn: Database connection
            limit: Maximum number of trades

        Returns:
            List of trade dictionaries with MFE/MAE times
        """
        query = f"""
            SELECT
                t.trade_id,
                t.date,
                t.ticker,
                t.direction,
                t.model,
                t.entry_time,
                m.mfe_potential_time,
                m.mae_potential_time
            FROM {TRADES_TABLE} t
            LEFT JOIN {MFE_MAE_TABLE} m ON t.trade_id = m.trade_id
            LEFT JOIN {TARGET_TABLE} tb ON t.trade_id = tb.trade_id
            WHERE tb.trade_id IS NULL
              AND t.entry_time IS NOT NULL
              AND t.date IS NOT NULL
              AND t.ticker IS NOT NULL
              AND t.direction IS NOT NULL
            ORDER BY t.date DESC, t.ticker, t.entry_time
        """

        if limit:
            query += f" LIMIT {limit}"

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            rows = cur.fetchall()

        return [dict(row) for row in rows]

    def insert_results(
        self,
        conn,
        results: List[M5TradeBarResult]
    ) -> int:
        """
        Insert calculation results into m5_trade_bars table.

        Args:
            conn: Database connection
            results: List of M5TradeBarResult objects

        Returns:
            Number of records inserted
        """
        if not results:
            return 0

        query = f"""
            INSERT INTO {TARGET_TABLE} (
                trade_id, bar_seq, bar_time, bars_from_entry, event_type,
                date, ticker, direction, model,
                open, high, low, close, volume,
                vwap, sma9, sma21, sma_spread,
                sma_alignment, sma_alignment_healthy,
                sma_momentum_ratio, sma_momentum_label, sma_momentum_healthy,
                vwap_position, vwap_healthy,
                vol_roc, vol_roc_healthy,
                vol_delta, vol_delta_healthy,
                cvd_slope, cvd_slope_healthy,
                h4_structure, h4_structure_healthy,
                h1_structure, h1_structure_healthy,
                m15_structure, m15_structure_healthy,
                m5_structure, m5_structure_healthy,
                health_score, health_label,
                structure_score, volume_score, price_score
            ) VALUES %s
            ON CONFLICT (trade_id, bar_seq) DO NOTHING
        """

        values = []
        for r in results:
            row = (
                r.trade_id,
                r.bar_seq,
                r.bar_time,
                r.bars_from_entry,
                r.event_type,
                r.date,
                r.ticker,
                r.direction,
                r.model,
                self._convert_numpy(r.open),
                self._convert_numpy(r.high),
                self._convert_numpy(r.low),
                self._convert_numpy(r.close),
                self._convert_numpy(r.volume),
                self._convert_numpy(r.vwap),
                self._convert_numpy(r.sma9),
                self._convert_numpy(r.sma21),
                self._convert_numpy(r.sma_spread),
                r.sma_alignment,
                self._convert_numpy(r.sma_alignment_healthy),
                self._convert_numpy(r.sma_momentum_ratio),
                r.sma_momentum_label,
                self._convert_numpy(r.sma_momentum_healthy),
                r.vwap_position,
                self._convert_numpy(r.vwap_healthy),
                self._convert_numpy(r.vol_roc),
                self._convert_numpy(r.vol_roc_healthy),
                self._convert_numpy(r.vol_delta),
                self._convert_numpy(r.vol_delta_healthy),
                self._convert_numpy(r.cvd_slope),
                self._convert_numpy(r.cvd_slope_healthy),
                r.h4_structure,
                self._convert_numpy(r.h4_structure_healthy),
                r.h1_structure,
                self._convert_numpy(r.h1_structure_healthy),
                r.m15_structure,
                self._convert_numpy(r.m15_structure_healthy),
                r.m5_structure,
                self._convert_numpy(r.m5_structure_healthy),
                self._convert_numpy(r.health_score),
                r.health_label,
                self._convert_numpy(r.structure_score),
                self._convert_numpy(r.volume_score),
                self._convert_numpy(r.price_score)
            )
            values.append(row)

        with conn.cursor() as cur:
            execute_values(cur, query, values, page_size=BATCH_INSERT_SIZE)

        return len(values)

    def get_status(self, conn) -> Dict[str, Any]:
        """
        Get current status of m5_trade_bars table.

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

        # Count unique trades
        with conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(DISTINCT trade_id) FROM {TARGET_TABLE}")
            status['unique_trades'] = cur.fetchone()[0]

        # Count by event type
        with conn.cursor() as cur:
            cur.execute(f"""
                SELECT event_type, COUNT(*)
                FROM {TARGET_TABLE}
                GROUP BY event_type
                ORDER BY event_type
            """)
            status['event_counts'] = dict(cur.fetchall())

        # Get date range
        with conn.cursor() as cur:
            cur.execute(f"SELECT MIN(date), MAX(date) FROM {TARGET_TABLE}")
            row = cur.fetchone()
            status['min_date'] = row[0]
            status['max_date'] = row[1]

        # Count pending trades
        pending = self.get_trades_needing_calculation(conn)
        status['pending_trades'] = len(pending)

        return status

    # =========================================================================
    # BATCH PROCESSING
    # =========================================================================

    def run_batch_population(
        self,
        limit: int = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Main entry point. Process all trades needing M5 trade bar calculation.

        Args:
            limit: Max trades to process
            dry_run: If True, calculate but don't write to DB

        Returns:
            Dictionary with execution statistics
        """
        start_time = datetime.now()

        print("=" * 60)
        print("M5 Trade Bars Populator")
        print("=" * 60)
        print(f"Source Table: {TRADES_TABLE}")
        print(f"MFE/MAE Table: {MFE_MAE_TABLE}")
        print(f"Target Table: {TARGET_TABLE}")
        print(f"Dry Run: {dry_run}")
        if limit:
            print(f"Limit: {limit} trades")
        print()

        # Reset statistics
        self.stats = {
            'trades_processed': 0,
            'trades_skipped': 0,
            'bars_inserted': 0,
            'api_calls_made': 0,
            'errors': []
        }

        conn = None
        calculator = None
        m5_fetcher = None
        indicator_calculator = None

        try:
            # Connect to database
            print("[1/4] Connecting to Supabase...")
            conn = psycopg2.connect(**DB_CONFIG)
            print("  Connected successfully")

            # Get trades needing calculation
            print("\n[2/4] Querying trades needing M5 trade bar calculation...")
            trades = self.get_trades_needing_calculation(conn, limit)
            print(f"  Found {len(trades)} trades to process")

            if not trades:
                print("\n  No trades need calculation. Exiting.")
                return self._build_result(start_time)

            # Initialize calculator and shared resources
            print("\n[3/4] Initializing calculator...")
            m5_fetcher = M5Fetcher()
            indicator_calculator = M5IndicatorCalculator()
            calculator = M5TradeBarsCalculator(
                m5_fetcher=m5_fetcher,
                indicator_calculator=indicator_calculator,
                verbose=False
            )
            print("  Calculator ready")

            # Group trades by (ticker, date) for efficient processing
            print("\n[4/4] Processing trades...")
            groups = {}
            for trade in trades:
                key = (trade['ticker'], trade['date'])
                if key not in groups:
                    groups[key] = []
                groups[key].append(trade)

            print(f"  {len(groups)} unique ticker-date combinations")

            all_results = []
            total_trades = len(trades)
            processed = 0

            for (ticker, trade_date), group_trades in groups.items():
                self._log(f"\nProcessing {ticker} on {trade_date} ({len(group_trades)} trades)...")

                # Fetch M5 bars once for this ticker-date
                df = m5_fetcher.fetch_extended_trading_day(ticker, trade_date)

                if df.empty:
                    self._log(f"No M5 bars for {ticker} {trade_date}, skipping group", 'warning')
                    for trade in group_trades:
                        self.stats['trades_skipped'] += 1
                        processed += 1
                    continue

                # Add indicators once for this ticker-date
                df_with_indicators = indicator_calculator.add_all_indicators(df)

                # Process each trade in the group
                for trade in group_trades:
                    processed += 1
                    trade_id = trade['trade_id']

                    try:
                        # Get MFE/MAE times
                        mfe_time = self._convert_time(trade.get('mfe_potential_time'))
                        mae_time = self._convert_time(trade.get('mae_potential_time'))

                        # Calculate trade bars
                        results = calculator.calculate_for_trade(
                            trade=trade,
                            mfe_time=mfe_time,
                            mae_time=mae_time,
                            df_with_indicators=df_with_indicators
                        )

                        if results:
                            all_results.extend(results)
                            self.stats['trades_processed'] += 1

                            if processed % 10 == 0 or processed == total_trades:
                                print(f"  [{processed}/{total_trades}] {trade_id}: {len(results)} bars")
                        else:
                            self.stats['trades_skipped'] += 1
                            self._log(f"Skipped {trade_id} (no bars)", 'debug')

                    except Exception as e:
                        self.stats['trades_skipped'] += 1
                        self.stats['errors'].append(f"{trade_id}: {str(e)}")
                        self._log(f"Error processing {trade_id}: {e}", 'error')

                # Clear structure cache between ticker-dates
                calculator.structure_analyzer.clear_cache()

            # Write results to database
            print(f"\nWriting results to database...")
            if dry_run:
                print(f"  [DRY-RUN] Would insert {len(all_results)} records")
            else:
                if all_results:
                    try:
                        inserted = self.insert_results(conn, all_results)
                        conn.commit()
                        self.stats['bars_inserted'] = inserted
                        print(f"  Inserted {inserted} records")
                    except Exception as e:
                        conn.rollback()
                        self.stats['errors'].append(f"Insert failed: {str(e)}")
                        self._log(f"Error inserting results: {e}", 'error')
                else:
                    print("  No results to insert")

            return self._build_result(start_time)

        except Exception as e:
            self.stats['errors'].append(f"Fatal: {str(e)}")
            if conn:
                conn.rollback()
            raise

        finally:
            if calculator:
                calculator.clear_caches()
            if m5_fetcher:
                m5_fetcher.clear_cache()
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
    print("M5 Trade Bars Populator - Test Run")
    print("=" * 60)

    populator = M5TradeBarsPopulator(verbose=True)

    # Test with dry run, limit 5
    results = populator.run_batch_population(limit=5, dry_run=True)

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
