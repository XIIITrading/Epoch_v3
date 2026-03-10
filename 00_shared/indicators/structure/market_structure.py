"""
================================================================================
EPOCH TRADING SYSTEM - MARKET STRUCTURE v3 (Canonical)
Anchor + Walk-Forward with BOS/CHoCH Detection
XIII Trading LLC
================================================================================

Ported from: market_structure_v3.pine (TradingView)

Method:
    1. Detect fractal highs/lows (Williams fractal, N bars each side)
    2. Find anchor: oldest pair of consecutive same-type fractals
       with no opposite-type fractal between them (tiered lookback)
    3. Walk forward from anchor tracking BOS (Break of Structure)
       and CHoCH (Change of Character) with retracement-based
       weak level anchoring

Outputs:
    direction: 1 (BULL), -1 (BEAR), 0 (NEUTRAL/no structure)
    label: "BULL", "BEAR", "NEUTRAL"
    strong_level: Invalidation price (support if bull, resistance if bear)
    weak_level: Target/continuation price (None if not yet anchored)

================================================================================
"""

import numpy as np
import pandas as pd
from typing import Tuple, Optional, List, Any

from ..config import CONFIG
from ..types import StructureResult
from .._utils import get_high, get_low, get_close


# =============================================================================
# STRUCTURE LABELS
# =============================================================================

STRUCTURE_LABELS = {1: "BULL", -1: "BEAR", 0: "NEUTRAL"}


# =============================================================================
# FRACTAL DETECTION
# =============================================================================

def _detect_fractals_core(
    high: np.ndarray,
    low: np.ndarray,
    length: int,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Detect fractal highs and lows.

    A fractal high is a bar where high > all bars within `length` on each side.
    A fractal low is a bar where low < all bars within `length` on each side.

    Args:
        high: Array of high prices
        low: Array of low prices
        length: Number of bars on each side (2 = classic 5-candle Williams fractal)

    Returns:
        Tuple of (fractal_highs, fractal_lows) as boolean arrays
    """
    n = len(high)
    frac_highs = np.zeros(n, dtype=bool)
    frac_lows = np.zeros(n, dtype=bool)

    if n < 2 * length + 1:
        return frac_highs, frac_lows

    for i in range(length, n - length):
        # Check fractal high
        is_high = True
        for j in range(1, length + 1):
            if high[i] <= high[i - j] or high[i] <= high[i + j]:
                is_high = False
                break
        frac_highs[i] = is_high

        # Check fractal low
        is_low = True
        for j in range(1, length + 1):
            if low[i] >= low[i - j] or low[i] >= low[i + j]:
                is_low = False
                break
        frac_lows[i] = is_low

    return frac_highs, frac_lows


# =============================================================================
# FRACTAL LIST BUILDER
# =============================================================================

def _build_fractal_list(
    high: np.ndarray,
    low: np.ndarray,
    frac_highs: np.ndarray,
    frac_lows: np.ndarray,
) -> List[Tuple[int, int, float]]:
    """
    Build sorted list of fractal events.

    Returns:
        List of (bar_index, type, price) tuples, sorted by bar_index.
        type: 1 = swing low (bullish fractal), -1 = swing high (bearish fractal)
    """
    fractals = []
    for i in range(len(high)):
        # Low first (matches Pine Script push order)
        if frac_lows[i]:
            fractals.append((i, 1, float(low[i])))
        if frac_highs[i]:
            fractals.append((i, -1, float(high[i])))
    return fractals


# =============================================================================
# ANCHOR DETECTION
# =============================================================================

def _find_anchor(
    fractals: List[Tuple[int, int, float]],
    cutoff_idx: int,
) -> Optional[Tuple[int, int, float, Optional[float], int, int, float]]:
    """
    Find the oldest pair of consecutive same-type fractals with no
    opposite-type fractal having bar_index strictly between them.

    Args:
        fractals: Sorted list of (bar_index, type, price)
        cutoff_idx: Only consider fractals with bar_index >= cutoff_idx

    Returns:
        (anchor_bar, anchor_type, strong_price,
         weak_price, weak_bar, frac1_bar, frac1_price)
        or None if no anchor found.
    """
    sz = len(fractals)
    if sz < 2:
        return None

    # Find scan start: first fractal at or after cutoff
    scan_start = -1
    for i in range(sz):
        if fractals[i][0] >= cutoff_idx:
            scan_start = i
            break

    if scan_start < 0 or scan_start >= sz - 1:
        return None

    last_bull_bar, last_bull_price = -1, 0.0
    last_bear_bar, last_bear_price = -1, 0.0

    for i in range(scan_start, sz):
        f_bar, f_type, f_price = fractals[i]

        if f_type == 1:  # Bull fractal (swing low)
            if last_bull_bar != -1:
                # No bear fractal strictly between the two bull fractals?
                bear_between = (
                    last_bear_bar > last_bull_bar and last_bear_bar < f_bar
                )
                if not bear_between:
                    # Found anchor pair — find weak (most recent opposite <= anchor)
                    weak_price, weak_bar = None, 0
                    for k in range(sz - 1, -1, -1):
                        if fractals[k][1] == -1 and fractals[k][0] <= f_bar:
                            weak_price = fractals[k][2]
                            weak_bar = fractals[k][0]
                            break
                    return (
                        f_bar, 1, f_price,
                        weak_price, weak_bar,
                        last_bull_bar, last_bull_price,
                    )
            last_bull_bar = f_bar
            last_bull_price = f_price

        elif f_type == -1:  # Bear fractal (swing high)
            if last_bear_bar != -1:
                bull_between = (
                    last_bull_bar > last_bear_bar and last_bull_bar < f_bar
                )
                if not bull_between:
                    weak_price, weak_bar = None, 0
                    for k in range(sz - 1, -1, -1):
                        if fractals[k][1] == 1 and fractals[k][0] <= f_bar:
                            weak_price = fractals[k][2]
                            weak_bar = fractals[k][0]
                            break
                    return (
                        f_bar, -1, f_price,
                        weak_price, weak_bar,
                        last_bear_bar, last_bear_price,
                    )
            last_bear_bar = f_bar
            last_bear_price = f_price

    return None


# =============================================================================
# HELPERS
# =============================================================================

def _find_nearest_frac(
    fractals: List[Tuple[int, int, float]],
    target_type: int,
    min_bar: int,
    max_bar: int,
) -> Tuple[Optional[float], Optional[int]]:
    """
    Find the most recent fractal of target_type with bar in [min_bar, max_bar].
    Scans backward for efficiency.
    """
    for i in range(len(fractals) - 1, -1, -1):
        f_bar = fractals[i][0]
        if f_bar < min_bar:
            break
        if f_bar <= max_bar and fractals[i][1] == target_type:
            return fractals[i][2], f_bar
    return None, None


# =============================================================================
# WALK-FORWARD STATE MACHINE
# =============================================================================

def _walk_forward(
    fractals: List[Tuple[int, int, float]],
    anchor: Tuple,
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    retrace_pct: float,
) -> Tuple[int, Optional[float], Optional[float]]:
    """
    Walk forward from anchor bar-by-bar, tracking BOS/CHoCH events.

    Returns:
        (direction, strong_level, weak_level)
        weak_level is None if not yet anchored via retracement.
    """
    anchor_bar = anchor[0]
    anchor_type = anchor[1]
    strong_price = anchor[2]
    weak_init_price = anchor[3]

    trend = anchor_type
    strong_level = strong_price
    strong_bar = anchor_bar
    weak_level = None
    weak_anchored = False

    # Initialize last_extreme from anchor's initial weak or anchor bar
    if weak_init_price is not None:
        last_extreme = weak_init_price
    else:
        last_extreme = (
            float(high[anchor_bar]) if trend == 1 else float(low[anchor_bar])
        )

    n_bars = len(high)

    for b in range(anchor_bar, n_bars):
        b_high = float(high[b])
        b_low = float(low[b])
        b_close = float(close[b])

        did_bos = False
        did_choch = False

        if trend == 1:
            # ==================== BULL ====================

            # BOS: close above confirmed weak high
            if (
                weak_anchored
                and weak_level is not None
                and b_close > weak_level
            ):
                did_bos = True
                new_sl, new_sl_bar = _find_nearest_frac(
                    fractals, 1, strong_bar, b
                )
                if new_sl is None:
                    new_sl = strong_level
                    new_sl_bar = strong_bar

                strong_level = new_sl
                strong_bar = new_sl_bar
                weak_level = None
                weak_anchored = False
                last_extreme = b_high

            # CHoCH: close below strong low -> flip to bear
            if (
                not did_bos
                and not did_choch
                and strong_level is not None
                and b_close < strong_level
            ):
                did_choch = True
                new_sh, new_sh_bar = _find_nearest_frac(
                    fractals, -1, strong_bar, b
                )
                if new_sh is None:
                    new_sh = b_high
                    new_sh_bar = b

                trend = -1
                strong_level = new_sh
                strong_bar = new_sh_bar
                weak_level = None
                weak_anchored = False
                last_extreme = b_low

            # Track new high (running extreme for retracement)
            if (
                not did_bos
                and not did_choch
                and last_extreme is not None
                and b_high > last_extreme
            ):
                last_extreme = b_high

            # 30% retracement check -> anchor weak at nearest swing high fractal
            if (
                not did_bos
                and not did_choch
                and not weak_anchored
                and last_extreme is not None
                and strong_level is not None
            ):
                rng = last_extreme - strong_level
                if rng > 0:
                    threshold = last_extreme - (rng * retrace_pct)
                    if b_low <= threshold:
                        f_wk, _ = _find_nearest_frac(
                            fractals, -1, strong_bar, b
                        )
                        if f_wk is not None:
                            weak_level = f_wk
                            weak_anchored = True

        elif trend == -1:
            # ==================== BEAR ====================

            # BOS: close below confirmed weak low
            if (
                weak_anchored
                and weak_level is not None
                and b_close < weak_level
            ):
                did_bos = True
                new_sh, new_sh_bar = _find_nearest_frac(
                    fractals, -1, strong_bar, b
                )
                if new_sh is None:
                    new_sh = strong_level
                    new_sh_bar = strong_bar

                strong_level = new_sh
                strong_bar = new_sh_bar
                weak_level = None
                weak_anchored = False
                last_extreme = b_low

            # CHoCH: close above strong high -> flip to bull
            if (
                not did_bos
                and not did_choch
                and strong_level is not None
                and b_close > strong_level
            ):
                did_choch = True
                new_sl, new_sl_bar = _find_nearest_frac(
                    fractals, 1, strong_bar, b
                )
                if new_sl is None:
                    new_sl = b_low
                    new_sl_bar = b

                trend = 1
                strong_level = new_sl
                strong_bar = new_sl_bar
                weak_level = None
                weak_anchored = False
                last_extreme = b_high

            # Track new low (running extreme for retracement)
            if (
                not did_bos
                and not did_choch
                and last_extreme is not None
                and b_low < last_extreme
            ):
                last_extreme = b_low

            # 30% retracement check (upward for bear)
            if (
                not did_bos
                and not did_choch
                and not weak_anchored
                and last_extreme is not None
                and strong_level is not None
            ):
                rng = strong_level - last_extreme
                if rng > 0:
                    threshold = last_extreme + (rng * retrace_pct)
                    if b_high >= threshold:
                        f_wk, _ = _find_nearest_frac(
                            fractals, 1, strong_bar, b
                        )
                        if f_wk is not None:
                            weak_level = f_wk
                            weak_anchored = True

    final_weak = weak_level if weak_anchored else None
    return trend, strong_level, final_weak


# =============================================================================
# V3 CORE: ANCHOR + WALK-FORWARD
# =============================================================================

def _calculate_structure_v3(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    fractal_length: int,
    retrace_pct: float,
    lookback_tiers: tuple,
) -> Tuple[int, str, Optional[float], Optional[float]]:
    """
    Full v3 structure calculation.

    Returns:
        (direction, label, strong_level, weak_level)
    """
    n = len(high)

    # Step 1: Detect fractals
    frac_highs, frac_lows = _detect_fractals_core(high, low, fractal_length)

    # Step 2: Build fractal list
    fractals = _build_fractal_list(high, low, frac_highs, frac_lows)
    if len(fractals) < 2:
        return 0, "NEUTRAL", None, None

    # Step 3: Find anchor with tiered lookback
    anchor = None
    for tier in lookback_tiers:
        cutoff_idx = max(0, n - tier)
        anchor = _find_anchor(fractals, cutoff_idx)
        if anchor is not None:
            break

    if anchor is None:
        return 0, "NEUTRAL", None, None

    # Step 4: Walk forward from anchor
    direction, strong, weak = _walk_forward(
        fractals, anchor, high, low, close, retrace_pct,
    )

    label = STRUCTURE_LABELS.get(direction, "NEUTRAL")
    return direction, label, strong, weak


# =============================================================================
# RESULT BUILDER
# =============================================================================

def _build_result(
    direction: int,
    label: str,
    strong: Optional[float],
    weak: Optional[float],
) -> StructureResult:
    """Build StructureResult with backward-compat field mapping."""
    if direction == 1:   # BULL: strong = support (low), weak = target (high)
        last_swing_low = strong
        last_swing_high = weak
        hh, hl = True, True
    elif direction == -1:  # BEAR: strong = resistance (high), weak = target (low)
        last_swing_high = strong
        last_swing_low = weak
        hh, hl = False, False
    else:
        last_swing_high = None
        last_swing_low = None
        hh, hl = False, False

    return StructureResult(
        direction=direction,
        label=label,
        last_swing_high=last_swing_high,
        last_swing_low=last_swing_low,
        higher_highs=hh,
        higher_lows=hl,
        strong_level=strong,
        weak_level=weak,
    )


# =============================================================================
# DATAFRAME WRAPPERS (public API)
# =============================================================================

def detect_fractals(
    df: pd.DataFrame,
    length: Optional[int] = None,
    high_col: str = "high",
    low_col: str = "low",
) -> Tuple[pd.Series, pd.Series]:
    """
    Detect fractal highs and lows in a DataFrame.

    Returns:
        Tuple of (fractal_highs, fractal_lows) as boolean Series
    """
    length = length or CONFIG.structure.fractal_length
    fh, fl = _detect_fractals_core(
        df[high_col].values.astype(np.float64),
        df[low_col].values.astype(np.float64),
        length,
    )
    return (
        pd.Series(fh, index=df.index, name="fractal_high"),
        pd.Series(fl, index=df.index, name="fractal_low"),
    )


def get_swing_points(
    df: pd.DataFrame,
    length: Optional[int] = None,
) -> Tuple[List[float], List[float]]:
    """Get lists of swing high and swing low prices."""
    frac_highs, frac_lows = detect_fractals(df, length)
    swing_highs = df.loc[frac_highs, "high"].tolist()
    swing_lows = df.loc[frac_lows, "low"].tolist()
    return swing_highs, swing_lows


def get_market_structure(
    df: pd.DataFrame,
    length: Optional[int] = None,
    retrace_pct: Optional[float] = None,
    lookback_tiers: Optional[tuple] = None,
) -> StructureResult:
    """
    Analyze market structure from a DataFrame using v3 anchor + walk-forward.

    Args:
        df: DataFrame with 'high', 'low', 'close' columns
        length: Fractal length (bars each side). Default from config.
        retrace_pct: Retracement % for weak level anchoring. Default from config.
        lookback_tiers: Anchor lookback tiers in bars. Default from config.

    Returns:
        StructureResult with direction, label, strong/weak levels
    """
    length = length or CONFIG.structure.fractal_length
    retrace_pct = (
        retrace_pct if retrace_pct is not None
        else CONFIG.structure.retrace_pct
    )
    lookback_tiers = lookback_tiers or CONFIG.structure.lookback_tiers

    high = df["high"].values.astype(np.float64)
    low = df["low"].values.astype(np.float64)
    close = df["close"].values.astype(np.float64)

    direction, label, strong, weak = _calculate_structure_v3(
        high, low, close, length, retrace_pct, lookback_tiers,
    )

    return _build_result(direction, label, strong, weak)


# =============================================================================
# BAR-LIST WRAPPER
# =============================================================================

def calculate_structure_from_bars(
    bars: List[Any],
    length: Optional[int] = None,
    up_to_index: Optional[int] = None,
    retrace_pct: Optional[float] = None,
    lookback_tiers: Optional[tuple] = None,
) -> StructureResult:
    """
    Calculate market structure from a list of bars using v3 algorithm.

    Args:
        bars: List of bar data (dict or object with high/low/close)
        length: Fractal length (bars each side)
        up_to_index: Analyze up to this index (inclusive)
        retrace_pct: Retracement % for weak level anchoring
        lookback_tiers: Anchor lookback tiers in bars

    Returns:
        StructureResult
    """
    length = length or CONFIG.structure.fractal_length
    retrace_pct = (
        retrace_pct if retrace_pct is not None
        else CONFIG.structure.retrace_pct
    )
    lookback_tiers = lookback_tiers or CONFIG.structure.lookback_tiers

    if not bars:
        return StructureResult(
            direction=0, label="NEUTRAL",
            last_swing_high=None, last_swing_low=None,
            higher_highs=False, higher_lows=False,
            strong_level=None, weak_level=None,
        )

    end = (up_to_index + 1) if up_to_index is not None else len(bars)
    end = min(end, len(bars))

    highs = np.array(
        [get_high(bars[i], 0.0) for i in range(end)], dtype=np.float64,
    )
    lows = np.array(
        [get_low(bars[i], 0.0) for i in range(end)], dtype=np.float64,
    )
    closes = np.array(
        [get_close(bars[i], 0.0) for i in range(end)], dtype=np.float64,
    )

    direction, label, strong, weak = _calculate_structure_v3(
        highs, lows, closes, length, retrace_pct, lookback_tiers,
    )

    return _build_result(direction, label, strong, weak)


# =============================================================================
# UTILITY HELPERS
# =============================================================================

def get_structure_label(direction: int) -> str:
    """Get structure label from direction integer."""
    return STRUCTURE_LABELS.get(direction, "NEUTRAL")


def is_structure_aligned(structure_direction: int, trade_direction: str) -> bool:
    """Check if structure aligns with trade direction."""
    is_long = trade_direction.upper() in ("LONG", "BULL", "BULLISH")
    return structure_direction == 1 if is_long else structure_direction == -1
