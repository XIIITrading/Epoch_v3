"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Indicator Statistics
XIII Trading LLC
================================================================================

Functions for calculating indicator-level statistics by model, outcome, event.
================================================================================
"""

from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np


INDICATOR_COLUMNS = [
    "health_score", "vwap", "sma9", "sma21", "sma_spread",
    "vol_roc", "vol_delta", "cvd_slope"
]

STRUCTURE_COLUMNS = ["m5_structure", "m15_structure", "h1_structure", "h4_structure"]


def get_indicator_averages(
    data: List[Dict[str, Any]],
    group_by: Optional[str] = None
) -> Dict[str, Any]:
    """Get average indicator values, optionally grouped."""
    if not data:
        return {}

    df = pd.DataFrame(data)

    if group_by and group_by in df.columns:
        results = {}
        for group_val in df[group_by].dropna().unique():
            group_df = df[df[group_by] == group_val]
            results[str(group_val)] = _calculate_indicator_stats(group_df)
        return results

    return _calculate_indicator_stats(df)


def _calculate_indicator_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate statistics for indicator columns."""
    stats = {"count": len(df)}

    for col in INDICATOR_COLUMNS:
        if col in df.columns:
            series = pd.to_numeric(df[col], errors="coerce")
            stats[f"{col}_mean"] = round(series.mean(), 4) if pd.notna(series.mean()) else None
            stats[f"{col}_median"] = round(series.median(), 4) if pd.notna(series.median()) else None
            stats[f"{col}_std"] = round(series.std(), 4) if pd.notna(series.std()) else None
            stats[f"{col}_min"] = round(series.min(), 4) if pd.notna(series.min()) else None
            stats[f"{col}_max"] = round(series.max(), 4) if pd.notna(series.max()) else None

    for col in STRUCTURE_COLUMNS:
        if col in df.columns:
            value_counts = df[col].value_counts(normalize=True)
            stats[f"{col}_bull_pct"] = round(value_counts.get("BULL", 0) * 100, 2)
            stats[f"{col}_bear_pct"] = round(value_counts.get("BEAR", 0) * 100, 2)
            stats[f"{col}_neutral_pct"] = round(value_counts.get("NEUTRAL", 0) * 100, 2)

    return stats


def get_indicator_by_event(
    optimal_trades: List[Dict[str, Any]],
    indicator: str
) -> Dict[str, Dict[str, Any]]:
    """Get indicator statistics by event type (ENTRY, MFE, MAE, EXIT)."""
    if not optimal_trades:
        return {}

    df = pd.DataFrame(optimal_trades)

    if "event_type" not in df.columns or indicator not in df.columns:
        return {}

    results = {}
    for event in ["ENTRY", "MFE", "MAE", "EXIT"]:
        event_df = df[df["event_type"] == event]
        if len(event_df) > 0:
            series = pd.to_numeric(event_df[indicator], errors="coerce")
            results[event] = {
                "count": len(event_df),
                "mean": round(series.mean(), 4) if pd.notna(series.mean()) else None,
                "median": round(series.median(), 4) if pd.notna(series.median()) else None,
                "std": round(series.std(), 4) if pd.notna(series.std()) else None
            }

    return results


def get_indicator_by_outcome(
    data: List[Dict[str, Any]],
    indicator: str
) -> Dict[str, Dict[str, Any]]:
    """Get indicator statistics by win/loss outcome."""
    if not data:
        return {}

    df = pd.DataFrame(data)

    win_col = "win" if "win" in df.columns else "is_winner"
    if win_col not in df.columns or indicator not in df.columns:
        return {}

    results = {}

    # Winners
    if win_col == "win":
        winners = df[df[win_col] == 1]
        losers = df[df[win_col] == 0]
    else:
        winners = df[df[win_col] == True]
        losers = df[df[win_col] == False]

    for label, subset in [("WIN", winners), ("LOSS", losers)]:
        if len(subset) > 0:
            series = pd.to_numeric(subset[indicator], errors="coerce")
            results[label] = {
                "count": len(subset),
                "mean": round(series.mean(), 4) if pd.notna(series.mean()) else None,
                "median": round(series.median(), 4) if pd.notna(series.median()) else None,
                "std": round(series.std(), 4) if pd.notna(series.std()) else None
            }

    return results


def get_health_distribution(
    data: List[Dict[str, Any]],
    by_outcome: bool = True
) -> Dict[str, Any]:
    """Get health score distribution."""
    if not data:
        return {}

    df = pd.DataFrame(data)

    if "health_score" not in df.columns:
        return {}

    results = {"overall": df["health_score"].value_counts().to_dict()}

    if by_outcome:
        win_col = "win" if "win" in df.columns else "is_winner"
        if win_col in df.columns:
            if win_col == "win":
                winners = df[df[win_col] == 1]
                losers = df[df[win_col] == 0]
            else:
                winners = df[df[win_col] == True]
                losers = df[df[win_col] == False]

            results["winners"] = winners["health_score"].value_counts().to_dict()
            results["losers"] = losers["health_score"].value_counts().to_dict()

    return results


def get_indicator_stats_by_event(
    optimal_trades: List[Dict[str, Any]],
    indicator: str
) -> Dict[str, Dict[str, Any]]:
    """Get indicator statistics by event type (ENTRY, MFE, MAE, EXIT).

    Alias for get_indicator_by_event for compatibility.
    """
    return get_indicator_by_event(optimal_trades, indicator)


def get_indicator_comparison_by_outcome(
    data: List[Dict[str, Any]]
) -> Dict[str, Dict[str, float]]:
    """Get average indicator values for winners vs losers."""
    if not data:
        return {}

    df = pd.DataFrame(data)

    win_col = "win" if "win" in df.columns else "is_winner"
    if win_col not in df.columns:
        return {}

    if win_col == "win":
        winners = df[df[win_col] == 1]
        losers = df[df[win_col] != 1]
    else:
        winners = df[df[win_col] == True]
        losers = df[df[win_col] == False]

    results = {"winners": {}, "losers": {}}

    for col in INDICATOR_COLUMNS + ["sma_momentum"]:
        if col in df.columns:
            win_series = pd.to_numeric(winners[col], errors="coerce")
            loss_series = pd.to_numeric(losers[col], errors="coerce")

            win_mean = win_series.mean()
            loss_mean = loss_series.mean()

            results["winners"][col] = round(win_mean, 4) if pd.notna(win_mean) else 0.0
            results["losers"][col] = round(loss_mean, 4) if pd.notna(loss_mean) else 0.0

    return results
