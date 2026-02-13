"""
================================================================================
EPOCH TRADING SYSTEM - BACKTEST WORKSHEET REPORT GENERATOR
================================================================================
Generates a .txt report for the backtest worksheet for Claude AI analysis.

Output: results/ subdirectory with filename: backtest_MMDDYY_bt_report.txt

Usage:
    from backtest_bt_report import BacktestReportGenerator
    generator = BacktestReportGenerator()
    filepath = generator.save_report()
================================================================================
"""

import xlwings as xw
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


# ============================================================================
# CONFIGURATION
# ============================================================================

RESULTS_DIR = Path(__file__).parent / "results"
WORKBOOK_NAME = "epoch_v1.xlsm"

# Column definitions for backtest worksheet (21 columns, A-U)
BACKTEST_HEADERS = [
    "trade_id", "date", "ticker", "model", "zone_type", "direction",
    "zone_high", "zone_low", "entry_price", "entry_time", "stop_price",
    "target_3r", "target_calc", "target_used", "exit_price", "exit_time",
    "exit_reason", "pnl_dollars", "pnl_r", "risk", "win"
]


# ============================================================================
# DATA READER
# ============================================================================

class ExcelDataReader:
    """Reads data from Excel worksheets for report generation."""

    def __init__(self, workbook_name: str = WORKBOOK_NAME):
        self.workbook_name = workbook_name
        self._wb = None

    def connect(self) -> bool:
        """Connect to the Excel workbook."""
        try:
            self._wb = xw.books[self.workbook_name]
            return True
        except Exception as e:
            print(f"  [ERROR] Failed to connect to Excel: {e}")
            return False

    def close(self):
        """Close connection."""
        self._wb = None

    def read_worksheet(self, sheet_name: str, range_str: str) -> List[List[Any]]:
        """Read data from a worksheet range."""
        if not self._wb:
            return []

        try:
            sheet = self._wb.sheets[sheet_name]
            data = sheet.range(range_str).value

            if data is None:
                return []

            # Normalize to list of lists
            if not isinstance(data, list):
                return [[data]]
            if data and not isinstance(data[0], list):
                return [data]

            # Filter out empty rows
            rows = []
            for row in data:
                if row and row[0] is not None and str(row[0]).strip() != "":
                    rows.append(row)
                else:
                    break

            return rows
        except Exception as e:
            print(f"  [WARNING] Could not read {sheet_name}: {e}")
            return []

    def read_backtest(self) -> List[List[Any]]:
        """Read backtest worksheet data."""
        return self.read_worksheet("backtest", "A2:U1000")


# ============================================================================
# STATISTICS CALCULATOR
# ============================================================================

class StatsCalculator:
    """Calculates summary statistics from raw data."""

    @staticmethod
    def _safe_float(val: Any) -> float:
        """Safely convert a value to float."""
        if val is None:
            return 0.0
        try:
            return float(val)
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def _safe_int(val: Any) -> int:
        """Safely convert a value to int."""
        if val is None:
            return 0
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return 0

    def calc_backtest_stats(self, rows: List[List[Any]]) -> Dict[str, Any]:
        """Calculate backtest summary statistics."""
        if not rows:
            return {"total_trades": 0}

        total = len(rows)
        wins = sum(1 for r in rows if self._safe_int(r[20]) == 1)  # win column

        pnl_r_values = [self._safe_float(r[18]) for r in rows if r[18] is not None]  # pnl_r column
        total_pnl = sum(pnl_r_values) if pnl_r_values else 0

        # By model
        by_model = {}
        for r in rows:
            model = r[3] or "Unknown"
            if model not in by_model:
                by_model[model] = {"trades": 0, "wins": 0, "pnl_r": 0}
            by_model[model]["trades"] += 1
            if self._safe_int(r[20]) == 1:
                by_model[model]["wins"] += 1
            if r[18] is not None:
                by_model[model]["pnl_r"] += self._safe_float(r[18])

        # By exit reason
        by_exit = {}
        for r in rows:
            exit_reason = r[16] or "Unknown"
            if exit_reason not in by_exit:
                by_exit[exit_reason] = {"trades": 0, "pnl_r": 0}
            by_exit[exit_reason]["trades"] += 1
            if r[18] is not None:
                by_exit[exit_reason]["pnl_r"] += self._safe_float(r[18])

        # By direction
        by_direction = {}
        for r in rows:
            direction = r[5] or "Unknown"
            if direction not in by_direction:
                by_direction[direction] = {"trades": 0, "wins": 0, "pnl_r": 0}
            by_direction[direction]["trades"] += 1
            if self._safe_int(r[20]) == 1:
                by_direction[direction]["wins"] += 1
            if r[18] is not None:
                by_direction[direction]["pnl_r"] += self._safe_float(r[18])

        win_rate = (wins / total * 100) if total > 0 else 0
        avg_r = (total_pnl / total) if total > 0 else 0

        # Profit factor
        gross_profit = sum(self._safe_float(r[18]) for r in rows if r[18] is not None and self._safe_float(r[18]) > 0)
        gross_loss = abs(sum(self._safe_float(r[18]) for r in rows if r[18] is not None and self._safe_float(r[18]) < 0))
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float('inf')

        return {
            "total_trades": total,
            "wins": wins,
            "losses": total - wins,
            "win_rate": win_rate,
            "total_pnl_r": total_pnl,
            "avg_r": avg_r,
            "profit_factor": profit_factor,
            "gross_profit": gross_profit,
            "gross_loss": gross_loss,
            "by_model": by_model,
            "by_exit": by_exit,
            "by_direction": by_direction,
        }


# ============================================================================
# REPORT GENERATOR
# ============================================================================

class BacktestReportGenerator:
    """Generates .txt report for backtest worksheet."""

    def __init__(self, workbook_name: str = WORKBOOK_NAME):
        self.reader = ExcelDataReader(workbook_name)
        self.stats = StatsCalculator()
        self.report_lines: List[str] = []

    def _add_line(self, line: str = ""):
        """Add a line to the report."""
        self.report_lines.append(line)

    def _add_separator(self, char: str = "=", width: int = 80):
        """Add a separator line."""
        self._add_line(char * width)

    def _format_value(self, val: Any) -> str:
        """Format a value for text output."""
        if val is None:
            return ""
        if isinstance(val, float):
            return f"{val:.4f}"
        if isinstance(val, datetime):
            return val.strftime("%Y-%m-%d %H:%M:%S")
        return str(val)

    def _add_raw_data_table(self, headers: List[str], rows: List[List[Any]]):
        """Add raw data as a pipe-delimited table."""
        if not rows:
            self._add_line("No data available.")
            return

        # Header row
        self._add_line("|" + "|".join(headers) + "|")
        self._add_line("|" + "|".join(["---"] * len(headers)) + "|")

        # Data rows
        for row in rows:
            formatted = [self._format_value(v) for v in row[:len(headers)]]
            self._add_line("|" + "|".join(formatted) + "|")

    def _generate_header(self):
        """Generate report header."""
        now = datetime.now()

        self._add_separator()
        self._add_line("EPOCH BACKTEST WORKSHEET REPORT")
        self._add_line("Generated for Claude AI Review")
        self._add_separator()
        self._add_line(f"Report Generated: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        self._add_line(f"Workbook: {WORKBOOK_NAME}")
        self._add_line(f"Worksheet: backtest")
        self._add_line()
        self._add_line("PURPOSE: This report contains raw data and summary statistics from")
        self._add_line("the backtest worksheet for validation and analysis by Claude AI.")
        self._add_separator()

    def _generate_stats_section(self, stats: Dict[str, Any]):
        """Generate statistics section."""
        self._add_line()
        self._add_line("SUMMARY STATISTICS")
        self._add_line("-" * 40)
        self._add_line(f"Total Trades:    {stats.get('total_trades', 0)}")
        self._add_line(f"Wins:            {stats.get('wins', 0)}")
        self._add_line(f"Losses:          {stats.get('losses', 0)}")
        self._add_line(f"Win Rate:        {stats.get('win_rate', 0):.1f}%")
        self._add_line(f"Total P&L:       {stats.get('total_pnl_r', 0):+.2f}R")
        self._add_line(f"Average R:       {stats.get('avg_r', 0):+.2f}R")
        self._add_line(f"Profit Factor:   {stats.get('profit_factor', 0):.2f}")
        self._add_line(f"Gross Profit:    {stats.get('gross_profit', 0):+.2f}R")
        self._add_line(f"Gross Loss:      {stats.get('gross_loss', 0):+.2f}R")

        self._add_line()
        self._add_line("BY MODEL:")
        for model, data in stats.get('by_model', {}).items():
            wr = (data['wins'] / data['trades'] * 100) if data['trades'] > 0 else 0
            self._add_line(f"  {model}: {data['trades']} trades, {wr:.0f}% WR, {data['pnl_r']:+.2f}R")

        self._add_line()
        self._add_line("BY EXIT REASON:")
        for reason, data in stats.get('by_exit', {}).items():
            self._add_line(f"  {reason}: {data['trades']} trades, {data['pnl_r']:+.2f}R")

        self._add_line()
        self._add_line("BY DIRECTION:")
        for direction, data in stats.get('by_direction', {}).items():
            wr = (data['wins'] / data['trades'] * 100) if data['trades'] > 0 else 0
            self._add_line(f"  {direction}: {data['trades']} trades, {wr:.0f}% WR, {data['pnl_r']:+.2f}R")

    def _generate_validation_checklist(self):
        """Generate validation checklist."""
        self._add_line()
        self._add_separator("-", 40)
        self._add_line("VALIDATION CHECKLIST")
        self._add_separator("-", 40)
        self._add_line()
        self._add_line("[ ] Win/Loss classification matches pnl_r sign (positive = win)")
        self._add_line("[ ] P&L R calculation: (exit_price - entry_price) / risk is correct")
        self._add_line("[ ] Exit reasons align with price action (stop hit, target hit, etc.)")
        self._add_line("[ ] Trade direction matches zone type logic")

    def _generate_footer(self):
        """Generate report footer."""
        self._add_line()
        self._add_separator()
        self._add_line("END OF BACKTEST REPORT")
        self._add_separator()

    def generate(self) -> str:
        """Generate the complete report."""
        self.report_lines = []

        # Connect to Excel
        if not self.reader.connect():
            return "ERROR: Could not connect to Excel workbook"

        try:
            # Read data
            print("  Reading backtest data...")
            backtest_rows = self.reader.read_backtest()

            # Calculate statistics
            print("  Calculating statistics...")
            stats = self.stats.calc_backtest_stats(backtest_rows)

            # Generate report sections
            print("  Generating report...")
            self._generate_header()
            self._generate_stats_section(stats)

            # Raw data
            self._add_line()
            self._add_line("RAW DATA")
            self._add_line("-" * 40)
            self._add_raw_data_table(BACKTEST_HEADERS, backtest_rows)

            self._generate_validation_checklist()
            self._generate_footer()

            return "\n".join(self.report_lines)

        finally:
            self.reader.close()

    def save_report(self) -> Optional[Path]:
        """Generate and save the report to file."""
        # Ensure results directory exists
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)

        # Generate filename with date
        date_str = datetime.now().strftime("%m%d%y")
        filename = f"backtest_{date_str}_bt_report.txt"
        filepath = RESULTS_DIR / filename

        print(f"\nGenerating backtest report...")

        # Generate report content
        content = self.generate()

        if content.startswith("ERROR"):
            print(f"  {content}")
            return None

        # Write to file
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"  Report saved: {filepath}")
            print(f"  Size: {len(content):,} characters, {len(self.report_lines):,} lines")

            return filepath

        except Exception as e:
            print(f"  ERROR saving report: {e}")
            return None


# ============================================================================
# STANDALONE ENTRY POINT
# ============================================================================

def main():
    """Standalone entry point for testing."""
    print("=" * 70)
    print("BACKTEST REPORT GENERATOR")
    print("=" * 70)

    generator = BacktestReportGenerator()
    filepath = generator.save_report()

    if filepath:
        print(f"\nReport generated successfully: {filepath}")
    else:
        print("\nReport generation failed.")


if __name__ == "__main__":
    main()
