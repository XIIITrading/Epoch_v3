"""
CALC-011: SMA Edge Analysis

Tests SMA (Simple Moving Average) indicators for statistical edge in trade outcomes.
Uses SMA9, SMA21, sma_spread, and sma_momentum_label from prior M1 bar (before entry at S15)
to avoid look-ahead bias.

Analyzes:
- SMA Spread: Raw difference between SMA9 and SMA21 (quintile analysis)
- SMA Spread Direction: BULLISH (SMA9 > SMA21) vs BEARISH (SMA9 < SMA21)
- SMA Spread Alignment: Does spread direction match trade direction?
- SMA Momentum: Spread widening vs narrowing (from sma_momentum_label)
- SMA Alignment with Price: Price above/below SMAs

Usage:
    python -m sma_edge.sma_edge
    python -m sma_edge.sma_edge --models EPCH01,EPCH03
    python -m sma_edge.sma_edge --direction LONG
    python -m sma_edge.sma_edge --output results/sma_2026.md
"""

import argparse
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from datetime import datetime

from .base_tester import (
    EdgeTestResult,
    fetch_sma_data,
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
# SMA METRIC CALCULATIONS
# ============================================================================

def calculate_sma_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add SMA-derived columns for edge testing.

    Adds:
        sma_spread_calc: Calculated spread (sma9 - sma21) for verification
        sma_spread_pct: Spread as percentage of price
        sma_spread_direction: 'BULLISH' (SMA9 > SMA21) or 'BEARISH' (SMA9 < SMA21)
        sma_spread_aligned: Boolean - True if spread direction matches trade direction
        sma_spread_aligned_str: 'ALIGNED' or 'MISALIGNED' for grouping
        sma_spread_quintile: Q1 (smallest/most negative) to Q5 (largest/most positive)
        sma_spread_abs_quintile: Q1 (smallest abs) to Q5 (largest abs) - for magnitude
        sma_momentum: From sma_momentum_label or calculated
        price_vs_sma9: 'ABOVE' or 'BELOW'
        price_vs_sma21: 'ABOVE' or 'BELOW'
        price_vs_both: 'ABOVE_BOTH', 'BELOW_BOTH', or 'BETWEEN'
    """
    df = df.copy()

    # Calculate spread if not present or verify
    if 'sma_spread' not in df.columns or df['sma_spread'].isna().all():
        df['sma_spread'] = df['sma9'] - df['sma21']

    # Spread as percentage of price
    df['sma_spread_pct'] = (df['sma_spread'] / df['bar_close']) * 100

    # Spread direction classification
    # BULLISH = SMA9 > SMA21 (short-term momentum above long-term)
    # BEARISH = SMA9 < SMA21 (short-term momentum below long-term)
    df['sma_spread_direction'] = np.where(df['sma_spread'] > 0, 'BULLISH', 'BEARISH')

    # Alignment: LONG should have BULLISH spread, SHORT should have BEARISH spread
    df['sma_spread_aligned'] = (
        ((df['direction'] == 'LONG') & (df['sma_spread'] > 0)) |
        ((df['direction'] == 'SHORT') & (df['sma_spread'] < 0))
    )
    df['sma_spread_aligned_str'] = df['sma_spread_aligned'].map({True: 'ALIGNED', False: 'MISALIGNED'})

    # Signed spread quintiles (captures both direction and magnitude)
    # Q1 = most negative (bearish), Q5 = most positive (bullish)
    try:
        df['sma_spread_quintile'] = pd.qcut(
            df['sma_spread'],
            q=5,
            labels=['Q1_MostBearish', 'Q2_Bearish', 'Q3_Neutral', 'Q4_Bullish', 'Q5_MostBullish'],
            duplicates='drop'
        )
    except ValueError:
        try:
            df['sma_spread_quintile'] = pd.qcut(
                df['sma_spread'],
                q=3,
                labels=['BEARISH', 'NEUTRAL', 'BULLISH'],
                duplicates='drop'
            )
        except ValueError:
            df['sma_spread_quintile'] = df['sma_spread_direction']

    # Absolute spread magnitude quintiles
    df['sma_spread_abs'] = df['sma_spread'].abs()
    try:
        df['sma_spread_abs_quintile'] = pd.qcut(
            df['sma_spread_abs'],
            q=5,
            labels=['Q1_Smallest', 'Q2', 'Q3', 'Q4', 'Q5_Largest'],
            duplicates='drop'
        )
    except ValueError:
        try:
            df['sma_spread_abs_quintile'] = pd.qcut(
                df['sma_spread_abs'],
                q=3,
                labels=['SMALL', 'MEDIUM', 'LARGE'],
                duplicates='drop'
            )
        except ValueError:
            median = df['sma_spread_abs'].median()
            df['sma_spread_abs_quintile'] = np.where(
                df['sma_spread_abs'] <= median, 'SMALL', 'LARGE'
            )

    # SMA Momentum from database label or calculate
    if 'sma_momentum_label' in df.columns and df['sma_momentum_label'].notna().any():
        df['sma_momentum'] = df['sma_momentum_label']
    else:
        # Cannot calculate momentum without previous bar data
        df['sma_momentum'] = 'UNKNOWN'

    # Price position relative to SMAs
    df['price_vs_sma9'] = np.where(df['bar_close'] > df['sma9'], 'ABOVE', 'BELOW')
    df['price_vs_sma21'] = np.where(df['bar_close'] > df['sma21'], 'ABOVE', 'BELOW')

    # Combined price position
    df['price_vs_both'] = np.where(
        (df['bar_close'] > df['sma9']) & (df['bar_close'] > df['sma21']),
        'ABOVE_BOTH',
        np.where(
            (df['bar_close'] < df['sma9']) & (df['bar_close'] < df['sma21']),
            'BELOW_BOTH',
            'BETWEEN'
        )
    )

    # Price position alignment with trade direction
    # LONG should have price ABOVE SMAs, SHORT should have price BELOW SMAs
    df['price_sma_aligned'] = (
        ((df['direction'] == 'LONG') & (df['price_vs_both'] == 'ABOVE_BOTH')) |
        ((df['direction'] == 'SHORT') & (df['price_vs_both'] == 'BELOW_BOTH'))
    )
    df['price_sma_aligned_str'] = df['price_sma_aligned'].map({True: 'ALIGNED', False: 'NOT_ALIGNED'})

    return df


# ============================================================================
# INDIVIDUAL EDGE TESTS
# ============================================================================

def test_sma_spread_direction(df: pd.DataFrame, segment: str = "ALL") -> EdgeTestResult:
    """
    Test: Does BULLISH vs BEARISH SMA spread affect win rate?

    Hypothesis: Bullish spread (SMA9 > SMA21) may favor LONG trades overall,
                Bearish spread may favor SHORT trades.
    """
    baseline_wr = df['is_winner'].mean() * 100
    groups = calculate_win_rates(df, 'sma_spread_direction')

    chi2, p_value, effect_size = chi_square_test(df, 'sma_spread_direction')

    min_group_size = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group_size)

    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    return EdgeTestResult(
        indicator="SMA",
        test_name="SMA Spread Direction (Bull/Bear)",
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


def test_sma_spread_alignment(df: pd.DataFrame, segment: str = "ALL") -> EdgeTestResult:
    """
    Test: Does alignment between spread direction and trade direction affect win rate?

    Hypothesis: LONG trades should perform better with bullish spread (SMA9 > SMA21),
                SHORT trades should perform better with bearish spread (SMA9 < SMA21).
    """
    baseline_wr = df['is_winner'].mean() * 100
    groups = calculate_win_rates(df, 'sma_spread_aligned_str')

    chi2, p_value, effect_size = chi_square_test(df, 'sma_spread_aligned_str')

    min_group_size = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group_size)

    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    return EdgeTestResult(
        indicator="SMA",
        test_name="SMA Spread Alignment",
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


def test_sma_spread_magnitude(df: pd.DataFrame, segment: str = "ALL") -> EdgeTestResult:
    """
    Test: Does absolute magnitude of SMA spread show monotonic relationship with win rate?

    Hypothesis: Wider spread may indicate stronger trend/conviction.
    """
    baseline_wr = df['is_winner'].mean() * 100

    quintile_col = 'sma_spread_abs_quintile'
    groups = calculate_win_rates(df, quintile_col)

    # Define order for quintiles
    quintile_order = ['Q1_Smallest', 'Q2', 'Q3', 'Q4', 'Q5_Largest']
    if 'SMALL' in groups:  # 3-bucket fallback
        quintile_order = ['SMALL', 'MEDIUM', 'LARGE']
    elif len(groups) == 2 and 'SMALL' in groups:  # 2-bucket fallback
        quintile_order = ['SMALL', 'LARGE']

    correlation, p_value, effect_size = spearman_monotonic_test(
        df, quintile_col, bucket_order=quintile_order
    )

    min_group_size = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group_size)

    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    if has_edge:
        direction = "wider" if correlation > 0 else "narrower"
        recommendation = f"EDGE DETECTED - {direction} spread correlates with higher win rate (r={correlation:.3f})"

    return EdgeTestResult(
        indicator="SMA",
        test_name="SMA Spread Magnitude (Quintiles)",
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


def test_sma_spread_signed_quintiles(df: pd.DataFrame, segment: str = "ALL") -> EdgeTestResult:
    """
    Test: Does the signed SMA spread show monotonic relationship with win rate?

    Hypothesis: Win rate may vary across spectrum from most bearish to most bullish.
    """
    baseline_wr = df['is_winner'].mean() * 100

    quintile_col = 'sma_spread_quintile'
    groups = calculate_win_rates(df, quintile_col)

    # Define order for quintiles
    quintile_order = ['Q1_MostBearish', 'Q2_Bearish', 'Q3_Neutral', 'Q4_Bullish', 'Q5_MostBullish']
    if 'BEARISH' in groups:  # 3-bucket fallback
        quintile_order = ['BEARISH', 'NEUTRAL', 'BULLISH']
    elif 'BULLISH' in groups and 'BEARISH' in groups and len(groups) == 2:
        quintile_order = ['BEARISH', 'BULLISH']

    correlation, p_value, effect_size = spearman_monotonic_test(
        df, quintile_col, bucket_order=quintile_order
    )

    min_group_size = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group_size)

    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    if has_edge:
        direction = "bullish" if correlation > 0 else "bearish"
        recommendation = f"EDGE DETECTED - {direction} spread correlates with higher win rate (r={correlation:.3f})"

    return EdgeTestResult(
        indicator="SMA",
        test_name="SMA Spread Signed (Direction+Magnitude)",
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


def test_sma_momentum(df: pd.DataFrame, segment: str = "ALL") -> EdgeTestResult:
    """
    Test: Does SMA momentum (spread widening/narrowing) affect win rate?

    Hypothesis: Widening spread in trade direction may indicate stronger momentum.
    """
    # Check if we have momentum data
    if 'sma_momentum' not in df.columns or df['sma_momentum'].isna().all() or (df['sma_momentum'] == 'UNKNOWN').all():
        return EdgeTestResult(
            indicator="SMA",
            test_name="SMA Momentum (Widening/Narrowing)",
            segment=segment,
            has_edge=False,
            p_value=1.0,
            effect_size=0.0,
            groups={},
            baseline_win_rate=df['is_winner'].mean() * 100,
            confidence="LOW",
            test_type="chi_square",
            recommendation="NO DATA - sma_momentum_label not available in database"
        )

    # Filter to rows with valid momentum data
    df_valid = df[df['sma_momentum'].notna() & (df['sma_momentum'] != 'UNKNOWN')]

    if len(df_valid) < 30:
        return EdgeTestResult(
            indicator="SMA",
            test_name="SMA Momentum (Widening/Narrowing)",
            segment=segment,
            has_edge=False,
            p_value=1.0,
            effect_size=0.0,
            groups={},
            baseline_win_rate=df['is_winner'].mean() * 100,
            confidence="LOW",
            test_type="chi_square",
            recommendation="INSUFFICIENT DATA - Not enough trades with momentum data"
        )

    baseline_wr = df_valid['is_winner'].mean() * 100
    groups = calculate_win_rates(df_valid, 'sma_momentum')

    chi2, p_value, effect_size = chi_square_test(df_valid, 'sma_momentum')

    min_group_size = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group_size)

    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    return EdgeTestResult(
        indicator="SMA",
        test_name="SMA Momentum (Widening/Narrowing)",
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


def test_price_sma_position(df: pd.DataFrame, segment: str = "ALL") -> EdgeTestResult:
    """
    Test: Does price position relative to both SMAs affect win rate?

    Categories: ABOVE_BOTH, BELOW_BOTH, BETWEEN

    Hypothesis: Price clearly above or below both SMAs may indicate trend strength.
    """
    baseline_wr = df['is_winner'].mean() * 100
    groups = calculate_win_rates(df, 'price_vs_both')

    chi2, p_value, effect_size = chi_square_test(df, 'price_vs_both')

    min_group_size = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group_size)

    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    return EdgeTestResult(
        indicator="SMA",
        test_name="Price vs SMA Position",
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


def test_price_sma_alignment(df: pd.DataFrame, segment: str = "ALL") -> EdgeTestResult:
    """
    Test: Does price/SMA alignment with trade direction affect win rate?

    ALIGNED: LONG with price ABOVE_BOTH, or SHORT with price BELOW_BOTH
    NOT_ALIGNED: Everything else

    Hypothesis: Trading in direction of price/SMA alignment should perform better.
    """
    baseline_wr = df['is_winner'].mean() * 100
    groups = calculate_win_rates(df, 'price_sma_aligned_str')

    chi2, p_value, effect_size = chi_square_test(df, 'price_sma_aligned_str')

    min_group_size = min(g['trades'] for g in groups.values()) if groups else 0
    confidence = get_confidence_level(min_group_size)

    has_edge, recommendation = determine_edge(p_value, effect_size, confidence)

    return EdgeTestResult(
        indicator="SMA",
        test_name="Price/SMA Alignment with Direction",
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
    Run complete SMA edge analysis across all segments.

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
    print("Fetching data from database (using prior M1 bar SMA data)...")
    df = fetch_sma_data(
        models=models,
        directions=directions,
        date_from=date_from,
        date_to=date_to,
        stop_type=stop_type
    )

    if df.empty:
        raise ValueError("No data returned from database. Check filters or m1_indicator_bars data.")

    # Calculate SMA metrics
    print(f"Calculating SMA metrics for {len(df):,} trades...")
    df = calculate_sma_metrics(df)

    # Print summary stats
    print(f"\nSMA Spread Summary:")
    print(f"  Mean: {df['sma_spread'].mean():.4f}")
    print(f"  Median: {df['sma_spread'].median():.4f}")
    print(f"  Std Dev: {df['sma_spread'].std():.4f}")
    print(f"  Min: {df['sma_spread'].min():.4f}")
    print(f"  Max: {df['sma_spread'].max():.4f}")
    bullish_pct = (df['sma_spread_direction'] == 'BULLISH').mean() * 100
    bearish_pct = (df['sma_spread_direction'] == 'BEARISH').mean() * 100
    print(f"  Bullish (SMA9 > SMA21): {(df['sma_spread'] > 0).sum():,} ({bullish_pct:.1f}%)")
    print(f"  Bearish (SMA9 < SMA21): {(df['sma_spread'] < 0).sum():,} ({bearish_pct:.1f}%)")
    print()

    # Build metadata
    metadata = {
        'indicator': 'SMA',
        'total_trades': len(df),
        'date_range': f"{df['date'].min()} to {df['date'].max()}",
        'baseline_win_rate': df['is_winner'].mean() * 100,
        'stop_type': stop_type,
        'models_filter': models,
        'directions_filter': directions,
        'sma_spread_mean': float(df['sma_spread'].mean()),
        'sma_spread_std': float(df['sma_spread'].std()),
        'sma_spread_min': float(df['sma_spread'].min()),
        'sma_spread_max': float(df['sma_spread'].max()),
        'bullish_pct': bullish_pct,
        'bearish_pct': bearish_pct
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

        # Test 1: SMA Spread Direction (Bullish/Bearish)
        results.append(test_sma_spread_direction(segment_df, segment_name))

        # Test 2: SMA Spread Alignment
        results.append(test_sma_spread_alignment(segment_df, segment_name))

        # Test 3: SMA Spread Magnitude (absolute quintiles)
        results.append(test_sma_spread_magnitude(segment_df, segment_name))

        # Test 4: SMA Spread Signed Quintiles
        results.append(test_sma_spread_signed_quintiles(segment_df, segment_name))

        # Test 5: SMA Momentum (widening/narrowing)
        results.append(test_sma_momentum(segment_df, segment_name))

        # Test 6: Price vs SMA Position
        results.append(test_price_sma_position(segment_df, segment_name))

        # Test 7: Price/SMA Alignment with Direction
        results.append(test_price_sma_alignment(segment_df, segment_name))

    return results, metadata


# ============================================================================
# CLI EXECUTION
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="CALC-011: SMA Edge Analysis - Test SMA indicators for statistical edge"
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
    print("CALC-011: SMA EDGE ANALYSIS")
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
        filename = f"sma_edge_{timestamp}.md"
        filepath = save_report(report, filename)
        print(f"\nReport saved to: {filepath}")

    # Return results for programmatic use
    return results, metadata


if __name__ == "__main__":
    main()
