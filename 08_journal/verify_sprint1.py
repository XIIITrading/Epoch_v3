"""Sprint 1 verification script — run from 08_journal/ directory."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.trade_processor import process_session


def verify_file(csv_path: Path):
    """Process a CSV and print results."""
    print(f"\n{'='*60}")
    print(f"FILE: {csv_path.name}")
    print(f"{'='*60}")

    log = process_session(csv_path)

    print(f"Date: {log.trade_date}")
    print(f"Trades: {log.trade_count} | Closed: {log.closed_count} | Open: {log.open_count}")
    print(f"Symbols: {log.symbols_traded}")
    print(f"Total P&L: ${log.total_pnl:.2f}")

    if log.win_rate is not None:
        print(f"Win Rate: {log.win_rate:.0%} ({log.win_count}W / {log.loss_count}L)")

    for t in log.trades:
        print(f"\n  {t.trade_id}: {t.symbol} {t.direction.value}")
        print(f"    Entry: ${t.entry_price:.4f} @ {t.entry_time} ({t.entry_leg.fill_count} fills, {t.entry_leg.total_qty} shares)")
        if t.exit_price is not None:
            print(f"    Exit:  ${t.exit_price:.4f} @ {t.exit_time} ({t.exit_leg.fill_count} fills, {t.exit_leg.total_qty} shares)")
        else:
            print(f"    Exit:  OPEN")
        if t.pnl_total is not None:
            print(f"    P&L:   ${t.pnl_total:.2f} per-share: ${t.pnl_dollars:.4f} ({t.outcome.value})")
        print(f"    Duration: {t.duration_display}")

    if log.parse_errors:
        print(f"\n  ERRORS:")
        for err in log.parse_errors:
            print(f"    - {err}")


def main():
    trade_log_dir = Path(__file__).parent / "trade_log" / "01_Jan_2026"

    # Test 1: Single AMD SHORT trade
    verify_file(trade_log_dir / "test_02_012826.csv")

    # Test 2: Multi-symbol (META LONG + MSFT SHORT with scaling)
    verify_file(trade_log_dir / "tl_012926.csv")


if __name__ == "__main__":
    main()
