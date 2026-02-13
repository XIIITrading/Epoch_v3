"""
================================================================================
EPOCH TRADING SYSTEM - OPTIMAL TRADE WORKSHEET REPORT GENERATOR
================================================================================
Generates a .txt report for the optimal_trade worksheet for Claude AI analysis.

Output: results/ subdirectory with filename: optimal_trade_MMDDYY_bt_report.txt

v3.1 Format: 45 columns (A-AS) including decay analysis and Win column

Usage:
    from optimal_trade_bt_report import OptimalTradeReportGenerator
    generator = OptimalTradeReportGenerator()
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

# Column definitions for optimal_trade worksheet (45 columns, A-AS)
OPTIMAL_TRADE_HEADERS = [
    # A-E: Trade ID
    "Trade_ID", "Date", "Ticker", "Direction", "Model",
    # F-J: Entry Conditions
    "Entry_Health", "Entry_Label", "Entry_VWAP", "Entry_Trend", "Entry_Structure",
    # K-R: Bar Data
    "Bar_Seq", "Bar_Time", "Bars_From_Entry", "Bars_From_MFE", "Event_Type",
    "Price", "R_If_Exit", "Health",
    # S-W: Current State
    "VWAP", "SMA9", "SMA21", "Volume", "Swing_High",
    # X-AB: Comparison
    "Health_vs_Entry", "R_vs_MFE", "R_vs_Actual", "Is_MFE", "Is_Exit",
    # AC-AL: Decay Analysis
    "Is_Post_MFE", "Bars_After_MFE", "R_Given_Back", "Health_at_MFE", "Health_Decay",
    "VWAP_Same", "SMA_Same", "Structure_Same", "CVD_Same", "Is_First_Flip",
    # AM-AS: Outcome
    "Actual_Exit_Price", "Actual_Exit_Time", "Actual_R", "Exit_Reason",
    "MFE_R", "MAE_R", "Win"
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

    def read_optimal_trade(self) -> List[List[Any]]:
        """Read optimal_trade worksheet data (45 columns, A-AS)."""
        return self.read_worksheet("optimal_trade", "A2:AS10000")


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

    def calc_optimal_trade_stats(self, rows: List[List[Any]]) -> Dict[str, Any]:
        """Calculate optimal trade summary statistics."""
        if not rows:
            return {"total_rows": 0}

        total = len(rows)

        # Unique trades
        trade_ids = set(r[0] for r in rows if r[0] is not None)

        # R statistics (column index 16 = R_If_Exit)
        r_values = [self._safe_float(r[16]) for r in rows if len(r) > 16 and r[16] is not None]
        avg_r_if_exit = sum(r_values) / len(r_values) if r_values else 0

        # Health at each bar (column index 17 = Health)
        health_r_map = {}
        for r in rows:
            if len(r) > 17:
                health = self._safe_int(r[17]) if r[17] is not None else None
                r_val = self._safe_float(r[16]) if len(r) > 16 and r[16] is not None else None
                if health is not None and r_val is not None:
                    if health not in health_r_map:
                        health_r_map[health] = []
                    health_r_map[health].append(r_val)

        health_avg_r = {}
        for h, vals in health_r_map.items():
            health_avg_r[h] = {
                "count": len(vals),
                "avg_r": sum(vals) / len(vals) if vals else 0,
                "win_rate": sum(1 for v in vals if v > 0) / len(vals) * 100 if vals else 0
            }

        # MFE rows (column index 26 = Is_MFE)
        mfe_rows = [r for r in rows if len(r) > 26 and self._safe_int(r[26]) == 1]
        mfe_r_values = [self._safe_float(r[16]) for r in mfe_rows if len(r) > 16 and r[16] is not None]
        avg_mfe_r = sum(mfe_r_values) / len(mfe_r_values) if mfe_r_values else 0

        # Exit rows (column index 27 = Is_Exit)
        exit_rows = [r for r in rows if len(r) > 27 and self._safe_int(r[27]) == 1]
        actual_r_values = [self._safe_float(r[42]) for r in exit_rows if len(r) > 42 and r[42] is not None]  # Actual_R
        avg_actual_r = sum(actual_r_values) / len(actual_r_values) if actual_r_values else 0

        # Capture rate
        capture_rate = (avg_actual_r / avg_mfe_r * 100) if avg_mfe_r > 0 else 0

        # Win statistics (column index 44 = Win)
        wins_by_exit = sum(1 for r in exit_rows if len(r) > 44 and self._safe_int(r[44]) == 1)
        losses_by_exit = len(exit_rows) - wins_by_exit
        win_rate = (wins_by_exit / len(exit_rows) * 100) if exit_rows else 0

        # Decay analysis stats
        post_mfe_rows = [r for r in rows if len(r) > 28 and self._safe_int(r[28]) == 1]  # Is_Post_MFE
        avg_r_given_back = 0
        if post_mfe_rows:
            r_given_back_vals = [self._safe_float(r[30]) for r in post_mfe_rows if len(r) > 30]  # R_Given_Back
            avg_r_given_back = sum(r_given_back_vals) / len(r_given_back_vals) if r_given_back_vals else 0

        # First flip stats
        first_flip_rows = [r for r in rows if len(r) > 37 and self._safe_int(r[37]) == 1]  # Is_First_Flip
        first_flip_r_values = [self._safe_float(r[16]) for r in first_flip_rows if len(r) > 16 and r[16] is not None]
        avg_first_flip_r = sum(first_flip_r_values) / len(first_flip_r_values) if first_flip_r_values else 0

        return {
            "total_rows": total,
            "unique_trades": len(trade_ids),
            "avg_bars_per_trade": total / len(trade_ids) if trade_ids else 0,
            "avg_r_if_exit": avg_r_if_exit,
            "avg_mfe_r": avg_mfe_r,
            "avg_actual_r": avg_actual_r,
            "capture_rate": capture_rate,
            "health_avg_r": health_avg_r,
            "wins": wins_by_exit,
            "losses": losses_by_exit,
            "win_rate": win_rate,
            "post_mfe_rows": len(post_mfe_rows),
            "avg_r_given_back": avg_r_given_back,
            "first_flip_count": len(first_flip_rows),
            "avg_first_flip_r": avg_first_flip_r,
        }


# ============================================================================
# REPORT GENERATOR
# ============================================================================

class OptimalTradeReportGenerator:
    """Generates .txt report for optimal_trade worksheet."""

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
        self._add_line("EPOCH OPTIMAL TRADE WORKSHEET REPORT")
        self._add_line("Generated for Claude AI Review")
        self._add_separator()
        self._add_line(f"Report Generated: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        self._add_line(f"Workbook: {WORKBOOK_NAME}")
        self._add_line(f"Worksheet: optimal_trade")
        self._add_line(f"Schema: v3.1 (45 columns, A-AS)")
        self._add_line()
        self._add_line("PURPOSE: This report contains expanded analysis data for each bar")
        self._add_line("of each trade, enabling AI-driven pattern discovery for exit optimization.")
        self._add_line()
        self._add_line("STRUCTURE: 1 row per bar per trade (~N trades x ~28 bars = 1,500+ rows)")
        self._add_line("Each row answers: 'If I exited HERE, what would happen?'")
        self._add_separator()

    def _generate_stats_section(self, stats: Dict[str, Any]):
        """Generate statistics section."""
        self._add_line()
        self._add_line("SUMMARY STATISTICS")
        self._add_line("-" * 40)
        self._add_line(f"Total Decision Points: {stats.get('total_rows', 0)}")
        self._add_line(f"Unique Trades:         {stats.get('unique_trades', 0)}")
        self._add_line(f"Avg Bars per Trade:    {stats.get('avg_bars_per_trade', 0):.1f}")
        self._add_line()
        self._add_line(f"Avg R if Exit:         {stats.get('avg_r_if_exit', 0):+.2f}R")
        self._add_line(f"Avg MFE R:             {stats.get('avg_mfe_r', 0):+.2f}R")
        self._add_line(f"Avg Actual R:          {stats.get('avg_actual_r', 0):+.2f}R")
        self._add_line(f"Capture Rate:          {stats.get('capture_rate', 0):.1f}%")

        self._add_line()
        self._add_line("WIN/LOSS (by exit rows):")
        self._add_line(f"  Wins:                {stats.get('wins', 0)}")
        self._add_line(f"  Losses:              {stats.get('losses', 0)}")
        self._add_line(f"  Win Rate:            {stats.get('win_rate', 0):.1f}%")

        self._add_line()
        self._add_line("DECAY ANALYSIS (Post-MFE):")
        self._add_line(f"  Post-MFE Rows:       {stats.get('post_mfe_rows', 0)}")
        self._add_line(f"  Avg R Given Back:    {stats.get('avg_r_given_back', 0):.2f}R")
        self._add_line(f"  First Flip Events:   {stats.get('first_flip_count', 0)}")
        self._add_line(f"  Avg R at First Flip: {stats.get('avg_first_flip_r', 0):+.2f}R")

        self._add_line()
        self._add_line("HEALTH SCORE -> AVERAGE R IF EXIT:")
        for health in sorted(stats.get('health_avg_r', {}).keys(), reverse=True):
            data = stats['health_avg_r'][health]
            self._add_line(f"  Health {health}: {data['count']} bars, {data['avg_r']:+.2f}R avg, {data['win_rate']:.0f}% win")

    def _generate_validation_checklist(self):
        """Generate validation checklist."""
        self._add_line()
        self._add_separator("-", 40)
        self._add_line("VALIDATION CHECKLIST")
        self._add_separator("-", 40)
        self._add_line()
        self._add_line("[ ] R_if_exit calculation matches price at that bar")
        self._add_line("[ ] Is_MFE=1 correctly identifies maximum favorable excursion")
        self._add_line("[ ] Is_Exit=1 correctly identifies actual exit bar")
        self._add_line("[ ] Health_vs_Entry delta is calculated correctly")
        self._add_line("[ ] Decay analysis columns correctly track post-MFE deterioration")
        self._add_line("[ ] Win column matches backtest worksheet values")

    def _generate_analysis_focus(self):
        """Generate analysis focus areas."""
        self._add_line()
        self._add_separator("-", 40)
        self._add_line("ANALYSIS FOCUS AREAS")
        self._add_separator("-", 40)
        self._add_line()
        self._add_line("1. EXIT OPTIMIZATION")
        self._add_line("   - What health score threshold would optimize exits?")
        self._add_line("   - How much R is being left on the table (capture rate)?")
        self._add_line("   - What's the optimal number of bars after MFE to exit?")
        self._add_line()
        self._add_line("2. DECAY PATTERNS")
        self._add_line("   - How quickly does R decay after MFE?")
        self._add_line("   - What indicator flips correlate with R decay?")
        self._add_line("   - Is first flip a reliable exit signal?")
        self._add_line()
        self._add_line("3. HEALTH CORRELATION")
        self._add_line("   - Do higher entry health scores lead to better outcomes?")
        self._add_line("   - What health decay rate predicts losers?")
        self._add_line("   - Can we exit on health threshold alone?")

    def _generate_footer(self):
        """Generate report footer."""
        self._add_line()
        self._add_separator()
        self._add_line("END OF OPTIMAL TRADE REPORT")
        self._add_separator()

    def generate(self) -> str:
        """Generate the complete report."""
        self.report_lines = []

        # Connect to Excel
        if not self.reader.connect():
            return "ERROR: Could not connect to Excel workbook"

        try:
            # Read data
            print("  Reading optimal_trade data...")
            optimal_trade_rows = self.reader.read_optimal_trade()

            # Calculate statistics
            print("  Calculating statistics...")
            stats = self.stats.calc_optimal_trade_stats(optimal_trade_rows)

            # Generate report sections
            print("  Generating report...")
            self._generate_header()
            self._generate_stats_section(stats)

            # Raw data
            self._add_line()
            self._add_line("RAW DATA")
            self._add_line("-" * 40)
            self._add_raw_data_table(OPTIMAL_TRADE_HEADERS, optimal_trade_rows)

            self._generate_validation_checklist()
            self._generate_analysis_focus()
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
        filename = f"optimal_trade_{date_str}_bt_report.txt"
        filepath = RESULTS_DIR / filename

        print(f"\nGenerating optimal_trade report...")

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
    print("OPTIMAL TRADE REPORT GENERATOR")
    print("=" * 70)

    generator = OptimalTradeReportGenerator()
    filepath = generator.save_report()

    if filepath:
        print(f"\nReport generated successfully: {filepath}")
    else:
        print("\nReport generation failed.")


if __name__ == "__main__":
    main()
