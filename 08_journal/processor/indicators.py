"""
Journal M1 Indicator Calculator - Self-contained indicator calculations.

Adapted from 03_backtest/processor/secondary_analysis/m1_indicator_bars/indicators.py.
Self-contained — no imports from backtest or 03_indicators library.

Calculates: VWAP, SMA9/21, Vol ROC, Vol Delta, CVD Slope, Health Score,
Candle Range %, Long Score, Short Score.
"""

import numpy as np
import pandas as pd
from typing import Optional
import sys
from pathlib import Path

# Add parent for config
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    SMA_FAST_PERIOD, SMA_SLOW_PERIOD,
    VOLUME_ROC_BASELINE_PERIOD, VOLUME_DELTA_ROLLING_PERIOD,
)

# Local constants (from backtest config)
SMA_MOMENTUM_LOOKBACK = 10
SMA_WIDENING_THRESHOLD = 1.1
CVD_WINDOW = 15
HEALTH_VOL_ROC_THRESHOLD = 50.0

# Composite score thresholds (from 03_indicators)
CANDLE_RANGE_THRESHOLD = 0.12
VOLUME_ROC_THRESHOLD = 30.0
VOLUME_DELTA_MAGNITUDE_THRESHOLD = 50000
SMA_SPREAD_THRESHOLD = 0.10


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
    Formula: position = (2 * (close - low) / bar_range) - 1; delta = position * volume
    """
    high = float(row.get('high', 0))
    low = float(row.get('low', 0))
    close = float(row.get('close', 0))
    volume = int(row.get('volume', 0))
    bar_range = high - low
    if bar_range == 0 or volume == 0:
        return 0.0
    position = (2 * (close - low) / bar_range) - 1
    return position * volume


# =============================================================================
# INDICATOR CALCULATION CLASS
# =============================================================================

class M1IndicatorCalculator:
    """
    Calculates direction-agnostic indicators for M1 bars.
    Self-contained — all calculations are inline.
    """

    def add_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add all indicator columns to the DataFrame."""
        if df.empty:
            return df
        df = df.copy()
        df = self._add_vwap(df)
        df = self._add_sma(df)
        df = self._add_sma_momentum(df)
        df = self._add_volume_roc(df)
        df = self._add_volume_delta(df)
        df = self._add_cvd_slope(df)
        df = self._add_health_score(df)
        df = self._add_candle_range(df)
        df = self._add_composite_scores(df)
        return df

    def _add_vwap(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add calculated VWAP column (cumulative daily VWAP)."""
        df['_tp'] = (df['high'] + df['low'] + df['close']) / 3
        df['_tpv'] = df['_tp'] * df['volume']
        df['_cum_tpv'] = df.groupby('bar_date')['_tpv'].cumsum()
        df['_cum_vol'] = df.groupby('bar_date')['volume'].cumsum()
        df['vwap_calc'] = df['_cum_tpv'] / df['_cum_vol'].replace(0, np.nan)
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
        df['_abs_spread'] = df['sma_spread'].abs()
        df['_prev_spread'] = df['_abs_spread'].shift(SMA_MOMENTUM_LOOKBACK)
        df['sma_momentum_ratio'] = df['_abs_spread'] / df['_prev_spread'].replace(0, np.nan)
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
        """Add Volume Delta column (rolling sum of bar deltas)."""
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
            window=CVD_WINDOW, min_periods=CVD_WINDOW
        ).apply(rolling_slope, raw=False)

        df['_avg_vol'] = df['volume'].rolling(window=CVD_WINDOW, min_periods=CVD_WINDOW).mean()
        df['cvd_slope'] = df['_cvd_slope_raw'] / df['_avg_vol'].replace(0, np.nan)
        df = df.drop(columns=['_bar_delta', '_cvd', '_cvd_slope_raw', '_avg_vol'])
        return df

    def _add_health_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add Health Score column (0-10 scale)."""
        def calculate_health(row):
            score = 0
            vol_roc = row.get('vol_roc')
            if pd.notna(vol_roc) and vol_roc > HEALTH_VOL_ROC_THRESHOLD:
                score += 2
            sma_momentum = row.get('sma_momentum_label')
            if sma_momentum == 'WIDENING':
                score += 2
            cvd_slope = row.get('cvd_slope')
            if pd.notna(cvd_slope) and abs(cvd_slope) > 0.001:
                score += 2
            sma_spread = row.get('sma_spread')
            close = row.get('close', 1)
            if pd.notna(sma_spread) and pd.notna(close) and close > 0:
                if abs(sma_spread) / close > 0.001:
                    score += 2
            vwap = row.get('vwap_calc')
            if pd.notna(vwap) and pd.notna(close) and close > 0:
                if abs(close - vwap) / close > 0.001:
                    score += 2
            return score

        df['health_score'] = df.apply(calculate_health, axis=1)
        return df

    def _add_candle_range(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add candle_range_pct: (high - low) / close * 100."""
        def calc(row):
            h = float(row['high'])
            l = float(row['low'])
            c = float(row['close'])
            if c == 0:
                return 0.0
            return (h - l) / c * 100
        df['candle_range_pct'] = df.apply(calc, axis=1)
        return df

    def _add_composite_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add long_score and short_score columns (0-5, without H1 structure)."""
        def calc_long(row):
            score = 0
            cr = row.get('candle_range_pct')
            if pd.notna(cr) and cr >= CANDLE_RANGE_THRESHOLD:
                score += 2
            vr = row.get('vol_roc')
            if pd.notna(vr) and vr >= VOLUME_ROC_THRESHOLD:
                score += 1
            vd = row.get('vol_delta')
            if pd.notna(vd) and abs(vd) > VOLUME_DELTA_MAGNITUDE_THRESHOLD:
                score += 1
            ss = row.get('sma_spread')
            c = row.get('close', 1)
            if pd.notna(ss) and pd.notna(c) and c > 0:
                if abs(ss) / c * 100 >= SMA_SPREAD_THRESHOLD:
                    score += 1
            return score

        def calc_short(row):
            score = 0
            cr = row.get('candle_range_pct')
            if pd.notna(cr) and cr >= CANDLE_RANGE_THRESHOLD:
                score += 2
            vr = row.get('vol_roc')
            if pd.notna(vr) and vr >= VOLUME_ROC_THRESHOLD:
                score += 1
            vd = row.get('vol_delta')
            if pd.notna(vd) and vd > 0:
                score += 1
            ss = row.get('sma_spread')
            if pd.notna(ss) and ss > 0:
                score += 1
            return score

        df['long_score'] = df.apply(calc_long, axis=1)
        df['short_score'] = df.apply(calc_short, axis=1)
        return df

    @staticmethod
    def _safe_float(value) -> Optional[float]:
        """Convert value to float, returning None for NaN."""
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return None
        try:
            return round(float(value), 6)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _safe_int(value) -> Optional[int]:
        """Convert value to int, returning None for NaN."""
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
