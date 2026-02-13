"""
DOW AI - Volume Analysis Tests
Epoch Trading System v1 - XIII Trading LLC

Run: python tests/test_volume_analysis.py
"""
import sys
from pathlib import Path
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from calculations.volume_analysis import VolumeAnalyzer, VolumeResult
from data.polygon_fetcher import PolygonFetcher
from config import debug_print, get_debug_filepath


class TestVolumeAnalysis:
    """Test suite for VolumeAnalyzer."""

    def __init__(self):
        self.analyzer = VolumeAnalyzer(verbose=False)
        self.fetcher = PolygonFetcher(verbose=False)
        self.results = []

    def log_result(self, test_name: str, passed: bool, message: str = ""):
        """Log test result."""
        status = "PASS" if passed else "FAIL"
        self.results.append((test_name, passed, message))
        print(f"  [{status}] {test_name}")
        if message and not passed:
            print(f"         {message}")

    def test_returns_volume_result(self):
        """Test that analyze returns VolumeResult."""
        df = self.fetcher.fetch_bars('SPY', 'M1', bars_needed=50)
        if df is None:
            self.log_result("returns_volume_result", False, "Could not fetch data")
            return False

        result = self.analyzer.analyze(df)

        if isinstance(result, VolumeResult):
            self.log_result("returns_volume_result", True)
            return True
        else:
            self.log_result("returns_volume_result", False, f"Got {type(result)}")
            return False

    def test_delta_signal_valid(self):
        """Test that delta_signal is Bullish, Bearish, or Neutral."""
        df = self.fetcher.fetch_bars('TSLA', 'M1', bars_needed=50)
        if df is None:
            self.log_result("delta_signal_valid", False, "Could not fetch data")
            return False

        result = self.analyzer.analyze(df)
        valid_signals = ['Bullish', 'Bearish', 'Neutral']

        if result.delta_signal in valid_signals:
            self.log_result("delta_signal_valid", True)
            print(f"         Signal: {result.delta_signal}")
            return True
        else:
            self.log_result("delta_signal_valid", False, f"Got {result.delta_signal}")
            return False

    def test_roc_signal_valid(self):
        """Test that roc_signal is Above Avg, Below Avg, or Average."""
        df = self.fetcher.fetch_bars('AAPL', 'M1', bars_needed=50)
        if df is None:
            self.log_result("roc_signal_valid", False, "Could not fetch data")
            return False

        result = self.analyzer.analyze(df)
        valid_signals = ['Above Avg', 'Below Avg', 'Average']

        if result.roc_signal in valid_signals:
            self.log_result("roc_signal_valid", True)
            print(f"         Signal: {result.roc_signal} ({result.roc_percent:+.1f}%)")
            return True
        else:
            self.log_result("roc_signal_valid", False, f"Got {result.roc_signal}")
            return False

    def test_cvd_trend_valid(self):
        """Test that cvd_trend is Rising, Falling, or Flat."""
        df = self.fetcher.fetch_bars('NVDA', 'M1', bars_needed=50)
        if df is None:
            self.log_result("cvd_trend_valid", False, "Could not fetch data")
            return False

        result = self.analyzer.analyze(df)
        valid_trends = ['Rising', 'Falling', 'Flat']

        if result.cvd_trend in valid_trends:
            self.log_result("cvd_trend_valid", True)
            print(f"         Trend: {result.cvd_trend}")
            return True
        else:
            self.log_result("cvd_trend_valid", False, f"Got {result.cvd_trend}")
            return False

    def test_cvd_values_is_list(self):
        """Test that cvd_values is a list."""
        df = self.fetcher.fetch_bars('AMD', 'M1', bars_needed=50)
        if df is None:
            self.log_result("cvd_values_is_list", False, "Could not fetch data")
            return False

        result = self.analyzer.analyze(df)

        if isinstance(result.cvd_values, list):
            self.log_result("cvd_values_is_list", True)
            print(f"         Values: {len(result.cvd_values)} entries")
            return True
        else:
            self.log_result("cvd_values_is_list", False, f"Got {type(result.cvd_values)}")
            return False

    def test_bar_delta_green_positive(self):
        """Test that green bars have positive delta."""
        # Create a clearly green bar
        green_bar = pd.Series({
            'open': 100.0,
            'high': 105.0,
            'low': 99.0,
            'close': 104.0,  # Close near high = very bullish
            'volume': 10000
        })

        delta = self.analyzer.calculate_bar_delta(green_bar)

        if delta > 0:
            self.log_result("bar_delta_green_positive", True)
            print(f"         Delta: {delta:+,.0f}")
            return True
        else:
            self.log_result("bar_delta_green_positive", False, f"Expected positive, got {delta}")
            return False

    def test_bar_delta_red_negative(self):
        """Test that red bars have negative delta."""
        # Create a clearly red bar
        red_bar = pd.Series({
            'open': 104.0,
            'high': 105.0,
            'low': 99.0,
            'close': 100.0,  # Close near low = very bearish
            'volume': 10000
        })

        delta = self.analyzer.calculate_bar_delta(red_bar)

        if delta < 0:
            self.log_result("bar_delta_red_negative", True)
            print(f"         Delta: {delta:+,.0f}")
            return True
        else:
            self.log_result("bar_delta_red_negative", False, f"Expected negative, got {delta}")
            return False

    def test_rolling_delta_numeric(self):
        """Test that rolling delta returns numeric value."""
        df = self.fetcher.fetch_bars('SPY', 'M1', bars_needed=50)
        if df is None:
            self.log_result("rolling_delta_numeric", False, "Could not fetch data")
            return False

        delta = self.analyzer.calculate_rolling_delta(df)

        if isinstance(delta, (int, float)):
            self.log_result("rolling_delta_numeric", True)
            print(f"         Delta: {delta:+,.0f}")
            return True
        else:
            self.log_result("rolling_delta_numeric", False, f"Got {type(delta)}")
            return False

    def test_volume_roc_tuple(self):
        """Test that volume ROC returns tuple."""
        df = self.fetcher.fetch_bars('TSLA', 'M1', bars_needed=50)
        if df is None:
            self.log_result("volume_roc_tuple", False, "Could not fetch data")
            return False

        roc, baseline = self.analyzer.calculate_volume_roc(df)

        if isinstance(roc, (int, float)) and isinstance(baseline, (int, float)):
            self.log_result("volume_roc_tuple", True)
            print(f"         ROC: {roc:+.1f}%, Baseline: {baseline:,.0f}")
            return True
        else:
            self.log_result("volume_roc_tuple", False, "Invalid return types")
            return False

    def test_insufficient_data(self):
        """Test handling of insufficient data."""
        # Create tiny DataFrame
        df = pd.DataFrame({
            'open': [100, 101],
            'high': [102, 103],
            'low': [99, 100],
            'close': [101, 102],
            'volume': [1000, 1000]
        })

        result = self.analyzer.analyze(df)

        # Should return neutral results
        if result.delta_signal == 'Neutral' and result.cvd_trend == 'Flat':
            self.log_result("insufficient_data", True)
            return True
        else:
            self.log_result("insufficient_data", False, "Expected neutral results")
            return False

    def run_all(self) -> bool:
        """Run all tests."""
        print("\n" + "=" * 60)
        print("VOLUME ANALYSIS - TEST SUITE")
        print("=" * 60 + "\n")

        self.test_returns_volume_result()
        self.test_delta_signal_valid()
        self.test_roc_signal_valid()
        self.test_cvd_trend_valid()
        self.test_cvd_values_is_list()
        self.test_bar_delta_green_positive()
        self.test_bar_delta_red_negative()
        self.test_rolling_delta_numeric()
        self.test_volume_roc_tuple()
        self.test_insufficient_data()

        # Summary
        passed = sum(1 for _, p, _ in self.results if p)
        total = len(self.results)

        print("\n" + "-" * 60)
        print(f"RESULTS: {passed}/{total} tests passed")
        print("-" * 60)

        # Write debug report if any failures
        if passed < total:
            filepath = get_debug_filepath('test', 'volume_analysis')
            with open(filepath, 'w') as f:
                f.write("VOLUME ANALYSIS TEST REPORT\n")
                f.write("=" * 60 + "\n\n")
                for name, passed, msg in self.results:
                    status = "PASS" if passed else "FAIL"
                    f.write(f"[{status}] {name}\n")
                    if msg:
                        f.write(f"       {msg}\n")
            print(f"\nDebug report saved to: {filepath}")

        return passed == total


if __name__ == '__main__':
    tester = TestVolumeAnalysis()
    success = tester.run_all()
    sys.exit(0 if success else 1)
