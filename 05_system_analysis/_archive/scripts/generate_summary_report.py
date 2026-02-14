"""
================================================================================
EPOCH TRADING SYSTEM - Summary Report Generator
XIII Trading LLC
================================================================================

PURPOSE:
    Generate a clean .md summary report from the stop_analysis database table.
    Outputs to 05_system_analysis/reports/01_summary/

USAGE:
    python scripts/generate_summary_report.py

================================================================================
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.supabase_client import get_client
from calculations.stop_analysis.results_aggregator import (
    aggregate_by_stop_type,
    aggregate_by_model_direction
)
from calculations.stop_analysis.ui_components import _safe_float, _convert_supabase_to_results_format
from calculations.model.win_rate_by_model import calculate_win_rate_by_model
from calculations.trade_management.mfe_mae_sequence import (
    calculate_sequence_summary,
    calculate_sequence_by_model
)


# Stop type display order (matches Stop Type Comparison ranking by Win Rate)
STOP_TYPE_KEYS = ['zone_buffer', 'prior_m1', 'prior_m5', 'm5_atr', 'm15_atr', 'fractal']
STOP_TYPE_NAMES = {
    'zone_buffer': 'Zone + 5% Buffer',
    'prior_m1': 'Prior M1 H/L',
    'prior_m5': 'Prior M5 H/L',
    'm5_atr': 'M5 ATR (Close)',
    'm15_atr': 'M15 ATR (Close)',
    'fractal': 'M5 Fractal H/L'
}


def fetch_stop_data():
    """Fetch all stop analysis data from Supabase."""
    client = get_client()
    count = client.get_stop_analysis_count()
    data = client.fetch_stop_analysis()
    return data, count


def fetch_mfe_mae_data():
    """Fetch MFE/MAE potential data from Supabase."""
    client = get_client()
    data = client.fetch_mfe_mae_potential()
    return data


def build_stop_type_comparison(stop_data, record_count):
    """
    Build the Stop Type Comparison table, stack ranked by Win Rate %.

    Returns markdown string.
    """
    results = _convert_supabase_to_results_format(stop_data)
    summary_df = aggregate_by_stop_type(results)

    # Sort by Win Rate % descending
    summary_df = summary_df.sort_values('Win Rate %', ascending=False).reset_index(drop=True)

    # Count unique trades
    unique_trades = len(set(r.get('trade_id') for r in stop_data))

    # Build markdown
    lines = []
    lines.append("## Stop Type Comparison")
    lines.append("")
    lines.append("Compares 6 stop placement methods to show the trade-off between tighter stops (higher win rate, smaller gains) and wider stops (lower win rate, larger gains per winner).")
    lines.append("")
    lines.append(f"*{record_count:,} stop analysis records across {unique_trades:,} trades, ranked by Win Rate %*")
    lines.append("")

    # Table header
    lines.append("| Stop Type | n | Avg Stop % | Stop Hit % | Win Rate % | Avg R (Win) | Avg R (All) | Net R (MFE) | Expectancy |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")

    # Table rows
    for _, row in summary_df.iterrows():
        lines.append(
            f"| {row['Stop Type']} "
            f"| {int(row['n']):,} "
            f"| {row['Avg Stop %']:.2f}% "
            f"| {row['Stop Hit %']:.1f}% "
            f"| {row['Win Rate %']:.1f}% "
            f"| {row['Avg R (Win)']:+.2f}R "
            f"| {row['Avg R (All)']:+.2f}R "
            f"| {row['Net R (MFE)']:+.2f}R "
            f"| {row['Expectancy']:+.3f} |"
        )

    lines.append("")
    return "\n".join(lines)


def build_win_rate_by_model(stop_data, stop_type_comparison_df):
    """
    Build Win Rate by Model tables - one per stop type, ordered by Win Rate % from
    the Stop Type Comparison table.

    Uses existing calculate_win_rate_by_model() from CALC-001.
    Returns markdown string.
    """
    results = _convert_supabase_to_results_format(stop_data)

    # Get stop type order from the comparison table (already sorted by Win Rate %)
    if stop_type_comparison_df is not None and 'stop_type_key' in stop_type_comparison_df.columns:
        ordered_keys = stop_type_comparison_df['stop_type_key'].tolist()
    else:
        ordered_keys = STOP_TYPE_KEYS

    lines = []
    lines.append("## Win Rate by Model")
    lines.append("")
    lines.append("Shows how each entry model (EPCH01-04) performs under each stop type, revealing which models carry the edge and which are a drag.")
    lines.append("")

    for stop_key in ordered_keys:
        outcomes = results.get(stop_key, [])
        if not outcomes:
            continue

        stop_name = STOP_TYPE_NAMES.get(stop_key, stop_key)
        model_df = calculate_win_rate_by_model(outcomes, stop_name)

        if model_df.empty or model_df['Total'].sum() == 0:
            continue

        # Overall stats
        total_trades = model_df['Total'].sum()
        total_wins = model_df['Wins'].sum()
        overall_wr = (total_wins / total_trades * 100) if total_trades > 0 else 0

        lines.append(f"### {stop_name}")
        lines.append(f"*{total_trades:,} trades | Overall Win Rate: {overall_wr:.1f}%*")
        lines.append("")
        lines.append("| Model | Wins | Losses | Total | Win % | Avg R (Win) | Avg R (All) | Expectancy |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")

        for _, row in model_df.iterrows():
            lines.append(
                f"| {row['Model']} "
                f"| {int(row['Wins']):,} "
                f"| {int(row['Losses']):,} "
                f"| {int(row['Total']):,} "
                f"| {row['Win%']:.1f}% "
                f"| {row['Avg R (Win)']:+.2f}R "
                f"| {row['Avg R (All)']:+.2f}R "
                f"| {row['Expectancy']:+.3f} |"
            )

        lines.append("")

    return "\n".join(lines)


def build_model_direction_grid(stop_data, stop_type_comparison_df):
    """
    Build Model-Direction win rate grid — 8 columns (EPCH01-L through EPCH04-S)
    with one row per stop type, ordered by Win Rate % from Stop Type Comparison.

    Uses existing aggregate_by_model_direction() logic from results_aggregator.
    Returns markdown string.
    """
    import pandas as pd

    results = _convert_supabase_to_results_format(stop_data)

    # Get stop type order from comparison table
    if stop_type_comparison_df is not None and 'stop_type_key' in stop_type_comparison_df.columns:
        ordered_keys = stop_type_comparison_df['stop_type_key'].tolist()
    else:
        ordered_keys = STOP_TYPE_KEYS

    # Normalize model names
    def _normalize_model(model):
        if model is None:
            return 'UNKNOWN'
        model_map = {'EPCH1': 'EPCH01', 'EPCH2': 'EPCH02', 'EPCH3': 'EPCH03', 'EPCH4': 'EPCH04'}
        return model_map.get(model, model)

    # Flatten all outcomes with model-direction key
    all_outcomes = []
    for stop_type, outcomes in results.items():
        for o in outcomes:
            normalized = _normalize_model(o.get('model', ''))
            direction_letter = o.get('direction', 'L')[0]
            all_outcomes.append({
                'stop_type': stop_type,
                'model_direction': f"{normalized}-{direction_letter}",
                'r_achieved': _safe_float(o.get('r_achieved', 0)),
                'outcome': o.get('outcome')
            })

    if not all_outcomes:
        return ""

    df = pd.DataFrame(all_outcomes)

    model_dirs = ['EPCH01-L', 'EPCH01-S', 'EPCH02-L', 'EPCH02-S',
                  'EPCH03-L', 'EPCH03-S', 'EPCH04-L', 'EPCH04-S']

    lines = []
    lines.append("## Win Rate by Model-Direction")
    lines.append("")
    lines.append("Splits each model by LONG and SHORT to expose directional bias — a model may look average overall but have a strong edge in one direction.")
    lines.append("")

    # Table header
    header = "| Stop Type | " + " | ".join(model_dirs) + " |"
    sep = "|---|" + "|".join(["---:" for _ in model_dirs]) + "|"
    lines.append(header)
    lines.append(sep)

    # Build rows in Win Rate % order
    for stop_key in ordered_keys:
        stop_name = STOP_TYPE_NAMES.get(stop_key, stop_key)
        row_parts = [f"| {stop_name} "]

        for md in model_dirs:
            subset = df[(df['stop_type'] == stop_key) & (df['model_direction'] == md)]
            if len(subset) == 0:
                row_parts.append("| - ")
            else:
                wins = len(subset[subset['r_achieved'] >= 1.0])
                wr = (wins / len(subset)) * 100
                row_parts.append(f"| {wr:.1f}% ")

        row_parts.append("|")
        lines.append("".join(row_parts))

    lines.append("")
    return "\n".join(lines)


def build_mfe_mae_sequence(mfe_mae_data):
    """
    Build MFE/MAE Sequence Analysis section.

    Uses existing calculate_sequence_summary() and calculate_sequence_by_model()
    from CALC-003. No new calculations.

    Returns markdown string.
    """
    summary = calculate_sequence_summary(mfe_mae_data)
    model_df = calculate_sequence_by_model(mfe_mae_data)

    if summary.get('total_trades', 0) == 0:
        return ""

    lines = []
    lines.append("## MFE/MAE Sequence Analysis")
    lines.append("")
    lines.append("Answers whether trades move favorably before adversely after entry — high P(MFE First) means the trade works in your direction before pulling back.")
    lines.append("")

    # Overall summary
    lines.append(f"*{summary['total_trades']:,} trades analyzed*")
    lines.append("")
    lines.append("### Overall")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|---|---:|")
    lines.append(f"| P(MFE First) | {summary['mfe_first_rate']:.1%} |")
    lines.append(f"| MFE First Count | {summary['mfe_first_count']:,} |")
    lines.append(f"| MAE First Count | {summary['mae_first_count']:,} |")
    lines.append(f"| Median Time to MFE | {summary['median_time_to_mfe']:.0f} min |")
    lines.append(f"| Median Time to MAE | {summary['median_time_to_mae']:.0f} min |")
    lines.append(f"| MFE within 30 min | {summary['pct_mfe_under_30min']:.1f}% |")
    lines.append(f"| MFE within 60 min | {summary['pct_mfe_under_60min']:.1f}% |")
    lines.append("")

    # Model-Direction breakdown
    if not model_df.empty:
        lines.append("### By Model-Direction")
        lines.append("")
        lines.append("*Ranked by P(MFE First) — higher = trade works in your favor sooner*")
        lines.append("")
        lines.append("| Model | Direction | n | P(MFE First) | Med Time MFE | Med Time MAE | Time Delta | Confidence |")
        lines.append("|---|---|---:|---:|---:|---:|---:|---|")

        for _, row in model_df.iterrows():
            lines.append(
                f"| {row['model']} "
                f"| {row['direction']} "
                f"| {int(row['n_trades']):,} "
                f"| {row['p_mfe_first']:.1%} "
                f"| {row['median_time_mfe']:.0f} min "
                f"| {row['median_time_mae']:.0f} min "
                f"| {row['median_time_delta']:+.0f} min "
                f"| {row['mc_confidence']} |"
            )

        lines.append("")

    return "\n".join(lines)


def generate_report():
    """Generate the full summary report."""
    print("Fetching stop analysis data...")
    stop_data, record_count = fetch_stop_data()

    if not stop_data:
        print("ERROR: No stop analysis data found in database.")
        return

    print(f"  Found {record_count:,} records")

    # Build report sections
    report_lines = []
    report_lines.append("# EPOCH System Analysis - Summary Report")
    report_lines.append("")
    report_lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | All trades in database*")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")

    # Section 1: Stop Type Comparison
    print("Building Stop Type Comparison...")
    # Get the sorted summary_df so we can reuse the sort order
    results = _convert_supabase_to_results_format(stop_data)
    summary_df = aggregate_by_stop_type(results)
    summary_df = summary_df.sort_values('Win Rate %', ascending=False).reset_index(drop=True)

    report_lines.append(build_stop_type_comparison(stop_data, record_count))

    # Section 2: Win Rate by Model (per stop type)
    print("Building Win Rate by Model...")
    report_lines.append(build_win_rate_by_model(stop_data, summary_df))

    # Section 3: Model-Direction Grid
    print("Building Model-Direction Grid...")
    report_lines.append(build_model_direction_grid(stop_data, summary_df))

    # Section 4: MFE/MAE Sequence Analysis
    print("Fetching MFE/MAE potential data...")
    mfe_mae_data = fetch_mfe_mae_data()
    if mfe_mae_data:
        print(f"  Found {len(mfe_mae_data):,} MFE/MAE records")
        print("Building MFE/MAE Sequence Analysis...")
        report_lines.append(build_mfe_mae_sequence(mfe_mae_data))
    else:
        print("  WARNING: No MFE/MAE data found, skipping sequence analysis")

    # Write report
    output_dir = Path(__file__).parent.parent / "reports" / "01_summary"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "summary_report.md"
    output_path.write_text("\n".join(report_lines), encoding="utf-8")

    print(f"\nReport written to: {output_path}")
    print("Done.")


if __name__ == "__main__":
    generate_report()
