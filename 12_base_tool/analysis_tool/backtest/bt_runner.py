"""
================================================================================
EPOCH TRADING SYSTEM - BACKTEST SEQUENTIAL RUNNER
================================================================================
Executes backtest modules in sequence with validation between each step.
Generates individual .txt reports per worksheet for Claude AI analysis.

Modules:
    1. Backtest Runner - Generates trades from zones
    2. Options Runner - Fetches options data and calculates R-multiples

Note: Trade Bars and Optimal Trade modules have been deprecated.
      The new optimal_trade calculation is in:
      09_backtest/processor/secondary_analysis/optimal_trade/
      Run separately via: python runner.py

Output:
    - Excel worksheets updated in epoch_v1.xlsm
    - Individual reports saved to results/:
        - backtest_MMDDYY_bt_report.txt
        - options_analysis_MMDDYY_bt_report.txt

Usage:
    python bt_runner.py

v3.0.0: Removed Trade Bars and Optimal Trade modules (deprecated)
        Now only runs Backtest and Options Analysis
v2.0.0: Removed entry_events and exit_events modules
        Added trade_bars module
        optimal_trade now sources from trade_bars
================================================================================
"""

import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Tuple, Optional, Dict
from dataclasses import dataclass

import xlwings as xw

from backtest_bt_report import BacktestReportGenerator
from options_analysis_bt_report import OptionsAnalysisReportGenerator


# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_DIR = Path(__file__).parent
WORKBOOK_NAME = "epoch_v1.xlsm"

# Module definitions: (name, script_path, entry_function)
# v3.0.0: Removed Trade Bars and Optimal Trade (deprecated - see secondary_analysis/optimal_trade/)
MODULES = [
    ("Backtest", BASE_DIR / "backtest_runner.py", "main"),
    ("Options Analysis", BASE_DIR / "processor" / "options_analysis" / "options_runner.py", "run_options_analysis"),
]


# ============================================================================
# VALIDATION DEFINITIONS
# ============================================================================

@dataclass
class ValidationRule:
    """Defines a cell validation rule."""
    worksheet: str
    range_start: str
    range_end: str
    min_populated: int
    description: str


# Validation rules for each module
# v3.0.0: Removed Trade Bars and Optimal Trade validation rules
VALIDATION_RULES: Dict[str, list] = {
    "Backtest": [
        ValidationRule("backtest", "A2", "U2", 1, "Trade data rows (21 cols, A-U)"),
    ],
    "Options Analysis": [
        ValidationRule("options_analysis", "A2", "V2", 1, "Options analysis data (22 cols, A-V)"),
    ],
}


# ============================================================================
# HELPER CLASSES
# ============================================================================

class ExcelValidator:
    """Validates Excel cell populations after module execution."""

    def __init__(self, workbook_name: str):
        self.workbook_name = workbook_name
        self._wb = None

    def connect(self) -> bool:
        """Connect to the Excel workbook."""
        try:
            self._wb = xw.books[self.workbook_name]
            return True
        except Exception as e:
            print(f"  [ERROR] Failed to connect to Excel: {e}")
            return False

    def close(self):
        """Close connection (but don't close the workbook)."""
        self._wb = None

    def validate_rules(self, rules: list) -> Tuple[bool, list]:
        """
        Validate all rules for a module.

        Returns:
            Tuple of (success, list of validation messages)
        """
        if not self._wb:
            return False, ["Excel connection not established"]

        messages = []
        all_passed = True

        for rule in rules:
            try:
                ws = self._wb.sheets[rule.worksheet]
                range_obj = ws.range(f"{rule.range_start}:{rule.range_end}")
                values = range_obj.value

                # Handle single cell vs range
                if not isinstance(values, list):
                    values = [[values]]
                elif values and not isinstance(values[0], list):
                    values = [values]

                # Count populated cells
                populated = 0
                total = 0
                for row in values:
                    if row is None:
                        continue
                    for cell in row:
                        total += 1
                        if cell is not None and str(cell).strip() != "":
                            populated += 1

                if populated >= rule.min_populated:
                    messages.append(f"  [OK] {rule.description}: {populated}/{total} cells populated")
                else:
                    messages.append(f"  [FAIL] {rule.description}: {populated}/{total} cells (need {rule.min_populated}+)")
                    all_passed = False

            except Exception as e:
                messages.append(f"  [ERROR] {rule.description}: {e}")
                all_passed = False

        return all_passed, messages


class ModuleRunner:
    """Runs individual backtest modules."""

    @staticmethod
    def run_module(script_path: Path, entry_function: str) -> Tuple[bool, str]:
        """
        Run a module by importing and calling its entry function.

        Returns:
            Tuple of (success, output/error message)
        """
        if not script_path.exists():
            return False, f"Script not found: {script_path}"

        # Add module directory to path
        module_dir = str(script_path.parent)
        if module_dir not in sys.path:
            sys.path.insert(0, module_dir)

        try:
            # Import the module
            module_name = script_path.stem

            # Clear any previously imported version
            if module_name in sys.modules:
                del sys.modules[module_name]

            import importlib.util
            spec = importlib.util.spec_from_file_location(module_name, script_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            # Get and call the entry function
            if not hasattr(module, entry_function):
                return False, f"Entry function '{entry_function}' not found in {module_name}"

            func = getattr(module, entry_function)
            func()

            return True, "Completed successfully"

        except SystemExit as e:
            # Handle sys.exit() calls from modules
            if e.code == 0 or e.code is None:
                return True, "Completed successfully"
            else:
                return False, f"Module exited with code {e.code}"
        except Exception as e:
            import traceback
            return False, f"Error: {e}\n{traceback.format_exc()}"
        finally:
            # Remove module directory from path
            if module_dir in sys.path:
                sys.path.remove(module_dir)


# ============================================================================
# MAIN RUNNER
# ============================================================================

class BacktestRunner:
    """Main orchestrator for the backtest pipeline."""

    def __init__(self):
        self.validator = ExcelValidator(WORKBOOK_NAME)
        self.start_time = None
        self.module_times: Dict[str, float] = {}
        self.validation_results: Dict[str, str] = {}
        self.failed_modules: list = []

    def print_header(self):
        """Print the runner header."""
        print("\n" + "=" * 70)
        print("EPOCH BACKTEST SYSTEM - SEQUENTIAL RUNNER v3.0.0")
        print("=" * 70)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Workbook: {WORKBOOK_NAME}")
        print(f"Modules: {len(MODULES)}")
        print("=" * 70 + "\n")

    def print_summary(self, completed: int, failed_module: Optional[str] = None):
        """Print the final summary."""
        elapsed = time.time() - self.start_time

        print("\n" + "=" * 70)
        print("EXECUTION SUMMARY")
        print("=" * 70)

        if failed_module:
            print(f"Status: FAILED at module '{failed_module}'")
            print(f"Completed: {completed}/{len(MODULES)} modules")
            self.failed_modules.append(failed_module)
        else:
            print(f"Status: SUCCESS")
            print(f"Completed: {completed}/{len(MODULES)} modules")

        print(f"\nModule Timings:")
        for name, duration in self.module_times.items():
            print(f"  {name}: {duration:.1f}s")

        print(f"\nTotal Time: {elapsed:.1f}s")
        print("=" * 70 + "\n")

    def get_execution_summary(self, completed: int, failed_module: Optional[str] = None) -> Dict:
        """Build execution summary dictionary for report generation."""
        elapsed = time.time() - self.start_time if self.start_time else 0

        return {
            "status": "FAILED" if failed_module else "SUCCESS",
            "completed": completed,
            "total_modules": len(MODULES),
            "total_time": elapsed,
            "module_times": self.module_times.copy(),
            "validation_results": self.validation_results.copy(),
            "failed_modules": self.failed_modules.copy(),
        }

    def generate_report(self, completed: int, failed_module: Optional[str] = None):
        """Generate individual analysis reports for each worksheet."""
        print("\n" + "=" * 70)
        print("GENERATING ANALYSIS REPORTS")
        print("=" * 70)

        report_paths = []

        # Generate backtest report
        try:
            generator = BacktestReportGenerator(WORKBOOK_NAME)
            path = generator.save_report()
            if path:
                report_paths.append(path)
        except Exception as e:
            print(f"  [WARNING] Could not generate backtest report: {e}")

        # Generate options_analysis report
        try:
            generator = OptionsAnalysisReportGenerator(WORKBOOK_NAME)
            path = generator.save_report()
            if path:
                report_paths.append(path)
        except Exception as e:
            print(f"  [WARNING] Could not generate options_analysis report: {e}")

        if report_paths:
            print(f"\n{len(report_paths)} analysis reports ready for Claude AI review:")
            for path in report_paths:
                print(f"  - {path}")
        else:
            print("\nWarning: Could not generate any analysis reports.")

    def run(self) -> bool:
        """
        Execute all modules in sequence.

        Returns:
            True if all modules completed successfully, False otherwise.
        """
        self.print_header()
        self.start_time = time.time()

        # Connect to Excel for validation
        print("Connecting to Excel workbook...")
        if not self.validator.connect():
            print(f"[FATAL] Cannot connect to Excel workbook '{WORKBOOK_NAME}'. Aborting.")
            print(f"Make sure {WORKBOOK_NAME} is open in Excel.")
            return False
        print("Connected.\n")

        completed = 0

        try:
            for idx, (name, script_path, entry_func) in enumerate(MODULES, 1):
                print("-" * 70)
                print(f"MODULE {idx}/{len(MODULES)}: {name}")
                print("-" * 70)
                print(f"Script: {script_path}")
                print(f"Entry: {entry_func}()")
                print()

                # Run the module
                module_start = time.time()
                print(f"Executing...")
                success, message = ModuleRunner.run_module(script_path, entry_func)
                module_elapsed = time.time() - module_start
                self.module_times[name] = module_elapsed

                if not success:
                    print(f"\n[FAILED] Module execution failed:")
                    print(message)
                    self.print_summary(completed, name)
                    self.generate_report(completed, name)
                    return False

                print(f"\nExecution completed in {module_elapsed:.1f}s")

                # Validate outputs
                rules = VALIDATION_RULES.get(name, [])
                if rules:
                    print(f"\nValidating outputs...")
                    valid, messages = self.validator.validate_rules(rules)
                    for msg in messages:
                        print(msg)

                    # Track validation result
                    self.validation_results[name] = "PASSED" if valid else "FAILED"

                    if not valid:
                        print(f"\n[FAILED] Validation failed for {name}")
                        self.print_summary(completed, name)
                        self.generate_report(completed, name)
                        return False

                    print(f"\nValidation passed.")
                else:
                    print(f"\nNo validation rules defined.")
                    self.validation_results[name] = "NO RULES"

                completed += 1
                print()

            self.print_summary(completed)
            self.generate_report(completed)
            return True

        finally:
            self.validator.close()


# ============================================================================
# ENTRY POINT
# ============================================================================

def main():
    """Main entry point."""
    runner = BacktestRunner()
    success = runner.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
