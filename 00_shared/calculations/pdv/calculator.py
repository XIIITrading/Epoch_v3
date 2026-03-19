"""
Prior Day Value (PDV) Calculator
=================================
XIII Trading LLC - Epoch Trading System v2.0

Calculates prior day volume profile levels and value alignment.

Concepts:
    - Prior Day POC: Price level with highest volume during prior day's session
    - Value Area: Price range containing 70% of prior day's volume around the POC
    - Value Alignment: Whether current price position relative to the value area
      is aligned with market structure direction

Alignment Logic:
    Bull structure + price above value area = ALIGNED
    Bear structure + price below value area = ALIGNED
    Inside value area + Bull + price >= POC  = ALIGNED
    Inside value area + Bear + price <= POC  = ALIGNED
    Otherwise = NOT ALIGNED

    Inside value area is always 'Inside' (within ATR bands by definition).
    Outside value area:
        Inside:  Distance from VA boundary <= ½ D1 ATR (within ATR bands)
        Outside: Distance from VA boundary >  ½ D1 ATR (beyond ATR bands)
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Optional, Tuple
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

ET_TIMEZONE = ZoneInfo("America/New_York")


# =============================================================================
# DATA MODELS
# =============================================================================

class Alignment(str, Enum):
    """Value alignment classification.

    Inside/Outside refers to whether price is within the D1 ATR bands
    (Price ± D1 ATR) around the value area boundary.
    Inside the value area itself is always classified as 'Inside'.
    """
    ALIGNED_INSIDE = "Aligned (Inside)"
    ALIGNED_OUTSIDE = "Aligned (Outside)"
    NOT_ALIGNED_INSIDE = "Not Aligned (Inside)"
    NOT_ALIGNED_OUTSIDE = "Not Aligned (Outside)"


@dataclass
class PDVResult:
    """Prior Day Value calculation result."""
    ticker: str
    analysis_date: date

    # Prior Day Volume Profile levels
    pd_poc: Optional[float] = None
    pd_vah: Optional[float] = None
    pd_val: Optional[float] = None

    # Current state at 08:00 ET
    price_at_0800: Optional[float] = None
    d1_atr: Optional[float] = None
    d1_atr_high: Optional[float] = None   # price + D1 ATR
    d1_atr_low: Optional[float] = None    # price - D1 ATR

    # Structure direction
    direction: Optional[str] = None  # "Bull" or "Bear" or "Neutral"

    # Alignment
    alignment: Optional[Alignment] = None

    # Metadata
    prior_day_date: Optional[date] = None
    error: Optional[str] = None


# =============================================================================
# CORE CALCULATION
# =============================================================================

def calculate_pdv(
    ticker: str,
    analysis_date: date,
    polygon_client=None,
) -> PDVResult:
    """
    Calculate Prior Day Value alignment for a ticker.

    Steps:
        1. Find the prior trading day
        2. Fetch 5-min bars for the prior day session (04:00 - 20:00 ET)
        3. Build volume profile -> POC, VAH, VAL
        4. Get price at 08:00 ET on analysis_date
        5. Calculate D1 ATR
        6. Get market structure composite direction at 08:00 ET
        7. Determine value alignment

    Args:
        ticker: Stock symbol
        analysis_date: The day to evaluate (price/structure assessed at 08:00 ET)
        polygon_client: Optional 01_application PolygonClient instance.
                       If None, will be created internally.

    Returns:
        PDVResult with all calculated fields
    """
    ticker = ticker.upper()
    result = PDVResult(ticker=ticker, analysis_date=analysis_date)

    # -------------------------------------------------------------------------
    # 0. Setup client
    # -------------------------------------------------------------------------
    client = polygon_client or _get_default_client()
    if client is None:
        result.error = "Could not initialize Polygon client"
        return result

    # -------------------------------------------------------------------------
    # 1. Find prior trading day
    # -------------------------------------------------------------------------
    prior_date = _find_prior_trading_day(client, ticker, analysis_date)
    if prior_date is None:
        result.error = "Could not find prior trading day"
        return result
    result.prior_day_date = prior_date

    # -------------------------------------------------------------------------
    # 2-3. Calculate Prior Day Volume Profile (POC, VAH, VAL)
    # -------------------------------------------------------------------------
    poc, vah, val = _calculate_prior_day_vp(client, ticker, prior_date)
    result.pd_poc = poc
    result.pd_vah = vah
    result.pd_val = val

    if poc is None:
        result.error = "Could not calculate prior day volume profile"
        return result

    # -------------------------------------------------------------------------
    # 4. Get price at 08:00 ET on analysis_date
    # -------------------------------------------------------------------------
    end_ts_0800 = datetime(
        analysis_date.year, analysis_date.month, analysis_date.day,
        8, 0, 0, tzinfo=ET_TIMEZONE
    )
    price = _get_price_at_time(client, ticker, end_ts_0800)
    result.price_at_0800 = price

    if price is None:
        result.error = "Could not get price at 08:00 ET"
        return result

    # -------------------------------------------------------------------------
    # 5. Calculate D1 ATR
    # -------------------------------------------------------------------------
    d1_atr = _calculate_d1_atr(client, ticker, analysis_date)
    result.d1_atr = d1_atr

    if d1_atr is not None and poc is not None:
        result.d1_atr_high = round(poc + d1_atr, 2)
        result.d1_atr_low = round(poc - d1_atr, 2)

    # -------------------------------------------------------------------------
    # 6. Get market structure direction at 08:00 ET
    # -------------------------------------------------------------------------
    direction = _get_structure_direction(client, ticker, analysis_date, end_ts_0800)
    result.direction = direction

    # -------------------------------------------------------------------------
    # 7. Determine value alignment
    # -------------------------------------------------------------------------
    if all(v is not None for v in [price, poc, vah, val, d1_atr, direction]):
        result.alignment = _determine_alignment(
            price=price,
            poc=poc,
            vah=vah,
            val=val,
            d1_atr=d1_atr,
            direction=direction,
        )

    return result


# =============================================================================
# PRIOR DAY VOLUME PROFILE
# =============================================================================

def _calculate_prior_day_vp(
    client, ticker: str, prior_date: date
) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """
    Calculate prior day POC, VAH, VAL using the Leviathan methodology.

    Uses 5-minute bars from 04:00-20:00 ET (full extended session) and
    the shared volume profile core functions.

    Returns:
        (poc, vah, val) or (None, None, None) on failure
    """
    from shared.indicators.core.volume_profile import (
        _build_profile_core,
        _find_poc_index,
        _calculate_poc_price,
        _calculate_value_area,
    )
    from shared.indicators.config import CONFIG as SHARED_CONFIG

    # Fetch 5-min bars for prior day
    df = client.fetch_minute_bars(ticker, prior_date, prior_date, multiplier=5)

    if df is None or df.empty:
        logger.warning(f"No 5-min bars for {ticker} on {prior_date}")
        return None, None, None

    # Ensure timestamp column is timezone-aware
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    if df['timestamp'].dt.tz is None:
        df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')

    # Filter to extended session: 04:00 - 20:00 ET = 09:00 - 01:00 UTC (EST)
    # Use 08:00 - 01:00 UTC to cover DST variations safely
    # More reliable: convert to ET and filter directly
    df['et_time'] = df['timestamp'].dt.tz_convert(ET_TIMEZONE)
    df['et_hour'] = df['et_time'].dt.hour

    # 04:00 - 20:00 ET
    df_session = df[(df['et_hour'] >= 4) & (df['et_hour'] < 20)]

    if df_session.empty or len(df_session) < 5:
        logger.warning(f"Insufficient session bars for {ticker} on {prior_date}")
        return None, None, None

    # Build volume profile using shared library
    vp_cfg = SHARED_CONFIG.volume_profile
    resolution = vp_cfg.resolution      # 30 zones
    va_pct = vp_cfg.value_area_pct      # 70%

    opens = df_session['open'].values.astype(np.float64)
    highs = df_session['high'].values.astype(np.float64)
    lows = df_session['low'].values.astype(np.float64)
    closes = df_session['close'].values.astype(np.float64)
    volumes = df_session['volume'].values.astype(np.float64)

    zone_tops, buy_prof, sell_prof, s_high, s_low, gap = _build_profile_core(
        opens, highs, lows, closes, volumes, resolution
    )

    if gap <= 0:
        logger.warning(f"Flat session for {ticker} on {prior_date}")
        return None, None, None

    poc_idx = _find_poc_index(buy_prof, sell_prof)
    poc = _calculate_poc_price(zone_tops, poc_idx, gap)
    val, vah = _calculate_value_area(
        buy_prof, sell_prof, zone_tops, gap, poc_idx, va_pct
    )

    logger.info(
        f"PD VP for {ticker} ({prior_date}): "
        f"POC=${poc:.2f}, VAH=${vah:.2f}, VAL=${val:.2f}"
    )

    return round(poc, 2), round(vah, 2), round(val, 2)


# =============================================================================
# PRICE AT TIME
# =============================================================================

def _get_price_at_time(
    client, ticker: str, end_timestamp: datetime
) -> Optional[float]:
    """
    Get the closing price of the last available bar before end_timestamp.

    For 08:00 ET this will typically be a pre-market bar.
    Uses 5-min bars from overnight + pre-market session.
    """
    start_date = end_timestamp.date() - timedelta(days=1)

    # Fetch 5-min bars up to the timestamp
    df = client.fetch_minute_bars(
        ticker, start_date, multiplier=5,
        end_timestamp=end_timestamp
    )

    if df is None or df.empty:
        # Fallback: try hourly bars
        df = client.fetch_hourly_bars(
            ticker, start_date,
            end_timestamp=end_timestamp
        )

    if df is None or df.empty:
        logger.warning(f"No price data for {ticker} at {end_timestamp}")
        return None

    return round(float(df.iloc[-1]['close']), 2)


# =============================================================================
# D1 ATR
# =============================================================================

def _calculate_d1_atr(
    client, ticker: str, analysis_date: date, period: int = 14
) -> Optional[float]:
    """
    Calculate D1 ATR (14-period SMA of true range).

    Fetches daily bars for the lookback period and calculates ATR.
    """
    lookback_days = period * 2 + 10  # Extra buffer for weekends/holidays
    start_date = analysis_date - timedelta(days=lookback_days)

    df = client.fetch_daily_bars(ticker, start_date, analysis_date)

    if df is None or df.empty or len(df) < period + 1:
        logger.warning(f"Insufficient daily bars for {ticker} D1 ATR")
        return None

    # Calculate true range
    highs = df['high'].values
    lows = df['low'].values
    closes = df['close'].values

    tr = np.zeros(len(df))
    tr[0] = highs[0] - lows[0]
    for i in range(1, len(df)):
        tr[i] = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1])
        )

    # SMA of last `period` true ranges
    atr = float(np.mean(tr[-period:]))
    return round(atr, 4)


# =============================================================================
# MARKET STRUCTURE DIRECTION
# =============================================================================

def _get_structure_direction(
    client, ticker: str, analysis_date: date, end_timestamp: datetime
) -> Optional[str]:
    """
    Get composite market structure direction at the given timestamp.

    Uses the 01_application MarketStructureCalculator with end_timestamp
    to get the direction as of 08:00 ET.

    Returns:
        "Bull", "Bear", or "Neutral"
    """
    try:
        # Import from 01_application calculators
        from calculators.market_structure import MarketStructureCalculator

        calc = MarketStructureCalculator()
        structure = calc.calculate(
            ticker=ticker,
            analysis_date=analysis_date,
            end_timestamp=end_timestamp,
        )

        composite = structure.composite.value  # e.g. "Bull+", "Bull", "Bear", etc.

        # Simplify to Bull/Bear/Neutral
        if "Bull" in composite:
            return "Bull"
        elif "Bear" in composite:
            return "Bear"
        else:
            return "Neutral"

    except Exception as e:
        logger.warning(f"Market structure calculation failed for {ticker}: {e}")
        return None


# =============================================================================
# ALIGNMENT LOGIC
# =============================================================================

def _determine_alignment(
    price: float,
    poc: float,
    vah: float,
    val: float,
    d1_atr: float,
    direction: str,
) -> Alignment:
    """
    Determine value alignment.

    Logic:
        1. Price ABOVE value area (price > VAH):
           -> Bull direction = ALIGNED
           -> Bear direction = NOT ALIGNED

        2. Price BELOW value area (price < VAL):
           -> Bear direction = ALIGNED
           -> Bull direction = NOT ALIGNED

        3. Price INSIDE value area (VAL <= price <= VAH):
           -> Bull + price >= POC = ALIGNED (Optimal)
           -> Bear + price <= POC = ALIGNED (Optimal)
           -> Bull + price <  POC = NOT ALIGNED (Optimal)
           -> Bear + price >  POC = NOT ALIGNED (Optimal)
           -> Inside VA is always 'Inside' (within ATR bands)

        4. Inside vs Outside ATR bands (outside VA only):
           - Distance from VA boundary <= ½ D1 ATR: Inside (within ATR bands)
           - Distance from VA boundary >  ½ D1 ATR: Outside (beyond ATR bands)

    Args:
        price: Current price at 08:00 ET
        poc: Prior day Point of Control
        vah: Prior day Value Area High
        val: Prior day Value Area Low
        d1_atr: Daily ATR
        direction: "Bull", "Bear", or "Neutral"
    """
    # Determine position relative to value area
    if price > vah:
        position = "above"
        distance_from_va = price - vah
    elif price < val:
        position = "below"
        distance_from_va = val - price
    else:
        # Inside value area — alignment depends on price vs POC
        position = "inside"
        distance_from_va = 0.0

    # Inside value area: check price relative to POC
    if position == "inside":
        if direction == "Bull":
            is_aligned = price >= poc
        elif direction == "Bear":
            is_aligned = price <= poc
        else:
            is_aligned = False

        if is_aligned:
            return Alignment.ALIGNED_INSIDE
        else:
            return Alignment.NOT_ALIGNED_INSIDE

    # Outside value area: check direction vs position
    half_atr = d1_atr / 2.0
    is_extended = distance_from_va > half_atr

    if direction == "Bull":
        is_aligned = position == "above"
    elif direction == "Bear":
        is_aligned = position == "below"
    else:
        # Neutral direction — treat as not aligned
        is_aligned = False

    if is_aligned and not is_extended:
        return Alignment.ALIGNED_INSIDE
    elif is_aligned and is_extended:
        return Alignment.ALIGNED_OUTSIDE
    elif not is_aligned and not is_extended:
        return Alignment.NOT_ALIGNED_INSIDE
    else:
        return Alignment.NOT_ALIGNED_OUTSIDE


# =============================================================================
# HELPERS
# =============================================================================

def _find_prior_trading_day(
    client, ticker: str, reference_date: date
) -> Optional[date]:
    """Find the most recent trading day before reference_date."""
    for i in range(1, 10):
        check_date = reference_date - timedelta(days=i)

        # Skip weekends
        if check_date.weekday() >= 5:
            continue

        df = client.fetch_daily_bars(ticker, check_date, check_date)
        if df is not None and not df.empty:
            return check_date

    return None


def _get_default_client():
    """Create a default Polygon client from 01_application."""
    try:
        from data import get_polygon_client
        return get_polygon_client()
    except ImportError:
        logger.error("Could not import 01_application data module")
        return None
