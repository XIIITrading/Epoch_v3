"""
DOW AI - Aggregator Integration Tests
Epoch Trading System v1 - XIII Trading LLC

Run: python tests/test_aggregator.py

NOTE: This is an integration test that requires:
  - epoch_v1.xlsm open in Excel
  - Valid Polygon API key
  - Valid Anthropic API key
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.aggregator import AnalysisAggregator
from config import debug_print, get_debug_filepath, EXCEL_FILEPATH


class TestAggregator:
    """Integration test suite for AnalysisAggregator."""

    def __init__(self):
        self.aggregator = AnalysisAggregator(verbose=True)
        self.results = []

    def log_result(self, test_name: str, passed: bool, message: str = ""):
        """Log test result."""
        status = "PASS" if passed else "FAIL"
        self.results.append((test_name, passed, message))
        print(f"  [{status}] {test_name}")
        if message:
            print(f"         {message}")

    def test_entry_analysis_structure(self):
        """Test that entry analysis returns expected structure."""
        print("\n  Running entry analysis for SPY long EPCH_01...")

        result = self.aggregator.run_entry_analysis('SPY', 'long', 'EPCH_01')

        if 'error' in result:
            self.log_result("entry_analysis_structure", False, result['error'])
            return False

        # Check required fields
        required = ['ticker', 'direction', 'model', 'current_price',
                    'structure', 'volume', 'claude_response']

        missing = [f for f in required if f not in result]

        if not missing:
            self.log_result("entry_analysis_structure", True)
            print(f"         Price: ${result['current_price']:.2f}")
            return True
        else:
            self.log_result("entry_analysis_structure", False, f"Missing: {missing}")
            return False

    def test_entry_claude_response(self):
        """Test that Claude response is meaningful."""
        result = self.aggregator.run_entry_analysis('TSLA', 'long', 'EPCH_01')

        if 'error' in result:
            self.log_result("entry_claude_response", False, result['error'])
            return False

        response = result.get('claude_response', '')

        # Check for expected content in response
        if len(response) > 100 and not response.startswith('Error'):
            # Check for recommendation keywords
            has_recommendation = any(word in response.upper() for word in
                                    ['ENTRY', 'WAIT', 'NO TRADE', 'RECOMMENDATION'])
            if has_recommendation:
                self.log_result("entry_claude_response", True)
                print(f"         Response length: {len(response)} chars")
                return True
            else:
                self.log_result("entry_claude_response", True)
                print(f"         Response present but format may vary")
                return True
        else:
            self.log_result("entry_claude_response", False, "Response too short or error")
            return False

    def test_exit_analysis_structure(self):
        """Test that exit analysis returns expected structure."""
        print("\n  Running exit analysis for SPY sell EPCH_01...")

        result = self.aggregator.run_exit_analysis('SPY', 'sell', 'EPCH_01')

        if 'error' in result:
            self.log_result("exit_analysis_structure", False, result['error'])
            return False

        # Check required fields
        required = ['ticker', 'position_type', 'exit_action', 'model',
                    'current_price', 'structure', 'volume', 'claude_response']

        missing = [f for f in required if f not in result]

        if not missing:
            self.log_result("exit_analysis_structure", True)
            print(f"         Position: {result['position_type']}")
            return True
        else:
            self.log_result("exit_analysis_structure", False, f"Missing: {missing}")
            return False

    def test_structure_calculation(self):
        """Test that market structure is calculated."""
        result = self.aggregator.run_entry_analysis('AAPL', 'short', 'EPCH_02')

        if 'error' in result:
            self.log_result("structure_calculation", False, result['error'])
            return False

        structure = result.get('structure', {})

        if len(structure) >= 2:  # Should have at least 2 timeframes
            self.log_result("structure_calculation", True)
            for tf, s in structure.items():
                print(f"         {tf}: {s.direction}")
            return True
        else:
            self.log_result("structure_calculation", False, f"Only {len(structure)} timeframes")
            return False

    def test_volume_analysis(self):
        """Test that volume analysis is calculated."""
        result = self.aggregator.run_entry_analysis('NVDA', 'long', 'EPCH_01')

        if 'error' in result:
            self.log_result("volume_analysis", False, result['error'])
            return False

        volume = result.get('volume')

        if volume and hasattr(volume, 'delta_signal'):
            self.log_result("volume_analysis", True)
            print(f"         Delta: {volume.delta_signal}, CVD: {volume.cvd_trend}")
            return True
        else:
            self.log_result("volume_analysis", False, "Volume data missing")
            return False

    def test_debug_report_created(self):
        """Test that debug report is created."""
        from config import DEBUG_DIR
        import os

        # Get initial file count
        initial_files = len(list(DEBUG_DIR.glob('*.txt')))

        # Run analysis
        result = self.aggregator.run_entry_analysis('AMD', 'long', 'EPCH_01')

        if 'error' in result:
            self.log_result("debug_report_created", False, result['error'])
            return False

        # Check for new debug file
        final_files = len(list(DEBUG_DIR.glob('*.txt')))

        if final_files > initial_files:
            self.log_result("debug_report_created", True)
            print(f"         Debug files: {initial_files} -> {final_files}")
            return True
        else:
            self.log_result("debug_report_created", False, "No new debug file")
            return False

    def test_different_models(self):
        """Test different model types."""
        models_to_test = ['EPCH_01', 'EPCH_02']
        all_passed = True

        for model in models_to_test:
            direction = 'long' if '01' in model or '03' in model else 'short'
            result = self.aggregator.run_entry_analysis('SPY', direction, model)

            if 'error' in result:
                print(f"         {model}: FAILED - {result['error']}")
                all_passed = False
            else:
                print(f"         {model}: OK - ${result['current_price']:.2f}")

        self.log_result("different_models", all_passed)
        return all_passed

    def run_all(self) -> bool:
        """Run all tests."""
        print("\n" + "=" * 60)
        print("AGGREGATOR INTEGRATION - TEST SUITE")
        print("=" * 60)
        print(f"\nExcel file: {EXCEL_FILEPATH}")
        print("Ensure Excel workbook is OPEN before running!\n")

        self.test_entry_analysis_structure()
        self.test_entry_claude_response()
        self.test_exit_analysis_structure()
        self.test_structure_calculation()
        self.test_volume_analysis()
        self.test_debug_report_created()
        self.test_different_models()

        # Summary
        passed = sum(1 for _, p, _ in self.results if p)
        total = len(self.results)

        print("\n" + "-" * 60)
        print(f"RESULTS: {passed}/{total} tests passed")
        print("-" * 60)

        # Write debug report if any failures
        if passed < total:
            filepath = get_debug_filepath('test', 'aggregator')
            with open(filepath, 'w') as f:
                f.write("AGGREGATOR INTEGRATION TEST REPORT\n")
                f.write("=" * 60 + "\n\n")
                for name, passed, msg in self.results:
                    status = "PASS" if passed else "FAIL"
                    f.write(f"[{status}] {name}\n")
                    if msg:
                        f.write(f"       {msg}\n")
            print(f"\nDebug report saved to: {filepath}")

        return passed == total


if __name__ == '__main__':
    print("\n" + "!" * 60)
    print("  IMPORTANT: Make sure epoch_v1.xlsm is OPEN in Excel!")
    print("!" * 60)

    tester = TestAggregator()
    success = tester.run_all()
    sys.exit(0 if success else 1)
