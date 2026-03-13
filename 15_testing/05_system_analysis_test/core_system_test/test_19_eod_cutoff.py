"""
Test 19: Does 15:30 cutoff = LOSS?
Source: 03_backtest/processor/.../m1_atr_stop_2/calculator.py

EOD logic:
  Only process bars AFTER entry_time and UP TO 15:30 (EOD_CUTOFF).
  If R1 is not hit by 15:30, result = LOSS.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import time
from conftest import make_check


EOD_CUTOFF = time(15, 30)


def time_to_minutes(t):
    return t.hour * 60 + t.minute


def walk_bars_with_time(entry_price, m1_atr, entry_time, bars, direction="LONG"):
    """
    Simulate bar walk with time-based EOD cutoff.
    bars = list of {high, low, close, bar_time: time object}
    """
    is_long = direction == "LONG"
    stop_price = entry_price - m1_atr if is_long else entry_price + m1_atr
    r1_price = entry_price + m1_atr if is_long else entry_price - m1_atr

    entry_minutes = time_to_minutes(entry_time)
    eod_minutes = time_to_minutes(EOD_CUTOFF)

    r1_hit = False
    stop_hit = False

    for bar in bars:
        bar_minutes = time_to_minutes(bar["bar_time"])

        # Skip bars at or before entry
        if bar_minutes <= entry_minutes:
            continue

        # Break at EOD cutoff
        if bar_minutes > eod_minutes:
            break

        # Check stop
        if is_long:
            stop_on_bar = bar["close"] <= stop_price
        else:
            stop_on_bar = bar["close"] >= stop_price

        # Check R1
        if is_long:
            r1_on_bar = bar["high"] >= r1_price
        else:
            r1_on_bar = bar["low"] <= r1_price

        if stop_on_bar:
            stop_hit = True
            break

        if r1_on_bar:
            r1_hit = True

    result = "WIN" if r1_hit else "LOSS"
    return {"r1_hit": r1_hit, "stop_hit": stop_hit, "result": result}


class TestEODCutoff:
    TEST_ID = "test_19_eod_cutoff"
    QUESTION = "Does 15:30 cutoff = LOSS?"

    def test_r1_before_cutoff(self, result_writer):
        """R1 hit at 14:00 → WIN."""
        bars = [
            {"high": 103.0, "low": 100.0, "close": 102.5,
             "bar_time": time(14, 0)},
        ]
        r = walk_bars_with_time(100.0, 2.0, time(10, 0), bars)
        assert r["result"] == "WIN"

    def test_no_r1_by_cutoff(self, result_writer):
        """No R1 by 15:30 → LOSS."""
        bars = [
            {"high": 101.0, "low": 99.0, "close": 100.5,
             "bar_time": time(14, 0)},
            {"high": 101.5, "low": 99.5, "close": 100.5,
             "bar_time": time(15, 0)},
            {"high": 101.0, "low": 99.0, "close": 100.0,
             "bar_time": time(15, 29)},
        ]
        r = walk_bars_with_time(100.0, 2.0, time(10, 0), bars)
        assert r["result"] == "LOSS"
        assert r["stop_hit"] is False

    def test_bars_after_cutoff_ignored(self, result_writer):
        """Bar at 15:31 is ignored even if it would hit R1."""
        bars = [
            {"high": 101.0, "low": 99.0, "close": 100.5,
             "bar_time": time(15, 0)},
            {"high": 103.0, "low": 100.0, "close": 102.5,
             "bar_time": time(15, 31)},  # After cutoff
        ]
        r = walk_bars_with_time(100.0, 2.0, time(10, 0), bars)
        assert r["result"] == "LOSS"

    def test_bars_at_entry_skipped(self, result_writer):
        """Bar at entry time is skipped (only process AFTER entry)."""
        bars = [
            {"high": 103.0, "low": 100.0, "close": 102.5,
             "bar_time": time(10, 0)},  # Same as entry time
        ]
        r = walk_bars_with_time(100.0, 2.0, time(10, 0), bars)
        assert r["result"] == "LOSS"

    def test_full_suite(self, result_writer):
        checks = []

        # R1 before cutoff
        bars = [{"high": 103.0, "low": 100.0, "close": 102.5,
                 "bar_time": time(14, 0)}]
        r = walk_bars_with_time(100.0, 2.0, time(10, 0), bars)
        checks.append(make_check("r1_before_cutoff", "WIN", r["result"]))

        # No R1 by cutoff
        bars = [{"high": 101.0, "low": 99.0, "close": 100.5,
                 "bar_time": time(15, 0)}]
        r = walk_bars_with_time(100.0, 2.0, time(10, 0), bars)
        checks.append(make_check("no_r1_by_cutoff", "LOSS", r["result"]))

        # After cutoff ignored
        bars = [{"high": 103.0, "low": 100.0, "close": 102.5,
                 "bar_time": time(15, 31)}]
        r = walk_bars_with_time(100.0, 2.0, time(10, 0), bars)
        checks.append(make_check("after_cutoff_ignored", "LOSS", r["result"]))

        result_writer.write_validation(self.TEST_ID, self.QUESTION, checks)
        assert all(c["passed"] for c in checks)
