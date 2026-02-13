"""
Epoch Trading System - Supabase Client
=======================================

Centralized Supabase/PostgreSQL client for database operations.
Provides a clean interface for all Epoch modules.

Usage:
    from shared.data.supabase import SupabaseClient

    db = SupabaseClient()
    if db.connect():
        zones = db.get_zones("AAPL")
        db.close()
"""

import psycopg2
import psycopg2.extras
import pandas as pd
from datetime import datetime, date
from typing import Optional, Dict, List, Any, Union
from contextlib import contextmanager

from ...config.credentials import SUPABASE_DB_CONFIG


class SupabaseClient:
    """
    Centralized Supabase/PostgreSQL client.

    Handles all database operations with:
    - Connection management
    - Query execution
    - Data loading and saving
    - Transaction support
    """

    def __init__(
        self,
        session_date: Optional[date] = None,
        verbose: bool = False,
    ):
        """
        Initialize Supabase client.

        Args:
            session_date: Trading session date (defaults to today)
            verbose: Enable verbose logging
        """
        self.session_date = session_date or date.today()
        self.verbose = verbose
        self._conn = None
        self._cursor = None

    def connect(self) -> bool:
        """
        Connect to Supabase PostgreSQL database.

        Returns:
            True if connected successfully, False otherwise
        """
        try:
            self._conn = psycopg2.connect(**SUPABASE_DB_CONFIG)
            self._cursor = self._conn.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            )

            if self.verbose:
                print(f"[Supabase] Connected to {SUPABASE_DB_CONFIG['host']}")
            return True

        except Exception as e:
            print(f"[Supabase] Connection error: {e}")
            return False

    def close(self):
        """Close database connection."""
        if self._cursor:
            self._cursor.close()
        if self._conn:
            self._conn.close()
        if self.verbose:
            print("[Supabase] Connection closed")

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def set_session_date(self, session_date: date):
        """Update the session date for queries."""
        self.session_date = session_date
        if self.verbose:
            print(f"[Supabase] Session date set to: {self.session_date}")

    # =========================================================================
    # ZONE DATA
    # =========================================================================

    def get_zones(
        self,
        ticker: Optional[str] = None,
        session_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """
        Get zone data from zones table.

        Args:
            ticker: Optional filter by ticker symbol
            session_date: Optional override for session date

        Returns:
            DataFrame with zone data
        """
        query_date = session_date or self.session_date

        query = """
            SELECT
                ticker_id, ticker, date, price, direction, zone_id,
                hvn_poc, zone_high, zone_low, overlap_count as overlaps,
                score, rank, confluences,
                is_epch_bull as epch_bull, is_epch_bear as epch_bear,
                epch_bull_price, epch_bear_price,
                epch_bull_target, epch_bear_target
            FROM zones
            WHERE date = %s
        """
        params = [query_date]

        if ticker:
            query += " AND UPPER(ticker) = UPPER(%s)"
            params.append(ticker)

        query += " ORDER BY ticker, score DESC"

        return self._execute_query(query, params)

    def get_primary_zone(
        self,
        ticker: str,
        session_date: Optional[date] = None,
    ) -> Optional[Dict]:
        """
        Get PRIMARY zone from setups table.

        Args:
            ticker: Stock symbol
            session_date: Optional override for session date

        Returns:
            Dict with zone info or None
        """
        query_date = session_date or self.session_date

        query = """
            SELECT
                ticker, direction, ticker_id, zone_id,
                hvn_poc, zone_high, zone_low,
                target_id, target_price as target, risk_reward as r_r
            FROM setups
            WHERE date = %s
              AND UPPER(ticker) = UPPER(%s)
              AND setup_type = 'PRIMARY'
        """

        try:
            self._cursor.execute(query, [query_date, ticker])
            row = self._cursor.fetchone()

            if not row:
                return None

            return dict(row)

        except Exception as e:
            print(f"[Supabase] Error getting primary zone: {e}")
            return None

    def get_secondary_zone(
        self,
        ticker: str,
        session_date: Optional[date] = None,
    ) -> Optional[Dict]:
        """
        Get SECONDARY zone from setups table.

        Args:
            ticker: Stock symbol
            session_date: Optional override for session date

        Returns:
            Dict with zone info or None
        """
        query_date = session_date or self.session_date

        query = """
            SELECT
                ticker, direction, ticker_id, zone_id,
                hvn_poc, zone_high, zone_low,
                target_id, target_price as target, risk_reward as r_r
            FROM setups
            WHERE date = %s
              AND UPPER(ticker) = UPPER(%s)
              AND setup_type = 'SECONDARY'
        """

        try:
            self._cursor.execute(query, [query_date, ticker])
            row = self._cursor.fetchone()
            return dict(row) if row else None

        except Exception as e:
            print(f"[Supabase] Error getting secondary zone: {e}")
            return None

    # =========================================================================
    # BAR DATA
    # =========================================================================

    def get_bar_data(
        self,
        ticker: str,
        session_date: Optional[date] = None,
    ) -> Optional[Dict]:
        """
        Get bar data metrics for a ticker.

        Args:
            ticker: Stock symbol
            session_date: Optional override for session date

        Returns:
            Dict with bar data or None
        """
        query_date = session_date or self.session_date

        query = """
            SELECT *
            FROM bar_data
            WHERE date = %s
              AND UPPER(ticker) = UPPER(%s)
        """

        try:
            self._cursor.execute(query, [query_date, ticker])
            row = self._cursor.fetchone()
            return dict(row) if row else None

        except Exception as e:
            print(f"[Supabase] Error getting bar data: {e}")
            return None

    def get_hvn_pocs(
        self,
        ticker: str,
        session_date: Optional[date] = None,
    ) -> List[float]:
        """
        Get HVN POC levels for a ticker.

        Args:
            ticker: Stock symbol
            session_date: Optional override for session date

        Returns:
            List of POC price levels
        """
        query_date = session_date or self.session_date

        query = """
            SELECT hvn_poc1, hvn_poc2, hvn_poc3, hvn_poc4, hvn_poc5,
                   hvn_poc6, hvn_poc7, hvn_poc8, hvn_poc9, hvn_poc10
            FROM bar_data
            WHERE date = %s
              AND UPPER(ticker) = UPPER(%s)
        """

        try:
            self._cursor.execute(query, [query_date, ticker])
            row = self._cursor.fetchone()

            if not row:
                return []

            # Extract non-null POC values
            pocs = []
            for i in range(1, 11):
                poc = row.get(f"hvn_poc{i}")
                if poc is not None:
                    pocs.append(float(poc))

            return pocs

        except Exception as e:
            print(f"[Supabase] Error getting HVN POCs: {e}")
            return []

    # =========================================================================
    # TRADE DATA
    # =========================================================================

    def get_trades(
        self,
        ticker: Optional[str] = None,
        session_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """
        Get trade records.

        Args:
            ticker: Optional filter by ticker symbol
            session_date: Optional override for session date

        Returns:
            DataFrame with trade data
        """
        query_date = session_date or self.session_date

        query = """
            SELECT *
            FROM trades
            WHERE date = %s
        """
        params = [query_date]

        if ticker:
            query += " AND UPPER(ticker) = UPPER(%s)"
            params.append(ticker)

        query += " ORDER BY ticker, entry_time"

        return self._execute_query(query, params)

    # =========================================================================
    # MARKET STRUCTURE
    # =========================================================================

    def get_market_structure(
        self,
        ticker: str,
        session_date: Optional[date] = None,
    ) -> Optional[Dict]:
        """
        Get market structure data for a ticker.

        Args:
            ticker: Stock symbol
            session_date: Optional override for session date

        Returns:
            Dict with structure data or None
        """
        query_date = session_date or self.session_date

        query = """
            SELECT *
            FROM market_structure
            WHERE date = %s
              AND UPPER(ticker) = UPPER(%s)
        """

        try:
            self._cursor.execute(query, [query_date, ticker])
            row = self._cursor.fetchone()
            return dict(row) if row else None

        except Exception as e:
            print(f"[Supabase] Error getting market structure: {e}")
            return None

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _execute_query(
        self,
        query: str,
        params: Optional[List] = None,
    ) -> pd.DataFrame:
        """
        Execute a query and return results as DataFrame.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            DataFrame with query results
        """
        try:
            self._cursor.execute(query, params or [])
            rows = self._cursor.fetchall()

            if not rows:
                return pd.DataFrame()

            return pd.DataFrame(rows)

        except Exception as e:
            print(f"[Supabase] Query error: {e}")
            return pd.DataFrame()

    def execute(self, query: str, params: Optional[List] = None) -> bool:
        """
        Execute a write query (INSERT, UPDATE, DELETE).

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            True if successful, False otherwise
        """
        try:
            self._cursor.execute(query, params or [])
            self._conn.commit()
            return True

        except Exception as e:
            print(f"[Supabase] Execute error: {e}")
            self._conn.rollback()
            return False

    def insert_dataframe(
        self,
        table: str,
        df: pd.DataFrame,
        on_conflict: str = "DO NOTHING",
    ) -> bool:
        """
        Insert DataFrame into table.

        Args:
            table: Table name
            df: DataFrame to insert
            on_conflict: Conflict resolution (DO NOTHING, DO UPDATE, etc.)

        Returns:
            True if successful, False otherwise
        """
        if df.empty:
            return True

        try:
            columns = list(df.columns)
            values_template = ", ".join(["%s"] * len(columns))
            columns_str = ", ".join(columns)

            query = f"""
                INSERT INTO {table} ({columns_str})
                VALUES ({values_template})
                ON CONFLICT {on_conflict}
            """

            # Insert rows
            for _, row in df.iterrows():
                self._cursor.execute(query, list(row))

            self._conn.commit()
            return True

        except Exception as e:
            print(f"[Supabase] Insert error: {e}")
            self._conn.rollback()
            return False


# Convenience function
def get_supabase_client(session_date: Optional[date] = None) -> SupabaseClient:
    """Get a configured Supabase client instance."""
    return SupabaseClient(session_date=session_date)
