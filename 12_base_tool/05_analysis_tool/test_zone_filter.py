"""
Test script for the zone filter.
Run from: C:/XIIITradingSystems/Epoch/05_analysis_tool
Command: python test_zone_filter.py
"""
import sys
from datetime import date, timedelta
from pathlib import Path

# Ensure we're in the right directory
sys.path.insert(0, str(Path(__file__).parent))


def test_imports():
    """Test that all imports work."""
    print("=" * 60)
    print("Testing imports...")
    print("=" * 60)

    from calculators import (
        calculate_bar_data,
        calculate_hvn,
        calculate_zones,
        ZoneFilter,
        filter_zones
    )
    from core import RawZone, FilteredZone, Direction, Rank, Tier
    from config.weights import TIER_MAP, get_tier_from_rank

    print("  [OK] All imports successful")
    print()
    return True


def test_tier_mapping():
    """Test tier assignment from ranks."""
    print("=" * 60)
    print("Testing Tier Mapping...")
    print("=" * 60)

    from config.weights import TIER_MAP, get_tier_from_rank

    print(f"  Tier mapping: {TIER_MAP}")
    print()

    test_cases = [
        ('L1', 'T1'),
        ('L2', 'T1'),
        ('L3', 'T2'),
        ('L4', 'T3'),
        ('L5', 'T3'),
    ]

    all_passed = True
    for rank, expected_tier in test_cases:
        actual_tier = get_tier_from_rank(rank)
        status = "[OK]" if actual_tier == expected_tier else "[FAIL]"
        print(f"  {status} {rank} -> {actual_tier} (expected {expected_tier})")
        if actual_tier != expected_tier:
            all_passed = False

    print()
    if all_passed:
        print("  [OK] All tier mapping tests passed")
    else:
        print("  [FAIL] Some tier mapping tests failed")
    print()
    return all_passed


def test_full_filter_pipeline():
    """Test the complete zone filter pipeline."""
    print("=" * 60)
    print("Testing Full Filter Pipeline...")
    print("=" * 60)

    from calculators import calculate_bar_data, calculate_hvn, calculate_zones, filter_zones
    from core import Direction

    ticker = "SPY"
    analysis_date = date.today() - timedelta(days=1)
    # Ensure we have a weekday
    if analysis_date.weekday() >= 5:
        analysis_date = analysis_date - timedelta(days=analysis_date.weekday() - 4)

    # Use 30 days as anchor period
    anchor_date = analysis_date - timedelta(days=30)

    print(f"  Ticker: {ticker}")
    print(f"  Analysis Date: {analysis_date}")
    print(f"  Anchor Date: {anchor_date}")
    print()

    # Step 1: Calculate bar data
    print("  Step 1: Calculating bar data...")
    bar_data = calculate_bar_data(ticker, analysis_date)
    print(f"    Price: ${bar_data.price:.2f}")
    print(f"    D1 ATR: ${bar_data.d1_atr:.4f}" if bar_data.d1_atr else "    D1 ATR: N/A")
    print()

    # Step 2: Calculate HVN POCs
    print("  Step 2: Calculating HVN POCs...")
    hvn_result = calculate_hvn(
        ticker=ticker,
        anchor_date=anchor_date,
        analysis_date=analysis_date,
        atr_value=bar_data.m15_atr
    )
    print(f"    POCs found: {len(hvn_result.pocs)}")
    print()

    # Step 3: Calculate raw zones
    print("  Step 3: Calculating raw zones...")
    raw_zones = calculate_zones(
        bar_data=bar_data,
        hvn_result=hvn_result,
        direction=Direction.NEUTRAL
    )
    print(f"    Raw zones: {len(raw_zones)}")
    print()

    # Step 4: Filter zones
    print("  Step 4: Filtering zones...")
    filtered_zones = filter_zones(
        raw_zones=raw_zones,
        bar_data=bar_data,
        direction=Direction.BULL
    )
    print(f"    Filtered zones: {len(filtered_zones)}")
    print()

    # Show filtered zone details
    print("  Filtered Zone Results:")
    print("  " + "-" * 80)
    print(f"  {'Zone':<10} {'POC':>8} {'Dist':>6} {'Grp':>3} {'Score':>6} {'Rank':<4} {'Tier':<3} {'Bull':>4} {'Bear':>4}")
    print("  " + "-" * 80)

    for zone in filtered_zones:
        bull_mark = "X" if zone.is_bull_poc else ""
        bear_mark = "X" if zone.is_bear_poc else ""
        print(
            f"  {zone.zone_id:<10} "
            f"${zone.hvn_poc:>7.2f} "
            f"{zone.atr_distance:>6.2f} "
            f"{zone.proximity_group or '-':>3} "
            f"{zone.score:>6.2f} "
            f"{zone.rank.value:<4} "
            f"{zone.tier.value:<3} "
            f"{bull_mark:>4} "
            f"{bear_mark:>4}"
        )

    print()

    # Summary stats
    tier_counts = {}
    for zone in filtered_zones:
        tier_counts[zone.tier.value] = tier_counts.get(zone.tier.value, 0) + 1

    print("  Summary:")
    print(f"    Total filtered zones: {len(filtered_zones)}")
    print(f"    Tier distribution: {tier_counts}")

    bull_count = sum(1 for z in filtered_zones if z.is_bull_poc)
    bear_count = sum(1 for z in filtered_zones if z.is_bear_poc)
    print(f"    Bull POCs: {bull_count}")
    print(f"    Bear POCs: {bear_count}")

    print()
    print("  [OK] Filter pipeline complete")
    print()
    return True


def test_overlap_elimination():
    """Test that overlapping zones are properly eliminated."""
    print("=" * 60)
    print("Testing Overlap Elimination...")
    print("=" * 60)

    from calculators import ZoneFilter
    from core import FilteredZone, Direction, Rank, Tier

    # Create test zones with overlaps
    test_zones = [
        FilteredZone(
            ticker="TEST",
            ticker_id="TEST_123",
            analysis_date=date.today(),
            price=100.0,
            direction=Direction.NEUTRAL,
            zone_id="hvn_poc1",
            poc_rank=1,
            hvn_poc=100.0,
            zone_high=100.5,
            zone_low=99.5,
            score=10.0,
            rank=Rank.L4,
            tier=Tier.T3,
            atr_distance=0.0,
            proximity_group="1",
        ),
        FilteredZone(
            ticker="TEST",
            ticker_id="TEST_123",
            analysis_date=date.today(),
            price=100.0,
            direction=Direction.NEUTRAL,
            zone_id="hvn_poc2",
            poc_rank=2,
            hvn_poc=100.2,  # Overlaps with poc1
            zone_high=100.7,
            zone_low=99.7,
            score=8.0,  # Lower score
            rank=Rank.L3,
            tier=Tier.T2,
            atr_distance=0.02,
            proximity_group="1",
        ),
        FilteredZone(
            ticker="TEST",
            ticker_id="TEST_123",
            analysis_date=date.today(),
            price=100.0,
            direction=Direction.NEUTRAL,
            zone_id="hvn_poc3",
            poc_rank=3,
            hvn_poc=102.0,  # No overlap
            zone_high=102.5,
            zone_low=101.5,
            score=7.0,
            rank=Rank.L3,
            tier=Tier.T2,
            atr_distance=0.4,
            proximity_group="1",
        ),
    ]

    zone_filter = ZoneFilter()

    # Sort first (as pipeline does)
    sorted_zones = zone_filter._sort_zones(test_zones)

    # Then eliminate overlaps
    result = zone_filter._eliminate_overlaps(sorted_zones)

    print(f"  Input zones: {len(test_zones)}")
    print(f"  After overlap elimination: {len(result)}")

    # Should have 2 zones: poc1 (highest score) and poc3 (no overlap)
    assert len(result) == 2, f"Expected 2 zones, got {len(result)}"

    zone_ids = [z.zone_id for z in result]
    assert "hvn_poc1" in zone_ids, "hvn_poc1 should be kept (highest score)"
    assert "hvn_poc3" in zone_ids, "hvn_poc3 should be kept (no overlap)"
    assert "hvn_poc2" not in zone_ids, "hvn_poc2 should be eliminated (overlap with higher score)"

    print(f"  Kept zones: {zone_ids}")
    print()
    print("  [OK] Overlap elimination works correctly")
    print()
    return True


def test_bull_bear_identification():
    """Test bull/bear POC identification."""
    print("=" * 60)
    print("Testing Bull/Bear POC Identification...")
    print("=" * 60)

    from calculators import ZoneFilter
    from core import FilteredZone, Direction, Rank, Tier

    price = 100.0

    # Create test zones: some above, some below price
    test_zones = [
        FilteredZone(
            ticker="TEST",
            ticker_id="TEST_123",
            analysis_date=date.today(),
            price=price,
            direction=Direction.NEUTRAL,
            zone_id="hvn_poc1",
            poc_rank=1,
            hvn_poc=102.0,  # Above price
            zone_high=102.5,
            zone_low=101.5,
            score=10.0,
            rank=Rank.L4,
            tier=Tier.T3,
            atr_distance=0.4,
            proximity_group="1",
        ),
        FilteredZone(
            ticker="TEST",
            ticker_id="TEST_123",
            analysis_date=date.today(),
            price=price,
            direction=Direction.NEUTRAL,
            zone_id="hvn_poc2",
            poc_rank=2,
            hvn_poc=105.0,  # Above price, farther
            zone_high=105.5,
            zone_low=104.5,
            score=8.0,
            rank=Rank.L3,
            tier=Tier.T2,
            atr_distance=1.0,
            proximity_group="1",
        ),
        FilteredZone(
            ticker="TEST",
            ticker_id="TEST_123",
            analysis_date=date.today(),
            price=price,
            direction=Direction.NEUTRAL,
            zone_id="hvn_poc3",
            poc_rank=3,
            hvn_poc=98.0,  # Below price
            zone_high=98.5,
            zone_low=97.5,
            score=7.0,
            rank=Rank.L3,
            tier=Tier.T2,
            atr_distance=0.4,
            proximity_group="1",
        ),
        FilteredZone(
            ticker="TEST",
            ticker_id="TEST_123",
            analysis_date=date.today(),
            price=price,
            direction=Direction.NEUTRAL,
            zone_id="hvn_poc4",
            poc_rank=4,
            hvn_poc=95.0,  # Below price, farther
            zone_high=95.5,
            zone_low=94.5,
            score=5.0,
            rank=Rank.L2,
            tier=Tier.T1,
            atr_distance=1.0,
            proximity_group="1",
        ),
    ]

    zone_filter = ZoneFilter()
    result = zone_filter._identify_bull_bear_pocs(test_zones, price)

    # Bull POC should be hvn_poc1 (minimum above price = 102.0)
    bull_zones = [z for z in result if z.is_bull_poc]
    assert len(bull_zones) == 1, f"Expected 1 bull POC, got {len(bull_zones)}"
    assert bull_zones[0].hvn_poc == 102.0, f"Bull POC should be 102.0, got {bull_zones[0].hvn_poc}"
    print(f"  Bull POC: ${bull_zones[0].hvn_poc:.2f} ({bull_zones[0].zone_id})")

    # Bear POC should be hvn_poc3 (maximum below price = 98.0)
    bear_zones = [z for z in result if z.is_bear_poc]
    assert len(bear_zones) == 1, f"Expected 1 bear POC, got {len(bear_zones)}"
    assert bear_zones[0].hvn_poc == 98.0, f"Bear POC should be 98.0, got {bear_zones[0].hvn_poc}"
    print(f"  Bear POC: ${bear_zones[0].hvn_poc:.2f} ({bear_zones[0].zone_id})")

    print()
    print("  [OK] Bull/Bear identification works correctly")
    print()
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("EPOCH ANALYSIS TOOL - ZONE FILTER TESTS")
    print("=" * 60 + "\n")

    results = []

    # Run tests in order
    results.append(("Imports", test_imports()))
    results.append(("Tier Mapping", test_tier_mapping()))
    results.append(("Overlap Elimination", test_overlap_elimination()))
    results.append(("Bull/Bear Identification", test_bull_bear_identification()))
    results.append(("Full Filter Pipeline", test_full_filter_pipeline()))

    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status} {name}")
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print("All tests passed!")
    else:
        print("Some tests failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
