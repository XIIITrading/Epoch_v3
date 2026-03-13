"""
Shared database connection utility for edge analysis scripts.
Uses the same Supabase PostgreSQL connection as the main Epoch system.
"""
import sys
from pathlib import Path
import psycopg2
import psycopg2.extras
from contextlib import contextmanager

# Use shared credentials from 00_shared
ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT))
from shared.config.credentials import SUPABASE_DB_CONFIG

INDEX_TICKERS = ('SPY', 'QQQ', 'DIA')


@contextmanager
def get_connection():
    """Context manager for database connections."""
    conn = psycopg2.connect(**SUPABASE_DB_CONFIG)
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def get_cursor(conn):
    """Context manager for RealDictCursor."""
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        yield cur
    finally:
        cur.close()


def query(sql, params=None):
    """Execute a query and return list of dicts."""
    with get_connection() as conn:
        with get_cursor(conn) as cur:
            cur.execute(sql, params)
            return cur.fetchall()


def query_one(sql, params=None):
    """Execute a query and return single dict."""
    with get_connection() as conn:
        with get_cursor(conn) as cur:
            cur.execute(sql, params)
            return cur.fetchone()
