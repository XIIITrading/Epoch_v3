"""
================================================================================
EPOCH TRADING SYSTEM - RAMP-UP INDICATOR ANALYSIS
Run Analysis - Main Orchestrator
XIII Trading LLC
================================================================================

Orchestrates all analysis calculations and populates Supabase tables.

Usage:
    # Run all analysis with default stop type (from config)
    python -m analysis.run_analysis

    # Run with specific stop type
    python -m analysis.run_analysis --stop-type zone_buffer

    # Run specific analyzers only
    python -m analysis.run_analysis --only direction model

    # Create tables first (if needed)
    python -m analysis.run_analysis --create-tables

================================================================================
"""

import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Optional

# Path structure: analysis/ -> ramp_up_analysis/ -> secondary_processor/ -> 12_system_analysis/
# Need to go up 4 levels from this file to reach 12_system_analysis
_system_analysis_dir = str(Path(__file__).parent.parent.parent.parent.resolve())
if _system_analysis_dir not in sys.path:
    sys.path.insert(0, _system_analysis_dir)

from config import DB_CONFIG, WIN_CONDITION_CONFIG
from .calculators import (
    DirectionAnalyzer,
    TradeTypeAnalyzer,
    ModelAnalyzer,
    ModelDirectionAnalyzer,
    IndicatorTrendAnalyzer,
    IndicatorMomentumAnalyzer,
    StructureConsistencyAnalyzer,
    EntrySnapshotAnalyzer,
    ProgressionAvgAnalyzer,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Map of analyzer names to classes
ANALYZERS = {
    'direction': DirectionAnalyzer,
    'trade_type': TradeTypeAnalyzer,
    'model': ModelAnalyzer,
    'model_direction': ModelDirectionAnalyzer,
    'indicator_trend': IndicatorTrendAnalyzer,
    'indicator_momentum': IndicatorMomentumAnalyzer,
    'structure_consistency': StructureConsistencyAnalyzer,
    'entry_snapshot': EntrySnapshotAnalyzer,
    'progression_avg': ProgressionAvgAnalyzer,
}


def create_tables():
    """Create analysis tables if they don't exist."""
    import psycopg2

    schema_path = Path(__file__).parent.parent / 'schema' / 'ramp_analysis_tables.sql'

    try:
        with open(schema_path, 'r') as f:
            schema_sql = f.read()

        conn = psycopg2.connect(**DB_CONFIG)
        with conn.cursor() as cur:
            cur.execute(schema_sql)
        conn.commit()
        conn.close()

        logger.info("Created analysis tables successfully")
        return True

    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        return False


def run_all_analysis(
    stop_type: Optional[str] = None,
    analyzers: Optional[List[str]] = None
) -> dict:
    """
    Run all (or specified) analysis calculations.

    Parameters:
        stop_type: Stop type for outcomes (default from config)
        analyzers: List of analyzer names to run (default all)

    Returns:
        Dict with results per analyzer
    """
    if stop_type is None:
        stop_type = WIN_CONDITION_CONFIG['default_stop_type']

    if analyzers is None:
        analyzers = list(ANALYZERS.keys())

    start_time = datetime.now()
    logger.info("=" * 60)
    logger.info("RAMP-UP INDICATOR ANALYSIS")
    logger.info(f"Stop Type: {stop_type}")
    logger.info(f"Analyzers: {', '.join(analyzers)}")
    logger.info("=" * 60)

    results = {}

    for name in analyzers:
        if name not in ANALYZERS:
            logger.warning(f"Unknown analyzer: {name}")
            continue

        logger.info(f"\nRunning {name} analyzer...")
        analyzer_class = ANALYZERS[name]
        analyzer = analyzer_class(stop_type=stop_type)

        try:
            rows_saved = analyzer.run()
            results[name] = {
                'status': 'success',
                'rows_saved': rows_saved,
            }
            logger.info(f"  -> Saved {rows_saved} rows")
        except Exception as e:
            logger.error(f"Error in {name} analyzer: {e}", exc_info=True)
            results[name] = {
                'status': 'error',
                'error': str(e),
            }

    duration = (datetime.now() - start_time).total_seconds()

    logger.info("\n" + "=" * 60)
    logger.info("ANALYSIS COMPLETE")
    logger.info(f"Duration: {duration:.1f} seconds")
    logger.info("Results:")
    for name, result in results.items():
        status = result['status']
        if status == 'success':
            logger.info(f"  {name}: {result['rows_saved']} rows")
        else:
            logger.info(f"  {name}: ERROR - {result.get('error', 'unknown')}")
    logger.info("=" * 60)

    return results


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Run ramp-up indicator analysis calculations'
    )
    parser.add_argument(
        '--stop-type',
        default=None,
        choices=list(WIN_CONDITION_CONFIG['stop_types'].keys()),
        help='Stop type for outcome data (default from config)'
    )
    parser.add_argument(
        '--only',
        nargs='+',
        choices=list(ANALYZERS.keys()),
        help='Only run specified analyzers'
    )
    parser.add_argument(
        '--create-tables',
        action='store_true',
        help='Create analysis tables before running'
    )

    args = parser.parse_args()

    if args.create_tables:
        if not create_tables():
            sys.exit(1)

    results = run_all_analysis(
        stop_type=args.stop_type,
        analyzers=args.only
    )

    # Exit with error if any analyzer failed
    if any(r['status'] == 'error' for r in results.values()):
        sys.exit(1)


if __name__ == '__main__':
    main()
