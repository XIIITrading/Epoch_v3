#!/usr/bin/env python3
"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
Indicator Refinement - CLI Runner
XIII Trading LLC
================================================================================

Runs the Indicator Refinement calculations for Continuation/Rejection scoring.

Trade Classification:
    - CONTINUATION (EPCH01/EPCH03): With-trend trades, scored 0-10
    - REJECTION (EPCH02/EPCH04): Counter-trend/exhaustion, scored 0-11

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

from config import DB_CONFIG, SCHEMA_DIR, VERBOSE
from populator import IndicatorRefinementPopulator


def run_schema():
    """Create the indicator_refinement table from schema file."""
    import psycopg2

    schema_file = SCHEMA_DIR / "indicator_refinement.sql"

    if not schema_file.exists():
        print(f"ERROR: Schema file not found: {schema_file}")
        return 1

    print()
    print("=" * 60)
    print("Creating indicator_refinement table")
    print("=" * 60)
    print()
    print(f"[1/3] Reading schema file...")
    print(f"      {schema_file}")

    with open(schema_file, 'r') as f:
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
    print("INDICATOR REFINEMENT STATUS")
    print("=" * 60)
    print()

    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check if table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'indicator_refinement'
                )
            """)
            table_exists = cur.fetchone()['exists']

            if not table_exists:
                print("Table 'indicator_refinement' does not exist.")
                print("Run 'python runner.py --schema' to create it.")
                return 0

            # Total trades in entry_indicators
            cur.execute("SELECT COUNT(*) as count FROM entry_indicators")
            total_trades = cur.fetchone()['count']

            # Processed trades
            cur.execute("SELECT COUNT(*) as count FROM indicator_refinement")
            processed = cur.fetchone()['count']

            # By trade type
            cur.execute("""
                SELECT
                    trade_type,
                    COUNT(*) as count,
                    AVG(continuation_score) as avg_cont,
                    AVG(rejection_score) as avg_rej
                FROM indicator_refinement
                GROUP BY trade_type
                ORDER BY trade_type
            """)
            by_type = cur.fetchall()

            # By model
            cur.execute("""
                SELECT
                    model,
                    trade_type,
                    COUNT(*) as count,
                    AVG(continuation_score) as avg_cont,
                    AVG(rejection_score) as avg_rej
                FROM indicator_refinement
                GROUP BY model, trade_type
                ORDER BY model
            """)
            by_model = cur.fetchall()

            # Score distribution for continuation
            cur.execute("""
                SELECT
                    continuation_label,
                    COUNT(*) as count
                FROM indicator_refinement
                WHERE trade_type = 'CONTINUATION'
                GROUP BY continuation_label
                ORDER BY
                    CASE continuation_label
                        WHEN 'STRONG' THEN 1
                        WHEN 'GOOD' THEN 2
                        WHEN 'WEAK' THEN 3
                        WHEN 'AVOID' THEN 4
                    END
            """)
            cont_dist = cur.fetchall()

            # Score distribution for rejection
            cur.execute("""
                SELECT
                    rejection_label,
                    COUNT(*) as count
                FROM indicator_refinement
                WHERE trade_type = 'REJECTION'
                GROUP BY rejection_label
                ORDER BY
                    CASE rejection_label
                        WHEN 'STRONG' THEN 1
                        WHEN 'GOOD' THEN 2
                        WHEN 'WEAK' THEN 3
                        WHEN 'AVOID' THEN 4
                    END
            """)
            rej_dist = cur.fetchall()

        # Print results
        print(f"Total Trades (entry_indicators):  {total_trades}")
        print(f"Processed (indicator_refinement): {processed}")
        print(f"Remaining:                        {total_trades - processed}")
        coverage = (processed / total_trades * 100) if total_trades > 0 else 0
        print(f"Coverage:                         {coverage:.1f}%")
        print()

        if by_type:
            print("By Trade Type:")
            print("-" * 60)
            print(f"{'Type':<15} {'Count':<10} {'Avg Cont':<12} {'Avg Rej':<12}")
            print("-" * 60)
            for row in by_type:
                avg_cont = f"{row['avg_cont']:.1f}" if row['avg_cont'] else "N/A"
                avg_rej = f"{row['avg_rej']:.1f}" if row['avg_rej'] else "N/A"
                print(f"{row['trade_type']:<15} {row['count']:<10} {avg_cont:<12} {avg_rej:<12}")
            print()

        if by_model:
            print("By Model:")
            print("-" * 60)
            print(f"{'Model':<10} {'Type':<15} {'Count':<8} {'Avg Cont':<10} {'Avg Rej':<10}")
            print("-" * 60)
            for row in by_model:
                avg_cont = f"{row['avg_cont']:.1f}" if row['avg_cont'] else "N/A"
                avg_rej = f"{row['avg_rej']:.1f}" if row['avg_rej'] else "N/A"
                print(f"{row['model']:<10} {row['trade_type']:<15} {row['count']:<8} "
                      f"{avg_cont:<10} {avg_rej:<10}")
            print()

        if cont_dist:
            print("Continuation Score Distribution:")
            print("-" * 40)
            for row in cont_dist:
                print(f"  {row['continuation_label']:<10}: {row['count']}")
            print()

        if rej_dist:
            print("Rejection Score Distribution:")
            print("-" * 40)
            for row in rej_dist:
                print(f"  {row['rejection_label']:<10}: {row['count']}")
            print()

    finally:
        conn.close()

    return 0


def main():
    parser = argparse.ArgumentParser(
        description='Indicator Refinement Calculator - Continuation/Rejection Scoring',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Trade Classification:
  CONTINUATION (EPCH01/EPCH03): With-trend trades, scored 0-10
    - CONT-01: MTF Alignment (0-4)
    - CONT-02: SMA Momentum (0-2)
    - CONT-03: Volume Thrust (0-2)
    - CONT-04: Pullback Quality (0-2)

  REJECTION (EPCH02/EPCH04): Counter-trend trades, scored 0-11
    - REJ-01: Structure Divergence (0-2)
    - REJ-02: SMA Exhaustion (0-3)
    - REJ-03: Delta Absorption (0-2)
    - REJ-04: Volume Climax (0-2)
    - REJ-05: CVD Extreme (0-2)

Examples:
  python runner.py                    # Full run
  python runner.py --dry-run          # Test without saving
  python runner.py --limit 10         # Process 10 trades
  python runner.py --schema           # Create database table
  python runner.py --status           # Show processing status
        """
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run without saving to database'
    )

    parser.add_argument(
        '--limit',
        type=int,
        metavar='N',
        help='Limit number of trades to process'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    parser.add_argument(
        '--schema',
        action='store_true',
        help='Create database table from schema'
    )

    parser.add_argument(
        '--status',
        action='store_true',
        help='Show processing status'
    )

    args = parser.parse_args()

    # Handle special commands
    if args.schema:
        return run_schema()

    if args.status:
        return show_status()

    # Run main calculation
    print()
    print("=" * 70)
    print("EPOCH TRADING SYSTEM - INDICATOR REFINEMENT")
    print("Continuation/Rejection Score Calculator v1.0")
    print("=" * 70)
    print()
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Dry Run:    {args.dry_run}")
    print(f"Limit:      {args.limit or 'None (all trades)'}")
    print()

    populator = IndicatorRefinementPopulator(verbose=args.verbose or VERBOSE)

    try:
        stats = populator.run_batch_population(
            limit=args.limit,
            dry_run=args.dry_run
        )

        print()
        print("=" * 70)
        print("EXECUTION SUMMARY")
        print("=" * 70)
        print()
        print(f"Trades Processed:  {stats['trades_processed']}")
        print(f"Trades Inserted:   {stats['trades_inserted']}")
        print(f"Trades Skipped:    {stats['trades_skipped']}")
        print(f"Errors:            {len(stats['errors'])}")
        print(f"Execution Time:    {stats.get('execution_time_seconds', 0):.1f}s")
        print()

        if stats['errors']:
            print("Errors (first 10):")
            for err in stats['errors'][:10]:
                print(f"  ! {err}")
            if len(stats['errors']) > 10:
                print(f"  ... and {len(stats['errors']) - 10} more")
            print()

        if len(stats['errors']) == 0:
            print("=" * 70)
            print("COMPLETED SUCCESSFULLY")
            print("=" * 70)
        else:
            print("=" * 70)
            print(f"COMPLETED WITH {len(stats['errors'])} ERROR(S)")
            print("=" * 70)

        return 0 if len(stats['errors']) == 0 else 1

    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
