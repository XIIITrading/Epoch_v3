"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
R Win/Loss Calculator
XIII Trading LLC
================================================================================

Evaluates trades using M5 ATR-based stop (14-period, 1.1x multiplier) and
R-multiple targets (1R through 5R) to determine win/loss outcomes.

LOGIC:
    1. Calculate M5 ATR(14) at entry using pre-entry M5 bars
    2. Set stop = entry -/+ (ATR * 1.1) => this distance = 1R
    3. Set R-level targets at entry +/- (N * 1R) for N = 1..5
    4. Walk M1 bars from entry to 15:30 ET:
       - R targets: hit when price high/low touches target (price-based)
       - Stop: hit when M1 bar CLOSES beyond stop level (close-based)
       - Same-candle conflict: if R-level hit AND close beyond stop => LOSS
    5. If no R1 and no stop by 15:30:
       - price > entry => WIN (EOD_WIN)
       - price <= entry => LOSS (EOD_LOSS)
    6. If R1+ hit before stop => WIN (R_TARGET)
    7. If stop before R1 => LOSS (STOP)

DATA SOURCES:
    - trades table (trade metadata)
    - m1_bars table (M1 candle data for bar-by-bar simulation)
    - m5_trade_bars table (M5 bars for ATR calculation)
    - m5_indicator_bars table (M5 bars for ATR calculation, pre-entry)

Version: 1.0.0
================================================================================
"""

import psycopg2
from psycopg2.extras import execute_values
import pandas as pd
import numpy as np
from datetime import datetime, date, time, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from decimal import Decimal
import logging

from config import (
    DB_CONFIG, EOD_CUTOFF, ATR_PERIOD, ATR_MULTIPLIER,
    R_LEVELS, SOURCE_TABLES, TARGET_TABLE
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


def _safe_float(value, default: float = 0.0) -> float:
    """Safely convert value to float, handling Decimal types."""
    if value is None:
        return default
    try:
        if isinstance(value, Decimal):
            return float(value)
        return float(value)
    except (ValueError, TypeError):
        return default


def _time_to_minutes(time_val) -> Optional[float]:
    """Convert a time value to minutes from midnight."""
    if time_val is None:
        return None
    try:
        if isinstance(time_val, timedelta):
            return time_val.total_seconds() / 60
        if isinstance(time_val, time):
            return time_val.hour * 60 + time_val.minute + time_val.second / 60
        if isinstance(time_val, datetime):
            return time_val.hour * 60 + time_val.minute + time_val.second / 60
        if hasattr(time_val, 'hour') and hasattr(time_val, 'minute'):
            sec = time_val.second if hasattr(time_val, 'second') else 0
            return time_val.hour * 60 + time_val.minute + sec / 60
        if isinstance(time_val, str):
            parts = time_val.split(':')
            if len(parts) >= 2:
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = int(parts[2]) if len(parts) > 2 else 0
                return hours * 60 + minutes + seconds / 60
        return None
    except Exception:
        return None


def _timedelta_to_time(td) -> Optional[time]:
    """Convert timedelta (from psycopg2) to time object."""
    if td is None:
        return None
    if isinstance(td, time):
        return td
    if isinstance(td, timedelta):
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return time(hours, minutes, seconds)
    return None


# =============================================================================
# ATR CALCULATION (matches stop_analysis/stop_calculator.py)
# =============================================================================

def calculate_true_range(high: float, low: float, prev_close: Optional[float] = None) -> float:
    """Calculate True Range for a single bar."""
    high = _safe_float(high)
    low = _safe_float(low)
    range_hl = high - low

    if prev_close is None:
        return range_hl

    prev_close = _safe_float(prev_close)
    return max(range_hl, abs(high - prev_close), abs(low - prev_close))


def calculate_atr_m5(m5_bars: List[Dict[str, Any]], period: int = ATR_PERIOD) -> Optional[float]:
    """Calculate 14-period ATR on M5 bars at or before entry."""
    if not m5_bars:
        return None

    pre_entry_bars = [b for b in m5_bars if b.get('bars_from_entry', 0) <= 0]
    pre_entry_bars.sort(key=lambda x: x.get('bars_from_entry', 0))

    if len(pre_entry_bars) < 2:
        return None

    actual_period = min(period, len(pre_entry_bars))
    recent_bars = pre_entry_bars[-actual_period:]

    true_ranges = []
    for i, bar in enumerate(recent_bars):
        high = _safe_float(bar.get('high'))
        low = _safe_float(bar.get('low'))

        if i == 0:
            tr = high - low
        else:
            prev_close = _safe_float(recent_bars[i - 1].get('close'))
            tr = calculate_true_range(high, low, prev_close)

        true_ranges.append(tr)

    if not true_ranges:
        return None

    return sum(true_ranges) / len(true_ranges)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class RWinLossResult:
    """Result of R Win/Loss calculation for a single trade."""
    trade_id: str
    date: date
    ticker: str
    direction: str
    model: str
    entry_time: time
    entry_price: float
    m5_atr_value: Optional[float]
    stop_price: Optional[float]
    stop_distance: Optional[float]
    stop_distance_pct: Optional[float]
    r1_price: Optional[float]
    r2_price: Optional[float]
    r3_price: Optional[float]
    r4_price: Optional[float]
    r5_price: Optional[float]
    r1_hit: bool = False
    r1_time: Optional[time] = None
    r1_bars_from_entry: Optional[int] = None
    r2_hit: bool = False
    r2_time: Optional[time] = None
    r2_bars_from_entry: Optional[int] = None
    r3_hit: bool = False
    r3_time: Optional[time] = None
    r3_bars_from_entry: Optional[int] = None
    r4_hit: bool = False
    r4_time: Optional[time] = None
    r4_bars_from_entry: Optional[int] = None
    r5_hit: bool = False
    r5_time: Optional[time] = None
    r5_bars_from_entry: Optional[int] = None
    stop_hit: bool = False
    stop_hit_time: Optional[time] = None
    stop_hit_bars_from_entry: Optional[int] = None
    max_r_achieved: int = 0
    outcome: str = 'LOSS'
    exit_reason: str = 'EOD_LOSS'
    eod_price: Optional[float] = None


# =============================================================================
# CALCULATOR CLASS
# =============================================================================

class RWinLossCalculator:
    """
    Calculates R Win/Loss outcomes using M5 ATR stop and R-multiple targets.

    This class:
    1. Queries trades from Supabase that need calculation
    2. Fetches M5 bars (for ATR calculation) and M1 bars (for simulation)
    3. Calculates M5 ATR stop price and R-level target prices
    4. Walks M1 bars to detect R-level hits and stop triggers
    5. Writes results back to Supabase r_win_loss table
    """

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.logger = logging.getLogger(__name__)
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
        Query trades that haven't been processed in r_win_loss yet.
        Requires entry_time and entry_price to be populated.
        """
        query = f"""
            SELECT
                t.trade_id,
                t.date,
                t.ticker,
                t.direction,
                t.model,
                t.entry_time,
                t.entry_price
            FROM {SOURCE_TABLES['trades']} t
            WHERE t.entry_time IS NOT NULL
              AND t.entry_price IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1 FROM {TARGET_TABLE} r
                  WHERE r.trade_id = t.trade_id
              )
            ORDER BY t.date, t.ticker, t.entry_time
        """

        if limit:
            query += f" LIMIT {limit}"

        with conn.cursor() as cur:
            cur.execute(query)
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()

        return pd.DataFrame(rows, columns=columns)

    def get_m1_bars(self, conn, ticker: str, trade_date: date) -> List[Dict[str, Any]]:
        """Fetch M1 bars for a ticker/date from the m1_bars table."""
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

        return [dict(zip(columns, row)) for row in rows]

    def get_m5_indicator_bars(self, conn, ticker: str, trade_date: date, entry_time) -> List[Dict[str, Any]]:
        """
        Fetch M5 indicator bars for ATR calculation. Includes pre-entry bars
        from prior trading day if needed for early morning entries.

        Required: 14+ pre-entry M5 bars for ATR(14).
        """
        REQUIRED_PRE_ENTRY_BARS = 16  # 14 for ATR + buffer

        # Handle entry_time as timedelta
        if isinstance(entry_time, timedelta):
            total_seconds = int(entry_time.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            entry_time_obj = time(hours, minutes, seconds)
        else:
            entry_time_obj = entry_time

        # Fetch current day bars
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

        # Count pre-entry bars on current day
        entry_minutes = entry_time_obj.hour * 60 + entry_time_obj.minute
        pre_entry_count = 0
        for row in rows:
            bar_time_val = row[1]
            if isinstance(bar_time_val, timedelta):
                bar_minutes = int(bar_time_val.total_seconds()) // 60
            else:
                bar_minutes = bar_time_val.hour * 60 + bar_time_val.minute
            if bar_minutes < entry_minutes:
                pre_entry_count += 1

        # Fetch prior day bars if needed
        prev_day_bars = []
        if pre_entry_count < REQUIRED_PRE_ENTRY_BARS:
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

        # Build combined list with bars_from_entry
        bars = []

        if prev_day_bars:
            prev_day_offset = pre_entry_count + len(prev_day_bars)
            for i, bar_dict in enumerate(prev_day_bars):
                bar_dict['bars_from_entry'] = -(prev_day_offset - i)
                bars.append(bar_dict)

        for row in rows:
            bar_dict = dict(zip(columns, row))
            bar_time_val = bar_dict['bar_time']
            if isinstance(bar_time_val, timedelta):
                bar_minutes = int(bar_time_val.total_seconds()) // 60
            else:
                bar_minutes = bar_time_val.hour * 60 + bar_time_val.minute
            bars_from_entry = (bar_minutes - entry_minutes) // 5
            bar_dict['bars_from_entry'] = bars_from_entry
            bars.append(bar_dict)

        return bars

    def insert_results(self, conn, results: List[RWinLossResult]) -> int:
        """Insert calculation results into r_win_loss table."""
        if not results:
            return 0

        query = f"""
            INSERT INTO {TARGET_TABLE} (
                trade_id, date, ticker, direction, model,
                entry_time, entry_price,
                m5_atr_value, stop_price, stop_distance, stop_distance_pct,
                r1_price, r2_price, r3_price, r4_price, r5_price,
                r1_hit, r1_time, r1_bars_from_entry,
                r2_hit, r2_time, r2_bars_from_entry,
                r3_hit, r3_time, r3_bars_from_entry,
                r4_hit, r4_time, r4_bars_from_entry,
                r5_hit, r5_time, r5_bars_from_entry,
                stop_hit, stop_hit_time, stop_hit_bars_from_entry,
                max_r_achieved, outcome, exit_reason, eod_price
            ) VALUES %s
            ON CONFLICT (trade_id) DO UPDATE SET
                m5_atr_value = EXCLUDED.m5_atr_value,
                stop_price = EXCLUDED.stop_price,
                stop_distance = EXCLUDED.stop_distance,
                stop_distance_pct = EXCLUDED.stop_distance_pct,
                r1_price = EXCLUDED.r1_price,
                r2_price = EXCLUDED.r2_price,
                r3_price = EXCLUDED.r3_price,
                r4_price = EXCLUDED.r4_price,
                r5_price = EXCLUDED.r5_price,
                r1_hit = EXCLUDED.r1_hit,
                r1_time = EXCLUDED.r1_time,
                r1_bars_from_entry = EXCLUDED.r1_bars_from_entry,
                r2_hit = EXCLUDED.r2_hit,
                r2_time = EXCLUDED.r2_time,
                r2_bars_from_entry = EXCLUDED.r2_bars_from_entry,
                r3_hit = EXCLUDED.r3_hit,
                r3_time = EXCLUDED.r3_time,
                r3_bars_from_entry = EXCLUDED.r3_bars_from_entry,
                r4_hit = EXCLUDED.r4_hit,
                r4_time = EXCLUDED.r4_time,
                r4_bars_from_entry = EXCLUDED.r4_bars_from_entry,
                r5_hit = EXCLUDED.r5_hit,
                r5_time = EXCLUDED.r5_time,
                r5_bars_from_entry = EXCLUDED.r5_bars_from_entry,
                stop_hit = EXCLUDED.stop_hit,
                stop_hit_time = EXCLUDED.stop_hit_time,
                stop_hit_bars_from_entry = EXCLUDED.stop_hit_bars_from_entry,
                max_r_achieved = EXCLUDED.max_r_achieved,
                outcome = EXCLUDED.outcome,
                exit_reason = EXCLUDED.exit_reason,
                eod_price = EXCLUDED.eod_price,
                updated_at = NOW()
        """

        values = [
            (
                r.trade_id, r.date, r.ticker, r.direction, r.model,
                r.entry_time, _convert_numpy(r.entry_price),
                _convert_numpy(r.m5_atr_value),
                _convert_numpy(r.stop_price),
                _convert_numpy(r.stop_distance),
                _convert_numpy(r.stop_distance_pct),
                _convert_numpy(r.r1_price),
                _convert_numpy(r.r2_price),
                _convert_numpy(r.r3_price),
                _convert_numpy(r.r4_price),
                _convert_numpy(r.r5_price),
                r.r1_hit, r.r1_time, r.r1_bars_from_entry,
                r.r2_hit, r.r2_time, r.r2_bars_from_entry,
                r.r3_hit, r.r3_time, r.r3_bars_from_entry,
                r.r4_hit, r.r4_time, r.r4_bars_from_entry,
                r.r5_hit, r.r5_time, r.r5_bars_from_entry,
                r.stop_hit, r.stop_hit_time, r.stop_hit_bars_from_entry,
                r.max_r_achieved, r.outcome, r.exit_reason,
                _convert_numpy(r.eod_price),
            )
            for r in results
        ]

        with conn.cursor() as cur:
            execute_values(cur, query, values)

        return len(results)

    # =========================================================================
    # CORE CALCULATION LOGIC
    # =========================================================================

    def calculate_single_trade(
        self,
        trade: Dict[str, Any],
        m1_bars: List[Dict[str, Any]],
        m5_bars: List[Dict[str, Any]]
    ) -> Optional[RWinLossResult]:
        """
        Calculate R Win/Loss for a single trade.

        Walk M1 bars sequentially from entry to 15:30:
        - Check R-level targets (price-based: high/low touch)
        - Check stop (close-based: M1 close beyond stop)
        - Same-candle conflict: R-level hit + close beyond stop => LOSS
        - Track all R-levels hit before stop
        """
        trade_id = trade['trade_id']

        # Parse entry time
        entry_time = _timedelta_to_time(trade['entry_time'])
        if entry_time is None:
            entry_time = trade['entry_time']

        entry_price = _safe_float(trade['entry_price'])
        direction = trade['direction']
        is_long = direction.upper() == 'LONG'

        # Calculate M5 ATR
        atr_value = calculate_atr_m5(m5_bars, period=ATR_PERIOD)
        if atr_value is None or atr_value <= 0:
            self._log(f"Skipping {trade_id}: could not calculate M5 ATR", 'warning')
            return None

        # Calculate stop price and 1R distance
        stop_distance = atr_value * ATR_MULTIPLIER
        if is_long:
            stop_price = entry_price - stop_distance
        else:
            stop_price = entry_price + stop_distance

        stop_distance_pct = (stop_distance / entry_price) * 100 if entry_price > 0 else 0

        # Calculate R-level target prices
        r_prices = {}
        for r in R_LEVELS:
            if is_long:
                r_prices[r] = entry_price + (r * stop_distance)
            else:
                r_prices[r] = entry_price - (r * stop_distance)

        # Build result with initial values
        result = RWinLossResult(
            trade_id=trade_id,
            date=trade['date'],
            ticker=trade['ticker'],
            direction=direction,
            model=trade['model'],
            entry_time=entry_time,
            entry_price=round(entry_price, 4),
            m5_atr_value=round(atr_value, 4),
            stop_price=round(stop_price, 4),
            stop_distance=round(stop_distance, 4),
            stop_distance_pct=round(stop_distance_pct, 4),
            r1_price=round(r_prices[1], 4),
            r2_price=round(r_prices[2], 4),
            r3_price=round(r_prices[3], 4),
            r4_price=round(r_prices[4], 4),
            r5_price=round(r_prices[5], 4),
        )

        # Walk M1 bars from entry to EOD
        entry_minutes = _time_to_minutes(entry_time)
        eod_minutes = _time_to_minutes(EOD_CUTOFF)

        if entry_minutes is None:
            self._log(f"Skipping {trade_id}: could not parse entry time", 'warning')
            return None

        # Track state during walk
        r_levels_hit = set()
        stop_triggered = False
        bar_count = 0
        last_close = None

        # Sort M1 bars by time
        sorted_m1 = sorted(m1_bars, key=lambda b: _time_to_minutes(b.get('bar_time')) or 0)

        for bar in sorted_m1:
            bar_minutes = _time_to_minutes(bar.get('bar_time'))
            if bar_minutes is None:
                continue

            # Only process bars after entry and up to EOD cutoff
            if bar_minutes <= entry_minutes:
                continue
            if bar_minutes > eod_minutes:
                break

            bar_count += 1
            bar_high = _safe_float(bar.get('high'))
            bar_low = _safe_float(bar.get('low'))
            bar_close = _safe_float(bar.get('close'))
            bar_time = _timedelta_to_time(bar.get('bar_time'))
            last_close = bar_close

            # --- Check stop (close-based) ---
            stop_on_this_bar = False
            if is_long:
                if bar_close <= stop_price:
                    stop_on_this_bar = True
            else:
                if bar_close >= stop_price:
                    stop_on_this_bar = True

            # --- Check R-level targets (price-based: high/low touch) ---
            new_r_hits_this_bar = []
            for r in R_LEVELS:
                if r in r_levels_hit:
                    continue  # Already hit this level

                target = r_prices[r]
                target_hit = False
                if is_long:
                    if bar_high >= target:
                        target_hit = True
                else:
                    if bar_low <= target:
                        target_hit = True

                if target_hit:
                    new_r_hits_this_bar.append(r)

            # --- Same-candle conflict resolution ---
            # If stop triggers on this bar, any R-level hits on this SAME bar
            # are invalidated. The trade is stopped out.
            if stop_on_this_bar:
                stop_triggered = True
                result.stop_hit = True
                result.stop_hit_time = bar_time
                result.stop_hit_bars_from_entry = bar_count
                # Do NOT credit R-levels hit on this same bar
                break

            # If no stop on this bar, credit R-level hits
            for r in new_r_hits_this_bar:
                r_levels_hit.add(r)
                if r == 1:
                    result.r1_hit = True
                    result.r1_time = bar_time
                    result.r1_bars_from_entry = bar_count
                elif r == 2:
                    result.r2_hit = True
                    result.r2_time = bar_time
                    result.r2_bars_from_entry = bar_count
                elif r == 3:
                    result.r3_hit = True
                    result.r3_time = bar_time
                    result.r3_bars_from_entry = bar_count
                elif r == 4:
                    result.r4_hit = True
                    result.r4_time = bar_time
                    result.r4_bars_from_entry = bar_count
                elif r == 5:
                    result.r5_hit = True
                    result.r5_time = bar_time
                    result.r5_bars_from_entry = bar_count

            # All R-levels hit, no need to continue
            if len(r_levels_hit) == len(R_LEVELS):
                break

        # --- Determine outcome ---
        result.max_r_achieved = max(r_levels_hit) if r_levels_hit else 0

        if stop_triggered:
            # Stop was hit - check if any R-levels were achieved BEFORE the stop bar
            if result.max_r_achieved >= 1:
                result.outcome = 'WIN'
                result.exit_reason = 'R_TARGET'
            else:
                result.outcome = 'LOSS'
                result.exit_reason = 'STOP'
        else:
            # No stop hit
            if result.max_r_achieved >= 1:
                # R1+ was reached
                result.outcome = 'WIN'
                result.exit_reason = 'R_TARGET'
            else:
                # Neither R1 nor stop by EOD - check price vs entry
                result.eod_price = round(last_close, 4) if last_close else None
                if last_close is not None and last_close > entry_price:
                    result.outcome = 'WIN'
                    result.exit_reason = 'EOD_WIN'
                else:
                    result.outcome = 'LOSS'
                    result.exit_reason = 'EOD_LOSS'

        return result

    # =========================================================================
    # BATCH PROCESSING
    # =========================================================================

    def run_batch_calculation(
        self,
        limit: int = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Main entry point. Process all trades needing R Win/Loss calculation.

        Args:
            limit: Max trades to process (for testing)
            dry_run: If True, calculate but don't write to DB

        Returns:
            Dictionary with execution statistics
        """
        start_time = datetime.now()

        print("=" * 60)
        print("R Win/Loss Calculator")
        print("=" * 60)
        print(f"ATR Period: {ATR_PERIOD}")
        print(f"ATR Multiplier: {ATR_MULTIPLIER}")
        print(f"R-Levels: {R_LEVELS}")
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

            # Caches to minimize DB queries
            m1_cache = {}
            m5_cache = {}

            for idx, trade in trades_df.iterrows():
                trade_id = trade['trade_id']
                ticker = trade['ticker']
                trade_date = trade['date']
                entry_time = trade['entry_time']

                # Cache key for M1 bars (same ticker+date)
                m1_key = f"{ticker}_{trade_date}"
                if m1_key not in m1_cache:
                    m1_cache[m1_key] = self.get_m1_bars(conn, ticker, trade_date)
                m1_bars = m1_cache[m1_key]

                if not m1_bars:
                    self._log(f"Skipping {trade_id}: no M1 bars", 'warning')
                    self.stats['trades_skipped'] += 1
                    continue

                # Cache key for M5 bars (ticker+date+entry_time for bars_from_entry calc)
                m5_key = f"{ticker}_{trade_date}_{entry_time}"
                if m5_key not in m5_cache:
                    m5_cache[m5_key] = self.get_m5_indicator_bars(
                        conn, ticker, trade_date, entry_time
                    )
                m5_bars = m5_cache[m5_key]

                if not m5_bars:
                    self._log(f"Skipping {trade_id}: no M5 indicator bars", 'warning')
                    self.stats['trades_skipped'] += 1
                    continue

                # Calculate
                try:
                    result = self.calculate_single_trade(
                        trade.to_dict(),
                        m1_bars,
                        m5_bars
                    )

                    if result is not None:
                        all_results.append(result)
                        self.stats['trades_processed'] += 1

                        # Trade-by-trade output
                        r_hits = ''.join([
                            f"R{r}" for r in R_LEVELS
                            if getattr(result, f'r{r}_hit', False)
                        ]) or '-'
                        print(
                            f"  [{idx + 1}/{len(trades_df)}] "
                            f"{result.trade_id:<35s} "
                            f"{result.direction:<6s} "
                            f"{result.outcome:<5s} "
                            f"exit={result.exit_reason:<10s} "
                            f"maxR={result.max_r_achieved} "
                            f"hits={r_hits}"
                        )
                    else:
                        self.stats['trades_skipped'] += 1
                        print(
                            f"  [{idx + 1}/{len(trades_df)}] "
                            f"{trade_id:<35s} "
                            f"SKIPPED (no ATR)"
                        )

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
    print("R Win/Loss Calculator - Test Mode")
    print("=" * 60)

    calculator = RWinLossCalculator(verbose=True)
    results = calculator.run_batch_calculation(limit=5, dry_run=True)

    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    for key, value in results.items():
        print(f"  {key}: {value}")
