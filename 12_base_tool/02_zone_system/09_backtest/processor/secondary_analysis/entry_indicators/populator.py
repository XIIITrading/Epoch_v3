"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
Entry Indicators - Database Populator
XIII Trading LLC
================================================================================

Batch populator that calculates entry indicators for all trades
and writes results to the entry_indicators table.

Version: 1.0.0
================================================================================
"""

import psycopg2
from psycopg2.extras import execute_values, RealDictCursor
from datetime import datetime, date, time
from typing import Dict, List, Any, Optional
import logging
import numpy as np

from config import (
    DB_CONFIG,
    SOURCE_TABLE,
    TARGET_TABLE,
    BATCH_INSERT_SIZE,
    VERBOSE
)
from calculator import EntryIndicatorsCalculator, EntryIndicatorsResult
from m1_data import M1DataProvider
from entry_ind_structure import StructureAnalyzer


class EntryIndicatorsPopulator:
    """
    Populates the entry_indicators table from mfe_mae_potential trades.

    Workflow:
    1. Query trades from mfe_mae_potential not yet in entry_indicators
    2. Group by (ticker, date) to optimize bar fetching
    3. Calculate indicators for each trade
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

    def get_trades_needing_calculation(
        self,
        conn,
        limit: int = None
    ) -> List[Dict[str, Any]]:
        """
        Get trades from mfe_mae_potential that need indicator calculation.

        Args:
            conn: Database connection
            limit: Maximum number of trades

        Returns:
            List of trade dictionaries
        """
        query = f"""
            SELECT
                m.trade_id,
                m.date,
                m.ticker,
                m.direction,
                m.model,
                m.entry_time,
                m.entry_price
            FROM {SOURCE_TABLE} m
            LEFT JOIN {TARGET_TABLE} ei ON m.trade_id = ei.trade_id
            WHERE ei.trade_id IS NULL
              AND m.entry_time IS NOT NULL
              AND m.entry_price IS NOT NULL
            ORDER BY m.date DESC, m.ticker, m.entry_time
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
        results: List[EntryIndicatorsResult]
    ) -> int:
        """
        Insert calculation results into entry_indicators table.

        Args:
            conn: Database connection
            results: List of EntryIndicatorsResult objects

        Returns:
            Number of records inserted
        """
        if not results:
            return 0

        query = f"""
            INSERT INTO {TARGET_TABLE} (
                trade_id, date, ticker, direction, model, entry_time, entry_price,
                indicator_bar_time, indicator_methodology,
                h4_structure, h4_structure_healthy,
                h1_structure, h1_structure_healthy,
                m15_structure, m15_structure_healthy,
                m5_structure, m5_structure_healthy,
                vol_roc, vol_roc_healthy,
                vol_delta, vol_delta_healthy,
                cvd_slope, cvd_slope_healthy,
                sma9, sma21, sma_spread, sma_alignment, sma_alignment_healthy,
                sma_momentum, sma_momentum_label, sma_momentum_healthy,
                vwap, vwap_position, vwap_healthy,
                health_score, health_label,
                structure_score, volume_score, price_score,
                bars_used, calculation_version
            ) VALUES %s
            ON CONFLICT (trade_id) DO NOTHING
        """

        values = []
        for r in results:
            # Convert all values to handle numpy types
            row = (
                r.trade_id, r.date, r.ticker, r.direction, r.model,
                r.entry_time, self._convert_numpy(r.entry_price),
                r.indicator_bar_time, r.indicator_methodology,
                r.h4_structure, self._convert_numpy(r.h4_structure_healthy),
                r.h1_structure, self._convert_numpy(r.h1_structure_healthy),
                r.m15_structure, self._convert_numpy(r.m15_structure_healthy),
                r.m5_structure, self._convert_numpy(r.m5_structure_healthy),
                self._convert_numpy(r.vol_roc), self._convert_numpy(r.vol_roc_healthy),
                self._convert_numpy(r.vol_delta), self._convert_numpy(r.vol_delta_healthy),
                self._convert_numpy(r.cvd_slope), self._convert_numpy(r.cvd_slope_healthy),
                self._convert_numpy(r.sma9), self._convert_numpy(r.sma21),
                self._convert_numpy(r.sma_spread), r.sma_alignment,
                self._convert_numpy(r.sma_alignment_healthy),
                self._convert_numpy(r.sma_momentum), r.sma_momentum_label,
                self._convert_numpy(r.sma_momentum_healthy),
                self._convert_numpy(r.vwap), r.vwap_position,
                self._convert_numpy(r.vwap_healthy),
                self._convert_numpy(r.health_score), r.health_label,
                self._convert_numpy(r.structure_score), self._convert_numpy(r.volume_score),
                self._convert_numpy(r.price_score),
                self._convert_numpy(r.bars_used), r.calculation_version
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
        Main entry point. Process all trades needing indicator calculation.

        Args:
            limit: Max trades to process
            dry_run: If True, calculate but don't write to DB

        Returns:
            Dictionary with execution statistics
        """
        start_time = datetime.now()

        print("=" * 60)
        print("Entry Indicators Populator")
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
            'api_calls_made': 0,
            'errors': []
        }

        conn = None
        calculator = None

        try:
            # Connect to database
            print("[1/5] Connecting to Supabase...")
            conn = psycopg2.connect(**DB_CONFIG)
            print("  Connected successfully")

            # Get trades needing calculation
            print("\n[2/5] Querying trades needing indicator calculation...")
            trades = self.get_trades_needing_calculation(conn, limit)
            print(f"  Found {len(trades)} trades to process")

            if not trades:
                print("\n  No trades need calculation. Exiting.")
                return self._build_result(start_time)

            # Initialize calculator with shared resources
            print("\n[3/5] Initializing calculator...")
            m1_provider = M1DataProvider(conn=conn)
            structure_analyzer = StructureAnalyzer()
            calculator = EntryIndicatorsCalculator(
                m1_provider=m1_provider,
                structure_analyzer=structure_analyzer,
                verbose=False  # Reduce noise
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

                            if processed % 10 == 0 or processed == total_trades:
                                print(f"  [{processed}/{total_trades}] {trade_id}: score={result.health_score}")
                        else:
                            self.stats['trades_skipped'] += 1
                            self._log(f"Skipped {trade_id} (calculation returned None)", 'debug')

                    except Exception as e:
                        self.stats['trades_skipped'] += 1
                        self.stats['errors'].append(f"{trade_id}: {str(e)}")
                        self._log(f"Error processing {trade_id}: {e}", 'error')

                # Clear caches between ticker-dates
                m1_provider.clear_cache()
                structure_analyzer.clear_cache()

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
    print("Entry Indicators Populator - Test Run")
    print("=" * 60)

    populator = EntryIndicatorsPopulator(verbose=True)

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
