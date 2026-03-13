"""
Test 14: Does EPCH2 fire on zone rejection?
Source: 03_backtest/engine/entry_models.py

EPCH2 (Rejection):
  LONG:  Opens ABOVE zone → wick enters zone (low <= zone_high) → closes ABOVE zone_high
  LONG:  Opens INSIDE zone → closes ABOVE zone_high → price_origin == ABOVE
  SHORT: Opens BELOW zone → wick enters zone (high >= zone_low) → closes BELOW zone_low
  SHORT: Opens INSIDE zone → closes BELOW zone_low → price_origin == BELOW
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from conftest import make_check


def check_epch2_long(bar_open, bar_high, bar_low, bar_close,
                     zone_high, zone_low, price_origin=None):
    """Replicate EPCH2 LONG logic."""
    opens_above = bar_open > zone_high
    opens_inside = zone_low <= bar_open <= zone_high
    wick_enters = bar_low <= zone_high
    closes_above = bar_close > zone_high

    if opens_above and wick_enters and closes_above:
        return True
    if opens_inside and closes_above and price_origin == "ABOVE":
        return True
    return False


def check_epch2_short(bar_open, bar_high, bar_low, bar_close,
                      zone_high, zone_low, price_origin=None):
    """Replicate EPCH2 SHORT logic."""
    opens_below = bar_open < zone_low
    opens_inside = zone_low <= bar_open <= zone_high
    wick_enters = bar_high >= zone_low
    closes_below = bar_close < zone_low

    if opens_below and wick_enters and closes_below:
        return True
    if opens_inside and closes_below and price_origin == "BELOW":
        return True
    return False


class TestEPCH2:
    TEST_ID = "test_14_epch2"
    QUESTION = "Does EPCH2 fire on zone rejection?"

    def test_long_rejection(self, result_writer):
        """Open above, wick into zone, close above → LONG fires."""
        # zone: [99, 101], open=102, low=100.5 (enters zone), close=102.5
        assert check_epch2_long(102.0, 103.0, 100.5, 102.5, 101.0, 99.0) is True

    def test_long_no_wick(self, result_writer):
        """Open above, wick does NOT enter zone → no fire."""
        # zone: [99, 101], open=102, low=101.5 (stays above zone_high)
        assert check_epch2_long(102.0, 103.0, 101.5, 102.5, 101.0, 99.0) is False

    def test_long_inside_above_origin(self, result_writer):
        """Open inside, close above, origin=ABOVE → LONG fires."""
        assert check_epch2_long(100.0, 103.0, 99.5, 102.0, 101.0, 99.0, "ABOVE") is True

    def test_short_rejection(self, result_writer):
        """Open below, wick into zone, close below → SHORT fires."""
        # zone: [99, 101], open=98, high=99.5 (enters zone), close=97.5
        assert check_epch2_short(98.0, 99.5, 97.0, 97.5, 101.0, 99.0) is True

    def test_short_no_wick(self, result_writer):
        """Open below, wick does NOT enter zone → no fire."""
        # zone: [99, 101], open=98, high=98.5 (stays below zone_low)
        assert check_epch2_short(98.0, 98.5, 97.0, 97.5, 101.0, 99.0) is False

    def test_short_inside_below_origin(self, result_writer):
        """Open inside, close below, origin=BELOW → SHORT fires."""
        assert check_epch2_short(100.0, 100.5, 98.0, 98.5, 101.0, 99.0, "BELOW") is True

    def test_full_suite(self, result_writer):
        checks = []
        checks.append(make_check("long_rejection", True,
                                 check_epch2_long(102.0, 103.0, 100.5, 102.5, 101.0, 99.0)))
        checks.append(make_check("long_no_wick", False,
                                 check_epch2_long(102.0, 103.0, 101.5, 102.5, 101.0, 99.0)))
        checks.append(make_check("short_rejection", True,
                                 check_epch2_short(98.0, 99.5, 97.0, 97.5, 101.0, 99.0)))
        checks.append(make_check("short_no_wick", False,
                                 check_epch2_short(98.0, 98.5, 97.0, 97.5, 101.0, 99.0)))

        result_writer.write_validation(self.TEST_ID, self.QUESTION, checks)
        assert all(c["passed"] for c in checks)
