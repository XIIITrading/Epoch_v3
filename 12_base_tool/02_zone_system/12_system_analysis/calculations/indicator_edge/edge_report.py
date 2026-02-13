"""
Report generation for indicator edge testing.
Outputs markdown reports suitable for Claude analysis.
"""

import os
from datetime import datetime
from typing import List, Dict
from .base_tester import EdgeTestResult


RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')


# =============================================================================
# CONSOLE OUTPUT
# =============================================================================

def print_console_summary(
    results: List[EdgeTestResult],
    metadata: Dict
) -> None:
    """Print condensed summary to terminal."""

    print("=" * 80)
    print(f"INDICATOR EDGE ANALYSIS - {metadata.get('indicator', 'UNKNOWN')}")
    print("=" * 80)
    print(f"Data: {metadata.get('total_trades', 0):,} trades | {metadata.get('date_range', 'Unknown')}")
    print(f"Stop Type: {metadata.get('stop_type', 'zone_buffer')}")
    print(f"Baseline Win Rate: {metadata.get('baseline_win_rate', 0):.1f}%")
    print("=" * 80)
    print()
    print(f"{'TEST':<35} | {'SEGMENT':<12} | {'EDGE?':<6} | {'P-VALUE':<8} | {'EFFECT':<8} | {'CONF':<6}")
    print("-" * 35 + "-+-" + "-" * 12 + "-+-" + "-" * 6 + "-+-" + "-" * 8 + "-+-" + "-" * 8 + "-+-" + "-" * 6)

    for r in results:
        edge_str = "YES" if r.has_edge else "NO"
        print(f"{r.test_name:<35} | {r.segment:<12} | {edge_str:<6} | {r.p_value:<8.4f} | {r.effect_size:<7.1f}pp | {r.confidence:<6}")

    print("=" * 80)

    # Summary of edges found
    edges_found = [r for r in results if r.has_edge]
    if edges_found:
        print("\nEDGES DETECTED:")
        for r in edges_found:
            print(f"  [+] {r.test_name} ({r.segment}): {r.effect_size:.1f}pp advantage")
    else:
        print("\nNO SIGNIFICANT EDGES DETECTED")

    print("=" * 80)


# =============================================================================
# MARKDOWN REPORT GENERATION
# =============================================================================

def generate_markdown_report(
    results: List[EdgeTestResult],
    metadata: Dict
) -> str:
    """Generate full markdown report from test results."""

    lines = []

    # Header
    lines.append(f"# {metadata.get('indicator', 'Indicator')} Edge Analysis Report (CALC-011)")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**Data Range:** {metadata.get('date_range', 'Unknown')}")
    lines.append(f"**Total Trades:** {metadata.get('total_trades', 0):,}")
    lines.append(f"**Stop Type:** {metadata.get('stop_type', 'zone_buffer')}")
    lines.append(f"**Baseline Win Rate:** {metadata.get('baseline_win_rate', 0):.1f}%")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Executive Summary
    lines.append("## Executive Summary")
    lines.append("")
    lines.append("| Test | Segment | Edge Detected | Confidence | Effect Size |")
    lines.append("|------|---------|---------------|------------|-------------|")

    for r in results:
        edge_icon = "YES" if r.has_edge else "NO"
        lines.append(f"| {r.test_name} | {r.segment} | {edge_icon} | {r.confidence} | {r.effect_size:.1f}pp |")

    lines.append("")

    # Key findings
    edges_found = [r for r in results if r.has_edge]
    if edges_found:
        lines.append("**Key Findings:**")
        for r in edges_found:
            lines.append(f"- {r.test_name} ({r.segment}): {r.effect_size:.1f}pp win rate advantage (p={r.p_value:.4f})")
        lines.append("")

    lines.append("---")
    lines.append("")

    # Detailed Results
    lines.append("## Detailed Results")
    lines.append("")

    # Group by test name
    test_names = list(dict.fromkeys([r.test_name for r in results]))

    for test_name in test_names:
        test_results = [r for r in results if r.test_name == test_name]

        lines.append(f"### {test_name}")
        lines.append("")

        for r in test_results:
            lines.append(f"**Segment: {r.segment}**")
            lines.append("")

            # Group statistics table
            lines.append("| Group | Trades | Wins | Win Rate | vs Baseline |")
            lines.append("|-------|--------|------|----------|-------------|")

            for group_name, stats in r.groups.items():
                vs_baseline = stats['win_rate'] - r.baseline_win_rate
                vs_str = f"+{vs_baseline:.1f}pp" if vs_baseline >= 0 else f"{vs_baseline:.1f}pp"
                lines.append(f"| {group_name} | {stats['trades']:,} | {stats['wins']:,} | {stats['win_rate']:.1f}% | {vs_str} |")

            lines.append("")
            lines.append(f"- **Test Type:** {r.test_type}")
            lines.append(f"- **P-value:** {r.p_value:.4f}")
            lines.append(f"- **Effect Size:** {r.effect_size:.1f}pp")
            lines.append(f"- **Confidence:** {r.confidence}")
            lines.append(f"- **Verdict:** {r.recommendation}")
            lines.append("")

    lines.append("---")
    lines.append("")

    # Recommendations
    lines.append("## Recommendations")
    lines.append("")

    if edges_found:
        lines.append("### Implement")
        for r in edges_found:
            lines.append(f"1. **{r.test_name} ({r.segment})**: {r.recommendation}")
        lines.append("")

    no_edge = [r for r in results if not r.has_edge and r.confidence != "LOW"]
    if no_edge:
        lines.append("### No Action Needed")
        for r in no_edge:
            lines.append(f"- {r.test_name} ({r.segment}): {r.recommendation}")
        lines.append("")

    low_conf = [r for r in results if r.confidence == "LOW"]
    if low_conf:
        lines.append("### Needs More Data")
        for r in low_conf:
            lines.append(f"- {r.test_name} ({r.segment}): Insufficient sample size for conclusion")
        lines.append("")

    lines.append("---")
    lines.append("")

    # Statistical Notes
    lines.append("## Statistical Notes")
    lines.append("")
    lines.append("- **Significance Level:** alpha = 0.05")
    lines.append("- **Effect Size Threshold:** 3.0pp minimum for practical significance")
    lines.append("- **Confidence Levels:**")
    lines.append("  - HIGH: >=100 trades per group")
    lines.append("  - MEDIUM: >=30 trades per group")
    lines.append("  - LOW: <30 trades per group (insufficient)")
    lines.append("")

    return "\n".join(lines)


def save_report(content: str, filename: str) -> str:
    """Save markdown report to results directory."""

    os.makedirs(RESULTS_DIR, exist_ok=True)
    filepath = os.path.join(RESULTS_DIR, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    return filepath
