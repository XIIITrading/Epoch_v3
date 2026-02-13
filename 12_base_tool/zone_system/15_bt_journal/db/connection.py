"""
Epoch Backtest Journal - Database Connection
Supabase PostgreSQL connection manager.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import Generator, Dict, List, Any, Optional
from datetime import date, timedelta
import sys
from pathlib import Path

# Add parent to path for config
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import DB_CONFIG


class EpochDatabase:
    """Connection manager for Epoch Supabase database."""

    def __init__(self, config: Dict = None):
        """
        Initialize database connection manager.

        Args:
            config: Database configuration dict. Uses default if not provided.
        """
        self.config = config or DB_CONFIG
        self._conn = None

    @contextmanager
    def connection(self) -> Generator[psycopg2.extensions.connection, None, None]:
        """Context manager for database connections."""
        conn = psycopg2.connect(**self.config)
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def cursor(self, dict_cursor: bool = True):
        """Context manager for database cursors."""
        with self.connection() as conn:
            cursor_factory = RealDictCursor if dict_cursor else None
            with conn.cursor(cursor_factory=cursor_factory) as cur:
                yield cur

    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute query and return results as list of dicts."""
        with self.cursor() as cur:
            cur.execute(query, params)
            return [dict(row) for row in cur.fetchall()]

    def execute_scalar(self, query: str, params: tuple = None) -> Any:
        """Execute query and return single value."""
        with self.cursor(dict_cursor=False) as cur:
            cur.execute(query, params)
            result = cur.fetchone()
            return result[0] if result else None

    # =========================================================================
    # Convenience Methods
    # =========================================================================

    def get_available_dates(self) -> List[date]:
        """Get all dates with data in the database."""
        query = "SELECT date FROM daily_sessions ORDER BY date DESC"
        results = self.execute_query(query)
        return [r["date"] for r in results]

    def get_date_range(self) -> tuple[Optional[date], Optional[date]]:
        """Get min and max dates in database."""
        query = "SELECT MIN(date), MAX(date) FROM daily_sessions"
        with self.cursor(dict_cursor=False) as cur:
            cur.execute(query)
            result = cur.fetchone()
            return (result[0], result[1]) if result else (None, None)

    def get_trades(
        self,
        start_date: date = None,
        end_date: date = None,
        tickers: List[str] = None,
        models: List[str] = None
    ) -> List[Dict]:
        """
        Load trades with optional filters.

        Args:
            start_date: Filter trades on or after this date
            end_date: Filter trades on or before this date
            tickers: Filter by specific tickers
            models: Filter by specific models (EPCH1-4)

        Returns:
            List of trade records as dicts
        """
        query = """
            SELECT
                t.trade_id, t.date, t.ticker, t.model, t.zone_type,
                t.direction, t.zone_high, t.zone_low, t.entry_price,
                t.entry_time, t.stop_price, t.target_3r, t.target_calc,
                t.target_used, t.exit_price, t.exit_time, t.exit_reason,
                t.pnl_dollars, t.pnl_r, t.risk, t.is_winner
            FROM trades t
            WHERE 1=1
        """
        params = []

        if start_date:
            query += " AND t.date >= %s"
            params.append(start_date)
        if end_date:
            query += " AND t.date <= %s"
            params.append(end_date)
        if tickers:
            placeholders = ",".join(["%s"] * len(tickers))
            query += f" AND t.ticker IN ({placeholders})"
            params.extend(tickers)
        if models:
            placeholders = ",".join(["%s"] * len(models))
            query += f" AND t.model IN ({placeholders})"
            params.extend(models)

        query += " ORDER BY t.date DESC, t.entry_time"

        return self.execute_query(query, tuple(params) if params else None)

    def get_trades_with_entry_events(
        self,
        start_date: date = None,
        end_date: date = None
    ) -> List[Dict]:
        """Load trades joined with entry event data."""
        query = """
            SELECT
                t.*,
                e.health_score, e.health_label, e.vwap_aligned,
                e.trend_aligned, e.structure_aligned, e.dominant_structure,
                e.volume_delta_pct, e.sma9_vs_sma21,
                e.m5_structure, e.m15_structure, e.h1_structure, e.h4_structure,
                e.entry_vs_vwap, e.volume_trend,
                e.vol_delta_class, e.prior_bar_qual,
                e.entry_vs_sma9, e.entry_vs_sma21
            FROM trades t
            LEFT JOIN trade_entry_events e ON t.trade_id = e.trade_id
            WHERE 1=1
        """
        params = []

        if start_date:
            query += " AND t.date >= %s"
            params.append(start_date)
        if end_date:
            query += " AND t.date <= %s"
            params.append(end_date)

        query += " ORDER BY t.date DESC, t.entry_time"

        return self.execute_query(query, tuple(params) if params else None)

    def get_exit_events(self, trade_ids: List[str] = None) -> List[Dict]:
        """Load exit events, optionally filtered by trade IDs."""
        query = "SELECT * FROM trade_exit_events WHERE 1=1"
        params = []

        if trade_ids:
            placeholders = ",".join(["%s"] * len(trade_ids))
            query += f" AND trade_id IN ({placeholders})"
            params.extend(trade_ids)

        query += " ORDER BY trade_id, event_seq"

        return self.execute_query(query, tuple(params) if params else None)

    def get_trade_count(self, start_date: date = None, end_date: date = None) -> int:
        """Get count of trades in date range."""
        query = "SELECT COUNT(*) FROM trades WHERE 1=1"
        params = []

        if start_date:
            query += " AND date >= %s"
            params.append(start_date)
        if end_date:
            query += " AND date <= %s"
            params.append(end_date)

        return self.execute_scalar(query, tuple(params) if params else None)