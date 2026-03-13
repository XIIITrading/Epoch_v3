"""
Test 06: Does structure detect bull/bear from fractals?
Source: shared.indicators.structure.market_structure
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from conftest import make_check

from shared.indicators.structure.market_structure import (
    get_market_structure, detect_fractals,
)


class TestStructure:
    TEST_ID = "test_06_structure"
    QUESTION = "Does structure detect bull/bear from fractals?"

    def _prices_to_df(self, prices):
        """Convert base prices into OHLC DataFrame with small spread."""
        return pd.DataFrame({
            "high": [p + 0.5 for p in prices],
            "low": [p - 0.5 for p in prices],
            "close": [p + 0.2 for p in prices],
        })

    def _make_bull_df(self):
        """Create data with bull anchor (two consecutive swing lows) → BULL.

        Phase 1: Two fractal lows without a fractal high between them.
                 Equal-high plateau (bars 4-6) prevents fractal high detection.
        Phase 2: Rising oscillations that maintain BULL direction.
        """
        prices = [
            # Phase 1: anchor establishment
            100, 99, 97, 99, 100,       # fractal low at idx 2
            100, 100, 96, 99, 100,      # fractal low at idx 7 (plateau blocks frac high)
            # Phase 2: bullish trend (HH + HL)
            101, 102, 103, 104, 105,
            104, 103, 104, 105, 106,
            107, 108, 109, 110, 111,
            110, 109, 110, 111, 112,
            113, 114, 115, 116, 117,
            116, 115, 116, 117, 118,
        ]
        return self._prices_to_df(prices)

    def _make_bear_df(self):
        """Create data with bear anchor (two consecutive swing highs) → BEAR.

        Phase 1: Two fractal highs without a fractal low between them.
                 Equal-low plateau (bars 4-6) prevents fractal low detection.
        Phase 2: Falling oscillations that maintain BEAR direction.
        """
        prices = [
            # Phase 1: anchor establishment
            100, 101, 103, 101, 100,    # fractal high at idx 2
            100, 100, 104, 101, 100,    # fractal high at idx 7 (plateau blocks frac low)
            # Phase 2: bearish trend (LH + LL)
            99, 98, 97, 96, 95,
            96, 97, 96, 95, 94,
            93, 92, 91, 90, 89,
            90, 91, 90, 89, 88,
            87, 86, 85, 84, 83,
            84, 85, 84, 83, 82,
        ]
        return self._prices_to_df(prices)

    def test_bull_structure(self, result_writer):
        """Rising prices → BULL structure."""
        df = self._make_bull_df()
        result = get_market_structure(df)
        assert result.direction == 1
        assert result.label == "BULL"

    def test_bear_structure(self, result_writer):
        """Falling prices → BEAR structure."""
        df = self._make_bear_df()
        result = get_market_structure(df)
        assert result.direction == -1
        assert result.label == "BEAR"

    def test_detect_fractals_returns_series(self, result_writer):
        """detect_fractals returns two boolean Series."""
        df = self._make_bull_df()
        frac_highs, frac_lows = detect_fractals(df, length=2)
        assert len(frac_highs) == len(df)
        assert len(frac_lows) == len(df)
        # Should detect at least some fractals
        assert frac_highs.sum() > 0 or frac_lows.sum() > 0

    def test_full_suite(self, result_writer):
        """Run all checks and write JSON result."""
        checks = []

        # Bull structure
        df_bull = self._make_bull_df()
        r = get_market_structure(df_bull)
        checks.append(make_check("bull_direction", 1, r.direction))
        checks.append(make_check("bull_label", "BULL", r.label))

        # Bear structure
        df_bear = self._make_bear_df()
        r = get_market_structure(df_bear)
        checks.append(make_check("bear_direction", -1, r.direction))
        checks.append(make_check("bear_label", "BEAR", r.label))

        result_writer.write_validation(self.TEST_ID, self.QUESTION, checks)
        assert all(c["passed"] for c in checks)
