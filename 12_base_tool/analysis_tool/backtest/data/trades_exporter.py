"""
================================================================================
EPOCH TRADING SYSTEM - ANALYSIS TOOL
Trades Exporter - Export backtest trades to Supabase
XIII Trading LLC
================================================================================

Standalone module to export backtest results to the Supabase trades table.
Run after backtest_runner.py completes to persist results.

Usage:
    # Export trades from backtest results
    from data.trades_exporter import export_trades
    stats = export_trades(completed_trades, trade_date)

    # Or run standalone
    python trades_exporter.py --date 2026-01-21

Version: 1.0.0
================================================================================
"""

import psycopg2
from psycopg2.extras import execute_values
from datetime import date, datetime, time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import argparse
import sys
from pathlib import Path

# Database configuration
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


@dataclass
class ExportStats:
    """Statistics from an export operation."""
    trades_exported: int = 0
    trades_skipped: int = 0
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []

    @property
    def success(self) -> bool:
        return len(self.errors) == 0


class TradesExporter:
    """
    Exports backtest trades to Supabase trades table.

    Handles:
    - CompletedTrade objects from trade_simulator
    - Cleanup of existing trades for the date
    - Batch insert with proper type conversion
    """

    def __init__(self, verbose: bool = True):
        self.conn = None
        self.stats = ExportStats()
        self.verbose = verbose

    def _log(self, message: str):
        """Print message if verbose."""
        if self.verbose:
            print(message)

    def connect(self) -> bool:
        """Establish database connection."""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            return True
        except Exception as e:
            self.stats.errors.append(f"Connection failed: {str(e)}")
            return False

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def export_trades(
        self,
        trades: List[Any],
        trade_date: date,
        clear_existing: bool = True
    ) -> ExportStats:
        """
        Export completed trades to Supabase.

        Args:
            trades: List of CompletedTrade objects from trade_simulator
            trade_date: Date of the trades
            clear_existing: If True, delete existing trades for the date first

        Returns:
            ExportStats with counts and any errors
        """
        self.stats = ExportStats()

        if not trades:
            self._log("No trades to export")
            return self.stats

        if not self.connect():
            return self.stats

        try:
            self._log(f"Exporting {len(trades)} trades for {trade_date}")

            # Ensure daily_sessions record exists (foreign key requirement)
            self._ensure_daily_session(trade_date)

            if clear_existing:
                deleted = self._cleanup_trades(trade_date)
                self._log(f"  Cleared {deleted} existing trades")

            # Export trades
            inserted = self._insert_trades(trades, trade_date)
            self.stats.trades_exported = inserted
            self._log(f"  Inserted {inserted} trades")

            # Update daily_sessions with trade stats
            self._update_daily_session_stats(trade_date, trades)

            # Commit transaction
            self.conn.commit()
            self._log("Export completed successfully")

        except Exception as e:
            self.stats.errors.append(f"Export failed: {str(e)}")
            if self.conn:
                self.conn.rollback()
        finally:
            self.close()

        return self.stats

    def _ensure_daily_session(self, trade_date: date):
        """Ensure a daily_sessions record exists for the date."""
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO daily_sessions (date, export_source, export_version)
                VALUES (%s, 'backtest_runner', '3.0')
                ON CONFLICT (date) DO NOTHING
            """, (trade_date,))

    def _cleanup_trades(self, trade_date: date) -> int:
        """Delete existing trades for the date."""
        with self.conn.cursor() as cur:
            cur.execute("DELETE FROM trades WHERE date = %s", (trade_date,))
            return cur.rowcount

    def _insert_trades(self, trades: List[Any], trade_date: date) -> int:
        """Insert trades into the trades table."""
        if not trades:
            return 0

        query = """
            INSERT INTO trades (
                trade_id, date, ticker, model, zone_type, direction,
                zone_high, zone_low, entry_price, entry_time,
                stop_price, target_3r, target_calc, target_used,
                exit_price, exit_time, exit_reason,
                pnl_dollars, pnl_r, risk, is_winner
            ) VALUES %s
            ON CONFLICT (trade_id) DO UPDATE SET
                exit_price = EXCLUDED.exit_price,
                exit_time = EXCLUDED.exit_time,
                exit_reason = EXCLUDED.exit_reason,
                pnl_dollars = EXCLUDED.pnl_dollars,
                pnl_r = EXCLUDED.pnl_r,
                is_winner = EXCLUDED.is_winner,
                updated_at = NOW()
        """

        # Track trade_ids to add sequence numbers for duplicates
        seen_trade_ids = {}
        values = []
        for trade in trades:
            # Handle both object and dict formats
            if hasattr(trade, 'trade_id'):
                # CompletedTrade object
                base_trade_id = trade.trade_id
                entry_time = self._extract_time(trade.entry_time)
                exit_time = self._extract_time(trade.exit_time)

                # Handle duplicate trade_ids by adding sequence suffix
                if base_trade_id in seen_trade_ids:
                    seen_trade_ids[base_trade_id] += 1
                    unique_trade_id = f"{base_trade_id}_{seen_trade_ids[base_trade_id]}"
                else:
                    seen_trade_ids[base_trade_id] = 0
                    unique_trade_id = base_trade_id

                row = (
                    unique_trade_id,
                    trade_date,
                    trade.ticker,
                    trade.model_name,  # e.g., 'EPCH1', 'EPCH2'
                    trade.zone_type,   # 'PRIMARY' or 'SECONDARY'
                    trade.direction,   # 'LONG' or 'SHORT'
                    float(trade.zone_high) if trade.zone_high else None,
                    float(trade.zone_low) if trade.zone_low else None,
                    float(trade.entry_price) if trade.entry_price else None,
                    entry_time,
                    float(trade.stop_price) if trade.stop_price else None,
                    float(trade.target_3r) if trade.target_3r else None,
                    float(trade.target_calc) if trade.target_calc else None,
                    float(trade.target_used) if trade.target_used else None,
                    float(trade.exit_price) if trade.exit_price else None,
                    exit_time,
                    trade.exit_reason,
                    float(trade.pnl_dollars) if trade.pnl_dollars else None,
                    float(trade.pnl_r) if trade.pnl_r else None,
                    float(trade.risk) if trade.risk else None,
                    trade.is_win,
                )
            else:
                # Dict format
                base_trade_id = trade.get('trade_id')
                entry_time = self._extract_time(trade.get('entry_time'))
                exit_time = self._extract_time(trade.get('exit_time'))

                # Handle duplicate trade_ids by adding sequence suffix
                if base_trade_id in seen_trade_ids:
                    seen_trade_ids[base_trade_id] += 1
                    unique_trade_id = f"{base_trade_id}_{seen_trade_ids[base_trade_id]}"
                else:
                    seen_trade_ids[base_trade_id] = 0
                    unique_trade_id = base_trade_id

                row = (
                    unique_trade_id,
                    trade_date,
                    trade.get('ticker'),
                    trade.get('model_name', trade.get('model')),
                    trade.get('zone_type'),
                    trade.get('direction'),
                    trade.get('zone_high'),
                    trade.get('zone_low'),
                    trade.get('entry_price'),
                    entry_time,
                    trade.get('stop_price'),
                    trade.get('target_3r'),
                    trade.get('target_calc'),
                    trade.get('target_used'),
                    trade.get('exit_price'),
                    exit_time,
                    trade.get('exit_reason'),
                    trade.get('pnl_dollars'),
                    trade.get('pnl_r'),
                    trade.get('risk'),
                    trade.get('is_win', trade.get('is_winner')),
                )
            values.append(row)

        with self.conn.cursor() as cur:
            execute_values(cur, query, values)

        return len(values)

    def _extract_time(self, dt_value) -> Optional[time]:
        """Extract time from datetime or time object."""
        if dt_value is None:
            return None
        if isinstance(dt_value, time):
            return dt_value
        if isinstance(dt_value, datetime):
            return dt_value.time()
        if isinstance(dt_value, str):
            try:
                return datetime.strptime(dt_value, '%H:%M:%S').time()
            except:
                try:
                    return datetime.strptime(dt_value, '%H:%M').time()
                except:
                    return None
        return None

    def _update_daily_session_stats(self, trade_date: date, trades: List[Any]):
        """Update daily_sessions with aggregated trade statistics."""
        total_trades = len(trades)

        # Count wins - handle both object and dict formats
        wins = 0
        for t in trades:
            if hasattr(t, 'is_win'):
                if t.is_win:
                    wins += 1
            elif hasattr(t, 'is_winner'):
                if t.is_winner:
                    wins += 1
            elif isinstance(t, dict):
                if t.get('is_win') or t.get('is_winner'):
                    wins += 1

        losses = total_trades - wins

        # Sum P&L - handle both object and dict formats
        net_pnl_r = 0.0
        for t in trades:
            if hasattr(t, 'pnl_r'):
                net_pnl_r += float(t.pnl_r or 0)
            elif isinstance(t, dict):
                net_pnl_r += float(t.get('pnl_r', 0) or 0)

        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0

        with self.conn.cursor() as cur:
            cur.execute("""
                UPDATE daily_sessions SET
                    total_trades = %s,
                    total_wins = %s,
                    total_losses = %s,
                    net_pnl_r = %s,
                    win_rate = %s,
                    updated_at = NOW()
                WHERE date = %s
            """, (total_trades, wins, losses, net_pnl_r, win_rate, trade_date))


def export_trades(trades: List[Any], trade_date: date, verbose: bool = True) -> ExportStats:
    """
    Convenience function to export trades to Supabase.

    Args:
        trades: List of CompletedTrade objects
        trade_date: Date of the trades
        verbose: Print progress messages

    Returns:
        ExportStats with export counts and any errors
    """
    exporter = TradesExporter(verbose=verbose)
    return exporter.export_trades(trades, trade_date)


def get_trades_from_last_backtest() -> List[Dict]:
    """
    Placeholder function to load trades from last backtest run.
    In production, this would load from a cached file or memory.
    """
    # This would be implemented to load from backtest results cache
    return []


# =============================================================================
# CLI Interface
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Export backtest trades to Supabase'
    )
    parser.add_argument(
        '--date',
        type=str,
        help='Trade date (YYYY-MM-DD), defaults to today'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be exported without actually exporting'
    )
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show current trades count in Supabase'
    )

    args = parser.parse_args()

    # Determine date
    if args.date:
        trade_date = datetime.strptime(args.date, '%Y-%m-%d').date()
    else:
        trade_date = date.today()

    if args.status:
        # Show status
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM trades WHERE date = %s", (trade_date,))
            count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM trades")
            total = cur.fetchone()[0]
            conn.close()
            print(f"Trades for {trade_date}: {count}")
            print(f"Total trades in database: {total}")
        except Exception as e:
            print(f"Error checking status: {e}")
        return

    print("=" * 60)
    print("TRADES EXPORTER")
    print("=" * 60)
    print(f"Date: {trade_date}")
    print()
    print("NOTE: This module is designed to be called from backtest_runner.py")
    print("      after trades are generated. To export trades, integrate this")
    print("      into your backtest workflow.")
    print()
    print("Example integration in backtest_runner.py:")
    print("  from data.trades_exporter import export_trades")
    print("  stats = export_trades(completed_trades, trade_date)")
    print()


if __name__ == "__main__":
    main()
