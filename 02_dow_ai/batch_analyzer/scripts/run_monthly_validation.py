#!/usr/bin/env python3
"""
DOW AI v3.0 Monthly Validation Runner
Epoch Trading System - XIII Trading LLC

VALIDATION MODE: Dual-pass analysis on 500 randomly sampled trades.
- Runs both Pass 1 (Trader's Eye) and Pass 2 (System Decision)
- Stores results in dual_pass_analysis table
- Used monthly to validate Pass 2 accuracy after instruction updates

This script wraps batch_analyze_v3.py with validation-specific settings.

Usage:
    python run_monthly_validation.py                    # Run on 500 random trades
    python run_monthly_validation.py --trades 250      # Custom sample size
    python run_monthly_validation.py --dry-run         # Preview without API calls
    python run_monthly_validation.py --recent-only     # Only trades from last 30 days
"""

import subprocess
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta

SCRIPT_DIR = Path(__file__).parent.resolve()


def main():
    parser = argparse.ArgumentParser(description="DOW AI v3.0 Monthly Validation")
    parser.add_argument('--trades', type=int, default=500, help='Number of trades to validate (default: 500)')
    parser.add_argument('--dry-run', action='store_true', help='Preview without API calls')
    parser.add_argument('--recent-only', action='store_true', help='Only trades from last 30 days')
    parser.add_argument('--reprocess', action='store_true', help='Re-validate already analyzed trades')
    parser.add_argument('--ticker', type=str, help='Filter by ticker')
    parser.add_argument('--direction', type=str, choices=['LONG', 'SHORT'], help='Filter by direction')
    parser.add_argument('--model', type=str, help='Filter by model')

    args = parser.parse_args()

    # Header
    print("=" * 80)
    print("DOW AI v3.0 MONTHLY VALIDATION")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("PURPOSE: Validate Pass 2 accuracy after instruction updates")
    print("- Runs dual-pass (Pass 1 + Pass 2) on sampled trades")
    print("- Compares Pass 1 vs Pass 2 accuracy")
    print("- Results stored in dual_pass_analysis table")
    print("=" * 80)
    print()

    # Build command
    batch_script = SCRIPT_DIR / "batch_analyze_v3.py"

    cmd = [
        sys.executable,
        str(batch_script),
        '--limit', str(args.trades),
        '--save-results',
    ]

    # Add filters
    if args.dry_run:
        cmd.append('--dry-run')

    if args.reprocess:
        cmd.append('--reprocess')

    if args.recent_only:
        # Last 30 days
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        cmd.extend(['--start-date', str(start_date)])
        cmd.extend(['--end-date', str(end_date)])

    if args.ticker:
        cmd.extend(['--ticker', args.ticker])

    if args.direction:
        cmd.extend(['--direction', args.direction])

    if args.model:
        cmd.extend(['--model', args.model])

    # Show command
    print("Running validation with command:")
    print(f"  {' '.join(cmd)}")
    print()

    # Execute
    result = subprocess.run(cmd)

    # Summary
    print()
    print("=" * 80)
    if result.returncode == 0:
        print("VALIDATION COMPLETE")
        print()
        print("NEXT STEPS:")
        print("1. Review dual_pass_analysis table for accuracy metrics")
        print("2. Run error analysis: python analyze_pass2_errors.py")
        print("3. Update ai_context files if Pass 2 accuracy dropped")
        print("4. Re-run validation after updates to confirm improvement")
    else:
        print("VALIDATION FAILED")
        print(f"Exit code: {result.returncode}")
    print("=" * 80)

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
