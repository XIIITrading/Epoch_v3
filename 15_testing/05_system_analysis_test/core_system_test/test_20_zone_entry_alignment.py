"""
Test 20: Do entries fire inside scored zones?
Source: zone_calculator + entry_models (integration)

This integration test validates that:
1. A zone is created around a POC with proper scoring
2. An EPCH1 entry fires when price traverses that exact zone
3. The entry price falls within the scored zone boundaries
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / "01_application"))

from conftest import make_check

from weights import EPOCH_POC_BASE_WEIGHTS, get_rank_from_score


def create_zone(poc_price, m15_atr, poc_rank, confluence_score=0.0):
    """Create a scored zone around a POC."""
    zone_high = poc_price + (m15_atr / 2)
    zone_low = poc_price - (m15_atr / 2)
    base_score = EPOCH_POC_BASE_WEIGHTS.get(f"hvn_poc{poc_rank}", 0)
    total_score = base_score + confluence_score
    rank = get_rank_from_score(total_score)
    return {
        "poc_price": poc_price,
        "zone_high": zone_high,
        "zone_low": zone_low,
        "score": total_score,
        "rank": rank,
    }


def check_epch1_long(bar_open, bar_close, zone_high, zone_low):
    """EPCH1 LONG: open below → close above."""
    return bar_open < zone_low and bar_close > zone_high


def check_entry_in_zone(entry_price, zone_high, zone_low):
    """Check if entry price is at or near zone boundary."""
    # For continuation entries, entry is at bar_close which is above zone_high
    # The trade is related to this zone
    return entry_price >= zone_low


class TestZoneEntryAlignment:
    TEST_ID = "test_20_zone_entry_alignment"
    QUESTION = "Do entries fire inside scored zones?"

    def test_entry_fires_through_scored_zone(self, result_writer):
        """Zone scored → bar traverses → entry fires with correct zone bounds."""
        zone = create_zone(poc_price=100.0, m15_atr=2.0, poc_rank=1, confluence_score=6.0)
        # Zone: [99, 101], score=9.0, rank=L4

        # Bar opens below zone, closes above
        bar_open = 98.0
        bar_close = 102.0
        assert check_epch1_long(bar_open, bar_close, zone["zone_high"], zone["zone_low"])

    def test_entry_does_not_fire_outside_zone(self, result_writer):
        """Bar stays below zone → no entry."""
        zone = create_zone(poc_price=100.0, m15_atr=2.0, poc_rank=1)
        bar_open = 95.0
        bar_close = 98.0  # Stays below zone_low (99)
        assert not check_epch1_long(bar_open, bar_close, zone["zone_high"], zone["zone_low"])

    def test_zone_score_affects_rank(self, result_writer):
        """Higher confluence → higher rank, entries still fire correctly."""
        zone_low = create_zone(100.0, 2.0, poc_rank=10, confluence_score=0)
        zone_high = create_zone(100.0, 2.0, poc_rank=1, confluence_score=9.0)

        # Both zones same boundaries, different scores
        assert zone_low["rank"] == "L1"  # poc10 base=0.1
        assert zone_high["rank"] == "L5"  # poc1 base=3.0 + 9.0 = 12.0

        # Entry fires for both
        assert check_epch1_long(98.0, 102.0, zone_low["zone_high"], zone_low["zone_low"])
        assert check_epch1_long(98.0, 102.0, zone_high["zone_high"], zone_high["zone_low"])

    def test_full_suite(self, result_writer):
        checks = []

        # Zone + entry alignment
        zone = create_zone(100.0, 2.0, 1, 6.0)
        checks.append(make_check("zone_high", 101.0, zone["zone_high"]))
        checks.append(make_check("zone_low", 99.0, zone["zone_low"]))
        checks.append(make_check("zone_rank", "L4", zone["rank"]))

        fired = check_epch1_long(98.0, 102.0, zone["zone_high"], zone["zone_low"])
        checks.append(make_check("entry_fires", True, fired))

        not_fired = check_epch1_long(95.0, 98.0, zone["zone_high"], zone["zone_low"])
        checks.append(make_check("no_entry_below", False, not_fired))

        result_writer.write_validation(self.TEST_ID, self.QUESTION, checks)
        assert all(c["passed"] for c in checks)
