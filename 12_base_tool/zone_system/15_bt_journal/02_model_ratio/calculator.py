"""
Epoch Backtest Journal - Model Ratio Calculator
Pulls trade data from Supabase database, calculates win/loss statistics
by model (EPCH1-4), and writes results to bt_journal.xlsx using xlwings.
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
class ModelStats:
    """Container for a single model's statistics."""
    model: str
    count: int = 0
    win_count: int = 0
    loss_count: int = 0
    win_rate: float = 0.0


@dataclass
class ModelRatioData:
    """Container for all model statistics."""
    epch1: ModelStats = None
    epch2: ModelStats = None
    epch3: ModelStats = None
    epch4: ModelStats = None

    def __post_init__(self):
        """Initialize empty ModelStats if not provided."""
        if self.epch1 is None:
            self.epch1 = ModelStats(model="EPCH1")
        if self.epch2 is None:
            self.epch2 = ModelStats(model="EPCH2")
        if self.epch3 is None:
            self.epch3 = ModelStats(model="EPCH3")
        if self.epch4 is None:
            self.epch4 = ModelStats(model="EPCH4")

    def get_all(self) -> List[ModelStats]:
        """Return all model stats as a list."""
        return [self.epch1, self.epch2, self.epch3, self.epch4]


class ModelRatioCalculator:
    """
    Calculates win/loss statistics by model from Supabase trades table
    and writes results to bt_journal.xlsx analysis sheet.

    Cell References (output):
        EPCH1 Count:      analysis!C10
        EPCH2 Count:      analysis!C11
        EPCH3 Count:      analysis!C12
        EPCH4 Count:      analysis!C13

        EPCH1 Win Count:  analysis!D10
        EPCH2 Win Count:  analysis!D11
        EPCH3 Win Count:  analysis!D12
        EPCH4 Win Count:  analysis!D13

        EPCH1 Loss Count: analysis!E10
        EPCH2 Loss Count: analysis!E11
        EPCH3 Loss Count: analysis!E12
        EPCH4 Loss Count: analysis!E13

        EPCH1 Win Rate:   analysis!F10
        EPCH2 Win Rate:   analysis!F11
        EPCH3 Win Rate:   analysis!F12
        EPCH4 Win Rate:   analysis!F13
    """

    # Excel file path
    EXCEL_PATH = Path(r"C:\XIIITradingSystems\Epoch\02_zone_system\12_bt_journal\bt_journal.xlsx")

    # Sheet name
    SHEET_NAME = "analysis"

    # Cell references by model (row 10-13)
    CELL_MAP = {
        "EPCH1": {"count": "C10", "win_count": "D10", "loss_count": "E10", "win_rate": "F10"},
        "EPCH2": {"count": "C11", "win_count": "D11", "loss_count": "E11", "win_rate": "F11"},
        "EPCH3": {"count": "C12", "win_count": "D12", "loss_count": "E12", "win_rate": "F12"},
        "EPCH4": {"count": "C13", "win_count": "D13", "loss_count": "E13", "win_rate": "F13"},
    }

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

    def calculate(self) -> ModelRatioData:
        """
        Pull trades from database and calculate win/loss statistics by model.

        Returns:
            ModelRatioData object containing statistics for each model.
        """
        # Get all trades from database
        trades = self.db.get_trades()

        if not trades:
            return ModelRatioData()

        # Group trades by model
        model_trades = {
            "EPCH1": [],
            "EPCH2": [],
            "EPCH3": [],
            "EPCH4": [],
        }

        for trade in trades:
            model = trade.get("model")
            if model in model_trades:
                model_trades[model].append(trade)

        # Calculate statistics for each model
        def calc_model_stats(model: str, trades_list: List[Dict]) -> ModelStats:
            count = len(trades_list)
            win_count = sum(1 for t in trades_list if t["is_winner"])
            loss_count = count - win_count
            win_rate = win_count / count if count > 0 else 0.0

            return ModelStats(
                model=model,
                count=count,
                win_count=win_count,
                loss_count=loss_count,
                win_rate=win_rate
            )

        return ModelRatioData(
            epch1=calc_model_stats("EPCH1", model_trades["EPCH1"]),
            epch2=calc_model_stats("EPCH2", model_trades["EPCH2"]),
            epch3=calc_model_stats("EPCH3", model_trades["EPCH3"]),
            epch4=calc_model_stats("EPCH4", model_trades["EPCH4"]),
        )

    def write_to_excel(self, data: ModelRatioData) -> None:
        """
        Write model ratio statistics to Excel cells.

        Args:
            data: ModelRatioData object containing statistics to write.
        """
        wb = self._connect_excel()
        ws = wb.sheets[self.SHEET_NAME]

        for stats in data.get_all():
            cells = self.CELL_MAP[stats.model]
            ws.range(cells["count"]).value = stats.count
            ws.range(cells["win_count"]).value = stats.win_count
            ws.range(cells["loss_count"]).value = stats.loss_count
            ws.range(cells["win_rate"]).value = stats.win_rate

    def print_results(self, data: ModelRatioData, verbose: bool = True):
        """
        Print model ratio statistics to console.

        Args:
            data: ModelRatioData object.
            verbose: If True, print header and formatting.
        """
        if verbose:
            print()
            print("=" * 60)
            print("MODEL RATIO STATISTICS")
            print("=" * 60)
            print()
            print(f"{'Model':<8} {'Count':>8} {'Wins':>8} {'Losses':>8} {'Win Rate':>10}")
            print("-" * 60)

        for stats in data.get_all():
            print(
                f"{stats.model:<8} "
                f"{stats.count:>8} "
                f"{stats.win_count:>8} "
                f"{stats.loss_count:>8} "
                f"{stats.win_rate:>10.2%}"
            )

        if verbose:
            print("-" * 60)
            # Calculate totals
            total_count = sum(s.count for s in data.get_all())
            total_wins = sum(s.win_count for s in data.get_all())
            total_losses = sum(s.loss_count for s in data.get_all())
            total_win_rate = total_wins / total_count if total_count > 0 else 0.0
            print(
                f"{'TOTAL':<8} "
                f"{total_count:>8} "
                f"{total_wins:>8} "
                f"{total_losses:>8} "
                f"{total_win_rate:>10.2%}"
            )
            print("=" * 60)
            print()
