"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
Trade Lifecycle Analysis - Database Populator
XIII Trading LLC
================================================================================

Batch populator that extracts lifecycle signals for all trades and writes
results to the trade_lifecycle_signals table.

Workflow:
    1. Query trade entries from m5_trade_bars (ENTRY events) + outcomes
    2. Group by (ticker, date) to load M1 bars once per group
    3. Calculate lifecycle signals for each trade
    4. Batch insert results

Version: 1.0.0
================================================================================
"""

import psycopg2
from psycopg2.extras import execute_values, RealDictCursor
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict

from config import (
    DB_CONFIG,
    M1_BARS_TABLE,
    M5_TRADE_BARS_TABLE,
    TRADES_TABLE,
    TARGET_TABLE,
    BATCH_INSERT_SIZE,
    VERBOSE,
    M1_NUMERIC_INDICATORS,
    M1_CATEGORICAL_INDICATORS,
    FLIP_INDICATORS,
    CALCULATION_VERSION,
)
from calculator import calculate_lifecycle, LifecycleResult


class LifecyclePopulator:
    """
    Populates the trade_lifecycle_signals table.

    Workflow:
    1. Query trade entries (ENTRY events) with outcomes
    2. Group by (ticker, date) for efficient M1 bar loading
    3. Calculate lifecycle signals via calculator.py
    4. Batch upsert results
    """

    def __init__(self, verbose: bool = None):
        self.verbose = verbose if verbose is not None else VERBOSE
        self.stats = {
            "trades_processed": 0,
            "trades_inserted": 0,
            "trades_skipped": 0,
            "groups_processed": 0,
            "errors": [],
            "execution_time_seconds": 0,
        }

    def _log(self, message: str, level: str = "info"):
        if self.verbose or level in ("error", "warning"):
            prefix = {"error": "!", "warning": "?", "info": " ", "debug": "  "}
            print(f"  {prefix.get(level, ' ')} {message}")

    # ------------------------------------------------------------------
    # DATA LOADING
    # ------------------------------------------------------------------

    def _load_trade_entries(self, conn, limit: Optional[int] = None) -> List[Dict]:
        """Load trade entry records with outcomes, excluding already-processed."""
        cur = conn.cursor(cursor_factory=RealDictCursor)

        query = f"""
            SELECT
                tb.trade_id,
                tb.ticker,
                tb.date,
                tb.bar_time AS entry_time,
                tb.direction,
                tb.model,
                t.is_winner
            FROM {M5_TRADE_BARS_TABLE} tb
            INNER JOIN {TRADES_TABLE} t ON tb.trade_id = t.trade_id
            WHERE tb.event_type = 'ENTRY'
              AND tb.trade_id NOT IN (
                  SELECT trade_id FROM {TARGET_TABLE}
              )
            ORDER BY tb.date, tb.ticker, tb.bar_time
        """

        if limit:
            query += f" LIMIT {limit}"

        cur.execute(query)
        rows = cur.fetchall()
        cur.close()
        return [dict(r) for r in rows]

    def _load_m1_bars(self, conn, ticker: str, bar_date) -> List[Dict]:
        """Load all M1 indicator bars for a ticker/date, ordered by time."""
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            f"""
            SELECT * FROM {M1_BARS_TABLE}
            WHERE ticker = %s AND bar_date = %s
            ORDER BY bar_time
            """,
            (ticker, bar_date),
        )
        rows = cur.fetchall()
        cur.close()
        return [dict(r) for r in rows]

    def _load_m5_trade_bars(self, conn, trade_id: str) -> List[Dict]:
        """Load M5 trade bars for a specific trade."""
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            f"""
            SELECT * FROM {M5_TRADE_BARS_TABLE}
            WHERE trade_id = %s
            ORDER BY bar_seq
            """,
            (trade_id,),
        )
        rows = cur.fetchall()
        cur.close()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # DATABASE WRITE
    # ------------------------------------------------------------------

    def _build_insert_tuple(self, result: LifecycleResult) -> tuple:
        """Convert a LifecycleResult into a tuple for batch insert."""
        return (
            result.trade_id,
            result.ticker,
            result.date,
            result.entry_time,
            result.direction,
            result.model,
            result.is_winner,
            result.rampup_bars_found,
            result.post_entry_bars_found,
            # Rampup trend signals
            result.rampup_signals.get("candle_range_pct"),
            result.rampup_signals.get("vol_delta"),
            result.rampup_signals.get("vol_roc"),
            result.rampup_signals.get("cvd_slope"),
            result.rampup_signals.get("sma_spread"),
            result.rampup_signals.get("sma_momentum_ratio"),
            result.rampup_signals.get("health_score"),
            result.rampup_signals.get("long_score"),
            result.rampup_signals.get("short_score"),
            # Entry level signals
            result.entry_levels.get("candle_range_pct"),
            result.entry_levels.get("vol_delta"),
            result.entry_levels.get("vol_roc"),
            result.entry_levels.get("cvd_slope"),
            result.entry_levels.get("sma_spread"),
            result.entry_levels.get("sma_momentum_ratio"),
            result.entry_levels.get("health_score"),
            result.entry_levels.get("long_score"),
            result.entry_levels.get("short_score"),
            # Entry categoricals
            result.entry_categoricals.get("sma_momentum_label"),
            result.entry_categoricals.get("m1_structure"),
            result.entry_categoricals.get("m5_structure"),
            result.entry_categoricals.get("m15_structure"),
            result.entry_categoricals.get("h1_structure"),
            result.entry_categoricals.get("h4_structure"),
            # Post-entry trend signals
            result.post_entry_signals.get("candle_range_pct"),
            result.post_entry_signals.get("vol_delta"),
            result.post_entry_signals.get("vol_roc"),
            result.post_entry_signals.get("cvd_slope"),
            result.post_entry_signals.get("sma_spread"),
            result.post_entry_signals.get("sma_momentum_ratio"),
            result.post_entry_signals.get("health_score"),
            result.post_entry_signals.get("long_score"),
            result.post_entry_signals.get("short_score"),
            # Flip signals
            result.flip_signals.get("vol_delta"),
            result.flip_signals.get("cvd_slope"),
            result.flip_signals.get("sma_spread"),
            # M5 progression
            result.m5_health_at_entry,
            result.m5_health_at_end,
            result.m5_health_trend,
            result.m5_bars_total,
            # Metadata
            CALCULATION_VERSION,
        )

    def _batch_insert(self, conn, results: List[LifecycleResult], dry_run: bool = False):
        """Batch insert lifecycle results into the target table."""
        if not results or dry_run:
            return

        columns = [
            "trade_id", "ticker", "date", "entry_time", "direction", "model",
            "is_winner", "rampup_bars_found", "post_entry_bars_found",
            # Rampup
            "rampup_candle_range_pct", "rampup_vol_delta", "rampup_vol_roc",
            "rampup_cvd_slope", "rampup_sma_spread", "rampup_sma_momentum_ratio",
            "rampup_health_score", "rampup_long_score", "rampup_short_score",
            # Entry levels
            "entry_candle_range_pct", "entry_vol_delta", "entry_vol_roc",
            "entry_cvd_slope", "entry_sma_spread", "entry_sma_momentum_ratio",
            "entry_health_score", "entry_long_score", "entry_short_score",
            # Entry categoricals
            "entry_sma_momentum_label", "entry_m1_structure", "entry_m5_structure",
            "entry_m15_structure", "entry_h1_structure", "entry_h4_structure",
            # Post-entry
            "post_candle_range_pct", "post_vol_delta", "post_vol_roc",
            "post_cvd_slope", "post_sma_spread", "post_sma_momentum_ratio",
            "post_health_score", "post_long_score", "post_short_score",
            # Flips
            "flip_vol_delta", "flip_cvd_slope", "flip_sma_spread",
            # M5 progression
            "m5_health_at_entry", "m5_health_at_end", "m5_health_trend",
            "m5_bars_total",
            # Metadata
            "calculation_version",
        ]

        col_str = ", ".join(columns)
        template = "(" + ", ".join(["%s"] * len(columns)) + ")"

        tuples = [self._build_insert_tuple(r) for r in results]

        cur = conn.cursor()
        try:
            execute_values(
                cur,
                f"INSERT INTO {TARGET_TABLE} ({col_str}) VALUES %s "
                f"ON CONFLICT (trade_id) DO NOTHING",
                tuples,
                template=template,
                page_size=BATCH_INSERT_SIZE,
            )
            conn.commit()
            self.stats["trades_inserted"] += len(tuples)
        except Exception as e:
            conn.rollback()
            self.stats["errors"].append(f"Batch insert error: {e}")
            self._log(f"Batch insert error: {e}", "error")
        finally:
            cur.close()

    # ------------------------------------------------------------------
    # MAIN BATCH PROCESSING
    # ------------------------------------------------------------------

    def run_batch_population(
        self,
        limit: Optional[int] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Run the full batch population pipeline.

        Args:
            limit: Max trades to process (None = all)
            dry_run: If True, calculate but don't write to database

        Returns:
            Stats dict with processing results
        """
        start_time = datetime.now()

        conn = psycopg2.connect(**DB_CONFIG)

        try:
            # Step 1: Load trade entries
            self._log("Loading trade entries...")
            trades = self._load_trade_entries(conn, limit)
            self._log(f"Found {len(trades)} unprocessed trades")

            if not trades:
                self._log("No trades to process.")
                self.stats["execution_time_seconds"] = (
                    datetime.now() - start_time
                ).total_seconds()
                return self.stats

            # Step 2: Group by ticker/date
            by_ticker_date = defaultdict(list)
            for t in trades:
                key = (t["ticker"], t["date"])
                by_ticker_date[key].append(t)

            self._log(f"Grouped into {len(by_ticker_date)} ticker/date batches")

            # Step 3: Process each group
            batch_results = []
            groups_done = 0

            for (ticker, date), group_trades in by_ticker_date.items():
                # Load M1 bars once per ticker/date
                m1_bars = self._load_m1_bars(conn, ticker, date)

                for trade in group_trades:
                    try:
                        # Load M5 trade bars for this specific trade
                        m5_bars = self._load_m5_trade_bars(conn, trade["trade_id"])

                        # Calculate lifecycle signals
                        result = calculate_lifecycle(trade, m1_bars, m5_bars)
                        batch_results.append(result)
                        self.stats["trades_processed"] += 1

                    except Exception as e:
                        self.stats["errors"].append(
                            f"Error processing {trade['trade_id']}: {e}"
                        )
                        self._log(
                            f"Error processing {trade['trade_id']}: {e}", "error"
                        )

                # Batch insert periodically
                if len(batch_results) >= BATCH_INSERT_SIZE:
                    self._batch_insert(conn, batch_results, dry_run)
                    batch_results = []

                groups_done += 1
                self.stats["groups_processed"] = groups_done

                if groups_done % 25 == 0:
                    self._log(
                        f"Progress: {groups_done}/{len(by_ticker_date)} groups, "
                        f"{self.stats['trades_processed']} trades processed"
                    )

            # Insert remaining
            if batch_results:
                self._batch_insert(conn, batch_results, dry_run)

        except Exception as e:
            self.stats["errors"].append(f"Fatal error: {e}")
            self._log(f"Fatal error: {e}", "error")
            import traceback
            traceback.print_exc()

        finally:
            conn.close()

        self.stats["execution_time_seconds"] = (
            datetime.now() - start_time
        ).total_seconds()

        return self.stats
