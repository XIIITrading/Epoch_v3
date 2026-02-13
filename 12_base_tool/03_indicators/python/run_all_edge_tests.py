"""
Master Edge Test Runner
Epoch Trading System v1 - XIII Trading LLC

Runs all indicator edge tests in sequence and generates consolidated reports.
Each indicator test saves its own .md file to its results/ directory.

Usage:
    python run_all_edge_tests.py                    # Run all tests with defaults
    python run_all_edge_tests.py --date-from 2026-01-01
    python run_all_edge_tests.py --stop-type zone_buffer
    python run_all_edge_tests.py --indicators candle_range,volume_delta
    python run_all_edge_tests.py --quiet            # Minimal console output

Output:
    - Individual .md reports in each indicator's results/ folder
    - Summary report in 03_indicators/python/results/
"""

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import traceback
import re

# Base directory for indicators
BASE_DIR = Path(__file__).parent


# ============================================================================
# INDICATOR REGISTRY
# ============================================================================

INDICATORS = {
    'candle_range': {
        'name': 'Candle Range',
        'module': 'candle_range.candle_range_edge',
        'description': 'Tests candle range thresholds and absorption zone filter',
        'calc_id': 'CALC-011'
    },
    'volume_delta': {
        'name': 'Volume Delta',
        'module': 'volume_delta.volume_delta_edge',
        'description': 'Tests volume delta sign, alignment, and magnitude',
        'calc_id': 'CALC-011'
    },
    'volume_roc': {
        'name': 'Volume ROC',
        'module': 'volume_roc.volume_roc_edge',
        'description': 'Tests volume rate of change thresholds',
        'calc_id': 'CALC-011'
    },
    'cvd_slope': {
        'name': 'CVD Slope',
        'module': 'cvd_slope.cvd_slope_edge',
        'description': 'Tests cumulative volume delta slope direction',
        'calc_id': 'CALC-011'
    },
    'sma_edge': {
        'name': 'SMA Analysis',
        'module': 'sma_edge.sma_edge',
        'description': 'Tests SMA spread, momentum, and alignment',
        'calc_id': 'CALC-011'
    },
    'structure_edge': {
        'name': 'Market Structure',
        'module': 'structure_edge.structure_edge',
        'description': 'Tests H1/M15 structure direction and alignment',
        'calc_id': 'CALC-011'
    },
    'vwap_simple': {
        'name': 'VWAP Simple',
        'module': 'vwap_simple.vwap_edge',
        'description': 'Tests VWAP position and alignment',
        'calc_id': 'CALC-011'
    }
}

# Default run order (strongest edges first based on validation)
DEFAULT_ORDER = [
    'candle_range',     # Strongest - 18-29pp edge
    'structure_edge',   # Strong - 24-54pp edge on H1
    'cvd_slope',        # Strong for SHORT - 15-27pp edge
    'volume_delta',     # Good - 10-20pp edge
    'sma_edge',         # Good - 19-25pp edge
    'volume_roc',       # Moderate edge
    'vwap_simple'       # Paradoxical - on hold
]


# ============================================================================
# RUNNER FUNCTIONS
# ============================================================================

def run_single_indicator(
    indicator_key: str,
    models: List[str] = None,
    directions: List[str] = None,
    date_from: str = None,
    date_to: str = None,
    stop_type: str = 'zone_buffer',
    quiet: bool = False
) -> Tuple[bool, Optional[str], Optional[Dict]]:
    """
    Run edge tests for a single indicator using subprocess.

    Each indicator module saves reports to its own results/ directory.

    Returns:
        (success: bool, report_path: str or None, metadata: dict or None)
    """
    info = INDICATORS[indicator_key]

    if not quiet:
        print(f"\n{'='*80}")
        print(f"  {info['calc_id']}: {info['name'].upper()} EDGE ANALYSIS")
        print(f"  {info['description']}")
        print(f"{'='*80}")

    # Build command
    cmd = [sys.executable, '-m', info['module']]

    if models:
        cmd.extend(['--models', ','.join(models)])
    if directions:
        cmd.extend(['--direction', directions[0]])  # CLI only accepts single direction
    if date_from:
        cmd.extend(['--date-from', date_from])
    if date_to:
        cmd.extend(['--date-to', date_to])
    if stop_type:
        cmd.extend(['--stop-type', stop_type])

    try:
        # Run the indicator edge test
        result = subprocess.run(
            cmd,
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout per indicator
        )

        # Parse output for report path and stats
        output = result.stdout + result.stderr

        # Extract report path from output
        report_path = None
        report_match = re.search(r'Report saved to: (.+\.md)', output)
        if report_match:
            report_path = report_match.group(1).strip()

        # Extract trade count
        total_trades = None
        trades_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s+trades', output)
        if trades_match:
            total_trades = int(trades_match.group(1).replace(',', ''))

        # Extract baseline win rate
        baseline_wr = None
        wr_match = re.search(r'Baseline Win Rate:\s*([\d.]+)%', output)
        if wr_match:
            baseline_wr = float(wr_match.group(1))

        # Extract edges found
        edges_found = 0
        edges_match = re.search(r'EDGES DETECTED:', output)
        if edges_match:
            # Count lines starting with [+]
            edges_found = output.count('[+]')

        if result.returncode == 0:
            if not quiet:
                print(output)
                if edges_found > 0:
                    print(f"\n  ✓ {edges_found} edges detected")
                else:
                    print(f"\n  ✓ Completed (no significant edges)")

            metadata = {
                'total_trades': total_trades,
                'baseline_win_rate': baseline_wr,
                'edges_found': edges_found
            }
            return True, report_path, metadata
        else:
            if not quiet:
                print(f"\n  ✗ FAILED (exit code {result.returncode})")
                print(output)
            return False, None, None

    except subprocess.TimeoutExpired:
        if not quiet:
            print(f"\n  ✗ TIMEOUT (exceeded 5 minutes)")
        return False, None, None
    except Exception as e:
        if not quiet:
            print(f"\n  ✗ ERROR: {str(e)}")
            traceback.print_exc()
        return False, None, None


def run_all_indicators(
    indicators: List[str] = None,
    models: List[str] = None,
    directions: List[str] = None,
    date_from: str = None,
    date_to: str = None,
    stop_type: str = 'zone_buffer',
    quiet: bool = False
) -> Dict:
    """
    Run edge tests for all (or specified) indicators.

    Returns:
        Summary dict with results for each indicator
    """
    if indicators is None:
        indicators = DEFAULT_ORDER

    # Validate indicator keys
    for ind in indicators:
        if ind not in INDICATORS:
            raise ValueError(f"Unknown indicator: {ind}. Valid options: {list(INDICATORS.keys())}")

    start_time = datetime.now()

    print("\n" + "=" * 80)
    print("           EPOCH INDICATOR EDGE TEST RUNNER")
    print("=" * 80)
    print(f"\n  Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Indicators: {len(indicators)}")
    print(f"  Stop Type: {stop_type}")
    if date_from:
        print(f"  Date From: {date_from}")
    if date_to:
        print(f"  Date To: {date_to}")
    if models:
        print(f"  Models: {', '.join(models)}")
    if directions:
        print(f"  Directions: {', '.join(directions)}")

    # Run each indicator
    summary = {
        'run_timestamp': start_time.isoformat(),
        'stop_type': stop_type,
        'filters': {
            'models': models,
            'directions': directions,
            'date_from': date_from,
            'date_to': date_to
        },
        'indicators': {}
    }

    successful = 0
    failed = 0

    for i, indicator_key in enumerate(indicators, 1):
        print(f"\n[{i}/{len(indicators)}] Running {INDICATORS[indicator_key]['name']}...")

        success, report_path, metadata = run_single_indicator(
            indicator_key=indicator_key,
            models=models,
            directions=directions,
            date_from=date_from,
            date_to=date_to,
            stop_type=stop_type,
            quiet=quiet
        )

        summary['indicators'][indicator_key] = {
            'name': INDICATORS[indicator_key]['name'],
            'success': success,
            'report_path': report_path,
            'total_trades': metadata.get('total_trades') if metadata else None,
            'baseline_win_rate': metadata.get('baseline_win_rate') if metadata else None,
            'edges_found': metadata.get('edges_found', 0) if metadata else 0
        }

        if success:
            successful += 1
        else:
            failed += 1

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    summary['duration_seconds'] = duration
    summary['successful'] = successful
    summary['failed'] = failed

    # Print final summary
    print("\n" + "=" * 80)
    print("                         EXECUTION SUMMARY")
    print("=" * 80)
    print(f"\n  Completed: {successful}/{len(indicators)} indicators")
    if failed > 0:
        print(f"  Failed: {failed}")
    print(f"  Duration: {duration:.1f} seconds")
    print(f"\n  Reports saved to individual indicator results/ folders")

    # Save summary report
    summary_report = generate_summary_report(summary)
    summary_path = save_summary_report(summary_report)
    print(f"  Summary report: {summary_path}")

    print("\n" + "=" * 80 + "\n")

    return summary


def generate_summary_report(summary: Dict) -> str:
    """Generate a markdown summary of all edge test runs."""
    lines = [
        "# Edge Test Run Summary",
        "",
        f"**Run Timestamp:** {summary['run_timestamp']}",
        f"**Duration:** {summary['duration_seconds']:.1f} seconds",
        f"**Stop Type:** {summary['stop_type']}",
        "",
    ]

    # Filters
    filters = summary['filters']
    if any(filters.values()):
        lines.append("## Filters Applied")
        if filters['date_from']:
            lines.append(f"- Date From: {filters['date_from']}")
        if filters['date_to']:
            lines.append(f"- Date To: {filters['date_to']}")
        if filters['models']:
            lines.append(f"- Models: {', '.join(filters['models'])}")
        if filters['directions']:
            lines.append(f"- Directions: {', '.join(filters['directions'])}")
        lines.append("")

    # Results table
    lines.extend([
        "## Results by Indicator",
        "",
        "| Indicator | Status | Trades | Baseline WR | Edges | Report |",
        "|-----------|--------|--------|-------------|-------|--------|"
    ])

    total_edges = 0
    for key, data in summary['indicators'].items():
        status = "✓ SUCCESS" if data['success'] else "✗ FAILED"
        trades = f"{data['total_trades']:,}" if data['total_trades'] else "-"
        wr = f"{data['baseline_win_rate']:.1f}%" if data['baseline_win_rate'] else "-"
        edges = data.get('edges_found', 0)
        total_edges += edges
        report = Path(data['report_path']).name if data['report_path'] else "-"
        lines.append(f"| {data['name']} | {status} | {trades} | {wr} | {edges} | {report} |")

    lines.extend([
        "",
        "---",
        "",
        f"**Successful:** {summary['successful']}/{summary['successful'] + summary['failed']}",
        f"**Total Edges Detected:** {total_edges}",
        "",
        "---",
        "",
        "*Run `python run_all_edge_tests.py --list` to see available indicators.*",
        ""
    ])

    return "\n".join(lines)


def save_summary_report(report: str) -> str:
    """Save the summary report to the results directory."""
    results_dir = BASE_DIR / "results"
    results_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"edge_test_summary_{timestamp}.md"
    filepath = results_dir / filename

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(report)

    return str(filepath)


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Run all indicator edge tests and generate reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_all_edge_tests.py
    python run_all_edge_tests.py --indicators candle_range,volume_delta
    python run_all_edge_tests.py --date-from 2026-01-01 --date-to 2026-01-21
    python run_all_edge_tests.py --models EPCH01,EPCH02 --direction LONG
    python run_all_edge_tests.py --stop-type zone_buffer --quiet

Available indicators:
    candle_range    - Candle range thresholds and absorption zone
    volume_delta    - Volume delta sign, alignment, magnitude
    volume_roc      - Volume rate of change
    cvd_slope       - Cumulative volume delta slope
    sma_edge        - SMA spread and alignment
    structure_edge  - H1/M15 market structure
    vwap_simple     - VWAP position
        """
    )

    parser.add_argument(
        '--indicators',
        type=str,
        default=None,
        help='Comma-separated list of indicators to run (default: all)'
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
        '--quiet',
        action='store_true',
        help='Minimal console output'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List available indicators and exit'
    )

    args = parser.parse_args()

    # List mode
    if args.list:
        print("\nAvailable Indicators:")
        print("-" * 60)
        for key, info in INDICATORS.items():
            print(f"  {key:20} - {info['description']}")
        print()
        return

    # Parse arguments
    indicators = args.indicators.split(',') if args.indicators else None
    models = args.models.split(',') if args.models else None
    directions = [args.direction] if args.direction else None

    # Run
    summary = run_all_indicators(
        indicators=indicators,
        models=models,
        directions=directions,
        date_from=args.date_from,
        date_to=args.date_to,
        stop_type=args.stop_type,
        quiet=args.quiet
    )

    # Exit with error code if any failed
    if summary['failed'] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
