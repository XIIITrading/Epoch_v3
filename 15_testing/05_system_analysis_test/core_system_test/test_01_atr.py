"""
Test 01: Does ATR calculate correctly from known OHLC?
Source: shared.indicators.core.atr
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
from conftest import make_check

from shared.indicators.core.atr import calculate_true_range, atr_df, calculate_atr


class TestATR:
    TEST_ID = "test_01_atr"
    QUESTION = "Does ATR calculate correctly from known OHLC?"

    def test_true_range_normal(self, result_writer):
        """TR = max(H-L, |H-prevC|, |L-prevC|) for normal bar."""
        # Bar: H=105, L=100, prev_close=102
        # H-L=5, |105-102|=3, |100-102|=2 → TR=5
        tr = calculate_true_range(105.0, 100.0, 102.0)
        print(f"\n  [TR Normal] H=105, L=100, prevC=102")
        print(f"    H-L=5.0, |H-prevC|=3.0, |L-prevC|=2.0")
        print(f"    Expected: 5.0  |  Actual: {tr}")
        assert abs(tr - 5.0) < 1e-6

    def test_true_range_gap_up(self, result_writer):
        """Gap up: prev_close well below current range."""
        # Bar: H=110, L=108, prev_close=100
        # H-L=2, |110-100|=10, |108-100|=8 → TR=10
        tr = calculate_true_range(110.0, 108.0, 100.0)
        print(f"\n  [TR Gap Up] H=110, L=108, prevC=100")
        print(f"    H-L=2.0, |H-prevC|=10.0, |L-prevC|=8.0")
        print(f"    Expected: 10.0  |  Actual: {tr}")
        assert abs(tr - 10.0) < 1e-6

    def test_true_range_gap_down(self, result_writer):
        """Gap down: prev_close well above current range."""
        # Bar: H=92, L=90, prev_close=100
        # H-L=2, |92-100|=8, |90-100|=10 → TR=10
        tr = calculate_true_range(92.0, 90.0, 100.0)
        print(f"\n  [TR Gap Down] H=92, L=90, prevC=100")
        print(f"    H-L=2.0, |H-prevC|=8.0, |L-prevC|=10.0")
        print(f"    Expected: 10.0  |  Actual: {tr}")
        assert abs(tr - 10.0) < 1e-6

    def test_atr_df_14_period(self, result_writer):
        """ATR over 14 bars should be SMA of True Range."""
        # 20 bars with known values
        data = {
            "high":  [102, 104, 103, 105, 106, 104, 107, 108, 106, 109,
                      110, 108, 111, 112, 110, 113, 114, 112, 115, 116],
            "low":   [98,  99, 100,  99, 101, 100, 102, 103, 101, 104,
                      105, 103, 106, 107, 105, 108, 109, 107, 110, 111],
            "close": [101, 103, 101, 104, 105, 102, 106, 107, 104, 108,
                      109, 106, 110, 111, 108, 112, 113, 110, 114, 115],
        }
        df = pd.DataFrame(data, dtype=float)
        result = atr_df(df, period=14)

        nan_count = sum(1 for i in range(13) if np.isnan(result.iloc[i]))
        print(f"\n  [ATR DataFrame 14-period] 20 bars of synthetic OHLC")
        print(f"    NaN count (first 13): {nan_count}/13")
        print(f"    ATR values:")
        for i in range(len(result)):
            val = result.iloc[i]
            label = f"      [{i:2d}] {val:.4f}" if not np.isnan(val) else f"      [{i:2d}] NaN"
            print(label)

        # First 13 values should be NaN
        assert all(np.isnan(result.iloc[i]) for i in range(13))
        # Value at index 13 should be defined
        assert not np.isnan(result.iloc[13])
        # ATR should be positive
        assert result.iloc[13] > 0

    def test_calculate_atr_bar_list(self, result_writer):
        """Bar-list wrapper returns ATRResult correctly."""
        bars = [{"high": 102, "low": 98, "close": 101}]
        for i in range(15):
            bars.append({
                "high": 100 + i * 0.5 + 2,
                "low": 100 + i * 0.5 - 2,
                "close": 100 + i * 0.5,
            })
        result = calculate_atr(bars, period=14)
        print(f"\n  [ATR Bar List] 16 bars, period=14")
        print(f"    ATR:        {result.atr}")
        print(f"    True Range: {result.true_range}")
        print(f"    Period:     {result.period}")
        assert result.atr is not None
        assert result.true_range is not None
        assert result.period == 14
        assert result.atr > 0

    def test_full_suite(self, result_writer):
        """Run all checks and write JSON result."""
        checks = []

        # Check 1: Normal TR
        tr1 = calculate_true_range(105.0, 100.0, 102.0)
        checks.append(make_check("true_range_normal", 5.0, tr1))

        # Check 2: Gap up TR
        tr2 = calculate_true_range(110.0, 108.0, 100.0)
        checks.append(make_check("true_range_gap_up", 10.0, tr2))

        # Check 3: Gap down TR
        tr3 = calculate_true_range(92.0, 90.0, 100.0)
        checks.append(make_check("true_range_gap_down", 10.0, tr3))

        # Check 4: ATR series produces valid values at index 13+
        data = {
            "high":  [102, 104, 103, 105, 106, 104, 107, 108, 106, 109,
                      110, 108, 111, 112, 110, 113, 114, 112, 115, 116],
            "low":   [98,  99, 100,  99, 101, 100, 102, 103, 101, 104,
                      105, 103, 106, 107, 105, 108, 109, 107, 110, 111],
            "close": [101, 103, 101, 104, 105, 102, 106, 107, 104, 108,
                      109, 106, 110, 111, 108, 112, 113, 110, 114, 115],
        }
        df = pd.DataFrame(data, dtype=float)
        atr_series = atr_df(df, period=14)
        atr_val = float(atr_series.iloc[13])
        checks.append(make_check(
            "atr_14_valid", True, not np.isnan(atr_val) and atr_val > 0
        ))

        print(f"\n  [Full Suite Summary]")
        print(f"  {'Check':<25} {'Expected':>10} {'Actual':>10} {'Pass':>6}")
        print(f"  {'-'*53}")
        for c in checks:
            exp = str(c['expected'])
            act = str(round(c['actual'], 6)) if isinstance(c['actual'], float) else str(c['actual'])
            status = "PASS" if c['passed'] else "FAIL"
            print(f"  {c['name']:<25} {exp:>10} {act:>10} {status:>6}")
        print(f"  {'-'*53}")
        passed = sum(1 for c in checks if c['passed'])
        print(f"  Result: {passed}/{len(checks)} checks passed")

        result_writer.write_validation(self.TEST_ID, self.QUESTION, checks)
        assert all(c["passed"] for c in checks)
