"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
Stop Analysis Calculator
XIII Trading LLC
================================================================================

Calculates 6 different stop types for all trades and simulates outcomes.
This processor:
1. Queries trades that need stop analysis
2. Fetches M1 and M5 bar data
3. Calculates stop prices for all 6 stop types
4. Simulates outcomes by walking through bars
5. Writes results to Supabase stop_analysis table

STOP TYPES:
    1. zone_buffer  - Zone Boundary + 5% Buffer (Default)
    2. prior_m1     - Prior M1 Bar High/Low (Tightest)
    3. prior_m5     - Prior M5 Bar High/Low
    4. m5_atr       - M5 ATR (1.1x), Close-based
    5. m15_atr      - M15 ATR (1.1x), Close-based
    6. fractal      - M5 Fractal High/Low (Market Structure)

Version: 1.0.0
================================================================================
"""

import psycopg2
from psycopg2.extras import execute_values
import pandas as pd
import numpy as np
from datetime import datetime, date, time, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging

from config import (
    DB_CONFIG, EOD_CUTOFF, STOP_TYPES, STOP_TYPE_DISPLAY_NAMES,
    SOURCE_TABLES, TARGET_TABLE
)
from stop_calculator import (
    calculate_all_stop_prices,
    simulate_outcome,
    _safe_float
)


def _convert_numpy(value):
    """Convert numpy types to Python native types for database insertion."""
    if value is None:
        return None
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value) if not np.isnan(value) else None
    if isinstance(value, np.ndarray):
        return value.tolist()
    return value


# =============================================================================
# DATA STRUCTURES
# =============================================================================
@dataclass
class StopAnalysisResult:
    """Result of stop analysis calculation for a single trade+stop_type."""
    trade_id: str
    stop_type: str
    date: date
    ticker: str
    direction: str
    model: str
    entry_time: time
    entry_price: float
    zone_low: float
    zone_high: float
    stop_price: Optional[float]
    stop_distance: Optional[float]
    stop_distance_pct: Optional[float]
    stop_hit: Optional[bool]
    stop_hit_time: Optional[time]
    mfe_price: Optional[float]
    mfe_time: Optional[time]
    mfe_distance: Optional[float]
    r_achieved: Optional[float]
    outcome: Optional[str]
    trigger_type: str


# =============================================================================
# CALCULATOR CLASS
# =============================================================================
class StopAnalysisCalculator:
    """
    Calculates stop prices and simulates outcomes for 6 stop types.

    This class:
    1. Queries trades from Supabase that need calculation
    2. Fetches M1 bars and M5 trade bars
    3. Calculates all 6 stop prices for each trade
    4. Simulates outcomes using bar data
    5. Writes results back to Supabase
    """

    def __init__(self, verbose: bool = True):
        """
        Initialize the calculator.

        Args:
            verbose: Enable verbose logging
        """
        self.verbose = verbose
        self.logger = logging.getLogger(__name__)

        # Statistics
        self.stats = {
            'trades_processed': 0,
            'trades_skipped': 0,
            'records_created': 0,
            'errors': []
        }

    def _log(self, message: str, level: str = 'info'):
        """Log message if verbose mode is enabled."""
        if self.verbose:
            if level == 'info':
                print(f"  {message}")
            elif level == 'warning':
                print(f"  WARNING: {message}")
            elif level == 'error':
                print(f"  ERROR: {message}")

    # =========================================================================
    # DATABASE OPERATIONS
    # =========================================================================
    def get_trades_needing_calculation(self, conn, limit: int = None) -> pd.DataFrame:
        """
        Query trades table for records not yet fully processed in stop_analysis.

        A trade is considered fully processed when it has 6 rows in stop_analysis
        (one for each stop type).
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
                t.zone_low,
                t.zone_high,
                m.mfe_potential_price,
                m.mfe_potential_time,
                m.mae_potential_price,
                m.mae_potential_time
            FROM {SOURCE_TABLES['trades']} t
            JOIN {SOURCE_TABLES['mfe_mae']} m ON t.trade_id = m.trade_id
            WHERE t.entry_time IS NOT NULL
              AND t.entry_price IS NOT NULL
              AND t.zone_low IS NOT NULL
              AND t.zone_high IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1 FROM {TARGET_TABLE} sa
                  WHERE sa.trade_id = t.trade_id
                  GROUP BY sa.trade_id
                  HAVING COUNT(DISTINCT sa.stop_type) = 6
              )
            ORDER BY t.date, t.ticker, t.entry_time
        """

        if limit:
            query += f" LIMIT {limit}"

        with conn.cursor() as cur:
            cur.execute(query)
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()

        df = pd.DataFrame(rows, columns=columns)
        return df

    def get_m1_bars(self, conn, ticker: str, trade_date: date, entry_time=None) -> List[Dict[str, Any]]:
        """
        Fetch M1 bars for a ticker/date from the m1_bars table.

        For early morning trades (e.g., 09:30), we also fetch the last few bars
        from the previous trading day to ensure we have a prior M1 bar for
        the prior_m1 stop calculation.

        Args:
            conn: Database connection
            ticker: Stock symbol
            trade_date: Trading date
            entry_time: Entry time (optional, used to determine if we need prior day bars)
        """
        # First fetch current day bars
        query = f"""
            SELECT bar_date, bar_time, high, low, open, close
            FROM {SOURCE_TABLES['m1_bars']}
            WHERE ticker = %s AND bar_date = %s
            ORDER BY bar_time
        """

        with conn.cursor() as cur:
            cur.execute(query, (ticker, trade_date))
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()

        current_day_bars = [dict(zip(columns, row)) for row in rows]

        # Check if we need prior day bars (for early morning entries)
        need_prior_day = False
        if entry_time is not None:
            # Handle entry_time as timedelta
            if isinstance(entry_time, timedelta):
                entry_minutes = int(entry_time.total_seconds()) // 60
            else:
                entry_minutes = entry_time.hour * 60 + entry_time.minute

            # Market open is 09:30 = 570 minutes
            # If entry is within first 5 minutes of market open, we may need prior day
            market_open_minutes = 9 * 60 + 30  # 09:30
            if entry_minutes <= market_open_minutes + 5:
                need_prior_day = True

        if need_prior_day:
            # Get the previous trading day
            prev_day_query = f"""
                SELECT DISTINCT bar_date
                FROM {SOURCE_TABLES['m1_bars']}
                WHERE ticker = %s AND bar_date < %s
                ORDER BY bar_date DESC
                LIMIT 1
            """

            with conn.cursor() as cur:
                cur.execute(prev_day_query, (ticker, trade_date))
                prev_day_result = cur.fetchone()

            if prev_day_result:
                prev_date = prev_day_result[0]

                # Fetch last 10 minutes from previous day (should be enough for prior_m1)
                prev_bars_query = f"""
                    SELECT bar_date, bar_time, high, low, open, close
                    FROM {SOURCE_TABLES['m1_bars']}
                    WHERE ticker = %s AND bar_date = %s AND bar_time >= '15:50:00'
                    ORDER BY bar_time
                """

                with conn.cursor() as cur:
                    cur.execute(prev_bars_query, (ticker, prev_date))
                    prev_columns = [desc[0] for desc in cur.description]
                    prev_rows = cur.fetchall()

                prev_day_bars = [dict(zip(prev_columns, row)) for row in prev_rows]

                # Prepend previous day bars to current day bars
                return prev_day_bars + current_day_bars

        return current_day_bars

    def get_m5_bars(self, conn, trade_id: str) -> List[Dict[str, Any]]:
        """Fetch M5 trade bars for a specific trade."""
        query = f"""
            SELECT bars_from_entry, bar_time, high, low, open, close
            FROM {SOURCE_TABLES['m5_bars']}
            WHERE trade_id = %s
            ORDER BY bars_from_entry
        """

        with conn.cursor() as cur:
            cur.execute(query, (trade_id,))
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()

        return [dict(zip(columns, row)) for row in rows]

    def get_m5_indicator_bars(self, conn, ticker: str, trade_date: date, entry_time) -> List[Dict[str, Any]]:
        """
        Fetch M5 indicator bars for a ticker/date, calculating bars_from_entry.
        This provides pre-entry bars needed for ATR and fractal calculations.

        For early morning trades (e.g., 09:30), we may need to fetch bars from
        the previous trading day to have enough data for ATR (14 bars) and
        M15 ATR (42 M5 bars = 14 M15 periods) calculations.

        Required bars before entry:
        - M5 ATR: 14 bars minimum
        - M15 ATR: 42 bars minimum (14 M15 periods × 3 M5 bars each)
        - Fractal: ~5 bars minimum

        We target 45 pre-entry bars to ensure we have enough for all calculations.
        """
        REQUIRED_PRE_ENTRY_BARS = 45  # Enough for M15 ATR (42) + buffer

        # Handle entry_time as timedelta
        if isinstance(entry_time, timedelta):
            total_seconds = int(entry_time.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            entry_time = time(hours, minutes, seconds)

        # First, query the current day's bars
        query = """
            SELECT bar_date, bar_time, high, low, open, close
            FROM m5_indicator_bars
            WHERE ticker = %s AND bar_date = %s
            ORDER BY bar_time
        """

        with conn.cursor() as cur:
            cur.execute(query, (ticker, trade_date))
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()

        if not rows:
            return []

        # Convert entry_time to comparable format
        entry_minutes = entry_time.hour * 60 + entry_time.minute

        # Count how many pre-entry bars we have on the current day
        pre_entry_count = 0
        for row in rows:
            bar_time_val = row[1]  # bar_time is second column
            if isinstance(bar_time_val, timedelta):
                bar_minutes = int(bar_time_val.total_seconds()) // 60
            else:
                bar_minutes = bar_time_val.hour * 60 + bar_time_val.minute

            if bar_minutes < entry_minutes:
                pre_entry_count += 1

        # If we don't have enough pre-entry bars, fetch from previous trading day
        prev_day_bars = []
        if pre_entry_count < REQUIRED_PRE_ENTRY_BARS:
            # Get the previous trading day (could be Friday if trade_date is Monday)
            # We query for any date before trade_date, ordered descending, limit to 1 distinct date
            prev_day_query = """
                SELECT DISTINCT bar_date
                FROM m5_indicator_bars
                WHERE ticker = %s AND bar_date < %s
                ORDER BY bar_date DESC
                LIMIT 1
            """

            with conn.cursor() as cur:
                cur.execute(prev_day_query, (ticker, trade_date))
                prev_day_result = cur.fetchone()

            if prev_day_result:
                prev_date = prev_day_result[0]

                # Fetch afternoon bars from previous day (12:00 onwards to avoid too much data)
                # This gives us ~4 hours × 12 bars/hour = ~48 bars
                prev_bars_query = """
                    SELECT bar_date, bar_time, high, low, open, close
                    FROM m5_indicator_bars
                    WHERE ticker = %s AND bar_date = %s AND bar_time >= '12:00:00'
                    ORDER BY bar_time
                """

                with conn.cursor() as cur:
                    cur.execute(prev_bars_query, (ticker, prev_date))
                    prev_columns = [desc[0] for desc in cur.description]
                    prev_rows = cur.fetchall()

                prev_day_bars = [dict(zip(prev_columns, row)) for row in prev_rows]

        # Build the combined list with bars_from_entry calculated
        bars = []

        # First add previous day bars (if any) with negative bars_from_entry
        # The last bar of the previous day will be -(pre_entry_count + 1)
        if prev_day_bars:
            prev_day_offset = pre_entry_count + len(prev_day_bars)
            for i, bar_dict in enumerate(prev_day_bars):
                bar_dict['bars_from_entry'] = -(prev_day_offset - i)
                bars.append(bar_dict)

        # Then add current day bars
        for row in rows:
            bar_dict = dict(zip(columns, row))
            bar_time_val = bar_dict['bar_time']

            # Handle bar_time as timedelta
            if isinstance(bar_time_val, timedelta):
                bar_minutes = int(bar_time_val.total_seconds()) // 60
            else:
                bar_minutes = bar_time_val.hour * 60 + bar_time_val.minute

            # Calculate bars_from_entry (5-minute increments)
            bars_from_entry = (bar_minutes - entry_minutes) // 5
            bar_dict['bars_from_entry'] = bars_from_entry
            bars.append(bar_dict)

        return bars

    def get_existing_stop_types(self, conn, trade_id: str) -> List[str]:
        """Get list of stop types already calculated for a trade."""
        query = f"""
            SELECT stop_type FROM {TARGET_TABLE}
            WHERE trade_id = %s
        """

        with conn.cursor() as cur:
            cur.execute(query, (trade_id,))
            rows = cur.fetchall()

        return [row[0] for row in rows]

    def insert_results(self, conn, results: List[StopAnalysisResult]) -> int:
        """Insert calculation results into stop_analysis table."""
        if not results:
            return 0

        query = f"""
            INSERT INTO {TARGET_TABLE} (
                trade_id, stop_type, date, ticker, direction, model,
                entry_time, entry_price, zone_low, zone_high,
                stop_price, stop_distance, stop_distance_pct,
                stop_hit, stop_hit_time,
                mfe_price, mfe_time, mfe_distance,
                r_achieved, outcome, trigger_type
            ) VALUES %s
            ON CONFLICT (trade_id, stop_type) DO UPDATE SET
                stop_price = EXCLUDED.stop_price,
                stop_distance = EXCLUDED.stop_distance,
                stop_distance_pct = EXCLUDED.stop_distance_pct,
                stop_hit = EXCLUDED.stop_hit,
                stop_hit_time = EXCLUDED.stop_hit_time,
                mfe_price = EXCLUDED.mfe_price,
                mfe_time = EXCLUDED.mfe_time,
                mfe_distance = EXCLUDED.mfe_distance,
                r_achieved = EXCLUDED.r_achieved,
                outcome = EXCLUDED.outcome,
                trigger_type = EXCLUDED.trigger_type,
                updated_at = NOW()
        """

        values = [
            (
                r.trade_id, r.stop_type, r.date, r.ticker, r.direction, r.model,
                r.entry_time, _convert_numpy(r.entry_price),
                _convert_numpy(r.zone_low), _convert_numpy(r.zone_high),
                _convert_numpy(r.stop_price), _convert_numpy(r.stop_distance),
                _convert_numpy(r.stop_distance_pct),
                r.stop_hit, r.stop_hit_time,
                _convert_numpy(r.mfe_price), r.mfe_time,
                _convert_numpy(r.mfe_distance),
                _convert_numpy(r.r_achieved), r.outcome, r.trigger_type
            )
            for r in results
        ]

        with conn.cursor() as cur:
            execute_values(cur, query, values)

        return len(results)

    # =========================================================================
    # CALCULATION LOGIC
    # =========================================================================
    def calculate_single_trade(
        self,
        trade: Dict[str, Any],
        m1_bars: List[Dict[str, Any]],
        m5_bars: List[Dict[str, Any]],
        existing_types: List[str]
    ) -> List[StopAnalysisResult]:
        """
        Calculate stop analysis for a single trade.

        Returns a list of StopAnalysisResult objects (one per stop type).
        """
        trade_id = trade['trade_id']
        results = []

        # Handle entry_time as timedelta (from psycopg2)
        entry_time = trade['entry_time']
        if isinstance(entry_time, timedelta):
            total_seconds = int(entry_time.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            entry_time = time(hours, minutes, seconds)

        # Build trade dict for calculator
        trade_dict = {
            'trade_id': trade_id,
            'date': trade['date'],  # Include date for prior-day bar handling
            'entry_price': float(trade['entry_price']),
            'direction': trade['direction'],
            'entry_time': entry_time,
            'zone_low': float(trade['zone_low']) if trade['zone_low'] else None,
            'zone_high': float(trade['zone_high']) if trade['zone_high'] else None,
            'model': trade['model'],
            'mfe_potential_price': float(trade['mfe_potential_price']) if trade['mfe_potential_price'] else None,
            'mfe_potential_time': trade['mfe_potential_time'],
        }

        # Calculate all stop prices
        stops = calculate_all_stop_prices(trade_dict, m1_bars, m5_bars)

        # Simulate outcome for each stop type
        for stop_type in STOP_TYPES:
            # Skip if already calculated
            if stop_type in existing_types:
                continue

            stop_price = stops.get(stop_type)

            if stop_price is None:
                # Create result with NULL stop data
                result = StopAnalysisResult(
                    trade_id=trade_id,
                    stop_type=stop_type,
                    date=trade['date'],
                    ticker=trade['ticker'],
                    direction=trade['direction'],
                    model=trade['model'],
                    entry_time=entry_time,
                    entry_price=float(trade['entry_price']),
                    zone_low=float(trade['zone_low']) if trade['zone_low'] else None,
                    zone_high=float(trade['zone_high']) if trade['zone_high'] else None,
                    stop_price=None,
                    stop_distance=None,
                    stop_distance_pct=None,
                    stop_hit=None,
                    stop_hit_time=None,
                    mfe_price=None,
                    mfe_time=None,
                    mfe_distance=None,
                    r_achieved=None,
                    outcome=None,
                    trigger_type='price_based' if stop_type not in ['m5_atr', 'm15_atr'] else 'close_based'
                )
            else:
                # Simulate outcome
                outcome_data = simulate_outcome(
                    trade=trade_dict,
                    stop_price=stop_price,
                    stop_type=stop_type,
                    m1_bars=m1_bars,
                    m5_bars=m5_bars
                )

                # Handle MFE time
                mfe_time = outcome_data.get('mfe_time')
                if isinstance(mfe_time, timedelta):
                    total_seconds = int(mfe_time.total_seconds())
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    seconds = total_seconds % 60
                    mfe_time = time(hours, minutes, seconds)

                # Handle stop_hit_time
                stop_hit_time = outcome_data.get('stop_hit_time')
                if isinstance(stop_hit_time, timedelta):
                    total_seconds = int(stop_hit_time.total_seconds())
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    seconds = total_seconds % 60
                    stop_hit_time = time(hours, minutes, seconds)

                result = StopAnalysisResult(
                    trade_id=trade_id,
                    stop_type=stop_type,
                    date=trade['date'],
                    ticker=trade['ticker'],
                    direction=trade['direction'],
                    model=trade['model'],
                    entry_time=entry_time,
                    entry_price=float(trade['entry_price']),
                    zone_low=float(trade['zone_low']) if trade['zone_low'] else None,
                    zone_high=float(trade['zone_high']) if trade['zone_high'] else None,
                    stop_price=round(stop_price, 4),
                    stop_distance=round(outcome_data['stop_distance'], 4),
                    stop_distance_pct=round(outcome_data['stop_distance_pct'], 4),
                    stop_hit=outcome_data['stop_hit'],
                    stop_hit_time=stop_hit_time,
                    mfe_price=round(outcome_data['mfe_price'], 4) if outcome_data['mfe_price'] else None,
                    mfe_time=mfe_time,
                    mfe_distance=round(outcome_data['mfe_distance'], 4) if outcome_data.get('mfe_distance') else None,
                    r_achieved=round(outcome_data['r_achieved'], 4),
                    outcome=outcome_data['outcome'],
                    trigger_type=outcome_data['trigger_type']
                )

            results.append(result)

        return results

    # =========================================================================
    # BATCH PROCESSING
    # =========================================================================
    def run_batch_calculation(
        self,
        limit: int = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Main entry point. Process all trades needing calculation.

        Args:
            limit: Max trades to process (for testing)
            dry_run: If True, calculate but don't write to DB

        Returns:
            Dictionary with execution statistics
        """
        start_time = datetime.now()

        print("=" * 60)
        print("Stop Analysis Calculator")
        print("=" * 60)
        print(f"Stop Types: {len(STOP_TYPES)}")
        print(f"Dry Run: {dry_run}")
        if limit:
            print(f"Limit: {limit} trades")
        print()

        # Reset statistics
        self.stats = {
            'trades_processed': 0,
            'trades_skipped': 0,
            'records_created': 0,
            'errors': []
        }

        conn = None
        try:
            # Connect to database
            print("[1/4] Connecting to Supabase...")
            conn = psycopg2.connect(**DB_CONFIG)
            print("  Connected successfully")

            # Get trades needing calculation
            print("\n[2/4] Querying trades needing calculation...")
            trades_df = self.get_trades_needing_calculation(conn, limit)
            print(f"  Found {len(trades_df)} trades to process")

            if trades_df.empty:
                print("\n  No trades need calculation. Exiting.")
                return self._build_result(start_time)

            # Process trades
            print("\n[3/4] Processing trades...")
            all_results = []

            # Cache M1 bars by ticker-date to minimize queries
            m1_cache = {}

            for idx, trade in trades_df.iterrows():
                trade_id = trade['trade_id']
                ticker = trade['ticker']
                trade_date = trade['date']

                # Get existing stop types for this trade
                existing_types = self.get_existing_stop_types(conn, trade_id)
                types_needed = len(STOP_TYPES) - len(existing_types)

                if types_needed == 0:
                    self.stats['trades_skipped'] += 1
                    continue

                # Get M1 bars (with caching)
                # For early morning trades, include prior day data, so cache by entry_time too
                entry_time = trade['entry_time']
                # Determine if this is an early morning trade
                if isinstance(entry_time, timedelta):
                    entry_minutes = int(entry_time.total_seconds()) // 60
                else:
                    entry_minutes = entry_time.hour * 60 + entry_time.minute
                market_open_minutes = 9 * 60 + 30  # 09:30

                # Use different cache key for early morning trades that need prior day bars
                if entry_minutes <= market_open_minutes + 5:
                    cache_key = f"{ticker}_{trade_date}_early"
                else:
                    cache_key = f"{ticker}_{trade_date}"

                if cache_key not in m1_cache:
                    m1_cache[cache_key] = self.get_m1_bars(conn, ticker, trade_date, entry_time)
                m1_bars = m1_cache[cache_key]

                # Get M5 indicator bars (includes pre-entry data for ATR/fractal)
                # Use the entry_time to calculate bars_from_entry
                m5_indicator_key = f"m5ind_{ticker}_{trade_date}_{trade['entry_time']}"
                if m5_indicator_key not in m1_cache:
                    m1_cache[m5_indicator_key] = self.get_m5_indicator_bars(
                        conn, ticker, trade_date, trade['entry_time']
                    )
                m5_bars = m1_cache[m5_indicator_key]

                if not m5_bars:
                    self._log(f"Skipping {trade_id}: no M5 indicator bars", 'warning')
                    self.stats['trades_skipped'] += 1
                    continue

                # Calculate for this trade
                try:
                    results = self.calculate_single_trade(
                        trade.to_dict(),
                        m1_bars,
                        m5_bars,
                        existing_types
                    )
                    all_results.extend(results)
                    self.stats['trades_processed'] += 1

                    if self.verbose and (idx + 1) % 50 == 0:
                        self._log(f"Processed {idx + 1}/{len(trades_df)} trades...")

                except Exception as e:
                    self.stats['errors'].append(f"{trade_id}: {str(e)}")
                    self._log(f"Error processing {trade_id}: {e}", 'error')

            # Write results to database
            print(f"\n[4/4] Writing results to database...")
            if dry_run:
                print(f"  [DRY-RUN] Would insert {len(all_results)} records")
            else:
                inserted = self.insert_results(conn, all_results)
                conn.commit()
                self.stats['records_created'] = inserted
                print(f"  Inserted {inserted} records")

            return self._build_result(start_time)

        except Exception as e:
            self.stats['errors'].append(str(e))
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
    print("Stop Analysis Calculator - Test Mode")
    print("=" * 60)

    # Run with limit for testing
    calculator = StopAnalysisCalculator(verbose=True)
    results = calculator.run_batch_calculation(limit=5, dry_run=True)

    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    for key, value in results.items():
        print(f"  {key}: {value}")
