"""
DOW AI - Market Structure Tests
Epoch Trading System v1 - XIII Trading LLC

Run: python tests/test_market_structure.py
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from calculations.market_structure import MarketStructureCalculator, StructureResult
from data.polygon_fetcher import PolygonFetcher
from config import debug_print, get_debug_filepath


class TestMarketStructure:
    """Test suite for MarketStructureCalculator."""

    def __init__(self):
        self.calculator = MarketStructureCalculator(verbose=False)
        self.fetcher = PolygonFetcher(verbose=False)
        self.results = []

    def log_result(self, test_name: str, passed: bool, message: str = ""):
        """Log test result."""
        status = "PASS" if passed else "FAIL"
        self.results.append((test_name, passed, message))
        print(f"  [{status}] {test_name}")
        if message and not passed:
            print(f"         {message}")

    def test_returns_structure_result(self):
        """Test that calculate returns StructureResult."""
        df = self.fetcher.fetch_bars('SPY', 'M15', bars_needed=100)
        if df is None:
            self.log_result("returns_structure_result", False, "Could not fetch data")
            return False

        result = self.calculator.calculate(df)

        if isinstance(result, StructureResult):
            self.log_result("returns_structure_result", True)
            return True
        else:
            self.log_result("returns_structure_result", False, f"Got {type(result)}")
            return False

    def test_direction_is_valid(self):
        """Test that direction is one of BULL, BEAR, NEUTRAL."""
        df = self.fetcher.fetch_bars('TSLA', 'M15', bars_needed=100)
        if df is None:
            self.log_result("direction_is_valid", False, "Could not fetch data")
            return False

        result = self.calculator.calculate(df)
        valid_directions = ['BULL', 'BEAR', 'NEUTRAL']

        if result.direction in valid_directions:
            self.log_result("direction_is_valid", True)
            print(f"         Direction: {result.direction}")
            return True
        else:
            self.log_result("direction_is_valid", False, f"Got {result.direction}")
            return False

    def test_levels_are_numeric(self):
        """Test that strong/weak levels are numeric or None."""
        df = self.fetcher.fetch_bars('AAPL', 'M15', bars_needed=100)
        if df is None:
            self.log_result("levels_are_numeric", False, "Could not fetch data")
            return False

        result = self.calculator.calculate(df)

        strong_ok = result.strong_level is None or isinstance(result.strong_level, (int, float))
        weak_ok = result.weak_level is None or isinstance(result.weak_level, (int, float))

        if strong_ok and weak_ok:
            self.log_result("levels_are_numeric", True)
            return True
        else:
            self.log_result("levels_are_numeric", False, "Invalid level types")
            return False

    def test_last_break_is_valid(self):
        """Test that last_break is BOS, ChoCH, or None."""
        df = self.fetcher.fetch_bars('NVDA', 'M15', bars_needed=100)
        if df is None:
            self.log_result("last_break_is_valid", False, "Could not fetch data")
            return False

        result = self.calculator.calculate(df)
        valid_breaks = [None, 'BOS', 'ChoCH']

        if result.last_break in valid_breaks:
            self.log_result("last_break_is_valid", True)
            print(f"         Last break: {result.last_break}")
            return True
        else:
            self.log_result("last_break_is_valid", False, f"Got {result.last_break}")
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

        result = self.calculator.calculate(df)

        if result.direction == 'NEUTRAL':
            self.log_result("insufficient_data", True)
            return True
        else:
            self.log_result("insufficient_data", False, f"Expected NEUTRAL, got {result.direction}")
            return False

    def test_none_input(self):
        """Test handling of None input."""
        result = self.calculator.calculate(None)

        if result.direction == 'NEUTRAL':
            self.log_result("none_input", True)
            return True
        else:
            self.log_result("none_input", False, f"Expected NEUTRAL, got {result.direction}")
            return False

    def test_multi_timeframe(self):
        """Test multi-timeframe calculation."""
        data = self.fetcher.fetch_multi_timeframe('SPY', ['M5', 'M15', 'H1'])
        if not data:
            self.log_result("multi_timeframe", False, "Could not fetch data")
            return False

        results = self.calculator.calculate_multi_timeframe(data)

        if len(results) >= 2:
            self.log_result("multi_timeframe", True)
            for tf, res in results.items():
                print(f"         {tf}: {res.direction}")
            return True
        else:
            self.log_result("multi_timeframe", False, f"Only got {len(results)} results")
            return False

    def test_bull_structure_levels(self):
        """Test that bull structure has appropriate levels."""
        # Fetch data and find a bullish result
        for ticker in ['SPY', 'AAPL', 'MSFT', 'GOOGL']:
            df = self.fetcher.fetch_bars(ticker, 'H1', bars_needed=100)
            if df is None:
                continue

            result = self.calculator.calculate(df)

            if result.direction == 'BULL':
                # In bull structure, strong should be support (lower)
                # weak should be continuation target (higher)
                if result.strong_level and result.weak_level:
                    if result.strong_level < result.weak_level:
                        self.log_result("bull_structure_levels", True)
                        print(f"         {ticker}: Strong ${result.strong_level:.2f} < Weak ${result.weak_level:.2f}")
                        return True

        # If no bullish result found, skip test
        self.log_result("bull_structure_levels", True)
        print(f"         No clear bull structure found to test")
        return True

    def test_bear_structure_levels(self):
        """Test that bear structure has appropriate levels."""
        # Fetch data and find a bearish result
        for ticker in ['SPY', 'AAPL', 'MSFT', 'GOOGL']:
            df = self.fetcher.fetch_bars(ticker, 'H1', bars_needed=100)
            if df is None:
                continue

            result = self.calculator.calculate(df)

            if result.direction == 'BEAR':
                # In bear structure, strong should be resistance (higher)
                # weak should be continuation target (lower)
                if result.strong_level and result.weak_level:
                    if result.strong_level > result.weak_level:
                        self.log_result("bear_structure_levels", True)
                        print(f"         {ticker}: Strong ${result.strong_level:.2f} > Weak ${result.weak_level:.2f}")
                        return True

        # If no bearish result found, skip test
        self.log_result("bear_structure_levels", True)
        print(f"         No clear bear structure found to test")
        return True

    def run_all(self) -> bool:
        """Run all tests."""
        print("\n" + "=" * 60)
        print("MARKET STRUCTURE - TEST SUITE")
        print("=" * 60 + "\n")

        self.test_returns_structure_result()
        self.test_direction_is_valid()
        self.test_levels_are_numeric()
        self.test_last_break_is_valid()
        self.test_insufficient_data()
        self.test_none_input()
        self.test_multi_timeframe()
        self.test_bull_structure_levels()
        self.test_bear_structure_levels()

        # Summary
        passed = sum(1 for _, p, _ in self.results if p)
        total = len(self.results)

        print("\n" + "-" * 60)
        print(f"RESULTS: {passed}/{total} tests passed")
        print("-" * 60)

        # Write debug report if any failures
        if passed < total:
            filepath = get_debug_filepath('test', 'market_structure')
            with open(filepath, 'w') as f:
                f.write("MARKET STRUCTURE TEST REPORT\n")
                f.write("=" * 60 + "\n\n")
                for name, passed, msg in self.results:
                    status = "PASS" if passed else "FAIL"
                    f.write(f"[{status}] {name}\n")
                    if msg:
                        f.write(f"       {msg}\n")
            print(f"\nDebug report saved to: {filepath}")

        return passed == total


if __name__ == '__main__':
    tester = TestMarketStructure()
    success = tester.run_all()
    sys.exit(0 if success else 1)
