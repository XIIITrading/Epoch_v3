"""
================================================================================
EPOCH TRADING SYSTEM - RAMP-UP ANALYSIS
Database Writer - Insert results to Supabase
XIII Trading LLC
================================================================================

Inserts calculated ramp-up analysis results to Supabase tables:
- ramp_up_macro: Summary metrics per trade
- ramp_up_progression: Bar-by-bar indicator values

================================================================================
"""

import psycopg2
from psycopg2.extras import execute_values
from typing import List, Optional
from dataclasses import asdict
import logging
import sys
from pathlib import Path

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import DB_CONFIG
from .ramp_config import BATCH_SIZE
from .calculator import RampUpMacro, RampUpProgression

logger = logging.getLogger(__name__)


class RampUpDBWriter:
    """
    Writes ramp-up analysis results to Supabase.
    """

    def __init__(self):
        self.conn = None

    def connect(self) -> bool:
        """Establish database connection."""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            logger.info("Connected to Supabase for writing")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
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

    # =========================================================================
    # TABLE CREATION
    # =========================================================================

    def create_tables(self) -> bool:
        """
        Create ramp_up_macro and ramp_up_progression tables if they don't exist.

        Returns:
            True if successful
        """
        self._ensure_connected()

        # Read schema file
        schema_path = Path(__file__).parent / 'schema' / 'ramp_up_tables.sql'

        try:
            with open(schema_path, 'r') as f:
                schema_sql = f.read()

            with self.conn.cursor() as cur:
                cur.execute(schema_sql)
            self.conn.commit()
            logger.info("Created ramp-up analysis tables")
            return True

        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            self.conn.rollback()
            return False

    # =========================================================================
    # MACRO INSERTS
    # =========================================================================

    def insert_macros(
        self,
        macros: List[RampUpMacro],
        batch_size: int = BATCH_SIZE
    ) -> int:
        """
        Insert macro records to ramp_up_macro table.

        Uses upsert (ON CONFLICT UPDATE) for idempotent processing.

        Parameters:
            macros: List of RampUpMacro dataclass instances
            batch_size: Number of records per batch

        Returns:
            Number of records inserted/updated
        """
        if not macros:
            return 0

        self._ensure_connected()

        # SQL for upsert
        sql = """
            INSERT INTO ramp_up_macro (
                trade_id, stop_type, lookback_bars,
                date, ticker, model, direction, entry_time,
                outcome, mfe_distance, r_achieved,
                entry_candle_range_pct, entry_vol_delta, entry_vol_roc,
                entry_sma_spread, entry_sma_momentum_ratio,
                entry_m15_structure, entry_h1_structure,
                entry_long_score, entry_short_score,
                ramp_avg_candle_range_pct, ramp_avg_vol_delta, ramp_avg_vol_roc,
                ramp_avg_sma_spread, ramp_avg_sma_momentum_ratio,
                ramp_avg_long_score, ramp_avg_short_score,
                ramp_trend_candle_range_pct, ramp_trend_vol_delta, ramp_trend_vol_roc,
                ramp_trend_sma_spread, ramp_trend_sma_momentum_ratio,
                ramp_trend_long_score, ramp_trend_short_score,
                ramp_momentum_candle_range_pct, ramp_momentum_vol_delta, ramp_momentum_vol_roc,
                ramp_momentum_sma_spread, ramp_momentum_sma_momentum_ratio,
                ramp_momentum_long_score, ramp_momentum_short_score,
                ramp_structure_m15, ramp_structure_h1,
                bars_analyzed, calculated_at
            ) VALUES %s
            ON CONFLICT (trade_id) DO UPDATE SET
                stop_type = EXCLUDED.stop_type,
                lookback_bars = EXCLUDED.lookback_bars,
                outcome = EXCLUDED.outcome,
                mfe_distance = EXCLUDED.mfe_distance,
                r_achieved = EXCLUDED.r_achieved,
                entry_candle_range_pct = EXCLUDED.entry_candle_range_pct,
                entry_vol_delta = EXCLUDED.entry_vol_delta,
                entry_vol_roc = EXCLUDED.entry_vol_roc,
                entry_sma_spread = EXCLUDED.entry_sma_spread,
                entry_sma_momentum_ratio = EXCLUDED.entry_sma_momentum_ratio,
                entry_m15_structure = EXCLUDED.entry_m15_structure,
                entry_h1_structure = EXCLUDED.entry_h1_structure,
                entry_long_score = EXCLUDED.entry_long_score,
                entry_short_score = EXCLUDED.entry_short_score,
                ramp_avg_candle_range_pct = EXCLUDED.ramp_avg_candle_range_pct,
                ramp_avg_vol_delta = EXCLUDED.ramp_avg_vol_delta,
                ramp_avg_vol_roc = EXCLUDED.ramp_avg_vol_roc,
                ramp_avg_sma_spread = EXCLUDED.ramp_avg_sma_spread,
                ramp_avg_sma_momentum_ratio = EXCLUDED.ramp_avg_sma_momentum_ratio,
                ramp_avg_long_score = EXCLUDED.ramp_avg_long_score,
                ramp_avg_short_score = EXCLUDED.ramp_avg_short_score,
                ramp_trend_candle_range_pct = EXCLUDED.ramp_trend_candle_range_pct,
                ramp_trend_vol_delta = EXCLUDED.ramp_trend_vol_delta,
                ramp_trend_vol_roc = EXCLUDED.ramp_trend_vol_roc,
                ramp_trend_sma_spread = EXCLUDED.ramp_trend_sma_spread,
                ramp_trend_sma_momentum_ratio = EXCLUDED.ramp_trend_sma_momentum_ratio,
                ramp_trend_long_score = EXCLUDED.ramp_trend_long_score,
                ramp_trend_short_score = EXCLUDED.ramp_trend_short_score,
                ramp_momentum_candle_range_pct = EXCLUDED.ramp_momentum_candle_range_pct,
                ramp_momentum_vol_delta = EXCLUDED.ramp_momentum_vol_delta,
                ramp_momentum_vol_roc = EXCLUDED.ramp_momentum_vol_roc,
                ramp_momentum_sma_spread = EXCLUDED.ramp_momentum_sma_spread,
                ramp_momentum_sma_momentum_ratio = EXCLUDED.ramp_momentum_sma_momentum_ratio,
                ramp_momentum_long_score = EXCLUDED.ramp_momentum_long_score,
                ramp_momentum_short_score = EXCLUDED.ramp_momentum_short_score,
                ramp_structure_m15 = EXCLUDED.ramp_structure_m15,
                ramp_structure_h1 = EXCLUDED.ramp_structure_h1,
                bars_analyzed = EXCLUDED.bars_analyzed,
                calculated_at = CURRENT_TIMESTAMP
        """

        total_inserted = 0

        try:
            # Process in batches
            for i in range(0, len(macros), batch_size):
                batch = macros[i:i + batch_size]

                # Convert to tuples
                values = [self._macro_to_tuple(m) for m in batch]

                with self.conn.cursor() as cur:
                    execute_values(cur, sql, values)

                self.conn.commit()
                total_inserted += len(batch)
                logger.debug(f"Inserted batch of {len(batch)} macro records")

            logger.info(f"Inserted {total_inserted} macro records total")
            return total_inserted

        except Exception as e:
            logger.error(f"Error inserting macros: {e}")
            self.conn.rollback()
            return 0

    def _macro_to_tuple(self, macro: RampUpMacro) -> tuple:
        """Convert RampUpMacro to tuple for insertion."""
        return (
            macro.trade_id,
            macro.stop_type,
            macro.lookback_bars,
            macro.date,
            macro.ticker,
            macro.model,
            macro.direction,
            macro.entry_time,
            macro.outcome,
            macro.mfe_distance,
            macro.r_achieved,
            macro.entry_candle_range_pct,
            macro.entry_vol_delta,
            macro.entry_vol_roc,
            macro.entry_sma_spread,
            macro.entry_sma_momentum_ratio,
            macro.entry_m15_structure,
            macro.entry_h1_structure,
            macro.entry_long_score,
            macro.entry_short_score,
            macro.ramp_avg_candle_range_pct,
            macro.ramp_avg_vol_delta,
            macro.ramp_avg_vol_roc,
            macro.ramp_avg_sma_spread,
            macro.ramp_avg_sma_momentum_ratio,
            macro.ramp_avg_long_score,
            macro.ramp_avg_short_score,
            macro.ramp_trend_candle_range_pct,
            macro.ramp_trend_vol_delta,
            macro.ramp_trend_vol_roc,
            macro.ramp_trend_sma_spread,
            macro.ramp_trend_sma_momentum_ratio,
            macro.ramp_trend_long_score,
            macro.ramp_trend_short_score,
            macro.ramp_momentum_candle_range_pct,
            macro.ramp_momentum_vol_delta,
            macro.ramp_momentum_vol_roc,
            macro.ramp_momentum_sma_spread,
            macro.ramp_momentum_sma_momentum_ratio,
            macro.ramp_momentum_long_score,
            macro.ramp_momentum_short_score,
            macro.ramp_structure_m15,
            macro.ramp_structure_h1,
            macro.bars_analyzed,
            None,  # calculated_at - will use CURRENT_TIMESTAMP
        )

    # =========================================================================
    # PROGRESSION INSERTS
    # =========================================================================

    def insert_progressions(
        self,
        progressions: List[RampUpProgression],
        batch_size: int = BATCH_SIZE * 16  # More rows per trade
    ) -> int:
        """
        Insert progression records to ramp_up_progression table.

        Uses upsert for idempotent processing.

        Parameters:
            progressions: List of RampUpProgression dataclass instances
            batch_size: Number of records per batch

        Returns:
            Number of records inserted/updated
        """
        if not progressions:
            return 0

        self._ensure_connected()

        sql = """
            INSERT INTO ramp_up_progression (
                trade_id, bars_to_entry, bar_time,
                candle_range_pct, vol_delta, vol_roc,
                sma_spread, sma_momentum_ratio,
                m15_structure, h1_structure,
                long_score, short_score,
                calculated_at
            ) VALUES %s
            ON CONFLICT (trade_id, bars_to_entry) DO UPDATE SET
                bar_time = EXCLUDED.bar_time,
                candle_range_pct = EXCLUDED.candle_range_pct,
                vol_delta = EXCLUDED.vol_delta,
                vol_roc = EXCLUDED.vol_roc,
                sma_spread = EXCLUDED.sma_spread,
                sma_momentum_ratio = EXCLUDED.sma_momentum_ratio,
                m15_structure = EXCLUDED.m15_structure,
                h1_structure = EXCLUDED.h1_structure,
                long_score = EXCLUDED.long_score,
                short_score = EXCLUDED.short_score,
                calculated_at = CURRENT_TIMESTAMP
        """

        total_inserted = 0

        try:
            for i in range(0, len(progressions), batch_size):
                batch = progressions[i:i + batch_size]

                values = [self._progression_to_tuple(p) for p in batch]

                with self.conn.cursor() as cur:
                    execute_values(cur, sql, values)

                self.conn.commit()
                total_inserted += len(batch)
                logger.debug(f"Inserted batch of {len(batch)} progression records")

            logger.info(f"Inserted {total_inserted} progression records total")
            return total_inserted

        except Exception as e:
            logger.error(f"Error inserting progressions: {e}")
            self.conn.rollback()
            return 0

    def _progression_to_tuple(self, prog: RampUpProgression) -> tuple:
        """Convert RampUpProgression to tuple for insertion."""
        return (
            prog.trade_id,
            prog.bars_to_entry,
            prog.bar_time,
            prog.candle_range_pct,
            prog.vol_delta,
            prog.vol_roc,
            prog.sma_spread,
            prog.sma_momentum_ratio,
            prog.m15_structure,
            prog.h1_structure,
            prog.long_score,
            prog.short_score,
            None,  # calculated_at
        )

    # =========================================================================
    # DELETION (for reprocessing)
    # =========================================================================

    def delete_trade(self, trade_id: str) -> bool:
        """
        Delete all data for a specific trade (for reprocessing).

        Parameters:
            trade_id: Trade ID to delete

        Returns:
            True if successful
        """
        self._ensure_connected()

        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM ramp_up_progression WHERE trade_id = %s",
                    [trade_id]
                )
                cur.execute(
                    "DELETE FROM ramp_up_macro WHERE trade_id = %s",
                    [trade_id]
                )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error deleting trade {trade_id}: {e}")
            self.conn.rollback()
            return False

    def delete_all(self) -> bool:
        """
        Delete all ramp-up analysis data.

        Returns:
            True if successful
        """
        self._ensure_connected()

        try:
            with self.conn.cursor() as cur:
                cur.execute("TRUNCATE TABLE ramp_up_progression")
                cur.execute("TRUNCATE TABLE ramp_up_macro")
            self.conn.commit()
            logger.info("Deleted all ramp-up analysis data")
            return True
        except Exception as e:
            logger.error(f"Error deleting all data: {e}")
            self.conn.rollback()
            return False


# Module-level singleton
_writer = None


def get_writer() -> RampUpDBWriter:
    """Get or create the database writer singleton."""
    global _writer
    if _writer is None:
        _writer = RampUpDBWriter()
        _writer.connect()
    return _writer
