"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
Trade Lifecycle Analysis - Signal Calculator
XIII Trading LLC
================================================================================

Pure calculation logic for trade lifecycle signal extraction.
No database access -- operates on in-memory data structures.

Analyzes M1 indicator bar sequences to produce:
  1. Trend signals (INCREASING, DECREASING, INC_THEN_DEC, etc.)
  2. Level signals (COMPRESSED, EXPANDING, STRONG_BUY, etc.)
  3. Flip signals (NO_FLIP, FLIP_TO_POSITIVE, FLIP_TO_NEGATIVE, etc.)

Version: 1.0.0
================================================================================
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

from config import (
    TREND_WINDOW,
    M1_NUMERIC_INDICATORS,
    M1_CATEGORICAL_INDICATORS,
    LEVEL_THRESHOLDS,
    FLIP_INDICATORS,
    RAMPUP_BARS,
    POST_ENTRY_BARS,
)


# =============================================================================
# RESULT DATA STRUCTURE
# =============================================================================

@dataclass
class LifecycleResult:
    """Complete lifecycle signal extraction for one trade."""
    trade_id: str
    ticker: str
    date: str
    entry_time: str
    direction: str
    model: str
    is_winner: bool

    rampup_bars_found: int = 0
    post_entry_bars_found: int = 0

    # Keyed by indicator name
    rampup_signals: Dict[str, str] = field(default_factory=dict)
    entry_levels: Dict[str, str] = field(default_factory=dict)
    post_entry_signals: Dict[str, str] = field(default_factory=dict)
    flip_signals: Dict[str, str] = field(default_factory=dict)

    # Categorical snapshots at entry
    entry_categoricals: Dict[str, Optional[str]] = field(default_factory=dict)

    # M5 progression
    m5_health_at_entry: Optional[int] = None
    m5_health_at_end: Optional[int] = None
    m5_health_trend: Optional[str] = None
    m5_bars_total: int = 0


# =============================================================================
# SIGNAL CLASSIFIERS
# =============================================================================

def classify_trend(values: List[Optional[float]], window: int = TREND_WINDOW) -> str:
    """Classify a sequence of numeric values into a trend signal.

    Returns one of:
        INCREASING, DECREASING, FLAT,
        INC_THEN_DEC, DEC_THEN_INC,
        VOLATILE, INSUFFICIENT
    """
    clean = [v for v in values if v is not None]
    if len(clean) < window:
        return "INSUFFICIENT"

    # Use the last `window` values
    recent = clean[-window:]

    # Calculate bar-to-bar deltas
    deltas = [recent[i + 1] - recent[i] for i in range(len(recent) - 1)]
    if not deltas:
        return "FLAT"

    pos_count = sum(1 for d in deltas if d > 0)
    neg_count = sum(1 for d in deltas if d < 0)
    total = len(deltas)

    # Strong directional
    if pos_count >= total * 0.75:
        return "INCREASING"
    if neg_count >= total * 0.75:
        return "DECREASING"

    # Reversal patterns: first half vs second half
    mid = len(deltas) // 2
    if mid == 0:
        return "FLAT"

    first_half_avg = sum(deltas[:mid]) / mid
    second_half_avg = sum(deltas[mid:]) / (len(deltas) - mid)

    if first_half_avg > 0 and second_half_avg < 0:
        return "INC_THEN_DEC"
    if first_half_avg < 0 and second_half_avg > 0:
        return "DEC_THEN_INC"

    # Volatility (many direction changes)
    sign_changes = sum(
        1 for i in range(len(deltas) - 1)
        if (deltas[i] > 0) != (deltas[i + 1] > 0)
    )
    if sign_changes >= total * 0.6:
        return "VOLATILE"

    return "FLAT"


def classify_level(value: Optional[float], indicator: str) -> str:
    """Classify a single indicator value into a level label using config thresholds."""
    if value is None:
        return "NULL"

    thresholds = LEVEL_THRESHOLDS.get(indicator)
    if not thresholds:
        return "UNKNOWN"

    for label, (low, high) in thresholds.items():
        if low is None and high is not None:
            if value < high:
                return label
        elif low is not None and high is None:
            if value >= low:
                return label
        elif low is not None and high is not None:
            if low <= value < high:
                return label

    return "UNKNOWN"


def detect_flip(values: List[Optional[float]]) -> str:
    """Detect if a sign-based indicator flipped direction in the sequence.

    Returns: NO_FLIP, FLIP_TO_POSITIVE, FLIP_TO_NEGATIVE, MULTIPLE_FLIPS, INSUFFICIENT
    """
    clean = [v for v in values if v is not None]
    if len(clean) < 3:
        return "INSUFFICIENT"

    signs = [1 if v > 0 else -1 if v < 0 else 0 for v in clean]
    flips = []
    for i in range(1, len(signs)):
        if signs[i] != signs[i - 1] and signs[i] != 0 and signs[i - 1] != 0:
            flips.append(signs[i])

    if len(flips) == 0:
        return "NO_FLIP"
    elif len(flips) == 1:
        return "FLIP_TO_POSITIVE" if flips[0] > 0 else "FLIP_TO_NEGATIVE"
    else:
        return "MULTIPLE_FLIPS"


# =============================================================================
# MAIN CALCULATION
# =============================================================================

def calculate_lifecycle(
    trade: Dict[str, Any],
    m1_bars: List[Dict[str, Any]],
    m5_bars: List[Dict[str, Any]],
) -> LifecycleResult:
    """Calculate all lifecycle signals for a single trade.

    Args:
        trade: dict with trade_id, ticker, date, entry_time, direction, model, is_winner
        m1_bars: all M1 indicator bars for this ticker/date, sorted by bar_time
        m5_bars: M5 trade bars for this trade_id, sorted by bar_seq

    Returns:
        LifecycleResult with all derived signals
    """
    entry_time = trade["entry_time"]

    result = LifecycleResult(
        trade_id=trade["trade_id"],
        ticker=trade["ticker"],
        date=str(trade["date"]),
        entry_time=str(entry_time),
        direction=trade["direction"],
        model=trade["model"],
        is_winner=trade["is_winner"],
    )

    # ------------------------------------------------------------------
    # Split M1 bars into ramp-up / entry / post-entry
    # ------------------------------------------------------------------
    rampup = []
    entry_bar = None
    post_entry = []

    for bar in m1_bars:
        bt = bar["bar_time"]
        if bt < entry_time:
            rampup.append(bar)
        elif bt == entry_time:
            entry_bar = bar
        else:
            post_entry.append(bar)

    # Trim to configured windows
    rampup = rampup[-RAMPUP_BARS:]
    post_entry = post_entry[:POST_ENTRY_BARS]

    # If no exact entry match, use closest bar before
    if entry_bar is None and rampup:
        entry_bar = rampup[-1]
        rampup = rampup[:-1]

    result.rampup_bars_found = len(rampup)
    result.post_entry_bars_found = len(post_entry)

    # ------------------------------------------------------------------
    # Compute signals for each numeric indicator
    # ------------------------------------------------------------------
    for ind in M1_NUMERIC_INDICATORS:
        rampup_values = [b.get(ind) for b in rampup]
        post_values = [b.get(ind) for b in post_entry]
        entry_value = entry_bar.get(ind) if entry_bar else None

        # Trend signals
        result.rampup_signals[ind] = classify_trend(rampup_values)
        result.post_entry_signals[ind] = classify_trend(post_values)

        # Entry level
        result.entry_levels[ind] = classify_level(entry_value, ind)

        # Flip detection (only for sign-based indicators)
        if ind in FLIP_INDICATORS:
            result.flip_signals[ind] = detect_flip(rampup_values)

    # ------------------------------------------------------------------
    # Capture categorical values at entry
    # ------------------------------------------------------------------
    for cat in M1_CATEGORICAL_INDICATORS:
        result.entry_categoricals[cat] = entry_bar.get(cat) if entry_bar else None

    # ------------------------------------------------------------------
    # M5 progression from trade bars
    # ------------------------------------------------------------------
    if m5_bars:
        result.m5_bars_total = len(m5_bars)
        health_scores = [
            b.get("health_score") for b in m5_bars
            if b.get("health_score") is not None
        ]
        if health_scores:
            result.m5_health_at_entry = health_scores[0]
            result.m5_health_at_end = health_scores[-1]
            result.m5_health_trend = classify_trend(
                health_scores, window=min(5, len(health_scores))
            )

    return result
