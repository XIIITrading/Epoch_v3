"""
System Analysis Test Runner
Usage:
    python run_all.py --part 1        # Synthetic validation (tests 01-20)
    python run_all.py --part 2        # Edge analysis (tests 21-37)
    python run_all.py                 # Run all tests
"""
import argparse
import sys
import json
from pathlib import Path

import pytest


def main():
    parser = argparse.ArgumentParser(description="System Analysis Test Runner")
    parser.add_argument("--part", type=int, choices=[1, 2], help="Test part to run")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    test_dir = Path(__file__).parent

    pytest_args = ["-v" if args.verbose else "-q"]

    if args.part == 1:
        pytest_args.append(str(test_dir / "core_system_test"))
    elif args.part == 2:
        pytest_args.append(str(test_dir / "edge_analysis_test"))
    else:
        pytest_args.append(str(test_dir))

    pytest_args.extend(["--tb=short", "-x"])

    exit_code = pytest.main(pytest_args)

    # Summarize JSON results
    results_dir = test_dir / "results"
    if results_dir.exists():
        results = sorted(results_dir.glob("*.json"))
        if results:
            print(f"\n{'='*60}")
            print(f"JSON Results: {len(results)} files in {results_dir}")
            print(f"{'='*60}")
            passed = 0
            failed = 0
            for r in results:
                data = json.loads(r.read_text())
                status = data.get("passed")
                if status is True:
                    passed += 1
                    print(f"  PASS  {data['test_id']}")
                elif status is False:
                    failed += 1
                    print(f"  FAIL  {data['test_id']}: {data.get('answer', '')}")
                else:
                    print(f"  INFO  {data['test_id']}: {data.get('answer', '')}")
            print(f"\nSummary: {passed} passed, {failed} failed, {len(results)} total")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
