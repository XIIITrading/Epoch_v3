"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Supabase Client - Isolated Database Access
XIII Trading LLC
================================================================================

Provides database access for indicator analysis.
Fetches trades, trade_bars, and optimal_trade data for recalculation.

================================================================================
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any
import logging

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DB_CONFIG

logger = logging.getLogger(__name__)


class SupabaseClient:
    """
    Client for Supabase PostgreSQL database.
    Provides read access to trades, trade_bars, and optimal_trade tables.
    """

    def __init__(self):
        self.conn = None

    def connect(self) -> bool:
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            logger.info("Connected to Supabase")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            return False

    def disconnect(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def _ensure_connected(self):
        if not self.conn or self.conn.closed:
            self.connect()

    def fetch_trades(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        models: Optional[List[str]] = None,
        directions: Optional[List[str]] = None,
        tickers: Optional[List[str]] = None,
        limit: int = 10000
    ) -> List[Dict[str, Any]]:
        self._ensure_connected()

        query = "SELECT * FROM trades WHERE 1=1"
        params = []

        if date_from:
            query += " AND date >= %s"
            params.append(date_from)
        if date_to:
            query += " AND date <= %s"
            params.append(date_to)
        if models:
            query += " AND model = ANY(%s)"
            params.append(models)
        if directions:
            query += " AND direction = ANY(%s)"
            params.append([d.upper() for d in directions])
        if tickers:
            query += " AND ticker = ANY(%s)"
            params.append([t.upper() for t in tickers])

        query += f" ORDER BY date DESC, entry_time DESC LIMIT {limit}"

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching trades: {e}")
            self.conn.rollback()
            return []

    def fetch_trade_bars(
        self,
        trade_ids: Optional[List[str]] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        limit: int = 100000
    ) -> List[Dict[str, Any]]:
        self._ensure_connected()

        query = """
            SELECT trade_id, date, event_seq, event_time, bars_from_entry, event_type,
                open_price, high_price, low_price, close_price, volume,
                r_at_event, health_score, vwap, sma9, sma21, vol_roc, vol_delta, cvd_slope,
                sma_spread, sma_momentum, m5_structure, m15_structure, h1_structure, h4_structure,
                health_summary, ticker, direction, model, win, actual_r, exit_reason
            FROM trade_bars WHERE 1=1
        """
        params = []

        if trade_ids:
            query += " AND trade_id = ANY(%s)"
            params.append(trade_ids)
        if date_from:
            query += " AND date >= %s"
            params.append(date_from)
        if date_to:
            query += " AND date <= %s"
            params.append(date_to)

        query += f" ORDER BY trade_id, event_seq LIMIT {limit}"

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching trade_bars: {e}")
            self.conn.rollback()
            return []

    def fetch_trade_bars_grouped(
        self,
        trade_ids: Optional[List[str]] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        bars = self.fetch_trade_bars(trade_ids, date_from, date_to)
        grouped = {}
        for bar in bars:
            trade_id = bar["trade_id"]
            if trade_id not in grouped:
                grouped[trade_id] = []
            grouped[trade_id].append(bar)
        return grouped

    def fetch_optimal_trades(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        models: Optional[List[str]] = None,
        event_types: Optional[List[str]] = None,
        limit: int = 50000
    ) -> List[Dict[str, Any]]:
        self._ensure_connected()

        query = """
            SELECT trade_id, event_type, date, ticker, direction, model, win,
                event_time, bars_from_entry, price_at_event,
                health_score, health_delta, health_summary,
                vwap, sma9, sma21, sma_spread, sma_momentum,
                vol_roc, vol_delta, cvd_slope,
                m5_structure, m15_structure, h1_structure, h4_structure,
                actual_r, exit_reason
            FROM optimal_trade WHERE 1=1
        """
        params = []

        if date_from:
            query += " AND date >= %s"
            params.append(date_from)
        if date_to:
            query += " AND date <= %s"
            params.append(date_to)
        if models:
            query += " AND model = ANY(%s)"
            params.append(models)
        if event_types:
            query += " AND event_type = ANY(%s)"
            params.append([e.upper() for e in event_types])

        query += f" ORDER BY date DESC, trade_id, event_type LIMIT {limit}"

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching optimal_trades: {e}")
            self.conn.rollback()
            return []

    def fetch_mfe_mae_potential(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        models: Optional[List[str]] = None,
        directions: Optional[List[str]] = None,
        limit: int = 50000
    ) -> List[Dict[str, Any]]:
        """
        Fetch MFE/MAE potential data for percentage-based analysis.

        Returns raw price data (entry, MFE price, MAE price) for calculating
        MFE/MAE as percentage of entry price. No R-values or stop-based
        calculations.

        Args:
            date_from: Start date filter
            date_to: End date filter
            models: List of models to filter (EPCH1, EPCH2, etc.)
            directions: List of directions to filter (LONG, SHORT)
            limit: Max rows to return

        Returns:
            List of trade dicts with entry_price, mfe_potential_price,
            mae_potential_price, direction, model columns
        """
        self._ensure_connected()

        query = """
            SELECT
                trade_id,
                date,
                ticker,
                direction,
                model,
                entry_time,
                entry_price,
                mfe_potential_price,
                mfe_potential_time,
                mfe_r_potential,
                mae_potential_price,
                mae_potential_time,
                mae_r_potential,
                bars_analyzed,
                is_winner,
                pnl_r
            FROM mfe_mae_potential
            WHERE 1=1
        """
        params = []

        if date_from:
            query += " AND date >= %s"
            params.append(date_from)
        if date_to:
            query += " AND date <= %s"
            params.append(date_to)
        if models:
            query += " AND model = ANY(%s)"
            params.append(models)
        if directions:
            query += " AND direction = ANY(%s)"
            params.append([d.upper() for d in directions])

        query += f" ORDER BY date DESC, ticker, entry_time LIMIT {limit}"

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching mfe_mae_potential: {e}")
            self.conn.rollback()
            return []

    def fetch_trades_m5_r_win(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        models: Optional[List[str]] = None,
        directions: Optional[List[str]] = None,
        limit: int = 50000
    ) -> List[Dict[str, Any]]:
        """
        Fetch canonical trade outcomes from trades_m5_r_win.

        This is the single source of truth for trade outcomes across all
        EPOCH modules. Uses M5 ATR(14) x 1.1 close-based stop methodology
        (outcome_method='atr_r_target') for 5,415 trades, with zone_buffer
        fallback for 25 trades missing r_win_loss data.

        Args:
            date_from: Start date filter
            date_to: End date filter
            models: List of models to filter (EPCH01, EPCH02, etc.)
            directions: List of directions to filter (LONG, SHORT)
            limit: Max rows to return

        Returns:
            List of trade dicts with canonical outcome fields
        """
        self._ensure_connected()

        query = """
            SELECT
                trade_id,
                date,
                ticker,
                model,
                direction,
                entry_price,
                stop_price,
                stop_distance,
                r1_price,
                outcome,
                exit_reason,
                outcome_method,
                is_winner,
                pnl_r,
                max_r_achieved,
                reached_2r,
                reached_3r,
                minutes_to_r1
            FROM trades_m5_r_win
            WHERE 1=1
        """
        params = []

        if date_from:
            query += " AND date >= %s"
            params.append(date_from)
        if date_to:
            query += " AND date <= %s"
            params.append(date_to)
        if models:
            query += " AND model = ANY(%s)"
            params.append(models)
        if directions:
            query += " AND direction = ANY(%s)"
            params.append([d.upper() for d in directions])

        query += f" ORDER BY date DESC, ticker LIMIT {limit}"

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching trades_m5_r_win: {e}")
            self.conn.rollback()
            return []

    def fetch_trades_m5_r_win_by_trade(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        models: Optional[List[str]] = None,
        directions: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Fetch trades_m5_r_win outcomes indexed by trade_id.

        Used as the canonical outcome source for indicator analysis merge.
        Returns a dict mapping trade_id to outcome info for fast lookup.

        Args:
            date_from: Start date filter
            date_to: End date filter
            models: List of models to filter
            directions: List of directions to filter

        Returns:
            Dict mapping trade_id to outcome dict:
            {
                'trade_id': {
                    'is_winner': bool,
                    'outcome': str ('WIN', 'LOSS'),
                    'pnl_r': float,
                    'stop_price': float,
                    'stop_distance': float,
                    'max_r_achieved': float
                }
            }
        """
        self._ensure_connected()

        query = """
            SELECT
                trade_id,
                outcome,
                is_winner,
                pnl_r,
                stop_price,
                stop_distance,
                max_r_achieved,
                model,
                direction
            FROM trades_m5_r_win
            WHERE 1=1
        """
        params = []

        if date_from:
            query += " AND date >= %s"
            params.append(date_from)
        if date_to:
            query += " AND date <= %s"
            params.append(date_to)
        if models:
            query += " AND model = ANY(%s)"
            params.append(models)
        if directions:
            query += " AND direction = ANY(%s)"
            params.append([d.upper() for d in directions])

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                rows = cur.fetchall()

            result = {}
            for row in rows:
                trade_id = row['trade_id']
                result[trade_id] = {
                    'is_winner': row['is_winner'],
                    'outcome': row['outcome'],
                    'pnl_r': float(row['pnl_r']) if row['pnl_r'] is not None else 0.0,
                    'stop_price': float(row['stop_price']) if row['stop_price'] is not None else None,
                    'stop_distance': float(row['stop_distance']) if row['stop_distance'] is not None else 0.0,
                    'max_r_achieved': float(row['max_r_achieved']) if row['max_r_achieved'] is not None else 0.0
                }

            return result

        except Exception as e:
            logger.error(f"Error fetching trades_m5_r_win by trade: {e}")
            self.conn.rollback()
            return {}

    def get_trade_summary(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> Dict[str, Any]:
        self._ensure_connected()

        query = """
            SELECT COUNT(*) as total_trades,
                SUM(CASE WHEN is_winner THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN NOT is_winner THEN 1 ELSE 0 END) as losses,
                AVG(pnl_r) as avg_r, SUM(pnl_r) as total_r
            FROM trades WHERE 1=1
        """
        params = []
        if date_from:
            query += " AND date >= %s"
            params.append(date_from)
        if date_to:
            query += " AND date <= %s"
            params.append(date_to)

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                row = cur.fetchone()
                if row:
                    result = dict(row)
                    total = result.get("total_trades", 0) or 0
                    wins = result.get("wins", 0) or 0
                    result["win_rate"] = (wins / total * 100) if total > 0 else 0
                    return result
                return {}
        except Exception as e:
            logger.error(f"Error fetching trade summary: {e}")
            self.conn.rollback()
            return {}

    def get_summary_by_model(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        self._ensure_connected()

        query = """
            SELECT model, COUNT(*) as total_trades,
                SUM(CASE WHEN is_winner THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN NOT is_winner THEN 1 ELSE 0 END) as losses,
                AVG(pnl_r) as avg_r, SUM(pnl_r) as total_r
            FROM trades WHERE model IS NOT NULL
        """
        params = []
        if date_from:
            query += " AND date >= %s"
            params.append(date_from)
        if date_to:
            query += " AND date <= %s"
            params.append(date_to)

        query += " GROUP BY model ORDER BY model"

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                results = []
                for row in cur.fetchall():
                    result = dict(row)
                    total = result.get("total_trades", 0) or 0
                    wins = result.get("wins", 0) or 0
                    result["win_rate"] = (wins / total * 100) if total > 0 else 0
                    results.append(result)
                return results
        except Exception as e:
            logger.error(f"Error fetching model summary: {e}")
            self.conn.rollback()
            return []

    def get_available_tickers(self) -> List[str]:
        self._ensure_connected()
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT DISTINCT ticker FROM trades ORDER BY ticker")
                return [row[0] for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching tickers: {e}")
            return []

    def get_available_models(self) -> List[str]:
        self._ensure_connected()
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT DISTINCT model FROM trades WHERE model IS NOT NULL ORDER BY model")
                return [row[0] for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching models: {e}")
            return ["EPCH1", "EPCH2", "EPCH3", "EPCH4"]

    def get_date_range(self) -> Dict[str, date]:
        self._ensure_connected()
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT MIN(date) as min_date, MAX(date) as max_date FROM trades")
                row = cur.fetchone()
                return dict(row) if row else {}
        except Exception as e:
            logger.error(f"Error fetching date range: {e}")
            return {}

    def get_trade_count(self) -> int:
        self._ensure_connected()
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM trades")
                return cur.fetchone()[0]
        except Exception as e:
            logger.error(f"Error counting trades: {e}")
            return 0

    def fetch_m1_bars(
        self,
        ticker: str,
        bar_date: date,
        start_time: Optional[str] = None,
        end_time: Optional[str] = "15:30:00"
    ) -> List[Dict[str, Any]]:
        """
        Fetch 1-minute bars for a specific ticker and date.

        Args:
            ticker: Stock symbol
            bar_date: Trading date
            start_time: Optional start time filter (HH:MM:SS format)
            end_time: Optional end time filter (default 15:30:00)

        Returns:
            List of bar dicts with open, high, low, close, volume, bar_time
        """
        self._ensure_connected()

        query = """
            SELECT bar_time, open, high, low, close, volume, vwap
            FROM m1_bars
            WHERE ticker = %s AND bar_date = %s
        """
        params = [ticker.upper(), bar_date]

        if start_time:
            query += " AND bar_time >= %s"
            params.append(start_time)
        if end_time:
            query += " AND bar_time <= %s"
            params.append(end_time)

        query += " ORDER BY bar_time ASC"

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching m1_bars: {e}")
            self.conn.rollback()
            return []

    def fetch_m1_bars_batch(
        self,
        ticker_dates: List[tuple],
        end_time: Optional[str] = "15:30:00"
    ) -> Dict[tuple, List[Dict[str, Any]]]:
        """
        Fetch 1-minute bars for multiple ticker-date combinations efficiently.

        Args:
            ticker_dates: List of (ticker, date) tuples
            end_time: End time filter (default 15:30:00)

        Returns:
            Dict mapping (ticker, date) to list of bars
        """
        self._ensure_connected()

        if not ticker_dates:
            return {}

        # Build query with VALUES clause for efficient batch lookup
        values_list = []
        for t, d in ticker_dates:
            if isinstance(d, date):
                d_str = d.strftime('%Y-%m-%d')
            else:
                d_str = str(d)
            values_list.append(f"('{t.upper()}', '{d_str}'::date)")

        values_clause = ", ".join(values_list)

        query = f"""
            SELECT ticker, bar_date, bar_time, open, high, low, close, volume, vwap
            FROM m1_bars
            WHERE (ticker, bar_date) IN ({values_clause})
        """

        if end_time:
            query += f" AND bar_time <= '{end_time}'"

        query += " ORDER BY ticker, bar_date, bar_time ASC"

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query)
                rows = cur.fetchall()

            # Group by (ticker, date)
            result = {}
            for row in rows:
                key = (row['ticker'], row['bar_date'])
                if key not in result:
                    result[key] = []
                result[key].append(dict(row))

            return result

        except Exception as e:
            logger.error(f"Error fetching m1_bars batch: {e}")
            self.conn.rollback()
            return {}

    def check_m1_bars_coverage(
        self,
        ticker_dates: List[tuple]
    ) -> Dict[str, Any]:
        """
        Check how many of the requested ticker-dates have m1_bars data.

        Args:
            ticker_dates: List of (ticker, date) tuples to check

        Returns:
            Dict with coverage statistics
        """
        self._ensure_connected()

        if not ticker_dates:
            return {'total_requested': 0, 'total_available': 0, 'coverage_pct': 0.0}

        # Build query
        values_list = []
        for t, d in ticker_dates:
            if isinstance(d, date):
                d_str = d.strftime('%Y-%m-%d')
            else:
                d_str = str(d)
            values_list.append(f"('{t.upper()}', '{d_str}'::date)")

        values_clause = ", ".join(values_list)

        query = f"""
            SELECT COUNT(DISTINCT (ticker, bar_date)) as available_count
            FROM m1_bars
            WHERE (ticker, bar_date) IN ({values_clause})
        """

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query)
                row = cur.fetchone()
                available = row['available_count'] if row else 0

            total = len(ticker_dates)
            return {
                'total_requested': total,
                'total_available': available,
                'missing': total - available,
                'coverage_pct': (available / total * 100) if total > 0 else 0.0
            }

        except Exception as e:
            logger.error(f"Error checking m1_bars coverage: {e}")
            self.conn.rollback()
            return {'total_requested': len(ticker_dates), 'total_available': 0, 'coverage_pct': 0.0}

    def fetch_m5_trade_bars_with_outcomes(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        models: Optional[List[str]] = None,
        directions: Optional[List[str]] = None,
        limit: int = 200000
    ) -> List[Dict[str, Any]]:
        """
        Fetch m5_trade_bars data with outcome information for progression analysis.

        Parameters:
            date_from: Start date filter
            date_to: End date filter
            models: List of models to include
            directions: List of directions (LONG, SHORT)
            limit: Maximum rows to return

        Returns:
            List of m5_trade_bar records with is_winner joined
        """
        self._ensure_connected()

        try:
            query = """
                SELECT
                    tb.trade_id,
                    tb.bar_seq,
                    tb.bar_time,
                    tb.bars_from_entry,
                    tb.event_type,
                    tb.date,
                    tb.ticker,
                    tb.direction,
                    tb.model,
                    tb.open,
                    tb.high,
                    tb.low,
                    tb.close,
                    tb.volume,
                    tb.vwap,
                    tb.sma9,
                    tb.sma21,
                    tb.sma_spread,
                    tb.sma_alignment,
                    tb.sma_alignment_healthy,
                    tb.sma_momentum_ratio,
                    tb.sma_momentum_label,
                    tb.sma_momentum_healthy,
                    tb.vwap_position,
                    tb.vwap_healthy,
                    tb.vol_roc,
                    tb.vol_roc_healthy,
                    tb.vol_delta,
                    tb.vol_delta_healthy,
                    tb.cvd_slope,
                    tb.cvd_slope_healthy,
                    tb.h4_structure,
                    tb.h4_structure_healthy,
                    tb.h1_structure,
                    tb.h1_structure_healthy,
                    tb.m15_structure,
                    tb.m15_structure_healthy,
                    tb.m5_structure,
                    tb.m5_structure_healthy,
                    tb.health_score,
                    tb.health_label,
                    tb.structure_score,
                    tb.volume_score,
                    tb.price_score,
                    mp.is_winner,
                    mp.mfe_r_potential,
                    mp.mae_r_potential,
                    mp.mfe_potential_time,
                    mp.mae_potential_time
                FROM m5_trade_bars tb
                JOIN mfe_mae_potential mp ON tb.trade_id = mp.trade_id
                WHERE 1=1
            """
            params = []

            if date_from:
                query += " AND tb.date >= %s"
                params.append(date_from)

            if date_to:
                query += " AND tb.date <= %s"
                params.append(date_to)

            if models:
                query += " AND tb.model = ANY(%s)"
                params.append(models)

            if directions:
                query += " AND tb.direction = ANY(%s)"
                params.append([d.upper() for d in directions])

            query += f" ORDER BY tb.trade_id, tb.bar_seq LIMIT {limit}"

            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]

        except Exception as e:
            logger.error(f"Error fetching m5_trade_bars with outcomes: {e}")
            self.conn.rollback()
            return []

    def fetch_entry_indicators(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        models: Optional[List[str]] = None,
        directions: Optional[List[str]] = None,
        tickers: Optional[List[str]] = None,
        health_score_min: Optional[int] = None,
        health_score_max: Optional[int] = None,
        limit: int = 50000
    ) -> List[Dict[str, Any]]:
        """
        Fetch entry indicator snapshots.

        Parameters:
            date_from: Start date filter
            date_to: End date filter
            models: List of models to include
            directions: List of directions to include
            tickers: List of tickers to include
            health_score_min: Minimum health score filter
            health_score_max: Maximum health score filter
            limit: Maximum rows to return

        Returns:
            List of entry indicator records
        """
        self._ensure_connected()

        try:
            query = """
                SELECT
                    ei.*,
                    mp.mfe_r_potential,
                    mp.mae_r_potential,
                    mp.mfe_potential_time,
                    mp.mae_potential_time,
                    mp.is_winner,
                    mp.pnl_r
                FROM entry_indicators ei
                JOIN mfe_mae_potential mp ON ei.trade_id = mp.trade_id
                WHERE 1=1
            """
            params = []

            if date_from:
                query += " AND ei.date >= %s"
                params.append(date_from)

            if date_to:
                query += " AND ei.date <= %s"
                params.append(date_to)

            if models:
                query += " AND ei.model = ANY(%s)"
                params.append(models)

            if directions:
                query += " AND ei.direction = ANY(%s)"
                params.append([d.upper() for d in directions])

            if tickers:
                query += " AND ei.ticker = ANY(%s)"
                params.append([t.upper() for t in tickers])

            if health_score_min is not None:
                query += " AND ei.health_score >= %s"
                params.append(health_score_min)

            if health_score_max is not None:
                query += " AND ei.health_score <= %s"
                params.append(health_score_max)

            query += f" ORDER BY ei.date DESC, ei.entry_time DESC LIMIT {limit}"

            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]

        except Exception as e:
            logger.error(f"Error fetching entry indicators: {e}")
            self.conn.rollback()
            return []


    def fetch_op_mfe_mae_potential(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        models: Optional[List[str]] = None,
        directions: Optional[List[str]] = None,
        contract_types: Optional[List[str]] = None,
        limit: int = 50000
    ) -> List[Dict[str, Any]]:
        """
        Fetch OPTIONS MFE/MAE potential data for options analysis.

        Returns options price movement data (entry, MFE, MAE, exit) measured
        in points and percentages from entry to 15:30 ET.

        Args:
            date_from: Start date filter
            date_to: End date filter
            models: List of models to filter (EPCH1, EPCH2, etc.)
            directions: List of directions to filter (LONG, SHORT)
            contract_types: List of contract types (CALL, PUT)
            limit: Max rows to return

        Returns:
            List of trade dicts with options MFE/MAE data
        """
        self._ensure_connected()

        query = """
            SELECT
                trade_id,
                date,
                ticker,
                direction,
                model,
                options_ticker,
                strike,
                expiration,
                contract_type,
                entry_time,
                option_entry_price,
                mfe_points,
                mfe_price,
                mfe_time,
                mfe_pct,
                mae_points,
                mae_price,
                mae_time,
                mae_pct,
                exit_price,
                exit_time,
                exit_points,
                exit_pct,
                underlying_mfe_pct,
                underlying_mae_pct,
                underlying_exit_pct,
                bars_analyzed
            FROM op_mfe_mae_potential
            WHERE 1=1
        """
        params = []

        if date_from:
            query += " AND date >= %s"
            params.append(date_from)
        if date_to:
            query += " AND date <= %s"
            params.append(date_to)
        if models:
            query += " AND model = ANY(%s)"
            params.append(models)
        if directions:
            query += " AND direction = ANY(%s)"
            params.append([d.upper() for d in directions])
        if contract_types:
            query += " AND contract_type = ANY(%s)"
            params.append([c.upper() for c in contract_types])

        query += f" ORDER BY date DESC, ticker, entry_time LIMIT {limit}"

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching op_mfe_mae_potential: {e}")
            self.conn.rollback()
            return []

    def get_options_summary(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Get summary statistics for options trades.

        Returns:
            Dict with total trades, win rate, avg MFE/MAE percentages
        """
        self._ensure_connected()

        query = """
            SELECT
                COUNT(*) as total_trades,
                SUM(CASE WHEN exit_pct > 0 THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN exit_pct <= 0 THEN 1 ELSE 0 END) as losses,
                AVG(mfe_pct) as avg_mfe_pct,
                AVG(mae_pct) as avg_mae_pct,
                AVG(exit_pct) as avg_exit_pct,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY mfe_pct) as median_mfe_pct,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY mae_pct) as median_mae_pct,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY exit_pct) as median_exit_pct
            FROM op_mfe_mae_potential
            WHERE 1=1
        """
        params = []
        if date_from:
            query += " AND date >= %s"
            params.append(date_from)
        if date_to:
            query += " AND date <= %s"
            params.append(date_to)

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                row = cur.fetchone()
                if row:
                    result = dict(row)
                    total = result.get("total_trades", 0) or 0
                    wins = result.get("wins", 0) or 0
                    result["win_rate"] = (wins / total * 100) if total > 0 else 0
                    return result
                return {}
        except Exception as e:
            logger.error(f"Error fetching options summary: {e}")
            self.conn.rollback()
            return {}


    def fetch_m5_trade_bars_for_stop_analysis(
        self,
        trade_ids: Optional[List[str]] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        limit: int = 500000
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch M5 trade bars grouped by trade_id for stop analysis.

        Returns bars needed for ATR calculation and fractal detection.

        Parameters:
            trade_ids: Optional list of specific trade IDs
            date_from: Start date filter
            date_to: End date filter
            limit: Maximum rows to return

        Returns:
            Dict mapping trade_id to list of bar records
        """
        self._ensure_connected()

        try:
            query = """
                SELECT
                    trade_id,
                    bar_seq,
                    bar_time,
                    bars_from_entry,
                    date,
                    ticker,
                    direction,
                    model,
                    open,
                    high,
                    low,
                    close,
                    volume
                FROM m5_trade_bars
                WHERE 1=1
            """
            params = []

            if trade_ids:
                query += " AND trade_id = ANY(%s)"
                params.append(trade_ids)

            if date_from:
                query += " AND date >= %s"
                params.append(date_from)

            if date_to:
                query += " AND date <= %s"
                params.append(date_to)

            query += f" ORDER BY trade_id, bar_seq LIMIT {limit}"

            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                rows = cur.fetchall()

            # Group by trade_id
            result = {}
            for row in rows:
                trade_id = row['trade_id']
                if trade_id not in result:
                    result[trade_id] = []
                result[trade_id].append(dict(row))

            return result

        except Exception as e:
            logger.error(f"Error fetching m5_trade_bars for stop analysis: {e}")
            self.conn.rollback()
            return {}

    def fetch_m1_bars_for_stop_analysis(
        self,
        ticker_dates: List[tuple],
        end_time: str = "15:30:00"
    ) -> Dict[tuple, List[Dict[str, Any]]]:
        """
        Fetch M1 bars for multiple ticker-date combinations for stop analysis.

        Optimized batch fetch that gets all needed M1 bars in a single query.

        Parameters:
            ticker_dates: List of (ticker, date) tuples
            end_time: End time filter (default 15:30:00)

        Returns:
            Dict mapping (ticker, date) to list of bar records
        """
        return self.fetch_m1_bars_batch(ticker_dates, end_time)

    def fetch_trades_with_zones(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        models: Optional[List[str]] = None,
        limit: int = 10000
    ) -> List[Dict[str, Any]]:
        """
        Fetch trades with zone boundary data for stop analysis.

        Parameters:
            date_from: Start date filter
            date_to: End date filter
            models: List of models to filter
            limit: Maximum rows to return

        Returns:
            List of trade records with zone_high, zone_low
        """
        self._ensure_connected()

        query = """
            SELECT
                trade_id,
                date,
                ticker,
                direction,
                model,
                entry_time,
                entry_price,
                zone_high,
                zone_low
            FROM trades
            WHERE zone_high IS NOT NULL
              AND zone_low IS NOT NULL
        """
        params = []

        if date_from:
            query += " AND date >= %s"
            params.append(date_from)
        if date_to:
            query += " AND date <= %s"
            params.append(date_to)
        if models:
            query += " AND model = ANY(%s)"
            params.append(models)

        query += f" ORDER BY date DESC, entry_time DESC LIMIT {limit}"

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching trades with zones: {e}")
            self.conn.rollback()
            return []

    # =========================================================================
    # STOP ANALYSIS DATA (CALC-009)
    # =========================================================================
    # These methods fetch pre-calculated stop analysis data from the
    # stop_analysis table populated by the backtest processor.
    # This eliminates the need to recalculate on each dashboard load.

    def fetch_stop_analysis(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        models: Optional[List[str]] = None,
        directions: Optional[List[str]] = None,
        stop_types: Optional[List[str]] = None,
        limit: int = 100000
    ) -> List[Dict[str, Any]]:
        """
        Fetch stop analysis results from Supabase.

        This returns pre-calculated stop outcomes for all 6 stop types,
        including accurate stop prices, R-multiples, and win/loss outcomes
        based on actual bar-by-bar simulation.

        Parameters:
            date_from: Start date filter
            date_to: End date filter
            models: List of models to filter
            directions: List of directions to filter
            stop_types: List of stop types to filter
            limit: Maximum rows to return

        Returns:
            List of stop analysis records with trade outcomes
        """
        self._ensure_connected()

        query = """
            SELECT
                trade_id,
                stop_type,
                date,
                ticker,
                direction,
                model,
                entry_time,
                entry_price,
                zone_low,
                zone_high,
                stop_price,
                stop_distance,
                stop_distance_pct,
                stop_hit,
                stop_hit_time,
                mfe_price,
                mfe_time,
                mfe_distance,
                r_achieved,
                outcome,
                trigger_type
            FROM stop_analysis
            WHERE stop_price IS NOT NULL
        """
        params = []

        if date_from:
            query += " AND date >= %s"
            params.append(date_from)
        if date_to:
            query += " AND date <= %s"
            params.append(date_to)
        if models:
            query += " AND model = ANY(%s)"
            params.append(models)
        if directions:
            query += " AND direction = ANY(%s)"
            params.append([d.upper() for d in directions])
        if stop_types:
            query += " AND stop_type = ANY(%s)"
            params.append(stop_types)

        query += f" ORDER BY date DESC, trade_id, stop_type LIMIT {limit}"

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching stop_analysis: {e}")
            self.conn.rollback()
            return []

    def fetch_stop_analysis_summary(self) -> List[Dict[str, Any]]:
        """
        Fetch aggregated stop analysis summary from the view.

        Returns summary statistics for each stop type including:
        - Total trades, wins, losses, partials
        - Win rate %
        - Average stop distance %
        - Average R for winners
        - Expectancy

        Returns:
            List of summary records, one per stop type
        """
        self._ensure_connected()

        query = """
            SELECT * FROM v_stop_analysis_summary
            ORDER BY expectancy DESC
        """

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query)
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching v_stop_analysis_summary: {e}")
            self.conn.rollback()
            return []

    def fetch_stop_analysis_by_model(self) -> List[Dict[str, Any]]:
        """
        Fetch stop analysis breakdown by model from the view.

        Returns:
            List of records with stop_type + model combinations
        """
        self._ensure_connected()

        query = """
            SELECT * FROM v_stop_analysis_by_model
            ORDER BY stop_type, model
        """

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query)
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching v_stop_analysis_by_model: {e}")
            self.conn.rollback()
            return []

    def fetch_stop_analysis_by_direction(self) -> List[Dict[str, Any]]:
        """
        Fetch stop analysis breakdown by direction from the view.

        Returns:
            List of records with stop_type + direction combinations
        """
        self._ensure_connected()

        query = """
            SELECT * FROM v_stop_analysis_by_direction
            ORDER BY stop_type, direction
        """

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query)
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching v_stop_analysis_by_direction: {e}")
            self.conn.rollback()
            return []

    def get_stop_analysis_count(self) -> int:
        """
        Get the count of records in stop_analysis table.

        Used to determine if the table has been populated.

        Returns:
            Number of records in stop_analysis table
        """
        self._ensure_connected()

        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM stop_analysis WHERE stop_price IS NOT NULL")
                result = cur.fetchone()
                return result[0] if result else 0
        except Exception as e:
            logger.error(f"Error counting stop_analysis: {e}")
            return 0

    def fetch_stop_outcomes_by_trade(
        self,
        stop_type: str = "m5_atr",
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        models: Optional[List[str]] = None,
        directions: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Fetch stop analysis outcomes indexed by trade_id for indicator analysis.

        This provides the win/loss classification for each trade based on the
        selected stop type. Used to compute is_winner for all indicator analysis
        calculations.

        Parameters:
            stop_type: Stop type key (default: 'm5_atr')
            date_from: Start date filter
            date_to: End date filter
            models: List of models to filter
            directions: List of directions to filter

        Returns:
            Dict mapping trade_id to outcome dict:
            {
                'trade_id': {
                    'is_winner': bool (True if outcome == 'WIN'),
                    'outcome': str ('WIN', 'LOSS', 'PARTIAL'),
                    'r_achieved': float,
                    'stop_price': float,
                    'stop_hit': bool,
                    'mfe_price': float
                }
            }
        """
        self._ensure_connected()

        query = """
            SELECT
                trade_id,
                outcome,
                r_achieved,
                stop_price,
                stop_hit,
                mfe_price,
                mfe_distance,
                stop_distance,
                model,
                direction
            FROM stop_analysis
            WHERE stop_type = %s
              AND stop_price IS NOT NULL
        """
        params = [stop_type]

        if date_from:
            query += " AND date >= %s"
            params.append(date_from)
        if date_to:
            query += " AND date <= %s"
            params.append(date_to)
        if models:
            query += " AND model = ANY(%s)"
            params.append(models)
        if directions:
            query += " AND direction = ANY(%s)"
            params.append([d.upper() for d in directions])

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                rows = cur.fetchall()

            # Index by trade_id
            result = {}
            for row in rows:
                trade_id = row['trade_id']
                outcome = row['outcome']
                result[trade_id] = {
                    'is_winner': outcome == 'WIN',
                    'outcome': outcome,
                    'r_achieved': float(row['r_achieved']) if row['r_achieved'] is not None else 0.0,
                    'stop_price': float(row['stop_price']) if row['stop_price'] is not None else None,
                    'stop_hit': row['stop_hit'],
                    'mfe_price': float(row['mfe_price']) if row['mfe_price'] is not None else None,
                    'mfe_distance': float(row['mfe_distance']) if row['mfe_distance'] is not None else 0.0,
                    'stop_distance': float(row['stop_distance']) if row['stop_distance'] is not None else 0.0
                }

            return result

        except Exception as e:
            logger.error(f"Error fetching stop outcomes by trade: {e}")
            self.conn.rollback()
            return {}

    def get_stop_analysis_trade_count(self, stop_type: str = "m5_atr") -> int:
        """
        Get count of trades with stop analysis data for a specific stop type.

        Used to check if stop_analysis table is populated.

        Parameters:
            stop_type: Stop type to check

        Returns:
            Number of trades with data for this stop type
        """
        self._ensure_connected()

        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(DISTINCT trade_id) FROM stop_analysis WHERE stop_type = %s AND stop_price IS NOT NULL",
                    [stop_type]
                )
                result = cur.fetchone()
                return result[0] if result else 0
        except Exception as e:
            logger.error(f"Error counting stop analysis trades: {e}")
            return 0

    # =========================================================================
    # INDICATOR REFINEMENT DATA (Continuation/Rejection Scores)
    # =========================================================================

    def fetch_indicator_refinement(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        models: Optional[List[str]] = None,
        directions: Optional[List[str]] = None,
        limit: int = 50000
    ) -> List[Dict[str, Any]]:
        """
        Fetch indicator refinement scores for trade qualification analysis.

        Returns continuation (0-10) and rejection (0-11) scores with
        individual indicator breakdowns.

        Parameters:
            date_from: Start date filter
            date_to: End date filter
            models: List of models to filter
            directions: List of directions to filter
            limit: Maximum rows to return

        Returns:
            List of indicator refinement records with scores
        """
        self._ensure_connected()

        query = """
            SELECT
                ir.trade_id,
                ir.date,
                ir.ticker,
                ir.direction,
                ir.model,
                ir.trade_type,
                ir.continuation_score,
                ir.continuation_label,
                ir.rejection_score,
                ir.rejection_label,
                ir.mtf_align_score as mtf_alignment_points,
                ir.mtf_h4_aligned,
                ir.mtf_h1_aligned,
                ir.mtf_m15_aligned,
                ir.mtf_m5_aligned,
                ir.sma_mom_score as sma_momentum_points,
                ir.sma_spread,
                ir.sma_spread_pct,
                ir.sma_spread_aligned,
                ir.sma_spread_expanding,
                ir.vol_thrust_score as volume_thrust_points,
                ir.vol_roc,
                ir.vol_delta_5,
                ir.vol_roc_strong,
                ir.vol_delta_aligned,
                ir.pullback_score as pullback_quality_points,
                ir.in_pullback,
                ir.pullback_delta_ratio,
                ir.struct_div_score as structure_divergence_points,
                ir.htf_aligned,
                ir.ltf_divergent,
                ir.sma_exhst_score as sma_exhaustion_points,
                ir.sma_spread_contracting,
                ir.sma_spread_very_tight,
                ir.sma_spread_tight,
                ir.delta_abs_score as delta_absorption_points,
                ir.absorption_ratio,
                ir.vol_climax_score as volume_climax_points,
                ir.vol_roc_q5,
                ir.vol_declining,
                ir.cvd_extr_score as cvd_extreme_points,
                ir.cvd_slope,
                ir.cvd_slope_normalized,
                ir.cvd_extreme,
                mp.is_winner,
                mp.mfe_r_potential,
                mp.mae_r_potential
            FROM indicator_refinement ir
            LEFT JOIN mfe_mae_potential mp ON ir.trade_id = mp.trade_id
            WHERE 1=1
        """
        params = []

        if date_from:
            query += " AND ir.date >= %s"
            params.append(date_from)
        if date_to:
            query += " AND ir.date <= %s"
            params.append(date_to)
        if models:
            query += " AND ir.model = ANY(%s)"
            params.append(models)
        if directions:
            query += " AND ir.direction = ANY(%s)"
            params.append([d.upper() for d in directions])

        query += f" ORDER BY ir.date DESC, ir.ticker LIMIT {limit}"

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching indicator_refinement: {e}")
            self.conn.rollback()
            return []

    def fetch_indicator_refinement_summary(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Fetch aggregated indicator refinement summary statistics.

        Returns summary by trade type (continuation vs rejection) with
        win rates at different score thresholds.

        Returns:
            Dict with summary statistics by trade type and score ranges
        """
        self._ensure_connected()

        query = """
            SELECT
                ir.trade_type,
                COUNT(*) as total_trades,
                AVG(ir.continuation_score) as avg_cont_score,
                AVG(ir.rejection_score) as avg_rej_score,
                SUM(CASE WHEN mp.is_winner THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN NOT mp.is_winner THEN 1 ELSE 0 END) as losses
            FROM indicator_refinement ir
            LEFT JOIN mfe_mae_potential mp ON ir.trade_id = mp.trade_id
            WHERE 1=1
        """
        params = []

        if date_from:
            query += " AND ir.date >= %s"
            params.append(date_from)
        if date_to:
            query += " AND ir.date <= %s"
            params.append(date_to)

        query += " GROUP BY ir.trade_type"

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                rows = cur.fetchall()

            result = {}
            for row in rows:
                trade_type = row['trade_type']
                total = row['total_trades'] or 0
                wins = row['wins'] or 0
                result[trade_type] = {
                    'total_trades': total,
                    'wins': wins,
                    'losses': row['losses'] or 0,
                    'win_rate': (wins / total * 100) if total > 0 else 0,
                    'avg_cont_score': float(row['avg_cont_score']) if row['avg_cont_score'] else 0,
                    'avg_rej_score': float(row['avg_rej_score']) if row['avg_rej_score'] else 0
                }

            return result

        except Exception as e:
            logger.error(f"Error fetching indicator_refinement summary: {e}")
            self.conn.rollback()
            return {}

    def get_indicator_refinement_count(self) -> int:
        """
        Get count of records in indicator_refinement table.

        Returns:
            Number of records in indicator_refinement table
        """
        self._ensure_connected()

        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM indicator_refinement")
                result = cur.fetchone()
                return result[0] if result else 0
        except Exception as e:
            logger.error(f"Error counting indicator_refinement: {e}")
            return 0


_client = None

def get_client() -> SupabaseClient:
    global _client
    if _client is None:
        _client = SupabaseClient()
        _client.connect()
    return _client
