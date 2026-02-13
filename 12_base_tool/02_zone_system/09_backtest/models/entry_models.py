"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: BACKTESTER v3.0
Entry Models - EPCH1-4 Entry Logic with Price Origin Detection (S15 Compatible)
XIII Trading LLC
================================================================================

ENTRY MODEL DEFINITIONS:

EPCH1 - PRIMARY ZONE CONTINUATION (price traversing through zone):
    LONG:
      - Opens BELOW zone → closes above zone_high
      - Opens INSIDE zone → most recent outside close was BELOW zone → closes above zone_high
    SHORT:
      - Opens ABOVE zone → closes below zone_low
      - Opens INSIDE zone → most recent outside close was ABOVE zone → closes below zone_low
    Stop: zone_low - (zone_distance * 5%) for LONG
          zone_high + (zone_distance * 5%) for SHORT

EPCH2 - PRIMARY ZONE REJECTION (price rejecting from zone):
    LONG:
      - Opens ABOVE zone → wick enters zone → closes above zone_high
      - Opens INSIDE zone → most recent outside close was ABOVE zone → closes above zone_high
    SHORT:
      - Opens BELOW zone → wick enters zone → closes below zone_low
      - Opens INSIDE zone → most recent outside close was BELOW zone → closes below zone_low
    Stop: zone_low - (zone_distance * 5%) for LONG
          zone_high + (zone_distance * 5%) for SHORT

EPCH3 - SECONDARY ZONE CONTINUATION:
    Same as EPCH1, using Secondary Zone

EPCH4 - SECONDARY ZONE REJECTION:
    Same as EPCH2, using Secondary Zone

KEY FEATURES:
    - Direction determined by price action, NOT market direction
    - Price origin detection ensures EPCH1 and EPCH2 are mutually exclusive
    - Both LONG and SHORT can trigger on same model/day
    - Multiple trades per model allowed
    - Stop = zone boundary + 5% of zone_distance buffer
    - Minimum risk filter to avoid tiny-risk trades
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
    STOP_BUFFER_PCT, TARGET_R_MULTIPLE, MIN_RISK_DOLLARS,
    VERBOSE
)

# Maximum bars to look back when searching for price origin
# v3.0: Increased from 50 to 1000 for S15 compatibility
# S15 generates ~20x more bars than M5, so 1000 S15 bars ≈ 50 M5 bars (~4 hours)
MAX_LOOKBACK_BARS = 1000


@dataclass
class EntrySignal:
    """Represents an entry signal"""
    model: int
    model_name: str
    zone_type: str  # 'PRIMARY' or 'SECONDARY'
    direction: str  # 'LONG' or 'SHORT'
    entry_price: float
    entry_time: datetime
    bar_index: int
    stop_price: float
    target_3r: float
    target_calc: Optional[float]
    target_used: float  # The actual target (max/min of 3R and calc)
    target_type: str    # '3R' or 'CALC' - which target is being used
    zone_high: float
    zone_low: float
    hvn_poc: float
    risk: float  # Per share risk


class EntryDetector:
    """
    Detects entry signals based on EPCH1-4 logic.
    
    Key principle: Direction is determined by price action relative to zone,
    NOT by market direction. Both long and short can trigger independently.
    
    When bar opens inside zone, find the MOST RECENT bar that closed outside
    the zone to determine if this is continuation (EPCH1/3) or rejection (EPCH2/4).
    This ensures mutual exclusivity - only one can trigger per candle/zone/direction.
    
    Stop placement: Zone-based (zone_low for longs, zone_high for shorts)
    with STOP_BUFFER offset ($0.05).
    """
    
    def __init__(self):
        # Track bar history for lookback
        self.bar_history: List[Dict] = []  # List of {'open', 'high', 'low', 'close'}
    
    def update_prior_bar(self, bar_open: float, bar_high: float, 
                         bar_low: float, bar_close: float):
        """Store current bar in history for lookback"""
        self.bar_history.append({
            'open': bar_open,
            'high': bar_high,
            'low': bar_low,
            'close': bar_close
        })
        
        # Limit history size
        if len(self.bar_history) > MAX_LOOKBACK_BARS + 10:
            self.bar_history = self.bar_history[-MAX_LOOKBACK_BARS:]
    
    def _find_price_origin(self, zone_high: float, zone_low: float) -> Optional[str]:
        """
        Look back through bar history to find the MOST RECENT bar that closed 
        OUTSIDE the zone.
        
        Returns:
            'BELOW' - if most recent outside close was below zone_low
            'ABOVE' - if most recent outside close was above zone_high
            None    - if no bar found that closed outside zone
        
        This ensures mutual exclusivity between EPCH1 and EPCH2:
            - If price came from BELOW → EPCH1 (continuation)
            - If price came from ABOVE → EPCH2 (rejection)
        """
        for bar in reversed(self.bar_history):
            if bar['close'] < zone_low:
                return 'BELOW'
            elif bar['close'] > zone_high:
                return 'ABOVE'
            # If close is inside zone, continue looking back
        return None
    
    def _is_in_entry_window(self, timestamp: datetime) -> bool:
        """Check if timestamp is within entry window"""
        bar_time = timestamp.time()
        return ENTRY_START_TIME <= bar_time <= ENTRY_END_TIME
    
    def _opens_below_zone(self, bar_open: float, zone_low: float) -> bool:
        """Check if bar opens below zone"""
        return bar_open < zone_low
    
    def _opens_above_zone(self, bar_open: float, zone_high: float) -> bool:
        """Check if bar opens above zone"""
        return bar_open > zone_high
    
    def _opens_inside_zone(self, bar_open: float, zone_high: float, zone_low: float) -> bool:
        """Check if bar opens inside zone (inclusive of boundaries)"""
        return zone_low <= bar_open <= zone_high
    
    def _closes_above_zone(self, close: float, zone_high: float) -> bool:
        """Check if bar closes above zone (must be clearly above)"""
        return close > zone_high
    
    def _closes_below_zone(self, close: float, zone_low: float) -> bool:
        """Check if bar closes below zone (must be clearly below)"""
        return close < zone_low
    
    def _wick_enters_zone_from_above(self, bar_low: float, zone_high: float) -> bool:
        """Check if bar's low wick entered zone from above"""
        return bar_low <= zone_high
    
    def _wick_enters_zone_from_below(self, bar_high: float, zone_low: float) -> bool:
        """Check if bar's high wick entered zone from below"""
        return bar_high >= zone_low
    
    def _calculate_targets(self, entry_price: float, stop_price: float,
                           is_long: bool, calc_target: Optional[float]) -> tuple:
        """
        Calculate targets and determine which to use.
        
        For LONG: use max(3R, calc_target) - but only if calc_target > entry
        For SHORT: use min(3R, calc_target) - but only if calc_target < entry
        
        Returns: (target_3r, target_used, target_type)
        """
        risk = abs(entry_price - stop_price)
        
        if is_long:
            target_3r = entry_price + (TARGET_R_MULTIPLE * risk)
            
            # Check if calc_target is valid (above entry for longs)
            if calc_target and calc_target > entry_price:
                # Use whichever is higher for longs
                if calc_target > target_3r:
                    return target_3r, calc_target, 'CALC'
            
            # Default to 3R
            return target_3r, target_3r, '3R'
        else:
            target_3r = entry_price - (TARGET_R_MULTIPLE * risk)
            
            # Check if calc_target is valid (below entry for shorts)
            if calc_target and calc_target < entry_price:
                # Use whichever is lower for shorts
                if calc_target < target_3r:
                    return target_3r, calc_target, 'CALC'
            
            # Default to 3R
            return target_3r, target_3r, '3R'
    
    def _create_signal(self, model: int, model_name: str, zone_type: str,
                       direction: str, entry_price: float, entry_time: datetime,
                       bar_index: int, zone_high: float, zone_low: float,
                       hvn_poc: float, calc_target: Optional[float]) -> Optional[EntrySignal]:
        """
        Create an entry signal with all calculated values.

        Stop placement: Zone-based with 5% buffer
          - LONG:  zone_low - (zone_distance * STOP_BUFFER_PCT)
                   where zone_distance = entry_price - zone_low
          - SHORT: zone_high + (zone_distance * STOP_BUFFER_PCT)
                   where zone_distance = zone_high - entry_price

        Returns None if risk is below minimum threshold.
        """
        is_long = direction == 'LONG'

        # Calculate stop based on ZONE boundaries with percentage buffer
        if is_long:
            zone_distance = entry_price - zone_low
            buffer = zone_distance * STOP_BUFFER_PCT
            stop_price = zone_low - buffer
        else:
            zone_distance = zone_high - entry_price
            buffer = zone_distance * STOP_BUFFER_PCT
            stop_price = zone_high + buffer
        
        # Calculate risk
        risk = abs(entry_price - stop_price)
        
        # FILTER: Skip trades with insufficient risk
        if risk < MIN_RISK_DOLLARS:
            if VERBOSE:
                print(f"    [SKIP] {model_name} {direction}: Risk ${risk:.2f} < min ${MIN_RISK_DOLLARS:.2f}")
            return None
        
        # Calculate targets
        target_3r, target_used, target_type = self._calculate_targets(
            entry_price, stop_price, is_long, calc_target
        )
        
        return EntrySignal(
            model=model,
            model_name=model_name,
            zone_type=zone_type,
            direction=direction,
            entry_price=entry_price,
            entry_time=entry_time,
            bar_index=bar_index,
            stop_price=stop_price,
            target_3r=target_3r,
            target_calc=calc_target,
            target_used=target_used,
            target_type=target_type,
            zone_high=zone_high,
            zone_low=zone_low,
            hvn_poc=hvn_poc,
            risk=risk
        )
    
    def check_epch1_entries(self, bar_idx: int, bar_time: datetime,
                            bar_open: float, bar_high: float,
                            bar_low: float, bar_close: float,
                            zone_high: float, zone_low: float,
                            hvn_poc: float, zone_type: str,
                            calc_target: Optional[float] = None) -> List[EntrySignal]:
        """
        Check for EPCH1/EPCH3 (Continuation) entries - both long and short.
        
        LONG (price traversing UP through zone):
          - Opens BELOW zone → closes above zone_high
          - Opens INSIDE zone → most recent outside close was BELOW → closes above zone_high
        
        SHORT (price traversing DOWN through zone):
          - Opens ABOVE zone → closes below zone_low
          - Opens INSIDE zone → most recent outside close was ABOVE → closes below zone_low
        
        Returns list of signals (0, 1, or 2 possible)
        """
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
            # Opens below zone, closes above → clear continuation
            long_triggered = True
        elif opens_inside and self._closes_above_zone(bar_close, zone_high):
            # Opens inside zone → check most recent outside close
            price_origin = self._find_price_origin(zone_high, zone_low)
            if price_origin == 'BELOW':
                # Price came from below → continuation
                long_triggered = True
        
        if long_triggered:
            signal = self._create_signal(
                model=model,
                model_name=model_name,
                zone_type=zone_type,
                direction='LONG',
                entry_price=bar_close,
                entry_time=bar_time,
                bar_index=bar_idx,
                zone_high=zone_high,
                zone_low=zone_low,
                hvn_poc=hvn_poc,
                calc_target=calc_target
            )
            if signal:
                signals.append(signal)
        
        # SHORT: Price traversing DOWN through zone
        short_triggered = False
        
        if opens_above and self._closes_below_zone(bar_close, zone_low):
            # Opens above zone, closes below → clear continuation
            short_triggered = True
        elif opens_inside and self._closes_below_zone(bar_close, zone_low):
            # Opens inside zone → check most recent outside close
            price_origin = self._find_price_origin(zone_high, zone_low)
            if price_origin == 'ABOVE':
                # Price came from above → continuation
                short_triggered = True
        
        if short_triggered:
            signal = self._create_signal(
                model=model,
                model_name=model_name,
                zone_type=zone_type,
                direction='SHORT',
                entry_price=bar_close,
                entry_time=bar_time,
                bar_index=bar_idx,
                zone_high=zone_high,
                zone_low=zone_low,
                hvn_poc=hvn_poc,
                calc_target=calc_target
            )
            if signal:
                signals.append(signal)
        
        return signals
    
    def check_epch2_entries(self, bar_idx: int, bar_time: datetime,
                            bar_open: float, bar_high: float,
                            bar_low: float, bar_close: float,
                            zone_high: float, zone_low: float,
                            hvn_poc: float, zone_type: str,
                            calc_target: Optional[float] = None) -> List[EntrySignal]:
        """
        Check for EPCH2/EPCH4 (Rejection) entries - both long and short.
        
        LONG (price rejecting from zone, continuing up):
          - Opens ABOVE zone → wick enters zone → closes above zone_high
          - Opens INSIDE zone → most recent outside close was ABOVE → closes above zone_high
        
        SHORT (price rejecting from zone, continuing down):
          - Opens BELOW zone → wick enters zone → closes below zone_low
          - Opens INSIDE zone → most recent outside close was BELOW → closes below zone_low
        
        Returns list of signals (0, 1, or 2 possible)
        """
        signals = []
        
        if not self._is_in_entry_window(bar_time):
            return signals
        
        model = ENTRY_MODELS['EPCH2'] if zone_type == 'PRIMARY' else ENTRY_MODELS['EPCH4']
        model_name = 'EPCH2' if zone_type == 'PRIMARY' else 'EPCH4'
        
        opens_below = self._opens_below_zone(bar_open, zone_low)
        opens_above = self._opens_above_zone(bar_open, zone_high)
        opens_inside = self._opens_inside_zone(bar_open, zone_high, zone_low)
        
        # LONG REJECTION (price came from above, dipped into zone, bounced)
        long_triggered = False
        
        if opens_above and self._wick_enters_zone_from_above(bar_low, zone_high) and self._closes_above_zone(bar_close, zone_high):
            # Opens above zone, wick enters zone, closes above → rejection
            long_triggered = True
        elif opens_inside and self._closes_above_zone(bar_close, zone_high):
            # Opens inside zone → check most recent outside close
            price_origin = self._find_price_origin(zone_high, zone_low)
            if price_origin == 'ABOVE':
                # Price came from above → rejection
                long_triggered = True
        
        if long_triggered:
            signal = self._create_signal(
                model=model,
                model_name=model_name,
                zone_type=zone_type,
                direction='LONG',
                entry_price=bar_close,
                entry_time=bar_time,
                bar_index=bar_idx,
                zone_high=zone_high,
                zone_low=zone_low,
                hvn_poc=hvn_poc,
                calc_target=calc_target
            )
            if signal:
                signals.append(signal)
        
        # SHORT REJECTION (price came from below, popped into zone, rejected)
        short_triggered = False
        
        if opens_below and self._wick_enters_zone_from_below(bar_high, zone_low) and self._closes_below_zone(bar_close, zone_low):
            # Opens below zone, wick enters zone, closes below → rejection
            short_triggered = True
        elif opens_inside and self._closes_below_zone(bar_close, zone_low):
            # Opens inside zone → check most recent outside close
            price_origin = self._find_price_origin(zone_high, zone_low)
            if price_origin == 'BELOW':
                # Price came from below → rejection
                short_triggered = True
        
        if short_triggered:
            signal = self._create_signal(
                model=model,
                model_name=model_name,
                zone_type=zone_type,
                direction='SHORT',
                entry_price=bar_close,
                entry_time=bar_time,
                bar_index=bar_idx,
                zone_high=zone_high,
                zone_low=zone_low,
                hvn_poc=hvn_poc,
                calc_target=calc_target
            )
            if signal:
                signals.append(signal)
        
        return signals
    
    def check_all_entries(self, bar_idx: int, bar_time: datetime,
                          bar_open: float, bar_high: float,
                          bar_low: float, bar_close: float,
                          primary_zone: Optional[dict] = None,
                          secondary_zone: Optional[dict] = None) -> List[EntrySignal]:
        """
        Check all entry models for both zones.
        
        Args:
            primary_zone: Dict with zone_high, zone_low, hvn_poc, target (optional)
            secondary_zone: Dict with zone_high, zone_low, hvn_poc, target (optional)
        
        Returns:
            List of all triggered entry signals
        """
        all_signals = []
        
        if primary_zone:
            # EPCH1 - Primary Continuation
            all_signals.extend(self.check_epch1_entries(
                bar_idx, bar_time, bar_open, bar_high, bar_low, bar_close,
                primary_zone['zone_high'], primary_zone['zone_low'],
                primary_zone['hvn_poc'], 'PRIMARY',
                primary_zone.get('target')
            ))
            
            # EPCH2 - Primary Rejection
            all_signals.extend(self.check_epch2_entries(
                bar_idx, bar_time, bar_open, bar_high, bar_low, bar_close,
                primary_zone['zone_high'], primary_zone['zone_low'],
                primary_zone['hvn_poc'], 'PRIMARY',
                primary_zone.get('target')
            ))
        
        if secondary_zone:
            # EPCH3 - Secondary Continuation
            all_signals.extend(self.check_epch1_entries(
                bar_idx, bar_time, bar_open, bar_high, bar_low, bar_close,
                secondary_zone['zone_high'], secondary_zone['zone_low'],
                secondary_zone['hvn_poc'], 'SECONDARY',
                secondary_zone.get('target')
            ))
            
            # EPCH4 - Secondary Rejection
            all_signals.extend(self.check_epch2_entries(
                bar_idx, bar_time, bar_open, bar_high, bar_low, bar_close,
                secondary_zone['zone_high'], secondary_zone['zone_low'],
                secondary_zone['hvn_poc'], 'SECONDARY',
                secondary_zone.get('target')
            ))
        
        return all_signals
    
    def reset(self):
        """Reset detector state"""
        self.bar_history.clear()


if __name__ == "__main__":
    print("Entry Models module - run backtest_runner.py to execute")