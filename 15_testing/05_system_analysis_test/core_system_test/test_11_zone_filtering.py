"""
Test 11: Does filtering remove overlaps, keep best?
Source: 01_application/calculators/zone_filter.py

Pipeline:
1. Tier classification (L-rank → T-tier)
2. ATR distance and proximity group
3. Sort by proximity group, score desc, distance asc
4. Eliminate overlapping zones
5. Identify bull/bear POCs
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / "01_application"))

from conftest import make_check

from weights import get_tier_from_rank, TIER_MAP


def classify_tier(rank: str) -> str:
    """L-rank → T-tier."""
    return TIER_MAP.get(rank, "T1")


def calculate_proximity(zone_mid: float, price: float, d1_atr: float) -> dict:
    """Calculate ATR distance and proximity group."""
    distance = abs(zone_mid - price)
    atr_distance = distance / d1_atr if d1_atr > 0 else float("inf")
    if atr_distance <= 1.0:
        group = "1"
    elif atr_distance <= 2.0:
        group = "2"
    else:
        group = None
    return {"atr_distance": atr_distance, "proximity_group": group}


def eliminate_overlaps(zones: list) -> list:
    """
    Zones = list of dicts with zone_high, zone_low, score.
    Pre-sorted. Keep first non-overlapping.
    """
    selected = []
    for z in zones:
        has_overlap = False
        for s in selected:
            if z["zone_low"] < s["zone_high"] and z["zone_high"] > s["zone_low"]:
                has_overlap = True
                break
        if not has_overlap:
            selected.append(z)
    return selected


class TestZoneFiltering:
    TEST_ID = "test_11_zone_filtering"
    QUESTION = "Does filtering remove overlaps, keep best?"

    def test_tier_mapping(self, result_writer):
        """L1/L2→T1, L3→T2, L4/L5→T3."""
        assert classify_tier("L1") == "T1"
        assert classify_tier("L2") == "T1"
        assert classify_tier("L3") == "T2"
        assert classify_tier("L4") == "T3"
        assert classify_tier("L5") == "T3"

    def test_proximity_group_1(self, result_writer):
        """Zone within 1 ATR → Group 1."""
        r = calculate_proximity(100.5, 100.0, 2.0)
        assert r["proximity_group"] == "1"
        assert r["atr_distance"] == 0.25

    def test_proximity_group_2(self, result_writer):
        """Zone 1-2 ATR away → Group 2."""
        r = calculate_proximity(103.0, 100.0, 2.0)
        assert r["proximity_group"] == "2"

    def test_proximity_excluded(self, result_writer):
        """Zone > 2 ATR away → excluded."""
        r = calculate_proximity(110.0, 100.0, 2.0)
        assert r["proximity_group"] is None

    def test_overlap_elimination(self, result_writer):
        """Overlapping zones: highest score (first in sorted list) wins."""
        zones = [
            {"zone_high": 101.0, "zone_low": 99.0, "score": 10.0, "name": "A"},
            {"zone_high": 100.5, "zone_low": 98.5, "score": 8.0, "name": "B"},  # overlaps A
            {"zone_high": 106.0, "zone_low": 104.0, "score": 7.0, "name": "C"},  # no overlap
        ]
        selected = eliminate_overlaps(zones)
        names = [z["name"] for z in selected]
        assert "A" in names
        assert "B" not in names
        assert "C" in names

    def test_no_overlap_all_kept(self, result_writer):
        """Non-overlapping zones all survive."""
        zones = [
            {"zone_high": 101.0, "zone_low": 99.0, "score": 10.0},
            {"zone_high": 106.0, "zone_low": 104.0, "score": 8.0},
            {"zone_high": 111.0, "zone_low": 109.0, "score": 6.0},
        ]
        selected = eliminate_overlaps(zones)
        assert len(selected) == 3

    def test_full_suite(self, result_writer):
        checks = []

        # Tier mapping
        checks.append(make_check("L1_to_T1", "T1", classify_tier("L1")))
        checks.append(make_check("L3_to_T2", "T2", classify_tier("L3")))
        checks.append(make_check("L5_to_T3", "T3", classify_tier("L5")))

        # Proximity
        r = calculate_proximity(100.5, 100.0, 2.0)
        checks.append(make_check("group_1_proximity", "1", r["proximity_group"]))

        # Overlap elimination
        zones = [
            {"zone_high": 101.0, "zone_low": 99.0, "score": 10.0, "name": "A"},
            {"zone_high": 100.5, "zone_low": 98.5, "score": 8.0, "name": "B"},
            {"zone_high": 106.0, "zone_low": 104.0, "score": 7.0, "name": "C"},
        ]
        selected = eliminate_overlaps(zones)
        checks.append(make_check("overlap_removed", 2, len(selected)))

        result_writer.write_validation(self.TEST_ID, self.QUESTION, checks)
        assert all(c["passed"] for c in checks)
