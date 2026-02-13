"""
CALC-011: CVD Slope Edge Analysis

Tests CVD Slope (Cumulative Volume Delta Slope) indicator for statistical edge in trade outcomes.
Uses cvd_slope from prior M1 bar (before entry at S15) to avoid look-ahead bias.

CVD Slope measures the trend/direction of cumulative volume delta over time:
- Positive slope = CVD rising = increasing buying pressure / bullish order flow
- Negative slope = CVD falling = increasing selling pressure / bearish order flow

Analyzes:
- CVD Slope Direction: POSITIVE vs NEGATIVE (rising vs falling CVD)
- CVD Slope Alignment: Does slope direction match trade direction?
- CVD Slope Magnitude: Quintile analysis of absolute slope values
- CVD Slope Extreme: Tests at various thresholds for extreme values

Usage:
    python -m cvd_slope.cvd_slope_edge
    python -m cvd_slope.cvd_slope_edge --models EPCH01,EPCH03
    python -m cvd_slope.cvd_slope_edge --direction LONG
    python -m cvd_slope.cvd_slope_edge --output results/cvd_slope_2026.md
"""

import argparse
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from datetime import datetime

from .base_tester import (
    EdgeTestResult,
    fetch_cvd_slope_data,
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
# CVD SLOPE METRIC CALCULATIONS
# ============================================================================

def calculate_cvd_slope_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add CVD Slope-derived columns for edge testing.

    Adds:
        cvd_slope_direction: 'POSITIVE' (rising CVD) or 'NEGATIVE' (falling CVD)
        cvd_slope_abs: Absolute value of slope
        cvd_slope_aligned: Boolean - True if slope direction matches trade direction
        cvd_slope_aligned_str: 'ALIGNED' or 'MISALIGNED' for grouping
        cvd_slope_quintile: Q1 (lowest abs) to Q5 (highest abs)
        cvd_slope_extreme: Classification based on percentile thresholds
    """
    df = df.copy()

    # Direction classification (positive = rising CVD = bullish order flow)
    df['cvd_slope_direction'] = np.where(df['cvd_slope'] >= 0, 'POSITIVE', 'NEGATIVE')

    # Absolute value for magnitude analysis
    df['cvd_slope_abs'] = df['cvd_slope'].abs()

    # Alignment: LONG should have POSITIVE slope (rising CVD = bullish)
    #            SHORT should have NEGATIVE slope (falling CVD = bearish)
    df['cvd_slope_aligned'] = (
        ((df['direction'] == 'LONG') & (df['cvd_slope'] > 0)) |
        ((df['direction'] == 'SHORT') & (df['cvd_slope'] < 0))
    )
    df['cvd_slope_aligned_str'] = df['cvd_slope_aligned'].map({True: 'ALIGNED', False: 'MISALIGNED'})

    # Magnitude quintiles (Q1 = smallest absolute slope, Q5 = largest/most extreme)
    try:
        df['cvd_slope_quintile'] = pd.qcut(
            df['cvd_slope_abs'],
            q=5,
            labels=['Q1_Smallest', 'Q2', 'Q3', 'Q4', 'Q5_Largest'],
            duplicates='drop'
        )
    except ValueError:
        # Not enough unique values for 5 quintiles
        try:
            df['cvd_slope_quintile'] = pd.qcut(
                df['cvd_slope_abs'],
                q=3,
                labels=['Q1_Small', 'Q2_Mid', 'Q3_Large'],
                duplicates='drop'
            )
        except ValueError:
            # Fallback - just use median split
            median = df['cvd_slope_abs'].median()
            df['cvd_slope_quintile'] = np.where(
                df['cvd_slope_abs'] <= median, 'SMALL', 'LARGE'
            )

    # Signed quintiles for directional analysis (most negative to most positive)
    try:
        df['cvd_slope_signed_quintile'] = pd.qcut(
            df['cvd_slope'],
            q=5,
            labels=['Q1_MostNeg', 'Q2_Neg', 'Q3_Neutral', 'Q4_Pos', 'Q5_MostPos'],
            duplicates='drop'
        )
    except ValueError:
        try:
            df['cvd_slope_signed_quintile'] = pd.qcut(
                df['cvd_slope'],
                q=3,
                labels=['NEGATIVE', 'NEUTRAL', 'POSITIVE'],
                duplicates='drop'
            )
        except ValueError:
            df['cvd_slope_signed_quintile'] = df['cvd_slope_direction']

    # Extreme value classification based on percentiles
    p25 = df['cvd_slope'].quantile(0.25)
    p75 = df['cvd_slope'].quantile(0.75)
    p10 = df['cvd_slope'].quantile(0.10)
    p90 = df['cvd_slope'].quantile(0.90)

    conditions = [
        df['cvd_slope'] <= p10,
        (df['cvd_slope'] > p10) & (df['cvd_slope'] <= p25),
        (df['cvd_slope'] > p25) & (df['cvd_slope'] < p75),
        (df['cvd_slope'] >= p75) & (df['cvd_slope'] < p90),
        df['cvd_slope'] >= p90
    ]
    categories = ['EXTREME_NEG', 'LOW', 'NEUTRAL', 'HIGH', 'EXTREME_POS']
    df['cvd_slope_category'] = np.select(conditions, categories, default='NEUTRAL')

    return df


# ============================================================================
# INDIVIDUAL EDGE TESTS
# ============================================================================

def test_cvd_slope_direction(df: pd.DataFrame, segment: str = "ALL") -> EdgeTestResult:
    """
    Test: Does POSITIVE vs NEGATIVE CVD slope affect win rate?

    Hypothesis: Positive slope (rising CVD/bullish order flow) may favor LONG trades,
                Negative slope (falling CVD/bearish order flow) may favor SHORT trades.
    """
    baseline_wr = df['is_winner'].mean() * 100
    groups = calculate_win_rates(df, 'cvd_slope_direction')

    chi2, p_value, effect_size = chi_square_test(df, 'cvd_slope_direction')

    min_group_size = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group_size)

    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    return EdgeTestResult(
        indicator="CVD Slope",
        test_name="CVD Slope Direction (Pos/Neg)",
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


def test_cvd_slope_alignment(df: pd.DataFrame, segment: str = "ALL") -> EdgeTestResult:
    """
    Test: Does alignment between CVD slope direction and trade direction affect win rate?

    Hypothesis: LONG trades should perform better with positive slope (bullish order flow),
                SHORT trades should perform better with negative slope (bearish order flow).
    """
    baseline_wr = df['is_winner'].mean() * 100
    groups = calculate_win_rates(df, 'cvd_slope_aligned_str')

    chi2, p_value, effect_size = chi_square_test(df, 'cvd_slope_aligned_str')

    min_group_size = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group_size)

    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    return EdgeTestResult(
        indicator="CVD Slope",
        test_name="CVD Slope Alignment",
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


def test_cvd_slope_magnitude(df: pd.DataFrame, segment: str = "ALL") -> EdgeTestResult:
    """
    Test: Does absolute magnitude of CVD slope show monotonic relationship with win rate?

    Hypothesis: Higher absolute slope may indicate stronger order flow momentum/conviction,
                which could lead to better or worse trade outcomes.
    """
    baseline_wr = df['is_winner'].mean() * 100

    quintile_col = 'cvd_slope_quintile'
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
        indicator="CVD Slope",
        test_name="CVD Slope Magnitude (Quintiles)",
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


def test_cvd_slope_signed_quintiles(df: pd.DataFrame, segment: str = "ALL") -> EdgeTestResult:
    """
    Test: Does the signed (directional) CVD slope show monotonic relationship with win rate?

    Hypothesis: Win rate may vary across the spectrum from most negative to most positive.
    """
    baseline_wr = df['is_winner'].mean() * 100

    quintile_col = 'cvd_slope_signed_quintile'
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
        recommendation = f"EDGE DETECTED - {direction} CVD slope correlates with higher win rate (r={correlation:.3f})"

    return EdgeTestResult(
        indicator="CVD Slope",
        test_name="CVD Slope Signed (Direction+Magnitude)",
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


def test_cvd_slope_category(df: pd.DataFrame, segment: str = "ALL") -> EdgeTestResult:
    """
    Test: Does the categorized CVD slope (EXTREME_NEG to EXTREME_POS) show edge?

    Categories based on percentiles:
    - EXTREME_NEG: bottom 10% (most negative slope)
    - LOW: 10-25%
    - NEUTRAL: 25-75%
    - HIGH: 75-90%
    - EXTREME_POS: top 10% (most positive slope)
    """
    baseline_wr = df['is_winner'].mean() * 100

    category_col = 'cvd_slope_category'
    groups = calculate_win_rates(df, category_col)

    # Define order for categories
    category_order = ['EXTREME_NEG', 'LOW', 'NEUTRAL', 'HIGH', 'EXTREME_POS']

    correlation, p_value, effect_size = spearman_monotonic_test(
        df, category_col, bucket_order=category_order
    )

    min_group_size = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group_size)

    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    if has_edge:
        direction = "positive" if correlation > 0 else "negative"
        recommendation = f"EDGE DETECTED - {direction} CVD slope category correlates with higher win rate (r={correlation:.3f})"

    return EdgeTestResult(
        indicator="CVD Slope",
        test_name="CVD Slope Category (5-tier)",
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


def test_cvd_slope_extreme(df: pd.DataFrame, segment: str = "ALL") -> EdgeTestResult:
    """
    Test: Do extreme CVD slope values (top/bottom 20%) show edge vs neutral?

    Hypothesis: Extreme order flow may indicate exhaustion or strong momentum.
    """
    baseline_wr = df['is_winner'].mean() * 100

    # Create extreme classification
    df = df.copy()
    p20 = df['cvd_slope'].quantile(0.20)
    p80 = df['cvd_slope'].quantile(0.80)

    df['cvd_slope_extreme'] = np.where(
        (df['cvd_slope'] <= p20) | (df['cvd_slope'] >= p80),
        'EXTREME',
        'NORMAL'
    )

    groups = calculate_win_rates(df, 'cvd_slope_extreme')

    chi2, p_value, effect_size = chi_square_test(df, 'cvd_slope_extreme')

    min_group_size = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group_size)

    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    return EdgeTestResult(
        indicator="CVD Slope",
        test_name="CVD Slope Extreme (Top/Bottom 20%)",
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
    Run complete CVD Slope edge analysis across all segments.

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
    print("Fetching data from database (using prior M1 bar cvd_slope)...")
    df = fetch_cvd_slope_data(
        models=models,
        directions=directions,
        date_from=date_from,
        date_to=date_to,
        stop_type=stop_type
    )

    if df.empty:
        raise ValueError("No data returned from database. Check filters or m1_indicator_bars data.")

    # Calculate CVD Slope metrics
    print(f"Calculating CVD Slope metrics for {len(df):,} trades...")
    df = calculate_cvd_slope_metrics(df)

    # Print summary stats
    print(f"\nCVD Slope Summary:")
    print(f"  Mean: {df['cvd_slope'].mean():.2f}")
    print(f"  Median: {df['cvd_slope'].median():.2f}")
    print(f"  Std Dev: {df['cvd_slope'].std():.2f}")
    print(f"  Min: {df['cvd_slope'].min():.2f}")
    print(f"  Max: {df['cvd_slope'].max():.2f}")
    print(f"  Positive (Rising CVD): {(df['cvd_slope'] > 0).sum():,} ({(df['cvd_slope'] > 0).mean()*100:.1f}%)")
    print(f"  Negative (Falling CVD): {(df['cvd_slope'] < 0).sum():,} ({(df['cvd_slope'] < 0).mean()*100:.1f}%)")
    print()

    # Build metadata
    metadata = {
        'indicator': 'CVD Slope',
        'total_trades': len(df),
        'date_range': f"{df['date'].min()} to {df['date'].max()}",
        'baseline_win_rate': df['is_winner'].mean() * 100,
        'stop_type': stop_type,
        'models_filter': models,
        'directions_filter': directions,
        'cvd_slope_mean': float(df['cvd_slope'].mean()),
        'cvd_slope_median': float(df['cvd_slope'].median()),
        'cvd_slope_std': float(df['cvd_slope'].std()),
        'cvd_slope_positive_pct': float((df['cvd_slope'] > 0).mean() * 100),
        'cvd_slope_negative_pct': float((df['cvd_slope'] < 0).mean() * 100)
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

        # Need to recalculate metrics for segment (quintiles are segment-specific)
        segment_df = calculate_cvd_slope_metrics(segment_df)

        # Test 1: CVD Slope Direction
        results.append(test_cvd_slope_direction(segment_df, segment_name))

        # Test 2: CVD Slope Alignment
        results.append(test_cvd_slope_alignment(segment_df, segment_name))

        # Test 3: CVD Slope Magnitude (Quintiles)
        results.append(test_cvd_slope_magnitude(segment_df, segment_name))

        # Test 4: CVD Slope Signed Quintiles
        results.append(test_cvd_slope_signed_quintiles(segment_df, segment_name))

        # Test 5: CVD Slope Category (5-tier)
        results.append(test_cvd_slope_category(segment_df, segment_name))

        # Test 6: CVD Slope Extreme (Top/Bottom 20%)
        results.append(test_cvd_slope_extreme(segment_df, segment_name))

    return results, metadata


# ============================================================================
# CLI EXECUTION
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="CALC-011: CVD Slope Edge Analysis - Test CVD Slope indicator for statistical edge"
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
    print("CALC-011: CVD SLOPE EDGE ANALYSIS")
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
        filename = f"cvd_slope_edge_{timestamp}.md"
        filepath = save_report(report, filename)
        print(f"\nReport saved to: {filepath}")

    # Return results for programmatic use
    return results, metadata


if __name__ == "__main__":
    main()
