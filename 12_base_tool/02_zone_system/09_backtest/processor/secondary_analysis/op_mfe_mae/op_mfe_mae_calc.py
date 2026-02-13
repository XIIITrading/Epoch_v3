"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
Options MFE/MAE Potential Calculator
XIII Trading LLC
================================================================================

Calculates POTENTIAL MFE (Max Favorable Excursion) and MAE (Max Adverse Excursion)
for OPTIONS trades, measuring from entry time to end-of-day (15:30 ET).

This mirrors mfe_mae_potential_calc.py but for options contracts.
All measurements are in POINTS (price movement) and PERCENTAGE.

CALCULATION LOGIC:
    For ALL OPTIONS (we always BUY options, never short):
        MFE = highest_high - entry_price (we want price UP)
        MAE = entry_price - lowest_low (price DOWN is adverse)

    Both MFE and MAE points are returned as positive values.

    Exit = price at 15:30 ET - entry_price (can be negative for losses)

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

from config import (
    DB_CONFIG,
    EOD_CUTOFF,
    MIN_OPTION_PRICE,
    SOURCE_TRADES_TABLE,
    SOURCE_OPTIONS_TABLE,
    SOURCE_MFE_MAE_TABLE,
    TARGET_TABLE
)
from options_bar_fetcher import OptionsBarFetcher


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
class OpMFEMAEResult:
    """Result of options MFE/MAE potential calculation for a single trade."""
    # Trade identification
    trade_id: str
    date: date
    ticker: str
    direction: str
    model: str

    # Options contract info
    options_ticker: str
    strike: float
    expiration: date
    contract_type: str

    # Entry
    entry_time: time
    option_entry_price: float

    # MFE (Max Favorable Excursion)
    mfe_points: float       # highest - entry (always positive)
    mfe_price: float        # Price at MFE
    mfe_time: time          # When MFE occurred
    mfe_pct: float          # MFE as % of entry price

    # MAE (Max Adverse Excursion)
    mae_points: float       # entry - lowest (always positive)
    mae_price: float        # Price at MAE
    mae_time: time          # When MAE occurred
    mae_pct: float          # MAE as % of entry price

    # Exit (15:30)
    exit_price: float       # Price at 15:30
    exit_time: time         # Always 15:30
    exit_points: float      # exit - entry (can be negative)
    exit_pct: float         # Exit as % of entry

    # Underlying comparison
    underlying_mfe_pct: Optional[float] = None
    underlying_mae_pct: Optional[float] = None
    underlying_exit_pct: Optional[float] = None

    # Metadata
    bars_analyzed: int = 0
    eod_cutoff: time = EOD_CUTOFF


# =============================================================================
# CALCULATOR CLASS
# =============================================================================
class OpMFEMAECalculator:
    """
    Calculates options MFE/MAE potential (entry to EOD) for all trades.

    This class:
    1. Queries trades that exist in options_analysis but not in op_mfe_mae_potential
    2. Groups trades by (options_ticker, date) to minimize API calls
    3. Fetches 1-minute options bars from Polygon
    4. Calculates MFE/MAE in points and percentages
    5. Writes results back to Supabase
    """

    def __init__(self,
                 fetcher: OptionsBarFetcher = None,
                 eod_time: time = None,
                 verbose: bool = True):
        """
        Initialize the calculator.

        Args:
            fetcher: OptionsBarFetcher instance (created if not provided)
            eod_time: End of day cutoff time (default 15:30 ET)
            verbose: Enable verbose logging
        """
        self.fetcher = fetcher or OptionsBarFetcher()
        self.eod_time = eod_time or EOD_CUTOFF
        self.verbose = verbose
        self.logger = logging.getLogger(__name__)

        # Statistics
        self.stats = {
            'trades_processed': 0,
            'trades_skipped': 0,
            'trades_no_bars': 0,
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
        Query trades that need options MFE/MAE calculation.

        Finds trades that:
        1. Exist in trades table
        2. Have options data in options_analysis table (status = SUCCESS)
        3. Do NOT yet exist in op_mfe_mae_potential

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
                o.options_ticker,
                o.strike,
                o.expiration,
                o.contract_type,
                o.option_entry_price,
                o.option_entry_time
            FROM {SOURCE_TRADES_TABLE} t
            INNER JOIN {SOURCE_OPTIONS_TABLE} o ON t.trade_id = o.trade_id
            LEFT JOIN {TARGET_TABLE} m ON t.trade_id = m.trade_id
            WHERE m.trade_id IS NULL
              AND o.options_ticker IS NOT NULL
              AND o.option_entry_price IS NOT NULL
              AND o.status = 'SUCCESS'
            ORDER BY t.date, o.options_ticker
        """

        if limit:
            query += f" LIMIT {limit}"

        with conn.cursor() as cur:
            cur.execute(query)
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()

        df = pd.DataFrame(rows, columns=columns)
        return df

    def get_underlying_mfe_mae(self, conn, trade_ids: List[str]) -> Dict[str, Dict]:
        """
        Fetch underlying MFE/MAE from mfe_mae_potential table for comparison.

        Args:
            conn: Database connection
            trade_ids: List of trade IDs to fetch

        Returns:
            Dict mapping trade_id to {'mfe_pct': float, 'mae_pct': float, 'exit_pct': float}
        """
        if not trade_ids:
            return {}

        # Build placeholders for IN clause
        placeholders = ','.join(['%s'] * len(trade_ids))

        query = f"""
            SELECT
                trade_id,
                mfe_r_potential,
                mae_r_potential,
                entry_price,
                mfe_potential_price,
                mae_potential_price
            FROM {SOURCE_MFE_MAE_TABLE}
            WHERE trade_id IN ({placeholders})
        """

        with conn.cursor() as cur:
            cur.execute(query, tuple(trade_ids))
            rows = cur.fetchall()

        # Calculate percentages from the underlying data
        result = {}
        for row in rows:
            trade_id, mfe_r, mae_r, entry_price, mfe_price, mae_price = row

            # Calculate MFE/MAE percentages for underlying
            if entry_price and mfe_price:
                mfe_pct = abs(float(mfe_price) - float(entry_price)) / float(entry_price) * 100
            else:
                mfe_pct = None

            if entry_price and mae_price:
                mae_pct = abs(float(entry_price) - float(mae_price)) / float(entry_price) * 100
            else:
                mae_pct = None

            result[trade_id] = {
                'mfe_pct': mfe_pct,
                'mae_pct': mae_pct,
                'exit_pct': None  # Could add if we store exit price in mfe_mae_potential
            }

        return result

    def insert_results(self, conn, results: List[OpMFEMAEResult]) -> int:
        """
        Insert calculation results into op_mfe_mae_potential table.

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
                options_ticker, strike, expiration, contract_type,
                entry_time, option_entry_price,
                mfe_points, mfe_price, mfe_time, mfe_pct,
                mae_points, mae_price, mae_time, mae_pct,
                exit_price, exit_time, exit_points, exit_pct,
                underlying_mfe_pct, underlying_mae_pct, underlying_exit_pct,
                bars_analyzed, eod_cutoff
            ) VALUES %s
            ON CONFLICT (trade_id) DO NOTHING
        """

        values = [
            (
                r.trade_id, r.date, r.ticker, r.direction, r.model,
                r.options_ticker, _convert_numpy(r.strike), r.expiration, r.contract_type,
                r.entry_time, _convert_numpy(r.option_entry_price),
                _convert_numpy(r.mfe_points), _convert_numpy(r.mfe_price), r.mfe_time, _convert_numpy(r.mfe_pct),
                _convert_numpy(r.mae_points), _convert_numpy(r.mae_price), r.mae_time, _convert_numpy(r.mae_pct),
                _convert_numpy(r.exit_price), r.exit_time, _convert_numpy(r.exit_points), _convert_numpy(r.exit_pct),
                _convert_numpy(r.underlying_mfe_pct), _convert_numpy(r.underlying_mae_pct), _convert_numpy(r.underlying_exit_pct),
                _convert_numpy(r.bars_analyzed), r.eod_cutoff
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
                               bars_df: pd.DataFrame) -> Optional[OpMFEMAEResult]:
        """
        Calculate MFE/MAE for a single options trade.

        For ALL OPTIONS (we always BUY, never short):
            - MFE = highest price - entry price (want price UP)
            - MAE = entry price - lowest price (DOWN is adverse)

        Args:
            trade: Trade record with options data
            bars_df: DataFrame of 1-minute options bars for the day

        Returns:
            OpMFEMAEResult or None if calculation fails
        """
        trade_id = trade['trade_id']
        options_ticker = trade['options_ticker']
        entry_price = float(trade['option_entry_price'])
        entry_time = trade.get('option_entry_time') or trade.get('entry_time')

        # Handle entry_time as timedelta (from psycopg2)
        if isinstance(entry_time, timedelta):
            total_seconds = int(entry_time.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            entry_time = time(hours, minutes, seconds)

        # Validate entry price
        if entry_price < MIN_OPTION_PRICE:
            self._log(f"Skipping {trade_id}: option price too low (${entry_price:.4f})", 'warning')
            return None

        if bars_df.empty:
            self._log(f"Skipping {trade_id}: no bar data available", 'warning')
            self.stats['trades_no_bars'] += 1
            return None

        # Filter bars: entry_time <= bar_time <= eod_time
        bars_df = bars_df.copy()
        bars_df['bar_time'] = bars_df['timestamp'].apply(lambda x: x.time())

        # Filter to bars from entry time onwards
        mask = (bars_df['bar_time'] >= entry_time) & (bars_df['bar_time'] <= self.eod_time)
        filtered_bars = bars_df[mask]

        if filtered_bars.empty:
            self._log(f"Skipping {trade_id}: no bars between {entry_time} and {self.eod_time}", 'warning')
            self.stats['trades_no_bars'] += 1
            return None

        bars_analyzed = len(filtered_bars)

        # Calculate MFE (highest price - we want UP)
        mfe_idx = filtered_bars['high'].idxmax()
        mfe_price = filtered_bars.loc[mfe_idx, 'high']
        mfe_time = filtered_bars.loc[mfe_idx, 'bar_time']
        mfe_points = mfe_price - entry_price  # Favorable movement (positive)

        # Calculate MAE (lowest price - DOWN is adverse)
        mae_idx = filtered_bars['low'].idxmin()
        mae_price = filtered_bars.loc[mae_idx, 'low']
        mae_time = filtered_bars.loc[mae_idx, 'bar_time']
        mae_points = entry_price - mae_price  # Adverse movement (positive)

        # Get exit price (last bar, which should be near 15:30)
        last_bar = filtered_bars.iloc[-1]
        exit_price = last_bar['close']
        exit_time_actual = last_bar['bar_time']
        exit_points = exit_price - entry_price  # Can be negative

        # Calculate percentages
        mfe_pct = (mfe_points / entry_price) * 100 if entry_price > 0 else 0
        mae_pct = (mae_points / entry_price) * 100 if entry_price > 0 else 0
        exit_pct = (exit_points / entry_price) * 100 if entry_price > 0 else 0

        # Ensure MFE and MAE points are positive
        mfe_points = abs(mfe_points)
        mae_points = abs(mae_points)

        # Parse expiration date
        expiration = trade.get('expiration')
        if isinstance(expiration, str):
            expiration = datetime.strptime(expiration, '%Y-%m-%d').date()

        # Build result
        return OpMFEMAEResult(
            trade_id=trade_id,
            date=trade['date'],
            ticker=trade['ticker'],
            direction=trade.get('direction'),
            model=trade.get('model'),
            options_ticker=options_ticker,
            strike=float(trade.get('strike', 0)),
            expiration=expiration,
            contract_type=trade.get('contract_type'),
            entry_time=entry_time,
            option_entry_price=round(entry_price, 4),
            mfe_points=round(mfe_points, 4),
            mfe_price=round(mfe_price, 4),
            mfe_time=mfe_time,
            mfe_pct=round(mfe_pct, 4),
            mae_points=round(mae_points, 4),
            mae_price=round(mae_price, 4),
            mae_time=mae_time,
            mae_pct=round(mae_pct, 4),
            exit_price=round(exit_price, 4),
            exit_time=exit_time_actual,
            exit_points=round(exit_points, 4),
            exit_pct=round(exit_pct, 4),
            bars_analyzed=bars_analyzed,
            eod_cutoff=self.eod_time
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
        print("Options MFE/MAE Potential Calculator")
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
            'trades_no_bars': 0,
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

            # Get underlying MFE/MAE for comparison
            print("\n[3/5] Fetching underlying MFE/MAE for comparison...")
            trade_ids = trades_df['trade_id'].tolist()
            underlying_data = self.get_underlying_mfe_mae(conn, trade_ids)
            print(f"  Found underlying data for {len(underlying_data)} trades")

            # Group by (options_ticker, date) to minimize API calls
            print("\n[4/5] Processing trades by options ticker-date groups...")
            groups = trades_df.groupby(['options_ticker', 'date'])
            print(f"  {len(groups)} unique options ticker-date combinations")

            all_results = []

            for (options_ticker, trade_date), group_df in groups:
                self._log(f"\nProcessing {options_ticker} on {trade_date} ({len(group_df)} trades)...")

                # Fetch 1-minute bars for this options contract on this date
                bars_df = self.fetcher.fetch_trading_day(options_ticker, trade_date)
                self.stats['api_calls_made'] += 1

                if bars_df.empty:
                    self._log(f"No bar data for {options_ticker} on {trade_date}", 'warning')
                    self.stats['trades_skipped'] += len(group_df)
                    self.stats['trades_no_bars'] += len(group_df)
                    continue

                # Calculate for each trade in this group
                for _, trade in group_df.iterrows():
                    trade_dict = trade.to_dict()

                    result = self.calculate_single_trade(trade_dict, bars_df)

                    if result:
                        # Attach underlying comparison data
                        trade_id = trade_dict['trade_id']
                        if trade_id in underlying_data:
                            result.underlying_mfe_pct = underlying_data[trade_id].get('mfe_pct')
                            result.underlying_mae_pct = underlying_data[trade_id].get('mae_pct')
                            result.underlying_exit_pct = underlying_data[trade_id].get('exit_pct')

                        all_results.append(result)
                        self.stats['trades_processed'] += 1
                    else:
                        self.stats['trades_skipped'] += 1

            # Write results to database
            print(f"\n[5/5] Writing results to database...")
            if dry_run:
                print(f"  [DRY-RUN] Would insert {len(all_results)} records")
                # Print sample results
                if all_results:
                    print("\n  Sample results:")
                    for r in all_results[:3]:
                        print(f"    {r.trade_id}: MFE={r.mfe_pct:.2f}%, MAE={r.mae_pct:.2f}%, Exit={r.exit_pct:.2f}%")
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
            'trades_no_bars': self.stats['trades_no_bars'],
            'api_calls_made': self.stats['api_calls_made'],
            'errors': self.stats['errors'],
            'execution_time_seconds': round(elapsed, 2)
        }


# =============================================================================
# STANDALONE TEST
# =============================================================================
if __name__ == "__main__":
    print("Options MFE/MAE Potential Calculator - Test Mode")
    print("=" * 60)

    # Run with limit for testing
    calculator = OpMFEMAECalculator(verbose=True)
    results = calculator.run_batch_calculation(limit=5, dry_run=True)

    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    for key, value in results.items():
        print(f"  {key}: {value}")
