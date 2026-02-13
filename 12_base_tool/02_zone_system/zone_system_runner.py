"""
Zone System Sequential Runner
=============================
Executes all 9 zone system modules in sequence with validation between each step.

Modules:
    1. Market Structure Runner - Fixed tickers (SPY, QQQ, DIA)
    2. Ticker Structure Runner - Dynamic tickers from market_overview
    3. Bar Data Runner - Fetches all bar data metrics
    4. HVN Runner - Identifies High Volume Nodes
    5. Raw Zones Runner - Generates zone candidates
    6. Zone Results Runner - Filters and ranks zones
    7. Setup Runner - Analyzes setups and targets
    8. Summary Exporter - Exports to Analysis sheet
    9. Pre-Market Analysis - Generates PDF report

Usage:
    python zone_system_runner.py
"""

import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Tuple, List, Optional, Dict, Any
from dataclasses import dataclass

import xlwings as xw


# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_DIR = Path(r"C:\XIIITradingSystems\Epoch\02_zone_system")
EXCEL_FILEPATH = Path(r"C:\XIIITradingSystems\Epoch\epoch_v1.xlsm")

# Module definitions: (name, script_path, entry_function)
MODULES = [
    ("Market Structure", BASE_DIR / "01_market_structure" / "market_structure_runner.py", "run"),
    ("Ticker Structure", BASE_DIR / "02_ticker_structure" / "ticker_structure_runner.py", "run"),
    ("Bar Data", BASE_DIR / "03_bar_data" / "bar_data_runner.py", "run"),
    ("HVN Identifier", BASE_DIR / "04_hvn_identifier" / "hvn_runner.py", "run"),
    ("Raw Zones", BASE_DIR / "05_raw_zones" / "raw_zones_runner.py", "main"),
    ("Zone Results", BASE_DIR / "06_zone_results" / "zone_results_runner.py", "run"),
    ("Setup Analysis", BASE_DIR / "07_setup_analysis" / "setup_runner.py", "run"),
    ("Summary Exporter", BASE_DIR / "08_visualization" / "summary_exporter.py", "main"),
    ("Pre-Market Analysis", BASE_DIR / "08_visualization" / "pre_market_analysis.py", "generate_report"),
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
VALIDATION_RULES: Dict[str, List[ValidationRule]] = {
    "Market Structure": [
        ValidationRule("market_overview", "C29", "C31", 3, "Fixed tickers (SPY, QQQ, DIA)"),
        ValidationRule("market_overview", "F29", "R31", 9, "Market structure columns (D1/H4/H1/M15)"),
    ],
    "Ticker Structure": [
        ValidationRule("market_overview", "C36", "C45", 1, "Dynamic tickers"),
        ValidationRule("market_overview", "F36", "R45", 1, "Ticker structure data"),
    ],
    "Bar Data": [
        ValidationRule("bar_data", "B4", "E13", 4, "Ticker structure section"),
        ValidationRule("bar_data", "E17", "L26", 8, "Monthly metrics"),
        ValidationRule("bar_data", "E31", "L40", 8, "Weekly metrics"),
        ValidationRule("bar_data", "E45", "L54", 8, "Daily metrics"),
        ValidationRule("bar_data", "Q73", "T82", 4, "ATR values"),
    ],
    "HVN Identifier": [
        ValidationRule("bar_data", "F59", "O68", 1, "HVN POC values"),
    ],
    "Raw Zones": [
        ValidationRule("raw_zones", "A2", "L2", 1, "Zone data rows"),
    ],
    "Zone Results": [
        ValidationRule("zone_results", "A2", "N2", 1, "Filtered zone data"),
    ],
    "Setup Analysis": [
        ValidationRule("Analysis", "B31", "L40", 1, "Primary setups"),
    ],
    "Summary Exporter": [
        ValidationRule("Analysis", "B3", "Z12", 10, "Summary table 1"),
    ],
    "Pre-Market Analysis": [
        # PDF generation - validation is just that the module completes
    ],
}


# ============================================================================
# HELPER CLASSES
# ============================================================================

class ExcelValidator:
    """Validates Excel cell populations after module execution."""

    def __init__(self, workbook_path: Path):
        self.workbook_path = workbook_path
        self._wb = None

    def connect(self) -> bool:
        """Connect to the Excel workbook."""
        try:
            self._wb = xw.Book(str(self.workbook_path))
            return True
        except Exception as e:
            print(f"  [ERROR] Failed to connect to Excel: {e}")
            return False

    def close(self):
        """Close connection (but don't close the workbook)."""
        self._wb = None

    def validate_rules(self, rules: List[ValidationRule]) -> Tuple[bool, List[str]]:
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
    """Runs individual zone system modules."""

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

        # Track modules loaded BEFORE this run
        modules_before = set(sys.modules.keys())

        try:
            # Import the module
            module_name = script_path.stem

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

        except Exception as e:
            import traceback
            return False, f"Error: {e}\n{traceback.format_exc()}"
        finally:
            # Remove module directory from path
            if module_dir in sys.path:
                sys.path.remove(module_dir)

            # Clear ALL modules that were imported during this run
            modules_after = set(sys.modules.keys())
            new_modules = modules_after - modules_before
            for mod_name in new_modules:
                del sys.modules[mod_name]


# ============================================================================
# MAIN RUNNER
# ============================================================================

class ZoneSystemRunner:
    """Main orchestrator for the zone system pipeline."""

    def __init__(self):
        self.validator = ExcelValidator(EXCEL_FILEPATH)
        self.start_time = None
        self.module_times: Dict[str, float] = {}

    def print_header(self):
        """Print the runner header."""
        print("\n" + "=" * 70)
        print("EPOCH ZONE SYSTEM - SEQUENTIAL RUNNER")
        print("=" * 70)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Workbook: {EXCEL_FILEPATH}")
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
        else:
            print(f"Status: SUCCESS")
            print(f"Completed: {completed}/{len(MODULES)} modules")

        print(f"\nModule Timings:")
        for name, duration in self.module_times.items():
            print(f"  {name}: {duration:.1f}s")

        print(f"\nTotal Time: {elapsed:.1f}s")
        print("=" * 70 + "\n")

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
            print("[FATAL] Cannot connect to Excel workbook. Aborting.")
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
                    return False

                print(f"\nExecution completed in {module_elapsed:.1f}s")

                # Validate outputs
                rules = VALIDATION_RULES.get(name, [])
                if rules:
                    print(f"\nValidating outputs...")
                    valid, messages = self.validator.validate_rules(rules)
                    for msg in messages:
                        print(msg)

                    if not valid:
                        print(f"\n[FAILED] Validation failed for {name}")
                        self.print_summary(completed, name)
                        return False

                    print(f"\nValidation passed.")
                else:
                    print(f"\nNo validation rules defined (module output is external).")

                completed += 1
                print()

            self.print_summary(completed)
            return True

        finally:
            self.validator.close()


# ============================================================================
# ENTRY POINT
# ============================================================================

def main():
    """Main entry point."""
    runner = ZoneSystemRunner()
    success = runner.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
