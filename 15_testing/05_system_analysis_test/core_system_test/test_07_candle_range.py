"""
Test 07: Does range classify absorption vs momentum?
Source: shared.indicators.core.candle_range
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from conftest import make_check

from shared.indicators.core.candle_range import (
    calculate_candle_range_pct, calculate_candle_range_from_bar,
    get_range_classification, is_absorption_zone, is_candle_range_healthy,
)


class TestCandleRange:
    TEST_ID = "test_07_candle_range"
    QUESTION = "Does range classify absorption vs momentum?"

    def test_absorption(self, result_writer):
        """Range < 0.12% → ABSORPTION."""
        # H=100.05, L=100.00, C=100.02 → pct = 0.05/100.02 * 100 ≈ 0.05%
        pct = calculate_candle_range_pct(100.05, 100.00, 100.02)
        assert pct < 0.12
        assert get_range_classification(pct) == "ABSORPTION"
        assert is_absorption_zone(pct) is True

    def test_low_range(self, result_writer):
        """Range 0.12-0.15% → LOW."""
        # H=100.13, L=100.00, C=100.00 → pct = 0.13/100.0 * 100 = 0.13%
        pct = calculate_candle_range_pct(100.13, 100.00, 100.00)
        assert 0.12 <= pct < 0.15
        assert get_range_classification(pct) == "LOW"

    def test_normal_range(self, result_writer):
        """Range 0.15-0.20% → NORMAL (has momentum)."""
        # H=100.17, L=100.00, C=100.00 → pct = 0.17/100.0 * 100 = 0.17%
        pct = calculate_candle_range_pct(100.17, 100.00, 100.00)
        assert 0.15 <= pct < 0.20
        assert get_range_classification(pct) == "NORMAL"
        assert is_candle_range_healthy(pct) is True

    def test_high_range(self, result_writer):
        """Range >= 0.20% → HIGH."""
        # H=100.25, L=100.00, C=100.00 → pct = 0.25/100.0 * 100 = 0.25%
        pct = calculate_candle_range_pct(100.25, 100.00, 100.00)
        assert pct >= 0.20
        assert get_range_classification(pct) == "HIGH"

    def test_from_bar_object(self, result_writer):
        """calculate_candle_range_from_bar returns CandleRangeResult."""
        bar = {"high": 100.25, "low": 100.00, "close": 100.00}
        result = calculate_candle_range_from_bar(bar)
        assert result.classification == "HIGH"
        assert result.is_absorption is False
        assert result.has_momentum is True

    def test_full_suite(self, result_writer):
        """Run all checks and write JSON result."""
        checks = []

        # Absorption
        pct1 = calculate_candle_range_pct(100.05, 100.00, 100.02)
        checks.append(make_check("absorption_class", "ABSORPTION",
                                 get_range_classification(pct1)))

        # Low
        pct2 = calculate_candle_range_pct(100.13, 100.00, 100.00)
        checks.append(make_check("low_class", "LOW",
                                 get_range_classification(pct2)))

        # Normal
        pct3 = calculate_candle_range_pct(100.17, 100.00, 100.00)
        checks.append(make_check("normal_class", "NORMAL",
                                 get_range_classification(pct3)))

        # High
        pct4 = calculate_candle_range_pct(100.25, 100.00, 100.00)
        checks.append(make_check("high_class", "HIGH",
                                 get_range_classification(pct4)))

        result_writer.write_validation(self.TEST_ID, self.QUESTION, checks)
        assert all(c["passed"] for c in checks)
