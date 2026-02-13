"""
HVN (High Volume Node) Identifier - Volume Profile POC Calculator

Ported from: 02_zone_system/04_hvn_identifier/calculations/epoch_hvn_identifier.py

Key features:
- $0.01 price granularity for volume profile
- Single user-defined epoch period (anchor_date to analysis_date)
- 10 non-overlapping POCs ranked by volume (highest volume = poc1)
- ATR/2 overlap prevention threshold
- Includes all market hours (pre/post/RTH)
"""
import logging
from datetime import date, datetime, timedelta
from math import floor, ceil
from typing import Dict, List, Optional, Tuple

import pandas as pd
import numpy as np

from data import get_polygon_client, cache, get_cache_key
from core import POCResult, HVNResult
from config import CACHE_TTL_DAILY

logger = logging.getLogger(__name__)


class HVNIdentifier:
    """
    Calculate HVN POCs for user-defined epoch periods.

    Key features:
    - $0.01 price granularity
    - Single epoch period (anchor_date to analysis_date)
    - 10 non-overlapping POCs ranked by volume
    - ATR/2 overlap prevention
    """

    # Configuration (matches Excel: 02_zone_system/04_hvn_identifier/config.py)
    PRICE_GRANULARITY = 0.01  # $0.01 per level
    POC_COUNT = 10            # Top 10 POCs
    OVERLAP_ATR_DIVISOR = 2   # Overlap threshold = ATR / 2
    DEFAULT_ATR = 2.0         # Fallback ATR if calculation fails
    CHUNK_DAYS = 30           # Days per API request for minute data (matches Excel CHUNK_SIZE_DAYS)

    def __init__(self):
        """Initialize the HVN Identifier."""
        self.client = get_polygon_client()

    def calculate(
        self,
        ticker: str,
        anchor_date: date,
        analysis_date: date = None,
        atr_value: float = None,
        end_timestamp: datetime = None
    ) -> HVNResult:
        """
        Calculate HVN POCs for the epoch period.

        Args:
            ticker: Stock symbol (e.g., "AAPL")
            anchor_date: Epoch start date (user-defined)
            analysis_date: Epoch end date (defaults to today)
            atr_value: D1 ATR for overlap calculation (calculates if not provided)
            end_timestamp: Optional precise end timestamp for pre/post market mode

        Returns:
            HVNResult with 10 non-overlapping POCs ranked by volume
        """
        ticker = ticker.upper().strip()
        analysis_date = analysis_date or date.today()

        # Include end_timestamp in cache key if provided
        cache_suffix = end_timestamp.isoformat() if end_timestamp else "live"
        logger.info(f"HVN Analysis: {ticker} from {anchor_date} to {analysis_date} (mode: {cache_suffix})")

        # Check cache first
        cache_key = get_cache_key(
            "hvn", ticker, str(anchor_date), str(analysis_date), cache_suffix
        )
        cached = cache.get_object(cache_key, ttl_seconds=CACHE_TTL_DAILY)
        if cached:
            logger.info(f"Using cached HVN result for {ticker}")
            return cached

        # Fetch minute data for the epoch
        bars = self._fetch_minute_data(ticker, anchor_date, analysis_date, end_timestamp)

        if bars.empty:
            logger.error(f"No data available for {ticker} in epoch period")
            return self._empty_result(ticker, anchor_date, analysis_date)

        logger.info(f"Loaded {len(bars)} minute bars for {ticker}")

        # Build volume profile at $0.01 granularity
        volume_profile = self._build_volume_profile(bars)

        if not volume_profile:
            logger.error(f"Could not build volume profile for {ticker}")
            return self._empty_result(ticker, anchor_date, analysis_date)

        logger.info(f"Built volume profile with {len(volume_profile)} price levels")

        # Determine ATR for overlap threshold
        if atr_value is None or atr_value <= 0:
            atr_value = self._calculate_simple_atr(bars)
            logger.info(f"Calculated ATR from data: ${atr_value:.2f}")
        else:
            logger.info(f"Using provided ATR: ${atr_value:.2f}")

        # Select top 10 non-overlapping POCs by volume
        pocs = self._select_pocs_no_overlap(volume_profile, atr_value)

        logger.info(f"Selected {len(pocs)} non-overlapping POCs")

        # Calculate totals
        total_volume = sum(volume_profile.values())
        price_range = (min(volume_profile.keys()), max(volume_profile.keys()))

        result = HVNResult(
            ticker=ticker,
            start_date=anchor_date,
            end_date=analysis_date,
            bars_analyzed=len(bars),
            total_volume=total_volume,
            price_range_low=price_range[0],
            price_range_high=price_range[1],
            atr_used=atr_value,
            pocs=pocs
        )

        # Cache the result
        cache.set_object(cache_key, result)

        return result

    def _fetch_minute_data(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
        end_timestamp: datetime = None
    ) -> pd.DataFrame:
        """
        Fetch 1-minute bars for the epoch period.
        Uses chunked requests to handle long date ranges.

        Args:
            ticker: Stock symbol
            start_date: Start date
            end_date: End date
            end_timestamp: Optional precise end timestamp for pre/post market mode
        """
        return self.client.fetch_minute_bars_chunked(
            ticker,
            start_date,
            end_date,
            multiplier=1,
            chunk_days=self.CHUNK_DAYS,
            end_timestamp=end_timestamp
        )

    def _build_volume_profile(self, bars: pd.DataFrame) -> Dict[float, float]:
        """
        Build volume profile at $0.01 granularity.

        For each bar, volume is distributed proportionally across all price levels
        touched by that bar (from low to high).

        Args:
            bars: DataFrame with OHLCV data

        Returns:
            Dict mapping price level (rounded to $0.01) to total volume
        """
        volume_profile: Dict[float, float] = {}

        for _, bar in bars.iterrows():
            bar_low = bar['low']
            bar_high = bar['high']
            bar_volume = bar['volume']

            # Skip invalid bars
            if bar_volume <= 0 or bar_high <= bar_low:
                continue

            if pd.isna(bar_low) or pd.isna(bar_high) or pd.isna(bar_volume):
                continue

            # Round to $0.01 boundaries
            low_level = floor(bar_low / self.PRICE_GRANULARITY) * self.PRICE_GRANULARITY
            high_level = ceil(bar_high / self.PRICE_GRANULARITY) * self.PRICE_GRANULARITY

            # Count number of $0.01 levels in this bar's range
            num_levels = int(round((high_level - low_level) / self.PRICE_GRANULARITY)) + 1

            if num_levels <= 0:
                continue

            # Distribute volume evenly across all levels
            volume_per_level = bar_volume / num_levels

            # Add volume to each price level
            current = low_level
            for _ in range(num_levels):
                price_key = round(current, 2)
                volume_profile[price_key] = volume_profile.get(price_key, 0) + volume_per_level
                current += self.PRICE_GRANULARITY

        return volume_profile

    def _calculate_simple_atr(self, bars: pd.DataFrame, period: int = 14) -> float:
        """
        Calculate a simple ATR from the minute data.
        Aggregates to daily bars first, then calculates ATR.

        Args:
            bars: Minute-level OHLCV DataFrame
            period: ATR lookback period (default 14 days)

        Returns:
            ATR value, or default if calculation fails
        """
        try:
            # Ensure timestamp is the index and is datetime
            if 'timestamp' in bars.columns:
                bars = bars.set_index('timestamp')

            # Resample to daily bars
            daily = bars.resample('D').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()

            if len(daily) < period:
                logger.warning(f"Not enough daily bars for ATR ({len(daily)} < {period}), using default")
                return self.DEFAULT_ATR

            # Calculate True Range
            daily['prev_close'] = daily['close'].shift(1)
            daily['tr1'] = daily['high'] - daily['low']
            daily['tr2'] = abs(daily['high'] - daily['prev_close'])
            daily['tr3'] = abs(daily['low'] - daily['prev_close'])
            daily['true_range'] = daily[['tr1', 'tr2', 'tr3']].max(axis=1)

            # Calculate ATR as simple moving average of True Range
            atr = daily['true_range'].tail(period).mean()

            if pd.isna(atr) or atr <= 0:
                return self.DEFAULT_ATR

            return round(atr, 2)

        except Exception as e:
            logger.warning(f"ATR calculation failed: {e}, using default")
            return self.DEFAULT_ATR

    def _select_pocs_no_overlap(
        self,
        volume_profile: Dict[float, float],
        atr: float
    ) -> List[POCResult]:
        """
        Select top POCs ensuring no overlap (minimum ATR/2 distance apart).

        POCs are ranked purely by volume (highest volume = poc1).
        No two POCs can be within ATR/2 of each other.

        Args:
            volume_profile: Dict of price -> volume
            atr: ATR value for overlap threshold

        Returns:
            List of POCResult objects, ranked by volume (rank 1 = highest)
        """
        overlap_threshold = atr / self.OVERLAP_ATR_DIVISOR

        logger.debug(f"Overlap threshold: ${overlap_threshold:.2f} (ATR/2)")

        # Sort all price levels by volume descending
        sorted_levels = sorted(
            volume_profile.items(),
            key=lambda x: x[1],
            reverse=True
        )

        selected_pocs: List[POCResult] = []

        for price, volume in sorted_levels:
            # Check if this price overlaps with any already-selected POC
            has_overlap = False

            for existing_poc in selected_pocs:
                if abs(price - existing_poc.price) < overlap_threshold:
                    has_overlap = True
                    break

            # Add if no overlap
            if not has_overlap:
                rank = len(selected_pocs) + 1
                selected_pocs.append(POCResult(
                    price=round(price, 2),
                    volume=volume,
                    rank=rank
                ))

            # Stop when we have enough POCs
            if len(selected_pocs) >= self.POC_COUNT:
                break

        return selected_pocs

    def _empty_result(
        self,
        ticker: str,
        start_date: date,
        end_date: date
    ) -> HVNResult:
        """Create an empty result when analysis fails."""
        return HVNResult(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            bars_analyzed=0,
            total_volume=0.0,
            price_range_low=None,
            price_range_high=None,
            atr_used=self.DEFAULT_ATR,
            pocs=[]
        )


# =========================================================================
# CONVENIENCE FUNCTION
# =========================================================================

def calculate_hvn(
    ticker: str,
    anchor_date: date,
    analysis_date: date = None,
    atr_value: float = None,
    end_timestamp: datetime = None
) -> HVNResult:
    """
    Calculate HVN POCs for a ticker.

    This is the main entry point for HVN calculation.

    Args:
        ticker: Stock symbol
        anchor_date: Epoch start date (user-defined anchor)
        analysis_date: Epoch end date (defaults to today)
        atr_value: D1 ATR for overlap calculation
        end_timestamp: Optional precise end timestamp for pre/post market mode

    Returns:
        HVNResult with 10 non-overlapping POCs
    """
    identifier = HVNIdentifier()
    return identifier.calculate(
        ticker=ticker,
        anchor_date=anchor_date,
        analysis_date=analysis_date,
        atr_value=atr_value,
        end_timestamp=end_timestamp
    )
