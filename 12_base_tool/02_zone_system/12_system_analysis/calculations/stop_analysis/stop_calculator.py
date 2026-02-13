"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Calculation: Stop Price Calculator (CALC-009)
XIII Trading LLC
================================================================================

PURPOSE:
    Calculate stop prices for all 6 stop types analyzed in CALC-009.

STOP TYPES:
    1. Zone Boundary + 5% Buffer - Stop beyond zone with buffer
    2. Prior M1 Bar High/Low - Tightest structural stop
    3. Prior M5 Bar High/Low - Short-term structure stop
    4. M5 ATR (1.1x) - Volatility-normalized, close-based
    5. M15 ATR (1.1x) - Wider volatility stop, close-based
    6. M5 Fractal High/Low - Market structure swing stop

================================================================================
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import time as dt_time, datetime as dt_datetime, timedelta as dt_timedelta

from .atr_calculator import calculate_atr_m5, calculate_atr_m15
from .fractal_detector import calculate_fractal_stop_price


def _safe_float(value, default: float = 0.0) -> float:
    """Safely convert value to float, handling Decimal types."""
    if value is None:
        return default
    try:
        if isinstance(value, Decimal):
            return float(value)
        return float(value)
    except (ValueError, TypeError):
        return default


def _time_to_minutes(time_val) -> Optional[float]:
    """Convert a time value to minutes from midnight."""
    if time_val is None:
        return None

    try:
        if isinstance(time_val, dt_timedelta):
            return time_val.total_seconds() / 60

        if isinstance(time_val, dt_time):
            return time_val.hour * 60 + time_val.minute + time_val.second / 60

        if isinstance(time_val, dt_datetime):
            return time_val.hour * 60 + time_val.minute + time_val.second / 60

        if hasattr(time_val, 'hour') and hasattr(time_val, 'minute'):
            return time_val.hour * 60 + time_val.minute + (time_val.second if hasattr(time_val, 'second') else 0) / 60

        if isinstance(time_val, str):
            # Parse HH:MM:SS format
            parts = time_val.split(':')
            if len(parts) >= 2:
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = int(parts[2]) if len(parts) > 2 else 0
                return hours * 60 + minutes + seconds / 60

        return None
    except Exception:
        return None


def calculate_zone_buffer_stop(
    entry_price: float,
    zone_low: float,
    zone_high: float,
    direction: str,
    buffer_pct: float = 0.05
) -> Optional[float]:
    """
    Stop Type 1: Zone boundary + 5% buffer.

    Stop placed just beyond the opposite side of the entry zone,
    with a buffer of 5% of the zone distance to avoid wick-outs.

    LONG:  stop = zone_low - (zone_distance * buffer_pct)
           where zone_distance = entry_price - zone_low
    SHORT: stop = zone_high + (zone_distance * buffer_pct)
           where zone_distance = zone_high - entry_price

    Parameters:
    -----------
    entry_price : float
        Trade entry price
    zone_low : float
        Lower boundary of entry zone
    zone_high : float
        Upper boundary of entry zone
    direction : str
        Trade direction ('LONG' or 'SHORT')
    buffer_pct : float
        Buffer percentage of zone distance (default 5%)

    Returns:
    --------
    float or None
        Stop price, or None if calculation fails
    """
    entry_price = _safe_float(entry_price)
    zone_low = _safe_float(zone_low)
    zone_high = _safe_float(zone_high)

    if entry_price <= 0 or zone_low <= 0 or zone_high <= 0:
        return None

    if zone_high <= zone_low:
        return None

    is_long = direction.upper() == 'LONG'

    if is_long:
        # LONG: Stop below zone_low with buffer based on zone distance
        zone_distance = entry_price - zone_low
        buffer = zone_distance * buffer_pct
        stop_price = zone_low - buffer
    else:
        # SHORT: Stop above zone_high with buffer based on zone distance
        zone_distance = zone_high - entry_price
        buffer = zone_distance * buffer_pct
        stop_price = zone_high + buffer

    return stop_price


def calculate_prior_m1_stop(
    m1_bars: List[Dict[str, Any]],
    entry_time,
    direction: str
) -> Optional[float]:
    """
    Stop Type 2: Prior M1 bar high/low.

    Stop at the high/low of the M1 candle immediately before entry.
    This is the tightest structural stop.

    Parameters:
    -----------
    m1_bars : List[Dict[str, Any]]
        List of M1 bar records with 'bar_time', 'high', 'low'
    entry_time : various
        Time of trade entry
    direction : str
        Trade direction ('LONG' or 'SHORT')

    Returns:
    --------
    float or None
        Stop price, or None if no prior bar found
    """
    if not m1_bars:
        return None

    entry_minutes = _time_to_minutes(entry_time)
    if entry_minutes is None:
        return None

    # Find bars before entry
    prior_bars = []
    for bar in m1_bars:
        bar_minutes = _time_to_minutes(bar.get('bar_time'))
        if bar_minutes is not None and bar_minutes < entry_minutes:
            prior_bars.append((bar_minutes, bar))

    if not prior_bars:
        return None

    # Get the most recent bar before entry
    prior_bars.sort(key=lambda x: x[0], reverse=True)
    prior_bar = prior_bars[0][1]

    is_long = direction.upper() == 'LONG'

    if is_long:
        return _safe_float(prior_bar.get('low'))
    else:
        return _safe_float(prior_bar.get('high'))


def calculate_prior_m5_stop(
    m5_bars: List[Dict[str, Any]],
    direction: str
) -> Optional[float]:
    """
    Stop Type 3: Prior M5 bar high/low.

    Stop at the high/low of the last completed M5 bar before entry.
    Uses bars_from_entry = -1.

    Parameters:
    -----------
    m5_bars : List[Dict[str, Any]]
        List of M5 bar records with 'bars_from_entry', 'high', 'low'
    direction : str
        Trade direction ('LONG' or 'SHORT')

    Returns:
    --------
    float or None
        Stop price, or None if no prior bar found
    """
    if not m5_bars:
        return None

    # Find bar with bars_from_entry = -1
    prior_bar = None
    for bar in m5_bars:
        if bar.get('bars_from_entry') == -1:
            prior_bar = bar
            break

    if prior_bar is None:
        return None

    is_long = direction.upper() == 'LONG'

    if is_long:
        return _safe_float(prior_bar.get('low'))
    else:
        return _safe_float(prior_bar.get('high'))


def calculate_m5_atr_stop(
    m5_bars: List[Dict[str, Any]],
    entry_price: float,
    direction: str,
    multiplier: float = 1.1,
    atr_period: int = 14
) -> Optional[float]:
    """
    Stop Type 4: M5 ATR-based stop (1.1x multiplier).

    Volatility-normalized stop using 14-period ATR on M5 bars.
    Close-based trigger - only exits if candle CLOSES beyond level.

    Parameters:
    -----------
    m5_bars : List[Dict[str, Any]]
        List of M5 bar records
    entry_price : float
        Trade entry price
    direction : str
        Trade direction ('LONG' or 'SHORT')
    multiplier : float
        ATR multiplier (default 1.1)
    atr_period : int
        ATR period (default 14)

    Returns:
    --------
    float or None
        Stop price, or None if ATR calculation fails
    """
    entry_price = _safe_float(entry_price)
    if entry_price <= 0:
        return None

    atr = calculate_atr_m5(m5_bars, period=atr_period)
    if atr is None or atr <= 0:
        return None

    is_long = direction.upper() == 'LONG'

    if is_long:
        stop_price = entry_price - (atr * multiplier)
    else:
        stop_price = entry_price + (atr * multiplier)

    return stop_price


def calculate_m15_atr_stop(
    m5_bars: List[Dict[str, Any]],
    entry_price: float,
    direction: str,
    multiplier: float = 1.1,
    atr_period: int = 14
) -> Optional[float]:
    """
    Stop Type 5: M15 ATR-based stop (1.1x multiplier).

    Wider volatility stop using M15 timeframe ATR.
    Close-based trigger - check at M15 boundaries.

    Parameters:
    -----------
    m5_bars : List[Dict[str, Any]]
        List of M5 bar records (will be aggregated to M15)
    entry_price : float
        Trade entry price
    direction : str
        Trade direction ('LONG' or 'SHORT')
    multiplier : float
        ATR multiplier (default 1.1)
    atr_period : int
        ATR period (default 14)

    Returns:
    --------
    float or None
        Stop price, or None if ATR calculation fails
    """
    entry_price = _safe_float(entry_price)
    if entry_price <= 0:
        return None

    atr = calculate_atr_m15(m5_bars, period=atr_period)
    if atr is None or atr <= 0:
        return None

    is_long = direction.upper() == 'LONG'

    if is_long:
        stop_price = entry_price - (atr * multiplier)
    else:
        stop_price = entry_price + (atr * multiplier)

    return stop_price


def calculate_fractal_stop(
    m5_bars: List[Dict[str, Any]],
    direction: str,
    fractal_length: int = 2
) -> Optional[float]:
    """
    Stop Type 6: M5 fractal high/low (market structure).

    Stop beyond the most recent confirmed swing high/low.
    Breaking this level means potential trend change.

    Parameters:
    -----------
    m5_bars : List[Dict[str, Any]]
        List of M5 bar records
    direction : str
        Trade direction ('LONG' or 'SHORT')
    fractal_length : int
        Bars on each side for fractal detection (default 2)

    Returns:
    --------
    float or None
        Stop price at fractal level, or None if no fractal found
    """
    return calculate_fractal_stop_price(m5_bars, direction, fractal_length)


def calculate_all_stop_prices(
    trade: Dict[str, Any],
    m1_bars: List[Dict[str, Any]],
    m5_bars: List[Dict[str, Any]]
) -> Dict[str, Optional[float]]:
    """
    Calculate all 6 stop prices for a single trade.

    Parameters:
    -----------
    trade : Dict[str, Any]
        Trade record with:
        - entry_price: Trade entry price
        - direction: 'LONG' or 'SHORT'
        - entry_time: Time of entry
        - zone_low: Lower zone boundary
        - zone_high: Upper zone boundary
    m1_bars : List[Dict[str, Any]]
        M1 bar data for this trade's ticker/date
    m5_bars : List[Dict[str, Any]]
        M5 trade bars for this trade

    Returns:
    --------
    Dict[str, Optional[float]]
        Dictionary with stop prices for each type:
        - zone_buffer: Zone + 5% buffer stop
        - prior_m1: Prior M1 bar stop
        - prior_m5: Prior M5 bar stop
        - m5_atr: M5 ATR stop
        - m15_atr: M15 ATR stop
        - fractal: Fractal stop
    """
    entry_price = _safe_float(trade.get('entry_price'))
    direction = trade.get('direction', 'LONG')
    entry_time = trade.get('entry_time')
    zone_low = _safe_float(trade.get('zone_low'))
    zone_high = _safe_float(trade.get('zone_high'))

    stops = {}

    # Stop Type 1: Zone Boundary + 5% Buffer
    stops['zone_buffer'] = calculate_zone_buffer_stop(
        entry_price=entry_price,
        zone_low=zone_low,
        zone_high=zone_high,
        direction=direction
    )

    # Stop Type 2: Prior M1 Bar High/Low
    stops['prior_m1'] = calculate_prior_m1_stop(
        m1_bars=m1_bars,
        entry_time=entry_time,
        direction=direction
    )

    # Stop Type 3: Prior M5 Bar High/Low
    stops['prior_m5'] = calculate_prior_m5_stop(
        m5_bars=m5_bars,
        direction=direction
    )

    # Stop Type 4: M5 ATR (1.1x)
    stops['m5_atr'] = calculate_m5_atr_stop(
        m5_bars=m5_bars,
        entry_price=entry_price,
        direction=direction
    )

    # Stop Type 5: M15 ATR (1.1x)
    stops['m15_atr'] = calculate_m15_atr_stop(
        m5_bars=m5_bars,
        entry_price=entry_price,
        direction=direction
    )

    # Stop Type 6: M5 Fractal High/Low
    stops['fractal'] = calculate_fractal_stop(
        m5_bars=m5_bars,
        direction=direction
    )

    return stops


# =============================================================================
# TESTING
# =============================================================================
if __name__ == "__main__":
    # Test trade
    test_trade = {
        'trade_id': 'TEST001',
        'entry_price': 100.0,
        'direction': 'LONG',
        'entry_time': '10:35:00',
        'zone_low': 99.50,
        'zone_high': 100.50
    }

    # Test M1 bars
    test_m1_bars = [
        {'bar_time': '10:32:00', 'high': 99.90, 'low': 99.70},
        {'bar_time': '10:33:00', 'high': 99.95, 'low': 99.75},
        {'bar_time': '10:34:00', 'high': 100.05, 'low': 99.85},  # Prior M1 bar
        {'bar_time': '10:35:00', 'high': 100.15, 'low': 99.95},  # Entry bar
    ]

    # Test M5 bars
    test_m5_bars = [
        {'bars_from_entry': -10, 'high': 100.50, 'low': 99.80, 'close': 100.20, 'open': 100.00},
        {'bars_from_entry': -9, 'high': 100.60, 'low': 99.90, 'close': 100.30, 'open': 100.20},
        {'bars_from_entry': -8, 'high': 100.70, 'low': 100.00, 'close': 100.40, 'open': 100.30},
        {'bars_from_entry': -7, 'high': 100.50, 'low': 99.70, 'close': 100.00, 'open': 100.40},
        {'bars_from_entry': -6, 'high': 100.30, 'low': 99.50, 'close': 99.80, 'open': 100.00},  # Swing low
        {'bars_from_entry': -5, 'high': 100.20, 'low': 99.60, 'close': 99.90, 'open': 99.80},
        {'bars_from_entry': -4, 'high': 100.40, 'low': 99.70, 'close': 100.10, 'open': 99.90},
        {'bars_from_entry': -3, 'high': 100.60, 'low': 99.90, 'close': 100.30, 'open': 100.10},
        {'bars_from_entry': -2, 'high': 100.50, 'low': 99.95, 'close': 100.20, 'open': 100.30},
        {'bars_from_entry': -1, 'high': 100.40, 'low': 99.90, 'close': 100.10, 'open': 100.20},  # Prior M5
        {'bars_from_entry': 0, 'high': 100.30, 'low': 99.85, 'close': 100.00, 'open': 100.10},   # Entry bar
    ]

    print("Stop Price Calculator Test")
    print("=" * 60)
    print(f"\nTrade: {test_trade['direction']} at ${test_trade['entry_price']:.2f}")
    print(f"Zone: ${test_trade['zone_low']:.2f} - ${test_trade['zone_high']:.2f}")

    # Calculate all stops
    stops = calculate_all_stop_prices(test_trade, test_m1_bars, test_m5_bars)

    print("\nCalculated Stop Prices:")
    print("-" * 40)

    stop_names = {
        'zone_buffer': 'Zone + 5% Buffer',
        'prior_m1': 'Prior M1 H/L',
        'prior_m5': 'Prior M5 H/L',
        'm5_atr': 'M5 ATR (1.1x)',
        'm15_atr': 'M15 ATR (1.1x)',
        'fractal': 'M5 Fractal H/L'
    }

    for key, name in stop_names.items():
        price = stops.get(key)
        if price is not None:
            distance = abs(test_trade['entry_price'] - price)
            pct = (distance / test_trade['entry_price']) * 100
            print(f"{name:20s}: ${price:.2f} ({pct:.2f}% from entry)")
        else:
            print(f"{name:20s}: N/A")
