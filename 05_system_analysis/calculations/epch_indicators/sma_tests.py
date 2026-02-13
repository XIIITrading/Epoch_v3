"""
================================================================================
EPOCH TRADING SYSTEM - EPCH Indicators Edge Analysis
SMA Configuration Edge Tests
================================================================================

Tests for SMA indicators (sma9, sma21, sma_spread):
- Spread direction test (BULLISH vs BEARISH)
- Spread alignment test (aligned with trade direction)
- Spread magnitude quintiles test
- Price position test (ABOVE_BOTH, BETWEEN, BELOW_BOTH)

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
# SMA METRIC CALCULATIONS
# =============================================================================

def calculate_sma_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate all SMA derived metrics.

    Adds columns:
    - sma_spread_direction: BULLISH (SMA9 > SMA21) or BEARISH
    - sma_spread_aligned: Boolean (aligned with direction)
    - sma_spread_aligned_str: ALIGNED or MISALIGNED
    - sma_spread_abs: Absolute spread value
    - sma_spread_quintile: Q1_Lowest to Q5_Highest
    - price_vs_sma9: ABOVE or BELOW
    - price_vs_sma21: ABOVE or BELOW
    - price_vs_both: ABOVE_BOTH, BETWEEN, BELOW_BOTH
    - price_sma_aligned_str: ALIGNED or NOT_ALIGNED
    """
    df = df.copy()

    if 'sma9' not in df.columns or 'sma21' not in df.columns:
        return df

    # Calculate spread if not present
    if 'sma_spread' not in df.columns:
        df['sma_spread'] = df['sma9'] - df['sma21']

    # Spread direction
    df['sma_spread_direction'] = df['sma_spread'].apply(
        lambda x: 'BULLISH' if pd.notna(x) and x > 0 else (
            'BEARISH' if pd.notna(x) and x < 0 else None
        )
    )

    # Alignment with trade direction
    # LONG: BULLISH spread = ALIGNED
    # SHORT: BEARISH spread = ALIGNED
    def check_alignment(row):
        if pd.isna(row.get('sma_spread')) or pd.isna(row.get('direction')):
            return None
        if row['direction'] == 'LONG':
            return row['sma_spread'] > 0
        elif row['direction'] == 'SHORT':
            return row['sma_spread'] < 0
        return None

    df['sma_spread_aligned'] = df.apply(check_alignment, axis=1)
    df['sma_spread_aligned_str'] = df['sma_spread_aligned'].apply(
        lambda x: 'ALIGNED' if x is True else ('MISALIGNED' if x is False else None)
    )

    # Absolute spread
    df['sma_spread_abs'] = df['sma_spread'].abs()

    # Spread magnitude quintiles (absolute)
    df = create_quintile_buckets(
        df,
        'sma_spread_abs',
        'sma_spread_quintile',
        ['Q1_Lowest', 'Q2', 'Q3', 'Q4', 'Q5_Highest']
    )

    # Price position relative to SMAs
    def price_vs_sma(row, sma_col):
        if pd.isna(row.get('bar_close')) or pd.isna(row.get(sma_col)):
            return None
        return 'ABOVE' if row['bar_close'] > row[sma_col] else 'BELOW'

    df['price_vs_sma9'] = df.apply(lambda r: price_vs_sma(r, 'sma9'), axis=1)
    df['price_vs_sma21'] = df.apply(lambda r: price_vs_sma(r, 'sma21'), axis=1)

    # Combined position
    def combined_position(row):
        vs9 = row.get('price_vs_sma9')
        vs21 = row.get('price_vs_sma21')
        if pd.isna(vs9) or pd.isna(vs21):
            return None
        if vs9 == 'ABOVE' and vs21 == 'ABOVE':
            return 'ABOVE_BOTH'
        elif vs9 == 'BELOW' and vs21 == 'BELOW':
            return 'BELOW_BOTH'
        else:
            return 'BETWEEN'

    df['price_vs_both'] = df.apply(combined_position, axis=1)

    # Price/SMA alignment with direction
    # LONG: price ABOVE_BOTH = ALIGNED
    # SHORT: price BELOW_BOTH = ALIGNED
    def check_price_alignment(row):
        pos = row.get('price_vs_both')
        direction = row.get('direction')
        if pd.isna(pos) or pd.isna(direction):
            return None
        if direction == 'LONG':
            return pos == 'ABOVE_BOTH'
        elif direction == 'SHORT':
            return pos == 'BELOW_BOTH'
        return None

    df['price_sma_aligned'] = df.apply(check_price_alignment, axis=1)
    df['price_sma_aligned_str'] = df['price_sma_aligned'].apply(
        lambda x: 'ALIGNED' if x is True else ('NOT_ALIGNED' if x is False else None)
    )

    return df


# =============================================================================
# INDIVIDUAL TESTS
# =============================================================================

def test_sma_spread_direction(df: pd.DataFrame, segment_name: str) -> EdgeTestResult:
    """Test if SMA spread direction affects win rate."""
    df = df[df['sma_spread_direction'].notna()].copy()

    if len(df) < 30:
        return None

    # Calculate statistics
    chi2, p_value, effect_size = chi_square_test(df, 'sma_spread_direction')
    groups = calculate_win_rates(df, 'sma_spread_direction')

    if not groups:
        return None

    # Determine confidence
    min_group = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group)

    # Determine edge
    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    baseline = (df['is_winner'].sum() / len(df) * 100) if len(df) > 0 else 0

    return EdgeTestResult(
        indicator="SMA Config",
        test_name="Spread Direction (Bull/Bear)",
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


def test_sma_spread_alignment(df: pd.DataFrame, segment_name: str) -> EdgeTestResult:
    """Test if SMA spread aligned with direction improves win rate."""
    df = df[df['sma_spread_aligned_str'].notna()].copy()

    if len(df) < 30:
        return None

    # Calculate statistics
    chi2, p_value, effect_size = chi_square_test(df, 'sma_spread_aligned_str')
    groups = calculate_win_rates(df, 'sma_spread_aligned_str')

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
            recommendation = f"EDGE: Prefer ALIGNED SMA spread. WR: {align_wr:.1f}% vs {misalign_wr:.1f}%"
        else:
            recommendation = f"EDGE: MISALIGNED outperforms. WR: {misalign_wr:.1f}% vs {align_wr:.1f}%"

    baseline = (df['is_winner'].sum() / len(df) * 100) if len(df) > 0 else 0

    return EdgeTestResult(
        indicator="SMA Config",
        test_name="Spread Alignment",
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


def test_sma_spread_magnitude(df: pd.DataFrame, segment_name: str) -> EdgeTestResult:
    """Test if wider SMA spread correlates with win rate."""
    df = df[df['sma_spread_quintile'].notna()].copy()

    if len(df) < 30:
        return None

    bucket_order = ['Q1_Lowest', 'Q2', 'Q3', 'Q4', 'Q5_Highest']

    # Calculate statistics
    correlation, p_value, effect_size = spearman_monotonic_test(
        df, 'sma_spread_quintile', bucket_order=bucket_order
    )
    groups = calculate_win_rates(df, 'sma_spread_quintile')

    if not groups:
        return None

    # Determine confidence
    existing_groups = {k: v for k, v in groups.items() if k in bucket_order}
    min_group = min(g['trades'] for g in existing_groups.values()) if existing_groups else 0
    confidence = get_confidence_level(min_group)

    # Determine edge
    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    if has_edge:
        direction = "WIDER = BETTER" if correlation > 0 else "TIGHTER = BETTER"
        recommendation = f"EDGE: {direction} (corr={correlation:.2f}, effect={effect_size:.1f}pp)"

    baseline = (df['is_winner'].sum() / len(df) * 100) if len(df) > 0 else 0

    return EdgeTestResult(
        indicator="SMA Config",
        test_name="Spread Magnitude (Quintiles)",
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


def test_price_sma_position(df: pd.DataFrame, segment_name: str) -> EdgeTestResult:
    """Test if price position relative to SMAs affects win rate."""
    df = df[df['price_vs_both'].notna()].copy()

    if len(df) < 30:
        return None

    # Calculate statistics
    chi2, p_value, effect_size = chi_square_test(df, 'price_vs_both')
    groups = calculate_win_rates(df, 'price_vs_both')

    if not groups:
        return None

    # Determine confidence
    min_group = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group)

    # Determine edge
    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    baseline = (df['is_winner'].sum() / len(df) * 100) if len(df) > 0 else 0

    return EdgeTestResult(
        indicator="SMA Config",
        test_name="Price vs SMAs Position",
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


def test_price_sma_alignment(df: pd.DataFrame, segment_name: str) -> EdgeTestResult:
    """Test if price/SMA alignment with direction improves win rate."""
    df = df[df['price_sma_aligned_str'].notna()].copy()

    if len(df) < 30:
        return None

    # Calculate statistics
    chi2, p_value, effect_size = chi_square_test(df, 'price_sma_aligned_str')
    groups = calculate_win_rates(df, 'price_sma_aligned_str')

    if not groups:
        return None

    # Determine confidence
    min_group = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group)

    # Determine edge
    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    baseline = (df['is_winner'].sum() / len(df) * 100) if len(df) > 0 else 0

    return EdgeTestResult(
        indicator="SMA Config",
        test_name="Price/SMA Alignment",
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


# =============================================================================
# RUN ALL SMA TESTS
# =============================================================================

def run_sma_tests(df: pd.DataFrame) -> List[EdgeTestResult]:
    """Run all SMA edge tests across all segments."""
    results = []

    # Calculate metrics
    df = calculate_sma_metrics(df)

    # Get segments
    segments = get_segments(df)

    for segment_name, segment_df, category in segments:
        # Recalculate metrics per segment
        segment_df = calculate_sma_metrics(segment_df)

        # Run each test
        result = test_sma_spread_direction(segment_df, segment_name)
        if result:
            results.append(result)

        result = test_sma_spread_alignment(segment_df, segment_name)
        if result:
            results.append(result)

        result = test_sma_spread_magnitude(segment_df, segment_name)
        if result:
            results.append(result)

        result = test_price_sma_position(segment_df, segment_name)
        if result:
            results.append(result)

        result = test_price_sma_alignment(segment_df, segment_name)
        if result:
            results.append(result)

    return results
