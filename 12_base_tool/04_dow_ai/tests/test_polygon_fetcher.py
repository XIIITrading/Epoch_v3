"""
DOW AI - Polygon Fetcher Tests
Epoch Trading System v1 - XIII Trading LLC

Run: python tests/test_polygon_fetcher.py
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.polygon_fetcher import PolygonFetcher
from config import TIMEFRAMES, debug_print, get_debug_filepath


class TestPolygonFetcher:
    """Test suite for PolygonFetcher."""

    def __init__(self):
        self.fetcher = PolygonFetcher(verbose=True)
        self.results = []

    def log_result(self, test_name: str, passed: bool, message: str = ""):
        """Log test result."""
        status = "PASS" if passed else "FAIL"
        self.results.append((test_name, passed, message))
        print(f"  [{status}] {test_name}")
        if message and not passed:
            print(f"         {message}")

    def test_fetch_m1_bars(self):
        """Test fetching M1 bars."""
        df = self.fetcher.fetch_bars('TSLA', 'M1', bars_needed=20)
        if df is not None and len(df) >= 10:
            self.log_result("fetch_m1_bars", True)
            return True
        else:
            self.log_result("fetch_m1_bars", False, f"Got {len(df) if df is not None else 0} bars")
            return False

    def test_fetch_m5_bars(self):
        """Test fetching M5 bars."""
        df = self.fetcher.fetch_bars('SPY', 'M5', bars_needed=50)
        if df is not None and len(df) >= 30:
            self.log_result("fetch_m5_bars", True)
            return True
        else:
            self.log_result("fetch_m5_bars", False, f"Got {len(df) if df is not None else 0} bars")
            return False

    def test_fetch_m15_bars(self):
        """Test fetching M15 bars."""
        df = self.fetcher.fetch_bars('AAPL', 'M15', bars_needed=50)
        if df is not None and len(df) >= 30:
            self.log_result("fetch_m15_bars", True)
            return True
        else:
            self.log_result("fetch_m15_bars", False, f"Got {len(df) if df is not None else 0} bars")
            return False

    def test_fetch_h1_bars(self):
        """Test fetching H1 bars."""
        df = self.fetcher.fetch_bars('NVDA', 'H1', bars_needed=50)
        if df is not None and len(df) >= 30:
            self.log_result("fetch_h1_bars", True)
            return True
        else:
            self.log_result("fetch_h1_bars", False, f"Got {len(df) if df is not None else 0} bars")
            return False

    def test_fetch_h4_bars(self):
        """Test fetching H4 bars."""
        df = self.fetcher.fetch_bars('AMD', 'H4', bars_needed=30)
        if df is not None and len(df) >= 20:
            self.log_result("fetch_h4_bars", True)
            return True
        else:
            self.log_result("fetch_h4_bars", False, f"Got {len(df) if df is not None else 0} bars")
            return False

    def test_dataframe_columns(self):
        """Test that DataFrame has correct columns."""
        df = self.fetcher.fetch_bars('TSLA', 'M5', bars_needed=10)
        if df is None:
            self.log_result("dataframe_columns", False, "No data returned")
            return False

        expected_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        has_all = all(col in df.columns for col in expected_cols)

        if has_all:
            self.log_result("dataframe_columns", True)
            return True
        else:
            missing = [c for c in expected_cols if c not in df.columns]
            self.log_result("dataframe_columns", False, f"Missing columns: {missing}")
            return False

    def test_multi_timeframe(self):
        """Test fetching multiple timeframes."""
        data = self.fetcher.fetch_multi_timeframe('TSLA', ['M5', 'M15', 'H1'])

        if len(data) >= 2:
            self.log_result("multi_timeframe", True)
            return True
        else:
            self.log_result("multi_timeframe", False, f"Only got {len(data)} timeframes")
            return False

    def test_get_current_price(self):
        """Test getting current price."""
        price = self.fetcher.get_current_price('TSLA')

        if price is not None and price > 0:
            self.log_result("get_current_price", True)
            return True
        else:
            self.log_result("get_current_price", False, f"Price: {price}")
            return False

    def test_historical_datetime(self):
        """Test fetching historical data at specific datetime."""
        import pytz
        tz = pytz.timezone('America/New_York')

        # Get data from 3 days ago at 10:30 AM
        hist_dt = datetime.now(tz) - timedelta(days=3)
        hist_dt = hist_dt.replace(hour=10, minute=30, second=0, microsecond=0)

        df = self.fetcher.fetch_bars('SPY', 'M5', end_datetime=hist_dt, bars_needed=20)

        if df is not None and len(df) > 0:
            # Verify last bar is before or at hist_dt
            last_ts = df.iloc[-1]['timestamp']
            if last_ts <= hist_dt:
                self.log_result("historical_datetime", True)
                return True
            else:
                self.log_result("historical_datetime", False, f"Last bar {last_ts} > {hist_dt}")
                return False
        else:
            self.log_result("historical_datetime", False, "No data returned")
            return False

    def test_invalid_ticker(self):
        """Test behavior with invalid ticker."""
        df = self.fetcher.fetch_bars('INVALIDTICKER123', 'M5', bars_needed=10)

        if df is None or len(df) == 0:
            self.log_result("invalid_ticker", True)
            return True
        else:
            self.log_result("invalid_ticker", False, "Should return None for invalid ticker")
            return False

    def run_all(self) -> bool:
        """Run all tests."""
        print("\n" + "=" * 60)
        print("POLYGON FETCHER - TEST SUITE")
        print("=" * 60 + "\n")

        self.test_fetch_m1_bars()
        self.test_fetch_m5_bars()
        self.test_fetch_m15_bars()
        self.test_fetch_h1_bars()
        self.test_fetch_h4_bars()
        self.test_dataframe_columns()
        self.test_multi_timeframe()
        self.test_get_current_price()
        self.test_historical_datetime()
        self.test_invalid_ticker()

        # Summary
        passed = sum(1 for _, p, _ in self.results if p)
        total = len(self.results)

        print("\n" + "-" * 60)
        print(f"RESULTS: {passed}/{total} tests passed")
        print("-" * 60)

        # Write debug report if any failures
        if passed < total:
            filepath = get_debug_filepath('test', 'polygon_fetcher')
            with open(filepath, 'w') as f:
                f.write("POLYGON FETCHER TEST REPORT\n")
                f.write("=" * 60 + "\n\n")
                for name, passed, msg in self.results:
                    status = "PASS" if passed else "FAIL"
                    f.write(f"[{status}] {name}\n")
                    if msg:
                        f.write(f"       {msg}\n")
            print(f"\nDebug report saved to: {filepath}")

        return passed == total


if __name__ == '__main__':
    tester = TestPolygonFetcher()
    success = tester.run_all()
    sys.exit(0 if success else 1)
