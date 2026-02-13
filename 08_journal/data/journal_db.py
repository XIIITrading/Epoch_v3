"""
Supabase operations for the Epoch Trading Journal.

Follows patterns from:
- 00_shared/data/supabase/client.py (connection management, context manager)
- 06_training/data/supabase_client.py (_ensure_connected, RealDictCursor)

Table: journal_trades
    - Separate from existing `trades` table to avoid conflicts
    - Stores aggregated trade data (fills are ephemeral)
    - account field distinguishes SIM vs LIVE trades

Usage:
    with JournalDB() as db:
        count = db.save_daily_log(log)
        trades = db.get_trades_by_date(date(2026, 1, 28))
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import date
from typing import List, Optional, Dict
import logging

logger = logging.getLogger(__name__)

# DB config — matches 00_shared/config/credentials.py and 06_training/config.py
DB_CONFIG = {
    "host": "db.pdbmcskznoaiybdiobje.supabase.co",
    "port": 5432,
    "database": "postgres",
    "user": "postgres",
    "password": "guid-saltation-covet",
    "sslmode": "require",
}


class JournalDB:
    """
    Supabase operations for the trading journal.

    Supports context manager:
        with JournalDB() as db:
            db.save_trade(trade)

    Or manual connection:
        db = JournalDB()
        db.connect()
        db.save_trade(trade)
        db.close()
    """

    TABLE = "journal_trades"

    def __init__(self):
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
    # WRITE OPERATIONS
    # =========================================================================

    def save_trade(self, trade, source_file: str = "") -> bool:
        """
        Save a single Trade to journal_trades.
        Uses ON CONFLICT to handle re-imports cleanly (upsert).

        Args:
            trade: Trade model instance
            source_file: Original CSV filename

        Returns:
            True if successful
        """
        self._ensure_connected()

        row = trade.to_db_row(source_file=source_file)

        query = f"""
            INSERT INTO {self.TABLE} (
                trade_id, trade_date, symbol, direction, account,
                entry_price, entry_time, entry_qty, entry_fills,
                exit_price, exit_time, exit_qty, exit_fills,
                pnl_dollars, pnl_total, pnl_r, outcome, duration_seconds,
                zone_id, model, stop_price, notes,
                source_file, is_closed, updated_at
            ) VALUES (
                %(trade_id)s, %(trade_date)s, %(symbol)s, %(direction)s, %(account)s,
                %(entry_price)s, %(entry_time)s, %(entry_qty)s, %(entry_fills)s,
                %(exit_price)s, %(exit_time)s, %(exit_qty)s, %(exit_fills)s,
                %(pnl_dollars)s, %(pnl_total)s, %(pnl_r)s, %(outcome)s, %(duration_seconds)s,
                %(zone_id)s, %(model)s, %(stop_price)s, %(notes)s,
                %(source_file)s, %(is_closed)s, NOW()
            )
            ON CONFLICT (trade_id) DO UPDATE SET
                trade_date = EXCLUDED.trade_date,
                symbol = EXCLUDED.symbol,
                direction = EXCLUDED.direction,
                account = EXCLUDED.account,
                entry_price = EXCLUDED.entry_price,
                entry_time = EXCLUDED.entry_time,
                entry_qty = EXCLUDED.entry_qty,
                entry_fills = EXCLUDED.entry_fills,
                exit_price = EXCLUDED.exit_price,
                exit_time = EXCLUDED.exit_time,
                exit_qty = EXCLUDED.exit_qty,
                exit_fills = EXCLUDED.exit_fills,
                pnl_dollars = EXCLUDED.pnl_dollars,
                pnl_total = EXCLUDED.pnl_total,
                pnl_r = EXCLUDED.pnl_r,
                outcome = EXCLUDED.outcome,
                duration_seconds = EXCLUDED.duration_seconds,
                source_file = EXCLUDED.source_file,
                is_closed = EXCLUDED.is_closed,
                updated_at = NOW()
        """

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, row)
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving trade {row.get('trade_id')}: {e}")
            self.conn.rollback()
            return False

    def save_daily_log(self, log) -> int:
        """
        Save all trades from a DailyTradeLog to the database.

        Args:
            log: DailyTradeLog model instance

        Returns:
            Count of trades saved successfully
        """
        saved = 0
        for trade in log.trades:
            if self.save_trade(trade, source_file=log.source_file):
                saved += 1
        return saved

    def update_review_fields(
        self,
        trade_id: str,
        zone_id: Optional[str] = None,
        model: Optional[str] = None,
        stop_price: Optional[float] = None,
        notes: Optional[str] = None,
    ) -> bool:
        """
        Update review fields for a trade (Sprint 3 review page).
        Also recalculates pnl_r if stop_price is provided.

        Returns:
            True if successful
        """
        self._ensure_connected()

        # If stop_price is set, recalculate pnl_r
        pnl_r = None
        if stop_price is not None:
            trade_row = self.get_trade(trade_id)
            if trade_row and trade_row.get("entry_price") and trade_row.get("pnl_dollars"):
                risk = abs(float(trade_row["entry_price"]) - stop_price)
                if risk != 0:
                    pnl_r = float(trade_row["pnl_dollars"]) / risk

        query = f"""
            UPDATE {self.TABLE}
            SET zone_id = %s,
                model = %s,
                stop_price = %s,
                notes = %s,
                pnl_r = %s,
                updated_at = NOW()
            WHERE trade_id = %s
        """

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (zone_id, model, stop_price, notes, pnl_r, trade_id))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating review for {trade_id}: {e}")
            self.conn.rollback()
            return False

    def delete_session(self, trade_date: date) -> int:
        """
        Delete all trades for a given date (for re-import).

        Returns:
            Count of trades deleted
        """
        self._ensure_connected()

        query = f"DELETE FROM {self.TABLE} WHERE trade_date = %s"

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (trade_date,))
                count = cur.rowcount
            self.conn.commit()
            return count
        except Exception as e:
            logger.error(f"Error deleting session {trade_date}: {e}")
            self.conn.rollback()
            return 0

    # =========================================================================
    # READ OPERATIONS
    # =========================================================================

    def get_trade(self, trade_id: str) -> Optional[Dict]:
        """
        Get a single trade by trade_id.

        Returns:
            Dict with trade data, or None if not found
        """
        self._ensure_connected()

        query = f"SELECT * FROM {self.TABLE} WHERE trade_id = %s"

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (trade_id,))
                row = cur.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting trade {trade_id}: {e}")
            return None

    def get_trades_by_date(self, trade_date: date) -> List[Dict]:
        """
        Get all trades for a given date.

        Returns:
            List of trade row dicts, ordered by entry_time
        """
        self._ensure_connected()

        query = f"""
            SELECT * FROM {self.TABLE}
            WHERE trade_date = %s
            ORDER BY entry_time
        """

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (trade_date,))
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error getting trades for {trade_date}: {e}")
            return []

    def get_trades_by_range(
        self,
        date_from: date,
        date_to: date,
        symbol: Optional[str] = None,
        account: Optional[str] = None,
    ) -> List[Dict]:
        """
        Get trades within a date range with optional filters.

        Returns:
            List of trade row dicts
        """
        self._ensure_connected()

        query = f"""
            SELECT * FROM {self.TABLE}
            WHERE trade_date >= %s AND trade_date <= %s
        """
        params = [date_from, date_to]

        if symbol:
            query += " AND symbol = %s"
            params.append(symbol.upper())

        if account:
            query += " AND account = %s"
            params.append(account)

        query += " ORDER BY trade_date, entry_time"

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error getting trades for range {date_from} to {date_to}: {e}")
            return []

    def get_all_dates(self) -> List[date]:
        """
        Get all unique dates that have journal entries.

        Returns:
            Sorted list of dates (most recent first)
        """
        self._ensure_connected()

        query = f"""
            SELECT DISTINCT trade_date FROM {self.TABLE}
            ORDER BY trade_date DESC
        """

        try:
            with self.conn.cursor() as cur:
                cur.execute(query)
                return [row[0] for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error getting dates: {e}")
            return []

    def get_all_accounts(self) -> List[str]:
        """
        Get all unique account identifiers.
        Useful for SIM vs LIVE filtering.

        Returns:
            Sorted list of account strings
        """
        self._ensure_connected()

        query = f"""
            SELECT DISTINCT account FROM {self.TABLE}
            WHERE account IS NOT NULL AND account != ''
            ORDER BY account
        """

        try:
            with self.conn.cursor() as cur:
                cur.execute(query)
                return [row[0] for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error getting accounts: {e}")
            return []

    def get_zones_for_ticker(self, ticker: str, trade_date: date) -> List[Dict]:
        """
        Fetch zones from the zones table for a ticker on a given date,
        enriched with setup_type (PRIMARY/SECONDARY) from the setups table.

        Uses a LEFT JOIN to setups so each zone gets its setup_type.
        The setups table is the source of truth for PRIMARY vs SECONDARY.

        Returns:
            List of zone dicts with zone_id, zone_high, zone_low, hvn_poc,
            rank, score, is_filtered, setup_type, sorted by score DESC.
        """
        self._ensure_connected()

        query = """
            SELECT z.zone_id, z.ticker, z.date, z.zone_high, z.zone_low,
                   z.hvn_poc, z.direction, z.rank, z.score, z.is_filtered,
                   s.setup_type
            FROM zones z
            LEFT JOIN setups s
                ON z.date = s.date AND z.zone_id = s.zone_id
            WHERE z.ticker = %s AND z.date = %s
            ORDER BY z.score DESC NULLS LAST
        """

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (ticker.upper(), trade_date))
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching zones for {ticker} on {trade_date}: {e}")
            self.conn.rollback()
            return []

    def trade_exists(self, trade_id: str) -> bool:
        """
        Check if a trade_id already exists in the database.
        Useful for duplicate detection before import.

        Returns:
            True if trade exists
        """
        self._ensure_connected()

        query = f"SELECT EXISTS(SELECT 1 FROM {self.TABLE} WHERE trade_id = %s)"

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (trade_id,))
                return cur.fetchone()[0]
        except Exception as e:
            logger.error(f"Error checking trade existence: {e}")
            return False

    # =========================================================================
    # NOTION SYNC TRACKING
    # =========================================================================

    def mark_notion_synced(
        self,
        trade_id: str,
        page_id: str,
        page_url: str,
    ) -> bool:
        """
        Record the Notion page_id and URL for a trade after successful
        page creation or update via MCP.

        Args:
            trade_id: The journal trade ID
            page_id: Notion page UUID (with dashes)
            page_url: Full Notion page URL

        Returns:
            True if successful
        """
        self._ensure_connected()

        query = f"""
            UPDATE {self.TABLE}
            SET notion_page_id = %s,
                notion_url = %s,
                notion_synced_at = NOW()
            WHERE trade_id = %s
        """

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (page_id, page_url, trade_id))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error marking notion sync for {trade_id}: {e}")
            self.conn.rollback()
            return False

    def fetch_unsynced_trades(self, up_to_date: date = None) -> List[Dict]:
        """
        Fetch all trades where notion_page_id IS NULL,
        optionally limited to trades on or before up_to_date.

        Returns:
            List of trade dicts ordered by trade_date, entry_time
        """
        self._ensure_connected()

        if up_to_date is None:
            up_to_date = date.today()

        query = f"""
            SELECT * FROM {self.TABLE}
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
