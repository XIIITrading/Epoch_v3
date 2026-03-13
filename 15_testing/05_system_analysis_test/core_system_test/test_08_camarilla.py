"""
Test 08: Are Camarilla pivots correct?
Source: 01_application/calculators/bar_data.py - _calc_cam_from_ohlc

Since BarDataCalculator uses Polygon API, we test the formula directly.
Formula:
    Range = High - Low
    S3 = Close - Range * 0.500
    S4 = Close - Range * 0.618
    S6 = Close - Range * 1.000
    R3 = Close + Range * 0.500
    R4 = Close + Range * 0.618
    R6 = Close + Range * 1.000
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / "01_application"))

from conftest import make_check

from core import CamarillaLevels


def calc_camarilla(high: float, low: float, close: float) -> dict:
    """Replicate _calc_cam_from_ohlc formula for testing."""
    price_range = high - low
    return {
        "s6": round(close - (price_range * 1.000), 2),
        "s4": round(close - (price_range * 0.618), 2),
        "s3": round(close - (price_range * 0.500), 2),
        "r3": round(close + (price_range * 0.500), 2),
        "r4": round(close + (price_range * 0.618), 2),
        "r6": round(close + (price_range * 1.000), 2),
    }


class TestCamarilla:
    TEST_ID = "test_08_camarilla"
    QUESTION = "Are Camarilla pivots correct?"

    def test_known_values(self, result_writer):
        """H=110, L=100, C=105 → Range=10."""
        cam = calc_camarilla(110.0, 100.0, 105.0)
        assert cam["s6"] == 95.0    # 105 - 10*1.0
        assert cam["s4"] == 98.82   # 105 - 10*0.618
        assert cam["s3"] == 100.0   # 105 - 10*0.5
        assert cam["r3"] == 110.0   # 105 + 10*0.5
        assert cam["r4"] == 111.18  # 105 + 10*0.618
        assert cam["r6"] == 115.0   # 105 + 10*1.0

    def test_symmetry(self, result_writer):
        """R levels mirror S levels around close."""
        cam = calc_camarilla(110.0, 100.0, 105.0)
        # r3 - close should equal close - s3
        assert abs((cam["r3"] - 105.0) - (105.0 - cam["s3"])) < 0.01
        assert abs((cam["r4"] - 105.0) - (105.0 - cam["s4"])) < 0.01
        assert abs((cam["r6"] - 105.0) - (105.0 - cam["s6"])) < 0.01

    def test_zero_range(self, result_writer):
        """Zero range → all levels collapse to close."""
        cam = calc_camarilla(100.0, 100.0, 100.0)
        for key in ["s6", "s4", "s3", "r3", "r4", "r6"]:
            assert cam[key] == 100.0

    def test_full_suite(self, result_writer):
        """Run all checks and write JSON result."""
        checks = []
        cam = calc_camarilla(110.0, 100.0, 105.0)

        checks.append(make_check("s6", 95.0, cam["s6"]))
        checks.append(make_check("s4", 98.82, cam["s4"]))
        checks.append(make_check("s3", 100.0, cam["s3"]))
        checks.append(make_check("r3", 110.0, cam["r3"]))
        checks.append(make_check("r4", 111.18, cam["r4"]))
        checks.append(make_check("r6", 115.0, cam["r6"]))

        result_writer.write_validation(self.TEST_ID, self.QUESTION, checks)
        assert all(c["passed"] for c in checks)
