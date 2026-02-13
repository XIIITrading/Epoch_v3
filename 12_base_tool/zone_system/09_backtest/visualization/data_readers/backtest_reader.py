# backtest_reader.py
# Location: C:\XIIITradingSystems\Epoch\02_zone_system\09_backtest\visualization\data_readers\
# Purpose: Read and parse backtest trade records from Excel

"""
Backtest Results Reader

Reads trade records from the 'backtest' worksheet in epoch_v1.xlsm.
Converts to TradeRecord dataclass objects and provides filtering capabilities.

Column Layout (A:T):
- A: Date
- B: Ticker
- C: Model (EPCH1, EPCH2, EPCH3, EPCH4)
- D: Zone_Type (PRIMARY, SECONDARY)
- E: Direction (LONG, SHORT)
- F: Zone_High
- G: Zone_Low
- H: Entry_Price
- I: Entry_Time
- J: Stop_Price
- K: Target_3R
- L: Target_Calc
- M: Target_Used ('3R' or 'CALC')
- N: Exit_Price
- O: Exit_Time
- P: Exit_Reason (STOP, TARGET_3R, TARGET_CALC, EOD)
- Q: PnL_$ (dollars)
- R: PnL_R (R-multiple)
- S: Risk
- T: Win (TRUE/FALSE)
"""

import xlwings as xw
import pandas as pd
from datetime import datetime, time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class TradeRecord:
    """Single backtested trade record"""
    # Identifiers
    trade_id: str           # Generated: {Date}_{Ticker}_{Model}_{idx}
    date: str               # YYYY-MM-DD
    ticker: str
    model: str              # EPCH1, EPCH2, EPCH3, EPCH4
    
    # Zone info
    zone_type: str          # PRIMARY, SECONDARY
    direction: str          # LONG, SHORT
    zone_high: float
    zone_low: float
    
    # Entry details
    entry_price: float
    entry_time: str         # HH:MM:SS
    
    # Risk management
    stop_price: float
    target_3r: float
    target_calc: float
    target_used: str        # '3R' or 'CALC'
    
    # Exit details
    exit_price: float
    exit_time: str          # HH:MM:SS
    exit_reason: str        # STOP, TARGET_3R, TARGET_CALC, EOD
    
    # Performance
    pnl_dollars: float
    pnl_r: float
    risk: float
    win: bool
    
    # Computed properties
    @property
    def zone_poc(self) -> float:
        """Calculate zone midpoint (POC)"""
        return (self.zone_high + self.zone_low) / 2
    
    @property
    def zone_width(self) -> float:
        """Calculate zone width"""
        return self.zone_high - self.zone_low
    
    @property
    def entry_datetime(self) -> datetime:
        """Combine date and entry time"""
        try:
            return datetime.strptime(f"{self.date} {self.entry_time}", "%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            return datetime.strptime(self.date, "%Y-%m-%d")
    
    @property
    def exit_datetime(self) -> datetime:
        """Combine date and exit time"""
        try:
            return datetime.strptime(f"{self.date} {self.exit_time}", "%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            return datetime.strptime(self.date, "%Y-%m-%d")
    
    @property
    def target_price(self) -> float:
        """Return the target price that was used"""
        if self.target_used == '3R':
            return self.target_3r
        elif self.target_used == 'CALC':
            return self.target_calc
        else:
            return self.target_3r  # Default to 3R
    
    @property
    def is_long(self) -> bool:
        """Check if trade direction is LONG"""
        return self.direction.upper() == 'LONG'
    
    @property
    def duration_minutes(self) -> int:
        """Calculate trade duration in minutes"""
        try:
            delta = self.exit_datetime - self.entry_datetime
            return int(delta.total_seconds() / 60)
        except:
            return 0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for DataFrame"""
        return {
            'trade_id': self.trade_id,
            'date': self.date,
            'ticker': self.ticker,
            'model': self.model,
            'zone_type': self.zone_type,
            'direction': self.direction,
            'zone_high': self.zone_high,
            'zone_low': self.zone_low,
            'zone_poc': self.zone_poc,
            'entry_price': self.entry_price,
            'entry_time': self.entry_time,
            'stop_price': self.stop_price,
            'target_3r': self.target_3r,
            'target_calc': self.target_calc,
            'target_used': self.target_used,
            'target_price': self.target_price,
            'exit_price': self.exit_price,
            'exit_time': self.exit_time,
            'exit_reason': self.exit_reason,
            'pnl_dollars': self.pnl_dollars,
            'pnl_r': self.pnl_r,
            'risk': self.risk,
            'win': self.win,
            'duration_minutes': self.duration_minutes,
        }


# =============================================================================
# BACKTEST READER CLASS
# =============================================================================

class BacktestResultsReader:
    """Read backtest output from Excel worksheet"""
    
    # Column mapping (0-indexed for pandas)
    COLUMN_MAP = {
        'date': 0,          # A
        'ticker': 1,        # B
        'model': 2,         # C
        'zone_type': 3,     # D
        'direction': 4,     # E
        'zone_high': 5,     # F
        'zone_low': 6,      # G
        'entry_price': 7,   # H
        'entry_time': 8,    # I
        'stop_price': 9,    # J
        'target_3r': 10,    # K
        'target_calc': 11,  # L
        'target_used': 12,  # M
        'exit_price': 13,   # N
        'exit_time': 14,    # O
        'exit_reason': 15,  # P
        'pnl_dollars': 16,  # Q
        'pnl_r': 17,        # R
        'risk': 18,         # S
        'win': 19,          # T
    }
    
    def __init__(self, workbook_path: str = None, worksheet_name: str = 'backtest'):
        """
        Initialize the reader.
        
        Args:
            workbook_path: Path to epoch_v1.xlsm (None for default)
            worksheet_name: Name of backtest worksheet
        """
        if workbook_path is None:
            workbook_path = r"C:\XIIITradingSystems\Epoch\epoch_v1.xlsm"
        
        self.workbook_path = Path(workbook_path)
        self.worksheet_name = worksheet_name
        self.wb = None
        self._trades_cache = None
    
    def connect(self) -> bool:
        """Connect to the Excel workbook"""
        try:
            self.wb = xw.Book(str(self.workbook_path))
            logger.info(f"Connected to workbook: {self.workbook_path.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to workbook: {e}")
            logger.error("Ensure the workbook is open in Excel")
            return False
    
    def read_trades(self, force_refresh: bool = False) -> List[TradeRecord]:
        """
        Read all trades from the backtest worksheet.
        
        Args:
            force_refresh: If True, re-read from Excel even if cached
            
        Returns:
            List of TradeRecord objects
        """
        if self._trades_cache is not None and not force_refresh:
            return self._trades_cache
        
        if not self.wb:
            if not self.connect():
                return []
        
        try:
            ws = self.wb.sheets[self.worksheet_name]
        except KeyError:
            logger.error(f"Worksheet '{self.worksheet_name}' not found")
            return []
        
        trades = []
        row = 2  # Start after header row
        empty_count = 0
        max_empty = 5  # Stop after 5 consecutive empty rows
        trade_idx = {}  # Track trade count per date/ticker/model for unique IDs
        
        logger.info(f"Reading trades from '{self.worksheet_name}' worksheet...")
        
        while empty_count < max_empty:
            # Read date to check if row has data
            date_val = ws.range(f'A{row}').value
            
            if date_val is None or str(date_val).strip() == '':
                empty_count += 1
                row += 1
                continue
            
            empty_count = 0
            
            try:
                # Read all columns for this row
                ticker = self._safe_str(ws.range(f'B{row}').value)
                model = self._safe_str(ws.range(f'C{row}').value)
                
                if not ticker or not model:
                    row += 1
                    continue
                
                # Parse date
                if isinstance(date_val, datetime):
                    date_str = date_val.strftime('%Y-%m-%d')
                else:
                    date_str = str(date_val)
                
                # Generate unique trade ID
                key = f"{date_str}_{ticker}_{model}"
                trade_idx[key] = trade_idx.get(key, 0) + 1
                trade_id = f"{key}_{trade_idx[key]}"
                
                # Parse entry time
                entry_time = self._parse_time(ws.range(f'I{row}').value)
                exit_time = self._parse_time(ws.range(f'O{row}').value)
                
                # Parse win as boolean
                win_val = ws.range(f'T{row}').value
                win = self._parse_bool(win_val)
                
                trade = TradeRecord(
                    trade_id=trade_id,
                    date=date_str,
                    ticker=ticker.upper(),
                    model=model.upper(),
                    zone_type=self._safe_str(ws.range(f'D{row}').value).upper(),
                    direction=self._safe_str(ws.range(f'E{row}').value).upper(),
                    zone_high=self._safe_float(ws.range(f'F{row}').value),
                    zone_low=self._safe_float(ws.range(f'G{row}').value),
                    entry_price=self._safe_float(ws.range(f'H{row}').value),
                    entry_time=entry_time,
                    stop_price=self._safe_float(ws.range(f'J{row}').value),
                    target_3r=self._safe_float(ws.range(f'K{row}').value),
                    target_calc=self._safe_float(ws.range(f'L{row}').value),
                    target_used=self._safe_str(ws.range(f'M{row}').value).upper(),
                    exit_price=self._safe_float(ws.range(f'N{row}').value),
                    exit_time=exit_time,
                    exit_reason=self._safe_str(ws.range(f'P{row}').value).upper(),
                    pnl_dollars=self._safe_float(ws.range(f'Q{row}').value),
                    pnl_r=self._safe_float(ws.range(f'R{row}').value),
                    risk=self._safe_float(ws.range(f'S{row}').value),
                    win=win
                )
                
                trades.append(trade)
                
            except Exception as e:
                logger.warning(f"Error reading row {row}: {e}")
            
            row += 1
        
        logger.info(f"Read {len(trades)} trades from worksheet")
        self._trades_cache = trades
        return trades
    
    def to_dataframe(self, trades: List[TradeRecord] = None) -> pd.DataFrame:
        """
        Convert trades to DataFrame for filtering and analysis.
        
        Args:
            trades: List of TradeRecord (None to use cached/read from Excel)
            
        Returns:
            DataFrame with all trade data
        """
        if trades is None:
            trades = self.read_trades()
        
        if not trades:
            return pd.DataFrame()
        
        return pd.DataFrame([t.to_dict() for t in trades])
    
    def filter_trades(self, 
                      trades: List[TradeRecord] = None,
                      ticker: str = None,
                      model: str = None,
                      zone_type: str = None,
                      direction: str = None,
                      start_date: str = None,
                      end_date: str = None,
                      win_only: bool = None,
                      exit_reason: str = None) -> List[TradeRecord]:
        """
        Filter trades based on criteria.
        
        Args:
            trades: List of trades to filter (None to use cached)
            ticker: Filter by ticker symbol
            model: Filter by model (EPCH1, EPCH2, EPCH3, EPCH4)
            zone_type: Filter by zone type (PRIMARY, SECONDARY)
            direction: Filter by direction (LONG, SHORT)
            start_date: Filter trades on or after this date (YYYY-MM-DD)
            end_date: Filter trades on or before this date (YYYY-MM-DD)
            win_only: If True, only winning trades; if False, only losing
            exit_reason: Filter by exit reason (STOP, TARGET_3R, TARGET_CALC, EOD)
            
        Returns:
            Filtered list of TradeRecord objects
        """
        if trades is None:
            trades = self.read_trades()
        
        result = trades.copy()
        
        if ticker:
            result = [t for t in result if t.ticker.upper() == ticker.upper()]
        
        if model:
            result = [t for t in result if t.model.upper() == model.upper()]
        
        if zone_type:
            result = [t for t in result if t.zone_type.upper() == zone_type.upper()]
        
        if direction:
            result = [t for t in result if t.direction.upper() == direction.upper()]
        
        if start_date:
            result = [t for t in result if t.date >= start_date]
        
        if end_date:
            result = [t for t in result if t.date <= end_date]
        
        if win_only is not None:
            result = [t for t in result if t.win == win_only]
        
        if exit_reason:
            result = [t for t in result if t.exit_reason.upper() == exit_reason.upper()]
        
        return result
    
    def get_unique_values(self, field: str) -> List:
        """
        Get unique values for a field (for filter dropdowns).
        
        Args:
            field: Field name (ticker, model, zone_type, direction, etc.)
            
        Returns:
            Sorted list of unique values
        """
        trades = self.read_trades()
        values = set()
        
        for trade in trades:
            if hasattr(trade, field):
                val = getattr(trade, field)
                if val:
                    values.add(val)
        
        return sorted(list(values))
    
    def get_statistics(self, trades: List[TradeRecord] = None) -> Dict:
        """
        Calculate summary statistics for trades.
        
        Args:
            trades: List of trades (None to use all)
            
        Returns:
            Dictionary with statistics
        """
        if trades is None:
            trades = self.read_trades()
        
        if not trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'total_pnl_dollars': 0,
                'total_pnl_r': 0,
                'avg_pnl_r': 0,
                'avg_winner_r': 0,
                'avg_loser_r': 0,
                'profit_factor': 0,
            }
        
        total = len(trades)
        winners = [t for t in trades if t.win]
        losers = [t for t in trades if not t.win]
        
        win_rate = len(winners) / total * 100 if total > 0 else 0
        total_pnl_dollars = sum(t.pnl_dollars for t in trades)
        total_pnl_r = sum(t.pnl_r for t in trades)
        avg_pnl_r = total_pnl_r / total if total > 0 else 0
        
        avg_winner_r = sum(t.pnl_r for t in winners) / len(winners) if winners else 0
        avg_loser_r = sum(t.pnl_r for t in losers) / len(losers) if losers else 0
        
        gross_profit = sum(t.pnl_dollars for t in winners)
        gross_loss = abs(sum(t.pnl_dollars for t in losers))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        return {
            'total_trades': total,
            'winners': len(winners),
            'losers': len(losers),
            'win_rate': round(win_rate, 1),
            'total_pnl_dollars': round(total_pnl_dollars, 2),
            'total_pnl_r': round(total_pnl_r, 2),
            'avg_pnl_r': round(avg_pnl_r, 2),
            'avg_winner_r': round(avg_winner_r, 2),
            'avg_loser_r': round(avg_loser_r, 2),
            'profit_factor': round(profit_factor, 2),
        }
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _safe_str(self, value) -> str:
        """Safely convert value to string"""
        if value is None:
            return ''
        return str(value).strip()
    
    def _safe_float(self, value) -> float:
        """Safely convert value to float"""
        if value is None or value == '':
            return 0.0
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    def _parse_time(self, value) -> str:
        """Parse time value to HH:MM:SS string"""
        if value is None:
            return '00:00:00'
        
        if isinstance(value, time):
            return value.strftime('%H:%M:%S')
        
        if isinstance(value, datetime):
            return value.strftime('%H:%M:%S')
        
        # Try to parse string
        time_str = str(value).strip()
        
        # Handle decimal time format (e.g., 0.4 for 09:36)
        try:
            if '.' in time_str and ':' not in time_str:
                decimal_time = float(time_str)
                hours = int(decimal_time * 24)
                minutes = int((decimal_time * 24 - hours) * 60)
                seconds = int(((decimal_time * 24 - hours) * 60 - minutes) * 60)
                return f'{hours:02d}:{minutes:02d}:{seconds:02d}'
        except:
            pass
        
        # Handle HH:MM:SS or HH:MM format
        if ':' in time_str:
            parts = time_str.split(':')
            if len(parts) == 2:
                return f'{parts[0]}:{parts[1]}:00'
            elif len(parts) >= 3:
                return f'{parts[0]}:{parts[1]}:{parts[2][:2]}'
        
        return '00:00:00'
    
    def _parse_bool(self, value) -> bool:
        """Parse boolean value"""
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        
        str_val = str(value).upper().strip()
        return str_val in ('TRUE', 'YES', '1', 'WIN', 'W')


# =============================================================================
# STANDALONE TEST
# =============================================================================

def main():
    """Test the backtest reader"""
    reader = BacktestResultsReader()
    
    if not reader.connect():
        print("Failed to connect to workbook. Ensure it's open.")
        return
    
    trades = reader.read_trades()
    
    print(f"\n{'='*60}")
    print(f"Loaded {len(trades)} trades")
    print(f"{'='*60}")
    
    if trades:
        # Show first few trades
        print("\nFirst 5 trades:")
        for trade in trades[:5]:
            print(f"  {trade.trade_id}: {trade.direction} @ ${trade.entry_price:.2f} -> "
                  f"${trade.exit_price:.2f} ({trade.exit_reason}) = {trade.pnl_r:.2f}R")
        
        # Show statistics
        stats = reader.get_statistics(trades)
        print(f"\nStatistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # Show unique values
        print(f"\nUnique tickers: {reader.get_unique_values('ticker')}")
        print(f"Unique models: {reader.get_unique_values('model')}")
        print(f"Unique dates: {len(reader.get_unique_values('date'))} days")


if __name__ == "__main__":
    main()
