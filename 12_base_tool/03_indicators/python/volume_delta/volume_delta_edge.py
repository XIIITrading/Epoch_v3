"""
CALC-011: Volume Delta Edge Analysis

Tests Volume Delta indicator for statistical edge in trade outcomes.
Uses vol_delta from prior M1 bar (before entry at S15) to avoid look-ahead bias.

Analyzes:
- Vol Delta Sign: POSITIVE vs NEGATIVE (bullish vs bearish pressure)
- Vol Delta Alignment: Does delta direction match trade direction?
- Vol Delta Magnitude: Quintile analysis of absolute delta values

Usage:
    python -m volume_delta.volume_delta_edge
    python -m volume_delta.volume_delta_edge --models EPCH01,EPCH03
    python -m volume_delta.volume_delta_edge --direction LONG
    python -m volume_delta.volume_delta_edge --output results/vol_delta_2025.md
"""

import argparse
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from datetime import datetime

from .base_tester import (
    EdgeTestResult,
    fetch_volume_delta_data,
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
# VOLUME DELTA METRIC CALCULATIONS
# ============================================================================

def calculate_vol_delta_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add Volume Delta-derived columns for edge testing.

    Adds:
        vol_delta_sign: 'POSITIVE' or 'NEGATIVE' (bullish vs bearish)
        vol_delta_abs: Absolute value of delta
        vol_delta_aligned: Boolean - True if delta direction matches trade direction
        vol_delta_aligned_str: 'ALIGNED' or 'MISALIGNED' for grouping
        vol_delta_quintile: Q1 (lowest abs) to Q5 (highest abs)
    """
    df = df.copy()

    # Sign classification
    df['vol_delta_sign'] = np.where(df['vol_delta'] >= 0, 'POSITIVE', 'NEGATIVE')

    # Absolute value
    df['vol_delta_abs'] = df['vol_delta'].abs()

    # Alignment: LONG should have POSITIVE delta, SHORT should have NEGATIVE delta
    # Positive delta = buying pressure = bullish
    # Negative delta = selling pressure = bearish
    df['vol_delta_aligned'] = (
        ((df['direction'] == 'LONG') & (df['vol_delta'] > 0)) |
        ((df['direction'] == 'SHORT') & (df['vol_delta'] < 0))
    )
    df['vol_delta_aligned_str'] = df['vol_delta_aligned'].map({True: 'ALIGNED', False: 'MISALIGNED'})

    # Magnitude quintiles (Q1 = smallest absolute delta, Q5 = largest)
    try:
        df['vol_delta_quintile'] = pd.qcut(
            df['vol_delta_abs'],
            q=5,
            labels=['Q1_Smallest', 'Q2', 'Q3', 'Q4', 'Q5_Largest'],
            duplicates='drop'
        )
    except ValueError:
        # Not enough unique values for 5 quintiles
        try:
            df['vol_delta_quintile'] = pd.qcut(
                df['vol_delta_abs'],
                q=3,
                labels=['Q1_Small', 'Q2_Mid', 'Q3_Large'],
                duplicates='drop'
            )
        except ValueError:
            # Fallback - just use median split
            median = df['vol_delta_abs'].median()
            df['vol_delta_quintile'] = np.where(
                df['vol_delta_abs'] <= median, 'SMALL', 'LARGE'
            )

    # Signed quintiles for directional analysis
    # This captures both direction and magnitude
    try:
        df['vol_delta_signed_quintile'] = pd.qcut(
            df['vol_delta'],
            q=5,
            labels=['Q1_MostNeg', 'Q2_Neg', 'Q3_Neutral', 'Q4_Pos', 'Q5_MostPos'],
            duplicates='drop'
        )
    except ValueError:
        try:
            df['vol_delta_signed_quintile'] = pd.qcut(
                df['vol_delta'],
                q=3,
                labels=['NEGATIVE', 'NEUTRAL', 'POSITIVE'],
                duplicates='drop'
            )
        except ValueError:
            df['vol_delta_signed_quintile'] = df['vol_delta_sign']

    return df


# ============================================================================
# INDIVIDUAL EDGE TESTS
# ============================================================================

def test_vol_delta_sign(df: pd.DataFrame, segment: str = "ALL") -> EdgeTestResult:
    """
    Test: Does POSITIVE vs NEGATIVE volume delta affect win rate?

    Hypothesis: Positive delta (buying pressure) may favor LONG trades,
                Negative delta (selling pressure) may favor SHORT trades.
    """
    baseline_wr = df['is_winner'].mean() * 100
    groups = calculate_win_rates(df, 'vol_delta_sign')

    chi2, p_value, effect_size = chi_square_test(df, 'vol_delta_sign')

    min_group_size = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group_size)

    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    return EdgeTestResult(
        indicator="Volume Delta",
        test_name="Vol Delta Sign (Pos/Neg)",
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


def test_vol_delta_alignment(df: pd.DataFrame, segment: str = "ALL") -> EdgeTestResult:
    """
    Test: Does alignment between delta direction and trade direction affect win rate?

    Hypothesis: LONG trades should perform better with positive delta,
                SHORT trades should perform better with negative delta.
    """
    baseline_wr = df['is_winner'].mean() * 100
    groups = calculate_win_rates(df, 'vol_delta_aligned_str')

    chi2, p_value, effect_size = chi_square_test(df, 'vol_delta_aligned_str')

    min_group_size = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group_size)

    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    return EdgeTestResult(
        indicator="Volume Delta",
        test_name="Vol Delta Alignment",
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


def test_vol_delta_magnitude(df: pd.DataFrame, segment: str = "ALL") -> EdgeTestResult:
    """
    Test: Does absolute magnitude of volume delta show monotonic relationship with win rate?

    Hypothesis: Higher absolute delta may indicate stronger conviction/momentum.
    """
    baseline_wr = df['is_winner'].mean() * 100

    quintile_col = 'vol_delta_quintile'
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
        indicator="Volume Delta",
        test_name="Vol Delta Magnitude (Quintiles)",
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


def test_vol_delta_signed_quintiles(df: pd.DataFrame, segment: str = "ALL") -> EdgeTestResult:
    """
    Test: Does the signed (directional) volume delta show monotonic relationship with win rate?

    Hypothesis: Win rate may vary across the spectrum from most negative to most positive.
    """
    baseline_wr = df['is_winner'].mean() * 100

    quintile_col = 'vol_delta_signed_quintile'
    groups = calculate_win_rates(df, quintile_col)

    # Define order for quintiles
    quintile_order = ['Q1_MostNeg', 'Q2_Neg', 'Q3_Neutral', 'Q4_Pos', 'Q5_MostPos']
    if 'NEGATIVE' in groups:  # 3-bucket fallback
        quintile_order = ['NEGATIVE', 'NEUTRAL', 'POSITIVE']
    elif 'POSITIVE' in groups and 'NEGATIVE' in groups and len(groups) == 2:
        quintile_order = ['NEGATIVE', 'POSITIVE']

    correlation, p_value, effect_size = spearman_monotonic_test(
        df, quintile_col, bucket_order=quintile_order
    )

    min_group_size = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group_size)

    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    if has_edge:
        direction = "positive" if correlation > 0 else "negative"
        recommendation = f"EDGE DETECTED - {direction} delta correlates with higher win rate (r={correlation:.3f})"

    return EdgeTestResult(
        indicator="Volume Delta",
        test_name="Vol Delta Signed (Direction+Magnitude)",
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
    Run complete Volume Delta edge analysis across all segments.

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
    print("Fetching data from database (using prior M1 bar vol_delta)...")
    df = fetch_volume_delta_data(
        models=models,
        directions=directions,
        date_from=date_from,
        date_to=date_to,
        stop_type=stop_type
    )

    if df.empty:
        raise ValueError("No data returned from database. Check filters or m1_indicator_bars data.")

    # Calculate Volume Delta metrics
    print(f"Calculating Volume Delta metrics for {len(df):,} trades...")
    df = calculate_vol_delta_metrics(df)

    # Print summary stats
    print(f"\nVolume Delta Summary:")
    print(f"  Mean: {df['vol_delta'].mean():,.0f}")
    print(f"  Median: {df['vol_delta'].median():,.0f}")
    print(f"  Std Dev: {df['vol_delta'].std():,.0f}")
    print(f"  Min: {df['vol_delta'].min():,.0f}")
    print(f"  Max: {df['vol_delta'].max():,.0f}")
    print(f"  Positive: {(df['vol_delta'] > 0).sum():,} ({(df['vol_delta'] > 0).mean()*100:.1f}%)")
    print(f"  Negative: {(df['vol_delta'] < 0).sum():,} ({(df['vol_delta'] < 0).mean()*100:.1f}%)")
    print()

    # Build metadata
    metadata = {
        'indicator': 'Volume Delta',
        'total_trades': len(df),
        'date_range': f"{df['date'].min()} to {df['date'].max()}",
        'baseline_win_rate': df['is_winner'].mean() * 100,
        'stop_type': stop_type,
        'models_filter': models,
        'directions_filter': directions,
        'vol_delta_mean': float(df['vol_delta'].mean()),
        'vol_delta_std': float(df['vol_delta'].std())
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

        # Test 1: Vol Delta Sign
        results.append(test_vol_delta_sign(segment_df, segment_name))

        # Test 2: Vol Delta Alignment
        results.append(test_vol_delta_alignment(segment_df, segment_name))

        # Test 3: Vol Delta Magnitude
        results.append(test_vol_delta_magnitude(segment_df, segment_name))

        # Test 4: Vol Delta Signed Quintiles
        results.append(test_vol_delta_signed_quintiles(segment_df, segment_name))

    return results, metadata


# ============================================================================
# CLI EXECUTION
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="CALC-011: Volume Delta Edge Analysis - Test Volume Delta indicator for statistical edge"
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
    print("CALC-011: VOLUME DELTA EDGE ANALYSIS")
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
        filename = f"vol_delta_edge_{timestamp}.md"
        filepath = save_report(report, filename)
        print(f"\nReport saved to: {filepath}")

    # Return results for programmatic use
    return results, metadata


if __name__ == "__main__":
    main()
