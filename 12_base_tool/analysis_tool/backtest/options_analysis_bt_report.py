"""
================================================================================
EPOCH TRADING SYSTEM - OPTIONS ANALYSIS WORKSHEET REPORT GENERATOR
================================================================================
Generates a .txt report for the options_analysis worksheet for Claude AI analysis.

Output: results/ subdirectory with filename: options_analysis_MMDDYY_bt_report.txt

v1.0 Format: 22 columns (A-V) including options P&L and R-multiples

Usage:
    from options_analysis_bt_report import OptionsAnalysisReportGenerator
    generator = OptionsAnalysisReportGenerator()
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

# Column definitions for options_analysis worksheet (22 columns, A-V)
OPTIONS_ANALYSIS_HEADERS = [
    # A-E: Trade Identification
    "Trade_ID", "Ticker", "Direction", "Entry_Date", "Entry_Time",
    # F-J: Entry and Contract Details
    "Entry_Price", "Options_Ticker", "Strike", "Expiration", "Contract_Type",
    # K-N: Options Entry/Exit
    "Option_Entry_Price", "Option_Entry_Time", "Option_Exit_Price", "Option_Exit_Time",
    # O-R: P&L Metrics
    "PnL_Dollars", "PnL_Percent", "Option_R", "Net_Return",
    # S-V: Comparison and Status
    "Underlying_R", "R_Multiplier", "Win", "Status"
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

    def read_options_analysis(self) -> List[List[Any]]:
        """Read options_analysis worksheet data (22 columns, A-V)."""
        return self.read_worksheet("options_analysis", "A2:V10000")


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

    def calc_options_analysis_stats(self, rows: List[List[Any]]) -> Dict[str, Any]:
        """Calculate options analysis summary statistics."""
        if not rows:
            return {"total_rows": 0}

        total = len(rows)

        # Count by status (column index 21 = Status)
        status_counts = {}
        for r in rows:
            if len(r) > 21:
                status = str(r[21]) if r[21] else "UNKNOWN"
                status_counts[status] = status_counts.get(status, 0) + 1

        successful = status_counts.get("SUCCESS", 0)
        failed = total - successful

        # Filter successful trades for metrics
        successful_rows = [r for r in rows if len(r) > 21 and str(r[21]) == "SUCCESS"]

        if not successful_rows:
            return {
                "total_rows": total,
                "successful": 0,
                "failed": failed,
                "status_counts": status_counts
            }

        # P&L statistics (column index 14 = PnL_Dollars)
        pnl_values = [self._safe_float(r[14]) for r in successful_rows if len(r) > 14 and r[14] is not None]
        total_pnl = sum(pnl_values)
        avg_pnl = total_pnl / len(pnl_values) if pnl_values else 0

        # Percentage returns (column index 15 = PnL_Percent)
        pct_values = [self._safe_float(r[15]) * 100 for r in successful_rows if len(r) > 15 and r[15] is not None]
        avg_pct = sum(pct_values) / len(pct_values) if pct_values else 0

        # Option R-multiples (column index 16 = Option_R)
        option_r_values = [self._safe_float(r[16]) for r in successful_rows if len(r) > 16 and r[16] is not None]
        avg_option_r = sum(option_r_values) / len(option_r_values) if option_r_values else 0
        total_option_r = sum(option_r_values)
        best_option_r = max(option_r_values) if option_r_values else 0
        worst_option_r = min(option_r_values) if option_r_values else 0

        # Underlying R-multiples (column index 18 = Underlying_R)
        underlying_r_values = [self._safe_float(r[18]) for r in successful_rows if len(r) > 18 and r[18] is not None]
        avg_underlying_r = sum(underlying_r_values) / len(underlying_r_values) if underlying_r_values else 0

        # R Multiplier (column index 19 = R_Multiplier)
        r_mult_values = [self._safe_float(r[19]) for r in successful_rows if len(r) > 19 and r[19] is not None and r[19] != '']
        avg_r_mult = sum(r_mult_values) / len(r_mult_values) if r_mult_values else 0

        # Win/Loss (column index 20 = Win)
        wins = sum(1 for r in successful_rows if len(r) > 20 and self._safe_int(r[20]) == 1)
        losses = len(successful_rows) - wins
        win_rate = (wins / len(successful_rows) * 100) if successful_rows else 0

        # Outperformance analysis
        outperformed = sum(1 for r in successful_rows if len(r) > 19 and self._safe_float(r[19]) > 1.0)

        # Direction breakdown
        direction_stats = {}
        for r in successful_rows:
            if len(r) > 16:
                direction = str(r[2]) if r[2] else "UNKNOWN"
                option_r = self._safe_float(r[16])
                if direction not in direction_stats:
                    direction_stats[direction] = {"count": 0, "r_values": [], "wins": 0}
                direction_stats[direction]["count"] += 1
                direction_stats[direction]["r_values"].append(option_r)
                if len(r) > 20 and self._safe_int(r[20]) == 1:
                    direction_stats[direction]["wins"] += 1

        for direction in direction_stats:
            vals = direction_stats[direction]["r_values"]
            direction_stats[direction]["avg_r"] = sum(vals) / len(vals) if vals else 0
            direction_stats[direction]["win_rate"] = (
                direction_stats[direction]["wins"] / direction_stats[direction]["count"] * 100
                if direction_stats[direction]["count"] > 0 else 0
            )

        # Contract type breakdown
        contract_stats = {}
        for r in successful_rows:
            if len(r) > 16:
                contract_type = str(r[9]) if r[9] else "UNKNOWN"
                option_r = self._safe_float(r[16])
                if contract_type not in contract_stats:
                    contract_stats[contract_type] = {"count": 0, "r_values": [], "wins": 0}
                contract_stats[contract_type]["count"] += 1
                contract_stats[contract_type]["r_values"].append(option_r)
                if len(r) > 20 and self._safe_int(r[20]) == 1:
                    contract_stats[contract_type]["wins"] += 1

        for ctype in contract_stats:
            vals = contract_stats[ctype]["r_values"]
            contract_stats[ctype]["avg_r"] = sum(vals) / len(vals) if vals else 0
            contract_stats[ctype]["win_rate"] = (
                contract_stats[ctype]["wins"] / contract_stats[ctype]["count"] * 100
                if contract_stats[ctype]["count"] > 0 else 0
            )

        return {
            "total_rows": total,
            "successful": successful,
            "failed": failed,
            "status_counts": status_counts,
            "total_pnl": total_pnl,
            "avg_pnl": avg_pnl,
            "avg_pct": avg_pct,
            "avg_option_r": avg_option_r,
            "total_option_r": total_option_r,
            "best_option_r": best_option_r,
            "worst_option_r": worst_option_r,
            "avg_underlying_r": avg_underlying_r,
            "avg_r_mult": avg_r_mult,
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
            "outperformed": outperformed,
            "direction_stats": direction_stats,
            "contract_stats": contract_stats,
        }


# ============================================================================
# REPORT GENERATOR
# ============================================================================

class OptionsAnalysisReportGenerator:
    """Generates .txt report for options_analysis worksheet."""

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
        self._add_line("EPOCH OPTIONS ANALYSIS WORKSHEET REPORT")
        self._add_line("Generated for Claude AI Review")
        self._add_separator()
        self._add_line(f"Report Generated: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        self._add_line(f"Workbook: {WORKBOOK_NAME}")
        self._add_line(f"Worksheet: options_analysis")
        self._add_line(f"Schema: v1.0 (22 columns, A-V)")
        self._add_line()
        self._add_line("PURPOSE: This report contains options analysis data comparing")
        self._add_line("options performance to underlying equity trades for each backtest trade.")
        self._add_line()
        self._add_line("STRUCTURE: 1 row per trade with options P&L and R-multiple comparison.")
        self._add_separator()

    def _generate_stats_section(self, stats: Dict[str, Any]):
        """Generate statistics section."""
        self._add_line()
        self._add_line("SUMMARY STATISTICS")
        self._add_line("-" * 40)
        self._add_line(f"Total Trades:          {stats.get('total_rows', 0)}")
        self._add_line(f"Successful:            {stats.get('successful', 0)}")
        self._add_line(f"Failed (No Data):      {stats.get('failed', 0)}")
        self._add_line()

        if stats.get('successful', 0) > 0:
            self._add_line("P&L METRICS (Successful Trades Only):")
            self._add_line(f"  Total P&L:           ${stats.get('total_pnl', 0):,.2f}")
            self._add_line(f"  Avg P&L:             ${stats.get('avg_pnl', 0):,.2f}")
            self._add_line(f"  Avg Return:          {stats.get('avg_pct', 0):.1f}%")
            self._add_line()
            self._add_line("R-MULTIPLE METRICS:")
            self._add_line(f"  Total Options R:     {stats.get('total_option_r', 0):+.2f}R")
            self._add_line(f"  Avg Options R:       {stats.get('avg_option_r', 0):+.2f}R")
            self._add_line(f"  Best Options R:      {stats.get('best_option_r', 0):+.2f}R")
            self._add_line(f"  Worst Options R:     {stats.get('worst_option_r', 0):+.2f}R")
            self._add_line(f"  Avg Underlying R:    {stats.get('avg_underlying_r', 0):+.2f}R")
            self._add_line(f"  Avg R Multiplier:    {stats.get('avg_r_mult', 0):.2f}x")
            self._add_line()
            self._add_line("WIN/LOSS ANALYSIS:")
            self._add_line(f"  Wins:                {stats.get('wins', 0)}")
            self._add_line(f"  Losses:              {stats.get('losses', 0)}")
            self._add_line(f"  Win Rate:            {stats.get('win_rate', 0):.1f}%")
            self._add_line(f"  Outperformed Equity: {stats.get('outperformed', 0)}/{stats.get('successful', 0)}")

            self._add_line()
            self._add_line("DIRECTION BREAKDOWN:")
            for direction, data in stats.get('direction_stats', {}).items():
                self._add_line(f"  {direction}: {data['count']} trades, {data['avg_r']:+.2f}R avg, {data['win_rate']:.0f}% win")

            self._add_line()
            self._add_line("CONTRACT TYPE BREAKDOWN:")
            for ctype, data in stats.get('contract_stats', {}).items():
                self._add_line(f"  {ctype}: {data['count']} trades, {data['avg_r']:+.2f}R avg, {data['win_rate']:.0f}% win")

        self._add_line()
        self._add_line("STATUS BREAKDOWN:")
        for status, count in stats.get('status_counts', {}).items():
            self._add_line(f"  {status}: {count}")

    def _generate_validation_checklist(self):
        """Generate validation checklist."""
        self._add_line()
        self._add_separator("-", 40)
        self._add_line("VALIDATION CHECKLIST")
        self._add_separator("-", 40)
        self._add_line()
        self._add_line("[ ] Trade_ID matches backtest worksheet")
        self._add_line("[ ] Options ticker format is valid (O:TICKER...)")
        self._add_line("[ ] Entry/Exit prices are within reasonable range")
        self._add_line("[ ] PnL_Dollars matches (Exit - Entry) * 100")
        self._add_line("[ ] Option_R calculation uses correct underlying risk")
        self._add_line("[ ] R_Multiplier = Option_R / Underlying_R")
        self._add_line("[ ] Win column matches PnL direction")

    def _generate_analysis_focus(self):
        """Generate analysis focus areas."""
        self._add_line()
        self._add_separator("-", 40)
        self._add_line("ANALYSIS FOCUS AREAS")
        self._add_separator("-", 40)
        self._add_line()
        self._add_line("1. OPTIONS VS EQUITY COMPARISON")
        self._add_line("   - Do options amplify R-multiples as expected?")
        self._add_line("   - What is the average R multiplier (options R / equity R)?")
        self._add_line("   - Which trades benefit most from options leverage?")
        self._add_line()
        self._add_line("2. CONTRACT SELECTION QUALITY")
        self._add_line("   - Are first ITM contracts providing good fills?")
        self._add_line("   - Do CALL vs PUT performance differ significantly?")
        self._add_line("   - Is expiration selection (2+ days out) appropriate?")
        self._add_line()
        self._add_line("3. FAILURE ANALYSIS")
        self._add_line("   - Why do some trades have NO_CHAIN or NO_CONTRACT?")
        self._add_line("   - Are there patterns in failed option lookups?")
        self._add_line("   - Should we relax/tighten contract selection criteria?")
        self._add_line()
        self._add_line("4. RISK/REWARD OPTIMIZATION")
        self._add_line("   - Is options trading improving overall system performance?")
        self._add_line("   - What is the net R contribution from options?")
        self._add_line("   - Should we trade options on all entries or filter?")

    def _generate_footer(self):
        """Generate report footer."""
        self._add_line()
        self._add_separator()
        self._add_line("END OF OPTIONS ANALYSIS REPORT")
        self._add_separator()

    def generate(self) -> str:
        """Generate the complete report."""
        self.report_lines = []

        # Connect to Excel
        if not self.reader.connect():
            return "ERROR: Could not connect to Excel workbook"

        try:
            # Read data
            print("  Reading options_analysis data...")
            options_rows = self.reader.read_options_analysis()

            # Calculate statistics
            print("  Calculating statistics...")
            stats = self.stats.calc_options_analysis_stats(options_rows)

            # Generate report sections
            print("  Generating report...")
            self._generate_header()
            self._generate_stats_section(stats)

            # Raw data
            self._add_line()
            self._add_line("RAW DATA")
            self._add_line("-" * 40)
            self._add_raw_data_table(OPTIONS_ANALYSIS_HEADERS, options_rows)

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
        filename = f"options_analysis_{date_str}_bt_report.txt"
        filepath = RESULTS_DIR / filename

        print(f"\nGenerating options_analysis report...")

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
    print("OPTIONS ANALYSIS REPORT GENERATOR")
    print("=" * 70)

    generator = OptionsAnalysisReportGenerator()
    filepath = generator.save_report()

    if filepath:
        print(f"\nReport generated successfully: {filepath}")
    else:
        print("\nReport generation failed.")


if __name__ == "__main__":
    main()
