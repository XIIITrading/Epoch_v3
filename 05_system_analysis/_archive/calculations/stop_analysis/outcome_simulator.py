"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Calculation: Outcome Simulator for Stop Analysis (CALC-009)
XIII Trading LLC
================================================================================

PURPOSE:
    Simulate trade outcomes for each stop type by walking through bars
    from entry to 15:30 ET and determining:
    1. Was stop hit?
    2. If yes, was MFE reached before stop?
    3. Calculate R achieved

TRIGGER TYPES:
    - Price-based (Stop Types 1, 2, 3, 6): Triggers when price touches stop
    - Close-based (Stop Types 4, 5): Triggers only when bar CLOSES beyond stop

================================================================================
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import time as dt_time, datetime as dt_datetime, timedelta as dt_timedelta


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


def check_price_based_stop(
    m1_bars: List[Dict[str, Any]],
    stop_price: float,
    entry_time,
    direction: str
) -> Dict[str, Any]:
    """
    Check if a price-based stop was hit.

    Price-based stops trigger when price touches the stop level
    (low <= stop for LONG, high >= stop for SHORT).

    Parameters:
    -----------
    m1_bars : List[Dict[str, Any]]
        M1 bar data from entry to 15:30
    stop_price : float
        Stop price level
    entry_time : various
        Trade entry time
    direction : str
        Trade direction ('LONG' or 'SHORT')

    Returns:
    --------
    Dict with 'stop_hit': bool, 'stop_time': time or None
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

    Close-based stops only trigger when bar CLOSES beyond the level.
    For M15 ATR, check at M15 boundaries (every 3rd M5 bar).

    Parameters:
    -----------
    m5_bars : List[Dict[str, Any]]
        M5 bar data with 'bars_from_entry', 'close'
    stop_price : float
        Stop price level
    stop_type : str
        'm5_atr' or 'm15_atr'
    direction : str
        Trade direction ('LONG' or 'SHORT')

    Returns:
    --------
    Dict with 'stop_hit': bool, 'stop_time': time or None
    """
    is_long = direction.upper() == 'LONG'

    # Get post-entry bars
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


def find_stop_hit_time(
    trade: Dict[str, Any],
    stop_price: float,
    stop_type: str,
    m1_bars: List[Dict[str, Any]],
    m5_bars: List[Dict[str, Any]]
) -> Optional[Any]:
    """
    Find the exact time when stop was hit.

    Parameters:
    -----------
    trade : Dict[str, Any]
        Trade record
    stop_price : float
        Stop price level
    stop_type : str
        Stop type identifier
    m1_bars : List[Dict[str, Any]]
        M1 bar data
    m5_bars : List[Dict[str, Any]]
        M5 bar data

    Returns:
    --------
    Time value when stop was hit, or None
    """
    direction = trade.get('direction', 'LONG')
    entry_time = trade.get('entry_time')

    if stop_type in ['m5_atr', 'm15_atr']:
        result = check_close_based_stop(m5_bars, stop_price, stop_type, direction)
    else:
        result = check_price_based_stop(m1_bars, stop_price, entry_time, direction)

    return result.get('stop_time')


def simulate_outcome(
    trade: Dict[str, Any],
    stop_price: float,
    stop_type: str,
    m1_bars: List[Dict[str, Any]],
    m5_bars: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Simulate trade outcome for a given stop price.

    Determines:
    1. Was stop hit?
    2. If yes, was MFE reached before stop?
    3. Calculate R achieved

    Parameters:
    -----------
    trade : Dict[str, Any]
        Trade record with entry_price, direction, mfe_potential_price/time, mae_potential_price/time
    stop_price : float
        Calculated stop price
    stop_type : str
        Stop type identifier ('zone_buffer', 'prior_m1', etc.)
    m1_bars : List[Dict[str, Any]]
        M1 bar data
    m5_bars : List[Dict[str, Any]]
        M5 bar data

    Returns:
    --------
    Dict with trade outcome details
    """
    entry_price = _safe_float(trade.get('entry_price'))
    direction = trade.get('direction', 'LONG')
    is_long = direction.upper() == 'LONG'

    mfe_price = _safe_float(trade.get('mfe_potential_price'))
    mfe_time = trade.get('mfe_potential_time')
    mae_price = _safe_float(trade.get('mae_potential_price'))
    mae_time = trade.get('mae_potential_time')

    # Calculate stop distance (R denominator)
    stop_distance = abs(entry_price - stop_price)
    stop_distance_pct = (stop_distance / entry_price) * 100 if entry_price > 0 else 0

    # Check if stop was hit based on stop type
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
        # Compare stop hit time with MFE time
        stop_minutes = _time_to_minutes(stop_hit_time)
        mfe_minutes = _time_to_minutes(mfe_time)

        if stop_minutes is not None and mfe_minutes is not None and mfe_minutes < stop_minutes:
            # MFE reached before stop - calculate R captured
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
        'outcome': outcome
    }


def simulate_all_outcomes(
    trades_with_data: List[Dict[str, Any]]
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Process all trades and simulate outcomes for each stop type.

    Parameters:
    -----------
    trades_with_data : List[Dict[str, Any]]
        List of trade records, each containing:
        - trade: Trade record dict
        - m1_bars: M1 bars for this trade
        - m5_bars: M5 bars for this trade
        - stops: Dict of calculated stop prices

    Returns:
    --------
    Dict mapping stop_type to list of outcome records
    """
    from .stop_calculator import calculate_all_stop_prices

    results = {
        'zone_buffer': [],
        'prior_m1': [],
        'prior_m5': [],
        'm5_atr': [],
        'm15_atr': [],
        'fractal': []
    }

    for trade_data in trades_with_data:
        trade = trade_data.get('trade', {})
        m1_bars = trade_data.get('m1_bars', [])
        m5_bars = trade_data.get('m5_bars', [])
        stops = trade_data.get('stops', {})

        # If stops not pre-calculated, calculate them
        if not stops:
            stops = calculate_all_stop_prices(trade, m1_bars, m5_bars)

        # Simulate each stop type
        for stop_type, stop_price in stops.items():
            if stop_price is None:
                continue

            outcome = simulate_outcome(
                trade=trade,
                stop_price=stop_price,
                stop_type=stop_type,
                m1_bars=m1_bars,
                m5_bars=m5_bars
            )

            results[stop_type].append(outcome)

    return results


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
        'model': 'EPCH01',
        'mfe_potential_price': 101.50,
        'mfe_potential_time': '11:15:00',
        'mae_potential_price': 99.20,
        'mae_potential_time': '14:30:00',
        'zone_low': 99.50,
        'zone_high': 100.50
    }

    # Test M1 bars - price touches 99.60 at 12:00
    test_m1_bars = [
        {'bar_time': '10:36:00', 'high': 100.20, 'low': 99.90},
        {'bar_time': '10:37:00', 'high': 100.30, 'low': 100.00},
        {'bar_time': '11:00:00', 'high': 101.00, 'low': 100.50},
        {'bar_time': '11:15:00', 'high': 101.50, 'low': 101.00},  # MFE hit
        {'bar_time': '12:00:00', 'high': 100.00, 'low': 99.60},   # Potential stop touch
        {'bar_time': '14:00:00', 'high': 99.80, 'low': 99.30},
    ]

    # Test M5 bars
    test_m5_bars = [
        {'bars_from_entry': -2, 'high': 100.40, 'low': 99.85, 'close': 100.10},
        {'bars_from_entry': -1, 'high': 100.30, 'low': 99.80, 'close': 100.00},
        {'bars_from_entry': 0, 'high': 100.20, 'low': 99.90, 'close': 100.10},
        {'bars_from_entry': 1, 'high': 100.50, 'low': 100.10, 'close': 100.40},
        {'bars_from_entry': 2, 'high': 101.00, 'low': 100.30, 'close': 100.90},
        {'bars_from_entry': 3, 'high': 101.50, 'low': 100.80, 'close': 101.30},
        {'bars_from_entry': 6, 'high': 100.50, 'low': 99.70, 'close': 99.80},  # M5 close below stop?
    ]

    print("Outcome Simulator Test")
    print("=" * 60)
    print(f"\nTrade: {test_trade['direction']} at ${test_trade['entry_price']:.2f}")
    print(f"MFE: ${test_trade['mfe_potential_price']:.2f} at {test_trade['mfe_potential_time']}")
    print(f"MAE: ${test_trade['mae_potential_price']:.2f} at {test_trade['mae_potential_time']}")

    # Test stop prices
    test_stops = {
        'zone_buffer': 99.475,  # Should not be hit (lowest is 99.30)
        'prior_m1': 99.85,
        'prior_m5': 99.80,
        'm5_atr': 99.50,
        'm15_atr': 99.30,
        'fractal': 99.70
    }

    print("\nSimulated Outcomes:")
    print("-" * 60)

    for stop_type, stop_price in test_stops.items():
        outcome = simulate_outcome(
            trade=test_trade,
            stop_price=stop_price,
            stop_type=stop_type,
            m1_bars=test_m1_bars,
            m5_bars=test_m5_bars
        )

        print(f"\n{stop_type}:")
        print(f"  Stop: ${outcome['stop_price']:.2f} ({outcome['stop_distance_pct']:.2f}%)")
        print(f"  Hit: {outcome['stop_hit']}")
        print(f"  Outcome: {outcome['outcome']}")
        print(f"  R Achieved: {outcome['r_achieved']:.2f}R")
