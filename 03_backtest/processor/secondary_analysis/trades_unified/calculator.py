"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
Trades Unified Calculator (trades_m5_r_win)
XIII Trading LLC
================================================================================

Builds the trades_m5_r_win canonical outcomes table by:
1. Joining trades metadata with r_win_loss ATR-based outcomes (primary)
2. Computing zone_buffer fallback outcomes for trades without r_win_loss records
3. Pre-computing convenience fields (pnl_r, reached_2r, reached_3r, minutes_to_r1)

OUTCOME PRIORITY:
    - If r_win_loss record exists: outcome_method = 'atr_r_target'
    - If no r_win_loss record: outcome_method = 'zone_buffer_fallback'
      (zone_buffer stop with close-based detection, matching ATR methodology)

DATA SOURCES:
    - trades table (trade metadata, zone boundaries, original outcomes)
    - r_win_loss table (ATR-based outcomes)
    - m1_bars table (for zone_buffer fallback bar-by-bar simulation)

Version: 1.0.0
================================================================================
"""

import psycopg2
from psycopg2.extras import execute_values
import numpy as np
from datetime import datetime, date, time, timedelta
from typing import Dict, List, Any, Optional
from decimal import Decimal
import logging

from config import (
    DB_CONFIG, EOD_CUTOFF, ZONE_BUFFER_PCT,
    SOURCE_TABLES, TARGET_TABLE
)


# =============================================================================
# HELPER FUNCTIONS (copied from r_win_loss/calculator.py for consistency)
# =============================================================================

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
# CALCULATOR CLASS
# =============================================================================

class TradesUnifiedCalculator:
    """
    Builds the trades_m5_r_win canonical outcomes table.

    This class:
    1. Queries all trades from the trades table
    2. Fetches all r_win_loss records (keyed by trade_id)
    3. For trades WITH r_win_loss: maps ATR-based outcome data
    4. For trades WITHOUT r_win_loss: runs zone_buffer fallback calculation
    5. Pre-computes convenience fields (pnl_r, reached_2r, etc.)
    6. Writes unified records to trades_m5_r_win table
    """

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.logger = logging.getLogger(__name__)
        self.stats = {
            'trades_processed': 0,
            'trades_skipped': 0,
            'atr_records': 0,
            'fallback_records': 0,
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

    def get_all_trades(self, conn, limit: int = None) -> List[Dict[str, Any]]:
        """
        Fetch all trades that need unified records.
        Only processes trades not already in trades_m5_r_win (incremental).
        """
        query = f"""
            SELECT
                t.trade_id,
                t.date,
                t.ticker,
                t.model,
                t.zone_type,
                t.direction,
                t.zone_high,
                t.zone_low,
                t.entry_price,
                t.entry_time,
                t.stop_price,
                t.target_3r,
                t.exit_price,
                t.exit_time,
                t.exit_reason,
                t.pnl_dollars,
                t.pnl_r,
                t.is_winner
            FROM {SOURCE_TABLES['trades']} t
            WHERE t.entry_time IS NOT NULL
              AND t.entry_price IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1 FROM {TARGET_TABLE} u
                  WHERE u.trade_id = t.trade_id
              )
            ORDER BY t.date, t.ticker, t.entry_time
        """

        if limit:
            query += f" LIMIT {limit}"

        with conn.cursor() as cur:
            cur.execute(query)
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()

        return [dict(zip(columns, row)) for row in rows]

    def get_r_win_loss_records(self, conn) -> Dict[str, Dict[str, Any]]:
        """
        Fetch all r_win_loss records, indexed by trade_id.
        Returns dict mapping trade_id -> full r_win_loss row.
        """
        query = f"""
            SELECT *
            FROM {SOURCE_TABLES['r_win_loss']}
        """

        with conn.cursor() as cur:
            cur.execute(query)
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()

        return {
            row[columns.index('trade_id')]: dict(zip(columns, row))
            for row in rows
        }

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

    # =========================================================================
    # ATR RECORD BUILDER (from r_win_loss data)
    # =========================================================================

    def build_atr_record(self, trade: Dict[str, Any], rwl: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build a unified record from trades + r_win_loss data.
        outcome_method = 'atr_r_target'
        """
        entry_price = _safe_float(trade['entry_price'])
        direction = (trade.get('direction') or '').upper()
        is_long = direction == 'LONG'

        # Extract r_win_loss fields
        outcome = rwl.get('outcome', 'LOSS')
        exit_reason = rwl.get('exit_reason', 'EOD_LOSS')
        max_r_achieved = int(rwl.get('max_r_achieved', 0) or 0)
        stop_distance = _safe_float(rwl.get('stop_distance'))
        eod_price = rwl.get('eod_price')

        # Calculate continuous pnl_r
        if outcome == 'WIN' and exit_reason == 'R_TARGET':
            pnl_r = float(max_r_achieved)
        elif exit_reason == 'STOP':
            pnl_r = -1.0
        elif exit_reason in ('EOD_WIN', 'EOD_LOSS') and eod_price is not None and stop_distance > 0:
            eod_price_f = _safe_float(eod_price)
            if is_long:
                pnl_r = round((eod_price_f - entry_price) / stop_distance, 4)
            else:
                pnl_r = round((entry_price - eod_price_f) / stop_distance, 4)
        else:
            pnl_r = float(max_r_achieved) if outcome == 'WIN' else -1.0

        # Parse entry_time
        entry_time = _timedelta_to_time(trade['entry_time'])
        if entry_time is None:
            entry_time = trade['entry_time']

        return {
            # Trade identification
            'trade_id': trade['trade_id'],
            'date': trade['date'],
            'ticker': trade['ticker'],
            'model': trade.get('model'),
            'zone_type': trade.get('zone_type'),
            'direction': trade.get('direction'),
            'zone_high': trade.get('zone_high'),
            'zone_low': trade.get('zone_low'),
            'entry_price': trade['entry_price'],
            'entry_time': entry_time,
            # Original zone buffer fields
            'zb_stop_price': trade.get('stop_price'),
            'zb_target_3r': trade.get('target_3r'),
            'zb_exit_price': trade.get('exit_price'),
            'zb_exit_time': _timedelta_to_time(trade.get('exit_time')),
            'zb_exit_reason': trade.get('exit_reason'),
            'zb_pnl_dollars': trade.get('pnl_dollars'),
            'zb_pnl_r': trade.get('pnl_r'),
            'zb_is_winner': trade.get('is_winner'),
            # ATR stop calculation
            'm5_atr_value': rwl.get('m5_atr_value'),
            'stop_price': rwl.get('stop_price'),
            'stop_distance': rwl.get('stop_distance'),
            'stop_distance_pct': rwl.get('stop_distance_pct'),
            # R-level prices
            'r1_price': rwl.get('r1_price'),
            'r2_price': rwl.get('r2_price'),
            'r3_price': rwl.get('r3_price'),
            'r4_price': rwl.get('r4_price'),
            'r5_price': rwl.get('r5_price'),
            # R-level hits
            'r1_hit': bool(rwl.get('r1_hit', False)),
            'r1_time': _timedelta_to_time(rwl.get('r1_time')),
            'r1_bars_from_entry': rwl.get('r1_bars_from_entry'),
            'r2_hit': bool(rwl.get('r2_hit', False)),
            'r2_time': _timedelta_to_time(rwl.get('r2_time')),
            'r2_bars_from_entry': rwl.get('r2_bars_from_entry'),
            'r3_hit': bool(rwl.get('r3_hit', False)),
            'r3_time': _timedelta_to_time(rwl.get('r3_time')),
            'r3_bars_from_entry': rwl.get('r3_bars_from_entry'),
            'r4_hit': bool(rwl.get('r4_hit', False)),
            'r4_time': _timedelta_to_time(rwl.get('r4_time')),
            'r4_bars_from_entry': rwl.get('r4_bars_from_entry'),
            'r5_hit': bool(rwl.get('r5_hit', False)),
            'r5_time': _timedelta_to_time(rwl.get('r5_time')),
            'r5_bars_from_entry': rwl.get('r5_bars_from_entry'),
            # Stop hit
            'stop_hit': bool(rwl.get('stop_hit', False)),
            'stop_hit_time': _timedelta_to_time(rwl.get('stop_hit_time')),
            'stop_hit_bars_from_entry': rwl.get('stop_hit_bars_from_entry'),
            # Canonical outcome
            'max_r_achieved': max_r_achieved,
            'outcome': outcome,
            'exit_reason': exit_reason,
            'eod_price': rwl.get('eod_price'),
            # Convenience fields
            'outcome_method': 'atr_r_target',
            'is_winner': outcome == 'WIN',
            'pnl_r': pnl_r,
            'reached_2r': bool(rwl.get('r2_hit', False)),
            'reached_3r': bool(rwl.get('r3_hit', False)),
            'minutes_to_r1': rwl.get('r1_bars_from_entry'),
        }

    # =========================================================================
    # ZONE BUFFER FALLBACK CALCULATION
    # =========================================================================

    def calculate_zone_buffer_fallback(
        self,
        trade: Dict[str, Any],
        m1_bars: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate WIN/LOSS for trades missing r_win_loss records.
        Uses zone_buffer stop with CLOSE-based detection (matching ATR methodology).

        Logic:
            1. Stop = zone_low - (zone_distance * 5%) for LONG
               Stop = zone_high + (zone_distance * 5%) for SHORT
            2. 1R distance = abs(entry_price - stop_price)
            3. R1 target = entry +/- 1R
            4. Walk M1 bars from entry to 15:30 ET:
               - R1: price-based (high/low touch)
               - Stop: close-based (M1 close beyond stop)
               - Same-candle conflict: stop takes priority
            5. Outcome: WIN if R1 before stop, LOSS otherwise

        Returns:
            Dict with fallback calculation results
        """
        entry_price = _safe_float(trade['entry_price'])
        direction = (trade.get('direction') or '').upper()
        is_long = direction == 'LONG'
        zone_high = _safe_float(trade.get('zone_high'))
        zone_low = _safe_float(trade.get('zone_low'))

        # Validate zone data
        if zone_high <= 0 or zone_low <= 0 or zone_high <= zone_low:
            # Cannot calculate zone buffer - use original trades.is_winner
            return self._build_minimal_fallback(trade)

        zone_distance = zone_high - zone_low

        # Calculate zone buffer stop price
        if is_long:
            stop_price = zone_low - (zone_distance * ZONE_BUFFER_PCT)
        else:
            stop_price = zone_high + (zone_distance * ZONE_BUFFER_PCT)

        stop_distance = abs(entry_price - stop_price)

        if stop_distance <= 0:
            return self._build_minimal_fallback(trade)

        stop_distance_pct = (stop_distance / entry_price) * 100 if entry_price > 0 else 0

        # Calculate R1 target
        if is_long:
            r1_price = entry_price + stop_distance
        else:
            r1_price = entry_price - stop_distance

        # Walk M1 bars from entry to 15:30 ET
        entry_minutes = _time_to_minutes(trade['entry_time'])
        eod_minutes = _time_to_minutes(EOD_CUTOFF)

        if entry_minutes is None:
            return self._build_minimal_fallback(trade)

        r1_hit = False
        r1_time_val = None
        r1_bars = None
        stop_triggered = False
        stop_time_val = None
        stop_bars = None
        last_close = None
        bar_count = 0

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

            # Stop check (CLOSE-based, matching ATR methodology)
            stop_on_this_bar = False
            if is_long and bar_close <= stop_price:
                stop_on_this_bar = True
            elif not is_long and bar_close >= stop_price:
                stop_on_this_bar = True

            # R1 check (PRICE-based)
            r1_on_this_bar = False
            if not r1_hit:
                if is_long and bar_high >= r1_price:
                    r1_on_this_bar = True
                elif not is_long and bar_low <= r1_price:
                    r1_on_this_bar = True

            # Same-candle conflict: stop takes priority
            if stop_on_this_bar:
                stop_triggered = True
                stop_time_val = bar_time
                stop_bars = bar_count
                break

            if r1_on_this_bar:
                r1_hit = True
                r1_time_val = bar_time
                r1_bars = bar_count
                break  # For fallback, we only track R1

        # Determine outcome
        if stop_triggered:
            outcome = 'LOSS'
            exit_reason = 'ZB_STOP'
        elif r1_hit:
            outcome = 'WIN'
            exit_reason = 'ZB_R_TARGET'
        elif last_close is not None:
            if is_long and last_close > entry_price:
                outcome = 'WIN'
                exit_reason = 'ZB_EOD_WIN'
            elif not is_long and last_close < entry_price:
                outcome = 'WIN'
                exit_reason = 'ZB_EOD_WIN'
            else:
                outcome = 'LOSS'
                exit_reason = 'ZB_EOD_LOSS'
        else:
            outcome = 'LOSS'
            exit_reason = 'ZB_EOD_LOSS'

        # Calculate pnl_r
        if outcome == 'WIN' and exit_reason == 'ZB_R_TARGET':
            pnl_r = 1.0
        elif exit_reason == 'ZB_STOP':
            pnl_r = -1.0
        elif last_close is not None and stop_distance > 0:
            if is_long:
                pnl_r = round((last_close - entry_price) / stop_distance, 4)
            else:
                pnl_r = round((entry_price - last_close) / stop_distance, 4)
        else:
            pnl_r = -1.0

        return {
            'stop_price': round(stop_price, 4),
            'stop_distance': round(stop_distance, 4),
            'stop_distance_pct': round(stop_distance_pct, 4),
            'r1_price': round(r1_price, 4),
            'r1_hit': r1_hit,
            'r1_time': r1_time_val,
            'r1_bars_from_entry': r1_bars,
            'stop_hit': stop_triggered,
            'stop_hit_time': stop_time_val,
            'stop_hit_bars_from_entry': stop_bars,
            'max_r_achieved': 1 if r1_hit else 0,
            'outcome': outcome,
            'exit_reason': exit_reason,
            'eod_price': round(last_close, 4) if last_close is not None else None,
            'pnl_r': pnl_r,
        }

    def _build_minimal_fallback(self, trade: Dict[str, Any]) -> Dict[str, Any]:
        """
        Last-resort fallback when zone data is invalid.
        Uses original trades.is_winner as the outcome.
        """
        original_winner = bool(trade.get('is_winner', False))
        original_pnl_r = _safe_float(trade.get('pnl_r'), default=0.0)

        return {
            'stop_price': _safe_float(trade.get('stop_price'), default=None),
            'stop_distance': None,
            'stop_distance_pct': None,
            'r1_price': None,
            'r1_hit': original_winner,
            'r1_time': None,
            'r1_bars_from_entry': None,
            'stop_hit': not original_winner,
            'stop_hit_time': None,
            'stop_hit_bars_from_entry': None,
            'max_r_achieved': 1 if original_winner else 0,
            'outcome': 'WIN' if original_winner else 'LOSS',
            'exit_reason': 'ZB_R_TARGET' if original_winner else 'ZB_STOP',
            'eod_price': None,
            'pnl_r': original_pnl_r if original_pnl_r != 0.0 else (1.0 if original_winner else -1.0),
        }

    def build_fallback_record(
        self,
        trade: Dict[str, Any],
        fallback: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build a unified record from trades + zone_buffer fallback data.
        outcome_method = 'zone_buffer_fallback'
        R2-R5 fields are all NULL (only R1 tracked in fallback).
        """
        entry_time = _timedelta_to_time(trade['entry_time'])
        if entry_time is None:
            entry_time = trade['entry_time']

        return {
            # Trade identification
            'trade_id': trade['trade_id'],
            'date': trade['date'],
            'ticker': trade['ticker'],
            'model': trade.get('model'),
            'zone_type': trade.get('zone_type'),
            'direction': trade.get('direction'),
            'zone_high': trade.get('zone_high'),
            'zone_low': trade.get('zone_low'),
            'entry_price': trade['entry_price'],
            'entry_time': entry_time,
            # Original zone buffer fields
            'zb_stop_price': trade.get('stop_price'),
            'zb_target_3r': trade.get('target_3r'),
            'zb_exit_price': trade.get('exit_price'),
            'zb_exit_time': _timedelta_to_time(trade.get('exit_time')),
            'zb_exit_reason': trade.get('exit_reason'),
            'zb_pnl_dollars': trade.get('pnl_dollars'),
            'zb_pnl_r': trade.get('pnl_r'),
            'zb_is_winner': trade.get('is_winner'),
            # Fallback stop calculation (no ATR for fallback)
            'm5_atr_value': None,
            'stop_price': fallback.get('stop_price'),
            'stop_distance': fallback.get('stop_distance'),
            'stop_distance_pct': fallback.get('stop_distance_pct'),
            # R-level prices (only R1 for fallback)
            'r1_price': fallback.get('r1_price'),
            'r2_price': None,
            'r3_price': None,
            'r4_price': None,
            'r5_price': None,
            # R-level hits (only R1 for fallback)
            'r1_hit': fallback.get('r1_hit', False),
            'r1_time': fallback.get('r1_time'),
            'r1_bars_from_entry': fallback.get('r1_bars_from_entry'),
            'r2_hit': False,
            'r2_time': None,
            'r2_bars_from_entry': None,
            'r3_hit': False,
            'r3_time': None,
            'r3_bars_from_entry': None,
            'r4_hit': False,
            'r4_time': None,
            'r4_bars_from_entry': None,
            'r5_hit': False,
            'r5_time': None,
            'r5_bars_from_entry': None,
            # Stop hit
            'stop_hit': fallback.get('stop_hit', False),
            'stop_hit_time': fallback.get('stop_hit_time'),
            'stop_hit_bars_from_entry': fallback.get('stop_hit_bars_from_entry'),
            # Canonical outcome
            'max_r_achieved': fallback.get('max_r_achieved', 0),
            'outcome': fallback['outcome'],
            'exit_reason': fallback['exit_reason'],
            'eod_price': fallback.get('eod_price'),
            # Convenience fields
            'outcome_method': 'zone_buffer_fallback',
            'is_winner': fallback['outcome'] == 'WIN',
            'pnl_r': fallback.get('pnl_r', -1.0),
            'reached_2r': False,
            'reached_3r': False,
            'minutes_to_r1': fallback.get('r1_bars_from_entry'),
        }

    # =========================================================================
    # DATABASE INSERT
    # =========================================================================

    def insert_records(self, conn, records: List[Dict[str, Any]]) -> int:
        """Insert unified records into trades_m5_r_win table with UPSERT."""
        if not records:
            return 0

        query = f"""
            INSERT INTO {TARGET_TABLE} (
                trade_id, date, ticker, model, zone_type, direction,
                zone_high, zone_low, entry_price, entry_time,
                zb_stop_price, zb_target_3r, zb_exit_price, zb_exit_time,
                zb_exit_reason, zb_pnl_dollars, zb_pnl_r, zb_is_winner,
                m5_atr_value, stop_price, stop_distance, stop_distance_pct,
                r1_price, r2_price, r3_price, r4_price, r5_price,
                r1_hit, r1_time, r1_bars_from_entry,
                r2_hit, r2_time, r2_bars_from_entry,
                r3_hit, r3_time, r3_bars_from_entry,
                r4_hit, r4_time, r4_bars_from_entry,
                r5_hit, r5_time, r5_bars_from_entry,
                stop_hit, stop_hit_time, stop_hit_bars_from_entry,
                max_r_achieved, outcome, exit_reason, eod_price,
                outcome_method, is_winner, pnl_r,
                reached_2r, reached_3r, minutes_to_r1
            ) VALUES %s
            ON CONFLICT (trade_id) DO UPDATE SET
                date = EXCLUDED.date,
                ticker = EXCLUDED.ticker,
                model = EXCLUDED.model,
                zone_type = EXCLUDED.zone_type,
                direction = EXCLUDED.direction,
                zone_high = EXCLUDED.zone_high,
                zone_low = EXCLUDED.zone_low,
                entry_price = EXCLUDED.entry_price,
                entry_time = EXCLUDED.entry_time,
                zb_stop_price = EXCLUDED.zb_stop_price,
                zb_target_3r = EXCLUDED.zb_target_3r,
                zb_exit_price = EXCLUDED.zb_exit_price,
                zb_exit_time = EXCLUDED.zb_exit_time,
                zb_exit_reason = EXCLUDED.zb_exit_reason,
                zb_pnl_dollars = EXCLUDED.zb_pnl_dollars,
                zb_pnl_r = EXCLUDED.zb_pnl_r,
                zb_is_winner = EXCLUDED.zb_is_winner,
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
                outcome_method = EXCLUDED.outcome_method,
                is_winner = EXCLUDED.is_winner,
                pnl_r = EXCLUDED.pnl_r,
                reached_2r = EXCLUDED.reached_2r,
                reached_3r = EXCLUDED.reached_3r,
                minutes_to_r1 = EXCLUDED.minutes_to_r1,
                updated_at = NOW()
        """

        values = []
        for r in records:
            values.append((
                r['trade_id'], r['date'], r['ticker'], r.get('model'), r.get('zone_type'), r.get('direction'),
                _convert_numpy(r.get('zone_high')), _convert_numpy(r.get('zone_low')),
                _convert_numpy(r['entry_price']), r['entry_time'],
                _convert_numpy(r.get('zb_stop_price')), _convert_numpy(r.get('zb_target_3r')),
                _convert_numpy(r.get('zb_exit_price')), r.get('zb_exit_time'),
                r.get('zb_exit_reason'), _convert_numpy(r.get('zb_pnl_dollars')),
                _convert_numpy(r.get('zb_pnl_r')), r.get('zb_is_winner'),
                _convert_numpy(r.get('m5_atr_value')), _convert_numpy(r.get('stop_price')),
                _convert_numpy(r.get('stop_distance')), _convert_numpy(r.get('stop_distance_pct')),
                _convert_numpy(r.get('r1_price')), _convert_numpy(r.get('r2_price')),
                _convert_numpy(r.get('r3_price')), _convert_numpy(r.get('r4_price')),
                _convert_numpy(r.get('r5_price')),
                r.get('r1_hit', False), r.get('r1_time'), r.get('r1_bars_from_entry'),
                r.get('r2_hit', False), r.get('r2_time'), r.get('r2_bars_from_entry'),
                r.get('r3_hit', False), r.get('r3_time'), r.get('r3_bars_from_entry'),
                r.get('r4_hit', False), r.get('r4_time'), r.get('r4_bars_from_entry'),
                r.get('r5_hit', False), r.get('r5_time'), r.get('r5_bars_from_entry'),
                r.get('stop_hit', False), r.get('stop_hit_time'), r.get('stop_hit_bars_from_entry'),
                r.get('max_r_achieved', 0), r['outcome'], r['exit_reason'],
                _convert_numpy(r.get('eod_price')),
                r['outcome_method'], r['is_winner'], _convert_numpy(r.get('pnl_r')),
                r.get('reached_2r', False), r.get('reached_3r', False), r.get('minutes_to_r1'),
            ))

        with conn.cursor() as cur:
            execute_values(cur, query, values)

        return len(records)

    # =========================================================================
    # BATCH PROCESSING
    # =========================================================================

    def run_batch_calculation(
        self,
        limit: int = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Main entry point. Build trades_m5_r_win from trades + r_win_loss.

        Args:
            limit: Max trades to process (for testing)
            dry_run: If True, calculate but don't write to DB

        Returns:
            Dictionary with execution statistics
        """
        start_time = datetime.now()

        print("=" * 60)
        print("Trades Unified Calculator (trades_m5_r_win)")
        print("=" * 60)
        print(f"Outcome Priority: r_win_loss ATR > zone_buffer fallback")
        print(f"Zone Buffer PCT: {ZONE_BUFFER_PCT}")
        print(f"Dry Run: {dry_run}")
        if limit:
            print(f"Limit: {limit} trades")
        print()

        # Reset statistics
        self.stats = {
            'trades_processed': 0,
            'trades_skipped': 0,
            'atr_records': 0,
            'fallback_records': 0,
            'records_created': 0,
            'errors': []
        }

        conn = None
        try:
            # Connect to database
            print("[1/5] Connecting to Supabase...")
            conn = psycopg2.connect(**DB_CONFIG)
            print("  Connected successfully")

            # Load r_win_loss records
            print("\n[2/5] Loading r_win_loss records...")
            rwl_dict = self.get_r_win_loss_records(conn)
            print(f"  Loaded {len(rwl_dict)} r_win_loss records")

            # Get trades needing calculation
            print("\n[3/5] Querying trades needing calculation...")
            trades = self.get_all_trades(conn, limit)
            print(f"  Found {len(trades)} trades to process")

            if not trades:
                print("\n  No trades need calculation. Exiting.")
                return self._build_result(start_time)

            # Process trades
            print(f"\n[4/5] Processing {len(trades)} trades...")
            all_records = []
            m1_cache = {}

            for idx, trade in enumerate(trades):
                trade_id = trade['trade_id']
                ticker = trade['ticker']
                trade_date = trade['date']

                try:
                    if trade_id in rwl_dict:
                        # ATR-based record (primary path)
                        record = self.build_atr_record(trade, rwl_dict[trade_id])
                        all_records.append(record)
                        self.stats['atr_records'] += 1
                        self.stats['trades_processed'] += 1

                        print(
                            f"  [{idx + 1}/{len(trades)}] "
                            f"{trade_id:<35s} "
                            f"ATR    "
                            f"{record['direction'] or '':<6s} "
                            f"{record['outcome']:<5s} "
                            f"exit={record['exit_reason']:<12s} "
                            f"maxR={record['max_r_achieved']} "
                            f"pnl_r={record['pnl_r']:+.2f}"
                        )

                    else:
                        # Zone buffer fallback (secondary path)
                        m1_key = f"{ticker}_{trade_date}"
                        if m1_key not in m1_cache:
                            m1_cache[m1_key] = self.get_m1_bars(conn, ticker, trade_date)
                        m1_bars = m1_cache[m1_key]

                        if not m1_bars:
                            self._log(f"Fallback {trade_id}: no M1 bars, using trades.is_winner", 'warning')

                        fallback = self.calculate_zone_buffer_fallback(trade, m1_bars)
                        record = self.build_fallback_record(trade, fallback)
                        all_records.append(record)
                        self.stats['fallback_records'] += 1
                        self.stats['trades_processed'] += 1

                        print(
                            f"  [{idx + 1}/{len(trades)}] "
                            f"{trade_id:<35s} "
                            f"ZB_FB  "
                            f"{record['direction'] or '':<6s} "
                            f"{record['outcome']:<5s} "
                            f"exit={record['exit_reason']:<12s} "
                            f"pnl_r={record['pnl_r']:+.2f}"
                        )

                except Exception as e:
                    self.stats['errors'].append(f"{trade_id}: {str(e)}")
                    self._log(f"Error processing {trade_id}: {e}", 'error')

            # Write results to database
            print(f"\n[5/5] Writing results to database...")
            if dry_run:
                print(f"  [DRY-RUN] Would insert {len(all_records)} records")
                print(f"  [DRY-RUN] ATR: {self.stats['atr_records']}, Fallback: {self.stats['fallback_records']}")
            else:
                inserted = self.insert_records(conn, all_records)
                conn.commit()
                self.stats['records_created'] = inserted
                print(f"  Inserted {inserted} records")
                print(f"  ATR: {self.stats['atr_records']}, Fallback: {self.stats['fallback_records']}")

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
            'atr_records': self.stats['atr_records'],
            'fallback_records': self.stats['fallback_records'],
            'records_created': self.stats['records_created'],
            'errors': self.stats['errors'],
            'execution_time_seconds': round(elapsed, 2)
        }


# =============================================================================
# STANDALONE TEST
# =============================================================================
if __name__ == "__main__":
    print("Trades Unified Calculator - Test Mode")
    print("=" * 60)

    calculator = TradesUnifiedCalculator(verbose=True)
    results = calculator.run_batch_calculation(limit=5, dry_run=True)

    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    for key, value in results.items():
        print(f"  {key}: {value}")
