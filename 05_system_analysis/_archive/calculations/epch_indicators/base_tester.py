"""
================================================================================
EPOCH TRADING SYSTEM - EPCH Indicators Edge Analysis
Base Infrastructure for Edge Testing
================================================================================

Provides:
- EdgeTestResult data structure
- Database fetching (trades + m1_indicator_bars + stop_analysis)
- Statistical tests (chi-square, Spearman)
- Edge detection logic

Version: 1.0.0
================================================================================
"""

import pandas as pd
import numpy as np
from scipy import stats
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from datetime import date

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import DB_CONFIG


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class EdgeTestResult:
    """Results from a single indicator edge test."""
    indicator: str              # e.g., "Candle Range"
    test_name: str              # e.g., "Range Threshold (0.15%)"
    segment: str                # e.g., "ALL", "LONG", "SHORT", "EPCH1"
    has_edge: bool              # Statistical + practical significance
    p_value: float              # From chi-square or spearman
    effect_size: float          # Win rate difference in percentage points
    groups: Dict[str, Dict]     # {group_name: {trades: n, wins: n, win_rate: pct}}
    baseline_win_rate: float    # Overall win rate for comparison
    confidence: str             # HIGH/MEDIUM/LOW based on min group sample size
    test_type: str              # "chi_square" or "spearman"
    recommendation: str         # Action to take

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'indicator': self.indicator,
            'test_name': self.test_name,
            'segment': self.segment,
            'has_edge': self.has_edge,
            'p_value': self.p_value,
            'effect_size': self.effect_size,
            'groups': self.groups,
            'baseline_win_rate': self.baseline_win_rate,
            'confidence': self.confidence,
            'test_type': self.test_type,
            'recommendation': self.recommendation
        }


# =============================================================================
# DATABASE FUNCTIONS
# =============================================================================

def fetch_epch_indicator_data(
    date_from: date = None,
    date_to: date = None,
    models: List[str] = None,
    directions: List[str] = None,
    stop_type: str = 'zone_buffer'
) -> pd.DataFrame:
    """
    Fetch trade data joined with indicators from prior M1 bar.

    Join Logic:
    - Entry at S15 means we use the PRIOR completed M1 bar
    - For entry at 09:35:15, use m1_indicator_bars at 09:34:00
    - This avoids look-ahead bias

    Args:
        date_from: Start date filter
        date_to: End date filter
        models: List of models to include (EPCH1, EPCH2, etc.)
        directions: List of directions (LONG, SHORT)
        stop_type: Stop type for win/loss determination

    Returns:
        DataFrame with trade + indicator data
    """
    import psycopg2
    from psycopg2.extras import RealDictCursor

    query = """
    WITH trade_with_prior_bar AS (
        SELECT
            t.trade_id,
            t.date,
            t.ticker,
            t.model,
            t.direction,
            t.entry_price,
            t.entry_time,
            -- Calculate prior M1 bar time: truncate to minute boundary, then subtract 1 minute
            -- Entry at 09:35:15 -> truncate to 09:35:00 -> subtract to 09:34:00
            (date_trunc('minute', ('2000-01-01'::date + t.entry_time)) - INTERVAL '1 minute')::time AS prior_bar_time
        FROM trades t
        WHERE t.entry_time IS NOT NULL
    )
    SELECT
        twpb.trade_id,
        twpb.date,
        twpb.ticker,
        twpb.model,
        twpb.direction,
        twpb.entry_price,
        twpb.entry_time,
        twpb.prior_bar_time,
        -- OHLC from prior M1 bar
        m1.open as bar_open,
        m1.high as bar_high,
        m1.low as bar_low,
        m1.close as bar_close,
        m1.volume as bar_volume,
        -- EPCH v1.0 Indicators
        m1.candle_range_pct,
        m1.vol_delta,
        m1.vol_roc,
        m1.sma9,
        m1.sma21,
        m1.sma_spread,
        m1.h1_structure,
        m1.long_score,
        m1.short_score,
        -- Additional context
        m1.vwap,
        m1.health_score,
        -- Outcome from stop_analysis
        CASE WHEN sa.outcome = 'WIN' THEN TRUE ELSE FALSE END as is_winner,
        sa.outcome as outcome_detail,
        sa.r_achieved
    FROM trade_with_prior_bar twpb
    JOIN m1_indicator_bars m1
        ON m1.ticker = twpb.ticker
        AND m1.bar_date = twpb.date
        AND m1.bar_time = twpb.prior_bar_time
    JOIN stop_analysis sa
        ON sa.trade_id = twpb.trade_id
    WHERE sa.stop_type = %s
      AND sa.stop_price IS NOT NULL
      AND m1.open IS NOT NULL
      AND m1.high IS NOT NULL
      AND m1.low IS NOT NULL
      AND m1.open > 0
    """

    params = [stop_type]

    # Add optional filters
    if date_from:
        query += " AND twpb.date >= %s"
        params.append(date_from)

    if date_to:
        query += " AND twpb.date <= %s"
        params.append(date_to)

    if models:
        query += " AND twpb.model = ANY(%s)"
        params.append(models)

    if directions:
        query += " AND twpb.direction = ANY(%s)"
        params.append(directions)

    query += " ORDER BY twpb.date, twpb.entry_time"

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
        conn.close()

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame([dict(row) for row in rows])

        # Convert Decimal types to float
        numeric_cols = [
            'entry_price', 'bar_open', 'bar_high', 'bar_low', 'bar_close',
            'candle_range_pct', 'vol_delta', 'vol_roc', 'sma9', 'sma21',
            'sma_spread', 'vwap', 'r_achieved'
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Convert integer columns
        int_cols = ['bar_volume', 'long_score', 'short_score', 'health_score']
        for col in int_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

        return df

    except Exception as e:
        print(f"Error fetching EPCH indicator data: {e}")
        return pd.DataFrame()


# =============================================================================
# STATISTICAL TEST FUNCTIONS
# =============================================================================

def get_confidence_level(min_group_size: int) -> str:
    """
    Determine confidence level based on minimum group sample size.

    HIGH: n >= 100 per group (reliable)
    MEDIUM: n >= 30 per group (usable with caution)
    LOW: n < 30 per group (insufficient for conclusions)
    """
    if min_group_size >= 100:
        return "HIGH"
    elif min_group_size >= 30:
        return "MEDIUM"
    else:
        return "LOW"


def calculate_win_rates(
    df: pd.DataFrame,
    group_col: str,
    outcome_col: str = 'is_winner'
) -> Dict[str, Dict]:
    """
    Calculate win rate statistics by group.

    Returns: {
        'GROUP_A': {'trades': 100, 'wins': 45, 'win_rate': 45.0},
        'GROUP_B': {'trades': 120, 'wins': 60, 'win_rate': 50.0}
    }
    """
    if group_col not in df.columns:
        return {}

    # Filter out null groups
    df_valid = df[df[group_col].notna()].copy()

    if len(df_valid) == 0:
        return {}

    grouped = df_valid.groupby(group_col, observed=True)[outcome_col].agg(['sum', 'count'])

    result = {}
    for group_name, row in grouped.iterrows():
        wins = int(row['sum'])
        trades = int(row['count'])
        win_rate = (wins / trades * 100) if trades > 0 else 0.0
        result[str(group_name)] = {
            'trades': trades,
            'wins': wins,
            'win_rate': round(win_rate, 2)
        }

    return result


def chi_square_test(
    df: pd.DataFrame,
    group_col: str,
    outcome_col: str = 'is_winner'
) -> Tuple[float, float, float]:
    """
    Run chi-square test for independence between group and outcome.

    Returns: (chi2_statistic, p_value, effect_size)
    Effect size = max win rate - min win rate (in percentage points)
    """
    # Filter valid data
    df_valid = df[df[group_col].notna()].copy()

    if len(df_valid) == 0:
        return 0.0, 1.0, 0.0

    # Create contingency table
    try:
        contingency = pd.crosstab(df_valid[group_col], df_valid[outcome_col])
    except Exception:
        return 0.0, 1.0, 0.0

    # Need at least 2 groups and both outcomes
    if contingency.shape[0] < 2 or contingency.shape[1] < 2:
        return 0.0, 1.0, 0.0

    # Chi-square test
    try:
        chi2, p_value, dof, expected = stats.chi2_contingency(contingency)
    except Exception:
        return 0.0, 1.0, 0.0

    # Calculate effect size (win rate difference)
    win_rates = calculate_win_rates(df_valid, group_col, outcome_col)
    rates = [g['win_rate'] for g in win_rates.values()]
    effect_size = max(rates) - min(rates) if rates else 0.0

    return chi2, p_value, effect_size


def spearman_monotonic_test(
    df: pd.DataFrame,
    bucket_col: str,
    outcome_col: str = 'is_winner',
    bucket_order: List[str] = None
) -> Tuple[float, float, float]:
    """
    Test for monotonic relationship between ordered buckets and win rate.

    Returns: (correlation, p_value, effect_size)
    Effect size = first bucket win rate - last bucket win rate
    """
    win_rates = calculate_win_rates(df, bucket_col, outcome_col)

    if bucket_order is None:
        bucket_order = sorted(win_rates.keys())

    # Filter to only buckets that exist
    bucket_order = [b for b in bucket_order if b in win_rates]

    if len(bucket_order) < 3:
        return 0.0, 1.0, 0.0

    # Create arrays for correlation
    positions = list(range(len(bucket_order)))
    rates = [win_rates[b]['win_rate'] for b in bucket_order]

    # Spearman correlation
    try:
        correlation, p_value = stats.spearmanr(positions, rates)
    except Exception:
        return 0.0, 1.0, 0.0

    # Effect size: difference between first and last
    effect_size = abs(rates[-1] - rates[0])

    return correlation, p_value, effect_size


def determine_edge(
    p_value: float,
    effect_size: float,
    confidence: str,
    p_threshold: float = 0.05,
    effect_threshold: float = 3.0
) -> Tuple[bool, str]:
    """
    Determine if edge exists and generate recommendation.

    Edge requires:
    - p_value < 0.05 (statistically significant)
    - effect_size > 3.0pp (practically significant)
    - confidence not LOW (sufficient sample size)

    Returns: (has_edge, recommendation)
    """
    if confidence == "LOW":
        return False, "INSUFFICIENT DATA - Need more trades for reliable conclusion"

    if p_value >= p_threshold:
        return False, f"NO EDGE - Not statistically significant (p={p_value:.4f})"

    if effect_size < effect_threshold:
        return False, f"NO EDGE - Effect too small ({effect_size:.1f}pp < {effect_threshold}pp threshold)"

    return True, f"EDGE DETECTED - Implement filter (p={p_value:.4f}, effect={effect_size:.1f}pp)"


# =============================================================================
# SEGMENT DEFINITIONS
# =============================================================================

def get_segments(df: pd.DataFrame) -> List[Tuple[str, pd.DataFrame, str]]:
    """
    Get all segments for testing.

    Returns list of (segment_name, segment_df, category)
    """
    segments = []

    # Overall
    segments.append(("ALL", df, "Overall"))

    # By Direction
    long_df = df[df['direction'] == 'LONG']
    short_df = df[df['direction'] == 'SHORT']
    if len(long_df) >= 30:
        segments.append(("LONG", long_df, "Direction"))
    if len(short_df) >= 30:
        segments.append(("SHORT", short_df, "Direction"))

    # By Trade Type
    cont_df = df[df['model'].isin(['EPCH1', 'EPCH3'])]
    rej_df = df[df['model'].isin(['EPCH2', 'EPCH4'])]
    if len(cont_df) >= 30:
        segments.append(("CONTINUATION (Combined)", cont_df, "Trade Type"))
    if len(rej_df) >= 30:
        segments.append(("REJECTION (Combined)", rej_df, "Trade Type"))

    # By Model - Continuation
    epch1_df = df[df['model'] == 'EPCH1']
    epch3_df = df[df['model'] == 'EPCH3']
    if len(epch1_df) >= 30:
        segments.append(("EPCH1 (Primary Cont.)", epch1_df, "Model - Continuation"))
    if len(epch3_df) >= 30:
        segments.append(("EPCH3 (Secondary Cont.)", epch3_df, "Model - Continuation"))

    # By Model - Rejection
    epch2_df = df[df['model'] == 'EPCH2']
    epch4_df = df[df['model'] == 'EPCH4']
    if len(epch2_df) >= 30:
        segments.append(("EPCH2 (Primary Rej.)", epch2_df, "Model - Rejection"))
    if len(epch4_df) >= 30:
        segments.append(("EPCH4 (Secondary Rej.)", epch4_df, "Model - Rejection"))

    return segments


# =============================================================================
# BUCKET CREATION UTILITIES
# =============================================================================

def create_quintile_buckets(
    df: pd.DataFrame,
    value_col: str,
    bucket_col: str,
    labels: List[str] = None
) -> pd.DataFrame:
    """
    Create quintile buckets for a numeric column.

    Falls back to fewer buckets if not enough unique values.
    """
    df = df.copy()

    if value_col not in df.columns:
        df[bucket_col] = None
        return df

    # Get valid values
    valid_mask = df[value_col].notna()
    values = df.loc[valid_mask, value_col]

    if len(values) < 10:
        df[bucket_col] = None
        return df

    # Try 5 buckets (quintiles)
    try:
        df.loc[valid_mask, bucket_col] = pd.qcut(
            values,
            q=5,
            labels=labels or ['Q1_Lowest', 'Q2', 'Q3', 'Q4', 'Q5_Highest'],
            duplicates='drop'
        )
        return df
    except ValueError:
        pass

    # Fallback to 3 buckets (terciles)
    try:
        df.loc[valid_mask, bucket_col] = pd.qcut(
            values,
            q=3,
            labels=['LOW', 'MEDIUM', 'HIGH'],
            duplicates='drop'
        )
        return df
    except ValueError:
        pass

    # Fallback to 2 buckets (median split)
    try:
        median = values.median()
        df.loc[valid_mask, bucket_col] = df.loc[valid_mask, value_col].apply(
            lambda x: 'ABOVE_MEDIAN' if x >= median else 'BELOW_MEDIAN'
        )
        return df
    except Exception:
        df[bucket_col] = None
        return df


def create_threshold_bucket(
    df: pd.DataFrame,
    value_col: str,
    bucket_col: str,
    threshold: float,
    above_label: str = 'ABOVE',
    below_label: str = 'BELOW'
) -> pd.DataFrame:
    """Create binary bucket based on threshold."""
    df = df.copy()

    if value_col not in df.columns:
        df[bucket_col] = None
        return df

    df[bucket_col] = df[value_col].apply(
        lambda x: above_label if pd.notna(x) and x >= threshold else (
            below_label if pd.notna(x) else None
        )
    )

    return df


# =============================================================================
# MASTER TEST RUNNER
# =============================================================================

def run_all_tests(df: pd.DataFrame) -> List[EdgeTestResult]:
    """
    Run all indicator edge tests across all segments.

    Returns list of EdgeTestResult for all tests.
    """
    from .candle_range_tests import run_candle_range_tests
    from .volume_delta_tests import run_volume_delta_tests
    from .volume_roc_tests import run_volume_roc_tests
    from .sma_tests import run_sma_tests
    from .structure_tests import run_structure_tests
    from .composite_score_tests import run_composite_score_tests

    all_results = []

    # Run each indicator's tests
    all_results.extend(run_candle_range_tests(df))
    all_results.extend(run_volume_delta_tests(df))
    all_results.extend(run_volume_roc_tests(df))
    all_results.extend(run_sma_tests(df))
    all_results.extend(run_structure_tests(df))
    all_results.extend(run_composite_score_tests(df))

    return all_results
