"""
DOW AI - Export Model Stats
Epoch Trading System v1 - XIII Trading LLC

Queries trade performance data from Supabase and exports:
1. JSON file to ai_context/model_stats.json
2. Upsert to ai_model_stats Supabase table

Run: python export_model_stats.py [--json-only] [--db-only] [--verbose]
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple

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
OUTPUT_FILE = AI_CONTEXT_DIR / "model_stats.json"


def get_db_connection():
    """Get PostgreSQL connection to Supabase."""
    return psycopg2.connect(**DB_CONFIG)


def fetch_model_stats(conn, verbose: bool = False) -> Tuple[Dict, str, str]:
    """
    Fetch aggregated model statistics from trades table.

    Returns:
        Tuple of (stats_dict, date_from, date_to)
    """
    query = """
    WITH trade_stats AS (
        SELECT
            t.model,
            t.direction,
            COUNT(*) as total_trades,
            SUM(CASE WHEN sa.outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
            ROUND(
                100.0 * SUM(CASE WHEN sa.outcome = 'WIN' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0),
                2
            ) as win_rate,
            MIN(t.date) as date_from,
            MAX(t.date) as date_to
        FROM trades t
        LEFT JOIN stop_analysis sa ON t.trade_id = sa.trade_id AND sa.stop_type = 'zone_buffer'
        WHERE t.model IS NOT NULL
          AND t.direction IS NOT NULL
        GROUP BY t.model, t.direction
    ),
    mfe_mae_stats AS (
        SELECT
            t.model,
            t.direction,
            ROUND(AVG(m.mfe_r_potential)::numeric, 2) as avg_mfe_r,
            ROUND(AVG(m.mae_r_potential)::numeric, 2) as avg_mae_r
        FROM trades t
        LEFT JOIN mfe_mae_potential m ON t.trade_id = m.trade_id
        WHERE t.model IS NOT NULL
          AND t.direction IS NOT NULL
          AND m.mfe_r_potential IS NOT NULL
        GROUP BY t.model, t.direction
    ),
    best_stops AS (
        SELECT DISTINCT ON (t.model, t.direction)
            t.model,
            t.direction,
            sa.stop_type as best_stop_type,
            ROUND(
                100.0 * SUM(CASE WHEN sa.outcome = 'WIN' THEN 1 ELSE 0 END) OVER (PARTITION BY t.model, t.direction, sa.stop_type) /
                NULLIF(COUNT(*) OVER (PARTITION BY t.model, t.direction, sa.stop_type), 0),
                2
            ) as best_stop_win_rate
        FROM trades t
        JOIN stop_analysis sa ON t.trade_id = sa.trade_id
        WHERE t.model IS NOT NULL
          AND t.direction IS NOT NULL
        ORDER BY t.model, t.direction,
            (100.0 * SUM(CASE WHEN sa.outcome = 'WIN' THEN 1 ELSE 0 END) OVER (PARTITION BY t.model, t.direction, sa.stop_type) /
             NULLIF(COUNT(*) OVER (PARTITION BY t.model, t.direction, sa.stop_type), 0)) DESC NULLS LAST
    )
    SELECT
        ts.model,
        ts.direction,
        ts.total_trades,
        ts.wins,
        ts.win_rate,
        COALESCE(mm.avg_mfe_r, 0) as avg_mfe_r,
        COALESCE(mm.avg_mae_r, 0) as avg_mae_r,
        bs.best_stop_type,
        bs.best_stop_win_rate,
        ts.date_from,
        ts.date_to
    FROM trade_stats ts
    LEFT JOIN mfe_mae_stats mm ON ts.model = mm.model AND ts.direction = mm.direction
    LEFT JOIN best_stops bs ON ts.model = bs.model AND ts.direction = bs.direction
    ORDER BY ts.model, ts.direction;
    """

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(query)
        rows = cur.fetchall()

    if verbose:
        print(f"  Fetched {len(rows)} model/direction combinations")

    # Organize by model and direction
    stats = {}
    overall_date_from = None
    overall_date_to = None

    for row in rows:
        model = row['model']
        direction = row['direction']

        if model not in stats:
            stats[model] = {}

        stats[model][direction] = {
            'trades': row['total_trades'],
            'wins': row['wins'],
            'win_rate': float(row['win_rate']) if row['win_rate'] else 0,
            'avg_mfe_r': float(row['avg_mfe_r']) if row['avg_mfe_r'] else 0,
            'avg_mae_r': float(row['avg_mae_r']) if row['avg_mae_r'] else 0,
            'best_stop_type': row['best_stop_type'],
            'best_stop_win_rate': float(row['best_stop_win_rate']) if row['best_stop_win_rate'] else 0
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
    """Export model stats to JSON file."""
    try:
        AI_CONTEXT_DIR.mkdir(parents=True, exist_ok=True)

        output = {
            "generated_at": datetime.now().isoformat(),
            "date_range": {
                "from": date_from,
                "to": date_to
            },
            "models": stats
        }

        with open(OUTPUT_FILE, 'w') as f:
            json.dump(output, f, indent=2)

        if verbose:
            print(f"  Exported to {OUTPUT_FILE}")

        return True
    except Exception as e:
        print(f"  ERROR exporting JSON: {e}")
        return False


def upsert_to_supabase(conn, stats: Dict, date_from: str, date_to: str, verbose: bool = False) -> bool:
    """Upsert model stats to ai_model_stats table."""
    upsert_query = """
    INSERT INTO ai_model_stats (
        model, direction, total_trades, wins, win_rate,
        avg_mfe_r, avg_mae_r, best_stop_type, best_stop_win_rate,
        date_from, date_to, updated_at
    ) VALUES (
        %(model)s, %(direction)s, %(total_trades)s, %(wins)s, %(win_rate)s,
        %(avg_mfe_r)s, %(avg_mae_r)s, %(best_stop_type)s, %(best_stop_win_rate)s,
        %(date_from)s, %(date_to)s, NOW()
    )
    ON CONFLICT (model, direction) DO UPDATE SET
        total_trades = EXCLUDED.total_trades,
        wins = EXCLUDED.wins,
        win_rate = EXCLUDED.win_rate,
        avg_mfe_r = EXCLUDED.avg_mfe_r,
        avg_mae_r = EXCLUDED.avg_mae_r,
        best_stop_type = EXCLUDED.best_stop_type,
        best_stop_win_rate = EXCLUDED.best_stop_win_rate,
        date_from = EXCLUDED.date_from,
        date_to = EXCLUDED.date_to,
        updated_at = NOW();
    """

    try:
        with conn.cursor() as cur:
            rows_affected = 0
            for model, directions in stats.items():
                for direction, data in directions.items():
                    params = {
                        'model': model,
                        'direction': direction,
                        'total_trades': data['trades'],
                        'wins': data['wins'],
                        'win_rate': data['win_rate'],
                        'avg_mfe_r': data['avg_mfe_r'],
                        'avg_mae_r': data['avg_mae_r'],
                        'best_stop_type': data['best_stop_type'],
                        'best_stop_win_rate': data['best_stop_win_rate'],
                        'date_from': date_from,
                        'date_to': date_to
                    }
                    cur.execute(upsert_query, params)
                    rows_affected += 1

            conn.commit()

        if verbose:
            print(f"  Upserted {rows_affected} rows to ai_model_stats")

        return True
    except Exception as e:
        print(f"  ERROR upserting to Supabase: {e}")
        conn.rollback()
        return False


def main():
    parser = argparse.ArgumentParser(description='Export model statistics to JSON and Supabase')
    parser.add_argument('--json-only', action='store_true', help='Only export to JSON, skip Supabase')
    parser.add_argument('--db-only', action='store_true', help='Only upsert to Supabase, skip JSON')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    args = parser.parse_args()

    print("=" * 60)
    print("DOW AI - Export Model Stats")
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
        print("\n[2] Fetching model statistics...")
        stats, date_from, date_to = fetch_model_stats(conn, args.verbose)

        if not stats:
            print("  WARNING: No model stats found in database")
        else:
            total_models = len(stats)
            total_combos = sum(len(d) for d in stats.values())
            print(f"  Found {total_models} models with {total_combos} direction combinations")
            print(f"  Date range: {date_from} to {date_to}")

        # Export to JSON
        if not args.db_only:
            print("\n[3] Exporting to JSON...")
            if export_to_json(stats, date_from, date_to, args.verbose):
                print("  JSON export complete")
            else:
                print("  JSON export failed")

        # Upsert to Supabase
        if not args.json_only and stats:
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
