"""
DOW AI - Export Zone Performance
Epoch Trading System v1 - XIII Trading LLC

Queries zone performance data from Supabase (trades joined with zone scores) and exports:
1. JSON file to ai_context/zone_performance.json
2. Upsert to ai_zone_performance Supabase table

Run: python export_zone_performance.py [--json-only] [--db-only] [--verbose]
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Tuple

import psycopg2
import psycopg2.extras

# =============================================================================
# Supabase Configuration
# =============================================================================
SUPABASE_HOST = "db.pdbmcskznoaiybdiobje.supabase.co"
SUPABASE_PORT = 5432
SUPABASE_DATABASE = "postgres"
SUPABASE_USER = "postgres"
SUPABASE_PASSWORD = "guid-saltation-covet"

DB_CONFIG = {
    "host": SUPABASE_HOST,
    "port": SUPABASE_PORT,
    "database": SUPABASE_DATABASE,
    "user": SUPABASE_USER,
    "password": SUPABASE_PASSWORD,
    "sslmode": "require"
}

# Output paths
SCRIPT_DIR = Path(__file__).parent.parent
AI_CONTEXT_DIR = SCRIPT_DIR / "ai_context"
OUTPUT_FILE = AI_CONTEXT_DIR / "zone_performance.json"

# Score buckets
# Low: 0-4, Mid: 5-8, High: 9+
SCORE_BUCKETS = {
    'low': (0, 4),
    'mid': (5, 8),
    'high': (9, 999)  # 9 and above
}


def get_db_connection():
    """Get PostgreSQL connection to Supabase."""
    return psycopg2.connect(**DB_CONFIG)


def fetch_zone_performance(conn, verbose: bool = False) -> Tuple[Dict, str, str]:
    """
    Fetch zone performance grouped by zone type, score bucket, and direction.

    Returns:
        Tuple of (stats_dict, date_from, date_to)
    """
    # Query trades with zone information
    # Zone type is determined by model: EPCH1/EPCH2 = primary, EPCH3/EPCH4 = secondary
    query = """
    WITH zone_trades AS (
        SELECT
            t.trade_id,
            t.date,
            t.direction,
            t.model,
            CASE
                WHEN t.model IN ('EPCH1', 'EPCH2') THEN 'primary'
                WHEN t.model IN ('EPCH3', 'EPCH4') THEN 'secondary'
                ELSE 'unknown'
            END as zone_type,
            COALESCE(z.score, 0) as zone_score,
            CASE
                WHEN COALESCE(z.score, 0) <= 4 THEN 'low'
                WHEN COALESCE(z.score, 0) <= 8 THEN 'mid'
                ELSE 'high'
            END as score_bucket,
            CASE WHEN sa.outcome = 'WIN' THEN 1 ELSE 0 END as is_winner
        FROM trades t
        LEFT JOIN zones z ON t.ticker = z.ticker
            AND t.date = z.date
            AND (
                (t.model IN ('EPCH1', 'EPCH2') AND z.is_epch_bull = TRUE AND t.direction = 'LONG')
                OR (t.model IN ('EPCH1', 'EPCH2') AND z.is_epch_bear = TRUE AND t.direction = 'SHORT')
                OR (t.model IN ('EPCH3', 'EPCH4'))
            )
        LEFT JOIN stop_analysis sa ON t.trade_id = sa.trade_id AND sa.stop_type = 'zone_buffer'
        WHERE t.model IS NOT NULL
          AND t.direction IS NOT NULL
    )
    SELECT
        zone_type,
        score_bucket,
        direction,
        COUNT(*) as total_trades,
        SUM(is_winner) as wins,
        ROUND(100.0 * SUM(is_winner) / NULLIF(COUNT(*), 0), 2) as win_rate,
        MIN(date) as date_from,
        MAX(date) as date_to
    FROM zone_trades
    WHERE zone_type != 'unknown'
    GROUP BY zone_type, score_bucket, direction
    ORDER BY zone_type, score_bucket, direction;
    """

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(query)
        rows = cur.fetchall()

    if verbose:
        print(f"  Fetched {len(rows)} zone/score/direction combinations")

    # Organize by zone_type -> direction -> score_bucket
    stats = {
        'primary': {'LONG': {}, 'SHORT': {}},
        'secondary': {'LONG': {}, 'SHORT': {}}
    }

    overall_date_from = None
    overall_date_to = None

    for row in rows:
        zone_type = row['zone_type']
        direction = row['direction']
        score_bucket = row['score_bucket']

        if zone_type not in stats:
            continue
        if direction not in stats[zone_type]:
            stats[zone_type][direction] = {}

        stats[zone_type][direction][score_bucket] = {
            'trades': row['total_trades'],
            'wins': row['wins'],
            'win_rate': float(row['win_rate']) if row['win_rate'] else 0
        }

        # Track overall date range
        if row['date_from']:
            if overall_date_from is None or row['date_from'] < overall_date_from:
                overall_date_from = row['date_from']
        if row['date_to']:
            if overall_date_to is None or row['date_to'] > overall_date_to:
                overall_date_to = row['date_to']

    date_from_str = overall_date_from.isoformat() if overall_date_from else None
    date_to_str = overall_date_to.isoformat() if overall_date_to else None

    return stats, date_from_str, date_to_str


def export_to_json(stats: Dict, date_from: str, date_to: str, verbose: bool = False) -> bool:
    """Export zone performance to JSON file."""
    try:
        AI_CONTEXT_DIR.mkdir(parents=True, exist_ok=True)

        # Create simplified output for prompts
        output = {
            "generated_at": datetime.now().isoformat(),
            "date_range": {
                "from": date_from,
                "to": date_to
            },
            "primary": {},
            "secondary": {}
        }

        # Flatten to win rates only for easier prompt consumption
        for zone_type in ['primary', 'secondary']:
            for direction in ['LONG', 'SHORT']:
                output[zone_type][direction] = {}
                for bucket in ['low', 'mid', 'high']:
                    bucket_data = stats.get(zone_type, {}).get(direction, {}).get(bucket, {})
                    output[zone_type][direction][bucket] = bucket_data.get('win_rate', 0)

        with open(OUTPUT_FILE, 'w') as f:
            json.dump(output, f, indent=2)

        if verbose:
            print(f"  Exported to {OUTPUT_FILE}")

        return True
    except Exception as e:
        print(f"  ERROR exporting JSON: {e}")
        return False


def upsert_to_supabase(conn, stats: Dict, date_from: str, date_to: str, verbose: bool = False) -> bool:
    """Upsert zone performance to ai_zone_performance table."""
    upsert_query = """
    INSERT INTO ai_zone_performance (
        zone_type, score_bucket, direction, total_trades, wins, win_rate,
        date_from, date_to, updated_at
    ) VALUES (
        %(zone_type)s, %(score_bucket)s, %(direction)s, %(total_trades)s, %(wins)s, %(win_rate)s,
        %(date_from)s, %(date_to)s, NOW()
    )
    ON CONFLICT (zone_type, score_bucket, direction) DO UPDATE SET
        total_trades = EXCLUDED.total_trades,
        wins = EXCLUDED.wins,
        win_rate = EXCLUDED.win_rate,
        date_from = EXCLUDED.date_from,
        date_to = EXCLUDED.date_to,
        updated_at = NOW();
    """

    try:
        with conn.cursor() as cur:
            rows_affected = 0

            for zone_type in ['primary', 'secondary']:
                for direction in ['LONG', 'SHORT']:
                    for bucket in ['low', 'mid', 'high']:
                        bucket_data = stats.get(zone_type, {}).get(direction, {}).get(bucket, {})

                        params = {
                            'zone_type': zone_type,
                            'score_bucket': bucket,
                            'direction': direction,
                            'total_trades': bucket_data.get('trades', 0),
                            'wins': bucket_data.get('wins', 0),
                            'win_rate': bucket_data.get('win_rate', 0),
                            'date_from': date_from,
                            'date_to': date_to
                        }
                        cur.execute(upsert_query, params)
                        rows_affected += 1

            conn.commit()

        if verbose:
            print(f"  Upserted {rows_affected} rows to ai_zone_performance")

        return True
    except Exception as e:
        print(f"  ERROR upserting to Supabase: {e}")
        conn.rollback()
        return False


def main():
    parser = argparse.ArgumentParser(description='Export zone performance to JSON and Supabase')
    parser.add_argument('--json-only', action='store_true', help='Only export to JSON, skip Supabase')
    parser.add_argument('--db-only', action='store_true', help='Only upsert to Supabase, skip JSON')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    args = parser.parse_args()

    print("=" * 60)
    print("DOW AI - Export Zone Performance")
    print("=" * 60)

    # Connect to database
    print("\n[1] Connecting to Supabase...")
    try:
        conn = get_db_connection()
        print("  Connected successfully")
    except Exception as e:
        print(f"  ERROR: Could not connect to Supabase: {e}")
        sys.exit(1)

    try:
        # Fetch stats
        print("\n[2] Fetching zone performance statistics...")
        stats, date_from, date_to = fetch_zone_performance(conn, args.verbose)

        # Print summary
        total_combos = 0
        for zone_type in ['primary', 'secondary']:
            for direction in ['LONG', 'SHORT']:
                for bucket in ['low', 'mid', 'high']:
                    if stats.get(zone_type, {}).get(direction, {}).get(bucket):
                        total_combos += 1

        print(f"  Found {total_combos} zone/score/direction combinations")
        print(f"  Date range: {date_from} to {date_to}")

        if args.verbose:
            print("\n  Summary by zone type:")
            for zone_type in ['primary', 'secondary']:
                print(f"\n    {zone_type.upper()}:")
                for direction in ['LONG', 'SHORT']:
                    print(f"      {direction}:")
                    for bucket in ['high', 'mid', 'low']:
                        data = stats.get(zone_type, {}).get(direction, {}).get(bucket, {})
                        if data:
                            print(f"        {bucket}: {data['win_rate']:.1f}% WR ({data['trades']} trades)")

        # Export to JSON
        if not args.db_only:
            print("\n[3] Exporting to JSON...")
            if export_to_json(stats, date_from, date_to, args.verbose):
                print("  JSON export complete")
            else:
                print("  JSON export failed")

        # Upsert to Supabase
        if not args.json_only:
            print("\n[4] Upserting to Supabase...")
            if upsert_to_supabase(conn, stats, date_from, date_to, args.verbose):
                print("  Supabase upsert complete")
            else:
                print("  Supabase upsert failed")

    finally:
        conn.close()

    print("\n" + "=" * 60)
    print("Export complete")
    print("=" * 60)


if __name__ == '__main__':
    main()
