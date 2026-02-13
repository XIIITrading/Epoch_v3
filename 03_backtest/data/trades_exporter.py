"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 03: BACKTEST RUNNER v4.0
Trades Exporter - Export entry records to Supabase trades_2 table
XIII Trading LLC
================================================================================

Exports entry detection results to the Supabase trades_2 table.
Simplified schema: entry data only, no exit/P&L columns.
================================================================================
"""
import sys
from pathlib import Path
import psycopg2
from psycopg2.extras import execute_values
from datetime import date, datetime, time
from typing import Any, List, Optional
from dataclasses import dataclass

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DB_CONFIG


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
    Exports entry records to Supabase trades_2 table.
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

    def export_trades(self, trades: List[Any], trade_date: date,
                      clear_existing: bool = True) -> ExportStats:
        """
        Export entry records to Supabase trades_2 table.
        """
        self.stats = ExportStats()

        if not trades:
            self._log("No entries to export")
            return self.stats

        if not self.connect():
            return self.stats

        try:
            self._log(f"Exporting {len(trades)} entries for {trade_date}")

            self._ensure_daily_session(trade_date)

            if clear_existing:
                deleted = self._cleanup_trades(trade_date)
                self._log(f"  Cleared {deleted} existing entries")

            inserted = self._insert_trades(trades, trade_date)
            self.stats.trades_exported = inserted
            self._log(f"  Inserted {inserted} entries")

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
                VALUES (%s, 'backtest_runner', '4.0')
                ON CONFLICT (date) DO NOTHING
            """, (trade_date,))

    def _cleanup_trades(self, trade_date: date) -> int:
        """Delete existing entries for the date from trades_2."""
        with self.conn.cursor() as cur:
            cur.execute("DELETE FROM trades_2 WHERE date = %s", (trade_date,))
            return cur.rowcount

    def _insert_trades(self, trades: List[Any], trade_date: date) -> int:
        """Insert entry records into the trades_2 table."""
        if not trades:
            return 0

        query = """
            INSERT INTO trades_2 (
                trade_id, date, ticker, model, zone_type, direction,
                zone_high, zone_low, entry_price, entry_time
            ) VALUES %s
            ON CONFLICT (trade_id) DO UPDATE SET
                entry_price = EXCLUDED.entry_price,
                entry_time = EXCLUDED.entry_time,
                updated_at = NOW()
        """

        seen_trade_ids = {}
        values = []
        for trade in trades:
            if hasattr(trade, 'trade_id'):
                base_trade_id = trade.trade_id
                entry_time = self._extract_time(trade.entry_time)

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
                    trade.model,
                    trade.zone_type,
                    trade.direction,
                    float(trade.zone_high) if trade.zone_high else None,
                    float(trade.zone_low) if trade.zone_low else None,
                    float(trade.entry_price) if trade.entry_price else None,
                    entry_time,
                )
            else:
                base_trade_id = trade.get('trade_id')
                entry_time = self._extract_time(trade.get('entry_time'))

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
                    trade.get('model'),
                    trade.get('zone_type'),
                    trade.get('direction'),
                    trade.get('zone_high'),
                    trade.get('zone_low'),
                    trade.get('entry_price'),
                    entry_time,
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


def export_trades(trades: List[Any], trade_date: date, verbose: bool = True) -> ExportStats:
    """
    Convenience function to export entries to Supabase trades_2 table.
    """
    exporter = TradesExporter(verbose=verbose)
    return exporter.export_trades(trades, trade_date)
