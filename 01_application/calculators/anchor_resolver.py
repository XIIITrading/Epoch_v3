"""
Auto-Anchor Resolver
Epoch Trading System v2.0 - XIII Trading LLC

Resolves anchor dates automatically using volume-based lookback.
Looks back 6 months of daily bars and identifies the single largest
volume day as the anchor date.
"""
import logging
from datetime import date, timedelta
from typing import Dict, Optional, Tuple

from config import MAX_VOLUME_LOOKBACK_DAYS, MAX_VOLUME_THRESHOLD_PCT
from data import get_polygon_client

logger = logging.getLogger(__name__)


def find_max_volume_anchor(
    ticker: str,
    analysis_date: date,
    lookback_days: int = MAX_VOLUME_LOOKBACK_DAYS,
) -> Tuple[date, Dict]:
    """
    Find the anchor date by identifying the largest volume day
    in the lookback window.

    Fetches daily bars for the lookback period and selects the day
    with the highest volume. Checks if it exceeds the second-highest
    by >= 20% (dominance threshold).

    Args:
        ticker: Stock symbol
        analysis_date: Reference date for lookback
        lookback_days: Number of calendar days to look back (default 180)

    Returns:
        Tuple of (anchor_date, metadata_dict)
        metadata_dict contains:
            - max_volume: Volume on the selected day
            - max_volume_date: The selected anchor date
            - second_volume: Volume of the second-highest day
            - second_volume_date: Date of the second-highest day
            - exceeds_threshold: Whether the 20% dominance threshold was met
            - bars_checked: Number of daily bars analyzed
    """
    client = get_polygon_client()

    start_date = analysis_date - timedelta(days=lookback_days)
    end_date = analysis_date - timedelta(days=1)  # Exclude analysis date itself

    logger.info(f"Auto-anchor: fetching daily bars for {ticker} from {start_date} to {end_date}")

    df = client.fetch_daily_bars(ticker, start_date, end_date)

    if df.empty:
        # Fallback: prior month
        fallback = _get_fallback_anchor(analysis_date)
        logger.warning(f"Auto-anchor: no daily data for {ticker}, falling back to {fallback}")
        return fallback, {
            "max_volume": 0,
            "max_volume_date": fallback.isoformat(),
            "second_volume": 0,
            "second_volume_date": None,
            "exceeds_threshold": False,
            "bars_checked": 0,
            "fallback": True,
        }

    # Sort by volume descending to find top 2
    df_sorted = df.sort_values("volume", ascending=False).reset_index(drop=True)

    max_row = df_sorted.iloc[0]
    max_volume = float(max_row["volume"])
    max_date = max_row["date"]

    # Get second-highest
    second_volume = 0.0
    second_date = None
    if len(df_sorted) > 1:
        second_row = df_sorted.iloc[1]
        second_volume = float(second_row["volume"])
        second_date = second_row["date"]

    # Check 20% dominance threshold
    exceeds_threshold = False
    if second_volume > 0:
        dominance = (max_volume - second_volume) / second_volume
        exceeds_threshold = dominance >= MAX_VOLUME_THRESHOLD_PCT

    metadata = {
        "max_volume": max_volume,
        "max_volume_date": max_date.isoformat() if hasattr(max_date, 'isoformat') else str(max_date),
        "second_volume": second_volume,
        "second_volume_date": second_date.isoformat() if second_date and hasattr(second_date, 'isoformat') else str(second_date) if second_date else None,
        "exceeds_threshold": exceeds_threshold,
        "bars_checked": len(df),
        "fallback": False,
    }

    if not exceeds_threshold and second_volume > 0:
        pct = ((max_volume - second_volume) / second_volume) * 100
        logger.info(
            f"Auto-anchor: {ticker} max vol day {max_date} ({max_volume:,.0f}) "
            f"only exceeds 2nd ({second_volume:,.0f}) by {pct:.1f}% (threshold: {MAX_VOLUME_THRESHOLD_PCT*100:.0f}%)"
        )

    # Convert date type if needed (pandas Timestamp → python date)
    if hasattr(max_date, 'date'):
        anchor_date = max_date.date()
    elif isinstance(max_date, date):
        anchor_date = max_date
    else:
        from datetime import datetime as dt
        anchor_date = dt.strptime(str(max_date), '%Y-%m-%d').date()

    logger.info(f"Auto-anchor: {ticker} → {anchor_date} (vol: {max_volume:,.0f}, bars: {len(df)})")

    return anchor_date, metadata


def _get_fallback_anchor(analysis_date: date) -> date:
    """Get fallback anchor date (first of prior month)."""
    first_of_month = analysis_date.replace(day=1)
    prior_month = first_of_month - timedelta(days=1)
    return prior_month.replace(day=1)
