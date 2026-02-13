"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
Stop Price Calculator (CALC-009)
XIII Trading LLC
================================================================================

PURPOSE:
    Calculate stop prices for all 6 stop types analyzed in CALC-009.
    Adapted from 12_system_analysis for use in the backtest processor.

STOP TYPES:
    1. Zone Boundary + 5% Buffer - Stop beyond zone with buffer
    2. Prior M1 Bar High/Low - Tightest structural stop
    3. Prior M5 Bar High/Low - Short-term structure stop
    4. M5 ATR (1.1x) - Volatility-normalized, close-based
    5. M15 ATR (1.1x) - Wider volatility stop, close-based
    6. M5 Fractal High/Low - Market structure swing stop

TRIGGER TYPES:
    - Price-based (1, 2, 3, 6): Triggers when price touches stop
    - Close-based (4, 5): Triggers only when bar CLOSES beyond stop

Version: 1.0.0
================================================================================
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import time as dt_time, datetime as dt_datetime, timedelta as dt_timedelta

from config import ZONE_BUFFER_PCT, ATR_PERIOD, ATR_MULTIPLIER, FRACTAL_LENGTH


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

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
            parts = time_val.split(':')
            if len(parts) >= 2:
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = int(parts[2]) if len(parts) > 2 else 0
                return hours * 60 + minutes + seconds / 60

        return None
    except Exception:
        return None


# =============================================================================
# ATR CALCULATIONS
# =============================================================================

def calculate_true_range(
    high: float,
    low: float,
    prev_close: Optional[float] = None
) -> float:
    """
    Calculate True Range for a single bar.

    True Range = max(
        high - low,
        abs(high - prev_close),
        abs(low - prev_close)
    )
    """
    high = _safe_float(high)
    low = _safe_float(low)

    range_hl = high - low

    if prev_close is None:
        return range_hl

    prev_close = _safe_float(prev_close)

    return max(
        range_hl,
        abs(high - prev_close),
        abs(low - prev_close)
    )


def calculate_atr_m5(
    m5_bars: List[Dict[str, Any]],
    period: int = ATR_PERIOD
) -> Optional[float]:
    """Calculate 14-period ATR on M5 bars at or before entry."""
    if not m5_bars:
        return None

    # Filter to bars at or before entry
    pre_entry_bars = [b for b in m5_bars if b.get('bars_from_entry', 0) <= 0]
    pre_entry_bars.sort(key=lambda x: x.get('bars_from_entry', 0))

    if len(pre_entry_bars) < 2:
        return None

    actual_period = min(period, len(pre_entry_bars))
    recent_bars = pre_entry_bars[-actual_period:]

    true_ranges = []
    for i, bar in enumerate(recent_bars):
        high = _safe_float(bar.get('high'))
        low = _safe_float(bar.get('low'))

        if i == 0:
            tr = high - low
        else:
            prev_close = _safe_float(recent_bars[i-1].get('close'))
            tr = calculate_true_range(high, low, prev_close)

        true_ranges.append(tr)

    if not true_ranges:
        return None

    return sum(true_ranges) / len(true_ranges)


def aggregate_m5_to_m15(m5_bars: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate M5 bars into M15 bars (3 M5 = 1 M15)."""
    if not m5_bars or len(m5_bars) < 3:
        return []

    sorted_bars = sorted(m5_bars, key=lambda x: x.get('bars_from_entry', 0))
    m15_bars = []

    for i in range(0, len(sorted_bars) - 2, 3):
        group = sorted_bars[i:i+3]
        if len(group) < 3:
            continue

        m15_bar = {
            'high': max(_safe_float(b.get('high')) for b in group),
            'low': min(_safe_float(b.get('low')) for b in group),
            'open': _safe_float(group[0].get('open')),
            'close': _safe_float(group[-1].get('close')),
            'bars_from_entry': group[-1].get('bars_from_entry', 0)
        }
        m15_bars.append(m15_bar)

    return m15_bars


def calculate_atr_m15(
    m5_bars: List[Dict[str, Any]],
    period: int = ATR_PERIOD
) -> Optional[float]:
    """Calculate 14-period ATR on M15 timeframe by aggregating M5 bars."""
    if not m5_bars:
        return None

    pre_entry_bars = [b for b in m5_bars if b.get('bars_from_entry', 0) <= 0]
    pre_entry_bars.sort(key=lambda x: x.get('bars_from_entry', 0))

    if len(pre_entry_bars) < 6:
        return None

    m15_bars = aggregate_m5_to_m15(pre_entry_bars)

    if len(m15_bars) < 2:
        return None

    actual_period = min(period, len(m15_bars))
    recent_bars = m15_bars[-actual_period:]

    true_ranges = []
    for i, bar in enumerate(recent_bars):
        high = bar['high']
        low = bar['low']

        if i == 0:
            tr = high - low
        else:
            prev_close = recent_bars[i-1]['close']
            tr = calculate_true_range(high, low, prev_close)

        true_ranges.append(tr)

    if not true_ranges:
        return None

    return sum(true_ranges) / len(true_ranges)


# =============================================================================
# FRACTAL DETECTION
# =============================================================================

def find_fractal_highs(
    bars: List[Dict[str, Any]],
    fractal_length: int = FRACTAL_LENGTH
) -> List[Dict[str, Any]]:
    """Find all fractal highs in a bar series."""
    if not bars or len(bars) < (2 * fractal_length + 1):
        return []

    sorted_bars = sorted(bars, key=lambda x: x.get('bars_from_entry', 0))
    fractals = []

    for i in range(fractal_length, len(sorted_bars) - fractal_length):
        bar = sorted_bars[i]
        bar_high = _safe_float(bar.get('high'))
        is_fractal = True

        for j in range(1, fractal_length + 1):
            if bar_high <= _safe_float(sorted_bars[i - j].get('high')):
                is_fractal = False
                break

        if is_fractal:
            for j in range(1, fractal_length + 1):
                if bar_high <= _safe_float(sorted_bars[i + j].get('high')):
                    is_fractal = False
                    break

        if is_fractal:
            fractals.append({
                'type': 'high',
                'price': bar_high,
                'bars_from_entry': bar.get('bars_from_entry', 0),
                'index': i
            })

    return fractals


def find_fractal_lows(
    bars: List[Dict[str, Any]],
    fractal_length: int = FRACTAL_LENGTH
) -> List[Dict[str, Any]]:
    """Find all fractal lows in a bar series."""
    if not bars or len(bars) < (2 * fractal_length + 1):
        return []

    sorted_bars = sorted(bars, key=lambda x: x.get('bars_from_entry', 0))
    fractals = []

    for i in range(fractal_length, len(sorted_bars) - fractal_length):
        bar = sorted_bars[i]
        bar_low = _safe_float(bar.get('low'))
        is_fractal = True

        for j in range(1, fractal_length + 1):
            if bar_low >= _safe_float(sorted_bars[i - j].get('low')):
                is_fractal = False
                break

        if is_fractal:
            for j in range(1, fractal_length + 1):
                if bar_low >= _safe_float(sorted_bars[i + j].get('low')):
                    is_fractal = False
                    break

        if is_fractal:
            fractals.append({
                'type': 'low',
                'price': bar_low,
                'bars_from_entry': bar.get('bars_from_entry', 0),
                'index': i
            })

    return fractals


def calculate_fractal_stop_price(
    m5_bars: List[Dict[str, Any]],
    direction: str,
    fractal_length: int = FRACTAL_LENGTH
) -> Optional[float]:
    """Calculate fractal-based stop price for a trade."""
    if not m5_bars:
        return None

    confirmable_bars = [
        b for b in m5_bars
        if b.get('bars_from_entry', 0) <= -fractal_length
    ]

    if len(confirmable_bars) < (2 * fractal_length + 1):
        return None

    is_long = direction.upper() == 'LONG'

    if is_long:
        fractals = find_fractal_lows(confirmable_bars, fractal_length)
    else:
        fractals = find_fractal_highs(confirmable_bars, fractal_length)

    if not fractals:
        return None

    # Get most recent fractal (highest bars_from_entry)
    most_recent = max(fractals, key=lambda x: x.get('bars_from_entry', -999))
    return most_recent['price']


# =============================================================================
# STOP PRICE CALCULATIONS
# =============================================================================

def calculate_zone_buffer_stop(
    entry_price: float,
    zone_low: float,
    zone_high: float,
    direction: str,
    buffer_pct: float = ZONE_BUFFER_PCT
) -> Optional[float]:
    """
    Stop Type 1: Zone boundary + 5% buffer.

    LONG:  stop = zone_low - (zone_distance * buffer_pct)
    SHORT: stop = zone_high + (zone_distance * buffer_pct)
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
        zone_distance = entry_price - zone_low
        buffer = zone_distance * buffer_pct
        stop_price = zone_low - buffer
    else:
        zone_distance = zone_high - entry_price
        buffer = zone_distance * buffer_pct
        stop_price = zone_high + buffer

    return stop_price


def calculate_prior_m1_stop(
    m1_bars: List[Dict[str, Any]],
    entry_time,
    direction: str,
    trade_date=None
) -> Optional[float]:
    """
    Stop Type 2: Prior M1 bar high/low.
    Stop at the high/low of the M1 candle immediately before entry.

    Now handles bars from previous trading day for early morning entries.
    Bars from previous day are considered "prior" to any bar on trade_date.
    """
    if not m1_bars:
        return None

    entry_minutes = _time_to_minutes(entry_time)
    if entry_minutes is None:
        return None

    # Build list of prior bars, considering both same-day and prior-day bars
    prior_bars = []
    for bar in m1_bars:
        bar_time = bar.get('bar_time')
        bar_date = bar.get('bar_date')
        bar_minutes = _time_to_minutes(bar_time)

        if bar_minutes is None:
            continue

        # Determine if this bar is prior to entry
        is_prior = False

        if trade_date is not None and bar_date is not None:
            # If bar is from a previous day, it's definitely prior
            if bar_date < trade_date:
                is_prior = True
            # If bar is from same day, check time
            elif bar_date == trade_date and bar_minutes < entry_minutes:
                is_prior = True
        else:
            # Fall back to time-only comparison (legacy behavior)
            if bar_minutes < entry_minutes:
                is_prior = True

        if is_prior:
            # Create a sortable key: (date, time_minutes) where date can be None
            # For sorting, we want most recent first, so use negative for reverse
            sort_key = (bar_date, bar_minutes) if bar_date else (None, bar_minutes)
            prior_bars.append((sort_key, bar))

    if not prior_bars:
        return None

    # Sort by (date, time) descending to get most recent bar first
    # None dates are treated as older than any date
    def sort_func(x):
        date, minutes = x[0]
        if date is None:
            return (0, minutes)  # Treat None as epoch 0
        # Convert date to ordinal for comparison
        return (date.toordinal(), minutes)

    prior_bars.sort(key=sort_func, reverse=True)
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
    Stop at the high/low of the M5 bar at bars_from_entry = -1.
    """
    if not m5_bars:
        return None

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
    multiplier: float = ATR_MULTIPLIER,
    atr_period: int = ATR_PERIOD
) -> Optional[float]:
    """
    Stop Type 4: M5 ATR-based stop (1.1x multiplier).
    Close-based trigger - only exits if candle CLOSES beyond level.
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
    multiplier: float = ATR_MULTIPLIER,
    atr_period: int = ATR_PERIOD
) -> Optional[float]:
    """
    Stop Type 5: M15 ATR-based stop (1.1x multiplier).
    Close-based trigger - check at M15 boundaries.
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
    fractal_length: int = FRACTAL_LENGTH
) -> Optional[float]:
    """
    Stop Type 6: M5 fractal high/low (market structure).
    Stop beyond the most recent confirmed swing high/low.
    """
    return calculate_fractal_stop_price(m5_bars, direction, fractal_length)


# =============================================================================
# MAIN CALCULATION WRAPPER
# =============================================================================

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
        Trade record with entry_price, direction, entry_time, zone_low, zone_high, date
    m1_bars : List[Dict[str, Any]]
        M1 bar data for this trade's ticker/date (may include prior day bars)
    m5_bars : List[Dict[str, Any]]
        M5 trade bars for this trade (may include prior day bars)

    Returns:
    --------
    Dict[str, Optional[float]]
        Dictionary with stop prices for each type
    """
    entry_price = _safe_float(trade.get('entry_price'))
    direction = trade.get('direction', 'LONG')
    entry_time = trade.get('entry_time')
    trade_date = trade.get('date')
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
        direction=direction,
        trade_date=trade_date
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
# OUTCOME SIMULATION
# =============================================================================

def check_price_based_stop(
    m1_bars: List[Dict[str, Any]],
    stop_price: float,
    entry_time,
    direction: str
) -> Dict[str, Any]:
    """
    Check if a price-based stop was hit.
    Triggers when price TOUCHES the stop level.
    Used for: zone_buffer, prior_m1, prior_m5, fractal
    """
    entry_minutes = _time_to_minutes(entry_time)
    if entry_minutes is None:
        return {'stop_hit': False, 'stop_time': None}

    is_long = direction.upper() == 'LONG'

    for bar in m1_bars:
        bar_minutes = _time_to_minutes(bar.get('bar_time'))
        if bar_minutes is None or bar_minutes <= entry_minutes:
            continue

        bar_high = _safe_float(bar.get('high'))
        bar_low = _safe_float(bar.get('low'))

        if is_long:
            if bar_low <= stop_price:
                return {'stop_hit': True, 'stop_time': bar.get('bar_time')}
        else:
            if bar_high >= stop_price:
                return {'stop_hit': True, 'stop_time': bar.get('bar_time')}

    return {'stop_hit': False, 'stop_time': None}


def check_close_based_stop(
    m5_bars: List[Dict[str, Any]],
    stop_price: float,
    stop_type: str,
    direction: str
) -> Dict[str, Any]:
    """
    Check if a close-based (ATR) stop was hit.
    Triggers only when bar CLOSES beyond the level.
    Used for: m5_atr, m15_atr
    """
    is_long = direction.upper() == 'LONG'

    post_entry_bars = sorted(
        [b for b in m5_bars if b.get('bars_from_entry', 0) > 0],
        key=lambda x: x.get('bars_from_entry', 0)
    )

    if stop_type == 'm15_atr':
        # Check at M15 boundaries (every 3rd M5 bar)
        for i in range(2, len(post_entry_bars), 3):
            bar = post_entry_bars[i]
            bar_close = _safe_float(bar.get('close'))

            if is_long:
                if bar_close <= stop_price:
                    return {'stop_hit': True, 'stop_time': bar.get('bar_time')}
            else:
                if bar_close >= stop_price:
                    return {'stop_hit': True, 'stop_time': bar.get('bar_time')}
    else:
        # M5 ATR - check each M5 close
        for bar in post_entry_bars:
            bar_close = _safe_float(bar.get('close'))

            if is_long:
                if bar_close <= stop_price:
                    return {'stop_hit': True, 'stop_time': bar.get('bar_time')}
            else:
                if bar_close >= stop_price:
                    return {'stop_hit': True, 'stop_time': bar.get('bar_time')}

    return {'stop_hit': False, 'stop_time': None}


def simulate_outcome(
    trade: Dict[str, Any],
    stop_price: float,
    stop_type: str,
    m1_bars: List[Dict[str, Any]],
    m5_bars: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Simulate trade outcome for a given stop price.

    Returns:
    --------
    Dict with trade outcome details including:
    - stop_distance, stop_distance_pct
    - stop_hit, stop_hit_time
    - mfe_price, mfe_time, mfe_distance
    - r_achieved
    - outcome (WIN, LOSS, PARTIAL)
    - trigger_type (price_based or close_based)
    """
    entry_price = _safe_float(trade.get('entry_price'))
    direction = trade.get('direction', 'LONG')
    is_long = direction.upper() == 'LONG'

    mfe_price = _safe_float(trade.get('mfe_potential_price'))
    mfe_time = trade.get('mfe_potential_time')

    # Calculate stop distance (R denominator)
    stop_distance = abs(entry_price - stop_price)
    stop_distance_pct = (stop_distance / entry_price) * 100 if entry_price > 0 else 0

    # Determine trigger type
    trigger_type = 'close_based' if stop_type in ['m5_atr', 'm15_atr'] else 'price_based'

    # Check if stop was hit
    if stop_type in ['m5_atr', 'm15_atr']:
        stop_result = check_close_based_stop(m5_bars, stop_price, stop_type, direction)
    else:
        stop_result = check_price_based_stop(m1_bars, stop_price, trade.get('entry_time'), direction)

    stop_hit = stop_result['stop_hit']
    stop_hit_time = stop_result['stop_time']

    # Calculate MFE distance
    if is_long:
        mfe_distance = mfe_price - entry_price
    else:
        mfe_distance = entry_price - mfe_price

    mfe_distance = max(0, mfe_distance)

    # Determine outcome
    if stop_hit:
        stop_minutes = _time_to_minutes(stop_hit_time)
        mfe_minutes = _time_to_minutes(mfe_time)

        if stop_minutes is not None and mfe_minutes is not None and mfe_minutes < stop_minutes:
            # MFE reached before stop
            r_achieved = mfe_distance / stop_distance if stop_distance > 0 else 0
            outcome = 'WIN' if r_achieved >= 1.0 else 'PARTIAL'
        else:
            # Stop hit before meaningful MFE
            r_achieved = -1.0
            outcome = 'LOSS'
    else:
        # Stop never hit - full MFE potentially captured
        r_achieved = mfe_distance / stop_distance if stop_distance > 0 else 0
        outcome = 'WIN' if r_achieved >= 1.0 else 'PARTIAL'

    return {
        'trade_id': trade.get('trade_id'),
        'direction': direction,
        'model': trade.get('model'),
        'stop_type': stop_type,
        'entry_price': entry_price,
        'stop_price': stop_price,
        'stop_distance': stop_distance,
        'stop_distance_pct': stop_distance_pct,
        'stop_hit': stop_hit,
        'stop_hit_time': stop_hit_time,
        'mfe_price': mfe_price,
        'mfe_time': mfe_time,
        'mfe_distance': mfe_distance,
        'r_achieved': r_achieved,
        'outcome': outcome,
        'trigger_type': trigger_type
    }


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

    # Test M5 bars
    test_m5_bars = [
        {'bars_from_entry': -10, 'high': 100.50, 'low': 99.80, 'close': 100.20, 'open': 100.00},
        {'bars_from_entry': -9, 'high': 100.60, 'low': 99.90, 'close': 100.30, 'open': 100.20},
        {'bars_from_entry': -8, 'high': 100.70, 'low': 100.00, 'close': 100.40, 'open': 100.30},
        {'bars_from_entry': -7, 'high': 100.50, 'low': 99.70, 'close': 100.00, 'open': 100.40},
        {'bars_from_entry': -6, 'high': 100.30, 'low': 99.50, 'close': 99.80, 'open': 100.00},
        {'bars_from_entry': -5, 'high': 100.20, 'low': 99.60, 'close': 99.90, 'open': 99.80},
        {'bars_from_entry': -4, 'high': 100.40, 'low': 99.70, 'close': 100.10, 'open': 99.90},
        {'bars_from_entry': -3, 'high': 100.60, 'low': 99.90, 'close': 100.30, 'open': 100.10},
        {'bars_from_entry': -2, 'high': 100.50, 'low': 99.95, 'close': 100.20, 'open': 100.30},
        {'bars_from_entry': -1, 'high': 100.40, 'low': 99.90, 'close': 100.10, 'open': 100.20},
        {'bars_from_entry': 0, 'high': 100.30, 'low': 99.85, 'close': 100.00, 'open': 100.10},
    ]

    # Test M1 bars
    test_m1_bars = [
        {'bar_time': '10:32:00', 'high': 99.90, 'low': 99.70},
        {'bar_time': '10:33:00', 'high': 99.95, 'low': 99.75},
        {'bar_time': '10:34:00', 'high': 100.05, 'low': 99.85},
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
