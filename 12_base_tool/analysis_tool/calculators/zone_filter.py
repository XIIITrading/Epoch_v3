"""
Zone Filter - Filter, Classify, and Identify Trading Setups

Ported from:
- 02_zone_system/06_zone_results/zone_filter.py
- 02_zone_system/07_setup_analysis/epoch_setup_analyzer.py

Key features:
- Tier classification (L-rank to T-tier)
- ATR distance calculation and proximity grouping
- Overlap elimination (highest score wins)
- Bull/Bear POC identification
- Primary/Secondary setup assignment
"""
import logging
from typing import Dict, List, Optional, Tuple

from core import (
    RawZone,
    FilteredZone,
    BarData,
    Direction,
    Rank,
    Tier,
)
from config.weights import TIER_MAP, get_tier_from_rank

logger = logging.getLogger(__name__)


# Configuration constants
ATR_GROUP_1_THRESHOLD = 1.0   # Within 1 ATR = Group 1 (closest)
ATR_GROUP_2_THRESHOLD = 2.0   # 1-2 ATR = Group 2
MAX_ZONES_PER_TICKER = 10     # Max zones to keep per ticker


class ZoneFilter:
    """
    Filter and classify zones for setup analysis.

    Pipeline:
    1. Add tier classification (T1/T2/T3)
    2. Calculate ATR distance from current price
    3. Assign proximity groups (Group 1/2 or excluded)
    4. Sort by proximity group, then score, then distance
    5. Eliminate overlapping zones (highest score wins)
    6. Identify bull/bear POCs (closest above/below price)
    """

    def __init__(
        self,
        atr_group_1_threshold: float = ATR_GROUP_1_THRESHOLD,
        atr_group_2_threshold: float = ATR_GROUP_2_THRESHOLD,
        max_zones_per_ticker: int = MAX_ZONES_PER_TICKER
    ):
        """
        Initialize the zone filter.

        Args:
            atr_group_1_threshold: ATR distance for Group 1 (default 1.0)
            atr_group_2_threshold: ATR distance for Group 2 (default 2.0)
            max_zones_per_ticker: Maximum zones to keep per ticker
        """
        self.atr_group_1_threshold = atr_group_1_threshold
        self.atr_group_2_threshold = atr_group_2_threshold
        self.max_zones_per_ticker = max_zones_per_ticker

    def filter_zones(
        self,
        raw_zones: List[RawZone],
        bar_data: BarData,
        direction: Direction = Direction.NEUTRAL
    ) -> List[FilteredZone]:
        """
        Execute complete filtering pipeline.

        Args:
            raw_zones: List of RawZone objects from zone calculator
            bar_data: BarData with price and ATR values
            direction: Market direction for setup classification

        Returns:
            List of FilteredZone objects, sorted and deduplicated
        """
        if not raw_zones:
            return []

        ticker = bar_data.ticker
        price = bar_data.price
        d1_atr = bar_data.d1_atr or 1.0  # Fallback if ATR not available

        logger.info(f"Zone Filter: Processing {len(raw_zones)} zones for {ticker}")
        logger.debug(f"  Price: ${price:.2f}, D1 ATR: ${d1_atr:.4f}")

        # Step 1: Convert to FilteredZone and add tier
        filtered_zones = self._add_tier_classification(raw_zones, direction)
        logger.debug(f"  Step 1: Tier classification complete")

        # Step 2: Add ATR distance and proximity group
        filtered_zones = self._add_proximity_data(filtered_zones, price, d1_atr)
        logger.debug(f"  Step 2: Proximity data added")

        # Step 3: Filter by proximity (within 2 ATR only)
        filtered_zones = self._filter_by_proximity(filtered_zones)
        logger.debug(f"  Step 3: Proximity filter - {len(filtered_zones)} zones remain")

        if not filtered_zones:
            logger.warning(f"  No zones within {self.atr_group_2_threshold} ATR of price")
            return []

        # Step 4: Sort by proximity group, then score, then distance
        filtered_zones = self._sort_zones(filtered_zones)
        logger.debug(f"  Step 4: Zones sorted")

        # Step 5: Eliminate overlapping zones
        filtered_zones = self._eliminate_overlaps(filtered_zones)
        logger.debug(f"  Step 5: Overlap elimination - {len(filtered_zones)} zones remain")

        # Step 6: Identify bull/bear POCs
        filtered_zones = self._identify_bull_bear_pocs(filtered_zones, price)
        logger.debug(f"  Step 6: Bull/Bear POCs identified")

        # Log summary
        self._log_summary(filtered_zones)

        return filtered_zones

    def _add_tier_classification(
        self,
        raw_zones: List[RawZone],
        direction: Direction
    ) -> List[FilteredZone]:
        """
        Convert RawZones to FilteredZones with tier classification.

        Tier mapping:
        - L1, L2 → T1 (Lower confluence quality)
        - L3 → T2 (Medium confluence quality)
        - L4, L5 → T3 (High confluence quality)
        """
        filtered_zones = []

        for zone in raw_zones:
            # Get tier from rank
            tier_str = get_tier_from_rank(zone.rank.value)
            tier = Tier(tier_str)

            # Create FilteredZone with all RawZone data plus tier
            filtered_zone = FilteredZone(
                # From RawZone
                ticker=zone.ticker,
                ticker_id=zone.ticker_id,
                analysis_date=zone.analysis_date,
                price=zone.price,
                direction=direction,
                zone_id=zone.zone_id,
                poc_rank=zone.poc_rank,
                hvn_poc=zone.hvn_poc,
                zone_high=zone.zone_high,
                zone_low=zone.zone_low,
                overlaps=zone.overlaps,
                score=zone.score,
                rank=zone.rank,
                confluences=zone.confluences,
                # FilteredZone additions
                tier=tier,
            )
            filtered_zones.append(filtered_zone)

        return filtered_zones

    def _add_proximity_data(
        self,
        zones: List[FilteredZone],
        price: float,
        d1_atr: float
    ) -> List[FilteredZone]:
        """
        Add ATR distance and proximity group to each zone.

        Proximity groups:
        - Group 1: Within 1 ATR of price
        - Group 2: 1-2 ATR from price
        - Excluded: Beyond 2 ATR
        """
        for zone in zones:
            # Calculate zone midpoint
            zone_midpoint = (zone.zone_high + zone.zone_low) / 2

            # Calculate ATR distance
            distance = abs(zone_midpoint - price)
            atr_distance = distance / d1_atr if d1_atr > 0 else float('inf')
            zone.atr_distance = round(atr_distance, 3)

            # Assign proximity group
            if atr_distance <= self.atr_group_1_threshold:
                zone.proximity_group = "1"  # Closest
            elif atr_distance <= self.atr_group_2_threshold:
                zone.proximity_group = "2"  # Medium
            else:
                zone.proximity_group = None  # Excluded

        return zones

    def _filter_by_proximity(
        self,
        zones: List[FilteredZone]
    ) -> List[FilteredZone]:
        """Remove zones beyond 2 ATR from current price."""
        return [z for z in zones if z.proximity_group is not None]

    def _sort_zones(
        self,
        zones: List[FilteredZone]
    ) -> List[FilteredZone]:
        """
        Sort zones by: proximity_group (asc), score (desc), atr_distance (asc).

        This ensures closest zones to price are prioritized, with higher
        scores breaking ties.
        """
        return sorted(
            zones,
            key=lambda z: (
                z.proximity_group or "9",  # None sorts last
                -z.score,                   # Higher score first
                z.atr_distance or float('inf')  # Closer first
            )
        )

    def _eliminate_overlaps(
        self,
        zones: List[FilteredZone]
    ) -> List[FilteredZone]:
        """
        Eliminate overlapping zones. Highest score wins.

        Two zones overlap if: zone1_low < zone2_high AND zone1_high > zone2_low
        """
        selected = []
        eliminated_count = 0

        for zone in zones:
            # Check if this zone overlaps with any already selected zone
            has_overlap = False

            for selected_zone in selected:
                if self._zones_overlap(zone, selected_zone):
                    has_overlap = True
                    eliminated_count += 1
                    break

            # Add zone if no overlap and haven't hit max limit
            if not has_overlap and len(selected) < self.max_zones_per_ticker:
                selected.append(zone)

        if eliminated_count > 0:
            logger.debug(f"    Eliminated {eliminated_count} overlapping zones")

        return selected

    def _zones_overlap(
        self,
        zone1: FilteredZone,
        zone2: FilteredZone
    ) -> bool:
        """Check if two zones overlap."""
        return (zone1.zone_low < zone2.zone_high and
                zone1.zone_high > zone2.zone_low)

    def _identify_bull_bear_pocs(
        self,
        zones: List[FilteredZone],
        price: float
    ) -> List[FilteredZone]:
        """
        Identify bull and bear POC anchor points.

        Bull POC: Minimum hvn_poc ABOVE current price (closest above)
        Bear POC: Maximum hvn_poc BELOW current price (closest below)
        """
        # Find bull POC (minimum above price)
        zones_above = [z for z in zones if z.hvn_poc > price]
        if zones_above:
            bull_poc_price = min(z.hvn_poc for z in zones_above)
            for zone in zones:
                if zone.hvn_poc == bull_poc_price:
                    zone.is_bull_poc = True

        # Find bear POC (maximum below price)
        zones_below = [z for z in zones if z.hvn_poc < price]
        if zones_below:
            bear_poc_price = max(z.hvn_poc for z in zones_below)
            for zone in zones:
                if zone.hvn_poc == bear_poc_price:
                    zone.is_bear_poc = True

        # Apply pivot logic: if only one exists, use for both
        has_bull = any(z.is_bull_poc for z in zones)
        has_bear = any(z.is_bear_poc for z in zones)

        if has_bull and not has_bear:
            # Use bull POC as bear pivot
            for zone in zones:
                if zone.is_bull_poc:
                    zone.is_bear_poc = True
        elif has_bear and not has_bull:
            # Use bear POC as bull pivot
            for zone in zones:
                if zone.is_bear_poc:
                    zone.is_bull_poc = True

        return zones

    def _log_summary(self, zones: List[FilteredZone]) -> None:
        """Log summary statistics for filtered zones."""
        if not zones:
            return

        # Tier distribution
        tier_counts = {}
        for zone in zones:
            tier_counts[zone.tier.value] = tier_counts.get(zone.tier.value, 0) + 1

        logger.info(f"  Final: {len(zones)} zones")
        logger.info(f"  Tiers: {tier_counts}")

        # Proximity group distribution
        group_counts = {}
        for zone in zones:
            group = zone.proximity_group or "excluded"
            group_counts[group] = group_counts.get(group, 0) + 1
        logger.info(f"  Proximity groups: {group_counts}")

        # Bull/Bear counts
        bull_count = sum(1 for z in zones if z.is_bull_poc)
        bear_count = sum(1 for z in zones if z.is_bear_poc)
        logger.info(f"  Bull POCs: {bull_count}, Bear POCs: {bear_count}")


# =========================================================================
# CONVENIENCE FUNCTION
# =========================================================================

def filter_zones(
    raw_zones: List[RawZone],
    bar_data: BarData,
    direction: Direction = Direction.NEUTRAL
) -> List[FilteredZone]:
    """
    Filter and classify zones for a ticker.

    This is the main entry point for zone filtering.

    Args:
        raw_zones: List of RawZone objects from zone calculator
        bar_data: BarData with price and ATR values
        direction: Market direction for setup classification

    Returns:
        List of FilteredZone objects, sorted and deduplicated
    """
    zone_filter = ZoneFilter()
    return zone_filter.filter_zones(
        raw_zones=raw_zones,
        bar_data=bar_data,
        direction=direction
    )
