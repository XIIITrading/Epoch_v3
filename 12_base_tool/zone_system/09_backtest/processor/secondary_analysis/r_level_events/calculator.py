"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: BACKTEST PROCESSOR
R-Level Events Calculator
XIII Trading LLC
================================================================================

Processes trades to detect R-level crossings and insert events into optimal_trade.
Uses M1 indicator bars for precise detection.

NOTE: This ADDS new event types (R1_CROSS, R2_CROSS, R3_CROSS) to optimal_trade
without modifying existing ENTRY, MFE, MAE, EXIT events.
================================================================================
"""

import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from datetime import date, time, datetime
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
import logging

try:
    from .detector import RLevelCrossingDetector, RCrossingEvent
    from .config import (
        DB_CONFIG,
        DEFAULT_STOP_TYPE,
        ZONE_BUFFER_PERCENT,
        EOD_EXIT_TIME,
        BATCH_SIZE,
        LOG_INTERVAL,
    )
except ImportError:
    from detector import RLevelCrossingDetector, RCrossingEvent
    from config import (
        DB_CONFIG,
        DEFAULT_STOP_TYPE,
        ZONE_BUFFER_PERCENT,
        EOD_EXIT_TIME,
        BATCH_SIZE,
        LOG_INTERVAL,
    )

logger = logging.getLogger(__name__)


class RLevelEventsCalculator:
    """
    Calculates R-level crossing events for trades.

    Workflow:
    1. Fetch trades with entry/stop data
    2. For each trade, fetch M1 bars from entry_time to 15:30
    3. Detect R-level crossings using RLevelCrossingDetector
    4. Insert R1_CROSS, R2_CROSS, R3_CROSS events to optimal_trade
    """

    def __init__(self, conn=None):
        """
        Initialize calculator.

        Args:
            conn: Optional existing database connection
        """
        self.conn = conn
        self._owns_connection = False

    def connect(self) -> bool:
        """Establish database connection if not provided."""
        if self.conn is None:
            try:
                self.conn = psycopg2.connect(**DB_CONFIG)
                self._owns_connection = True
                logger.info("Connected to database")
                return True
            except Exception as e:
                logger.error(f"Failed to connect to database: {e}")
                return False
        return True

    def disconnect(self):
        """Close database connection if we own it."""
        if self._owns_connection and self.conn:
            self.conn.close()
            self.conn = None
            logger.info("Disconnected from database")

    def process_trades(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        ticker: Optional[str] = None,
        reprocess: bool = False
    ) -> Dict[str, int]:
        """
        Process trades to generate R-level crossing events.

        Args:
            date_from: Start date filter (inclusive)
            date_to: End date filter (inclusive)
            ticker: Optional ticker filter
            reprocess: If True, delete existing R-level events and recalculate

        Returns:
            Dict with processing statistics
        """
        if not self.connect():
            return {'error': 'Failed to connect to database'}

        stats = {
            'trades_processed': 0,
            'r1_events': 0,
            'r2_events': 0,
            'r3_events': 0,
            'trades_skipped': 0,
            'errors': 0,
        }

        try:
            # Get trades to process
            trades = self._fetch_trades(date_from, date_to, ticker, reprocess)
            logger.info(f"Found {len(trades)} trades to process")

            if not trades:
                return stats

            # Process each trade
            for i, trade in enumerate(trades):
                try:
                    result = self._process_single_trade(trade)
                    stats['r1_events'] += result.get('R1', 0)
                    stats['r2_events'] += result.get('R2', 0)
                    stats['r3_events'] += result.get('R3', 0)
                    stats['trades_processed'] += 1

                    if (i + 1) % LOG_INTERVAL == 0:
                        logger.info(f"Processed {i + 1}/{len(trades)} trades")

                except Exception as e:
                    logger.error(f"Error processing trade {trade.get('trade_id')}: {e}")
                    stats['errors'] += 1
                    stats['trades_skipped'] += 1

            self.conn.commit()
            logger.info(f"Processing complete: {stats}")

        except Exception as e:
            logger.error(f"Error in process_trades: {e}")
            self.conn.rollback()
            stats['error'] = str(e)

        return stats

    def _fetch_trades(
        self,
        date_from: Optional[date],
        date_to: Optional[date],
        ticker: Optional[str],
        reprocess: bool
    ) -> List[Dict]:
        """
        Fetch trades that need R-level event processing.

        Returns trades with entry/stop data from trades + stop_analysis tables.
        """
        # Base query: Get trades with stop_analysis data
        query = """
            SELECT DISTINCT
                t.trade_id,
                t.date,
                t.ticker,
                t.direction,
                t.model,
                t.entry_price,
                t.entry_time,
                t.zone_high,
                t.zone_low,
                sa.stop_price,
                sa.stop_distance
            FROM trades t
            LEFT JOIN stop_analysis sa
                ON t.trade_id = sa.trade_id
                AND sa.stop_type = %s
            WHERE t.entry_price IS NOT NULL
              AND t.entry_time IS NOT NULL
              AND t.direction IS NOT NULL
        """
        params = [DEFAULT_STOP_TYPE]

        # Add date filters
        if date_from:
            query += " AND t.date >= %s"
            params.append(date_from)

        if date_to:
            query += " AND t.date <= %s"
            params.append(date_to)

        # Add ticker filter
        if ticker:
            query += " AND t.ticker = %s"
            params.append(ticker.upper())

        # Exclude trades that already have R-level events (unless reprocessing)
        if not reprocess:
            query += """
                AND NOT EXISTS (
                    SELECT 1 FROM optimal_trade ot
                    WHERE ot.trade_id = t.trade_id
                    AND ot.event_type IN ('R1_CROSS', 'R2_CROSS', 'R3_CROSS')
                )
            """

        query += " ORDER BY t.date, t.entry_time"

        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            return [dict(row) for row in cur.fetchall()]

    def _process_single_trade(self, trade: Dict) -> Dict[str, int]:
        """
        Process a single trade to detect R-level crossings.

        Returns count of events created per R-level.
        """
        trade_id = trade['trade_id']
        ticker = trade['ticker']
        trade_date = trade['date']
        direction = trade['direction']
        entry_price = self._to_float(trade['entry_price'])
        entry_time = trade['entry_time']

        # Get stop price (from stop_analysis or calculate)
        stop_price = self._get_stop_price(trade)
        if stop_price is None:
            logger.warning(f"No stop price for trade {trade_id}, skipping")
            return {}

        # Create detector
        try:
            detector = RLevelCrossingDetector(
                direction=direction,
                entry_price=entry_price,
                stop_price=stop_price
            )
        except ValueError as e:
            logger.warning(f"Cannot create detector for {trade_id}: {e}")
            return {}

        # Fetch M1 bars from entry to EOD
        m1_bars = self._fetch_m1_bars(ticker, trade_date, entry_time)
        if not m1_bars:
            logger.debug(f"No M1 bars for trade {trade_id}")
            return {}

        # Detect crossings
        crossings = detector.detect_crossings(m1_bars)

        if not crossings:
            return {}

        # Get win condition from existing ENTRY event
        win = self._get_trade_win(trade_id)

        # Get entry health for delta calculation
        entry_health = self._get_entry_health(trade_id)

        # Delete existing R-level events for this trade (if reprocessing)
        self._delete_existing_r_events(trade_id)

        # Insert new events
        result = {}
        for r_level, crossing in crossings.items():
            self._insert_r_event(
                trade=trade,
                crossing=crossing,
                win=win,
                entry_health=entry_health,
                detector=detector
            )
            result[r_level] = 1

        return result

    def _get_stop_price(self, trade: Dict) -> Optional[float]:
        """Get stop price from stop_analysis or calculate from zone."""
        # Prefer stop_analysis
        if trade.get('stop_price'):
            return self._to_float(trade['stop_price'])

        # Fallback: Calculate from zone
        zone_high = trade.get('zone_high')
        zone_low = trade.get('zone_low')
        direction = trade.get('direction')

        if not zone_high or not zone_low or not direction:
            return None

        zone_high = self._to_float(zone_high)
        zone_low = self._to_float(zone_low)
        zone_height = zone_high - zone_low
        buffer = zone_height * ZONE_BUFFER_PERCENT

        if direction == 'LONG':
            return zone_low - buffer
        else:  # SHORT
            return zone_high + buffer

    def _fetch_m1_bars(
        self,
        ticker: str,
        trade_date: date,
        entry_time: time
    ) -> List[Dict]:
        """Fetch M1 indicator bars from entry time to EOD."""
        query = """
            SELECT
                bar_time,
                open, high, low, close, volume,
                vwap, sma9, sma21, sma_spread,
                sma_momentum_ratio, sma_momentum_label,
                vol_roc, vol_delta, cvd_slope,
                h4_structure, h1_structure, m15_structure,
                m5_structure, m1_structure,
                health_score
            FROM m1_indicator_bars
            WHERE ticker = %s
              AND bar_date = %s
              AND bar_time >= %s
              AND bar_time <= %s
            ORDER BY bar_time ASC
        """
        eod_time = datetime.strptime(EOD_EXIT_TIME, "%H:%M:%S").time()

        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (ticker, trade_date, entry_time, eod_time))
            return [dict(row) for row in cur.fetchall()]

    def _get_trade_win(self, trade_id: str) -> Optional[int]:
        """Get win value from existing ENTRY event."""
        query = """
            SELECT win FROM optimal_trade
            WHERE trade_id = %s AND event_type = 'ENTRY'
            LIMIT 1
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (trade_id,))
            row = cur.fetchone()
            return row[0] if row else None

    def _get_entry_health(self, trade_id: str) -> Optional[int]:
        """Get health_score from existing ENTRY event."""
        query = """
            SELECT health_score FROM optimal_trade
            WHERE trade_id = %s AND event_type = 'ENTRY'
            LIMIT 1
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (trade_id,))
            row = cur.fetchone()
            return row[0] if row else None

    def _delete_existing_r_events(self, trade_id: str):
        """Delete existing R-level events for a trade."""
        query = """
            DELETE FROM optimal_trade
            WHERE trade_id = %s
              AND event_type IN ('R1_CROSS', 'R2_CROSS', 'R3_CROSS')
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (trade_id,))

    def _insert_r_event(
        self,
        trade: Dict,
        crossing: RCrossingEvent,
        win: Optional[int],
        entry_health: Optional[int],
        detector: RLevelCrossingDetector
    ):
        """Insert a single R-level crossing event into optimal_trade."""
        # Calculate fields
        entry_price = self._to_float(trade['entry_price'])
        entry_time = trade['entry_time']

        # Points at event (direction-adjusted)
        if trade['direction'] == 'LONG':
            points_at_event = crossing.crossing_price - entry_price
        else:
            points_at_event = entry_price - crossing.crossing_price

        # Bars from entry (approximate using minutes)
        if crossing.crossing_time and entry_time:
            entry_minutes = entry_time.hour * 60 + entry_time.minute
            crossing_minutes = crossing.crossing_time.hour * 60 + crossing.crossing_time.minute
            bars_from_entry = crossing_minutes - entry_minutes  # 1-minute bars
        else:
            bars_from_entry = 0  # Default to 0 if can't calculate

        # Ensure win is not null (default to 0 if unknown)
        if win is None:
            win = 0

        # actual_points = points_at_event for R-level events
        actual_points = points_at_event

        # Health delta
        health_delta = None
        if crossing.health_score is not None and entry_health is not None:
            health_delta = crossing.health_score - entry_health

        # Health summary
        health_summary = None
        if health_delta is not None:
            if health_delta > 0:
                health_summary = 'IMPROVING'
            elif health_delta < 0:
                health_summary = 'DEGRADING'
            else:
                health_summary = 'STABLE'

        # Build insert query
        query = """
            INSERT INTO optimal_trade (
                trade_id, event_type, date, ticker, direction, model, win,
                event_time, bars_from_entry,
                entry_price, price_at_event, points_at_event, actual_points,
                health_score, health_delta, health_summary,
                vwap, sma9, sma21, sma_spread, sma_momentum_label,
                vol_roc, vol_delta, cvd_slope,
                m5_structure, m15_structure, h1_structure, h4_structure,
                calculated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s,
                NOW()
            )
            ON CONFLICT (trade_id, event_type) DO UPDATE SET
                event_time = EXCLUDED.event_time,
                bars_from_entry = EXCLUDED.bars_from_entry,
                price_at_event = EXCLUDED.price_at_event,
                points_at_event = EXCLUDED.points_at_event,
                actual_points = EXCLUDED.actual_points,
                health_score = EXCLUDED.health_score,
                health_delta = EXCLUDED.health_delta,
                health_summary = EXCLUDED.health_summary,
                vwap = EXCLUDED.vwap,
                sma9 = EXCLUDED.sma9,
                sma21 = EXCLUDED.sma21,
                sma_spread = EXCLUDED.sma_spread,
                sma_momentum_label = EXCLUDED.sma_momentum_label,
                vol_roc = EXCLUDED.vol_roc,
                vol_delta = EXCLUDED.vol_delta,
                cvd_slope = EXCLUDED.cvd_slope,
                m5_structure = EXCLUDED.m5_structure,
                m15_structure = EXCLUDED.m15_structure,
                h1_structure = EXCLUDED.h1_structure,
                h4_structure = EXCLUDED.h4_structure,
                calculated_at = NOW()
        """

        values = (
            trade['trade_id'],
            f"{crossing.r_level}_CROSS",  # R1_CROSS, R2_CROSS, R3_CROSS
            trade['date'],
            trade['ticker'],
            trade['direction'],
            trade.get('model'),
            win,
            crossing.crossing_time,
            bars_from_entry,
            entry_price,
            crossing.crossing_price,
            points_at_event,
            actual_points,
            crossing.health_score,
            health_delta,
            health_summary,
            crossing.vwap,
            crossing.sma9,
            crossing.sma21,
            crossing.sma_spread,
            crossing.sma_momentum_label,
            crossing.vol_roc,
            crossing.vol_delta,
            crossing.cvd_slope,
            crossing.m5_structure,
            crossing.m15_structure,
            crossing.h1_structure,
            crossing.h4_structure,
        )

        with self.conn.cursor() as cur:
            cur.execute(query, values)

    @staticmethod
    def _to_float(value) -> Optional[float]:
        """Convert value to float, handling None and Decimal."""
        if value is None:
            return None
        if isinstance(value, Decimal):
            return float(value)
        return float(value)
