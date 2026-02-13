"""
================================================================================
EPOCH TRADING SYSTEM - EPCH Indicators Edge Analysis
Candle Range Edge Tests
================================================================================

Tests for candle_range_pct indicator:
- Absorption zone test (< 0.12% vs >= 0.12%)
- Threshold tests (0.12%, 0.15%, 0.18%, 0.20%)
- Magnitude quintiles test
- Category test (VERY_SMALL to VERY_LARGE)

Version: 1.0.0
================================================================================
"""

import pandas as pd
import numpy as np
from typing import List

from .base_tester import (
    EdgeTestResult,
    get_segments,
    calculate_win_rates,
    chi_square_test,
    spearman_monotonic_test,
    get_confidence_level,
    determine_edge,
    create_quintile_buckets,
    create_threshold_bucket
)


# =============================================================================
# CANDLE RANGE METRIC CALCULATIONS
# =============================================================================

def calculate_candle_range_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate all candle range derived metrics.

    Adds columns:
    - range_threshold_012: LARGE if >= 0.12%, else SMALL
    - range_threshold_015: LARGE if >= 0.15%, else SMALL
    - range_threshold_018: LARGE if >= 0.18%, else SMALL
    - range_threshold_020: LARGE if >= 0.20%, else SMALL
    - range_absorption: ABSORPTION if < 0.12%, else NORMAL
    - range_quintile: Q1_Lowest to Q5_Highest
    - range_category: VERY_SMALL, SMALL, MEDIUM, LARGE, VERY_LARGE
    """
    df = df.copy()

    if 'candle_range_pct' not in df.columns:
        return df

    # Threshold classifications
    df = create_threshold_bucket(df, 'candle_range_pct', 'range_threshold_012', 0.12, 'LARGE', 'SMALL')
    df = create_threshold_bucket(df, 'candle_range_pct', 'range_threshold_015', 0.15, 'LARGE', 'SMALL')
    df = create_threshold_bucket(df, 'candle_range_pct', 'range_threshold_018', 0.18, 'LARGE', 'SMALL')
    df = create_threshold_bucket(df, 'candle_range_pct', 'range_threshold_020', 0.20, 'LARGE', 'SMALL')

    # Absorption zone (low range = absorption = skip)
    df['range_absorption'] = df['candle_range_pct'].apply(
        lambda x: 'ABSORPTION' if pd.notna(x) and x < 0.12 else (
            'NORMAL' if pd.notna(x) else None
        )
    )

    # Quintile buckets
    df = create_quintile_buckets(
        df,
        'candle_range_pct',
        'range_quintile',
        ['Q1_Lowest', 'Q2', 'Q3', 'Q4', 'Q5_Highest']
    )

    # Category classification
    def categorize_range(val):
        if pd.isna(val):
            return None
        if val < 0.12:
            return 'VERY_SMALL'
        elif val < 0.15:
            return 'SMALL'
        elif val < 0.18:
            return 'MEDIUM'
        elif val < 0.20:
            return 'LARGE'
        else:
            return 'VERY_LARGE'

    df['range_category'] = df['candle_range_pct'].apply(categorize_range)

    return df


# =============================================================================
# INDIVIDUAL TESTS
# =============================================================================

def test_absorption_zone(df: pd.DataFrame, segment_name: str) -> EdgeTestResult:
    """Test if absorption zone (< 0.12%) underperforms."""
    df = df[df['range_absorption'].notna()].copy()

    if len(df) < 30:
        return None

    # Calculate statistics
    chi2, p_value, effect_size = chi_square_test(df, 'range_absorption')
    groups = calculate_win_rates(df, 'range_absorption')

    if not groups:
        return None

    # Determine confidence
    min_group = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group)

    # Determine edge
    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    # Add specific recommendation
    if has_edge and 'ABSORPTION' in groups and 'NORMAL' in groups:
        abs_wr = groups['ABSORPTION']['win_rate']
        norm_wr = groups['NORMAL']['win_rate']
        if abs_wr < norm_wr:
            recommendation = f"EDGE: Skip absorption zone (Range < 0.12%). WR: {abs_wr:.1f}% vs {norm_wr:.1f}%"

    baseline = (df['is_winner'].sum() / len(df) * 100) if len(df) > 0 else 0

    return EdgeTestResult(
        indicator="Candle Range",
        test_name="Absorption Zone (<0.12%)",
        segment=segment_name,
        has_edge=has_edge,
        p_value=p_value,
        effect_size=effect_size,
        groups=groups,
        baseline_win_rate=baseline,
        confidence=confidence,
        test_type="chi_square",
        recommendation=recommendation
    )


def test_range_threshold(df: pd.DataFrame, segment_name: str, threshold: float) -> EdgeTestResult:
    """Test if range above threshold performs better."""
    threshold_col = f'range_threshold_{int(threshold * 100):03d}'

    df = df[df[threshold_col].notna()].copy()

    if len(df) < 30:
        return None

    # Calculate statistics
    chi2, p_value, effect_size = chi_square_test(df, threshold_col)
    groups = calculate_win_rates(df, threshold_col)

    if not groups:
        return None

    # Determine confidence
    min_group = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group)

    # Determine edge
    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    baseline = (df['is_winner'].sum() / len(df) * 100) if len(df) > 0 else 0

    return EdgeTestResult(
        indicator="Candle Range",
        test_name=f"Range Threshold ({threshold:.2f}%)",
        segment=segment_name,
        has_edge=has_edge,
        p_value=p_value,
        effect_size=effect_size,
        groups=groups,
        baseline_win_rate=baseline,
        confidence=confidence,
        test_type="chi_square",
        recommendation=recommendation
    )


def test_range_magnitude(df: pd.DataFrame, segment_name: str) -> EdgeTestResult:
    """Test if larger ranges correlate with higher win rates (quintiles)."""
    df = df[df['range_quintile'].notna()].copy()

    if len(df) < 30:
        return None

    bucket_order = ['Q1_Lowest', 'Q2', 'Q3', 'Q4', 'Q5_Highest']

    # Calculate statistics
    correlation, p_value, effect_size = spearman_monotonic_test(
        df, 'range_quintile', bucket_order=bucket_order
    )
    groups = calculate_win_rates(df, 'range_quintile')

    if not groups:
        return None

    # Determine confidence
    existing_groups = {k: v for k, v in groups.items() if k in bucket_order}
    min_group = min(g['trades'] for g in existing_groups.values()) if existing_groups else 0
    confidence = get_confidence_level(min_group)

    # Determine edge
    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    if has_edge:
        direction = "LARGER = BETTER" if correlation > 0 else "SMALLER = BETTER"
        recommendation = f"EDGE: {direction} (corr={correlation:.2f}, effect={effect_size:.1f}pp)"

    baseline = (df['is_winner'].sum() / len(df) * 100) if len(df) > 0 else 0

    return EdgeTestResult(
        indicator="Candle Range",
        test_name="Range Magnitude (Quintiles)",
        segment=segment_name,
        has_edge=has_edge,
        p_value=p_value,
        effect_size=effect_size,
        groups=groups,
        baseline_win_rate=baseline,
        confidence=confidence,
        test_type="spearman",
        recommendation=recommendation
    )


def test_range_category(df: pd.DataFrame, segment_name: str) -> EdgeTestResult:
    """Test if range category (VERY_SMALL to VERY_LARGE) correlates with win rate."""
    df = df[df['range_category'].notna()].copy()

    if len(df) < 30:
        return None

    category_order = ['VERY_SMALL', 'SMALL', 'MEDIUM', 'LARGE', 'VERY_LARGE']

    # Calculate statistics
    correlation, p_value, effect_size = spearman_monotonic_test(
        df, 'range_category', bucket_order=category_order
    )
    groups = calculate_win_rates(df, 'range_category')

    if not groups:
        return None

    # Determine confidence
    existing_groups = {k: v for k, v in groups.items() if k in category_order}
    min_group = min(g['trades'] for g in existing_groups.values()) if existing_groups else 0
    confidence = get_confidence_level(min_group)

    # Determine edge
    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    baseline = (df['is_winner'].sum() / len(df) * 100) if len(df) > 0 else 0

    return EdgeTestResult(
        indicator="Candle Range",
        test_name="Range Category",
        segment=segment_name,
        has_edge=has_edge,
        p_value=p_value,
        effect_size=effect_size,
        groups=groups,
        baseline_win_rate=baseline,
        confidence=confidence,
        test_type="spearman",
        recommendation=recommendation
    )


# =============================================================================
# RUN ALL CANDLE RANGE TESTS
# =============================================================================

def run_candle_range_tests(df: pd.DataFrame) -> List[EdgeTestResult]:
    """Run all candle range edge tests across all segments."""
    results = []

    # Calculate metrics
    df = calculate_candle_range_metrics(df)

    # Get segments
    segments = get_segments(df)

    for segment_name, segment_df, category in segments:
        # Recalculate metrics per segment (quintiles need segment-specific calculation)
        segment_df = calculate_candle_range_metrics(segment_df)

        # Run each test
        result = test_absorption_zone(segment_df, segment_name)
        if result:
            results.append(result)

        for threshold in [0.12, 0.15, 0.18, 0.20]:
            result = test_range_threshold(segment_df, segment_name, threshold)
            if result:
                results.append(result)

        result = test_range_magnitude(segment_df, segment_name)
        if result:
            results.append(result)

        result = test_range_category(segment_df, segment_name)
        if result:
            results.append(result)

    return results
