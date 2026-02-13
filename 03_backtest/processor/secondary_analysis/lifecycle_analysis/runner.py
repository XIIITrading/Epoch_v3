#!/usr/bin/env python3
"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
Trade Lifecycle Analysis - CLI Runner
XIII Trading LLC
================================================================================

Runs the Trade Lifecycle Signal extraction for all trades.
Links M1 indicator bars to trade entries and computes derivative signals
(INCREASING, DECREASING, FLIP, etc.) for each indicator across lifecycle
phases: RAMPUP -> ENTRY -> POST-ENTRY.

Usage:
    python runner.py                    # Full run
    python runner.py --dry-run          # Test without saving
    python runner.py --limit 10         # Process 10 trades
    python runner.py --schema           # Create database table
    python runner.py --status           # Show processing status

Version: 1.0.0
================================================================================
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

# Add module directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import DB_CONFIG, SCHEMA_DIR, VERBOSE, TARGET_TABLE
from populator import LifecyclePopulator


def run_schema():
    """Create the trade_lifecycle_signals table from schema file."""
    import psycopg2

    schema_file = SCHEMA_DIR / "trade_lifecycle_signals.sql"

    if not schema_file.exists():
        print(f"ERROR: Schema file not found: {schema_file}")
        return 1

    print()
    print("=" * 60)
    print("Creating trade_lifecycle_signals table")
    print("=" * 60)
    print()
    print(f"[1/3] Reading schema file...")
    print(f"      {schema_file}")

    with open(schema_file, "r") as f:
        schema_sql = f.read()

    print(f"      {len(schema_sql)} characters read")

    print(f"\n[2/3] Connecting to Supabase...")
    conn = psycopg2.connect(**DB_CONFIG)
    print("      Connected successfully")

    print(f"\n[3/3] Executing schema...")
    try:
        with conn.cursor() as cur:
            cur.execute(schema_sql)
        conn.commit()
        print("      Table created successfully")
        print()
        print("=" * 60)
        print("SCHEMA CREATION COMPLETE")
        print("=" * 60)
        return 0
    except Exception as e:
        print(f"      ERROR: {e}")
        conn.rollback()
        return 1
    finally:
        conn.close()


def show_status():
    """Show processing status and statistics."""
    import psycopg2
    from psycopg2.extras import RealDictCursor

    print()
    print("=" * 60)
    print("TRADE LIFECYCLE SIGNALS STATUS")
    print("=" * 60)
    print()

    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check if table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = %s
                )
            """, (TARGET_TABLE,))
            table_exists = cur.fetchone()["exists"]

            if not table_exists:
                print(f"Table '{TARGET_TABLE}' does not exist.")
                print("Run 'python runner.py --schema' to create it.")
                return 0

            # Total trade entries available
            cur.execute("""
                SELECT COUNT(DISTINCT trade_id)
                FROM m5_trade_bars WHERE event_type = 'ENTRY'
            """)
            total_available = cur.fetchone()["count"]

            # Processed
            cur.execute(f"SELECT COUNT(*) as count FROM {TARGET_TABLE}")
            processed = cur.fetchone()["count"]

            # Winners vs losers
            cur.execute(f"""
                SELECT
                    is_winner,
                    COUNT(*) as count
                FROM {TARGET_TABLE}
                GROUP BY is_winner
            """)
            by_outcome = cur.fetchall()

            # Rampup signal distribution for key indicators
            cur.execute(f"""
                SELECT
                    rampup_candle_range_pct as signal,
                    COUNT(*) as total,
                    SUM(CASE WHEN is_winner THEN 1 ELSE 0 END) as wins
                FROM {TARGET_TABLE}
                WHERE rampup_candle_range_pct IS NOT NULL
                GROUP BY rampup_candle_range_pct
                ORDER BY total DESC
            """)
            candle_signals = cur.fetchall()

            cur.execute(f"""
                SELECT
                    flip_vol_delta as signal,
                    COUNT(*) as total,
                    SUM(CASE WHEN is_winner THEN 1 ELSE 0 END) as wins
                FROM {TARGET_TABLE}
                WHERE flip_vol_delta IS NOT NULL
                GROUP BY flip_vol_delta
                ORDER BY total DESC
            """)
            flip_signals = cur.fetchall()

        # Print results
        print(f"Total Trade Entries:   {total_available}")
        print(f"Processed:             {processed}")
        print(f"Remaining:             {total_available - processed}")
        coverage = (processed / total_available * 100) if total_available > 0 else 0
        print(f"Coverage:              {coverage:.1f}%")
        print()

        if by_outcome:
            print("By Outcome:")
            print("-" * 40)
            for row in by_outcome:
                label = "WINNER" if row["is_winner"] else "LOSER"
                print(f"  {label:<10}: {row['count']}")
            print()

        if candle_signals:
            print("Rampup Candle Range Trend Distribution:")
            print("-" * 55)
            print(f"  {'Signal':<20} {'N':>6} {'Wins':>6} {'WR':>7}")
            print(f"  {'-'*20} {'-'*6} {'-'*6} {'-'*7}")
            for row in candle_signals:
                wr = row["wins"] / row["total"] * 100 if row["total"] > 0 else 0
                print(f"  {row['signal']:<20} {row['total']:>6} {row['wins']:>6} {wr:>6.1f}%")
            print()

        if flip_signals:
            print("Vol Delta Flip Distribution:")
            print("-" * 55)
            print(f"  {'Signal':<20} {'N':>6} {'Wins':>6} {'WR':>7}")
            print(f"  {'-'*20} {'-'*6} {'-'*6} {'-'*7}")
            for row in flip_signals:
                wr = row["wins"] / row["total"] * 100 if row["total"] > 0 else 0
                print(f"  {row['signal']:<20} {row['total']:>6} {row['wins']:>6} {wr:>6.1f}%")
            print()

    finally:
        conn.close()

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Trade Lifecycle Signal Extractor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Lifecycle Phases:
  RAMPUP     30 M1 bars before entry (trend signals)
  ENTRY      Single bar snapshot (level signals)
  POST       30 M1 bars after entry (trend signals)

Signal Types:
  Trend:  INCREASING, DECREASING, FLAT, INC_THEN_DEC, DEC_THEN_INC, VOLATILE
  Level:  indicator-specific (COMPRESSED, EXPANDING, STRONG_BUY, etc.)
  Flip:   NO_FLIP, FLIP_TO_POSITIVE, FLIP_TO_NEGATIVE, MULTIPLE_FLIPS

Examples:
  python runner.py                    # Full run
  python runner.py --dry-run          # Test without saving
  python runner.py --limit 10         # Process 10 trades
  python runner.py --schema           # Create database table
  python runner.py --status           # Show processing status
        """,
    )

    parser.add_argument(
        "--dry-run", action="store_true", help="Run without saving to database"
    )
    parser.add_argument(
        "--limit", type=int, metavar="N", help="Limit number of trades to process"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument(
        "--schema", action="store_true", help="Create database table from schema"
    )
    parser.add_argument(
        "--status", action="store_true", help="Show processing status"
    )

    args = parser.parse_args()

    if args.schema:
        return run_schema()

    if args.status:
        return show_status()

    # Run main calculation
    print()
    print("=" * 70)
    print("EPOCH TRADING SYSTEM - TRADE LIFECYCLE SIGNAL EXTRACTION")
    print("M1 Indicator Bar Analysis v1.0")
    print("=" * 70)
    print()
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Dry Run:    {args.dry_run}")
    print(f"Limit:      {args.limit or 'None (all trades)'}")
    print()

    populator = LifecyclePopulator(verbose=args.verbose or VERBOSE)

    try:
        stats = populator.run_batch_population(
            limit=args.limit, dry_run=args.dry_run
        )

        print()
        print("=" * 70)
        print("EXECUTION SUMMARY")
        print("=" * 70)
        print()
        print(f"Trades Processed:  {stats['trades_processed']}")
        print(f"Trades Inserted:   {stats['trades_inserted']}")
        print(f"Trades Skipped:    {stats['trades_skipped']}")
        print(f"Groups Processed:  {stats['groups_processed']}")
        print(f"Errors:            {len(stats['errors'])}")
        print(f"Execution Time:    {stats.get('execution_time_seconds', 0):.1f}s")
        print()

        if stats["errors"]:
            print("Errors (first 10):")
            for err in stats["errors"][:10]:
                print(f"  ! {err}")
            if len(stats["errors"]) > 10:
                print(f"  ... and {len(stats['errors']) - 10} more")
            print()

        if len(stats["errors"]) == 0:
            print("=" * 70)
            print("COMPLETED SUCCESSFULLY")
            print("=" * 70)
        else:
            print("=" * 70)
            print(f"COMPLETED WITH {len(stats['errors'])} ERROR(S)")
            print("=" * 70)

        return 0 if len(stats["errors"]) == 0 else 1

    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
