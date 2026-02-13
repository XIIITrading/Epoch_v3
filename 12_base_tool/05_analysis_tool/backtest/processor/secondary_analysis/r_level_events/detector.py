"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: BACKTEST PROCESSOR
R-Level Crossing Detector
XIII Trading LLC
================================================================================

Detects when price crosses R-level thresholds (1R, 2R, 3R) using M1 bars.
Returns the first bar where each level is crossed.
================================================================================
"""

from dataclasses import dataclass
from datetime import time
from typing import Dict, List, Optional
from decimal import Decimal


@dataclass
class RCrossingEvent:
    """Data captured when an R-level is crossed."""
    r_level: str  # 'R1', 'R2', 'R3'
    r_value: float  # 1.0, 2.0, 3.0
    crossing_time: time
    crossing_price: float  # The R-level price that was crossed
    bar_high: float
    bar_low: float
    bar_close: float
    # Indicators from m1_indicator_bars at crossing
    health_score: Optional[int] = None
    vwap: Optional[float] = None
    sma9: Optional[float] = None
    sma21: Optional[float] = None
    sma_spread: Optional[float] = None
    sma_momentum_label: Optional[str] = None
    vol_roc: Optional[float] = None
    vol_delta: Optional[float] = None
    cvd_slope: Optional[float] = None
    m1_structure: Optional[str] = None
    m5_structure: Optional[str] = None
    m15_structure: Optional[str] = None
    h1_structure: Optional[str] = None
    h4_structure: Optional[str] = None


class RLevelCrossingDetector:
    """
    Detects when price crosses 1R, 2R, 3R levels.

    Uses M1 bars for precise detection.
    Returns the first bar where each level is crossed.
    """

    def __init__(
        self,
        direction: str,
        entry_price: float,
        stop_price: float
    ):
        """
        Initialize detector with trade parameters.

        Args:
            direction: 'LONG' or 'SHORT'
            entry_price: Trade entry price
            stop_price: Stop loss price (defines 1R distance)
        """
        self.direction = direction.upper()
        self.entry_price = float(entry_price)
        self.stop_price = float(stop_price)

        # Calculate risk (1R distance)
        self.risk = abs(self.entry_price - self.stop_price)

        if self.risk == 0:
            raise ValueError("Risk cannot be zero (entry_price == stop_price)")

        # Calculate R-level prices
        self._calculate_r_levels()

    def _calculate_r_levels(self):
        """Calculate price levels for 1R, 2R, 3R."""
        if self.direction == 'LONG':
            self.r1_price = self.entry_price + self.risk
            self.r2_price = self.entry_price + (2 * self.risk)
            self.r3_price = self.entry_price + (3 * self.risk)
        else:  # SHORT
            self.r1_price = self.entry_price - self.risk
            self.r2_price = self.entry_price - (2 * self.risk)
            self.r3_price = self.entry_price - (3 * self.risk)

    def get_r_level_price(self, r_level: str) -> float:
        """Get the price for a specific R-level."""
        prices = {
            'R1': self.r1_price,
            'R2': self.r2_price,
            'R3': self.r3_price,
        }
        return prices.get(r_level, 0)

    def detect_crossings(
        self,
        m1_bars: List[Dict]
    ) -> Dict[str, RCrossingEvent]:
        """
        Detect R-level crossings in a sequence of M1 bars.

        Args:
            m1_bars: List of M1 bar dicts with OHLCV + indicators.
                     Must be sorted by bar_time ascending.

        Returns:
            Dict mapping 'R1', 'R2', 'R3' to RCrossingEvent objects.
            Only includes levels that were actually crossed.
        """
        crossings: Dict[str, RCrossingEvent] = {}

        # Track which levels have been crossed
        r1_crossed = False
        r2_crossed = False
        r3_crossed = False

        for bar in m1_bars:
            # Extract bar data (handle Decimal types)
            high = self._to_float(bar.get('high', 0))
            low = self._to_float(bar.get('low', 0))
            close = self._to_float(bar.get('close', 0))
            bar_time = bar.get('bar_time')

            if self.direction == 'LONG':
                # LONG: crossing is when high >= R-level price
                if not r1_crossed and high >= self.r1_price:
                    crossings['R1'] = self._create_crossing_event(
                        r_level='R1',
                        r_value=1.0,
                        bar=bar,
                        crossing_price=self.r1_price
                    )
                    r1_crossed = True

                if not r2_crossed and high >= self.r2_price:
                    crossings['R2'] = self._create_crossing_event(
                        r_level='R2',
                        r_value=2.0,
                        bar=bar,
                        crossing_price=self.r2_price
                    )
                    r2_crossed = True

                if not r3_crossed and high >= self.r3_price:
                    crossings['R3'] = self._create_crossing_event(
                        r_level='R3',
                        r_value=3.0,
                        bar=bar,
                        crossing_price=self.r3_price
                    )
                    r3_crossed = True

            else:  # SHORT
                # SHORT: crossing is when low <= R-level price
                if not r1_crossed and low <= self.r1_price:
                    crossings['R1'] = self._create_crossing_event(
                        r_level='R1',
                        r_value=1.0,
                        bar=bar,
                        crossing_price=self.r1_price
                    )
                    r1_crossed = True

                if not r2_crossed and low <= self.r2_price:
                    crossings['R2'] = self._create_crossing_event(
                        r_level='R2',
                        r_value=2.0,
                        bar=bar,
                        crossing_price=self.r2_price
                    )
                    r2_crossed = True

                if not r3_crossed and low <= self.r3_price:
                    crossings['R3'] = self._create_crossing_event(
                        r_level='R3',
                        r_value=3.0,
                        bar=bar,
                        crossing_price=self.r3_price
                    )
                    r3_crossed = True

            # Early exit if all levels crossed
            if r1_crossed and r2_crossed and r3_crossed:
                break

        return crossings

    def _create_crossing_event(
        self,
        r_level: str,
        r_value: float,
        bar: Dict,
        crossing_price: float
    ) -> RCrossingEvent:
        """Create an RCrossingEvent from a bar dict."""
        return RCrossingEvent(
            r_level=r_level,
            r_value=r_value,
            crossing_time=bar.get('bar_time'),
            crossing_price=crossing_price,
            bar_high=self._to_float(bar.get('high')),
            bar_low=self._to_float(bar.get('low')),
            bar_close=self._to_float(bar.get('close')),
            health_score=bar.get('health_score'),
            vwap=self._to_float(bar.get('vwap')),
            sma9=self._to_float(bar.get('sma9')),
            sma21=self._to_float(bar.get('sma21')),
            sma_spread=self._to_float(bar.get('sma_spread')),
            sma_momentum_label=bar.get('sma_momentum_label'),
            vol_roc=self._to_float(bar.get('vol_roc')),
            vol_delta=self._to_float(bar.get('vol_delta')),
            cvd_slope=self._to_float(bar.get('cvd_slope')),
            m1_structure=bar.get('m1_structure'),
            m5_structure=bar.get('m5_structure'),
            m15_structure=bar.get('m15_structure'),
            h1_structure=bar.get('h1_structure'),
            h4_structure=bar.get('h4_structure'),
        )

    @staticmethod
    def _to_float(value) -> Optional[float]:
        """Convert value to float, handling None and Decimal."""
        if value is None:
            return None
        if isinstance(value, Decimal):
            return float(value)
        return float(value)
