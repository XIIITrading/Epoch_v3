"""
================================================================================
EPOCH TRADING SYSTEM - EPCH Indicators Edge Analysis
Monte AI Prompt Generator
================================================================================

Generates comprehensive prompts for Claude analysis of EPCH indicator edge results.
Includes all test data so insights can evolve as trade count grows.

Version: 1.0.0
================================================================================
"""

import pandas as pd
from typing import List, Dict, Any
from datetime import datetime

from .base_tester import EdgeTestResult


def generate_epch_indicators_prompt(
    results: List[EdgeTestResult],
    df: pd.DataFrame,
    stop_type: str
) -> str:
    """
    Generate comprehensive Claude prompt with all edge test results.

    Args:
        results: List of EdgeTestResult from all tests
        df: DataFrame with trade data
        stop_type: Stop type used for win determination

    Returns:
        Formatted prompt string for Claude analysis
    """
    lines = []

    # Header
    lines.append("# EPCH Indicators Edge Analysis Report")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**Stop Type:** {stop_type}")
    lines.append("")

    # Data summary
    total_trades = len(df)
    wins = df['is_winner'].sum() if len(df) > 0 else 0
    baseline_wr = (wins / total_trades * 100) if total_trades > 0 else 0

    lines.append("## Data Summary")
    lines.append("")
    lines.append(f"- **Total Trades:** {total_trades:,}")
    lines.append(f"- **Wins:** {wins:,}")
    lines.append(f"- **Baseline Win Rate:** {baseline_wr:.1f}%")

    if len(df) > 0:
        min_date = df['date'].min()
        max_date = df['date'].max()
        lines.append(f"- **Date Range:** {min_date} to {max_date}")

        # Model distribution
        model_dist = df['model'].value_counts().to_dict()
        model_str = ", ".join([f"{k}: {v}" for k, v in sorted(model_dist.items())])
        lines.append(f"- **Trades by Model:** {model_str}")

        # Direction distribution
        dir_dist = df['direction'].value_counts().to_dict()
        dir_str = ", ".join([f"{k}: {v}" for k, v in sorted(dir_dist.items())])
        lines.append(f"- **Trades by Direction:** {dir_str}")

    lines.append("")
    lines.append("---")
    lines.append("")

    # Model Legend
    lines.append("## Model Legend")
    lines.append("")
    lines.append("| Model | Description |")
    lines.append("|-------|-------------|")
    lines.append("| EPCH1 | Primary Continuation |")
    lines.append("| EPCH2 | Primary Rejection |")
    lines.append("| EPCH3 | Secondary Continuation |")
    lines.append("| EPCH4 | Secondary Rejection |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Edge Summary
    edges = [r for r in results if r.has_edge]
    no_edge = [r for r in results if not r.has_edge and r.confidence != "LOW"]
    low_conf = [r for r in results if r.confidence == "LOW"]

    lines.append("## Edge Summary")
    lines.append("")
    lines.append(f"- **Total Tests Run:** {len(results)}")
    lines.append(f"- **Edges Detected:** {len(edges)}")
    lines.append(f"- **No Edge (sufficient data):** {len(no_edge)}")
    lines.append(f"- **Insufficient Data:** {len(low_conf)}")
    lines.append("")

    if edges:
        lines.append("### Edges Detected")
        lines.append("")
        lines.append("| Indicator | Test | Segment | Effect (pp) | p-value |")
        lines.append("|-----------|------|---------|-------------|---------|")
        for r in sorted(edges, key=lambda x: x.effect_size, reverse=True):
            lines.append(f"| {r.indicator} | {r.test_name} | {r.segment} | {r.effect_size:.1f} | {r.p_value:.4f} |")
        lines.append("")

    lines.append("---")
    lines.append("")

    # Detailed Results by Indicator
    lines.append("## Detailed Results by Indicator")
    lines.append("")

    indicators = sorted(set(r.indicator for r in results))

    for indicator in indicators:
        indicator_results = [r for r in results if r.indicator == indicator]

        lines.append(f"### {indicator}")
        lines.append("")

        # Group by test name
        test_names = sorted(set(r.test_name for r in indicator_results))

        for test_name in test_names:
            test_results = [r for r in indicator_results if r.test_name == test_name]

            lines.append(f"#### {test_name}")
            lines.append("")

            lines.append("| Segment | Edge? | Conf | Effect (pp) | p-value | Recommendation |")
            lines.append("|---------|-------|------|-------------|---------|----------------|")

            for r in test_results:
                edge_str = "YES" if r.has_edge else "NO"
                rec_short = r.recommendation[:50] + "..." if len(r.recommendation) > 50 else r.recommendation
                lines.append(f"| {r.segment} | {edge_str} | {r.confidence} | {r.effect_size:.1f} | {r.p_value:.4f} | {rec_short} |")

            lines.append("")

            # Show group details for ALL segment
            all_result = next((r for r in test_results if r.segment == "ALL"), None)
            if all_result and all_result.groups:
                lines.append("**Group Statistics (ALL):**")
                lines.append("")
                lines.append("| Group | Trades | Wins | Win Rate | vs Baseline |")
                lines.append("|-------|--------|------|----------|-------------|")

                for group_name, stats in all_result.groups.items():
                    vs_baseline = stats['win_rate'] - all_result.baseline_win_rate
                    vs_str = f"+{vs_baseline:.1f}pp" if vs_baseline >= 0 else f"{vs_baseline:.1f}pp"
                    lines.append(f"| {group_name} | {stats['trades']:,} | {stats['wins']:,} | {stats['win_rate']:.1f}% | {vs_str} |")

                lines.append("")

        lines.append("---")
        lines.append("")

    # Indicator Statistics
    lines.append("## Indicator Statistics")
    lines.append("")

    if len(df) > 0:
        stats_data = []

        if 'candle_range_pct' in df.columns:
            cr = df['candle_range_pct'].dropna()
            if len(cr) > 0:
                stats_data.append(f"- **Candle Range:** Mean={cr.mean():.4f}%, Median={cr.median():.4f}%, Std={cr.std():.4f}%")

        if 'vol_delta' in df.columns:
            vd = df['vol_delta'].dropna()
            if len(vd) > 0:
                stats_data.append(f"- **Volume Delta:** Mean={vd.mean():.2f}, Median={vd.median():.2f}, Std={vd.std():.2f}")

        if 'vol_roc' in df.columns:
            vr = df['vol_roc'].dropna()
            if len(vr) > 0:
                stats_data.append(f"- **Volume ROC:** Mean={vr.mean():.2f}%, Median={vr.median():.2f}%, Std={vr.std():.2f}%")

        if 'sma_spread' in df.columns:
            ss = df['sma_spread'].dropna()
            if len(ss) > 0:
                stats_data.append(f"- **SMA Spread:** Mean={ss.mean():.4f}, Median={ss.median():.4f}, Std={ss.std():.4f}")

        if 'h1_structure' in df.columns:
            h1_dist = df['h1_structure'].value_counts(normalize=True) * 100
            h1_str = ", ".join([f"{k}: {v:.1f}%" for k, v in h1_dist.items()])
            stats_data.append(f"- **H1 Structure Distribution:** {h1_str}")

        if 'long_score' in df.columns:
            ls = df['long_score'].dropna()
            if len(ls) > 0:
                stats_data.append(f"- **LONG Score:** Mean={ls.mean():.2f}, Median={ls.median():.1f}, Range={ls.min():.0f}-{ls.max():.0f}")

        if 'short_score' in df.columns:
            ss = df['short_score'].dropna()
            if len(ss) > 0:
                stats_data.append(f"- **SHORT Score:** Mean={ss.mean():.2f}, Median={ss.median():.1f}, Range={ss.min():.0f}-{ss.max():.0f}")

        for line in stats_data:
            lines.append(line)

    lines.append("")
    lines.append("---")
    lines.append("")

    # Analysis Request
    lines.append("## Analysis Request")
    lines.append("")
    lines.append("Based on the above EPCH indicator edge analysis, please provide insights on:")
    lines.append("")
    lines.append("1. **Which indicators show the strongest edges for predicting winning LONG trades?**")
    lines.append("2. **Which indicators show the strongest edges for predicting winning SHORT trades?**")
    lines.append("3. **Are there any indicator combinations that could improve entry filtering?**")
    lines.append("4. **For indicators with LOW confidence, what is the recommended sample size to reach HIGH confidence?**")
    lines.append("5. **Based on the edge analysis, what specific trade filters would you recommend implementing?**")
    lines.append("6. **Are there any concerning patterns (e.g., indicators that seem to hurt win rate)?**")
    lines.append("")
    lines.append("Please structure your response with specific, actionable recommendations that can be implemented in the trading system.")
    lines.append("")

    return "\n".join(lines)


def generate_indicator_summary(results: List[EdgeTestResult]) -> str:
    """
    Generate a concise summary of edge results for quick reference.

    Args:
        results: List of EdgeTestResult

    Returns:
        Concise summary string
    """
    edges = [r for r in results if r.has_edge]

    if not edges:
        return "No statistically significant edges detected."

    lines = ["Edges Detected:"]
    for r in sorted(edges, key=lambda x: x.effect_size, reverse=True)[:5]:
        lines.append(f"- {r.indicator} ({r.test_name}): {r.effect_size:.1f}pp @ {r.segment}")

    return "\n".join(lines)
