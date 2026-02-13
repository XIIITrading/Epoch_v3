"""
Module 10: History Manager
SQLite database for historical trade data accumulation.
"""
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from config import DATABASE_PATH


class HistoryManager:
    """Manages SQLite database for historical trading data."""
    
    def __init__(self, db_path: Path = None):
        self.db_path = db_path or DATABASE_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Daily summary table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_summary (
                    date TEXT PRIMARY KEY,
                    total_trades INTEGER,
                    winning_trades INTEGER,
                    losing_trades INTEGER,
                    win_rate REAL,
                    net_pnl_r REAL,
                    expectancy_r REAL,
                    spy_direction TEXT,
                    vix_level REAL,
                    tickers_analyzed INTEGER,
                    created_at TEXT
                )
            """)
            
            # Individual trades table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    ticker TEXT,
                    model TEXT,
                    model_name TEXT,
                    zone_type TEXT,
                    direction TEXT,
                    zone_high REAL,
                    zone_low REAL,
                    entry_price REAL,
                    entry_time TEXT,
                    stop_price REAL,
                    exit_price REAL,
                    exit_time TEXT,
                    exit_reason TEXT,
                    pnl_dollars REAL,
                    pnl_r REAL,
                    is_win INTEGER,
                    created_at TEXT,
                    UNIQUE(date, ticker, model, entry_time)
                )
            """)
            
            # No-trades table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS no_trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    ticker TEXT,
                    model TEXT,
                    model_name TEXT,
                    zone_type TEXT,
                    direction TEXT,
                    zone_high REAL,
                    zone_low REAL,
                    reason TEXT,
                    day_high REAL,
                    day_low REAL,
                    day_open REAL,
                    day_close REAL,
                    zone_touched INTEGER,
                    bars_in_zone INTEGER,
                    created_at TEXT,
                    UNIQUE(date, ticker, model, zone_type)
                )
            """)
            
            # Zone configurations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS zones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    ticker TEXT,
                    zone_type TEXT,
                    direction TEXT,
                    zone_high REAL,
                    zone_low REAL,
                    hvn_poc REAL,
                    target REAL,
                    rr_ratio REAL,
                    created_at TEXT,
                    UNIQUE(date, ticker, zone_type)
                )
            """)
            
            # Model performance by day
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    model TEXT,
                    model_name TEXT,
                    trades INTEGER,
                    wins INTEGER,
                    win_rate REAL,
                    net_r REAL,
                    expectancy_r REAL,
                    created_at TEXT,
                    UNIQUE(date, model)
                )
            """)
            
            # Price action metrics
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS price_action (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    ticker TEXT,
                    day_open REAL,
                    day_high REAL,
                    day_low REAL,
                    day_close REAL,
                    volume INTEGER,
                    gap_percent REAL,
                    range_percent REAL,
                    created_at TEXT,
                    UNIQUE(date, ticker)
                )
            """)
            
            conn.commit()
    
    def save_daily_export(self, export_data: Dict[str, Any]):
        """Save complete daily export to database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            
            meta = export_data["meta"]
            stats = export_data["statistics"]["overall"]
            context = export_data["market_context"]
            
            # Save daily summary
            cursor.execute("""
                INSERT OR REPLACE INTO daily_summary 
                (date, total_trades, winning_trades, losing_trades, win_rate,
                 net_pnl_r, expectancy_r, spy_direction, vix_level, 
                 tickers_analyzed, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                meta["date"],
                stats["total_trades"],
                stats["winning_trades"],
                stats["losing_trades"],
                stats["win_rate"],
                stats["net_pnl_r"],
                stats["expectancy_r"],
                context["spy_direction"],
                context.get("vix_level"),
                meta["tickers_analyzed"],
                now,
            ))
            
            # Save trades
            for trade in export_data["trades"]:
                cursor.execute("""
                    INSERT OR REPLACE INTO trades
                    (date, ticker, model, model_name, zone_type, direction,
                     zone_high, zone_low, entry_price, entry_time, stop_price,
                     exit_price, exit_time, exit_reason, pnl_dollars, pnl_r, 
                     is_win, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    meta["date"],
                    trade["ticker"],
                    trade["model"],
                    trade.get("model_name", ""),
                    trade["zone_type"],
                    trade["direction"],
                    trade["zone_high"],
                    trade["zone_low"],
                    trade["entry_price"],
                    trade["entry_time"],
                    trade["stop_price"],
                    trade["exit_price"],
                    trade["exit_time"],
                    trade["exit_reason"],
                    trade["pnl_dollars"],
                    trade["pnl_r"],
                    1 if trade["is_win"] else 0,
                    now,
                ))
            
            # Save no-trades
            for nt in export_data["no_trades"]:
                cursor.execute("""
                    INSERT OR REPLACE INTO no_trades
                    (date, ticker, model, model_name, zone_type, direction,
                     zone_high, zone_low, reason, day_high, day_low, day_open,
                     day_close, zone_touched, bars_in_zone, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    meta["date"],
                    nt["ticker"],
                    nt["model"],
                    nt.get("model_name", ""),
                    nt["zone_type"],
                    nt["direction"],
                    nt["zone_high"],
                    nt["zone_low"],
                    nt["reason"],
                    nt["day_high"],
                    nt["day_low"],
                    nt["day_open"],
                    nt["day_close"],
                    1 if nt["zone_touched"] else 0,
                    nt["bars_in_zone"],
                    now,
                ))
            
            # Save zones
            for ticker, zone_data in export_data["zone_analysis"].items():
                primary = zone_data.get("primary_zone")
                if primary:
                    cursor.execute("""
                        INSERT OR REPLACE INTO zones
                        (date, ticker, zone_type, direction, zone_high, zone_low,
                         hvn_poc, target, rr_ratio, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        meta["date"],
                        ticker,
                        "PRIMARY",
                        zone_data["direction"],
                        primary["zone_high"],
                        primary["zone_low"],
                        primary["hvn_poc"],
                        primary["target"],
                        primary["rr_ratio"],
                        now,
                    ))
                
                secondary = zone_data.get("secondary_zone")
                if secondary:
                    cursor.execute("""
                        INSERT OR REPLACE INTO zones
                        (date, ticker, zone_type, direction, zone_high, zone_low,
                         hvn_poc, target, rr_ratio, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        meta["date"],
                        ticker,
                        "SECONDARY",
                        zone_data["direction"],
                        secondary["zone_high"],
                        secondary["zone_low"],
                        secondary["hvn_poc"],
                        secondary["target"],
                        secondary["rr_ratio"],
                        now,
                    ))
            
            # Save model stats
            for model, model_stats in export_data["statistics"]["by_model"].items():
                cursor.execute("""
                    INSERT OR REPLACE INTO model_stats
                    (date, model, model_name, trades, wins, win_rate, net_r, 
                     expectancy_r, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    meta["date"],
                    model,
                    model_stats.get("model_name", ""),
                    model_stats["trades"],
                    int(model_stats["trades"] * model_stats["win_rate"]),
                    model_stats["win_rate"],
                    model_stats["net_r"],
                    model_stats["expectancy_r"],
                    now,
                ))
            
            conn.commit()
    
    def get_summary_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate summary report for last N days."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get daily summaries
            cursor.execute("""
                SELECT * FROM daily_summary
                ORDER BY date DESC
                LIMIT ?
            """, (days,))
            daily = [dict(row) for row in cursor.fetchall()]
            
            # Aggregate stats
            if daily:
                total_trades = sum(d["total_trades"] for d in daily)
                total_wins = sum(d["winning_trades"] for d in daily)
                total_r = sum(d["net_pnl_r"] for d in daily)
                
                aggregate = {
                    "days_analyzed": len(daily),
                    "total_trades": total_trades,
                    "total_wins": total_wins,
                    "overall_win_rate": total_wins / total_trades if total_trades else 0,
                    "total_r": round(total_r, 2),
                    "avg_daily_r": round(total_r / len(daily), 2) if daily else 0,
                }
            else:
                aggregate = {
                    "days_analyzed": 0,
                    "total_trades": 0,
                    "total_wins": 0,
                    "overall_win_rate": 0,
                    "total_r": 0,
                    "avg_daily_r": 0,
                }
            
            # Model performance
            cursor.execute("""
                SELECT model, model_name,
                       SUM(trades) as total_trades,
                       SUM(wins) as total_wins,
                       SUM(net_r) as total_r
                FROM model_stats
                GROUP BY model
                ORDER BY total_r DESC
            """)
            model_perf = [dict(row) for row in cursor.fetchall()]
            
            return {
                "period_days": days,
                "aggregate": aggregate,
                "daily_breakdown": daily,
                "model_performance": model_perf,
            }
    
    def query_trades(
        self, 
        model: str = None,
        direction: str = None,
        ticker: str = None,
        min_date: str = None,
        max_date: str = None,
    ) -> List[Dict]:
        """Query historical trades with filters."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM trades WHERE 1=1"
            params = []
            
            if model:
                query += " AND model = ?"
                params.append(model)
            if direction:
                query += " AND direction = ?"
                params.append(direction)
            if ticker:
                query += " AND ticker = ?"
                params.append(ticker)
            if min_date:
                query += " AND date >= ?"
                params.append(min_date)
            if max_date:
                query += " AND date <= ?"
                params.append(max_date)
            
            query += " ORDER BY date DESC, entry_time ASC"
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]


def main():
    """Test the history manager."""
    print("Testing History Manager...")
    print(f"Database: {DATABASE_PATH}")
    
    manager = HistoryManager()
    
    # Show report
    report = manager.get_summary_report(30)
    print(f"\nSummary Report (last 30 days):")
    print(f"  Days analyzed: {report['aggregate']['days_analyzed']}")
    print(f"  Total trades: {report['aggregate']['total_trades']}")
    print(f"  Total R: {report['aggregate']['total_r']}")
    
    if report["model_performance"]:
        print("\nModel Performance:")
        for m in report["model_performance"]:
            print(f"  {m['model']} ({m['model_name']}): {m['total_trades']} trades, {m['total_r']:.2f}R")


if __name__ == "__main__":
    main()