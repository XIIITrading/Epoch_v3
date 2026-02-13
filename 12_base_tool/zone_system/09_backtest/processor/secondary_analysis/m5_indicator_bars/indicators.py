"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
M5 Indicator Bars - Indicator Calculations
XIII Trading LLC
================================================================================

Direction-agnostic indicator calculation functions for M5 bars.
Calculates SMA, VWAP, Volume ROC, Volume Delta, and CVD Slope.

All functions work with pandas DataFrames containing M5 bar data.
Results are direction-agnostic (no health scoring here).

Version: 1.0.0
================================================================================
"""

from typing import List, Dict, Optional, NamedTuple
import numpy as np
import pandas as pd

from config import (
    SMA_FAST_PERIOD,
    SMA_SLOW_PERIOD,
    SMA_MOMENTUM_LOOKBACK,
    SMA_WIDENING_THRESHOLD,
    VOLUME_ROC_BASELINE_PERIOD,
    VOLUME_DELTA_ROLLING_PERIOD,
    CVD_WINDOW
)


# =============================================================================
# RESULT DATA STRUCTURES
# =============================================================================

class IndicatorSnapshot(NamedTuple):
    """Complete indicator snapshot for a single M5 bar."""
    # Price Indicators
    vwap: Optional[float]
    sma9: Optional[float]
    sma21: Optional[float]
    sma_spread: Optional[float]
    sma_momentum_ratio: Optional[float]
    sma_momentum_label: Optional[str]

    # Volume Indicators
    vol_roc: Optional[float]
    vol_delta: Optional[float]
    cvd_slope: Optional[float]

    # Metadata
    bars_in_calculation: int


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _simple_moving_average(values: pd.Series, period: int) -> pd.Series:
    """Calculate simple moving average."""
    return values.rolling(window=period, min_periods=period).mean()


def _linear_regression_slope(values: np.ndarray) -> float:
    """Calculate slope of linear regression line through values."""
    n = len(values)
    if n < 2:
        return 0.0

    x = np.arange(n)
    y = np.array(values)

    x_mean = np.mean(x)
    y_mean = np.mean(y)

    numerator = np.sum((x - x_mean) * (y - y_mean))
    denominator = np.sum((x - x_mean) ** 2)

    if denominator == 0:
        return 0.0

    return numerator / denominator


def _calculate_bar_delta(row: pd.Series) -> float:
    """
    Estimate volume delta for a single bar.

    Uses (close - open) / (high - low) ratio to estimate buying vs selling.
    Positive = more buying, Negative = more selling.
    """
    open_price = float(row.get('open', 0))
    high = float(row.get('high', 0))
    low = float(row.get('low', 0))
    close = float(row.get('close', 0))
    volume = float(row.get('volume', 0))

    bar_range = high - low
    if bar_range == 0:
        return 0.0

    # Calculate position of close within bar range
    # 1 = closed at high, -1 = closed at low
    position = (2 * (close - low) / bar_range) - 1

    return position * volume


# =============================================================================
# INDICATOR CALCULATION CLASS
# =============================================================================

class M5IndicatorCalculator:
    """
    Calculates direction-agnostic indicators for M5 bars.

    All indicators are calculated on a rolling basis to support
    calculating values at any bar in the sequence.
    """

    def __init__(self):
        """Initialize the indicator calculator."""
        pass

    def add_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add all indicator columns to the DataFrame.

        Args:
            df: DataFrame with columns: open, high, low, close, volume, vwap

        Returns:
            DataFrame with added indicator columns
        """
        if df.empty:
            return df

        df = df.copy()

        # Calculate VWAP (cumulative for the trading day)
        df = self._add_vwap(df)

        # Calculate SMAs
        df = self._add_sma(df)

        # Calculate SMA momentum
        df = self._add_sma_momentum(df)

        # Calculate Volume ROC
        df = self._add_volume_roc(df)

        # Calculate Volume Delta
        df = self._add_volume_delta(df)

        # Calculate CVD Slope
        df = self._add_cvd_slope(df)

        return df

    def _add_vwap(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add calculated VWAP column (cumulative daily VWAP).

        Note: If 'vwap' column already exists from API, we still recalculate
        for consistency across the entire bar sequence.
        """
        # Calculate typical price
        df['_tp'] = (df['high'] + df['low'] + df['close']) / 3

        # Calculate TPV (typical price * volume)
        df['_tpv'] = df['_tp'] * df['volume']

        # Group by bar_date and calculate cumulative sums
        df['_cum_tpv'] = df.groupby('bar_date')['_tpv'].cumsum()
        df['_cum_vol'] = df.groupby('bar_date')['volume'].cumsum()

        # Calculate VWAP
        df['vwap_calc'] = df['_cum_tpv'] / df['_cum_vol'].replace(0, np.nan)

        # Clean up temp columns
        df = df.drop(columns=['_tp', '_tpv', '_cum_tpv', '_cum_vol'])

        return df

    def _add_sma(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add SMA9, SMA21, and SMA spread columns."""
        df['sma9'] = _simple_moving_average(df['close'], SMA_FAST_PERIOD)
        df['sma21'] = _simple_moving_average(df['close'], SMA_SLOW_PERIOD)
        df['sma_spread'] = df['sma9'] - df['sma21']

        return df

    def _add_sma_momentum(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add SMA momentum ratio and label columns."""
        # Get absolute spread
        df['_abs_spread'] = df['sma_spread'].abs()

        # Calculate spread from N bars ago
        df['_prev_spread'] = df['_abs_spread'].shift(SMA_MOMENTUM_LOOKBACK)

        # Calculate ratio
        df['sma_momentum_ratio'] = df['_abs_spread'] / df['_prev_spread'].replace(0, np.nan)

        # Cap ratio to prevent database overflow (max 9999.999999 for DECIMAL(10,6))
        df['sma_momentum_ratio'] = df['sma_momentum_ratio'].clip(upper=999.0)

        # Determine momentum label
        def get_momentum_label(ratio):
            if pd.isna(ratio):
                return None
            if ratio > SMA_WIDENING_THRESHOLD:
                return 'WIDENING'
            elif ratio < 1.0 / SMA_WIDENING_THRESHOLD:
                return 'NARROWING'
            else:
                return 'STABLE'

        df['sma_momentum_label'] = df['sma_momentum_ratio'].apply(get_momentum_label)

        # Clean up temp columns
        df = df.drop(columns=['_abs_spread', '_prev_spread'])

        return df

    def _add_volume_roc(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add Volume ROC column."""
        # Calculate baseline average (previous N bars, excluding current)
        df['_vol_baseline'] = df['volume'].shift(1).rolling(
            window=VOLUME_ROC_BASELINE_PERIOD,
            min_periods=VOLUME_ROC_BASELINE_PERIOD
        ).mean()

        # Calculate ROC percentage
        df['vol_roc'] = ((df['volume'] - df['_vol_baseline']) / df['_vol_baseline'].replace(0, np.nan)) * 100

        # Clean up
        df = df.drop(columns=['_vol_baseline'])

        return df

    def _add_volume_delta(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add Volume Delta column (rolling sum of bar deltas)."""
        # Calculate bar delta for each row
        df['_bar_delta'] = df.apply(_calculate_bar_delta, axis=1)

        # Calculate rolling sum
        df['vol_delta'] = df['_bar_delta'].rolling(
            window=VOLUME_DELTA_ROLLING_PERIOD,
            min_periods=VOLUME_DELTA_ROLLING_PERIOD
        ).sum()

        # Clean up
        df = df.drop(columns=['_bar_delta'])

        return df

    def _add_cvd_slope(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add CVD Slope column."""
        # Calculate bar delta for each row
        df['_bar_delta'] = df.apply(_calculate_bar_delta, axis=1)

        # Calculate cumulative volume delta
        df['_cvd'] = df['_bar_delta'].cumsum()

        # Calculate slope over window
        def rolling_slope(series):
            if len(series) < CVD_WINDOW:
                return np.nan
            return _linear_regression_slope(series.values)

        df['_cvd_slope_raw'] = df['_cvd'].rolling(
            window=CVD_WINDOW,
            min_periods=CVD_WINDOW
        ).apply(rolling_slope, raw=False)

        # Normalize by average volume for interpretability
        df['_avg_vol'] = df['volume'].rolling(window=CVD_WINDOW, min_periods=CVD_WINDOW).mean()
        df['cvd_slope'] = df['_cvd_slope_raw'] / df['_avg_vol'].replace(0, np.nan)

        # Clean up
        df = df.drop(columns=['_bar_delta', '_cvd', '_cvd_slope_raw', '_avg_vol'])

        return df

    def get_snapshot_at_index(self, df: pd.DataFrame, index: int) -> Optional[IndicatorSnapshot]:
        """
        Get indicator snapshot at a specific DataFrame index.

        Args:
            df: DataFrame with indicator columns already added
            index: Row index to get snapshot for

        Returns:
            IndicatorSnapshot or None if index is invalid
        """
        if index < 0 or index >= len(df):
            return None

        row = df.iloc[index]

        return IndicatorSnapshot(
            vwap=self._safe_float(row.get('vwap_calc')),
            sma9=self._safe_float(row.get('sma9')),
            sma21=self._safe_float(row.get('sma21')),
            sma_spread=self._safe_float(row.get('sma_spread')),
            sma_momentum_ratio=self._safe_float(row.get('sma_momentum_ratio')),
            sma_momentum_label=row.get('sma_momentum_label'),
            vol_roc=self._safe_float(row.get('vol_roc')),
            vol_delta=self._safe_float(row.get('vol_delta')),
            cvd_slope=self._safe_float(row.get('cvd_slope')),
            bars_in_calculation=index + 1
        )

    def _safe_float(self, value) -> Optional[float]:
        """Convert value to float, returning None for NaN."""
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return None
        try:
            return round(float(value), 6)
        except (ValueError, TypeError):
            return None


# =============================================================================
# STANDALONE TEST
# =============================================================================

if __name__ == "__main__":
    print("M5 Indicators - Direction-Agnostic Calculations")
    print("=" * 60)

    # Create sample data
    import random
    random.seed(42)

    sample_data = []
    price = 100.0
    for i in range(50):
        change = random.uniform(-1, 1)
        o = price
        h = price + abs(change) + random.uniform(0, 0.5)
        l = price - abs(change) - random.uniform(0, 0.5)
        c = price + change
        v = random.randint(10000, 50000)

        from datetime import date, time, datetime
        sample_data.append({
            'timestamp': datetime(2025, 1, 2, 9, 30 + i * 5 // 60, (30 + i * 5) % 60),
            'bar_date': date(2025, 1, 2),
            'bar_time': time(9, 30 + i * 5 // 60, (30 + i * 5) % 60),
            'open': o,
            'high': h,
            'low': l,
            'close': c,
            'volume': v,
            'vwap': (h + l + c) / 3
        })
        price = c

    df = pd.DataFrame(sample_data)
    print(f"Sample data: {len(df)} bars")

    # Calculate indicators
    calculator = M5IndicatorCalculator()
    df_with_indicators = calculator.add_all_indicators(df)

    print("\nSample output (last 5 rows):")
    cols = ['bar_time', 'close', 'sma9', 'sma21', 'sma_spread', 'sma_momentum_label', 'vol_roc', 'cvd_slope']
    print(df_with_indicators[cols].tail().to_string())

    # Get snapshot at last index
    snapshot = calculator.get_snapshot_at_index(df_with_indicators, len(df_with_indicators) - 1)
    print(f"\nSnapshot at last bar:")
    print(f"  SMA9: {snapshot.sma9}")
    print(f"  SMA21: {snapshot.sma21}")
    print(f"  Spread: {snapshot.sma_spread}")
    print(f"  Momentum: {snapshot.sma_momentum_label}")
    print(f"  Vol ROC: {snapshot.vol_roc}")
    print(f"  CVD Slope: {snapshot.cvd_slope}")
