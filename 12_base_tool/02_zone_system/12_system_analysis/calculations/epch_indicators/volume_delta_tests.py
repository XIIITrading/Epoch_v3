"""
================================================================================
EPOCH TRADING SYSTEM - EPCH Indicators Edge Analysis
Volume Delta Edge Tests
================================================================================

Tests for vol_delta indicator:
- Sign test (POSITIVE vs NEGATIVE)
- Alignment test (aligned with trade direction)
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
    create_quintile_buckets
)


# =============================================================================
# VOLUME DELTA METRIC CALCULATIONS
# =============================================================================

def calculate_vol_delta_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate all volume delta derived metrics.

    Adds columns:
    - vol_delta_sign: POSITIVE or NEGATIVE
    - vol_delta_abs: Absolute value
    - vol_delta_aligned: Boolean (aligned with direction)
    - vol_delta_aligned_str: ALIGNED or MISALIGNED
    - vol_delta_quintile: Q1_Lowest to Q5_Highest (absolute)
    """
    df = df.copy()

    if 'vol_delta' not in df.columns:
        return df

    # Sign classification
    df['vol_delta_sign'] = df['vol_delta'].apply(
        lambda x: 'POSITIVE' if pd.notna(x) and x > 0 else (
            'NEGATIVE' if pd.notna(x) and x < 0 else None
        )
    )

    # Absolute value
    df['vol_delta_abs'] = df['vol_delta'].abs()

    # Alignment with trade direction
    # LONG: positive delta (buying) = ALIGNED
    # SHORT: negative delta (selling) = ALIGNED
    def check_alignment(row):
        if pd.isna(row.get('vol_delta')) or pd.isna(row.get('direction')):
            return None
        if row['direction'] == 'LONG':
            return row['vol_delta'] > 0
        elif row['direction'] == 'SHORT':
            return row['vol_delta'] < 0
        return None

    df['vol_delta_aligned'] = df.apply(check_alignment, axis=1)
    df['vol_delta_aligned_str'] = df['vol_delta_aligned'].apply(
        lambda x: 'ALIGNED' if x is True else ('MISALIGNED' if x is False else None)
    )

    # Magnitude quintiles (absolute value)
    df = create_quintile_buckets(
        df,
        'vol_delta_abs',
        'vol_delta_quintile',
        ['Q1_Lowest', 'Q2', 'Q3', 'Q4', 'Q5_Highest']
    )

    return df


# =============================================================================
# INDIVIDUAL TESTS
# =============================================================================

def test_vol_delta_sign(df: pd.DataFrame, segment_name: str) -> EdgeTestResult:
    """Test if positive vs negative delta affects win rate."""
    df = df[df['vol_delta_sign'].notna()].copy()

    if len(df) < 30:
        return None

    # Calculate statistics
    chi2, p_value, effect_size = chi_square_test(df, 'vol_delta_sign')
    groups = calculate_win_rates(df, 'vol_delta_sign')

    if not groups:
        return None

    # Determine confidence
    min_group = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group)

    # Determine edge
    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    baseline = (df['is_winner'].sum() / len(df) * 100) if len(df) > 0 else 0

    return EdgeTestResult(
        indicator="Volume Delta",
        test_name="Delta Sign (Pos vs Neg)",
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


def test_vol_delta_alignment(df: pd.DataFrame, segment_name: str) -> EdgeTestResult:
    """Test if delta aligned with direction improves win rate."""
    df = df[df['vol_delta_aligned_str'].notna()].copy()

    if len(df) < 30:
        return None

    # Calculate statistics
    chi2, p_value, effect_size = chi_square_test(df, 'vol_delta_aligned_str')
    groups = calculate_win_rates(df, 'vol_delta_aligned_str')

    if not groups:
        return None

    # Determine confidence
    min_group = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group)

    # Determine edge
    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    # Add specific recommendation
    if has_edge and 'ALIGNED' in groups and 'MISALIGNED' in groups:
        align_wr = groups['ALIGNED']['win_rate']
        misalign_wr = groups['MISALIGNED']['win_rate']
        if align_wr > misalign_wr:
            recommendation = f"EDGE: Prefer ALIGNED delta. WR: {align_wr:.1f}% vs {misalign_wr:.1f}%"
        else:
            recommendation = f"EDGE: MISALIGNED outperforms. WR: {misalign_wr:.1f}% vs {align_wr:.1f}%"

    baseline = (df['is_winner'].sum() / len(df) * 100) if len(df) > 0 else 0

    return EdgeTestResult(
        indicator="Volume Delta",
        test_name="Delta Alignment",
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


def test_vol_delta_magnitude(df: pd.DataFrame, segment_name: str) -> EdgeTestResult:
    """Test if higher absolute delta correlates with win rate."""
    df = df[df['vol_delta_quintile'].notna()].copy()

    if len(df) < 30:
        return None

    bucket_order = ['Q1_Lowest', 'Q2', 'Q3', 'Q4', 'Q5_Highest']

    # Calculate statistics
    correlation, p_value, effect_size = spearman_monotonic_test(
        df, 'vol_delta_quintile', bucket_order=bucket_order
    )
    groups = calculate_win_rates(df, 'vol_delta_quintile')

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
        indicator="Volume Delta",
        test_name="Delta Magnitude (Quintiles)",
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
# RUN ALL VOLUME DELTA TESTS
# =============================================================================

def run_volume_delta_tests(df: pd.DataFrame) -> List[EdgeTestResult]:
    """Run all volume delta edge tests across all segments."""
    results = []

    # Calculate metrics
    df = calculate_vol_delta_metrics(df)

    # Get segments
    segments = get_segments(df)

    for segment_name, segment_df, category in segments:
        # Recalculate metrics per segment
        segment_df = calculate_vol_delta_metrics(segment_df)

        # Run each test
        result = test_vol_delta_sign(segment_df, segment_name)
        if result:
            results.append(result)

        result = test_vol_delta_alignment(segment_df, segment_name)
        if result:
            results.append(result)

        result = test_vol_delta_magnitude(segment_df, segment_name)
        if result:
            results.append(result)

    return results
