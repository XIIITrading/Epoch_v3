"""
Journal Training Processors — Populate secondary analysis tables for flashcard UI.

Four processors that mirror the backtest secondary analysis pipeline:
1. JournalEntryIndicatorsProcessor — Indicator snapshot at entry time
2. JournalMFEMAEProcessor — MFE/MAE in R-multiples
3. JournalRLevelsProcessor — R-level price calculations and hit tracking
4. JournalOptimalTradeProcessor — Indicator snapshots at critical events

Gate: Only processes trades where stop_price IS NOT NULL.

Usage:
    from processor.training_processors import (
        JournalEntryIndicatorsProcessor,
        JournalMFEMAEProcessor,
        JournalRLevelsProcessor,
        JournalOptimalTradeProcessor,
    )

    with JournalEntryIndicatorsProcessor() as proc:
        proc.process_all()
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, date, time, timedelta
from typing import Dict, List, Optional, Any
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DB_CONFIG

logger = logging.getLogger(__name__)


# =============================================================================
# HELPERS
# =============================================================================

def _safe_float(val) -> Optional[float]:
    """Convert to float, returning None for invalid values."""
    if val is None:
        return None
    try:
        f = float(val)
        import math
        return None if math.isnan(f) or math.isinf(f) else f
    except (TypeError, ValueError):
        return None


def _safe_int(val) -> Optional[int]:
    """Convert to int, returning None for invalid values."""
    if val is None:
        return None
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def _health_label(score: Optional[int]) -> Optional[str]:
    """Classify health score into label."""
    if score is None:
        return None
    if score >= 8:
        return "STRONG"
    elif score >= 6:
        return "MODERATE"
    elif score >= 4:
        return "WEAK"
    else:
        return "CRITICAL"


def _health_summary(delta: Optional[int]) -> Optional[str]:
    """Classify health delta into summary."""
    if delta is None:
        return None
    if delta > 0:
        return "IMPROVING"
    elif delta < 0:
        return "DEGRADING"
    else:
        return "STABLE"


def _calculate_component_scores(bar: Dict, direction: str) -> Dict:
    """Calculate structure/volume/price component scores from an indicator bar."""
    scores = {'structure_score': 0, 'volume_score': 0, 'price_score': 0}
    is_long = direction.upper() == 'LONG'

    # Structure score (0-4): h4, h1, m15, m1 alignment
    for tf in ['h4_structure', 'h1_structure', 'm15_structure', 'm1_structure']:
        struct = (bar.get(tf) or '').upper()
        if is_long and struct == 'BULL':
            scores['structure_score'] += 1
        elif not is_long and struct == 'BEAR':
            scores['structure_score'] += 1

    # Volume score (0-3): vol_roc > 30, vol_delta aligned, cvd_slope aligned
    vol_roc = _safe_float(bar.get('vol_roc'))
    if vol_roc is not None and vol_roc > 30:
        scores['volume_score'] += 1
    vol_delta = _safe_float(bar.get('vol_delta'))
    if vol_delta is not None:
        if (is_long and vol_delta > 0) or (not is_long and vol_delta < 0):
            scores['volume_score'] += 1
    cvd_slope = _safe_float(bar.get('cvd_slope'))
    if cvd_slope is not None:
        if (is_long and cvd_slope > 0) or (not is_long and cvd_slope < 0):
            scores['volume_score'] += 1

    # Price score (0-3): sma_alignment, sma_momentum, vwap_position
    sma9 = _safe_float(bar.get('sma9'))
    sma21 = _safe_float(bar.get('sma21'))
    if sma9 is not None and sma21 is not None:
        if (is_long and sma9 > sma21) or (not is_long and sma9 < sma21):
            scores['price_score'] += 1
    sma_momentum_label = (bar.get('sma_momentum_label') or '').upper()
    if sma_momentum_label == 'WIDENING':
        scores['price_score'] += 1
    vwap = _safe_float(bar.get('vwap'))
    close = _safe_float(bar.get('close'))
    if vwap is not None and close is not None:
        if (is_long and close > vwap) or (not is_long and close < vwap):
            scores['price_score'] += 1

    return scores


def _calculate_healthy_flags(bar: Dict, direction: str) -> Dict:
    """Calculate healthy boolean flags for an indicator bar."""
    is_long = direction.upper() == 'LONG'
    flags = {}

    sma9 = _safe_float(bar.get('sma9'))
    sma21 = _safe_float(bar.get('sma21'))
    flags['sma_alignment_healthy'] = (
        sma9 is not None and sma21 is not None and
        ((is_long and sma9 > sma21) or (not is_long and sma9 < sma21))
    )

    sma_momentum_label = (bar.get('sma_momentum_label') or '').upper()
    flags['sma_momentum_healthy'] = sma_momentum_label == 'WIDENING'

    vwap = _safe_float(bar.get('vwap'))
    close = _safe_float(bar.get('close'))
    flags['vwap_healthy'] = (
        vwap is not None and close is not None and
        ((is_long and close > vwap) or (not is_long and close < vwap))
    )

    vol_roc = _safe_float(bar.get('vol_roc'))
    flags['vol_roc_healthy'] = vol_roc is not None and vol_roc > 30

    vol_delta = _safe_float(bar.get('vol_delta'))
    flags['vol_delta_healthy'] = (
        vol_delta is not None and
        ((is_long and vol_delta > 0) or (not is_long and vol_delta < 0))
    )

    cvd_slope = _safe_float(bar.get('cvd_slope'))
    flags['cvd_slope_healthy'] = (
        cvd_slope is not None and
        ((is_long and cvd_slope > 0) or (not is_long and cvd_slope < 0))
    )

    return flags


# =============================================================================
# BASE PROCESSOR
# =============================================================================

class BaseTrainingProcessor:
    """Base class with DB connection management."""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.conn = None

    def connect(self) -> bool:
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            return True
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _ensure_connected(self):
        if not self.conn or self.conn.closed:
            self.connect()

    def _log(self, msg: str, level: str = 'info'):
        if self.verbose or level in ('error', 'warning'):
            prefix = {'error': '!', 'warning': '?', 'info': ' ', 'debug': '  '}
            print(f"  {prefix.get(level, ' ')} {msg}")

    def _fetch_eligible_trades(self, trade_id: str = None, trade_date: date = None) -> List[Dict]:
        """Fetch trades that have stop_price set (eligible for training processing)."""
        self._ensure_connected()
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = """
                SELECT trade_id, trade_date, symbol, direction, account,
                       entry_price, entry_time, exit_price, exit_time,
                       pnl_dollars, pnl_total, pnl_r, outcome,
                       zone_id, model, stop_price, notes,
                       duration_seconds, is_closed
                FROM journal_trades
                WHERE stop_price IS NOT NULL
                  AND entry_time IS NOT NULL
                  AND is_closed = TRUE
            """
            params = []
            if trade_id:
                query += " AND trade_id = %s"
                params.append(trade_id)
            if trade_date:
                query += " AND trade_date = %s"
                params.append(trade_date)
            query += " ORDER BY trade_date, entry_time"
            cur.execute(query, params)
            return cur.fetchall()

    def get_table_count(self, table: str) -> int:
        """Get row count for a table."""
        self._ensure_connected()
        with self.conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            return cur.fetchone()[0]


# =============================================================================
# 1. ENTRY INDICATORS PROCESSOR
# =============================================================================

class JournalEntryIndicatorsProcessor(BaseTrainingProcessor):
    """
    Snapshots journal_m1_indicator_bars at trade entry time.
    Looks up the M1 indicator bar at or just before entry_time.
    """

    TARGET_TABLE = "journal_entry_indicators"

    def process_all(self, trade_id: str = None, trade_date: date = None, dry_run: bool = False) -> Dict:
        """Process all eligible trades."""
        trades = self._fetch_eligible_trades(trade_id, trade_date)
        stats = {'processed': 0, 'skipped': 0, 'errors': []}
        self._log(f"Entry Indicators: {len(trades)} eligible trades")

        for trade in trades:
            try:
                result = self._process_one(trade, dry_run)
                if result:
                    stats['processed'] += 1
                else:
                    stats['skipped'] += 1
            except Exception as e:
                stats['errors'].append(f"{trade['trade_id']}: {e}")
                self._log(f"Error {trade['trade_id']}: {e}", 'error')

        self._log(f"Entry Indicators: {stats['processed']} processed, {stats['skipped']} skipped, {len(stats['errors'])} errors")
        return stats

    def _process_one(self, trade: Dict, dry_run: bool = False) -> bool:
        """Process a single trade."""
        trade_id = trade['trade_id']
        ticker = trade['symbol']
        trade_date = trade['trade_date']
        entry_time = trade['entry_time']
        direction = trade['direction']

        # Fetch indicator bar at or before entry time
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM journal_m1_indicator_bars
                WHERE ticker = %s AND bar_date = %s AND bar_time <= %s
                ORDER BY bar_time DESC
                LIMIT 1
            """, (ticker, trade_date, entry_time))
            bar = cur.fetchone()

        if not bar:
            self._log(f"  [{trade_id}] No indicator bar found at/before entry", 'warning')
            return False

        # Calculate component scores
        comp_scores = _calculate_component_scores(bar, direction)

        if dry_run:
            self._log(f"  [{trade_id}] Would insert entry indicators (health={bar.get('health_score')})")
            return True

        # Upsert
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO journal_entry_indicators (
                    trade_id, trade_date, ticker, direction, entry_time, entry_price,
                    indicator_bar_time,
                    vwap, sma9, sma21, sma_spread, sma_momentum_ratio, sma_momentum_label,
                    vol_roc, vol_delta, cvd_slope,
                    h4_structure, h1_structure, m15_structure, m5_structure, m1_structure,
                    health_score, candle_range_pct, long_score, short_score,
                    structure_score, volume_score, price_score,
                    calculated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s,
                    %s,
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    NOW()
                )
                ON CONFLICT (trade_id) DO UPDATE SET
                    indicator_bar_time = EXCLUDED.indicator_bar_time,
                    vwap = EXCLUDED.vwap, sma9 = EXCLUDED.sma9, sma21 = EXCLUDED.sma21,
                    sma_spread = EXCLUDED.sma_spread, sma_momentum_ratio = EXCLUDED.sma_momentum_ratio,
                    sma_momentum_label = EXCLUDED.sma_momentum_label,
                    vol_roc = EXCLUDED.vol_roc, vol_delta = EXCLUDED.vol_delta, cvd_slope = EXCLUDED.cvd_slope,
                    h4_structure = EXCLUDED.h4_structure, h1_structure = EXCLUDED.h1_structure,
                    m15_structure = EXCLUDED.m15_structure, m5_structure = EXCLUDED.m5_structure,
                    m1_structure = EXCLUDED.m1_structure,
                    health_score = EXCLUDED.health_score,
                    candle_range_pct = EXCLUDED.candle_range_pct,
                    long_score = EXCLUDED.long_score, short_score = EXCLUDED.short_score,
                    structure_score = EXCLUDED.structure_score, volume_score = EXCLUDED.volume_score,
                    price_score = EXCLUDED.price_score,
                    calculated_at = NOW()
            """, (
                trade_id, trade_date, ticker, direction, entry_time, _safe_float(trade['entry_price']),
                bar['bar_time'],
                _safe_float(bar.get('vwap')), _safe_float(bar.get('sma9')), _safe_float(bar.get('sma21')),
                _safe_float(bar.get('sma_spread')), _safe_float(bar.get('sma_momentum_ratio')),
                bar.get('sma_momentum_label'),
                _safe_float(bar.get('vol_roc')), _safe_float(bar.get('vol_delta')),
                _safe_float(bar.get('cvd_slope')),
                bar.get('h4_structure'), bar.get('h1_structure'),
                bar.get('m15_structure'), bar.get('m5_structure'), bar.get('m1_structure'),
                _safe_int(bar.get('health_score')),
                _safe_float(bar.get('candle_range_pct')),
                _safe_int(bar.get('long_score')), _safe_int(bar.get('short_score')),
                comp_scores['structure_score'], comp_scores['volume_score'], comp_scores['price_score'],
            ))
            self.conn.commit()

        self._log(f"  [{trade_id}] Entry indicators saved (health={bar.get('health_score')}, bar={bar['bar_time']})")
        return True


# =============================================================================
# 2. MFE/MAE PROCESSOR
# =============================================================================

class JournalMFEMAEProcessor(BaseTrainingProcessor):
    """
    Calculates MFE/MAE in R-multiples by walking M1 bars from entry to exit.
    """

    TARGET_TABLE = "journal_mfe_mae_potential"

    def process_all(self, trade_id: str = None, trade_date: date = None, dry_run: bool = False) -> Dict:
        trades = self._fetch_eligible_trades(trade_id, trade_date)
        stats = {'processed': 0, 'skipped': 0, 'errors': []}
        self._log(f"MFE/MAE: {len(trades)} eligible trades")

        for trade in trades:
            try:
                result = self._process_one(trade, dry_run)
                if result:
                    stats['processed'] += 1
                else:
                    stats['skipped'] += 1
            except Exception as e:
                stats['errors'].append(f"{trade['trade_id']}: {e}")
                self._log(f"Error {trade['trade_id']}: {e}", 'error')

        self._log(f"MFE/MAE: {stats['processed']} processed, {stats['skipped']} skipped, {len(stats['errors'])} errors")
        return stats

    def _process_one(self, trade: Dict, dry_run: bool = False) -> bool:
        trade_id = trade['trade_id']
        ticker = trade['symbol']
        trade_date = trade['trade_date']
        entry_time = trade['entry_time']
        exit_time = trade['exit_time']
        entry_price = float(trade['entry_price'])
        stop_price = float(trade['stop_price'])
        direction = trade['direction'].upper()

        if exit_time is None:
            self._log(f"  [{trade_id}] No exit_time, skipping", 'warning')
            return False

        stop_distance = abs(entry_price - stop_price)
        if stop_distance <= 0:
            self._log(f"  [{trade_id}] Zero stop distance, skipping", 'warning')
            return False

        # Fetch M1 bars from entry to exit
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT bar_time, open, high, low, close, volume
                FROM journal_m1_bars
                WHERE ticker = %s AND bar_date = %s
                  AND bar_time >= %s AND bar_time <= %s
                ORDER BY bar_time ASC
            """, (ticker, trade_date, entry_time, exit_time))
            bars = cur.fetchall()

        if not bars:
            self._log(f"  [{trade_id}] No M1 bars found between entry/exit", 'warning')
            return False

        # Walk bars to find MFE/MAE
        is_long = direction == 'LONG'
        mfe_price = entry_price
        mfe_time = entry_time
        mfe_bar_idx = 0
        mae_price = entry_price
        mae_time = entry_time
        mae_bar_idx = 0

        for i, bar in enumerate(bars):
            if is_long:
                if float(bar['high']) > mfe_price:
                    mfe_price = float(bar['high'])
                    mfe_time = bar['bar_time']
                    mfe_bar_idx = i
                if float(bar['low']) < mae_price:
                    mae_price = float(bar['low'])
                    mae_time = bar['bar_time']
                    mae_bar_idx = i
            else:
                if float(bar['low']) < mfe_price:
                    mfe_price = float(bar['low'])
                    mfe_time = bar['bar_time']
                    mfe_bar_idx = i
                if float(bar['high']) > mae_price:
                    mae_price = float(bar['high'])
                    mae_time = bar['bar_time']
                    mae_bar_idx = i

        # Calculate R-multiples
        mfe_r = abs(mfe_price - entry_price) / stop_distance
        mae_r = abs(mae_price - entry_price) / stop_distance
        temporal_win = mfe_time < mae_time if mfe_time and mae_time else None

        if dry_run:
            self._log(f"  [{trade_id}] Would insert MFE={mfe_r:.2f}R MAE={mae_r:.2f}R ({len(bars)} bars)")
            return True

        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO journal_mfe_mae_potential (
                    trade_id, trade_date, ticker, direction, entry_time, entry_price,
                    exit_time, exit_price, stop_price, stop_distance,
                    mfe_r, mfe_price, mfe_time, mfe_bar_index,
                    mae_r, mae_price, mae_time, mae_bar_index,
                    temporal_win, bars_analyzed, calculated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, NOW()
                )
                ON CONFLICT (trade_id) DO UPDATE SET
                    mfe_r = EXCLUDED.mfe_r, mfe_price = EXCLUDED.mfe_price,
                    mfe_time = EXCLUDED.mfe_time, mfe_bar_index = EXCLUDED.mfe_bar_index,
                    mae_r = EXCLUDED.mae_r, mae_price = EXCLUDED.mae_price,
                    mae_time = EXCLUDED.mae_time, mae_bar_index = EXCLUDED.mae_bar_index,
                    temporal_win = EXCLUDED.temporal_win, bars_analyzed = EXCLUDED.bars_analyzed,
                    calculated_at = NOW()
            """, (
                trade_id, trade_date, ticker, direction, entry_time, entry_price,
                exit_time, _safe_float(trade.get('exit_price')), stop_price, stop_distance,
                round(mfe_r, 4), mfe_price, mfe_time, mfe_bar_idx,
                round(mae_r, 4), mae_price, mae_time, mae_bar_idx,
                temporal_win, len(bars),
            ))
            self.conn.commit()

        self._log(f"  [{trade_id}] MFE={mfe_r:.2f}R MAE={mae_r:.2f}R ({len(bars)} bars)")
        return True


# =============================================================================
# 3. R-LEVELS PROCESSOR
# =============================================================================

class JournalRLevelsProcessor(BaseTrainingProcessor):
    """
    Calculates R-level prices and tracks which levels were hit.
    Uses the user-set stop_price from journal_trades.
    """

    TARGET_TABLE = "journal_r_levels"

    def process_all(self, trade_id: str = None, trade_date: date = None, dry_run: bool = False) -> Dict:
        trades = self._fetch_eligible_trades(trade_id, trade_date)
        stats = {'processed': 0, 'skipped': 0, 'errors': []}
        self._log(f"R-Levels: {len(trades)} eligible trades")

        for trade in trades:
            try:
                result = self._process_one(trade, dry_run)
                if result:
                    stats['processed'] += 1
                else:
                    stats['skipped'] += 1
            except Exception as e:
                stats['errors'].append(f"{trade['trade_id']}: {e}")
                self._log(f"Error {trade['trade_id']}: {e}", 'error')

        self._log(f"R-Levels: {stats['processed']} processed, {stats['skipped']} skipped, {len(stats['errors'])} errors")
        return stats

    def _process_one(self, trade: Dict, dry_run: bool = False) -> bool:
        trade_id = trade['trade_id']
        ticker = trade['symbol']
        trade_date = trade['trade_date']
        entry_time = trade['entry_time']
        exit_time = trade['exit_time']
        entry_price = float(trade['entry_price'])
        stop_price = float(trade['stop_price'])
        direction = trade['direction'].upper()

        if exit_time is None:
            return False

        stop_distance = abs(entry_price - stop_price)
        if stop_distance <= 0:
            return False

        is_long = direction == 'LONG'

        # Calculate R-level prices
        if is_long:
            r1_price = entry_price + stop_distance
            r2_price = entry_price + 2 * stop_distance
            r3_price = entry_price + 3 * stop_distance
        else:
            r1_price = entry_price - stop_distance
            r2_price = entry_price - 2 * stop_distance
            r3_price = entry_price - 3 * stop_distance

        # Fetch M1 bars from entry to exit
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT bar_time, open, high, low, close, volume
                FROM journal_m1_bars
                WHERE ticker = %s AND bar_date = %s
                  AND bar_time >= %s AND bar_time <= %s
                ORDER BY bar_time ASC
            """, (ticker, trade_date, entry_time, exit_time))
            bars = cur.fetchall()

        if not bars:
            return False

        # Walk bars to track R-level crossings and stop hits
        r1_hit = False
        r1_hit_time = None
        r1_hit_bar_idx = None
        r2_hit = False
        r2_hit_time = None
        r2_hit_bar_idx = None
        r3_hit = False
        r3_hit_time = None
        r3_hit_bar_idx = None
        stop_hit = False
        stop_hit_time = None
        max_r = 0.0

        for i, bar in enumerate(bars):
            bar_high = float(bar['high'])
            bar_low = float(bar['low'])
            bar_close = float(bar['close'])

            if is_long:
                # R-levels (price-based: high touches)
                if not r1_hit and bar_high >= r1_price:
                    r1_hit = True
                    r1_hit_time = bar['bar_time']
                    r1_hit_bar_idx = i
                if not r2_hit and bar_high >= r2_price:
                    r2_hit = True
                    r2_hit_time = bar['bar_time']
                    r2_hit_bar_idx = i
                if not r3_hit and bar_high >= r3_price:
                    r3_hit = True
                    r3_hit_time = bar['bar_time']
                    r3_hit_bar_idx = i
                # Stop (close-based)
                if not stop_hit and bar_close <= stop_price:
                    stop_hit = True
                    stop_hit_time = bar['bar_time']
                # Max R achieved
                current_r = (bar_high - entry_price) / stop_distance
                max_r = max(max_r, current_r)
            else:
                # R-levels (price-based: low touches)
                if not r1_hit and bar_low <= r1_price:
                    r1_hit = True
                    r1_hit_time = bar['bar_time']
                    r1_hit_bar_idx = i
                if not r2_hit and bar_low <= r2_price:
                    r2_hit = True
                    r2_hit_time = bar['bar_time']
                    r2_hit_bar_idx = i
                if not r3_hit and bar_low <= r3_price:
                    r3_hit = True
                    r3_hit_time = bar['bar_time']
                    r3_hit_bar_idx = i
                # Stop (close-based)
                if not stop_hit and bar_close >= stop_price:
                    stop_hit = True
                    stop_hit_time = bar['bar_time']
                # Max R achieved
                current_r = (entry_price - bar_low) / stop_distance
                max_r = max(max_r, current_r)

        # Calculate outcome
        exit_price = _safe_float(trade.get('exit_price'))
        if exit_price is not None:
            if is_long:
                pnl_r = (exit_price - entry_price) / stop_distance
            else:
                pnl_r = (entry_price - exit_price) / stop_distance
        else:
            pnl_r = None

        is_winner = pnl_r is not None and pnl_r > 0
        outcome = 'WIN' if is_winner else 'LOSS'

        if dry_run:
            self._log(f"  [{trade_id}] Would insert R-levels: R1={'HIT' if r1_hit else 'miss'} R2={'HIT' if r2_hit else 'miss'} R3={'HIT' if r3_hit else 'miss'}")
            return True

        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO journal_r_levels (
                    trade_id, trade_date, ticker, direction, entry_price, stop_price, stop_distance,
                    r1_price, r2_price, r3_price,
                    r1_hit, r1_hit_time, r1_hit_bar_index,
                    r2_hit, r2_hit_time, r2_hit_bar_index,
                    r3_hit, r3_hit_time, r3_hit_bar_index,
                    stop_hit, stop_hit_time,
                    max_r_achieved, pnl_r, outcome, is_winner,
                    bars_analyzed, calculated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s,
                    %s, %s, %s, %s,
                    %s, NOW()
                )
                ON CONFLICT (trade_id) DO UPDATE SET
                    r1_price = EXCLUDED.r1_price, r2_price = EXCLUDED.r2_price, r3_price = EXCLUDED.r3_price,
                    r1_hit = EXCLUDED.r1_hit, r1_hit_time = EXCLUDED.r1_hit_time, r1_hit_bar_index = EXCLUDED.r1_hit_bar_index,
                    r2_hit = EXCLUDED.r2_hit, r2_hit_time = EXCLUDED.r2_hit_time, r2_hit_bar_index = EXCLUDED.r2_hit_bar_index,
                    r3_hit = EXCLUDED.r3_hit, r3_hit_time = EXCLUDED.r3_hit_time, r3_hit_bar_index = EXCLUDED.r3_hit_bar_index,
                    stop_hit = EXCLUDED.stop_hit, stop_hit_time = EXCLUDED.stop_hit_time,
                    max_r_achieved = EXCLUDED.max_r_achieved, pnl_r = EXCLUDED.pnl_r,
                    outcome = EXCLUDED.outcome, is_winner = EXCLUDED.is_winner,
                    bars_analyzed = EXCLUDED.bars_analyzed, calculated_at = NOW()
            """, (
                trade_id, trade_date, ticker, direction, entry_price, stop_price, round(stop_distance, 4),
                round(r1_price, 4), round(r2_price, 4), round(r3_price, 4),
                r1_hit, r1_hit_time, r1_hit_bar_idx,
                r2_hit, r2_hit_time, r2_hit_bar_idx,
                r3_hit, r3_hit_time, r3_hit_bar_idx,
                stop_hit, stop_hit_time,
                round(max_r, 4), round(pnl_r, 4) if pnl_r is not None else None,
                outcome, is_winner,
                len(bars),
            ))
            self.conn.commit()

        self._log(f"  [{trade_id}] R-levels: R1={'HIT' if r1_hit else 'miss'} R2={'HIT' if r2_hit else 'miss'} R3={'HIT' if r3_hit else 'miss'} maxR={max_r:.2f}")
        return True


# =============================================================================
# 4. OPTIMAL TRADE PROCESSOR
# =============================================================================

class JournalOptimalTradeProcessor(BaseTrainingProcessor):
    """
    Creates indicator snapshots at critical trade events.
    Depends on journal_mfe_mae_potential and journal_r_levels being populated first.
    """

    TARGET_TABLE = "journal_optimal_trade"

    def process_all(self, trade_id: str = None, trade_date: date = None, dry_run: bool = False) -> Dict:
        trades = self._fetch_eligible_trades(trade_id, trade_date)
        stats = {'processed': 0, 'skipped': 0, 'events_created': 0, 'errors': []}
        self._log(f"Optimal Trade: {len(trades)} eligible trades")

        for trade in trades:
            try:
                events = self._process_one(trade, dry_run)
                if events > 0:
                    stats['processed'] += 1
                    stats['events_created'] += events
                else:
                    stats['skipped'] += 1
            except Exception as e:
                stats['errors'].append(f"{trade['trade_id']}: {e}")
                self._log(f"Error {trade['trade_id']}: {e}", 'error')

        self._log(f"Optimal Trade: {stats['processed']} processed, {stats['events_created']} events, {len(stats['errors'])} errors")
        return stats

    def _process_one(self, trade: Dict, dry_run: bool = False) -> int:
        """Process a single trade. Returns number of events created."""
        trade_id = trade['trade_id']
        ticker = trade['symbol']
        trade_date = trade['trade_date']
        entry_time = trade['entry_time']
        exit_time = trade['exit_time']
        entry_price = float(trade['entry_price'])
        direction = trade['direction'].upper()
        model = trade.get('model')
        is_long = direction == 'LONG'

        # Fetch MFE/MAE data
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM journal_mfe_mae_potential WHERE trade_id = %s", (trade_id,))
            mfe_mae = cur.fetchone()

        # Fetch R-levels data
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM journal_r_levels WHERE trade_id = %s", (trade_id,))
            r_levels = cur.fetchone()

        if not mfe_mae or not r_levels:
            self._log(f"  [{trade_id}] Missing MFE/MAE or R-levels, skipping", 'warning')
            return 0

        # Fetch entry health for delta calculation
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT health_score FROM journal_entry_indicators WHERE trade_id = %s", (trade_id,))
            entry_ind = cur.fetchone()
        entry_health = _safe_int(entry_ind['health_score']) if entry_ind else None

        win = 1 if mfe_mae.get('temporal_win') else 0

        # Build event list
        events = []

        # ENTRY event
        events.append(('ENTRY', entry_time, entry_price, 0))

        # MFE event
        if mfe_mae.get('mfe_time'):
            events.append(('MFE', mfe_mae['mfe_time'], float(mfe_mae['mfe_price']), _safe_int(mfe_mae.get('mfe_bar_index')) or 0))

        # MAE event
        if mfe_mae.get('mae_time'):
            events.append(('MAE', mfe_mae['mae_time'], float(mfe_mae['mae_price']), _safe_int(mfe_mae.get('mae_bar_index')) or 0))

        # EXIT event
        if exit_time and trade.get('exit_price'):
            events.append(('EXIT', exit_time, float(trade['exit_price']), None))

        # R-level crossing events
        if r_levels.get('r1_hit') and r_levels.get('r1_hit_time'):
            events.append(('R1_CROSS', r_levels['r1_hit_time'], float(r_levels['r1_price']), _safe_int(r_levels.get('r1_hit_bar_index'))))
        if r_levels.get('r2_hit') and r_levels.get('r2_hit_time'):
            events.append(('R2_CROSS', r_levels['r2_hit_time'], float(r_levels['r2_price']), _safe_int(r_levels.get('r2_hit_bar_index'))))
        if r_levels.get('r3_hit') and r_levels.get('r3_hit_time'):
            events.append(('R3_CROSS', r_levels['r3_hit_time'], float(r_levels['r3_price']), _safe_int(r_levels.get('r3_hit_bar_index'))))

        if dry_run:
            self._log(f"  [{trade_id}] Would insert {len(events)} events: {[e[0] for e in events]}")
            return len(events)

        # For each event, snapshot indicators from journal_m1_indicator_bars
        event_count = 0
        for event_type, event_time, event_price, bars_from_entry in events:
            bar = self._get_indicator_bar(ticker, trade_date, event_time)

            # Calculate points at event
            if is_long:
                points = event_price - entry_price
            else:
                points = entry_price - event_price

            # Health delta
            event_health = _safe_int(bar.get('health_score')) if bar else None
            health_delta = None
            if event_health is not None and entry_health is not None:
                health_delta = event_health - entry_health

            # Calculate bars_from_entry if not provided
            if bars_from_entry is None and event_time and entry_time:
                # Approximate: count M1 bars between entry and event
                with self.conn.cursor() as cur:
                    cur.execute("""
                        SELECT COUNT(*) FROM journal_m1_bars
                        WHERE ticker = %s AND bar_date = %s
                          AND bar_time > %s AND bar_time <= %s
                    """, (ticker, trade_date, entry_time, event_time))
                    bars_from_entry = cur.fetchone()[0]

            # Component scores
            comp_scores = _calculate_component_scores(bar, direction) if bar else {'structure_score': None, 'volume_score': None, 'price_score': None}
            healthy_flags = _calculate_healthy_flags(bar, direction) if bar else {}

            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO journal_optimal_trade (
                        trade_id, event_type, trade_date, ticker, direction, model, win,
                        event_time, bars_from_entry, entry_price, price_at_event, points_at_event,
                        health_score, health_label, health_delta, health_summary,
                        structure_score, volume_score, price_score,
                        vwap, sma9, sma21, sma_spread, sma_momentum_ratio, sma_momentum_label,
                        vol_roc, vol_delta, cvd_slope,
                        m1_structure, m15_structure, h1_structure, h4_structure,
                        sma_alignment_healthy, sma_momentum_healthy, vwap_healthy,
                        vol_roc_healthy, vol_delta_healthy, cvd_slope_healthy,
                        calculated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, %s, %s,
                        NOW()
                    )
                    ON CONFLICT (trade_id, event_type) DO UPDATE SET
                        event_time = EXCLUDED.event_time,
                        bars_from_entry = EXCLUDED.bars_from_entry,
                        price_at_event = EXCLUDED.price_at_event,
                        points_at_event = EXCLUDED.points_at_event,
                        health_score = EXCLUDED.health_score,
                        health_label = EXCLUDED.health_label,
                        health_delta = EXCLUDED.health_delta,
                        health_summary = EXCLUDED.health_summary,
                        structure_score = EXCLUDED.structure_score,
                        volume_score = EXCLUDED.volume_score,
                        price_score = EXCLUDED.price_score,
                        vwap = EXCLUDED.vwap, sma9 = EXCLUDED.sma9, sma21 = EXCLUDED.sma21,
                        sma_spread = EXCLUDED.sma_spread,
                        sma_momentum_ratio = EXCLUDED.sma_momentum_ratio,
                        sma_momentum_label = EXCLUDED.sma_momentum_label,
                        vol_roc = EXCLUDED.vol_roc, vol_delta = EXCLUDED.vol_delta,
                        cvd_slope = EXCLUDED.cvd_slope,
                        m1_structure = EXCLUDED.m1_structure,
                        m15_structure = EXCLUDED.m15_structure,
                        h1_structure = EXCLUDED.h1_structure,
                        h4_structure = EXCLUDED.h4_structure,
                        sma_alignment_healthy = EXCLUDED.sma_alignment_healthy,
                        sma_momentum_healthy = EXCLUDED.sma_momentum_healthy,
                        vwap_healthy = EXCLUDED.vwap_healthy,
                        vol_roc_healthy = EXCLUDED.vol_roc_healthy,
                        vol_delta_healthy = EXCLUDED.vol_delta_healthy,
                        cvd_slope_healthy = EXCLUDED.cvd_slope_healthy,
                        calculated_at = NOW()
                """, (
                    trade_id, event_type, trade_date, ticker, direction, model, win,
                    event_time, bars_from_entry, entry_price, event_price, round(points, 4),
                    event_health, _health_label(event_health), health_delta, _health_summary(health_delta),
                    comp_scores.get('structure_score'), comp_scores.get('volume_score'), comp_scores.get('price_score'),
                    _safe_float(bar.get('vwap')) if bar else None,
                    _safe_float(bar.get('sma9')) if bar else None,
                    _safe_float(bar.get('sma21')) if bar else None,
                    _safe_float(bar.get('sma_spread')) if bar else None,
                    _safe_float(bar.get('sma_momentum_ratio')) if bar else None,
                    bar.get('sma_momentum_label') if bar else None,
                    _safe_float(bar.get('vol_roc')) if bar else None,
                    _safe_float(bar.get('vol_delta')) if bar else None,
                    _safe_float(bar.get('cvd_slope')) if bar else None,
                    bar.get('m1_structure') if bar else None,
                    bar.get('m15_structure') if bar else None,
                    bar.get('h1_structure') if bar else None,
                    bar.get('h4_structure') if bar else None,
                    healthy_flags.get('sma_alignment_healthy'),
                    healthy_flags.get('sma_momentum_healthy'),
                    healthy_flags.get('vwap_healthy'),
                    healthy_flags.get('vol_roc_healthy'),
                    healthy_flags.get('vol_delta_healthy'),
                    healthy_flags.get('cvd_slope_healthy'),
                ))
                self.conn.commit()
            event_count += 1

        self._log(f"  [{trade_id}] {event_count} events: {[e[0] for e in events]}")
        return event_count

    def _get_indicator_bar(self, ticker: str, trade_date: date, event_time: time) -> Optional[Dict]:
        """Get the indicator bar at or just before event_time."""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM journal_m1_indicator_bars
                WHERE ticker = %s AND bar_date = %s AND bar_time <= %s
                ORDER BY bar_time DESC
                LIMIT 1
            """, (ticker, trade_date, event_time))
            return cur.fetchone()
