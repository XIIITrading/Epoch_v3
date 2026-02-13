"""
Zone Calculator - Confluence Zone Scoring Engine

Ported from: 02_zone_system/05_raw_zones/epoch_calc_engine.py

Key features:
- Creates zones around each HVN POC (POC +/- m15_atr/2)
- Calculates confluence with all technical levels
- Tracks max weight per bucket type (no stacking)
- Assigns L1-L5 ranks based on total score
"""
import logging
from datetime import date
from typing import Dict, List, Optional, Tuple

from core import (
    BarData,
    HVNResult,
    RawZone,
    Direction,
    Rank,
    MarketStructure,
)
from config.weights import (
    EPOCH_POC_BASE_WEIGHTS,
    ZONE_WEIGHTS,
    CAM_WEIGHTS,
    BUCKET_WEIGHTS,
    ZONE_NAME_MAP,
    get_rank_from_score,
)

logger = logging.getLogger(__name__)


class ZoneCalculator:
    """
    Calculate confluence zones from HVN POCs and technical levels.

    Zone Creation:
    - zone_high = hvn_poc + (m15_atr / 2)
    - zone_low = hvn_poc - (m15_atr / 2)

    Confluence Scoring:
    - Check overlap with all technical levels
    - Track max weight per bucket type (no stacking beyond max)
    - total_score = base_score + sum(bucket_scores)
    """

    # Configuration
    ZONE_ATR_DIVISOR = 2.0  # Zone = POC +/- (M15_ATR / 2)
    DEFAULT_ATR = 1.0       # Fallback if ATR not available

    def __init__(self):
        """Initialize the zone calculator."""
        pass

    def calculate(
        self,
        bar_data: BarData,
        hvn_result: HVNResult,
        direction: Direction = Direction.NEUTRAL,
        market_structure: Optional[MarketStructure] = None
    ) -> List[RawZone]:
        """
        Calculate confluence zones for all HVN POCs.

        Args:
            bar_data: BarData with all technical levels
            hvn_result: HVNResult with POCs
            direction: Market direction for zone classification
            market_structure: Optional market structure data

        Returns:
            List of RawZone objects sorted by score descending
        """
        ticker = bar_data.ticker
        logger.info(f"Zone Calculator: Processing {ticker}")

        # Get ATR for zone calculation
        m15_atr = bar_data.m15_atr or bar_data.h1_atr or self.DEFAULT_ATR
        m5_atr = bar_data.m5_atr or (m15_atr / 2)

        logger.debug(f"  Using M15 ATR: ${m15_atr:.4f}, M5 ATR: ${m5_atr:.4f}")

        # Build all confluence zones from technical levels
        confluence_zones = self._build_confluence_zones(
            bar_data, market_structure, m15_atr, m5_atr
        )
        logger.info(f"  Built {len(confluence_zones)} confluence zones from technical levels")

        # Process each HVN POC
        raw_zones = []
        for poc in hvn_result.pocs:
            zone = self._calculate_zone_confluence(
                bar_data=bar_data,
                poc_rank=poc.rank,
                poc_price=poc.price,
                m15_atr=m15_atr,
                confluence_zones=confluence_zones,
                direction=direction
            )
            raw_zones.append(zone)
            logger.debug(
                f"    POC{poc.rank}: {poc.price:.2f}, "
                f"Score={zone.score:.1f}, Rank={zone.rank.value}"
            )

        # Sort by score descending
        raw_zones.sort(key=lambda z: z.score, reverse=True)

        # Log summary
        rank_counts = {}
        for zone in raw_zones:
            rank_counts[zone.rank.value] = rank_counts.get(zone.rank.value, 0) + 1

        logger.info(f"  Results for {ticker}:")
        logger.info(f"    Total zones: {len(raw_zones)}")
        for rank in ['L5', 'L4', 'L3', 'L2', 'L1']:
            if rank in rank_counts:
                logger.info(f"    {rank}: {rank_counts[rank]}")

        return raw_zones

    def _build_confluence_zones(
        self,
        bar_data: BarData,
        market_structure: Optional[MarketStructure],
        m15_atr: float,
        m5_atr: float
    ) -> Dict[str, Dict]:
        """
        Build zones around all technical levels for confluence checking.

        Each confluence zone has:
        - midpoint: The technical level price
        - high: midpoint + (atr / 2)
        - low: midpoint - (atr / 2)
        - weight: Confluence weight from config
        - con_type: Bucket type for max weight tracking
        """
        zones = {}

        # Get all levels from bar_data
        all_levels = bar_data.get_all_levels()

        # ATR values for different zone types
        atr_values = {
            'm5': m5_atr,
            'm15': m15_atr,
        }

        # Process OHLC levels (monthly, weekly, daily)
        for level_key, level_value in all_levels.items():
            if level_value is None:
                continue

            # Get weight configuration
            zone_config = ZONE_WEIGHTS.get(level_key) or CAM_WEIGHTS.get(level_key)

            if zone_config:
                zone_atr = zone_config.get('zone_atr', 'm15')
                atr_half = atr_values.get(zone_atr, m15_atr) / 2

                zones[level_key] = {
                    'midpoint': level_value,
                    'high': level_value + atr_half,
                    'low': level_value - atr_half,
                    'weight': zone_config.get('weight', 1.0),
                    'con_type': zone_config.get('con_type', 'unknown'),
                }

        # Add market structure levels if available
        if market_structure:
            ms_levels = self._extract_market_structure_levels(market_structure)
            for level_key, level_value in ms_levels.items():
                if level_value is None:
                    continue

                zone_config = ZONE_WEIGHTS.get(level_key, {})
                atr_half = m5_atr / 2  # Market structure uses tight ATR

                zones[level_key] = {
                    'midpoint': level_value,
                    'high': level_value + atr_half,
                    'low': level_value - atr_half,
                    'weight': zone_config.get('weight', 1.0),
                    'con_type': zone_config.get('con_type', 'market_structure_daily'),
                }

        return zones

    def _extract_market_structure_levels(
        self,
        market_structure: MarketStructure
    ) -> Dict[str, Optional[float]]:
        """Extract market structure levels into standardized keys."""
        return {
            'd1_s': market_structure.d1.strong,
            'd1_w': market_structure.d1.weak,
            'h4_s': market_structure.h4.strong,
            'h4_w': market_structure.h4.weak,
            'h1_s': market_structure.h1.strong,
            'h1_w': market_structure.h1.weak,
            'm15_s': market_structure.m15.strong,
            'm15_w': market_structure.m15.weak,
        }

    def _calculate_zone_confluence(
        self,
        bar_data: BarData,
        poc_rank: int,
        poc_price: float,
        m15_atr: float,
        confluence_zones: Dict[str, Dict],
        direction: Direction
    ) -> RawZone:
        """
        Calculate confluence for one HVN POC zone.

        Args:
            bar_data: Source bar data
            poc_rank: POC rank (1-10)
            poc_price: The POC price level
            m15_atr: M15 ATR for zone calculation
            confluence_zones: All technical levels as zones
            direction: Market direction

        Returns:
            RawZone with confluence data
        """
        # Create zone boundaries
        zone_high = poc_price + (m15_atr / self.ZONE_ATR_DIVISOR)
        zone_low = poc_price - (m15_atr / self.ZONE_ATR_DIVISOR)

        # Initialize bucket tracking (max weight per bucket type)
        bucket_scores = {bucket: 0.0 for bucket in BUCKET_WEIGHTS.keys()}
        overlapping_zones = []
        overlapping_names = []

        # Check overlap with all confluence zones
        for zone_id, zone_data in confluence_zones.items():
            zone_h = zone_data['high']
            zone_l = zone_data['low']

            # Check for ANY overlap
            if zone_low < zone_h and zone_high > zone_l:
                weight = zone_data['weight']
                con_type = zone_data['con_type']

                overlapping_zones.append(zone_id)
                overlapping_names.append(self._get_zone_display_name(zone_id))

                # Track MAX weight per bucket (no stacking)
                if con_type in bucket_scores:
                    bucket_scores[con_type] = max(bucket_scores[con_type], weight)

        # Calculate scores
        bucket_total = sum(bucket_scores.values())
        poc_key = f'hvn_poc{poc_rank}'
        base_score = EPOCH_POC_BASE_WEIGHTS.get(poc_key, 0)
        total_score = bucket_total + base_score

        # Assign rank
        rank_str = get_rank_from_score(total_score)
        rank = Rank(rank_str)

        # Limit confluences to top 6 for display
        if len(overlapping_names) > 6:
            display_confluences = overlapping_names[:6]
            display_confluences.append(f'+{len(overlapping_names) - 6} more')
        else:
            display_confluences = overlapping_names

        return RawZone(
            ticker=bar_data.ticker,
            ticker_id=bar_data.ticker_id,
            analysis_date=bar_data.analysis_date,
            price=bar_data.price,
            direction=direction,
            zone_id=poc_key,
            poc_rank=poc_rank,
            hvn_poc=round(poc_price, 2),
            zone_high=round(zone_high, 2),
            zone_low=round(zone_low, 2),
            overlaps=len(overlapping_zones),
            score=round(total_score, 2),
            rank=rank,
            confluences=display_confluences,
        )

    def _get_zone_display_name(self, zone_id: str) -> str:
        """Get human-readable name for a zone key."""
        return ZONE_NAME_MAP.get(zone_id, zone_id)


# =========================================================================
# CONVENIENCE FUNCTION
# =========================================================================

def calculate_zones(
    bar_data: BarData,
    hvn_result: HVNResult,
    direction: Direction = Direction.NEUTRAL,
    market_structure: Optional[MarketStructure] = None
) -> List[RawZone]:
    """
    Calculate confluence zones for a ticker.

    This is the main entry point for zone calculation.

    Args:
        bar_data: BarData with all technical levels
        hvn_result: HVNResult with POCs
        direction: Market direction for zone classification
        market_structure: Optional market structure data

    Returns:
        List of RawZone objects sorted by score descending
    """
    calculator = ZoneCalculator()
    return calculator.calculate(
        bar_data=bar_data,
        hvn_result=hvn_result,
        direction=direction,
        market_structure=market_structure
    )
