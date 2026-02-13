"""
Data access layer for Notion page generation.

Follows the same psycopg2 + RealDictCursor + context manager pattern as
08_journal/data/journal_db.py. READ-ONLY — no writes to any table.

Primary tables:
  - journal_trades          (trade data from CSV imports)
  - journal_m1_indicator_bars (M1 bars with pre-calculated indicators)
  - zones + setups          (zone context, LEFT JOIN for setup_type)
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import date, time, timedelta
from typing import List, Optional, Dict, Tuple
from decimal import Decimal
import logging

from .config import DB_CONFIG

logger = logging.getLogger(__name__)


class NotionDataFetcher:
    """
    All Supabase read queries needed for Notion trade journal pages.

    Usage:
        with NotionDataFetcher() as fetcher:
            trade = fetcher.fetch_trade("SPY_012826_JRNL_1417")
            entry_bar = fetcher.fetch_entry_indicator_bar("SPY", date(2026,1,28), time(14,17))
    """

    def __init__(self):
        self.conn = None

    def connect(self) -> bool:
        """Establish database connection."""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            logger.info("NotionDataFetcher connected to Supabase")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            return False

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _ensure_connected(self):
        """Ensure we have an active connection."""
        if not self.conn or self.conn.closed:
            self.connect()

    # =========================================================================
    # CORE TRADE DATA (from journal_trades)
    # =========================================================================

    def fetch_trade(self, trade_id: str) -> Optional[Dict]:
        """Fetch single trade by trade_id."""
        self._ensure_connected()
        query = "SELECT * FROM journal_trades WHERE trade_id = %s"
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (trade_id,))
                row = cur.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error fetching trade {trade_id}: {e}")
            return None

    def fetch_trades_by_date(self, trade_date: date) -> List[Dict]:
        """Fetch all trades for a given date, ordered by entry_time."""
        self._ensure_connected()
        query = """
            SELECT * FROM journal_trades
            WHERE trade_date = %s
            ORDER BY entry_time
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (trade_date,))
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching trades for {trade_date}: {e}")
            return []

    def fetch_trades_by_range(self, date_from: date, date_to: date) -> List[Dict]:
        """Fetch trades within date range (inclusive), ordered by date + time."""
        self._ensure_connected()
        query = """
            SELECT * FROM journal_trades
            WHERE trade_date >= %s AND trade_date <= %s
            ORDER BY trade_date, entry_time
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (date_from, date_to))
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching trades for {date_from} to {date_to}: {e}")
            return []

    # =========================================================================
    # NOTION SYNC STATUS
    # =========================================================================

    def fetch_unsynced_trades(self, up_to_date: date = None) -> List[Dict]:
        """Fetch trades needing Notion sync (notion_page_id IS NULL)."""
        self._ensure_connected()
        if up_to_date is None:
            from datetime import date as date_cls
            up_to_date = date_cls.today()
        query = """
            SELECT * FROM journal_trades
            WHERE notion_page_id IS NULL
              AND trade_date <= %s
            ORDER BY trade_date, entry_time
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (up_to_date,))
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching unsynced trades: {e}")
            return []

    def fetch_stale_synced_trades(self) -> List[Dict]:
        """
        Fetch trades pushed to Notion but whose data changed since last sync.
        These need a notion-update-page call to refresh content.
        """
        self._ensure_connected()
        query = """
            SELECT * FROM journal_trades
            WHERE notion_page_id IS NOT NULL
              AND updated_at > notion_synced_at
            ORDER BY trade_date, entry_time
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query)
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching stale synced trades: {e}")
            return []

    def fetch_sync_stats(self) -> Dict:
        """
        Return sync status counts for the status summary display.
        Returns dict with: total, synced, unsynced, stale
        """
        self._ensure_connected()
        query = """
            SELECT
                COUNT(*) as total,
                COUNT(notion_page_id) as synced,
                COUNT(*) - COUNT(notion_page_id) as unsynced,
                COUNT(*) FILTER (
                    WHERE notion_page_id IS NOT NULL
                    AND updated_at > notion_synced_at
                ) as stale
            FROM journal_trades
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query)
                row = cur.fetchone()
                return dict(row) if row else {'total': 0, 'synced': 0, 'unsynced': 0, 'stale': 0}
        except Exception as e:
            logger.error(f"Error fetching sync stats: {e}")
            return {'total': 0, 'synced': 0, 'unsynced': 0, 'stale': 0}

    # =========================================================================
    # INDICATOR BAR AT ENTRY TIME
    # =========================================================================

    def fetch_entry_indicator_bar(
        self, ticker: str, trade_date: date, entry_time: time
    ) -> Optional[Dict]:
        """
        Get the journal_m1_indicator_bars row at or just before entry_time.
        This is the indicator snapshot at the moment of entry.
        """
        self._ensure_connected()
        query = """
            SELECT * FROM journal_m1_indicator_bars
            WHERE ticker = %s AND bar_date = %s AND bar_time <= %s
            ORDER BY bar_time DESC
            LIMIT 1
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (ticker.upper(), trade_date, entry_time))
                row = cur.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error fetching entry bar for {ticker} on {trade_date}: {e}")
            return None

    # =========================================================================
    # M1 RAMP-UP BARS (before entry)
    # =========================================================================

    def fetch_ramp_up_bars(
        self, ticker: str, trade_date: date, entry_time: time, count: int = 15
    ) -> List[Dict]:
        """
        Fetch M1 indicator bars BEFORE entry for ramp-up display.
        Returns chronological order (oldest first).
        """
        self._ensure_connected()
        query = """
            SELECT * FROM journal_m1_indicator_bars
            WHERE ticker = %s AND bar_date = %s AND bar_time < %s
            ORDER BY bar_time DESC
            LIMIT %s
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (ticker.upper(), trade_date, entry_time, count))
                rows = [dict(row) for row in cur.fetchall()]
                rows.reverse()  # chronological order
                return rows
        except Exception as e:
            logger.error(f"Error fetching ramp-up bars for {ticker}: {e}")
            return []

    # =========================================================================
    # ZONE DATA
    # =========================================================================

    def fetch_zone_data(
        self, zone_id: str, ticker: str, trade_date: date
    ) -> Optional[Dict]:
        """
        Fetch zone + setup_type for a specific zone_id.
        Uses the same LEFT JOIN pattern as JournalDB.get_zones_for_ticker.
        """
        self._ensure_connected()
        query = """
            SELECT z.zone_id, z.ticker, z.date, z.zone_high, z.zone_low,
                   z.hvn_poc, z.direction, z.rank, z.score, z.is_filtered,
                   s.setup_type
            FROM zones z
            LEFT JOIN setups s
                ON z.date = s.date AND z.zone_id = s.zone_id
            WHERE z.zone_id = %s AND z.ticker = %s AND z.date = %s
            LIMIT 1
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (zone_id, ticker.upper(), trade_date))
                row = cur.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error fetching zone {zone_id}: {e}")
            return None

    # =========================================================================
    # TRADE REVIEW DATA (from journal_trade_reviews)
    # =========================================================================

    def fetch_trade_review(self, trade_id: str) -> Optional[Dict]:
        """
        Fetch the flashcard review for a trade from journal_trade_reviews.
        Returns None if no review exists.
        """
        self._ensure_connected()
        query = "SELECT * FROM journal_trade_reviews WHERE trade_id = %s"
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (trade_id,))
                row = cur.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error fetching review for {trade_id}: {e}")
            return None

    # =========================================================================
    # BARS BETWEEN ENTRY AND EXIT (for MFE/MAE calculation)
    # =========================================================================

    def fetch_bars_between(
        self, ticker: str, trade_date: date,
        entry_time: time, exit_time: time
    ) -> List[Dict]:
        """
        Fetch journal_m1_indicator_bars from entry to exit (inclusive).
        Used for MFE/MAE and R-level calculations.
        """
        self._ensure_connected()
        query = """
            SELECT * FROM journal_m1_indicator_bars
            WHERE ticker = %s AND bar_date = %s
              AND bar_time >= %s AND bar_time <= %s
            ORDER BY bar_time
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (ticker.upper(), trade_date, entry_time, exit_time))
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching bars between {entry_time}-{exit_time}: {e}")
            return []

    # =========================================================================
    # MFE / MAE CALCULATION (from journal bars)
    # =========================================================================

    def calculate_mfe_mae(self, trade: Dict) -> Optional[Dict]:
        """
        Calculate Maximum Favorable/Adverse Excursion from journal M1 bars.

        Requires: stop_price, entry_price, exit_time, direction.
        Returns dict with: mfe_r, mfe_price, mfe_time, mae_r, mae_price, mae_time,
                           mfe_before_mae, duration_minutes, efficiency_pct
        Returns None if stop_price is not set or no bars found.
        """
        stop_price = trade.get('stop_price')
        entry_price = trade.get('entry_price')
        exit_time = trade.get('exit_time')
        entry_time = trade.get('entry_time')
        direction = trade.get('direction', '').upper()
        ticker = trade.get('symbol', '')
        trade_date = trade.get('trade_date')

        if not all([stop_price, entry_price, exit_time, entry_time, direction, ticker, trade_date]):
            return None

        entry_price = float(entry_price)
        stop_price = float(stop_price)
        stop_distance = abs(entry_price - stop_price)
        if stop_distance == 0:
            return None

        # Use exit_time if available, otherwise use 15:30 (EOD)
        end_time = exit_time if exit_time else time(15, 30)

        bars = self.fetch_bars_between(ticker, trade_date, entry_time, end_time)
        if not bars:
            return None

        # Walk bars to find MFE and MAE
        mfe_price = entry_price
        mae_price = entry_price
        mfe_time = entry_time
        mae_time = entry_time
        mfe_bar_idx = 0
        mae_bar_idx = 0

        for i, bar in enumerate(bars):
            high = float(bar.get('high', entry_price))
            low = float(bar.get('low', entry_price))
            bar_time = bar.get('bar_time')

            if direction == 'LONG':
                if high > mfe_price:
                    mfe_price = high
                    mfe_time = bar_time
                    mfe_bar_idx = i
                if low < mae_price:
                    mae_price = low
                    mae_time = bar_time
                    mae_bar_idx = i
            else:  # SHORT
                if low < mfe_price:
                    mfe_price = low
                    mfe_time = bar_time
                    mfe_bar_idx = i
                if high > mae_price:
                    mae_price = high
                    mae_time = bar_time
                    mae_bar_idx = i

        # Calculate R-multiples
        if direction == 'LONG':
            mfe_r = (mfe_price - entry_price) / stop_distance
            mae_r = (entry_price - mae_price) / stop_distance
        else:
            mfe_r = (entry_price - mfe_price) / stop_distance
            mae_r = (mae_price - entry_price) / stop_distance

        # MFE before MAE?
        mfe_before_mae = mfe_bar_idx <= mae_bar_idx

        # Duration in minutes
        duration_minutes = None
        if entry_time and exit_time:
            try:
                from datetime import datetime as dt
                entry_dt = dt.combine(date.today(), entry_time)
                exit_dt = dt.combine(date.today(), exit_time)
                duration_minutes = int((exit_dt - entry_dt).total_seconds() / 60)
            except Exception:
                pass

        # Edge efficiency: actual R / MFE R * 100
        pnl_r = trade.get('pnl_r')
        efficiency_pct = None
        if pnl_r is not None and mfe_r > 0:
            efficiency_pct = round(float(pnl_r) / mfe_r * 100, 1)

        return {
            'mfe_r': round(mfe_r, 2),
            'mfe_price': round(mfe_price, 4),
            'mfe_time': mfe_time,
            'mfe_bars': mfe_bar_idx,
            'mae_r': round(mae_r, 2),
            'mae_price': round(mae_price, 4),
            'mae_time': mae_time,
            'mae_bars': mae_bar_idx,
            'mfe_before_mae': mfe_before_mae,
            'duration_minutes': duration_minutes,
            'efficiency_pct': efficiency_pct,
        }

    # =========================================================================
    # R-LEVEL EVENT CALCULATION (from journal bars)
    # =========================================================================

    def calculate_r_level_events(self, trade: Dict) -> List[Dict]:
        """
        Walk M1 bars and detect R1, R2, R3 crossings + MFE/MAE events.

        Returns list of events: [
            {event_type, time, price, r_multiple, health_score, health_delta, status}
        ]

        Requires stop_price to calculate R-levels. Returns empty list if not set.
        """
        stop_price = trade.get('stop_price')
        entry_price = trade.get('entry_price')
        exit_time = trade.get('exit_time')
        exit_price = trade.get('exit_price')
        entry_time = trade.get('entry_time')
        direction = trade.get('direction', '').upper()
        ticker = trade.get('symbol', '')
        trade_date = trade.get('trade_date')

        if not all([stop_price, entry_price, entry_time, direction, ticker, trade_date]):
            return []

        entry_price = float(entry_price)
        stop_price = float(stop_price)
        stop_distance = abs(entry_price - stop_price)
        if stop_distance == 0:
            return []

        # Calculate R-level prices
        if direction == 'LONG':
            r1_price = entry_price + stop_distance
            r2_price = entry_price + 2 * stop_distance
            r3_price = entry_price + 3 * stop_distance
        else:
            r1_price = entry_price - stop_distance
            r2_price = entry_price - 2 * stop_distance
            r3_price = entry_price - 3 * stop_distance

        end_time = exit_time if exit_time else time(15, 30)
        bars = self.fetch_bars_between(ticker, trade_date, entry_time, end_time)
        if not bars:
            return []

        events = []
        r1_hit = False
        r2_hit = False
        r3_hit = False
        prev_health = None

        # Track MFE/MAE
        mfe_price = entry_price
        mae_price = entry_price
        mfe_time = entry_time
        mae_time = entry_time
        mfe_health = None
        mae_health = None

        # ENTRY event (first bar)
        first_bar = bars[0] if bars else None
        entry_health = int(first_bar.get('health_score', 0)) if first_bar and first_bar.get('health_score') is not None else None
        events.append({
            'event_type': 'ENTRY',
            'time': entry_time,
            'price': entry_price,
            'r_multiple': 0.0,
            'health_score': entry_health,
            'health_delta': None,
            'status': _health_status(None),
        })
        prev_health = entry_health

        for bar in bars:
            high = float(bar.get('high', entry_price))
            low = float(bar.get('low', entry_price))
            bar_time = bar.get('bar_time')
            health = int(bar.get('health_score', 0)) if bar.get('health_score') is not None else None

            # Check R-level crossings
            if direction == 'LONG':
                price_check = high
                # MFE/MAE tracking
                if high > mfe_price:
                    mfe_price = high
                    mfe_time = bar_time
                    mfe_health = health
                if low < mae_price:
                    mae_price = low
                    mae_time = bar_time
                    mae_health = health

                if not r1_hit and high >= r1_price:
                    r1_hit = True
                    delta = (health - prev_health) if health is not None and prev_health is not None else None
                    events.append({
                        'event_type': 'R1',
                        'time': bar_time,
                        'price': r1_price,
                        'r_multiple': 1.0,
                        'health_score': health,
                        'health_delta': delta,
                        'status': _health_status(delta),
                    })
                    prev_health = health

                if not r2_hit and high >= r2_price:
                    r2_hit = True
                    delta = (health - prev_health) if health is not None and prev_health is not None else None
                    events.append({
                        'event_type': 'R2',
                        'time': bar_time,
                        'price': r2_price,
                        'r_multiple': 2.0,
                        'health_score': health,
                        'health_delta': delta,
                        'status': _health_status(delta),
                    })
                    prev_health = health

                if not r3_hit and high >= r3_price:
                    r3_hit = True
                    delta = (health - prev_health) if health is not None and prev_health is not None else None
                    events.append({
                        'event_type': 'R3',
                        'time': bar_time,
                        'price': r3_price,
                        'r_multiple': 3.0,
                        'health_score': health,
                        'health_delta': delta,
                        'status': _health_status(delta),
                    })
                    prev_health = health

            else:  # SHORT
                # MFE/MAE tracking
                if low < mfe_price:
                    mfe_price = low
                    mfe_time = bar_time
                    mfe_health = health
                if high > mae_price:
                    mae_price = high
                    mae_time = bar_time
                    mae_health = health

                if not r1_hit and low <= r1_price:
                    r1_hit = True
                    delta = (health - prev_health) if health is not None and prev_health is not None else None
                    events.append({
                        'event_type': 'R1',
                        'time': bar_time,
                        'price': r1_price,
                        'r_multiple': 1.0,
                        'health_score': health,
                        'health_delta': delta,
                        'status': _health_status(delta),
                    })
                    prev_health = health

                if not r2_hit and low <= r2_price:
                    r2_hit = True
                    delta = (health - prev_health) if health is not None and prev_health is not None else None
                    events.append({
                        'event_type': 'R2',
                        'time': bar_time,
                        'price': r2_price,
                        'r_multiple': 2.0,
                        'health_score': health,
                        'health_delta': delta,
                        'status': _health_status(delta),
                    })
                    prev_health = health

                if not r3_hit and low <= r3_price:
                    r3_hit = True
                    delta = (health - prev_health) if health is not None and prev_health is not None else None
                    events.append({
                        'event_type': 'R3',
                        'time': bar_time,
                        'price': r3_price,
                        'r_multiple': 3.0,
                        'health_score': health,
                        'health_delta': delta,
                        'status': _health_status(delta),
                    })
                    prev_health = health

        # MFE event
        if direction == 'LONG':
            mfe_r = (mfe_price - entry_price) / stop_distance
            mae_r = (entry_price - mae_price) / stop_distance
        else:
            mfe_r = (entry_price - mfe_price) / stop_distance
            mae_r = (mae_price - entry_price) / stop_distance

        delta = (mfe_health - prev_health) if mfe_health is not None and prev_health is not None else None
        events.append({
            'event_type': 'MFE',
            'time': mfe_time,
            'price': round(mfe_price, 4),
            'r_multiple': round(mfe_r, 2),
            'health_score': mfe_health,
            'health_delta': delta,
            'status': _health_status(delta),
        })
        prev_health = mfe_health if mfe_health is not None else prev_health

        # MAE event
        delta = (mae_health - prev_health) if mae_health is not None and prev_health is not None else None
        events.append({
            'event_type': 'MAE',
            'time': mae_time,
            'price': round(mae_price, 4),
            'r_multiple': round(-mae_r, 2),
            'health_score': mae_health,
            'health_delta': delta,
            'status': _health_status(delta),
        })
        prev_health = mae_health if mae_health is not None else prev_health

        # EXIT event
        if exit_price and exit_time:
            exit_p = float(exit_price)
            if direction == 'LONG':
                exit_r = (exit_p - entry_price) / stop_distance
            else:
                exit_r = (entry_price - exit_p) / stop_distance

            # Find health at exit time
            exit_bar = None
            for bar in reversed(bars):
                if bar.get('bar_time') and bar['bar_time'] <= exit_time:
                    exit_bar = bar
                    break
            exit_health = int(exit_bar.get('health_score', 0)) if exit_bar and exit_bar.get('health_score') is not None else None
            delta = (exit_health - prev_health) if exit_health is not None and prev_health is not None else None

            events.append({
                'event_type': 'EXIT',
                'time': exit_time,
                'price': round(exit_p, 4),
                'r_multiple': round(exit_r, 2),
                'health_score': exit_health,
                'health_delta': delta,
                'status': _health_status(delta),
            })

        # Sort by time
        events.sort(key=lambda e: e.get('time') or time(0, 0))

        return events


def _health_status(delta) -> str:
    """Classify health delta as IMPROVING / STABLE / DEGRADING."""
    if delta is None:
        return "—"
    if delta >= 2:
        return "IMPROVING"
    elif delta <= -2:
        return "DEGRADING"
    return "STABLE"
