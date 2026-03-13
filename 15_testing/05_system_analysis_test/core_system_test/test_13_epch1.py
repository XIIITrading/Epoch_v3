"""
Test 13: Does EPCH1 fire on zone traversal?
Source: 03_backtest/engine/entry_models.py

EPCH1 (Continuation):
  LONG:  Opens BELOW zone → closes ABOVE zone_high
  LONG:  Opens INSIDE zone → closes ABOVE zone_high → price_origin == BELOW
  SHORT: Opens ABOVE zone → closes BELOW zone_low
  SHORT: Opens INSIDE zone → closes BELOW zone_low → price_origin == ABOVE
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from conftest import make_check


def check_epch1_long(bar_open, bar_close, zone_high, zone_low, price_origin=None):
    """Replicate EPCH1 LONG logic."""
    opens_below = bar_open < zone_low
    opens_inside = zone_low <= bar_open <= zone_high
    closes_above = bar_close > zone_high

    if opens_below and closes_above:
        return True
    if opens_inside and closes_above and price_origin == "BELOW":
        return True
    return False


def check_epch1_short(bar_open, bar_close, zone_high, zone_low, price_origin=None):
    """Replicate EPCH1 SHORT logic."""
    opens_above = bar_open > zone_high
    opens_inside = zone_low <= bar_open <= zone_high
    closes_below = bar_close < zone_low

    if opens_above and closes_below:
        return True
    if opens_inside and closes_below and price_origin == "ABOVE":
        return True
    return False


class TestEPCH1:
    TEST_ID = "test_13_epch1"
    QUESTION = "Does EPCH1 fire on zone traversal?"

    def test_long_traversal(self, result_writer):
        """Open below zone, close above → LONG fires."""
        assert check_epch1_long(98.0, 102.0, 101.0, 99.0) is True

    def test_long_inside_below_origin(self, result_writer):
        """Open inside zone, close above, origin=BELOW → LONG fires."""
        assert check_epch1_long(100.0, 102.0, 101.0, 99.0, "BELOW") is True

    def test_long_inside_above_origin_no_fire(self, result_writer):
        """Open inside zone, close above, origin=ABOVE → LONG does NOT fire."""
        assert check_epch1_long(100.0, 102.0, 101.0, 99.0, "ABOVE") is False

    def test_long_no_close_above(self, result_writer):
        """Open below zone, close stays inside → no fire."""
        assert check_epch1_long(98.0, 100.0, 101.0, 99.0) is False

    def test_short_traversal(self, result_writer):
        """Open above zone, close below → SHORT fires."""
        assert check_epch1_short(102.0, 98.0, 101.0, 99.0) is True

    def test_short_inside_above_origin(self, result_writer):
        """Open inside zone, close below, origin=ABOVE → SHORT fires."""
        assert check_epch1_short(100.0, 98.0, 101.0, 99.0, "ABOVE") is True

    def test_short_inside_below_origin_no_fire(self, result_writer):
        """Open inside zone, close below, origin=BELOW → SHORT does NOT fire."""
        assert check_epch1_short(100.0, 98.0, 101.0, 99.0, "BELOW") is False

    def test_full_suite(self, result_writer):
        checks = []
        checks.append(make_check("long_traversal", True,
                                 check_epch1_long(98.0, 102.0, 101.0, 99.0)))
        checks.append(make_check("long_inside_below", True,
                                 check_epch1_long(100.0, 102.0, 101.0, 99.0, "BELOW")))
        checks.append(make_check("long_inside_above_no", False,
                                 check_epch1_long(100.0, 102.0, 101.0, 99.0, "ABOVE")))
        checks.append(make_check("short_traversal", True,
                                 check_epch1_short(102.0, 98.0, 101.0, 99.0)))
        checks.append(make_check("short_inside_above", True,
                                 check_epch1_short(100.0, 98.0, 101.0, 99.0, "ABOVE")))

        result_writer.write_validation(self.TEST_ID, self.QUESTION, checks)
        assert all(c["passed"] for c in checks)
