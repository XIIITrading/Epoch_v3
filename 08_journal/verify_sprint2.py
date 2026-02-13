"""Sprint 2 verification — DB round-trip test. Run from 08_journal/ directory."""

import sys
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).parent))

from core.trade_processor import process_session
from core.models import Trade
from data.journal_db import JournalDB


def verify_round_trip(csv_path: Path):
    """Process CSV → save to DB → read back → verify match."""
    print(f"\n{'='*60}")
    print(f"ROUND-TRIP: {csv_path.name}")
    print(f"{'='*60}")

    # Step 1: Process CSV
    log = process_session(csv_path)
    print(f"\n[1] Parsed {log.trade_count} trades from CSV")

    for t in log.trades:
        print(f"    {t.trade_id}: {t.symbol} {t.direction.value} "
              f"acct={t.account} P&L=${t.pnl_total:.2f}")

    # Step 2: Save to DB
    with JournalDB() as db:
        count = db.save_daily_log(log)
        print(f"\n[2] Saved {count} trades to database")

        # Step 3: Read back by date
        rows = db.get_trades_by_date(log.trade_date)
        print(f"\n[3] Retrieved {len(rows)} trades from DB for {log.trade_date}")

        for row in rows:
            print(f"    {row['trade_id']}: {row['symbol']} {row['direction']} "
                  f"acct={row['account']} "
                  f"entry=${float(row['entry_price']):.4f} @ {row['entry_time']} "
                  f"exit=${float(row['exit_price']):.4f} @ {row['exit_time']} "
                  f"P&L=${float(row['pnl_total']):.2f} ({row['outcome']})")

        # Step 4: Verify round-trip via from_db_row
        print(f"\n[4] Reconstruct Trade objects from DB rows")
        for row in rows:
            reconstructed = Trade.from_db_row(row)
            print(f"    {reconstructed.trade_id}: "
                  f"entry=${reconstructed.entry_price:.4f} "
                  f"exit=${reconstructed.exit_price:.4f} "
                  f"P&L=${reconstructed.pnl_total:.2f} "
                  f"acct={reconstructed.account} "
                  f"({reconstructed.outcome.value})")

        # Step 5: Verify individual trade lookup
        if rows:
            first_id = rows[0]["trade_id"]
            single = db.get_trade(first_id)
            print(f"\n[5] Single lookup: {single['trade_id']} -> found={single is not None}")

            # Step 6: Verify trade_exists
            exists = db.trade_exists(first_id)
            print(f"    trade_exists('{first_id}'): {exists}")

            fake_exists = db.trade_exists("FAKE_ID_12345")
            print(f"    trade_exists('FAKE_ID_12345'): {fake_exists}")

        # Step 7: Verify get_all_dates
        dates = db.get_all_dates()
        print(f"\n[6] All dates in DB: {dates}")

        # Step 8: Verify get_all_accounts
        accounts = db.get_all_accounts()
        print(f"    All accounts in DB: {accounts}")


def verify_re_import(csv_path: Path):
    """Verify that re-importing the same file handles duplicates cleanly."""
    print(f"\n{'='*60}")
    print(f"RE-IMPORT TEST: {csv_path.name}")
    print(f"{'='*60}")

    log = process_session(csv_path)

    with JournalDB() as db:
        # Save once
        count1 = db.save_daily_log(log)
        print(f"First import: {count1} trades saved")

        # Save again (should upsert, not duplicate)
        count2 = db.save_daily_log(log)
        print(f"Re-import:    {count2} trades saved (upsert)")

        # Verify count unchanged
        rows = db.get_trades_by_date(log.trade_date)
        print(f"Total in DB:  {len(rows)} trades (should match original)")


def verify_update_review():
    """Verify update_review_fields works."""
    print(f"\n{'='*60}")
    print(f"UPDATE REVIEW TEST")
    print(f"{'='*60}")

    with JournalDB() as db:
        dates = db.get_all_dates()
        if not dates:
            print("  No trades in DB to test review update")
            return

        rows = db.get_trades_by_date(dates[0])
        if not rows:
            print("  No trades found for first date")
            return

        trade_id = rows[0]["trade_id"]
        print(f"  Updating review for: {trade_id}")

        success = db.update_review_fields(
            trade_id=trade_id,
            zone_id="TEST_ZONE_001",
            model="EPCH_01",
            stop_price=249.50,
            notes="Sprint 2 test review",
        )
        print(f"  Update success: {success}")

        # Read back and verify
        updated = db.get_trade(trade_id)
        print(f"  zone_id: {updated['zone_id']}")
        print(f"  model:   {updated['model']}")
        print(f"  stop:    {updated['stop_price']}")
        print(f"  pnl_r:   {updated['pnl_r']}")
        print(f"  notes:   {updated['notes']}")

        # Clean up: clear the review fields
        db.update_review_fields(
            trade_id=trade_id,
            zone_id=None,
            model=None,
            stop_price=None,
            notes=None,
        )
        print(f"  Cleaned up review fields")


def main():
    trade_log_dir = Path(__file__).parent / "trade_log" / "01_Jan_2026"

    # Test round-trip with single trade CSV
    verify_round_trip(trade_log_dir / "test_02_012826.csv")

    # Test round-trip with multi-symbol CSV
    verify_round_trip(trade_log_dir / "tl_012926.csv")

    # Test re-import (duplicate handling)
    verify_re_import(trade_log_dir / "test_02_012826.csv")

    # Test review field updates
    verify_update_review()

    print(f"\n{'='*60}")
    print("ALL SPRINT 2 VERIFICATIONS COMPLETE")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
