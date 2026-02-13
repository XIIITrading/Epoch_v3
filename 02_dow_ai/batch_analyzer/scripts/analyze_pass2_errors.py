#!/usr/bin/env python3
"""
DOW AI v3.0 Error Analysis Script
Epoch Trading System - XIII Trading LLC

Analyzes Pass 2 errors to identify patterns for instruction refinement.

This script queries dual_pass_analysis for trades where Pass 2 was wrong
and categorizes errors by:
- Zone type
- Model
- Direction
- H1 structure
- Indicator combinations
- Confidence level

Usage:
    python analyze_pass2_errors.py                      # Full analysis
    python analyze_pass2_errors.py --output report.txt  # Save to file
    python analyze_pass2_errors.py --recent             # Last 30 days only
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Any

# Setup paths
SCRIPT_DIR = Path(__file__).parent.resolve()
BATCH_DIR = SCRIPT_DIR.parent.resolve()
sys.path.insert(0, str(BATCH_DIR))

import psycopg2
from psycopg2.extras import RealDictCursor
from config import DB_CONFIG


def fetch_pass2_errors(recent_only: bool = False) -> List[Dict[str, Any]]:
    """Fetch all trades where Pass 2 was incorrect."""

    date_filter = ""
    if recent_only:
        cutoff = datetime.now().date() - timedelta(days=30)
        date_filter = f"AND trade_date >= '{cutoff}'"

    query = f"""
    SELECT
        trade_id, ticker, trade_date, direction, model, zone_type,
        pass2_decision, pass2_confidence, pass2_reasoning,
        actual_outcome, actual_pnl_r,
        h1_structure, h1_status,
        candle_pct, candle_status,
        vol_delta, vol_delta_status,
        vol_roc, vol_roc_status,
        sma_spread, sma_status,
        passes_agree, pass1_decision
    FROM dual_pass_analysis
    WHERE actual_outcome IS NOT NULL
      AND pass2_correct = FALSE
      {date_filter}
    ORDER BY trade_date DESC, entry_time DESC
    """

    conn = psycopg2.connect(**DB_CONFIG)
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query)
        rows = cur.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def fetch_all_trades(recent_only: bool = False) -> List[Dict[str, Any]]:
    """Fetch all analyzed trades for context."""

    date_filter = ""
    if recent_only:
        cutoff = datetime.now().date() - timedelta(days=30)
        date_filter = f"AND trade_date >= '{cutoff}'"

    query = f"""
    SELECT
        trade_id, ticker, direction, model, zone_type,
        pass2_decision, pass2_confidence, pass2_correct,
        actual_outcome,
        h1_structure, h1_status
    FROM dual_pass_analysis
    WHERE actual_outcome IS NOT NULL
      {date_filter}
    """

    conn = psycopg2.connect(**DB_CONFIG)
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query)
        rows = cur.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def analyze_errors(errors: List[Dict], all_trades: List[Dict]) -> Dict[str, Any]:
    """Categorize errors and identify patterns."""

    analysis = {
        'total_errors': len(errors),
        'total_trades': len(all_trades),
        'error_rate': len(errors) / len(all_trades) * 100 if all_trades else 0,
        'by_error_type': defaultdict(int),
        'by_zone_type': defaultdict(lambda: {'errors': 0, 'total': 0}),
        'by_model': defaultdict(lambda: {'errors': 0, 'total': 0}),
        'by_direction': defaultdict(lambda: {'errors': 0, 'total': 0}),
        'by_h1_structure': defaultdict(lambda: {'errors': 0, 'total': 0}),
        'by_confidence': defaultdict(lambda: {'errors': 0, 'total': 0}),
        'false_positives': [],  # TRADE on LOSS
        'false_negatives': [],  # NO_TRADE on WIN
        'high_confidence_errors': [],  # HIGH confidence wrong
        'pass_disagreement_errors': [],  # Pass 1 was right, Pass 2 wrong
    }

    # Count totals by category
    for trade in all_trades:
        analysis['by_zone_type'][trade['zone_type']]['total'] += 1
        analysis['by_model'][trade['model']]['total'] += 1
        analysis['by_direction'][trade['direction']]['total'] += 1
        if trade['h1_structure']:
            analysis['by_h1_structure'][trade['h1_structure']]['total'] += 1
        if trade['pass2_confidence']:
            analysis['by_confidence'][trade['pass2_confidence']]['total'] += 1

    # Analyze errors
    for error in errors:
        # Error type
        if error['pass2_decision'] == 'TRADE' and error['actual_outcome'] == 'LOSS':
            analysis['by_error_type']['FALSE_POSITIVE'] += 1
            analysis['false_positives'].append(error)
        elif error['pass2_decision'] == 'NO_TRADE' and error['actual_outcome'] == 'WIN':
            analysis['by_error_type']['FALSE_NEGATIVE'] += 1
            analysis['false_negatives'].append(error)

        # Category breakdowns
        analysis['by_zone_type'][error['zone_type']]['errors'] += 1
        analysis['by_model'][error['model']]['errors'] += 1
        analysis['by_direction'][error['direction']]['errors'] += 1

        if error['h1_structure']:
            analysis['by_h1_structure'][error['h1_structure']]['errors'] += 1

        if error['pass2_confidence']:
            analysis['by_confidence'][error['pass2_confidence']]['errors'] += 1
            if error['pass2_confidence'] == 'HIGH':
                analysis['high_confidence_errors'].append(error)

        # Pass disagreement where Pass 1 was right
        if not error['passes_agree']:
            # Determine if Pass 1 would have been correct
            p1_would_be_correct = (
                (error['pass1_decision'] == 'TRADE' and error['actual_outcome'] == 'WIN') or
                (error['pass1_decision'] == 'NO_TRADE' and error['actual_outcome'] == 'LOSS')
            )
            if p1_would_be_correct:
                analysis['pass_disagreement_errors'].append(error)

    return analysis


def calculate_error_rates(category_data: Dict) -> List[tuple]:
    """Calculate error rates for a category, sorted by rate."""
    rates = []
    for key, data in category_data.items():
        if data['total'] > 0:
            rate = data['errors'] / data['total'] * 100
            rates.append((key, data['errors'], data['total'], rate))

    return sorted(rates, key=lambda x: x[3], reverse=True)


def format_report(analysis: Dict, recent_only: bool) -> str:
    """Format analysis into readable report."""

    lines = []
    lines.append("=" * 80)
    lines.append("DOW AI v3.0 PASS 2 ERROR ANALYSIS")
    lines.append("=" * 80)
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Period: {'Last 30 days' if recent_only else 'All time'}")
    lines.append("")

    # Overview
    lines.append("OVERVIEW")
    lines.append("-" * 40)
    lines.append(f"Total Trades Analyzed: {analysis['total_trades']}")
    lines.append(f"Total Errors: {analysis['total_errors']}")
    lines.append(f"Pass 2 Accuracy: {100 - analysis['error_rate']:.1f}%")
    lines.append(f"Error Rate: {analysis['error_rate']:.1f}%")
    lines.append("")

    # Error types
    lines.append("ERROR TYPE BREAKDOWN")
    lines.append("-" * 40)
    fp = analysis['by_error_type'].get('FALSE_POSITIVE', 0)
    fn = analysis['by_error_type'].get('FALSE_NEGATIVE', 0)
    lines.append(f"False Positives (TRADE -> LOSS): {fp} ({fp/analysis['total_errors']*100:.1f}% of errors)" if analysis['total_errors'] else "False Positives: 0")
    lines.append(f"False Negatives (NO_TRADE -> WIN): {fn} ({fn/analysis['total_errors']*100:.1f}% of errors)" if analysis['total_errors'] else "False Negatives: 0")
    lines.append("")

    # Key insight
    if fp > fn:
        lines.append(">> INSIGHT: Pass 2 is TOO AGGRESSIVE (taking bad trades)")
        lines.append("   Consider: Tightening TRADE criteria in instructions")
    elif fn > fp:
        lines.append(">> INSIGHT: Pass 2 is TOO CONSERVATIVE (missing good trades)")
        lines.append("   Consider: Relaxing NO_TRADE criteria in instructions")
    lines.append("")

    # Error rates by category
    def add_category_section(title: str, data: Dict, min_total: int = 5):
        lines.append(title)
        lines.append("-" * 40)
        rates = calculate_error_rates(data)
        for key, errors, total, rate in rates:
            if total >= min_total:
                lines.append(f"  {key:20} {errors:3}/{total:3} = {rate:5.1f}% error rate")
        lines.append("")

    add_category_section("ERROR RATE BY ZONE TYPE", analysis['by_zone_type'])
    add_category_section("ERROR RATE BY MODEL", analysis['by_model'])
    add_category_section("ERROR RATE BY DIRECTION", analysis['by_direction'])
    add_category_section("ERROR RATE BY H1 STRUCTURE", analysis['by_h1_structure'])
    add_category_section("ERROR RATE BY CONFIDENCE", analysis['by_confidence'])

    # High confidence errors (most concerning)
    high_conf = analysis['high_confidence_errors']
    if high_conf:
        lines.append("HIGH CONFIDENCE ERRORS (Most Critical)")
        lines.append("-" * 40)
        lines.append(f"Count: {len(high_conf)} trades where Pass 2 was HIGH confidence but WRONG")
        lines.append("")
        for i, err in enumerate(high_conf[:10], 1):
            lines.append(f"  {i}. {err['trade_id']}")
            lines.append(f"     {err['ticker']} {err['direction']} | {err['model']} | {err['zone_type']}")
            lines.append(f"     Decision: {err['pass2_decision']} (HIGH) -> Actual: {err['actual_outcome']}")
            if err['pass2_reasoning']:
                reason = err['pass2_reasoning'][:100].replace('\n', ' ')
                lines.append(f"     Reasoning: {reason}...")
            lines.append("")
        if len(high_conf) > 10:
            lines.append(f"  ... and {len(high_conf) - 10} more")
        lines.append("")

    # Pass disagreement errors (Pass 1 was right)
    disagree = analysis['pass_disagreement_errors']
    if disagree:
        lines.append("PASS DISAGREEMENT ERRORS (Pass 1 was correct, Pass 2 wrong)")
        lines.append("-" * 40)
        lines.append(f"Count: {len(disagree)} trades where backtested context led to WORSE decision")
        lines.append("")
        lines.append(">> INSIGHT: These cases suggest the backtested context may be")
        lines.append("   OVERRIDING good intuition. Review ai_context files.")
        lines.append("")
        for i, err in enumerate(disagree[:5], 1):
            lines.append(f"  {i}. {err['trade_id']}")
            lines.append(f"     Pass 1: {err['pass1_decision']} (would be CORRECT)")
            lines.append(f"     Pass 2: {err['pass2_decision']} (WRONG)")
            lines.append(f"     Actual: {err['actual_outcome']}")
            lines.append("")
        lines.append("")

    # Recommendations
    lines.append("=" * 80)
    lines.append("RECOMMENDATIONS")
    lines.append("=" * 80)
    lines.append("")

    # Generate specific recommendations
    zone_rates = calculate_error_rates(analysis['by_zone_type'])
    h1_rates = calculate_error_rates(analysis['by_h1_structure'])

    for key, errors, total, rate in zone_rates[:3]:
        if rate > 40 and total >= 10:
            lines.append(f"1. ZONE TYPE '{key}' has {rate:.0f}% error rate")
            lines.append(f"   -> Consider adding specific guidance for {key} zones")
            lines.append("")

    for key, errors, total, rate in h1_rates[:3]:
        if rate > 45 and total >= 10:
            lines.append(f"2. H1 STRUCTURE '{key}' has {rate:.0f}% error rate")
            lines.append(f"   -> Review indicator_edges.json for H1 {key} conditions")
            lines.append("")

    if len(disagree) > len(analysis['total_errors']) * 0.2:
        lines.append("3. HIGH DISAGREMENT ERROR RATE")
        lines.append("   -> Backtested context may be too prescriptive")
        lines.append("   -> Consider softening guidance in ai_context files")
        lines.append("")

    lines.append("=" * 80)
    lines.append("END OF REPORT")
    lines.append("=" * 80)

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="DOW AI v3.0 Error Analysis")
    parser.add_argument('--output', '-o', type=str, help='Save report to file')
    parser.add_argument('--recent', action='store_true', help='Analyze last 30 days only')

    args = parser.parse_args()

    print("Loading data from dual_pass_analysis...")

    try:
        errors = fetch_pass2_errors(recent_only=args.recent)
        all_trades = fetch_all_trades(recent_only=args.recent)
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return 1

    if not all_trades:
        print("No trades found in dual_pass_analysis table.")
        print("Run validation first: python run_monthly_validation.py")
        return 1

    print(f"Found {len(errors)} errors out of {len(all_trades)} trades")
    print()

    # Analyze
    analysis = analyze_errors(errors, all_trades)

    # Generate report
    report = format_report(analysis, args.recent)

    # Output
    print(report)

    if args.output:
        output_path = Path(args.output)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\nReport saved to: {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
