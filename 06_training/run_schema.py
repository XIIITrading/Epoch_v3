"""
Epoch Trading System - Schema Runner for Training Module
Creates trade_reviews, trade_images tables and views in Supabase.

Usage:
    python run_schema.py           # Run all schema files
    python run_schema.py --dry-run # Show SQL without executing

Author: XIII Trading LLC
Version: 1.0.0
"""

import psycopg2
import argparse
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent))

from config import DB_CONFIG

SCHEMA_DIR = Path(__file__).parent / "schema"


def run_schema(dry_run: bool = False):
    """Execute all schema files in order."""
    print("=" * 60)
    print("Epoch Training Module - Schema Setup")
    print("=" * 60)

    # Find all SQL files
    sql_files = sorted(SCHEMA_DIR.glob("*.sql"))

    if not sql_files:
        print(f"No SQL files found in {SCHEMA_DIR}")
        return

    print(f"Found {len(sql_files)} schema files:")
    for f in sql_files:
        print(f"  - {f.name}")
    print()

    if dry_run:
        print("[DRY RUN] Would execute the following SQL:\n")
        for sql_file in sql_files:
            print(f"--- {sql_file.name} ---")
            print(sql_file.read_text())
            print()
        return

    # Connect to database
    print("Connecting to Supabase...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("Connected successfully")
        print()
    except Exception as e:
        print(f"Failed to connect: {e}")
        return

    # Execute each file
    for sql_file in sql_files:
        print(f"Executing {sql_file.name}...")
        try:
            sql = sql_file.read_text()
            with conn.cursor() as cur:
                cur.execute(sql)
            print(f"  [OK] {sql_file.name} completed")
        except Exception as e:
            print(f"  [ERROR] Error in {sql_file.name}: {e}")
            conn.rollback()
            continue

    # Commit all changes
    print()
    print("Committing changes...")
    conn.commit()
    print("[OK] All schema changes committed")

    # Verify tables exist
    print()
    print("Verifying tables...")
    with conn.cursor() as cur:
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('trade_reviews', 'trade_images')
        """)
        tables = [row[0] for row in cur.fetchall()]
        for table in tables:
            print(f"  [OK] {table} exists")

        if 'trade_reviews' not in tables:
            print("  [MISSING] trade_reviews not found")
        if 'trade_images' not in tables:
            print("  [MISSING] trade_images not found")

    # Verify views
    print()
    print("Verifying views...")
    with conn.cursor() as cur:
        cur.execute("""
            SELECT table_name
            FROM information_schema.views
            WHERE table_schema = 'public'
            AND table_name IN ('unreviewed_trades', 'reviewed_trades')
        """)
        views = [row[0] for row in cur.fetchall()]
        for view in views:
            print(f"  [OK] {view} exists")

    # Verify functions
    print()
    print("Verifying functions...")
    with conn.cursor() as cur:
        cur.execute("""
            SELECT routine_name
            FROM information_schema.routines
            WHERE routine_schema = 'public'
            AND routine_name IN ('get_calibration_stats', 'get_recent_calibration_stats', 'get_review_summary')
        """)
        functions = [row[0] for row in cur.fetchall()]
        for func in functions:
            print(f"  [OK] {func}() exists")

    conn.close()
    print()
    print("=" * 60)
    print("Schema setup complete!")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Set up database schema for training module"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show SQL without executing"
    )

    args = parser.parse_args()
    run_schema(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
