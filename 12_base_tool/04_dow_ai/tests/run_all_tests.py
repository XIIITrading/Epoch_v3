"""
DOW AI - Master Test Runner
Epoch Trading System v1 - XIII Trading LLC

Runs all test modules in sequence.

Run: python tests/run_all_tests.py

Options:
    --skip-excel     Skip tests requiring Excel
    --skip-claude    Skip tests requiring Claude API
    --quick          Only run fast tests (skip integration)
"""
import sys
import os
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DEBUG_DIR


def run_test_module(module_name: str, description: str) -> bool:
    """
    Run a test module and return success status.

    Args:
        module_name: Name of test module (e.g., 'test_polygon_fetcher')
        description: Human-readable description

    Returns:
        True if all tests passed, False otherwise
    """
    print(f"\n{'='*60}")
    print(f"RUNNING: {description}")
    print(f"{'='*60}")

    try:
        # Import and run the test module
        module = __import__(module_name)

        # Find the test class (naming convention: Test<ModuleName>)
        test_class_name = None
        for name in dir(module):
            if name.startswith('Test') and name != 'Test':
                test_class_name = name
                break

        if test_class_name:
            test_class = getattr(module, test_class_name)
            tester = test_class()
            return tester.run_all()
        else:
            print(f"  No test class found in {module_name}")
            return False

    except Exception as e:
        print(f"  ERROR running {module_name}: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("DOW AI - MASTER TEST SUITE")
    print("="*70)
    print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Parse command line args
    skip_excel = '--skip-excel' in sys.argv
    skip_claude = '--skip-claude' in sys.argv
    quick_mode = '--quick' in sys.argv

    if skip_excel:
        print("NOTE: Skipping Excel tests (--skip-excel)")
    if skip_claude:
        print("NOTE: Skipping Claude tests (--skip-claude)")
    if quick_mode:
        print("NOTE: Quick mode - skipping integration tests (--quick)")

    results = []

    # Test 1: Polygon Fetcher
    print("\n[1/7] Polygon Fetcher Tests")
    success = run_test_module('test_polygon_fetcher', 'Polygon API Data Fetching')
    results.append(('Polygon Fetcher', success))

    # Test 2: Epoch Reader (requires Excel)
    if not skip_excel:
        print("\n[2/7] Epoch Reader Tests")
        print("  NOTE: Requires epoch_v1.xlsm to be open!")
        success = run_test_module('test_epoch_reader', 'Excel Workbook Reading')
        results.append(('Epoch Reader', success))
    else:
        print("\n[2/7] Epoch Reader Tests - SKIPPED")
        results.append(('Epoch Reader', None))

    # Test 3: Market Structure
    print("\n[3/7] Market Structure Tests")
    success = run_test_module('test_market_structure', 'BOS/ChoCH Calculation')
    results.append(('Market Structure', success))

    # Test 4: Volume Analysis
    print("\n[4/7] Volume Analysis Tests")
    success = run_test_module('test_volume_analysis', 'Volume Delta/ROC/CVD')
    results.append(('Volume Analysis', success))

    # Test 5: Pattern Detection
    print("\n[5/7] Pattern Detection Tests")
    success = run_test_module('test_patterns', 'Candlestick Patterns')
    results.append(('Pattern Detection', success))

    # Test 6: Claude Client (requires API)
    if not skip_claude:
        print("\n[6/7] Claude Client Tests")
        success = run_test_module('test_claude_client', 'Claude API Integration')
        results.append(('Claude Client', success))
    else:
        print("\n[6/7] Claude Client Tests - SKIPPED")
        results.append(('Claude Client', None))

    # Test 7: Aggregator (integration - requires everything)
    if not quick_mode and not skip_excel and not skip_claude:
        print("\n[7/7] Aggregator Integration Tests")
        print("  NOTE: Requires epoch_v1.xlsm to be open!")
        success = run_test_module('test_aggregator', 'Full Analysis Pipeline')
        results.append(('Aggregator', success))
    else:
        print("\n[7/7] Aggregator Tests - SKIPPED")
        results.append(('Aggregator', None))

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = 0
    failed = 0
    skipped = 0

    for name, success in results:
        if success is None:
            status = "SKIPPED"
            skipped += 1
            style = ""
        elif success:
            status = "PASSED"
            passed += 1
            style = ""
        else:
            status = "FAILED"
            failed += 1
            style = ""

        print(f"  {name:<25} {status}")

    print("-"*70)
    print(f"  TOTAL: {passed} passed, {failed} failed, {skipped} skipped")
    print("="*70)

    # Write summary report
    report_path = DEBUG_DIR / f"test_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_path, 'w') as f:
        f.write("DOW AI TEST SUMMARY REPORT\n")
        f.write("="*60 + "\n\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        for name, success in results:
            if success is None:
                status = "SKIPPED"
            elif success:
                status = "PASSED"
            else:
                status = "FAILED"
            f.write(f"{name:<25} {status}\n")

        f.write("\n" + "-"*60 + "\n")
        f.write(f"TOTAL: {passed} passed, {failed} failed, {skipped} skipped\n")

    print(f"\nReport saved to: {report_path}")

    # Exit with appropriate code
    if failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    # Change to tests directory
    os.chdir(Path(__file__).parent)
    main()
