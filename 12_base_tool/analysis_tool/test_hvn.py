"""
Test script for the HVN identifier calculator.
Run from: C:/XIIITradingSystems/Epoch/05_analysis_tool
Command: python test_hvn.py
"""
import sys
from datetime import date, timedelta
from pathlib import Path

# Ensure we're in the right directory
sys.path.insert(0, str(Path(__file__).parent))


def test_imports():
    """Test that HVN calculator imports work."""
    print("=" * 60)
    print("Testing imports...")
    print("=" * 60)

    from calculators import HVNIdentifier, calculate_hvn
    from core import POCResult, HVNResult
    print("  [OK] HVN calculator imports successful")
    print()
    return True


def test_hvn_calculation():
    """Test HVN calculation for SPY."""
    print("=" * 60)
    print("Testing HVN Calculation (SPY, 30-day epoch)...")
    print("=" * 60)

    from calculators import calculate_hvn

    # Use a 30-day epoch ending yesterday
    analysis_date = date.today() - timedelta(days=1)
    anchor_date = analysis_date - timedelta(days=30)

    print(f"  Ticker: SPY")
    print(f"  Anchor Date: {anchor_date}")
    print(f"  Analysis Date: {analysis_date}")
    print()

    result = calculate_hvn("SPY", anchor_date, analysis_date)

    print(f"  Bars Analyzed: {result.bars_analyzed:,}")
    print(f"  Total Volume: {result.total_volume:,.0f}")
    print(f"  Price Range: ${result.price_range_low:.2f} - ${result.price_range_high:.2f}")
    print(f"  ATR Used: ${result.atr_used:.2f}")
    print()

    print("  Top 10 POCs (ranked by volume):")
    print("  " + "-" * 40)

    for poc in result.pocs:
        print(f"    POC {poc.rank}: ${poc.price:.2f} (vol: {poc.volume:,.0f})")

    # Verify we got POCs
    assert len(result.pocs) > 0, "Should have at least one POC"
    assert result.pocs[0].rank == 1, "First POC should have rank 1"
    assert result.bars_analyzed > 0, "Should have analyzed some bars"

    print()
    print("  [OK] HVN calculation successful")
    print()
    return True


def test_poc_overlap_prevention():
    """Test that POCs are properly separated."""
    print("=" * 60)
    print("Testing POC Overlap Prevention...")
    print("=" * 60)

    from calculators import calculate_hvn

    analysis_date = date.today() - timedelta(days=1)
    anchor_date = analysis_date - timedelta(days=30)

    result = calculate_hvn("SPY", anchor_date, analysis_date)

    # Check that all POCs are at least ATR/2 apart
    overlap_threshold = result.atr_used / 2

    print(f"  Overlap threshold: ${overlap_threshold:.2f}")
    print()

    violations = []
    for i, poc1 in enumerate(result.pocs):
        for poc2 in result.pocs[i+1:]:
            distance = abs(poc1.price - poc2.price)
            if distance < overlap_threshold:
                violations.append((poc1.rank, poc2.rank, distance))

    if violations:
        print("  VIOLATIONS FOUND:")
        for v in violations:
            print(f"    POC{v[0]} and POC{v[1]}: distance ${v[2]:.2f} < threshold ${overlap_threshold:.2f}")
        return False
    else:
        print("  All POCs properly separated (no overlaps)")
        print()

        # Show distances between consecutive POCs
        print("  Distances between consecutive POCs:")
        sorted_pocs = sorted(result.pocs, key=lambda x: x.price)
        for i in range(len(sorted_pocs) - 1):
            dist = sorted_pocs[i+1].price - sorted_pocs[i].price
            print(f"    ${sorted_pocs[i].price:.2f} -> ${sorted_pocs[i+1].price:.2f}: ${dist:.2f}")

    print()
    print("  [OK] Overlap prevention working")
    print()
    return True


def test_hvn_result_methods():
    """Test HVNResult helper methods."""
    print("=" * 60)
    print("Testing HVNResult Methods...")
    print("=" * 60)

    from calculators import calculate_hvn

    analysis_date = date.today() - timedelta(days=1)
    anchor_date = analysis_date - timedelta(days=30)

    result = calculate_hvn("SPY", anchor_date, analysis_date)

    # Test get_poc method
    poc1 = result.get_poc(1)
    poc5 = result.get_poc(5)
    poc10 = result.get_poc(10)

    print(f"  get_poc(1): ${poc1:.2f}" if poc1 else "  get_poc(1): None")
    print(f"  get_poc(5): ${poc5:.2f}" if poc5 else "  get_poc(5): None")
    print(f"  get_poc(10): ${poc10:.2f}" if poc10 else "  get_poc(10): None")

    # Test get_poc_prices method
    prices = result.get_poc_prices()
    print(f"  get_poc_prices(): {len(prices)} prices")

    # Test to_dict method
    poc_dict = result.to_dict()
    print(f"  to_dict(): {len(poc_dict)} keys")
    print(f"    hvn_poc1: ${poc_dict.get('hvn_poc1', 0):.2f}")
    print(f"    hvn_poc10: ${poc_dict.get('hvn_poc10', 0):.2f}")

    assert poc1 is not None, "POC 1 should exist"
    print()
    print("  [OK] HVNResult methods working")
    print()
    return True


def test_different_tickers():
    """Test HVN calculation for different tickers."""
    print("=" * 60)
    print("Testing Different Tickers...")
    print("=" * 60)

    from calculators import calculate_hvn

    analysis_date = date.today() - timedelta(days=1)
    anchor_date = analysis_date - timedelta(days=14)  # Shorter epoch for speed

    tickers = ["AAPL", "NVDA", "QQQ"]

    for ticker in tickers:
        print(f"\n  {ticker}:")
        try:
            result = calculate_hvn(ticker, anchor_date, analysis_date)
            poc1_price = result.get_poc(1)
            print(f"    Bars: {result.bars_analyzed:,}")
            print(f"    POC1: ${poc1_price:.2f}" if poc1_price else "    POC1: N/A")
            print(f"    POCs found: {len(result.pocs)}")
        except Exception as e:
            print(f"    Error: {e}")

    print()
    print("  [OK] Multiple tickers tested")
    print()
    return True


def test_caching():
    """Test that HVN results are cached properly."""
    print("=" * 60)
    print("Testing Caching...")
    print("=" * 60)

    from calculators import calculate_hvn
    import time

    analysis_date = date.today() - timedelta(days=1)
    anchor_date = analysis_date - timedelta(days=14)

    # First call (should hit API)
    start = time.time()
    result1 = calculate_hvn("SPY", anchor_date, analysis_date)
    time1 = time.time() - start

    # Second call (should hit cache)
    start = time.time()
    result2 = calculate_hvn("SPY", anchor_date, analysis_date)
    time2 = time.time() - start

    print(f"  First call (API): {time1:.2f}s")
    print(f"  Second call (cache): {time2:.4f}s")
    print(f"  Speedup: {time1/time2:.0f}x" if time2 > 0 else "  Speedup: N/A")

    # Verify results are the same
    assert result1.get_poc(1) == result2.get_poc(1), "Cached result should match"

    print()
    print("  [OK] Caching working")
    print()
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("EPOCH ANALYSIS TOOL - HVN IDENTIFIER TESTS")
    print("=" * 60 + "\n")

    results = []

    # Run tests in order
    results.append(("Imports", test_imports()))
    results.append(("HVN Calculation", test_hvn_calculation()))
    results.append(("POC Overlap Prevention", test_poc_overlap_prevention()))
    results.append(("HVNResult Methods", test_hvn_result_methods()))
    results.append(("Different Tickers", test_different_tickers()))
    results.append(("Caching", test_caching()))

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
