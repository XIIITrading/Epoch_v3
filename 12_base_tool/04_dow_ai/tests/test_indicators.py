"""
DOW AI - New Indicator Tests
Epoch Trading System v1 - XIII Trading LLC

Tests for SMA and VWAP calculations added for 10-step methodology.

Run: python tests/test_indicators.py
"""
import sys
from pathlib import Path
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from calculations.moving_averages import MovingAverageAnalyzer, SMAResult
from calculations.vwap import VWAPCalculator, VWAPResult
from data.polygon_fetcher import PolygonFetcher
from config import debug_print, get_debug_filepath


class TestIndicators:
    """Test suite for new indicator calculations."""

    def __init__(self):
        self.sma_analyzer = MovingAverageAnalyzer(verbose=False)
        self.vwap_calc = VWAPCalculator(verbose=False)
        self.fetcher = PolygonFetcher(verbose=False)
        self.results = []

    def log_result(self, test_name: str, passed: bool, message: str = ""):
        """Log test result."""
        status = "PASS" if passed else "FAIL"
        self.results.append((test_name, passed, message))
        print(f"  [{status}] {test_name}")
        if message:
            print(f"         {message}")

    # =========================================================================
    # SMA TESTS
    # =========================================================================

    def test_sma_returns_result(self):
        """Test that calculate_smas returns SMAResult."""
        df = self.fetcher.fetch_bars('SPY', 'M5', bars_needed=50)
        if df is None:
            self.log_result("sma_returns_result", False, "Could not fetch data")
            return False

        result = self.sma_analyzer.calculate_smas(df)

        if isinstance(result, SMAResult):
            self.log_result("sma_returns_result", True)
            return True
        else:
            self.log_result("sma_returns_result", False, f"Got {type(result)}")
            return False

    def test_sma_values_numeric(self):
        """Test that SMA values are numeric."""
        df = self.fetcher.fetch_bars('TSLA', 'M5', bars_needed=50)
        if df is None:
            self.log_result("sma_values_numeric", False, "Could not fetch data")
            return False

        result = self.sma_analyzer.calculate_smas(df)

        if isinstance(result.sma9, (int, float)) and isinstance(result.sma21, (int, float)):
            self.log_result("sma_values_numeric", True)
            print(f"         SMA9: ${result.sma9:.2f}, SMA21: ${result.sma21:.2f}")
            return True
        else:
            self.log_result("sma_values_numeric", False, "Non-numeric values")
            return False

    def test_sma_alignment_valid(self):
        """Test that alignment is BULLISH, BEARISH, or NEUTRAL."""
        df = self.fetcher.fetch_bars('AAPL', 'M5', bars_needed=50)
        if df is None:
            self.log_result("sma_alignment_valid", False, "Could not fetch data")
            return False

        result = self.sma_analyzer.calculate_smas(df)
        valid = ['BULLISH', 'BEARISH', 'NEUTRAL']

        if result.alignment in valid:
            self.log_result("sma_alignment_valid", True)
            print(f"         Alignment: {result.alignment}")
            return True
        else:
            self.log_result("sma_alignment_valid", False, f"Got {result.alignment}")
            return False

    def test_sma_spread_trend_valid(self):
        """Test that spread_trend is WIDENING, NARROWING, or FLAT."""
        df = self.fetcher.fetch_bars('NVDA', 'M5', bars_needed=50)
        if df is None:
            self.log_result("sma_spread_trend_valid", False, "Could not fetch data")
            return False

        result = self.sma_analyzer.calculate_smas(df)
        valid = ['WIDENING', 'NARROWING', 'FLAT']

        if result.spread_trend in valid:
            self.log_result("sma_spread_trend_valid", True)
            print(f"         Spread trend: {result.spread_trend}")
            return True
        else:
            self.log_result("sma_spread_trend_valid", False, f"Got {result.spread_trend}")
            return False

    def test_sma_bullish_alignment(self):
        """Test bullish alignment when SMA9 > SMA21."""
        # Create synthetic bullish data (rising prices)
        df = pd.DataFrame({
            'close': [100 + i * 0.5 for i in range(30)]  # Rising prices
        })

        result = self.sma_analyzer.calculate_smas(df)

        if result.alignment == 'BULLISH' and result.sma9 > result.sma21:
            self.log_result("sma_bullish_alignment", True)
            return True
        else:
            self.log_result("sma_bullish_alignment", False,
                           f"Expected BULLISH, got {result.alignment}")
            return False

    def test_sma_bearish_alignment(self):
        """Test bearish alignment when SMA9 < SMA21."""
        # Create synthetic bearish data (falling prices)
        df = pd.DataFrame({
            'close': [100 - i * 0.5 for i in range(30)]  # Falling prices
        })

        result = self.sma_analyzer.calculate_smas(df)

        if result.alignment == 'BEARISH' and result.sma9 < result.sma21:
            self.log_result("sma_bearish_alignment", True)
            return True
        else:
            self.log_result("sma_bearish_alignment", False,
                           f"Expected BEARISH, got {result.alignment}")
            return False

    def test_sma_multi_timeframe(self):
        """Test multi-timeframe SMA calculation."""
        data = self.fetcher.fetch_multi_timeframe('SPY', ['M5', 'M15'])
        if not data:
            self.log_result("sma_multi_timeframe", False, "Could not fetch data")
            return False

        results = self.sma_analyzer.calculate_multi_timeframe(data)

        if 'M5' in results and 'M15' in results:
            self.log_result("sma_multi_timeframe", True)
            for tf, sma in results.items():
                print(f"         {tf}: SMA9=${sma.sma9:.2f}, Alignment={sma.alignment}")
            return True
        else:
            self.log_result("sma_multi_timeframe", False, f"Only got {list(results.keys())}")
            return False

    def test_sma_insufficient_data(self):
        """Test handling of insufficient data."""
        df = pd.DataFrame({'close': [100, 101, 102]})  # Only 3 bars

        result = self.sma_analyzer.calculate_smas(df)

        if result.alignment == 'NEUTRAL':
            self.log_result("sma_insufficient_data", True)
            return True
        else:
            self.log_result("sma_insufficient_data", False, "Should return NEUTRAL")
            return False

    # =========================================================================
    # VWAP TESTS
    # =========================================================================

    def test_vwap_returns_result(self):
        """Test that analyze returns VWAPResult."""
        df = self.fetcher.fetch_bars('SPY', 'M1', bars_needed=100)
        if df is None:
            self.log_result("vwap_returns_result", False, "Could not fetch data")
            return False

        result = self.vwap_calc.analyze(df, 500.0)

        if isinstance(result, VWAPResult):
            self.log_result("vwap_returns_result", True)
            return True
        else:
            self.log_result("vwap_returns_result", False, f"Got {type(result)}")
            return False

    def test_vwap_value_numeric(self):
        """Test that VWAP value is numeric."""
        df = self.fetcher.fetch_bars('TSLA', 'M1', bars_needed=100)
        if df is None:
            self.log_result("vwap_value_numeric", False, "Could not fetch data")
            return False

        result = self.vwap_calc.analyze(df)

        if isinstance(result.vwap, (int, float)) and result.vwap > 0:
            self.log_result("vwap_value_numeric", True)
            print(f"         VWAP: ${result.vwap:.2f}")
            return True
        else:
            self.log_result("vwap_value_numeric", False, f"Got {result.vwap}")
            return False

    def test_vwap_side_valid(self):
        """Test that side is ABOVE, BELOW, or AT."""
        df = self.fetcher.fetch_bars('AAPL', 'M1', bars_needed=100)
        if df is None:
            self.log_result("vwap_side_valid", False, "Could not fetch data")
            return False

        current_price = float(df.iloc[-1]['close'])
        result = self.vwap_calc.analyze(df, current_price)
        valid = ['ABOVE', 'BELOW', 'AT', 'N/A']

        if result.side in valid:
            self.log_result("vwap_side_valid", True)
            print(f"         Side: {result.side} ({result.price_pct:+.2f}%)")
            return True
        else:
            self.log_result("vwap_side_valid", False, f"Got {result.side}")
            return False

    def test_vwap_price_relationship(self):
        """Test price vs VWAP calculation."""
        vwap = 500.0
        current_price = 505.0

        result = self.vwap_calc.get_price_vs_vwap(current_price, vwap)

        if result.side == 'ABOVE' and result.price_diff == 5.0:
            self.log_result("vwap_price_relationship", True)
            return True
        else:
            self.log_result("vwap_price_relationship", False,
                           f"Expected ABOVE +5, got {result.side} {result.price_diff}")
            return False

    def test_vwap_empty_data(self):
        """Test handling of empty DataFrame."""
        df = pd.DataFrame()
        result = self.vwap_calc.analyze(df)

        if result.vwap == 0.0:
            self.log_result("vwap_empty_data", True)
            return True
        else:
            self.log_result("vwap_empty_data", False, f"Expected 0, got {result.vwap}")
            return False

    def test_vwap_percentage_calculation(self):
        """Test VWAP percentage calculation."""
        vwap = 100.0
        current_price = 102.0  # 2% above

        result = self.vwap_calc.get_price_vs_vwap(current_price, vwap)

        if abs(result.price_pct - 2.0) < 0.01:
            self.log_result("vwap_percentage_calculation", True)
            print(f"         Price pct: {result.price_pct:.2f}%")
            return True
        else:
            self.log_result("vwap_percentage_calculation", False,
                           f"Expected 2%, got {result.price_pct:.2f}%")
            return False

    def run_all(self) -> bool:
        """Run all tests."""
        print("\n" + "=" * 60)
        print("NEW INDICATORS - TEST SUITE")
        print("=" * 60)

        print("\n--- SMA TESTS ---")
        self.test_sma_returns_result()
        self.test_sma_values_numeric()
        self.test_sma_alignment_valid()
        self.test_sma_spread_trend_valid()
        self.test_sma_bullish_alignment()
        self.test_sma_bearish_alignment()
        self.test_sma_multi_timeframe()
        self.test_sma_insufficient_data()

        print("\n--- VWAP TESTS ---")
        self.test_vwap_returns_result()
        self.test_vwap_value_numeric()
        self.test_vwap_side_valid()
        self.test_vwap_price_relationship()
        self.test_vwap_empty_data()
        self.test_vwap_percentage_calculation()

        # Summary
        passed = sum(1 for _, p, _ in self.results if p)
        total = len(self.results)

        print("\n" + "-" * 60)
        print(f"RESULTS: {passed}/{total} tests passed")
        print("-" * 60)

        # Write debug report if any failures
        if passed < total:
            filepath = get_debug_filepath('test', 'indicators')
            with open(filepath, 'w') as f:
                f.write("NEW INDICATORS TEST REPORT\n")
                f.write("=" * 60 + "\n\n")
                for name, passed, msg in self.results:
                    status = "PASS" if passed else "FAIL"
                    f.write(f"[{status}] {name}\n")
                    if msg:
                        f.write(f"       {msg}\n")
            print(f"\nDebug report saved to: {filepath}")

        return passed == total


if __name__ == '__main__':
    tester = TestIndicators()
    success = tester.run_all()
    sys.exit(0 if success else 1)
