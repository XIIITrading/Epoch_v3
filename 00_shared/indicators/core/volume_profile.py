"""
================================================================================
EPOCH TRADING SYSTEM - VOLUME PROFILE (Canonical)
Session-Based Volume Profile with POC / VAH / VAL
XIII Trading LLC
================================================================================

Calculates volume distribution across price levels within a session.

Core algorithm (Leviathan / LonesomeTheBlue methodology):
  1. Divide session price range into N zones (resolution)
  2. For each bar, distribute volume across overlapping zones:
     - Body volume proportional to body overlap
     - Wick volume proportional to wick overlap (split buy/sell equally)
     - Green (close >= open) body -> buy volume; Red body -> sell volume
  3. POC = midpoint of zone with highest total volume
  4. Value Area = expand from POC zone until VA% of total volume captured

Usage:
    from shared.indicators.core.volume_profile import (
        volume_profile_df,
        calculate_volume_profile,
        calculate_session_targets,
    )

================================================================================
"""

import numpy as np
import pandas as pd
from typing import List, Optional, Any, Tuple

from ..config import CONFIG
from ..types import VolumeProfileResult, SessionTargets
from .._utils import get_open, get_high, get_low, get_close, get_volume, bars_to_arrays


# =============================================================================
# NUMPY CORE
# =============================================================================

def _zone_overlap_volume(
    zone_bot: float,
    zone_top: float,
    range_bot: float,
    range_top: float,
    range_height: float,
    vol: float,
) -> float:
    """
    Calculate volume allocated to a zone from a bar's price range segment.

    Matches Pine Script get_vol():
        overlap = max(min(max(y11,y12), max(y21,y22)) - max(min(y11,y12), min(y21,y22)), 0)
        result = overlap * vol / height

    Args:
        zone_bot, zone_top: zone price boundaries
        range_bot, range_top: bar segment boundaries (body or wick)
        range_height: total height of the bar segment
        vol: volume to distribute from this segment

    Returns:
        Volume allocated to this zone
    """
    if range_height <= 0 or vol <= 0:
        return 0.0
    overlap = max(min(zone_top, range_top) - max(zone_bot, range_bot), 0.0)
    return overlap * vol / range_height


def _distribute_bar_volume(
    open_price: float,
    high: float,
    low: float,
    close: float,
    volume: float,
    zone_tops: np.ndarray,
    gap: float,
    buy_profile: np.ndarray,
    sell_profile: np.ndarray,
) -> None:
    """
    Distribute a single bar's volume across profile zones (in-place).

    Matches Pine Script profileAdd() logic:
    - Candle body, top wick, bottom wick each get proportional volume
    - Green bar body -> buy; Red bar body -> sell
    - Wicks split 50/50 between buy and sell

    Args:
        open_price, high, low, close, volume: bar OHLCV
        zone_tops: array of zone upper boundaries
        gap: zone height (session_range / resolution)
        buy_profile: buy volume array to update (mutated in-place)
        sell_profile: sell volume array to update (mutated in-place)
    """
    if volume <= 0 or high == low:
        return

    body_top = max(close, open_price)
    body_bot = min(close, open_price)
    is_green = close >= open_price

    top_wick = high - body_top
    bottom_wick = body_bot - low
    body = body_top - body_bot

    denominator = 2.0 * top_wick + 2.0 * bottom_wick + body
    if denominator <= 0:
        return

    body_vol = body * volume / denominator
    top_wick_vol = 2.0 * top_wick * volume / denominator
    bottom_wick_vol = 2.0 * bottom_wick * volume / denominator

    n_zones = len(zone_tops)
    for i in range(n_zones):
        zone_top = zone_tops[i]
        zone_bot = zone_top - gap

        # Body volume -> buy if green, sell if red
        bv = _zone_overlap_volume(zone_bot, zone_top, body_bot, body_top, body, body_vol)
        if is_green:
            buy_profile[i] += bv
        else:
            sell_profile[i] += bv

        # Wick volume -> split 50/50
        tw = _zone_overlap_volume(zone_bot, zone_top, body_top, high, top_wick, top_wick_vol)
        bw = _zone_overlap_volume(zone_bot, zone_top, low, body_bot, bottom_wick, bottom_wick_vol)
        buy_profile[i] += (tw + bw) / 2.0
        sell_profile[i] += (tw + bw) / 2.0


def _build_profile_core(
    open_arr: np.ndarray,
    high_arr: np.ndarray,
    low_arr: np.ndarray,
    close_arr: np.ndarray,
    volume_arr: np.ndarray,
    resolution: int,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, float, float, float]:
    """
    Build a volume profile from OHLCV arrays.

    Args:
        open_arr, high_arr, low_arr, close_arr, volume_arr: numpy arrays
        resolution: number of price zones

    Returns:
        (zone_tops, buy_profile, sell_profile, session_high, session_low, gap)
    """
    session_high = float(np.max(high_arr))
    session_low = float(np.min(low_arr))

    price_range = session_high - session_low
    if price_range <= 0:
        # Flat session - return degenerate profile
        zone_tops = np.full(resolution, session_high)
        return zone_tops, np.zeros(resolution), np.zeros(resolution), session_high, session_low, 0.0

    gap = price_range / resolution
    zone_tops = np.array([session_high - gap * i for i in range(resolution)])

    buy_profile = np.zeros(resolution, dtype=np.float64)
    sell_profile = np.zeros(resolution, dtype=np.float64)

    for j in range(len(open_arr)):
        _distribute_bar_volume(
            open_arr[j], high_arr[j], low_arr[j], close_arr[j], volume_arr[j],
            zone_tops, gap, buy_profile, sell_profile,
        )

    return zone_tops, buy_profile, sell_profile, session_high, session_low, gap


def _find_poc_index(buy_profile: np.ndarray, sell_profile: np.ndarray) -> int:
    """Find the zone index with highest total volume."""
    total = buy_profile + sell_profile
    return int(np.argmax(total))


def _calculate_poc_price(zone_tops: np.ndarray, poc_index: int, gap: float) -> float:
    """Calculate POC price as midpoint of the highest-volume zone."""
    if gap <= 0:
        return float(zone_tops[0]) if len(zone_tops) > 0 else 0.0
    return float(zone_tops[poc_index] - gap / 2.0)


def _calculate_value_area(
    buy_profile: np.ndarray,
    sell_profile: np.ndarray,
    zone_tops: np.ndarray,
    gap: float,
    poc_index: int,
    va_pct: int,
) -> Tuple[float, float]:
    """
    Calculate VAH and VAL by expanding from POC zone.

    Matches Pine Script valueLevels() logic:
    - Start at POC zone
    - Expand outward (above and below) adding adjacent zones
    - Stop when cumulative volume >= va_pct% of total

    Returns:
        (val, vah) price levels
    """
    total_profile = buy_profile + sell_profile
    total_volume = float(np.sum(total_profile))

    if total_volume <= 0:
        return float(zone_tops[-1] - gap) if len(zone_tops) > 0 else 0.0, float(zone_tops[0]) if len(zone_tops) > 0 else 0.0

    n = len(total_profile)
    threshold = total_volume * (va_pct / 100.0)

    vol_count = total_profile[poc_index]
    vah = float(zone_tops[poc_index])
    val = float(zone_tops[poc_index] - gap)

    for i in range(1, n):
        if vol_count >= threshold:
            break

        # Add zone above POC
        above_idx = poc_index - i
        if 0 <= above_idx < n:
            vol_count += total_profile[above_idx]
            if vol_count < threshold:
                vah = float(zone_tops[above_idx])

        if vol_count >= threshold:
            break

        # Add zone below POC
        below_idx = poc_index + i
        if 0 <= below_idx < n:
            vol_count += total_profile[below_idx]
            if vol_count < threshold:
                val = float(zone_tops[below_idx] - gap)

    return val, vah


# =============================================================================
# DATAFRAME WRAPPER
# =============================================================================

def volume_profile_df(
    df: pd.DataFrame,
    date_col: str = "bar_date",
    open_col: str = "open",
    high_col: str = "high",
    low_col: str = "low",
    close_col: str = "close",
    volume_col: str = "volume",
    resolution: Optional[int] = None,
    va_pct: Optional[int] = None,
) -> pd.DataFrame:
    """
    Calculate per-session volume profile levels for a DataFrame.

    Groups bars by date_col and computes POC/VAH/VAL for each session.

    Args:
        df: DataFrame with OHLCV data and a date grouping column
        date_col: column to group sessions by (e.g., 'bar_date')
        resolution: number of price zones (default from config)
        va_pct: value area percentage (default from config)

    Returns:
        DataFrame with columns: date, poc, vah, val, total_volume
    """
    cfg = CONFIG.volume_profile
    resolution = resolution or cfg.resolution
    va_pct = va_pct or cfg.value_area_pct
    min_bars = cfg.min_bars

    if date_col not in df.columns:
        # Try timestamp
        if "timestamp" in df.columns:
            df = df.copy()
            df["_session_date"] = pd.to_datetime(df["timestamp"]).dt.date
            date_col = "_session_date"
        else:
            raise ValueError(f"Column '{date_col}' not found. Need a date column to group sessions.")

    results = []
    for session_date, group in df.groupby(date_col):
        if len(group) < min_bars:
            continue

        o = group[open_col].values.astype(np.float64)
        h = group[high_col].values.astype(np.float64)
        l = group[low_col].values.astype(np.float64)
        c = group[close_col].values.astype(np.float64)
        v = group[volume_col].values.astype(np.float64)

        zone_tops, buy_prof, sell_prof, s_high, s_low, gap = _build_profile_core(o, h, l, c, v, resolution)

        if gap <= 0:
            continue

        poc_idx = _find_poc_index(buy_prof, sell_prof)
        poc = _calculate_poc_price(zone_tops, poc_idx, gap)
        val, vah = _calculate_value_area(buy_prof, sell_prof, zone_tops, gap, poc_idx, va_pct)

        results.append({
            "date": session_date,
            "poc": poc,
            "vah": vah,
            "val": val,
            "session_high": s_high,
            "session_low": s_low,
            "total_volume": float(np.sum(buy_prof) + np.sum(sell_prof)),
            "buy_volume": float(np.sum(buy_prof)),
            "sell_volume": float(np.sum(sell_prof)),
        })

    return pd.DataFrame(results)


def prior_day_levels_df(
    df: pd.DataFrame,
    date_col: str = "bar_date",
    open_col: str = "open",
    high_col: str = "high",
    low_col: str = "low",
    close_col: str = "close",
    volume_col: str = "volume",
    resolution: Optional[int] = None,
    va_pct: Optional[int] = None,
) -> pd.DataFrame:
    """
    Add prior-day POC/VAH/VAL columns to a bar DataFrame.

    For each bar, looks up the previous session's volume profile levels.
    This is the primary function for target integration.

    Args:
        df: DataFrame with OHLCV data and date column
        resolution: number of price zones
        va_pct: value area percentage

    Returns:
        DataFrame with added columns: pd_poc, pd_vah, pd_val
    """
    profiles = volume_profile_df(
        df, date_col=date_col, open_col=open_col, high_col=high_col,
        low_col=low_col, close_col=close_col, volume_col=volume_col,
        resolution=resolution, va_pct=va_pct,
    )

    if profiles.empty:
        df = df.copy()
        df["pd_poc"] = np.nan
        df["pd_vah"] = np.nan
        df["pd_val"] = np.nan
        return df

    # Create a lookup: for each date, the prior session's levels
    profiles = profiles.sort_values("date").reset_index(drop=True)
    prior_lookup = {}
    for i in range(1, len(profiles)):
        current_date = profiles.iloc[i]["date"]
        prior_row = profiles.iloc[i - 1]
        prior_lookup[current_date] = {
            "pd_poc": prior_row["poc"],
            "pd_vah": prior_row["vah"],
            "pd_val": prior_row["val"],
        }

    # Determine the date column to use for lookup
    df = df.copy()
    if date_col not in df.columns and "timestamp" in df.columns:
        df["_lookup_date"] = pd.to_datetime(df["timestamp"]).dt.date
        lookup_col = "_lookup_date"
    else:
        lookup_col = date_col

    df["pd_poc"] = df[lookup_col].map(lambda d: prior_lookup.get(d, {}).get("pd_poc", np.nan))
    df["pd_vah"] = df[lookup_col].map(lambda d: prior_lookup.get(d, {}).get("pd_vah", np.nan))
    df["pd_val"] = df[lookup_col].map(lambda d: prior_lookup.get(d, {}).get("pd_val", np.nan))

    if "_lookup_date" in df.columns:
        df.drop(columns=["_lookup_date"], inplace=True)

    return df


# =============================================================================
# BAR-LIST WRAPPER
# =============================================================================

def calculate_volume_profile(
    bars: List[Any],
    resolution: Optional[int] = None,
    va_pct: Optional[int] = None,
) -> Optional[VolumeProfileResult]:
    """
    Calculate volume profile for a list of bars (single session).

    Args:
        bars: List of bar dicts/objects with OHLCV data
        resolution: number of price zones (default from config)
        va_pct: value area percentage (default from config)

    Returns:
        VolumeProfileResult or None if insufficient data
    """
    cfg = CONFIG.volume_profile
    resolution = resolution or cfg.resolution
    va_pct = va_pct or cfg.value_area_pct

    if not bars or len(bars) < cfg.min_bars:
        return None

    opens, highs, lows, closes, volumes = bars_to_arrays(bars)

    zone_tops, buy_prof, sell_prof, s_high, s_low, gap = _build_profile_core(
        opens, highs, lows, closes, volumes, resolution,
    )

    if gap <= 0:
        return None

    poc_idx = _find_poc_index(buy_prof, sell_prof)
    poc = _calculate_poc_price(zone_tops, poc_idx, gap)
    val, vah = _calculate_value_area(buy_prof, sell_prof, zone_tops, gap, poc_idx, va_pct)

    # Build profile list: (zone_mid_price, buy_vol, sell_vol)
    profile = []
    for i in range(len(zone_tops)):
        mid = zone_tops[i] - gap / 2.0
        profile.append((float(mid), float(buy_prof[i]), float(sell_prof[i])))

    return VolumeProfileResult(
        poc=poc,
        vah=vah,
        val=val,
        total_volume=float(np.sum(buy_prof) + np.sum(sell_prof)),
        buy_volume=float(np.sum(buy_prof)),
        sell_volume=float(np.sum(sell_prof)),
        session_high=s_high,
        session_low=s_low,
        resolution=resolution,
        profile=profile,
    )


def calculate_session_targets(
    prior_session_bars: List[Any],
    current_session_bars: Optional[List[Any]] = None,
    resolution: Optional[int] = None,
    va_pct: Optional[int] = None,
) -> SessionTargets:
    """
    Calculate prior and current session target levels.

    Args:
        prior_session_bars: Bars from the previous session
        current_session_bars: Bars from the current session (optional)
        resolution: number of price zones
        va_pct: value area percentage

    Returns:
        SessionTargets with prior_day and current session levels
    """
    targets = SessionTargets()

    prior = calculate_volume_profile(prior_session_bars, resolution, va_pct)
    if prior is not None:
        targets.prior_day_poc = prior.poc
        targets.prior_day_vah = prior.vah
        targets.prior_day_val = prior.val

    if current_session_bars:
        current = calculate_volume_profile(current_session_bars, resolution, va_pct)
        if current is not None:
            targets.current_poc = current.poc
            targets.current_vah = current.vah
            targets.current_val = current.val

    return targets
