"""
Test 02: Do SMA9/SMA21 produce correct averages?
Source: shared.indicators.core.sma
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
from conftest import make_check

from shared.indicators.core.sma import sma_df, sma_spread_df, get_sma_config_str


class TestSMA:
    TEST_ID = "test_02_sma"
    QUESTION = "Do SMA9/SMA21 produce correct averages?"

    def test_sma9_known_values(self, result_writer):
        """SMA9 at index 8 should be mean of first 9 closes."""
        closes = list(range(1, 25))  # 1..24
        df = pd.DataFrame({"close": closes}, dtype=float)
        sma9 = sma_df(df, period=9)
        # Mean of [1,2,3,4,5,6,7,8,9] = 5.0
        assert abs(sma9.iloc[8] - 5.0) < 1e-6

    def test_sma21_known_values(self, result_writer):
        """SMA21 at index 20 should be mean of first 21 closes."""
        closes = list(range(1, 30))  # 1..29
        df = pd.DataFrame({"close": closes}, dtype=float)
        sma21 = sma_df(df, period=21)
        # Mean of [1..21] = 11.0
        assert abs(sma21.iloc[20] - 11.0) < 1e-6

    def test_sma_spread_bull_config(self, result_writer):
        """When SMA9 > SMA21, config should be BULL."""
        # Rising prices → SMA9 > SMA21
        closes = [float(i) for i in range(1, 30)]
        df = pd.DataFrame({"close": closes})
        spread = sma_spread_df(df)
        # At last bar, SMA9 should be > SMA21 since prices are rising
        last_config = spread["sma_config"].iloc[-1]
        assert last_config == "BULL"

    def test_sma_spread_bear_config(self, result_writer):
        """When SMA9 < SMA21, config should be BEAR."""
        # Falling prices → SMA9 < SMA21
        closes = [float(30 - i) for i in range(30)]
        df = pd.DataFrame({"close": closes})
        spread = sma_spread_df(df)
        last_config = spread["sma_config"].iloc[-1]
        assert last_config == "BEAR"

    def test_sma_config_helper(self, result_writer):
        """get_sma_config_str returns correct labels."""
        assert get_sma_config_str(110.0, 100.0) == "BULL"
        assert get_sma_config_str(90.0, 100.0) == "BEAR"
        assert get_sma_config_str(100.0, 100.0) == "FLAT"

    def test_full_suite(self, result_writer):
        """Run all checks and write JSON result."""
        checks = []

        # Check 1: SMA9 value
        closes = list(range(1, 25))
        df = pd.DataFrame({"close": closes}, dtype=float)
        sma9 = sma_df(df, period=9)
        checks.append(make_check("sma9_at_index_8", 5.0, float(sma9.iloc[8])))

        # Check 2: SMA21 value
        closes = list(range(1, 30))
        df = pd.DataFrame({"close": closes}, dtype=float)
        sma21 = sma_df(df, period=21)
        checks.append(make_check("sma21_at_index_20", 11.0, float(sma21.iloc[20])))

        # Check 3: BULL config
        df_bull = pd.DataFrame({"close": [float(i) for i in range(1, 30)]})
        spread = sma_spread_df(df_bull)
        checks.append(make_check("bull_config", "BULL", spread["sma_config"].iloc[-1]))

        # Check 4: BEAR config
        df_bear = pd.DataFrame({"close": [float(30 - i) for i in range(30)]})
        spread = sma_spread_df(df_bear)
        checks.append(make_check("bear_config", "BEAR", spread["sma_config"].iloc[-1]))

        result_writer.write_validation(self.TEST_ID, self.QUESTION, checks)
        assert all(c["passed"] for c in checks)
