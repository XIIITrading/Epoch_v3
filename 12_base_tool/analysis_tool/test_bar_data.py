"""
Test script for the bar data calculator.
Run from: C:/XIIITradingSystems/Epoch/05_analysis_tool
Command: python test_bar_data.py
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

    from calculators import BarDataCalculator, calculate_bar_data
    from core import BarData, OHLCData, CamarillaLevels
    print("  [OK] Calculator imports successful")
    print()
    return True


def test_monthly_metrics():
    """Test monthly OHLC calculation."""
    print("=" * 60)
    print("Testing Monthly Metrics (M1)...")
    print("=" * 60)

    from calculators import BarDataCalculator

    calc = BarDataCalculator()
    analysis_date = date.today() - timedelta(days=1)

    m1_current, m1_prior = calc.calculate_monthly_metrics("SPY", analysis_date)

    print(f"  Analysis date: {analysis_date}")
    print(f"  Current Month:")
    print(f"    Open:  ${m1_current.open:.2f}" if m1_current.open else "    Open:  N/A")
    print(f"    High:  ${m1_current.high:.2f}" if m1_current.high else "    High:  N/A")
    print(f"    Low:   ${m1_current.low:.2f}" if m1_current.low else "    Low:   N/A")
    print(f"    Close: ${m1_current.close:.2f}" if m1_current.close else "    Close: N/A")
    print(f"  Prior Month:")
    print(f"    Open:  ${m1_prior.open:.2f}" if m1_prior.open else "    Open:  N/A")
    print(f"    High:  ${m1_prior.high:.2f}" if m1_prior.high else "    High:  N/A")
    print(f"    Low:   ${m1_prior.low:.2f}" if m1_prior.low else "    Low:   N/A")
    print(f"    Close: ${m1_prior.close:.2f}" if m1_prior.close else "    Close: N/A")

    assert m1_current.is_complete(), "Current month OHLC incomplete"
    print("  [OK] Monthly metrics calculated")
    print()
    return True


def test_weekly_metrics():
    """Test weekly OHLC calculation."""
    print("=" * 60)
    print("Testing Weekly Metrics (W1)...")
    print("=" * 60)

    from calculators import BarDataCalculator

    calc = BarDataCalculator()
    analysis_date = date.today() - timedelta(days=1)

    w1_current, w1_prior = calc.calculate_weekly_metrics("SPY", analysis_date)

    print(f"  Analysis date: {analysis_date}")
    print(f"  Current Week:")
    print(f"    Open:  ${w1_current.open:.2f}" if w1_current.open else "    Open:  N/A")
    print(f"    High:  ${w1_current.high:.2f}" if w1_current.high else "    High:  N/A")
    print(f"    Low:   ${w1_current.low:.2f}" if w1_current.low else "    Low:   N/A")
    print(f"    Close: ${w1_current.close:.2f}" if w1_current.close else "    Close: N/A")
    print(f"  Prior Week:")
    print(f"    Open:  ${w1_prior.open:.2f}" if w1_prior.open else "    Open:  N/A")
    print(f"    Close: ${w1_prior.close:.2f}" if w1_prior.close else "    Close: N/A")

    assert w1_prior.is_complete(), "Prior week OHLC incomplete"
    print("  [OK] Weekly metrics calculated")
    print()
    return True


def test_daily_metrics():
    """Test daily OHLC calculation."""
    print("=" * 60)
    print("Testing Daily Metrics (D1)...")
    print("=" * 60)

    from calculators import BarDataCalculator

    calc = BarDataCalculator()
    # Use a recent trading day
    analysis_date = date.today() - timedelta(days=1)
    if analysis_date.weekday() >= 5:
        analysis_date = analysis_date - timedelta(days=analysis_date.weekday() - 4)

    d1_current, d1_prior = calc.calculate_daily_metrics("SPY", analysis_date)

    print(f"  Analysis date: {analysis_date}")
    print(f"  Current Day:")
    if d1_current.is_complete():
        print(f"    Open:  ${d1_current.open:.2f}")
        print(f"    High:  ${d1_current.high:.2f}")
        print(f"    Low:   ${d1_current.low:.2f}")
        print(f"    Close: ${d1_current.close:.2f}")
    else:
        print("    No data (market may be closed)")

    print(f"  Prior Day:")
    print(f"    Open:  ${d1_prior.open:.2f}" if d1_prior.open else "    Open:  N/A")
    print(f"    Close: ${d1_prior.close:.2f}" if d1_prior.close else "    Close: N/A")

    print("  [OK] Daily metrics calculated")
    print()
    return True


def test_overnight_metrics():
    """Test overnight high/low calculation."""
    print("=" * 60)
    print("Testing Overnight Metrics...")
    print("=" * 60)

    from calculators import BarDataCalculator

    calc = BarDataCalculator()
    # Use a recent trading day
    analysis_date = date.today() - timedelta(days=1)
    if analysis_date.weekday() >= 5:
        analysis_date = analysis_date - timedelta(days=analysis_date.weekday() - 4)

    on_high, on_low = calc.calculate_overnight_metrics("SPY", analysis_date)

    print(f"  Analysis date: {analysis_date}")
    print(f"  Overnight High: ${on_high:.2f}" if on_high else "  Overnight High: N/A")
    print(f"  Overnight Low:  ${on_low:.2f}" if on_low else "  Overnight Low: N/A")

    print("  [OK] Overnight metrics calculated")
    print()
    return True


def test_atr_calculations():
    """Test ATR calculations."""
    print("=" * 60)
    print("Testing ATR Calculations...")
    print("=" * 60)

    from calculators import BarDataCalculator

    calc = BarDataCalculator()
    # Use a recent trading day
    analysis_date = date.today() - timedelta(days=1)
    if analysis_date.weekday() >= 5:
        analysis_date = analysis_date - timedelta(days=analysis_date.weekday() - 4)

    m5_atr = calc.calculate_m5_atr("SPY", analysis_date)
    m15_atr = calc.calculate_m15_atr("SPY", analysis_date)
    h1_atr = calc.calculate_h1_atr("SPY", analysis_date)
    d1_atr = calc.calculate_d1_atr("SPY", analysis_date)

    print(f"  Analysis date: {analysis_date}")
    print(f"  M5 ATR:  ${m5_atr:.4f}" if m5_atr else "  M5 ATR:  N/A")
    print(f"  M15 ATR: ${m15_atr:.4f}" if m15_atr else "  M15 ATR: N/A")
    print(f"  H1 ATR:  ${h1_atr:.4f}" if h1_atr else "  H1 ATR:  N/A")
    print(f"  D1 ATR:  ${d1_atr:.4f}" if d1_atr else "  D1 ATR:  N/A")

    assert m15_atr is not None, "M15 ATR should be calculated"
    assert d1_atr is not None, "D1 ATR should be calculated"
    print("  [OK] ATR calculations complete")
    print()
    return True


def test_camarilla_levels():
    """Test Camarilla pivot calculation."""
    print("=" * 60)
    print("Testing Camarilla Levels...")
    print("=" * 60)

    from calculators import BarDataCalculator

    calc = BarDataCalculator()
    analysis_date = date.today() - timedelta(days=1)

    cam_daily, cam_weekly, cam_monthly = calc.calculate_camarilla_levels("SPY", analysis_date)

    print(f"  Analysis date: {analysis_date}")
    print(f"  Daily Camarilla:")
    print(f"    S6: ${cam_daily.s6:.2f}" if cam_daily.s6 else "    S6: N/A")
    print(f"    S3: ${cam_daily.s3:.2f}" if cam_daily.s3 else "    S3: N/A")
    print(f"    R3: ${cam_daily.r3:.2f}" if cam_daily.r3 else "    R3: N/A")
    print(f"    R6: ${cam_daily.r6:.2f}" if cam_daily.r6 else "    R6: N/A")

    print(f"  Weekly Camarilla:")
    print(f"    S3: ${cam_weekly.s3:.2f}" if cam_weekly.s3 else "    S3: N/A")
    print(f"    R3: ${cam_weekly.r3:.2f}" if cam_weekly.r3 else "    R3: N/A")

    print(f"  Monthly Camarilla:")
    print(f"    S3: ${cam_monthly.s3:.2f}" if cam_monthly.s3 else "    S3: N/A")
    print(f"    R3: ${cam_monthly.r3:.2f}" if cam_monthly.r3 else "    R3: N/A")

    assert cam_daily.s3 is not None, "Daily Camarilla S3 should be calculated"
    print("  [OK] Camarilla levels calculated")
    print()
    return True


def test_unified_calculate():
    """Test the unified calculate_bar_data function."""
    print("=" * 60)
    print("Testing Unified calculate_bar_data()...")
    print("=" * 60)

    from calculators import calculate_bar_data

    analysis_date = date.today() - timedelta(days=1)
    if analysis_date.weekday() >= 5:
        analysis_date = analysis_date - timedelta(days=analysis_date.weekday() - 4)

    bar_data = calculate_bar_data("SPY", analysis_date)

    print(f"  Ticker: {bar_data.ticker}")
    print(f"  Ticker ID: {bar_data.ticker_id}")
    print(f"  Analysis Date: {bar_data.analysis_date}")
    print(f"  Price: ${bar_data.price:.2f}")

    print(f"\n  Monthly:")
    print(f"    Current: O=${bar_data.m1_current.open:.2f}" if bar_data.m1_current.open else "    Current: N/A")

    print(f"\n  Weekly:")
    print(f"    Prior: O=${bar_data.w1_prior.open:.2f}" if bar_data.w1_prior.open else "    Prior: N/A")

    print(f"\n  ATR Values:")
    print(f"    M15: ${bar_data.m15_atr:.4f}" if bar_data.m15_atr else "    M15: N/A")
    print(f"    D1:  ${bar_data.d1_atr:.4f}" if bar_data.d1_atr else "    D1:  N/A")

    print(f"\n  Overnight:")
    print(f"    High: ${bar_data.overnight_high:.2f}" if bar_data.overnight_high else "    High: N/A")
    print(f"    Low:  ${bar_data.overnight_low:.2f}" if bar_data.overnight_low else "    Low: N/A")

    print(f"\n  Camarilla Daily:")
    print(f"    S3: ${bar_data.camarilla_daily.s3:.2f}" if bar_data.camarilla_daily.s3 else "    S3: N/A")
    print(f"    R3: ${bar_data.camarilla_daily.r3:.2f}" if bar_data.camarilla_daily.r3 else "    R3: N/A")

    # Test get_all_levels method
    all_levels = bar_data.get_all_levels()
    print(f"\n  Total technical levels: {len(all_levels)}")

    print("  [OK] Unified calculation complete")
    print()
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("EPOCH ANALYSIS TOOL - BAR DATA CALCULATOR TESTS")
    print("=" * 60 + "\n")

    results = []

    # Run tests in order
    results.append(("Imports", test_imports()))
    results.append(("Monthly Metrics", test_monthly_metrics()))
    results.append(("Weekly Metrics", test_weekly_metrics()))
    results.append(("Daily Metrics", test_daily_metrics()))
    results.append(("Overnight Metrics", test_overnight_metrics()))
    results.append(("ATR Calculations", test_atr_calculations()))
    results.append(("Camarilla Levels", test_camarilla_levels()))
    results.append(("Unified calculate_bar_data()", test_unified_calculate()))

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
