"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: BACKTESTER v2.0
Exit Models - Stop, Target, CHoCH, EOD Exit Logic
XIII Trading LLC
================================================================================

EXIT PRIORITY:
1. STOP    - bar_close beyond stop price
2. TARGET  - bar_close reaches target (max/min of calc_target and 3R)
3. CHoCH   - M5 Change of Character on structure break
4. EOD     - Force close at 15:50 ET

EXIT TYPES:
- STOP: Price closes beyond stop level
- TARGET_3R: Price reaches 3R target (when 3R was the active target)
- TARGET_CALC: Price reaches calculated target (when calc was the active target)
- CHOCH: M5 structure change of character
- EOD: End of day forced exit

KEY CHANGES FROM v1:
- Removed 2R target
- Target uses max(calc, 3R) for longs, min(calc, 3R) for shorts
- EOD time changed to 15:50
- Exit reason shows which target type triggered
================================================================================
"""
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from datetime import datetime, time
from enum import Enum

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import FORCE_EXIT_TIME, FRACTAL_LENGTH, USE_CHOCH_EXIT, VERBOSE


class ExitReason(Enum):
    """Exit reason codes"""
    STOP = "STOP"
    TARGET_3R = "TARGET_3R"
    TARGET_CALC = "TARGET_CALC"
    CHOCH = "CHOCH"
    EOD = "EOD"


@dataclass
class ExitSignal:
    """Represents an exit signal"""
    reason: ExitReason
    exit_price: float
    exit_time: datetime
    bar_index: int
    pnl_dollars: float  # Per share
    pnl_r: float
    is_win: bool


class M5StructureTracker:
    """
    Tracks M5 market structure for CHoCH detection.
    Implements same logic as PineScript fractal/structure detection.
    """
    
    def __init__(self, fractal_length: int = None):
        self.fractal_length = fractal_length or FRACTAL_LENGTH
        self.p = self.fractal_length // 2  # Bars on each side
        
        # Structure state
        self.os = 0  # Order state: 1 = bullish, -1 = bearish
        self.upper_fractal_value = None
        self.upper_fractal_crossed = False
        self.lower_fractal_value = None
        self.lower_fractal_crossed = False
        
        # Continuation tracking
        self.bull_continuation_high = None
        self.bear_continuation_low = None
        
        # Bar history for fractal detection
        self.highs = []
        self.lows = []
        self.closes = []
    
    def update(self, high: float, low: float, close: float) -> tuple:
        """
        Update structure with new bar.
        Returns: (choch_bullish, choch_bearish)
        """
        self.highs.append(high)
        self.lows.append(low)
        self.closes.append(close)
        
        # Need enough bars for fractal detection
        if len(self.highs) < self.fractal_length:
            return False, False
        
        # Keep only needed history
        if len(self.highs) > self.fractal_length * 3:
            self.highs = self.highs[-self.fractal_length * 3:]
            self.lows = self.lows[-self.fractal_length * 3:]
            self.closes = self.closes[-self.fractal_length * 3:]
        
        choch_bullish = False
        choch_bearish = False
        
        # Detect bearish fractal (swing high)
        if self._is_bearish_fractal():
            self.upper_fractal_value = self.highs[-self.p - 1]
            self.upper_fractal_crossed = False
        
        # Detect bullish fractal (swing low)
        if self._is_bullish_fractal():
            self.lower_fractal_value = self.lows[-self.p - 1]
            self.lower_fractal_crossed = False
        
        # Check for structure breaks
        if self.upper_fractal_value is not None and not self.upper_fractal_crossed:
            if close > self.upper_fractal_value:
                if self.os == -1:  # Was bearish, now breaking bullish
                    choch_bullish = True
                self.upper_fractal_crossed = True
                self.os = 1
                self.bull_continuation_high = high
        
        if self.lower_fractal_value is not None and not self.lower_fractal_crossed:
            if close < self.lower_fractal_value:
                if self.os == 1:  # Was bullish, now breaking bearish
                    choch_bearish = True
                self.lower_fractal_crossed = True
                self.os = -1
                self.bear_continuation_low = low
        
        # Update continuation levels
        if self.os == 1 and self.bull_continuation_high is not None:
            if high > self.bull_continuation_high:
                self.bull_continuation_high = high
        
        if self.os == -1 and self.bear_continuation_low is not None:
            if low < self.bear_continuation_low:
                self.bear_continuation_low = low
        
        return choch_bullish, choch_bearish
    
    def _is_bearish_fractal(self) -> bool:
        """Check if we have a bearish fractal (swing high) at position -p-1"""
        if len(self.highs) < self.fractal_length:
            return False
        
        pivot_idx = -self.p - 1
        pivot_high = self.highs[pivot_idx]
        
        # Check bars before pivot
        for i in range(self.p):
            if self.highs[pivot_idx - self.p + i] >= pivot_high:
                return False
        
        # Check bars after pivot
        for i in range(self.p):
            if self.highs[pivot_idx + 1 + i] >= pivot_high:
                return False
        
        return True
    
    def _is_bullish_fractal(self) -> bool:
        """Check if we have a bullish fractal (swing low) at position -p-1"""
        if len(self.lows) < self.fractal_length:
            return False
        
        pivot_idx = -self.p - 1
        pivot_low = self.lows[pivot_idx]
        
        # Check bars before pivot
        for i in range(self.p):
            if self.lows[pivot_idx - self.p + i] <= pivot_low:
                return False
        
        # Check bars after pivot
        for i in range(self.p):
            if self.lows[pivot_idx + 1 + i] <= pivot_low:
                return False
        
        return True
    
    def reset(self):
        """Reset structure tracking for new trade"""
        self.os = 0
        self.upper_fractal_value = None
        self.upper_fractal_crossed = False
        self.lower_fractal_value = None
        self.lower_fractal_crossed = False
        self.bull_continuation_high = None
        self.bear_continuation_low = None
        self.highs.clear()
        self.lows.clear()
        self.closes.clear()


class ExitManager:
    """
    Manages exit detection for active positions.
    
    Priority order: STOP > TARGET > CHoCH > EOD
    """
    
    def __init__(self, use_choch: bool = None, fractal_length: int = None):
        self.use_choch = use_choch if use_choch is not None else USE_CHOCH_EXIT
        self.structure_tracker = M5StructureTracker(fractal_length) if self.use_choch else None
    
    def check_exit(self,
                   bar_idx: int,
                   bar_time: datetime,
                   bar_open: float,
                   bar_high: float,
                   bar_low: float,
                   bar_close: float,
                   is_long: bool,
                   entry_price: float,
                   stop_price: float,
                   target_used: float,
                   target_type: str,
                   risk: float) -> Optional[ExitSignal]:
        """
        Check for exit conditions on current bar.
        
        Args:
            bar_idx: Current bar index
            bar_time: Bar timestamp
            bar_open, bar_high, bar_low, bar_close: OHLC
            is_long: True if long position
            entry_price: Position entry price
            stop_price: Stop loss price
            target_used: The active target price (already max/min of 3R and calc)
            target_type: '3R' or 'CALC' - which target is active
            risk: Per share risk amount
        
        Returns:
            ExitSignal if exit triggered, None otherwise
        
        Priority: STOP > TARGET > CHoCH > EOD
        """
        
        # PRIORITY 1: Stop Loss
        if self._check_stop(bar_close, stop_price, is_long):
            return self._create_exit(
                ExitReason.STOP, bar_close, bar_time, bar_idx,
                entry_price, risk, is_long
            )
        
        # PRIORITY 2: Target
        if self._check_target(bar_close, target_used, is_long):
            # Determine which target type to report
            reason = ExitReason.TARGET_CALC if target_type == 'CALC' else ExitReason.TARGET_3R
            return self._create_exit(
                reason, bar_close, bar_time, bar_idx,
                entry_price, risk, is_long
            )
        
        # PRIORITY 3: CHoCH Exit
        if self.use_choch and self.structure_tracker:
            choch_bull, choch_bear = self.structure_tracker.update(bar_high, bar_low, bar_close)
            
            if is_long and choch_bear:  # Long position, bearish CHoCH
                return self._create_exit(
                    ExitReason.CHOCH, bar_close, bar_time, bar_idx,
                    entry_price, risk, is_long
                )
            elif not is_long and choch_bull:  # Short position, bullish CHoCH
                return self._create_exit(
                    ExitReason.CHOCH, bar_close, bar_time, bar_idx,
                    entry_price, risk, is_long
                )
        
        # PRIORITY 4: EOD Exit
        if self._is_eod(bar_time):
            return self._create_exit(
                ExitReason.EOD, bar_close, bar_time, bar_idx,
                entry_price, risk, is_long
            )
        
        return None
    
    def _is_eod(self, bar_time: datetime) -> bool:
        """Check if we've reached end of day (15:50 ET)"""
        return bar_time.time() >= FORCE_EXIT_TIME
    
    def _check_stop(self, close: float, stop_price: float, is_long: bool) -> bool:
        """Check if stop loss hit (close beyond stop level)"""
        if is_long:
            return close < stop_price
        else:
            return close > stop_price
    
    def _check_target(self, close: float, target: float, is_long: bool) -> bool:
        """Check if target hit"""
        if is_long:
            return close >= target
        else:
            return close <= target
    
    def _create_exit(self, reason: ExitReason, exit_price: float,
                     exit_time: datetime, bar_idx: int,
                     entry_price: float, risk: float,
                     is_long: bool) -> ExitSignal:
        """Create exit signal with P&L calculation"""
        
        if is_long:
            pnl_dollars = exit_price - entry_price
        else:
            pnl_dollars = entry_price - exit_price
        
        pnl_r = pnl_dollars / risk if risk > 0 else 0
        is_win = pnl_dollars > 0
        
        return ExitSignal(
            reason=reason,
            exit_price=exit_price,
            exit_time=exit_time,
            bar_index=bar_idx,
            pnl_dollars=round(pnl_dollars, 4),
            pnl_r=round(pnl_r, 2),
            is_win=is_win
        )
    
    def reset(self):
        """Reset exit manager for new trade"""
        if self.structure_tracker:
            self.structure_tracker.reset()


if __name__ == "__main__":
    print("Exit Models module - run backtest_runner.py to execute")