"""
Test 18: Is R-hit + stop-close = LOSS?
Source: 03_backtest/processor/.../m1_atr_stop_2/calculator.py

Same-candle conflict resolution:
  If stop triggers on a bar, R-level hits on THAT SAME BAR are INVALIDATED.
  The stop takes priority → LOSS.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from conftest import make_check


def walk_bars_same_candle(entry_price, m1_atr, bars, direction="LONG"):
    """
    Simulate bar walk with same-candle conflict logic.
    Stop invalidates R-hits on the same bar.
    """
    is_long = direction == "LONG"
    stop_price = entry_price - m1_atr if is_long else entry_price + m1_atr
    r_prices = {}
    for r in range(1, 6):
        r_prices[r] = entry_price + (r * m1_atr) if is_long else entry_price - (r * m1_atr)

    r_hits = {}
    stop_hit = False

    for bar in bars:
        bar_high = bar["high"]
        bar_low = bar["low"]
        bar_close = bar["close"]

        # Check stop (close-based)
        if is_long:
            stop_on_this_bar = bar_close <= stop_price
        else:
            stop_on_this_bar = bar_close >= stop_price

        # Check R-levels (price-based)
        new_hits = []
        for r in range(1, 6):
            if r not in r_hits:
                if is_long and bar_high >= r_prices[r]:
                    new_hits.append(r)
                elif not is_long and bar_low <= r_prices[r]:
                    new_hits.append(r)

        # CRITICAL: Same-candle conflict - stop invalidates R-hits
        if stop_on_this_bar:
            stop_hit = True
            # DO NOT credit R-levels hit on this same bar
            break

        # Only credit R-hits if no stop on this bar
        for r in new_hits:
            r_hits[r] = True

    max_r = max(r_hits.keys()) if r_hits else -1
    result = "WIN" if 1 in r_hits else "LOSS"
    return {"r_hits": r_hits, "stop_hit": stop_hit, "max_r": max_r, "result": result}


class TestSameCandle:
    TEST_ID = "test_18_same_candle"
    QUESTION = "Is R-hit + stop-close = LOSS?"

    def test_same_candle_long(self, result_writer):
        """LONG: Bar touches R1 high AND closes below stop → LOSS."""
        # entry=100, atr=2 → stop=98, R1=102
        # Bar: high=102.5 (touches R1), close=97.5 (below stop)
        bars = [{"high": 102.5, "low": 97.0, "close": 97.5}]
        r = walk_bars_same_candle(100.0, 2.0, bars, "LONG")
        assert r["stop_hit"] is True
        assert 1 not in r["r_hits"]  # R1 invalidated
        assert r["result"] == "LOSS"

    def test_same_candle_short(self, result_writer):
        """SHORT: Bar touches R1 low AND closes above stop → LOSS."""
        # entry=100, atr=2 → stop=102, R1=98
        # Bar: low=97.5 (touches R1), close=102.5 (above stop)
        bars = [{"high": 103.0, "low": 97.5, "close": 102.5}]
        r = walk_bars_same_candle(100.0, 2.0, bars, "SHORT")
        assert r["stop_hit"] is True
        assert 1 not in r["r_hits"]
        assert r["result"] == "LOSS"

    def test_r_hit_without_stop(self, result_writer):
        """R1 hit without stop on same bar → WIN."""
        bars = [{"high": 102.5, "low": 99.0, "close": 102.0}]
        r = walk_bars_same_candle(100.0, 2.0, bars, "LONG")
        assert r["stop_hit"] is False
        assert 1 in r["r_hits"]
        assert r["result"] == "WIN"

    def test_r_prior_bar_then_stop(self, result_writer):
        """R1 hit on bar 1, stop on bar 2 → WIN (R1 already credited)."""
        bars = [
            {"high": 102.5, "low": 99.0, "close": 102.0},  # R1 hit
            {"high": 101.0, "low": 97.0, "close": 97.5},   # stop hit
        ]
        r = walk_bars_same_candle(100.0, 2.0, bars, "LONG")
        assert 1 in r["r_hits"]
        assert r["stop_hit"] is True
        assert r["result"] == "WIN"

    def test_full_suite(self, result_writer):
        checks = []

        # Same candle → LOSS
        bars = [{"high": 102.5, "low": 97.0, "close": 97.5}]
        r = walk_bars_same_candle(100.0, 2.0, bars, "LONG")
        checks.append(make_check("same_candle_loss", "LOSS", r["result"]))
        checks.append(make_check("r1_invalidated", True, 1 not in r["r_hits"]))

        # R1 without stop → WIN
        bars = [{"high": 102.5, "low": 99.0, "close": 102.0}]
        r = walk_bars_same_candle(100.0, 2.0, bars, "LONG")
        checks.append(make_check("r1_no_stop_win", "WIN", r["result"]))

        # R1 bar 1, stop bar 2 → WIN
        bars = [
            {"high": 102.5, "low": 99.0, "close": 102.0},
            {"high": 101.0, "low": 97.0, "close": 97.5},
        ]
        r = walk_bars_same_candle(100.0, 2.0, bars, "LONG")
        checks.append(make_check("r1_then_stop_win", "WIN", r["result"]))

        result_writer.write_validation(self.TEST_ID, self.QUESTION, checks)
        assert all(c["passed"] for c in checks)
