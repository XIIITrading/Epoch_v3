"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
M5 Trade Bars - Indicator Calculations
XIII Trading LLC
================================================================================

Indicator calculation functions for M5 trade bars.
Import from m5_indicator_bars module for consistency.

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
    vwap: Optional[float]
    sma9: Optional[float]
    sma21: Optional[float]
    sma_spread: Optional[float]
    sma_momentum_ratio: Optional[float]
    sma_momentum_label: Optional[str]
    vol_roc: Optional[float]
    vol_delta: Optional[float]
    cvd_slope: Optional[float]
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
    """Estimate volume delta for a single bar."""
    open_price = float(row.get('open', 0))
    high = float(row.get('high', 0))
    low = float(row.get('low', 0))
    close = float(row.get('close', 0))
    volume = float(row.get('volume', 0))

    bar_range = high - low
    if bar_range == 0:
        return 0.0

    position = (2 * (close - low) / bar_range) - 1
    return position * volume


# =============================================================================
# INDICATOR CALCULATION CLASS
# =============================================================================

class M5IndicatorCalculator:
    """
    Calculates indicators for M5 trade bars.
    """

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

        # Calculate VWAP
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
        """Add calculated VWAP column."""
        df['_tp'] = (df['high'] + df['low'] + df['close']) / 3
        df['_tpv'] = df['_tp'] * df['volume']
        df['_cum_tpv'] = df.groupby('bar_date')['_tpv'].cumsum()
        df['_cum_vol'] = df.groupby('bar_date')['volume'].cumsum()
        df['vwap_calc'] = df['_cum_tpv'] / df['_cum_vol'].replace(0, np.nan)
        df = df.drop(columns=['_tp', '_tpv', '_cum_tpv', '_cum_vol'])
        return df

    def _add_sma(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add SMA columns."""
        df['sma9'] = _simple_moving_average(df['close'], SMA_FAST_PERIOD)
        df['sma21'] = _simple_moving_average(df['close'], SMA_SLOW_PERIOD)
        df['sma_spread'] = df['sma9'] - df['sma21']
        return df

    def _add_sma_momentum(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add SMA momentum columns."""
        df['_abs_spread'] = df['sma_spread'].abs()
        df['_prev_spread'] = df['_abs_spread'].shift(SMA_MOMENTUM_LOOKBACK)
        df['sma_momentum_ratio'] = df['_abs_spread'] / df['_prev_spread'].replace(0, np.nan)

        # Cap ratio to prevent database overflow (max 9999.999999 for DECIMAL(10,6))
        df['sma_momentum_ratio'] = df['sma_momentum_ratio'].clip(upper=999.0)

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
        df = df.drop(columns=['_abs_spread', '_prev_spread'])
        return df

    def _add_volume_roc(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add Volume ROC column."""
        df['_vol_baseline'] = df['volume'].shift(1).rolling(
            window=VOLUME_ROC_BASELINE_PERIOD,
            min_periods=VOLUME_ROC_BASELINE_PERIOD
        ).mean()
        df['vol_roc'] = ((df['volume'] - df['_vol_baseline']) / df['_vol_baseline'].replace(0, np.nan)) * 100
        df = df.drop(columns=['_vol_baseline'])
        return df

    def _add_volume_delta(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add Volume Delta column."""
        df['_bar_delta'] = df.apply(_calculate_bar_delta, axis=1)
        df['vol_delta'] = df['_bar_delta'].rolling(
            window=VOLUME_DELTA_ROLLING_PERIOD,
            min_periods=VOLUME_DELTA_ROLLING_PERIOD
        ).sum()
        df = df.drop(columns=['_bar_delta'])
        return df

    def _add_cvd_slope(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add CVD Slope column."""
        df['_bar_delta'] = df.apply(_calculate_bar_delta, axis=1)
        df['_cvd'] = df['_bar_delta'].cumsum()

        def rolling_slope(series):
            if len(series) < CVD_WINDOW:
                return np.nan
            return _linear_regression_slope(series.values)

        df['_cvd_slope_raw'] = df['_cvd'].rolling(
            window=CVD_WINDOW,
            min_periods=CVD_WINDOW
        ).apply(rolling_slope, raw=False)

        df['_avg_vol'] = df['volume'].rolling(window=CVD_WINDOW, min_periods=CVD_WINDOW).mean()
        df['cvd_slope'] = df['_cvd_slope_raw'] / df['_avg_vol'].replace(0, np.nan)
        df = df.drop(columns=['_bar_delta', '_cvd', '_cvd_slope_raw', '_avg_vol'])
        return df
