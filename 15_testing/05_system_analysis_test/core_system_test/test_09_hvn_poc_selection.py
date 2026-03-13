"""
Test 09: Do POCs select non-overlapping levels?
Source: 01_application/calculators/hvn_identifier.py - _select_pocs_no_overlap

We test the POC selection algorithm directly with synthetic volume profiles.
Algorithm:
1. Sort price levels by volume descending
2. For each level, check overlap with all selected POCs
3. Overlap = |price1 - price2| < ATR/2
4. Select up to 10 non-overlapping POCs
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from conftest import make_check


def select_pocs_no_overlap(volume_profile: dict, atr: float, max_pocs: int = 10) -> list:
    """
    Replicate HVNIdentifier._select_pocs_no_overlap for testing.
    Returns list of (price, volume, rank) tuples.
    """
    overlap_threshold = atr / 2
    sorted_levels = sorted(volume_profile.items(), key=lambda x: x[1], reverse=True)

    selected = []
    for price, volume in sorted_levels:
        has_overlap = False
        for sel_price, _, _ in selected:
            if abs(price - sel_price) < overlap_threshold:
                has_overlap = True
                break
        if not has_overlap:
            rank = len(selected) + 1
            selected.append((round(price, 2), volume, rank))
        if len(selected) >= max_pocs:
            break

    return selected


class TestHVNPOCSelection:
    TEST_ID = "test_09_hvn_poc_selection"
    QUESTION = "Do POCs select non-overlapping levels?"

    def test_basic_selection(self, result_writer):
        """Select top POC from well-separated levels."""
        profile = {100.0: 5000, 105.0: 4000, 110.0: 3000}
        pocs = select_pocs_no_overlap(profile, atr=4.0)
        # ATR/2 = 2.0, all levels >2.0 apart → all selected
        assert len(pocs) == 3
        assert pocs[0][0] == 100.0  # Highest volume first
        assert pocs[0][2] == 1      # Rank 1

    def test_overlap_rejection(self, result_writer):
        """Overlapping levels get rejected (keep highest volume)."""
        # 100.0 and 100.5 are within ATR/2=1.0
        profile = {100.0: 5000, 100.5: 4000, 105.0: 3000}
        pocs = select_pocs_no_overlap(profile, atr=2.0)
        assert len(pocs) == 2
        # 100.0 selected (highest vol), 100.5 rejected, 105.0 selected
        prices = [p[0] for p in pocs]
        assert 100.0 in prices
        assert 100.5 not in prices
        assert 105.0 in prices

    def test_max_10_pocs(self, result_writer):
        """Never select more than 10 POCs."""
        # 20 well-separated levels
        profile = {float(i * 10): 1000 - i for i in range(20)}
        pocs = select_pocs_no_overlap(profile, atr=2.0)
        assert len(pocs) == 10

    def test_rank_ordering(self, result_writer):
        """POCs are ranked 1-N in selection order (highest volume first)."""
        profile = {100.0: 5000, 110.0: 4000, 120.0: 3000}
        pocs = select_pocs_no_overlap(profile, atr=4.0)
        for i, (_, _, rank) in enumerate(pocs):
            assert rank == i + 1

    def test_full_suite(self, result_writer):
        """Run all checks and write JSON result."""
        checks = []

        # Basic selection
        profile = {100.0: 5000, 105.0: 4000, 110.0: 3000}
        pocs = select_pocs_no_overlap(profile, atr=4.0)
        checks.append(make_check("basic_count", 3, len(pocs)))
        checks.append(make_check("highest_vol_first", 100.0, pocs[0][0]))

        # Overlap rejection
        profile = {100.0: 5000, 100.5: 4000, 105.0: 3000}
        pocs = select_pocs_no_overlap(profile, atr=2.0)
        checks.append(make_check("overlap_rejected_count", 2, len(pocs)))
        prices = [p[0] for p in pocs]
        checks.append(make_check("overlap_rejected_100.5", True, 100.5 not in prices))

        # Max 10
        profile = {float(i * 10): 1000 - i for i in range(20)}
        pocs = select_pocs_no_overlap(profile, atr=2.0)
        checks.append(make_check("max_10_pocs", 10, len(pocs)))

        result_writer.write_validation(self.TEST_ID, self.QUESTION, checks)
        assert all(c["passed"] for c in checks)
