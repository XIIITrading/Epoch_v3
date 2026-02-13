"""
CALC-011: Market Structure Edge Analysis

Tests multi-timeframe market structure indicators for statistical edge in trade outcomes.
Uses structure data from entry_indicators table which captures:
- H4 Structure (highest timeframe - trend context)
- H1 Structure (secondary trend confirmation)
- M15 Structure (intermediate structure)
- M5 Structure (entry timeframe)

Each structure can be: BULL, BEAR, or NEUTRAL
Each has a _healthy flag indicating alignment with trade direction.

Analyzes:
- Individual Timeframe Structure: Does each TF's structure predict win rate?
- Structure Alignment: Does healthy structure (aligned with direction) improve win rate?
- HTF Alignment: Do higher timeframes (H4+H1) aligned matter more?
- MTF Alignment: Do medium timeframes (M15+M5) aligned matter?
- Full Alignment: All 4 timeframes aligned with direction
- Structure Score: Does total structure score (0-4) correlate with win rate?
- Structure Confluence Score: Weighted directional pressure (+bull/-bear) like volume delta

Structure Confluence Score:
    Weights derived from edge analysis effect sizes:
    - H1: 1.5 (strongest predictor, 30-54pp effects)
    - M15: 1.0 (second strongest, 24-31pp effects)
    - M5: 0.5 (entry timeframe, 19-25pp effects)
    - H4: excluded (no data currently - always NEUTRAL)

    Calculation: BULL=+1, BEAR=-1, NEUTRAL=0
    Confluence = (H1 × 1.5) + (M15 × 1.0) + (M5 × 0.5)
    Range: -3.0 (max bearish) to +3.0 (max bullish)

Usage:
    python -m structure_edge.structure_edge
    python -m structure_edge.structure_edge --models EPCH01,EPCH03
    python -m structure_edge.structure_edge --direction LONG
    python -m structure_edge.structure_edge --output results/structure_2026.md
"""

import argparse
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from datetime import datetime

from .base_tester import (
    EdgeTestResult,
    fetch_structure_data,
    calculate_win_rates,
    chi_square_test,
    spearman_monotonic_test,
    get_confidence_level,
    determine_edge
)
from .edge_report import (
    print_console_summary,
    generate_markdown_report,
    save_report
)


# ============================================================================
# STRUCTURE CONFLUENCE CONFIGURATION
# ============================================================================

# Weights derived from edge analysis effect sizes
# Higher weight = stronger predictor of trade outcomes
CONFLUENCE_WEIGHTS = {
    'h1': 1.5,   # Strongest predictor (30-54pp effects)
    'm15': 1.0,  # Second strongest (24-31pp effects)
    'm5': 0.5,   # Entry timeframe (19-25pp effects)
    'h4': 0.0,   # Excluded - no data currently (always NEUTRAL)
}

# Structure direction to numeric mapping
STRUCTURE_TO_NUMERIC = {
    'BULL': 1,
    'BEAR': -1,
    'NEUTRAL': 0,
    'UNKNOWN': 0,
    None: 0
}

# Confluence score ranges for categorization
# Max bullish = +3.0, Max bearish = -3.0
CONFLUENCE_BUCKETS = [
    (-3.1, -2.0, 'STRONG_BEAR'),    # -3.0 to -2.0
    (-2.0, -1.0, 'MODERATE_BEAR'),  # -2.0 to -1.0
    (-1.0, -0.1, 'WEAK_BEAR'),      # -1.0 to -0.1
    (-0.1, 0.1, 'NEUTRAL'),         # -0.1 to 0.1
    (0.1, 1.0, 'WEAK_BULL'),        # 0.1 to 1.0
    (1.0, 2.0, 'MODERATE_BULL'),    # 1.0 to 2.0
    (2.0, 3.1, 'STRONG_BULL'),      # 2.0 to 3.0
]


# ============================================================================
# STRUCTURE METRIC CALCULATIONS
# ============================================================================

def calculate_structure_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add Structure-derived columns for edge testing.

    Adds:
        htf_aligned: Both H4 and H1 are healthy (aligned with direction)
        mtf_aligned: Both M15 and M5 are healthy
        all_aligned: All 4 timeframes healthy
        aligned_count: Number of aligned timeframes (0-4)
        htf_structure_combo: Combined H4+H1 structure category
        structure_score_bucket: Binned structure score for analysis
        confluence_score: Weighted directional score (-3.0 to +3.0)
        confluence_bucket: Category (STRONG_BEAR to STRONG_BULL)
        confluence_aligned: Does confluence direction match trade direction?
    """
    df = df.copy()

    # Fill NaN healthy flags with False
    for tf in ['h4', 'h1', 'm15', 'm5']:
        healthy_col = f'{tf}_structure_healthy'
        if healthy_col in df.columns:
            df[healthy_col] = df[healthy_col].fillna(False)

    # =========================================================================
    # CONFLUENCE SCORE CALCULATION
    # =========================================================================

    # Convert structure directions to numeric values
    for tf in ['h4', 'h1', 'm15', 'm5']:
        col = f'{tf}_structure'
        numeric_col = f'{tf}_numeric'
        if col in df.columns:
            df[numeric_col] = df[col].map(STRUCTURE_TO_NUMERIC).fillna(0)
        else:
            df[numeric_col] = 0

    # Calculate weighted confluence score
    # Confluence = (H1 × 1.5) + (M15 × 1.0) + (M5 × 0.5)
    df['confluence_score'] = (
        df['h1_numeric'] * CONFLUENCE_WEIGHTS['h1'] +
        df['m15_numeric'] * CONFLUENCE_WEIGHTS['m15'] +
        df['m5_numeric'] * CONFLUENCE_WEIGHTS['m5'] +
        df['h4_numeric'] * CONFLUENCE_WEIGHTS['h4']
    )

    # Categorize confluence score into buckets
    def categorize_confluence(score):
        for low, high, label in CONFLUENCE_BUCKETS:
            if low <= score < high:
                return label
        return 'NEUTRAL'

    df['confluence_bucket'] = df['confluence_score'].apply(categorize_confluence)

    # Simplified confluence direction
    df['confluence_direction'] = np.where(
        df['confluence_score'] > 0.5, 'BULLISH',
        np.where(df['confluence_score'] < -0.5, 'BEARISH', 'NEUTRAL')
    )

    # Check if confluence aligns with trade direction
    # LONG should have positive confluence, SHORT should have negative
    df['confluence_aligned'] = (
        ((df['direction'] == 'LONG') & (df['confluence_score'] > 0)) |
        ((df['direction'] == 'SHORT') & (df['confluence_score'] < 0))
    )
    df['confluence_aligned_str'] = df['confluence_aligned'].map(
        {True: 'CONFLUENCE_ALIGNED', False: 'CONFLUENCE_MISALIGNED'}
    )

    # Magnitude of confluence (absolute value)
    df['confluence_magnitude'] = df['confluence_score'].abs()

    # Magnitude buckets for analysis
    df['confluence_magnitude_bucket'] = pd.cut(
        df['confluence_magnitude'],
        bins=[-0.01, 0.5, 1.5, 2.5, 3.1],
        labels=['WEAK', 'MODERATE', 'STRONG', 'VERY_STRONG']
    )

    # Quintile buckets for spearman test
    try:
        df['confluence_quintile'] = pd.qcut(
            df['confluence_score'],
            q=5,
            labels=['Q1_MostBear', 'Q2_Bear', 'Q3_Neutral', 'Q4_Bull', 'Q5_MostBull'],
            duplicates='drop'
        )
    except ValueError:
        # Fallback if not enough unique values
        df['confluence_quintile'] = df['confluence_bucket']

    # HTF Alignment (H4 + H1 both healthy)
    df['htf_aligned'] = (
        df['h4_structure_healthy'].fillna(False) &
        df['h1_structure_healthy'].fillna(False)
    )
    df['htf_aligned_str'] = df['htf_aligned'].map({True: 'HTF_ALIGNED', False: 'HTF_NOT_ALIGNED'})

    # MTF Alignment (M15 + M5 both healthy)
    df['mtf_aligned'] = (
        df['m15_structure_healthy'].fillna(False) &
        df['m5_structure_healthy'].fillna(False)
    )
    df['mtf_aligned_str'] = df['mtf_aligned'].map({True: 'MTF_ALIGNED', False: 'MTF_NOT_ALIGNED'})

    # All Timeframes Aligned
    df['all_aligned'] = df['htf_aligned'] & df['mtf_aligned']
    df['all_aligned_str'] = df['all_aligned'].map({True: 'ALL_ALIGNED', False: 'NOT_ALL_ALIGNED'})

    # Count of aligned timeframes
    df['aligned_count'] = (
        df['h4_structure_healthy'].fillna(False).astype(int) +
        df['h1_structure_healthy'].fillna(False).astype(int) +
        df['m15_structure_healthy'].fillna(False).astype(int) +
        df['m5_structure_healthy'].fillna(False).astype(int)
    )

    # Aligned count as category for chi-square
    df['aligned_count_str'] = df['aligned_count'].astype(str) + '_ALIGNED'

    # Structure score buckets (if available)
    if 'structure_score' in df.columns and df['structure_score'].notna().any():
        df['structure_score_bucket'] = pd.cut(
            df['structure_score'],
            bins=[-1, 0, 1, 2, 3, 4],
            labels=['0_NONE', '1_LOW', '2_MED', '3_HIGH', '4_FULL']
        )
    else:
        # Use aligned_count as proxy
        df['structure_score_bucket'] = df['aligned_count'].map({
            0: '0_NONE', 1: '1_LOW', 2: '2_MED', 3: '3_HIGH', 4: '4_FULL'
        })

    # H4 structure string (for grouping)
    df['h4_structure_str'] = df['h4_structure'].fillna('UNKNOWN')
    df['h1_structure_str'] = df['h1_structure'].fillna('UNKNOWN')
    df['m15_structure_str'] = df['m15_structure'].fillna('UNKNOWN')
    df['m5_structure_str'] = df['m5_structure'].fillna('UNKNOWN')

    # H4 healthy string
    df['h4_healthy_str'] = df['h4_structure_healthy'].map({True: 'H4_HEALTHY', False: 'H4_NOT_HEALTHY'})
    df['h1_healthy_str'] = df['h1_structure_healthy'].map({True: 'H1_HEALTHY', False: 'H1_NOT_HEALTHY'})
    df['m15_healthy_str'] = df['m15_structure_healthy'].map({True: 'M15_HEALTHY', False: 'M15_NOT_HEALTHY'})
    df['m5_healthy_str'] = df['m5_structure_healthy'].map({True: 'M5_HEALTHY', False: 'M5_NOT_HEALTHY'})

    # Combined HTF structure (for pattern analysis)
    df['htf_combo'] = df['h4_structure_str'] + '_' + df['h1_structure_str']

    return df


# ============================================================================
# INDIVIDUAL EDGE TESTS
# ============================================================================

def test_h4_structure(df: pd.DataFrame, segment: str = "ALL") -> EdgeTestResult:
    """
    Test: Does H4 (4-hour) structure direction affect win rate?

    H4 is the highest timeframe and provides overall trend context.
    """
    df_valid = df[df['h4_structure_str'] != 'UNKNOWN']
    if len(df_valid) < 30:
        return EdgeTestResult(
            indicator="Structure",
            test_name="H4 Structure Direction",
            segment=segment,
            has_edge=False,
            p_value=1.0,
            effect_size=0.0,
            groups={},
            baseline_win_rate=df['is_winner'].mean() * 100 if len(df) > 0 else 0,
            confidence="LOW",
            test_type="chi_square",
            recommendation="INSUFFICIENT DATA - H4 structure data not available"
        )

    baseline_wr = df_valid['is_winner'].mean() * 100
    groups = calculate_win_rates(df_valid, 'h4_structure_str')

    chi2, p_value, effect_size = chi_square_test(df_valid, 'h4_structure_str')

    min_group_size = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group_size)

    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    return EdgeTestResult(
        indicator="Structure",
        test_name="H4 Structure Direction",
        segment=segment,
        has_edge=has_edge,
        p_value=p_value,
        effect_size=effect_size,
        groups=groups,
        baseline_win_rate=baseline_wr,
        confidence=confidence,
        test_type="chi_square",
        recommendation=recommendation
    )


def test_h4_alignment(df: pd.DataFrame, segment: str = "ALL") -> EdgeTestResult:
    """
    Test: Does H4 structure alignment with trade direction affect win rate?

    Healthy = H4 BULL for LONG trades, H4 BEAR for SHORT trades
    """
    df_valid = df[df['h4_healthy_str'].notna()]
    if len(df_valid) < 30:
        return EdgeTestResult(
            indicator="Structure",
            test_name="H4 Structure Alignment",
            segment=segment,
            has_edge=False,
            p_value=1.0,
            effect_size=0.0,
            groups={},
            baseline_win_rate=df['is_winner'].mean() * 100 if len(df) > 0 else 0,
            confidence="LOW",
            test_type="chi_square",
            recommendation="INSUFFICIENT DATA - H4 alignment data not available"
        )

    baseline_wr = df_valid['is_winner'].mean() * 100
    groups = calculate_win_rates(df_valid, 'h4_healthy_str')

    chi2, p_value, effect_size = chi_square_test(df_valid, 'h4_healthy_str')

    min_group_size = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group_size)

    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    return EdgeTestResult(
        indicator="Structure",
        test_name="H4 Structure Alignment",
        segment=segment,
        has_edge=has_edge,
        p_value=p_value,
        effect_size=effect_size,
        groups=groups,
        baseline_win_rate=baseline_wr,
        confidence=confidence,
        test_type="chi_square",
        recommendation=recommendation
    )


def test_h1_structure(df: pd.DataFrame, segment: str = "ALL") -> EdgeTestResult:
    """
    Test: Does H1 (1-hour) structure direction affect win rate?
    """
    df_valid = df[df['h1_structure_str'] != 'UNKNOWN']
    if len(df_valid) < 30:
        return EdgeTestResult(
            indicator="Structure",
            test_name="H1 Structure Direction",
            segment=segment,
            has_edge=False,
            p_value=1.0,
            effect_size=0.0,
            groups={},
            baseline_win_rate=df['is_winner'].mean() * 100 if len(df) > 0 else 0,
            confidence="LOW",
            test_type="chi_square",
            recommendation="INSUFFICIENT DATA - H1 structure data not available"
        )

    baseline_wr = df_valid['is_winner'].mean() * 100
    groups = calculate_win_rates(df_valid, 'h1_structure_str')

    chi2, p_value, effect_size = chi_square_test(df_valid, 'h1_structure_str')

    min_group_size = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group_size)

    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    return EdgeTestResult(
        indicator="Structure",
        test_name="H1 Structure Direction",
        segment=segment,
        has_edge=has_edge,
        p_value=p_value,
        effect_size=effect_size,
        groups=groups,
        baseline_win_rate=baseline_wr,
        confidence=confidence,
        test_type="chi_square",
        recommendation=recommendation
    )


def test_h1_alignment(df: pd.DataFrame, segment: str = "ALL") -> EdgeTestResult:
    """
    Test: Does H1 structure alignment with trade direction affect win rate?
    """
    df_valid = df[df['h1_healthy_str'].notna()]
    if len(df_valid) < 30:
        return EdgeTestResult(
            indicator="Structure",
            test_name="H1 Structure Alignment",
            segment=segment,
            has_edge=False,
            p_value=1.0,
            effect_size=0.0,
            groups={},
            baseline_win_rate=df['is_winner'].mean() * 100 if len(df) > 0 else 0,
            confidence="LOW",
            test_type="chi_square",
            recommendation="INSUFFICIENT DATA - H1 alignment data not available"
        )

    baseline_wr = df_valid['is_winner'].mean() * 100
    groups = calculate_win_rates(df_valid, 'h1_healthy_str')

    chi2, p_value, effect_size = chi_square_test(df_valid, 'h1_healthy_str')

    min_group_size = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group_size)

    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    return EdgeTestResult(
        indicator="Structure",
        test_name="H1 Structure Alignment",
        segment=segment,
        has_edge=has_edge,
        p_value=p_value,
        effect_size=effect_size,
        groups=groups,
        baseline_win_rate=baseline_wr,
        confidence=confidence,
        test_type="chi_square",
        recommendation=recommendation
    )


def test_m15_structure(df: pd.DataFrame, segment: str = "ALL") -> EdgeTestResult:
    """
    Test: Does M15 (15-minute) structure direction affect win rate?
    """
    df_valid = df[df['m15_structure_str'] != 'UNKNOWN']
    if len(df_valid) < 30:
        return EdgeTestResult(
            indicator="Structure",
            test_name="M15 Structure Direction",
            segment=segment,
            has_edge=False,
            p_value=1.0,
            effect_size=0.0,
            groups={},
            baseline_win_rate=df['is_winner'].mean() * 100 if len(df) > 0 else 0,
            confidence="LOW",
            test_type="chi_square",
            recommendation="INSUFFICIENT DATA - M15 structure data not available"
        )

    baseline_wr = df_valid['is_winner'].mean() * 100
    groups = calculate_win_rates(df_valid, 'm15_structure_str')

    chi2, p_value, effect_size = chi_square_test(df_valid, 'm15_structure_str')

    min_group_size = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group_size)

    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    return EdgeTestResult(
        indicator="Structure",
        test_name="M15 Structure Direction",
        segment=segment,
        has_edge=has_edge,
        p_value=p_value,
        effect_size=effect_size,
        groups=groups,
        baseline_win_rate=baseline_wr,
        confidence=confidence,
        test_type="chi_square",
        recommendation=recommendation
    )


def test_m15_alignment(df: pd.DataFrame, segment: str = "ALL") -> EdgeTestResult:
    """
    Test: Does M15 structure alignment with trade direction affect win rate?
    """
    df_valid = df[df['m15_healthy_str'].notna()]
    if len(df_valid) < 30:
        return EdgeTestResult(
            indicator="Structure",
            test_name="M15 Structure Alignment",
            segment=segment,
            has_edge=False,
            p_value=1.0,
            effect_size=0.0,
            groups={},
            baseline_win_rate=df['is_winner'].mean() * 100 if len(df) > 0 else 0,
            confidence="LOW",
            test_type="chi_square",
            recommendation="INSUFFICIENT DATA - M15 alignment data not available"
        )

    baseline_wr = df_valid['is_winner'].mean() * 100
    groups = calculate_win_rates(df_valid, 'm15_healthy_str')

    chi2, p_value, effect_size = chi_square_test(df_valid, 'm15_healthy_str')

    min_group_size = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group_size)

    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    return EdgeTestResult(
        indicator="Structure",
        test_name="M15 Structure Alignment",
        segment=segment,
        has_edge=has_edge,
        p_value=p_value,
        effect_size=effect_size,
        groups=groups,
        baseline_win_rate=baseline_wr,
        confidence=confidence,
        test_type="chi_square",
        recommendation=recommendation
    )


def test_m5_structure(df: pd.DataFrame, segment: str = "ALL") -> EdgeTestResult:
    """
    Test: Does M5 (5-minute) structure direction affect win rate?

    M5 is the entry timeframe - closest to trade execution.
    """
    df_valid = df[df['m5_structure_str'] != 'UNKNOWN']
    if len(df_valid) < 30:
        return EdgeTestResult(
            indicator="Structure",
            test_name="M5 Structure Direction",
            segment=segment,
            has_edge=False,
            p_value=1.0,
            effect_size=0.0,
            groups={},
            baseline_win_rate=df['is_winner'].mean() * 100 if len(df) > 0 else 0,
            confidence="LOW",
            test_type="chi_square",
            recommendation="INSUFFICIENT DATA - M5 structure data not available"
        )

    baseline_wr = df_valid['is_winner'].mean() * 100
    groups = calculate_win_rates(df_valid, 'm5_structure_str')

    chi2, p_value, effect_size = chi_square_test(df_valid, 'm5_structure_str')

    min_group_size = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group_size)

    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    return EdgeTestResult(
        indicator="Structure",
        test_name="M5 Structure Direction",
        segment=segment,
        has_edge=has_edge,
        p_value=p_value,
        effect_size=effect_size,
        groups=groups,
        baseline_win_rate=baseline_wr,
        confidence=confidence,
        test_type="chi_square",
        recommendation=recommendation
    )


def test_m5_alignment(df: pd.DataFrame, segment: str = "ALL") -> EdgeTestResult:
    """
    Test: Does M5 structure alignment with trade direction affect win rate?
    """
    df_valid = df[df['m5_healthy_str'].notna()]
    if len(df_valid) < 30:
        return EdgeTestResult(
            indicator="Structure",
            test_name="M5 Structure Alignment",
            segment=segment,
            has_edge=False,
            p_value=1.0,
            effect_size=0.0,
            groups={},
            baseline_win_rate=df['is_winner'].mean() * 100 if len(df) > 0 else 0,
            confidence="LOW",
            test_type="chi_square",
            recommendation="INSUFFICIENT DATA - M5 alignment data not available"
        )

    baseline_wr = df_valid['is_winner'].mean() * 100
    groups = calculate_win_rates(df_valid, 'm5_healthy_str')

    chi2, p_value, effect_size = chi_square_test(df_valid, 'm5_healthy_str')

    min_group_size = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group_size)

    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    return EdgeTestResult(
        indicator="Structure",
        test_name="M5 Structure Alignment",
        segment=segment,
        has_edge=has_edge,
        p_value=p_value,
        effect_size=effect_size,
        groups=groups,
        baseline_win_rate=baseline_wr,
        confidence=confidence,
        test_type="chi_square",
        recommendation=recommendation
    )


def test_htf_alignment(df: pd.DataFrame, segment: str = "ALL") -> EdgeTestResult:
    """
    Test: Does Higher Timeframe alignment (H4+H1 both healthy) affect win rate?

    HTF alignment provides strong trend context confirmation.
    """
    baseline_wr = df['is_winner'].mean() * 100
    groups = calculate_win_rates(df, 'htf_aligned_str')

    chi2, p_value, effect_size = chi_square_test(df, 'htf_aligned_str')

    min_group_size = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group_size)

    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    return EdgeTestResult(
        indicator="Structure",
        test_name="HTF Alignment (H4+H1)",
        segment=segment,
        has_edge=has_edge,
        p_value=p_value,
        effect_size=effect_size,
        groups=groups,
        baseline_win_rate=baseline_wr,
        confidence=confidence,
        test_type="chi_square",
        recommendation=recommendation
    )


def test_mtf_alignment(df: pd.DataFrame, segment: str = "ALL") -> EdgeTestResult:
    """
    Test: Does Medium Timeframe alignment (M15+M5 both healthy) affect win rate?

    MTF alignment provides entry-level structure confirmation.
    """
    baseline_wr = df['is_winner'].mean() * 100
    groups = calculate_win_rates(df, 'mtf_aligned_str')

    chi2, p_value, effect_size = chi_square_test(df, 'mtf_aligned_str')

    min_group_size = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group_size)

    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    return EdgeTestResult(
        indicator="Structure",
        test_name="MTF Alignment (M15+M5)",
        segment=segment,
        has_edge=has_edge,
        p_value=p_value,
        effect_size=effect_size,
        groups=groups,
        baseline_win_rate=baseline_wr,
        confidence=confidence,
        test_type="chi_square",
        recommendation=recommendation
    )


def test_all_alignment(df: pd.DataFrame, segment: str = "ALL") -> EdgeTestResult:
    """
    Test: Does full alignment (all 4 timeframes healthy) affect win rate?

    Full alignment = maximum structure confirmation.
    """
    baseline_wr = df['is_winner'].mean() * 100
    groups = calculate_win_rates(df, 'all_aligned_str')

    chi2, p_value, effect_size = chi_square_test(df, 'all_aligned_str')

    min_group_size = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group_size)

    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    return EdgeTestResult(
        indicator="Structure",
        test_name="Full Alignment (All 4 TF)",
        segment=segment,
        has_edge=has_edge,
        p_value=p_value,
        effect_size=effect_size,
        groups=groups,
        baseline_win_rate=baseline_wr,
        confidence=confidence,
        test_type="chi_square",
        recommendation=recommendation
    )


def test_aligned_count(df: pd.DataFrame, segment: str = "ALL") -> EdgeTestResult:
    """
    Test: Does number of aligned timeframes show monotonic relationship with win rate?

    Tests if more aligned timeframes = better win rate.
    """
    baseline_wr = df['is_winner'].mean() * 100

    groups = calculate_win_rates(df, 'aligned_count')

    # Define order
    bucket_order = [0, 1, 2, 3, 4]

    correlation, p_value, effect_size = spearman_monotonic_test(
        df, 'aligned_count', bucket_order=[str(x) for x in bucket_order]
    )

    # Recalculate with numeric for actual correlation
    if df['aligned_count'].nunique() >= 3:
        win_by_count = df.groupby('aligned_count')['is_winner'].mean() * 100
        positions = list(range(len(win_by_count)))
        from scipy import stats as sp_stats
        correlation, p_value = sp_stats.spearmanr(positions, win_by_count.values)
        effect_size = abs(win_by_count.max() - win_by_count.min())

    min_group_size = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group_size)

    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    if has_edge:
        direction = "more" if correlation > 0 else "fewer"
        recommendation = f"EDGE DETECTED - {direction} aligned TFs correlate with higher win rate (r={correlation:.3f})"

    # Convert groups keys to strings for consistency
    groups_str = {str(k): v for k, v in groups.items()}

    return EdgeTestResult(
        indicator="Structure",
        test_name="Aligned TF Count (0-4)",
        segment=segment,
        has_edge=has_edge,
        p_value=p_value,
        effect_size=effect_size,
        groups=groups_str,
        baseline_win_rate=baseline_wr,
        confidence=confidence,
        test_type="spearman",
        recommendation=recommendation
    )


def test_structure_score(df: pd.DataFrame, segment: str = "ALL") -> EdgeTestResult:
    """
    Test: Does structure score (0-4) show monotonic relationship with win rate?

    Structure score is sum of healthy flags across all 4 timeframes.
    """
    if 'structure_score' not in df.columns or df['structure_score'].isna().all():
        # Use aligned_count as proxy
        return test_aligned_count(df, segment)

    df_valid = df[df['structure_score'].notna()]
    if len(df_valid) < 30:
        return EdgeTestResult(
            indicator="Structure",
            test_name="Structure Score (0-4)",
            segment=segment,
            has_edge=False,
            p_value=1.0,
            effect_size=0.0,
            groups={},
            baseline_win_rate=df['is_winner'].mean() * 100 if len(df) > 0 else 0,
            confidence="LOW",
            test_type="spearman",
            recommendation="INSUFFICIENT DATA - Structure score not available"
        )

    baseline_wr = df_valid['is_winner'].mean() * 100
    groups = calculate_win_rates(df_valid, 'structure_score_bucket')

    bucket_order = ['0_NONE', '1_LOW', '2_MED', '3_HIGH', '4_FULL']

    correlation, p_value, effect_size = spearman_monotonic_test(
        df_valid, 'structure_score_bucket', bucket_order=bucket_order
    )

    min_group_size = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group_size)

    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    if has_edge:
        direction = "higher" if correlation > 0 else "lower"
        recommendation = f"EDGE DETECTED - {direction} structure score correlates with higher win rate (r={correlation:.3f})"

    return EdgeTestResult(
        indicator="Structure",
        test_name="Structure Score (0-4)",
        segment=segment,
        has_edge=has_edge,
        p_value=p_value,
        effect_size=effect_size,
        groups=groups,
        baseline_win_rate=baseline_wr,
        confidence=confidence,
        test_type="spearman",
        recommendation=recommendation
    )


# ============================================================================
# CONFLUENCE SCORE EDGE TESTS
# ============================================================================

def test_confluence_direction(df: pd.DataFrame, segment: str = "ALL") -> EdgeTestResult:
    """
    Test: Does confluence direction (BULLISH/BEARISH/NEUTRAL) affect win rate?

    Tests the raw directional signal from the weighted structure confluence.
    """
    baseline_wr = df['is_winner'].mean() * 100
    groups = calculate_win_rates(df, 'confluence_direction')

    chi2, p_value, effect_size = chi_square_test(df, 'confluence_direction')

    min_group_size = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group_size)

    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    return EdgeTestResult(
        indicator="Structure",
        test_name="Confluence Direction (Bull/Bear)",
        segment=segment,
        has_edge=has_edge,
        p_value=p_value,
        effect_size=effect_size,
        groups=groups,
        baseline_win_rate=baseline_wr,
        confidence=confidence,
        test_type="chi_square",
        recommendation=recommendation
    )


def test_confluence_alignment(df: pd.DataFrame, segment: str = "ALL") -> EdgeTestResult:
    """
    Test: Does confluence alignment with trade direction affect win rate?

    ALIGNED = LONG with positive confluence, SHORT with negative confluence
    MISALIGNED = opposite

    Hypothesis: Trading WITH structure confluence should outperform.
    """
    baseline_wr = df['is_winner'].mean() * 100
    groups = calculate_win_rates(df, 'confluence_aligned_str')

    chi2, p_value, effect_size = chi_square_test(df, 'confluence_aligned_str')

    min_group_size = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group_size)

    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    return EdgeTestResult(
        indicator="Structure",
        test_name="Confluence Alignment",
        segment=segment,
        has_edge=has_edge,
        p_value=p_value,
        effect_size=effect_size,
        groups=groups,
        baseline_win_rate=baseline_wr,
        confidence=confidence,
        test_type="chi_square",
        recommendation=recommendation
    )


def test_confluence_buckets(df: pd.DataFrame, segment: str = "ALL") -> EdgeTestResult:
    """
    Test: Does confluence bucket (STRONG_BEAR to STRONG_BULL) affect win rate?

    Tests the 7-level categorization of confluence score.
    """
    baseline_wr = df['is_winner'].mean() * 100
    groups = calculate_win_rates(df, 'confluence_bucket')

    # Define order from most bearish to most bullish
    bucket_order = [
        'STRONG_BEAR', 'MODERATE_BEAR', 'WEAK_BEAR',
        'NEUTRAL',
        'WEAK_BULL', 'MODERATE_BULL', 'STRONG_BULL'
    ]

    correlation, p_value, effect_size = spearman_monotonic_test(
        df, 'confluence_bucket', bucket_order=bucket_order
    )

    min_group_size = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group_size)

    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    if has_edge:
        direction = "bullish" if correlation > 0 else "bearish"
        recommendation = f"EDGE DETECTED - {direction} confluence correlates with higher win rate (r={correlation:.3f})"

    return EdgeTestResult(
        indicator="Structure",
        test_name="Confluence Score Buckets",
        segment=segment,
        has_edge=has_edge,
        p_value=p_value,
        effect_size=effect_size,
        groups=groups,
        baseline_win_rate=baseline_wr,
        confidence=confidence,
        test_type="spearman",
        recommendation=recommendation
    )


def test_confluence_magnitude(df: pd.DataFrame, segment: str = "ALL") -> EdgeTestResult:
    """
    Test: Does confluence magnitude (absolute value) affect win rate?

    Hypothesis: Stronger confluence (regardless of direction) = more conviction = better win rate.
    """
    baseline_wr = df['is_winner'].mean() * 100

    # Filter to valid magnitude buckets
    df_valid = df[df['confluence_magnitude_bucket'].notna()]
    if len(df_valid) < 30:
        return EdgeTestResult(
            indicator="Structure",
            test_name="Confluence Magnitude",
            segment=segment,
            has_edge=False,
            p_value=1.0,
            effect_size=0.0,
            groups={},
            baseline_win_rate=baseline_wr,
            confidence="LOW",
            test_type="spearman",
            recommendation="INSUFFICIENT DATA"
        )

    groups = calculate_win_rates(df_valid, 'confluence_magnitude_bucket')

    bucket_order = ['WEAK', 'MODERATE', 'STRONG', 'VERY_STRONG']

    correlation, p_value, effect_size = spearman_monotonic_test(
        df_valid, 'confluence_magnitude_bucket', bucket_order=bucket_order
    )

    min_group_size = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group_size)

    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    if has_edge:
        direction = "higher" if correlation > 0 else "lower"
        recommendation = f"EDGE DETECTED - {direction} confluence magnitude correlates with higher win rate (r={correlation:.3f})"

    return EdgeTestResult(
        indicator="Structure",
        test_name="Confluence Magnitude",
        segment=segment,
        has_edge=has_edge,
        p_value=p_value,
        effect_size=effect_size,
        groups=groups,
        baseline_win_rate=baseline_wr,
        confidence=confidence,
        test_type="spearman",
        recommendation=recommendation
    )


def test_confluence_quintiles(df: pd.DataFrame, segment: str = "ALL") -> EdgeTestResult:
    """
    Test: Does confluence score (quintiles) show monotonic relationship with win rate?

    Uses signed confluence score from most bearish to most bullish.
    """
    baseline_wr = df['is_winner'].mean() * 100
    groups = calculate_win_rates(df, 'confluence_quintile')

    quintile_order = ['Q1_MostBear', 'Q2_Bear', 'Q3_Neutral', 'Q4_Bull', 'Q5_MostBull']

    correlation, p_value, effect_size = spearman_monotonic_test(
        df, 'confluence_quintile', bucket_order=quintile_order
    )

    min_group_size = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group_size)

    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    if has_edge:
        direction = "bullish" if correlation > 0 else "bearish"
        recommendation = f"EDGE DETECTED - {direction} confluence correlates with higher win rate (r={correlation:.3f})"

    return EdgeTestResult(
        indicator="Structure",
        test_name="Confluence Score (Quintiles)",
        segment=segment,
        has_edge=has_edge,
        p_value=p_value,
        effect_size=effect_size,
        groups=groups,
        baseline_win_rate=baseline_wr,
        confidence=confidence,
        test_type="spearman",
        recommendation=recommendation
    )


# ============================================================================
# FULL ANALYSIS RUNNER
# ============================================================================

def run_full_analysis(
    models: List[str] = None,
    directions: List[str] = None,
    date_from: str = None,
    date_to: str = None,
    stop_type: str = 'zone_buffer'
) -> Tuple[List[EdgeTestResult], Dict]:
    """
    Run complete Market Structure edge analysis across all segments.

    Segments tested:
    1. ALL - All trades combined
    2. CONTINUATION (Combined) - EPCH1 + EPCH3
    3. REJECTION (Combined) - EPCH2 + EPCH4
    4. EPCH1 - Primary Continuation
    5. EPCH2 - Primary Rejection
    6. EPCH3 - Secondary Continuation
    7. EPCH4 - Secondary Rejection
    8. LONG - Long trades only
    9. SHORT - Short trades only

    Returns: (list of EdgeTestResults, metadata dict)
    """
    # Fetch data
    print("Fetching data from database (using entry_indicators structure data)...")
    df = fetch_structure_data(
        models=models,
        directions=directions,
        date_from=date_from,
        date_to=date_to,
        stop_type=stop_type
    )

    if df.empty:
        raise ValueError("No data returned from database. Check filters or entry_indicators data.")

    # Calculate structure metrics
    print(f"Calculating Structure metrics for {len(df):,} trades...")
    df = calculate_structure_metrics(df)

    # Print summary stats
    print(f"\nStructure Summary:")

    # Calculate percentages for each timeframe
    def get_structure_pcts(col):
        if col not in df.columns:
            return 0, 0, 0
        valid = df[df[col].notna() & (df[col] != 'UNKNOWN')]
        if len(valid) == 0:
            return 0, 0, 0
        bull = (valid[col] == 'BULL').mean() * 100
        bear = (valid[col] == 'BEAR').mean() * 100
        neutral = (valid[col] == 'NEUTRAL').mean() * 100
        return bull, bear, neutral

    h4_bull, h4_bear, h4_neutral = get_structure_pcts('h4_structure')
    h1_bull, h1_bear, h1_neutral = get_structure_pcts('h1_structure')
    m15_bull, m15_bear, m15_neutral = get_structure_pcts('m15_structure')
    m5_bull, m5_bear, m5_neutral = get_structure_pcts('m5_structure')

    print(f"  H4:  BULL {h4_bull:.1f}% | BEAR {h4_bear:.1f}% | NEUTRAL {h4_neutral:.1f}%")
    print(f"  H1:  BULL {h1_bull:.1f}% | BEAR {h1_bear:.1f}% | NEUTRAL {h1_neutral:.1f}%")
    print(f"  M15: BULL {m15_bull:.1f}% | BEAR {m15_bear:.1f}% | NEUTRAL {m15_neutral:.1f}%")
    print(f"  M5:  BULL {m5_bull:.1f}% | BEAR {m5_bear:.1f}% | NEUTRAL {m5_neutral:.1f}%")

    # Aligned count distribution
    aligned_dist = df['aligned_count'].value_counts().sort_index()
    print(f"\n  Aligned TF Count Distribution:")
    for count, n in aligned_dist.items():
        pct = n / len(df) * 100
        print(f"    {count}/4 aligned: {n:,} ({pct:.1f}%)")

    # Confluence Score Summary
    print(f"\n  Confluence Score Summary:")
    print(f"    Range: {df['confluence_score'].min():.2f} to {df['confluence_score'].max():.2f}")
    print(f"    Mean: {df['confluence_score'].mean():.2f}")
    print(f"    Median: {df['confluence_score'].median():.2f}")
    print(f"    Std Dev: {df['confluence_score'].std():.2f}")

    # Confluence bucket distribution
    print(f"\n  Confluence Bucket Distribution:")
    conf_dist = df['confluence_bucket'].value_counts()
    bucket_order = ['STRONG_BEAR', 'MODERATE_BEAR', 'WEAK_BEAR', 'NEUTRAL', 'WEAK_BULL', 'MODERATE_BULL', 'STRONG_BULL']
    for bucket in bucket_order:
        if bucket in conf_dist.index:
            n = conf_dist[bucket]
            pct = n / len(df) * 100
            print(f"    {bucket}: {n:,} ({pct:.1f}%)")
    print()

    # Build metadata
    structure_score_mean = df['structure_score'].mean() if 'structure_score' in df.columns and df['structure_score'].notna().any() else df['aligned_count'].mean()
    structure_score_median = df['structure_score'].median() if 'structure_score' in df.columns and df['structure_score'].notna().any() else df['aligned_count'].median()

    metadata = {
        'indicator': 'Market Structure',
        'total_trades': len(df),
        'date_range': f"{df['date'].min()} to {df['date'].max()}",
        'baseline_win_rate': df['is_winner'].mean() * 100,
        'stop_type': stop_type,
        'models_filter': models,
        'directions_filter': directions,
        'h4_bull_pct': h4_bull,
        'h4_bear_pct': h4_bear,
        'h4_neutral_pct': h4_neutral,
        'h1_bull_pct': h1_bull,
        'h1_bear_pct': h1_bear,
        'h1_neutral_pct': h1_neutral,
        'm15_bull_pct': m15_bull,
        'm15_bear_pct': m15_bear,
        'm15_neutral_pct': m15_neutral,
        'm5_bull_pct': m5_bull,
        'm5_bear_pct': m5_bear,
        'm5_neutral_pct': m5_neutral,
        'structure_score_mean': structure_score_mean,
        'structure_score_median': structure_score_median,
        # Confluence score metadata
        'confluence_score_min': float(df['confluence_score'].min()),
        'confluence_score_max': float(df['confluence_score'].max()),
        'confluence_score_mean': float(df['confluence_score'].mean()),
        'confluence_score_median': float(df['confluence_score'].median()),
        'confluence_score_std': float(df['confluence_score'].std()),
        'confluence_weights': CONFLUENCE_WEIGHTS,
    }

    results = []

    # Define segments to test
    segments = [
        # Overall
        ("ALL", df, "Overall"),

        # By Direction
        ("LONG", df[df['direction'] == 'LONG'], "Direction"),
        ("SHORT", df[df['direction'] == 'SHORT'], "Direction"),

        # By Trade Type (Combined)
        ("CONTINUATION (Combined)", df[df['model'].isin(['EPCH1', 'EPCH3'])], "Trade Type"),
        ("REJECTION (Combined)", df[df['model'].isin(['EPCH2', 'EPCH4'])], "Trade Type"),

        # By Individual Model - Continuation
        ("EPCH1 (Primary Cont.)", df[df['model'] == 'EPCH1'], "Model - Continuation"),
        ("EPCH3 (Secondary Cont.)", df[df['model'] == 'EPCH3'], "Model - Continuation"),

        # By Individual Model - Rejection
        ("EPCH2 (Primary Rej.)", df[df['model'] == 'EPCH2'], "Model - Rejection"),
        ("EPCH4 (Secondary Rej.)", df[df['model'] == 'EPCH4'], "Model - Rejection"),
    ]

    # Run tests for each segment
    for segment_name, segment_df, category in segments:
        if len(segment_df) < 30:
            print(f"  Skipping {segment_name} - insufficient data ({len(segment_df)} trades)")
            continue

        print(f"  Testing {segment_name} ({len(segment_df):,} trades)...")

        # Test individual timeframe structures
        results.append(test_h4_structure(segment_df, segment_name))
        results.append(test_h4_alignment(segment_df, segment_name))
        results.append(test_h1_structure(segment_df, segment_name))
        results.append(test_h1_alignment(segment_df, segment_name))
        results.append(test_m15_structure(segment_df, segment_name))
        results.append(test_m15_alignment(segment_df, segment_name))
        results.append(test_m5_structure(segment_df, segment_name))
        results.append(test_m5_alignment(segment_df, segment_name))

        # Test composite alignment metrics
        results.append(test_htf_alignment(segment_df, segment_name))
        results.append(test_mtf_alignment(segment_df, segment_name))
        results.append(test_all_alignment(segment_df, segment_name))

        # Test structure score / aligned count
        results.append(test_aligned_count(segment_df, segment_name))

        # Test confluence score metrics
        results.append(test_confluence_direction(segment_df, segment_name))
        results.append(test_confluence_alignment(segment_df, segment_name))
        results.append(test_confluence_buckets(segment_df, segment_name))
        results.append(test_confluence_magnitude(segment_df, segment_name))
        results.append(test_confluence_quintiles(segment_df, segment_name))

    return results, metadata


# ============================================================================
# CLI EXECUTION
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="CALC-011: Market Structure Edge Analysis - Test structure indicators for statistical edge"
    )
    parser.add_argument(
        '--models',
        type=str,
        default=None,
        help='Comma-separated list of models (e.g., EPCH01,EPCH03)'
    )
    parser.add_argument(
        '--direction',
        type=str,
        default=None,
        choices=['LONG', 'SHORT'],
        help='Filter by direction'
    )
    parser.add_argument(
        '--date-from',
        type=str,
        default=None,
        help='Start date (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--date-to',
        type=str,
        default=None,
        help='End date (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--stop-type',
        type=str,
        default='zone_buffer',
        help='Stop type for win/loss definition (default: zone_buffer)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output file path for markdown report'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress console output (only save report)'
    )

    args = parser.parse_args()

    # Parse models list
    models = args.models.split(',') if args.models else None
    directions = [args.direction] if args.direction else None

    # Run analysis
    print("\n" + "=" * 80)
    print("CALC-011: MARKET STRUCTURE EDGE ANALYSIS")
    print("=" * 80 + "\n")

    results, metadata = run_full_analysis(
        models=models,
        directions=directions,
        date_from=args.date_from,
        date_to=args.date_to,
        stop_type=args.stop_type
    )

    # Console output
    if not args.quiet:
        print()
        print_console_summary(results, metadata)

    # Generate markdown report
    report = generate_markdown_report(results, metadata)

    # Save report
    if args.output:
        filepath = save_report(report, args.output)
        print(f"\nReport saved to: {filepath}")
    else:
        # Default filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"structure_edge_{timestamp}.md"
        filepath = save_report(report, filename)
        print(f"\nReport saved to: {filepath}")

    # Return results for programmatic use
    return results, metadata


if __name__ == "__main__":
    main()
