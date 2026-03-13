"""
Test 17: Are R-hits detected at correct bar?
Source: 03_backtest/processor/.../m1_atr_stop_2/calculator.py

R-level hit detection:
  LONG:  bar_high >= r_price (price-based, high touch)
  SHORT: bar_low <= r_price (price-based, low touch)

Stop detection:
  LONG:  bar_close <= stop_price (close-based)
  SHORT: bar_close >= stop_price (close-based)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from conftest import make_check


def walk_bars_long(entry_price, m1_atr, bars):
    """
    Simulate M1 bar walk for LONG trade.
    bars = list of {high, low, close, bar_idx}
    Returns dict with r_hits, stop_hit, max_r, result.
    """
    stop_price = entry_price - m1_atr
    r_prices = {r: entry_price + (r * m1_atr) for r in range(1, 6)}

    r_hits = {}
    stop_hit = False
    stop_bar = None

    for bar in bars:
        bar_idx = bar["bar_idx"]
        bar_high = bar["high"]
        bar_close = bar["close"]

        # Check stop (close-based)
        stop_on_this_bar = bar_close <= stop_price

        # Check R-levels (price-based)
        new_hits = []
        for r in range(1, 6):
            if r not in r_hits and bar_high >= r_prices[r]:
                new_hits.append(r)

        # Same-candle conflict: stop invalidates R-hits
        if stop_on_this_bar:
            stop_hit = True
            stop_bar = bar_idx
            break

        for r in new_hits:
            r_hits[r] = bar_idx

    max_r = max(r_hits.keys()) if r_hits else -1
    result = "WIN" if 1 in r_hits else "LOSS"
    return {"r_hits": r_hits, "stop_hit": stop_hit, "stop_bar": stop_bar,
            "max_r": max_r, "result": result}


class TestRLevelHits:
    TEST_ID = "test_17_r_level_hits"
    QUESTION = "Are R-hits detected at correct bar?"

    def test_r1_hit_at_bar_2(self, result_writer):
        """R1 hit when bar_high touches R1 price."""
        # entry=100, atr=2 → R1=102
        bars = [
            {"high": 101.0, "low": 100.0, "close": 100.5, "bar_idx": 1},
            {"high": 102.5, "low": 101.0, "close": 102.0, "bar_idx": 2},
        ]
        r = walk_bars_long(100.0, 2.0, bars)
        assert 1 in r["r_hits"]
        assert r["r_hits"][1] == 2
        assert r["result"] == "WIN"

    def test_multiple_r_hits(self, result_writer):
        """Multiple R-levels hit across bars."""
        bars = [
            {"high": 102.5, "low": 100.0, "close": 102.0, "bar_idx": 1},  # R1
            {"high": 105.0, "low": 103.0, "close": 104.5, "bar_idx": 2},  # R2
            {"high": 107.0, "low": 105.0, "close": 106.5, "bar_idx": 3},  # R3
        ]
        r = walk_bars_long(100.0, 2.0, bars)
        assert r["max_r"] == 3
        assert r["result"] == "WIN"

    def test_stop_before_r1(self, result_writer):
        """Stop hit before R1 → LOSS."""
        bars = [
            {"high": 101.0, "low": 97.0, "close": 97.5, "bar_idx": 1},  # close <= 98 (stop)
        ]
        r = walk_bars_long(100.0, 2.0, bars)
        assert r["stop_hit"] is True
        assert r["result"] == "LOSS"

    def test_no_r_no_stop(self, result_writer):
        """No R-hit and no stop → LOSS (EOD implicit)."""
        bars = [
            {"high": 101.0, "low": 99.0, "close": 100.5, "bar_idx": 1},
            {"high": 101.5, "low": 99.5, "close": 100.0, "bar_idx": 2},
        ]
        r = walk_bars_long(100.0, 2.0, bars)
        assert r["result"] == "LOSS"
        assert r["max_r"] == -1

    def test_full_suite(self, result_writer):
        checks = []

        # R1 at bar 2
        bars = [
            {"high": 101.0, "low": 100.0, "close": 100.5, "bar_idx": 1},
            {"high": 102.5, "low": 101.0, "close": 102.0, "bar_idx": 2},
        ]
        r = walk_bars_long(100.0, 2.0, bars)
        checks.append(make_check("r1_at_bar_2", 2, r["r_hits"].get(1)))
        checks.append(make_check("r1_win", "WIN", r["result"]))

        # Stop before R1
        bars = [{"high": 101.0, "low": 97.0, "close": 97.5, "bar_idx": 1}]
        r = walk_bars_long(100.0, 2.0, bars)
        checks.append(make_check("stop_loss", "LOSS", r["result"]))

        result_writer.write_validation(self.TEST_ID, self.QUESTION, checks)
        assert all(c["passed"] for c in checks)
