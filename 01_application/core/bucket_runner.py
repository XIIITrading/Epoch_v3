"""
Bucket Runner — CLI Entry Point
Screener Pipeline Build (Seed 004) — XIII Trading LLC

Routes to the correct bucket runner based on --bucket flag.
Loads universe tickers from Supabase screener_universe table
or falls back to config/universe_tickers.txt.

Usage:
    python -m core.bucket_runner --bucket nightly
    python -m core.bucket_runner --bucket weekly
    python -m core.bucket_runner --bucket morning
    python -m core.bucket_runner --bucket nightly --date 2026-03-21
"""
import argparse
import logging
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def load_universe_tickers(
    analysis_date: date,
    ticker_file: Optional[str] = None,
) -> List[Dict]:
    """
    Load the ticker universe for bucket processing.

    Priority:
    1. Supabase screener_universe table (active tickers)
    2. Fallback to config/universe_tickers.txt

    Args:
        analysis_date: Date for analysis (used for anchor date fallback)
        ticker_file: Optional override path to ticker file

    Returns:
        List of dicts with 'ticker', 'anchor_date', 'needs_auto_anchor'
    """
    # Try Supabase first
    tickers = _load_from_supabase()
    if tickers:
        print(f"Loaded {len(tickers)} tickers from Supabase screener_universe")
        return tickers

    # Fallback to file
    if ticker_file is None:
        ticker_file = Path(__file__).parent.parent / "config" / "universe_tickers.txt"
    else:
        ticker_file = Path(ticker_file)

    if not ticker_file.exists():
        logger.error(f"Ticker file not found: {ticker_file}")
        print(f"ERROR: No ticker source available. Create {ticker_file} or "
              f"populate screener_universe in Supabase.")
        return []

    tickers = _load_from_file(ticker_file)
    print(f"Loaded {len(tickers)} tickers from {ticker_file.name}")
    return tickers


def _load_from_supabase() -> List[Dict]:
    """Load active tickers from screener_universe table."""
    try:
        import psycopg2
        from config import DB_CONFIG

        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        cur.execute("""
            SELECT ticker, epoch_anchor_date
            FROM screener_universe
            WHERE status = 'active'
            ORDER BY ticker
        """)

        rows = cur.fetchall()
        cur.close()
        conn.close()

        if not rows:
            return []

        tickers = []
        for ticker, anchor_date in rows:
            tickers.append({
                "ticker": ticker,
                "anchor_date": anchor_date,
                "needs_auto_anchor": anchor_date is None,
            })

        return tickers

    except Exception as e:
        logger.debug(f"Supabase universe load failed (falling back to file): {e}")
        return []


def _load_from_file(filepath: Path) -> List[Dict]:
    """Load tickers from a text file."""
    tickers = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = line.split(',')
            ticker = parts[0].strip().upper()

            anchor_date = None
            needs_auto_anchor = True
            if len(parts) > 1 and parts[1].strip():
                try:
                    anchor_date = datetime.strptime(parts[1].strip(), '%Y-%m-%d').date()
                    needs_auto_anchor = False
                except ValueError:
                    logger.warning(f"Invalid date for {ticker}: {parts[1].strip()}")

            tickers.append({
                "ticker": ticker,
                "anchor_date": anchor_date,
                "needs_auto_anchor": needs_auto_anchor,
            })

    return tickers


def _get_analysis_date(date_str: Optional[str] = None) -> date:
    """
    Determine the analysis date.

    If not provided, uses the most recent trading day:
    - If today is a weekday, use today
    - If today is Saturday, use Friday
    - If today is Sunday, use Friday
    """
    if date_str:
        return datetime.strptime(date_str, '%Y-%m-%d').date()

    today = date.today()
    # Roll back to most recent weekday
    while today.weekday() >= 5:
        today = today - timedelta(days=1)
    return today


def main():
    parser = argparse.ArgumentParser(
        description="Screener Pipeline — Bucket Runner (Seed 004)",
    )
    parser.add_argument(
        "--bucket",
        required=True,
        choices=["weekly", "nightly", "morning"],
        help="Which bucket to run",
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Analysis date (YYYY-MM-DD). Defaults to most recent trading day.",
    )
    parser.add_argument(
        "--tickers",
        type=str,
        default=None,
        help="Override ticker file path",
    )

    args = parser.parse_args()
    analysis_date = _get_analysis_date(args.date)

    print(f"\n{'='*60}")
    print(f"SCREENER PIPELINE — BUCKET RUNNER")
    print(f"Bucket: {args.bucket.upper()}")
    print(f"Analysis Date: {analysis_date}")
    print(f"{'='*60}")

    # Load universe
    tickers = load_universe_tickers(analysis_date, args.tickers)
    if not tickers:
        print("ERROR: No tickers to process. Exiting.")
        sys.exit(1)

    # Route to bucket
    if args.bucket == "weekly":
        from core.bucket_a_weekly import run_weekly
        result = run_weekly(tickers, analysis_date)

    elif args.bucket == "nightly":
        from core.bucket_b_nightly import run_nightly
        result = run_nightly(tickers, analysis_date)

    elif args.bucket == "morning":
        from core.bucket_c_morning import run_morning
        result = run_morning(tickers, analysis_date)

    else:
        print(f"Unknown bucket: {args.bucket}")
        sys.exit(1)

    # Report
    if result["errors"]:
        print(f"\n--- Errors ({len(result['errors'])}) ---")
        for err in result["errors"]:
            print(f"  • {err}")

    exit_code = 0 if result["failed"] == 0 else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
