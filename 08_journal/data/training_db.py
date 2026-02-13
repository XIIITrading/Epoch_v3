"""
Database operations for the journal training flashcard UI.

Follows JournalDB patterns (psycopg2, RealDictCursor, context manager).
Reads from the 5 journal training tables and builds JournalTradeWithMetrics objects.

Usage:
    with JournalTrainingDB() as db:
        trades = db.fetch_trades_with_metrics(date_from=..., date_to=...)
        events = db.fetch_optimal_trade_events(trade_id)
        db.upsert_review(trade_id, review_data)
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import date, time
from typing import List, Optional, Dict
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DB_CONFIG
from core.training_models import JournalTradeWithMetrics
from core.models import Trade

logger = logging.getLogger(__name__)


class JournalTrainingDB:
    """
    Database operations for training flashcard tables.

    Reads from:
        - journal_trades (trade data)
        - journal_mfe_mae_potential (MFE/MAE)
        - journal_r_levels (R-level tracking)
        - journal_entry_indicators (entry snapshot)
        - journal_optimal_trade (event indicators)
        - journal_trade_reviews (flashcard reviews)
        - zones LEFT JOIN setups (zone info)
    """

    def __init__(self):
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

    # =========================================================================
    # TRADE LOADING
    # =========================================================================

    def fetch_trade_with_metrics(self, trade_id: str) -> Optional[JournalTradeWithMetrics]:
        """Load a single trade with all metrics."""
        self._ensure_connected()

        # Fetch base trade
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM journal_trades WHERE trade_id = %s", (trade_id,))
            trade_row = cur.fetchone()

        if not trade_row:
            return None

        return self._build_trade_with_metrics(trade_row)

    def fetch_trades_with_metrics(
        self,
        date_from: date = None,
        date_to: date = None,
        ticker: str = None,
        model: str = None,
        unreviewed_only: bool = False,
        limit: int = 200,
    ) -> List[JournalTradeWithMetrics]:
        """
        Load trades with all metrics for flashcard queue.
        Only returns trades with stop_price set (training-eligible).
        """
        self._ensure_connected()

        # Build query
        conditions = ["jt.stop_price IS NOT NULL", "jt.is_closed = TRUE"]
        params = []

        if date_from:
            conditions.append("jt.trade_date >= %s")
            params.append(date_from)
        if date_to:
            conditions.append("jt.trade_date <= %s")
            params.append(date_to)
        if ticker:
            conditions.append("jt.symbol = %s")
            params.append(ticker.upper())
        if model:
            conditions.append("jt.model = %s")
            params.append(model)
        if unreviewed_only:
            conditions.append("""
                NOT EXISTS (
                    SELECT 1 FROM journal_trade_reviews jtr
                    WHERE jtr.trade_id = jt.trade_id
                )
            """)

        where = " AND ".join(conditions)
        params.append(limit)

        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(f"""
                SELECT jt.*
                FROM journal_trades jt
                WHERE {where}
                ORDER BY jt.trade_date DESC, jt.entry_time DESC
                LIMIT %s
            """, params)
            trade_rows = cur.fetchall()

        if not trade_rows:
            return []

        # Batch load all supporting data
        trade_ids = [r['trade_id'] for r in trade_rows]
        mfe_mae_map = self._batch_fetch('journal_mfe_mae_potential', trade_ids)
        r_levels_map = self._batch_fetch('journal_r_levels', trade_ids)
        entry_ind_map = self._batch_fetch('journal_entry_indicators', trade_ids)
        events_map = self._batch_fetch_events(trade_ids)
        zones_map = self._batch_fetch_zones(trade_rows)

        # Build TradeWithMetrics objects
        results = []
        for row in trade_rows:
            tid = row['trade_id']
            try:
                twm = JournalTradeWithMetrics.from_db_rows(
                    trade_row=row,
                    mfe_mae_row=mfe_mae_map.get(tid),
                    r_levels_row=r_levels_map.get(tid),
                    entry_indicators_row=entry_ind_map.get(tid),
                    optimal_events=events_map.get(tid),
                    zone_row=zones_map.get(tid),
                )
                results.append(twm)
            except Exception as e:
                logger.warning(f"Failed to build TradeWithMetrics for {tid}: {e}")

        return results

    def _build_trade_with_metrics(self, trade_row: Dict) -> JournalTradeWithMetrics:
        """Build a single JournalTradeWithMetrics from all tables."""
        trade_id = trade_row['trade_id']

        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            # MFE/MAE
            cur.execute("SELECT * FROM journal_mfe_mae_potential WHERE trade_id = %s", (trade_id,))
            mfe_mae = cur.fetchone()

            # R-Levels
            cur.execute("SELECT * FROM journal_r_levels WHERE trade_id = %s", (trade_id,))
            r_levels = cur.fetchone()

            # Entry Indicators
            cur.execute("SELECT * FROM journal_entry_indicators WHERE trade_id = %s", (trade_id,))
            entry_ind = cur.fetchone()

        # Optimal trade events
        events = self.fetch_optimal_trade_events(trade_id)

        # Zone info
        zone = self._fetch_zone_for_trade(trade_row)

        return JournalTradeWithMetrics.from_db_rows(
            trade_row=trade_row,
            mfe_mae_row=mfe_mae,
            r_levels_row=r_levels,
            entry_indicators_row=entry_ind,
            optimal_events=events,
            zone_row=zone,
        )

    # =========================================================================
    # BATCH HELPERS
    # =========================================================================

    def _batch_fetch(self, table: str, trade_ids: List[str]) -> Dict[str, Dict]:
        """Batch fetch rows from a table keyed by trade_id."""
        if not trade_ids:
            return {}
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"SELECT * FROM {table} WHERE trade_id = ANY(%s)",
                (trade_ids,)
            )
            rows = cur.fetchall()
        return {r['trade_id']: r for r in rows}

    def _batch_fetch_events(self, trade_ids: List[str]) -> Dict[str, Dict[str, Dict]]:
        """Batch fetch optimal trade events, grouped by trade_id → event_type → data."""
        if not trade_ids:
            return {}
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM journal_optimal_trade WHERE trade_id = ANY(%s) ORDER BY trade_id",
                (trade_ids,)
            )
            rows = cur.fetchall()

        result = {}
        for row in rows:
            tid = row['trade_id']
            etype = row['event_type']
            if tid not in result:
                result[tid] = {}
            result[tid][etype] = dict(row)
        return result

    def _batch_fetch_zones(self, trade_rows: List[Dict]) -> Dict[str, Dict]:
        """Batch fetch zone info for trades that have zone_id set."""
        zone_map = {}
        for row in trade_rows:
            zone_id = row.get('zone_id')
            if zone_id:
                zone = self._fetch_zone_for_trade(row)
                if zone:
                    zone_map[row['trade_id']] = zone
        return zone_map

    def _fetch_zone_for_trade(self, trade_row: Dict) -> Optional[Dict]:
        """Fetch zone data for a trade."""
        zone_id = trade_row.get('zone_id')
        ticker = trade_row.get('symbol')
        trade_date = trade_row.get('trade_date')

        if not zone_id:
            return None

        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT z.zone_id, z.zone_high, z.zone_low, z.hvn_poc,
                       z.rank, z.score, z.is_filtered,
                       s.setup_type
                FROM zones z
                LEFT JOIN setups s
                    ON z.date = s.date AND z.zone_id = s.zone_id
                WHERE z.zone_id = %s AND z.ticker = %s AND z.date = %s
                LIMIT 1
            """, (zone_id, ticker, trade_date))
            return cur.fetchone()

    # =========================================================================
    # EVENT INDICATORS
    # =========================================================================

    def fetch_optimal_trade_events(self, trade_id: str) -> Optional[Dict[str, Dict]]:
        """
        Fetch all optimal trade events for a single trade.
        Returns Dict[event_type → Dict] with all indicator columns.
        """
        self._ensure_connected()
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM journal_optimal_trade
                WHERE trade_id = %s
                ORDER BY
                    CASE event_type
                        WHEN 'ENTRY' THEN 1
                        WHEN 'R1_CROSS' THEN 2
                        WHEN 'R2_CROSS' THEN 3
                        WHEN 'R3_CROSS' THEN 4
                        WHEN 'MAE' THEN 5
                        WHEN 'MFE' THEN 6
                        WHEN 'EXIT' THEN 7
                    END
            """, (trade_id,))
            rows = cur.fetchall()

        if not rows:
            return None

        return {row['event_type']: dict(row) for row in rows}

    # =========================================================================
    # AVAILABLE OPTIONS (for sidebar filters)
    # =========================================================================

    def get_available_tickers(self, date_from: date = None) -> List[str]:
        """Get list of tickers with training-eligible trades."""
        self._ensure_connected()
        with self.conn.cursor() as cur:
            query = """
                SELECT DISTINCT symbol FROM journal_trades
                WHERE stop_price IS NOT NULL AND is_closed = TRUE
            """
            params = []
            if date_from:
                query += " AND trade_date >= %s"
                params.append(date_from)
            query += " ORDER BY symbol"
            cur.execute(query, params)
            return [row[0] for row in cur.fetchall()]

    def get_available_models(self) -> List[str]:
        """Get list of models used in training-eligible trades."""
        self._ensure_connected()
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT model FROM journal_trades
                WHERE stop_price IS NOT NULL AND model IS NOT NULL AND is_closed = TRUE
                ORDER BY model
            """)
            return [row[0] for row in cur.fetchall()]

    def get_date_range(self) -> Optional[tuple]:
        """Get min/max dates of training-eligible trades."""
        self._ensure_connected()
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT MIN(trade_date), MAX(trade_date) FROM journal_trades
                WHERE stop_price IS NOT NULL AND is_closed = TRUE
            """)
            row = cur.fetchone()
            if row and row[0]:
                return (row[0], row[1])
        return None

    # =========================================================================
    # REVIEWS
    # =========================================================================

    def fetch_review(self, trade_id: str) -> Optional[Dict]:
        """Fetch review for a trade."""
        self._ensure_connected()
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM journal_trade_reviews WHERE trade_id = %s",
                (trade_id,)
            )
            return cur.fetchone()

    def upsert_review(self, trade_id: str, review_data: Dict) -> bool:
        """Insert or update a trade review."""
        self._ensure_connected()
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO journal_trade_reviews (
                        trade_id, actual_outcome,
                        notes, notes_differently, notes_pattern, notes_observations,
                        accuracy, tape_confirmation,
                        good_trade, signal_aligned, confirmation_required,
                        prior_candle_stop, two_candle_stop, atr_stop, zone_edge_stop,
                        entry_attempt,
                        with_trend, counter_trend, stopped_by_wick,
                        reviewed_at
                    ) VALUES (
                        %s, %s,
                        %s, %s, %s, %s,
                        %s, %s,
                        %s, %s, %s,
                        %s, %s, %s, %s,
                        %s,
                        %s, %s, %s,
                        NOW()
                    )
                    ON CONFLICT (trade_id) DO UPDATE SET
                        actual_outcome = EXCLUDED.actual_outcome,
                        notes = EXCLUDED.notes,
                        notes_differently = EXCLUDED.notes_differently,
                        notes_pattern = EXCLUDED.notes_pattern,
                        notes_observations = EXCLUDED.notes_observations,
                        accuracy = EXCLUDED.accuracy,
                        tape_confirmation = EXCLUDED.tape_confirmation,
                        good_trade = EXCLUDED.good_trade,
                        signal_aligned = EXCLUDED.signal_aligned,
                        confirmation_required = EXCLUDED.confirmation_required,
                        prior_candle_stop = EXCLUDED.prior_candle_stop,
                        two_candle_stop = EXCLUDED.two_candle_stop,
                        atr_stop = EXCLUDED.atr_stop,
                        zone_edge_stop = EXCLUDED.zone_edge_stop,
                        entry_attempt = EXCLUDED.entry_attempt,
                        with_trend = EXCLUDED.with_trend,
                        counter_trend = EXCLUDED.counter_trend,
                        stopped_by_wick = EXCLUDED.stopped_by_wick,
                        reviewed_at = NOW()
                """, (
                    trade_id,
                    review_data.get('actual_outcome'),
                    review_data.get('notes'),
                    review_data.get('notes_differently'),
                    review_data.get('notes_pattern'),
                    review_data.get('notes_observations'),
                    review_data.get('accuracy', False),
                    review_data.get('tape_confirmation', False),
                    review_data.get('good_trade', False),
                    review_data.get('signal_aligned', False),
                    review_data.get('confirmation_required', False),
                    review_data.get('prior_candle_stop', False),
                    review_data.get('two_candle_stop', False),
                    review_data.get('atr_stop', False),
                    review_data.get('zone_edge_stop', False),
                    review_data.get('entry_attempt'),
                    review_data.get('with_trend', False),
                    review_data.get('counter_trend', False),
                    review_data.get('stopped_by_wick', False),
                ))
                self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to upsert review for {trade_id}: {e}")
            return False

    def is_reviewed(self, trade_id: str) -> bool:
        """Check if a trade has been reviewed."""
        self._ensure_connected()
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM journal_trade_reviews WHERE trade_id = %s",
                (trade_id,)
            )
            return cur.fetchone() is not None
