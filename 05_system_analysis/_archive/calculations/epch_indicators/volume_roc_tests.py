"""
================================================================================
EPOCH TRADING SYSTEM - EPCH Indicators Edge Analysis
Volume ROC Edge Tests
================================================================================

Tests for vol_roc indicator:
- Level test (ABOVE vs BELOW 0%)
- Threshold tests (10%, 20%, 30%)
- Magnitude quintiles test

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
# VOLUME ROC METRIC CALCULATIONS
# =============================================================================

def calculate_vol_roc_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate all volume ROC derived metrics.

    Adds columns:
    - vol_roc_level: ABOVE or BELOW (0% baseline)
    - vol_roc_abs: Absolute value
    - vol_roc_threshold_10: ABOVE_10 or BELOW_10
    - vol_roc_threshold_20: ABOVE_20 or BELOW_20
    - vol_roc_threshold_30: ABOVE_30 or BELOW_30
    - vol_roc_quintile: Q1_Lowest to Q5_Highest
    """
    df = df.copy()

    if 'vol_roc' not in df.columns:
        return df

    # Level classification (above/below 0%)
    df['vol_roc_level'] = df['vol_roc'].apply(
        lambda x: 'ABOVE' if pd.notna(x) and x >= 0 else (
            'BELOW' if pd.notna(x) else None
        )
    )

    # Absolute value
    df['vol_roc_abs'] = df['vol_roc'].abs()

    # Threshold classifications
    df = create_threshold_bucket(df, 'vol_roc', 'vol_roc_threshold_10', 10.0, 'ABOVE_10', 'BELOW_10')
    df = create_threshold_bucket(df, 'vol_roc', 'vol_roc_threshold_20', 20.0, 'ABOVE_20', 'BELOW_20')
    df = create_threshold_bucket(df, 'vol_roc', 'vol_roc_threshold_30', 30.0, 'ABOVE_30', 'BELOW_30')

    # Magnitude quintiles
    df = create_quintile_buckets(
        df,
        'vol_roc',
        'vol_roc_quintile',
        ['Q1_Lowest', 'Q2', 'Q3', 'Q4', 'Q5_Highest']
    )

    return df


# =============================================================================
# INDIVIDUAL TESTS
# =============================================================================

def test_vol_roc_level(df: pd.DataFrame, segment_name: str) -> EdgeTestResult:
    """Test if positive vs negative ROC affects win rate."""
    df = df[df['vol_roc_level'].notna()].copy()

    if len(df) < 30:
        return None

    # Calculate statistics
    chi2, p_value, effect_size = chi_square_test(df, 'vol_roc_level')
    groups = calculate_win_rates(df, 'vol_roc_level')

    if not groups:
        return None

    # Determine confidence
    min_group = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group)

    # Determine edge
    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    baseline = (df['is_winner'].sum() / len(df) * 100) if len(df) > 0 else 0

    return EdgeTestResult(
        indicator="Volume ROC",
        test_name="ROC Level (Above/Below 0%)",
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


def test_vol_roc_threshold(df: pd.DataFrame, segment_name: str, threshold: float) -> EdgeTestResult:
    """Test if ROC above threshold performs better."""
    threshold_col = f'vol_roc_threshold_{int(threshold)}'

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
        indicator="Volume ROC",
        test_name=f"ROC Threshold ({int(threshold)}%)",
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


def test_vol_roc_magnitude(df: pd.DataFrame, segment_name: str) -> EdgeTestResult:
    """Test if higher ROC correlates with win rate."""
    df = df[df['vol_roc_quintile'].notna()].copy()

    if len(df) < 30:
        return None

    bucket_order = ['Q1_Lowest', 'Q2', 'Q3', 'Q4', 'Q5_Highest']

    # Calculate statistics
    correlation, p_value, effect_size = spearman_monotonic_test(
        df, 'vol_roc_quintile', bucket_order=bucket_order
    )
    groups = calculate_win_rates(df, 'vol_roc_quintile')

    if not groups:
        return None

    # Determine confidence
    existing_groups = {k: v for k, v in groups.items() if k in bucket_order}
    min_group = min(g['trades'] for g in existing_groups.values()) if existing_groups else 0
    confidence = get_confidence_level(min_group)

    # Determine edge
    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    if has_edge:
        direction = "HIGHER = BETTER" if correlation > 0 else "LOWER = BETTER"
        recommendation = f"EDGE: {direction} (corr={correlation:.2f}, effect={effect_size:.1f}pp)"

    baseline = (df['is_winner'].sum() / len(df) * 100) if len(df) > 0 else 0

    return EdgeTestResult(
        indicator="Volume ROC",
        test_name="ROC Magnitude (Quintiles)",
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
# RUN ALL VOLUME ROC TESTS
# =============================================================================

def run_volume_roc_tests(df: pd.DataFrame) -> List[EdgeTestResult]:
    """Run all volume ROC edge tests across all segments."""
    results = []

    # Calculate metrics
    df = calculate_vol_roc_metrics(df)

    # Get segments
    segments = get_segments(df)

    for segment_name, segment_df, category in segments:
        # Recalculate metrics per segment
        segment_df = calculate_vol_roc_metrics(segment_df)

        # Run each test
        result = test_vol_roc_level(segment_df, segment_name)
        if result:
            results.append(result)

        for threshold in [10, 20, 30]:
            result = test_vol_roc_threshold(segment_df, segment_name, threshold)
            if result:
                results.append(result)

        result = test_vol_roc_magnitude(segment_df, segment_name)
        if result:
            results.append(result)

    return results
