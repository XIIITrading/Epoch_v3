"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 05: SYSTEM ANALYSIS
Data Provider - Central data access for all analysis tabs
XIII Trading LLC
================================================================================
"""
import json
import psycopg2
import psycopg2.extras
import pandas as pd
from pathlib import Path
from datetime import date, timedelta
from typing import Optional, Dict

from config import DB_CONFIG, TABLE_TRADES, TABLE_M1_ATR, TABLE_M5_ATR, TABLE_INDICATORS, ML_STATE_DIR


class DataProvider:
    """Provides all data needed by system analysis tabs."""

    def __init__(self):
        self._conn = None

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------
    def connect(self) -> bool:
        try:
            self._conn = psycopg2.connect(**DB_CONFIG)
            return True
        except Exception as e:
            print(f"[DataProvider] Connection failed: {e}")
            return False

    def close(self):
        if self._conn and not self._conn.closed:
            self._conn.close()

    def _query(self, sql: str, params=None) -> pd.DataFrame:
        if not self._conn or self._conn.closed:
            self.connect()
        try:
            return pd.read_sql_query(sql, self._conn, params=params)
        except Exception as e:
            print(f"[DataProvider] Query error: {e}")
            # Try reconnecting once
            self.connect()
            return pd.read_sql_query(sql, self._conn, params=params)

    # ------------------------------------------------------------------
    # Tab 1: System Performance
    # ------------------------------------------------------------------
    def get_trades(self, model: Optional[str] = None,
                   direction: Optional[str] = None,
                   ticker: Optional[str] = None,
                   date_from: Optional[date] = None,
                   date_to: Optional[date] = None) -> pd.DataFrame:
        """Get all trades from the consolidated table with optional filters."""
        sql = f"SELECT * FROM {TABLE_TRADES} WHERE 1=1"
        params = []

        if model:
            sql += " AND model = %s"
            params.append(model)
        if direction:
            sql += " AND direction = %s"
            params.append(direction)
        if ticker:
            sql += " AND ticker = %s"
            params.append(ticker)
        if date_from:
            sql += " AND date >= %s"
            params.append(date_from)
        if date_to:
            sql += " AND date <= %s"
            params.append(date_to)

        sql += " ORDER BY date, entry_time"
        return self._query(sql, params if params else None)

    def get_date_range(self) -> Dict:
        """Get the min/max dates available in trades."""
        sql = f"SELECT MIN(date) as min_date, MAX(date) as max_date, COUNT(*) as total FROM {TABLE_TRADES}"
        df = self._query(sql)
        if df.empty:
            return {"min_date": date.today(), "max_date": date.today(), "total": 0}
        return {
            "min_date": df.iloc[0]["min_date"],
            "max_date": df.iloc[0]["max_date"],
            "total": int(df.iloc[0]["total"]),
        }

    def get_tickers(self) -> list:
        """Get distinct tickers."""
        sql = f"SELECT DISTINCT ticker FROM {TABLE_TRADES} ORDER BY ticker"
        df = self._query(sql)
        return df["ticker"].tolist() if not df.empty else []

    # ------------------------------------------------------------------
    # Tab 2: Entry Quality - indicator snapshots at entry time
    # ------------------------------------------------------------------
    def get_entry_indicators(self, model: Optional[str] = None,
                             direction: Optional[str] = None,
                             date_from: Optional[date] = None,
                             date_to: Optional[date] = None) -> pd.DataFrame:
        """Join trades with indicator bars at entry time."""
        sql = f"""
            SELECT
                t.trade_id, t.date, t.ticker, t.model, t.direction, t.zone_type,
                t.entry_price, t.entry_time, t.is_winner, t.pnl_r, t.max_r_achieved,
                i.health_score, i.long_score, i.short_score,
                i.sma_config, i.sma_spread_pct, i.sma_momentum_label, i.price_position,
                i.vol_roc, i.vol_delta_roll, i.cvd_slope, i.candle_range_pct,
                i.h4_structure, i.h1_structure, i.m15_structure, i.m5_structure, i.m1_structure
            FROM {TABLE_TRADES} t
            LEFT JOIN {TABLE_INDICATORS} i
                ON t.ticker = i.ticker
                AND t.date = i.bar_date
                AND date_trunc('minute', t.entry_time::time::interval + '0 seconds'::interval)::time
                    = i.bar_time
            WHERE 1=1
        """
        params = []

        if model:
            sql += " AND t.model = %s"
            params.append(model)
        if direction:
            sql += " AND t.direction = %s"
            params.append(direction)
        if date_from:
            sql += " AND t.date >= %s"
            params.append(date_from)
        if date_to:
            sql += " AND t.date <= %s"
            params.append(date_to)

        sql += " ORDER BY t.date, t.entry_time"
        return self._query(sql, params if params else None)

    # ------------------------------------------------------------------
    # Tab 3: Trade Management - ATR stop outcomes
    # ------------------------------------------------------------------
    def get_m5_atr_stops(self, model: Optional[str] = None,
                         direction: Optional[str] = None,
                         date_from: Optional[date] = None,
                         date_to: Optional[date] = None) -> pd.DataFrame:
        """Get M5 ATR stop analysis data."""
        sql = f"SELECT * FROM {TABLE_M5_ATR} WHERE 1=1"
        params = []

        if model:
            sql += " AND model = %s"
            params.append(model)
        if direction:
            sql += " AND direction = %s"
            params.append(direction)
        if date_from:
            sql += " AND date >= %s"
            params.append(date_from)
        if date_to:
            sql += " AND date <= %s"
            params.append(date_to)

        sql += " ORDER BY date, entry_time"
        return self._query(sql, params if params else None)

    def get_m1_atr_stops(self, model: Optional[str] = None,
                         direction: Optional[str] = None,
                         date_from: Optional[date] = None,
                         date_to: Optional[date] = None) -> pd.DataFrame:
        """Get M1 ATR stop analysis data for comparison."""
        sql = f"SELECT * FROM {TABLE_M1_ATR} WHERE 1=1"
        params = []

        if model:
            sql += " AND model = %s"
            params.append(model)
        if direction:
            sql += " AND direction = %s"
            params.append(direction)
        if date_from:
            sql += " AND date >= %s"
            params.append(date_from)
        if date_to:
            sql += " AND date <= %s"
            params.append(date_to)

        sql += " ORDER BY date, entry_time"
        return self._query(sql, params if params else None)

    # ------------------------------------------------------------------
    # Tab 4: Edge Monitor - ML state files
    # ------------------------------------------------------------------
    def get_ml_system_state(self) -> Optional[Dict]:
        """Read ML system state from JSON file."""
        path = ML_STATE_DIR / "system_state.json"
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text())
        except Exception:
            return None

    def get_ml_hypothesis_tracker(self) -> Optional[Dict]:
        """Read ML hypothesis tracker from JSON file."""
        path = ML_STATE_DIR / "hypothesis_tracker.json"
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text())
        except Exception:
            return None

    def get_ml_pending_edges(self) -> Optional[list]:
        """Read pending edges from JSON file."""
        path = ML_STATE_DIR / "pending_edges.json"
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text())
        except Exception:
            return None
