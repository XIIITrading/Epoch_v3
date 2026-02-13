"""
Epoch Trading System - Base Exporter Class
Provides common database operations for all exporters.
"""

import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values
from datetime import date, datetime, time
from typing import Any, Dict, List, Optional, Tuple
from abc import ABC, abstractmethod
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DB_CONFIG


class BaseExporter(ABC):
    """
    Base class for all database exporters.
    Handles connection management and common operations.
    """

    # Subclasses must define these
    TABLE_NAME: str = ""
    PRIMARY_KEY: List[str] = []

    def __init__(self, connection=None):
        """
        Initialize exporter with optional shared connection.

        Args:
            connection: Existing psycopg2 connection, or None to create new
        """
        self._conn = connection
        self._owns_connection = connection is None

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        if self._owns_connection:
            self.close()

    def connect(self):
        """Establish database connection if needed."""
        if self._conn is None:
            self._conn = psycopg2.connect(**DB_CONFIG)

    def commit(self):
        """Commit current transaction."""
        if self._conn:
            self._conn.commit()

    def rollback(self):
        """Rollback current transaction."""
        if self._conn:
            self._conn.rollback()

    def close(self):
        """Close connection if we own it."""
        if self._owns_connection and self._conn:
            self._conn.close()
            self._conn = None

    @property
    def connection(self):
        """Get the database connection."""
        return self._conn

    def set_connection(self, conn):
        """Set a shared connection."""
        self._conn = conn
        self._owns_connection = False

    # =========================================================================
    # Common Database Operations
    # =========================================================================

    def execute(self, query: str, params: tuple = None) -> None:
        """Execute a single query."""
        with self._conn.cursor() as cur:
            cur.execute(query, params)

    def execute_many(self, query: str, params_list: List[tuple]) -> None:
        """Execute query with multiple parameter sets."""
        with self._conn.cursor() as cur:
            cur.executemany(query, params_list)

    def fetch_one(self, query: str, params: tuple = None) -> Optional[tuple]:
        """Execute query and fetch one result."""
        with self._conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchone()

    def fetch_all(self, query: str, params: tuple = None) -> List[tuple]:
        """Execute query and fetch all results."""
        with self._conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()

    def upsert(self, data: Dict[str, Any]) -> None:
        """
        Insert or update a single record.
        Uses ON CONFLICT DO UPDATE for upsert behavior.
        """
        if not data:
            return

        columns = list(data.keys())
        values = [self._convert_value(data[col]) for col in columns]

        # Build column and value placeholders
        col_names = ", ".join(columns)
        placeholders = ", ".join(["%s"] * len(columns))

        # Build conflict clause
        pk_cols = ", ".join(self.PRIMARY_KEY)
        update_cols = [c for c in columns if c not in self.PRIMARY_KEY]
        update_clause = ", ".join([f"{c} = EXCLUDED.{c}" for c in update_cols])

        query = f"""
            INSERT INTO {self.TABLE_NAME} ({col_names})
            VALUES ({placeholders})
            ON CONFLICT ({pk_cols}) DO UPDATE SET {update_clause}
        """

        self.execute(query, tuple(values))

    def upsert_many(self, records: List[Dict[str, Any]]) -> int:
        """
        Insert or update multiple records efficiently.
        Returns count of records processed.
        """
        if not records:
            return 0

        # Get columns from first record
        columns = list(records[0].keys())
        col_names = ", ".join(columns)

        # Build conflict clause
        pk_cols = ", ".join(self.PRIMARY_KEY)
        update_cols = [c for c in columns if c not in self.PRIMARY_KEY]
        update_clause = ", ".join([f"{c} = EXCLUDED.{c}" for c in update_cols])

        # Prepare values
        values = [
            tuple(self._convert_value(record.get(col)) for col in columns)
            for record in records
        ]

        query = f"""
            INSERT INTO {self.TABLE_NAME} ({col_names})
            VALUES %s
            ON CONFLICT ({pk_cols}) DO UPDATE SET {update_clause}
        """

        with self._conn.cursor() as cur:
            execute_values(cur, query, values)

        return len(records)

    def delete_by_date(self, session_date: date) -> int:
        """Delete all records for a given date. Returns count deleted."""
        if "date" not in self.PRIMARY_KEY and "date" in self._get_table_columns():
            query = f"DELETE FROM {self.TABLE_NAME} WHERE date = %s"
            with self._conn.cursor() as cur:
                cur.execute(query, (session_date,))
                return cur.rowcount
        return 0

    def count_by_date(self, session_date: date) -> int:
        """Count records for a given date."""
        if "date" in self._get_table_columns():
            query = f"SELECT COUNT(*) FROM {self.TABLE_NAME} WHERE date = %s"
            result = self.fetch_one(query, (session_date,))
            return result[0] if result else 0
        return 0

    def _get_table_columns(self) -> List[str]:
        """Get list of columns for this table from database."""
        query = """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position
        """
        results = self.fetch_all(query, (self.TABLE_NAME,))
        return [r[0] for r in results]

    def _convert_value(self, value: Any) -> Any:
        """Convert Python values to PostgreSQL-compatible types."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, date):
            return value
        if isinstance(value, time):
            return value
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value
        if isinstance(value, str):
            return value.strip() if value else None
        # Convert other types to string
        return str(value)

    # =========================================================================
    # Abstract Methods - Subclasses must implement
    # =========================================================================

    @abstractmethod
    def export(self, data: List[Dict[str, Any]], session_date: date) -> int:
        """
        Export data to database.

        Args:
            data: List of records to export
            session_date: The trading date for this data

        Returns:
            Number of records exported
        """
        pass

    @abstractmethod
    def validate(self, data: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """
        Validate data before export.

        Args:
            data: List of records to validate

        Returns:
            Tuple of (is_valid, list_of_error_messages)
        """
        pass
