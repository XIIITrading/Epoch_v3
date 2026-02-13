"""
================================================================================
EPOCH TRADING SYSTEM - WORKBOOK CLEANER
Clears data from all worksheets while preserving headers
XIII Trading LLC
Version: 1.0.0
================================================================================

This script clears data from all Epoch worksheets based on the master workflow
map (19_zone_analysis_workflow.json). Headers are preserved in all worksheets.

Usage:
    cd C:\XIIITradingSystems\Epoch
    .\venv\Scripts\Activate.ps1
    python epoch_sheet_cleaner.py

Options:
    --dry-run       Show what would be cleared without making changes
    --worksheet     Clear only specific worksheet (e.g., --worksheet backtest)
    --confirm       Skip confirmation prompt

================================================================================
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime

try:
    import xlwings as xw
except ImportError:
    print("ERROR: xlwings not installed. Run: pip install xlwings")
    sys.exit(1)


# =============================================================================
# CONFIGURATION
# =============================================================================

BASE_DIR = Path(r"C:\XIIITradingSystems\Epoch")
WORKBOOK_PATH = BASE_DIR / "epoch_v1.xlsm"
WORKFLOW_MAP_PATH = BASE_DIR / "02_zone_system" / "13_documentation" / "20_maps" / "19_zone_analysis_workflow.json"


# =============================================================================
# WORKSHEET CLEANING SPECIFICATIONS
# =============================================================================

# Define what to clear for each worksheet
# Format: worksheet_name -> list of (start_row, start_col, end_col, max_rows)
# Headers are preserved by starting clearing from data_start_row

WORKSHEET_SPECS = {
    "market_overview": {
        "sections": [
            # Scanner workflow section (rows 4-24, cols B-P)
            {"name": "scanner_workflow", "start_row": 4, "end_row": 24, "start_col": "B", "end_col": "P"},
            # Index structure (rows 29-31, cols B-R) - SPY/QQQ/DIA
            {"name": "index_structure", "start_row": 29, "end_row": 31, "start_col": "B", "end_col": "R"},
            # Ticker structure (rows 36-45, cols B-S) - 10 dynamic tickers
            {"name": "ticker_structure", "start_row": 36, "end_row": 45, "start_col": "B", "end_col": "S"}
        ],
        "preserve_headers": True
    },
    "bar_data": {
        "sections": [
            # ticker_structure (rows 4-13, cols B-M) - Extended to M
            {"name": "ticker_structure", "start_row": 4, "end_row": 13, "start_col": "B", "end_col": "M"},
            # monthly_metrics (rows 17-26, cols B-L)
            {"name": "monthly_metrics", "start_row": 17, "end_row": 26, "start_col": "B", "end_col": "L"},
            # weekly_metrics (rows 31-40, cols B-L)
            {"name": "weekly_metrics", "start_row": 31, "end_row": 40, "start_col": "B", "end_col": "L"},
            # daily_metrics (rows 45-54, cols B-L)
            {"name": "daily_metrics", "start_row": 45, "end_row": 54, "start_col": "B", "end_col": "L"},
            # time_hvn (rows 59-68, cols B-O)
            {"name": "time_hvn", "start_row": 59, "end_row": 68, "start_col": "B", "end_col": "O"},
            # on_options_metrics (rows 73-82, cols B-T)
            {"name": "on_options_metrics", "start_row": 73, "end_row": 82, "start_col": "B", "end_col": "T"},
            # add_metrics (rows 86-95, cols B-V)
            {"name": "add_metrics", "start_row": 86, "end_row": 95, "start_col": "B", "end_col": "V"}
        ],
        "preserve_headers": True
    },
    "raw_zones": {
        "sections": [
            # Dynamic rows, header row 1, data starts row 2
            # Columns A-M, clear from row 2 to max 500 rows
            {"name": "zone_data", "start_row": 2, "end_row": 500, "start_col": "A", "end_col": "M"}
        ],
        "preserve_headers": True,
        "header_row": 1
    },
    "zone_results": {
        "sections": [
            # Dynamic rows, header row 1, data starts row 2
            # Columns A-T, clear from row 2 to max 500 rows
            {"name": "zone_data", "start_row": 2, "end_row": 500, "start_col": "A", "end_col": "T"}
        ],
        "preserve_headers": True,
        "header_row": 1
    },
    "Analysis": {
        "sections": [
            # Primary section (rows 31-40, cols B-L) - Clear data
            {"name": "primary_section", "start_row": 31, "end_row": 40, "start_col": "B", "end_col": "L"},
            # Secondary section (rows 31-40, cols N-X) - Clear data
            {"name": "secondary_section", "start_row": 31, "end_row": 40, "start_col": "N", "end_col": "X"},
            # Setup strings (rows 44-53, cols B-C) - Clear C only, keep B (ticker)
            {"name": "setup_strings", "start_row": 44, "end_row": 53, "start_col": "C", "end_col": "C"},
            # Summary table 1 (rows 3-12, cols B-AC) - Clear data
            {"name": "summary_table1", "start_row": 3, "end_row": 12, "start_col": "B", "end_col": "AC"},
            # Summary table 2 (rows 15-24, cols B-V) - Clear data
            {"name": "summary_table2", "start_row": 15, "end_row": 24, "start_col": "B", "end_col": "V"}
        ],
        "preserve_headers": True
    },
    "backtest": {
        "sections": [
            # Trade log, header row 1, data starts row 2
            # Columns A-U, clear from row 2 to max 1000 rows
            {"name": "trade_log", "start_row": 2, "end_row": 1000, "start_col": "A", "end_col": "U"},
            # Summary section starts at column W - clear that too
            {"name": "summary", "start_row": 2, "end_row": 50, "start_col": "W", "end_col": "AH"}
        ],
        "preserve_headers": True,
        "header_row": 1
    },
    "entry_events": {
        "sections": [
            # Header row 1, data starts row 2
            # Columns A-AR (44 columns), clear from row 2 to max 1000 rows
            {"name": "entry_data", "start_row": 2, "end_row": 1000, "start_col": "A", "end_col": "AR"}
        ],
        "preserve_headers": True,
        "header_row": 1
    },
    "exit_events": {
        "sections": [
            # Header row 1, data starts row 2
            # Columns A-AF (32 columns), clear from row 2 to max 5000 rows (many events per trade)
            {"name": "exit_data", "start_row": 2, "end_row": 5000, "start_col": "A", "end_col": "AF"}
        ],
        "preserve_headers": True,
        "header_row": 1
    },
    "optimal_trade": {
        "sections": [
            # Header row 1, data starts row 2
            # Columns A-AS (45 columns), clear from row 2 to max 5000 rows (many rows per trade)
            {"name": "optimal_data", "start_row": 2, "end_row": 5000, "start_col": "A", "end_col": "AS"}
        ],
        "preserve_headers": True,
        "header_row": 1
    },
    "options_analysis": {
        "sections": [
            # Header row 1, data starts row 2
            # Columns A-V (22 columns), clear from row 2 to max 1000 rows
            {"name": "options_data", "start_row": 2, "end_row": 1000, "start_col": "A", "end_col": "V"}
        ],
        "preserve_headers": True,
        "header_row": 1
    }
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def col_letter_to_number(col_letter: str) -> int:
    """Convert Excel column letter to number (A=1, B=2, etc.)"""
    result = 0
    for char in col_letter.upper():
        result = result * 26 + (ord(char) - ord('A') + 1)
    return result


def load_workflow_map() -> dict:
    """Load the master workflow map for reference."""
    if WORKFLOW_MAP_PATH.exists():
        with open(WORKFLOW_MAP_PATH, 'r') as f:
            return json.load(f)
    return {}


def get_worksheet_info(workflow_map: dict) -> dict:
    """Extract worksheet information from workflow map."""
    return workflow_map.get("worksheet_registry", {})


# =============================================================================
# CLEANER CLASS
# =============================================================================

class EpochWorkbookCleaner:
    """Clears data from Epoch workbook worksheets while preserving headers."""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.app = None
        self.wb = None
        self.workflow_map = load_workflow_map()
        self.cleared_ranges = []

    def connect(self) -> bool:
        """Connect to the Excel workbook."""
        try:
            # Try to connect to existing Excel instance with the workbook open
            for app in xw.apps:
                for wb in app.books:
                    if wb.name == WORKBOOK_PATH.name:
                        self.app = app
                        self.wb = wb
                        print(f"Connected to open workbook: {wb.name}")
                        return True

            # If not open, open it
            print(f"Opening workbook: {WORKBOOK_PATH}")
            self.app = xw.App(visible=True)
            self.wb = self.app.books.open(str(WORKBOOK_PATH))
            return True

        except Exception as e:
            print(f"ERROR: Failed to connect to workbook: {e}")
            return False

    def get_sheet(self, sheet_name: str):
        """Get worksheet by name."""
        try:
            return self.wb.sheets[sheet_name]
        except Exception:
            return None

    def clear_range(self, sheet, start_row: int, end_row: int,
                    start_col: str, end_col: str, section_name: str) -> int:
        """
        Clear a range of cells.

        Returns number of cells cleared.
        """
        start_col_num = col_letter_to_number(start_col)
        end_col_num = col_letter_to_number(end_col)

        range_str = f"{start_col}{start_row}:{end_col}{end_row}"
        cell_count = (end_row - start_row + 1) * (end_col_num - start_col_num + 1)

        if self.dry_run:
            print(f"    [DRY RUN] Would clear: {range_str} ({section_name}) - {cell_count} cells")
        else:
            try:
                sheet.range(range_str).clear_contents()
                print(f"    Cleared: {range_str} ({section_name}) - {cell_count} cells")
            except Exception as e:
                print(f"    ERROR clearing {range_str}: {e}")
                return 0

        self.cleared_ranges.append({
            "sheet": sheet.name,
            "range": range_str,
            "section": section_name,
            "cells": cell_count
        })

        return cell_count

    def clear_worksheet(self, sheet_name: str) -> int:
        """
        Clear all data sections from a worksheet.

        Returns total cells cleared.
        """
        if sheet_name not in WORKSHEET_SPECS:
            print(f"  WARNING: No specification found for worksheet '{sheet_name}'")
            return 0

        sheet = self.get_sheet(sheet_name)
        if sheet is None:
            print(f"  WARNING: Worksheet '{sheet_name}' not found in workbook")
            return 0

        spec = WORKSHEET_SPECS[sheet_name]
        total_cleared = 0

        print(f"\n  Clearing: {sheet_name}")

        for section in spec["sections"]:
            cleared = self.clear_range(
                sheet,
                section["start_row"],
                section["end_row"],
                section["start_col"],
                section["end_col"],
                section["name"]
            )
            total_cleared += cleared

        return total_cleared

    def clear_all(self, specific_worksheet: str = None) -> dict:
        """
        Clear all worksheets (or specific one).

        Returns summary dict.
        """
        if not self.connect():
            return {"success": False, "error": "Failed to connect to workbook"}

        print("\n" + "=" * 60)
        print("EPOCH WORKBOOK CLEANER")
        print("=" * 60)

        if self.dry_run:
            print("\n*** DRY RUN MODE - No changes will be made ***\n")

        print(f"Workbook: {self.wb.name}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        worksheets_to_clear = [specific_worksheet] if specific_worksheet else list(WORKSHEET_SPECS.keys())

        total_cells = 0
        worksheets_cleared = 0

        for ws_name in worksheets_to_clear:
            cells = self.clear_worksheet(ws_name)
            total_cells += cells
            if cells > 0:
                worksheets_cleared += 1

        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Worksheets processed: {worksheets_cleared}")
        print(f"Total cells cleared: {total_cells:,}")
        print(f"Ranges cleared: {len(self.cleared_ranges)}")

        if self.dry_run:
            print("\n*** DRY RUN COMPLETE - No changes were made ***")
        else:
            print("\n*** CLEANING COMPLETE ***")
            print("Headers have been preserved in all worksheets.")

        return {
            "success": True,
            "worksheets_cleared": worksheets_cleared,
            "total_cells": total_cells,
            "ranges": self.cleared_ranges,
            "dry_run": self.dry_run
        }


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Clear data from Epoch workbook worksheets while preserving headers."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be cleared without making changes"
    )
    parser.add_argument(
        "--worksheet",
        type=str,
        help="Clear only specific worksheet (e.g., backtest, entry_events)"
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Skip confirmation prompt"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all worksheets that can be cleared"
    )

    args = parser.parse_args()

    # List mode
    if args.list:
        print("\nWorksheets available for clearing:")
        print("-" * 40)
        for ws_name, spec in WORKSHEET_SPECS.items():
            section_count = len(spec["sections"])
            print(f"  {ws_name}: {section_count} section(s)")
        print()
        return

    # Validation
    if args.worksheet and args.worksheet not in WORKSHEET_SPECS:
        print(f"ERROR: Unknown worksheet '{args.worksheet}'")
        print(f"Valid worksheets: {', '.join(WORKSHEET_SPECS.keys())}")
        sys.exit(1)

    # Confirmation
    if not args.confirm and not args.dry_run:
        print("\n" + "=" * 60)
        print("WARNING: This will clear data from the Epoch workbook!")
        print("=" * 60)

        if args.worksheet:
            print(f"\nWorksheet to clear: {args.worksheet}")
        else:
            print(f"\nWorksheets to clear: {', '.join(WORKSHEET_SPECS.keys())}")

        print("\nHeaders will be preserved.")
        print("Make sure you have a backup before proceeding.\n")

        response = input("Type 'yes' to continue or 'dry' for dry run: ").strip().lower()

        if response == 'dry':
            args.dry_run = True
        elif response != 'yes':
            print("Aborted.")
            sys.exit(0)

    # Run cleaner
    cleaner = EpochWorkbookCleaner(dry_run=args.dry_run)
    result = cleaner.clear_all(specific_worksheet=args.worksheet)

    if not result["success"]:
        print(f"\nERROR: {result.get('error', 'Unknown error')}")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
