"""
Setup Schema
Creates the ai_predictions table in Supabase.

Usage:
    python setup_schema.py
"""

import psycopg2
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DB_CONFIG


def run_schema():
    """Execute the ai_predictions schema SQL."""
    schema_file = Path(__file__).parent.parent / "schema" / "ai_predictions.sql"

    if not schema_file.exists():
        print(f"Schema file not found: {schema_file}")
        return False

    with open(schema_file, 'r') as f:
        sql = f.read()

    print("Connecting to Supabase...")
    conn = psycopg2.connect(**DB_CONFIG)

    print("Creating ai_predictions table...")
    with conn.cursor() as cur:
        cur.execute(sql)

    conn.commit()
    conn.close()

    print("Schema created successfully!")
    return True


def verify_schema():
    """Verify the table was created."""
    query = """
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'ai_predictions'
    ORDER BY ordinal_position
    """

    conn = psycopg2.connect(**DB_CONFIG)
    with conn.cursor() as cur:
        cur.execute(query)
        columns = cur.fetchall()
    conn.close()

    if not columns:
        print("Table ai_predictions not found!")
        return False

    print(f"\nai_predictions table has {len(columns)} columns:")
    for name, dtype in columns[:10]:
        print(f"  {name}: {dtype}")
    print("  ...")

    return True


if __name__ == '__main__':
    if run_schema():
        verify_schema()
