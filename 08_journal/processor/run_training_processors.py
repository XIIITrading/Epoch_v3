"""
CLI runner for journal training processors.

Populates secondary analysis tables from journal_trades + journal_m1_bars data.
Must run AFTER processor/populator.py has populated M1 bars and indicators.

Usage:
    python processor/run_training_processors.py                    # All eligible trades
    python processor/run_training_processors.py --trade-id XXX     # Single trade
    python processor/run_training_processors.py --date 2026-02-03  # Specific date
    python processor/run_training_processors.py --status           # Show table row counts
    python processor/run_training_processors.py --dry-run          # Preview without writing
    python processor/run_training_processors.py --create-tables    # Create tables (idempotent)
"""

import argparse
import sys
from datetime import date
from pathlib import Path

# Add parent for config
sys.path.insert(0, str(Path(__file__).parent.parent))

from processor.training_processors import (
    BaseTrainingProcessor,
    JournalEntryIndicatorsProcessor,
    JournalMFEMAEProcessor,
    JournalRLevelsProcessor,
    JournalOptimalTradeProcessor,
)
from config import DB_CONFIG

# Processor execution order (dependency chain)
PROCESSOR_ORDER = [
    ("Entry Indicators", JournalEntryIndicatorsProcessor),
    ("MFE/MAE", JournalMFEMAEProcessor),
    ("R-Levels", JournalRLevelsProcessor),
    ("Optimal Trade", JournalOptimalTradeProcessor),
]

TRAINING_TABLES = [
    "journal_entry_indicators",
    "journal_mfe_mae_potential",
    "journal_r_levels",
    "journal_optimal_trade",
    "journal_trade_reviews",
]


def show_status():
    """Show row counts for all training tables."""
    print("\n" + "=" * 60)
    print("  JOURNAL TRAINING TABLES - STATUS")
    print("=" * 60)

    with BaseTrainingProcessor() as proc:
        # Count eligible trades
        trades = proc._fetch_eligible_trades()
        print(f"\n  Eligible trades (stop_price set): {len(trades)}")
        print()

        for table in TRAINING_TABLES:
            try:
                count = proc.get_table_count(table)
                print(f"  {table:40s} {count:>6d} rows")
            except Exception as e:
                print(f"  {table:40s} ERROR: {e}")

    print()


def create_tables():
    """Run the CREATE TABLE DDL."""
    import psycopg2
    sql_path = Path(__file__).parent / "schema" / "create_training_tables.sql"

    if not sql_path.exists():
        print(f"ERROR: SQL file not found: {sql_path}")
        sys.exit(1)

    sql = sql_path.read_text()

    print("Creating training tables...")
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        print("  Tables created successfully (IF NOT EXISTS - safe to re-run)")
    except Exception as e:
        conn.rollback()
        print(f"  ERROR: {e}")
        sys.exit(1)
    finally:
        conn.close()


def run_processors(trade_id: str = None, trade_date: date = None, dry_run: bool = False):
    """Run all processors in dependency order."""
    print("\n" + "=" * 60)
    print("  JOURNAL TRAINING PROCESSORS")
    if dry_run:
        print("  *** DRY RUN - no data will be written ***")
    print("=" * 60)

    all_stats = {}

    for name, processor_cls in PROCESSOR_ORDER:
        print(f"\n--- {name} ---")
        with processor_cls() as proc:
            stats = proc.process_all(
                trade_id=trade_id,
                trade_date=trade_date,
                dry_run=dry_run,
            )
            all_stats[name] = stats

    # Summary
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    for name, stats in all_stats.items():
        errors = len(stats.get('errors', []))
        processed = stats.get('processed', 0)
        skipped = stats.get('skipped', 0)
        events = stats.get('events_created', '')
        events_str = f" ({events} events)" if events else ""
        status = "OK" if errors == 0 else "FAIL"
        print(f"  {status} {name:25s} {processed} processed, {skipped} skipped{events_str}" +
              (f", {errors} ERRORS" if errors else ""))

    print()
    return all_stats


def main():
    parser = argparse.ArgumentParser(
        description="Run journal training processors"
    )
    parser.add_argument(
        '--trade-id', type=str, default=None,
        help="Process a single trade by ID"
    )
    parser.add_argument(
        '--date', type=str, default=None,
        help="Process all trades on a specific date (YYYY-MM-DD)"
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help="Preview what would be processed without writing"
    )
    parser.add_argument(
        '--status', action='store_true',
        help="Show table row counts and exit"
    )
    parser.add_argument(
        '--create-tables', action='store_true',
        help="Create training tables (idempotent)"
    )
    args = parser.parse_args()

    if args.create_tables:
        create_tables()
        show_status()
        return

    if args.status:
        show_status()
        return

    trade_date = None
    if args.date:
        try:
            trade_date = date.fromisoformat(args.date)
        except ValueError:
            print(f"ERROR: Invalid date format: {args.date} (expected YYYY-MM-DD)")
            sys.exit(1)

    # Ensure tables exist
    create_tables()

    # Run processors
    run_processors(
        trade_id=args.trade_id,
        trade_date=trade_date,
        dry_run=args.dry_run,
    )

    # Show final status
    if not args.dry_run:
        show_status()


if __name__ == "__main__":
    main()
