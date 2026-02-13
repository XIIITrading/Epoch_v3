"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: BACKTESTER v3.0
Trade Simulator - Position Management and Exit Logic (Hybrid S15/M5 Model)
XIII Trading LLC
================================================================================

HYBRID MODEL (v3.0):
    - ENTRY: Detected on S15 (15-second) bar close via process_bar_entries_only()
    - EXIT: Managed on M5 (5-minute) bar via process_bar_exits_only()

Manages active positions and handles all exit logic:
    - Stop Loss: Exits at STOP PRICE (always -1R when ASSUME_STOP_FILL_AT_PRICE=True)
    - Target: 3R or calculated target (whichever is better)
    - CHoCH: M5 structure break (Change of Character)
    - EOD: Force close at 15:50 ET

EXIT PRIORITY: STOP > TARGET > CHoCH > EOD

TRADE_ID FORMAT: {ticker}_{MMDDYY}_{model}_{HHMM}
    Example: LLY_120925_EPCH2_1450
================================================================================
"""
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple
from datetime import datetime, time
from enum import Enum

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    FORCE_EXIT_TIME, USE_CHOCH_EXIT, FRACTAL_LENGTH, 
    VERBOSE, ASSUME_STOP_FILL_AT_PRICE
)
from models.entry_models import EntrySignal


class ExitReason(Enum):
    """Exit reason codes"""
    STOP = "STOP"
    TARGET_3R = "TARGET_3R"
    TARGET_CALC = "TARGET_CALC"
    CHOCH = "CHOCH"
    EOD = "EOD"


@dataclass
class ActivePosition:
    """Represents an active position"""
    position_id: int
    signal: EntrySignal
    entry_bar_idx: int
    
    # CHoCH tracking
    swing_high: float = 0.0
    swing_low: float = float('inf')
    bars_since_entry: int = 0


@dataclass
class CompletedTrade:
    """Represents a completed trade with full details"""
    trade_id: str  # Format: {ticker}_{MMDDYY}_{model}_{HHMM}
    ticker: str
    date: str
    model: int
    model_name: str
    zone_type: str
    direction: str
    zone_high: float
    zone_low: float
    entry_price: float
    entry_time: datetime
    stop_price: float
    target_3r: float
    target_calc: Optional[float]
    target_used: float
    target_type: str  # '3R' or 'CALC'
    exit_price: float
    exit_time: datetime
    exit_reason: str
    pnl_dollars: float
    pnl_r: float
    risk: float
    is_win: bool


def generate_trade_id(ticker: str, entry_time: datetime, model_name: str) -> str:
    """
    Generate formatted trade_id string.
    
    Format: {ticker}_{MMDDYY}_{model}_{HHMM}
    Example: LLY_120925_EPCH2_1450
    
    Args:
        ticker: Stock symbol (e.g., 'LLY')
        entry_time: Entry datetime
        model_name: Model name (e.g., 'EPCH2')
    
    Returns:
        Formatted trade_id string
    """
    date_str = entry_time.strftime('%m%d%y')  # MMDDYY
    time_str = entry_time.strftime('%H%M')    # HHMM
    return f"{ticker}_{date_str}_{model_name}_{time_str}"


class TradeSimulator:
    """
    Simulates trade execution with multiple concurrent positions.
    
    Features:
        - Unlimited concurrent positions
        - Each position tracked independently
        - Exit priority: STOP > TARGET > CHoCH > EOD
        - Stop losses always result in -1R (when ASSUME_STOP_FILL_AT_PRICE=True)
        - Trade IDs in format: {ticker}_{MMDDYY}_{model}_{HHMM}
    """
    
    def __init__(self, ticker: str, trade_date: str):
        self.ticker = ticker
        self.trade_date = trade_date
        
        # Position tracking
        self.active_positions: Dict[int, ActivePosition] = {}
        self.completed_trades: List[CompletedTrade] = []
        self.next_position_id = 1
        
        # Zone references
        self.primary_zone: Optional[dict] = None
        self.secondary_zone: Optional[dict] = None
        
        # Entry detector
        from models.entry_models import EntryDetector
        self.entry_detector = EntryDetector()
        
        # CHoCH tracking (shared across positions for structure)
        self.recent_highs: List[float] = []
        self.recent_lows: List[float] = []
    
    def set_zones(self, primary_zone: Optional[dict] = None, 
                  secondary_zone: Optional[dict] = None):
        """Set zone data for entry detection"""
        self.primary_zone = primary_zone
        self.secondary_zone = secondary_zone
    
    def process_bar_entries_only(self, bar_idx: int, bar_time: datetime,
                                   bar_open: float, bar_high: float,
                                   bar_low: float, bar_close: float) -> List[EntrySignal]:
        """
        Process a bar for ENTRY detection only (used with S15 bars in hybrid model).

        This method checks for new entries on the S15 timeframe without
        processing exits (exits are handled separately on M5 bars).

        Returns: List of new entry signals
        """
        new_entries = []

        # Check for new entries
        entries = self.entry_detector.check_all_entries(
            bar_idx, bar_time, bar_open, bar_high, bar_low, bar_close,
            self.primary_zone, self.secondary_zone
        )

        for signal in entries:
            self._open_position(signal, bar_idx)
            new_entries.append(signal)

            if VERBOSE:
                print(f"  [{bar_time.strftime('%H:%M:%S')}] NEW {signal.direction} {signal.model_name} "
                      f"@ ${signal.entry_price:.2f} (Stop: ${signal.stop_price:.2f}, "
                      f"Target: ${signal.target_used:.2f})")

        # Update entry detector's prior bar history (for price origin detection)
        self.entry_detector.update_prior_bar(bar_open, bar_high, bar_low, bar_close)

        return new_entries

    def process_bar_exits_only(self, bar_idx: int, bar_time: datetime,
                                bar_open: float, bar_high: float,
                                bar_low: float, bar_close: float) -> List[CompletedTrade]:
        """
        Process a bar for EXIT management only (used with M5 bars in hybrid model).

        This method checks exits for active positions and updates CHoCH tracking
        on the M5 timeframe without detecting new entries.

        Returns: List of closed trades
        """
        closed_trades = []

        # Update CHoCH tracking (M5 timeframe)
        self.recent_highs.append(bar_high)
        self.recent_lows.append(bar_low)
        if len(self.recent_highs) > FRACTAL_LENGTH * 2:
            self.recent_highs.pop(0)
            self.recent_lows.pop(0)

        # Check exits for active positions
        positions_to_close = []

        for pos_id, position in self.active_positions.items():
            exit_result = self._check_exits(position, bar_idx, bar_time,
                                           bar_open, bar_high, bar_low, bar_close)
            if exit_result:
                exit_price, exit_reason = exit_result
                positions_to_close.append((pos_id, exit_price, exit_reason, bar_time))

        # Close positions
        for pos_id, exit_price, exit_reason, exit_time in positions_to_close:
            trade = self._close_position(pos_id, exit_price, exit_time, exit_reason)
            if trade:
                closed_trades.append(trade)

        # Update active position tracking
        for position in self.active_positions.values():
            position.bars_since_entry += 1
            position.swing_high = max(position.swing_high, bar_high)
            position.swing_low = min(position.swing_low, bar_low)

        return closed_trades

    def process_bar(self, bar_idx: int, bar_time: datetime,
                    bar_open: float, bar_high: float,
                    bar_low: float, bar_close: float) -> Tuple[List[EntrySignal], List[CompletedTrade]]:
        """
        Process a single bar for BOTH entries and exits (legacy single-timeframe mode).

        For hybrid S15/M5 model, use process_bar_entries_only() and
        process_bar_exits_only() separately instead.

        1. Check exits for all active positions (STOP > TARGET > CHoCH)
        2. Check for new entries
        3. Update tracking data

        Returns: (new_entries, closed_trades)
        """
        new_entries = []
        closed_trades = []
        
        # Update CHoCH tracking
        self.recent_highs.append(bar_high)
        self.recent_lows.append(bar_low)
        if len(self.recent_highs) > FRACTAL_LENGTH * 2:
            self.recent_highs.pop(0)
            self.recent_lows.pop(0)
        
        # 1. Check exits for active positions
        positions_to_close = []
        
        for pos_id, position in self.active_positions.items():
            exit_result = self._check_exits(position, bar_idx, bar_time,
                                           bar_open, bar_high, bar_low, bar_close)
            if exit_result:
                exit_price, exit_reason = exit_result
                positions_to_close.append((pos_id, exit_price, exit_reason, bar_time))
        
        # Close positions
        for pos_id, exit_price, exit_reason, exit_time in positions_to_close:
            trade = self._close_position(pos_id, exit_price, exit_time, exit_reason)
            if trade:
                closed_trades.append(trade)
        
        # 2. Check for new entries
        entries = self.entry_detector.check_all_entries(
            bar_idx, bar_time, bar_open, bar_high, bar_low, bar_close,
            self.primary_zone, self.secondary_zone
        )
        
        for signal in entries:
            self._open_position(signal, bar_idx)
            new_entries.append(signal)
            
            if VERBOSE:
                print(f"  [{bar_time.strftime('%H:%M')}] NEW {signal.direction} {signal.model_name} "
                      f"@ ${signal.entry_price:.2f} (Stop: ${signal.stop_price:.2f}, "
                      f"Target: ${signal.target_used:.2f})")
        
        # 3. Update entry detector's prior bar
        self.entry_detector.update_prior_bar(bar_open, bar_high, bar_low, bar_close)
        
        # 4. Update active position tracking
        for position in self.active_positions.values():
            position.bars_since_entry += 1
            position.swing_high = max(position.swing_high, bar_high)
            position.swing_low = min(position.swing_low, bar_low)
        
        return new_entries, closed_trades
    
    def _check_exits(self, position: ActivePosition, bar_idx: int, bar_time: datetime,
                     bar_open: float, bar_high: float, bar_low: float, 
                     bar_close: float) -> Optional[Tuple[float, ExitReason]]:
        """
        Check all exit conditions for a position.
        
        Priority: STOP > TARGET > CHoCH > EOD
        
        Returns: (exit_price, exit_reason) or None
        """
        signal = position.signal
        is_long = signal.direction == 'LONG'
        
        # 1. Check STOP
        if is_long:
            if bar_low <= signal.stop_price:
                # Stop hit - exit at stop price (not bar low) for clean -1R
                if ASSUME_STOP_FILL_AT_PRICE:
                    return (signal.stop_price, ExitReason.STOP)
                else:
                    return (bar_low, ExitReason.STOP)
        else:
            if bar_high >= signal.stop_price:
                # Stop hit - exit at stop price (not bar high) for clean -1R
                if ASSUME_STOP_FILL_AT_PRICE:
                    return (signal.stop_price, ExitReason.STOP)
                else:
                    return (bar_high, ExitReason.STOP)
        
        # 2. Check TARGET
        if is_long:
            if bar_high >= signal.target_used:
                exit_reason = ExitReason.TARGET_CALC if signal.target_type == 'CALC' else ExitReason.TARGET_3R
                return (signal.target_used, exit_reason)
        else:
            if bar_low <= signal.target_used:
                exit_reason = ExitReason.TARGET_CALC if signal.target_type == 'CALC' else ExitReason.TARGET_3R
                return (signal.target_used, exit_reason)
        
        # 3. Check CHoCH (Change of Character)
        if USE_CHOCH_EXIT and position.bars_since_entry >= FRACTAL_LENGTH:
            choch_exit = self._check_choch(position, bar_close)
            if choch_exit:
                return (bar_close, ExitReason.CHOCH)
        
        # 4. Check EOD (End of Day)
        if bar_time.time() >= FORCE_EXIT_TIME:
            return (bar_close, ExitReason.EOD)
        
        return None
    
    def _check_choch(self, position: ActivePosition, bar_close: float) -> bool:
        """
        Check for Change of Character (structure break).
        
        LONG: Close below the lowest low of last N bars (structure break down)
        SHORT: Close above the highest high of last N bars (structure break up)
        """
        if len(self.recent_lows) < FRACTAL_LENGTH:
            return False
        
        is_long = position.signal.direction == 'LONG'
        
        if is_long:
            # For longs, check if we broke below recent structure
            recent_low = min(self.recent_lows[-FRACTAL_LENGTH:])
            if bar_close < recent_low:
                return True
        else:
            # For shorts, check if we broke above recent structure
            recent_high = max(self.recent_highs[-FRACTAL_LENGTH:])
            if bar_close > recent_high:
                return True
        
        return False
    
    def _open_position(self, signal: EntrySignal, bar_idx: int):
        """Open a new position"""
        position = ActivePosition(
            position_id=self.next_position_id,
            signal=signal,
            entry_bar_idx=bar_idx,
            swing_high=signal.entry_price,
            swing_low=signal.entry_price
        )
        self.active_positions[self.next_position_id] = position
        self.next_position_id += 1
    
    def _close_position(self, position_id: int, exit_price: float,
                        exit_time: datetime, exit_reason: ExitReason) -> Optional[CompletedTrade]:
        """Close a position and create completed trade record"""
        if position_id not in self.active_positions:
            return None
        
        position = self.active_positions.pop(position_id)
        signal = position.signal
        
        # Calculate P&L
        if signal.direction == 'LONG':
            pnl_dollars = exit_price - signal.entry_price
        else:
            pnl_dollars = signal.entry_price - exit_price
        
        pnl_r = pnl_dollars / signal.risk if signal.risk > 0 else 0
        is_win = pnl_dollars > 0
        
        # Generate formatted trade_id
        trade_id = generate_trade_id(self.ticker, signal.entry_time, signal.model_name)
        
        trade = CompletedTrade(
            trade_id=trade_id,
            ticker=self.ticker,
            date=self.trade_date,
            model=signal.model,
            model_name=signal.model_name,
            zone_type=signal.zone_type,
            direction=signal.direction,
            zone_high=signal.zone_high,
            zone_low=signal.zone_low,
            entry_price=signal.entry_price,
            entry_time=signal.entry_time,
            stop_price=signal.stop_price,
            target_3r=signal.target_3r,
            target_calc=signal.target_calc,
            target_used=signal.target_used,
            target_type=signal.target_type,
            exit_price=exit_price,
            exit_time=exit_time,
            exit_reason=exit_reason.value,
            pnl_dollars=pnl_dollars,
            pnl_r=pnl_r,
            risk=signal.risk,
            is_win=is_win
        )
        
        self.completed_trades.append(trade)
        
        return trade
    
    def force_close_all(self, bar_idx: int, bar_time: datetime, bar_close: float):
        """Force close all remaining positions (EOD)"""
        for pos_id in list(self.active_positions.keys()):
            self._close_position(pos_id, bar_close, bar_time, ExitReason.EOD)
    
    def get_active_position_count(self) -> int:
        """Get number of active positions"""
        return len(self.active_positions)
    
    def get_completed_trades(self) -> List[CompletedTrade]:
        """Get all completed trades"""
        return self.completed_trades
    
    def reset(self):
        """Reset simulator state"""
        self.active_positions.clear()
        self.completed_trades.clear()
        self.next_position_id = 1
        self.entry_detector.reset()
        self.recent_highs.clear()
        self.recent_lows.clear()


if __name__ == "__main__":
    print("Trade Simulator module - run backtest_runner.py to execute")