"""
================================================================================
EPOCH TRADING SYSTEM - RAMP-UP INDICATOR ANALYSIS
Base Analyzer Class
XIII Trading LLC
================================================================================

Base class for all analysis calculators with shared database operations.

================================================================================
"""

import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from datetime import datetime
import logging
import sys
from pathlib import Path

# Path structure: analysis/ -> ramp_up_analysis/ -> secondary_processor/ -> 12_system_analysis/
# Need to go up 4 levels from this file to reach 12_system_analysis
_system_analysis_dir = str(Path(__file__).parent.parent.parent.parent.resolve())
if _system_analysis_dir not in sys.path:
    sys.path.insert(0, _system_analysis_dir)

from config import DB_CONFIG, ENTRY_MODELS, CONTINUATION_MODELS, REJECTION_MODELS

logger = logging.getLogger(__name__)

# Minimum trades for statistical significance
MIN_TRADES_SIGNIFICANT = 30


class BaseAnalyzer(ABC):
    """
    Base class for all ramp-up analysis calculators.

    Provides:
    - Database connection management
    - Common query methods
    - Significance flagging
    - Upsert operations
    """

    def __init__(self, stop_type: str):
        self.stop_type = stop_type
        self.conn = None
        self._model_metadata = self._build_model_metadata()

    def _build_model_metadata(self) -> Dict[str, Dict[str, str]]:
        """Build metadata lookup for models."""
        metadata = {}
        for model, info in ENTRY_MODELS.items():
            metadata[model] = {
                'trade_type': info['type'].upper(),
                'zone_type': info['zone'].upper(),
            }
        return metadata

    def get_trade_type(self, model: str) -> str:
        """Get trade type (CONTINUATION/REJECTION) for a model."""
        return self._model_metadata.get(model, {}).get('trade_type', 'UNKNOWN')

    def get_zone_type(self, model: str) -> str:
        """Get zone type (PRIMARY/SECONDARY) for a model."""
        return self._model_metadata.get(model, {}).get('zone_type', 'UNKNOWN')

    def connect(self) -> bool:
        """Establish database connection."""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            logger.info(f"{self.__class__.__name__}: Connected to Supabase")
            return True
        except Exception as e:
            logger.error(f"{self.__class__.__name__}: Failed to connect: {e}")
            return False

    def disconnect(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def _ensure_connected(self):
        """Ensure connection is active."""
        if not self.conn or self.conn.closed:
            self.connect()

    def fetch_macro_data(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Fetch data from ramp_up_macro table with optional filters.

        Uses CLEAN outcome classification:
        - WIN: outcome='WIN' AND stop_hit_time IS NULL (clean winners, no stop hit)
        - LOSS: outcome='LOSS' AND stop_hit_time IS NOT NULL (pure losses)

        Excludes PARTIAL trades and messy wins (WIN with stop hit).

        Parameters:
            filters: Dict of column -> value filters

        Returns:
            List of row dicts
        """
        self._ensure_connected()

        # Join with stop_analysis to get stop_hit_time for clean classification
        query = """
            SELECT m.*,
                   CASE
                       WHEN m.outcome = 'WIN' AND sa.stop_hit_time IS NULL THEN 'WIN'
                       WHEN m.outcome = 'LOSS' AND sa.stop_hit_time IS NOT NULL THEN 'LOSS'
                   END as clean_outcome
            FROM ramp_up_macro m
            JOIN stop_analysis sa ON m.trade_id = sa.trade_id AND m.stop_type = sa.stop_type
            WHERE m.stop_type = %s
              AND (
                  (m.outcome = 'WIN' AND sa.stop_hit_time IS NULL)
                  OR (m.outcome = 'LOSS' AND sa.stop_hit_time IS NOT NULL)
              )
        """
        params = [self.stop_type]

        if filters:
            for col, val in filters.items():
                if isinstance(val, list):
                    query += f" AND m.{col} = ANY(%s)"
                    params.append(val)
                else:
                    query += f" AND m.{col} = %s"
                    params.append(val)

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching macro data: {e}")
            self.conn.rollback()
            return []

    def fetch_progression_data(
        self,
        trade_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch data from ramp_up_progression table.

        Uses CLEAN outcome classification:
        - WIN: outcome='WIN' AND stop_hit_time IS NULL (clean winners)
        - LOSS: outcome='LOSS' AND stop_hit_time IS NOT NULL (pure losses)

        Parameters:
            trade_ids: Optional list of trade IDs to filter

        Returns:
            List of row dicts
        """
        self._ensure_connected()

        query = """
            SELECT p.*, m.outcome, m.direction, m.model
            FROM ramp_up_progression p
            JOIN ramp_up_macro m ON p.trade_id = m.trade_id
            JOIN stop_analysis sa ON m.trade_id = sa.trade_id AND m.stop_type = sa.stop_type
            WHERE m.stop_type = %s
              AND (
                  (m.outcome = 'WIN' AND sa.stop_hit_time IS NULL)
                  OR (m.outcome = 'LOSS' AND sa.stop_hit_time IS NOT NULL)
              )
        """
        params = [self.stop_type]

        if trade_ids:
            query += " AND p.trade_id = ANY(%s)"
            params.append(trade_ids)

        query += " ORDER BY p.trade_id, p.bars_to_entry"

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching progression data: {e}")
            self.conn.rollback()
            return []

    def calculate_win_rate(self, trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate win rate statistics for a set of trades.

        Returns:
            Dict with total_trades, wins, losses, win_rate, avg_r_achieved, avg_mfe_distance
        """
        if not trades:
            return {
                'total_trades': 0,
                'wins': 0,
                'losses': 0,
                'win_rate': None,
                'avg_r_achieved': None,
                'avg_mfe_distance': None,
                'is_significant': False,
            }

        wins = sum(1 for t in trades if t['outcome'] == 'WIN')
        losses = sum(1 for t in trades if t['outcome'] == 'LOSS')
        total = wins + losses

        win_rate = wins / total if total > 0 else None

        r_values = [t['r_achieved'] for t in trades if t.get('r_achieved') is not None]
        avg_r = sum(r_values) / len(r_values) if r_values else None

        mfe_values = [t['mfe_distance'] for t in trades if t.get('mfe_distance') is not None]
        avg_mfe = sum(mfe_values) / len(mfe_values) if mfe_values else None

        return {
            'total_trades': total,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'avg_r_achieved': avg_r,
            'avg_mfe_distance': avg_mfe,
            'is_significant': total >= MIN_TRADES_SIGNIFICANT,
        }

    def calculate_lift(self, win_rate: float, baseline: float) -> Optional[float]:
        """Calculate lift vs baseline win rate."""
        if win_rate is None or baseline is None:
            return None
        return win_rate - baseline

    @abstractmethod
    def calculate(self) -> List[Dict[str, Any]]:
        """
        Calculate analysis results.

        Returns:
            List of result dicts to insert
        """
        pass

    @abstractmethod
    def get_table_name(self) -> str:
        """Return the target table name for this analyzer."""
        pass

    @abstractmethod
    def get_upsert_columns(self) -> List[str]:
        """Return list of columns for upsert."""
        pass

    @abstractmethod
    def get_conflict_columns(self) -> List[str]:
        """Return list of columns for ON CONFLICT clause."""
        pass

    def save_results(self, results: List[Dict[str, Any]]) -> int:
        """
        Save results to the target table using upsert.

        Returns:
            Number of rows inserted/updated
        """
        if not results:
            return 0

        self._ensure_connected()

        table = self.get_table_name()
        columns = self.get_upsert_columns()
        conflict_cols = self.get_conflict_columns()

        # Build upsert SQL
        col_list = ', '.join(columns)
        conflict_list = ', '.join(conflict_cols)
        update_cols = [c for c in columns if c not in conflict_cols and c != 'id']
        update_set = ', '.join([f"{c} = EXCLUDED.{c}" for c in update_cols])

        sql = f"""
            INSERT INTO {table} ({col_list})
            VALUES %s
            ON CONFLICT ({conflict_list}) DO UPDATE SET
                {update_set},
                calculated_at = CURRENT_TIMESTAMP
        """

        # Convert results to tuples
        values = []
        for r in results:
            row = tuple(r.get(c) for c in columns)
            values.append(row)

        try:
            with self.conn.cursor() as cur:
                execute_values(cur, sql, values)
            self.conn.commit()
            logger.info(f"{self.__class__.__name__}: Saved {len(results)} rows to {table}")
            return len(results)
        except Exception as e:
            logger.error(f"Error saving results to {table}: {e}")
            self.conn.rollback()
            return 0

    def run(self) -> int:
        """
        Run the full analysis: calculate and save.

        Returns:
            Number of rows saved
        """
        if not self.connect():
            return 0

        try:
            results = self.calculate()
            return self.save_results(results)
        finally:
            self.disconnect()
