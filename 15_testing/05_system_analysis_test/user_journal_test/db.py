"""
Shared database connection utility for user journal.
Uses shared credentials from 00_shared.
"""
import sys
from pathlib import Path
import psycopg2
import psycopg2.extras
from contextlib import contextmanager

ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT))
from shared.config.credentials import SUPABASE_DB_CONFIG


@contextmanager
def get_connection():
    conn = psycopg2.connect(**SUPABASE_DB_CONFIG)
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def get_cursor(conn):
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        yield cur
    finally:
        cur.close()


def query(sql, params=None):
    with get_connection() as conn:
        with get_cursor(conn) as cur:
            cur.execute(sql, params)
            return cur.fetchall()


def query_one(sql, params=None):
    with get_connection() as conn:
        with get_cursor(conn) as cur:
            cur.execute(sql, params)
            return cur.fetchone()


def execute(sql, params=None):
    """Execute INSERT/UPDATE/DELETE and commit."""
    with get_connection() as conn:
        with get_cursor(conn) as cur:
            cur.execute(sql, params)
            conn.commit()
            return cur.rowcount
