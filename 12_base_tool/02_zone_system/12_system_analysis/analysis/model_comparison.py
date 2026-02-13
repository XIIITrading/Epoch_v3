"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Model Comparison (Continuation vs Rejection)
XIII Trading LLC
================================================================================

Functions for comparing continuation (EPCH1/3) vs rejection (EPCH2/4) models.
================================================================================
"""

from typing import List, Dict, Any
import pandas as pd

from .trade_stats import get_trade_statistics
from .indicator_stats import get_indicator_averages


def compare_continuation_vs_rejection(
    trades: List[Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:
    """Compare continuation and rejection trade performance."""
    if not trades:
        return {}

    df = pd.DataFrame(trades)

    if "model" not in df.columns:
        return {}

    continuation_df = df[df["model"].isin(["EPCH1", "EPCH3"])]
    rejection_df = df[df["model"].isin(["EPCH2", "EPCH4"])]

    return {
        "continuation": get_trade_statistics(continuation_df.to_dict("records")),
        "rejection": get_trade_statistics(rejection_df.to_dict("records"))
    }


def compare_primary_vs_secondary(
    trades: List[Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:
    """Compare primary zone (EPCH1/2) vs secondary zone (EPCH3/4) trades."""
    if not trades:
        return {}

    df = pd.DataFrame(trades)

    if "model" not in df.columns:
        return {}

    primary_df = df[df["model"].isin(["EPCH1", "EPCH2"])]
    secondary_df = df[df["model"].isin(["EPCH3", "EPCH4"])]

    return {
        "primary": get_trade_statistics(primary_df.to_dict("records")),
        "secondary": get_trade_statistics(secondary_df.to_dict("records"))
    }


def get_indicator_comparison_by_trade_type(
    optimal_trades: List[Dict[str, Any]],
    event_type: str = "ENTRY"
) -> Dict[str, Dict[str, Any]]:
    """Compare indicator values at entry for continuation vs rejection trades."""
    if not optimal_trades:
        return {}

    df = pd.DataFrame(optimal_trades)

    if "model" not in df.columns or "event_type" not in df.columns:
        return {}

    event_df = df[df["event_type"] == event_type]

    continuation_df = event_df[event_df["model"].isin(["EPCH1", "EPCH3"])]
    rejection_df = event_df[event_df["model"].isin(["EPCH2", "EPCH4"])]

    return {
        "continuation": get_indicator_averages(continuation_df.to_dict("records")),
        "rejection": get_indicator_averages(rejection_df.to_dict("records"))
    }


def get_win_rate_by_model_and_indicator(
    optimal_trades: List[Dict[str, Any]],
    indicator: str,
    threshold: float
) -> Dict[str, Dict[str, float]]:
    """Calculate win rate when indicator is above/below threshold."""
    if not optimal_trades:
        return {}

    df = pd.DataFrame(optimal_trades)

    if indicator not in df.columns or "model" not in df.columns:
        return {}

    entry_df = df[df["event_type"] == "ENTRY"]
    results = {}

    for model in ["EPCH1", "EPCH2", "EPCH3", "EPCH4"]:
        model_df = entry_df[entry_df["model"] == model]

        if len(model_df) == 0:
            continue

        above = model_df[pd.to_numeric(model_df[indicator], errors="coerce") > threshold]
        below = model_df[pd.to_numeric(model_df[indicator], errors="coerce") <= threshold]

        win_col = "win" if "win" in model_df.columns else None
        if win_col is None:
            continue

        above_wins = len(above[above[win_col] == 1])
        below_wins = len(below[below[win_col] == 1])

        results[model] = {
            "above_threshold_count": len(above),
            "above_threshold_wins": above_wins,
            "above_threshold_win_rate": round(above_wins / len(above) * 100, 2) if len(above) > 0 else 0,
            "below_threshold_count": len(below),
            "below_threshold_wins": below_wins,
            "below_threshold_win_rate": round(below_wins / len(below) * 100, 2) if len(below) > 0 else 0,
        }

    return results
