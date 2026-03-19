"""
H4 Supply & Demand Zone Calculator
====================================
XIII Trading LLC - Epoch Trading System v2.0

Pivot-based supply/demand zone detection fixed to 4-Hour timeframe.
Runs independently from the Market Structure v3 engine — designed to be
layered with H1 zones, HVN zones, PDV levels, and structure for confluence.

Higher timeframe complement to the H1 calculator — captures broader
swing structure that H1 misses.

Method:
    1. Detect pivot highs/lows using left/right bar lookback on H4 candles
    2. Draw zones ± (ATR * multiplier / 2) around each pivot price
    3. Track polarity: zones flip from resistance→support (and vice versa)
       when price closes through them
    4. Merge overlapping zones to create higher-conviction areas
    5. Output ranked zones with age, touch count, and polarity

Fixed Parameters (H4):
    left_bars:       10  (10 × 4h = 40h ≈ ~3 trading days lookback)
    right_bars:       8  ( 8 × 4h = 32h ≈ ~2 trading days confirmation)
    atr_length:      20  (20 × 4h ≈ 2 trading weeks)
    zone_width_mult: 0.5 (half ATR from bottom to top)
    max_zone_pct:    5.0 (cap zone size at 5% of price)
    max_zones:       8   (per side — 8 supply + 8 demand)
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS — FIXED TO H4
# =============================================================================

LEFT_BARS = 10          # bars to look left for pivot confirmation (40h ≈ 3 days)
RIGHT_BARS = 8          # bars to look right for pivot confirmation (32h ≈ 2 days)
ATR_LENGTH = 20         # ATR period (20 × 4h ≈ 2 weeks)
ZONE_WIDTH_MULT = 0.5   # ATR multiplier for zone width
MAX_ZONE_PCT = 5.0      # max zone size as % of price
MAX_ZONES = 8           # max zones per side (supply / demand)

# Exhaustion thresholds — zones exceeding these are depleted
MAX_FLIPS = 4           # ≥4 polarity reversals = no directional conviction
MAX_TOUCHES = 20        # ≥20 touches on H4 = exhausted (fewer bars than H1)

# Recency window — only count touches/flips from the last N H4 bars
# 25 bars ≈ 2 trading weeks on H4
RECENCY_BARS = 25


# =============================================================================
# DATA MODELS
# =============================================================================

class ZoneType(str, Enum):
    """Zone classification."""
    SUPPLY = "Supply"       # resistance — price rejected downward from here
    DEMAND = "Demand"       # support — price rejected upward from here


class ZoneStatus(str, Enum):
    """Zone lifecycle status."""
    ACTIVE = "Active"       # zone is live and untested
    TESTED = "Tested"       # price has touched zone but it held
    BROKEN = "Broken"       # price closed through the zone


@dataclass
class Zone:
    """A single supply or demand zone."""
    zone_id: str                # unique identifier (e.g. "S1", "D3")
    zone_type: ZoneType         # Supply or Demand
    top: float                  # upper edge of zone
    bottom: float               # lower edge of zone
    pivot_price: float          # the pivot price that created this zone
    pivot_bar: int              # bar index where pivot occurred
    created_bar: int            # bar index where zone was confirmed (pivot_bar + right_bars)
    status: ZoneStatus = ZoneStatus.ACTIVE
    touches: int = 0            # lifetime touches
    flips: int = 0              # lifetime polarity flips
    recent_touches: int = 0     # touches within RECENCY_BARS window
    recent_flips: int = 0       # flips within RECENCY_BARS window
    merged: bool = False        # whether this zone was created by merging overlapping zones

    @property
    def midpoint(self) -> float:
        return (self.top + self.bottom) / 2

    @property
    def width(self) -> float:
        return self.top - self.bottom

    @property
    def width_pct(self) -> float:
        """Zone width as percentage of midpoint price."""
        mid = self.midpoint
        return (self.width / mid * 100) if mid > 0 else 0.0


@dataclass
class H4SupplyDemandResult:
    """Complete result from H4 zone calculation."""
    ticker: str
    bar_count: int                          # total H4 bars analyzed

    # Active zones at the end of the data
    supply_zones: List[Zone] = field(default_factory=list)
    demand_zones: List[Zone] = field(default_factory=list)

    # Exhausted zones (too many touches/flips — order imbalance depleted)
    exhausted_zones: List[Zone] = field(default_factory=list)

    # Summary
    total_supply: int = 0
    total_demand: int = 0
    nearest_supply: Optional[float] = None  # nearest supply zone bottom
    nearest_demand: Optional[float] = None  # nearest demand zone top
    last_close: Optional[float] = None

    # Error
    error: Optional[str] = None

    @property
    def all_zones(self) -> List[Zone]:
        """All active zones sorted by price (highest first)."""
        return sorted(
            self.supply_zones + self.demand_zones,
            key=lambda z: z.midpoint,
            reverse=True,
        )


# =============================================================================
# HEIKIN ASHI BODY CALCULATION
# =============================================================================

def _calculate_ha_bodies(
    open_: np.ndarray,
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate Heikin Ashi open/close for body-based pivot detection.

    Returns:
        (ha_body_high, ha_body_low) — the max/min of haOpen, haClose per bar.
    """
    n = len(open_)
    ha_close = (open_ + high + low + close) / 4.0
    ha_open = np.zeros(n)
    ha_open[0] = (open_[0] + close[0]) / 2.0

    for i in range(1, n):
        ha_open[i] = (ha_open[i - 1] + ha_close[i - 1]) / 2.0

    ha_body_high = np.maximum(ha_open, ha_close)
    ha_body_low = np.minimum(ha_open, ha_close)

    return ha_body_high, ha_body_low


# =============================================================================
# ATR CALCULATION
# =============================================================================

def _calculate_atr(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    length: int,
) -> np.ndarray:
    """Calculate ATR using Wilder's smoothing (RMA)."""
    n = len(high)
    tr = np.zeros(n)
    atr = np.zeros(n)

    for i in range(n):
        if i == 0:
            tr[i] = high[i] - low[i]
        else:
            tr[i] = max(
                high[i] - low[i],
                abs(high[i] - close[i - 1]),
                abs(low[i] - close[i - 1]),
            )

    # RMA (Wilder's smoothing)
    if n >= length:
        atr[length - 1] = np.mean(tr[:length])
        for i in range(length, n):
            atr[i] = (atr[i - 1] * (length - 1) + tr[i]) / length

    return atr


# =============================================================================
# PIVOT DETECTION
# =============================================================================

def _detect_pivots(
    high: np.ndarray,
    low: np.ndarray,
    left: int,
    right: int,
) -> Tuple[List[Tuple[int, float]], List[Tuple[int, float]]]:
    """
    Detect pivot highs and pivot lows.

    A pivot high at bar i requires:
        high[i] > all highs in [i-left, i-1] AND [i+1, i+right]

    A pivot low at bar i requires:
        low[i] < all lows in [i-left, i-1] AND [i+1, i+right]

    Returns:
        (pivot_highs, pivot_lows) — each is a list of (bar_index, price)
    """
    n = len(high)
    pivot_highs: List[Tuple[int, float]] = []
    pivot_lows: List[Tuple[int, float]] = []

    for i in range(left, n - right):
        # --- Pivot High ---
        is_pivot_high = True
        for j in range(1, left + 1):
            if high[i] <= high[i - j]:
                is_pivot_high = False
                break
        if is_pivot_high:
            for j in range(1, right + 1):
                if high[i] <= high[i + j]:
                    is_pivot_high = False
                    break
        if is_pivot_high:
            pivot_highs.append((i, float(high[i])))

        # --- Pivot Low ---
        is_pivot_low = True
        for j in range(1, left + 1):
            if low[i] >= low[i - j]:
                is_pivot_low = False
                break
        if is_pivot_low:
            for j in range(1, right + 1):
                if low[i] >= low[i + j]:
                    is_pivot_low = False
                    break
        if is_pivot_low:
            pivot_lows.append((i, float(low[i])))

    return pivot_highs, pivot_lows


# =============================================================================
# ZONE CREATION
# =============================================================================

def _create_zone(
    zone_id: str,
    zone_type: ZoneType,
    pivot_bar: int,
    pivot_price: float,
    atr_value: float,
    close_price: float,
    right_bars: int,
) -> Optional[Zone]:
    """
    Create a zone around a pivot price.

    Zone width = ATR * ZONE_WIDTH_MULT, capped at MAX_ZONE_PCT of price.
    """
    if atr_value <= 0 or pivot_price <= 0:
        return None

    half_width = (atr_value * ZONE_WIDTH_MULT) / 2.0

    # Cap at max percent of price
    max_half = pivot_price * (MAX_ZONE_PCT / 100.0) / 2.0
    half_width = min(half_width, max_half)

    top = pivot_price + half_width
    bottom = pivot_price - half_width

    return Zone(
        zone_id=zone_id,
        zone_type=zone_type,
        top=top,
        bottom=bottom,
        pivot_price=pivot_price,
        pivot_bar=pivot_bar,
        created_bar=pivot_bar + right_bars,
    )


# =============================================================================
# ZONE MERGING (ALIGN OVERLAPPING ZONES)
# =============================================================================

def _zones_overlap(z1: Zone, z2: Zone) -> bool:
    """Check if two zones overlap."""
    return z1.top >= z2.bottom and z2.top >= z1.bottom


def _align_zones(zones: List[Zone]) -> List[Zone]:
    """
    Align overlapping zones (Bjorgum-style).

    When a new zone's edges overlap ANY existing zone, the new zone
    adopts the existing zone's dimensions. Works across types.
    """
    if len(zones) <= 1:
        return zones

    sorted_zones = sorted(zones, key=lambda z: z.pivot_bar)
    aligned: List[Zone] = []

    for zone in sorted_zones:
        for existing in aligned:
            if _zones_overlap(existing, zone):
                zone.top = existing.top
                zone.bottom = existing.bottom
                zone.merged = True
        aligned.append(zone)

    return aligned


# =============================================================================
# POLARITY TRACKING (WALK FORWARD)
# =============================================================================

def _walk_forward_zones(
    zones: List[Zone],
    close: np.ndarray,
    high: np.ndarray,
    low: np.ndarray,
    start_bar: int,
) -> List[Zone]:
    """
    Walk forward bar-by-bar from start_bar, updating zone state.

    Tracks both lifetime and recent (last RECENCY_BARS) touches/flips.
    """
    n = len(close)
    recency_start = max(0, n - RECENCY_BARS)

    for b in range(start_bar, n):
        b_close = float(close[b])
        b_high = float(high[b])
        b_low = float(low[b])
        is_recent = b >= recency_start

        for zone in zones:
            if b < zone.created_bar:
                continue

            # Check if price entered the zone
            if b_high >= zone.bottom and b_low <= zone.top:
                zone.touches += 1
                if is_recent:
                    zone.recent_touches += 1

            # Check for polarity flip
            if zone.zone_type == ZoneType.SUPPLY and b_close > zone.top:
                zone.zone_type = ZoneType.DEMAND
                zone.flips += 1
                if is_recent:
                    zone.recent_flips += 1
                zone.status = ZoneStatus.TESTED

            elif zone.zone_type == ZoneType.DEMAND and b_close < zone.bottom:
                zone.zone_type = ZoneType.SUPPLY
                zone.flips += 1
                if is_recent:
                    zone.recent_flips += 1
                zone.status = ZoneStatus.TESTED

    return zones


# =============================================================================
# ZONE TRIMMING
# =============================================================================

def _trim_zones(
    supply: List[Zone],
    demand: List[Zone],
    max_per_side: int,
    last_close: float = 0.0,
) -> Tuple[List[Zone], List[Zone]]:
    """
    Keep the most relevant max_per_side zones per type.

    Priority: proximity to current price (closest zones are most actionable).
    """
    if last_close > 0:
        supply_sorted = sorted(supply, key=lambda z: abs(z.bottom - last_close))
        demand_sorted = sorted(demand, key=lambda z: abs(z.top - last_close))
    else:
        supply_sorted = sorted(supply, key=lambda z: z.pivot_bar, reverse=True)
        demand_sorted = sorted(demand, key=lambda z: z.pivot_bar, reverse=True)

    return supply_sorted[:max_per_side], demand_sorted[:max_per_side]


def _dedup_zones(zones: List[Zone]) -> List[Zone]:
    """
    Collapse zones with identical top/bottom bounds into a single zone.
    """
    if len(zones) <= 1:
        return zones

    groups: dict[Tuple[float, float], List[Zone]] = {}
    for z in zones:
        key = (round(z.top, 4), round(z.bottom, 4))
        groups.setdefault(key, []).append(z)

    deduped: List[Zone] = []
    for group in groups.values():
        if len(group) == 1:
            deduped.append(group[0])
        else:
            best = max(group, key=lambda z: z.touches)
            best.flips = max(z.flips for z in group)
            deduped.append(best)

    return deduped


# =============================================================================
# NEAREST ZONE HELPERS
# =============================================================================

def _nearest_supply(zones: List[Zone], price: float) -> Optional[float]:
    """Find the bottom of the nearest supply zone above price."""
    above = [z for z in zones if z.bottom >= price]
    if not above:
        return None
    return min(z.bottom for z in above)


def _nearest_demand(zones: List[Zone], price: float) -> Optional[float]:
    """Find the top of the nearest demand zone below price."""
    below = [z for z in zones if z.top <= price]
    if not below:
        return None
    return max(z.top for z in below)


# =============================================================================
# PUBLIC API
# =============================================================================

def calculate_h4_zones(
    df: pd.DataFrame,
    ticker: str = "",
    d1_atr: Optional[float] = None,
    atr_filter: Optional[float] = None,
) -> H4SupplyDemandResult:
    """
    Calculate H4 supply and demand zones from a DataFrame of 4-hour bars.

    Args:
        df: DataFrame with columns: high, low, close, open
            Must be 4-hour bars sorted chronologically (oldest first).
        ticker: Symbol name for labeling.
        d1_atr: D1 ATR value for zone filtering (from daily bars).
        atr_filter: Multiplier for ATR band filter. Zones outside
                    last_close ± (d1_atr * atr_filter) are discarded.

    Returns:
        H4SupplyDemandResult with active supply and demand zones.
    """
    if df is None or len(df) < LEFT_BARS + RIGHT_BARS + 1:
        return H4SupplyDemandResult(
            ticker=ticker,
            bar_count=0 if df is None else len(df),
            error=f"Insufficient data: need at least {LEFT_BARS + RIGHT_BARS + 1} H4 bars",
        )

    high = df["high"].values.astype(np.float64)
    low = df["low"].values.astype(np.float64)
    close = df["close"].values.astype(np.float64)
    open_ = df["open"].values.astype(np.float64)
    n = len(high)

    # Step 1: Calculate ATR (on raw OHLC)
    atr = _calculate_atr(high, low, close, ATR_LENGTH)

    # Step 2: Dual-pass pivot detection (raw + HA)
    raw_pivot_highs, raw_pivot_lows = _detect_pivots(high, low, LEFT_BARS, RIGHT_BARS)

    ha_high, ha_low = _calculate_ha_bodies(open_, high, low, close)
    ha_pivot_highs, ha_pivot_lows = _detect_pivots(ha_high, ha_low, LEFT_BARS, RIGHT_BARS)

    # Combine pivots from both passes
    raw_high_bars = {bar: price for bar, price in raw_pivot_highs}
    raw_low_bars = {bar: price for bar, price in raw_pivot_lows}

    combined_highs = list(raw_pivot_highs)
    for bar, ha_price in ha_pivot_highs:
        if bar not in raw_high_bars:
            combined_highs.append((bar, ha_price))
        else:
            raw_price = raw_high_bars[bar]
            atr_val = atr[bar] if bar < n else 0.0
            if atr_val > 0:
                hw = min(atr_val * ZONE_WIDTH_MULT, min(raw_price, ha_price) * (MAX_ZONE_PCT / 100.0)) / 2.0
                if abs(raw_price - ha_price) >= 2 * hw:
                    combined_highs.append((bar, ha_price))

    combined_lows = list(raw_pivot_lows)
    for bar, ha_price in ha_pivot_lows:
        if bar not in raw_low_bars:
            combined_lows.append((bar, ha_price))
        else:
            raw_price = raw_low_bars[bar]
            atr_val = atr[bar] if bar < n else 0.0
            if atr_val > 0:
                hw = min(atr_val * ZONE_WIDTH_MULT, min(raw_price, ha_price) * (MAX_ZONE_PCT / 100.0)) / 2.0
                if abs(raw_price - ha_price) >= 2 * hw:
                    combined_lows.append((bar, ha_price))

    logger.debug(
        "H4 S/D [%s]: %d bars, %d raw PH + %d HA PH = %d combined, "
        "%d raw PL + %d HA PL = %d combined",
        ticker, n,
        len(raw_pivot_highs), len(ha_pivot_highs), len(combined_highs),
        len(raw_pivot_lows), len(ha_pivot_lows), len(combined_lows),
    )

    # Step 3: Create zones around each pivot
    all_zones: List[Zone] = []

    for i, (bar_idx, price) in enumerate(combined_highs):
        atr_val = atr[bar_idx] if bar_idx < n else 0.0
        zone = _create_zone(
            f"_S{i}", ZoneType.SUPPLY, bar_idx, price, atr_val, close[bar_idx], RIGHT_BARS,
        )
        if zone:
            all_zones.append(zone)

    for i, (bar_idx, price) in enumerate(combined_lows):
        atr_val = atr[bar_idx] if bar_idx < n else 0.0
        zone = _create_zone(
            f"_D{i}", ZoneType.DEMAND, bar_idx, price, atr_val, close[bar_idx], RIGHT_BARS,
        )
        if zone:
            all_zones.append(zone)

    if not all_zones:
        return H4SupplyDemandResult(
            ticker=ticker,
            bar_count=n,
            last_close=float(close[-1]),
            error="No pivots detected in data range",
        )

    # Step 4: Align overlapping zones (cross-type, Bjorgum-style)
    all_zones = _align_zones(all_zones)

    # Step 4b: Deduplicate zones with identical bounds
    all_zones = _dedup_zones(all_zones)

    # Step 5: Walk forward -- track touches and polarity flips
    earliest_zone_bar = min(z.created_bar for z in all_zones)
    all_zones = _walk_forward_zones(all_zones, close, high, low, earliest_zone_bar)

    # Step 6: ATR filter
    last_close = float(close[-1])
    if atr_filter is not None and d1_atr is not None and d1_atr > 0:
        band = d1_atr * atr_filter
        upper_bound = last_close + band
        lower_bound = last_close - band
        all_zones = [
            z for z in all_zones
            if z.bottom <= upper_bound and z.top >= lower_bound
        ]

    # Step 7: Separate exhausted zones (recent counts)
    exhausted: List[Zone] = []
    active: List[Zone] = []
    for z in all_zones:
        if z.recent_flips >= MAX_FLIPS or z.recent_touches >= MAX_TOUCHES:
            z.status = ZoneStatus.BROKEN
            exhausted.append(z)
        else:
            active.append(z)

    # Step 8: Split active by type and trim
    supply = [z for z in active if z.zone_type == ZoneType.SUPPLY]
    demand = [z for z in active if z.zone_type == ZoneType.DEMAND]
    supply, demand = _trim_zones(supply, demand, MAX_ZONES, last_close)

    # Step 9: Assign final IDs
    supply = sorted(supply, key=lambda z: z.midpoint, reverse=True)
    demand = sorted(demand, key=lambda z: z.midpoint, reverse=True)
    for i, z in enumerate(supply):
        z.zone_id = f"S{i + 1}"
    for i, z in enumerate(demand):
        z.zone_id = f"D{i + 1}"

    exhausted = sorted(exhausted, key=lambda z: z.midpoint, reverse=True)
    for i, z in enumerate(exhausted):
        z.zone_id = f"X{i + 1}"

    return H4SupplyDemandResult(
        ticker=ticker,
        bar_count=n,
        supply_zones=supply,
        demand_zones=demand,
        exhausted_zones=exhausted,
        total_supply=len(supply),
        total_demand=len(demand),
        nearest_supply=_nearest_supply(supply, last_close),
        nearest_demand=_nearest_demand(demand, last_close),
        last_close=last_close,
    )


def calculate_h4_zones_from_bars(
    bars: list,
    ticker: str = "",
    d1_atr: Optional[float] = None,
    atr_filter: Optional[float] = None,
) -> H4SupplyDemandResult:
    """
    Calculate H4 zones from a list of bar dicts/objects.

    Each bar must have: high, low, close, open (as attributes or dict keys).
    """
    if not bars:
        return H4SupplyDemandResult(ticker=ticker, bar_count=0, error="No bars provided")

    def _get(bar, key):
        return bar[key] if isinstance(bar, dict) else getattr(bar, key)

    df = pd.DataFrame({
        "high": [_get(b, "high") for b in bars],
        "low": [_get(b, "low") for b in bars],
        "close": [_get(b, "close") for b in bars],
        "open": [_get(b, "open") for b in bars],
    })

    return calculate_h4_zones(df, ticker, d1_atr=d1_atr, atr_filter=atr_filter)
