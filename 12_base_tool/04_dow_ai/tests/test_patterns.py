"""
DOW AI - Pattern Detection Tests
Epoch Trading System v1 - XIII Trading LLC

Run: python tests/test_patterns.py
"""
import sys
from pathlib import Path
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from calculations.patterns import PatternDetector, PatternResult
from data.polygon_fetcher import PolygonFetcher
from config import debug_print, get_debug_filepath


class TestPatterns:
    """Test suite for PatternDetector."""

    def __init__(self):
        self.detector = PatternDetector(verbose=False)
        self.fetcher = PolygonFetcher(verbose=False)
        self.results = []

    def log_result(self, test_name: str, passed: bool, message: str = ""):
        """Log test result."""
        status = "PASS" if passed else "FAIL"
        self.results.append((test_name, passed, message))
        print(f"  [{status}] {test_name}")
        if message and not passed:
            print(f"         {message}")

    def test_detect_all_returns_list(self):
        """Test that detect_all returns a list."""
        df = self.fetcher.fetch_bars('SPY', 'M5', bars_needed=50)
        if df is None:
            self.log_result("detect_all_returns_list", False, "Could not fetch data")
            return False

        patterns = self.detector.detect_all(df)

        if isinstance(patterns, list):
            self.log_result("detect_all_returns_list", True)
            print(f"         Found {len(patterns)} patterns")
            return True
        else:
            self.log_result("detect_all_returns_list", False, f"Got {type(patterns)}")
            return False

    def test_pattern_result_structure(self):
        """Test that patterns have correct structure."""
        df = self.fetcher.fetch_bars('TSLA', 'M5', bars_needed=50)
        if df is None:
            self.log_result("pattern_result_structure", False, "Could not fetch data")
            return False

        patterns = self.detector.detect_all(df)

        if not patterns:
            # No patterns found - test with synthetic data
            patterns = self.detector.detect_doji(df)

        if patterns:
            p = patterns[0]
            has_required = all(hasattr(p, attr) for attr in ['pattern', 'price', 'bars_ago', 'direction'])
            if has_required:
                self.log_result("pattern_result_structure", True)
                return True
            else:
                self.log_result("pattern_result_structure", False, "Missing attributes")
                return False
        else:
            # Skip if no patterns to check
            self.log_result("pattern_result_structure", True)
            print(f"         No patterns to verify structure")
            return True

    def test_detect_doji(self):
        """Test doji detection with synthetic data."""
        # Create data with clear doji (tiny body)
        df = pd.DataFrame({
            'open': [100.0, 100.5, 100.2],
            'high': [102.0, 102.0, 102.0],
            'low': [98.0, 98.0, 98.0],
            'close': [100.0, 100.5, 100.3],  # Middle bar is doji
            'volume': [1000, 1000, 1000]
        })

        patterns = self.detector.detect_doji(df, lookback=3)

        # Should find at least one doji
        dojis = [p for p in patterns if p.pattern == 'Doji']
        if len(dojis) > 0:
            self.log_result("detect_doji", True)
            print(f"         Found {len(dojis)} doji(s)")
            return True
        else:
            self.log_result("detect_doji", False, "No doji detected in test data")
            return False

    def test_detect_bullish_engulfing(self):
        """Test bullish engulfing detection."""
        # Create data with bullish engulfing pattern
        df = pd.DataFrame({
            'open': [102.0, 100.0],  # Bar 1: red, Bar 2: green engulfing
            'high': [103.0, 104.0],
            'low': [99.0, 99.0],
            'close': [100.0, 103.0],
            'volume': [1000, 1500]
        })

        patterns = self.detector.detect_engulfing(df, lookback=2)

        bullish = [p for p in patterns if p.pattern == 'Bullish Engulfing']
        if len(bullish) > 0:
            self.log_result("detect_bullish_engulfing", True)
            return True
        else:
            self.log_result("detect_bullish_engulfing", False, "Pattern not detected")
            return False

    def test_detect_bearish_engulfing(self):
        """Test bearish engulfing detection."""
        # Create data with bearish engulfing pattern
        df = pd.DataFrame({
            'open': [100.0, 104.0],  # Bar 1: green, Bar 2: red engulfing
            'high': [104.0, 105.0],
            'low': [99.0, 99.0],
            'close': [103.0, 99.5],
            'volume': [1000, 1500]
        })

        patterns = self.detector.detect_engulfing(df, lookback=2)

        bearish = [p for p in patterns if p.pattern == 'Bearish Engulfing']
        if len(bearish) > 0:
            self.log_result("detect_bearish_engulfing", True)
            return True
        else:
            self.log_result("detect_bearish_engulfing", False, "Pattern not detected")
            return False

    def test_direction_values(self):
        """Test that pattern directions are valid."""
        df = self.fetcher.fetch_bars('AAPL', 'M5', bars_needed=50)
        if df is None:
            self.log_result("direction_values", False, "Could not fetch data")
            return False

        patterns = self.detector.detect_all(df)
        valid_directions = ['bullish', 'bearish', 'neutral']

        if not patterns:
            self.log_result("direction_values", True)
            print(f"         No patterns to check")
            return True

        all_valid = all(p.direction in valid_directions for p in patterns)
        if all_valid:
            self.log_result("direction_values", True)
            return True
        else:
            invalid = [p.direction for p in patterns if p.direction not in valid_directions]
            self.log_result("direction_values", False, f"Invalid directions: {invalid}")
            return False

    def test_bars_ago_non_negative(self):
        """Test that bars_ago is non-negative."""
        df = self.fetcher.fetch_bars('NVDA', 'M5', bars_needed=50)
        if df is None:
            self.log_result("bars_ago_non_negative", False, "Could not fetch data")
            return False

        patterns = self.detector.detect_all(df)

        if not patterns:
            self.log_result("bars_ago_non_negative", True)
            print(f"         No patterns to check")
            return True

        all_valid = all(p.bars_ago >= 0 for p in patterns)
        if all_valid:
            self.log_result("bars_ago_non_negative", True)
            return True
        else:
            self.log_result("bars_ago_non_negative", False, "Negative bars_ago found")
            return False

    def test_multi_timeframe(self):
        """Test multi-timeframe pattern detection."""
        data = self.fetcher.fetch_multi_timeframe('SPY', ['M5', 'M15', 'H1'])
        if not data:
            self.log_result("multi_timeframe", False, "Could not fetch data")
            return False

        results = self.detector.detect_multi_timeframe(data)

        if isinstance(results, dict) and len(results) >= 2:
            self.log_result("multi_timeframe", True)
            for tf, patterns in results.items():
                print(f"         {tf}: {len(patterns)} patterns")
            return True
        else:
            self.log_result("multi_timeframe", False, "Invalid results structure")
            return False

    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        df = pd.DataFrame()

        patterns = self.detector.detect_all(df)

        if patterns == []:
            self.log_result("empty_dataframe", True)
            return True
        else:
            self.log_result("empty_dataframe", False, f"Expected empty list, got {len(patterns)}")
            return False

    def test_sorted_by_bars_ago(self):
        """Test that patterns are sorted by bars_ago (most recent first)."""
        df = self.fetcher.fetch_bars('AMD', 'M5', bars_needed=50)
        if df is None:
            self.log_result("sorted_by_bars_ago", False, "Could not fetch data")
            return False

        patterns = self.detector.detect_all(df)

        if len(patterns) < 2:
            self.log_result("sorted_by_bars_ago", True)
            print(f"         Not enough patterns to verify sorting")
            return True

        is_sorted = all(patterns[i].bars_ago <= patterns[i+1].bars_ago for i in range(len(patterns)-1))
        if is_sorted:
            self.log_result("sorted_by_bars_ago", True)
            return True
        else:
            self.log_result("sorted_by_bars_ago", False, "Patterns not sorted")
            return False

    def run_all(self) -> bool:
        """Run all tests."""
        print("\n" + "=" * 60)
        print("PATTERN DETECTION - TEST SUITE")
        print("=" * 60 + "\n")

        self.test_detect_all_returns_list()
        self.test_pattern_result_structure()
        self.test_detect_doji()
        self.test_detect_bullish_engulfing()
        self.test_detect_bearish_engulfing()
        self.test_direction_values()
        self.test_bars_ago_non_negative()
        self.test_multi_timeframe()
        self.test_empty_dataframe()
        self.test_sorted_by_bars_ago()

        # Summary
        passed = sum(1 for _, p, _ in self.results if p)
        total = len(self.results)

        print("\n" + "-" * 60)
        print(f"RESULTS: {passed}/{total} tests passed")
        print("-" * 60)

        # Write debug report if any failures
        if passed < total:
            filepath = get_debug_filepath('test', 'patterns')
            with open(filepath, 'w') as f:
                f.write("PATTERN DETECTION TEST REPORT\n")
                f.write("=" * 60 + "\n\n")
                for name, passed, msg in self.results:
                    status = "PASS" if passed else "FAIL"
                    f.write(f"[{status}] {name}\n")
                    if msg:
                        f.write(f"       {msg}\n")
            print(f"\nDebug report saved to: {filepath}")

        return passed == total


if __name__ == '__main__':
    tester = TestPatterns()
    success = tester.run_all()
    sys.exit(0 if success else 1)
