"""
Test 15: Does lookback find correct side?
Source: 03_backtest/engine/entry_models.py - _find_price_origin

Algorithm:
  Scan bar_history in REVERSE (most recent first).
  Return 'BELOW' if bar.close < zone_low
  Return 'ABOVE' if bar.close > zone_high
  Return None if no bar found outside zone.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from conftest import make_check


def find_price_origin(bar_history: list, zone_high: float, zone_low: float):
    """Replicate _find_price_origin logic."""
    for bar in reversed(bar_history):
        if bar["close"] < zone_low:
            return "BELOW"
        elif bar["close"] > zone_high:
            return "ABOVE"
    return None


class TestPriceOrigin:
    TEST_ID = "test_15_price_origin"
    QUESTION = "Does lookback find correct side?"

    def test_origin_below(self, result_writer):
        """Most recent bar outside zone closed below → BELOW."""
        history = [
            {"close": 95.0},  # below zone
            {"close": 100.0},  # inside zone
            {"close": 100.5},  # inside zone
        ]
        assert find_price_origin(history, 101.0, 99.0) == "BELOW"

    def test_origin_above(self, result_writer):
        """Most recent bar outside zone closed above → ABOVE."""
        history = [
            {"close": 105.0},  # above zone
            {"close": 100.0},  # inside zone
            {"close": 100.5},  # inside zone
        ]
        assert find_price_origin(history, 101.0, 99.0) == "ABOVE"

    def test_origin_none(self, result_writer):
        """All bars inside zone → None."""
        history = [
            {"close": 100.0},
            {"close": 100.5},
            {"close": 99.5},
        ]
        assert find_price_origin(history, 101.0, 99.0) is None

    def test_most_recent_wins(self, result_writer):
        """Most recent outside bar determines origin, not oldest."""
        history = [
            {"close": 95.0},   # below (oldest)
            {"close": 102.0},  # above
            {"close": 100.0},  # inside (most recent)
        ]
        # Reversed scan: [100.0 (inside), 102.0 (above → return ABOVE)]
        assert find_price_origin(history, 101.0, 99.0) == "ABOVE"

    def test_empty_history(self, result_writer):
        """Empty history → None."""
        assert find_price_origin([], 101.0, 99.0) is None

    def test_full_suite(self, result_writer):
        checks = []

        h1 = [{"close": 95.0}, {"close": 100.0}]
        checks.append(make_check("origin_below", "BELOW",
                                 find_price_origin(h1, 101.0, 99.0)))

        h2 = [{"close": 105.0}, {"close": 100.0}]
        checks.append(make_check("origin_above", "ABOVE",
                                 find_price_origin(h2, 101.0, 99.0)))

        h3 = [{"close": 100.0}, {"close": 100.5}]
        checks.append(make_check("origin_none", None,
                                 find_price_origin(h3, 101.0, 99.0)))

        h4 = [{"close": 95.0}, {"close": 102.0}, {"close": 100.0}]
        checks.append(make_check("most_recent_wins", "ABOVE",
                                 find_price_origin(h4, 101.0, 99.0)))

        result_writer.write_validation(self.TEST_ID, self.QUESTION, checks)
        assert all(c["passed"] for c in checks)
