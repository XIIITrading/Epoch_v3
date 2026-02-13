"""
================================================================================
EPOCH TRADING SYSTEM - ENTRY EVENTS WORKSHEET REPORT GENERATOR
================================================================================
Generates a .txt report for the entry_events worksheet for Claude AI analysis.

Output: results/ subdirectory with filename: entry_events_MMDDYY_bt_report.txt

v4.1 Format: 44 columns (A-AR) including Win column

Usage:
    from entry_events_bt_report import EntryEventsReportGenerator
    generator = EntryEventsReportGenerator()
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

# Column definitions for entry_events worksheet (44 columns, A-AR)
ENTRY_EVENTS_HEADERS = [
    # A: Join Key
    "Trade_ID",

    # B-I: VWAP Analysis
    "Entry_VWAP", "Entry_vs_VWAP", "VWAP_Diff", "VWAP_Pct",
    "Entry_SMA9", "Entry_vs_SMA9", "Entry_SMA21", "Entry_vs_SMA21",

    # J-M: SMA Analysis
    "SMA9_vs_SMA21", "SMA_Spread", "SMA_Spread_Momentum", "Cross_Price_Est",

    # N-V: Volume Analysis
    "Entry_Volume", "Vol_ROC", "Vol_ROC_Signal", "Vol_Baseline_Avg",
    "Vol_Delta_Signal", "Vol_Delta_Value", "CVD_Trend", "CVD_Slope",
    "Relative_Volume",

    # W-AF: Structure
    "M5_Structure", "M15_Structure", "H1_Structure", "H4_Structure",
    "Structure_Alignment", "Dominant_Structure", "M5_Last_Break", "M15_Last_Break",
    "M5_Pct_to_Strong", "M5_Pct_to_Weak",

    # AG-AJ: Health Score
    "Health_Score", "Health_Max", "Health_Pct", "Health_Label",

    # AK-AN: Alignment Flags
    "HTF_Aligned", "MTF_Aligned", "Vol_Aligned", "Ind_Aligned",

    # AO-AQ: Metadata
    "Enrichment_Time", "Status", "Error",

    # AR: Trade Outcome
    "Win"
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

    def read_entry_events(self) -> List[List[Any]]:
        """Read entry_events worksheet data (44 columns, A-AR)."""
        return self.read_worksheet("entry_events", "A2:AR1000")


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

    def calc_entry_events_stats(self, rows: List[List[Any]]) -> Dict[str, Any]:
        """Calculate entry events summary statistics."""
        if not rows:
            return {"total_entries": 0}

        total = len(rows)

        # Health score distribution (column index 32 = Health_Score)
        health_scores = [self._safe_float(r[32]) for r in rows if r[32] is not None]
        avg_health = sum(health_scores) / len(health_scores) if health_scores else 0

        # Health label distribution (column index 35 = Health_Label)
        health_dist = {}
        for r in rows:
            label = r[35] if len(r) > 35 else "Unknown"
            label = label or "Unknown"
            health_dist[label] = health_dist.get(label, 0) + 1

        # Structure counts (columns 22-25)
        m5_bull = sum(1 for r in rows if len(r) > 22 and r[22] == "BULL")
        m5_bear = sum(1 for r in rows if len(r) > 22 and r[22] == "BEAR")
        m15_bull = sum(1 for r in rows if len(r) > 23 and r[23] == "BULL")
        m15_bear = sum(1 for r in rows if len(r) > 23 and r[23] == "BEAR")
        h1_bull = sum(1 for r in rows if len(r) > 24 and r[24] == "BULL")
        h1_bear = sum(1 for r in rows if len(r) > 24 and r[24] == "BEAR")
        h4_bull = sum(1 for r in rows if len(r) > 25 and r[25] == "BULL")
        h4_bear = sum(1 for r in rows if len(r) > 25 and r[25] == "BEAR")

        # Alignment counts (columns 36-39)
        htf_aligned = sum(1 for r in rows if len(r) > 36 and (r[36] == 1 or r[36] is True))
        mtf_aligned = sum(1 for r in rows if len(r) > 37 and (r[37] == 1 or r[37] is True))
        vol_aligned = sum(1 for r in rows if len(r) > 38 and (r[38] == 1 or r[38] is True))
        ind_aligned = sum(1 for r in rows if len(r) > 39 and (r[39] == 1 or r[39] is True))

        # Win statistics (column index 43 = Win)
        wins = sum(1 for r in rows if len(r) > 43 and self._safe_int(r[43]) == 1)
        losses = total - wins

        # Win rate by health label
        win_by_health = {}
        for r in rows:
            label = r[35] if len(r) > 35 else "Unknown"
            label = label or "Unknown"
            if label not in win_by_health:
                win_by_health[label] = {"total": 0, "wins": 0}
            win_by_health[label]["total"] += 1
            if len(r) > 43 and self._safe_int(r[43]) == 1:
                win_by_health[label]["wins"] += 1

        return {
            "total_entries": total,
            "avg_health": avg_health,
            "health_distribution": health_dist,
            "m5_bull": m5_bull,
            "m5_bear": m5_bear,
            "m15_bull": m15_bull,
            "m15_bear": m15_bear,
            "h1_bull": h1_bull,
            "h1_bear": h1_bear,
            "h4_bull": h4_bull,
            "h4_bear": h4_bear,
            "htf_aligned": htf_aligned,
            "htf_aligned_pct": (htf_aligned / total * 100) if total > 0 else 0,
            "mtf_aligned": mtf_aligned,
            "mtf_aligned_pct": (mtf_aligned / total * 100) if total > 0 else 0,
            "vol_aligned": vol_aligned,
            "vol_aligned_pct": (vol_aligned / total * 100) if total > 0 else 0,
            "ind_aligned": ind_aligned,
            "ind_aligned_pct": (ind_aligned / total * 100) if total > 0 else 0,
            "wins": wins,
            "losses": losses,
            "win_rate": (wins / total * 100) if total > 0 else 0,
            "win_by_health": win_by_health,
        }


# ============================================================================
# REPORT GENERATOR
# ============================================================================

class EntryEventsReportGenerator:
    """Generates .txt report for entry_events worksheet."""

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
        self._add_line("EPOCH ENTRY EVENTS WORKSHEET REPORT")
        self._add_line("Generated for Claude AI Review")
        self._add_separator()
        self._add_line(f"Report Generated: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        self._add_line(f"Workbook: {WORKBOOK_NAME}")
        self._add_line(f"Worksheet: entry_events")
        self._add_line(f"Schema: v4.1 (44 columns, A-AR)")
        self._add_line()
        self._add_line("PURPOSE: This report contains raw data and summary statistics from")
        self._add_line("the entry_events worksheet for validation and analysis by Claude AI.")
        self._add_separator()

    def _generate_stats_section(self, stats: Dict[str, Any]):
        """Generate statistics section."""
        self._add_line()
        self._add_line("SUMMARY STATISTICS")
        self._add_line("-" * 40)
        self._add_line(f"Total Entries:       {stats.get('total_entries', 0)}")
        self._add_line(f"Avg Health Score:    {stats.get('avg_health', 0):.1f}/10")
        self._add_line(f"Wins:                {stats.get('wins', 0)}")
        self._add_line(f"Losses:              {stats.get('losses', 0)}")
        self._add_line(f"Win Rate:            {stats.get('win_rate', 0):.1f}%")

        self._add_line()
        self._add_line("HEALTH DISTRIBUTION:")
        for label, count in stats.get('health_distribution', {}).items():
            pct = (count / stats.get('total_entries', 1)) * 100
            self._add_line(f"  {label}: {count} ({pct:.1f}%)")

        self._add_line()
        self._add_line("WIN RATE BY HEALTH LABEL:")
        for label, data in stats.get('win_by_health', {}).items():
            wr = (data['wins'] / data['total'] * 100) if data['total'] > 0 else 0
            self._add_line(f"  {label}: {data['wins']}/{data['total']} ({wr:.1f}% WR)")

        self._add_line()
        self._add_line("STRUCTURE ANALYSIS:")
        self._add_line(f"  H4: {stats.get('h4_bull', 0)} BULL / {stats.get('h4_bear', 0)} BEAR")
        self._add_line(f"  H1: {stats.get('h1_bull', 0)} BULL / {stats.get('h1_bear', 0)} BEAR")
        self._add_line(f"  M15: {stats.get('m15_bull', 0)} BULL / {stats.get('m15_bear', 0)} BEAR")
        self._add_line(f"  M5: {stats.get('m5_bull', 0)} BULL / {stats.get('m5_bear', 0)} BEAR")

        self._add_line()
        self._add_line("ALIGNMENT RATES:")
        self._add_line(f"  HTF Aligned (H4+H1):  {stats.get('htf_aligned', 0)} ({stats.get('htf_aligned_pct', 0):.1f}%)")
        self._add_line(f"  MTF Aligned (M15+M5): {stats.get('mtf_aligned', 0)} ({stats.get('mtf_aligned_pct', 0):.1f}%)")
        self._add_line(f"  Volume Aligned:       {stats.get('vol_aligned', 0)} ({stats.get('vol_aligned_pct', 0):.1f}%)")
        self._add_line(f"  Indicator Aligned:    {stats.get('ind_aligned', 0)} ({stats.get('ind_aligned_pct', 0):.1f}%)")

    def _generate_validation_checklist(self):
        """Generate validation checklist."""
        self._add_line()
        self._add_separator("-", 40)
        self._add_line("VALIDATION CHECKLIST")
        self._add_separator("-", 40)
        self._add_line()
        self._add_line("[ ] Health score (0-10) correctly sums individual factor scores")
        self._add_line("[ ] Structure labels (BULL/BEAR) match higher timeframe trends")
        self._add_line("[ ] VWAP position correctly identifies above/below")
        self._add_line("[ ] SMA alignment logic is consistent")
        self._add_line("[ ] Win column matches backtest worksheet values")

    def _generate_footer(self):
        """Generate report footer."""
        self._add_line()
        self._add_separator()
        self._add_line("END OF ENTRY EVENTS REPORT")
        self._add_separator()

    def generate(self) -> str:
        """Generate the complete report."""
        self.report_lines = []

        # Connect to Excel
        if not self.reader.connect():
            return "ERROR: Could not connect to Excel workbook"

        try:
            # Read data
            print("  Reading entry_events data...")
            entry_events_rows = self.reader.read_entry_events()

            # Calculate statistics
            print("  Calculating statistics...")
            stats = self.stats.calc_entry_events_stats(entry_events_rows)

            # Generate report sections
            print("  Generating report...")
            self._generate_header()
            self._generate_stats_section(stats)

            # Raw data
            self._add_line()
            self._add_line("RAW DATA")
            self._add_line("-" * 40)
            self._add_raw_data_table(ENTRY_EVENTS_HEADERS, entry_events_rows)

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
        filename = f"entry_events_{date_str}_bt_report.txt"
        filepath = RESULTS_DIR / filename

        print(f"\nGenerating entry_events report...")

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
    print("ENTRY EVENTS REPORT GENERATOR")
    print("=" * 70)

    generator = EntryEventsReportGenerator()
    filepath = generator.save_report()

    if filepath:
        print(f"\nReport generated successfully: {filepath}")
    else:
        print("\nReport generation failed.")


if __name__ == "__main__":
    main()
