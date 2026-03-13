"""
Test 10: Does scoring sum confluences correctly?
Source: 01_application/calculators/zone_calculator.py

Zone scoring logic:
1. Create zone around POC: [poc - m15_atr/2, poc + m15_atr/2]
2. For each confluence level that overlaps the zone, track max weight per bucket type
3. total_score = poc_base_weight + sum(bucket_max_weights)
4. Rank = L1-L5 based on score thresholds
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / "01_application"))

from conftest import make_check

from weights import (
    EPOCH_POC_BASE_WEIGHTS,
    BUCKET_WEIGHTS,
    get_rank_from_score,
    get_tier_from_rank,
)


def calculate_zone_score(
    poc_rank: int,
    poc_price: float,
    m15_atr: float,
    confluence_levels: list,
) -> dict:
    """
    Replicate zone scoring logic for testing.

    Args:
        poc_rank: 1-10 POC rank
        poc_price: POC price level
        m15_atr: M15 ATR for zone width
        confluence_levels: list of dicts with {price, weight, con_type}

    Returns:
        dict with zone_high, zone_low, score, rank, bucket_scores
    """
    zone_high = poc_price + (m15_atr / 2)
    zone_low = poc_price - (m15_atr / 2)

    bucket_scores = {b: 0.0 for b in BUCKET_WEIGHTS}

    for level in confluence_levels:
        lev_price = level["price"]
        lev_high = lev_price + (m15_atr / 2)
        lev_low = lev_price - (m15_atr / 2)

        # Check overlap
        if zone_low < lev_high and zone_high > lev_low:
            con_type = level["con_type"]
            weight = level["weight"]
            if con_type in bucket_scores:
                bucket_scores[con_type] = max(bucket_scores[con_type], weight)

    poc_key = f"hvn_poc{poc_rank}"
    base_score = EPOCH_POC_BASE_WEIGHTS.get(poc_key, 0)
    bucket_total = sum(bucket_scores.values())
    total_score = base_score + bucket_total
    rank = get_rank_from_score(total_score)

    return {
        "zone_high": zone_high,
        "zone_low": zone_low,
        "base_score": base_score,
        "bucket_total": bucket_total,
        "total_score": total_score,
        "rank": rank,
        "bucket_scores": bucket_scores,
    }


class TestZoneScoring:
    TEST_ID = "test_10_zone_scoring"
    QUESTION = "Does scoring sum confluences correctly?"

    def test_poc1_no_confluence(self, result_writer):
        """POC1 with no confluences → score = base only (3.0) → L2."""
        result = calculate_zone_score(1, 100.0, 2.0, [])
        assert abs(result["base_score"] - 3.0) < 1e-6
        assert abs(result["total_score"] - 3.0) < 1e-6
        assert result["rank"] == "L2"

    def test_bucket_max_not_stacking(self, result_writer):
        """Two monthly levels in zone → only max weight (3.0), not 6.0."""
        levels = [
            {"price": 100.0, "weight": 3.0, "con_type": "monthly_level"},
            {"price": 100.2, "weight": 3.0, "con_type": "monthly_level"},
        ]
        result = calculate_zone_score(1, 100.0, 2.0, levels)
        # Both overlap, but bucket max = 3.0 (not 6.0)
        assert abs(result["bucket_scores"]["monthly_level"] - 3.0) < 1e-6
        # Total = 3.0 (base) + 3.0 (monthly) = 6.0 → L3
        assert abs(result["total_score"] - 6.0) < 1e-6
        assert result["rank"] == "L3"

    def test_multi_bucket_scoring(self, result_writer):
        """Multiple bucket types add up correctly."""
        levels = [
            {"price": 100.0, "weight": 3.0, "con_type": "monthly_level"},
            {"price": 100.0, "weight": 2.0, "con_type": "weekly_level"},
            {"price": 100.0, "weight": 1.0, "con_type": "daily_level"},
        ]
        result = calculate_zone_score(1, 100.0, 2.0, levels)
        # base=3.0 + monthly=3.0 + weekly=2.0 + daily=1.0 = 9.0 → L4
        assert abs(result["total_score"] - 9.0) < 1e-6
        assert result["rank"] == "L4"

    def test_l5_rank(self, result_writer):
        """Score >= 12 → L5."""
        levels = [
            {"price": 100.0, "weight": 3.0, "con_type": "monthly_level"},
            {"price": 100.0, "weight": 3.0, "con_type": "monthly_cam"},
            {"price": 100.0, "weight": 3.0, "con_type": "prior_monthly"},
        ]
        result = calculate_zone_score(1, 100.0, 2.0, levels)
        # base=3.0 + 3+3+3=9 = 12.0 → L5
        assert abs(result["total_score"] - 12.0) < 1e-6
        assert result["rank"] == "L5"

    def test_no_overlap(self, result_writer):
        """Confluence level far from zone → no contribution."""
        levels = [{"price": 200.0, "weight": 3.0, "con_type": "monthly_level"}]
        result = calculate_zone_score(1, 100.0, 2.0, levels)
        assert abs(result["bucket_scores"]["monthly_level"] - 0.0) < 1e-6

    def test_full_suite(self, result_writer):
        checks = []

        # POC1 base
        r = calculate_zone_score(1, 100.0, 2.0, [])
        checks.append(make_check("poc1_base_score", 3.0, r["base_score"]))

        # Bucket max (no stacking)
        levels = [
            {"price": 100.0, "weight": 3.0, "con_type": "monthly_level"},
            {"price": 100.2, "weight": 3.0, "con_type": "monthly_level"},
        ]
        r = calculate_zone_score(1, 100.0, 2.0, levels)
        checks.append(make_check("no_stacking_monthly", 3.0, r["bucket_scores"]["monthly_level"]))

        # Multi-bucket
        levels = [
            {"price": 100.0, "weight": 3.0, "con_type": "monthly_level"},
            {"price": 100.0, "weight": 2.0, "con_type": "weekly_level"},
            {"price": 100.0, "weight": 1.0, "con_type": "daily_level"},
        ]
        r = calculate_zone_score(1, 100.0, 2.0, levels)
        checks.append(make_check("multi_bucket_total", 9.0, r["total_score"]))
        checks.append(make_check("multi_bucket_rank", "L4", r["rank"]))

        result_writer.write_validation(self.TEST_ID, self.QUESTION, checks)
        assert all(c["passed"] for c in checks)
