"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: BACKTESTER v2.0
Excel Writer - Write Backtest Results to Excel
XIII Trading LLC
================================================================================

Writes trade log and summary statistics to backtest worksheet.

TRADE LOG COLUMNS (A-U):
    A: trade_id (format: ticker_MMDDYY_model_HHMM)
    B: date
    C: ticker
    ... (see config.py for full mapping)
================================================================================
"""
import sys
from pathlib import Path
from typing import List, Optional, TYPE_CHECKING
from dataclasses import dataclass
from datetime import datetime

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    WORKSHEETS, VERBOSE,
    BACKTEST_TRADE_LOG_START_ROW, BACKTEST_TRADE_LOG_COLUMNS,
    BACKTEST_SUMMARY_START_ROW, BACKTEST_SUMMARY_START_COL
)

if TYPE_CHECKING:
    from engine.trade_simulator import CompletedTrade


@dataclass
class BacktestStats:
    """Summary statistics for backtest results"""
    total_trades: int
    wins: int
    losses: int
    win_rate: float
    total_pnl_r: float
    total_pnl_dollars: float
    avg_win_r: float
    avg_loss_r: float
    expectancy: float
    profit_factor: float
    max_win_r: float
    max_loss_r: float
    by_model: dict
    by_exit: dict


class ExcelWriter:
    """
    Writes backtest results to Excel workbook.
    """
    
    def __init__(self, workbook):
        """
        Initialize with xlwings workbook reference.
        
        Args:
            workbook: xlwings Book object
        """
        self.wb = workbook
        self.ws = workbook.sheets[WORKSHEETS['backtest']]
    
    def clear_results(self):
        """Clear existing backtest results"""
        # Find last row with data
        last_row = self.ws.range('A' + str(self.ws.cells.last_cell.row)).end('up').row
        
        if last_row >= BACKTEST_TRADE_LOG_START_ROW:
            # Clear trade log area (A through U now)
            clear_range = f"A{BACKTEST_TRADE_LOG_START_ROW}:U{last_row}"
            self.ws.range(clear_range).clear_contents()
        
        # Clear summary area (shifted to W)
        summary_clear = f"{BACKTEST_SUMMARY_START_COL}{BACKTEST_SUMMARY_START_ROW}:AA30"
        self.ws.range(summary_clear).clear_contents()
        
        if VERBOSE:
            print("  Cleared existing backtest results")
    
    def write_trades(self, trades: List['CompletedTrade']):
        """Write trade log to Excel"""
        if not trades:
            return
        
        cols = BACKTEST_TRADE_LOG_COLUMNS
        row = BACKTEST_TRADE_LOG_START_ROW
        
        for trade in trades:
            # Format times
            entry_time_str = trade.entry_time.strftime('%H:%M:%S') if trade.entry_time else ''
            exit_time_str = trade.exit_time.strftime('%H:%M:%S') if trade.exit_time else ''
            
            # Write trade data (trade_id now in column A)
            self.ws.range(f"{cols['trade_id']}{row}").value = trade.trade_id
            self.ws.range(f"{cols['date']}{row}").value = trade.date
            self.ws.range(f"{cols['ticker']}{row}").value = trade.ticker
            self.ws.range(f"{cols['model']}{row}").value = trade.model_name
            self.ws.range(f"{cols['zone_type']}{row}").value = trade.zone_type
            self.ws.range(f"{cols['direction']}{row}").value = trade.direction
            self.ws.range(f"{cols['zone_high']}{row}").value = trade.zone_high
            self.ws.range(f"{cols['zone_low']}{row}").value = trade.zone_low
            self.ws.range(f"{cols['entry_price']}{row}").value = trade.entry_price
            self.ws.range(f"{cols['entry_time']}{row}").value = entry_time_str
            self.ws.range(f"{cols['stop_price']}{row}").value = trade.stop_price
            self.ws.range(f"{cols['target_3r']}{row}").value = trade.target_3r
            self.ws.range(f"{cols['target_calc']}{row}").value = trade.target_calc
            self.ws.range(f"{cols['target_used']}{row}").value = trade.target_used
            self.ws.range(f"{cols['exit_price']}{row}").value = trade.exit_price
            self.ws.range(f"{cols['exit_time']}{row}").value = exit_time_str
            self.ws.range(f"{cols['exit_reason']}{row}").value = trade.exit_reason
            self.ws.range(f"{cols['pnl_dollars']}{row}").value = trade.pnl_dollars
            self.ws.range(f"{cols['pnl_r']}{row}").value = trade.pnl_r
            self.ws.range(f"{cols['risk']}{row}").value = trade.risk
            self.ws.range(f"{cols['win']}{row}").value = 1 if trade.is_win else 0
            
            row += 1
        
        if VERBOSE:
            print(f"  Wrote {len(trades)} trades to Excel (rows {BACKTEST_TRADE_LOG_START_ROW}-{row-1})")
    
    def calculate_stats(self, trades: List['CompletedTrade']) -> BacktestStats:
        """Calculate summary statistics from trades"""
        if not trades:
            return BacktestStats(
                total_trades=0, wins=0, losses=0, win_rate=0,
                total_pnl_r=0, total_pnl_dollars=0,
                avg_win_r=0, avg_loss_r=0, expectancy=0, profit_factor=0,
                max_win_r=0, max_loss_r=0, by_model={}, by_exit={}
            )
        
        # Basic stats
        total_trades = len(trades)
        wins = sum(1 for t in trades if t.is_win)
        losses = total_trades - wins
        win_rate = wins / total_trades if total_trades > 0 else 0
        
        # P&L stats
        total_pnl_r = sum(t.pnl_r for t in trades)
        total_pnl_dollars = sum(t.pnl_dollars for t in trades)
        
        winning_trades = [t for t in trades if t.pnl_r > 0]
        losing_trades = [t for t in trades if t.pnl_r <= 0]
        
        avg_win_r = sum(t.pnl_r for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss_r = sum(t.pnl_r for t in losing_trades) / len(losing_trades) if losing_trades else 0
        
        # Expectancy
        expectancy = total_pnl_r / total_trades if total_trades > 0 else 0
        
        # Profit factor
        gross_profit = sum(t.pnl_r for t in winning_trades)
        gross_loss = abs(sum(t.pnl_r for t in losing_trades))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Max win/loss
        max_win_r = max((t.pnl_r for t in trades), default=0)
        max_loss_r = min((t.pnl_r for t in trades), default=0)
        
        # By model
        by_model = {}
        model_names = set(t.model_name for t in trades)
        for model in sorted(model_names):
            model_trades = [t for t in trades if t.model_name == model]
            model_wins = sum(1 for t in model_trades if t.is_win)
            by_model[model] = {
                'trades': len(model_trades),
                'wins': model_wins,
                'win_rate': model_wins / len(model_trades) if model_trades else 0,
                'total_r': sum(t.pnl_r for t in model_trades)
            }
        
        # By exit type
        by_exit = {}
        exit_types = set(t.exit_reason for t in trades)
        for exit_type in sorted(exit_types):
            exit_trades = [t for t in trades if t.exit_reason == exit_type]
            by_exit[exit_type] = {
                'trades': len(exit_trades),
                'total_r': sum(t.pnl_r for t in exit_trades)
            }
        
        return BacktestStats(
            total_trades=total_trades,
            wins=wins,
            losses=losses,
            win_rate=win_rate,
            total_pnl_r=total_pnl_r,
            total_pnl_dollars=total_pnl_dollars,
            avg_win_r=avg_win_r,
            avg_loss_r=avg_loss_r,
            expectancy=expectancy,
            profit_factor=profit_factor,
            max_win_r=max_win_r,
            max_loss_r=max_loss_r,
            by_model=by_model,
            by_exit=by_exit
        )
    
    def write_summary(self, stats: BacktestStats):
        """Write summary statistics to Excel"""
        col = BACKTEST_SUMMARY_START_COL
        row = BACKTEST_SUMMARY_START_ROW
        
        # Write summary header
        self.ws.range(f"{col}{row}").value = "BACKTEST SUMMARY"
        row += 2
        
        # Overall stats
        stats_data = [
            ("Total Trades", stats.total_trades),
            ("Wins", stats.wins),
            ("Losses", stats.losses),
            ("Win Rate", f"{stats.win_rate:.1%}"),
            ("", ""),
            ("Total P&L (R)", f"{stats.total_pnl_r:+.2f}"),
            ("Expectancy (R)", f"{stats.expectancy:+.2f}"),
            ("Profit Factor", f"{stats.profit_factor:.2f}"),
            ("", ""),
            ("Avg Win (R)", f"{stats.avg_win_r:+.2f}"),
            ("Avg Loss (R)", f"{stats.avg_loss_r:+.2f}"),
            ("Max Win (R)", f"{stats.max_win_r:+.2f}"),
            ("Max Loss (R)", f"{stats.max_loss_r:+.2f}"),
        ]
        
        for label, value in stats_data:
            self.ws.range(f"{col}{row}").value = label
            self.ws.range(f"{chr(ord(col)+1)}{row}").value = value
            row += 1
        
        # By Model
        row += 1
        self.ws.range(f"{col}{row}").value = "BY MODEL"
        row += 1
        
        for model, data in stats.by_model.items():
            self.ws.range(f"{col}{row}").value = model
            self.ws.range(f"{chr(ord(col)+1)}{row}").value = f"{data['trades']} trades"
            self.ws.range(f"{chr(ord(col)+2)}{row}").value = f"{data['win_rate']:.0%} WR"
            self.ws.range(f"{chr(ord(col)+3)}{row}").value = f"{data['total_r']:+.1f}R"
            row += 1
        
        # By Exit Type
        row += 1
        self.ws.range(f"{col}{row}").value = "BY EXIT TYPE"
        row += 1
        
        for exit_type, data in stats.by_exit.items():
            self.ws.range(f"{col}{row}").value = exit_type
            self.ws.range(f"{chr(ord(col)+1)}{row}").value = f"{data['trades']} trades"
            self.ws.range(f"{chr(ord(col)+2)}{row}").value = f"{data['total_r']:+.1f}R"
            row += 1
        
        if VERBOSE:
            print("  Wrote summary statistics to Excel")


if __name__ == "__main__":
    print("Excel Writer module - run backtest_runner.py to execute")