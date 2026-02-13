"""
================================================================================
EPOCH TRADING SYSTEM - RAMP-UP ANALYSIS
Data Fetcher - Query trades, stop_analysis, m1_indicator_bars
XIII Trading LLC
================================================================================

Fetches all required data for ramp-up analysis:
- Trades (trade identity)
- Stop analysis (outcome, mfe_distance, r_achieved)
- M1 indicator bars (indicator values before entry)

================================================================================
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import date, time, datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import logging
import sys
from pathlib import Path

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import DB_CONFIG
from .ramp_config import STOP_TYPE, LOOKBACK_BARS, INDICATORS

logger = logging.getLogger(__name__)


class RampUpDataFetcher:
    """
    Fetches data required for ramp-up analysis.
    """

    def __init__(self):
        self.conn = None

    def connect(self) -> bool:
        """Establish database connection."""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            logger.info("Connected to Supabase")
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
    # TRADE DATA
    # =========================================================================

    def fetch_all_trade_ids(self) -> List[str]:
        """
        Fetch all trade IDs from trades table.

        Returns:
            List of trade_id strings
        """
        self._ensure_connected()

        query = """
            SELECT trade_id
            FROM trades
            ORDER BY date, entry_time
        """

        try:
            with self.conn.cursor() as cur:
                cur.execute(query)
                return [row[0] for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching trade IDs: {e}")
            self.conn.rollback()
            return []

    def fetch_processed_trade_ids(self, stop_type: str = STOP_TYPE) -> List[str]:
        """
        Fetch trade IDs that have already been processed.

        Parameters:
            stop_type: Stop type used for analysis

        Returns:
            List of already-processed trade_id strings
        """
        self._ensure_connected()

        query = """
            SELECT trade_id
            FROM ramp_up_macro
            WHERE stop_type = %s
        """

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, [stop_type])
                return [row[0] for row in cur.fetchall()]
        except psycopg2.errors.UndefinedTable:
            # Table doesn't exist yet - no trades processed
            self.conn.rollback()
            return []
        except Exception as e:
            logger.error(f"Error fetching processed trade IDs: {e}")
            self.conn.rollback()
            return []

    def fetch_trades(
        self,
        trade_ids: Optional[List[str]] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch trade records.

        Parameters:
            trade_ids: Optional list of specific trade IDs
            date_from: Start date filter
            date_to: End date filter

        Returns:
            List of trade dicts with trade identity fields
        """
        self._ensure_connected()

        query = """
            SELECT
                trade_id,
                date,
                ticker,
                model,
                direction,
                entry_time,
                entry_price
            FROM trades
            WHERE 1=1
        """
        params = []

        if trade_ids:
            query += " AND trade_id = ANY(%s)"
            params.append(trade_ids)
        if date_from:
            query += " AND date >= %s"
            params.append(date_from)
        if date_to:
            query += " AND date <= %s"
            params.append(date_to)

        query += " ORDER BY date, entry_time"

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching trades: {e}")
            self.conn.rollback()
            return []

    # =========================================================================
    # STOP ANALYSIS DATA
    # =========================================================================

    def fetch_stop_analysis(
        self,
        trade_ids: Optional[List[str]] = None,
        stop_type: str = STOP_TYPE
    ) -> Dict[str, Dict[str, Any]]:
        """
        Fetch stop analysis results indexed by trade_id.

        Parameters:
            trade_ids: Optional list of specific trade IDs
            stop_type: Stop type to fetch (default from config)

        Returns:
            Dict mapping trade_id to stop analysis record
        """
        self._ensure_connected()

        query = """
            SELECT
                trade_id,
                outcome,
                mfe_distance,
                r_achieved,
                stop_price,
                stop_hit,
                mfe_price,
                mfe_time
            FROM stop_analysis
            WHERE stop_type = %s
              AND stop_price IS NOT NULL
        """
        params = [stop_type]

        if trade_ids:
            query += " AND trade_id = ANY(%s)"
            params.append(trade_ids)

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                rows = cur.fetchall()

            # Index by trade_id
            result = {}
            for row in rows:
                result[row['trade_id']] = dict(row)
            return result

        except Exception as e:
            logger.error(f"Error fetching stop analysis: {e}")
            self.conn.rollback()
            return {}

    # =========================================================================
    # M1 INDICATOR BARS DATA
    # =========================================================================

    def fetch_m1_indicator_bars_before_entry(
        self,
        ticker: str,
        bar_date: date,
        entry_time: time,
        num_bars: int = LOOKBACK_BARS + 1  # +1 for entry bar
    ) -> List[Dict[str, Any]]:
        """
        Fetch M1 indicator bars leading up to and including entry.

        Parameters:
            ticker: Stock symbol
            bar_date: Trading date
            entry_time: Entry time (bar 0)
            num_bars: Number of bars to fetch (default 16 = 15 + entry)

        Returns:
            List of bar dicts in chronological order (oldest first)
        """
        self._ensure_connected()

        # Convert entry_time to string if needed
        if isinstance(entry_time, time):
            entry_time_str = entry_time.strftime('%H:%M:%S')
        else:
            entry_time_str = str(entry_time)

        query = """
            SELECT
                bar_time,
                candle_range_pct,
                vol_delta,
                vol_roc,
                sma_spread,
                sma_momentum_ratio,
                m15_structure,
                h1_structure,
                long_score,
                short_score
            FROM m1_indicator_bars
            WHERE ticker = %s
              AND bar_date = %s
              AND bar_time <= %s
            ORDER BY bar_time DESC
            LIMIT %s
        """
        params = [ticker.upper(), bar_date, entry_time_str, num_bars]

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                rows = cur.fetchall()

            # Reverse to chronological order (oldest first)
            return [dict(row) for row in reversed(rows)]

        except Exception as e:
            logger.error(f"Error fetching m1_indicator_bars: {e}")
            self.conn.rollback()
            return []

    def fetch_m1_indicator_bars_batch(
        self,
        trade_requests: List[Tuple[str, str, date, time]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Batch fetch M1 indicator bars for multiple trades.

        More efficient than individual queries for bulk processing.

        Parameters:
            trade_requests: List of (trade_id, ticker, bar_date, entry_time) tuples

        Returns:
            Dict mapping trade_id to list of bars
        """
        result = {}
        for trade_id, ticker, bar_date, entry_time in trade_requests:
            bars = self.fetch_m1_indicator_bars_before_entry(
                ticker=ticker,
                bar_date=bar_date,
                entry_time=entry_time,
                num_bars=LOOKBACK_BARS + 1
            )
            result[trade_id] = bars

        return result

    # =========================================================================
    # COMBINED DATA FETCH
    # =========================================================================

    def fetch_complete_trade_data(
        self,
        trade_ids: Optional[List[str]] = None,
        stop_type: str = STOP_TYPE
    ) -> List[Dict[str, Any]]:
        """
        Fetch complete data needed for ramp-up analysis.

        Combines trades, stop_analysis, and m1_indicator_bars.

        Parameters:
            trade_ids: Optional list of specific trade IDs
            stop_type: Stop type for outcome data

        Returns:
            List of complete trade records with all required fields
        """
        # Get trades
        trades = self.fetch_trades(trade_ids=trade_ids)
        if not trades:
            return []

        # Get trade IDs for filtering
        ids = [t['trade_id'] for t in trades]

        # Get stop analysis indexed by trade_id
        stop_data = self.fetch_stop_analysis(trade_ids=ids, stop_type=stop_type)

        # Build complete records
        complete_trades = []
        for trade in trades:
            trade_id = trade['trade_id']

            # Skip if no stop analysis data
            if trade_id not in stop_data:
                logger.debug(f"Skipping {trade_id}: no stop analysis data")
                continue

            # Merge stop analysis data
            stop = stop_data[trade_id]
            trade['outcome'] = stop['outcome']
            trade['mfe_distance'] = stop['mfe_distance']
            trade['r_achieved'] = stop['r_achieved']

            # Fetch M1 indicator bars
            bars = self.fetch_m1_indicator_bars_before_entry(
                ticker=trade['ticker'],
                bar_date=trade['date'],
                entry_time=trade['entry_time']
            )

            trade['m1_bars'] = bars
            trade['bars_count'] = len(bars)

            complete_trades.append(trade)

        return complete_trades

    # =========================================================================
    # STATISTICS
    # =========================================================================

    def get_processing_stats(self, stop_type: str = STOP_TYPE) -> Dict[str, int]:
        """
        Get statistics about processing state.

        Returns:
            Dict with counts: total_trades, processed, remaining
        """
        all_trades = set(self.fetch_all_trade_ids())
        processed = set(self.fetch_processed_trade_ids(stop_type))

        return {
            'total_trades': len(all_trades),
            'processed': len(processed),
            'remaining': len(all_trades - processed),
        }


# Module-level singleton
_fetcher = None


def get_fetcher() -> RampUpDataFetcher:
    """Get or create the data fetcher singleton."""
    global _fetcher
    if _fetcher is None:
        _fetcher = RampUpDataFetcher()
        _fetcher.connect()
    return _fetcher
