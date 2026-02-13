"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: BACKTEST PROCESSOR
R-Level Events Runner
XIII Trading LLC
================================================================================

Main entry point for generating R-level crossing events.

Usage:
    python run.py                           # Process all unprocessed trades
    python run.py --date-from 2024-01-01    # Process from date
    python run.py --ticker SPY              # Process specific ticker
    python run.py --reprocess               # Reprocess all (delete existing)

NOTE: This adds R1_CROSS, R2_CROSS, R3_CROSS events to optimal_trade
without affecting existing ENTRY, MFE, MAE, EXIT events.
================================================================================
"""

import argparse
import logging
from datetime import datetime

from calculator import RLevelEventsCalculator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_date(date_str: str):
    """Parse date string to date object."""
    if not date_str:
        return None
    return datetime.strptime(date_str, '%Y-%m-%d').date()


def main():
    parser = argparse.ArgumentParser(
        description='Generate R-level crossing events for trades'
    )
    parser.add_argument(
        '--date-from',
        type=str,
        help='Start date (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--date-to',
        type=str,
        help='End date (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--ticker',
        type=str,
        help='Filter by ticker symbol'
    )
    parser.add_argument(
        '--reprocess',
        action='store_true',
        help='Reprocess all trades (delete existing R-level events)'
    )

    args = parser.parse_args()

    # Parse dates
    date_from = parse_date(args.date_from)
    date_to = parse_date(args.date_to)

    logger.info("=" * 60)
    logger.info("R-LEVEL EVENTS CALCULATOR")
    logger.info("=" * 60)
    logger.info(f"Date from: {date_from or 'All'}")
    logger.info(f"Date to: {date_to or 'All'}")
    logger.info(f"Ticker: {args.ticker or 'All'}")
    logger.info(f"Reprocess: {args.reprocess}")
    logger.info("=" * 60)

    # Run calculator
    calculator = RLevelEventsCalculator()

    try:
        stats = calculator.process_trades(
            date_from=date_from,
            date_to=date_to,
            ticker=args.ticker,
            reprocess=args.reprocess
        )

        logger.info("=" * 60)
        logger.info("RESULTS")
        logger.info("=" * 60)
        logger.info(f"Trades processed: {stats.get('trades_processed', 0)}")
        logger.info(f"R1 events created: {stats.get('r1_events', 0)}")
        logger.info(f"R2 events created: {stats.get('r2_events', 0)}")
        logger.info(f"R3 events created: {stats.get('r3_events', 0)}")
        logger.info(f"Trades skipped: {stats.get('trades_skipped', 0)}")
        logger.info(f"Errors: {stats.get('errors', 0)}")

        if 'error' in stats:
            logger.error(f"Error: {stats['error']}")

    finally:
        calculator.disconnect()


if __name__ == '__main__':
    main()
