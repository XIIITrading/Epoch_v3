"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
MFE/MAE Potential Calculator
XIII Trading LLC
================================================================================

Calculates POTENTIAL MFE (Max Favorable Excursion) and MAE (Max Adverse Excursion)
for all trades, measuring from entry time to end-of-day (15:30 ET).

This supplements the REALIZED MFE/MAE which measures entry to exit.

Realized MFE/MAE (in optimal_trade):  "What happened during the trade?"
Potential MFE/MAE (this calculator):  "What was possible in the market?"

The potential metrics allow us to evaluate exit timing effectiveness
and identify if we're leaving money on the table.

CALCULATION LOGIC:
    For LONG trades:
        MFE = (highest_high - entry_price) / stop_distance
        MAE = (entry_price - lowest_low) / stop_distance

    For SHORT trades:
        MFE = (entry_price - lowest_low) / stop_distance
        MAE = (highest_high - entry_price) / stop_distance

    Both MAE and MFE are returned as positive values.

Version: 1.0.0
================================================================================
"""

import psycopg2
from psycopg2.extras import execute_values
import pandas as pd
import numpy as np
from datetime import datetime, date, time, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging

from config import DB_CONFIG, EOD_CUTOFF, MIN_RISK_DOLLARS, SOURCE_TABLE, TARGET_TABLE
from m1_fetcher import M1Fetcher


def _convert_numpy(value):
    """Convert numpy types to Python native types for database insertion."""
    if value is None:
        return None
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value) if not np.isnan(value) else None
    if isinstance(value, np.ndarray):
        return value.tolist()
    return value


# =============================================================================
# DATA STRUCTURES
# =============================================================================
@dataclass
class MFEMAEPotentialResult:
    """Result of MFE/MAE potential calculation for a single trade."""
    trade_id: str
    date: date
    ticker: str
    direction: str
    model: str
    entry_time: time
    entry_price: float
    stop_price: float
    stop_distance: float

    # Potential MFE
    mfe_r_potential: float
    mfe_potential_price: float
    mfe_potential_time: time

    # Potential MAE
    mae_r_potential: float
    mae_potential_price: float
    mae_potential_time: time

    # Metadata
    bars_analyzed: int
    eod_cutoff: time

    # Comparison (from trades table)
    pnl_r: Optional[float] = None
    is_winner: Optional[bool] = None

    # Realized MFE/MAE (from optimal_trade if available)
    mfe_r_realized: Optional[float] = None
    mae_r_realized: Optional[float] = None


# =============================================================================
# CALCULATOR CLASS
# =============================================================================
class MFEMAEPotentialCalculator:
    """
    Calculates potential MFE/MAE (entry to EOD) for all trades.

    This class:
    1. Queries trades from Supabase that need calculation
    2. Groups trades by (ticker, date) to minimize API calls
    3. Fetches 1-minute bars from Polygon
    4. Calculates MFE/MAE potential for each trade
    5. Writes results back to Supabase
    """

    def __init__(self,
                 fetcher: M1Fetcher = None,
                 eod_time: time = None,
                 verbose: bool = True):
        """
        Initialize the calculator.

        Args:
            fetcher: M1Fetcher instance (created if not provided)
            eod_time: End of day cutoff time (default 15:30 ET)
            verbose: Enable verbose logging
        """
        self.fetcher = fetcher or M1Fetcher()
        self.eod_time = eod_time or EOD_CUTOFF
        self.verbose = verbose
        self.logger = logging.getLogger(__name__)

        # Statistics
        self.stats = {
            'trades_processed': 0,
            'trades_skipped': 0,
            'api_calls_made': 0,
            'errors': []
        }

    def _log(self, message: str, level: str = 'info'):
        """Log message if verbose mode is enabled."""
        if self.verbose:
            if level == 'info':
                print(f"  {message}")
            elif level == 'warning':
                print(f"  WARNING: {message}")
            elif level == 'error':
                print(f"  ERROR: {message}")

    # =========================================================================
    # DATABASE OPERATIONS
    # =========================================================================
    def get_trades_needing_calculation(self, conn, limit: int = None) -> pd.DataFrame:
        """
        Query trades table for records not yet in mfe_mae_potential.

        Args:
            conn: Database connection
            limit: Maximum number of trades to return (for testing)

        Returns:
            DataFrame of trades needing calculation
        """
        query = f"""
            SELECT
                t.trade_id,
                t.date,
                t.ticker,
                t.direction,
                t.model,
                t.entry_time,
                t.entry_price,
                t.stop_price,
                t.pnl_r,
                t.is_winner
            FROM {SOURCE_TABLE} t
            LEFT JOIN {TARGET_TABLE} m ON t.trade_id = m.trade_id
            WHERE m.trade_id IS NULL
              AND t.entry_time IS NOT NULL
              AND t.entry_price IS NOT NULL
              AND t.stop_price IS NOT NULL
            ORDER BY t.date, t.ticker, t.entry_time
        """

        if limit:
            query += f" LIMIT {limit}"

        # Use cursor to avoid pandas SQLAlchemy warning
        with conn.cursor() as cur:
            cur.execute(query)
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()

        df = pd.DataFrame(rows, columns=columns)
        return df

    def get_realized_mfe_mae(self, conn, trade_ids: List[str]) -> Dict[str, Dict]:
        """
        Fetch realized MFE/MAE from optimal_trade table for comparison.

        Args:
            conn: Database connection
            trade_ids: List of trade IDs to fetch

        Returns:
            Dict mapping trade_id to {'mfe_r': float, 'mae_r': float}
        """
        if not trade_ids:
            return {}

        # Build placeholders for IN clause
        placeholders = ','.join(['%s'] * len(trade_ids))

        query = f"""
            SELECT
                trade_id,
                event_type,
                points_at_event
            FROM optimal_trade
            WHERE trade_id IN ({placeholders})
              AND event_type IN ('MFE', 'MAE')
        """

        with conn.cursor() as cur:
            cur.execute(query, tuple(trade_ids))
            rows = cur.fetchall()

        # Organize by trade_id
        result = {}
        for trade_id, event_type, points_at_event in rows:
            if trade_id not in result:
                result[trade_id] = {}

            if event_type == 'MFE':
                result[trade_id]['mfe_r'] = abs(float(points_at_event)) if points_at_event else None
            elif event_type == 'MAE':
                result[trade_id]['mae_r'] = abs(float(points_at_event)) if points_at_event else None

        return result

    def insert_results(self, conn, results: List[MFEMAEPotentialResult]) -> int:
        """
        Insert calculation results into mfe_mae_potential table.

        Args:
            conn: Database connection
            results: List of calculation results

        Returns:
            Number of records inserted
        """
        if not results:
            return 0

        query = f"""
            INSERT INTO {TARGET_TABLE} (
                trade_id, date, ticker, direction, model,
                entry_time, entry_price, stop_price, stop_distance,
                mfe_r_potential, mfe_potential_price, mfe_potential_time,
                mae_r_potential, mae_potential_price, mae_potential_time,
                bars_analyzed, eod_cutoff,
                mfe_r_realized, mae_r_realized, pnl_r, is_winner
            ) VALUES %s
            ON CONFLICT (trade_id) DO NOTHING
        """

        values = [
            (
                r.trade_id, r.date, r.ticker, r.direction, r.model,
                r.entry_time, _convert_numpy(r.entry_price), _convert_numpy(r.stop_price), _convert_numpy(r.stop_distance),
                _convert_numpy(r.mfe_r_potential), _convert_numpy(r.mfe_potential_price), r.mfe_potential_time,
                _convert_numpy(r.mae_r_potential), _convert_numpy(r.mae_potential_price), r.mae_potential_time,
                _convert_numpy(r.bars_analyzed), r.eod_cutoff,
                _convert_numpy(r.mfe_r_realized), _convert_numpy(r.mae_r_realized), _convert_numpy(r.pnl_r), r.is_winner
            )
            for r in results
        ]

        with conn.cursor() as cur:
            execute_values(cur, query, values)

        return len(results)

    # =========================================================================
    # CALCULATION LOGIC
    # =========================================================================
    def calculate_single_trade(self,
                               trade: Dict[str, Any],
                               bars_df: pd.DataFrame) -> Optional[MFEMAEPotentialResult]:
        """
        Calculate MFE/MAE potential for a single trade.

        Args:
            trade: Trade record from database
            bars_df: DataFrame of 1-minute bars for the day

        Returns:
            MFEMAEPotentialResult or None if calculation fails
        """
        trade_id = trade['trade_id']
        direction = trade['direction'].upper() if trade['direction'] else None
        entry_price = float(trade['entry_price'])
        stop_price = float(trade['stop_price'])
        entry_time = trade['entry_time']

        # Handle entry_time as timedelta (from psycopg2)
        if isinstance(entry_time, timedelta):
            total_seconds = int(entry_time.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            entry_time = time(hours, minutes, seconds)

        # Calculate stop distance (1R unit)
        stop_distance = abs(entry_price - stop_price)

        if stop_distance < MIN_RISK_DOLLARS:
            self._log(f"Skipping {trade_id}: stop_distance too small ({stop_distance:.4f})", 'warning')
            return None

        if not direction or direction not in ('LONG', 'SHORT'):
            self._log(f"Skipping {trade_id}: invalid direction ({direction})", 'warning')
            return None

        if bars_df.empty:
            self._log(f"Skipping {trade_id}: no bar data available", 'warning')
            return None

        # Filter bars: entry_time <= bar_time <= eod_time
        bars_df = bars_df.copy()
        bars_df['bar_time'] = bars_df['timestamp'].apply(lambda x: x.time())

        # Filter to bars from entry time onwards
        mask = (bars_df['bar_time'] >= entry_time) & (bars_df['bar_time'] <= self.eod_time)
        filtered_bars = bars_df[mask]

        if filtered_bars.empty:
            self._log(f"Skipping {trade_id}: no bars between {entry_time} and {self.eod_time}", 'warning')
            return None

        bars_analyzed = len(filtered_bars)

        # Calculate MFE and MAE based on direction
        if direction == 'LONG':
            # MFE: highest high (favorable for long)
            mfe_idx = filtered_bars['high'].idxmax()
            mfe_price = filtered_bars.loc[mfe_idx, 'high']
            mfe_time = filtered_bars.loc[mfe_idx, 'bar_time']
            mfe_r = (mfe_price - entry_price) / stop_distance

            # MAE: lowest low (adverse for long)
            mae_idx = filtered_bars['low'].idxmin()
            mae_price = filtered_bars.loc[mae_idx, 'low']
            mae_time = filtered_bars.loc[mae_idx, 'bar_time']
            mae_r = (entry_price - mae_price) / stop_distance

        else:  # SHORT
            # MFE: lowest low (favorable for short)
            mfe_idx = filtered_bars['low'].idxmin()
            mfe_price = filtered_bars.loc[mfe_idx, 'low']
            mfe_time = filtered_bars.loc[mfe_idx, 'bar_time']
            mfe_r = (entry_price - mfe_price) / stop_distance

            # MAE: highest high (adverse for short)
            mae_idx = filtered_bars['high'].idxmax()
            mae_price = filtered_bars.loc[mae_idx, 'high']
            mae_time = filtered_bars.loc[mae_idx, 'bar_time']
            mae_r = (mae_price - entry_price) / stop_distance

        # MAE should always be positive (adverse = bad)
        mae_r = abs(mae_r)

        # Build result
        return MFEMAEPotentialResult(
            trade_id=trade_id,
            date=trade['date'],
            ticker=trade['ticker'],
            direction=trade['direction'],
            model=trade['model'],
            entry_time=entry_time,
            entry_price=entry_price,
            stop_price=stop_price,
            stop_distance=round(stop_distance, 4),
            mfe_r_potential=round(mfe_r, 4),
            mfe_potential_price=round(mfe_price, 4),
            mfe_potential_time=mfe_time,
            mae_r_potential=round(mae_r, 4),
            mae_potential_price=round(mae_price, 4),
            mae_potential_time=mae_time,
            bars_analyzed=bars_analyzed,
            eod_cutoff=self.eod_time,
            pnl_r=float(trade['pnl_r']) if trade.get('pnl_r') else None,
            is_winner=trade.get('is_winner')
        )

    # =========================================================================
    # BATCH PROCESSING
    # =========================================================================
    def run_batch_calculation(self,
                              limit: int = None,
                              dry_run: bool = False) -> Dict[str, Any]:
        """
        Main entry point. Process all trades needing calculation.

        Args:
            limit: Max trades to process (for testing)
            dry_run: If True, calculate but don't write to DB

        Returns:
            Dictionary with execution statistics
        """
        start_time = datetime.now()

        print("=" * 60)
        print("MFE/MAE Potential Calculator")
        print("=" * 60)
        print(f"EOD Cutoff: {self.eod_time}")
        print(f"Dry Run: {dry_run}")
        if limit:
            print(f"Limit: {limit} trades")
        print()

        # Reset statistics
        self.stats = {
            'trades_processed': 0,
            'trades_skipped': 0,
            'api_calls_made': 0,
            'errors': []
        }

        conn = None
        try:
            # Connect to database
            print("[1/5] Connecting to Supabase...")
            conn = psycopg2.connect(**DB_CONFIG)
            print("  Connected successfully")

            # Get trades needing calculation
            print("\n[2/5] Querying trades needing calculation...")
            trades_df = self.get_trades_needing_calculation(conn, limit)
            print(f"  Found {len(trades_df)} trades to process")

            if trades_df.empty:
                print("\n  No trades need calculation. Exiting.")
                return self._build_result(start_time)

            # Get realized MFE/MAE for comparison
            print("\n[3/5] Fetching realized MFE/MAE from optimal_trade...")
            trade_ids = trades_df['trade_id'].tolist()
            realized_data = self.get_realized_mfe_mae(conn, trade_ids)
            print(f"  Found realized data for {len(realized_data)} trades")

            # Group by (ticker, date) to minimize API calls
            print("\n[4/5] Processing trades by ticker-date groups...")
            groups = trades_df.groupby(['ticker', 'date'])
            print(f"  {len(groups)} unique ticker-date combinations")

            all_results = []

            for (ticker, trade_date), group_df in groups:
                self._log(f"\nProcessing {ticker} on {trade_date} ({len(group_df)} trades)...")

                # Fetch 1-minute bars for this ticker-date
                bars_df = self.fetcher.fetch_trading_day(ticker, trade_date)
                self.stats['api_calls_made'] += 1

                if bars_df.empty:
                    self._log(f"No bar data for {ticker} on {trade_date}", 'warning')
                    self.stats['trades_skipped'] += len(group_df)
                    continue

                # Calculate for each trade in this group
                for _, trade in group_df.iterrows():
                    trade_dict = trade.to_dict()

                    # Add realized MFE/MAE if available
                    trade_id = trade_dict['trade_id']
                    if trade_id in realized_data:
                        trade_dict['mfe_r_realized'] = realized_data[trade_id].get('mfe_r')
                        trade_dict['mae_r_realized'] = realized_data[trade_id].get('mae_r')

                    result = self.calculate_single_trade(trade_dict, bars_df)

                    if result:
                        # Attach realized data
                        if trade_id in realized_data:
                            result.mfe_r_realized = realized_data[trade_id].get('mfe_r')
                            result.mae_r_realized = realized_data[trade_id].get('mae_r')

                        all_results.append(result)
                        self.stats['trades_processed'] += 1
                    else:
                        self.stats['trades_skipped'] += 1

            # Write results to database
            print(f"\n[5/5] Writing results to database...")
            if dry_run:
                print(f"  [DRY-RUN] Would insert {len(all_results)} records")
            else:
                inserted = self.insert_results(conn, all_results)
                conn.commit()
                print(f"  Inserted {inserted} records")

            return self._build_result(start_time)

        except Exception as e:
            self.stats['errors'].append(str(e))
            if conn:
                conn.rollback()
            raise

        finally:
            if conn:
                conn.close()
            # Clear fetcher cache
            self.fetcher.clear_cache()

    def _build_result(self, start_time: datetime) -> Dict[str, Any]:
        """Build the result dictionary."""
        elapsed = (datetime.now() - start_time).total_seconds()

        return {
            'trades_processed': self.stats['trades_processed'],
            'trades_skipped': self.stats['trades_skipped'],
            'api_calls_made': self.stats['api_calls_made'],
            'errors': self.stats['errors'],
            'execution_time_seconds': round(elapsed, 2)
        }


# =============================================================================
# STANDALONE TEST
# =============================================================================
if __name__ == "__main__":
    print("MFE/MAE Potential Calculator - Test Mode")
    print("=" * 60)

    # Run with limit for testing
    calculator = MFEMAEPotentialCalculator(verbose=True)
    results = calculator.run_batch_calculation(limit=5, dry_run=True)

    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    for key, value in results.items():
        print(f"  {key}: {value}")
