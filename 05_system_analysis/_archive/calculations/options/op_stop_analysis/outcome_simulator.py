"""
Options Outcome Simulator

Simulates trade outcomes for each stop type.
Determines win/loss based on whether target was reached before stop.

Target is fixed at 1R (same percentage as stop loss).
Example: 25% stop = 25% target for 1R
"""

from typing import Dict, Any, List, Optional
from decimal import Decimal

from .stop_types import OPTIONS_STOP_TYPES, STOP_TYPE_ORDER


def _safe_float(value, default: float = None) -> Optional[float]:
    """Safely convert value to float."""
    if value is None:
        return default
    try:
        if isinstance(value, Decimal):
            return float(value)
        return float(value)
    except (ValueError, TypeError):
        return default


def simulate_single_trade(
    trade: Dict[str, Any]
) -> Dict[str, Dict[str, Any]]:
    """
    Simulate outcomes for a single trade across all stop types.

    Target is 1R (same percentage as stop loss).
    Win = MFE% >= stop_loss_pct before MAE% >= stop_loss_pct

    Parameters:
    -----------
    trade : Dict
        Trade data with keys:
        - option_entry_price: Entry price of option
        - mfe_pct: Maximum favorable excursion (% gain)
        - mae_pct: Maximum adverse excursion (% loss, positive value)
        - exit_pct: Final exit (% gain/loss at 15:30)
        - mfe_time: When MFE occurred
        - mae_time: When MAE occurred
        - model: EPCH01-04
        - contract_type: CALL or PUT
        - trade_id: Unique identifier

    Returns:
    --------
    Dict[str, Dict]
        Results for each stop type
    """
    entry_price = _safe_float(trade.get('option_entry_price'))
    mfe_pct = _safe_float(trade.get('mfe_pct'), 0)
    mae_pct = _safe_float(trade.get('mae_pct'), 0)
    exit_pct = _safe_float(trade.get('exit_pct'), 0)

    if entry_price is None or entry_price <= 0:
        return {}

    results = {}

    for stop_type in STOP_TYPE_ORDER:
        stop_loss_pct = OPTIONS_STOP_TYPES[stop_type]['loss_pct']

        # Target is 1R (same percentage as stop)
        target_pct = stop_loss_pct

        # Determine if stop was hit
        # mae_pct is stored as positive value (e.g., 25 means -25% move)
        stop_hit = mae_pct >= stop_loss_pct

        # Determine if target was reached
        target_reached = mfe_pct >= target_pct

        # Determine outcome
        # Need to check WHICH happened first using time data
        mfe_time = trade.get('mfe_time')
        mae_time = trade.get('mae_time')

        if stop_hit and target_reached:
            # Both happened - need to check which was first
            # If mfe_time < mae_time, target was hit first (WIN)
            # If mae_time < mfe_time, stop was hit first (LOSS)
            if mfe_time and mae_time:
                # Compare times
                mfe_first = mfe_time < mae_time
                outcome = 'WIN' if mfe_first else 'LOSS'
                r_achieved = 1.0 if mfe_first else -1.0
            else:
                # No time data - assume stop hit first (conservative)
                outcome = 'LOSS'
                r_achieved = -1.0
        elif target_reached and not stop_hit:
            # Target reached, stop never hit
            outcome = 'WIN'
            r_achieved = 1.0
        elif stop_hit and not target_reached:
            # Stop hit, target never reached
            outcome = 'LOSS'
            r_achieved = -1.0
        else:
            # Neither hit - use exit_pct at 15:30 to determine outcome
            if exit_pct > 0:
                outcome = 'WIN'
                r_achieved = exit_pct / stop_loss_pct
            else:
                outcome = 'LOSS'
                r_achieved = exit_pct / stop_loss_pct  # Will be negative

        results[stop_type] = {
            'trade_id': trade.get('trade_id'),
            'model': trade.get('model'),
            'contract_type': trade.get('contract_type'),
            'direction': trade.get('direction', 'LONG'),
            'stop_type': stop_type,
            'entry_price': entry_price,
            'stop_loss_pct': stop_loss_pct,
            'target_pct': target_pct,
            'mfe_pct': mfe_pct,
            'mae_pct': mae_pct,
            'exit_pct': exit_pct,
            'stop_hit': stop_hit,
            'target_reached': target_reached,
            'r_achieved': r_achieved,
            'outcome': outcome
        }

    return results


def simulate_all_outcomes(
    trades_data: List[Dict[str, Any]]
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Simulate outcomes for all trades across all stop types.

    Returns:
    --------
    Dict[str, List[Dict]]
        Results grouped by stop_type
    """
    results = {stop_type: [] for stop_type in STOP_TYPE_ORDER}

    for trade in trades_data:
        trade_results = simulate_single_trade(trade)

        for stop_type, result in trade_results.items():
            results[stop_type].append(result)

    return results
