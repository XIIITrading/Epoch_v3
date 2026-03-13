"""
Test 05: Does CVD slope detect rising/falling/flat?
Source: shared.indicators.core.cvd
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np
from conftest import make_check, make_ohlcv_df

from shared.indicators.core.cvd import cvd_slope_df, classify_cvd_trend


class TestCVDSlope:
    TEST_ID = "test_05_cvd_slope"
    QUESTION = "Does CVD slope detect rising/falling/flat?"

    def test_rising_cvd(self, result_writer):
        """Consistently bullish bars → CVD slope > 0.1 → Rising."""
        n = 30
        # All bars close at high → positive delta → rising CVD
        df = pd.DataFrame({
            "open": [100.0] * n,
            "high": [105.0] * n,
            "low":  [100.0] * n,
            "close": [105.0] * n,
            "volume": [1000] * n,
        })
        slope = cvd_slope_df(df, window=15)
        last_slope = float(slope.iloc[-1])
        assert last_slope > 0.1
        assert classify_cvd_trend(last_slope) == "Rising"

    def test_falling_cvd(self, result_writer):
        """Consistently bearish bars → CVD slope < -0.1 → Falling."""
        n = 30
        # All bars close at low → negative delta → falling CVD
        df = pd.DataFrame({
            "open": [105.0] * n,
            "high": [105.0] * n,
            "low":  [100.0] * n,
            "close": [100.0] * n,
            "volume": [1000] * n,
        })
        slope = cvd_slope_df(df, window=15)
        last_slope = float(slope.iloc[-1])
        assert last_slope < -0.1
        assert classify_cvd_trend(last_slope) == "Falling"

    def test_flat_cvd(self, result_writer):
        """Alternating bull/bear bars → CVD slope ~0 → Flat."""
        n = 30
        opens = []
        highs = []
        lows = []
        closes = []
        for i in range(n):
            if i % 2 == 0:
                opens.append(100.0); highs.append(105.0)
                lows.append(100.0); closes.append(105.0)
            else:
                opens.append(105.0); highs.append(105.0)
                lows.append(100.0); closes.append(100.0)

        df = pd.DataFrame({
            "open": opens, "high": highs,
            "low": lows, "close": closes,
            "volume": [1000] * n,
        })
        slope = cvd_slope_df(df, window=15)
        last_slope = float(slope.iloc[-1])
        assert abs(last_slope) <= 0.1
        assert classify_cvd_trend(last_slope) == "Flat"

    def test_clamping(self, result_writer):
        """CVD slope is clamped to [-2, 2]."""
        # Extreme bullish with escalating volume to push slope high
        n = 30
        df = pd.DataFrame({
            "open": [100.0] * n,
            "high": [105.0] * n,
            "low":  [100.0] * n,
            "close": [105.0] * n,
            "volume": [i * 10000 for i in range(1, n + 1)],
        })
        slope = cvd_slope_df(df, window=15)
        last_slope = float(slope.iloc[-1])
        assert last_slope <= 2.0
        assert last_slope >= -2.0

    def test_full_suite(self, result_writer):
        """Run all checks and write JSON result."""
        checks = []

        # Rising
        n = 30
        df = pd.DataFrame({
            "open": [100.0]*n, "high": [105.0]*n,
            "low": [100.0]*n, "close": [105.0]*n,
            "volume": [1000]*n,
        })
        slope = cvd_slope_df(df, window=15)
        checks.append(make_check("rising_trend", "Rising",
                                 classify_cvd_trend(float(slope.iloc[-1]))))

        # Falling
        df = pd.DataFrame({
            "open": [105.0]*n, "high": [105.0]*n,
            "low": [100.0]*n, "close": [100.0]*n,
            "volume": [1000]*n,
        })
        slope = cvd_slope_df(df, window=15)
        checks.append(make_check("falling_trend", "Falling",
                                 classify_cvd_trend(float(slope.iloc[-1]))))

        # Clamped
        df = pd.DataFrame({
            "open": [100.0]*n, "high": [105.0]*n,
            "low": [100.0]*n, "close": [105.0]*n,
            "volume": [i*10000 for i in range(1, n+1)],
        })
        slope = cvd_slope_df(df, window=15)
        val = float(slope.iloc[-1])
        checks.append(make_check("clamp_max", True, val <= 2.0))
        checks.append(make_check("clamp_min", True, val >= -2.0))

        result_writer.write_validation(self.TEST_ID, self.QUESTION, checks)
        assert all(c["passed"] for c in checks)
