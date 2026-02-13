"""
================================================================================
EPOCH TRADING SYSTEM - EPCH Indicators Edge Analysis
H1 Structure Edge Tests
================================================================================

Tests for h1_structure indicator:
- State test (BULL vs BEAR vs NEUTRAL distribution)
- Alignment test (structure aligned with trade direction)
- Neutral edge test (NEUTRAL vs non-NEUTRAL)

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
    get_confidence_level,
    determine_edge
)


# =============================================================================
# STRUCTURE METRIC CALCULATIONS
# =============================================================================

def calculate_structure_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate all H1 structure derived metrics.

    Adds columns:
    - h1_structure_aligned: Boolean (aligned with direction)
    - h1_structure_aligned_str: ALIGNED or MISALIGNED
    - h1_structure_neutral: NEUTRAL or NOT_NEUTRAL
    """
    df = df.copy()

    if 'h1_structure' not in df.columns:
        return df

    # Clean structure values (uppercase, strip whitespace)
    df['h1_structure'] = df['h1_structure'].apply(
        lambda x: x.strip().upper() if pd.notna(x) and isinstance(x, str) else x
    )

    # Alignment with trade direction
    # LONG: BULL structure = ALIGNED
    # SHORT: BEAR structure = ALIGNED
    # NEUTRAL is always MISALIGNED (no directional support)
    def check_alignment(row):
        structure = row.get('h1_structure')
        direction = row.get('direction')
        if pd.isna(structure) or pd.isna(direction):
            return None
        if direction == 'LONG':
            return structure == 'BULL'
        elif direction == 'SHORT':
            return structure == 'BEAR'
        return None

    df['h1_structure_aligned'] = df.apply(check_alignment, axis=1)
    df['h1_structure_aligned_str'] = df['h1_structure_aligned'].apply(
        lambda x: 'ALIGNED' if x is True else ('MISALIGNED' if x is False else None)
    )

    # Neutral vs non-neutral
    df['h1_structure_neutral'] = df['h1_structure'].apply(
        lambda x: 'NEUTRAL' if x == 'NEUTRAL' else (
            'NOT_NEUTRAL' if pd.notna(x) else None
        )
    )

    return df


# =============================================================================
# INDIVIDUAL TESTS
# =============================================================================

def test_h1_structure_state(df: pd.DataFrame, segment_name: str) -> EdgeTestResult:
    """Test if H1 structure state (BULL/BEAR/NEUTRAL) affects win rate."""
    df = df[df['h1_structure'].notna()].copy()

    if len(df) < 30:
        return None

    # Calculate statistics
    chi2, p_value, effect_size = chi_square_test(df, 'h1_structure')
    groups = calculate_win_rates(df, 'h1_structure')

    if not groups:
        return None

    # Determine confidence
    min_group = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group)

    # Determine edge
    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    baseline = (df['is_winner'].sum() / len(df) * 100) if len(df) > 0 else 0

    return EdgeTestResult(
        indicator="H1 Structure",
        test_name="Structure State (Bull/Bear/Neutral)",
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


def test_h1_structure_alignment(df: pd.DataFrame, segment_name: str) -> EdgeTestResult:
    """Test if H1 structure aligned with direction improves win rate."""
    df = df[df['h1_structure_aligned_str'].notna()].copy()

    if len(df) < 30:
        return None

    # Calculate statistics
    chi2, p_value, effect_size = chi_square_test(df, 'h1_structure_aligned_str')
    groups = calculate_win_rates(df, 'h1_structure_aligned_str')

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
            recommendation = f"EDGE: Prefer ALIGNED H1 structure. WR: {align_wr:.1f}% vs {misalign_wr:.1f}%"
        else:
            recommendation = f"EDGE: Counter-trend structure better. WR: {misalign_wr:.1f}% vs {align_wr:.1f}%"

    baseline = (df['is_winner'].sum() / len(df) * 100) if len(df) > 0 else 0

    return EdgeTestResult(
        indicator="H1 Structure",
        test_name="Structure Alignment",
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


def test_h1_neutral_edge(df: pd.DataFrame, segment_name: str) -> EdgeTestResult:
    """Test if NEUTRAL structure performs differently than directional."""
    df = df[df['h1_structure_neutral'].notna()].copy()

    if len(df) < 30:
        return None

    # Calculate statistics
    chi2, p_value, effect_size = chi_square_test(df, 'h1_structure_neutral')
    groups = calculate_win_rates(df, 'h1_structure_neutral')

    if not groups:
        return None

    # Determine confidence
    min_group = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group)

    # Determine edge
    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    # Add specific recommendation per EPCH spec
    if has_edge and 'NEUTRAL' in groups and 'NOT_NEUTRAL' in groups:
        neutral_wr = groups['NEUTRAL']['win_rate']
        not_neutral_wr = groups['NOT_NEUTRAL']['win_rate']
        if neutral_wr < not_neutral_wr:
            recommendation = f"EDGE: Avoid NEUTRAL structure. WR: {neutral_wr:.1f}% vs {not_neutral_wr:.1f}%"
        else:
            recommendation = f"EDGE: NEUTRAL outperforms. WR: {neutral_wr:.1f}% vs {not_neutral_wr:.1f}%"

    baseline = (df['is_winner'].sum() / len(df) * 100) if len(df) > 0 else 0

    return EdgeTestResult(
        indicator="H1 Structure",
        test_name="Neutral vs Directional",
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
# RUN ALL STRUCTURE TESTS
# =============================================================================

def run_structure_tests(df: pd.DataFrame) -> List[EdgeTestResult]:
    """Run all H1 structure edge tests across all segments."""
    results = []

    # Calculate metrics
    df = calculate_structure_metrics(df)

    # Get segments
    segments = get_segments(df)

    for segment_name, segment_df, category in segments:
        # Recalculate metrics per segment
        segment_df = calculate_structure_metrics(segment_df)

        # Run each test
        result = test_h1_structure_state(segment_df, segment_name)
        if result:
            results.append(result)

        result = test_h1_structure_alignment(segment_df, segment_name)
        if result:
            results.append(result)

        result = test_h1_neutral_edge(segment_df, segment_name)
        if result:
            results.append(result)

    return results
