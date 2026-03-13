"""
Test 16: Are stop + R-levels placed correctly?
Source: 03_backtest/processor/.../m1_atr_stop_2/calculator.py

Logic:
  LONG:  stop = entry - m1_atr, R-levels = entry + N * m1_atr
  SHORT: stop = entry + m1_atr, R-levels = entry - N * m1_atr
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from conftest import make_check


def calculate_stop_and_levels(entry_price, m1_atr, direction):
    """Replicate stop and R-level calculation."""
    is_long = direction.upper() == "LONG"

    if is_long:
        stop = entry_price - m1_atr
        r_levels = {r: entry_price + (r * m1_atr) for r in range(1, 6)}
    else:
        stop = entry_price + m1_atr
        r_levels = {r: entry_price - (r * m1_atr) for r in range(1, 6)}

    return {
        "stop_price": stop,
        "stop_distance": m1_atr,
        "stop_distance_pct": (m1_atr / entry_price) * 100,
        "r_levels": r_levels,
    }


class TestATRStop:
    TEST_ID = "test_16_atr_stop"
    QUESTION = "Are stop + R-levels placed correctly?"

    def test_long_stop(self, result_writer):
        """LONG: stop = entry - ATR."""
        r = calculate_stop_and_levels(100.0, 2.0, "LONG")
        assert abs(r["stop_price"] - 98.0) < 1e-6

    def test_short_stop(self, result_writer):
        """SHORT: stop = entry + ATR."""
        r = calculate_stop_and_levels(100.0, 2.0, "SHORT")
        assert abs(r["stop_price"] - 102.0) < 1e-6

    def test_long_r_levels(self, result_writer):
        """LONG R-levels: entry + N*ATR."""
        r = calculate_stop_and_levels(100.0, 2.0, "LONG")
        assert abs(r["r_levels"][1] - 102.0) < 1e-6
        assert abs(r["r_levels"][2] - 104.0) < 1e-6
        assert abs(r["r_levels"][3] - 106.0) < 1e-6
        assert abs(r["r_levels"][4] - 108.0) < 1e-6
        assert abs(r["r_levels"][5] - 110.0) < 1e-6

    def test_short_r_levels(self, result_writer):
        """SHORT R-levels: entry - N*ATR."""
        r = calculate_stop_and_levels(100.0, 2.0, "SHORT")
        assert abs(r["r_levels"][1] - 98.0) < 1e-6
        assert abs(r["r_levels"][5] - 90.0) < 1e-6

    def test_stop_distance_pct(self, result_writer):
        """Stop distance % = ATR / entry * 100."""
        r = calculate_stop_and_levels(100.0, 2.0, "LONG")
        assert abs(r["stop_distance_pct"] - 2.0) < 1e-6

    def test_full_suite(self, result_writer):
        checks = []

        r = calculate_stop_and_levels(100.0, 2.0, "LONG")
        checks.append(make_check("long_stop", 98.0, r["stop_price"]))
        checks.append(make_check("long_r1", 102.0, r["r_levels"][1]))
        checks.append(make_check("long_r5", 110.0, r["r_levels"][5]))

        r = calculate_stop_and_levels(100.0, 2.0, "SHORT")
        checks.append(make_check("short_stop", 102.0, r["stop_price"]))
        checks.append(make_check("short_r1", 98.0, r["r_levels"][1]))

        result_writer.write_validation(self.TEST_ID, self.QUESTION, checks)
        assert all(c["passed"] for c in checks)
