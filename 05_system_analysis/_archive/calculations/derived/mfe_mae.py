"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
MFE/MAE (Maximum Favorable/Adverse Excursion) Calculation
XIII Trading LLC
================================================================================

MFE: Best R achieved during trade (max high for LONG, min low for SHORT)
MAE: Worst R achieved during trade (min low for LONG, max high for SHORT)
================================================================================
"""

from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class MFEMAEResult:
    mfe_bar_index: int
    mfe_price: float
    mfe_r: Optional[float]
    mae_bar_index: int
    mae_price: float
    mae_r: Optional[float]
    bars_to_mfe: int
    bars_to_mae: int


def find_mfe_bar(bars: List[Dict], direction: str) -> Optional[Dict]:
    """Find the bar with Maximum Favorable Excursion."""
    if not bars:
        return None

    is_long = direction.upper() == "LONG"

    if is_long:
        return max(bars, key=lambda b: _safe_float(b.get("high_price") or b.get("high"), 0))
    else:
        return min(bars, key=lambda b: _safe_float(b.get("low_price") or b.get("low"), float('inf')))


def find_mae_bar(bars: List[Dict], direction: str) -> Optional[Dict]:
    """Find the bar with Maximum Adverse Excursion."""
    if not bars:
        return None

    is_long = direction.upper() == "LONG"

    if is_long:
        return min(bars, key=lambda b: _safe_float(b.get("low_price") or b.get("low"), float('inf')))
    else:
        return max(bars, key=lambda b: _safe_float(b.get("high_price") or b.get("high"), 0))


def calculate_mfe_mae(
    bars: List[Dict],
    direction: str,
    entry_price: float,
    risk: float
) -> MFEMAEResult:
    """Calculate MFE and MAE with R-multiples."""
    if not bars or risk == 0:
        return MFEMAEResult(
            mfe_bar_index=0, mfe_price=entry_price, mfe_r=0,
            mae_bar_index=0, mae_price=entry_price, mae_r=0,
            bars_to_mfe=0, bars_to_mae=0
        )

    is_long = direction.upper() == "LONG"

    mfe_bar = find_mfe_bar(bars, direction)
    mae_bar = find_mae_bar(bars, direction)

    mfe_idx = bars.index(mfe_bar) if mfe_bar else 0
    mae_idx = bars.index(mae_bar) if mae_bar else 0

    if is_long:
        mfe_price = _safe_float(mfe_bar.get("high_price") or mfe_bar.get("high"), entry_price) if mfe_bar else entry_price
        mae_price = _safe_float(mae_bar.get("low_price") or mae_bar.get("low"), entry_price) if mae_bar else entry_price
        mfe_r = (mfe_price - entry_price) / risk
        mae_r = (mae_price - entry_price) / risk
    else:
        mfe_price = _safe_float(mfe_bar.get("low_price") or mfe_bar.get("low"), entry_price) if mfe_bar else entry_price
        mae_price = _safe_float(mae_bar.get("high_price") or mae_bar.get("high"), entry_price) if mae_bar else entry_price
        mfe_r = (entry_price - mfe_price) / risk
        mae_r = (entry_price - mae_price) / risk

    return MFEMAEResult(
        mfe_bar_index=mfe_idx,
        mfe_price=mfe_price,
        mfe_r=mfe_r,
        mae_bar_index=mae_idx,
        mae_price=mae_price,
        mae_r=mae_r,
        bars_to_mfe=mfe_idx,
        bars_to_mae=mae_idx
    )


def _safe_float(value, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default
