"""
Test 12: Is R:R calculated correctly?
Source: 01_application/calculators/setup_analyzer.py

R:R Logic:
  Bull: reward = target - hvn_poc, risk = hvn_poc - zone_low
  Bear: reward = hvn_poc - target, risk = zone_high - hvn_poc

Target Selection (3R/4R Cascade):
  Bull: Find POC above zone where POC >= zone_high + risk*3. If none, use 4R calc.
  Bear: Find POC below zone where POC <= zone_low - risk*3. If none, use 4R calc.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from conftest import make_check


def calculate_rr_bull(hvn_poc: float, zone_low: float, target: float) -> float:
    """Bull R:R = reward / risk."""
    risk = hvn_poc - zone_low
    if risk <= 0:
        return 0.0
    reward = target - hvn_poc
    return round(reward / risk, 2)


def calculate_rr_bear(hvn_poc: float, zone_high: float, target: float) -> float:
    """Bear R:R = reward / risk."""
    risk = zone_high - hvn_poc
    if risk <= 0:
        return 0.0
    reward = hvn_poc - target
    return round(reward / risk, 2)


def find_bull_target(
    hvn_poc: float, zone_high: float, zone_low: float,
    poc_list: list, min_rr: float = 3.0, default_rr: float = 4.0,
) -> tuple:
    """
    3R/4R cascade for bull target.
    Returns (target_price, target_id).
    """
    zone_risk = zone_high - zone_low
    target_3r = zone_high + (zone_risk * min_rr)

    best_target = None
    best_idx = None
    for i, poc in enumerate(poc_list):
        if poc > hvn_poc and poc >= target_3r:
            if best_idx is None or i < best_idx:
                best_target = poc
                best_idx = i

    if best_target is not None:
        return best_target, f"hvn_poc{best_idx + 1}"

    fallback = zone_high + (zone_risk * default_rr)
    return fallback, "4R_calc"


def find_bear_target(
    hvn_poc: float, zone_high: float, zone_low: float,
    poc_list: list, min_rr: float = 3.0, default_rr: float = 4.0,
) -> tuple:
    """3R/4R cascade for bear target."""
    zone_risk = zone_high - zone_low
    target_3r = zone_low - (zone_risk * min_rr)

    best_target = None
    best_idx = None
    for i, poc in enumerate(poc_list):
        if poc < hvn_poc and poc <= target_3r:
            if best_idx is None or i < best_idx:
                best_target = poc
                best_idx = i

    if best_target is not None:
        return best_target, f"hvn_poc{best_idx + 1}"

    fallback = zone_low - (zone_risk * default_rr)
    return fallback, "4R_calc"


class TestSetupRR:
    TEST_ID = "test_12_setup_rr"
    QUESTION = "Is R:R calculated correctly?"

    def test_bull_rr(self, result_writer):
        """Bull: poc=100, zone_low=99, target=103 → R:R=3.0."""
        rr = calculate_rr_bull(100.0, 99.0, 103.0)
        assert abs(rr - 3.0) < 0.01

    def test_bear_rr(self, result_writer):
        """Bear: poc=100, zone_high=101, target=96 → R:R=4.0."""
        rr = calculate_rr_bear(100.0, 101.0, 96.0)
        assert abs(rr - 4.0) < 0.01

    def test_bull_target_3r_found(self, result_writer):
        """POC above zone meets 3R threshold → selected."""
        # zone: [99, 101], risk=2, 3R threshold = 101 + 6 = 107
        poc_list = [100.0, 108.0, 95.0]  # poc2 at 108 qualifies
        target, target_id = find_bull_target(100.0, 101.0, 99.0, poc_list)
        assert target == 108.0
        assert target_id == "hvn_poc2"

    def test_bull_target_4r_fallback(self, result_writer):
        """No POC meets 3R → 4R calc fallback."""
        poc_list = [100.0, 102.0, 95.0]  # none >= 107
        target, target_id = find_bull_target(100.0, 101.0, 99.0, poc_list)
        assert target_id == "4R_calc"
        # 4R = 101 + 2*4 = 109
        assert abs(target - 109.0) < 0.01

    def test_bear_target_3r_found(self, result_writer):
        """POC below zone meets 3R threshold → selected."""
        # zone: [99, 101], risk=2, 3R threshold = 99 - 6 = 93
        poc_list = [100.0, 92.0, 105.0]  # poc2 at 92 qualifies
        target, target_id = find_bear_target(100.0, 101.0, 99.0, poc_list)
        assert target == 92.0
        assert target_id == "hvn_poc2"

    def test_bear_target_4r_fallback(self, result_writer):
        """No POC meets 3R → 4R calc fallback."""
        poc_list = [100.0, 97.0, 105.0]  # none <= 93
        target, target_id = find_bear_target(100.0, 101.0, 99.0, poc_list)
        assert target_id == "4R_calc"
        # 4R = 99 - 2*4 = 91
        assert abs(target - 91.0) < 0.01

    def test_full_suite(self, result_writer):
        checks = []

        checks.append(make_check("bull_rr_3.0", 3.0, calculate_rr_bull(100.0, 99.0, 103.0)))
        checks.append(make_check("bear_rr_4.0", 4.0, calculate_rr_bear(100.0, 101.0, 96.0)))

        poc_list = [100.0, 108.0, 95.0]
        target, tid = find_bull_target(100.0, 101.0, 99.0, poc_list)
        checks.append(make_check("bull_target_3r", 108.0, target))

        poc_list = [100.0, 102.0, 95.0]
        target, tid = find_bull_target(100.0, 101.0, 99.0, poc_list)
        checks.append(make_check("bull_target_4r_fallback", "4R_calc", tid))

        result_writer.write_validation(self.TEST_ID, self.QUESTION, checks)
        assert all(c["passed"] for c in checks)
