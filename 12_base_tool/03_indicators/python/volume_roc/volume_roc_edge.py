"""
CALC-011: Volume ROC Edge Analysis

Tests Volume ROC indicator for statistical edge in trade outcomes.
Uses vol_roc from prior M1 bar (before entry at S15) to avoid look-ahead bias.

Analyzes:
- Vol ROC Level: ABOVE vs BELOW baseline (0%)
- Vol ROC Magnitude: Quintile analysis of absolute ROC values
- Vol ROC Threshold: Tests at +10%, +20%, +30% thresholds

Usage:
    python -m volume_roc.volume_roc_edge
    python -m volume_roc.volume_roc_edge --models EPCH01,EPCH03
    python -m volume_roc.volume_roc_edge --direction LONG
    python -m volume_roc.volume_roc_edge --output results/vol_roc_2026.md
"""

import argparse
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from datetime import datetime

from .base_tester import (
    EdgeTestResult,
    fetch_volume_roc_data,
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
# VOLUME ROC METRIC CALCULATIONS
# ============================================================================

def calculate_vol_roc_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add Volume ROC-derived columns for edge testing.

    Adds:
        vol_roc_level: 'ABOVE' or 'BELOW' (relative to 0% baseline)
        vol_roc_abs: Absolute value of ROC
        vol_roc_quintile: Q1 (lowest abs) to Q5 (highest abs)
        vol_roc_threshold_10: 'ABOVE_10%' or 'BELOW_10%'
        vol_roc_threshold_20: 'ABOVE_20%' or 'BELOW_20%'
        vol_roc_threshold_30: 'ABOVE_30%' or 'BELOW_30%'
    """
    df = df.copy()

    # Level classification (above or below 0%)
    df['vol_roc_level'] = np.where(df['vol_roc'] >= 0, 'ABOVE', 'BELOW')

    # Absolute value for magnitude analysis
    df['vol_roc_abs'] = df['vol_roc'].abs()

    # Magnitude quintiles (Q1 = smallest absolute ROC, Q5 = largest)
    try:
        df['vol_roc_quintile'] = pd.qcut(
            df['vol_roc_abs'],
            q=5,
            labels=['Q1_Smallest', 'Q2', 'Q3', 'Q4', 'Q5_Largest'],
            duplicates='drop'
        )
    except ValueError:
        # Not enough unique values for 5 quintiles
        try:
            df['vol_roc_quintile'] = pd.qcut(
                df['vol_roc_abs'],
                q=3,
                labels=['Q1_Small', 'Q2_Mid', 'Q3_Large'],
                duplicates='drop'
            )
        except ValueError:
            # Fallback - just use median split
            median = df['vol_roc_abs'].median()
            df['vol_roc_quintile'] = np.where(
                df['vol_roc_abs'] <= median, 'SMALL', 'LARGE'
            )

    # Threshold classifications (10%, 20%, 30%)
    # Note: vol_roc is stored as percentage (e.g., 15.5 means 15.5%)
    df['vol_roc_threshold_10'] = np.where(df['vol_roc'] >= 10, 'ABOVE_10%', 'BELOW_10%')
    df['vol_roc_threshold_20'] = np.where(df['vol_roc'] >= 20, 'ABOVE_20%', 'BELOW_20%')
    df['vol_roc_threshold_30'] = np.where(df['vol_roc'] >= 30, 'ABOVE_30%', 'BELOW_30%')

    # Signed quintiles for directional analysis (most negative to most positive)
    try:
        df['vol_roc_signed_quintile'] = pd.qcut(
            df['vol_roc'],
            q=5,
            labels=['Q1_MostNeg', 'Q2_Neg', 'Q3_Neutral', 'Q4_Pos', 'Q5_MostPos'],
            duplicates='drop'
        )
    except ValueError:
        try:
            df['vol_roc_signed_quintile'] = pd.qcut(
                df['vol_roc'],
                q=3,
                labels=['NEGATIVE', 'NEUTRAL', 'POSITIVE'],
                duplicates='drop'
            )
        except ValueError:
            df['vol_roc_signed_quintile'] = df['vol_roc_level']

    return df


# ============================================================================
# INDIVIDUAL EDGE TESTS
# ============================================================================

def test_vol_roc_level(df: pd.DataFrame, segment: str = "ALL") -> EdgeTestResult:
    """
    Test: Does ABOVE vs BELOW 0% volume ROC affect win rate?

    Hypothesis: Volume above baseline (ROC > 0%) may indicate stronger
                conviction/momentum and better trade outcomes.
    """
    baseline_wr = df['is_winner'].mean() * 100
    groups = calculate_win_rates(df, 'vol_roc_level')

    chi2, p_value, effect_size = chi_square_test(df, 'vol_roc_level')

    min_group_size = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group_size)

    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    return EdgeTestResult(
        indicator="Volume ROC",
        test_name="Vol ROC Level (Above/Below 0%)",
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


def test_vol_roc_magnitude(df: pd.DataFrame, segment: str = "ALL") -> EdgeTestResult:
    """
    Test: Does absolute magnitude of volume ROC show monotonic relationship with win rate?

    Hypothesis: Higher absolute ROC may indicate stronger volume conviction.
    """
    baseline_wr = df['is_winner'].mean() * 100

    quintile_col = 'vol_roc_quintile'
    groups = calculate_win_rates(df, quintile_col)

    # Define order for quintiles
    quintile_order = ['Q1_Smallest', 'Q2', 'Q3', 'Q4', 'Q5_Largest']
    if 'Q1_Small' in groups:  # 3-bucket fallback
        quintile_order = ['Q1_Small', 'Q2_Mid', 'Q3_Large']
    elif 'SMALL' in groups:  # 2-bucket fallback
        quintile_order = ['SMALL', 'LARGE']

    correlation, p_value, effect_size = spearman_monotonic_test(
        df, quintile_col, bucket_order=quintile_order
    )

    min_group_size = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group_size)

    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    if has_edge:
        direction = "higher" if correlation > 0 else "lower"
        recommendation = f"EDGE DETECTED - {direction} magnitude correlates with higher win rate (r={correlation:.3f})"

    return EdgeTestResult(
        indicator="Volume ROC",
        test_name="Vol ROC Magnitude (Quintiles)",
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


def test_vol_roc_threshold(
    df: pd.DataFrame,
    threshold: int,
    segment: str = "ALL"
) -> EdgeTestResult:
    """
    Test: Does volume ROC above a specific threshold affect win rate?

    Hypothesis: Volume significantly above baseline may indicate stronger momentum.
    """
    baseline_wr = df['is_winner'].mean() * 100

    threshold_col = f'vol_roc_threshold_{threshold}'
    groups = calculate_win_rates(df, threshold_col)

    chi2, p_value, effect_size = chi_square_test(df, threshold_col)

    min_group_size = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group_size)

    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    return EdgeTestResult(
        indicator="Volume ROC",
        test_name=f"Vol ROC Threshold ({threshold}%)",
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


def test_vol_roc_signed_quintiles(df: pd.DataFrame, segment: str = "ALL") -> EdgeTestResult:
    """
    Test: Does the signed (directional) volume ROC show monotonic relationship with win rate?

    Hypothesis: Win rate may vary across the spectrum from most negative to most positive ROC.
    """
    baseline_wr = df['is_winner'].mean() * 100

    quintile_col = 'vol_roc_signed_quintile'
    groups = calculate_win_rates(df, quintile_col)

    # Define order for quintiles
    quintile_order = ['Q1_MostNeg', 'Q2_Neg', 'Q3_Neutral', 'Q4_Pos', 'Q5_MostPos']
    if 'NEGATIVE' in groups:  # 3-bucket fallback
        quintile_order = ['NEGATIVE', 'NEUTRAL', 'POSITIVE']
    elif 'ABOVE' in groups and 'BELOW' in groups and len(groups) == 2:
        quintile_order = ['BELOW', 'ABOVE']

    correlation, p_value, effect_size = spearman_monotonic_test(
        df, quintile_col, bucket_order=quintile_order
    )

    min_group_size = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group_size)

    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    if has_edge:
        direction = "higher" if correlation > 0 else "lower"
        recommendation = f"EDGE DETECTED - {direction} ROC correlates with higher win rate (r={correlation:.3f})"

    return EdgeTestResult(
        indicator="Volume ROC",
        test_name="Vol ROC Signed (Direction+Magnitude)",
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
    Run complete Volume ROC edge analysis across all segments.

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
    print("Fetching data from database (using prior M1 bar vol_roc)...")
    df = fetch_volume_roc_data(
        models=models,
        directions=directions,
        date_from=date_from,
        date_to=date_to,
        stop_type=stop_type
    )

    if df.empty:
        raise ValueError("No data returned from database. Check filters or m1_indicator_bars data.")

    # Calculate Volume ROC metrics
    print(f"Calculating Volume ROC metrics for {len(df):,} trades...")
    df = calculate_vol_roc_metrics(df)

    # Print summary stats
    print(f"\nVolume ROC Summary:")
    print(f"  Mean: {df['vol_roc'].mean():.1f}%")
    print(f"  Median: {df['vol_roc'].median():.1f}%")
    print(f"  Std Dev: {df['vol_roc'].std():.1f}%")
    print(f"  Min: {df['vol_roc'].min():.1f}%")
    print(f"  Max: {df['vol_roc'].max():.1f}%")
    print(f"  Above 0%: {(df['vol_roc'] >= 0).sum():,} ({(df['vol_roc'] >= 0).mean()*100:.1f}%)")
    print(f"  Below 0%: {(df['vol_roc'] < 0).sum():,} ({(df['vol_roc'] < 0).mean()*100:.1f}%)")
    print(f"  Above 10%: {(df['vol_roc'] >= 10).sum():,} ({(df['vol_roc'] >= 10).mean()*100:.1f}%)")
    print(f"  Above 20%: {(df['vol_roc'] >= 20).sum():,} ({(df['vol_roc'] >= 20).mean()*100:.1f}%)")
    print(f"  Above 30%: {(df['vol_roc'] >= 30).sum():,} ({(df['vol_roc'] >= 30).mean()*100:.1f}%)")
    print()

    # Build metadata
    metadata = {
        'indicator': 'Volume ROC',
        'total_trades': len(df),
        'date_range': f"{df['date'].min()} to {df['date'].max()}",
        'baseline_win_rate': df['is_winner'].mean() * 100,
        'stop_type': stop_type,
        'models_filter': models,
        'directions_filter': directions,
        'vol_roc_mean': float(df['vol_roc'].mean()),
        'vol_roc_std': float(df['vol_roc'].std())
    }

    results = []

    # Define segments to test - organized by category
    # Model definitions:
    #   EPCH1 = Primary Continuation
    #   EPCH2 = Primary Rejection
    #   EPCH3 = Secondary Continuation
    #   EPCH4 = Secondary Rejection

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

        # Test 1: Vol ROC Level (Above/Below 0%)
        results.append(test_vol_roc_level(segment_df, segment_name))

        # Test 2: Vol ROC Magnitude (Quintiles)
        results.append(test_vol_roc_magnitude(segment_df, segment_name))

        # Test 3: Vol ROC Threshold at 10%
        results.append(test_vol_roc_threshold(segment_df, 10, segment_name))

        # Test 4: Vol ROC Threshold at 20%
        results.append(test_vol_roc_threshold(segment_df, 20, segment_name))

        # Test 5: Vol ROC Threshold at 30%
        results.append(test_vol_roc_threshold(segment_df, 30, segment_name))

        # Test 6: Vol ROC Signed Quintiles
        results.append(test_vol_roc_signed_quintiles(segment_df, segment_name))

    return results, metadata


# ============================================================================
# CLI EXECUTION
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="CALC-011: Volume ROC Edge Analysis - Test Volume ROC indicator for statistical edge"
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
    print("CALC-011: VOLUME ROC EDGE ANALYSIS")
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
        filename = f"vol_roc_edge_{timestamp}.md"
        filepath = save_report(report, filename)
        print(f"\nReport saved to: {filepath}")

    # Return results for programmatic use
    return results, metadata


if __name__ == "__main__":
    main()
