"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
Optimal Trade Calculator (Points-Based)
XIII Trading LLC
================================================================================

Calculates optimal_trade events (ENTRY, MFE, MAE, EXIT) using:
- trades table for entry data
- mfe_mae_potential table for MFE/MAE timing
- m5_trade_bars table for indicator values and health scores

Win Condition: mfe_potential_time < mae_potential_time (temporal)
P&L: Points (absolute dollars) instead of R-multiples
Exit: Fixed 15:30 ET

Version: 2.0.0
================================================================================
"""

import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, date, time, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import logging

from config import (
    DB_CONFIG, EOD_CUTOFF, TARGET_TABLE,
    TRADES_TABLE, MFE_MAE_TABLE, M5_TRADE_BARS_TABLE,
    HEALTH_IMPROVING_THRESHOLD, HEALTH_DEGRADING_THRESHOLD,
    BATCH_INSERT_SIZE, VERBOSE
)


# =============================================================================
# DATA STRUCTURES
# =============================================================================
@dataclass
class TradeData:
    """Trade data from trades and mfe_mae_potential tables."""
    trade_id: str
    date: date
    ticker: str
    direction: str
    model: Optional[str]
    entry_time: time
    entry_price: float

    # From mfe_mae_potential
    mfe_time: time
    mfe_price: float
    mae_time: time
    mae_price: float


@dataclass
class BarIndicators:
    """Indicator values from m5_trade_bars."""
    bar_time: time
    close: float

    # Health
    health_score: Optional[int] = None
    health_label: Optional[str] = None
    structure_score: Optional[int] = None
    volume_score: Optional[int] = None
    price_score: Optional[int] = None

    # Price indicators
    vwap: Optional[float] = None
    sma9: Optional[float] = None
    sma21: Optional[float] = None
    sma_spread: Optional[float] = None
    sma_momentum_ratio: Optional[float] = None
    sma_momentum_label: Optional[str] = None

    # Volume indicators
    vol_roc: Optional[float] = None
    vol_delta: Optional[float] = None
    cvd_slope: Optional[float] = None

    # Structure
    m5_structure: Optional[str] = None
    m15_structure: Optional[str] = None
    h1_structure: Optional[str] = None
    h4_structure: Optional[str] = None

    # Healthy flags
    sma_alignment_healthy: Optional[bool] = None
    sma_momentum_healthy: Optional[bool] = None
    vwap_healthy: Optional[bool] = None
    vol_roc_healthy: Optional[bool] = None
    vol_delta_healthy: Optional[bool] = None
    cvd_slope_healthy: Optional[bool] = None
    m5_structure_healthy: Optional[bool] = None
    m15_structure_healthy: Optional[bool] = None
    h1_structure_healthy: Optional[bool] = None
    h4_structure_healthy: Optional[bool] = None


@dataclass
class OptimalTradeEvent:
    """Single event row for optimal_trade table."""
    trade_id: str
    event_type: str  # ENTRY, MFE, MAE, EXIT
    date: date
    ticker: str
    direction: str
    model: Optional[str]
    win: int  # 1 or 0

    event_time: time
    bars_from_entry: int

    entry_price: float
    price_at_event: float
    points_at_event: float
    actual_points: float

    # Health
    health_score: Optional[int] = None
    health_label: Optional[str] = None
    health_delta: Optional[int] = None
    health_summary: Optional[str] = None

    # Component scores
    structure_score: Optional[int] = None
    volume_score: Optional[int] = None
    price_score: Optional[int] = None

    # Price indicators
    vwap: Optional[float] = None
    sma9: Optional[float] = None
    sma21: Optional[float] = None
    sma_spread: Optional[float] = None
    sma_momentum_ratio: Optional[float] = None
    sma_momentum_label: Optional[str] = None

    # Volume indicators
    vol_roc: Optional[float] = None
    vol_delta: Optional[float] = None
    cvd_slope: Optional[float] = None

    # Structure
    m5_structure: Optional[str] = None
    m15_structure: Optional[str] = None
    h1_structure: Optional[str] = None
    h4_structure: Optional[str] = None

    # Healthy flags
    sma_alignment_healthy: Optional[bool] = None
    sma_momentum_healthy: Optional[bool] = None
    vwap_healthy: Optional[bool] = None
    vol_roc_healthy: Optional[bool] = None
    vol_delta_healthy: Optional[bool] = None
    cvd_slope_healthy: Optional[bool] = None
    m5_structure_healthy: Optional[bool] = None
    m15_structure_healthy: Optional[bool] = None
    h1_structure_healthy: Optional[bool] = None
    h4_structure_healthy: Optional[bool] = None


# =============================================================================
# CALCULATOR CLASS
# =============================================================================
class OptimalTradeCalculator:
    """
    Calculates optimal_trade events using points-based methodology.

    Data Flow:
        trades (source of truth)
            │
            ├──► mfe_mae_potential (MFE/MAE times & prices)
            │
            └──► m5_trade_bars (health scores & indicators by bar_time)
                    │
                    ▼
              optimal_trade (4 events per trade)
    """

    def __init__(self, verbose: bool = VERBOSE):
        """Initialize the calculator."""
        self.verbose = verbose
        self.logger = logging.getLogger(__name__)

        # Statistics
        self.stats = {
            'trades_processed': 0,
            'trades_skipped': 0,
            'events_created': 0,
            'errors': []
        }

    def _log(self, message: str, level: str = 'info'):
        """Log message if verbose mode is enabled."""
        if self.verbose:
            prefix = {'info': '  ', 'warning': '  WARNING: ', 'error': '  ERROR: '}
            print(f"{prefix.get(level, '  ')}{message}")

    # =========================================================================
    # UTILITY FUNCTIONS
    # =========================================================================
    @staticmethod
    def floor_to_m5(event_time: time) -> time:
        """Floor a time to the start of its M5 bar.

        Example: 10:07:23 → 10:05:00
        """
        if isinstance(event_time, timedelta):
            total_seconds = int(event_time.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            event_time = time(hours, minutes)

        total_minutes = event_time.hour * 60 + event_time.minute
        floored_minutes = (total_minutes // 5) * 5
        return time(floored_minutes // 60, floored_minutes % 60)

    @staticmethod
    def calculate_points(direction: str, entry_price: float, current_price: float) -> float:
        """Calculate points from entry (direction-adjusted).

        LONG: current - entry (positive = profit)
        SHORT: entry - current (positive = profit)
        """
        if direction.upper() == 'LONG':
            return round(current_price - entry_price, 4)
        else:  # SHORT
            return round(entry_price - current_price, 4)

    @staticmethod
    def calculate_bars_from_entry(entry_time: time, event_time: time) -> int:
        """Calculate M5 bars from entry to event."""
        entry_minutes = entry_time.hour * 60 + entry_time.minute
        event_minutes = event_time.hour * 60 + event_time.minute
        return max(0, (event_minutes - entry_minutes) // 5)

    @staticmethod
    def calculate_health_summary(health_delta: Optional[int]) -> str:
        """Determine health trend from entry."""
        if health_delta is None:
            return 'STABLE'
        if health_delta >= HEALTH_IMPROVING_THRESHOLD:
            return 'IMPROVING'
        elif health_delta <= HEALTH_DEGRADING_THRESHOLD:
            return 'DEGRADING'
        return 'STABLE'

    @staticmethod
    def time_to_comparable(t: time) -> int:
        """Convert time to minutes since midnight for comparison."""
        if isinstance(t, timedelta):
            return int(t.total_seconds() // 60)
        return t.hour * 60 + t.minute

    # =========================================================================
    # DATABASE QUERIES
    # =========================================================================
    def get_trades_with_mfe_mae(self, conn, limit: Optional[int] = None) -> List[TradeData]:
        """
        Get trades that have mfe_mae_potential data.

        Returns trades joined with mfe_mae_potential.
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
                m.mfe_potential_time,
                m.mfe_potential_price,
                m.mae_potential_time,
                m.mae_potential_price
            FROM {TRADES_TABLE} t
            INNER JOIN {MFE_MAE_TABLE} m ON t.trade_id = m.trade_id
            WHERE t.entry_time IS NOT NULL
              AND t.entry_price IS NOT NULL
              AND t.direction IS NOT NULL
              AND m.mfe_potential_time IS NOT NULL
              AND m.mae_potential_time IS NOT NULL
            ORDER BY t.date, t.ticker, t.entry_time
        """

        if limit:
            query += f" LIMIT {limit}"

        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]

        trades = []
        for row in rows:
            row_dict = dict(zip(columns, row))

            # Convert timedelta to time if needed
            entry_time = row_dict['entry_time']
            if isinstance(entry_time, timedelta):
                total_sec = int(entry_time.total_seconds())
                entry_time = time(total_sec // 3600, (total_sec % 3600) // 60, total_sec % 60)

            mfe_time = row_dict['mfe_potential_time']
            if isinstance(mfe_time, timedelta):
                total_sec = int(mfe_time.total_seconds())
                mfe_time = time(total_sec // 3600, (total_sec % 3600) // 60, total_sec % 60)

            mae_time = row_dict['mae_potential_time']
            if isinstance(mae_time, timedelta):
                total_sec = int(mae_time.total_seconds())
                mae_time = time(total_sec // 3600, (total_sec % 3600) // 60, total_sec % 60)

            trades.append(TradeData(
                trade_id=row_dict['trade_id'],
                date=row_dict['date'],
                ticker=row_dict['ticker'],
                direction=row_dict['direction'],
                model=row_dict['model'],
                entry_time=entry_time,
                entry_price=float(row_dict['entry_price']),
                mfe_time=mfe_time,
                mfe_price=float(row_dict['mfe_potential_price']),
                mae_time=mae_time,
                mae_price=float(row_dict['mae_potential_price']),
            ))

        return trades

    def get_trade_bars(self, conn, trade_id: str) -> Dict[time, BarIndicators]:
        """
        Get all m5_trade_bars for a trade, indexed by bar_time.
        """
        query = f"""
            SELECT
                bar_time,
                close,
                health_score,
                health_label,
                structure_score,
                volume_score,
                price_score,
                vwap,
                sma9,
                sma21,
                sma_spread,
                sma_momentum_ratio,
                sma_momentum_label,
                vol_roc,
                vol_delta,
                cvd_slope,
                m5_structure,
                m15_structure,
                h1_structure,
                h4_structure,
                sma_alignment_healthy,
                sma_momentum_healthy,
                vwap_healthy,
                vol_roc_healthy,
                vol_delta_healthy,
                cvd_slope_healthy,
                m5_structure_healthy,
                m15_structure_healthy,
                h1_structure_healthy,
                h4_structure_healthy
            FROM {M5_TRADE_BARS_TABLE}
            WHERE trade_id = %s
            ORDER BY bar_time
        """

        with conn.cursor() as cur:
            cur.execute(query, (trade_id,))
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]

        bars = {}
        for row in rows:
            row_dict = dict(zip(columns, row))

            bar_time = row_dict['bar_time']
            if isinstance(bar_time, timedelta):
                total_sec = int(bar_time.total_seconds())
                bar_time = time(total_sec // 3600, (total_sec % 3600) // 60)

            bars[bar_time] = BarIndicators(
                bar_time=bar_time,
                close=float(row_dict['close']) if row_dict['close'] else 0,
                health_score=row_dict['health_score'],
                health_label=row_dict['health_label'],
                structure_score=row_dict['structure_score'],
                volume_score=row_dict['volume_score'],
                price_score=row_dict['price_score'],
                vwap=float(row_dict['vwap']) if row_dict['vwap'] else None,
                sma9=float(row_dict['sma9']) if row_dict['sma9'] else None,
                sma21=float(row_dict['sma21']) if row_dict['sma21'] else None,
                sma_spread=float(row_dict['sma_spread']) if row_dict['sma_spread'] else None,
                sma_momentum_ratio=float(row_dict['sma_momentum_ratio']) if row_dict['sma_momentum_ratio'] else None,
                sma_momentum_label=row_dict['sma_momentum_label'],
                vol_roc=float(row_dict['vol_roc']) if row_dict['vol_roc'] else None,
                vol_delta=float(row_dict['vol_delta']) if row_dict['vol_delta'] else None,
                cvd_slope=float(row_dict['cvd_slope']) if row_dict['cvd_slope'] else None,
                m5_structure=row_dict['m5_structure'],
                m15_structure=row_dict['m15_structure'],
                h1_structure=row_dict['h1_structure'],
                h4_structure=row_dict['h4_structure'],
                sma_alignment_healthy=row_dict['sma_alignment_healthy'],
                sma_momentum_healthy=row_dict['sma_momentum_healthy'],
                vwap_healthy=row_dict['vwap_healthy'],
                vol_roc_healthy=row_dict['vol_roc_healthy'],
                vol_delta_healthy=row_dict['vol_delta_healthy'],
                cvd_slope_healthy=row_dict['cvd_slope_healthy'],
                m5_structure_healthy=row_dict['m5_structure_healthy'],
                m15_structure_healthy=row_dict['m15_structure_healthy'],
                h1_structure_healthy=row_dict['h1_structure_healthy'],
                h4_structure_healthy=row_dict['h4_structure_healthy'],
            )

        return bars

    def truncate_optimal_trade(self, conn):
        """Delete all rows from optimal_trade table."""
        with conn.cursor() as cur:
            cur.execute(f"TRUNCATE TABLE {TARGET_TABLE}")
        self._log("Truncated optimal_trade table")

    def insert_events(self, conn, events: List[OptimalTradeEvent]) -> int:
        """Insert events into optimal_trade table."""
        if not events:
            return 0

        query = f"""
            INSERT INTO {TARGET_TABLE} (
                trade_id, event_type, date, ticker, direction, model, win,
                event_time, bars_from_entry,
                entry_price, price_at_event, points_at_event, actual_points,
                health_score, health_label, health_delta, health_summary,
                structure_score, volume_score, price_score,
                vwap, sma9, sma21, sma_spread, sma_momentum_ratio, sma_momentum_label,
                vol_roc, vol_delta, cvd_slope,
                m5_structure, m15_structure, h1_structure, h4_structure,
                sma_alignment_healthy, sma_momentum_healthy, vwap_healthy,
                vol_roc_healthy, vol_delta_healthy, cvd_slope_healthy,
                m5_structure_healthy, m15_structure_healthy, h1_structure_healthy, h4_structure_healthy
            ) VALUES %s
        """

        values = [
            (
                e.trade_id, e.event_type, e.date, e.ticker, e.direction, e.model, e.win,
                e.event_time, e.bars_from_entry,
                e.entry_price, e.price_at_event, e.points_at_event, e.actual_points,
                e.health_score, e.health_label, e.health_delta, e.health_summary,
                e.structure_score, e.volume_score, e.price_score,
                e.vwap, e.sma9, e.sma21, e.sma_spread, e.sma_momentum_ratio, e.sma_momentum_label,
                e.vol_roc, e.vol_delta, e.cvd_slope,
                e.m5_structure, e.m15_structure, e.h1_structure, e.h4_structure,
                e.sma_alignment_healthy, e.sma_momentum_healthy, e.vwap_healthy,
                e.vol_roc_healthy, e.vol_delta_healthy, e.cvd_slope_healthy,
                e.m5_structure_healthy, e.m15_structure_healthy, e.h1_structure_healthy, e.h4_structure_healthy
            )
            for e in events
        ]

        with conn.cursor() as cur:
            execute_values(cur, query, values)

        return len(events)

    # =========================================================================
    # CALCULATION LOGIC
    # =========================================================================
    def calculate_trade_events(
        self,
        trade: TradeData,
        bars: Dict[time, BarIndicators]
    ) -> Optional[List[OptimalTradeEvent]]:
        """
        Calculate all 4 events for a single trade.

        Returns list of 4 OptimalTradeEvent objects, or None if bars are missing.
        """
        # Find the bars we need
        entry_bar_time = self.floor_to_m5(trade.entry_time)
        mfe_bar_time = self.floor_to_m5(trade.mfe_time)
        mae_bar_time = self.floor_to_m5(trade.mae_time)
        exit_bar_time = EOD_CUTOFF  # 15:30

        # Check if we have the required bars
        if entry_bar_time not in bars:
            self._log(f"Missing entry bar {entry_bar_time} for {trade.trade_id}", 'warning')
            return None

        if exit_bar_time not in bars:
            # Try to find the last available bar
            available_times = sorted(bars.keys(), key=lambda t: t.hour * 60 + t.minute)
            if available_times:
                exit_bar_time = available_times[-1]
                self._log(f"Using last bar {exit_bar_time} instead of 15:30 for {trade.trade_id}", 'warning')
            else:
                self._log(f"No bars available for {trade.trade_id}", 'warning')
                return None

        # Get bar data (use closest available if exact bar missing)
        entry_bar = bars.get(entry_bar_time)
        mfe_bar = bars.get(mfe_bar_time) or self._find_closest_bar(bars, mfe_bar_time)
        mae_bar = bars.get(mae_bar_time) or self._find_closest_bar(bars, mae_bar_time)
        exit_bar = bars.get(exit_bar_time)

        if not all([entry_bar, mfe_bar, mae_bar, exit_bar]):
            self._log(f"Missing required bars for {trade.trade_id}", 'warning')
            return None

        # Determine win condition: mfe_time < mae_time
        mfe_minutes = self.time_to_comparable(trade.mfe_time)
        mae_minutes = self.time_to_comparable(trade.mae_time)
        win = 1 if mfe_minutes < mae_minutes else 0

        # Calculate points
        mfe_points = self.calculate_points(trade.direction, trade.entry_price, trade.mfe_price)
        mae_points = self.calculate_points(trade.direction, trade.entry_price, trade.mae_price)
        exit_points = self.calculate_points(trade.direction, trade.entry_price, exit_bar.close)

        # Get entry health for delta calculation
        entry_health = entry_bar.health_score

        # Build events
        events = []

        # ENTRY event
        events.append(self._build_event(
            trade=trade,
            event_type='ENTRY',
            event_time=trade.entry_time,
            price_at_event=trade.entry_price,
            points_at_event=0.0,
            actual_points=exit_points,
            win=win,
            bar=entry_bar,
            entry_health=entry_health,
            entry_time=trade.entry_time
        ))

        # MFE event
        events.append(self._build_event(
            trade=trade,
            event_type='MFE',
            event_time=trade.mfe_time,
            price_at_event=trade.mfe_price,
            points_at_event=mfe_points,
            actual_points=exit_points,
            win=win,
            bar=mfe_bar,
            entry_health=entry_health,
            entry_time=trade.entry_time
        ))

        # MAE event
        events.append(self._build_event(
            trade=trade,
            event_type='MAE',
            event_time=trade.mae_time,
            price_at_event=trade.mae_price,
            points_at_event=mae_points,
            actual_points=exit_points,
            win=win,
            bar=mae_bar,
            entry_health=entry_health,
            entry_time=trade.entry_time
        ))

        # EXIT event
        events.append(self._build_event(
            trade=trade,
            event_type='EXIT',
            event_time=exit_bar_time,
            price_at_event=exit_bar.close,
            points_at_event=exit_points,
            actual_points=exit_points,
            win=win,
            bar=exit_bar,
            entry_health=entry_health,
            entry_time=trade.entry_time
        ))

        return events

    def _find_closest_bar(self, bars: Dict[time, BarIndicators], target_time: time) -> Optional[BarIndicators]:
        """Find the closest available bar to target_time."""
        if not bars:
            return None

        target_minutes = target_time.hour * 60 + target_time.minute
        closest_bar = None
        min_diff = float('inf')

        for bar_time, bar in bars.items():
            bar_minutes = bar_time.hour * 60 + bar_time.minute
            diff = abs(bar_minutes - target_minutes)
            if diff < min_diff:
                min_diff = diff
                closest_bar = bar

        return closest_bar

    def _build_event(
        self,
        trade: TradeData,
        event_type: str,
        event_time: time,
        price_at_event: float,
        points_at_event: float,
        actual_points: float,
        win: int,
        bar: BarIndicators,
        entry_health: Optional[int],
        entry_time: time
    ) -> OptimalTradeEvent:
        """Build a single OptimalTradeEvent."""

        # Calculate health delta
        health_delta = None
        if bar.health_score is not None and entry_health is not None:
            health_delta = bar.health_score - entry_health

        health_summary = self.calculate_health_summary(health_delta)

        # Calculate bars from entry
        bars_from_entry = self.calculate_bars_from_entry(entry_time, event_time)

        return OptimalTradeEvent(
            trade_id=trade.trade_id,
            event_type=event_type,
            date=trade.date,
            ticker=trade.ticker,
            direction=trade.direction,
            model=trade.model,
            win=win,
            event_time=event_time,
            bars_from_entry=bars_from_entry,
            entry_price=trade.entry_price,
            price_at_event=price_at_event,
            points_at_event=points_at_event,
            actual_points=actual_points,
            health_score=bar.health_score,
            health_label=bar.health_label,
            health_delta=health_delta,
            health_summary=health_summary,
            structure_score=bar.structure_score,
            volume_score=bar.volume_score,
            price_score=bar.price_score,
            vwap=bar.vwap,
            sma9=bar.sma9,
            sma21=bar.sma21,
            sma_spread=bar.sma_spread,
            sma_momentum_ratio=bar.sma_momentum_ratio,
            sma_momentum_label=bar.sma_momentum_label,
            vol_roc=bar.vol_roc,
            vol_delta=bar.vol_delta,
            cvd_slope=bar.cvd_slope,
            m5_structure=bar.m5_structure,
            m15_structure=bar.m15_structure,
            h1_structure=bar.h1_structure,
            h4_structure=bar.h4_structure,
            sma_alignment_healthy=bar.sma_alignment_healthy,
            sma_momentum_healthy=bar.sma_momentum_healthy,
            vwap_healthy=bar.vwap_healthy,
            vol_roc_healthy=bar.vol_roc_healthy,
            vol_delta_healthy=bar.vol_delta_healthy,
            cvd_slope_healthy=bar.cvd_slope_healthy,
            m5_structure_healthy=bar.m5_structure_healthy,
            m15_structure_healthy=bar.m15_structure_healthy,
            h1_structure_healthy=bar.h1_structure_healthy,
            h4_structure_healthy=bar.h4_structure_healthy,
        )

    # =========================================================================
    # BATCH PROCESSING
    # =========================================================================
    def run_calculation(
        self,
        limit: Optional[int] = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Main entry point. Process all trades.

        Args:
            limit: Max trades to process (for testing)
            dry_run: If True, calculate but don't write to DB

        Returns:
            Dictionary with execution statistics
        """
        start_time = datetime.now()

        print("=" * 70)
        print("OPTIMAL TRADE CALCULATOR (Points-Based) v2.0.0")
        print("=" * 70)
        print(f"EOD Cutoff: {EOD_CUTOFF}")
        print(f"Dry Run: {dry_run}")
        if limit:
            print(f"Limit: {limit} trades")
        print()

        # Reset statistics
        self.stats = {
            'trades_processed': 0,
            'trades_skipped': 0,
            'events_created': 0,
            'errors': []
        }

        conn = None
        try:
            # Connect to database
            print("[1/5] Connecting to Supabase...")
            conn = psycopg2.connect(**DB_CONFIG)
            print("  Connected successfully")

            # Truncate existing data
            print("\n[2/5] Truncating optimal_trade table...")
            if not dry_run:
                self.truncate_optimal_trade(conn)
            else:
                print("  [DRY-RUN] Would truncate optimal_trade table")

            # Get trades with MFE/MAE data
            print("\n[3/5] Querying trades with mfe_mae_potential data...")
            trades = self.get_trades_with_mfe_mae(conn, limit)
            print(f"  Found {len(trades)} trades to process")

            if not trades:
                print("\n  No trades to process. Exiting.")
                return self._build_result(start_time)

            # Process trades
            print("\n[4/5] Processing trades...")
            all_events = []

            for i, trade in enumerate(trades):
                if (i + 1) % 50 == 0:
                    self._log(f"Processing trade {i + 1}/{len(trades)}...")

                # Get bars for this trade
                bars = self.get_trade_bars(conn, trade.trade_id)

                if not bars:
                    self._log(f"No bars for trade {trade.trade_id}", 'warning')
                    self.stats['trades_skipped'] += 1
                    continue

                # Calculate events
                events = self.calculate_trade_events(trade, bars)

                if events:
                    all_events.extend(events)
                    self.stats['trades_processed'] += 1
                    self.stats['events_created'] += len(events)
                else:
                    self.stats['trades_skipped'] += 1

            # Insert events
            print(f"\n[5/5] Inserting {len(all_events)} events...")
            if dry_run:
                print(f"  [DRY-RUN] Would insert {len(all_events)} events")
            else:
                # Insert in batches
                for i in range(0, len(all_events), BATCH_INSERT_SIZE):
                    batch = all_events[i:i + BATCH_INSERT_SIZE]
                    self.insert_events(conn, batch)
                conn.commit()
                print(f"  Inserted {len(all_events)} events")

            return self._build_result(start_time)

        except Exception as e:
            self.stats['errors'].append(str(e))
            if conn:
                conn.rollback()
            raise

        finally:
            if conn:
                conn.close()

    def _build_result(self, start_time: datetime) -> Dict[str, Any]:
        """Build the result dictionary."""
        elapsed = (datetime.now() - start_time).total_seconds()

        result = {
            'trades_processed': self.stats['trades_processed'],
            'trades_skipped': self.stats['trades_skipped'],
            'events_created': self.stats['events_created'],
            'errors': self.stats['errors'],
            'execution_time_seconds': round(elapsed, 2)
        }

        # Print summary
        print("\n" + "=" * 70)
        print("CALCULATION COMPLETE")
        print("=" * 70)
        for key, value in result.items():
            print(f"  {key}: {value}")

        return result


# =============================================================================
# STANDALONE TEST
# =============================================================================
if __name__ == "__main__":
    print("Optimal Trade Calculator - Test Mode")
    print("=" * 70)

    calculator = OptimalTradeCalculator(verbose=True)
    results = calculator.run_calculation(limit=5, dry_run=True)
