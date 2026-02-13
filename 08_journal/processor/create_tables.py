"""
Create journal_m1_bars and journal_m1_indicator_bars tables in Supabase.

Usage:
    python processor/create_tables.py
"""

import psycopg2
from pathlib import Path
import sys

# Add parent to path for config
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DB_CONFIG

SCHEMA_FILE = Path(__file__).parent / "schema" / "create_tables.sql"


def create_tables():
    """Execute the CREATE TABLE SQL script."""
    print("=" * 60)
    print("Journal M1 Tables - Schema Creator")
    print("=" * 60)

    # Read SQL
    sql = SCHEMA_FILE.read_text()
    print(f"\nSQL file: {SCHEMA_FILE}")
    print(f"SQL length: {len(sql)} chars")

    # Execute
    print(f"\nConnecting to Supabase...")
    conn = psycopg2.connect(**DB_CONFIG)

    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        print("Tables created successfully!")

        # Verify
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name FROM information_schema.tables
                WHERE table_name IN ('journal_m1_bars', 'journal_m1_indicator_bars')
                ORDER BY table_name
            """)
            tables = [row[0] for row in cur.fetchall()]

        print(f"\nVerified tables: {tables}")

    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

    print("\nDone.")


if __name__ == "__main__":
    create_tables()
