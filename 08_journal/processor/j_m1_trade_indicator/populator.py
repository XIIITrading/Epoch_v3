"""
================================================================================
EPOCH TRADING SYSTEM - JOURNAL PROCESSOR 6
j_m1_trade_indicator - Populator
XIII Trading LLC
================================================================================

Captures the M1 indicator snapshot at entry for each journal trade.
Reads the last completed M1 bar BEFORE the entry candle from j_m1_indicator_bars,
then denormalizes trade context and outcome (from j_m5_atr_stop) into a single row.

Pipeline: journal_trades + j_m5_atr_stop + j_m1_indicator_bars -> j_m1_trade_indicator

Version: 1.0.0
================================================================================
"""

import sys
from pathlib import Path

# Add parent directory to path for db_config import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, date, time, timedelta
from typing import Dict, List, Any, Optional
from decimal import Decimal
import logging

from db_config import (
    DB_CONFIG, SOURCE_TABLE, J_M1_INDICATOR_BARS_TABLE,
    J_M1_TRADE_INDICATOR_TABLE, J_M5_ATR_STOP_TABLE,
    BATCH_INSERT_SIZE, VERBOSE,
    JOURNAL_SYMBOL_COL, JOURNAL_DATE_COL,
    SCHEMA_DIR
)


# =============================================================================
# INDICATOR COLUMNS (shared across procs 6, 7, 8)
# =============================================================================

INDICATOR_COLUMNS = [
    'candle_range_pct', 'vol_delta_raw', 'vol_delta_roll', 'vol_roc',
    'sma9', 'sma21', 'sma_config', 'sma_spread_pct', 'sma_momentum_label',
    'price_position', 'cvd_slope',
    'm5_structure', 'm15_structure', 'h1_structure',
    'health_score', 'long_score', 'short_score'
]


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def _to_time(val):
    """Convert psycopg2 timedelta or other types to a time object."""
    if val is None:
        return None
    if isinstance(val, time):
        return val
    if isinstance(val, timedelta):
        total = int(val.total_seconds())
        return time(total // 3600, (total % 3600) // 60, total % 60)
    return val


def _safe_float(value, default=None):
    """Safely convert value to float, handling Decimal and None."""
    if value is None:
        return default
    try:
        if isinstance(value, Decimal):
            return float(value)
        return float(value)
    except (ValueError, TypeError):
        return default


def _safe_int(value, default=None):
    """Safely convert value to int."""
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


# =============================================================================
# POPULATOR CLASS
# =============================================================================

class JM1TradeIndicatorPopulator:
    """
    Populates j_m1_trade_indicator with entry-bar indicator snapshots.

    For each journal trade that has a j_m5_atr_stop outcome:
    1. Finds the M1 indicator bar that closed just BEFORE the entry candle
    2. Combines trade context (ticker, direction, model) + outcome (is_winner, pnl_r)
       + indicator values into a single denormalized row
    3. Inserts into j_m1_trade_indicator
    """

    def __init__(self, verbose: bool = None):
        self.verbose = verbose if verbose is not None else VERBOSE
        self.logger = logging.getLogger(__name__)
        self.stats = {
            'trades_processed': 0,
            'trades_skipped': 0,
            'records_created': 0,
            'errors': []
        }

    def _log(self, message: str, level: str = 'info'):
        """Log message if verbose mode is enabled."""
        if self.verbose or level in ('error', 'warning'):
            prefix = {'error': '  ERROR:', 'warning': '  WARNING:', 'info': ' '}
            print(f"{prefix.get(level, ' ')} {message}")

    # =========================================================================
    # DATABASE OPERATIONS
    # =========================================================================

    def get_eligible_trades(self, conn, limit: int = None) -> List[Dict[str, Any]]:
        """
        Get trades from journal_trades that have j_m5_atr_stop outcomes
        but are NOT yet in j_m1_trade_indicator.
        """
        query = f"""
            SELECT t.trade_id, t.{JOURNAL_DATE_COL} AS trade_date,
                   t.{JOURNAL_SYMBOL_COL} AS ticker, t.direction, t.model,
                   t.entry_time, t.entry_price,
                   a.result AS atr_result, a.max_r,
                   CASE WHEN a.result = 'WIN' THEN TRUE ELSE FALSE END AS is_winner,
                   CASE WHEN a.result = 'WIN' THEN a.max_r ELSE -1 END AS pnl_r_approx
            FROM {SOURCE_TABLE} t
            INNER JOIN {J_M5_ATR_STOP_TABLE} a ON t.trade_id = a.trade_id
            WHERE NOT EXISTS (
                SELECT 1 FROM {J_M1_TRADE_INDICATOR_TABLE} ti
                WHERE ti.trade_id = t.trade_id
            )
              AND t.entry_time IS NOT NULL
            ORDER BY t.{JOURNAL_DATE_COL}, t.entry_time
        """

        if limit:
            query += f" LIMIT {limit}"

        with conn.cursor() as cur:
            cur.execute(query)
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()

        return [dict(zip(columns, row)) for row in rows]

    def get_indicator_bar_before_entry(
        self, conn, ticker: str, trade_date, entry_time: time
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch the M1 indicator bar that closed just BEFORE the entry candle.

        entry_time is truncated to M1 candle, then we fetch the bar with
        bar_time < that truncated time, ordered descending, limit 1.
        """
        # Truncate entry_time to M1 candle boundary
        entry_m1 = entry_time.replace(second=0, microsecond=0)

        query = f"""
            SELECT *
            FROM {J_M1_INDICATOR_BARS_TABLE}
            WHERE ticker = %s AND bar_date = %s AND bar_time < %s
            ORDER BY bar_time DESC
            LIMIT 1
        """

        with conn.cursor() as cur:
            cur.execute(query, (ticker, trade_date, entry_m1))
            columns = [desc[0] for desc in cur.description]
            row = cur.fetchone()

        if row is None:
            return None

        return dict(zip(columns, row))

    def build_row(
        self, trade: Dict[str, Any], indicator_bar: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build a single j_m1_trade_indicator row from trade context + indicator bar.
        """
        entry_time = _to_time(trade['entry_time'])

        row = {
            # Trade reference
            'trade_id': trade['trade_id'],

            # Trade context
            'ticker': trade['ticker'],
            'trade_date': trade['trade_date'],
            'direction': trade['direction'],
            'model': trade.get('model'),
            'entry_time': entry_time,
            'entry_price': _safe_float(trade['entry_price']),

            # Trade outcome (from j_m5_atr_stop via the join)
            'is_winner': trade['is_winner'],
            'pnl_r': _safe_float(trade['pnl_r_approx']),
            'max_r_achieved': _safe_int(trade['max_r']),

            # Bar identification
            'bar_date': indicator_bar.get('bar_date'),
            'bar_time': _to_time(indicator_bar.get('bar_time')),

            # OHLCV
            'open': _safe_float(indicator_bar.get('open')),
            'high': _safe_float(indicator_bar.get('high')),
            'low': _safe_float(indicator_bar.get('low')),
            'close': _safe_float(indicator_bar.get('close')),
            'volume': _safe_int(indicator_bar.get('volume')),
        }

        # Add all indicator columns
        for col in INDICATOR_COLUMNS:
            val = indicator_bar.get(col)
            if col in ('sma_config', 'sma_momentum_label', 'price_position',
                       'm5_structure', 'm15_structure', 'h1_structure'):
                row[col] = val  # string columns
            elif col in ('health_score', 'long_score', 'short_score'):
                row[col] = _safe_int(val)
            else:
                row[col] = _safe_float(val)

        return row

    def insert_results(self, conn, rows: List[Dict[str, Any]]) -> int:
        """Insert results into j_m1_trade_indicator with ON CONFLICT DO NOTHING."""
        if not rows:
            return 0

        query = f"""
            INSERT INTO {J_M1_TRADE_INDICATOR_TABLE} (
                trade_id, ticker, trade_date, direction, model,
                entry_time, entry_price,
                is_winner, pnl_r, max_r_achieved,
                bar_date, bar_time,
                open, high, low, close, volume,
                candle_range_pct, vol_delta_raw, vol_delta_roll, vol_roc,
                sma9, sma21, sma_config, sma_spread_pct, sma_momentum_label,
                price_position, cvd_slope,
                m5_structure, m15_structure, h1_structure,
                health_score, long_score, short_score
            ) VALUES %s
            ON CONFLICT (trade_id) DO NOTHING
        """

        values = [
            (
                r['trade_id'], r['ticker'], r['trade_date'], r['direction'], r['model'],
                r['entry_time'], r['entry_price'],
                r['is_winner'], r['pnl_r'], r['max_r_achieved'],
                r['bar_date'], r['bar_time'],
                r['open'], r['high'], r['low'], r['close'], r['volume'],
                r['candle_range_pct'], r['vol_delta_raw'], r['vol_delta_roll'], r['vol_roc'],
                r['sma9'], r['sma21'], r['sma_config'], r['sma_spread_pct'],
                r['sma_momentum_label'],
                r['price_position'], r['cvd_slope'],
                r['m5_structure'], r['m15_structure'], r['h1_structure'],
                r['health_score'], r['long_score'], r['short_score'],
            )
            for r in rows
        ]

        with conn.cursor() as cur:
            execute_values(cur, query, values, page_size=BATCH_INSERT_SIZE)

        return len(values)

    # =========================================================================
    # STATUS
    # =========================================================================

    def get_status(self, conn) -> Dict[str, Any]:
        """Get current processing status."""
        status = {}

        with conn.cursor() as cur:
            # Total trades with atr_stop outcome
            cur.execute(f"""
                SELECT COUNT(*)
                FROM {SOURCE_TABLE} t
                INNER JOIN {J_M5_ATR_STOP_TABLE} a ON t.trade_id = a.trade_id
                WHERE t.entry_time IS NOT NULL
            """)
            status['total_eligible'] = cur.fetchone()[0]

            # Already processed
            cur.execute(f"SELECT COUNT(*) FROM {J_M1_TRADE_INDICATOR_TABLE}")
            status['total_processed'] = cur.fetchone()[0]

            # Remaining
            cur.execute(f"""
                SELECT COUNT(*)
                FROM {SOURCE_TABLE} t
                INNER JOIN {J_M5_ATR_STOP_TABLE} a ON t.trade_id = a.trade_id
                WHERE t.entry_time IS NOT NULL
                  AND NOT EXISTS (
                      SELECT 1 FROM {J_M1_TRADE_INDICATOR_TABLE} ti
                      WHERE ti.trade_id = t.trade_id
                  )
            """)
            status['remaining'] = cur.fetchone()[0]

            # Win/loss breakdown
            cur.execute(f"""
                SELECT is_winner, COUNT(*)
                FROM {J_M1_TRADE_INDICATOR_TABLE}
                GROUP BY is_winner
            """)
            outcomes = dict(cur.fetchall())
            status['winners'] = outcomes.get(True, 0)
            status['losers'] = outcomes.get(False, 0)

        return status

    # =========================================================================
    # BATCH PROCESSING
    # =========================================================================

    def run_batch_population(
        self,
        limit: int = None,
        dry_run: bool = False,
        callback=None
    ) -> Dict[str, Any]:
        """
        Main entry point. Process all trades needing entry-bar indicator snapshot.

        Args:
            limit: Max trades to process
            dry_run: If True, calculate but don't write to DB
            callback: Optional callback for progress updates

        Returns:
            Dictionary with execution statistics
        """
        start_time = datetime.now()

        # Reset statistics
        self.stats = {
            'trades_processed': 0,
            'trades_skipped': 0,
            'records_created': 0,
            'errors': []
        }

        def _emit(msg):
            print(msg)
            if callback:
                callback(msg)

        _emit("=" * 60)
        _emit("Journal M1 Trade Indicator Populator v1.0")
        _emit("=" * 60)
        _emit(f"Source: {SOURCE_TABLE} + {J_M5_ATR_STOP_TABLE} + {J_M1_INDICATOR_BARS_TABLE}")
        _emit(f"Target: {J_M1_TRADE_INDICATOR_TABLE}")
        _emit(f"Dry Run: {dry_run}")
        if limit:
            _emit(f"Limit: {limit} trades")
        _emit("")

        conn = None
        try:
            _emit("[1/4] Connecting to Supabase...")
            conn = psycopg2.connect(**DB_CONFIG)
            _emit("  Connected successfully")

            _emit("\n[2/4] Querying eligible trades...")
            trades = self.get_eligible_trades(conn, limit)
            _emit(f"  Found {len(trades)} trades to process")

            if not trades:
                _emit("\n  No trades need processing. Exiting.")
                return self._build_result(start_time)

            _emit("\n[3/4] Processing trades...")
            all_rows = []
            total = len(trades)

            for idx, trade in enumerate(trades, 1):
                trade_id = trade['trade_id']
                ticker = trade['ticker']
                trade_date = trade['trade_date']

                try:
                    # Convert entry_time from potential timedelta
                    entry_time = _to_time(trade['entry_time'])
                    if entry_time is None:
                        self._log(f"Skipping {trade_id}: could not parse entry_time", 'warning')
                        self.stats['trades_skipped'] += 1
                        continue

                    # Get indicator bar before entry
                    indicator_bar = self.get_indicator_bar_before_entry(
                        conn, ticker, trade_date, entry_time
                    )

                    if indicator_bar is None:
                        self._log(
                            f"Skipping {trade_id}: no indicator bar before entry "
                            f"({ticker} {trade_date} {entry_time})", 'warning'
                        )
                        self.stats['trades_skipped'] += 1
                        continue

                    # Build row
                    row = self.build_row(trade, indicator_bar)
                    all_rows.append(row)
                    self.stats['trades_processed'] += 1

                    bar_time = _to_time(indicator_bar.get('bar_time'))
                    winner_str = "WIN" if trade['is_winner'] else "LOSS"
                    _emit(
                        f"  [{idx}/{total}] {trade_id:<35s} "
                        f"{ticker:<6s} {trade['direction']:<6s} "
                        f"{winner_str:<5s} bar={bar_time}"
                    )

                except Exception as e:
                    self.stats['errors'].append(f"{trade_id}: {str(e)}")
                    self._log(f"Error processing {trade_id}: {e}", 'error')

            # Insert results
            _emit(f"\n[4/4] Writing results to database...")
            if dry_run:
                _emit(f"  [DRY-RUN] Would insert {len(all_rows)} records")
            else:
                if all_rows:
                    inserted = self.insert_results(conn, all_rows)
                    conn.commit()
                    self.stats['records_created'] = inserted
                    _emit(f"  Inserted {inserted} records")
                else:
                    _emit("  No records to insert")

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
        return {
            'trades_processed': self.stats['trades_processed'],
            'trades_skipped': self.stats['trades_skipped'],
            'records_created': self.stats['records_created'],
            'errors': self.stats['errors'],
            'execution_time_seconds': round(elapsed, 2)
        }


# =============================================================================
# STANDALONE TEST
# =============================================================================
if __name__ == "__main__":
    print("J_M1 Trade Indicator Populator - Test Mode")
    print("=" * 60)

    populator = JM1TradeIndicatorPopulator(verbose=True)
    results = populator.run_batch_population(limit=5, dry_run=True)

    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    for key, value in results.items():
        print(f"  {key}: {value}")
