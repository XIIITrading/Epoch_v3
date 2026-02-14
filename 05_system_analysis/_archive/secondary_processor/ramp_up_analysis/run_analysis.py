"""
================================================================================
EPOCH TRADING SYSTEM - RAMP-UP ANALYSIS
Run Analysis - CLI orchestration with incremental processing
XIII Trading LLC
================================================================================

Main entry point for ramp-up analysis calculation.
Supports incremental processing (only new trades) and full reprocessing.

Usage:
    # Process new trades only (incremental)
    python run_analysis.py

    # Reprocess all trades
    python run_analysis.py --full

    # Reprocess specific trades
    python run_analysis.py --trades T001 T002 T003

    # Use different stop type
    python run_analysis.py --stop-type zone_buffer

    # Export to CSV after processing
    python run_analysis.py --export

================================================================================
"""

import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Optional

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from .ramp_config import STOP_TYPE, LOOKBACK_BARS
from .data_fetcher import RampUpDataFetcher
from .calculator import calculate_for_trades
from .db_writer import RampUpDBWriter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_analysis(
    stop_type: str = STOP_TYPE,
    lookback_bars: int = LOOKBACK_BARS,
    trade_ids: Optional[List[str]] = None,
    full_reprocess: bool = False,
    export_csv: bool = False
) -> dict:
    """
    Run ramp-up analysis with incremental processing.

    Parameters:
        stop_type: Stop type for outcome data
        lookback_bars: Number of bars to analyze before entry
        trade_ids: Optional specific trade IDs to process
        full_reprocess: If True, reprocess all trades
        export_csv: If True, export results to CSV after processing

    Returns:
        Dict with processing statistics
    """
    start_time = datetime.now()
    logger.info("=" * 60)
    logger.info("RAMP-UP ANALYSIS")
    logger.info(f"Stop Type: {stop_type}")
    logger.info(f"Lookback Bars: {lookback_bars}")
    logger.info("=" * 60)

    # Initialize components
    fetcher = RampUpDataFetcher()
    writer = RampUpDBWriter()

    if not fetcher.connect():
        logger.error("Failed to connect to database (fetcher)")
        return {'error': 'Database connection failed'}

    if not writer.connect():
        logger.error("Failed to connect to database (writer)")
        return {'error': 'Database connection failed'}

    try:
        # Create tables if needed
        logger.info("Ensuring tables exist...")
        writer.create_tables()

        # Determine which trades to process
        if trade_ids:
            # Specific trades requested
            trades_to_process = trade_ids
            logger.info(f"Processing {len(trades_to_process)} specified trades")
        elif full_reprocess:
            # Full reprocess - delete all and process all
            logger.info("Full reprocess requested - deleting existing data...")
            writer.delete_all()
            trades_to_process = fetcher.fetch_all_trade_ids()
            logger.info(f"Processing all {len(trades_to_process)} trades")
        else:
            # Incremental - only new trades
            all_trades = set(fetcher.fetch_all_trade_ids())
            processed = set(fetcher.fetch_processed_trade_ids(stop_type))
            trades_to_process = list(all_trades - processed)
            logger.info(
                f"Incremental mode: {len(trades_to_process)} new trades "
                f"({len(processed)} already processed)"
            )

        if not trades_to_process:
            logger.info("No trades to process")
            return {
                'status': 'complete',
                'trades_processed': 0,
                'duration_seconds': (datetime.now() - start_time).total_seconds()
            }

        # Fetch complete trade data
        logger.info(f"Fetching data for {len(trades_to_process)} trades...")
        trades = fetcher.fetch_complete_trade_data(
            trade_ids=trades_to_process,
            stop_type=stop_type
        )
        logger.info(f"Fetched {len(trades)} trades with complete data")

        if not trades:
            logger.warning("No trades with complete data found")
            return {
                'status': 'complete',
                'trades_processed': 0,
                'trades_skipped': len(trades_to_process),
                'duration_seconds': (datetime.now() - start_time).total_seconds()
            }

        # Calculate metrics
        logger.info("Calculating ramp-up metrics...")
        macros, progressions = calculate_for_trades(
            trades=trades,
            stop_type=stop_type,
            lookback_bars=lookback_bars
        )
        logger.info(
            f"Calculated {len(macros)} macro records, "
            f"{len(progressions)} progression records"
        )

        # Write to database
        logger.info("Writing results to database...")
        macros_inserted = writer.insert_macros(macros)
        progressions_inserted = writer.insert_progressions(progressions)

        # Export if requested
        if export_csv:
            logger.info("Exporting to CSV...")
            from .exporters.csv_exporter import export_all
            export_all(stop_type=stop_type)

        # Calculate stats
        duration = (datetime.now() - start_time).total_seconds()
        trades_with_data = len(trades)
        trades_skipped = len(trades_to_process) - trades_with_data

        result = {
            'status': 'complete',
            'trades_requested': len(trades_to_process),
            'trades_with_data': trades_with_data,
            'trades_skipped': trades_skipped,
            'macros_inserted': macros_inserted,
            'progressions_inserted': progressions_inserted,
            'duration_seconds': duration,
        }

        logger.info("=" * 60)
        logger.info("ANALYSIS COMPLETE")
        logger.info(f"Trades processed: {trades_with_data}")
        logger.info(f"Trades skipped (no data): {trades_skipped}")
        logger.info(f"Macro records: {macros_inserted}")
        logger.info(f"Progression records: {progressions_inserted}")
        logger.info(f"Duration: {duration:.1f} seconds")
        logger.info("=" * 60)

        return result

    except Exception as e:
        logger.error(f"Error during analysis: {e}", exc_info=True)
        return {'error': str(e)}

    finally:
        fetcher.disconnect()
        writer.disconnect()


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Run ramp-up indicator progression analysis'
    )
    parser.add_argument(
        '--stop-type',
        default=STOP_TYPE,
        choices=['zone_buffer', 'prior_m1', 'prior_m5', 'm5_atr', 'm15_atr', 'fractal'],
        help=f'Stop type for outcome data (default: {STOP_TYPE})'
    )
    parser.add_argument(
        '--lookback',
        type=int,
        default=LOOKBACK_BARS,
        help=f'Number of bars before entry to analyze (default: {LOOKBACK_BARS})'
    )
    parser.add_argument(
        '--trades',
        nargs='+',
        help='Specific trade IDs to process'
    )
    parser.add_argument(
        '--full',
        action='store_true',
        help='Reprocess all trades (delete existing data)'
    )
    parser.add_argument(
        '--export',
        action='store_true',
        help='Export results to CSV after processing'
    )

    args = parser.parse_args()

    result = run_analysis(
        stop_type=args.stop_type,
        lookback_bars=args.lookback,
        trade_ids=args.trades,
        full_reprocess=args.full,
        export_csv=args.export
    )

    if 'error' in result:
        sys.exit(1)


if __name__ == '__main__':
    main()
