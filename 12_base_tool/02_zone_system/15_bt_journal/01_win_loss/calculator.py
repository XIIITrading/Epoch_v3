"""
Epoch Backtest Journal - Win/Loss Calculator
Pulls trade data from Supabase database, calculates win/loss statistics,
and writes results to bt_journal.xlsx using xlwings.
"""

import xlwings as xw
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List, Dict
import sys

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.connection import EpochDatabase


@dataclass
class WinLossData:
    """Container for win/loss statistics."""
    total_trades: int = 0
    total_wins: int = 0
    total_losses: int = 0
    percent_wins: float = 0.0
    percent_losses: float = 0.0


class WinLossCalculator:
    """
    Calculates win/loss statistics from Supabase trades table
    and writes results to bt_journal.xlsx analysis sheet.

    Cell References (output):
        Total Trades:           analysis!C2
        Total Wins:             analysis!C6
        Total Losses:           analysis!C7
        Percent Wins / Trades:  analysis!D6
        Percent Losses / Trades: analysis!D7
    """

    # Excel file path
    EXCEL_PATH = Path(r"C:\XIIITradingSystems\Epoch\02_zone_system\12_bt_journal\bt_journal.xlsx")

    # Sheet name
    SHEET_NAME = "analysis"

    # Cell references
    CELL_TOTAL_TRADES = "C2"
    CELL_TOTAL_WINS = "C6"
    CELL_TOTAL_LOSSES = "C7"
    CELL_PERCENT_WINS = "D6"
    CELL_PERCENT_LOSSES = "D7"

    def __init__(self, db: EpochDatabase = None, workbook: xw.Book = None):
        """
        Initialize calculator.

        Args:
            db: Database connection. Creates new if not provided.
            workbook: xlwings Book object. If None, will connect to the file.
        """
        self.db = db or EpochDatabase()
        self._external_wb = workbook is not None
        self._wb = workbook

    def _connect_excel(self) -> xw.Book:
        """Connect to the Excel workbook."""
        if self._wb is None:
            self._wb = xw.Book(str(self.EXCEL_PATH))
        return self._wb

    def calculate(self) -> WinLossData:
        """
        Pull trades from database and calculate win/loss statistics.

        Returns:
            WinLossData object containing calculated statistics.
        """
        # Get all trades from database
        trades = self.db.get_trades()

        if not trades:
            return WinLossData()

        # Calculate statistics
        total_trades = len(trades)
        total_wins = sum(1 for t in trades if t["is_winner"])
        total_losses = total_trades - total_wins

        percent_wins = total_wins / total_trades if total_trades > 0 else 0.0
        percent_losses = total_losses / total_trades if total_trades > 0 else 0.0

        return WinLossData(
            total_trades=total_trades,
            total_wins=total_wins,
            total_losses=total_losses,
            percent_wins=percent_wins,
            percent_losses=percent_losses
        )

    def write_to_excel(self, data: WinLossData) -> None:
        """
        Write win/loss statistics to Excel cells.

        Args:
            data: WinLossData object containing statistics to write.
        """
        wb = self._connect_excel()
        ws = wb.sheets[self.SHEET_NAME]

        ws.range(self.CELL_TOTAL_TRADES).value = data.total_trades
        ws.range(self.CELL_TOTAL_WINS).value = data.total_wins
        ws.range(self.CELL_TOTAL_LOSSES).value = data.total_losses
        ws.range(self.CELL_PERCENT_WINS).value = data.percent_wins
        ws.range(self.CELL_PERCENT_LOSSES).value = data.percent_losses

    def print_results(self, data: WinLossData, verbose: bool = True):
        """
        Print win/loss statistics to console.

        Args:
            data: WinLossData object.
            verbose: If True, print header and formatting.
        """
        if verbose:
            print()
            print("=" * 40)
            print("WIN/LOSS STATISTICS")
            print("=" * 40)

        print(f"Total Trades:    {data.total_trades}")
        print(f"Total Wins:      {data.total_wins}")
        print(f"Total Losses:    {data.total_losses}")
        print(f"Percent Wins:    {data.percent_wins:.2%}")
        print(f"Percent Losses:  {data.percent_losses:.2%}")

        if verbose:
            print("=" * 40)
            print()
