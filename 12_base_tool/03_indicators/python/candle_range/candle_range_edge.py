"""
CALC-011: Candle Range Edge Analysis

Tests Candle Range indicator for statistical edge in trade outcomes.
Uses OHLC from prior M1 bar (before entry at S15) to avoid look-ahead bias.

Calculation:
    candle_range_pct = (high - low) / open * 100

Analyzes:
- Range Threshold: Binary classification at 0.12%, 0.15%, 0.18%, 0.20%
- Range Magnitude: Quintile analysis of candle range values
- Small Range (Absorption): Range < 0.12% as skip filter
- Large Range (Momentum): Range >= 0.15% as take filter

Usage:
    python -m candle_range.candle_range_edge
    python -m candle_range.candle_range_edge --models EPCH01,EPCH03
    python -m candle_range.candle_range_edge --direction LONG
    python -m candle_range.candle_range_edge --output results/candle_range_2026.md
"""

import argparse
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from datetime import datetime

from .base_tester import (
    EdgeTestResult,
    fetch_candle_range_data,
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
# CANDLE RANGE METRIC CALCULATIONS
# ============================================================================

def calculate_candle_range_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add Candle Range-derived columns for edge testing.

    Adds:
        candle_range: Raw range in price (high - low)
        candle_range_pct: Range as percentage of open price
        range_threshold_012: 'LARGE' (>=0.12%) or 'SMALL' (<0.12%)
        range_threshold_015: 'LARGE' (>=0.15%) or 'SMALL' (<0.15%)
        range_threshold_018: 'LARGE' (>=0.18%) or 'SMALL' (<0.18%)
        range_threshold_020: 'LARGE' (>=0.20%) or 'SMALL' (<0.20%)
        range_quintile: Q1 (smallest) to Q5 (largest)
        range_category: 'VERY_SMALL', 'SMALL', 'MEDIUM', 'LARGE', 'VERY_LARGE'
    """
    df = df.copy()

    # Calculate candle range
    df['candle_range'] = df['bar_high'] - df['bar_low']
    df['candle_range_pct'] = (df['candle_range'] / df['bar_open']) * 100

    # Threshold classifications (key thresholds from validation document)
    df['range_threshold_012'] = np.where(
        df['candle_range_pct'] >= 0.12, 'LARGE_>=0.12%', 'SMALL_<0.12%'
    )
    df['range_threshold_015'] = np.where(
        df['candle_range_pct'] >= 0.15, 'LARGE_>=0.15%', 'SMALL_<0.15%'
    )
    df['range_threshold_018'] = np.where(
        df['candle_range_pct'] >= 0.18, 'LARGE_>=0.18%', 'SMALL_<0.18%'
    )
    df['range_threshold_020'] = np.where(
        df['candle_range_pct'] >= 0.20, 'LARGE_>=0.20%', 'SMALL_<0.20%'
    )

    # Magnitude quintiles (Q1 = smallest range, Q5 = largest)
    try:
        df['range_quintile'] = pd.qcut(
            df['candle_range_pct'],
            q=5,
            labels=['Q1_Smallest', 'Q2', 'Q3', 'Q4', 'Q5_Largest'],
            duplicates='drop'
        )
    except ValueError:
        # Not enough unique values for 5 quintiles
        try:
            df['range_quintile'] = pd.qcut(
                df['candle_range_pct'],
                q=3,
                labels=['Q1_Small', 'Q2_Mid', 'Q3_Large'],
                duplicates='drop'
            )
        except ValueError:
            # Fallback - just use median split
            median = df['candle_range_pct'].median()
            df['range_quintile'] = np.where(
                df['candle_range_pct'] <= median, 'SMALL', 'LARGE'
            )

    # Category classification based on validation document findings
    # Very Small: < 0.12% (absorption zone, SKIP)
    # Small: 0.12% - 0.15%
    # Medium: 0.15% - 0.18%
    # Large: 0.18% - 0.20%
    # Very Large: >= 0.20% (strong momentum, TAKE)
    conditions = [
        df['candle_range_pct'] < 0.12,
        (df['candle_range_pct'] >= 0.12) & (df['candle_range_pct'] < 0.15),
        (df['candle_range_pct'] >= 0.15) & (df['candle_range_pct'] < 0.18),
        (df['candle_range_pct'] >= 0.18) & (df['candle_range_pct'] < 0.20),
        df['candle_range_pct'] >= 0.20
    ]
    categories = ['VERY_SMALL', 'SMALL', 'MEDIUM', 'LARGE', 'VERY_LARGE']
    df['range_category'] = np.select(conditions, categories, default='MEDIUM')

    return df


# ============================================================================
# INDIVIDUAL EDGE TESTS
# ============================================================================

def test_range_threshold(
    df: pd.DataFrame,
    threshold: float,
    segment: str = "ALL"
) -> EdgeTestResult:
    """
    Test: Does candle range above/below a specific threshold affect win rate?

    Key thresholds from validation document:
    - 0.12%: Absorption threshold (below = SKIP)
    - 0.15%: Standard threshold (above = momentum)
    - 0.18%: High threshold for continuation trades
    - 0.20%: Very high threshold (above = strong momentum)
    """
    baseline_wr = df['is_winner'].mean() * 100

    # Map threshold to column name
    threshold_str = str(threshold).replace('.', '').replace('0', '')
    if threshold == 0.12:
        threshold_col = 'range_threshold_012'
    elif threshold == 0.15:
        threshold_col = 'range_threshold_015'
    elif threshold == 0.18:
        threshold_col = 'range_threshold_018'
    elif threshold == 0.20:
        threshold_col = 'range_threshold_020'
    else:
        # Create dynamic threshold column
        threshold_col = f'range_threshold_{int(threshold*100):03d}'
        df = df.copy()
        df[threshold_col] = np.where(
            df['candle_range_pct'] >= threshold,
            f'LARGE_>={threshold}%',
            f'SMALL_<{threshold}%'
        )

    groups = calculate_win_rates(df, threshold_col)

    chi2, p_value, effect_size = chi_square_test(df, threshold_col)

    min_group_size = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group_size)

    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    # Add specific recommendations based on threshold
    if has_edge:
        if threshold == 0.12:
            recommendation = f"EDGE DETECTED - Range < 0.12% = SKIP (absorption zone). Effect: {effect_size:.1f}pp"
        elif threshold >= 0.15:
            recommendation = f"EDGE DETECTED - Range >= {threshold}% = TAKE. Effect: {effect_size:.1f}pp"

    return EdgeTestResult(
        indicator="Candle Range",
        test_name=f"Range Threshold ({threshold}%)",
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


def test_range_magnitude(df: pd.DataFrame, segment: str = "ALL") -> EdgeTestResult:
    """
    Test: Does candle range magnitude show monotonic relationship with win rate?

    Hypothesis: Larger candle ranges indicate stronger price movement/momentum
                and may correlate with better trade outcomes.
    """
    baseline_wr = df['is_winner'].mean() * 100

    quintile_col = 'range_quintile'
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
        direction = "larger" if correlation > 0 else "smaller"
        recommendation = f"EDGE DETECTED - {direction} candle range correlates with higher win rate (r={correlation:.3f})"

    return EdgeTestResult(
        indicator="Candle Range",
        test_name="Range Magnitude (Quintiles)",
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


def test_range_category(df: pd.DataFrame, segment: str = "ALL") -> EdgeTestResult:
    """
    Test: Does the categorized range (VERY_SMALL to VERY_LARGE) show edge?

    Categories based on validation document:
    - VERY_SMALL: < 0.12% (absorption - SKIP)
    - SMALL: 0.12% - 0.15%
    - MEDIUM: 0.15% - 0.18%
    - LARGE: 0.18% - 0.20%
    - VERY_LARGE: >= 0.20% (strong momentum - TAKE)
    """
    baseline_wr = df['is_winner'].mean() * 100

    category_col = 'range_category'
    groups = calculate_win_rates(df, category_col)

    # Define order for categories
    category_order = ['VERY_SMALL', 'SMALL', 'MEDIUM', 'LARGE', 'VERY_LARGE']

    correlation, p_value, effect_size = spearman_monotonic_test(
        df, category_col, bucket_order=category_order
    )

    min_group_size = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group_size)

    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    if has_edge:
        direction = "larger" if correlation > 0 else "smaller"
        recommendation = f"EDGE DETECTED - {direction} range category correlates with higher win rate (r={correlation:.3f})"

    return EdgeTestResult(
        indicator="Candle Range",
        test_name="Range Category (5-tier)",
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


def test_absorption_zone(df: pd.DataFrame, segment: str = "ALL") -> EdgeTestResult:
    """
    Test: Does the absorption zone (Range < 0.12%) show negative edge?

    This is a specific test for the SKIP filter - trades in this zone
    should have significantly lower win rates.
    """
    baseline_wr = df['is_winner'].mean() * 100

    # Create binary absorption classification
    df = df.copy()
    df['absorption_zone'] = np.where(
        df['candle_range_pct'] < 0.12, 'ABSORPTION', 'NORMAL'
    )

    groups = calculate_win_rates(df, 'absorption_zone')

    chi2, p_value, effect_size = chi_square_test(df, 'absorption_zone')

    min_group_size = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group_size)

    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    # Check if absorption has lower win rate
    if has_edge and 'ABSORPTION' in groups and 'NORMAL' in groups:
        absorption_wr = groups['ABSORPTION']['win_rate']
        normal_wr = groups['NORMAL']['win_rate']
        if absorption_wr < normal_wr:
            recommendation = f"SKIP FILTER VALIDATED - Absorption zone ({absorption_wr:.1f}% WR) underperforms normal ({normal_wr:.1f}% WR). Effect: {effect_size:.1f}pp"
        else:
            recommendation = f"UNEXPECTED - Absorption zone outperforms (may need investigation)"

    return EdgeTestResult(
        indicator="Candle Range",
        test_name="Absorption Zone (<0.12%)",
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
    Run complete Candle Range edge analysis across all segments.

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
    print("Fetching data from database (using prior M1 bar OHLC for candle range)...")
    df = fetch_candle_range_data(
        models=models,
        directions=directions,
        date_from=date_from,
        date_to=date_to,
        stop_type=stop_type
    )

    if df.empty:
        raise ValueError("No data returned from database. Check filters or m1_indicator_bars data.")

    # Calculate Candle Range metrics
    print(f"Calculating Candle Range metrics for {len(df):,} trades...")
    df = calculate_candle_range_metrics(df)

    # Print summary stats
    print(f"\nCandle Range Summary:")
    print(f"  Mean: {df['candle_range_pct'].mean():.3f}%")
    print(f"  Median: {df['candle_range_pct'].median():.3f}%")
    print(f"  Std Dev: {df['candle_range_pct'].std():.3f}%")
    print(f"  Min: {df['candle_range_pct'].min():.3f}%")
    print(f"  Max: {df['candle_range_pct'].max():.3f}%")
    print(f"  < 0.12% (Absorption): {(df['candle_range_pct'] < 0.12).sum():,} ({(df['candle_range_pct'] < 0.12).mean()*100:.1f}%)")
    print(f"  >= 0.15% (Large): {(df['candle_range_pct'] >= 0.15).sum():,} ({(df['candle_range_pct'] >= 0.15).mean()*100:.1f}%)")
    print(f"  >= 0.20% (Very Large): {(df['candle_range_pct'] >= 0.20).sum():,} ({(df['candle_range_pct'] >= 0.20).mean()*100:.1f}%)")
    print()

    # Build metadata
    metadata = {
        'indicator': 'Candle Range',
        'total_trades': len(df),
        'date_range': f"{df['date'].min()} to {df['date'].max()}",
        'baseline_win_rate': df['is_winner'].mean() * 100,
        'stop_type': stop_type,
        'models_filter': models,
        'directions_filter': directions,
        'candle_range_mean': float(df['candle_range_pct'].mean()),
        'candle_range_median': float(df['candle_range_pct'].median()),
        'candle_range_std': float(df['candle_range_pct'].std())
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
        segment_df = calculate_candle_range_metrics(segment_df)

        # Test 1: Absorption Zone (<0.12%) - SKIP filter
        results.append(test_absorption_zone(segment_df, segment_name))

        # Test 2: Range Threshold at 0.12%
        results.append(test_range_threshold(segment_df, 0.12, segment_name))

        # Test 3: Range Threshold at 0.15% (key threshold from validation)
        results.append(test_range_threshold(segment_df, 0.15, segment_name))

        # Test 4: Range Threshold at 0.18% (continuation threshold)
        results.append(test_range_threshold(segment_df, 0.18, segment_name))

        # Test 5: Range Threshold at 0.20% (strong momentum)
        results.append(test_range_threshold(segment_df, 0.20, segment_name))

        # Test 6: Range Magnitude (Quintiles)
        results.append(test_range_magnitude(segment_df, segment_name))

        # Test 7: Range Category (5-tier)
        results.append(test_range_category(segment_df, segment_name))

    return results, metadata


# ============================================================================
# CLI EXECUTION
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="CALC-011: Candle Range Edge Analysis - Test Candle Range indicator for statistical edge"
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
    print("CALC-011: CANDLE RANGE EDGE ANALYSIS")
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
        filename = f"candle_range_edge_{timestamp}.md"
        filepath = save_report(report, filename)
        print(f"\nReport saved to: {filepath}")

    # Return results for programmatic use
    return results, metadata


if __name__ == "__main__":
    main()
