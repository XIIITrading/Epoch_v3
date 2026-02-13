"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
M5 Trade Bars - Calculator
XIII Trading LLC
================================================================================

Core calculator that computes trade-specific M5 bars from entry to 15:30.
Includes direction-specific health scoring and MFE/MAE event marking.

Version: 1.0.0
================================================================================
"""

from dataclasses import dataclass
from datetime import datetime, date, time, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging
import pandas as pd
import numpy as np

from config import (
    MARKET_OPEN,
    EOD_CUTOFF,
    CALCULATION_VERSION
)

from m5_fetcher import M5Fetcher
from indicators import M5IndicatorCalculator
from structure import StructureAnalyzer, StructureResult
from health import HealthCalculator, HealthResult


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class M5TradeBarResult:
    """Complete M5 trade bar result for database insertion."""
    # Primary Key
    trade_id: str
    bar_seq: int  # Sequential within trade (0, 1, 2...)

    # Bar Identification
    bar_time: time
    bars_from_entry: int  # 0 at entry bar
    event_type: str  # ENTRY, IN_TRADE, MFE, MAE, MFE_MAE

    # Trade Context (denormalized)
    date: date
    ticker: str
    direction: str
    model: Optional[str]

    # OHLCV
    open: float
    high: float
    low: float
    close: float
    volume: int

    # Price Indicators
    vwap: Optional[float]
    sma9: Optional[float]
    sma21: Optional[float]
    sma_spread: Optional[float]
    sma_alignment: Optional[str]
    sma_alignment_healthy: Optional[bool]
    sma_momentum_ratio: Optional[float]
    sma_momentum_label: Optional[str]
    sma_momentum_healthy: Optional[bool]
    vwap_position: Optional[str]
    vwap_healthy: Optional[bool]

    # Volume Indicators
    vol_roc: Optional[float]
    vol_roc_healthy: Optional[bool]
    vol_delta: Optional[float]
    vol_delta_healthy: Optional[bool]
    cvd_slope: Optional[float]
    cvd_slope_healthy: Optional[bool]

    # Structure
    h4_structure: Optional[str]
    h4_structure_healthy: Optional[bool]
    h1_structure: Optional[str]
    h1_structure_healthy: Optional[bool]
    m15_structure: Optional[str]
    m15_structure_healthy: Optional[bool]
    m5_structure: Optional[str]
    m5_structure_healthy: Optional[bool]

    # Composite Health Score
    health_score: Optional[int]
    health_label: Optional[str]
    structure_score: Optional[int]
    volume_score: Optional[int]
    price_score: Optional[int]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_event_type(
    bar_time: time,
    bar_seq: int,
    mfe_time: Optional[time],
    mae_time: Optional[time]
) -> str:
    """
    Determine event type for a bar.

    Args:
        bar_time: Time of this bar
        bar_seq: Sequential bar number (0 = entry)
        mfe_time: Time of MFE event (if known)
        mae_time: Time of MAE event (if known)

    Returns:
        Event type: 'ENTRY', 'MFE', 'MAE', 'MFE_MAE', or 'IN_TRADE'
    """
    is_entry = (bar_seq == 0)
    is_mfe = (bar_time == mfe_time) if mfe_time else False
    is_mae = (bar_time == mae_time) if mae_time else False

    if is_entry:
        return 'ENTRY'
    elif is_mfe and is_mae:
        return 'MFE_MAE'
    elif is_mfe:
        return 'MFE'
    elif is_mae:
        return 'MAE'
    else:
        return 'IN_TRADE'


def round_to_m5(t: time) -> time:
    """Round time down to nearest 5-minute boundary."""
    minute = (t.minute // 5) * 5
    return time(t.hour, minute, 0)


def time_to_minutes(t: time) -> int:
    """Convert time to minutes since midnight."""
    return t.hour * 60 + t.minute


# =============================================================================
# MAIN CALCULATOR CLASS
# =============================================================================

class M5TradeBarsCalculator:
    """
    Calculates trade-specific M5 bars from entry to 15:30 ET.

    Includes:
    - Full indicator snapshots
    - Direction-specific health scoring
    - MFE/MAE event marking
    """

    def __init__(
        self,
        m5_fetcher: M5Fetcher = None,
        indicator_calculator: M5IndicatorCalculator = None,
        structure_analyzer: StructureAnalyzer = None,
        health_calculator: HealthCalculator = None,
        verbose: bool = True
    ):
        """
        Initialize the calculator.

        Args:
            m5_fetcher: M5Fetcher instance
            indicator_calculator: M5IndicatorCalculator instance
            structure_analyzer: StructureAnalyzer instance
            health_calculator: HealthCalculator instance
            verbose: Enable verbose logging
        """
        self.m5_fetcher = m5_fetcher or M5Fetcher()
        self.indicator_calculator = indicator_calculator or M5IndicatorCalculator()
        self.structure_analyzer = structure_analyzer or StructureAnalyzer()
        self.health_calculator = health_calculator or HealthCalculator()
        self.verbose = verbose
        self.logger = logging.getLogger(__name__)

    def _log(self, message: str, level: str = 'info'):
        """Log message if verbose mode enabled."""
        if self.verbose:
            prefix = {'error': '!', 'warning': '?', 'info': ' ', 'debug': '  '}
            print(f"  {prefix.get(level, ' ')} {message}")

    def calculate_for_trade(
        self,
        trade: Dict[str, Any],
        mfe_time: Optional[time] = None,
        mae_time: Optional[time] = None,
        df_with_indicators: Optional[pd.DataFrame] = None
    ) -> List[M5TradeBarResult]:
        """
        Calculate all M5 trade bars for a single trade.

        Args:
            trade: Trade dictionary with keys:
                - trade_id, date, ticker, direction, model, entry_time
            mfe_time: Time of MFE event (from mfe_mae_potential)
            mae_time: Time of MAE event (from mfe_mae_potential)
            df_with_indicators: Pre-calculated M5 bars with indicators (optional)

        Returns:
            List of M5TradeBarResult objects (one per bar from entry to 15:30)
        """
        trade_id = trade.get('trade_id')
        trade_date = trade.get('date')
        ticker = trade.get('ticker')
        direction = trade.get('direction')
        model = trade.get('model')
        entry_time = trade.get('entry_time')

        # Handle entry_time as timedelta (from psycopg2)
        if isinstance(entry_time, timedelta):
            total_seconds = int(entry_time.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            entry_time = time(hours, minutes, 0)

        if not all([trade_id, trade_date, ticker, direction, entry_time]):
            self._log(f"Missing required fields for {trade_id}", 'warning')
            return []

        # Round entry time to M5 boundary
        entry_time_m5 = round_to_m5(entry_time)

        # Convert MFE/MAE times to M5 boundaries if provided
        if mfe_time:
            if isinstance(mfe_time, timedelta):
                total_seconds = int(mfe_time.total_seconds())
                mfe_time = time(total_seconds // 3600, (total_seconds % 3600) // 60, 0)
            mfe_time = round_to_m5(mfe_time)

        if mae_time:
            if isinstance(mae_time, timedelta):
                total_seconds = int(mae_time.total_seconds())
                mae_time = time(total_seconds // 3600, (total_seconds % 3600) // 60, 0)
            mae_time = round_to_m5(mae_time)

        self._log(f"Calculating trade bars for {trade_id}: {ticker} {direction} on {trade_date}")

        # Get M5 bars with indicators if not provided
        if df_with_indicators is None:
            df = self.m5_fetcher.fetch_extended_trading_day(ticker, trade_date)
            if df.empty:
                self._log(f"No M5 bars found for {ticker} on {trade_date}", 'warning')
                return []
            df_with_indicators = self.indicator_calculator.add_all_indicators(df)

        # Filter to trading day bars from entry to EOD_CUTOFF (15:30)
        trade_bars = df_with_indicators[
            (df_with_indicators['bar_date'] == trade_date) &
            (df_with_indicators['bar_time'] >= entry_time_m5) &
            (df_with_indicators['bar_time'] <= EOD_CUTOFF)
        ].copy()

        if trade_bars.empty:
            self._log(f"No trade bars for {trade_id} from {entry_time_m5} to {EOD_CUTOFF}", 'warning')
            return []

        self._log(f"Processing {len(trade_bars)} bars from {entry_time_m5} to {EOD_CUTOFF}")

        # Calculate results for each bar
        results = []
        entry_minutes = time_to_minutes(entry_time_m5)

        for bar_seq, (idx, row) in enumerate(trade_bars.iterrows()):
            bar_time = row['bar_time']
            bar_minutes = time_to_minutes(bar_time)
            bars_from_entry = (bar_minutes - entry_minutes) // 5

            # Determine event type
            event_type = get_event_type(bar_time, bar_seq, mfe_time, mae_time)

            # Get structure at this bar time
            structures = self.structure_analyzer.get_all_structures(
                ticker=ticker,
                trade_date=trade_date,
                bar_time=bar_time
            )

            # Calculate health
            vwap = self._safe_float(row.get('vwap_calc'))
            close = self._safe_float(row.get('close'))
            sma9 = self._safe_float(row.get('sma9'))
            sma21 = self._safe_float(row.get('sma21'))
            sma_momentum_label = row.get('sma_momentum_label')
            vol_roc = self._safe_float(row.get('vol_roc'))
            vol_delta = self._safe_float(row.get('vol_delta'))
            cvd_slope = self._safe_float(row.get('cvd_slope'))

            health = self.health_calculator.calculate(
                direction=direction,
                h4_structure=structures['H4'].direction_label if structures.get('H4') else None,
                h1_structure=structures['H1'].direction_label if structures.get('H1') else None,
                m15_structure=structures['M15'].direction_label if structures.get('M15') else None,
                m5_structure=structures['M5'].direction_label if structures.get('M5') else None,
                vol_roc=vol_roc,
                vol_delta=vol_delta,
                cvd_slope=cvd_slope,
                sma9=sma9,
                sma21=sma21,
                sma_momentum_label=sma_momentum_label,
                close=close,
                vwap=vwap
            )

            # Build result
            result = M5TradeBarResult(
                trade_id=trade_id,
                bar_seq=bar_seq,
                bar_time=bar_time,
                bars_from_entry=bars_from_entry,
                event_type=event_type,
                date=trade_date,
                ticker=ticker,
                direction=direction,
                model=model,

                # OHLCV
                open=float(row['open']),
                high=float(row['high']),
                low=float(row['low']),
                close=float(row['close']),
                volume=int(row['volume']),

                # Price Indicators
                vwap=vwap,
                sma9=sma9,
                sma21=sma21,
                sma_spread=self._safe_float(row.get('sma_spread')),
                sma_alignment=health.sma_alignment,
                sma_alignment_healthy=health.sma_alignment_healthy,
                sma_momentum_ratio=self._safe_float(row.get('sma_momentum_ratio')),
                sma_momentum_label=sma_momentum_label,
                sma_momentum_healthy=health.sma_momentum_healthy,
                vwap_position=health.vwap_position,
                vwap_healthy=health.vwap_healthy,

                # Volume Indicators
                vol_roc=vol_roc,
                vol_roc_healthy=health.vol_roc_healthy,
                vol_delta=vol_delta,
                vol_delta_healthy=health.vol_delta_healthy,
                cvd_slope=cvd_slope,
                cvd_slope_healthy=health.cvd_slope_healthy,

                # Structure
                h4_structure=structures['H4'].direction_label if structures.get('H4') else None,
                h4_structure_healthy=health.h4_structure_healthy,
                h1_structure=structures['H1'].direction_label if structures.get('H1') else None,
                h1_structure_healthy=health.h1_structure_healthy,
                m15_structure=structures['M15'].direction_label if structures.get('M15') else None,
                m15_structure_healthy=health.m15_structure_healthy,
                m5_structure=structures['M5'].direction_label if structures.get('M5') else None,
                m5_structure_healthy=health.m5_structure_healthy,

                # Composite Health
                health_score=health.health_score,
                health_label=health.health_label,
                structure_score=health.structure_score,
                volume_score=health.volume_score,
                price_score=health.price_score
            )

            results.append(result)

        self._log(f"Calculated {len(results)} trade bars")

        return results

    def _safe_float(self, value) -> Optional[float]:
        """Convert value to float, returning None for NaN."""
        if value is None:
            return None
        if isinstance(value, float) and (np.isnan(value) or np.isinf(value)):
            return None
        try:
            return round(float(value), 6)
        except (ValueError, TypeError):
            return None

    def clear_caches(self):
        """Clear all internal caches."""
        self.m5_fetcher.clear_cache()
        self.structure_analyzer.clear_cache()


# =============================================================================
# STANDALONE TEST
# =============================================================================

if __name__ == "__main__":
    print("M5 Trade Bars - Calculator Test")
    print("=" * 60)

    calculator = M5TradeBarsCalculator(verbose=True)

    # Test trade
    test_trade = {
        'trade_id': 'TEST_001',
        'date': date(2025, 12, 30),
        'ticker': 'SPY',
        'direction': 'LONG',
        'model': 'MODEL_A',
        'entry_time': time(10, 7, 0)
    }

    print(f"\nCalculating trade bars for {test_trade['trade_id']}...")

    results = calculator.calculate_for_trade(
        trade=test_trade,
        mfe_time=time(11, 30),
        mae_time=time(13, 15)
    )

    if results:
        print(f"\n{'='*60}")
        print(f"Results: {len(results)} bars")
        print(f"{'='*60}")

        # Show first few bars
        print("\nFirst 3 bars:")
        for r in results[:3]:
            print(f"  {r.bar_time} [{r.event_type}]: score={r.health_score} ({r.health_label})")

        # Show MFE/MAE bars
        print("\nEvent bars (MFE/MAE):")
        for r in results:
            if r.event_type in ('MFE', 'MAE', 'MFE_MAE'):
                print(f"  {r.bar_time} [{r.event_type}]: score={r.health_score}")

        # Show last few bars
        print("\nLast 3 bars:")
        for r in results[-3:]:
            print(f"  {r.bar_time} [{r.event_type}]: score={r.health_score} ({r.health_label})")
    else:
        print("No results (may be holiday or weekend)")

    calculator.clear_caches()
    print("\nDone.")
