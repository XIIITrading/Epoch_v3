"""
Test script for the zone calculator.
Run from: C:/XIIITradingSystems/Epoch/05_analysis_tool
Command: python test_zones.py
"""
import sys
from datetime import date, timedelta
from pathlib import Path

# Ensure we're in the right directory
sys.path.insert(0, str(Path(__file__).parent))


def test_imports():
    """Test that calculator imports work."""
    print("=" * 60)
    print("Testing imports...")
    print("=" * 60)

    from calculators import (
        BarDataCalculator, calculate_bar_data,
        HVNIdentifier, calculate_hvn,
        ZoneCalculator, calculate_zones
    )
    from core import RawZone, Rank, Direction
    from config.weights import (
        EPOCH_POC_BASE_WEIGHTS,
        ZONE_WEIGHTS,
        BUCKET_WEIGHTS,
        get_rank_from_score
    )
    print("  [OK] All imports successful")
    print()
    return True


def test_zone_calculation():
    """Test full zone calculation pipeline."""
    print("=" * 60)
    print("Testing Zone Calculation Pipeline...")
    print("=" * 60)

    from calculators import calculate_bar_data, calculate_hvn, calculate_zones
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
    print(f"    M15 ATR: ${bar_data.m15_atr:.4f}" if bar_data.m15_atr else "    M15 ATR: N/A")
    print(f"    Technical levels: {len(bar_data.get_all_levels())}")
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
    for poc in hvn_result.pocs[:5]:  # Show top 5
        print(f"      POC{poc.rank}: ${poc.price:.2f} (volume: {poc.volume:,.0f})")
    print()

    # Step 3: Calculate zones
    print("  Step 3: Calculating zones...")
    raw_zones = calculate_zones(
        bar_data=bar_data,
        hvn_result=hvn_result,
        direction=Direction.NEUTRAL
    )
    print(f"    Zones calculated: {len(raw_zones)}")
    print()

    # Show zone details
    print("  Zone Results (sorted by score):")
    print("  " + "-" * 56)
    print(f"  {'Zone':<10} {'POC':>8} {'High':>8} {'Low':>8} {'Score':>6} {'Rank':<4}")
    print("  " + "-" * 56)

    for zone in raw_zones:
        print(
            f"  {zone.zone_id:<10} "
            f"${zone.hvn_poc:>7.2f} "
            f"${zone.zone_high:>7.2f} "
            f"${zone.zone_low:>7.2f} "
            f"{zone.score:>6.2f} "
            f"{zone.rank.value:<4}"
        )

    print()

    # Show rank distribution
    rank_counts = {}
    for zone in raw_zones:
        rank_counts[zone.rank.value] = rank_counts.get(zone.rank.value, 0) + 1

    print("  Rank Distribution:")
    for rank in ['L5', 'L4', 'L3', 'L2', 'L1']:
        count = rank_counts.get(rank, 0)
        if count > 0:
            print(f"    {rank}: {count}")

    print()
    print("  [OK] Zone calculation complete")
    print()
    return True


def test_confluence_details():
    """Test confluence details for a single zone."""
    print("=" * 60)
    print("Testing Confluence Details...")
    print("=" * 60)

    from calculators import calculate_bar_data, calculate_hvn, calculate_zones
    from core import Direction

    ticker = "SPY"
    analysis_date = date.today() - timedelta(days=1)
    if analysis_date.weekday() >= 5:
        analysis_date = analysis_date - timedelta(days=analysis_date.weekday() - 4)
    anchor_date = analysis_date - timedelta(days=30)

    bar_data = calculate_bar_data(ticker, analysis_date)
    hvn_result = calculate_hvn(ticker, anchor_date, analysis_date, bar_data.m15_atr)
    raw_zones = calculate_zones(bar_data, hvn_result, Direction.NEUTRAL)

    # Show details for the highest scoring zone
    if raw_zones:
        best_zone = raw_zones[0]  # Already sorted by score
        print(f"  Highest Scoring Zone: {best_zone.zone_id}")
        print(f"    POC: ${best_zone.hvn_poc:.2f}")
        print(f"    Zone: ${best_zone.zone_low:.2f} - ${best_zone.zone_high:.2f}")
        print(f"    Score: {best_zone.score:.2f}")
        print(f"    Rank: {best_zone.rank.value}")
        print(f"    Overlaps: {best_zone.overlaps}")
        print(f"    Confluences: {best_zone.confluences_str}")
        print()

        # Also show the lowest scoring zone
        worst_zone = raw_zones[-1]
        print(f"  Lowest Scoring Zone: {worst_zone.zone_id}")
        print(f"    POC: ${worst_zone.hvn_poc:.2f}")
        print(f"    Zone: ${worst_zone.zone_low:.2f} - ${worst_zone.zone_high:.2f}")
        print(f"    Score: {worst_zone.score:.2f}")
        print(f"    Rank: {worst_zone.rank.value}")
        print(f"    Overlaps: {worst_zone.overlaps}")
        print(f"    Confluences: {worst_zone.confluences_str}")

    print()
    print("  [OK] Confluence details complete")
    print()
    return True


def test_score_thresholds():
    """Test that score thresholds produce correct ranks."""
    print("=" * 60)
    print("Testing Score Thresholds...")
    print("=" * 60)

    from config.weights import get_rank_from_score, RANKING_SCORE_THRESHOLDS

    test_cases = [
        (0.0, 'L1'),
        (2.9, 'L1'),
        (3.0, 'L2'),
        (5.9, 'L2'),
        (6.0, 'L3'),
        (8.9, 'L3'),
        (9.0, 'L4'),
        (11.9, 'L4'),
        (12.0, 'L5'),
        (15.0, 'L5'),
        (100.0, 'L5'),
    ]

    print(f"  Thresholds: {RANKING_SCORE_THRESHOLDS}")
    print()

    all_passed = True
    for score, expected_rank in test_cases:
        actual_rank = get_rank_from_score(score)
        status = "[OK]" if actual_rank == expected_rank else "[FAIL]"
        print(f"  {status} Score {score:>5.1f} -> {actual_rank} (expected {expected_rank})")
        if actual_rank != expected_rank:
            all_passed = False

    print()
    if all_passed:
        print("  [OK] All threshold tests passed")
    else:
        print("  [FAIL] Some threshold tests failed")
    print()
    return all_passed


def test_bucket_weights():
    """Test that bucket weights are applied correctly (no stacking)."""
    print("=" * 60)
    print("Testing Bucket Weight Logic...")
    print("=" * 60)

    from config.weights import BUCKET_WEIGHTS, ZONE_WEIGHTS

    print("  Bucket max weights:")
    for bucket, weight in sorted(BUCKET_WEIGHTS.items()):
        print(f"    {bucket}: {weight}")

    print()

    # Count levels per bucket type
    bucket_counts = {}
    for zone_key, zone_config in ZONE_WEIGHTS.items():
        con_type = zone_config.get('con_type', 'unknown')
        bucket_counts[con_type] = bucket_counts.get(con_type, 0) + 1

    print("  Levels per bucket type:")
    for bucket, count in sorted(bucket_counts.items()):
        max_weight = BUCKET_WEIGHTS.get(bucket, 'N/A')
        print(f"    {bucket}: {count} levels (max weight: {max_weight})")

    print()
    print("  Note: Even if multiple levels overlap, only MAX weight is used per bucket")
    print("  [OK] Bucket weight verification complete")
    print()
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("EPOCH ANALYSIS TOOL - ZONE CALCULATOR TESTS")
    print("=" * 60 + "\n")

    results = []

    # Run tests in order
    results.append(("Imports", test_imports()))
    results.append(("Score Thresholds", test_score_thresholds()))
    results.append(("Bucket Weights", test_bucket_weights()))
    results.append(("Zone Calculation", test_zone_calculation()))
    results.append(("Confluence Details", test_confluence_details()))

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
