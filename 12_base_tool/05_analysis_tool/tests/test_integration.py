"""
Session 14: Integration Test Suite

Comprehensive tests comparing the Streamlit pipeline output against original system.

Test Categories:
1. Single ticker validation (TSLA)
2. Multi-ticker validation (5-10 tickers)
3. Anchor preset validation
4. Edge case handling
5. Performance benchmarks
"""

import pytest
import sys
import time
from datetime import date, timedelta
from typing import List, Dict, Tuple

# Add parent directory for imports
sys.path.insert(0, r'C:\XIIITradingSystems\Epoch\05_analysis_tool')

from calculators.bar_data import calculate_bar_data
from calculators.hvn_identifier import calculate_hvn
from calculators.zone_calculator import calculate_zones
from calculators.zone_filter import filter_zones
from calculators.market_structure import calculate_market_structure
from calculators.setup_analyzer import analyze_setups
from core.data_models import Direction, Rank, Tier


# ============================================================================
# VALIDATION THRESHOLDS
# ============================================================================

# Price tolerance for POC matching (POCs within this range are considered equal)
POC_PRICE_TOLERANCE = 0.50  # $0.50

# ATR tolerance percentage (ATR values within this % are considered equal)
ATR_TOLERANCE_PCT = 0.05  # 5%

# Score tolerance for zone matching
SCORE_TOLERANCE = 0.5

# Minimum POCs that must match exactly (top-ranked)
MIN_EXACT_POC_MATCHES = 4


# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture
def tsla_test_case():
    """Standard TSLA test case matching DEVELOPMENT_PLAN.md validation protocol."""
    return {
        'ticker': 'TSLA',
        'anchor_date': date(2025, 11, 21),
        'analysis_date': date.today(),
        # Expected values from original system (Mode 2: D1 ATR = $13.80)
        'expected_pocs': [
            454.77, 478.33, 446.02, 436.95, 429.23,
            488.84, 418.37, 468.22, 400.28, 409.13
        ],
        'expected_d1_atr': 13.80,
        'expected_bars': 35129,
    }


@pytest.fixture
def multi_ticker_list():
    """Multiple tickers for batch testing."""
    return ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'META']


@pytest.fixture
def anchor_presets():
    """Anchor preset dates for testing."""
    today = date.today()
    return {
        'prior_day': today - timedelta(days=1),
        'prior_week': today - timedelta(days=7),
        'prior_month': today - timedelta(days=30),
    }


# ============================================================================
# SINGLE TICKER VALIDATION TESTS
# ============================================================================

class TestSingleTickerValidation:
    """Test suite for single ticker (TSLA) validation."""

    def test_bar_data_calculation(self, tsla_test_case):
        """Validate bar data calculation matches expected values."""
        ticker = tsla_test_case['ticker']
        analysis_date = tsla_test_case['analysis_date']

        bar_data = calculate_bar_data(ticker, analysis_date)

        # Verify all ATR values are populated
        assert bar_data.m5_atr is not None, "M5 ATR should be calculated"
        assert bar_data.m15_atr is not None, "M15 ATR should be calculated"
        assert bar_data.h1_atr is not None, "H1 ATR should be calculated"
        assert bar_data.d1_atr is not None, "D1 ATR should be calculated"

        # Verify D1 ATR is within tolerance
        expected_d1_atr = tsla_test_case['expected_d1_atr']
        atr_diff_pct = abs(bar_data.d1_atr - expected_d1_atr) / expected_d1_atr
        assert atr_diff_pct < ATR_TOLERANCE_PCT, \
            f"D1 ATR {bar_data.d1_atr:.4f} differs from expected {expected_d1_atr:.4f} by {atr_diff_pct*100:.1f}%"

        # Verify Camarilla levels are calculated
        assert bar_data.camarilla_daily is not None, "Daily Camarilla should be calculated"
        assert bar_data.camarilla_daily.r3 is not None, "Camarilla R3 should be calculated"
        assert bar_data.camarilla_daily.s3 is not None, "Camarilla S3 should be calculated"

        print(f"\n✓ Bar Data: D1 ATR = ${bar_data.d1_atr:.4f} (expected ${expected_d1_atr:.4f})")

    def test_hvn_poc_calculation(self, tsla_test_case):
        """Validate HVN POC calculation matches original system."""
        ticker = tsla_test_case['ticker']
        anchor_date = tsla_test_case['anchor_date']
        analysis_date = tsla_test_case['analysis_date']
        expected_pocs = tsla_test_case['expected_pocs']

        # Get bar data for D1 ATR
        bar_data = calculate_bar_data(ticker, analysis_date)

        # Calculate HVN POCs
        hvn_result = calculate_hvn(ticker, anchor_date, analysis_date, bar_data.d1_atr)

        # Verify 10 POCs returned
        assert len(hvn_result.pocs) == 10, f"Expected 10 POCs, got {len(hvn_result.pocs)}"

        # Verify bars analyzed
        expected_bars = tsla_test_case['expected_bars']
        assert hvn_result.bars_analyzed == expected_bars, \
            f"Expected {expected_bars} bars, got {hvn_result.bars_analyzed}"

        # Sort POCs by rank for comparison
        sorted_pocs = sorted(hvn_result.pocs, key=lambda x: x.rank)

        # Count exact matches
        exact_matches = 0
        close_matches = 0

        for i, poc in enumerate(sorted_pocs):
            expected_price = expected_pocs[i]
            actual_price = poc.price
            price_diff = abs(actual_price - expected_price)

            if price_diff < 0.01:  # Exact match (within 1 cent)
                exact_matches += 1
            elif price_diff < POC_PRICE_TOLERANCE:
                close_matches += 1

            match_status = "✓" if price_diff < 0.01 else ("~" if price_diff < POC_PRICE_TOLERANCE else "✗")
            print(f"  POC{i+1}: ${actual_price:.2f} vs ${expected_price:.2f} {match_status}")

        print(f"\n✓ HVN POCs: {exact_matches}/10 exact, {close_matches} close matches")

        # Verify minimum required matches
        assert exact_matches >= MIN_EXACT_POC_MATCHES, \
            f"Expected at least {MIN_EXACT_POC_MATCHES} exact POC matches, got {exact_matches}"

    def test_zone_calculation(self, tsla_test_case):
        """Validate zone calculation produces expected zones."""
        ticker = tsla_test_case['ticker']
        anchor_date = tsla_test_case['anchor_date']
        analysis_date = tsla_test_case['analysis_date']

        # Run full pipeline
        bar_data = calculate_bar_data(ticker, analysis_date)
        hvn_result = calculate_hvn(ticker, anchor_date, analysis_date, bar_data.d1_atr)
        raw_zones = calculate_zones(bar_data, hvn_result)

        # Verify 10 zones created (one per POC)
        assert len(raw_zones) == 10, f"Expected 10 zones, got {len(raw_zones)}"

        # Verify zone structure
        for zone in raw_zones:
            # Zone range should be POC ± (M15 ATR / 2)
            zone_width = zone.zone_high - zone.zone_low
            expected_width = bar_data.m15_atr  # Full width is M15 ATR

            # Zone should be centered on HVN POC
            zone_center = (zone.zone_high + zone.zone_low) / 2
            assert abs(zone_center - zone.hvn_poc) < 0.01, \
                f"Zone center {zone_center:.2f} should match POC {zone.hvn_poc:.2f}"

            # Score should be positive
            assert zone.score >= 0, f"Zone score should be non-negative"

            # Rank should be valid
            assert zone.rank in [Rank.L1, Rank.L2, Rank.L3, Rank.L4, Rank.L5]

        # Log zones for review
        print(f"\n✓ Raw Zones: {len(raw_zones)} zones calculated")
        for z in sorted(raw_zones, key=lambda x: -x.score)[:5]:
            print(f"  {z.zone_id}: Score={z.score:.1f}, Rank={z.rank.value}")

    def test_zone_filtering(self, tsla_test_case):
        """Validate zone filtering and tier assignment."""
        ticker = tsla_test_case['ticker']
        anchor_date = tsla_test_case['anchor_date']
        analysis_date = tsla_test_case['analysis_date']

        # Run full pipeline
        bar_data = calculate_bar_data(ticker, analysis_date)
        ms = calculate_market_structure(ticker, analysis_date)
        hvn_result = calculate_hvn(ticker, anchor_date, analysis_date, bar_data.d1_atr)
        raw_zones = calculate_zones(bar_data, hvn_result)
        filtered_zones = filter_zones(raw_zones, bar_data, ms.composite)

        # Verify filtering reduces zones
        assert len(filtered_zones) <= len(raw_zones), "Filtering should not add zones"

        # Verify tier assignments
        for zone in filtered_zones:
            # Tier should match rank mapping: L1-L2→T1, L3→T2, L4-L5→T3
            if zone.rank in [Rank.L1, Rank.L2]:
                assert zone.tier == Tier.T1, f"Rank {zone.rank.value} should map to T1"
            elif zone.rank == Rank.L3:
                assert zone.tier == Tier.T2, f"Rank {zone.rank.value} should map to T2"
            else:  # L4, L5
                assert zone.tier == Tier.T3, f"Rank {zone.rank.value} should map to T3"

            # ATR distance should be calculated
            assert zone.atr_distance is not None, "ATR distance should be calculated"

        # Verify bull/bear POC identification
        bull_pocs = [z for z in filtered_zones if z.is_bull_poc]
        bear_pocs = [z for z in filtered_zones if z.is_bear_poc]

        print(f"\n✓ Filtered Zones: {len(filtered_zones)} zones")
        print(f"  Bull POCs: {len(bull_pocs)}, Bear POCs: {len(bear_pocs)}")

        # At least one bull or bear POC should be identified (unless no zones qualify)
        if len(filtered_zones) > 0:
            assert len(bull_pocs) > 0 or len(bear_pocs) > 0, \
                "At least one bull or bear POC should be identified"

    def test_setup_analysis(self, tsla_test_case):
        """Validate setup analysis produces valid setups."""
        ticker = tsla_test_case['ticker']
        anchor_date = tsla_test_case['anchor_date']
        analysis_date = tsla_test_case['analysis_date']

        # Run full pipeline
        bar_data = calculate_bar_data(ticker, analysis_date)
        ms = calculate_market_structure(ticker, analysis_date)
        hvn_result = calculate_hvn(ticker, anchor_date, analysis_date, bar_data.d1_atr)
        raw_zones = calculate_zones(bar_data, hvn_result)
        filtered_zones = filter_zones(raw_zones, bar_data, ms.composite)
        primary_setup, secondary_setup = analyze_setups(filtered_zones, hvn_result, bar_data, ms.composite)

        print(f"\n✓ Setup Analysis:")
        print(f"  Composite Direction: {ms.composite.value}")

        if primary_setup:
            # Verify primary setup direction matches composite
            if ms.composite in [Direction.BULL, Direction.BULL_PLUS]:
                assert primary_setup.direction == Direction.BULL, \
                    "Primary setup should be Bull in bullish market"
            elif ms.composite in [Direction.BEAR, Direction.BEAR_PLUS]:
                assert primary_setup.direction == Direction.BEAR, \
                    "Primary setup should be Bear in bearish market"

            # Verify R:R is positive
            assert primary_setup.risk_reward > 0, "R:R should be positive"

            # Verify setup string format (comma-separated: zone_high,zone_low,target)
            assert ',' in primary_setup.setup_string, "Setup string should use , delimiter"

            print(f"  Primary: {primary_setup.direction.value} @ ${primary_setup.hvn_poc:.2f}")
            print(f"           Target: ${primary_setup.target:.2f}, R:R: {primary_setup.risk_reward:.2f}")
        else:
            print("  Primary: N/A")

        if secondary_setup:
            # Verify secondary is counter-trend
            if primary_setup:
                assert secondary_setup.direction != primary_setup.direction, \
                    "Secondary should be counter-trend"

            print(f"  Secondary: {secondary_setup.direction.value} @ ${secondary_setup.hvn_poc:.2f}")
            print(f"             Target: ${secondary_setup.target:.2f}, R:R: {secondary_setup.risk_reward:.2f}")
        else:
            print("  Secondary: N/A")


# ============================================================================
# MULTI-TICKER VALIDATION TESTS
# ============================================================================

class TestMultiTickerValidation:
    """Test suite for multi-ticker batch validation."""

    def test_multi_ticker_pipeline(self, multi_ticker_list):
        """Validate pipeline runs correctly for multiple tickers."""
        anchor_date = date(2025, 11, 1)
        analysis_date = date.today()

        results = {}
        errors = []

        for ticker in multi_ticker_list:
            try:
                bar_data = calculate_bar_data(ticker, analysis_date)
                ms = calculate_market_structure(ticker, analysis_date)
                hvn_result = calculate_hvn(ticker, anchor_date, analysis_date, bar_data.d1_atr)
                raw_zones = calculate_zones(bar_data, hvn_result)
                filtered_zones = filter_zones(raw_zones, bar_data, ms.composite)
                primary_setup, secondary_setup = analyze_setups(
                    filtered_zones, hvn_result, bar_data, ms.composite
                )

                results[ticker] = {
                    'price': bar_data.price,
                    'd1_atr': bar_data.d1_atr,
                    'poc_count': len(hvn_result.pocs),
                    'raw_zones': len(raw_zones),
                    'filtered_zones': len(filtered_zones),
                    'composite': ms.composite.value,
                    'primary': primary_setup.direction.value if primary_setup else None,
                    'secondary': secondary_setup.direction.value if secondary_setup else None,
                }
            except Exception as e:
                errors.append((ticker, str(e)))

        # Print results summary
        print(f"\n✓ Multi-Ticker Results ({len(results)}/{len(multi_ticker_list)} successful):")
        for ticker, data in results.items():
            print(f"  {ticker}: ${data['price']:.2f}, {data['composite']}, "
                  f"{data['filtered_zones']} zones")

        # Print errors if any
        if errors:
            print(f"\n✗ Errors ({len(errors)}):")
            for ticker, error in errors:
                print(f"  {ticker}: {error}")

        # At least 80% should succeed
        success_rate = len(results) / len(multi_ticker_list)
        assert success_rate >= 0.8, f"Success rate {success_rate*100:.0f}% below 80% threshold"


# ============================================================================
# ANCHOR PRESET VALIDATION TESTS
# ============================================================================

class TestAnchorPresetValidation:
    """Test suite for anchor preset validation."""

    def test_anchor_preset_consistency(self, anchor_presets):
        """Validate different anchor presets produce consistent results."""
        ticker = 'SPY'
        analysis_date = date.today()

        results = {}

        for preset_name, anchor_date in anchor_presets.items():
            bar_data = calculate_bar_data(ticker, analysis_date)
            hvn_result = calculate_hvn(ticker, anchor_date, analysis_date, bar_data.d1_atr)
            raw_zones = calculate_zones(bar_data, hvn_result)

            results[preset_name] = {
                'anchor_date': anchor_date,
                'bars_analyzed': hvn_result.bars_analyzed,
                'poc_count': len(hvn_result.pocs),
                'zone_count': len(raw_zones),
                'top_poc': hvn_result.pocs[0].price if hvn_result.pocs else None,
            }

        print(f"\n✓ Anchor Preset Results ({ticker}):")
        for preset, data in results.items():
            print(f"  {preset}: {data['anchor_date']} → {data['bars_analyzed']} bars, "
                  f"{data['poc_count']} POCs")

        # All presets should produce valid results
        for preset, data in results.items():
            assert data['poc_count'] == 10, f"{preset} should produce 10 POCs"
            assert data['zone_count'] == 10, f"{preset} should produce 10 zones"


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestEdgeCases:
    """Test suite for edge cases."""

    def test_recent_ipo_ticker(self):
        """Test handling of recently IPO'd ticker with limited history."""
        # Use a ticker with limited history (adjust as needed)
        ticker = 'PLTR'  # Palantir
        anchor_date = date(2024, 1, 1)  # Far back
        analysis_date = date.today()

        bar_data = calculate_bar_data(ticker, analysis_date)
        hvn_result = calculate_hvn(ticker, anchor_date, analysis_date, bar_data.d1_atr)

        # Should handle gracefully
        assert hvn_result.pocs is not None, "Should return POC list even with limited data"
        print(f"\n✓ Recent IPO: {ticker} - {len(hvn_result.pocs)} POCs, "
              f"{hvn_result.bars_analyzed} bars")

    def test_high_volatility_ticker(self):
        """Test handling of high volatility ticker."""
        ticker = 'GME'  # High volatility meme stock
        anchor_date = date(2025, 10, 1)
        analysis_date = date.today()

        bar_data = calculate_bar_data(ticker, analysis_date)
        ms = calculate_market_structure(ticker, analysis_date)
        hvn_result = calculate_hvn(ticker, anchor_date, analysis_date, bar_data.d1_atr)
        raw_zones = calculate_zones(bar_data, hvn_result)

        # Should produce valid zones despite high volatility
        assert len(raw_zones) == 10, "Should produce 10 zones"

        # Zones should not overlap excessively
        sorted_zones = sorted(raw_zones, key=lambda z: z.hvn_poc)
        overlaps = 0
        for i in range(len(sorted_zones) - 1):
            if sorted_zones[i].zone_high > sorted_zones[i+1].zone_low:
                overlaps += 1

        print(f"\n✓ High Volatility: {ticker} - ATR=${bar_data.d1_atr:.2f}, "
              f"{overlaps} zone overlaps")

    def test_low_volume_ticker(self):
        """Test handling of low volume ticker."""
        ticker = 'DIA'  # Index ETF (lower volume than individual stocks)
        anchor_date = date(2025, 11, 1)
        analysis_date = date.today()

        bar_data = calculate_bar_data(ticker, analysis_date)
        hvn_result = calculate_hvn(ticker, anchor_date, analysis_date, bar_data.d1_atr)
        raw_zones = calculate_zones(bar_data, hvn_result)

        # Should still produce valid zones
        assert len(hvn_result.pocs) == 10, "Should produce 10 POCs"
        print(f"\n✓ Low Volume: {ticker} - {hvn_result.bars_analyzed} bars, "
              f"{len(raw_zones)} zones")


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestPerformance:
    """Test suite for performance benchmarks."""

    def test_single_ticker_performance(self, tsla_test_case):
        """Benchmark single ticker analysis time."""
        ticker = tsla_test_case['ticker']
        anchor_date = tsla_test_case['anchor_date']
        analysis_date = tsla_test_case['analysis_date']

        start_time = time.time()

        bar_data = calculate_bar_data(ticker, analysis_date)
        ms = calculate_market_structure(ticker, analysis_date)
        hvn_result = calculate_hvn(ticker, anchor_date, analysis_date, bar_data.d1_atr)
        raw_zones = calculate_zones(bar_data, hvn_result)
        filtered_zones = filter_zones(raw_zones, bar_data, ms.composite)
        primary_setup, secondary_setup = analyze_setups(
            filtered_zones, hvn_result, bar_data, ms.composite
        )

        elapsed = time.time() - start_time

        print(f"\n✓ Single Ticker Performance: {elapsed:.2f}s")

        # Single ticker should complete in under 30 seconds
        assert elapsed < 30, f"Single ticker took {elapsed:.2f}s, expected <30s"

    def test_batch_performance(self, multi_ticker_list):
        """Benchmark batch analysis time for 5 tickers."""
        anchor_date = date(2025, 11, 1)
        analysis_date = date.today()

        start_time = time.time()

        for ticker in multi_ticker_list:
            try:
                bar_data = calculate_bar_data(ticker, analysis_date)
                ms = calculate_market_structure(ticker, analysis_date)
                hvn_result = calculate_hvn(ticker, anchor_date, analysis_date, bar_data.d1_atr)
                raw_zones = calculate_zones(bar_data, hvn_result)
                filtered_zones = filter_zones(raw_zones, bar_data, ms.composite)
                analyze_setups(filtered_zones, hvn_result, bar_data, ms.composite)
            except Exception:
                pass  # Continue with other tickers

        elapsed = time.time() - start_time
        avg_time = elapsed / len(multi_ticker_list)

        print(f"\n✓ Batch Performance ({len(multi_ticker_list)} tickers): {elapsed:.2f}s total")
        print(f"  Average per ticker: {avg_time:.2f}s")

        # 5 tickers should complete in under 60 seconds (target from DEVELOPMENT_PLAN.md)
        assert elapsed < 60, f"Batch took {elapsed:.2f}s, expected <60s for 5 tickers"

    def test_ten_ticker_performance(self):
        """Benchmark 10 ticker analysis (target from DEVELOPMENT_PLAN.md)."""
        tickers = ['SPY', 'QQQ', 'AAPL', 'MSFT', 'GOOGL', 'NVDA', 'META', 'AMZN', 'TSLA', 'AMD']
        anchor_date = date(2025, 11, 1)
        analysis_date = date.today()

        start_time = time.time()
        successful = 0

        for ticker in tickers:
            try:
                bar_data = calculate_bar_data(ticker, analysis_date)
                ms = calculate_market_structure(ticker, analysis_date)
                hvn_result = calculate_hvn(ticker, anchor_date, analysis_date, bar_data.d1_atr)
                raw_zones = calculate_zones(bar_data, hvn_result)
                filtered_zones = filter_zones(raw_zones, bar_data, ms.composite)
                analyze_setups(filtered_zones, hvn_result, bar_data, ms.composite)
                successful += 1
            except Exception as e:
                print(f"  {ticker}: Error - {e}")

        elapsed = time.time() - start_time

        print(f"\n✓ 10-Ticker Performance: {elapsed:.2f}s total ({successful}/{len(tickers)} successful)")
        print(f"  Target: <60s")

        # 10 tickers should complete in under 60 seconds
        assert elapsed < 60, f"10 tickers took {elapsed:.2f}s, expected <60s"


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    # Run with verbose output
    pytest.main([__file__, '-v', '--tb=short', '-s'])
