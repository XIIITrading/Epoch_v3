"""
CALC-011: VWAP Edge Analysis

Tests VWAP indicator for statistical edge in trade outcomes.
Analyzes: VWAP side, alignment, and distance relationships.

Usage:
    python -m calculations.indicator_edge.vwap_edge
    python -m calculations.indicator_edge.vwap_edge --models EPCH01,EPCH03
    python -m calculations.indicator_edge.vwap_edge --direction LONG
    python -m calculations.indicator_edge.vwap_edge --output results/vwap_2025.md
"""

import argparse
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from datetime import datetime

from .base_tester import (
    EdgeTestResult,
    fetch_entry_data,
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
# VWAP METRIC CALCULATIONS
# ============================================================================

def calculate_vwap_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add VWAP-derived columns for edge testing.

    Adds:
        vwap_side: 'ABOVE' or 'BELOW' (uses existing vwap_position if available)
        vwap_distance_pct: (price - vwap) / vwap * 100
        vwap_distance_abs: Absolute distance percentage
        vwap_aligned: Boolean - True if direction matches VWAP position
        vwap_aligned_str: 'ALIGNED' or 'MISALIGNED' for grouping
        vwap_distance_quintile: Q1 (closest) to Q5 (farthest)
    """
    df = df.copy()

    # Use existing vwap_position if available, otherwise calculate
    # Note: We treat AT as ABOVE for simplicity (very rare case)
    if 'vwap_position' in df.columns and df['vwap_position'].notna().all():
        # Map AT to ABOVE for binary analysis
        df['vwap_side'] = df['vwap_position'].replace('AT', 'ABOVE')
    else:
        df['vwap_side'] = np.where(df['entry_price'] >= df['vwap'], 'ABOVE', 'BELOW')

    # Distance calculations
    df['vwap_distance_pct'] = (df['entry_price'] - df['vwap']) / df['vwap'] * 100
    df['vwap_distance_abs'] = df['vwap_distance_pct'].abs()

    # Alignment: LONG should be ABOVE, SHORT should be BELOW
    df['vwap_aligned'] = (
        ((df['direction'] == 'LONG') & (df['vwap_side'] == 'ABOVE')) |
        ((df['direction'] == 'SHORT') & (df['vwap_side'] == 'BELOW'))
    )
    df['vwap_aligned_str'] = df['vwap_aligned'].map({True: 'ALIGNED', False: 'MISALIGNED'})

    # Distance quintiles (Q1 = closest to VWAP, Q5 = farthest)
    try:
        df['vwap_distance_quintile'] = pd.qcut(
            df['vwap_distance_abs'],
            q=5,
            labels=['Q1_Closest', 'Q2', 'Q3', 'Q4', 'Q5_Farthest'],
            duplicates='drop'
        )
    except ValueError:
        # Not enough unique values for 5 quintiles
        try:
            df['vwap_distance_quintile'] = pd.qcut(
                df['vwap_distance_abs'],
                q=3,
                labels=['Q1_Close', 'Q2_Mid', 'Q3_Far'],
                duplicates='drop'
            )
        except ValueError:
            # Fallback - just use median split
            median = df['vwap_distance_abs'].median()
            df['vwap_distance_quintile'] = np.where(
                df['vwap_distance_abs'] <= median, 'CLOSE', 'FAR'
            )

    return df


# ============================================================================
# INDIVIDUAL EDGE TESTS
# ============================================================================

def test_vwap_side(df: pd.DataFrame, segment: str = "ALL") -> EdgeTestResult:
    """
    Test: Does being ABOVE vs BELOW VWAP affect win rate?

    Hypothesis: VWAP side alone may indicate market bias.
    """
    baseline_wr = df['is_winner'].mean() * 100
    groups = calculate_win_rates(df, 'vwap_side')

    chi2, p_value, effect_size = chi_square_test(df, 'vwap_side')

    min_group_size = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group_size)

    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    return EdgeTestResult(
        indicator="VWAP",
        test_name="VWAP Side (Above/Below)",
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


def test_vwap_alignment(df: pd.DataFrame, segment: str = "ALL") -> EdgeTestResult:
    """
    Test: Does VWAP alignment with trade direction affect win rate?

    Hypothesis: LONG trades should perform better ABOVE VWAP,
                SHORT trades should perform better BELOW VWAP.
    """
    baseline_wr = df['is_winner'].mean() * 100
    groups = calculate_win_rates(df, 'vwap_aligned_str')

    chi2, p_value, effect_size = chi_square_test(df, 'vwap_aligned_str')

    min_group_size = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group_size)

    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    return EdgeTestResult(
        indicator="VWAP",
        test_name="VWAP Alignment",
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


def test_vwap_distance(df: pd.DataFrame, segment: str = "ALL") -> EdgeTestResult:
    """
    Test: Does distance from VWAP show monotonic relationship with win rate?

    Hypothesis: There may be an optimal distance from VWAP for entries.
    """
    baseline_wr = df['is_winner'].mean() * 100

    quintile_col = 'vwap_distance_quintile'
    groups = calculate_win_rates(df, quintile_col)

    # Define order for quintiles
    quintile_order = ['Q1_Closest', 'Q2', 'Q3', 'Q4', 'Q5_Farthest']
    if 'Q1_Close' in groups:  # 3-bucket fallback
        quintile_order = ['Q1_Close', 'Q2_Mid', 'Q3_Far']
    elif 'CLOSE' in groups:  # 2-bucket fallback
        quintile_order = ['CLOSE', 'FAR']

    correlation, p_value, effect_size = spearman_monotonic_test(
        df, quintile_col, bucket_order=quintile_order
    )

    min_group_size = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group_size)

    # For monotonic tests, use p < 0.10 as threshold (less strict)
    has_edge, recommendation = determine_edge(p_value, effect_size, confidence, p_threshold=0.10)

    if has_edge:
        direction = "farther" if correlation > 0 else "closer"
        recommendation = f"EDGE DETECTED - {direction} from VWAP correlates with higher win rate (r={correlation:.3f})"

    return EdgeTestResult(
        indicator="VWAP",
        test_name="VWAP Distance (Quintiles)",
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
    Run complete VWAP edge analysis across all segments.

    Segments tested:
    1. ALL - All trades combined
    2. CONTINUATION - EPCH01 + EPCH03
    3. REJECTION - EPCH02 + EPCH04
    4. LONG - Long trades only
    5. SHORT - Short trades only

    Returns: (list of EdgeTestResults, metadata dict)
    """
    # Fetch data
    print("Fetching data from database...")
    df = fetch_entry_data(
        models=models,
        directions=directions,
        date_from=date_from,
        date_to=date_to,
        stop_type=stop_type
    )

    if df.empty:
        raise ValueError("No data returned from database. Check filters.")

    # Calculate VWAP metrics
    print(f"Calculating VWAP metrics for {len(df):,} trades...")
    df = calculate_vwap_metrics(df)

    # Build metadata
    metadata = {
        'indicator': 'VWAP',
        'total_trades': len(df),
        'date_range': f"{df['date'].min()} to {df['date'].max()}",
        'baseline_win_rate': df['is_winner'].mean() * 100,
        'stop_type': stop_type,
        'models_filter': models,
        'directions_filter': directions
    }

    results = []

    # Define segments to test
    segments = [
        ("ALL", df),
        ("CONTINUATION", df[df['model'].isin(['EPCH01', 'EPCH1', 'EPCH03', 'EPCH3'])]),
        ("REJECTION", df[df['model'].isin(['EPCH02', 'EPCH2', 'EPCH04', 'EPCH4'])]),
        ("LONG", df[df['direction'] == 'LONG']),
        ("SHORT", df[df['direction'] == 'SHORT'])
    ]

    # Run tests for each segment
    for segment_name, segment_df in segments:
        if len(segment_df) < 30:
            print(f"  Skipping {segment_name} - insufficient data ({len(segment_df)} trades)")
            continue

        print(f"  Testing {segment_name} ({len(segment_df):,} trades)...")

        # Test 1: VWAP Side
        results.append(test_vwap_side(segment_df, segment_name))

        # Test 2: VWAP Alignment
        results.append(test_vwap_alignment(segment_df, segment_name))

        # Test 3: VWAP Distance
        results.append(test_vwap_distance(segment_df, segment_name))

    return results, metadata


# ============================================================================
# CLI EXECUTION
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="CALC-011: VWAP Edge Analysis - Test VWAP indicator for statistical edge"
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
    print("CALC-011: VWAP EDGE ANALYSIS")
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
        filename = f"vwap_edge_{timestamp}.md"
        filepath = save_report(report, filename)
        print(f"\nReport saved to: {filepath}")

    # Return results for programmatic use
    return results, metadata


if __name__ == "__main__":
    main()
