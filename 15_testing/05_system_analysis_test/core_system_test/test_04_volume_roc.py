"""
Test 04: Is ROC% correct vs 20-bar baseline?
Source: shared.indicators.core.volume_roc
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np
from conftest import make_check

from shared.indicators.core.volume_roc import (
    volume_roc_df, classify_volume_roc, is_elevated_volume, is_high_volume,
)


class TestVolumeROC:
    TEST_ID = "test_04_volume_roc"
    QUESTION = "Is ROC% correct vs 20-bar baseline?"

    def test_roc_double_volume(self, result_writer):
        """Current vol = 2x baseline avg → ROC = +100%."""
        # 20 bars at 1000 vol, then 1 bar at 2000
        volumes = [1000] * 20 + [2000]
        df = pd.DataFrame({"volume": volumes})
        roc = volume_roc_df(df, period=20)
        # At index 20: baseline avg = 1000, current = 2000
        # ROC = (2000 - 1000) / 1000 * 100 = 100%
        assert abs(roc.iloc[20] - 100.0) < 1e-6

    def test_roc_half_volume(self, result_writer):
        """Current vol = 0.5x baseline avg → ROC = -50%."""
        volumes = [1000] * 20 + [500]
        df = pd.DataFrame({"volume": volumes})
        roc = volume_roc_df(df, period=20)
        assert abs(roc.iloc[20] - (-50.0)) < 1e-6

    def test_roc_same_volume(self, result_writer):
        """Current vol = baseline avg → ROC = 0%."""
        volumes = [1000] * 21
        df = pd.DataFrame({"volume": volumes})
        roc = volume_roc_df(df, period=20)
        assert abs(roc.iloc[20] - 0.0) < 1e-6

    def test_classify_above_avg(self, result_writer):
        """ROC > 30% → 'Above Avg'."""
        assert classify_volume_roc(35.0) == "Above Avg"

    def test_classify_below_avg(self, result_writer):
        """ROC < -20% → 'Below Avg'."""
        assert classify_volume_roc(-25.0) == "Below Avg"

    def test_classify_average(self, result_writer):
        """ROC between -20% and 30% → 'Average'."""
        assert classify_volume_roc(10.0) == "Average"

    def test_is_elevated(self, result_writer):
        """is_elevated_volume checks >= 30%."""
        assert is_elevated_volume(30.0) is True
        assert is_elevated_volume(29.9) is False

    def test_is_high(self, result_writer):
        """is_high_volume checks >= 50%."""
        assert is_high_volume(50.0) is True
        assert is_high_volume(49.9) is False

    def test_full_suite(self, result_writer):
        """Run all checks and write JSON result."""
        checks = []

        # Check 1: Double volume = +100%
        volumes = [1000] * 20 + [2000]
        df = pd.DataFrame({"volume": volumes})
        roc = volume_roc_df(df, period=20)
        checks.append(make_check("roc_double_volume", 100.0, float(roc.iloc[20])))

        # Check 2: Half volume = -50%
        volumes = [1000] * 20 + [500]
        df = pd.DataFrame({"volume": volumes})
        roc = volume_roc_df(df, period=20)
        checks.append(make_check("roc_half_volume", -50.0, float(roc.iloc[20])))

        # Check 3: Classification
        checks.append(make_check("classify_above", "Above Avg", classify_volume_roc(35.0)))
        checks.append(make_check("classify_below", "Below Avg", classify_volume_roc(-25.0)))

        result_writer.write_validation(self.TEST_ID, self.QUESTION, checks)
        assert all(c["passed"] for c in checks)
