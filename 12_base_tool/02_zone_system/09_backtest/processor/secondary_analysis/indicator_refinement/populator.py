"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
Indicator Refinement - Database Populator
XIII Trading LLC
================================================================================

Batch populator that calculates Continuation/Rejection scores for all trades
and writes results to the indicator_refinement table.

Workflow:
    1. Query trades from entry_indicators not yet in indicator_refinement
    2. Fetch M5 bars for each trade's ticker-date
    3. Calculate continuation and rejection scores
    4. Batch insert results

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
    SOURCE_TABLE,
    TARGET_TABLE,
    M5_BARS_TABLE,
    TRADES_TABLE,
    BATCH_INSERT_SIZE,
    VERBOSE
)
from calculator import IndicatorRefinementCalculator, IndicatorRefinementResult


class IndicatorRefinementPopulator:
    """
    Populates the indicator_refinement table from entry_indicators data.

    Workflow:
    1. Query trades from entry_indicators not yet in indicator_refinement
    2. Group by (ticker, date) to optimize M5 bar fetching
    3. Calculate continuation/rejection scores for each trade
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

    def _convert_time(self, value):
        """Convert timedelta to time object."""
        if isinstance(value, timedelta):
            total_seconds = int(value.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            return time(hours, minutes, seconds)
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
        Get trades from entry_indicators that need refinement calculation.

        Args:
            conn: Database connection
            limit: Maximum number of trades

        Returns:
            List of trade dictionaries with entry_indicators data
        """
        query = f"""
            SELECT
                ei.trade_id,
                ei.date,
                ei.ticker,
                ei.direction,
                ei.model,
                ei.entry_time,
                ei.entry_price,
                -- Structure data
                ei.h4_structure,
                ei.h1_structure,
                ei.m15_structure,
                ei.m5_structure,
                -- Volume data
                ei.vol_roc,
                ei.vol_delta,
                ei.cvd_slope,
                -- SMA data
                ei.sma9,
                ei.sma21,
                ei.sma_spread,
                ei.sma_alignment,
                ei.sma_momentum
            FROM {SOURCE_TABLE} ei
            LEFT JOIN {TARGET_TABLE} ir ON ei.trade_id = ir.trade_id
            WHERE ir.trade_id IS NULL
              AND ei.entry_time IS NOT NULL
              AND ei.entry_price IS NOT NULL
              AND ei.model IS NOT NULL
            ORDER BY ei.date DESC, ei.ticker, ei.entry_time
        """

        if limit:
            query += f" LIMIT {limit}"

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            rows = cur.fetchall()

        return [dict(row) for row in rows]

    def get_m5_bars_for_trade(
        self,
        conn,
        ticker: str,
        trade_date: date,
        entry_time: time
    ) -> List[Dict[str, Any]]:
        """
        Get M5 indicator bars for a trade.

        Args:
            conn: Database connection
            ticker: Stock ticker
            trade_date: Trade date
            entry_time: Entry time

        Returns:
            List of M5 bar dictionaries
        """
        query = f"""
            SELECT
                bar_time,
                open,
                high,
                low,
                close,
                volume,
                vwap,
                sma9,
                sma21,
                vol_delta,
                cvd_slope
            FROM {M5_BARS_TABLE}
            WHERE ticker = %s
              AND bar_date = %s
              AND bar_time <= %s
            ORDER BY bar_time ASC
        """

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (ticker, trade_date, entry_time))
            rows = cur.fetchall()

        return [dict(row) for row in rows]

    def insert_results(
        self,
        conn,
        results: List[IndicatorRefinementResult]
    ) -> int:
        """
        Insert calculation results into indicator_refinement table.

        Args:
            conn: Database connection
            results: List of IndicatorRefinementResult objects

        Returns:
            Number of records inserted
        """
        if not results:
            return 0

        query = f"""
            INSERT INTO {TARGET_TABLE} (
                trade_id, date, ticker, direction, model, entry_time, entry_price,
                trade_type,
                -- Continuation indicators
                mtf_align_score, mtf_h4_aligned, mtf_h1_aligned, mtf_m15_aligned, mtf_m5_aligned,
                sma_mom_score, sma_spread, sma_spread_pct, sma_spread_roc,
                sma_spread_aligned, sma_spread_expanding,
                vol_thrust_score, vol_roc, vol_delta_5, vol_roc_strong, vol_delta_aligned,
                pullback_score, in_pullback, pullback_delta_ratio,
                continuation_score, continuation_label,
                -- Rejection indicators
                struct_div_score, htf_aligned, ltf_divergent,
                sma_exhst_score, sma_spread_contracting, sma_spread_very_tight, sma_spread_tight,
                delta_abs_score, absorption_ratio,
                vol_climax_score, vol_roc_q5, vol_declining,
                cvd_extr_score, cvd_slope, cvd_slope_normalized, cvd_extreme,
                rejection_score, rejection_label,
                -- Metadata
                calculation_version
            ) VALUES %s
            ON CONFLICT (trade_id) DO NOTHING
        """

        values = []
        for r in results:
            row = (
                r.trade_id, r.date, r.ticker, r.direction, r.model,
                r.entry_time, self._convert_numpy(r.entry_price),
                r.trade_type,
                # Continuation
                self._convert_numpy(r.mtf_align_score),
                self._convert_numpy(r.mtf_h4_aligned),
                self._convert_numpy(r.mtf_h1_aligned),
                self._convert_numpy(r.mtf_m15_aligned),
                self._convert_numpy(r.mtf_m5_aligned),
                self._convert_numpy(r.sma_mom_score),
                self._convert_numpy(r.sma_spread),
                self._convert_numpy(r.sma_spread_pct),
                self._convert_numpy(r.sma_spread_roc),
                self._convert_numpy(r.sma_spread_aligned),
                self._convert_numpy(r.sma_spread_expanding),
                self._convert_numpy(r.vol_thrust_score),
                self._convert_numpy(r.vol_roc),
                self._convert_numpy(r.vol_delta_5),
                self._convert_numpy(r.vol_roc_strong),
                self._convert_numpy(r.vol_delta_aligned),
                self._convert_numpy(r.pullback_score),
                self._convert_numpy(r.in_pullback),
                self._convert_numpy(r.pullback_delta_ratio),
                self._convert_numpy(r.continuation_score),
                r.continuation_label,
                # Rejection
                self._convert_numpy(r.struct_div_score),
                self._convert_numpy(r.htf_aligned),
                self._convert_numpy(r.ltf_divergent),
                self._convert_numpy(r.sma_exhst_score),
                self._convert_numpy(r.sma_spread_contracting),
                self._convert_numpy(r.sma_spread_very_tight),
                self._convert_numpy(r.sma_spread_tight),
                self._convert_numpy(r.delta_abs_score),
                self._convert_numpy(r.absorption_ratio),
                self._convert_numpy(r.vol_climax_score),
                self._convert_numpy(r.vol_roc_q5),
                self._convert_numpy(r.vol_declining),
                self._convert_numpy(r.cvd_extr_score),
                self._convert_numpy(r.cvd_slope),
                self._convert_numpy(r.cvd_slope_normalized),
                self._convert_numpy(r.cvd_extreme),
                self._convert_numpy(r.rejection_score),
                r.rejection_label,
                # Metadata
                r.calculation_version
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
        Main entry point. Process all trades needing indicator refinement.

        Args:
            limit: Max trades to process
            dry_run: If True, calculate but don't write to DB

        Returns:
            Dictionary with execution statistics
        """
        start_time = datetime.now()

        print("=" * 60)
        print("Indicator Refinement Populator")
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
            'errors': []
        }

        conn = None

        try:
            # Connect to database
            print("[1/5] Connecting to Supabase...")
            conn = psycopg2.connect(**DB_CONFIG)
            print("  Connected successfully")

            # Get trades needing calculation
            print("\n[2/5] Querying trades needing indicator refinement...")
            trades = self.get_trades_needing_calculation(conn, limit)
            print(f"  Found {len(trades)} trades to process")

            if not trades:
                print("\n  No trades need calculation. Exiting.")
                return self._build_result(start_time)

            # Initialize calculator
            print("\n[3/5] Initializing calculator...")
            calculator = IndicatorRefinementCalculator(verbose=False)
            print("  Calculator ready")

            # Group by (ticker, date) for efficient M5 bar fetching
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
            m5_cache = {}  # Cache M5 bars by (ticker, date)

            for (ticker, trade_date), group_trades in groups.items():
                self._log(f"\nProcessing {ticker} on {trade_date} ({len(group_trades)} trades)...")

                for trade in group_trades:
                    processed += 1
                    trade_id = trade['trade_id']

                    try:
                        # Convert entry_time
                        entry_time = self._convert_time(trade.get('entry_time'))
                        trade['entry_time'] = entry_time

                        # Get M5 bars (cached by ticker-date)
                        cache_key = (ticker, trade_date)
                        if cache_key not in m5_cache:
                            # Fetch all M5 bars for the day
                            m5_cache[cache_key] = self.get_m5_bars_for_trade(
                                conn, ticker, trade_date, time(16, 0)
                            )

                        # Filter M5 bars up to entry time
                        all_m5_bars = m5_cache[cache_key]
                        m5_bars = [
                            bar for bar in all_m5_bars
                            if self._convert_time(bar.get('bar_time')) <= entry_time
                        ]

                        # Calculate scores
                        result = calculator.calculate(
                            trade=trade,
                            entry_indicators=trade,
                            m5_bars=m5_bars,
                            structure_data=None  # Use entry_indicators structure
                        )

                        if result:
                            all_results.append(result)
                            self.stats['trades_processed'] += 1

                            if processed % 10 == 0 or processed == total_trades:
                                print(f"  [{processed}/{total_trades}] {trade_id}: "
                                      f"cont={result.continuation_score}, "
                                      f"rej={result.rejection_score}")
                        else:
                            self.stats['trades_skipped'] += 1
                            self._log(f"Skipped {trade_id} (calculation returned None)", 'debug')

                    except Exception as e:
                        self.stats['trades_skipped'] += 1
                        self.stats['errors'].append(f"{trade_id}: {str(e)}")
                        self._log(f"Error processing {trade_id}: {e}", 'error')

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
    print("Indicator Refinement Populator - Test Run")
    print("=" * 60)

    populator = IndicatorRefinementPopulator(verbose=True)

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
