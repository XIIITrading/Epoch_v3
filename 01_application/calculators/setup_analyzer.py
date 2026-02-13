"""
Setup Analyzer - Calculate targets and R:R for trading setups.

Ported from:
- 02_zone_system/07_setup_analysis/epoch_setup_analyzer.py

Key features:
- Target selection using 3R/4R HVN POC cascade
- R:R calculation for bull and bear setups
- Primary/Secondary assignment based on market direction
- Setup string generation for TradingView export
"""
import logging
from typing import Dict, List, Optional, Tuple

from core import (
    FilteredZone,
    HVNResult,
    BarData,
    Direction,
    Tier,
    Setup,
)

logger = logging.getLogger(__name__)


# Configuration constants (from epoch_config.py)
MIN_RR_THRESHOLD = 3.0    # 3R minimum for POC target selection
DEFAULT_RR_CALC = 4.0     # 4R fallback if no POC qualifies


class SetupAnalyzer:
    """
    Analyze filtered zones to identify trading setups with targets and R:R.

    Pipeline:
    1. Calculate targets using 3R/4R HVN POC cascade
    2. Calculate R:R ratios
    3. Assign primary/secondary based on market direction
    4. Generate setup strings for TradingView
    """

    def __init__(
        self,
        min_rr_threshold: float = MIN_RR_THRESHOLD,
        default_rr_calc: float = DEFAULT_RR_CALC
    ):
        """
        Initialize the setup analyzer.

        Args:
            min_rr_threshold: Minimum R:R for POC target selection (default 3.0)
            default_rr_calc: Default R:R for calculated targets (default 4.0)
        """
        self.min_rr_threshold = min_rr_threshold
        self.default_rr_calc = default_rr_calc

    def analyze_setups(
        self,
        filtered_zones: List[FilteredZone],
        hvn_result: HVNResult,
        bar_data: BarData,
        direction: Direction
    ) -> Tuple[Optional[Setup], Optional[Setup]]:
        """
        Analyze filtered zones to create primary and secondary setups.

        Args:
            filtered_zones: List of FilteredZone objects (must have bull/bear POC flags)
            hvn_result: HVNResult with all 10 POCs for target selection
            bar_data: BarData for price and zone risk calculations
            direction: Market direction (Bull/Bull+/Bear/Bear+/Neutral)

        Returns:
            Tuple of (primary_setup, secondary_setup)
        """
        if not filtered_zones:
            return None, None

        ticker = bar_data.ticker
        ticker_id = bar_data.ticker_id
        price = bar_data.price

        logger.info(f"Setup Analysis: Processing {len(filtered_zones)} zones for {ticker}")
        logger.debug(f"  Direction: {direction.value}, Price: ${price:.2f}")

        # Get all HVN POCs for target selection
        hvn_pocs = hvn_result.get_poc_prices()

        # Find bull and bear POC zones
        bull_zone = next((z for z in filtered_zones if z.is_bull_poc), None)
        bear_zone = next((z for z in filtered_zones if z.is_bear_poc), None)

        # Calculate targets for both directions
        bull_target, bull_target_id = self._calculate_bull_target(bull_zone, hvn_pocs)
        bear_target, bear_target_id = self._calculate_bear_target(bear_zone, hvn_pocs)

        logger.debug(f"  Bull target: {bull_target_id} = ${bull_target:.2f}" if bull_target else "  Bull target: N/A")
        logger.debug(f"  Bear target: {bear_target_id} = ${bear_target:.2f}" if bear_target else "  Bear target: N/A")

        # Create setups based on direction
        primary_setup, secondary_setup = self._create_setups(
            bull_zone=bull_zone,
            bear_zone=bear_zone,
            bull_target=bull_target,
            bull_target_id=bull_target_id,
            bear_target=bear_target,
            bear_target_id=bear_target_id,
            direction=direction,
            ticker=ticker,
            ticker_id=ticker_id
        )

        # Log summary
        if primary_setup:
            logger.info(f"  Primary: {primary_setup.direction.value} at ${primary_setup.hvn_poc:.2f} → ${primary_setup.target:.2f} ({primary_setup.risk_reward:.2f}R)")
        if secondary_setup:
            logger.info(f"  Secondary: {secondary_setup.direction.value} at ${secondary_setup.hvn_poc:.2f} → ${secondary_setup.target:.2f} ({secondary_setup.risk_reward:.2f}R)")

        return primary_setup, secondary_setup

    def _calculate_bull_target(
        self,
        zone: Optional[FilteredZone],
        hvn_pocs: List[float]
    ) -> Tuple[Optional[float], Optional[str]]:
        """
        Calculate bull target using 3R/4R HVN POC cascade.

        Bull target: Find POC ABOVE zone's hvn_poc that is >= 3R from zone_high.
        Priority: Lower index (higher volume) POC wins.
        Fallback: Calculated 4R level from zone_high.

        Args:
            zone: The bull POC zone
            hvn_pocs: List of all HVN POC prices in rank order

        Returns:
            Tuple of (target_price, target_id)
        """
        if not zone:
            return None, None

        zone_high = zone.zone_high
        zone_low = zone.zone_low
        hvn_poc = zone.hvn_poc
        zone_risk = zone_high - zone_low

        if zone_risk <= 0:
            return None, None

        # Calculate 3R and 4R thresholds
        target_3r = zone_high + (zone_risk * self.min_rr_threshold)
        target_4r = zone_high + (zone_risk * self.default_rr_calc)

        # Find POCs above hvn_poc that meet 3R threshold
        # Priority: lower index = higher volume
        bull_target = None
        bull_target_id = None

        for i, poc in enumerate(hvn_pocs):
            if poc is None:
                continue
            # POC must be above the zone's hvn_poc AND >= 3R from zone_high
            if poc > hvn_poc and poc >= target_3r:
                # Select by highest volume (lowest index)
                if bull_target is None:
                    bull_target = poc
                    bull_target_id = f"hvn_poc{i + 1}"
                elif i < int(bull_target_id.replace('hvn_poc', '')) - 1:
                    bull_target = poc
                    bull_target_id = f"hvn_poc{i + 1}"

        # If no POC meets 3R, use calculated 4R
        if bull_target is None:
            bull_target = target_4r
            bull_target_id = "4R_calc"

        return bull_target, bull_target_id

    def _calculate_bear_target(
        self,
        zone: Optional[FilteredZone],
        hvn_pocs: List[float]
    ) -> Tuple[Optional[float], Optional[str]]:
        """
        Calculate bear target using 3R/4R HVN POC cascade.

        Bear target: Find POC BELOW zone's hvn_poc that is <= 3R from zone_low.
        Priority: Lower index (higher volume) POC wins.
        Fallback: Calculated 4R level from zone_low.

        Args:
            zone: The bear POC zone
            hvn_pocs: List of all HVN POC prices in rank order

        Returns:
            Tuple of (target_price, target_id)
        """
        if not zone:
            return None, None

        zone_high = zone.zone_high
        zone_low = zone.zone_low
        hvn_poc = zone.hvn_poc
        zone_risk = zone_high - zone_low

        if zone_risk <= 0:
            return None, None

        # Calculate 3R and 4R thresholds
        target_3r = zone_low - (zone_risk * self.min_rr_threshold)
        target_4r = zone_low - (zone_risk * self.default_rr_calc)

        # Find POCs below hvn_poc that meet 3R threshold
        bear_target = None
        bear_target_id = None

        for i, poc in enumerate(hvn_pocs):
            if poc is None:
                continue
            # POC must be below the zone's hvn_poc AND <= 3R from zone_low
            if poc < hvn_poc and poc <= target_3r:
                # Select by highest volume (lowest index)
                if bear_target is None:
                    bear_target = poc
                    bear_target_id = f"hvn_poc{i + 1}"
                elif i < int(bear_target_id.replace('hvn_poc', '')) - 1:
                    bear_target = poc
                    bear_target_id = f"hvn_poc{i + 1}"

        # If no POC meets 3R, use calculated 4R
        if bear_target is None:
            bear_target = target_4r
            bear_target_id = "4R_calc"

        return bear_target, bear_target_id

    def _create_setups(
        self,
        bull_zone: Optional[FilteredZone],
        bear_zone: Optional[FilteredZone],
        bull_target: Optional[float],
        bull_target_id: Optional[str],
        bear_target: Optional[float],
        bear_target_id: Optional[str],
        direction: Direction,
        ticker: str,
        ticker_id: str
    ) -> Tuple[Optional[Setup], Optional[Setup]]:
        """
        Create primary and secondary setups based on market direction.

        Bull/Bull+ direction: Primary = Bull, Secondary = Bear
        Bear/Bear+ direction: Primary = Bear, Secondary = Bull
        Neutral: Primary = Bull (default), Secondary = Bear

        Args:
            bull_zone: Bull POC zone (if exists)
            bear_zone: Bear POC zone (if exists)
            bull_target: Calculated bull target price
            bull_target_id: Bull target identifier
            bear_target: Calculated bear target price
            bear_target_id: Bear target identifier
            direction: Market composite direction
            ticker: Ticker symbol
            ticker_id: Ticker ID

        Returns:
            Tuple of (primary_setup, secondary_setup)
        """
        primary_setup = None
        secondary_setup = None

        # Determine which direction is primary based on market composite
        if direction in [Direction.BULL, Direction.BULL_PLUS]:
            # Bull market: Primary = Bull (with trend), Secondary = Bear (counter-trend)
            if bull_zone and bull_target:
                primary_setup = self._create_setup(
                    zone=bull_zone,
                    target=bull_target,
                    target_id=bull_target_id,
                    setup_direction=Direction.BULL,
                    setup_type="Primary",
                    ticker=ticker,
                    ticker_id=ticker_id
                )

            if bear_zone and bear_target:
                secondary_setup = self._create_setup(
                    zone=bear_zone,
                    target=bear_target,
                    target_id=bear_target_id,
                    setup_direction=Direction.BEAR,
                    setup_type="Secondary",
                    ticker=ticker,
                    ticker_id=ticker_id
                )
            elif bull_zone and bear_target:
                # Use bull zone as secondary with bear direction (pivot logic)
                secondary_setup = self._create_setup(
                    zone=bull_zone,
                    target=bear_target,
                    target_id=bear_target_id,
                    setup_direction=Direction.BEAR,
                    setup_type="Secondary",
                    ticker=ticker,
                    ticker_id=ticker_id
                )

        elif direction in [Direction.BEAR, Direction.BEAR_PLUS]:
            # Bear market: Primary = Bear (with trend), Secondary = Bull (counter-trend)
            if bear_zone and bear_target:
                primary_setup = self._create_setup(
                    zone=bear_zone,
                    target=bear_target,
                    target_id=bear_target_id,
                    setup_direction=Direction.BEAR,
                    setup_type="Primary",
                    ticker=ticker,
                    ticker_id=ticker_id
                )

            if bull_zone and bull_target:
                secondary_setup = self._create_setup(
                    zone=bull_zone,
                    target=bull_target,
                    target_id=bull_target_id,
                    setup_direction=Direction.BULL,
                    setup_type="Secondary",
                    ticker=ticker,
                    ticker_id=ticker_id
                )
            elif bear_zone and bull_target:
                # Use bear zone as secondary with bull direction (pivot logic)
                secondary_setup = self._create_setup(
                    zone=bear_zone,
                    target=bull_target,
                    target_id=bull_target_id,
                    setup_direction=Direction.BULL,
                    setup_type="Secondary",
                    ticker=ticker,
                    ticker_id=ticker_id
                )

        else:
            # Neutral: Default to Bull primary, Bear secondary
            if bull_zone and bull_target:
                primary_setup = self._create_setup(
                    zone=bull_zone,
                    target=bull_target,
                    target_id=bull_target_id,
                    setup_direction=Direction.BULL,
                    setup_type="Primary",
                    ticker=ticker,
                    ticker_id=ticker_id
                )

            if bear_zone and bear_target:
                secondary_setup = self._create_setup(
                    zone=bear_zone,
                    target=bear_target,
                    target_id=bear_target_id,
                    setup_direction=Direction.BEAR,
                    setup_type="Secondary",
                    ticker=ticker,
                    ticker_id=ticker_id
                )

        return primary_setup, secondary_setup

    def _create_setup(
        self,
        zone: FilteredZone,
        target: float,
        target_id: str,
        setup_direction: Direction,
        setup_type: str,
        ticker: str,
        ticker_id: str
    ) -> Setup:
        """
        Create a Setup object with R:R calculation.

        R:R Calculation:
        - Bull (target > hvn_poc): reward = target - hvn_poc, risk = hvn_poc - zone_low
        - Bear (target < hvn_poc): reward = hvn_poc - target, risk = zone_high - hvn_poc

        Args:
            zone: The zone to create setup from
            target: Target price
            target_id: Target identifier (e.g., "hvn_poc3" or "4R_calc")
            setup_direction: Bull or Bear
            setup_type: "Primary" or "Secondary"
            ticker: Ticker symbol
            ticker_id: Ticker ID

        Returns:
            Setup object with all fields populated
        """
        # Calculate R:R
        hvn_poc = zone.hvn_poc
        zone_high = zone.zone_high
        zone_low = zone.zone_low

        if target > hvn_poc:
            # Bull setup
            reward = target - hvn_poc
            risk = hvn_poc - zone_low
        else:
            # Bear setup
            reward = hvn_poc - target
            risk = zone_high - hvn_poc

        risk_reward = round(reward / risk, 2) if risk > 0 else 0.0

        return Setup(
            ticker=ticker,
            ticker_id=ticker_id,
            direction=setup_direction,
            setup_type=setup_type,
            zone_id=zone.zone_id,
            hvn_poc=hvn_poc,
            zone_high=zone_high,
            zone_low=zone_low,
            tier=zone.tier,
            target_id=target_id,
            target=target,
            risk_reward=risk_reward
        )


# =========================================================================
# CONVENIENCE FUNCTION
# =========================================================================

def analyze_setups(
    filtered_zones: List[FilteredZone],
    hvn_result: HVNResult,
    bar_data: BarData,
    direction: Direction
) -> Tuple[Optional[Setup], Optional[Setup]]:
    """
    Analyze filtered zones to create primary and secondary setups.

    This is the main entry point for setup analysis.

    Args:
        filtered_zones: List of FilteredZone objects (must have bull/bear POC flags)
        hvn_result: HVNResult with all 10 POCs for target selection
        bar_data: BarData for price and zone risk calculations
        direction: Market direction (Bull/Bull+/Bear/Bear+/Neutral)

    Returns:
        Tuple of (primary_setup, secondary_setup)
    """
    analyzer = SetupAnalyzer()
    return analyzer.analyze_setups(
        filtered_zones=filtered_zones,
        hvn_result=hvn_result,
        bar_data=bar_data,
        direction=direction
    )
