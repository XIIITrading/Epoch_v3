"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 03: BACKTEST RUNNER v4.0
Entry Models - EPCH1-4 Entry Logic with Price Origin Detection
XIII Trading LLC
================================================================================

ENTRY MODEL DEFINITIONS:

EPCH1 - PRIMARY ZONE CONTINUATION (price traversing through zone):
    LONG:  Opens BELOW zone -> closes above zone_high
    SHORT: Opens ABOVE zone -> closes below zone_low

EPCH2 - PRIMARY ZONE REJECTION (price rejecting from zone):
    LONG:  Opens ABOVE zone -> wick enters zone -> closes above zone_high
    SHORT: Opens BELOW zone -> wick enters zone -> closes below zone_low

EPCH3 - SECONDARY ZONE CONTINUATION: Same as EPCH1, using Secondary Zone
EPCH4 - SECONDARY ZONE REJECTION: Same as EPCH2, using Secondary Zone
================================================================================
"""
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List, Dict
from datetime import datetime

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    ENTRY_MODELS, ENTRY_START_TIME, ENTRY_END_TIME,
    VERBOSE
)

MAX_LOOKBACK_BARS = 1000


@dataclass
class EntrySignal:
    """Represents an entry signal (entry detection only, no stops/targets)."""
    model: int
    model_name: str
    zone_type: str  # 'PRIMARY' or 'SECONDARY'
    direction: str  # 'LONG' or 'SHORT'
    entry_price: float
    entry_time: datetime
    bar_index: int
    zone_high: float
    zone_low: float


class EntryDetector:
    """Detects entry signals based on EPCH1-4 logic."""

    def __init__(self):
        self.bar_history: List[Dict] = []

    def update_prior_bar(self, bar_open: float, bar_high: float,
                         bar_low: float, bar_close: float):
        """Store current bar in history for lookback"""
        self.bar_history.append({
            'open': bar_open,
            'high': bar_high,
            'low': bar_low,
            'close': bar_close
        })

        if len(self.bar_history) > MAX_LOOKBACK_BARS + 10:
            self.bar_history = self.bar_history[-MAX_LOOKBACK_BARS:]

    def _find_price_origin(self, zone_high: float, zone_low: float) -> Optional[str]:
        """Find the MOST RECENT bar that closed OUTSIDE the zone."""
        for bar in reversed(self.bar_history):
            if bar['close'] < zone_low:
                return 'BELOW'
            elif bar['close'] > zone_high:
                return 'ABOVE'
        return None

    def _is_in_entry_window(self, timestamp: datetime) -> bool:
        """Check if timestamp is within entry window"""
        bar_time = timestamp.time()
        return ENTRY_START_TIME <= bar_time <= ENTRY_END_TIME

    def _opens_below_zone(self, bar_open: float, zone_low: float) -> bool:
        return bar_open < zone_low

    def _opens_above_zone(self, bar_open: float, zone_high: float) -> bool:
        return bar_open > zone_high

    def _opens_inside_zone(self, bar_open: float, zone_high: float, zone_low: float) -> bool:
        return zone_low <= bar_open <= zone_high

    def _closes_above_zone(self, close: float, zone_high: float) -> bool:
        return close > zone_high

    def _closes_below_zone(self, close: float, zone_low: float) -> bool:
        return close < zone_low

    def _wick_enters_zone_from_above(self, bar_low: float, zone_high: float) -> bool:
        return bar_low <= zone_high

    def _wick_enters_zone_from_below(self, bar_high: float, zone_low: float) -> bool:
        return bar_high >= zone_low

    def _create_signal(self, model: int, model_name: str, zone_type: str,
                       direction: str, entry_price: float, entry_time: datetime,
                       bar_index: int, zone_high: float, zone_low: float) -> EntrySignal:
        """Create an entry signal."""
        return EntrySignal(
            model=model,
            model_name=model_name,
            zone_type=zone_type,
            direction=direction,
            entry_price=entry_price,
            entry_time=entry_time,
            bar_index=bar_index,
            zone_high=zone_high,
            zone_low=zone_low
        )

    def check_epch1_entries(self, bar_idx: int, bar_time: datetime,
                            bar_open: float, bar_high: float,
                            bar_low: float, bar_close: float,
                            zone_high: float, zone_low: float,
                            zone_type: str) -> List[EntrySignal]:
        """Check for EPCH1/EPCH3 (Continuation) entries."""
        signals = []

        if not self._is_in_entry_window(bar_time):
            return signals

        model = ENTRY_MODELS['EPCH1'] if zone_type == 'PRIMARY' else ENTRY_MODELS['EPCH3']
        model_name = 'EPCH1' if zone_type == 'PRIMARY' else 'EPCH3'

        opens_below = self._opens_below_zone(bar_open, zone_low)
        opens_above = self._opens_above_zone(bar_open, zone_high)
        opens_inside = self._opens_inside_zone(bar_open, zone_high, zone_low)

        # LONG: Price traversing UP through zone
        long_triggered = False

        if opens_below and self._closes_above_zone(bar_close, zone_high):
            long_triggered = True
        elif opens_inside and self._closes_above_zone(bar_close, zone_high):
            price_origin = self._find_price_origin(zone_high, zone_low)
            if price_origin == 'BELOW':
                long_triggered = True

        if long_triggered:
            signal = self._create_signal(
                model=model, model_name=model_name, zone_type=zone_type,
                direction='LONG', entry_price=bar_close, entry_time=bar_time,
                bar_index=bar_idx, zone_high=zone_high, zone_low=zone_low
            )
            signals.append(signal)

        # SHORT: Price traversing DOWN through zone
        short_triggered = False

        if opens_above and self._closes_below_zone(bar_close, zone_low):
            short_triggered = True
        elif opens_inside and self._closes_below_zone(bar_close, zone_low):
            price_origin = self._find_price_origin(zone_high, zone_low)
            if price_origin == 'ABOVE':
                short_triggered = True

        if short_triggered:
            signal = self._create_signal(
                model=model, model_name=model_name, zone_type=zone_type,
                direction='SHORT', entry_price=bar_close, entry_time=bar_time,
                bar_index=bar_idx, zone_high=zone_high, zone_low=zone_low
            )
            signals.append(signal)

        return signals

    def check_epch2_entries(self, bar_idx: int, bar_time: datetime,
                            bar_open: float, bar_high: float,
                            bar_low: float, bar_close: float,
                            zone_high: float, zone_low: float,
                            zone_type: str) -> List[EntrySignal]:
        """Check for EPCH2/EPCH4 (Rejection) entries."""
        signals = []

        if not self._is_in_entry_window(bar_time):
            return signals

        model = ENTRY_MODELS['EPCH2'] if zone_type == 'PRIMARY' else ENTRY_MODELS['EPCH4']
        model_name = 'EPCH2' if zone_type == 'PRIMARY' else 'EPCH4'

        opens_below = self._opens_below_zone(bar_open, zone_low)
        opens_above = self._opens_above_zone(bar_open, zone_high)
        opens_inside = self._opens_inside_zone(bar_open, zone_high, zone_low)

        # LONG REJECTION
        long_triggered = False

        if opens_above and self._wick_enters_zone_from_above(bar_low, zone_high) and self._closes_above_zone(bar_close, zone_high):
            long_triggered = True
        elif opens_inside and self._closes_above_zone(bar_close, zone_high):
            price_origin = self._find_price_origin(zone_high, zone_low)
            if price_origin == 'ABOVE':
                long_triggered = True

        if long_triggered:
            signal = self._create_signal(
                model=model, model_name=model_name, zone_type=zone_type,
                direction='LONG', entry_price=bar_close, entry_time=bar_time,
                bar_index=bar_idx, zone_high=zone_high, zone_low=zone_low
            )
            signals.append(signal)

        # SHORT REJECTION
        short_triggered = False

        if opens_below and self._wick_enters_zone_from_below(bar_high, zone_low) and self._closes_below_zone(bar_close, zone_low):
            short_triggered = True
        elif opens_inside and self._closes_below_zone(bar_close, zone_low):
            price_origin = self._find_price_origin(zone_high, zone_low)
            if price_origin == 'BELOW':
                short_triggered = True

        if short_triggered:
            signal = self._create_signal(
                model=model, model_name=model_name, zone_type=zone_type,
                direction='SHORT', entry_price=bar_close, entry_time=bar_time,
                bar_index=bar_idx, zone_high=zone_high, zone_low=zone_low
            )
            signals.append(signal)

        return signals

    def check_all_entries(self, bar_idx: int, bar_time: datetime,
                          bar_open: float, bar_high: float,
                          bar_low: float, bar_close: float,
                          primary_zone: Optional[dict] = None,
                          secondary_zone: Optional[dict] = None) -> List[EntrySignal]:
        """Check all entry models for both zones."""
        all_signals = []

        if primary_zone:
            all_signals.extend(self.check_epch1_entries(
                bar_idx, bar_time, bar_open, bar_high, bar_low, bar_close,
                primary_zone['zone_high'], primary_zone['zone_low'],
                'PRIMARY'
            ))

            all_signals.extend(self.check_epch2_entries(
                bar_idx, bar_time, bar_open, bar_high, bar_low, bar_close,
                primary_zone['zone_high'], primary_zone['zone_low'],
                'PRIMARY'
            ))

        if secondary_zone:
            all_signals.extend(self.check_epch1_entries(
                bar_idx, bar_time, bar_open, bar_high, bar_low, bar_close,
                secondary_zone['zone_high'], secondary_zone['zone_low'],
                'SECONDARY'
            ))

            all_signals.extend(self.check_epch2_entries(
                bar_idx, bar_time, bar_open, bar_high, bar_low, bar_close,
                secondary_zone['zone_high'], secondary_zone['zone_low'],
                'SECONDARY'
            ))

        return all_signals

    def reset(self):
        """Reset detector state"""
        self.bar_history.clear()
