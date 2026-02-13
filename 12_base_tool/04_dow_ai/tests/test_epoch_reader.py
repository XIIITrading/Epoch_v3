"""
DOW AI - Epoch Reader Tests
Epoch Trading System v1 - XIII Trading LLC

Run: python tests/test_epoch_reader.py

NOTE: Requires epoch_v1.xlsm to be open in Excel!
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.epoch_reader import EpochReader
from config import EXCEL_FILEPATH, debug_print, get_debug_filepath


class TestEpochReader:
    """Test suite for EpochReader."""

    def __init__(self):
        self.reader = EpochReader(verbose=True)
        self.results = []
        self.test_ticker = None  # Will be set after reading zone_results

    def log_result(self, test_name: str, passed: bool, message: str = ""):
        """Log test result."""
        status = "PASS" if passed else "FAIL"
        self.results.append((test_name, passed, message))
        print(f"  [{status}] {test_name}")
        if message and not passed:
            print(f"         {message}")

    def test_connect(self) -> bool:
        """Test Excel connection."""
        connected = self.reader.connect()
        self.log_result("excel_connect", connected,
                        "Make sure epoch_v1.xlsm is open!" if not connected else "")
        return connected

    def test_read_zone_results(self) -> bool:
        """Test reading zone_results worksheet."""
        df = self.reader.read_zone_results()

        if df is not None and len(df) > 0:
            # Save first ticker for subsequent tests
            self.test_ticker = str(df.iloc[0]['ticker'])
            self.log_result("read_zone_results", True)
            print(f"         Found {len(df)} zones, using {self.test_ticker} for tests")
            return True
        else:
            self.log_result("read_zone_results", False, "No zones found")
            return False

    def test_zone_results_columns(self) -> bool:
        """Test that zone_results has expected columns."""
        df = self.reader.read_zone_results()

        if df is None or df.empty:
            self.log_result("zone_results_columns", False, "No data")
            return False

        expected = ['ticker', 'zone_id', 'hvn_poc', 'zone_high', 'zone_low', 'score', 'rank']
        missing = [c for c in expected if c not in df.columns]

        if not missing:
            self.log_result("zone_results_columns", True)
            return True
        else:
            self.log_result("zone_results_columns", False, f"Missing: {missing}")
            return False

    def test_get_primary_zone_long(self) -> bool:
        """Test getting primary zone for long direction."""
        if not self.test_ticker:
            self.log_result("get_primary_zone_long", False, "No test ticker")
            return False

        zone = self.reader.get_primary_zone(self.test_ticker, 'long')

        if zone is not None:
            # Validate zone has required fields
            required = ['zone_id', 'zone_high', 'zone_low', 'hvn_poc']
            has_all = all(k in zone for k in required)

            if has_all:
                self.log_result("get_primary_zone_long", True)
                print(f"         Zone: ${zone['zone_low']:.2f} - ${zone['zone_high']:.2f}")
                return True
            else:
                self.log_result("get_primary_zone_long", False, f"Missing fields in zone")
                return False
        else:
            # It's ok if no zone is marked - just log as pass with note
            self.log_result("get_primary_zone_long", True)
            print(f"         No primary long zone marked for {self.test_ticker}")
            return True

    def test_get_primary_zone_short(self) -> bool:
        """Test getting primary zone for short direction."""
        if not self.test_ticker:
            self.log_result("get_primary_zone_short", False, "No test ticker")
            return False

        zone = self.reader.get_primary_zone(self.test_ticker, 'short')

        # Either we get a valid zone or None is acceptable
        if zone is None or 'zone_id' in zone:
            self.log_result("get_primary_zone_short", True)
            return True
        else:
            self.log_result("get_primary_zone_short", False, "Invalid zone structure")
            return False

    def test_read_hvn_pocs(self) -> bool:
        """Test reading HVN POC levels."""
        if not self.test_ticker:
            self.log_result("read_hvn_pocs", False, "No test ticker")
            return False

        pocs = self.reader.read_hvn_pocs(self.test_ticker)

        # POCs should be a list (possibly empty)
        if isinstance(pocs, list):
            self.log_result("read_hvn_pocs", True)
            if pocs:
                print(f"         Found {len(pocs)} POCs: ${pocs[0]:.2f}...")
            else:
                print(f"         No POCs found for {self.test_ticker}")
            return True
        else:
            self.log_result("read_hvn_pocs", False, f"Expected list, got {type(pocs)}")
            return False

    def test_read_camarilla(self) -> bool:
        """Test reading Camarilla levels."""
        if not self.test_ticker:
            self.log_result("read_camarilla", False, "No test ticker")
            return False

        cam = self.reader.read_camarilla_levels(self.test_ticker)

        # Camarilla should be a dict
        if isinstance(cam, dict):
            self.log_result("read_camarilla", True)
            if cam.get('d1_s3') and cam.get('d1_r3'):
                print(f"         S3: ${cam['d1_s3']:.2f}, R3: ${cam['d1_r3']:.2f}")
            else:
                print(f"         Camarilla levels empty for {self.test_ticker}")
            return True
        else:
            self.log_result("read_camarilla", False, f"Expected dict, got {type(cam)}")
            return False

    def test_read_atr(self) -> bool:
        """Test reading ATR."""
        if not self.test_ticker:
            self.log_result("read_atr", False, "No test ticker")
            return False

        atr = self.reader.read_atr(self.test_ticker, 'd1')

        # ATR can be None or a float
        if atr is None or (isinstance(atr, (int, float)) and atr >= 0):
            self.log_result("read_atr", True)
            if atr:
                print(f"         D1 ATR: ${atr:.2f}")
            else:
                print(f"         No ATR found for {self.test_ticker}")
            return True
        else:
            self.log_result("read_atr", False, f"Invalid ATR: {atr}")
            return False

    def test_read_analysis_setups(self) -> bool:
        """Test reading analysis worksheet setups."""
        if not self.test_ticker:
            self.log_result("read_analysis_setups", False, "No test ticker")
            return False

        setups = self.reader.read_analysis_setups(self.test_ticker)

        # Should return dict with 'primary' and 'secondary' keys
        if isinstance(setups, dict) and 'primary' in setups and 'secondary' in setups:
            self.log_result("read_analysis_setups", True)
            if setups['primary']:
                print(f"         Primary: {setups['primary'].get('direction')} -> {setups['primary'].get('target')}")
            else:
                print(f"         No setups found for {self.test_ticker}")
            return True
        else:
            self.log_result("read_analysis_setups", False, "Invalid structure")
            return False

    def test_filter_by_ticker(self) -> bool:
        """Test filtering zone_results by ticker."""
        if not self.test_ticker:
            self.log_result("filter_by_ticker", False, "No test ticker")
            return False

        df = self.reader.read_zone_results(self.test_ticker)

        if df is not None:
            # All rows should be for test_ticker
            if df.empty or all(str(t).upper() == self.test_ticker.upper() for t in df['ticker']):
                self.log_result("filter_by_ticker", True)
                print(f"         Found {len(df)} zones for {self.test_ticker}")
                return True
            else:
                self.log_result("filter_by_ticker", False, "Filter didn't work correctly")
                return False
        else:
            self.log_result("filter_by_ticker", False, "No data returned")
            return False

    def run_all(self) -> bool:
        """Run all tests."""
        print("\n" + "=" * 60)
        print("EPOCH READER - TEST SUITE")
        print("=" * 60)
        print(f"\nExcel file: {EXCEL_FILEPATH}\n")

        # First test connection - abort if fails
        if not self.test_connect():
            print("\n[ABORT] Cannot continue without Excel connection")
            return False

        # Run remaining tests
        self.test_read_zone_results()
        self.test_zone_results_columns()
        self.test_get_primary_zone_long()
        self.test_get_primary_zone_short()
        self.test_read_hvn_pocs()
        self.test_read_camarilla()
        self.test_read_atr()
        self.test_read_analysis_setups()
        self.test_filter_by_ticker()

        # Summary
        passed = sum(1 for _, p, _ in self.results if p)
        total = len(self.results)

        print("\n" + "-" * 60)
        print(f"RESULTS: {passed}/{total} tests passed")
        print("-" * 60)

        # Write debug report if any failures
        if passed < total:
            filepath = get_debug_filepath('test', 'epoch_reader')
            with open(filepath, 'w') as f:
                f.write("EPOCH READER TEST REPORT\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"Excel file: {EXCEL_FILEPATH}\n")
                f.write(f"Test ticker: {self.test_ticker}\n\n")
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

    tester = TestEpochReader()
    success = tester.run_all()
    sys.exit(0 if success else 1)
