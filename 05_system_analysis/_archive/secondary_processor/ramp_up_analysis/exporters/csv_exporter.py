"""
================================================================================
EPOCH TRADING SYSTEM - RAMP-UP ANALYSIS
CSV Exporter - Export results for Claude Code analysis
XIII Trading LLC
================================================================================

Exports ramp-up analysis results to CSV files for bulk analysis by Claude Code.

Output files:
- ramp_up_macro_YYYYMMDD.csv: Summary metrics per trade
- ramp_up_progression_YYYYMMDD.csv: Bar-by-bar indicator values

================================================================================
"""

import csv
import psycopg2
from psycopg2.extras import RealDictCursor
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging
import sys
import importlib.util

# Path structure: exporters/ -> ramp_up_analysis/ -> secondary_processor/ -> 12_system_analysis/
# Need to go up 4 levels from this file to reach 12_system_analysis
_system_analysis_dir = str(Path(__file__).parent.parent.parent.parent.resolve())
if _system_analysis_dir not in sys.path:
    sys.path.insert(0, _system_analysis_dir)

from config import DB_CONFIG

# Load local config (ramp_up_analysis/ramp_config.py) for OUTPUT_DIR, DATE_FORMAT, STOP_TYPE
_local_config_path = Path(__file__).parent.parent / "ramp_config.py"
_spec = importlib.util.spec_from_file_location("ramp_config", _local_config_path)
_ramp_config = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_ramp_config)
OUTPUT_DIR = _ramp_config.OUTPUT_DIR
DATE_FORMAT = _ramp_config.DATE_FORMAT
STOP_TYPE = _ramp_config.STOP_TYPE

logger = logging.getLogger(__name__)


class CSVExporter:
    """
    Exports ramp-up analysis results to CSV.
    """

    def __init__(self):
        self.conn = None
        self.output_dir = Path(__file__).parent.parent / OUTPUT_DIR

    def connect(self) -> bool:
        """Establish database connection."""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            return True
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return False

    def disconnect(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def _ensure_output_dir(self):
        """Ensure output directory exists."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_macro(
        self,
        stop_type: str = STOP_TYPE,
        output_path: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Export macro summary data to CSV.

        Parameters:
            stop_type: Filter by stop type
            output_path: Optional custom output path

        Returns:
            Path to created CSV file, or None on error
        """
        if not self.conn:
            if not self.connect():
                return None

        self._ensure_output_dir()

        # Generate filename
        if output_path is None:
            date_str = datetime.now().strftime(DATE_FORMAT)
            output_path = self.output_dir / f"ramp_up_macro_{date_str}.csv"

        # Query data
        query = """
            SELECT
                trade_id,
                date,
                ticker,
                model,
                direction,
                entry_time,
                stop_type,
                outcome,
                mfe_distance,
                r_achieved,

                -- Entry bar values
                entry_candle_range_pct,
                entry_vol_delta,
                entry_vol_roc,
                entry_sma_spread,
                entry_sma_momentum_ratio,
                entry_m15_structure,
                entry_h1_structure,
                entry_long_score,
                entry_short_score,

                -- Ramp averages
                ramp_avg_candle_range_pct,
                ramp_avg_vol_delta,
                ramp_avg_vol_roc,
                ramp_avg_sma_spread,
                ramp_avg_sma_momentum_ratio,
                ramp_avg_long_score,
                ramp_avg_short_score,

                -- Ramp trends
                ramp_trend_candle_range_pct,
                ramp_trend_vol_delta,
                ramp_trend_vol_roc,
                ramp_trend_sma_spread,
                ramp_trend_sma_momentum_ratio,
                ramp_trend_long_score,
                ramp_trend_short_score,

                -- Ramp momentum
                ramp_momentum_candle_range_pct,
                ramp_momentum_vol_delta,
                ramp_momentum_vol_roc,
                ramp_momentum_sma_spread,
                ramp_momentum_sma_momentum_ratio,
                ramp_momentum_long_score,
                ramp_momentum_short_score,

                -- Structure consistency
                ramp_structure_m15,
                ramp_structure_h1,

                bars_analyzed
            FROM ramp_up_macro
            WHERE stop_type = %s
            ORDER BY date, entry_time
        """

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, [stop_type])
                rows = cur.fetchall()

            if not rows:
                logger.warning("No macro data to export")
                return None

            # Write CSV
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)

            logger.info(f"Exported {len(rows)} macro records to {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error exporting macro data: {e}")
            return None

    def export_progression(
        self,
        stop_type: str = STOP_TYPE,
        trade_ids: Optional[List[str]] = None,
        output_path: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Export progression (bar-by-bar) data to CSV.

        Parameters:
            stop_type: Filter by stop type (used to get matching trade_ids)
            trade_ids: Optional specific trade IDs to export
            output_path: Optional custom output path

        Returns:
            Path to created CSV file, or None on error
        """
        if not self.conn:
            if not self.connect():
                return None

        self._ensure_output_dir()

        # Generate filename
        if output_path is None:
            date_str = datetime.now().strftime(DATE_FORMAT)
            output_path = self.output_dir / f"ramp_up_progression_{date_str}.csv"

        # Build query
        if trade_ids:
            query = """
                SELECT
                    p.trade_id,
                    p.bars_to_entry,
                    p.bar_time,
                    m.model,
                    m.direction,
                    m.outcome,
                    p.candle_range_pct,
                    p.vol_delta,
                    p.vol_roc,
                    p.sma_spread,
                    p.sma_momentum_ratio,
                    p.m15_structure,
                    p.h1_structure,
                    p.long_score,
                    p.short_score
                FROM ramp_up_progression p
                JOIN ramp_up_macro m ON p.trade_id = m.trade_id
                WHERE p.trade_id = ANY(%s)
                ORDER BY p.trade_id, p.bars_to_entry
            """
            params = [trade_ids]
        else:
            query = """
                SELECT
                    p.trade_id,
                    p.bars_to_entry,
                    p.bar_time,
                    m.model,
                    m.direction,
                    m.outcome,
                    p.candle_range_pct,
                    p.vol_delta,
                    p.vol_roc,
                    p.sma_spread,
                    p.sma_momentum_ratio,
                    p.m15_structure,
                    p.h1_structure,
                    p.long_score,
                    p.short_score
                FROM ramp_up_progression p
                JOIN ramp_up_macro m ON p.trade_id = m.trade_id
                WHERE m.stop_type = %s
                ORDER BY p.trade_id, p.bars_to_entry
            """
            params = [stop_type]

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                rows = cur.fetchall()

            if not rows:
                logger.warning("No progression data to export")
                return None

            # Write CSV
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)

            logger.info(f"Exported {len(rows)} progression records to {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error exporting progression data: {e}")
            return None

    def export_combined(
        self,
        stop_type: str = STOP_TYPE,
        output_path: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Export combined view with flattened progression data.

        Each row contains:
        - Macro summary
        - Entry bar values
        - Flattened indicator values for each bar (-15 to 0)

        This format is optimized for Claude pattern analysis across trades.

        Parameters:
            stop_type: Filter by stop type
            output_path: Optional custom output path

        Returns:
            Path to created CSV file, or None on error
        """
        if not self.conn:
            if not self.connect():
                return None

        self._ensure_output_dir()

        if output_path is None:
            date_str = datetime.now().strftime(DATE_FORMAT)
            output_path = self.output_dir / f"ramp_up_combined_{date_str}.csv"

        try:
            # Get macro data
            macro_query = """
                SELECT * FROM ramp_up_macro
                WHERE stop_type = %s
                ORDER BY date, entry_time
            """
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(macro_query, [stop_type])
                macros = {row['trade_id']: dict(row) for row in cur.fetchall()}

            if not macros:
                logger.warning("No data to export")
                return None

            # Get progression data
            prog_query = """
                SELECT * FROM ramp_up_progression
                WHERE trade_id = ANY(%s)
                ORDER BY trade_id, bars_to_entry
            """
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(prog_query, [list(macros.keys())])
                progressions = cur.fetchall()

            # Group progressions by trade
            prog_by_trade = {}
            for row in progressions:
                tid = row['trade_id']
                if tid not in prog_by_trade:
                    prog_by_trade[tid] = {}
                prog_by_trade[tid][row['bars_to_entry']] = dict(row)

            # Build combined rows with flattened progression
            indicators = ['long_score', 'short_score', 'vol_roc', 'sma_spread']
            bar_positions = list(range(-15, 1))  # -15 to 0

            combined_rows = []
            for trade_id, macro in macros.items():
                row = dict(macro)

                # Add flattened progression values
                progs = prog_by_trade.get(trade_id, {})
                for bar_pos in bar_positions:
                    bar_data = progs.get(bar_pos, {})
                    for ind in indicators:
                        col_name = f"bar_{bar_pos}_{ind}"
                        row[col_name] = bar_data.get(ind)

                combined_rows.append(row)

            # Write CSV
            if combined_rows:
                with open(output_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=combined_rows[0].keys())
                    writer.writeheader()
                    writer.writerows(combined_rows)

                logger.info(f"Exported {len(combined_rows)} combined records to {output_path}")
                return output_path

        except Exception as e:
            logger.error(f"Error exporting combined data: {e}")
            return None

        return None


def export_macro(stop_type: str = STOP_TYPE) -> Optional[Path]:
    """Export macro summary to CSV."""
    exporter = CSVExporter()
    try:
        return exporter.export_macro(stop_type=stop_type)
    finally:
        exporter.disconnect()


def export_progression(
    stop_type: str = STOP_TYPE,
    trade_ids: Optional[List[str]] = None
) -> Optional[Path]:
    """Export progression data to CSV."""
    exporter = CSVExporter()
    try:
        return exporter.export_progression(stop_type=stop_type, trade_ids=trade_ids)
    finally:
        exporter.disconnect()


def export_all(stop_type: str = STOP_TYPE) -> Dict[str, Optional[Path]]:
    """
    Export all data formats.

    Returns:
        Dict mapping format name to output path
    """
    exporter = CSVExporter()
    try:
        return {
            'macro': exporter.export_macro(stop_type=stop_type),
            'progression': exporter.export_progression(stop_type=stop_type),
            'combined': exporter.export_combined(stop_type=stop_type),
        }
    finally:
        exporter.disconnect()
