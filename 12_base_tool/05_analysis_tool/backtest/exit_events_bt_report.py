"""
================================================================================
EPOCH TRADING SYSTEM - EXIT EVENTS WORKSHEET REPORT GENERATOR
================================================================================
Generates a .txt report for the exit_events worksheet for Claude AI analysis.

Output: results/ subdirectory with filename: exit_events_MMDDYY_bt_report.txt

v3.2 Format: 32 columns (A-AF) including Win column

Usage:
    from exit_events_bt_report import ExitEventsReportGenerator
    generator = ExitEventsReportGenerator()
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

# Column definitions for exit_events worksheet (32 columns, A-AF)
EXIT_EVENTS_HEADERS = [
    # A-E: Core identification
    "Trade_ID",           # A - Join key (NOT unique)
    "Event_Seq",          # B
    "Event_Time",         # C
    "Bars_From_Entry",    # D
    "Bars_From_MFE",      # E

    # F-H: Event details
    "Event_Type",         # F
    "From_State",         # G
    "To_State",           # H

    # I-L: Position at event
    "Price_at_Event",     # I
    "R_at_Event",         # J
    "Health_Score",       # K
    "Health_Delta",       # L

    # M-O: Price indicators
    "VWAP",               # M
    "SMA9",               # N
    "SMA21",              # O

    # P: Volume (raw)
    "Volume",             # P

    # Q-S: Volume indicators
    "Vol_ROC",            # Q
    "Vol_Delta",          # R
    "CVD_Slope",          # S

    # T-U: SMA analysis
    "SMA_Spread",         # T
    "SMA_Momentum",       # U

    # V-Y: Structure
    "M5_Structure",       # V
    "M15_Structure",      # W
    "H1_Structure",       # X
    "H4_Structure",       # Y

    # Z-AB: Swing levels
    "Swing_High",         # Z
    "Swing_Low",          # AA
    "Bars_Since_Swing",   # AB

    # AC-AE: v3.0 columns
    "Health_Summary",     # AC
    "Event_Priority",     # AD
    "Indicator_Changed",  # AE

    # AF: Trade Outcome (v3.1)
    "Win",                # AF
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

    def read_exit_events(self) -> List[List[Any]]:
        """Read exit_events worksheet data (32 columns, A-AF)."""
        return self.read_worksheet("exit_events", "A2:AF10000")


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

    def calc_exit_events_stats(self, rows: List[List[Any]]) -> Dict[str, Any]:
        """Calculate exit events summary statistics."""
        if not rows:
            return {"total_events": 0}

        total = len(rows)

        # Unique trades
        trade_ids = set(r[0] for r in rows if r[0] is not None)

        # Event type distribution (column index 5 = event_type)
        event_types = {}
        for r in rows:
            event_type = r[5] or "Unknown"
            event_types[event_type] = event_types.get(event_type, 0) + 1

        # Health score stats (column index 10 = health_score)
        health_scores = [self._safe_float(r[10]) for r in rows if r[10] is not None]
        avg_health = sum(health_scores) / len(health_scores) if health_scores else 0

        # Health delta stats (column index 11 = health_delta)
        health_deltas = [self._safe_float(r[11]) for r in rows if r[11] is not None]
        degradation_events = sum(1 for d in health_deltas if d < 0)

        # MFE/MAE counts
        mfe_count = sum(1 for r in rows if r[5] and "MFE" in str(r[5]))
        mae_count = sum(1 for r in rows if r[5] and "MAE" in str(r[5]))
        entry_count = sum(1 for r in rows if r[5] and str(r[5]) == "ENTRY")
        exit_count = sum(1 for r in rows if r[5] and str(r[5]) == "EXIT")

        # Health summary distribution (column index 28 = Health_Summary)
        health_summary_dist = {}
        for r in rows:
            if len(r) > 28:
                summary = r[28] or "Unknown"
                health_summary_dist[summary] = health_summary_dist.get(summary, 0) + 1

        # Event priority distribution (column index 29 = Event_Priority)
        priority_dist = {}
        for r in rows:
            if len(r) > 29:
                priority = r[29] or "Unknown"
                priority_dist[priority] = priority_dist.get(priority, 0) + 1

        # Win statistics (column index 31 = Win)
        wins = sum(1 for r in rows if len(r) > 31 and self._safe_int(r[31]) == 1)
        unique_wins = len(set(r[0] for r in rows if len(r) > 31 and self._safe_int(r[31]) == 1 and r[0]))
        unique_losses = len(trade_ids) - unique_wins

        return {
            "total_events": total,
            "unique_trades": len(trade_ids),
            "avg_events_per_trade": total / len(trade_ids) if trade_ids else 0,
            "event_types": event_types,
            "avg_health": avg_health,
            "degradation_events": degradation_events,
            "mfe_count": mfe_count,
            "mae_count": mae_count,
            "entry_count": entry_count,
            "exit_count": exit_count,
            "health_summary_dist": health_summary_dist,
            "priority_dist": priority_dist,
            "unique_wins": unique_wins,
            "unique_losses": unique_losses,
            "win_rate": (unique_wins / len(trade_ids) * 100) if trade_ids else 0,
        }


# ============================================================================
# REPORT GENERATOR
# ============================================================================

class ExitEventsReportGenerator:
    """Generates .txt report for exit_events worksheet."""

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
        self._add_line("EPOCH EXIT EVENTS WORKSHEET REPORT")
        self._add_line("Generated for Claude AI Review")
        self._add_separator()
        self._add_line(f"Report Generated: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        self._add_line(f"Workbook: {WORKBOOK_NAME}")
        self._add_line(f"Worksheet: exit_events")
        self._add_line(f"Schema: v3.2 (32 columns, A-AF)")
        self._add_line()
        self._add_line("PURPOSE: This report contains raw data and summary statistics from")
        self._add_line("the exit_events worksheet for validation and analysis by Claude AI.")
        self._add_line()
        self._add_line("NOTE: trade_id is NOT unique in exit_events - multiple events share")
        self._add_line("the same trade_id. Use (trade_id, event_seq) for unique identification.")
        self._add_separator()

    def _generate_stats_section(self, stats: Dict[str, Any]):
        """Generate statistics section."""
        self._add_line()
        self._add_line("SUMMARY STATISTICS")
        self._add_line("-" * 40)
        self._add_line(f"Total Events:        {stats.get('total_events', 0)}")
        self._add_line(f"Unique Trades:       {stats.get('unique_trades', 0)}")
        self._add_line(f"Avg Events/Trade:    {stats.get('avg_events_per_trade', 0):.1f}")
        self._add_line(f"Avg Health Score:    {stats.get('avg_health', 0):.1f}")
        self._add_line(f"Degradation Events:  {stats.get('degradation_events', 0)}")
        self._add_line()
        self._add_line(f"Entry Events:        {stats.get('entry_count', 0)}")
        self._add_line(f"Exit Events:         {stats.get('exit_count', 0)}")
        self._add_line(f"MFE Events:          {stats.get('mfe_count', 0)}")
        self._add_line(f"MAE Events:          {stats.get('mae_count', 0)}")

        self._add_line()
        self._add_line("WIN/LOSS (by unique trade):")
        self._add_line(f"  Winning Trades:    {stats.get('unique_wins', 0)}")
        self._add_line(f"  Losing Trades:     {stats.get('unique_losses', 0)}")
        self._add_line(f"  Win Rate:          {stats.get('win_rate', 0):.1f}%")

        self._add_line()
        self._add_line("EVENT TYPE DISTRIBUTION:")
        for event_type, count in sorted(stats.get('event_types', {}).items(), key=lambda x: x[1], reverse=True):
            self._add_line(f"  {event_type}: {count}")

        self._add_line()
        self._add_line("HEALTH SUMMARY DISTRIBUTION:")
        for summary, count in stats.get('health_summary_dist', {}).items():
            self._add_line(f"  {summary}: {count}")

        self._add_line()
        self._add_line("EVENT PRIORITY DISTRIBUTION:")
        for priority, count in stats.get('priority_dist', {}).items():
            self._add_line(f"  {priority}: {count}")

    def _generate_validation_checklist(self):
        """Generate validation checklist."""
        self._add_line()
        self._add_separator("-", 40)
        self._add_line("VALIDATION CHECKLIST")
        self._add_separator("-", 40)
        self._add_line()
        self._add_line("[ ] Event sequence is chronologically ordered")
        self._add_line("[ ] Health delta correctly shows change from previous bar")
        self._add_line("[ ] MFE/MAE events correctly identify extremes")
        self._add_line("[ ] Bars from entry count is accurate")
        self._add_line("[ ] Win column matches backtest worksheet values")
        self._add_line("[ ] Win value is consistent across all events for same trade_id")

    def _generate_footer(self):
        """Generate report footer."""
        self._add_line()
        self._add_separator()
        self._add_line("END OF EXIT EVENTS REPORT")
        self._add_separator()

    def generate(self) -> str:
        """Generate the complete report."""
        self.report_lines = []

        # Connect to Excel
        if not self.reader.connect():
            return "ERROR: Could not connect to Excel workbook"

        try:
            # Read data
            print("  Reading exit_events data...")
            exit_events_rows = self.reader.read_exit_events()

            # Calculate statistics
            print("  Calculating statistics...")
            stats = self.stats.calc_exit_events_stats(exit_events_rows)

            # Generate report sections
            print("  Generating report...")
            self._generate_header()
            self._generate_stats_section(stats)

            # Raw data
            self._add_line()
            self._add_line("RAW DATA")
            self._add_line("-" * 40)
            self._add_raw_data_table(EXIT_EVENTS_HEADERS, exit_events_rows)

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
        filename = f"exit_events_{date_str}_bt_report.txt"
        filepath = RESULTS_DIR / filename

        print(f"\nGenerating exit_events report...")

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
    print("EXIT EVENTS REPORT GENERATOR")
    print("=" * 70)

    generator = ExitEventsReportGenerator()
    filepath = generator.save_report()

    if filepath:
        print(f"\nReport generated successfully: {filepath}")
    else:
        print("\nReport generation failed.")


if __name__ == "__main__":
    main()
