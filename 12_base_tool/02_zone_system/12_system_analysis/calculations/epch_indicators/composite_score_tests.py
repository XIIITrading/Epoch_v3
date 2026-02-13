"""
================================================================================
EPOCH TRADING SYSTEM - EPCH Indicators Edge Analysis
Composite Score Edge Tests
================================================================================

Tests for LONG/SHORT composite scores (0-7):
- Score bucket tests (0-2 LOW, 3-4 MEDIUM, 5-7 HIGH)
- Score monotonic correlation test
- Direction-specific score tests

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
# COMPOSITE SCORE METRIC CALCULATIONS
# =============================================================================

def calculate_composite_score_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate all composite score derived metrics.

    Adds columns:
    - long_score_bucket: LOW (0-2), MEDIUM (3-4), HIGH (5-7)
    - short_score_bucket: LOW (0-2), MEDIUM (3-4), HIGH (5-7)
    - relevant_score: LONG score for LONG trades, SHORT score for SHORT trades
    - relevant_score_bucket: Bucket for relevant score
    """
    df = df.copy()

    # Long score buckets
    def bucket_score(score):
        if pd.isna(score):
            return None
        score = int(score)
        if score <= 2:
            return 'LOW (0-2)'
        elif score <= 4:
            return 'MEDIUM (3-4)'
        else:
            return 'HIGH (5-7)'

    if 'long_score' in df.columns:
        df['long_score_bucket'] = df['long_score'].apply(bucket_score)

    if 'short_score' in df.columns:
        df['short_score_bucket'] = df['short_score'].apply(bucket_score)

    # Relevant score (score that matches trade direction)
    def get_relevant_score(row):
        direction = row.get('direction')
        if direction == 'LONG':
            return row.get('long_score')
        elif direction == 'SHORT':
            return row.get('short_score')
        return None

    df['relevant_score'] = df.apply(get_relevant_score, axis=1)
    df['relevant_score_bucket'] = df['relevant_score'].apply(bucket_score)

    # Opposing score (score opposite to trade direction)
    def get_opposing_score(row):
        direction = row.get('direction')
        if direction == 'LONG':
            return row.get('short_score')
        elif direction == 'SHORT':
            return row.get('long_score')
        return None

    df['opposing_score'] = df.apply(get_opposing_score, axis=1)
    df['opposing_score_bucket'] = df['opposing_score'].apply(bucket_score)

    return df


# =============================================================================
# INDIVIDUAL TESTS
# =============================================================================

def test_long_score_buckets(df: pd.DataFrame, segment_name: str) -> EdgeTestResult:
    """Test if LONG score buckets affect win rate."""
    df = df[df['long_score_bucket'].notna()].copy()

    if len(df) < 30:
        return None

    # Calculate statistics
    chi2, p_value, effect_size = chi_square_test(df, 'long_score_bucket')
    groups = calculate_win_rates(df, 'long_score_bucket')

    if not groups:
        return None

    # Determine confidence
    min_group = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group)

    # Determine edge
    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    baseline = (df['is_winner'].sum() / len(df) * 100) if len(df) > 0 else 0

    return EdgeTestResult(
        indicator="LONG Score",
        test_name="Score Buckets (Low/Med/High)",
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


def test_short_score_buckets(df: pd.DataFrame, segment_name: str) -> EdgeTestResult:
    """Test if SHORT score buckets affect win rate."""
    df = df[df['short_score_bucket'].notna()].copy()

    if len(df) < 30:
        return None

    # Calculate statistics
    chi2, p_value, effect_size = chi_square_test(df, 'short_score_bucket')
    groups = calculate_win_rates(df, 'short_score_bucket')

    if not groups:
        return None

    # Determine confidence
    min_group = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group)

    # Determine edge
    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    baseline = (df['is_winner'].sum() / len(df) * 100) if len(df) > 0 else 0

    return EdgeTestResult(
        indicator="SHORT Score",
        test_name="Score Buckets (Low/Med/High)",
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


def test_relevant_score_buckets(df: pd.DataFrame, segment_name: str) -> EdgeTestResult:
    """Test if direction-relevant score buckets affect win rate."""
    df = df[df['relevant_score_bucket'].notna()].copy()

    if len(df) < 30:
        return None

    # Calculate statistics
    chi2, p_value, effect_size = chi_square_test(df, 'relevant_score_bucket')
    groups = calculate_win_rates(df, 'relevant_score_bucket')

    if not groups:
        return None

    # Determine confidence
    min_group = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group)

    # Determine edge
    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    # Add specific recommendation
    if has_edge:
        bucket_wrs = {k: v['win_rate'] for k, v in groups.items()}
        best_bucket = max(bucket_wrs, key=bucket_wrs.get)
        worst_bucket = min(bucket_wrs, key=bucket_wrs.get)
        recommendation = f"EDGE: {best_bucket} outperforms ({bucket_wrs[best_bucket]:.1f}% vs {bucket_wrs[worst_bucket]:.1f}%)"

    baseline = (df['is_winner'].sum() / len(df) * 100) if len(df) > 0 else 0

    return EdgeTestResult(
        indicator="Relevant Score",
        test_name="Direction-Matched Score Buckets",
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


def test_long_score_monotonic(df: pd.DataFrame, segment_name: str) -> EdgeTestResult:
    """Test if higher LONG scores correlate with higher win rates."""
    df = df[df['long_score'].notna()].copy()

    if len(df) < 30:
        return None

    bucket_order = ['LOW (0-2)', 'MEDIUM (3-4)', 'HIGH (5-7)']

    # Calculate statistics
    correlation, p_value, effect_size = spearman_monotonic_test(
        df, 'long_score_bucket', bucket_order=bucket_order
    )
    groups = calculate_win_rates(df, 'long_score_bucket')

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
        recommendation = f"EDGE: {direction} LONG score (corr={correlation:.2f}, effect={effect_size:.1f}pp)"

    baseline = (df['is_winner'].sum() / len(df) * 100) if len(df) > 0 else 0

    return EdgeTestResult(
        indicator="LONG Score",
        test_name="Score Monotonic Trend",
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


def test_short_score_monotonic(df: pd.DataFrame, segment_name: str) -> EdgeTestResult:
    """Test if higher SHORT scores correlate with higher win rates."""
    df = df[df['short_score'].notna()].copy()

    if len(df) < 30:
        return None

    bucket_order = ['LOW (0-2)', 'MEDIUM (3-4)', 'HIGH (5-7)']

    # Calculate statistics
    correlation, p_value, effect_size = spearman_monotonic_test(
        df, 'short_score_bucket', bucket_order=bucket_order
    )
    groups = calculate_win_rates(df, 'short_score_bucket')

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
        recommendation = f"EDGE: {direction} SHORT score (corr={correlation:.2f}, effect={effect_size:.1f}pp)"

    baseline = (df['is_winner'].sum() / len(df) * 100) if len(df) > 0 else 0

    return EdgeTestResult(
        indicator="SHORT Score",
        test_name="Score Monotonic Trend",
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


def test_relevant_score_monotonic(df: pd.DataFrame, segment_name: str) -> EdgeTestResult:
    """Test if higher direction-relevant scores correlate with win rates."""
    df = df[df['relevant_score'].notna()].copy()

    if len(df) < 30:
        return None

    bucket_order = ['LOW (0-2)', 'MEDIUM (3-4)', 'HIGH (5-7)']

    # Calculate statistics
    correlation, p_value, effect_size = spearman_monotonic_test(
        df, 'relevant_score_bucket', bucket_order=bucket_order
    )
    groups = calculate_win_rates(df, 'relevant_score_bucket')

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
        recommendation = f"EDGE: {direction} direction-matched score (corr={correlation:.2f}, effect={effect_size:.1f}pp)"

    baseline = (df['is_winner'].sum() / len(df) * 100) if len(df) > 0 else 0

    return EdgeTestResult(
        indicator="Relevant Score",
        test_name="Direction-Matched Monotonic Trend",
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
# RUN ALL COMPOSITE SCORE TESTS
# =============================================================================

def run_composite_score_tests(df: pd.DataFrame) -> List[EdgeTestResult]:
    """Run all composite score edge tests across all segments."""
    results = []

    # Calculate metrics
    df = calculate_composite_score_metrics(df)

    # Get segments
    segments = get_segments(df)

    for segment_name, segment_df, category in segments:
        # Recalculate metrics per segment
        segment_df = calculate_composite_score_metrics(segment_df)

        # Run LONG score tests
        result = test_long_score_buckets(segment_df, segment_name)
        if result:
            results.append(result)

        result = test_long_score_monotonic(segment_df, segment_name)
        if result:
            results.append(result)

        # Run SHORT score tests
        result = test_short_score_buckets(segment_df, segment_name)
        if result:
            results.append(result)

        result = test_short_score_monotonic(segment_df, segment_name)
        if result:
            results.append(result)

        # Run relevant score tests (direction-matched)
        result = test_relevant_score_buckets(segment_df, segment_name)
        if result:
            results.append(result)

        result = test_relevant_score_monotonic(segment_df, segment_name)
        if result:
            results.append(result)

    return results
