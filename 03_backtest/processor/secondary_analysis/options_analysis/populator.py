"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
Options Analysis - Database Populator
XIII Trading LLC
================================================================================

Batch populator that calculates options analysis for all trades
and writes results to the options_analysis table.

Version: 1.0.0
================================================================================
"""

import psycopg2
from psycopg2.extras import execute_values, RealDictCursor
from datetime import datetime, date, time
from typing import Dict, List, Any, Optional
import logging
import numpy as np

# Handle both relative and absolute imports
try:
    from .config import (
        DB_CONFIG,
        SOURCE_TABLE,
        TARGET_TABLE,
        BATCH_INSERT_SIZE,
        VERBOSE
    )
    from .calculator import (
        OptionsAnalysisCalculator,
        OptionsAnalysisResult,
        calculate_summary_stats
    )
    from .fetcher import OptionsFetcher
except ImportError:
    from config import (
        DB_CONFIG,
        SOURCE_TABLE,
        TARGET_TABLE,
        BATCH_INSERT_SIZE,
        VERBOSE
    )
    from calculator import (
        OptionsAnalysisCalculator,
        OptionsAnalysisResult,
        calculate_summary_stats
    )
    from fetcher import OptionsFetcher


class OptionsAnalysisPopulator:
    """
    Populates the options_analysis table from trades.

    Workflow:
    1. Query trades from trades table not yet in options_analysis
    2. Group by (ticker, date) to optimize chain fetching
    3. Calculate options metrics for each trade
    4. Batch insert results
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
            'trades_inserted': 0,
            'trades_success': 0,
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
        elif isinstance(value, (np.integer, np.int64, np.int32)):
            return int(value)
        elif isinstance(value, (np.floating, np.float64, np.float32)):
            return float(value) if not np.isnan(value) else None
        elif isinstance(value, np.ndarray):
            return value.tolist()
        return value

    # =========================================================================
    # DATABASE OPERATIONS
    # =========================================================================

    def get_trades_needing_analysis(
        self,
        conn,
        limit: int = None
    ) -> List[Dict[str, Any]]:
        """
        Get trades from trades table that need options analysis.

        Args:
            conn: Database connection
            limit: Maximum number of trades

        Returns:
            List of trade dictionaries
        """
        query = f"""
            SELECT
                t.trade_id,
                t.date,
                t.ticker,
                t.direction,
                t.model,
                t.entry_time,
                t.entry_price,
                t.exit_time,
                t.stop_price,
                t.risk,
                t.pnl_r,
                t.is_winner
            FROM {SOURCE_TABLE} t
            LEFT JOIN {TARGET_TABLE} oa ON t.trade_id = oa.trade_id
            WHERE oa.trade_id IS NULL
              AND t.entry_time IS NOT NULL
              AND t.entry_price IS NOT NULL
              AND t.exit_time IS NOT NULL
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
        results: List[OptionsAnalysisResult]
    ) -> int:
        """
        Insert calculation results into options_analysis table.

        Args:
            conn: Database connection
            results: List of OptionsAnalysisResult objects

        Returns:
            Number of records inserted
        """
        if not results:
            return 0

        query = f"""
            INSERT INTO {TARGET_TABLE} (
                trade_id, ticker, direction, entry_date, entry_time, entry_price,
                options_ticker, strike, expiration, contract_type,
                option_entry_price, option_entry_time,
                option_exit_price, option_exit_time,
                pnl_dollars, pnl_percent, option_r, net_return,
                underlying_r, r_multiplier, win, status
            ) VALUES %s
            ON CONFLICT (trade_id) DO NOTHING
        """

        values = []
        for r in results:
            # Convert all values to handle numpy types and format properly
            row = (
                r.trade_id,
                r.ticker,
                r.direction,
                r.entry_date,
                r.entry_time,
                self._convert_numpy(r.entry_price),
                r.options_ticker or None,
                self._convert_numpy(r.strike) if r.strike else None,
                r.expiration if r.expiration and r.expiration != r.entry_date else None,
                r.contract_type or None,
                self._convert_numpy(r.option_entry_price),
                r.option_entry_time or None,
                self._convert_numpy(r.option_exit_price),
                r.option_exit_time or None,
                self._convert_numpy(r.pnl_dollars),
                self._convert_numpy(r.pnl_percent),
                self._convert_numpy(r.option_r),
                self._convert_numpy(r.net_return),
                self._convert_numpy(r.underlying_r),
                self._convert_numpy(r.r_multiplier),
                self._convert_numpy(r.win),
                r.status
            )
            values.append(row)

        with conn.cursor() as cur:
            execute_values(cur, query, values, page_size=BATCH_INSERT_SIZE)

        return len(values)

    # =========================================================================
    # BATCH PROCESSING
    # =========================================================================

    def run_batch_population(
        self,
        limit: int = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Main entry point. Process all trades needing options analysis.

        Args:
            limit: Max trades to process
            dry_run: If True, calculate but don't write to DB

        Returns:
            Dictionary with execution statistics
        """
        start_time = datetime.now()

        print("=" * 60)
        print("Options Analysis Populator")
        print("=" * 60)
        print(f"Source Table: {SOURCE_TABLE}")
        print(f"Target Table: {TARGET_TABLE}")
        print(f"Dry Run: {dry_run}")
        if limit:
            print(f"Limit: {limit} trades")
        print()

        # Reset statistics
        self.stats = {
            'trades_processed': 0,
            'trades_skipped': 0,
            'trades_inserted': 0,
            'trades_success': 0,
            'api_calls_made': 0,
            'errors': []
        }

        conn = None
        calculator = None
        fetcher = None

        try:
            # Connect to database
            print("[1/5] Connecting to Supabase...")
            conn = psycopg2.connect(**DB_CONFIG)
            print("  Connected successfully")

            # Get trades needing analysis
            print("\n[2/5] Querying trades needing options analysis...")
            trades = self.get_trades_needing_analysis(conn, limit)
            print(f"  Found {len(trades)} trades to process")

            if not trades:
                print("\n  No trades need analysis. Exiting.")
                return self._build_result(start_time)

            # Initialize fetcher and calculator
            print("\n[3/5] Initializing options fetcher and calculator...")
            fetcher = OptionsFetcher(verbose=False)
            calculator = OptionsAnalysisCalculator(
                fetcher=fetcher,
                verbose=self.verbose
            )
            print("  Calculator ready")

            # Group by (ticker, date) for efficient processing
            print("\n[4/5] Processing trades...")
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

                for trade in group_trades:
                    processed += 1
                    trade_id = trade['trade_id']

                    try:
                        result = calculator.calculate(trade)

                        if result:
                            all_results.append(result)
                            self.stats['trades_processed'] += 1

                            if result.status == 'SUCCESS':
                                self.stats['trades_success'] += 1

                            if processed % 10 == 0 or processed == total_trades:
                                status_icon = "+" if result.status == 'SUCCESS' else "-"
                                print(f"  [{processed}/{total_trades}] {trade_id}: {status_icon} {result.status}")
                        else:
                            self.stats['trades_skipped'] += 1
                            self._log(f"Skipped {trade_id} (calculation returned None)", 'debug')

                    except Exception as e:
                        self.stats['trades_skipped'] += 1
                        self.stats['errors'].append(f"{trade_id}: {str(e)}")
                        self._log(f"Error processing {trade_id}: {e}", 'error')

                # Clear caches between ticker-dates to manage memory
                fetcher.clear_cache()

            # Write results to database
            print(f"\n[5/5] Writing results to database...")
            if dry_run:
                print(f"  [DRY-RUN] Would insert {len(all_results)} records")
            else:
                if all_results:
                    inserted = self.insert_results(conn, all_results)
                    conn.commit()
                    self.stats['trades_inserted'] = inserted
                    print(f"  Inserted {inserted} records")
                else:
                    print("  No results to insert")

            # Print summary stats
            if all_results:
                summary = calculate_summary_stats(all_results)
                print(f"\n  Summary: {summary.successful_trades} success, "
                      f"{summary.failed_trades} failed, "
                      f"Win rate: {summary.win_rate:.1f}%")

            return self._build_result(start_time)

        except Exception as e:
            self.stats['errors'].append(f"Fatal: {str(e)}")
            if conn:
                conn.rollback()
            raise

        finally:
            if calculator:
                calculator.close()
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
    print("Options Analysis Populator - Test Run")
    print("=" * 60)

    populator = OptionsAnalysisPopulator(verbose=True)

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
