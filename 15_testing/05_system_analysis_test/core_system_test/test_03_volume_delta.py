"""
Test 03: Is bar delta correct from bar position?
Source: shared.indicators.core.volume_delta
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from conftest import make_check

from shared.indicators.core.volume_delta import calculate_bar_delta


class TestVolumeDelta:
    TEST_ID = "test_03_volume_delta"
    QUESTION = "Is bar delta correct from bar position?"

    def test_close_at_high(self, result_writer):
        """Close at high → position=1.0, multiplier=+1.0, delta=+volume."""
        result = calculate_bar_delta(100.0, 105.0, 100.0, 105.0, 1000)
        assert abs(result.bar_position - 1.0) < 1e-6
        assert abs(result.delta_multiplier - 1.0) < 1e-6
        assert abs(result.bar_delta - 1000.0) < 1e-6

    def test_close_at_low(self, result_writer):
        """Close at low → position=0.0, multiplier=-1.0, delta=-volume."""
        result = calculate_bar_delta(105.0, 105.0, 100.0, 100.0, 1000)
        assert abs(result.bar_position - 0.0) < 1e-6
        assert abs(result.delta_multiplier - (-1.0)) < 1e-6
        assert abs(result.bar_delta - (-1000.0)) < 1e-6

    def test_close_at_midpoint(self, result_writer):
        """Close at midpoint → position=0.5, multiplier=0.0, delta=0."""
        result = calculate_bar_delta(100.0, 110.0, 100.0, 105.0, 1000)
        assert abs(result.bar_position - 0.5) < 1e-6
        assert abs(result.delta_multiplier - 0.0) < 1e-6
        assert abs(result.bar_delta - 0.0) < 1e-6

    def test_doji_close_above_open(self, result_writer):
        """Doji (H==L): close >= open → position=1.0, delta=+volume."""
        result = calculate_bar_delta(100.0, 100.0, 100.0, 100.0, 500)
        assert abs(result.bar_position - 1.0) < 1e-6
        assert abs(result.bar_delta - 500.0) < 1e-6

    def test_doji_close_below_open(self, result_writer):
        """Doji (H==L): close < open → position=0.0, delta=-volume."""
        result = calculate_bar_delta(101.0, 100.0, 100.0, 99.0, 500)
        # H==L==100, close(99) < open(101)
        # But H-L=0, so doji handling: close < open → position=0, delta=-vol
        # Wait: H=100, L=100 → range=0. close=99 < open=101 → position=0
        assert abs(result.bar_position - 0.0) < 1e-6
        assert abs(result.bar_delta - (-500.0)) < 1e-6

    def test_full_suite(self, result_writer):
        """Run all checks and write JSON result."""
        checks = []

        # Check 1: Close at high
        r = calculate_bar_delta(100.0, 105.0, 100.0, 105.0, 1000)
        checks.append(make_check("close_at_high_position", 1.0, r.bar_position))
        checks.append(make_check("close_at_high_delta", 1000.0, r.bar_delta))

        # Check 2: Close at low
        r = calculate_bar_delta(105.0, 105.0, 100.0, 100.0, 1000)
        checks.append(make_check("close_at_low_position", 0.0, r.bar_position))
        checks.append(make_check("close_at_low_delta", -1000.0, r.bar_delta))

        # Check 3: Close at midpoint
        r = calculate_bar_delta(100.0, 110.0, 100.0, 105.0, 1000)
        checks.append(make_check("close_at_mid_delta", 0.0, r.bar_delta))

        # Check 4: Doji
        r = calculate_bar_delta(100.0, 100.0, 100.0, 100.0, 500)
        checks.append(make_check("doji_bullish_delta", 500.0, r.bar_delta))

        result_writer.write_validation(self.TEST_ID, self.QUESTION, checks)
        assert all(c["passed"] for c in checks)
