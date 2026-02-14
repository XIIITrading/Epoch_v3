"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Trade Statistics
XIII Trading LLC
================================================================================

Functions for calculating trade-level statistics.

WIN CONDITION (Stop-Based):
    Win = MFE reached (>=1R) before stop hit
    Loss = Stop hit before reaching 1R
    Partial = Stop hit after some MFE but < 1R

    The is_winner flag must be pre-computed from stop_analysis table
    and merged into the data before calling these functions.

POINTS CALCULATION:
- Win Points: abs(mfe_potential_price - entry_price) for winning trades
- Loss Points: abs(mae_potential_price - entry_price) for losing trades
- Total Points: Win Points - Loss Points

Updated: 2026-01-11
- Removed temporal mfe_time < mae_time logic
- Now requires pre-computed is_winner from stop_analysis
- Stop type selected via UI (default: Zone + 5% Buffer)
================================================================================
"""

from typing import List, Dict, Any, Optional
import pandas as pd


def _safe_float(value, default: float = 0.0) -> float:
    """Safely convert value to float."""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def get_trade_statistics(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate overall trade statistics using stop-based win condition.

    WIN CONDITION:
        Uses pre-computed is_winner from stop_analysis table.
        Win = MFE reached (>=1R) before stop hit (is_winner=True)
        Loss = Stop hit before reaching 1R (is_winner=False)

    POINTS CALCULATION:
    - Win Points: abs(mfe_potential_price - entry_price) for winning trades
    - Loss Points: abs(mae_potential_price - entry_price) for losing trades
    - Total Points: Sum of win points - Sum of loss points
    - Avg Points: Total Points / Total Trades

    Parameters:
    -----------
    data : List[Dict[str, Any]]
        List of records with is_winner already computed from stop_analysis.
        Required columns: is_winner, entry_price, mfe_potential_price, mae_potential_price

    Returns:
    --------
    Dict with: total, wins, losses, win_rate, avg_points, total_points,
               median_mfe_pct, median_mae_pct
    """
    empty_result = {
        "total": 0,
        "wins": 0,
        "losses": 0,
        "win_rate": 0,
        "avg_points": 0,
        "total_points": 0,
        "median_mfe_pct": 0,
        "median_mae_pct": 0
    }

    if not data:
        return empty_result

    df = pd.DataFrame(data)

    # Check for is_winner column (must be pre-computed from stop_analysis)
    if 'is_winner' not in df.columns:
        return empty_result

    # Drop rows without is_winner
    df_valid = df.dropna(subset=['is_winner']).copy()

    if df_valid.empty:
        return empty_result

    total = len(df_valid)
    wins = int(df_valid['is_winner'].sum())
    losses = total - wins
    win_rate = (wins / total * 100) if total > 0 else 0

    # Calculate points if price columns available
    has_prices = all(col in df_valid.columns for col in
                     ['entry_price', 'mfe_potential_price', 'mae_potential_price'])

    if has_prices:
        df_valid['entry_price'] = df_valid['entry_price'].apply(lambda x: _safe_float(x))
        df_valid['mfe_potential_price'] = df_valid['mfe_potential_price'].apply(lambda x: _safe_float(x))
        df_valid['mae_potential_price'] = df_valid['mae_potential_price'].apply(lambda x: _safe_float(x))

        df_valid['trade_points'] = df_valid.apply(
            lambda row: abs(row['mfe_potential_price'] - row['entry_price']) if row['is_winner']
                        else -abs(row['mae_potential_price'] - row['entry_price']),
            axis=1
        )

        total_points = df_valid['trade_points'].sum()
        avg_points = total_points / total if total > 0 else 0

        # Calculate MFE/MAE percentages for reference
        df_valid['mfe_pct'] = df_valid.apply(
            lambda row: abs(row['mfe_potential_price'] - row['entry_price']) / row['entry_price'] * 100
                        if row['entry_price'] > 0 else 0,
            axis=1
        )
        df_valid['mae_pct'] = df_valid.apply(
            lambda row: abs(row['mae_potential_price'] - row['entry_price']) / row['entry_price'] * 100
                        if row['entry_price'] > 0 else 0,
            axis=1
        )

        median_mfe_pct = df_valid['mfe_pct'].median() if len(df_valid) > 0 else 0
        median_mae_pct = df_valid['mae_pct'].median() if len(df_valid) > 0 else 0
    else:
        total_points = 0
        avg_points = 0
        median_mfe_pct = 0
        median_mae_pct = 0

    return {
        "total": total,
        "wins": wins,
        "losses": losses,
        "win_rate": round(win_rate, 1),
        "avg_points": round(avg_points, 2),
        "total_points": round(total_points, 2),
        "median_mfe_pct": round(median_mfe_pct, 3) if pd.notna(median_mfe_pct) else 0,
        "median_mae_pct": round(median_mae_pct, 3) if pd.notna(median_mae_pct) else 0
    }


def get_stats_by_model(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Get statistics grouped by model using stop-based win condition.

    Parameters:
    -----------
    data : List[Dict[str, Any]]
        List of records with is_winner pre-computed from stop_analysis

    Returns:
    --------
    List of dicts with model stats including points calculations
    """
    if not data:
        return []

    df = pd.DataFrame(data)

    if "model" not in df.columns:
        return []

    # Normalize model names
    model_map = {"EPCH1": "EPCH01", "EPCH2": "EPCH02", "EPCH3": "EPCH03", "EPCH4": "EPCH04"}
    df["model"] = df["model"].apply(lambda x: model_map.get(x, x) if x else x)

    results = []
    for model in sorted(df["model"].dropna().unique()):
        model_df = df[df["model"] == model]
        stats = get_trade_statistics(model_df.to_dict("records"))
        stats["model"] = model
        stats["trade_type"] = "continuation" if model in ["EPCH01", "EPCH03"] else "rejection"
        stats["zone_type"] = "primary" if model in ["EPCH01", "EPCH02"] else "secondary"
        results.append(stats)

    return results


def get_stats_by_direction(data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Get statistics grouped by direction using stop-based win condition.

    Parameters:
    -----------
    data : List[Dict[str, Any]]
        List of records with is_winner pre-computed from stop_analysis

    Returns:
    --------
    Dict mapping direction to stats dict
    """
    if not data:
        return {}

    df = pd.DataFrame(data)

    if "direction" not in df.columns:
        return {}

    results = {}
    for direction in ["LONG", "SHORT"]:
        dir_df = df[df["direction"].str.upper() == direction]
        if len(dir_df) > 0:
            results[direction] = get_trade_statistics(dir_df.to_dict("records"))

    return results


def get_stats_by_exit_reason(data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Get statistics grouped by exit reason.

    NOTE: This function is maintained for archived tab compatibility.
    The mfe_mae_potential table does not have exit_reason column,
    so this returns empty results when using the new data source.

    Parameters:
    -----------
    data : List[Dict[str, Any]]
        List of trade records

    Returns:
    --------
    Dict mapping exit_reason to stats dict
    """
    if not data:
        return {}

    df = pd.DataFrame(data)

    if "exit_reason" not in df.columns:
        return {}

    results = {}
    for reason in df["exit_reason"].dropna().unique():
        reason_df = df[df["exit_reason"] == reason]
        if len(reason_df) > 0:
            results[str(reason)] = get_trade_statistics(reason_df.to_dict("records"))

    return results
