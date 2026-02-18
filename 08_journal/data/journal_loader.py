"""
Journal Trade Loader - Singleton data layer for the journal viewer.
Epoch Trading System - XIII Trading LLC

Queries j_trades_m5_r_win for pre-computed data (with fallback to
journal_trades if j_trades_m5_r_win is not yet populated).

Follows the same pattern as 11_trade_reel/data/highlight_loader.py:
- Singleton class with _ensure_connected
- RealDictCursor for dict-based row access
- Reconnect-on-stale for long-running PyQt sessions
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import date, time
from typing import List, Optional, Tuple, Dict
from decimal import Decimal
import logging
import pandas as pd

logger = logging.getLogger(__name__)

# DB config — matches journal_db.py and 00_shared/config/credentials.py
DB_CONFIG = {
    "host": "db.pdbmcskznoaiybdiobje.supabase.co",
    "port": 5432,
    "database": "postgres",
    "user": "postgres",
    "password": "guid-saltation-covet",
    "sslmode": "require",
}


class JournalTradeLoader:
    """
    Load journal trades from j_trades_m5_r_win (pre-computed) with
    fallback to journal_trades.

    Primary table: j_trades_m5_r_win
        - Has all ATR/R-level data pre-computed (stop_price, r1_price, etc.)
        - Direct column names (no m5_ prefix): stop_price, stop_distance, etc.

    Fallback table: journal_trades
        - Raw journal data, ATR/R computed on-the-fly by trade_adapter.py

    Supporting tables:
        - zones + setups (zone overlays)
        - j_m1_indicator_bars (ramp-up / post-trade indicator data)
        - j_m1_bars (intraday VbP bars)
    """

    def __init__(self):
        self.conn = None

    def connect(self) -> bool:
        """Establish database connection."""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            logger.info("JournalTradeLoader: Connected to Supabase")
            return True
        except Exception as e:
            logger.error(f"JournalTradeLoader: Failed to connect: {e}")
            return False

    def disconnect(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def _ensure_connected(self) -> bool:
        """Reconnect if needed. Returns True if connected."""
        if not self.conn or self.conn.closed:
            return self.connect()
        return True

    # =========================================================================
    # TRADE FETCHING (primary method)
    # =========================================================================

    def fetch_trades(
        self,
        date_from: date,
        date_to: date,
        symbol: Optional[str] = None,
        direction: Optional[str] = None,
        account: Optional[str] = None,
    ) -> List[Dict]:
        """
        Fetch trades for the journal viewer.

        Strategy:
        1. Try j_trades_m5_r_win first (has pre-computed ATR/R data)
        2. Fall back to journal_trades if j_trades_m5_r_win is empty or missing

        Args:
            date_from: Start date (inclusive)
            date_to: End date (inclusive)
            symbol: Filter by ticker symbol
            direction: Filter by direction (LONG/SHORT)
            account: Filter by account (SIM/LIVE)

        Returns:
            List of trade dicts (RealDictCursor rows)
        """
        if not self._ensure_connected():
            logger.warning("Skipping fetch_trades - no database connection")
            return []

        # Try pre-computed table first
        rows = self._fetch_from_precomputed(date_from, date_to, symbol, direction, account)

        if rows:
            logger.info(f"Loaded {len(rows)} trades from j_trades_m5_r_win")
            return rows

        # Fallback to journal_trades
        logger.info("j_trades_m5_r_win empty or unavailable, falling back to journal_trades")
        return self._fetch_from_journal(date_from, date_to, symbol, direction, account)

    def _fetch_from_precomputed(
        self,
        date_from: date,
        date_to: date,
        symbol: Optional[str] = None,
        direction: Optional[str] = None,
        account: Optional[str] = None,
    ) -> List[Dict]:
        """Fetch from j_trades_m5_r_win (pre-computed ATR/R data)."""
        query = """
            SELECT * FROM j_trades_m5_r_win
            WHERE trade_date >= %s AND trade_date <= %s
        """
        params: list = [date_from, date_to]

        if symbol:
            query += " AND UPPER(symbol) = UPPER(%s)"
            params.append(symbol)

        if direction:
            query += " AND UPPER(direction) = UPPER(%s)"
            params.append(direction)

        if account:
            query += " AND account = %s"
            params.append(account)

        query += " ORDER BY trade_date, entry_time"

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]
        except psycopg2.errors.UndefinedTable:
            logger.warning("Table j_trades_m5_r_win does not exist yet")
            if self.conn and not self.conn.closed:
                self.conn.rollback()
            return []
        except Exception as e:
            logger.error(f"Error fetching from j_trades_m5_r_win: {e}")
            if self.conn and not self.conn.closed:
                self.conn.rollback()
            return []

    def _fetch_from_journal(
        self,
        date_from: date,
        date_to: date,
        symbol: Optional[str] = None,
        direction: Optional[str] = None,
        account: Optional[str] = None,
    ) -> List[Dict]:
        """Fetch from journal_trades (raw journal data, fallback)."""
        query = """
            SELECT * FROM journal_trades
            WHERE trade_date >= %s AND trade_date <= %s
        """
        params: list = [date_from, date_to]

        if symbol:
            query += " AND UPPER(symbol) = UPPER(%s)"
            params.append(symbol)

        if direction:
            query += " AND UPPER(direction) = UPPER(%s)"
            params.append(direction)

        if account:
            query += " AND account = %s"
            params.append(account)

        query += " ORDER BY trade_date, entry_time"

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching from journal_trades: {e}")
            if self.conn and not self.conn.closed:
                self.conn.rollback()
            return []

    # =========================================================================
    # ZONE DATA
    # =========================================================================

    def fetch_zones_for_trade(self, ticker: str, trade_date: date) -> List[Dict]:
        """
        Fetch PRIMARY and SECONDARY setups directly from the setups table.

        The setups table PK is (date, ticker_id, setup_type), guaranteeing
        at most 1 PRIMARY and 1 SECONDARY per ticker per day. Each row
        already contains hvn_poc, zone_high, zone_low — no zones JOIN needed.

        Returns:
            List of setup dicts (max 2) with setup_type, hvn_poc, zone_high,
            zone_low, direction, zone_id.
        """
        if not self._ensure_connected():
            logger.warning("Skipping fetch_zones_for_trade - no database connection")
            return []

        query = """
            SELECT setup_type, hvn_poc, zone_high, zone_low,
                   direction, zone_id, ticker, date
            FROM setups
            WHERE ticker = %s AND date = %s
              AND setup_type IN ('PRIMARY', 'SECONDARY')
            ORDER BY setup_type
        """

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (ticker.upper(), trade_date))
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching setups for {ticker} on {trade_date}: {e}")
            if self.conn and not self.conn.closed:
                self.conn.rollback()
            return []

    def fetch_hvn_pocs(self, ticker: str, trade_date: date) -> List[float]:
        """
        Fetch HVN POC prices from zones table for a ticker-date pair.

        Returns:
            List of POC prices (floats), filtering out nulls.
        """
        if not self._ensure_connected():
            logger.warning("Skipping fetch_hvn_pocs - no database connection")
            return []

        query = """
            SELECT hvn_poc FROM zones
            WHERE ticker = %s AND date = %s AND hvn_poc IS NOT NULL
        """

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (ticker.upper(), trade_date))
                return [float(row[0]) for row in cur.fetchall() if row[0] is not None]
        except Exception as e:
            logger.error(f"Error fetching hvn_pocs for {ticker}: {e}")
            if self.conn and not self.conn.closed:
                self.conn.rollback()
            return []

    # =========================================================================
    # INDICATOR BAR DATA (ramp-up / post-trade)
    # =========================================================================

    def fetch_rampup_data(self, ticker: str, trade_date: date, entry_time: time) -> pd.DataFrame:
        """
        Fetch M1 indicator bars leading up to entry (ramp-up context).

        Returns up to 45 bars before entry_time in chronological order.
        Uses j_m1_indicator_bars table.

        Args:
            ticker: Ticker symbol
            trade_date: Trade date
            entry_time: Entry time (exclusive upper bound)

        Returns:
            DataFrame with indicator bar columns, chronological order
        """
        if not self._ensure_connected():
            logger.warning("Skipping fetch_rampup_data - no database connection")
            return pd.DataFrame()

        query = """
            SELECT * FROM j_m1_indicator_bars
            WHERE ticker = %s AND bar_date = %s AND bar_time < %s
            ORDER BY bar_time DESC
            LIMIT 45
        """

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (ticker.upper(), trade_date, entry_time))
                rows = cur.fetchall()

                if not rows:
                    return pd.DataFrame()

                df = pd.DataFrame([dict(r) for r in rows])
                df = self._convert_decimal_columns(df)

                # Reverse to chronological order
                df = df.iloc[::-1].reset_index(drop=True)

                logger.info(f"Rampup: {ticker} {trade_date} < {entry_time} ({len(df)} bars)")
                return df
        except psycopg2.errors.UndefinedTable:
            logger.warning("Table j_m1_indicator_bars does not exist yet")
            if self.conn and not self.conn.closed:
                self.conn.rollback()
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error fetching rampup data: {e}")
            if self.conn and not self.conn.closed:
                self.conn.rollback()
            return pd.DataFrame()

    def fetch_posttrade_data(self, ticker: str, trade_date: date, entry_time: time) -> pd.DataFrame:
        """
        Fetch M1 indicator bars from entry onward (post-trade analysis).

        Returns up to 46 bars from entry_time (inclusive) in chronological order.
        Uses j_m1_indicator_bars table.

        Args:
            ticker: Ticker symbol
            trade_date: Trade date
            entry_time: Entry time (inclusive lower bound)

        Returns:
            DataFrame with indicator bar columns, chronological order
        """
        if not self._ensure_connected():
            logger.warning("Skipping fetch_posttrade_data - no database connection")
            return pd.DataFrame()

        query = """
            SELECT * FROM j_m1_indicator_bars
            WHERE ticker = %s AND bar_date = %s AND bar_time >= %s
            ORDER BY bar_time ASC
            LIMIT 46
        """

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (ticker.upper(), trade_date, entry_time))
                rows = cur.fetchall()

                if not rows:
                    return pd.DataFrame()

                df = pd.DataFrame([dict(r) for r in rows])
                df = self._convert_decimal_columns(df)

                logger.info(f"Posttrade: {ticker} {trade_date} >= {entry_time} ({len(df)} bars)")
                return df
        except psycopg2.errors.UndefinedTable:
            logger.warning("Table j_m1_indicator_bars does not exist yet")
            if self.conn and not self.conn.closed:
                self.conn.rollback()
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error fetching posttrade data: {e}")
            if self.conn and not self.conn.closed:
                self.conn.rollback()
            return pd.DataFrame()

    # =========================================================================
    # EPOCH / VBP DATA
    # =========================================================================

    def fetch_epoch_start_date(self, ticker: str, trade_date: date) -> Optional[date]:
        """
        Fetch the earliest zone date for a ticker up to trade_date.
        This serves as the epoch start for Volume by Price calculation.

        Args:
            ticker: Ticker symbol
            trade_date: Trade/analysis date

        Returns:
            Earliest zone date, or None if not found
        """
        if not self._ensure_connected():
            logger.warning("Skipping fetch_epoch_start_date - no database connection")
            return None

        query = """
            SELECT MIN(date) FROM zones
            WHERE ticker = %s AND date <= %s
        """

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (ticker.upper(), trade_date))
                row = cur.fetchone()
                if row and row[0]:
                    return row[0]
                return None
        except Exception as e:
            logger.error(f"Error fetching epoch_start_date for {ticker}: {e}")
            if self.conn and not self.conn.closed:
                self.conn.rollback()
            return None

    def fetch_intraday_vbp_bars(self, ticker: str, trade_date: date, entry_time: time) -> pd.DataFrame:
        """
        Fetch M1 bars from j_m1_bars for intraday Volume by Price.
        Returns bars from 04:00 ET on trade_date up to (not including) entry_time.

        Args:
            ticker: Ticker symbol
            trade_date: Trade date
            entry_time: Trade entry time (exclusive upper bound)

        Returns:
            DataFrame with open, high, low, close, volume columns
        """
        if not self._ensure_connected():
            logger.warning("Skipping fetch_intraday_vbp_bars - no database connection")
            return pd.DataFrame()

        query = """
            SELECT bar_time, open, high, low, close, volume
            FROM j_m1_bars
            WHERE ticker = %s
              AND bar_date = %s
              AND bar_time >= '04:00'
              AND bar_time < %s
            ORDER BY bar_time
        """

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (ticker.upper(), trade_date, entry_time))
                rows = cur.fetchall()

                if not rows:
                    return pd.DataFrame()

                df = pd.DataFrame([dict(r) for r in rows])
                df = self._convert_decimal_columns(df)

                logger.info(f"Intraday VbP: {ticker} {trade_date} 04:00->{entry_time} ({len(df)} M1 bars)")
                return df
        except psycopg2.errors.UndefinedTable:
            logger.warning("Table j_m1_bars does not exist yet")
            if self.conn and not self.conn.closed:
                self.conn.rollback()
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error fetching intraday vbp bars: {e}")
            if self.conn and not self.conn.closed:
                self.conn.rollback()
            return pd.DataFrame()

    # =========================================================================
    # FILTER HELPERS (for UI dropdowns)
    # =========================================================================

    def get_available_tickers(self, date_from: date, date_to: date) -> List[str]:
        """
        Get unique ticker symbols within a date range.

        Returns:
            Sorted list of ticker strings
        """
        if not self._ensure_connected():
            logger.warning("Skipping get_available_tickers - no database connection")
            return []

        query = """
            SELECT DISTINCT symbol FROM journal_trades
            WHERE trade_date >= %s AND trade_date <= %s
            ORDER BY symbol
        """

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (date_from, date_to))
                return [row[0] for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching available tickers: {e}")
            return []

    def get_available_accounts(self) -> List[str]:
        """
        Get unique account identifiers (SIM, LIVE, etc.).

        Returns:
            Sorted list of account strings
        """
        if not self._ensure_connected():
            logger.warning("Skipping get_available_accounts - no database connection")
            return []

        query = """
            SELECT DISTINCT account FROM journal_trades
            WHERE account IS NOT NULL AND account != ''
            ORDER BY account
        """

        try:
            with self.conn.cursor() as cur:
                cur.execute(query)
                return [row[0] for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching available accounts: {e}")
            return []

    def get_date_range(self) -> Tuple[Optional[date], Optional[date]]:
        """
        Get min/max trade_date from journal_trades.

        Returns:
            Tuple of (earliest_date, latest_date), or (None, None)
        """
        if not self._ensure_connected():
            logger.warning("Skipping get_date_range - no database connection")
            return None, None

        query = "SELECT MIN(trade_date), MAX(trade_date) FROM journal_trades"

        try:
            with self.conn.cursor() as cur:
                cur.execute(query)
                row = cur.fetchone()
                if row:
                    return row[0], row[1]
                return None, None
        except Exception as e:
            logger.error(f"Error fetching date range: {e}")
            return None, None

    # =========================================================================
    # UTILITIES
    # =========================================================================

    @staticmethod
    def _convert_decimal_columns(df: pd.DataFrame) -> pd.DataFrame:
        """Convert Decimal columns to float for Plotly compatibility."""
        for col in df.columns:
            if df[col].dtype == object and len(df) > 0:
                sample = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
                if isinstance(sample, Decimal):
                    df[col] = df[col].apply(lambda x: float(x) if isinstance(x, Decimal) else x)
        return df


# =============================================================================
# Singleton
# =============================================================================

_loader: Optional[JournalTradeLoader] = None


def get_journal_loader() -> JournalTradeLoader:
    """Get or create the JournalTradeLoader singleton."""
    global _loader
    if _loader is None:
        _loader = JournalTradeLoader()
        _loader.connect()
    return _loader
