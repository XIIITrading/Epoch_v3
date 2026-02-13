#!/usr/bin/env python3
"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
Master Runner - Sequential Execution
XIII Trading LLC
================================================================================

Runs all secondary analysis modules in the correct dependency order:

    1. m1_bars              - Store raw M1 bar data from Polygon
    2. h1_bars              - Store raw H1 bar data from Polygon
    3. mfe_mae              - Calculate MFE/MAE potential (entry to EOD)
    4. entry_indicators     - Calculate entry-time indicator snapshots
    5. m5_indicator_bars    - Calculate M5 indicator bars for all ticker-dates
    6. m1_indicator_bars    - Calculate M1 indicator bars for all ticker-dates
    7. m5_trade_bars        - Calculate trade-specific M5 bars with health scores
    8. optimal_trade        - Calculate optimal trade events (ENTRY, MFE, MAE, EXIT)
    9. r_level_events       - Generate R1, R2, R3 crossing events for optimal_trade
   10. options_analysis     - Calculate options performance for trades (FIRST_ITM strikes)
   11. op_mfe_mae           - Calculate options MFE/MAE potential
   12. stop_analysis        - Calculate 6 stop types and simulate outcomes (CALC-009)
   13. indicator_refinement - Calculate Continuation/Rejection scores (CALC-010)

Usage:
    python run_all.py                    # Full run of all modules
    python run_all.py --dry-run          # Test run (no database writes)
    python run_all.py --limit 10         # Limit records per module
    python run_all.py --start-from 3     # Start from step 3 (mfe_mae)
    python run_all.py --only 2           # Run only step 2 (h1_bars)
    python run_all.py --only 9           # Run only step 9 (r_level_events)
    python run_all.py --verbose          # Detailed logging

Version: 1.4.0
================================================================================
"""

import argparse
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional


# =============================================================================
# MODULE CONFIGURATION
# =============================================================================
# Order matters! Each module depends on the ones before it.

MODULES = [
    {
        'step': 1,
        'name': 'm1_bars',
        'description': 'Store raw M1 bar data from Polygon',
        'path': 'm1_bars',
        'runner': 'm1_bars_runner.py',
        'depends_on': [],
    },
    {
        'step': 2,
        'name': 'h1_bars',
        'description': 'Store raw H1 bar data from Polygon',
        'path': 'h1_bars',
        'runner': 'h1_bars_runner.py',
        'depends_on': [],
    },
    {
        'step': 3,
        'name': 'mfe_mae',
        'description': 'Calculate MFE/MAE potential (entry to EOD)',
        'path': 'mfe_mae',
        'runner': 'mfe_mae_potential_runner.py',
        'depends_on': ['m1_bars'],
    },
    {
        'step': 4,
        'name': 'entry_indicators',
        'description': 'Calculate entry-time indicator snapshots',
        'path': 'entry_indicators',
        'runner': 'runner.py',
        'depends_on': ['mfe_mae'],
    },
    {
        'step': 5,
        'name': 'm5_indicator_bars',
        'description': 'Calculate M5 indicator bars for all ticker-dates',
        'path': 'm5_indicator_bars',
        'runner': 'runner.py',
        'depends_on': [],  # Can run in parallel with entry_indicators
    },
    {
        'step': 6,
        'name': 'm1_indicator_bars',
        'description': 'Calculate M1 indicator bars for all ticker-dates',
        'path': 'm1_indicator_bars',
        'runner': 'runner.py',
        'depends_on': ['m1_bars'],  # Can run in parallel with entry_indicators, m5_indicator_bars
    },
    {
        'step': 7,
        'name': 'm5_trade_bars',
        'description': 'Calculate trade-specific M5 bars with health scores',
        'path': 'm5_trade_bars',
        'runner': 'runner.py',
        'depends_on': ['mfe_mae', 'm5_indicator_bars'],
    },
    {
        'step': 8,
        'name': 'optimal_trade',
        'description': 'Calculate optimal trade events (ENTRY, MFE, MAE, EXIT)',
        'path': 'optimal_trade',
        'runner': 'runner.py',
        'depends_on': ['mfe_mae', 'm5_trade_bars'],
    },
    {
        'step': 9,
        'name': 'r_level_events',
        'description': 'Generate R1, R2, R3 crossing events for optimal_trade',
        'path': 'r_level_events',
        'runner': 'run.py',
        'depends_on': ['optimal_trade'],
        'supports_limit': False,  # This module doesn't accept --limit
    },
    {
        'step': 10,
        'name': 'options_analysis',
        'description': 'Calculate options performance for trades (FIRST_ITM strikes)',
        'path': 'options_analysis',
        'runner': 'runner.py',
        'depends_on': [],  # Only depends on trades table, not other secondary analysis
    },
    {
        'step': 11,
        'name': 'op_mfe_mae',
        'description': 'Calculate options MFE/MAE potential',
        'path': 'op_mfe_mae',
        'runner': 'op_mfe_mae_runner.py',
        'depends_on': ['options_analysis'],
    },
    {
        'step': 12,
        'name': 'stop_analysis',
        'description': 'Calculate 6 stop types and simulate outcomes (CALC-009)',
        'path': 'stop_analysis',
        'runner': 'runner.py',
        'depends_on': ['mfe_mae', 'm1_bars', 'm5_trade_bars'],
    },
    {
        'step': 13,
        'name': 'indicator_refinement',
        'description': 'Calculate Continuation/Rejection scores (CALC-010)',
        'path': 'indicator_refinement',
        'runner': 'runner.py',
        'depends_on': ['entry_indicators', 'm5_indicator_bars'],
    },
]


# =============================================================================
# RUNNER CLASS
# =============================================================================
class SecondaryAnalysisRunner:
    """Orchestrates sequential execution of all secondary analysis modules."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.base_path = Path(__file__).parent
        self.results: List[Dict[str, Any]] = []

    def _print_header(self):
        """Print the main header."""
        print()
        print("=" * 70)
        print("EPOCH TRADING SYSTEM - SECONDARY ANALYSIS")
        print("Master Runner v1.4.0")
        print("=" * 70)
        print()
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Base Path:  {self.base_path}")
        print()

    def _print_module_list(self, start_from: int = 1, only: int = None):
        """Print the list of modules to be executed."""
        print("Execution Plan:")
        print("-" * 50)

        for module in MODULES:
            step = module['step']

            # Determine if this module will run
            if only is not None:
                will_run = step == only
            else:
                will_run = step >= start_from

            status = "[RUN]" if will_run else "[SKIP]"
            print(f"  {status} Step {step}: {module['name']}")
            print(f"         {module['description']}")

        print()

    def run_module(
        self,
        module: Dict[str, Any],
        dry_run: bool = False,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Run a single module.

        Args:
            module: Module configuration dict
            dry_run: If True, pass --dry-run to the module
            limit: If set, pass --limit to the module

        Returns:
            Result dict with success status and details
        """
        step = module['step']
        name = module['name']
        runner_path = self.base_path / module['path'] / module['runner']

        print()
        print("=" * 70)
        print(f"STEP {step}: {name.upper()}")
        print(f"  {module['description']}")
        print("=" * 70)

        # Check if runner exists
        if not runner_path.exists():
            print(f"  ERROR: Runner not found: {runner_path}")
            return {
                'step': step,
                'name': name,
                'success': False,
                'error': f'Runner not found: {runner_path}',
                'duration': 0
            }

        # Build command
        cmd = [sys.executable, str(runner_path)]

        if dry_run:
            cmd.append('--dry-run')

        # Only pass --limit if the module supports it (default: True)
        supports_limit = module.get('supports_limit', True)
        if limit and supports_limit:
            cmd.extend(['--limit', str(limit)])

        if self.verbose:
            cmd.append('--verbose')

        print(f"  Command: {' '.join(cmd)}")
        print()

        # Execute
        start_time = datetime.now()

        try:
            result = subprocess.run(
                cmd,
                cwd=str(runner_path.parent),
                capture_output=False,  # Show output in real-time
                text=True
            )

            duration = (datetime.now() - start_time).total_seconds()
            success = result.returncode == 0

            return {
                'step': step,
                'name': name,
                'success': success,
                'return_code': result.returncode,
                'duration': duration
            }

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return {
                'step': step,
                'name': name,
                'success': False,
                'error': str(e),
                'duration': duration
            }

    def run_all(
        self,
        dry_run: bool = False,
        limit: Optional[int] = None,
        start_from: int = 1,
        only: Optional[int] = None,
        stop_on_error: bool = True
    ) -> Dict[str, Any]:
        """
        Run all modules in sequence.

        Args:
            dry_run: Pass --dry-run to all modules
            limit: Pass --limit to all modules
            start_from: Start from this step number (1-6)
            only: Run only this step number
            stop_on_error: Stop execution if a module fails

        Returns:
            Summary dict with all results
        """
        self._print_header()

        print("Configuration:")
        print(f"  Dry Run:       {dry_run}")
        print(f"  Limit:         {limit if limit else 'None (all records)'}")
        print(f"  Start From:    Step {start_from}")
        print(f"  Only:          {'Step ' + str(only) if only else 'All applicable'}")
        print(f"  Stop on Error: {stop_on_error}")
        print()

        self._print_module_list(start_from, only)

        # Determine which modules to run
        modules_to_run = []
        for module in MODULES:
            step = module['step']
            if only is not None:
                if step == only:
                    modules_to_run.append(module)
            elif step >= start_from:
                modules_to_run.append(module)

        if not modules_to_run:
            print("No modules to run based on configuration.")
            return {'success': True, 'modules_run': 0, 'results': []}

        print(f"Running {len(modules_to_run)} module(s)...")

        # Run modules
        start_time = datetime.now()
        self.results = []

        for module in modules_to_run:
            result = self.run_module(module, dry_run=dry_run, limit=limit)
            self.results.append(result)

            if not result['success'] and stop_on_error:
                print()
                print("!" * 70)
                print(f"STOPPING: Step {result['step']} ({result['name']}) failed")
                print("!" * 70)
                break

        # Print summary
        total_duration = (datetime.now() - start_time).total_seconds()
        self._print_summary(total_duration)

        # Determine overall success
        all_success = all(r['success'] for r in self.results)

        return {
            'success': all_success,
            'modules_run': len(self.results),
            'modules_succeeded': sum(1 for r in self.results if r['success']),
            'modules_failed': sum(1 for r in self.results if not r['success']),
            'total_duration': total_duration,
            'results': self.results
        }

    def _print_summary(self, total_duration: float):
        """Print execution summary."""
        print()
        print()
        print("=" * 70)
        print("EXECUTION SUMMARY")
        print("=" * 70)
        print()

        # Results table
        print(f"{'Step':<6} {'Module':<20} {'Status':<10} {'Duration':<12}")
        print("-" * 50)

        for result in self.results:
            status = "OK" if result['success'] else "FAILED"
            duration = f"{result['duration']:.1f}s"
            print(f"{result['step']:<6} {result['name']:<20} {status:<10} {duration:<12}")

        print("-" * 50)
        print()

        # Totals
        succeeded = sum(1 for r in self.results if r['success'])
        failed = sum(1 for r in self.results if not r['success'])

        print(f"  Total Modules:   {len(self.results)}")
        print(f"  Succeeded:       {succeeded}")
        print(f"  Failed:          {failed}")
        print(f"  Total Duration:  {total_duration:.1f}s")
        print()

        # Final status
        if failed == 0:
            print("=" * 70)
            print("ALL MODULES COMPLETED SUCCESSFULLY")
            print("=" * 70)
        else:
            print("=" * 70)
            print(f"COMPLETED WITH {failed} FAILURE(S)")
            print("=" * 70)


# =============================================================================
# MAIN
# =============================================================================
def main():
    parser = argparse.ArgumentParser(
        description='Run all secondary analysis modules in order',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Execution Order:
  1. m1_bars              - Store raw M1 bar data from Polygon
  2. h1_bars              - Store raw H1 bar data from Polygon
  3. mfe_mae              - Calculate MFE/MAE potential (entry to EOD)
  4. entry_indicators     - Calculate entry-time indicator snapshots
  5. m5_indicator_bars    - Calculate M5 indicator bars for all ticker-dates
  6. m1_indicator_bars    - Calculate M1 indicator bars for all ticker-dates
  7. m5_trade_bars        - Calculate trade-specific M5 bars with health scores
  8. optimal_trade        - Calculate optimal trade events
  9. r_level_events       - Generate R1, R2, R3 crossing events
 10. options_analysis     - Calculate options performance for trades
 11. op_mfe_mae           - Calculate options MFE/MAE potential
 12. stop_analysis        - Calculate 6 stop types and simulate outcomes (CALC-009)
 13. indicator_refinement - Calculate Continuation/Rejection scores (CALC-010)

Examples:
  python run_all.py                    # Full run
  python run_all.py --dry-run          # Test without saving
  python run_all.py --limit 10         # Process 10 records per module
  python run_all.py --start-from 3     # Start from mfe_mae
  python run_all.py --only 2           # Run only h1_bars
  python run_all.py --only 9           # Run only r_level_events
  python run_all.py --only 12          # Run only stop_analysis
  python run_all.py --only 13          # Run only indicator_refinement
  python run_all.py --no-stop          # Continue even if a module fails
        """
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Pass --dry-run to all modules (no database writes)'
    )

    parser.add_argument(
        '--limit',
        type=int,
        metavar='N',
        help='Limit number of records per module'
    )

    parser.add_argument(
        '--start-from',
        type=int,
        choices=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13],
        default=1,
        metavar='STEP',
        help='Start from this step number (1-13)'
    )

    parser.add_argument(
        '--only',
        type=int,
        choices=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13],
        metavar='STEP',
        help='Run only this step number (1-13)'
    )

    parser.add_argument(
        '--no-stop',
        action='store_true',
        help='Continue execution even if a module fails'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging for all modules'
    )

    args = parser.parse_args()

    # Run
    runner = SecondaryAnalysisRunner(verbose=args.verbose)

    try:
        result = runner.run_all(
            dry_run=args.dry_run,
            limit=args.limit,
            start_from=args.start_from,
            only=args.only,
            stop_on_error=not args.no_stop
        )

        sys.exit(0 if result['success'] else 1)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
