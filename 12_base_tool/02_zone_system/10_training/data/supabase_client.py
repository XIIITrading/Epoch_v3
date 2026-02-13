"""
Epoch Trading System - Supabase Client for Training Module
Handles trade fetching for the training module.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import date, datetime
from typing import List, Optional, Dict, Any
import logging

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DB_CONFIG
from models.trade import Trade, TradeWithMetrics, OptimalTradeEvent, Zone, TradeReview, TradeAnalysis

logger = logging.getLogger(__name__)


class SupabaseClient:
    """
    Client for Supabase PostgreSQL database.
    Handles trade fetching for the training module.
    """

    def __init__(self):
        """Initialize the client (connection created on demand)."""
        self.conn = None

    def connect(self) -> bool:
        """Establish database connection."""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            logger.info("Connected to Supabase")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            return False

    def disconnect(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def _ensure_connected(self):
        """Ensure we have an active connection."""
        if not self.conn or self.conn.closed:
            self.connect()

    # =========================================================================
    # Trade Fetching
    # =========================================================================

    def fetch_trades(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        ticker: Optional[str] = None,
        model: Optional[str] = None,
        unreviewed_only: bool = False,
        limit: int = 500
    ) -> List[Trade]:
        """
        Fetch trades from database with optional filters.

        Args:
            date_from: Start date filter (inclusive)
            date_to: End date filter (inclusive)
            ticker: Filter by ticker symbol
            model: Filter by model (EPCH1-4)
            unreviewed_only: If True, only return trades not in trade_reviews
            limit: Maximum number of trades to fetch

        Returns:
            List of Trade objects
        """
        self._ensure_connected()

        if unreviewed_only:
            query = """
                SELECT t.* FROM trades t
                LEFT JOIN trade_reviews r ON t.trade_id = r.trade_id
                WHERE r.id IS NULL
            """
        else:
            query = "SELECT * FROM trades WHERE 1=1"

        params = []

        if date_from:
            query += " AND date >= %s"
            params.append(date_from)

        if date_to:
            query += " AND date <= %s"
            params.append(date_to)

        if ticker:
            query += " AND ticker = %s"
            params.append(ticker.upper())

        if model:
            query += " AND model = %s"
            params.append(model.upper())

        query += " ORDER BY date DESC, entry_time DESC"
        query += f" LIMIT {limit}"

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                rows = cur.fetchall()
                return [Trade.from_db_row(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching trades: {e}")
            return []

    def fetch_trade_with_metrics(self, trade_id: str) -> Optional[TradeWithMetrics]:
        """
        Fetch a single trade with all metrics (MFE/MAE, zone info, bookmap).

        Args:
            trade_id: The trade ID to fetch

        Returns:
            TradeWithMetrics object or None if not found
        """
        self._ensure_connected()

        # Fetch trade
        trade_query = "SELECT * FROM trades WHERE trade_id = %s"

        # Fetch optimal_trade events (including R-level crossings v2.2.0)
        events_query = """
            SELECT * FROM optimal_trade
            WHERE trade_id = %s
            ORDER BY
                CASE event_type
                    WHEN 'ENTRY' THEN 1
                    WHEN 'R1_CROSS' THEN 2
                    WHEN 'R2_CROSS' THEN 3
                    WHEN 'R3_CROSS' THEN 4
                    WHEN 'MFE' THEN 5
                    WHEN 'MAE' THEN 6
                    WHEN 'EXIT' THEN 7
                END
        """

        # Fetch zone info
        zone_query = """
            SELECT rank, tier, score
            FROM zones
            WHERE ticker = %s AND date = %s AND is_filtered = true
            LIMIT 1
        """

        # Fetch bookmap image
        image_query = "SELECT bookmap_url FROM trade_images WHERE trade_id = %s"

        # Fetch stop analysis (zone_buffer stop type)
        stop_analysis_query = """
            SELECT stop_price, r_achieved, outcome, mfe_price
            FROM stop_analysis
            WHERE trade_id = %s AND stop_type = 'zone_buffer'
        """

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get trade
                cur.execute(trade_query, (trade_id,))
                trade_row = cur.fetchone()
                if not trade_row:
                    return None
                trade = Trade.from_db_row(dict(trade_row))

                # Get events
                cur.execute(events_query, (trade_id,))
                event_rows = cur.fetchall()
                events = [OptimalTradeEvent.from_db_row(dict(row)) for row in event_rows]

                # Get zone info
                cur.execute(zone_query, (trade.ticker, trade.date))
                zone_row = cur.fetchone()
                zone_info = dict(zone_row) if zone_row else None

                # Get bookmap
                cur.execute(image_query, (trade_id,))
                image_row = cur.fetchone()
                bookmap_url = image_row['bookmap_url'] if image_row else None

                # Get stop analysis (zone_buffer)
                cur.execute(stop_analysis_query, (trade_id,))
                stop_row = cur.fetchone()
                stop_analysis = dict(stop_row) if stop_row else None

                return TradeWithMetrics.from_trade_and_events(
                    trade=trade,
                    events=events,
                    zone_info=zone_info,
                    bookmap_url=bookmap_url,
                    stop_analysis=stop_analysis
                )

        except Exception as e:
            logger.error(f"Error fetching trade with metrics: {e}")
            return None

    def fetch_trades_with_metrics(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        ticker: Optional[str] = None,
        model: Optional[str] = None,
        unreviewed_only: bool = False,
        limit: int = 500
    ) -> List[TradeWithMetrics]:
        """
        Fetch multiple trades with metrics.
        More efficient than calling fetch_trade_with_metrics for each.
        """
        # First get the trade IDs
        trades = self.fetch_trades(
            date_from=date_from,
            date_to=date_to,
            ticker=ticker,
            model=model,
            unreviewed_only=unreviewed_only,
            limit=limit
        )

        if not trades:
            return []

        # Batch fetch all related data
        trade_ids = [t.trade_id for t in trades]

        self._ensure_connected()

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Fetch all events at once
                events_query = """
                    SELECT * FROM optimal_trade
                    WHERE trade_id = ANY(%s)
                """
                cur.execute(events_query, (trade_ids,))
                all_events = [OptimalTradeEvent.from_db_row(dict(row)) for row in cur.fetchall()]

                # Group events by trade_id
                events_by_trade = {}
                for event in all_events:
                    if event.trade_id not in events_by_trade:
                        events_by_trade[event.trade_id] = []
                    events_by_trade[event.trade_id].append(event)

                # Fetch all bookmap URLs at once
                images_query = """
                    SELECT trade_id, bookmap_url FROM trade_images
                    WHERE trade_id = ANY(%s)
                """
                cur.execute(images_query, (trade_ids,))
                bookmap_by_trade = {row['trade_id']: row['bookmap_url'] for row in cur.fetchall()}

                # Fetch all stop_analysis (zone_buffer) at once
                stop_analysis_query = """
                    SELECT trade_id, stop_price, r_achieved, outcome, mfe_price
                    FROM stop_analysis
                    WHERE trade_id = ANY(%s) AND stop_type = 'zone_buffer'
                """
                cur.execute(stop_analysis_query, (trade_ids,))
                stop_by_trade = {row['trade_id']: dict(row) for row in cur.fetchall()}

                # Build TradeWithMetrics for each
                result = []
                for trade in trades:
                    events = events_by_trade.get(trade.trade_id, [])
                    bookmap_url = bookmap_by_trade.get(trade.trade_id)
                    stop_analysis = stop_by_trade.get(trade.trade_id)

                    twm = TradeWithMetrics.from_trade_and_events(
                        trade=trade,
                        events=events,
                        bookmap_url=bookmap_url,
                        stop_analysis=stop_analysis
                    )
                    result.append(twm)

                return result

        except Exception as e:
            logger.error(f"Error batch fetching trades with metrics: {e}")
            # Fallback to individual fetches
            return [self.fetch_trade_with_metrics(t.trade_id) for t in trades if self.fetch_trade_with_metrics(t.trade_id)]

    def fetch_optimal_trade_events(self, trade_id: str) -> Optional[Dict[str, Dict[str, Any]]]:
        """
        Fetch all event indicators from optimal_trade table (v2.2.0 - R-Level Events).
        Returns data for ENTRY, R1_CROSS, R2_CROSS, R3_CROSS, MFE, MAE, EXIT events.

        Args:
            trade_id: The trade ID to fetch indicators for

        Returns:
            Dict keyed by event_type with indicator values, or None if not found
        """
        self._ensure_connected()

        query = """
            SELECT
                event_type,
                event_time,
                bars_from_entry,
                entry_price,
                price_at_event,
                points_at_event,
                actual_points,
                win,
                health_score,
                health_label,
                health_delta,
                health_summary,
                structure_score,
                volume_score,
                price_score,
                vwap,
                sma9,
                sma21,
                sma_spread,
                sma_momentum_ratio,
                sma_momentum_label,
                vol_roc,
                vol_delta,
                cvd_slope,
                m5_structure,
                m15_structure,
                h1_structure,
                h4_structure
            FROM optimal_trade
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
        """

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (trade_id,))
                rows = cur.fetchall()
                if not rows:
                    return None
                # Return dict keyed by event_type
                return {row['event_type']: dict(row) for row in rows}
        except Exception as e:
            logger.error(f"Error fetching optimal trade events: {e}")
            self.conn.rollback()  # Reset transaction state
            return None

    def fetch_zones_for_trade(self, ticker: str, trade_date: date) -> List[Zone]:
        """
        Fetch zones for a specific ticker and date.

        Args:
            ticker: Stock symbol
            trade_date: Trading date

        Returns:
            List of Zone objects
        """
        self._ensure_connected()

        query = """
            SELECT zone_id, ticker, date, zone_high, zone_low, hvn_poc,
                   rank, score, is_filtered
            FROM zones
            WHERE ticker = %s AND date = %s
            ORDER BY score DESC NULLS LAST
        """

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (ticker.upper(), trade_date))
                rows = cur.fetchall()
                return [Zone.from_db_row(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching zones: {e}")
            self.conn.rollback()  # Reset transaction state
            return []


    # =========================================================================
    # Trade Reviews
    # =========================================================================

    def fetch_review(self, trade_id: str) -> Optional[TradeReview]:
        """
        Fetch existing review for a trade.

        Args:
            trade_id: The trade ID to fetch review for

        Returns:
            TradeReview object or None if not found
        """
        self._ensure_connected()

        query = """
            SELECT trade_id, actual_outcome, notes,
                   good_trade, signal_aligned, confirmation_required,
                   prior_candle_stop, two_candle_stop, atr_stop, zone_edge_stop,
                   entry_attempt, with_trend, counter_trend, stopped_by_wick
            FROM trade_reviews
            WHERE trade_id = %s
        """

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (trade_id,))
                row = cur.fetchone()
                if row:
                    return TradeReview.from_db_row(dict(row))
                return None
        except Exception as e:
            logger.error(f"Error fetching review: {e}")
            self.conn.rollback()
            return None

    def upsert_review(self, review: TradeReview) -> bool:
        """
        Insert or update a trade review.

        Args:
            review: TradeReview object to save

        Returns:
            True if successful, False otherwise
        """
        self._ensure_connected()

        query = """
            INSERT INTO trade_reviews (
                trade_id, actual_outcome, notes,
                good_trade, signal_aligned, confirmation_required,
                prior_candle_stop, two_candle_stop, atr_stop, zone_edge_stop,
                entry_attempt, with_trend, counter_trend, stopped_by_wick
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (trade_id) DO UPDATE SET
                actual_outcome = EXCLUDED.actual_outcome,
                notes = EXCLUDED.notes,
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
                stopped_by_wick = EXCLUDED.stopped_by_wick
        """

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (
                    review.trade_id,
                    review.actual_outcome,
                    review.notes,
                    review.good_trade,
                    review.signal_aligned,
                    review.confirmation_required,
                    review.prior_candle_stop,
                    review.two_candle_stop,
                    review.atr_stop,
                    review.zone_edge_stop,
                    review.entry_attempt,
                    review.with_trend,
                    review.counter_trend,
                    review.stopped_by_wick,
                ))
                self.conn.commit()
                logger.info(f"Saved review for trade {review.trade_id}")
                return True
        except Exception as e:
            logger.error(f"Error saving review: {e}")
            self.conn.rollback()
            return False

    # =========================================================================
    # Trade Analysis (Claude AI)
    # =========================================================================

    def fetch_analysis(self, trade_id: str, analysis_type: str) -> Optional[TradeAnalysis]:
        """
        Fetch existing analysis for a trade.

        Args:
            trade_id: The trade ID to fetch analysis for
            analysis_type: 'pre_trade' or 'post_trade'

        Returns:
            TradeAnalysis object or None if not found
        """
        self._ensure_connected()

        query = """
            SELECT trade_id, analysis_type, prompt_text, response_text,
                   created_at, updated_at
            FROM trade_analysis
            WHERE trade_id = %s AND analysis_type = %s
        """

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (trade_id, analysis_type))
                row = cur.fetchone()
                if row:
                    return TradeAnalysis.from_db_row(dict(row))
                return None
        except Exception as e:
            logger.error(f"Error fetching analysis: {e}")
            self.conn.rollback()
            return None

    def fetch_all_analysis(self, trade_id: str) -> Dict[str, TradeAnalysis]:
        """
        Fetch all analysis for a trade (both pre and post).

        Args:
            trade_id: The trade ID to fetch analysis for

        Returns:
            Dict keyed by analysis_type with TradeAnalysis objects
        """
        self._ensure_connected()

        query = """
            SELECT trade_id, analysis_type, prompt_text, response_text,
                   created_at, updated_at
            FROM trade_analysis
            WHERE trade_id = %s
        """

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (trade_id,))
                rows = cur.fetchall()
                return {
                    row['analysis_type']: TradeAnalysis.from_db_row(dict(row))
                    for row in rows
                }
        except Exception as e:
            logger.error(f"Error fetching all analysis: {e}")
            self.conn.rollback()
            return {}

    def upsert_analysis(
        self,
        trade_id: str,
        analysis_type: str,
        response_text: str,
        prompt_text: Optional[str] = None
    ) -> bool:
        """
        Insert or update a trade analysis.

        Args:
            trade_id: Trade ID
            analysis_type: 'pre_trade' or 'post_trade'
            response_text: Claude's analysis response
            prompt_text: Optional prompt that was sent

        Returns:
            True if successful, False otherwise
        """
        self._ensure_connected()

        query = """
            INSERT INTO trade_analysis (
                trade_id, analysis_type, response_text, prompt_text, updated_at
            ) VALUES (
                %s, %s, %s, %s, NOW()
            )
            ON CONFLICT (trade_id, analysis_type) DO UPDATE SET
                response_text = EXCLUDED.response_text,
                prompt_text = EXCLUDED.prompt_text,
                updated_at = NOW()
        """

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (trade_id, analysis_type, response_text, prompt_text))
                self.conn.commit()
                logger.info(f"Saved {analysis_type} analysis for trade {trade_id}")
                return True
        except Exception as e:
            logger.error(f"Error saving analysis: {e}")
            self.conn.rollback()
            return False

    # =========================================================================
    # Indicator Refinement
    # =========================================================================

    def fetch_indicator_refinement(self, trade_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch indicator refinement scores for a trade.

        Returns continuation and rejection scores from the indicator_refinement table.
        These scores qualify trades as CONTINUATION (EPCH01/03) or REJECTION (EPCH02/04).

        Args:
            trade_id: The trade ID to fetch refinement data for

        Returns:
            Dict with all indicator scores, or None if not found
        """
        self._ensure_connected()

        query = """
            SELECT
                trade_id, date, ticker, direction, model, entry_time, entry_price,
                trade_type,
                -- Continuation indicators (CONT-01 to CONT-04)
                mtf_align_score, mtf_h4_aligned, mtf_h1_aligned, mtf_m15_aligned, mtf_m5_aligned,
                sma_mom_score, sma_spread, sma_spread_pct, sma_spread_roc,
                sma_spread_aligned, sma_spread_expanding,
                vol_thrust_score, vol_roc, vol_delta_5, vol_roc_strong, vol_delta_aligned,
                pullback_score, in_pullback, pullback_delta_ratio,
                continuation_score, continuation_label,
                -- Rejection indicators (REJ-01 to REJ-05)
                struct_div_score, htf_aligned, ltf_divergent,
                sma_exhst_score, sma_spread_contracting, sma_spread_very_tight, sma_spread_tight,
                delta_abs_score, absorption_ratio,
                vol_climax_score, vol_roc_q5, vol_declining,
                cvd_extr_score, cvd_slope, cvd_slope_normalized, cvd_extreme,
                rejection_score, rejection_label,
                -- Outcome & metadata
                trade_outcome, outcome_validated, calculation_version
            FROM indicator_refinement
            WHERE trade_id = %s
        """

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (trade_id,))
                row = cur.fetchone()
                if row:
                    return dict(row)
                return None
        except Exception as e:
            logger.error(f"Error fetching indicator refinement: {e}")
            self.conn.rollback()
            return None

    def fetch_indicator_refinement_batch(self, trade_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Fetch indicator refinement data for multiple trades at once.

        Args:
            trade_ids: List of trade IDs to fetch

        Returns:
            Dict keyed by trade_id with refinement data
        """
        if not trade_ids:
            return {}

        self._ensure_connected()

        query = """
            SELECT
                trade_id, date, ticker, direction, model, trade_type,
                mtf_align_score, sma_mom_score, vol_thrust_score, pullback_score,
                continuation_score, continuation_label,
                struct_div_score, sma_exhst_score, delta_abs_score, vol_climax_score, cvd_extr_score,
                rejection_score, rejection_label,
                trade_outcome, outcome_validated
            FROM indicator_refinement
            WHERE trade_id = ANY(%s)
        """

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (trade_ids,))
                rows = cur.fetchall()
                return {row['trade_id']: dict(row) for row in rows}
        except Exception as e:
            logger.error(f"Error batch fetching indicator refinement: {e}")
            self.conn.rollback()
            return {}

    # =========================================================================
    # AI Predictions (Batch Analyzer)
    # =========================================================================

    def fetch_ai_prediction(self, trade_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch pre-computed AI prediction from ai_predictions table.

        Args:
            trade_id: The trade ID to fetch prediction for

        Returns:
            Dict with prediction fields, or None if not found
        """
        self._ensure_connected()

        query = """
            SELECT
                prediction, confidence,
                candle_pct, candle_status,
                vol_delta, vol_delta_status,
                vol_roc, vol_roc_status,
                sma, h1_struct, snapshot,
                actual_outcome
            FROM ai_predictions
            WHERE trade_id = %s
        """

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (trade_id,))
                row = cur.fetchone()
                if row:
                    return dict(row)
                return None
        except Exception as e:
            logger.error(f"Error fetching AI prediction: {e}")
            self.conn.rollback()
            return None

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def get_available_tickers(self, date_from: Optional[date] = None) -> List[str]:
        """Get list of unique tickers with trades."""
        self._ensure_connected()

        query = "SELECT DISTINCT ticker FROM trades"
        params = []

        if date_from:
            query += " WHERE date >= %s"
            params.append(date_from)

        query += " ORDER BY ticker"

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, params)
                return [row[0] for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching tickers: {e}")
            return []

    def get_available_models(self) -> List[str]:
        """Get list of unique models."""
        self._ensure_connected()

        query = "SELECT DISTINCT model FROM trades WHERE model IS NOT NULL ORDER BY model"

        try:
            with self.conn.cursor() as cur:
                cur.execute(query)
                return [row[0] for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching models: {e}")
            return ['EPCH1', 'EPCH2', 'EPCH3', 'EPCH4']

    def get_trade_count(self) -> int:
        """Get count of trades."""
        self._ensure_connected()

        query = "SELECT COUNT(*) FROM trades"

        try:
            with self.conn.cursor() as cur:
                cur.execute(query)
                return cur.fetchone()[0]
        except Exception as e:
            logger.error(f"Error counting trades: {e}")
            return 0


# Singleton instance
_client = None


def get_supabase_client() -> SupabaseClient:
    """Get or create the Supabase client singleton."""
    global _client
    if _client is None:
        _client = SupabaseClient()
        _client.connect()
    return _client
