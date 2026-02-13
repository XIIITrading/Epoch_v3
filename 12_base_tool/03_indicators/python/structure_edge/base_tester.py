"""
Base infrastructure for Market Structure indicator edge testing.
Provides database access, statistical tests, and result structures.
"""

import pandas as pd
import numpy as np
from scipy import stats
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any

from .credentials import (
    SUPABASE_HOST, SUPABASE_PORT, SUPABASE_DATABASE,
    SUPABASE_USER, SUPABASE_PASSWORD
)
import psycopg2


# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

DB_CONFIG = {
    "host": SUPABASE_HOST,
    "port": SUPABASE_PORT,
    "database": SUPABASE_DATABASE,
    "user": SUPABASE_USER,
    "password": SUPABASE_PASSWORD,
    "sslmode": "require"
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class EdgeTestResult:
    """Results from a single indicator edge test."""
    indicator: str              # e.g., "Structure"
    test_name: str              # e.g., "H4 Structure"
    segment: str                # e.g., "ALL", "CONTINUATION", "REJECTION", "LONG", "SHORT"
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

def get_db_connection():
    """Get PostgreSQL connection using existing config."""
    return psycopg2.connect(
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        database=DB_CONFIG['database'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        sslmode=DB_CONFIG.get('sslmode', 'require')
    )


def fetch_structure_data(
    models: List[str] = None,
    directions: List[str] = None,
    date_from: str = None,
    date_to: str = None,
    stop_type: str = 'zone_buffer'
) -> pd.DataFrame:
    """
    Fetch trade data joined with structure indicators from entry_indicators table.

    The entry_indicators table contains multi-timeframe structure data:
    - H4 Structure (highest timeframe)
    - H1 Structure
    - M15 Structure
    - M5 Structure (entry timeframe)

    Each structure field has a corresponding _healthy boolean indicating
    if the structure aligns with trade direction.

    Returns DataFrame with columns:
        trade_id, date, ticker, model, direction, entry_price, entry_time,
        h4_structure, h4_structure_healthy, h1_structure, h1_structure_healthy,
        m15_structure, m15_structure_healthy, m5_structure, m5_structure_healthy,
        structure_score, is_winner
    """
    query = """
    SELECT
        t.trade_id,
        t.date,
        t.ticker,
        t.model,
        t.direction,
        t.entry_price,
        t.entry_time,
        -- Structure fields from entry_indicators
        ei.h4_structure,
        ei.h4_structure_healthy,
        ei.h1_structure,
        ei.h1_structure_healthy,
        ei.m15_structure,
        ei.m15_structure_healthy,
        ei.m5_structure,
        ei.m5_structure_healthy,
        ei.structure_score,
        -- Outcome from stop_analysis
        CASE WHEN sa.outcome = 'WIN' THEN TRUE ELSE FALSE END as is_winner,
        sa.outcome as outcome_detail,
        sa.r_achieved
    FROM trades t
    JOIN entry_indicators ei ON ei.trade_id = t.trade_id
    JOIN stop_analysis sa ON sa.trade_id = t.trade_id
    WHERE sa.stop_type = %s
      AND sa.stop_price IS NOT NULL
      AND t.entry_time IS NOT NULL
      AND (ei.h4_structure IS NOT NULL OR ei.h1_structure IS NOT NULL
           OR ei.m15_structure IS NOT NULL OR ei.m5_structure IS NOT NULL)
    """

    params = [stop_type]

    # Add optional filters
    if models:
        query += " AND t.model = ANY(%s)"
        params.append(models)

    if directions:
        query += " AND t.direction = ANY(%s)"
        params.append(directions)

    if date_from:
        query += " AND t.date >= %s"
        params.append(date_from)

    if date_to:
        query += " AND t.date <= %s"
        params.append(date_to)

    query += " ORDER BY t.date, t.entry_time"

    conn = get_db_connection()
    try:
        df = pd.read_sql_query(query, conn, params=params)
        return df
    finally:
        conn.close()


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
    grouped = df.groupby(group_col, observed=True)[outcome_col].agg(['sum', 'count'])

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
    # Create contingency table
    contingency = pd.crosstab(df[group_col], df[outcome_col])

    # Need at least 2 groups and both outcomes
    if contingency.shape[0] < 2 or contingency.shape[1] < 2:
        return 0.0, 1.0, 0.0

    # Chi-square test
    chi2, p_value, dof, expected = stats.chi2_contingency(contingency)

    # Calculate effect size (win rate difference)
    win_rates = calculate_win_rates(df, group_col, outcome_col)
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
    correlation, p_value = stats.spearmanr(positions, rates)

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
